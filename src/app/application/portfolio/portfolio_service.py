"""
Portfolio Service.

Application service for managing user portfolio calculations and snapshots.
Provides functionality to:
- Calculate current portfolio value for a wallet
- Create portfolio snapshots
- Retrieve portfolio history
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.domain.portfolio.entities.portfolio_snapshot import (
    PortfolioSnapshot,
    TokenHolding,
    TokenHoldingId,
)
from app.domain.entities.wallet import Wallet, WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.portfolio.ports.portfolio.portfolio_repository import PortfolioRepository
from app.domain.ports.wallet.wallet_repository import WalletRepository

logger = logging.getLogger(__name__)


# Common ERC-20 token configurations
TOKEN_CONFIGS: dict[str, dict[str, Any]] = {
    # Stablecoins
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {
        "symbol": "USDC",
        "name": "USD Coin",
        "decimals": 6,
    },
    "0xdac17f958d2ee523a2206206994597c13d831ec7": {
        "symbol": "USDT",
        "name": "Tether USD",
        "decimals": 6,
    },
    "0x6b175474e89094c44da98b954eedeac495271d0f": {
        "symbol": "DAI",
        "name": "Dai Stablecoin",
        "decimals": 18,
    },
    # Wrapped tokens
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {
        "symbol": "WETH",
        "name": "Wrapped Ether",
        "decimals": 18,
    },
    "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": {
        "symbol": "WBTC",
        "name": "Wrapped BTC",
        "decimals": 8,
    },
    # DeFi tokens
    "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": {
        "symbol": "UNI",
        "name": "Uniswap",
        "decimals": 18,
    },
    "0x514910771af9ca656af840dff83e8264ecf986ca": {
        "symbol": "LINK",
        "name": "Chainlink",
        "decimals": 18,
    },
    "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9": {
        "symbol": "AAVE",
        "name": "Aave",
        "decimals": 18,
    },
}

# Base chain tokens
BASE_TOKEN_CONFIGS: dict[str, dict[str, Any]] = {
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": {
        "symbol": "USDC",
        "name": "USD Coin",
        "decimals": 6,
    },
    "0x4200000000000000000000000000000000000006": {
        "symbol": "WETH",
        "name": "Wrapped Ether",
        "decimals": 18,
    },
}


@dataclass
class PortfolioDTO:
    """Data transfer object for portfolio data."""

    wallet_address: str
    chain: str
    total_usd: float
    native_balance: float
    native_usd_value: float | None
    native_symbol: str
    tokens: list[dict[str, Any]]
    captured_at: str
    has_value: bool


@dataclass
class TokenBalanceDTO:
    """Data transfer object for token balance."""

    token_address: str | None
    symbol: str
    name: str
    decimals: int
    amount: float
    usd_value: float | None
    usd_price: float | None
    percentage: float


class PortfolioService:
    """
    Service for calculating and managing user portfolios.

    This service:
    1. Fetches on-chain balances via RPC
    2. Resolves USD prices via external APIs
    3. Creates and stores portfolio snapshots
    4. Provides portfolio retrieval for users
    """

    # RPC endpoints by chain
    RPC_ENDPOINTS: dict[ChainType, str] = {
        ChainType.ETHEREUM: "https://eth.llamarpc.com",
        ChainType.BASE: "https://mainnet.base.org",
        ChainType.ARBITRUM: "https://arb1.arbitrum.io/rpc",
        ChainType.POLYGON: "https://polygon-rpc.com",
        ChainType.OPTIMISM: "https://mainnet.optimism.io",
    }

    # Testnet RPC endpoints - using reliable public endpoints
    # For production, consider using Alchemy/Infura with API keys
    TESTNET_RPC_ENDPOINTS: dict[ChainType, str] = {
        ChainType.ETHEREUM: "https://ethereum-sepolia-rpc.publicnode.com",  # More reliable than rpc.sepolia.org
        ChainType.BASE: "https://sepolia.base.org",
    }

    def __init__(
        self,
        portfolio_repository: PortfolioRepository,
        wallet_repository: WalletRepository,
        *,
        use_testnet: bool = False,
        http_timeout: int = 10,  # Reduced from 30s to fail faster
    ):
        """
        Initialize the portfolio service.

        Args:
            portfolio_repository: Repository for portfolio persistence.
            wallet_repository: Repository for wallet lookups.
            use_testnet: Whether to use testnet RPC endpoints.
            http_timeout: HTTP timeout for RPC calls.
        """
        self._portfolio_repo = portfolio_repository
        self._wallet_repo = wallet_repository
        self._use_testnet = use_testnet
        self._http_timeout = http_timeout
        self._rpc_endpoints = (
            self.TESTNET_RPC_ENDPOINTS if use_testnet else self.RPC_ENDPOINTS
        )

    def _get_rpc_url(self, chain: ChainType) -> str | None:
        """Get RPC URL for a chain."""
        return self._rpc_endpoints.get(chain)

    async def _fetch_native_balance(
        self,
        rpc_url: str,
        address: str,
    ) -> Decimal:
        """
        Fetch native token balance via RPC.

        Args:
            rpc_url: RPC endpoint URL.
            address: Wallet address.

        Returns:
            Balance in token units (not wei).
        """
        import aiohttp

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getBalance",
            "params": [address, "latest"],
        }

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    rpc_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._http_timeout),
                ) as response,
            ):
                if response.status != 200:
                    logger.warning(f"RPC request failed: {response.status}")
                    return Decimal("0")

                data = await response.json()

                if "error" in data:
                    logger.warning(f"RPC error: {data['error']}")
                    return Decimal("0")

                result = data.get("result", "0x0")
                balance_wei = int(result, 16)
                return Decimal(balance_wei) / Decimal(10**18)

        except Exception as e:
            logger.error(f"Error fetching native balance from {rpc_url}: {type(e).__name__}: {e}")
            return Decimal("0")

    async def _fetch_token_balance(
        self,
        rpc_url: str,
        wallet_address: str,
        token_address: str,
        decimals: int = 18,
    ) -> Decimal:
        """
        Fetch ERC-20 token balance via RPC.

        Args:
            rpc_url: RPC endpoint URL.
            wallet_address: Wallet address.
            token_address: Token contract address.
            decimals: Token decimals.

        Returns:
            Balance in token units.
        """
        import aiohttp

        # balanceOf(address) function signature
        data = f"0x70a08231000000000000000000000000{wallet_address[2:].lower()}"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_call",
            "params": [{"to": token_address, "data": data}, "latest"],
        }

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    rpc_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._http_timeout),
                ) as response,
            ):
                if response.status != 200:
                    return Decimal("0")

                result_data = await response.json()

                if "error" in result_data:
                    return Decimal("0")

                result = result_data.get("result", "0x0")
                if result == "0x" or result == "0x0":
                    return Decimal("0")

                balance_raw = int(result, 16)
                return Decimal(balance_raw) / Decimal(10**decimals)

        except Exception as e:
            logger.debug(f"Error fetching token balance for {token_address} from {rpc_url}: {type(e).__name__}: {e}")
            return Decimal("0")

    async def _fetch_eth_price(self) -> Decimal | None:
        """Fetch ETH price in USD from DeFiLlama."""
        import aiohttp

        try:
            url = "https://coins.llama.fi/prices/current/coingecko:ethereum"
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self._http_timeout),
                ) as response,
            ):
                if response.status != 200:
                    return None

                data = await response.json()
                coins = data.get("coins", {})
                eth_data = coins.get("coingecko:ethereum", {})
                price = eth_data.get("price")

                if price is not None:
                    return Decimal(str(price))
                return None

        except Exception as e:
            logger.error(f"Error fetching ETH price: {e}")
            return None

    async def _fetch_token_price(
        self, chain: str, token_address: str
    ) -> Decimal | None:
        """Fetch token price in USD from DeFiLlama."""
        import aiohttp

        try:
            coin_id = f"{chain}:{token_address}"
            url = f"https://coins.llama.fi/prices/current/{coin_id}"

            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self._http_timeout),
                ) as response,
            ):
                if response.status != 200:
                    return None

                data = await response.json()
                coins = data.get("coins", {})
                token_data = coins.get(coin_id, {})
                price = token_data.get("price")

                if price is not None:
                    return Decimal(str(price))
                return None

        except Exception as e:
            logger.debug(f"Error fetching token price: {e}")
            return None

    async def get_current_portfolio(
        self,
        wallet_id: WalletId,
        chain: ChainType | None = None,
        *,
        save_snapshot: bool = False,
    ) -> PortfolioDTO | None:
        """
        Calculate the current portfolio for a wallet.

        This fetches on-chain balances and USD prices in real-time.

        Args:
            wallet_id: The wallet's database ID.
            chain: Optional chain to calculate for (defaults to wallet's default chain).
            save_snapshot: Whether to save a snapshot to the database.

        Returns:
            PortfolioDTO with current portfolio data, or None if wallet not found.
        """
        # Get wallet
        wallet = await self._wallet_repo.get_by_id(wallet_id)
        if not wallet:
            logger.warning(f"Wallet {wallet_id.value} not found")
            return None

        target_chain = chain or wallet.default_chain
        rpc_url = self._get_rpc_url(target_chain)

        if not rpc_url:
            logger.warning(f"No RPC endpoint for chain {target_chain.value}")
            return None

        # Fetch native balance
        native_balance = await self._fetch_native_balance(rpc_url, wallet.address)

        # Fetch ETH price
        eth_price = await self._fetch_eth_price()
        native_usd_value = float(native_balance * eth_price) if eth_price else None

        # Get token configs for this chain
        token_configs = (
            BASE_TOKEN_CONFIGS if target_chain == ChainType.BASE else TOKEN_CONFIGS
        )

        # Fetch token balances
        tokens: list[dict[str, Any]] = []
        total_usd = native_usd_value or 0.0

        for token_address, config in token_configs.items():
            balance = await self._fetch_token_balance(
                rpc_url,
                wallet.address,
                token_address,
                config["decimals"],
            )

            if balance > 0:
                # Get token price
                chain_name = (
                    "ethereum" if target_chain == ChainType.ETHEREUM else "base"
                )
                token_price = await self._fetch_token_price(chain_name, token_address)

                usd_value = float(balance * token_price) if token_price else None

                tokens.append({
                    "token_address": token_address,
                    "symbol": config["symbol"],
                    "name": config["name"],
                    "decimals": config["decimals"],
                    "amount": float(balance),
                    "usd_value": usd_value,
                    "usd_price": float(token_price) if token_price else None,
                    "percentage": 0.0,  # Calculated below
                })

                if usd_value:
                    total_usd += usd_value

        # Calculate percentages
        if total_usd > 0:
            native_percentage = (
                (native_usd_value / total_usd * 100) if native_usd_value else 0
            )
            for token in tokens:
                if token["usd_value"]:
                    token["percentage"] = token["usd_value"] / total_usd * 100

        # Get native symbol
        native_symbols = {
            ChainType.ETHEREUM: "ETH",
            ChainType.BASE: "ETH",
            ChainType.ARBITRUM: "ETH",
            ChainType.OPTIMISM: "ETH",
            ChainType.POLYGON: "MATIC",
        }
        native_symbol = native_symbols.get(target_chain, "ETH")

        # Create snapshot if requested
        if save_snapshot:
            snapshot = await self._create_snapshot(
                wallet=wallet,
                chain=target_chain,
                native_balance=native_balance,
                native_usd_value=Decimal(str(native_usd_value))
                if native_usd_value
                else None,
                tokens=tokens,
            )
            logger.info(
                f"Created portfolio snapshot {snapshot.id_.value} for wallet {wallet.address}"
            )

        return PortfolioDTO(
            wallet_address=wallet.address,
            chain=target_chain.value,
            total_usd=total_usd,
            native_balance=float(native_balance),
            native_usd_value=native_usd_value,
            native_symbol=native_symbol,
            tokens=tokens,
            captured_at=datetime.now(UTC).isoformat(),
            has_value=total_usd > 0,
        )

    async def get_portfolio_by_address(
        self,
        address: str,
        chain: ChainType = ChainType.BASE,
        *,
        save_snapshot: bool = False,
    ) -> PortfolioDTO | None:
        """
        Calculate portfolio for a wallet address.

        This is a convenience method that doesn't require a wallet_id.

        Args:
            address: Wallet address (0x...).
            chain: Blockchain to calculate for.
            save_snapshot: Whether to save a snapshot.

        Returns:
            PortfolioDTO or None.
        """
        # Try to find wallet by address
        wallet = await self._wallet_repo.get_by_address(address)

        if wallet:
            return await self.get_current_portfolio(
                wallet.id_, chain, save_snapshot=save_snapshot
            )

        # Calculate without wallet (no persistence)
        rpc_url = self._get_rpc_url(chain)
        if not rpc_url:
            return None

        # Fetch native balance
        native_balance = await self._fetch_native_balance(rpc_url, address)
        eth_price = await self._fetch_eth_price()
        native_usd_value = float(native_balance * eth_price) if eth_price else None

        # Get token configs
        token_configs = BASE_TOKEN_CONFIGS if chain == ChainType.BASE else TOKEN_CONFIGS

        tokens: list[dict[str, Any]] = []
        total_usd = native_usd_value or 0.0

        for token_address, config in token_configs.items():
            balance = await self._fetch_token_balance(
                rpc_url, address, token_address, config["decimals"]
            )

            if balance > 0:
                chain_name = "ethereum" if chain == ChainType.ETHEREUM else "base"
                token_price = await self._fetch_token_price(chain_name, token_address)
                usd_value = float(balance * token_price) if token_price else None

                tokens.append({
                    "token_address": token_address,
                    "symbol": config["symbol"],
                    "name": config["name"],
                    "decimals": config["decimals"],
                    "amount": float(balance),
                    "usd_value": usd_value,
                    "usd_price": float(token_price) if token_price else None,
                    "percentage": 0.0,
                })

                if usd_value:
                    total_usd += usd_value

        # Calculate percentages
        if total_usd > 0:
            for token in tokens:
                if token["usd_value"]:
                    token["percentage"] = token["usd_value"] / total_usd * 100

        native_symbols = {
            ChainType.ETHEREUM: "ETH",
            ChainType.BASE: "ETH",
            ChainType.ARBITRUM: "ETH",
            ChainType.OPTIMISM: "ETH",
            ChainType.POLYGON: "MATIC",
        }

        return PortfolioDTO(
            wallet_address=address,
            chain=chain.value,
            total_usd=total_usd,
            native_balance=float(native_balance),
            native_usd_value=native_usd_value,
            native_symbol=native_symbols.get(chain, "ETH"),
            tokens=tokens,
            captured_at=datetime.now(UTC).isoformat(),
            has_value=total_usd > 0,
        )

    async def _create_snapshot(
        self,
        wallet: Wallet,
        chain: ChainType,
        native_balance: Decimal,
        native_usd_value: Decimal | None,
        tokens: list[dict[str, Any]],
    ) -> PortfolioSnapshot:
        """Create and save a portfolio snapshot."""
        snapshot = PortfolioSnapshot.create(
            wallet_id=wallet.id_,
            chain=chain,
            native_balance=native_balance,
            native_usd_value=native_usd_value,
        )

        # Add token holdings
        for token_data in tokens:
            holding = TokenHolding(
                id_=TokenHoldingId(0),
                snapshot_id=snapshot.id_,
                token_address=token_data["token_address"],
                symbol=token_data["symbol"],
                name=token_data["name"],
                decimals=token_data["decimals"],
                amount=Decimal(str(token_data["amount"])),
                usd_value=(
                    Decimal(str(token_data["usd_value"]))
                    if token_data["usd_value"]
                    else None
                ),
                usd_price=(
                    Decimal(str(token_data["usd_price"]))
                    if token_data["usd_price"]
                    else None
                ),
                percentage=token_data["percentage"],
            )
            snapshot.add_holding(holding)

        # Save to database
        return await self._portfolio_repo.save(snapshot)

    async def snapshot_portfolio(self, wallet_id: WalletId) -> PortfolioSnapshot | None:
        """
        Create a portfolio snapshot for a wallet.

        This is called automatically when transactions are confirmed.

        Args:
            wallet_id: The wallet's database ID.

        Returns:
            The created snapshot, or None if failed.
        """
        portfolio_dto = await self.get_current_portfolio(wallet_id, save_snapshot=True)

        if portfolio_dto:
            # Return the latest snapshot
            wallet = await self._wallet_repo.get_by_id(wallet_id)
            if wallet:
                return await self._portfolio_repo.get_latest_by_wallet(wallet_id)

        return None

    async def get_latest_portfolio(
        self,
        wallet_id: WalletId,
        *,
        max_age_seconds: int = 300,
    ) -> PortfolioDTO | None:
        """
        Get the latest portfolio snapshot if fresh, otherwise calculate new.

        Args:
            wallet_id: The wallet's database ID.
            max_age_seconds: Maximum age of snapshot to return (default 5 min).

        Returns:
            PortfolioDTO from snapshot or fresh calculation.
        """
        # Check for recent snapshot
        latest = await self._portfolio_repo.get_latest_by_wallet(wallet_id)

        if latest:
            age = (datetime.now(UTC) - latest.captured_at).total_seconds()
            if age < max_age_seconds:
                # Return from snapshot
                wallet = await self._wallet_repo.get_by_id(wallet_id)
                if not wallet:
                    return None

                tokens = [
                    {
                        "token_address": h.token_address,
                        "symbol": h.symbol,
                        "name": h.name,
                        "decimals": h.decimals,
                        "amount": float(h.amount),
                        "usd_value": float(h.usd_value) if h.usd_value else None,
                        "usd_price": float(h.usd_price) if h.usd_price else None,
                        "percentage": h.percentage,
                    }
                    for h in latest.holdings
                ]

                native_symbols = {
                    ChainType.ETHEREUM: "ETH",
                    ChainType.BASE: "ETH",
                    ChainType.ARBITRUM: "ETH",
                    ChainType.OPTIMISM: "ETH",
                    ChainType.POLYGON: "MATIC",
                }

                return PortfolioDTO(
                    wallet_address=wallet.address,
                    chain=latest.chain.value,
                    total_usd=float(latest.total_usd),
                    native_balance=float(latest.native_balance),
                    native_usd_value=(
                        float(latest.native_usd_value)
                        if latest.native_usd_value
                        else None
                    ),
                    native_symbol=native_symbols.get(latest.chain, "ETH"),
                    tokens=tokens,
                    captured_at=latest.captured_at.isoformat(),
                    has_value=latest.has_value,
                )

        # Calculate fresh
        return await self.get_current_portfolio(wallet_id, save_snapshot=True)
