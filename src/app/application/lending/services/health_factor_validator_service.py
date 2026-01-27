"""
Health Factor Validator Application Service.

Orchestrates domain validation logic with infrastructure dependencies
(Aave positions, price data) to validate lending operations.
"""

import logging
from decimal import Decimal
from typing import Protocol

from app.domain.entities.lending.aave_position import AavePosition
from app.domain.services.lending.health_factor_validator import HealthFactorValidator
from app.domain.value_objects.lending.health_factor_result import HealthFactorResult

logger = logging.getLogger(__name__)


class IAavePositionProvider(Protocol):
    """
    Port for fetching Aave position data.

    This abstracts the infrastructure layer (MCP, direct RPC, etc.)
    from the application service.
    """

    async def get_user_position(
        self,
        wallet: str,
        chain: str = "ethereum",
    ) -> AavePosition:
        """
        Get user's current Aave position.

        Args:
            wallet: User wallet address
            chain: Blockchain network

        Returns:
            AavePosition with collateral, debt, and health metrics
        """
        ...


class IPriceProvider(Protocol):
    """
    Port for fetching asset prices.

    Abstracts price data sources (CoinGecko, Chainlink, etc.)
    """

    async def get_price_usd(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> Decimal:
        """
        Get current price of an asset in USD.

        Args:
            asset: Asset symbol (e.g., "ETH", "USDC")
            chain: Blockchain network

        Returns:
            Current price in USD
        """
        ...


class HealthFactorValidatorService:
    """
    Application service for health factor validation.

    Orchestrates:
    1. Domain validation logic (HealthFactorValidator)
    2. Infrastructure calls (Aave positions, price data)
    3. Business rules (minimum HF thresholds)

    This service has NO presentation layer dependencies - it's pure
    application logic that can be used by any presentation layer
    (HTTP controllers, CLI, agents, etc.)
    """

    def __init__(
        self,
        domain_validator: HealthFactorValidator,
        aave_provider: IAavePositionProvider,
        price_provider: IPriceProvider,
    ) -> None:
        """
        Initialize health factor validator service.

        Args:
            domain_validator: Domain service for HF calculations
            aave_provider: Infrastructure adapter for Aave data
            price_provider: Infrastructure adapter for price data
        """
        self._validator = domain_validator
        self._aave = aave_provider
        self._prices = price_provider

    async def validate_borrow(
        self,
        wallet: str,
        borrow_asset: str,
        borrow_amount: Decimal,
        chain: str = "ethereum",
    ) -> HealthFactorResult:
        """
        Validate if a borrow operation is safe.

        This method:
        1. Fetches current Aave position (collateral, debt, LT)
        2. Fetches current prices for assets
        3. Delegates to domain validator for HF calculation
        4. Returns comprehensive validation result

        Args:
            wallet: User wallet address
            borrow_asset: Asset to borrow (e.g., "USDC")
            borrow_amount: Amount to borrow (in asset units)
            chain: Blockchain network

        Returns:
            HealthFactorResult with safety assessment

        Raises:
            ValueError: If wallet or asset is invalid
            Exception: If infrastructure calls fail

        Example:
            >>> result = await validator.validate_borrow(
            ...     wallet="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            ...     borrow_asset="USDC",
            ...     borrow_amount=Decimal("2000"),
            ...     chain="ethereum",
            ... )
            >>> if not result.is_safe:
            ...     raise UnsafeBorrowError(result.warning_message)
        """
        logger.info(
            f"Validating borrow: wallet={wallet[:10]}..., "
            f"asset={borrow_asset}, amount={borrow_amount}, chain={chain}"
        )

        # Step 1: Fetch current Aave position
        try:
            position = await self._aave.get_user_position(wallet=wallet, chain=chain)
        except Exception as e:
            logger.error(f"Failed to fetch Aave position: {e}")
            raise ValueError(f"Could not fetch lending position for wallet: {e}") from e

        # Step 2: Fetch current price for borrow asset
        try:
            borrow_price = await self._prices.get_price_usd(asset=borrow_asset, chain=chain)
        except Exception as e:
            logger.error(f"Failed to fetch price for {borrow_asset}: {e}")
            raise ValueError(f"Could not fetch price for {borrow_asset}: {e}") from e

        # Calculate borrow value in USD
        borrow_usd = borrow_amount * borrow_price

        # Step 3: Determine primary collateral asset and price (for liquidation calc)
        collateral_asset = "ETH"  # Default
        collateral_price = Decimal("0")

        if position.supplies:
            # Use largest collateral position
            largest_supply = max(position.supplies, key=lambda s: s.balance_usd)
            collateral_asset = largest_supply.symbol
            try:
                collateral_price = await self._prices.get_price_usd(
                    asset=collateral_asset,
                    chain=chain,
                )
            except Exception as e:
                logger.warning(f"Failed to fetch collateral price: {e}")
                collateral_price = Decimal("0")

        # Step 4: Extract liquidation threshold from position
        # In Aave, this is calculated as weighted average of all collateral LTs
        # For now, we use a reasonable default if not available
        liquidation_threshold = Decimal("0.825")  # ETH default

        # If position has max_ltv, we can estimate liquidation threshold
        # Typically: liquidation_threshold = max_ltv + 0.05
        if position.max_ltv > 0:
            liquidation_threshold = position.max_ltv + Decimal("0.05")

        logger.debug(
            f"Position data: collateral_usd={position.total_collateral_usd}, "
            f"debt_usd={position.total_debt_usd}, lt={liquidation_threshold}"
        )

        # Step 5: Delegate to domain validator
        result = self._validator.validate_borrow(
            current_collateral_usd=position.total_collateral_usd,
            current_debt_usd=position.total_debt_usd,
            new_borrow_usd=borrow_usd,
            liquidation_threshold=liquidation_threshold,
            collateral_asset=collateral_asset,
            current_price=collateral_price if collateral_price > 0 else None,
        )

        logger.info(
            f"Validation result: is_safe={result.is_safe}, "
            f"projected_hf={result.projected_hf}, level={result.level}"
        )

        return result

    async def validate_supply(
        self,
        wallet: str,
        supply_asset: str,
        supply_amount: Decimal,
        chain: str = "ethereum",
    ) -> HealthFactorResult:
        """
        Validate if a supply (collateral increase) operation is safe.

        Supply operations generally IMPROVE health factor, but this
        method ensures the operation is valid and calculates the impact.

        Args:
            wallet: User wallet address
            supply_asset: Asset to supply (e.g., "ETH")
            supply_amount: Amount to supply
            chain: Blockchain network

        Returns:
            HealthFactorResult showing improved HF

        Example:
            >>> result = await validator.validate_supply(
            ...     wallet="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            ...     supply_asset="ETH",
            ...     supply_amount=Decimal("1.0"),
            ... )
            >>> # Supply always improves HF
            >>> assert result.projected_hf > result.current_hf
        """
        logger.info(
            f"Validating supply: wallet={wallet[:10]}..., "
            f"asset={supply_asset}, amount={supply_amount}, chain={chain}"
        )

        # Fetch current position
        position = await self._aave.get_user_position(wallet=wallet, chain=chain)

        # Fetch supply asset price
        supply_price = await self._prices.get_price_usd(asset=supply_asset, chain=chain)
        supply_usd = supply_amount * supply_price

        # Estimate liquidation threshold for new collateral
        # TODO: Make this more accurate by fetching from Aave reserve data
        lt_estimates = {
            "ETH": Decimal("0.825"),
            "WETH": Decimal("0.825"),
            "WBTC": Decimal("0.70"),
            "USDC": Decimal("0.85"),
            "USDT": Decimal("0.85"),
            "DAI": Decimal("0.80"),
        }
        new_asset_lt = lt_estimates.get(supply_asset.upper(), Decimal("0.75"))

        # Calculate new collateral value
        new_collateral_usd = position.total_collateral_usd + supply_usd

        # Calculate weighted average liquidation threshold
        if position.total_collateral_usd > 0:
            current_lt = position.max_ltv + Decimal("0.05")  # Estimate
            weighted_lt = (
                (position.total_collateral_usd * current_lt) +
                (supply_usd * new_asset_lt)
            ) / new_collateral_usd
        else:
            weighted_lt = new_asset_lt

        # Calculate new health factor (debt stays same)
        # Supply ALWAYS improves or maintains HF
        current_hf = position.health_factor
        if position.total_debt_usd > 0:
            projected_hf = (new_collateral_usd * weighted_lt) / position.total_debt_usd
        else:
            projected_hf = Decimal("inf")

        # Create result
        level = self._validator._determine_level(projected_hf)
        is_safe = True  # Supply is always safe

        result = HealthFactorResult(
            current_hf=current_hf,
            projected_hf=projected_hf,
            level=level,
            is_safe=is_safe,
            warning_message=f"✅ Supply will improve health factor: {current_hf:.2f} → {projected_hf:.2f}",
            liquidation_price=None,
            max_safe_borrow_usd=self._validator._calculate_max_safe_borrow(
                current_collateral_usd=new_collateral_usd,
                current_debt_usd=position.total_debt_usd,
                liquidation_threshold=weighted_lt,
            ),
            collateral_usd=new_collateral_usd,
            current_debt_usd=position.total_debt_usd,
            projected_debt_usd=position.total_debt_usd,
        )

        logger.info(
            f"Supply validation: current_hf={current_hf:.2f}, "
            f"projected_hf={projected_hf:.2f}"
        )

        return result
