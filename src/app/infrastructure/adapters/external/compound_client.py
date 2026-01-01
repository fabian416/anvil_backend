"""
Compound V3 (Comet) API Client.

Provides access to Compound V3 lending protocol:
- Market data (supply/borrow rates)
- User positions and health factors
- Protocol statistics
- Multi-chain support (Ethereum, Base, Arbitrum, Polygon)

API: Uses Compound's Comet smart contracts via RPC
Docs: https://docs.compound.finance/
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


# Compound V3 Comet deployments by chain
# Each chain can have multiple markets (USDC, WETH base assets)
COMPOUND_V3_MARKETS = {
    "ethereum": {
        "USDC": {
            "comet": "0xc3d688B66703497DAA19211EEdff47f25384cdc3",
            "base_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "base_symbol": "USDC",
            "decimals": 6,
        },
        "WETH": {
            "comet": "0xA17581A9E3356d9A858b789D68B4d866e593aE94",
            "base_token": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "base_symbol": "WETH",
            "decimals": 18,
        },
    },
    "base": {
        "USDC": {
            "comet": "0xb125E6687d4313864e53df431d5425969c15Eb2F",
            "base_token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "base_symbol": "USDC",
            "decimals": 6,
        },
        "WETH": {
            "comet": "0x46e6b214b524310239732D51387075E0e70970bf",
            "base_token": "0x4200000000000000000000000000000000000006",
            "base_symbol": "WETH",
            "decimals": 18,
        },
    },
    "arbitrum": {
        "USDC": {
            "comet": "0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf",
            "base_token": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "base_symbol": "USDC",
            "decimals": 6,
        },
        "WETH": {
            "comet": "0x6f7D514bB0C91fCb5a7d2b0B8e4FE4f0C0d4a1E2",
            "base_token": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            "base_symbol": "WETH",
            "decimals": 18,
        },
    },
    "polygon": {
        "USDC": {
            "comet": "0xF25212E676D1F7F89Cd72fFEe66158f541246445",
            "base_token": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "base_symbol": "USDC",
            "decimals": 6,
        },
    },
}

# RPC endpoints
CHAIN_RPC = {
    "ethereum": "https://eth.llamarpc.com",
    "base": "https://mainnet.base.org",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "polygon": "https://polygon-rpc.com",
}

# Comet ABI for rate functions (minimal)
# getSupplyRate(utilization) -> uint64
# getBorrowRate(utilization) -> uint64
# getUtilization() -> uint
COMET_ABI_SUPPLY_RATE = "0xd955759d"  # getSupplyRate(uint)
COMET_ABI_BORROW_RATE = "0x9fa83b5a"  # getBorrowRate(uint)
COMET_ABI_UTILIZATION = "0x7eb71131"  # getUtilization()
COMET_ABI_BASE_TOKEN = "0xc55dae63"  # baseToken()
COMET_ABI_TOTAL_SUPPLY = "0x18160ddd"  # totalSupply()
COMET_ABI_TOTAL_BORROW = "0x8285ef40"  # totalBorrow()


@dataclass
class CompoundMarket:
    """Compound V3 market data."""

    chain: str
    base_asset: str  # USDC, WETH
    comet_address: str
    supply_apy: float  # Annual percentage yield for supply
    borrow_apy: float  # Annual percentage yield for borrow
    utilization: float  # Utilization rate (0-1)
    total_supply: float  # Total supplied in base asset
    total_borrow: float  # Total borrowed in base asset
    supply_apy_base: float  # Base APY without rewards
    supply_apy_reward: float  # COMP reward APY
    borrow_apy_base: float  # Base APY without rewards
    borrow_apy_reward: float  # COMP reward APY


@dataclass
class CompoundPosition:
    """User position in Compound V3."""

    chain: str
    base_asset: str
    comet_address: str
    user_address: str
    supplied: float
    borrowed: float
    collateral_usd: float
    health_factor: float
    is_liquidatable: bool


class CompoundClient:
    """
    Compound V3 (Comet) API client.

    Features:
    - Real-time supply/borrow rates from on-chain
    - Multi-chain support (Ethereum, Base, Arbitrum, Polygon)
    - Multiple markets per chain (USDC, WETH)
    - User position tracking

    Note: Uses direct RPC calls to Comet contracts for accurate data.
    """

    # Seconds per year for APY calculation
    SECONDS_PER_YEAR = 31536000
    # Rate scale (1e18)
    RATE_SCALE = 10**18

    def __init__(self, timeout: int = 30):
        """
        Initialize Compound V3 client.

        Args:
            timeout: HTTP request timeout in seconds
        """
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def get_market(
        self,
        asset: str = "USDC",
        chain: str = "ethereum",
    ) -> Optional[CompoundMarket]:
        """
        Get market data for a specific asset on a chain.

        Args:
            asset: Base asset (USDC, WETH)
            chain: Blockchain (ethereum, base, arbitrum, polygon)

        Returns:
            CompoundMarket with current rates and stats
        """
        chain_markets = COMPOUND_V3_MARKETS.get(chain.lower())
        if not chain_markets:
            logger.warning(f"Compound V3 not deployed on {chain}")
            return None

        market_info = chain_markets.get(asset.upper())
        if not market_info:
            logger.warning(f"No {asset} market on Compound V3 {chain}")
            return None

        comet = market_info["comet"]
        decimals = market_info["decimals"]
        rpc_url = CHAIN_RPC.get(chain.lower())

        if not rpc_url:
            return None

        try:
            # Fetch utilization
            utilization = await self._call_contract(
                rpc_url, comet, COMET_ABI_UTILIZATION, []
            )
            utilization_float = int(utilization, 16) / self.RATE_SCALE if utilization else 0

            # Fetch supply rate (per second)
            supply_rate_hex = await self._call_contract(
                rpc_url, comet, COMET_ABI_SUPPLY_RATE, [utilization]
            )
            supply_rate = int(supply_rate_hex, 16) if supply_rate_hex else 0

            # Fetch borrow rate (per second)
            borrow_rate_hex = await self._call_contract(
                rpc_url, comet, COMET_ABI_BORROW_RATE, [utilization]
            )
            borrow_rate = int(borrow_rate_hex, 16) if borrow_rate_hex else 0

            # Fetch total supply
            total_supply_hex = await self._call_contract(
                rpc_url, comet, COMET_ABI_TOTAL_SUPPLY, []
            )
            total_supply = int(total_supply_hex, 16) / (10**decimals) if total_supply_hex else 0

            # Fetch total borrow
            total_borrow_hex = await self._call_contract(
                rpc_url, comet, COMET_ABI_TOTAL_BORROW, []
            )
            total_borrow = int(total_borrow_hex, 16) / (10**decimals) if total_borrow_hex else 0

            # Convert per-second rates to APY
            # APY = (1 + rate_per_second)^seconds_per_year - 1
            # Simplified: APY ≈ rate_per_second * seconds_per_year (for small rates)
            supply_apy = (supply_rate / self.RATE_SCALE) * self.SECONDS_PER_YEAR * 100
            borrow_apy = (borrow_rate / self.RATE_SCALE) * self.SECONDS_PER_YEAR * 100

            return CompoundMarket(
                chain=chain,
                base_asset=asset.upper(),
                comet_address=comet,
                supply_apy=supply_apy,
                borrow_apy=borrow_apy,
                utilization=utilization_float,
                total_supply=total_supply,
                total_borrow=total_borrow,
                supply_apy_base=supply_apy,
                supply_apy_reward=0.0,  # TODO: Fetch COMP rewards
                borrow_apy_base=borrow_apy,
                borrow_apy_reward=0.0,  # TODO: Fetch COMP rewards
            )

        except Exception as e:
            logger.error(f"Error fetching Compound market {asset} on {chain}: {e}")
            return None

    async def get_markets(
        self,
        chain: str = "ethereum",
    ) -> list[CompoundMarket]:
        """
        Get all markets on a specific chain.

        Args:
            chain: Blockchain

        Returns:
            List of CompoundMarket objects
        """
        chain_markets = COMPOUND_V3_MARKETS.get(chain.lower(), {})
        markets = []

        for asset in chain_markets.keys():
            market = await self.get_market(asset=asset, chain=chain)
            if market:
                markets.append(market)

        return markets

    async def get_all_markets(self) -> list[CompoundMarket]:
        """
        Get all Compound V3 markets across all chains.

        Returns:
            List of CompoundMarket objects from all chains
        """
        all_markets = []

        for chain in COMPOUND_V3_MARKETS.keys():
            chain_markets = await self.get_markets(chain=chain)
            all_markets.extend(chain_markets)

        return all_markets

    async def get_user_position(
        self,
        user_address: str,
        asset: str = "USDC",
        chain: str = "ethereum",
    ) -> Optional[CompoundPosition]:
        """
        Get user's position in a specific market.

        Args:
            user_address: User's wallet address
            asset: Base asset
            chain: Blockchain

        Returns:
            CompoundPosition with user's supply/borrow info
        """
        # TODO: Implement user position fetching via RPC
        # Requires calling balanceOf(user) and borrowBalanceOf(user)
        logger.warning("get_user_position not yet implemented - returning None")
        return None

    async def _call_contract(
        self,
        rpc_url: str,
        contract: str,
        method_signature: str,
        params: list,
    ) -> Optional[str]:
        """
        Make an eth_call to a contract.

        Args:
            rpc_url: RPC endpoint URL
            contract: Contract address
            method_signature: Function selector (4 bytes hex)
            params: Parameters to encode (optional)

        Returns:
            Hex-encoded result or None on error
        """
        # Build call data
        data = method_signature
        for param in params:
            if isinstance(param, str) and param.startswith("0x"):
                # Already hex-encoded
                data += param[2:].zfill(64)
            elif isinstance(param, int):
                data += hex(param)[2:].zfill(64)

        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [
                {
                    "to": contract,
                    "data": data,
                },
                "latest",
            ],
            "id": 1,
        }

        try:
            response = await self._client.post(rpc_url, json=payload)
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                logger.error(f"RPC error: {result['error']}")
                return None

            return result.get("result")

        except Exception as e:
            logger.error(f"RPC call failed: {e}")
            return None

    @staticmethod
    def get_supported_chains() -> list[str]:
        """Get list of supported chains."""
        return list(COMPOUND_V3_MARKETS.keys())

    @staticmethod
    def get_supported_assets(chain: str) -> list[str]:
        """Get supported assets on a chain."""
        return list(COMPOUND_V3_MARKETS.get(chain.lower(), {}).keys())
