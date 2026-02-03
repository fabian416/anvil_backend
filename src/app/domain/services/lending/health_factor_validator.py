"""
Health Factor Validator Domain Service.

Pure business logic for validating health factor safety in lending operations.
This service has NO infrastructure dependencies - only domain logic.
"""

from decimal import Decimal
from typing import Optional

from app.domain.value_objects.lending.health_factor_result import (
    HealthFactorLevel,
    HealthFactorResult,
)


class HealthFactorValidator:
    """
    Domain service for validating health factor safety.

    This service implements the core business rules for assessing
    whether a lending operation (particularly borrows) is safe based
    on health factor calculations.

    Health Factor Formula:
        HF = (Collateral * Liquidation Threshold) / Debt

    Safety Thresholds:
        HF >= 2.0:   SAFE (recommended)
        HF >= 1.5:   CAUTION (acceptable)
        HF >= 1.2:   DANGER (risky)
        HF >= 1.0:   CRITICAL (very risky)
        HF < 1.0:    LIQUIDATABLE (will be liquidated)

    Minimum Safe HF: 1.2 (operations below this are blocked)
    Recommended HF: 1.5 (target for safety)
    """

    # Safety thresholds (business rules)
    MINIMUM_SAFE_HF = Decimal("1.2")
    """Minimum HF to allow operations (safety threshold)"""

    RECOMMENDED_HF = Decimal("1.5")
    """Recommended target HF for safety"""

    SAFE_HF = Decimal("2.0")
    """HF level considered very safe"""

    def validate_borrow(
        self,
        current_collateral_usd: Decimal,
        current_debt_usd: Decimal,
        new_borrow_usd: Decimal,
        liquidation_threshold: Decimal,
        collateral_asset: str = "ETH",
        current_price: Optional[Decimal] = None,
    ) -> HealthFactorResult:
        """
        Validate if a new borrow operation is safe.

        Args:
            current_collateral_usd: Current collateral value in USD
            current_debt_usd: Current debt value in USD
            new_borrow_usd: New borrow amount in USD
            liquidation_threshold: Weighted average liquidation threshold (e.g., 0.825 for ETH)
            collateral_asset: Primary collateral asset symbol (for liquidation price calc)
            current_price: Current price of collateral asset (for liquidation price calc)

        Returns:
            HealthFactorResult with comprehensive safety assessment

        Example:
            >>> validator = HealthFactorValidator()
            >>> result = validator.validate_borrow(
            ...     current_collateral_usd=Decimal("5000"),  # $5000 ETH
            ...     current_debt_usd=Decimal("0"),
            ...     new_borrow_usd=Decimal("2000"),  # Borrow $2000 USDC
            ...     liquidation_threshold=Decimal("0.825"),
            ... )
            >>> result.is_safe
            True
            >>> result.level
            HealthFactorLevel.SAFE
        """
        # Calculate current health factor
        current_hf = self._calculate_health_factor(
            collateral_usd=current_collateral_usd,
            debt_usd=current_debt_usd,
            liquidation_threshold=liquidation_threshold,
        )

        # Calculate projected health factor after borrow
        projected_debt_usd = current_debt_usd + new_borrow_usd
        projected_hf = self._calculate_health_factor(
            collateral_usd=current_collateral_usd,
            debt_usd=projected_debt_usd,
            liquidation_threshold=liquidation_threshold,
        )

        # Determine risk level
        level = self._determine_level(projected_hf)

        # Check if operation is safe
        is_safe = projected_hf >= self.MINIMUM_SAFE_HF

        # Calculate liquidation price (if applicable)
        liquidation_price = None
        if current_price and projected_debt_usd > 0:
            liquidation_price = self._calculate_liquidation_price(
                current_collateral_usd=current_collateral_usd,
                projected_debt_usd=projected_debt_usd,
                liquidation_threshold=liquidation_threshold,
                current_price=current_price,
            )

        # Calculate max safe borrow
        max_safe_borrow = self._calculate_max_safe_borrow(
            current_collateral_usd=current_collateral_usd,
            current_debt_usd=current_debt_usd,
            liquidation_threshold=liquidation_threshold,
        )

        # Generate warning message
        warning = self._generate_warning(
            projected_hf=projected_hf,
            level=level,
            current_price=current_price,
            liquidation_price=liquidation_price,
            collateral_asset=collateral_asset,
        )

        return HealthFactorResult(
            current_hf=current_hf,
            projected_hf=projected_hf,
            level=level,
            is_safe=is_safe,
            warning_message=warning,
            liquidation_price=liquidation_price,
            max_safe_borrow_usd=max_safe_borrow,
            collateral_usd=current_collateral_usd,
            current_debt_usd=current_debt_usd,
            projected_debt_usd=projected_debt_usd,
        )

    def _calculate_health_factor(
        self,
        collateral_usd: Decimal,
        debt_usd: Decimal,
        liquidation_threshold: Decimal,
    ) -> Decimal:
        """
        Calculate health factor using standard Aave formula.

        Formula: HF = (Collateral * Liquidation Threshold) / Debt

        Args:
            collateral_usd: Total collateral value in USD
            debt_usd: Total debt value in USD
            liquidation_threshold: Weighted avg liquidation threshold (0 to 1)

        Returns:
            Health factor (Decimal.inf if no debt)

        Notes:
            - HF < 1.0 means position can be liquidated
            - HF = inf means no debt (no liquidation risk)
        """
        if debt_usd <= 0:
            return Decimal("inf")

        adjusted_collateral = collateral_usd * liquidation_threshold
        return adjusted_collateral / debt_usd

    def _determine_level(self, hf: Decimal) -> HealthFactorLevel:
        """
        Determine risk level based on health factor value.

        Args:
            hf: Health factor value

        Returns:
            Risk level classification
        """
        if hf >= self.SAFE_HF:
            return HealthFactorLevel.SAFE
        elif hf >= self.RECOMMENDED_HF:
            return HealthFactorLevel.CAUTION
        elif hf >= self.MINIMUM_SAFE_HF:
            return HealthFactorLevel.DANGER
        elif hf >= Decimal("1.0"):
            return HealthFactorLevel.CRITICAL
        else:
            return HealthFactorLevel.LIQUIDATABLE

    def _calculate_max_safe_borrow(
        self,
        current_collateral_usd: Decimal,
        current_debt_usd: Decimal,
        liquidation_threshold: Decimal,
    ) -> Decimal:
        """
        Calculate maximum additional borrow to maintain HF >= 1.5 (recommended).

        Args:
            current_collateral_usd: Current collateral in USD
            current_debt_usd: Current debt in USD
            liquidation_threshold: Liquidation threshold

        Returns:
            Maximum safe additional borrow amount in USD
        """
        target_hf = self.RECOMMENDED_HF

        # Calculate max total debt to maintain target HF
        # HF = (Collateral * LT) / Debt
        # Debt = (Collateral * LT) / HF
        max_total_debt = (current_collateral_usd * liquidation_threshold) / target_hf

        # Calculate additional borrow capacity
        additional_borrow = max_total_debt - current_debt_usd

        # Cannot borrow negative amounts
        return max(Decimal("0"), additional_borrow)

    def _calculate_liquidation_price(
        self,
        current_collateral_usd: Decimal,
        projected_debt_usd: Decimal,
        liquidation_threshold: Decimal,
        current_price: Decimal,
    ) -> Decimal:
        """
        Calculate asset price at which liquidation would occur.

        At liquidation, HF = 1.0:
            1.0 = (Collateral_Amount * Price * LT) / Debt
            Price = Debt / (Collateral_Amount * LT)

        Args:
            current_collateral_usd: Current collateral value in USD
            projected_debt_usd: Projected debt in USD
            liquidation_threshold: Liquidation threshold
            current_price: Current asset price

        Returns:
            Price at which liquidation occurs
        """
        if current_collateral_usd == 0 or current_price == 0:
            return Decimal("0")

        # Calculate collateral amount in asset units
        collateral_amount = current_collateral_usd / current_price

        # Calculate liquidation price
        # HF = 1.0 when: Price * Collateral * LT = Debt
        liquidation_price = projected_debt_usd / (
            collateral_amount * liquidation_threshold
        )

        return liquidation_price

    def _generate_warning(
        self,
        projected_hf: Decimal,
        level: HealthFactorLevel,
        current_price: Optional[Decimal],
        liquidation_price: Optional[Decimal],
        collateral_asset: str,
    ) -> str:
        """
        Generate human-readable warning message.

        Args:
            projected_hf: Projected health factor
            level: Risk level
            current_price: Current asset price
            liquidation_price: Liquidation price
            collateral_asset: Collateral asset symbol

        Returns:
            Warning message with emoji and recommendations
        """
        hf_display = f"{projected_hf:.2f}" if projected_hf != Decimal("inf") else "∞"

        if level == HealthFactorLevel.SAFE:
            return f"✅ SAFE - Your position is well-collateralized (HF: {hf_display})"

        elif level == HealthFactorLevel.CAUTION:
            msg = f"⚠️ CAUTION - Health Factor {hf_display}. Monitor your position closely."
            if liquidation_price and current_price:
                price_drop_pct = (
                    (current_price - liquidation_price) / current_price
                ) * 100
                msg += f"\n\nLiquidation if {collateral_asset} drops {price_drop_pct:.1f}% to ${liquidation_price:.2f}"
            return msg

        elif level == HealthFactorLevel.DANGER:
            msg = f"🔶 DANGER - Health Factor {hf_display}. Consider reducing borrow or adding collateral."
            if liquidation_price and current_price:
                price_drop_pct = (
                    (current_price - liquidation_price) / current_price
                ) * 100
                msg += f"\n\nLiquidation if {collateral_asset} drops {price_drop_pct:.1f}% to ${liquidation_price:.2f}"
            msg += f"\n\nRecommendation: Reduce borrow to maintain HF >= {self.RECOMMENDED_HF}"
            return msg

        elif level == HealthFactorLevel.CRITICAL:
            msg = (
                f"🔴 CRITICAL - Health Factor {hf_display}. Very high liquidation risk!"
            )
            if liquidation_price and current_price:
                price_drop_pct = (
                    (current_price - liquidation_price) / current_price
                ) * 100
                msg += f"\n\nLiquidation if {collateral_asset} drops just {price_drop_pct:.1f}% to ${liquidation_price:.2f}"
            msg += f"\n\n⚠️ OPERATION BLOCKED - Minimum recommended HF is {self.MINIMUM_SAFE_HF}"
            return msg

        else:  # LIQUIDATABLE
            msg = f"❌ LIQUIDATABLE - Health Factor {hf_display}. Position will be immediately liquidated!"
            msg += f"\n\n⚠️ OPERATION BLOCKED - This borrow would result in immediate liquidation."
            msg += f"\n\nYou must add more collateral or reduce borrow amount."
            return msg
