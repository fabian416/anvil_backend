"""
End-to-End Tests for Borrow Workflow.

Tests complete borrow flow with health factor validation.
Critical: Validates that unsafe borrows are BLOCKED before approval UI.
"""

import pytest
from decimal import Decimal
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock

from app.application.lending.interactors.borrow_interactor import (
    BorrowInteractor,
    UnsafeBorrowError,
    InsufficientCollateralError,
)
from app.application.lending.commands.borrow_command import BorrowCommand
from app.domain.value_objects.lending.health_factor_result import (
    HealthFactorResult,
    HealthFactorLevel,
)


@pytest.mark.e2e
@pytest.mark.defi
class TestBorrowWorkflowE2E:
    """End-to-end tests for complete borrow workflow with safety validation."""

    @pytest.mark.asyncio
    async def test_successful_safe_borrow_complete_flow(
        self,
        mock_hf_validator,
        mock_balance_checker,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """
        Test complete successful borrow flow with SAFE health factor.

        Flow:
        1. User initiates borrow via LENDING_BORROW shortcut
        2. BorrowInteractor validates health factor (SAFE: HF > 2.0)
        3. Generate execute_data for Privy
        4. Save position to database
        5. Return result with health factor context
        """
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        command = BorrowCommand(
            user_id=user_id,
            protocol="aave",
            asset="USDC",
            amount=Decimal("2000.0"),
            chain="ethereum",
            rate_mode="variable",
            min_health_factor=Decimal("1.5"),
        )

        # Mock SAFE health factor validation
        safe_hf_result = HealthFactorResult(
            current_hf=Decimal("3.5"),
            projected_hf=Decimal("2.8"),
            level=HealthFactorLevel.SAFE,
            collateral_usd=Decimal("10000.0"),
            current_debt_usd=Decimal("1000.0"),
            projected_debt_usd=Decimal("3000.0"),
            max_safe_borrow_usd=Decimal("5000.0"),
            liquidation_price=Decimal("1200.0"),
            warning_message="SAFE - Your position is well-collateralized",
            emoji="✅",
            is_safe=True,
        )
        mock_hf_validator.validate_borrow.return_value = safe_hf_result

        # Mock Aave market data
        mock_market_data = [
            MagicMock(
                symbol="USDC",
                variable_borrow_apy=Decimal("6.5"),
                stable_borrow_apy=Decimal("7.5"),
                address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            )
        ]
        mock_aave_gateway.get_market_data.return_value = mock_market_data

        # Mock repository
        expected_position_id = uuid4()
        mock_lending_repository.save_borrow_position.return_value = expected_position_id

        # Create interactor
        interactor = BorrowInteractor(
            hf_validator=mock_hf_validator,
            balance_checker=mock_balance_checker,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT
        result = await interactor.execute(
            command=command,
            wallet_address=wallet_address,
        )

        # ASSERT

        # 1. Health factor was validated FIRST
        mock_hf_validator.validate_borrow.assert_called_once_with(
            wallet=wallet_address,
            borrow_asset="USDC",
            borrow_amount=Decimal("2000.0"),
            chain="ethereum",
        )

        # 2. Aave market data was fetched
        mock_aave_gateway.get_market_data.assert_called_once_with(chain="ethereum")

        # 3. Position was saved with health factor tracking
        mock_lending_repository.save_borrow_position.assert_called_once()
        call_args = mock_lending_repository.save_borrow_position.call_args[1]
        assert call_args["user_id"] == user_id
        assert call_args["protocol"] == "aave"
        assert call_args["asset"] == "USDC"
        assert call_args["amount"] == "2000.0"
        assert call_args["health_factor_before"] == "3.5"
        assert call_args["health_factor_after"] == "2.8"
        assert call_args["rate_mode"] == "variable"

        # 4. Result has execute_data
        assert result.position_id == expected_position_id
        assert result.status == "awaiting_signature"
        assert result.health_factor_current == Decimal("3.5")
        assert result.health_factor_projected == Decimal("2.8")
        assert result.risk_level == "SAFE"
        assert result.borrow_apy == Decimal("6.5")

        # 5. execute_data structure
        execute_data = result.execute_data
        assert execute_data["action_type"] == "borrow"
        assert execute_data["provider"] == "aave"
        assert execute_data["asset_symbol"] == "USDC"
        assert execute_data["amount"] == "2000.0"
        assert execute_data["rate_mode"] == "variable"
        assert execute_data["health_factor_before"] == "3.5"
        assert execute_data["health_factor_after"] == "2.8"

    @pytest.mark.asyncio
    async def test_borrow_BLOCKED_unsafe_health_factor(
        self,
        mock_hf_validator,
        mock_balance_checker,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """
        Test borrow is BLOCKED when projected HF < min_health_factor.

        CRITICAL: User should NEVER see approval UI for unsafe borrows.
        This prevents users from accidentally liquidating themselves.
        """
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        command = BorrowCommand(
            user_id=user_id,
            protocol="aave",
            asset="USDC",
            amount=Decimal("8000.0"),  # Too much to borrow
            chain="ethereum",
            rate_mode="variable",
            min_health_factor=Decimal("1.5"),  # Safety threshold
        )

        # Mock DANGER health factor (projected HF = 1.1 < 1.5)
        danger_hf_result = HealthFactorResult(
            current_hf=Decimal("2.0"),
            projected_hf=Decimal("1.1"),  # BELOW min_health_factor!
            level=HealthFactorLevel.DANGER,
            collateral_usd=Decimal("10000.0"),
            current_debt_usd=Decimal("2000.0"),
            projected_debt_usd=Decimal("10000.0"),
            max_safe_borrow_usd=Decimal("3000.0"),
            liquidation_price=Decimal("1800.0"),
            warning_message="DANGER - Health Factor 1.1. Very high liquidation risk!",
            emoji="🔶",
            is_safe=False,
        )
        mock_hf_validator.validate_borrow.return_value = danger_hf_result

        interactor = BorrowInteractor(
            hf_validator=mock_hf_validator,
            balance_checker=mock_balance_checker,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT & ASSERT: Should raise UnsafeBorrowError
        with pytest.raises(UnsafeBorrowError) as exc_info:
            await interactor.execute(command=command, wallet_address=wallet_address)

        # Verify exception contains health factor details
        assert exc_info.value.validation_result.projected_hf == Decimal("1.1")
        assert exc_info.value.validation_result.level == HealthFactorLevel.DANGER

        # CRITICAL: NO execute_data was generated
        mock_aave_gateway.get_market_data.assert_not_called()

        # CRITICAL: NO database write occurred
        mock_lending_repository.save_borrow_position.assert_not_called()

    @pytest.mark.asyncio
    async def test_borrow_BLOCKED_critical_health_factor(
        self,
        mock_hf_validator,
        mock_balance_checker,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """Test borrow blocked when HF would be CRITICAL (< 1.2)."""
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        command = BorrowCommand(
            user_id=user_id,
            protocol="aave",
            asset="USDC",
            amount=Decimal("9000.0"),
            chain="ethereum",
            rate_mode="variable",
            min_health_factor=Decimal("1.2"),
        )

        # Mock CRITICAL health factor (projected HF = 1.05)
        critical_hf_result = HealthFactorResult(
            current_hf=Decimal("1.8"),
            projected_hf=Decimal("1.05"),  # CRITICAL!
            level=HealthFactorLevel.CRITICAL,
            collateral_usd=Decimal("10000.0"),
            current_debt_usd=Decimal("3000.0"),
            projected_debt_usd=Decimal("12000.0"),
            max_safe_borrow_usd=Decimal("2000.0"),
            liquidation_price=Decimal("1950.0"),
            warning_message="CRITICAL - Immediate liquidation risk!",
            emoji="🔴",
            is_safe=False,
        )
        mock_hf_validator.validate_borrow.return_value = critical_hf_result

        interactor = BorrowInteractor(
            hf_validator=mock_hf_validator,
            balance_checker=mock_balance_checker,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT & ASSERT
        with pytest.raises(UnsafeBorrowError):
            await interactor.execute(command=command, wallet_address=wallet_address)

        # No execute_data or database write
        mock_aave_gateway.get_market_data.assert_not_called()
        mock_lending_repository.save_borrow_position.assert_not_called()

    @pytest.mark.asyncio
    async def test_borrow_caution_level_allowed_above_threshold(
        self,
        mock_hf_validator,
        mock_balance_checker,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """
        Test borrow ALLOWED when HF is CAUTION but above min threshold.

        CAUTION (1.5 < HF < 2.0) is allowed if HF >= min_health_factor.
        User gets warning but can proceed.
        """
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        command = BorrowCommand(
            user_id=user_id,
            protocol="aave",
            asset="USDC",
            amount=Decimal("4000.0"),
            chain="ethereum",
            rate_mode="variable",
            min_health_factor=Decimal("1.5"),  # User accepts CAUTION level
        )

        # Mock CAUTION health factor (projected HF = 1.7 >= 1.5)
        caution_hf_result = HealthFactorResult(
            current_hf=Decimal("2.5"),
            projected_hf=Decimal("1.7"),  # CAUTION but >= min_health_factor
            level=HealthFactorLevel.CAUTION,
            collateral_usd=Decimal("10000.0"),
            current_debt_usd=Decimal("1500.0"),
            projected_debt_usd=Decimal("5500.0"),
            max_safe_borrow_usd=Decimal("4500.0"),
            liquidation_price=Decimal("1600.0"),
            warning_message="CAUTION - Monitor your position closely",
            emoji="⚠️",
            is_safe=True,  # Safe enough given user's threshold
        )
        mock_hf_validator.validate_borrow.return_value = caution_hf_result

        # Mock Aave data
        mock_market_data = [
            MagicMock(
                symbol="USDC",
                variable_borrow_apy=Decimal("6.0"),
                address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            )
        ]
        mock_aave_gateway.get_market_data.return_value = mock_market_data

        expected_position_id = uuid4()
        mock_lending_repository.save_borrow_position.return_value = expected_position_id

        interactor = BorrowInteractor(
            hf_validator=mock_hf_validator,
            balance_checker=mock_balance_checker,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT
        result = await interactor.execute(
            command=command, wallet_address=wallet_address
        )

        # ASSERT: Borrow allowed but with warning
        assert result.status == "awaiting_signature"
        assert result.risk_level == "CAUTION"
        assert result.health_factor_projected == Decimal("1.7")
        assert "⚠️" in result.message or "CAUTION" in result.message

        # execute_data and database write occurred
        mock_aave_gateway.get_market_data.assert_called_once()
        mock_lending_repository.save_borrow_position.assert_called_once()

    @pytest.mark.asyncio
    async def test_borrow_blocked_no_collateral(
        self,
        mock_hf_validator,
        mock_balance_checker,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """Test borrow blocked when user has no collateral."""
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        command = BorrowCommand(
            user_id=user_id,
            protocol="aave",
            asset="USDC",
            amount=Decimal("1000.0"),
            chain="ethereum",
            rate_mode="variable",
            min_health_factor=Decimal("1.5"),
        )

        # Mock validation result with NO collateral
        no_collateral_result = HealthFactorResult(
            current_hf=Decimal("inf"),  # No debt yet
            projected_hf=Decimal("0"),  # Would be infinite risk
            level=HealthFactorLevel.CRITICAL,
            collateral_usd=Decimal("0"),  # NO COLLATERAL
            current_debt_usd=Decimal("0"),
            projected_debt_usd=Decimal("1000.0"),
            max_safe_borrow_usd=Decimal("0"),
            liquidation_price=None,
            warning_message="No collateral available",
            emoji="❌",
            is_safe=False,
        )
        mock_hf_validator.validate_borrow.return_value = no_collateral_result

        interactor = BorrowInteractor(
            hf_validator=mock_hf_validator,
            balance_checker=mock_balance_checker,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT & ASSERT: Should raise InsufficientCollateralError
        with pytest.raises(InsufficientCollateralError) as exc_info:
            await interactor.execute(command=command, wallet_address=wallet_address)

        assert exc_info.value.available_usd == Decimal("0")

    @pytest.mark.asyncio
    async def test_borrow_with_stable_rate_mode(
        self,
        mock_hf_validator,
        mock_balance_checker,
        mock_aave_gateway,
        mock_lending_repository,
        test_user_context,
    ):
        """Test borrow with stable rate mode uses correct APY."""
        # ARRANGE
        user_id = test_user_context["user_id"]
        wallet_address = test_user_context["wallet_address"]

        command = BorrowCommand(
            user_id=user_id,
            protocol="aave",
            asset="USDC",
            amount=Decimal("1000.0"),
            chain="ethereum",
            rate_mode="stable",  # STABLE rate mode
            min_health_factor=Decimal("1.5"),
        )

        # Mock safe validation
        safe_hf_result = HealthFactorResult(
            current_hf=Decimal("5.0"),
            projected_hf=Decimal("3.5"),
            level=HealthFactorLevel.SAFE,
            collateral_usd=Decimal("15000.0"),
            current_debt_usd=Decimal("0"),
            projected_debt_usd=Decimal("1000.0"),
            max_safe_borrow_usd=Decimal("8000.0"),
            liquidation_price=Decimal("1000.0"),
            warning_message="SAFE",
            emoji="✅",
            is_safe=True,
        )
        mock_hf_validator.validate_borrow.return_value = safe_hf_result

        # Mock market data with different APYs
        mock_market_data = [
            MagicMock(
                symbol="USDC",
                variable_borrow_apy=Decimal("5.5"),
                stable_borrow_apy=Decimal("7.0"),  # Higher stable rate
                address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            )
        ]
        mock_aave_gateway.get_market_data.return_value = mock_market_data

        expected_position_id = uuid4()
        mock_lending_repository.save_borrow_position.return_value = expected_position_id

        interactor = BorrowInteractor(
            hf_validator=mock_hf_validator,
            balance_checker=mock_balance_checker,
            aave_gateway=mock_aave_gateway,
            repository=mock_lending_repository,
        )

        # ACT
        result = await interactor.execute(
            command=command, wallet_address=wallet_address
        )

        # ASSERT: Uses stable_borrow_apy
        assert result.borrow_apy == Decimal("7.0")  # Stable rate, not variable
        assert result.execute_data["rate_mode"] == "stable"


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
def mock_hf_validator():
    """Mock health factor validator service."""
    mock = AsyncMock()
    mock.validate_borrow = AsyncMock()
    return mock


@pytest.fixture
def mock_balance_checker():
    """Mock balance checker."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_aave_gateway():
    """Mock Aave gateway."""
    mock = AsyncMock()
    mock.get_market_data = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_lending_repository():
    """Mock lending repository."""
    mock = AsyncMock()
    mock.save_borrow_position = AsyncMock(return_value=uuid4())
    return mock
