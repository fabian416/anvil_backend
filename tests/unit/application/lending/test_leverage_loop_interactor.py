"""
Unit tests for LeverageLoopInteractor.

Tests leverage loop calculation, health factor validation, and multi-step generation.
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, MagicMock

from app.application.lending.commands.leverage_loop_command import (
    LeverageLoopCommand,
    LeverageLoopResult,
    LeverageLoopStep,
)
from app.application.lending.interactors.leverage_loop_interactor import (
    LeverageLoopInteractor,
    InsufficientBalanceError,
    UnsupportedAssetError,
)
from app.domain.entities.lending.aave_position import AavePosition
from app.domain.value_objects.lending.health_factor_result import HealthFactorResult, HealthFactorLevel


@pytest.fixture
def mock_hf_validator_service():
    """Mock health factor validator service."""
    mock = AsyncMock()
    mock.validate_borrow = AsyncMock(return_value=HealthFactorResult(
        current_hf=Decimal("5.0"),
        projected_hf=Decimal("2.5"),
        level=HealthFactorLevel.SAFE,
        is_safe=True,
        warning_message="✅ SAFE",
        liquidation_price=None,
        max_safe_borrow_usd=Decimal("10000"),
        collateral_usd=Decimal("15000"),
        current_debt_usd=Decimal("0"),
        projected_debt_usd=Decimal("5000"),
    ))
    return mock


@pytest.fixture
def mock_hf_validator_domain():
    """Mock domain health factor validator."""
    mock = Mock()
    mock._calculate_health_factor = Mock(side_effect=lambda collateral_usd, debt_usd, liquidation_threshold:
        Decimal("inf") if debt_usd == 0 else (collateral_usd * liquidation_threshold) / debt_usd
    )
    mock._determine_level = Mock(return_value=HealthFactorLevel.SAFE)
    mock._calculate_max_safe_borrow = Mock(return_value=Decimal("5000"))
    return mock


@pytest.fixture
def mock_balance_checker():
    """Mock balance checker."""
    mock = AsyncMock()
    mock.check_balance = AsyncMock(return_value=True)
    mock.get_balance = AsyncMock(return_value=Decimal("10.0"))
    return mock


@pytest.fixture
def mock_swap_executor():
    """Mock swap executor."""
    mock = AsyncMock()
    mock.get_swap_quote = AsyncMock(return_value={
        "amount_out": Decimal("0.5"),
        "rate": Decimal("0.0005"),
        "price_impact": Decimal("0.1"),
        "min_amount_out": Decimal("0.495"),
        "gas_estimate": Decimal("0.001"),
        "gas_estimate_usd": Decimal("3.0"),
        "route": ["USDC", "ETH"],
    })
    mock.build_swap_execute_data = AsyncMock(return_value={
        "action_type": "swap",
        "provider": "1inch",
        "from_token": "USDC",
        "to_token": "ETH",
    })
    return mock


@pytest.fixture
def mock_aave_gateway():
    """Mock Aave gateway."""
    mock = AsyncMock()

    # Mock user position
    position = Mock(spec=AavePosition)
    position.total_collateral_usd = Decimal("0")
    position.total_debt_usd = Decimal("0")
    position.health_factor = Decimal("inf")
    mock.get_user_position = AsyncMock(return_value=position)

    # Mock market data
    eth_market = Mock()
    eth_market.symbol = "ETH"
    eth_market.address = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
    eth_market.price_usd = Decimal("3000")
    eth_market.ltv = Decimal("0.825")
    eth_market.supply_apy = Decimal("0.03")

    usdc_market = Mock()
    usdc_market.symbol = "USDC"
    usdc_market.address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    usdc_market.price_usd = Decimal("1.0")
    usdc_market.variable_borrow_apy = Decimal("0.05")

    mock.get_market_data = AsyncMock(return_value=[eth_market, usdc_market])

    return mock


@pytest.fixture
def mock_repository():
    """Mock lending repository."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def interactor(
    mock_hf_validator_service,
    mock_hf_validator_domain,
    mock_balance_checker,
    mock_swap_executor,
    mock_aave_gateway,
    mock_repository,
):
    """Create leverage loop interactor with mocked dependencies."""
    return LeverageLoopInteractor(
        hf_validator_service=mock_hf_validator_service,
        hf_validator_domain=mock_hf_validator_domain,
        balance_checker=mock_balance_checker,
        swap_executor=mock_swap_executor,
        aave_gateway=mock_aave_gateway,
        repository=mock_repository,
    )


class TestLeverageLoopCommand:
    """Test leverage loop command validation."""

    def test_valid_command(self):
        """Test creating valid leverage loop command."""
        user_id = uuid4()

        command = LeverageLoopCommand(
            user_id=user_id,
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("3.0"),
            protocol="aave",
            chain="ethereum",
        )

        assert command.user_id == user_id
        assert command.asset == "ETH"
        assert command.target_leverage == Decimal("3.0")

    def test_invalid_amount(self):
        """Test command with invalid amount."""
        with pytest.raises(ValueError, match="must be positive"):
            LeverageLoopCommand(
                user_id=uuid4(),
                asset="ETH",
                initial_amount=Decimal("0"),
                target_leverage=Decimal("3.0"),
            )

    def test_unsupported_asset(self):
        """Test command with unsupported asset."""
        with pytest.raises(ValueError, match="not supported"):
            LeverageLoopCommand(
                user_id=uuid4(),
                asset="USDC",  # Not supported for leverage
                initial_amount=Decimal("10.0"),
                target_leverage=Decimal("3.0"),
            )

    def test_invalid_leverage_range(self):
        """Test command with invalid leverage."""
        # Too low
        with pytest.raises(ValueError, match="between 2.0 and 4.0"):
            LeverageLoopCommand(
                user_id=uuid4(),
                asset="ETH",
                initial_amount=Decimal("10.0"),
                target_leverage=Decimal("1.5"),
            )

        # Too high
        with pytest.raises(ValueError, match="between 2.0 and 4.0"):
            LeverageLoopCommand(
                user_id=uuid4(),
                asset="ETH",
                initial_amount=Decimal("10.0"),
                target_leverage=Decimal("5.0"),
            )

    def test_invalid_protocol(self):
        """Test command with invalid protocol."""
        with pytest.raises(ValueError, match="Only Aave"):
            LeverageLoopCommand(
                user_id=uuid4(),
                asset="ETH",
                initial_amount=Decimal("10.0"),
                target_leverage=Decimal("3.0"),
                protocol="morpho",  # Morpho doesn't support borrowing
            )


class TestLeverageLoopInteractor:
    """Test leverage loop interactor."""

    @pytest.mark.asyncio
    async def test_calculate_2x_leverage(self, interactor):
        """Test calculating 2x leverage loop."""
        command = LeverageLoopCommand(
            user_id=uuid4(),
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("2.0"),
            chain="ethereum",
        )

        result = await interactor.calculate_loop_steps(
            command=command,
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        )

        # Should have steps: initial supply + iterations (supply, borrow, swap each)
        assert result.total_steps > 0
        assert result.initial_collateral == Decimal("10.0")
        # actual_leverage achieved depends on mock data - just verify it's > 1.0
        assert result.actual_leverage > Decimal("1.0")
        assert len(result.steps) == result.total_steps

        # Each step should require approval
        for step in result.steps:
            assert step.requires_approval is True

    @pytest.mark.asyncio
    async def test_calculate_3x_leverage(self, interactor):
        """Test calculating 3x leverage loop."""
        command = LeverageLoopCommand(
            user_id=uuid4(),
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("3.0"),
            chain="ethereum",
        )

        result = await interactor.calculate_loop_steps(
            command=command,
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        )

        assert result.total_steps > 0
        # More aggressive leverage should require more steps
        assert result.total_steps >= 4  # At least 2 iterations

    @pytest.mark.asyncio
    async def test_insufficient_balance(self, interactor, mock_balance_checker):
        """Test handling insufficient balance."""
        # Mock insufficient balance
        mock_balance_checker.check_balance.return_value = False
        mock_balance_checker.get_balance.return_value = Decimal("5.0")

        command = LeverageLoopCommand(
            user_id=uuid4(),
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("3.0"),
        )

        with pytest.raises(InsufficientBalanceError) as exc_info:
            await interactor.calculate_loop_steps(
                command=command,
                wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            )

        assert exc_info.value.required == Decimal("10.0")
        assert exc_info.value.available == Decimal("5.0")
        assert exc_info.value.asset == "ETH"

    @pytest.mark.asyncio
    async def test_health_factor_validation(self, interactor):
        """Test health factor validation during loop calculation."""
        command = LeverageLoopCommand(
            user_id=uuid4(),
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("3.0"),
            min_health_factor=Decimal("1.5"),  # Strict safety
        )

        result = await interactor.calculate_loop_steps(
            command=command,
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        )

        # All borrow steps should maintain health factor above minimum
        for step in result.steps:
            if step.action == "borrow":
                assert step.health_factor_after >= command.min_health_factor

    @pytest.mark.asyncio
    async def test_step_types(self, interactor):
        """Test that steps have correct action types."""
        command = LeverageLoopCommand(
            user_id=uuid4(),
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("3.0"),
        )

        result = await interactor.calculate_loop_steps(
            command=command,
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        )

        # Should have supply, borrow, and swap steps
        actions = [step.action for step in result.steps]
        assert "supply" in actions
        assert "borrow" in actions
        assert "swap" in actions

    @pytest.mark.asyncio
    async def test_execute_data_generated(self, interactor):
        """Test that execute_data is generated for each step."""
        command = LeverageLoopCommand(
            user_id=uuid4(),
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("3.0"),
        )

        result = await interactor.calculate_loop_steps(
            command=command,
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        )

        # Every step should have execute_data
        for step in result.steps:
            assert step.execute_data is not None
            assert "action_type" in step.execute_data

    @pytest.mark.asyncio
    async def test_warnings_generation(self, interactor):
        """Test that warnings are generated when appropriate."""
        command = LeverageLoopCommand(
            user_id=uuid4(),
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("4.0"),  # Very aggressive
        )

        result = await interactor.calculate_loop_steps(
            command=command,
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        )

        # May have warnings about not achieving target or low health factor
        # (depending on market conditions in mocks)
        assert isinstance(result.warnings, list)

    @pytest.mark.asyncio
    async def test_resumable_state(self, interactor):
        """Test that result has resumable state tracking."""
        command = LeverageLoopCommand(
            user_id=uuid4(),
            asset="ETH",
            initial_amount=Decimal("10.0"),
            target_leverage=Decimal("3.0"),
        )

        result = await interactor.calculate_loop_steps(
            command=command,
            wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        )

        # Should start at step 0 (not started)
        assert result.current_step == 0
        assert result.is_complete is False
        assert result.next_step is not None
        assert result.next_step == result.steps[0]


class TestCalculationHelpers:
    """Test helper calculation methods."""

    def test_iterations_calculation(self, interactor):
        """Test iteration calculation for different leverage targets."""
        # 2x leverage should need fewer iterations
        iterations_2x = interactor._calculate_iterations(
            target_leverage=Decimal("2.0"),
            max_iterations=4,
        )

        # 4x leverage should need more iterations
        iterations_4x = interactor._calculate_iterations(
            target_leverage=Decimal("4.0"),
            max_iterations=4,
        )

        assert iterations_2x < iterations_4x
        assert iterations_2x >= 1
        assert iterations_4x <= 4  # Should respect max

    def test_max_safe_borrow_calculation(self, interactor):
        """Test max safe borrow calculation."""
        max_borrow = interactor._calculate_max_safe_borrow(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("0"),
            liquidation_threshold=Decimal("0.825"),
            min_health_factor=Decimal("1.5"),
        )

        # Should return positive borrow amount
        assert max_borrow > 0

        # Should be less than collateral value
        assert max_borrow < Decimal("10000")

        # With existing debt, should return less
        max_borrow_with_debt = interactor._calculate_max_safe_borrow(
            collateral_usd=Decimal("10000"),
            debt_usd=Decimal("2000"),
            liquidation_threshold=Decimal("0.825"),
            min_health_factor=Decimal("1.5"),
        )

        assert max_borrow_with_debt < max_borrow
