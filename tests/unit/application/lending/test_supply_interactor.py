"""
Unit tests for SupplyInteractor.

Tests supply command orchestration with mocked dependencies.
Target: >90% coverage for interactor logic.
"""

import pytest
from decimal import Decimal
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.lending.commands.supply_command import SupplyCommand, SupplyResult
from app.application.lending.interactors.supply_interactor import (
    SupplyInteractor,
    BalanceInsufficientError,
    ProtocolNotSupportedError,
)


@pytest.fixture
def mock_balance_checker():
    """Mock balance checker."""
    checker = AsyncMock()
    checker.get_balance = AsyncMock(return_value=Decimal("1500.0"))
    checker.check_gas_balance = AsyncMock(return_value=True)
    return checker


@pytest.fixture
def mock_aave_gateway():
    """Mock Aave gateway."""
    gateway = AsyncMock()

    # Mock market data
    mock_market = MagicMock()
    mock_market.symbol = "USDC"
    mock_market.supply_apy = Decimal("5.25")
    mock_market.address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    mock_market.price_usd = Decimal("1.00")

    gateway.get_market_data = AsyncMock(return_value=[mock_market])
    return gateway


@pytest.fixture
def mock_morpho_gateway():
    """Mock Morpho gateway."""
    gateway = AsyncMock()

    # Mock vault details
    mock_vault = MagicMock()
    mock_vault.address = "0x1234..."
    mock_vault.name = "Steakhouse USDC"
    mock_vault.asset = "USDC"
    mock_vault.apy = Decimal("12.5")
    mock_vault.asset_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    mock_vault.total_assets = Decimal("10000000.0")

    gateway.get_vault_details = AsyncMock(return_value=mock_vault)
    return gateway


@pytest.fixture
def mock_repository():
    """Mock lending repository."""
    repo = AsyncMock()
    repo.save_supply_position = AsyncMock(return_value=uuid4())
    return repo


@pytest.fixture
def supply_interactor(
    mock_balance_checker,
    mock_aave_gateway,
    mock_morpho_gateway,
    mock_repository,
):
    """Create supply interactor with mocked dependencies."""
    return SupplyInteractor(
        balance_checker=mock_balance_checker,
        aave_gateway=mock_aave_gateway,
        morpho_gateway=mock_morpho_gateway,
        repository=mock_repository,
    )


class TestSupplyCommandValidation:
    """Test supply command validation."""

    def test_valid_aave_command(self):
        """Test valid Aave supply command."""
        command = SupplyCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="USDC",
            amount=Decimal("1000.0"),
            chain="ethereum",
        )
        assert command.protocol == "aave"
        assert command.amount == Decimal("1000.0")

    def test_valid_morpho_command(self):
        """Test valid Morpho supply command."""
        command = SupplyCommand(
            user_id=uuid4(),
            protocol="morpho",
            asset="USDC",
            amount=Decimal("1000.0"),
            chain="ethereum",
            vault_address="0x1234...",
        )
        assert command.protocol == "morpho"
        assert command.vault_address == "0x1234..."

    def test_invalid_negative_amount(self):
        """Test validation fails for negative amount."""
        with pytest.raises(ValueError, match="Amount must be positive"):
            SupplyCommand(
                user_id=uuid4(),
                protocol="aave",
                asset="USDC",
                amount=Decimal("-100.0"),
                chain="ethereum",
            )

    def test_invalid_zero_amount(self):
        """Test validation fails for zero amount."""
        with pytest.raises(ValueError, match="Amount must be positive"):
            SupplyCommand(
                user_id=uuid4(),
                protocol="aave",
                asset="USDC",
                amount=Decimal("0"),
                chain="ethereum",
            )

    def test_invalid_protocol(self):
        """Test validation fails for unsupported protocol."""
        with pytest.raises(ValueError, match="Unsupported protocol"):
            SupplyCommand(
                user_id=uuid4(),
                protocol="compound",
                asset="USDC",
                amount=Decimal("1000.0"),
                chain="ethereum",
            )

    def test_morpho_requires_vault_address(self):
        """Test Morpho protocol requires vault_address."""
        with pytest.raises(ValueError, match="requires vault_address"):
            SupplyCommand(
                user_id=uuid4(),
                protocol="morpho",
                asset="USDC",
                amount=Decimal("1000.0"),
                chain="ethereum",
                vault_address=None,
            )

    def test_invalid_chain(self):
        """Test validation fails for unsupported chain."""
        with pytest.raises(ValueError, match="Unsupported chain"):
            SupplyCommand(
                user_id=uuid4(),
                protocol="aave",
                asset="USDC",
                amount=Decimal("1000.0"),
                chain="fantom",
            )


class TestSupplyInteractorAave:
    """Test Aave supply operations."""

    @pytest.mark.asyncio
    async def test_successful_aave_supply(self, supply_interactor, mock_repository):
        """Test successful Aave supply operation."""
        command = SupplyCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="USDC",
            amount=Decimal("1000.0"),
            chain="ethereum",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        result = await supply_interactor.execute(command, wallet_address)

        # Verify result structure
        assert result.protocol == "aave"
        assert result.asset == "USDC"
        assert result.amount == Decimal("1000.0")
        assert result.apy == Decimal("5.25")
        assert result.status == "awaiting_signature"
        assert result.execute_data["action_type"] == "supply"
        assert result.execute_data["provider"] == "aave"

        # Verify repository was called
        mock_repository.save_supply_position.assert_called_once()

    @pytest.mark.asyncio
    async def test_insufficient_balance_aave(self, supply_interactor, mock_balance_checker):
        """Test supply fails with insufficient balance."""
        # Set balance lower than required
        mock_balance_checker.get_balance = AsyncMock(return_value=Decimal("500.0"))

        command = SupplyCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="USDC",
            amount=Decimal("1000.0"),
            chain="ethereum",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        with pytest.raises(BalanceInsufficientError) as exc_info:
            await supply_interactor.execute(command, wallet_address)

        assert exc_info.value.asset == "USDC"
        assert exc_info.value.required == Decimal("1000.0")
        assert exc_info.value.available == Decimal("500.0")

    @pytest.mark.asyncio
    async def test_insufficient_gas_aave(self, supply_interactor, mock_balance_checker):
        """Test supply fails with insufficient gas."""
        # Set gas balance to False
        mock_balance_checker.check_gas_balance = AsyncMock(return_value=False)

        command = SupplyCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="USDC",
            amount=Decimal("1000.0"),
            chain="ethereum",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        with pytest.raises(BalanceInsufficientError) as exc_info:
            await supply_interactor.execute(command, wallet_address)

        assert exc_info.value.asset == "ETH"

    @pytest.mark.asyncio
    async def test_asset_not_found_aave(self, supply_interactor, mock_aave_gateway):
        """Test supply fails when asset not in Aave market."""
        # Mock empty market data
        mock_aave_gateway.get_market_data = AsyncMock(return_value=[])

        command = SupplyCommand(
            user_id=uuid4(),
            protocol="aave",
            asset="XYZ",
            amount=Decimal("1000.0"),
            chain="ethereum",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        with pytest.raises(ValueError, match="not found in Aave market"):
            await supply_interactor.execute(command, wallet_address)


class TestSupplyInteractorMorpho:
    """Test Morpho supply operations."""

    @pytest.mark.asyncio
    async def test_successful_morpho_supply(self, supply_interactor, mock_repository):
        """Test successful Morpho supply operation."""
        command = SupplyCommand(
            user_id=uuid4(),
            protocol="morpho",
            asset="USDC",
            amount=Decimal("1000.0"),
            chain="ethereum",
            vault_address="0x1234...",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        result = await supply_interactor.execute(command, wallet_address)

        # Verify result structure
        assert result.protocol == "morpho"
        assert result.asset == "USDC"
        assert result.amount == Decimal("1000.0")
        assert result.apy == Decimal("12.5")
        assert result.vault_name == "Steakhouse USDC"
        assert result.status == "awaiting_signature"
        assert result.execute_data["action_type"] == "supply"
        assert result.execute_data["provider"] == "morpho"

        # Verify repository was called
        mock_repository.save_supply_position.assert_called_once()

    @pytest.mark.asyncio
    async def test_asset_mismatch_morpho(self, supply_interactor):
        """Test supply fails when asset doesn't match vault."""
        command = SupplyCommand(
            user_id=uuid4(),
            protocol="morpho",
            asset="DAI",  # Different from vault asset (USDC)
            amount=Decimal("1000.0"),
            chain="ethereum",
            vault_address="0x1234...",
        )
        wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

        with pytest.raises(ValueError, match="Asset mismatch"):
            await supply_interactor.execute(command, wallet_address)


class TestSupplyResultSerialization:
    """Test supply result serialization."""

    def test_supply_result_to_dict(self):
        """Test SupplyResult serialization to dictionary."""
        result = SupplyResult(
            transaction_hash=None,
            position_id=uuid4(),
            apy=Decimal("5.25"),
            execute_data={"test": "data"},
            protocol="aave",
            asset="USDC",
            amount=Decimal("1000.0"),
            chain="ethereum",
            vault_name=None,
            status="awaiting_signature",
            message="Test message",
        )

        result_dict = result.to_dict()

        assert result_dict["protocol"] == "aave"
        assert result_dict["asset"] == "USDC"
        assert result_dict["amount"] == "1000.0"
        assert result_dict["apy"] == "5.25"
        assert result_dict["status"] == "awaiting_signature"
        assert "position_id" in result_dict
