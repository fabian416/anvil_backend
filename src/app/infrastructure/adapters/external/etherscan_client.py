"""
Etherscan API Client for Address Labels and Transaction History.

Provides access to Etherscan's API for:
- Address labels (exchanges, contracts, scams)
- Transaction history
- Contract verification status

Used by:
- Transfer Workflow (safety checks)
- Transaction History Agent
- Security Auditor Agent

API Documentation: https://docs.etherscan.io/
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AddressType(str, Enum):
    """Types of addresses based on Etherscan labels."""

    EOA = "eoa"  # Externally Owned Account (regular wallet)
    CONTRACT = "contract"  # Smart Contract
    EXCHANGE = "exchange"  # Centralized Exchange
    DEX = "dex"  # Decentralized Exchange
    BRIDGE = "bridge"  # Cross-chain Bridge
    MIXER = "mixer"  # Mixer/Privacy Protocol (risky)
    SCAM = "scam"  # Known scam address
    PHISHING = "phishing"  # Phishing address
    TOKEN = "token"  # Token Contract
    NFT = "nft"  # NFT Contract
    DEFI = "defi"  # DeFi Protocol
    UNKNOWN = "unknown"


@dataclass
class AddressLabel:
    """Address label information from Etherscan."""

    address: str
    label: str | None
    name_tag: str | None
    address_type: AddressType
    is_verified: bool  # Contract verification status
    is_risky: bool  # Known risky address
    category: str | None  # e.g., "exchange", "defi", "gaming"
    metadata: dict | None = None


@dataclass
class TransactionInfo:
    """Basic transaction information."""

    tx_hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    value_wei: int
    gas_used: int
    is_error: bool
    function_name: str | None = None


class EtherscanClient:
    """
    Etherscan API V2 client for address labels and transaction history.

    Uses Etherscan API V2 unified endpoint that supports 60+ EVM chains
    with a single API key by specifying the chain ID.

    Supports multiple networks:
    - Ethereum Mainnet (chainid=1)
    - Base (chainid=8453)
    - Arbitrum (chainid=42161)
    - Optimism (chainid=10)
    - Polygon (chainid=137)

    Usage:
        client = EtherscanClient(api_key="your-key", network="base")
        label = await client.get_address_label("0x...")
        print(f"Address: {label.name_tag} ({label.address_type})")

    API V2 Documentation: https://docs.etherscan.io/etherscan-v2
    """

    # Etherscan API V2 unified endpoint
    API_V2_BASE_URL = "https://api.etherscan.io/v2/api"

    # Chain IDs for API V2
    CHAIN_IDS = {
        "ethereum": 1,
        "base": 8453,
        "arbitrum": 42161,
        "optimism": 10,
        "polygon": 137,
        "polygon_zkevm": 1101,
        "avalanche": 43114,
        "bsc": 56,
        "fantom": 250,
        "linea": 59144,
        "scroll": 534352,
        "zksync": 324,
        "blast": 81457,
    }

    # Legacy network-specific URLs (fallback)
    BASE_URLS = {
        "ethereum": "https://api.etherscan.io/api",
        "base": "https://api.basescan.org/api",
        "arbitrum": "https://api.arbiscan.io/api",
        "optimism": "https://api-optimistic.etherscan.io/api",
        "polygon": "https://api.polygonscan.com/api",
    }

    # Known label categories that indicate risk
    RISKY_CATEGORIES = {"mixer", "scam", "phishing", "exploit", "hacker"}

    # Known exchanges (fallback if API doesn't return label)
    KNOWN_EXCHANGES = {
        # Coinbase
        "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase",
        "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43": "Coinbase",
        "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Coinbase",
        # Binance
        "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": "Binance",
        "0xd551234ae421e3bcba99a0da6d736074f22192ff": "Binance",
        # Kraken
        "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": "Kraken",
        # Other major exchanges
        "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640": "Uniswap V3 USDC/ETH",
    }

    # Known DeFi protocols
    KNOWN_DEFI = {
        # Uniswap
        "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": "Uniswap Universal Router",
        "0x2626664c2603336e57b271c5c0b26f421741e481": "Uniswap V3 Router",
        # Aave
        "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2": "Aave V3 Pool",
        # Compound
        "0xc3d688b66703497daa19211eedff47f25384cdc3": "Compound V3 USDC",
        # Base-specific
        "0x6131b5fae19ea4f9d964eac0408e4408b66337b5": "Hyperliquid Bridge",
    }

    def __init__(
        self,
        api_key: str | None = None,
        network: str = "base",
        timeout: float = 10.0,
        use_v2_api: bool = True,
    ):
        """
        Initialize Etherscan client.

        Args:
            api_key: Etherscan API key (or set ETHERSCAN_API_KEY env var)
            network: Network to query (ethereum, base, arbitrum, etc.)
            timeout: Request timeout in seconds
            use_v2_api: Use Etherscan API V2 (unified endpoint with chain ID)
        """
        self._api_key = api_key or os.getenv("ETHERSCAN_API_KEY", "")
        self._network = network
        self._chain_id = self.CHAIN_IDS.get(network, 8453)  # Default to Base
        self._use_v2_api = use_v2_api

        # Use V2 API or legacy network-specific URL
        if use_v2_api:
            self._base_url = self.API_V2_BASE_URL
        else:
            self._base_url = self.BASE_URLS.get(network, self.BASE_URLS["ethereum"])

        self._client = httpx.AsyncClient(timeout=timeout)
        self._cache: dict[str, AddressLabel] = {}  # Simple in-memory cache

    def _build_params(self, params: dict) -> dict:
        """Build request params, adding chainid for V2 API."""
        if self._use_v2_api:
            params["chainid"] = self._chain_id
        params["apikey"] = self._api_key
        return params

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def get_address_label(
        self,
        address: str,
        use_cache: bool = True,
    ) -> AddressLabel:
        """
        Get label information for an address.

        Checks:
        1. Local cache
        2. Known addresses (exchanges, DeFi)
        3. Etherscan API (if API key available)

        Args:
            address: Ethereum address (0x...)
            use_cache: Whether to use cached results

        Returns:
            AddressLabel with label info
        """
        address_lower = address.lower()

        # Check cache first
        if use_cache and address_lower in self._cache:
            return self._cache[address_lower]

        # Check known addresses (fallback)
        label = self._check_known_addresses(address_lower)
        if label:
            self._cache[address_lower] = label
            return label

        # Try Etherscan API if key available
        if self._api_key:
            try:
                label = await self._fetch_address_label(address_lower)
                if label:
                    self._cache[address_lower] = label
                    return label
            except Exception as e:
                logger.warning(f"Etherscan API error for {address[:10]}...: {e}")

        # Return unknown label
        unknown_label = AddressLabel(
            address=address_lower,
            label=None,
            name_tag=None,
            address_type=AddressType.UNKNOWN,
            is_verified=False,
            is_risky=False,
            category=None,
        )
        self._cache[address_lower] = unknown_label
        return unknown_label

    async def get_transaction_count(
        self,
        address: str,
    ) -> int:
        """
        Get total transaction count for an address.

        Args:
            address: Ethereum address

        Returns:
            Number of transactions
        """
        if not self._api_key:
            return -1  # Unknown without API key

        try:
            params = self._build_params({
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": 1,  # Just get count, not full list
                "sort": "desc",
            })

            response = await self._client.get(self._base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "1":
                # Etherscan doesn't return total count directly
                # We'd need to paginate, so return estimate
                return len(data.get("result", []))
            return 0
        except Exception as e:
            logger.warning(f"Failed to get tx count for {address[:10]}...: {e}")
            return -1

    async def get_recent_interactions(
        self,
        from_address: str,
        to_address: str,
        limit: int = 10,
    ) -> list[TransactionInfo]:
        """
        Get recent transactions between two addresses.

        Useful for checking if sender has previously interacted with recipient.

        Args:
            from_address: Sender address
            to_address: Recipient address
            limit: Maximum transactions to return

        Returns:
            List of transactions between the addresses
        """
        if not self._api_key:
            return []

        try:
            params = self._build_params({
                "module": "account",
                "action": "txlist",
                "address": from_address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": 100,  # Get last 100 txs
                "sort": "desc",
            })

            response = await self._client.get(self._base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "1":
                return []

            # Filter for transactions to the target address
            interactions = []
            to_lower = to_address.lower()

            for tx in data.get("result", []):
                if tx.get("to", "").lower() == to_lower:
                    interactions.append(
                        TransactionInfo(
                            tx_hash=tx.get("hash", ""),
                            block_number=int(tx.get("blockNumber", 0)),
                            timestamp=datetime.fromtimestamp(
                                int(tx.get("timeStamp", 0)), tz=UTC
                            ),
                            from_address=tx.get("from", ""),
                            to_address=tx.get("to", ""),
                            value_wei=int(tx.get("value", 0)),
                            gas_used=int(tx.get("gasUsed", 0)),
                            is_error=tx.get("isError") == "1",
                            function_name=tx.get("functionName"),
                        )
                    )

                    if len(interactions) >= limit:
                        break

            return interactions
        except Exception as e:
            logger.warning(f"Failed to get interactions: {e}")
            return []

    async def is_contract_verified(self, address: str) -> bool:
        """
        Check if a contract is verified on Etherscan.

        Args:
            address: Contract address

        Returns:
            True if verified
        """
        if not self._api_key:
            return False

        try:
            params = self._build_params({
                "module": "contract",
                "action": "getabi",
                "address": address,
            })

            response = await self._client.get(self._base_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Status "1" means ABI found = verified
            return data.get("status") == "1"
        except Exception as e:
            logger.warning(f"Failed to check verification for {address[:10]}...: {e}")
            return False

    async def get_token_balance(
        self,
        wallet_address: str,
        contract_address: str,
        decimals: int = 6,
    ) -> tuple[int, float] | None:
        """
        Get ERC-20 token balance for a wallet address.

        Uses Etherscan API V2:
        GET /v2/api?chainid={chain_id}&module=account&action=tokenbalance
            &contractaddress={contract}&address={wallet}&tag=latest&apikey={key}

        Args:
            wallet_address: Wallet address to check
            contract_address: Token contract address (e.g., USDT, USDC)
            decimals: Token decimals (default 6 for USDT/USDC)

        Returns:
            Tuple of (raw_balance, formatted_balance) or None on error
            - raw_balance: Balance in smallest unit (e.g., 3000000 for 3 USDT)
            - formatted_balance: Human-readable balance (e.g., 3.0 USDT)

        Example:
            >>> client = EtherscanClient(network="ethereum")
            >>> raw, formatted = await client.get_token_balance(
            ...     wallet_address="0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B",
            ...     contract_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            ...     decimals=6,
            ... )
            >>> print(f"Balance: {formatted} USDT ({raw} raw)")
            Balance: 3.0 USDT (3000000 raw)
        """
        if not self._api_key:
            logger.warning("Etherscan API key not configured")
            return None

        try:
            params = self._build_params({
                "module": "account",
                "action": "tokenbalance",
                "contractaddress": contract_address,
                "address": wallet_address,
                "tag": "latest",
            })

            response = await self._client.get(self._base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "1" and data.get("result"):
                raw_balance = int(data["result"])
                formatted_balance = raw_balance / (10**decimals)

                logger.debug(
                    f"Token balance for {wallet_address[:10]}...: "
                    f"{formatted_balance} ({raw_balance} raw)"
                )

                return (raw_balance, formatted_balance)
            elif data.get("status") == "0":
                # Status "0" can mean error or zero balance
                message = data.get("message", "")
                if "balance" in message.lower() or "result" in message.lower():
                    # Likely zero balance
                    logger.debug(f"Zero token balance for {wallet_address[:10]}...")
                    return (0, 0.0)
                else:
                    logger.warning(
                        f"Etherscan API error for {wallet_address[:10]}...: {message}"
                    )
                    return None
            else:
                logger.warning(f"Unexpected Etherscan response: {data}")
                return None

        except httpx.TimeoutException:
            logger.warning(f"Etherscan API timeout for wallet {wallet_address[:10]}...")
            return None
        except ValueError as e:
            logger.error(f"Invalid balance value: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Etherscan API error for wallet {wallet_address[:10]}...: {e}"
            )
            return None

    def _check_known_addresses(self, address: str) -> AddressLabel | None:
        """Check if address is in known addresses list."""
        # Check exchanges
        if address in self.KNOWN_EXCHANGES:
            return AddressLabel(
                address=address,
                label=self.KNOWN_EXCHANGES[address],
                name_tag=self.KNOWN_EXCHANGES[address],
                address_type=AddressType.EXCHANGE,
                is_verified=True,
                is_risky=False,
                category="exchange",
            )

        # Check DeFi protocols
        if address in self.KNOWN_DEFI:
            return AddressLabel(
                address=address,
                label=self.KNOWN_DEFI[address],
                name_tag=self.KNOWN_DEFI[address],
                address_type=AddressType.DEFI,
                is_verified=True,
                is_risky=False,
                category="defi",
            )

        return None

    async def _fetch_address_label(self, address: str) -> AddressLabel | None:
        """
        Fetch address label from Etherscan API.

        Note: Etherscan's public API doesn't directly expose labels.
        This uses a combination of:
        1. Contract source verification check
        2. Token info if it's a token contract
        """
        is_verified = False
        name_tag = None
        address_type = AddressType.UNKNOWN

        # Check if it's a verified contract
        try:
            params = self._build_params({
                "module": "contract",
                "action": "getsourcecode",
                "address": address,
            })

            response = await self._client.get(self._base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "1" and data.get("result"):
                result = data["result"][0]
                source_code = result.get("SourceCode", "")
                contract_name = result.get("ContractName", "")

                if source_code and contract_name:
                    is_verified = True
                    name_tag = contract_name
                    address_type = AddressType.CONTRACT

                    # Try to categorize based on contract name
                    name_lower = contract_name.lower()
                    if any(
                        x in name_lower
                        for x in ["swap", "router", "pool", "uniswap", "sushi"]
                    ):
                        address_type = AddressType.DEX
                    elif any(x in name_lower for x in ["bridge", "portal", "gateway"]):
                        address_type = AddressType.BRIDGE
                    elif any(x in name_lower for x in ["token", "erc20", "coin"]):
                        address_type = AddressType.TOKEN
                    elif any(x in name_lower for x in ["nft", "erc721", "erc1155"]):
                        address_type = AddressType.NFT
                    elif any(
                        x in name_lower
                        for x in ["lending", "borrow", "aave", "compound"]
                    ):
                        address_type = AddressType.DEFI
        except Exception as e:
            logger.debug(f"Contract verification check failed: {e}")

        if name_tag:
            return AddressLabel(
                address=address,
                label=name_tag,
                name_tag=name_tag,
                address_type=address_type,
                is_verified=is_verified,
                is_risky=False,
                category=address_type.value,
            )

        return None
