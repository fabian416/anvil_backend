"""
Health Check Query Handler for Lending Operations.

Handles health factor monitoring queries following CQRS principles.
"""

import logging
from decimal import Decimal
from typing import List

from app.application.lending.queries.health_check_query import (
    HealthCheckQuery,
    HealthCheckResult,
    PositionSummary,
)
from app.domain.ports.aave_gateway import AaveGateway
from app.domain.services.lending.health_factor_validator import HealthFactorValidator
from app.domain.value_objects.lending.health_factor_result import HealthFactorLevel

logger = logging.getLogger(__name__)


class HealthCheckQueryHandler:
    """
    Query handler for health factor monitoring.

    Orchestrates:
    1. Fetch user positions from Aave
    2. Calculate current health factor
    3. Determine risk level and recommendations
    4. Return comprehensive health check result

    This is a READ-ONLY operation (CQRS query):
    - No state modification
    - Optimized for fast reads
    - Can be cached aggressively
    - Idempotent

    Dependencies are injected via Dishka DI with REQUEST scope.
    """

    __slots__ = (
        "_aave_gateway",
        "_hf_validator",
    )

    def __init__(
        self,
        aave_gateway: AaveGateway,
        hf_validator: HealthFactorValidator,
    ):
        """
        Initialize health check query handler.

        Args:
            aave_gateway: Port for Aave operations
            hf_validator: Domain service for health factor classification
        """
        self._aave_gateway = aave_gateway
        self._hf_validator = hf_validator

    async def handle(
        self,
        query: HealthCheckQuery,
        wallet_address: str,
    ) -> HealthCheckResult:
        """
        Handle health check query.

        Flow:
        1. Fetch user position from Aave
        2. Extract supplies and borrows
        3. Calculate health factor metrics
        4. Determine risk level
        5. Generate recommendations
        6. Return comprehensive result

        Args:
            query: Health check query
            wallet_address: User's wallet address (from auth context)

        Returns:
            HealthCheckResult with comprehensive analysis

        Example:
            >>> result = await handler.handle(
            ...     query=HealthCheckQuery(
            ...         user_id=UUID("..."),
            ...         protocol="aave",
            ...         chain="ethereum",
            ...     ),
            ...     wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            ... )
            >>> print(f"Health Factor: {result.current_hf}")
            >>> print(f"Risk Level: {result.level}")
        """
        logger.info(
            f"Handling health check query: user={query.user_id}, "
            f"protocol={query.protocol}, chain={query.chain}"
        )

        # STEP 1: Fetch user position from Aave
        position = await self._aave_gateway.get_user_positions(
            user_address=wallet_address,
            chain=query.chain,
        )

        # STEP 2: Extract position details
        positions = self._build_position_summaries(position)

        # STEP 3: Calculate health factor and risk level
        current_hf = position.health_factor
        level = self._hf_validator._determine_level(current_hf)

        # STEP 4: Get color and emoji for risk level
        emoji, color = self._get_risk_display(level)

        # STEP 5: Calculate available borrowing capacity
        available_to_borrow_usd = self._hf_validator._calculate_max_safe_borrow(
            current_collateral_usd=position.total_collateral_usd,
            current_debt_usd=position.total_debt_usd,
            liquidation_threshold=position.max_ltv + Decimal("0.05"),  # Estimate
        )

        # STEP 6: Calculate liquidation price (if applicable)
        liquidation_price = None
        if position.total_debt_usd > 0 and position.supplies:
            # Use largest collateral position for liquidation calc
            largest_supply = max(position.supplies, key=lambda s: s.balance_usd)
            liquidation_threshold = position.max_ltv + Decimal("0.05")

            # Calculate liquidation price
            if largest_supply.balance > 0:
                collateral_amount = largest_supply.balance
                liquidation_price = position.total_debt_usd / (
                    collateral_amount * liquidation_threshold
                )

        # STEP 7: Generate warning message
        warning_message = self._generate_warning(
            current_hf=current_hf,
            level=level,
            total_debt=position.total_debt_usd,
        )

        # STEP 8: Generate recommendations
        recommendations = self._generate_recommendations(
            current_hf=current_hf,
            level=level,
            available_to_borrow=available_to_borrow_usd,
            total_debt=position.total_debt_usd,
        )

        # STEP 9: Build result
        result = HealthCheckResult(
            current_hf=current_hf,
            level=level.value.upper(),
            emoji=emoji,
            color=color,
            positions=positions,
            total_collateral_usd=position.total_collateral_usd,
            total_debt_usd=position.total_debt_usd,
            available_to_borrow_usd=available_to_borrow_usd,
            liquidation_threshold=position.max_ltv + Decimal("0.05"),
            liquidation_price=liquidation_price,
            warning_message=warning_message,
            recommendations=recommendations,
            protocol=query.protocol,
            chain=query.chain,
        )

        logger.info(
            f"Health check complete: hf={current_hf:.2f}, level={level.value}, "
            f"collateral=${position.total_collateral_usd:.2f}, "
            f"debt=${position.total_debt_usd:.2f}"
        )

        return result

    def _build_position_summaries(self, position) -> List[PositionSummary]:
        """
        Build position summaries from Aave position.

        Args:
            position: Aave position entity

        Returns:
            List of position summaries
        """
        summaries = []

        # Add supplies
        for supply in position.supplies:
            summaries.append(
                PositionSummary(
                    asset=supply.symbol,
                    type="supply",
                    amount=supply.balance,
                    amount_usd=supply.balance_usd,
                    apy=supply.supply_apy,
                    is_collateral=supply.is_collateral,
                )
            )

        # Add borrows
        for borrow in position.borrows:
            summaries.append(
                PositionSummary(
                    asset=borrow.symbol,
                    type="borrow",
                    amount=borrow.balance,
                    amount_usd=borrow.balance_usd,
                    apy=borrow.borrow_apy,
                    is_collateral=False,
                )
            )

        return summaries

    def _get_risk_display(self, level: HealthFactorLevel) -> tuple[str, str]:
        """
        Get emoji and color for risk level.

        Args:
            level: Risk level classification

        Returns:
            Tuple of (emoji, color_hex)
        """
        RISK_DISPLAY = {
            HealthFactorLevel.SAFE: ("✅", "#00CC66"),
            HealthFactorLevel.CAUTION: ("⚠️", "#FFB84D"),
            HealthFactorLevel.DANGER: ("🔶", "#FF6B35"),
            HealthFactorLevel.CRITICAL: ("🔴", "#DC143C"),
            HealthFactorLevel.LIQUIDATABLE: ("❌", "#8B0000"),
        }
        return RISK_DISPLAY.get(level, ("❓", "#808080"))

    def _generate_warning(
        self,
        current_hf: Decimal,
        level: HealthFactorLevel,
        total_debt: Decimal,
    ) -> str:
        """
        Generate human-readable warning message.

        Args:
            current_hf: Current health factor
            level: Risk level
            total_debt: Total debt in USD

        Returns:
            Warning message
        """
        hf_display = f"{current_hf:.2f}" if current_hf != Decimal("inf") else "∞"

        if level == HealthFactorLevel.SAFE:
            return f"✅ SAFE - Your position is well-collateralized (HF: {hf_display})"

        elif level == HealthFactorLevel.CAUTION:
            return f"⚠️ CAUTION - Health Factor {hf_display}. Monitor your position closely."

        elif level == HealthFactorLevel.DANGER:
            return f"🔶 DANGER - Health Factor {hf_display}. Consider reducing debt or adding collateral."

        elif level == HealthFactorLevel.CRITICAL:
            return f"🔴 CRITICAL - Health Factor {hf_display}. Very high liquidation risk! Take action immediately."

        else:  # LIQUIDATABLE
            return f"❌ LIQUIDATABLE - Health Factor {hf_display}. Position is at risk of immediate liquidation!"

    def _generate_recommendations(
        self,
        current_hf: Decimal,
        level: HealthFactorLevel,
        available_to_borrow: Decimal,
        total_debt: Decimal,
    ) -> List[str]:
        """
        Generate actionable recommendations based on health factor.

        Args:
            current_hf: Current health factor
            level: Risk level
            available_to_borrow: Available borrowing capacity
            total_debt: Total debt in USD

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if level == HealthFactorLevel.SAFE:
            if available_to_borrow > 0:
                recommendations.append(
                    f"💡 You can safely borrow up to ${available_to_borrow:.2f} more"
                )
            recommendations.append(
                "✅ Your position is healthy - maintain current strategy"
            )

        elif level == HealthFactorLevel.CAUTION:
            recommendations.append(
                "⚠️ Consider adding more collateral or reducing debt to improve health factor"
            )
            recommendations.append(
                "📊 Monitor price movements of your collateral assets"
            )

        elif level == HealthFactorLevel.DANGER:
            repay_amount = total_debt * Decimal("0.25")  # Repay 25% to improve HF
            recommendations.append(
                f"🔶 URGENT: Repay at least ${repay_amount:.2f} to reduce liquidation risk"
            )
            recommendations.append(
                "💰 Or add more collateral to improve your health factor above 1.5"
            )

        elif (
            level == HealthFactorLevel.CRITICAL
            or level == HealthFactorLevel.LIQUIDATABLE
        ):
            repay_amount = total_debt * Decimal("0.5")  # Repay 50% for critical
            recommendations.append(
                f"🚨 IMMEDIATE ACTION REQUIRED: Repay at least ${repay_amount:.2f}"
            )
            recommendations.append(
                "💰 Add significant collateral immediately to avoid liquidation"
            )
            recommendations.append(
                "⚡ Set up price alerts to monitor your position 24/7"
            )

        return recommendations
