"""
Integration tests for PortfolioBalanceChecker adapter.

Tests the adapter's integration with PortfolioService and RPC endpoints.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.adapters.balance.portfolio_balance_checker import (
    PortfolioBalanceChecker,
)
from app.application.portfolio.portfolio_service import PortfolioService
from app.domain.enums.chain_type import ChainType


@pytest.fixture
def mock_portfolio_service():
    """Create a mock PortfolioService for testing."""
    service = MagicMock(spec=PortfolioService)

    # Mock RPC URL getter
    service._get_rpc_url = MagicMock(return_value="https://eth.llamarpc.com")

    # Mock native balance fetcher
    async def mock_fetch_native_balance(rpc_url: str, address: str) -> Decimal:
        # Return different balances based on address for testing
        if "insufficient" in address.lower():
            return Decimal("0.005")  # Insufficient gas
        return Decimal("1.5")  # Sufficient balance

    service._fetch_native_balance = AsyncMock(side_effect=mock_fetch_native_balance)

    # Mock token balance fetcher
    async def mock_fetch_token_balance(
        rpc_url: str,
        wallet_address: str,
        token_address: str,
        decimals: int = 18,
    ) -> Decimal:
        # Return different balances based on wallet for testing
        if "insufficient" in wallet_address.lower():
            return Decimal("100.0")  # Insufficient
        elif "zero" in wallet_address.lower():
            return Decimal("0")  # No balance
        return Decimal("5000.0")  # Sufficient balance

    service._fetch_token_balance = AsyncMock(side_effect=mock_fetch_token_balance)

    return service


@pytest.fixture
def balance_checker(mock_portfolio_service):
    """Create PortfolioBalanceChecker with mocked service."""
    return PortfolioBalanceChecker(portfolio_service=mock_portfolio_service)


@pytest.mark.asyncio
async def test_check_balance_sufficient(balance_checker):
    """Test check_balance returns True for sufficient balance."""
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC

    has_balance = await balance_checker.check_balance(
        wallet_address=wallet,
        token_address=token,
        required_amount=Decimal("1000.0"),
        chain="ethereum",
    )

    assert has_balance is True


@pytest.mark.asyncio
async def test_check_balance_insufficient(balance_checker):
    """Test check_balance returns False for insufficient balance."""
    wallet = "0xinsufficient742d35Cc6634C0532925a3b844Bc9e"
    token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC

    has_balance = await balance_checker.check_balance(
        wallet_address=wallet,
        token_address=token,
        required_amount=Decimal("1000.0"),
        chain="ethereum",
    )

    assert has_balance is False


@pytest.mark.asyncio
async def test_get_balance_erc20(balance_checker):
    """Test get_balance returns correct ERC20 token balance."""
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC

    balance = await balance_checker.get_balance(
        wallet_address=wallet,
        token_address=token,
        chain="ethereum",
    )

    assert balance == Decimal("5000.0")


@pytest.mark.asyncio
async def test_get_balance_native_token(balance_checker):
    """Test get_balance returns correct native token balance."""
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

    balance = await balance_checker.get_balance(
        wallet_address=wallet,
        token_address="native",
        chain="ethereum",
    )

    assert balance == Decimal("1.5")


@pytest.mark.asyncio
async def test_get_balance_zero(balance_checker):
    """Test get_balance returns zero for wallet with no balance."""
    wallet = "0xzero742d35Cc6634C0532925a3b844Bc9e7595f0"
    token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

    balance = await balance_checker.get_balance(
        wallet_address=wallet,
        token_address=token,
        chain="ethereum",
    )

    assert balance == Decimal("0")


@pytest.mark.asyncio
async def test_check_gas_balance_sufficient(balance_checker):
    """Test check_gas_balance returns True for sufficient gas."""
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

    has_gas = await balance_checker.check_gas_balance(
        wallet_address=wallet,
        chain="ethereum",
    )

    assert has_gas is True


@pytest.mark.asyncio
async def test_check_gas_balance_insufficient(balance_checker):
    """Test check_gas_balance returns False for insufficient gas."""
    wallet = "0xinsufficient742d35Cc6634C0532925a3b844Bc9e"

    has_gas = await balance_checker.check_gas_balance(
        wallet_address=wallet,
        chain="ethereum",
    )

    assert has_gas is False


@pytest.mark.asyncio
async def test_check_gas_balance_custom_minimum(balance_checker):
    """Test check_gas_balance with custom minimum gas amount."""
    wallet = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

    has_gas = await balance_checker.check_gas_balance(
        wallet_address=wallet,
        chain="ethereum",
        min_gas_amount=Decimal("0.5"),
    )

    assert has_gas is True


@pytest.mark.asyncio
async def test_parse_chain_ethereum(balance_checker):
    """Test _parse_chain correctly parses Ethereum variants."""
    assert balance_checker._parse_chain("ethereum") == ChainType.ETHEREUM
    assert balance_checker._parse_chain("eth") == ChainType.ETHEREUM
    assert balance_checker._parse_chain("mainnet") == ChainType.ETHEREUM


@pytest.mark.asyncio
async def test_parse_chain_base(balance_checker):
    """Test _parse_chain correctly parses Base."""
    assert balance_checker._parse_chain("base") == ChainType.BASE


@pytest.mark.asyncio
async def test_parse_chain_arbitrum(balance_checker):
    """Test _parse_chain correctly parses Arbitrum."""
    assert balance_checker._parse_chain("arbitrum") == ChainType.ARBITRUM
    assert balance_checker._parse_chain("arb") == ChainType.ARBITRUM


@pytest.mark.asyncio
async def test_parse_chain_invalid(balance_checker):
    """Test _parse_chain raises ValueError for unsupported chain."""
    with pytest.raises(ValueError, match="Unsupported chain"):
        balance_checker._parse_chain("unsupported_chain")


def test_get_token_decimals_known_token(balance_checker):
    """Test _get_token_decimals returns correct decimals for known tokens."""
    usdc_eth = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    assert balance_checker._get_token_decimals(usdc_eth, "ethereum") == 6

    weth_eth = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    assert balance_checker._get_token_decimals(weth_eth, "ethereum") == 18

    usdc_base = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
    assert balance_checker._get_token_decimals(usdc_base, "base") == 6


def test_get_token_decimals_unknown_token(balance_checker):
    """Test _get_token_decimals returns default 18 for unknown tokens."""
    unknown_token = "0x0000000000000000000000000000000000000000"
    assert balance_checker._get_token_decimals(unknown_token, "ethereum") == 18


def test_get_token_symbol_known_token(balance_checker):
    """Test get_token_symbol returns correct symbol for known tokens."""
    usdc_eth = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    assert balance_checker.get_token_symbol(usdc_eth, "ethereum") == "USDC"

    weth_eth = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    assert balance_checker.get_token_symbol(weth_eth, "ethereum") == "WETH"


def test_get_token_symbol_unknown_token(balance_checker):
    """Test get_token_symbol returns None for unknown tokens."""
    unknown_token = "0x0000000000000000000000000000000000000000"
    assert balance_checker.get_token_symbol(unknown_token, "ethereum") is None


def test_min_gas_amounts_configured(balance_checker):
    """Test MIN_GAS_AMOUNTS are properly configured for all chains."""
    assert ChainType.ETHEREUM in balance_checker.MIN_GAS_AMOUNTS
    assert ChainType.BASE in balance_checker.MIN_GAS_AMOUNTS
    assert ChainType.ARBITRUM in balance_checker.MIN_GAS_AMOUNTS
    assert ChainType.POLYGON in balance_checker.MIN_GAS_AMOUNTS
    assert ChainType.OPTIMISM in balance_checker.MIN_GAS_AMOUNTS

    # Verify amounts are reasonable
    assert balance_checker.MIN_GAS_AMOUNTS[ChainType.ETHEREUM] >= Decimal("0.001")
    assert balance_checker.MIN_GAS_AMOUNTS[ChainType.BASE] >= Decimal("0.0001")


def test_token_addresses_configured(balance_checker):
    """Test TOKEN_ADDRESSES are properly configured."""
    assert "ethereum" in balance_checker.TOKEN_ADDRESSES
    assert "base" in balance_checker.TOKEN_ADDRESSES

    # Verify common tokens exist
    eth_tokens = balance_checker.TOKEN_ADDRESSES["ethereum"]
    assert "USDC" in eth_tokens
    assert "USDT" in eth_tokens
    assert "DAI" in eth_tokens
    assert "WETH" in eth_tokens

    base_tokens = balance_checker.TOKEN_ADDRESSES["base"]
    assert "USDC" in base_tokens
    assert "WETH" in base_tokens


def test_token_decimals_configured(balance_checker):
    """Test TOKEN_DECIMALS are properly configured."""
    assert balance_checker.TOKEN_DECIMALS["USDC"] == 6
    assert balance_checker.TOKEN_DECIMALS["USDT"] == 6
    assert balance_checker.TOKEN_DECIMALS["DAI"] == 18
    assert balance_checker.TOKEN_DECIMALS["ETH"] == 18
    assert balance_checker.TOKEN_DECIMALS["WETH"] == 18
    assert balance_checker.TOKEN_DECIMALS["WBTC"] == 8
