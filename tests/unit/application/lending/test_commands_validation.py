"""
Standalone unit tests for command validation (no database required).

Tests command dataclass validation logic without any fixtures.
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from app.application.lending.commands.supply_command import SupplyCommand, SupplyResult
from app.application.lending.commands.borrow_command import BorrowCommand, BorrowResult


class TestSupplyCommandValidation:
    """Test supply command validation (standalone, no fixtures)."""

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
        assert command.use_as_collateral is True

    def test_valid_morpho_command(self):
        """Test valid Morpho supply command."""
        command = SupplyCommand(
            user_id=uuid4(),
            protocol="morpho",
            asset="USDC",
            amount=Decimal("1000.0"),
            chain="ethereum",
            vault_address="0x1234567890123456789012345678901234567890",
        )
        assert command.protocol == "morpho"
        assert command.vault_address is not None

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


class TestBorrowCommandValidation:
    """Test borrow command validation (standalone, no fixtures)."""

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
        assert command.rate_mode == "variable"
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


class TestResultSerialization:
    """Test result serialization (standalone)."""

    def test_supply_result_to_dict(self):
        """Test SupplyResult serialization."""
        position_id = uuid4()
        result = SupplyResult(
            transaction_hash=None,
            position_id=position_id,
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
        assert result_dict["position_id"] == str(position_id)

    def test_borrow_result_to_dict(self):
        """Test BorrowResult serialization."""
        position_id = uuid4()
        result = BorrowResult(
            transaction_hash=None,
            position_id=position_id,
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
