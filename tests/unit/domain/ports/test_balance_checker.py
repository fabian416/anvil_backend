"""
Unit tests for IBalanceChecker port.

Tests the domain interface contract for balance checking.
"""

import pytest
from decimal import Decimal
from typing import Protocol

from app.domain.ports.balance_checker import IBalanceChecker


class MockBalanceChecker(IBalanceChecker):
    """Mock implementation of IBalanceChecker for testing."""

    def __init__(self):
        self.balances = {}

    async def check_balance(
        self,
        wallet_address: str,
        token_address: str,
        required_amount: Decimal,
        chain: str = "ethereum",
    ) -> bool:
        """Mock check_balance implementation."""
        key = f"{chain}:{wallet_address}:{token_address}"
        balance = self.balances.get(key, Decimal("0"))
        return balance >= required_amount

    async def get_balance(
        self,
        wallet_address: str,
        token_address: str,
        chain: str = "ethereum",
    ) -> Decimal:
        """Mock get_balance implementation."""
        key = f"{chain}:{wallet_address}:{token_address}"
        return self.balances.get(key, Decimal("0"))

    async def check_gas_balance(
        self,
        wallet_address: str,
        chain: str = "ethereum",
        min_gas_amount: Decimal | None = None,
    ) -> bool:
        """Mock check_gas_balance implementation."""
        if min_gas_amount is None:
            min_gas_amount = Decimal("0.01")
        key = f"{chain}:{wallet_address}:native"
        balance = self.balances.get(key, Decimal("0"))
        return balance >= min_gas_amount

    def set_balance(
        self,
        wallet_address: str,
        token_address: str,
        balance: Decimal,
        chain: str = "ethereum",
    ):
        """Helper method to set balance for testing."""
        key = f"{chain}:{wallet_address}:{token_address}"
        self.balances[key] = balance


@pytest.mark.asyncio
async def test_balance_checker_interface():
    """Test that MockBalanceChecker implements the expected methods."""
    # Verify our mock has all required methods
    checker = MockBalanceChecker()
    assert hasattr(checker, 'check_balance')
    assert hasattr(checker, 'get_balance')
    assert hasattr(checker, 'check_gas_balance')
    assert callable(checker.check_balance)
    assert callable(checker.get_balance)
    assert callable(checker.check_gas_balance)


@pytest.mark.asyncio
async def test_check_balance_sufficient():
    """Test check_balance returns True when balance is sufficient."""
    checker = MockBalanceChecker()
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC

    # Set balance
    checker.set_balance(wallet, token, Decimal("5000.0"), chain="ethereum")

    # Check balance
    has_balance = await checker.check_balance(
        wallet_address=wallet,
        token_address=token,
        required_amount=Decimal("1000.0"),
        chain="ethereum",
    )

    assert has_balance is True


@pytest.mark.asyncio
async def test_check_balance_insufficient():
    """Test check_balance returns False when balance is insufficient."""
    checker = MockBalanceChecker()
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC

    # Set balance (insufficient)
    checker.set_balance(wallet, token, Decimal("500.0"), chain="ethereum")

    # Check balance
    has_balance = await checker.check_balance(
        wallet_address=wallet,
        token_address=token,
        required_amount=Decimal("1000.0"),
        chain="ethereum",
    )

    assert has_balance is False


@pytest.mark.asyncio
async def test_get_balance():
    """Test get_balance returns correct balance."""
    checker = MockBalanceChecker()
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC
    expected_balance = Decimal("2500.5")

    # Set balance
    checker.set_balance(wallet, token, expected_balance, chain="ethereum")

    # Get balance
    balance = await checker.get_balance(
        wallet_address=wallet,
        token_address=token,
        chain="ethereum",
    )

    assert balance == expected_balance


@pytest.mark.asyncio
async def test_get_balance_zero_when_not_set():
    """Test get_balance returns 0 when no balance is set."""
    checker = MockBalanceChecker()
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC

    # Don't set any balance
    balance = await checker.get_balance(
        wallet_address=wallet,
        token_address=token,
        chain="ethereum",
    )

    assert balance == Decimal("0")


@pytest.mark.asyncio
async def test_check_gas_balance_sufficient():
    """Test check_gas_balance returns True when gas is sufficient."""
    checker = MockBalanceChecker()
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

    # Set native token balance
    checker.set_balance(wallet, "native", Decimal("0.5"), chain="ethereum")

    # Check gas balance
    has_gas = await checker.check_gas_balance(
        wallet_address=wallet,
        chain="ethereum",
        min_gas_amount=Decimal("0.01"),
    )

    assert has_gas is True


@pytest.mark.asyncio
async def test_check_gas_balance_insufficient():
    """Test check_gas_balance returns False when gas is insufficient."""
    checker = MockBalanceChecker()
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

    # Set native token balance (insufficient)
    checker.set_balance(wallet, "native", Decimal("0.005"), chain="ethereum")

    # Check gas balance
    has_gas = await checker.check_gas_balance(
        wallet_address=wallet,
        chain="ethereum",
        min_gas_amount=Decimal("0.01"),
    )

    assert has_gas is False


@pytest.mark.asyncio
async def test_check_gas_balance_default_minimum():
    """Test check_gas_balance uses default minimum when not specified."""
    checker = MockBalanceChecker()
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

    # Set native token balance (just above default minimum)
    checker.set_balance(wallet, "native", Decimal("0.015"), chain="ethereum")

    # Check gas balance without specifying minimum
    has_gas = await checker.check_gas_balance(
        wallet_address=wallet,
        chain="ethereum",
    )

    assert has_gas is True


@pytest.mark.asyncio
async def test_balance_checker_multi_chain():
    """Test balance checker works across multiple chains."""
    checker = MockBalanceChecker()
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    usdc_eth = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    usdc_base = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"

    # Set balances on different chains
    checker.set_balance(wallet, usdc_eth, Decimal("1000.0"), chain="ethereum")
    checker.set_balance(wallet, usdc_base, Decimal("500.0"), chain="base")

    # Check Ethereum balance
    eth_balance = await checker.get_balance(wallet, usdc_eth, chain="ethereum")
    assert eth_balance == Decimal("1000.0")

    # Check Base balance
    base_balance = await checker.get_balance(wallet, usdc_base, chain="base")
    assert base_balance == Decimal("500.0")

    # Verify chain isolation
    wrong_balance = await checker.get_balance(wallet, usdc_eth, chain="base")
    assert wrong_balance == Decimal("0")
