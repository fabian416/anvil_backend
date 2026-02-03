"""
E2E tests for LendingHandler with balance validation.

Tests the complete flow of lending recommendations with balance checking.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.application.chat.handlers.lending_handler import (
    LendingHandler,
    LendingHandlerResult,
)
from app.domain.entities.lending.morpho_vault import MorphoVault
from app.domain.ports.morpho_gateway import MorphoGateway
from app.domain.ports.balance_checker import IBalanceChecker


@pytest.fixture
def mock_morpho_gateway():
    """Create a mock MorphoGateway."""
    gateway = MagicMock(spec=MorphoGateway)

    # Create sample vaults
    vaults = [
        MorphoVault(
            address="0xvault1",
            name="Steakhouse USDC",
            symbol="stUSDC",
            asset="USDC",
            asset_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            apy=0.125,  # 12.5%
            total_assets=10_000_000.0,
            whitelisted=True,
            chain="ethereum",
            risk_tier="low",
        ),
        MorphoVault(
            address="0xvault2",
            name="Compound USDC",
            symbol="cUSDC",
            asset="USDC",
            asset_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            apy=0.095,  # 9.5%
            total_assets=5_000_000.0,
            whitelisted=True,
            chain="ethereum",
            risk_tier="low",
        ),
    ]

    gateway.get_vaults = AsyncMock(return_value=vaults)

    return gateway


@pytest.fixture
def mock_balance_checker_sufficient():
    """Create a mock IBalanceChecker that always returns sufficient balance."""
    checker = MagicMock(spec=IBalanceChecker)
    checker.check_balance = AsyncMock(return_value=True)
    checker.get_balance = AsyncMock(return_value=Decimal("5000.0"))
    return checker


@pytest.fixture
def mock_balance_checker_insufficient():
    """Create a mock IBalanceChecker that always returns insufficient balance."""
    checker = MagicMock(spec=IBalanceChecker)
    checker.check_balance = AsyncMock(return_value=False)
    checker.get_balance = AsyncMock(return_value=Decimal("100.0"))
    return checker


@pytest.mark.asyncio
async def test_lending_handler_with_sufficient_balance(
    mock_morpho_gateway,
    mock_balance_checker_sufficient,
):
    """Test lending handler generates execute_data when balance is sufficient."""
    handler = LendingHandler(
        morpho_gateway=mock_morpho_gateway,
        balance_checker=mock_balance_checker_sufficient,
    )

    result = await handler.execute(
        message="Show me USDC lending vaults",
        chain="ethereum",
        asset="USDC",
        language="en",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )

    # Verify vaults were returned
    assert len(result.vaults) > 0
    assert result.best_apy > 0

    # Verify execute_data was generated (balance sufficient)
    assert result.execute_data is not None
    assert result.execute_data["action_type"] == "deposit"
    assert result.execute_data["protocol"] == "morpho"
    assert result.execute_data["asset_symbol"] == "USDC"

    # Verify no balance error in content
    assert "Insufficient Balance" not in result.content


@pytest.mark.asyncio
async def test_lending_handler_with_insufficient_balance(
    mock_morpho_gateway,
    mock_balance_checker_insufficient,
):
    """Test lending handler blocks execute_data when balance is insufficient."""
    handler = LendingHandler(
        morpho_gateway=mock_morpho_gateway,
        balance_checker=mock_balance_checker_insufficient,
    )

    result = await handler.execute(
        message="Show me USDC lending vaults",
        chain="ethereum",
        asset="USDC",
        language="en",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )

    # Verify vaults were returned (recommendations shown)
    assert len(result.vaults) > 0

    # Verify execute_data was NOT generated (insufficient balance)
    assert result.execute_data is None

    # Verify balance error in content
    assert "Insufficient Balance" in result.content
    assert "100.0 USDC" in result.content  # Current balance shown
    assert "1000" in result.content  # Required amount shown


@pytest.mark.asyncio
async def test_lending_handler_without_balance_checker(mock_morpho_gateway):
    """Test lending handler works without balance checker (optional)."""
    handler = LendingHandler(
        morpho_gateway=mock_morpho_gateway,
        balance_checker=None,  # No balance checker
    )

    result = await handler.execute(
        message="Show me USDC lending vaults",
        chain="ethereum",
        asset="USDC",
        language="en",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )

    # Verify vaults were returned
    assert len(result.vaults) > 0

    # Verify execute_data was generated (no balance check performed)
    assert result.execute_data is not None

    # Verify no balance error in content
    assert "Insufficient Balance" not in result.content


@pytest.mark.asyncio
async def test_lending_handler_without_wallet_address(
    mock_morpho_gateway,
    mock_balance_checker_sufficient,
):
    """Test lending handler skips balance check when no wallet address provided."""
    handler = LendingHandler(
        morpho_gateway=mock_morpho_gateway,
        balance_checker=mock_balance_checker_sufficient,
    )

    result = await handler.execute(
        message="Show me USDC lending vaults",
        chain="ethereum",
        asset="USDC",
        language="en",
        wallet_address=None,  # No wallet address
    )

    # Verify vaults were returned
    assert len(result.vaults) > 0

    # Verify execute_data was generated (no wallet to check)
    assert result.execute_data is not None

    # Verify balance checker was never called
    mock_balance_checker_sufficient.check_balance.assert_not_called()


@pytest.mark.asyncio
async def test_lending_handler_insufficient_balance_multi_language():
    """Test insufficient balance error messages in multiple languages."""
    gateway = MagicMock(spec=MorphoGateway)
    vaults = [
        MorphoVault(
            address="0xvault1",
            name="Test Vault",
            symbol="tUSDC",
            asset="USDC",
            asset_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            apy=0.10,
            total_assets=1_000_000.0,
            whitelisted=True,
            chain="ethereum",
            risk_tier="low",
        )
    ]
    gateway.get_vaults = AsyncMock(return_value=vaults)

    checker = MagicMock(spec=IBalanceChecker)
    checker.check_balance = AsyncMock(return_value=False)
    checker.get_balance = AsyncMock(return_value=Decimal("50.0"))

    handler = LendingHandler(
        morpho_gateway=gateway,
        balance_checker=checker,
    )

    # Test English
    result_en = await handler.execute(
        message="lend USDC",
        language="en",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )
    assert "Insufficient Balance" in result_en.content

    # Test Spanish
    result_es = await handler.execute(
        message="prestar USDC",
        language="es",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )
    assert "Saldo Insuficiente" in result_es.content

    # Test Portuguese
    result_pt = await handler.execute(
        message="emprestar USDC",
        language="pt",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )
    assert "Saldo Insuficiente" in result_pt.content

    # Test Chinese
    result_zh = await handler.execute(
        message="借出 USDC",
        language="zh",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )
    assert "余额不足" in result_zh.content


@pytest.mark.asyncio
async def test_lending_handler_balance_check_error_handling(mock_morpho_gateway):
    """Test lending handler handles balance check errors gracefully."""
    checker = MagicMock(spec=IBalanceChecker)
    checker.check_balance = AsyncMock(side_effect=Exception("RPC Error"))
    checker.get_balance = AsyncMock(return_value=Decimal("0"))

    handler = LendingHandler(
        morpho_gateway=mock_morpho_gateway,
        balance_checker=checker,
    )

    result = await handler.execute(
        message="Show me USDC vaults",
        chain="ethereum",
        asset="USDC",
        language="en",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )

    # Verify handler doesn't crash
    assert len(result.vaults) > 0

    # Verify execute_data was NOT generated (conservative approach on error)
    assert result.execute_data is None


@pytest.mark.asyncio
async def test_lending_handler_execute_data_structure(
    mock_morpho_gateway,
    mock_balance_checker_sufficient,
):
    """Test execute_data has correct structure for frontend."""
    handler = LendingHandler(
        morpho_gateway=mock_morpho_gateway,
        balance_checker=mock_balance_checker_sufficient,
    )

    result = await handler.execute(
        message="deposit USDC",
        chain="ethereum",
        asset="USDC",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )

    # Verify execute_data structure
    assert result.execute_data is not None
    execute_data = result.execute_data

    # Required fields
    assert "action_type" in execute_data
    assert "protocol" in execute_data
    assert "chain" in execute_data
    assert "vault_address" in execute_data
    assert "asset_address" in execute_data
    assert "asset_symbol" in execute_data
    assert "amount" in execute_data

    # Verify values
    assert execute_data["action_type"] == "deposit"
    assert execute_data["protocol"] == "morpho"
    assert execute_data["chain"] == "ethereum"
    assert execute_data["asset_symbol"] == "USDC"

    # Metadata fields
    assert "vault_name" in execute_data
    assert "vault_apy" in execute_data
    assert "vault_tvl" in execute_data
