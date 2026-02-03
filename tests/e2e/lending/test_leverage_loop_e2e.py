"""
End-to-End Tests for Leverage Loop Workflow.

Tests complete 3x leverage loop execution with multi-step approval.
Validates loop calculation, step execution, and safety interruption.
"""

import pytest
from decimal import Decimal
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from app.application.lending.interactors.leverage_loop_interactor import (
    LeverageLoopInteractor,
    InsufficientBalanceError,
    UnsupportedAssetError,
)
from app.application.lending.commands.leverage_loop_command import (
    LeverageLoopCommand,
    LeverageLoopResult,
    LeverageLoopStep,
)


@pytest.mark.e2e
@pytest.mark.defi
class TestLeverageLoopE2E:
    """End-to-end tests for leverage loop workflow."""

    @pytest.mark.asyncio
    async def test_successful_3x_leverage_loop_calculation(
        self,
        mock_hf_validator_service,
        mock_hf_validator_domain,
        mock_balance_checker,
        mock_swap_executor,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """
        Test successful 3x leverage loop calculation.

        Scenario: User wants 3x leverage on 10 ETH
        Expected: 9 steps calculated (supply → borrow → swap) × 3 iterations

        Flow:
        1. User: "loop 10 ETH for 3x"
        2. Calculate optimal iterations
        3. For each iteration: supply → borrow → swap
        4. Return complete execution plan
        5. NO AUTOMATIC EXECUTION - each step needs approval
        """
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        command = LeverageLoopCommand(
            user_id=user_id,
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("3.0"),
            chain="ethereum",
            min_health_factor=Decimal("1.5"),
            slippage_tolerance=Decimal("0.005"),  # 0.5%
            max_iterations=5,
        )

        # Mock balance check - user has 10 ETH
        mock_balance_checker.check_balance.return_value = True
        mock_balance_checker.get_balance.return_value = Decimal("10.0")

        # Mock Aave position data
        mock_position = MagicMock(
            health_factor=Decimal("inf"),  # No existing debt
            total_collateral_usd=Decimal("0"),
            total_debt_usd=Decimal("0"),
            max_ltv=Decimal("0.825"),
            supplies=[],
            borrows=[],
        )
        mock_aave_gateway.get_user_position.return_value = mock_position

        # Mock Aave market data
        mock_market_data = [
            MagicMock(
                symbol="ETH",
                supply_apy=Decimal("3.5"),
                ltv=Decimal("0.825"),
                price_usd=Decimal("2000.0"),
                address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            ),
            MagicMock(
                symbol="USDC",
                variable_borrow_apy=Decimal("5.0"),
                price_usd=Decimal("1.0"),
                address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            ),
        ]
        mock_aave_gateway.get_market_data.return_value = mock_market_data

        # Mock swap quotes
        async def mock_swap_quote(token_in, token_out, amount_in, chain, slippage):
            # USDC → ETH conversion
            eth_price = 2000.0
            amount_out = float(amount_in) / eth_price * 0.998  # 0.2% swap fee
            return {
                "amount_out": Decimal(str(amount_out)),
                "gas_estimate_usd": Decimal("10.0"),
            }

        mock_swap_executor.get_swap_quote = AsyncMock(side_effect=mock_swap_quote)
        mock_swap_executor.build_swap_execute_data = AsyncMock(
            return_value={"action": "swap", "dex": "1inch"}
        )

        # Mock domain HF calculations
        def mock_calc_hf(collateral_usd, debt_usd, liquidation_threshold):
            if debt_usd == 0:
                return Decimal("inf")
            return (collateral_usd * liquidation_threshold) / debt_usd

        mock_hf_validator_domain._calculate_health_factor = mock_calc_hf

        # Create interactor
        interactor = LeverageLoopInteractor(
            hf_validator_service=mock_hf_validator_service,
            hf_validator_domain=mock_hf_validator_domain,
            balance_checker=mock_balance_checker,
            swap_executor=mock_swap_executor,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT
        result = await interactor.calculate_loop_steps(
            command=command,
            wallet_address=wallet_address,
        )

        # ASSERT

        # 1. Balance was checked
        mock_balance_checker.check_balance.assert_called_once()

        # 2. Loop has multiple steps (supply + borrow + swap per iteration)
        assert result.total_steps > 3  # At least 1 iteration (3 steps minimum)
        assert result.total_steps % 3 == 1  # Initial supply + (supply+borrow+swap) × N

        # 3. Steps are in correct order
        steps = result.steps
        assert steps[0].action == "supply"  # Initial supply

        # Validate step pattern for iterations
        for i in range(1, len(steps), 3):
            if i + 2 < len(steps):
                assert steps[i].action == "borrow"
                assert steps[i + 1].action == "swap"
                assert steps[i + 2].action == "supply"

        # 4. Leverage achieved is close to target
        assert Decimal("2.8") <= result.actual_leverage <= Decimal("3.2")

        # 5. Final health factor is safe
        assert result.final_health_factor >= command.min_health_factor

        # 6. Each step has execute_data for Privy
        for step in steps:
            assert step.execute_data is not None
            assert "action_type" in step.execute_data or "action" in step.execute_data
            assert step.requires_approval is True

        # 7. Initial collateral matches command
        assert result.initial_collateral == Decimal("10.0")

        # 8. Final exposure > initial (leveraged)
        assert result.final_exposure > result.initial_collateral

        # 9. Cost estimation included
        assert result.total_cost_usd > 0

        # 10. Loop not yet started
        assert result.current_step == 0

    @pytest.mark.asyncio
    async def test_leverage_loop_interrupted_by_hf_drop(
        self,
        mock_hf_validator_service,
        mock_hf_validator_domain,
        mock_balance_checker,
        mock_swap_executor,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """
        Test leverage loop calculation stops when HF drops below threshold.

        Scenario:
        - Start 3x leverage loop
        - During iteration 2, market conditions change
        - Projected HF drops below min_health_factor
        - Loop calculation stops early with warning
        """
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        command = LeverageLoopCommand(
            user_id=user_id,
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("3.0"),
            chain="ethereum",
            min_health_factor=Decimal("1.8"),  # Higher threshold
            slippage_tolerance=Decimal("0.005"),
            max_iterations=5,
        )

        # Mock balance check
        mock_balance_checker.check_balance.return_value = True

        # Mock position
        mock_position = MagicMock(
            health_factor=Decimal("inf"),
            total_collateral_usd=Decimal("0"),
            total_debt_usd=Decimal("0"),
            max_ltv=Decimal("0.825"),
            supplies=[],
            borrows=[],
        )
        mock_aave_gateway.get_user_position.return_value = mock_position

        # Mock market data
        mock_market_data = [
            MagicMock(
                symbol="ETH",
                supply_apy=Decimal("3.5"),
                ltv=Decimal("0.825"),
                price_usd=Decimal("2000.0"),
                address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            ),
            MagicMock(
                symbol="USDC",
                variable_borrow_apy=Decimal("5.0"),
                price_usd=Decimal("1.0"),
                address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            ),
        ]
        mock_aave_gateway.get_market_data.return_value = mock_market_data

        # Mock swap quotes
        mock_swap_executor.get_swap_quote = AsyncMock(
            return_value={
                "amount_out": Decimal("4.0"),
                "gas_estimate_usd": Decimal("10.0"),
            }
        )
        mock_swap_executor.build_swap_execute_data = AsyncMock(
            return_value={"action": "swap"}
        )

        # Mock domain HF calculations that drop below threshold on iteration 2
        iteration_count = {"count": 0}

        def mock_calc_hf(collateral_usd, debt_usd, liquidation_threshold):
            if debt_usd == 0:
                return Decimal("inf")

            hf = (collateral_usd * liquidation_threshold) / debt_usd

            # Simulate HF drop on 2nd iteration
            iteration_count["count"] += 1
            if iteration_count["count"] > 5:  # After some calculations
                return Decimal("1.6")  # Below 1.8 threshold

            return hf

        mock_hf_validator_domain._calculate_health_factor = mock_calc_hf

        interactor = LeverageLoopInteractor(
            hf_validator_service=mock_hf_validator_service,
            hf_validator_domain=mock_hf_validator_domain,
            balance_checker=mock_balance_checker,
            swap_executor=mock_swap_executor,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT
        result = await interactor.calculate_loop_steps(
            command=command,
            wallet_address=wallet_address,
        )

        # ASSERT

        # 1. Loop stopped early
        assert result.total_steps < 10  # Didn't complete all iterations

        # 2. Warning about early stop
        assert len(result.warnings) > 0
        assert any("health factor" in w.lower() for w in result.warnings)

        # 3. Achieved leverage below target
        assert result.actual_leverage < command.target_leverage

    @pytest.mark.asyncio
    async def test_leverage_loop_blocked_insufficient_balance(
        self,
        mock_hf_validator_service,
        mock_hf_validator_domain,
        mock_balance_checker,
        mock_swap_executor,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """Test leverage loop blocked when user has insufficient initial balance."""
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        command = LeverageLoopCommand(
            user_id=user_id,
            asset="ETH",
            initial_amount=Decimal("10.0"),  # Wants to use 10 ETH
            target_leverage=Decimal("3.0"),
            chain="ethereum",
            min_health_factor=Decimal("1.5"),
            slippage_tolerance=Decimal("0.005"),
            max_iterations=5,
        )

        # Mock insufficient balance
        mock_balance_checker.check_balance.return_value = False
        mock_balance_checker.get_balance.return_value = Decimal("5.0")  # Only has 5 ETH

        interactor = LeverageLoopInteractor(
            hf_validator_service=mock_hf_validator_service,
            hf_validator_domain=mock_hf_validator_domain,
            balance_checker=mock_balance_checker,
            swap_executor=mock_swap_executor,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT & ASSERT
        with pytest.raises(InsufficientBalanceError) as exc_info:
            await interactor.calculate_loop_steps(
                command=command,
                wallet_address=wallet_address,
            )

        assert exc_info.value.asset == "ETH"
        assert exc_info.value.required == Decimal("10.0")
        assert exc_info.value.available == Decimal("5.0")

    @pytest.mark.asyncio
    async def test_leverage_loop_blocked_unsupported_asset(
        self,
        mock_hf_validator_service,
        mock_hf_validator_domain,
        mock_balance_checker,
        mock_swap_executor,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """Test leverage loop blocked for unsupported assets."""
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        command = LeverageLoopCommand(
            user_id=user_id,
            asset="USDC",  # Stablecoins not supported for leverage loops
            initial_amount=Decimal("10000.0"),
            target_leverage=Decimal("3.0"),
            chain="ethereum",
            min_health_factor=Decimal("1.5"),
            slippage_tolerance=Decimal("0.005"),
            max_iterations=5,
        )

        # Mock balance check passes
        mock_balance_checker.check_balance.return_value = True

        interactor = LeverageLoopInteractor(
            hf_validator_service=mock_hf_validator_service,
            hf_validator_domain=mock_hf_validator_domain,
            balance_checker=mock_balance_checker,
            swap_executor=mock_swap_executor,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT & ASSERT
        with pytest.raises(UnsupportedAssetError) as exc_info:
            await interactor.calculate_loop_steps(
                command=command,
                wallet_address=wallet_address,
            )

        assert exc_info.value.asset == "USDC"
        assert "ETH" in str(exc_info.value) or "WETH" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_leverage_loop_invalid_leverage_range(
        self,
        mock_hf_validator_service,
        mock_hf_validator_domain,
        mock_balance_checker,
        mock_swap_executor,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """Test leverage loop rejects leverage outside valid range (2x-4x)."""
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        # Test leverage too low
        command_too_low = LeverageLoopCommand(
            user_id=user_id,
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("1.5"),  # Below 2.0 minimum
            chain="ethereum",
            min_health_factor=Decimal("1.5"),
            slippage_tolerance=Decimal("0.005"),
            max_iterations=5,
        )

        mock_balance_checker.check_balance.return_value = True

        interactor = LeverageLoopInteractor(
            hf_validator_service=mock_hf_validator_service,
            hf_validator_domain=mock_hf_validator_domain,
            balance_checker=mock_balance_checker,
            swap_executor=mock_swap_executor,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT & ASSERT: Too low
        with pytest.raises(ValueError) as exc_info:
            await interactor.calculate_loop_steps(
                command=command_too_low,
                wallet_address=wallet_address,
            )

        assert "between 2.0 and 4.0" in str(exc_info.value)

        # Test leverage too high
        command_too_high = LeverageLoopCommand(
            user_id=user_id,
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("5.0"),  # Above 4.0 maximum
            chain="ethereum",
            min_health_factor=Decimal("1.5"),
            slippage_tolerance=Decimal("0.005"),
            max_iterations=5,
        )

        with pytest.raises(ValueError) as exc_info:
            await interactor.calculate_loop_steps(
                command=command_too_high,
                wallet_address=wallet_address,
            )

        assert "between 2.0 and 4.0" in str(exc_info.value)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def test_user_context():
    """Provide test user context."""
    return {
        "user_id": uuid4(),
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    }


@pytest.fixture
def mock_hf_validator_service():
    """Mock health factor validator service (application layer)."""
    mock = AsyncMock()
    mock.validate_borrow = AsyncMock()
    return mock


@pytest.fixture
def mock_hf_validator_domain():
    """Mock health factor validator (domain service)."""
    mock = MagicMock()
    mock._calculate_health_factor = MagicMock(return_value=Decimal("2.5"))
    mock._determine_level = MagicMock()
    return mock


@pytest.fixture
def mock_balance_checker():
    """Mock balance checker."""
    mock = AsyncMock()
    mock.check_balance = AsyncMock(return_value=True)
    mock.get_balance = AsyncMock(return_value=Decimal("100.0"))
    return mock


@pytest.fixture
def mock_swap_executor():
    """Mock swap executor."""
    mock = AsyncMock()
    mock.get_swap_quote = AsyncMock()
    mock.build_swap_execute_data = AsyncMock()
    return mock


@pytest.fixture
def mock_aave_gateway():
    """Mock Aave gateway."""
    mock = AsyncMock()
    mock.get_user_position = AsyncMock()
    mock.get_market_data = AsyncMock()
    return mock


@pytest.fixture
def mock_lending_repository():
    """Mock lending repository."""
    mock = AsyncMock()
    mock.save_loop_execution = AsyncMock()
    mock.get_loop_execution = AsyncMock()
    return mock
