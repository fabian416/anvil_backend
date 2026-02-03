"""
Unit tests for BorrowInteractor.

Tests borrow command orchestration with health factor validation.
Target: >90% coverage for interactor logic and edge cases.
"""

import pytest
from decimal import Decimal
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock

from app.application.lending.commands.borrow_command import BorrowCommand, BorrowResult
from app.application.lending.interactors.borrow_interactor import (
    BorrowInteractor,
    UnsafeBorrowError,
    InsufficientCollateralError,
)
from app.domain.value_objects.lending.health_factor_result import (
    HealthFactorResult,
    HealthFactorLevel,
)


@pytest.fixture
def mock_hf_validator():
    """Mock health factor validator service."""
    validator = AsyncMock()

    # Default: safe borrow
    validator.validate_borrow = AsyncMock(
        return_value=HealthFactorResult(
            current_hf=Decimal("3.5"),
            projected_hf=Decimal("2.1"),
            level=HealthFactorLevel.CAUTION,
            is_safe=True,
            warning_message="⚠️ CAUTION - Health Factor 2.1",
            liquidation_price=Decimal("3200.50"),
            max_safe_borrow_usd=Decimal("1500.00"),
            collateral_usd=Decimal("5000.00"),
            current_debt_usd=Decimal("0.00"),
            projected_debt_usd=Decimal("2000.00"),
        )
    )
    return validator


@pytest.fixture
def mock_balance_checker():
    """Mock balance checker."""
    checker = AsyncMock()
    checker.check_gas_balance = AsyncMock(return_value=True)
    return checker


@pytest.fixture
def mock_aave_gateway():
    """Mock Aave gateway."""
    gateway = AsyncMock()

    # Mock market data
    mock_market = MagicMock()
    mock_market.symbol = "USDC"
    mock_market.variable_borrow_apy = Decimal("4.2")
    mock_market.stable_borrow_apy = Decimal("5.5")
    mock_market.address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

    gateway.get_market_data = AsyncMock(return_value=[mock_market])
    return gateway


@pytest.fixture
def mock_repository():
    """Mock lending repository."""
    repo = AsyncMock()
    repo.save_borrow_position = AsyncMock(return_value=uuid4())
    return repo


@pytest.fixture
def borrow_interactor(
    mock_hf_validator,
    mock_balance_checker,
    mock_aave_gateway,
    mock_repository,
):
    """Create borrow interactor with mocked dependencies."""
    return BorrowInteractor(
        hf_validator=mock_hf_validator,
        balance_checker=mock_balance_checker,
        aave_gateway=mock_aave_gateway,
        repository=mock_repository,
    )


class TestBorrowCommandValidation:
    """Test borrow command validation."""

    def test_valid_borrow_command(self):
        """Test valid borrow command."""
        command = BorrowCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="USDC",
            amount=Decimal("2000.0"),
            chain="ethereum",
            rate_mode="variable",
            min_health_factor=Decimal("1.5"),
        )
        assert command.protocol == "aave"
        assert command.amount == Decimal("2000.0")
        assert command.min_health_factor == Decimal("1.5")

    def test_invalid_negative_amount(self):
        """Test validation fails for negative amount."""
        with pytest.raises(ValueError, match="must be positive"):
            BorrowCommand(
                user_id=uuid4(),
                protocol="aave",
                asset="USDC",
                amount=Decimal("-100.0"),
                chain="ethereum",
            )

    def test_invalid_protocol(self):
        """Test validation fails for non-Aave protocol."""
        with pytest.raises(ValueError, match="Only Aave protocol"):
            BorrowCommand(
                user_id=uuid4(),
                protocol="morpho",
                asset="USDC",
                amount=Decimal("2000.0"),
                chain="ethereum",
            )

    def test_invalid_rate_mode(self):
        """Test validation fails for invalid rate mode."""
        with pytest.raises(ValueError, match="must be 'variable' or 'stable'"):
            BorrowCommand(
                user_id=uuid4(),
                protocol="aave",
                asset="USDC",
                amount=Decimal("2000.0"),
                chain="ethereum",
                rate_mode="fixed",
            )

    def test_invalid_min_health_factor(self):
        """Test validation fails for HF < 1.0."""
        with pytest.raises(ValueError, match="must be >= 1.0"):
            BorrowCommand(
                user_id=uuid4(),
                protocol="aave",
                asset="USDC",
                amount=Decimal("2000.0"),
                chain="ethereum",
                min_health_factor=Decimal("0.5"),
            )


class TestBorrowInteractorSafeBorrow:
    """Test safe borrow operations."""

    @pytest.mark.asyncio
    async def test_successful_borrow_variable(self, borrow_interactor, mock_repository):
        """Test successful borrow with variable rate."""
        command = BorrowCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="USDC",
            amount=Decimal("2000.0"),
            chain="ethereum",
            rate_mode="variable",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        result = await borrow_interactor.execute(command, wallet_address)

        # Verify result structure
        assert result.protocol == "aave"
        assert result.asset == "USDC"
        assert result.amount == Decimal("2000.0")
        assert result.rate_mode == "variable"
        assert result.borrow_apy == Decimal("4.2")
        assert result.status == "awaiting_signature"
        assert result.health_factor_current == Decimal("3.5")
        assert result.health_factor_projected == Decimal("2.1")
        assert result.risk_level == "CAUTION"

        # Verify execute_data structure
        assert result.execute_data["action_type"] == "borrow"
        assert result.execute_data["provider"] == "aave"
        assert result.execute_data["rate_mode"] == "variable"

        # Verify repository was called
        mock_repository.save_borrow_position.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_borrow_stable(self, borrow_interactor):
        """Test successful borrow with stable rate."""
        command = BorrowCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="USDC",
            amount=Decimal("2000.0"),
            chain="ethereum",
            rate_mode="stable",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        result = await borrow_interactor.execute(command, wallet_address)

        assert result.rate_mode == "stable"
        assert result.borrow_apy == Decimal("5.5")


class TestBorrowInteractorUnsafeBorrow:
    """Test unsafe borrow scenarios."""

    @pytest.mark.asyncio
    async def test_unsafe_borrow_blocked(self, borrow_interactor, mock_hf_validator):
        """Test borrow blocked when projected HF < min_health_factor."""
        # Mock unsafe validation result
        mock_hf_validator.validate_borrow = AsyncMock(
            return_value=HealthFactorResult(
                current_hf=Decimal("1.8"),
                projected_hf=Decimal("1.1"),  # Below minimum 1.5
                level=HealthFactorLevel.DANGER,
                is_safe=False,
                warning_message="🔶 DANGER - Health Factor 1.1",
                liquidation_price=Decimal("3500.00"),
                max_safe_borrow_usd=Decimal("500.00"),
                collateral_usd=Decimal("5000.00"),
                current_debt_usd=Decimal("2000.00"),
                projected_debt_usd=Decimal("4000.00"),
            )
        )

        command = BorrowCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="USDC",
            amount=Decimal("2000.0"),
            chain="ethereum",
            min_health_factor=Decimal("1.5"),
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        with pytest.raises(UnsafeBorrowError) as exc_info:
            await borrow_interactor.execute(command, wallet_address)

        assert exc_info.value.validation_result.projected_hf == Decimal("1.1")
        assert exc_info.value.validation_result.level == HealthFactorLevel.DANGER

    @pytest.mark.asyncio
    async def test_critical_health_factor_blocked(self, borrow_interactor, mock_hf_validator):
        """Test borrow blocked with critical health factor."""
        # Mock critical validation result
        mock_hf_validator.validate_borrow = AsyncMock(
            return_value=HealthFactorResult(
                current_hf=Decimal("1.3"),
                projected_hf=Decimal("0.95"),  # Below 1.0 = liquidatable
                level=HealthFactorLevel.LIQUIDATABLE,
                is_safe=False,
                warning_message="❌ LIQUIDATABLE - Immediate liquidation risk",
                liquidation_price=None,
                max_safe_borrow_usd=Decimal("0.00"),
                collateral_usd=Decimal("3000.00"),
                current_debt_usd=Decimal("2000.00"),
                projected_debt_usd=Decimal("4000.00"),
            )
        )

        command = BorrowCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="USDC",
            amount=Decimal("2000.0"),
            chain="ethereum",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        with pytest.raises(UnsafeBorrowError):
            await borrow_interactor.execute(command, wallet_address)


class TestBorrowInteractorEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_zero_collateral(self, borrow_interactor, mock_hf_validator):
        """Test borrow fails with zero collateral."""
        # Mock validation with zero collateral
        mock_hf_validator.validate_borrow = AsyncMock(
            return_value=HealthFactorResult(
                current_hf=Decimal("0"),
                projected_hf=Decimal("0"),
                level=HealthFactorLevel.LIQUIDATABLE,
                is_safe=False,
                warning_message="❌ No collateral",
                liquidation_price=None,
                max_safe_borrow_usd=Decimal("0.00"),
                collateral_usd=Decimal("0.00"),  # Zero collateral
                current_debt_usd=Decimal("0.00"),
                projected_debt_usd=Decimal("2000.00"),
            )
        )

        command = BorrowCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="USDC",
            amount=Decimal("2000.0"),
            chain="ethereum",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        with pytest.raises(UnsafeBorrowError):
            await borrow_interactor.execute(command, wallet_address)

    @pytest.mark.asyncio
    async def test_asset_not_found(self, borrow_interactor, mock_aave_gateway):
        """Test borrow fails when asset not in market."""
        # Mock empty market data
        mock_aave_gateway.get_market_data = AsyncMock(return_value=[])

        command = BorrowCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="XYZ",
            amount=Decimal("2000.0"),
            chain="ethereum",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        with pytest.raises(ValueError, match="not found in Aave market"):
            await borrow_interactor.execute(command, wallet_address)


class TestBorrowResultSerialization:
    """Test borrow result serialization."""

    def test_borrow_result_to_dict(self):
        """Test BorrowResult serialization to dictionary."""
        result = BorrowResult(
            transaction_hash=None,
            position_id=uuid4(),
            health_factor_current=Decimal("3.5"),
            health_factor_projected=Decimal("2.1"),
            risk_level="CAUTION",
            liquidation_price=Decimal("3200.50"),
            max_safe_borrow_usd=Decimal("1500.00"),
            execute_data={"test": "data"},
            protocol="aave",
            asset="USDC",
            amount=Decimal("2000.0"),
            chain="ethereum",
            rate_mode="variable",
            borrow_apy=Decimal("4.2"),
            status="awaiting_signature",
            message="Test message",
        )

        result_dict = result.to_dict()

        assert result_dict["protocol"] == "aave"
        assert result_dict["asset"] == "USDC"
        assert result_dict["amount"] == "2000.0"
        assert result_dict["health_factor"]["current"] == "3.5"
        assert result_dict["health_factor"]["projected"] == "2.1"
        assert result_dict["health_factor"]["risk_level"] == "CAUTION"
        assert result_dict["health_factor"]["liquidation_price"] == "3200.50"
