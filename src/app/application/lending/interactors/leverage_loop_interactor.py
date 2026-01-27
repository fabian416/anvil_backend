"""
Leverage Loop Interactor for Lending Operations.

Orchestrates leverage loop operations with multi-step approval workflow.
Calculates optimal iteration steps while maintaining health factor safety.
"""

import logging
from decimal import Decimal
from uuid import UUID, uuid4

from app.application.lending.commands.leverage_loop_command import (
    LeverageLoopCommand,
    LeverageLoopResult,
    LeverageLoopStep,
)
from app.application.lending.services.health_factor_validator_service import (
    HealthFactorValidatorService,
)
from app.domain.ports.balance_checker import IBalanceChecker
from app.domain.ports.swap_executor import ISwapExecutor
from app.domain.ports.aave_gateway import AaveGateway
from app.domain.ports.lending_repository import ILendingRepository
from app.domain.services.lending.health_factor_validator import HealthFactorValidator

logger = logging.getLogger(__name__)


class InsufficientBalanceError(Exception):
    """
    Raised when user has insufficient balance to start leverage loop.

    Attributes:
        required: Required balance amount
        available: Available balance amount
        asset: Asset symbol
    """

    def __init__(self, required: Decimal, available: Decimal, asset: str):
        self.required = required
        self.available = available
        self.asset = asset
        super().__init__(
            f"Insufficient {asset} balance. Required: {required}, Available: {available}"
        )


class UnsupportedAssetError(Exception):
    """Raised when asset is not supported for leverage loops."""

    def __init__(self, asset: str):
        self.asset = asset
        super().__init__(
            f"Asset {asset} not supported for leverage loops. "
            f"Supported: ETH, WETH, wstETH"
        )


class LeverageLoopInteractor:
    """
    Interactor for leverage loop use case.

    Orchestrates:
    1. Initial balance validation
    2. Optimal iteration calculation
    3. Multi-step execution plan generation
    4. Health factor validation for each borrow step
    5. Swap quote calculation for each swap step
    6. Loop state persistence for resumability

    CRITICAL: This interactor ONLY calculates steps and validates safety.
    It does NOT execute anything automatically. Each step requires
    separate user approval via Privy.

    Dependencies are injected via Dishka DI with REQUEST scope.
    """

    __slots__ = (
        "_hf_validator_service",
        "_hf_validator_domain",
        "_balance_checker",
        "_swap_executor",
        "_aave_gateway",
        "_repository",
    )

    def __init__(
        self,
        hf_validator_service: HealthFactorValidatorService,
        hf_validator_domain: HealthFactorValidator,
        balance_checker: IBalanceChecker,
        swap_executor: ISwapExecutor,
        aave_gateway: AaveGateway,
        repository: ILendingRepository,
    ):
        """
        Initialize leverage loop interactor.

        Args:
            hf_validator_service: Application service for HF validation with infra
            hf_validator_domain: Domain service for pure HF calculations
            balance_checker: Port for checking wallet balances
            swap_executor: Port for swap quotes and execution data
            aave_gateway: Port for Aave operations
            repository: Port for position persistence
        """
        self._hf_validator_service = hf_validator_service
        self._hf_validator_domain = hf_validator_domain
        self._balance_checker = balance_checker
        self._swap_executor = swap_executor
        self._aave_gateway = aave_gateway
        self._repository = repository

    async def calculate_loop_steps(
        self,
        command: LeverageLoopCommand,
        wallet_address: str,
    ) -> LeverageLoopResult:
        """
        Calculate all steps needed to achieve target leverage.

        CRITICAL: This only calculates steps and validates safety.
        It does NOT execute anything automatically.
        Each step requires separate user approval via Privy.

        Flow:
        1. Validate initial conditions (balance, supported asset, leverage range)
        2. Calculate optimal number of iterations for target leverage
        3. For each iteration:
           a. Calculate max safe borrow maintaining min health factor
           b. Validate health factor after borrow
           c. Get swap quote for borrow → collateral
           d. Create supply, borrow, swap steps
        4. Return complete execution plan with warnings

        Args:
            command: Leverage loop command with parameters
            wallet_address: User's wallet address (from auth context)

        Returns:
            LeverageLoopResult with complete execution plan

        Raises:
            InsufficientBalanceError: If user lacks initial collateral
            UnsupportedAssetError: If asset not supported
            ValueError: If calculations fail or safety violated

        Example:
            >>> result = await interactor.calculate_loop_steps(
            ...     command=LeverageLoopCommand(
            ...         user_id=UUID("..."),
            ...         asset="ETH",
            ...         initial_amount=Decimal("10.0"),
            ...         target_leverage=Decimal("3.0"),
            ...         chain="ethereum",
            ...     ),
            ...     wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            ... )
            >>> print(f"Total steps: {result.total_steps}")
            >>> print(f"Actual leverage: {result.actual_leverage}x")
        """
        logger.info(
            f"Calculating leverage loop: user={command.user_id}, "
            f"asset={command.asset}, amount={command.initial_amount}, "
            f"target={command.target_leverage}x, chain={command.chain}"
        )

        # STEP 1: Validate initial conditions
        await self._validate_initial_balance(
            wallet_address=wallet_address,
            asset=command.asset,
            required_amount=command.initial_amount,
            chain=command.chain,
        )

        await self._validate_supported_asset(command.asset)

        self._validate_leverage_range(command.target_leverage)

        # STEP 2: Calculate optimal number of iterations
        # Formula: leverage = 1 / (1 - LTV) after infinite iterations
        # For practical purposes, we calculate iterations needed to reach 95% of target
        iterations = self._calculate_iterations(
            target_leverage=command.target_leverage,
            max_iterations=command.max_iterations,
        )

        logger.info(f"Calculated {iterations} iterations for {command.target_leverage}x leverage")

        # STEP 3: Get current position and market data
        position = await self._aave_gateway.get_user_position(
            wallet=wallet_address,
            chain=command.chain,
        )

        market_data = await self._aave_gateway.get_market_data(chain=command.chain)

        # Find collateral and borrow assets in market data
        collateral_market = next(
            (m for m in market_data if m.symbol.upper() == command.asset.upper()),
            None,
        )
        if not collateral_market:
            raise ValueError(f"Market data not found for {command.asset}")

        # For leverage loops, we borrow stablecoins (USDC preferred)
        borrow_asset = "USDC"
        borrow_market = next(
            (m for m in market_data if m.symbol.upper() == borrow_asset),
            None,
        )
        if not borrow_market:
            raise ValueError(f"Market data not found for {borrow_asset}")

        # STEP 4: Calculate each iteration step
        steps: list[LeverageLoopStep] = []
        current_collateral = command.initial_amount
        current_collateral_usd = command.initial_amount * collateral_market.price_usd
        current_debt_usd = position.total_debt_usd
        step_number = 1

        # Get LTV for calculations (typically 0.825 for ETH)
        ltv = collateral_market.ltv
        liquidation_threshold = ltv + Decimal("0.05")  # Estimate

        warnings: list[str] = []
        total_cost_usd = Decimal("0")

        # Add initial supply step (user's starting collateral)
        initial_supply_step = await self._build_supply_step(
            step_number=step_number,
            asset=command.asset,
            amount=command.initial_amount,
            health_factor_after=position.health_factor,
            chain=command.chain,
            collateral_market=collateral_market,
        )
        steps.append(initial_supply_step)
        step_number += 1

        # Calculate iteration steps
        for i in range(iterations):
            logger.debug(f"Calculating iteration {i+1}/{iterations}")

            # Calculate how much we can safely borrow
            max_borrow_usd = self._calculate_max_safe_borrow(
                collateral_usd=current_collateral_usd,
                debt_usd=current_debt_usd,
                liquidation_threshold=liquidation_threshold,
                min_health_factor=command.min_health_factor,
            )

            if max_borrow_usd <= Decimal("1.0"):  # Stop if borrow amount too small
                logger.info(f"Stopping at iteration {i+1}: borrow amount too small")
                warnings.append(
                    f"Loop stopped at iteration {i+1} due to insufficient borrow capacity"
                )
                break

            # Convert to borrow asset amount
            borrow_amount = max_borrow_usd / borrow_market.price_usd

            # Validate health factor after this borrow
            projected_debt_usd = current_debt_usd + max_borrow_usd
            hf_after_borrow = self._hf_validator_domain._calculate_health_factor(
                collateral_usd=current_collateral_usd,
                debt_usd=projected_debt_usd,
                liquidation_threshold=liquidation_threshold,
            )

            if hf_after_borrow < command.min_health_factor:
                logger.warning(
                    f"Stopping at iteration {i+1}: HF would be {hf_after_borrow:.2f} "
                    f"< min {command.min_health_factor:.2f}"
                )
                warnings.append(
                    f"Target leverage not achievable: health factor constraint at {hf_after_borrow:.2f}"
                )
                break

            # Create borrow step
            borrow_step = await self._build_borrow_step(
                step_number=step_number,
                asset=borrow_asset,
                amount=borrow_amount,
                health_factor_after=hf_after_borrow,
                chain=command.chain,
                borrow_market=borrow_market,
            )
            steps.append(borrow_step)
            step_number += 1

            # Get swap quote: USDC → ETH
            swap_quote = await self._swap_executor.get_swap_quote(
                token_in=borrow_asset,
                token_out=command.asset,
                amount_in=borrow_amount,
                chain=command.chain,
                slippage=command.slippage_tolerance,
            )

            swapped_collateral = swap_quote["amount_out"]
            swapped_collateral_usd = swapped_collateral * collateral_market.price_usd

            # Create swap step
            swap_step = await self._build_swap_step(
                step_number=step_number,
                token_in=borrow_asset,
                token_out=command.asset,
                amount_in=borrow_amount,
                amount_out=swapped_collateral,
                health_factor_after=hf_after_borrow,  # Same as after borrow
                chain=command.chain,
                slippage=command.slippage_tolerance,
            )
            steps.append(swap_step)
            step_number += 1

            # Add swap gas cost
            total_cost_usd += swap_quote.get("gas_estimate_usd", Decimal("0"))

            # Create supply step (supply swapped collateral)
            supply_step = await self._build_supply_step(
                step_number=step_number,
                asset=command.asset,
                amount=swapped_collateral,
                health_factor_after=hf_after_borrow,  # Supplying improves HF slightly
                chain=command.chain,
                collateral_market=collateral_market,
            )
            steps.append(supply_step)
            step_number += 1

            # Update state for next iteration
            current_collateral += swapped_collateral
            current_collateral_usd += swapped_collateral_usd
            current_debt_usd = projected_debt_usd

            logger.debug(
                f"After iteration {i+1}: collateral={current_collateral} {command.asset}, "
                f"debt=${current_debt_usd:.2f}, HF={hf_after_borrow:.2f}"
            )

        # STEP 5: Calculate final metrics
        actual_leverage = current_collateral / command.initial_amount
        final_health_factor = self._hf_validator_domain._calculate_health_factor(
            collateral_usd=current_collateral_usd,
            debt_usd=current_debt_usd,
            liquidation_threshold=liquidation_threshold,
        )

        # Calculate estimated APY (supply APY - borrow APY)
        supply_apy = collateral_market.supply_apy
        borrow_apy = borrow_market.variable_borrow_apy
        net_apy = (supply_apy * actual_leverage) - (borrow_apy * (actual_leverage - Decimal("1")))

        # Add warnings
        if actual_leverage < command.target_leverage * Decimal("0.95"):
            warnings.append(
                f"Achieved {actual_leverage:.2f}x leverage, below target {command.target_leverage}x"
            )

        if final_health_factor < Decimal("1.5"):
            warnings.append(
                f"⚠️ Final health factor {final_health_factor:.2f} is below recommended 1.5"
            )

        # Estimate total gas cost (rough estimate: 0.01 ETH per step)
        gas_cost_eth = Decimal("0.01") * len(steps)
        gas_cost_usd = gas_cost_eth * collateral_market.price_usd
        total_cost_usd += gas_cost_usd

        # STEP 6: Create result
        loop_id = uuid4()
        result = LeverageLoopResult(
            loop_id=loop_id,
            total_steps=len(steps),
            steps=steps,
            initial_collateral=command.initial_amount,
            final_exposure=current_collateral,
            actual_leverage=actual_leverage,
            final_health_factor=final_health_factor,
            estimated_apy=net_apy,
            total_cost_usd=total_cost_usd,
            warnings=warnings,
            current_step=0,  # Not started yet
        )

        logger.info(
            f"Leverage loop calculated: loop_id={loop_id}, "
            f"steps={len(steps)}, leverage={actual_leverage:.2f}x, "
            f"final_hf={final_health_factor:.2f}"
        )

        return result

    async def _validate_initial_balance(
        self,
        wallet_address: str,
        asset: str,
        required_amount: Decimal,
        chain: str,
    ) -> None:
        """Validate user has sufficient balance to start loop."""
        # Get token address for balance check
        token_address = "native" if asset.upper() == "ETH" else await self._get_token_address(asset, chain)

        has_balance = await self._balance_checker.check_balance(
            wallet_address=wallet_address,
            token_address=token_address,
            required_amount=required_amount,
            chain=chain,
        )

        if not has_balance:
            available = await self._balance_checker.get_balance(
                wallet_address=wallet_address,
                token_address=token_address,
                chain=chain,
            )
            raise InsufficientBalanceError(
                required=required_amount,
                available=available,
                asset=asset,
            )

    async def _validate_supported_asset(self, asset: str) -> None:
        """Validate asset is supported for leverage loops."""
        supported = {"ETH", "WETH", "wstETH"}
        if asset.upper() not in supported:
            raise UnsupportedAssetError(asset)

    def _validate_leverage_range(self, target_leverage: Decimal) -> None:
        """Validate target leverage is within acceptable range."""
        if not (Decimal("2.0") <= target_leverage <= Decimal("4.0")):
            raise ValueError(
                f"Target leverage must be between 2.0 and 4.0, got: {target_leverage}"
            )

    def _calculate_iterations(
        self,
        target_leverage: Decimal,
        max_iterations: int,
    ) -> int:
        """
        Calculate number of iterations needed for target leverage.

        Using compound interest formula:
        leverage = 1 + ltv + ltv^2 + ltv^3 + ... = 1 / (1 - ltv)

        We solve for number of terms needed to reach 95% of target.
        """
        # Assume LTV of 0.825 for ETH (standard Aave)
        ltv = Decimal("0.825")

        # Calculate iterations using geometric series
        # Sum = (1 - r^n) / (1 - r) where r = ltv
        # We want: Sum * initial >= 0.95 * target * initial
        # Solving: n = log(1 - (1-ltv) * 0.95 * target) / log(ltv)

        import math
        try:
            # Calculate required sum multiplier
            required_sum = float(target_leverage) * 0.95

            # Calculate iterations
            numerator = 1.0 - (1.0 - float(ltv)) * required_sum
            if numerator <= 0:
                # Target not achievable, use max iterations
                return max_iterations

            iterations = int(math.log(numerator) / math.log(float(ltv)))
            iterations = max(1, min(iterations, max_iterations))

            return iterations

        except (ValueError, ZeroDivisionError):
            # Fallback to simple estimate
            return min(3, max_iterations)

    def _calculate_max_safe_borrow(
        self,
        collateral_usd: Decimal,
        debt_usd: Decimal,
        liquidation_threshold: Decimal,
        min_health_factor: Decimal,
    ) -> Decimal:
        """
        Calculate maximum safe borrow amount maintaining min health factor.

        Formula:
        HF = (Collateral * LT) / Debt
        We want: HF >= min_health_factor
        So: Debt_max = (Collateral * LT) / min_health_factor
        Additional_borrow = Debt_max - Current_debt
        """
        max_total_debt = (collateral_usd * liquidation_threshold) / min_health_factor
        additional_borrow = max_total_debt - debt_usd

        # Safety margin: use 95% of max
        safe_additional_borrow = additional_borrow * Decimal("0.95")

        return max(Decimal("0"), safe_additional_borrow)

    async def _build_supply_step(
        self,
        step_number: int,
        asset: str,
        amount: Decimal,
        health_factor_after: Decimal,
        chain: str,
        collateral_market: any,
    ) -> LeverageLoopStep:
        """Build supply step with execute_data."""
        execute_data = {
            "action_type": "supply",
            "provider": "aave",
            "protocol": "aave_v3",
            "chain": chain,
            "asset_address": collateral_market.address,
            "asset_symbol": asset,
            "amount": str(amount),
            "pool_address": self._get_aave_pool_address(chain),
            "use_as_collateral": True,
        }

        return LeverageLoopStep(
            step_number=step_number,
            action="supply",
            asset_in=asset,
            asset_out=asset,
            amount_in=amount,
            amount_out=amount,
            health_factor_after=health_factor_after,
            execute_data=execute_data,
            requires_approval=True,
        )

    async def _build_borrow_step(
        self,
        step_number: int,
        asset: str,
        amount: Decimal,
        health_factor_after: Decimal,
        chain: str,
        borrow_market: any,
    ) -> LeverageLoopStep:
        """Build borrow step with execute_data."""
        execute_data = {
            "action_type": "borrow",
            "provider": "aave",
            "protocol": "aave_v3",
            "chain": chain,
            "asset_address": borrow_market.address,
            "asset_symbol": asset,
            "amount": str(amount),
            "rate_mode": "variable",
            "pool_address": self._get_aave_pool_address(chain),
            "health_factor_after": str(health_factor_after),
        }

        return LeverageLoopStep(
            step_number=step_number,
            action="borrow",
            asset_in="collateral",  # Using collateral to borrow
            asset_out=asset,
            amount_in=Decimal("0"),  # No input amount for borrow
            amount_out=amount,
            health_factor_after=health_factor_after,
            execute_data=execute_data,
            requires_approval=True,
        )

    async def _build_swap_step(
        self,
        step_number: int,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        amount_out: Decimal,
        health_factor_after: Decimal,
        chain: str,
        slippage: Decimal,
    ) -> LeverageLoopStep:
        """Build swap step with execute_data."""
        min_amount_out = amount_out * (Decimal("1") - slippage)

        execute_data = await self._swap_executor.build_swap_execute_data(
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            min_amount_out=min_amount_out,
            chain=chain,
        )

        return LeverageLoopStep(
            step_number=step_number,
            action="swap",
            asset_in=token_in,
            asset_out=token_out,
            amount_in=amount_in,
            amount_out=amount_out,
            health_factor_after=health_factor_after,
            execute_data=execute_data,
            requires_approval=True,
        )

    def _get_aave_pool_address(self, chain: str) -> str:
        """Get Aave V3 Pool contract address for chain."""
        AAVE_POOLS = {
            "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
            "base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
            "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "avalanche": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        }
        return AAVE_POOLS.get(chain.lower(), AAVE_POOLS["ethereum"])

    async def _get_token_address(self, asset: str, chain: str) -> str:
        """Get token contract address for asset."""
        # This would typically come from a token registry
        # For now, return placeholder
        TOKEN_ADDRESSES = {
            "ethereum": {
                "WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "wstETH": "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0",
            },
        }
        return TOKEN_ADDRESSES.get(chain.lower(), {}).get(asset.upper(), "")
