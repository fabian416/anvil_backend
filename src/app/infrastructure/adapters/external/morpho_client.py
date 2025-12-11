"""
Morpho Protocol API Client.

Provides access to Morpho Protocol via GraphQL subgraph:
- MetaMorpho vaults
- Morpho Blue markets
- User positions
- APY data

Subgraph: https://api.thegraph.com/subgraphs/name/morpho-association/morpho-blue-mainnet
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class MorphoVaultData:
    """Raw vault data from subgraph."""

    id: str
    name: str
    symbol: str
    asset_address: str
    asset_symbol: str
    asset_decimals: int
    total_assets: str
    total_supply: str
    performance_fee: str
    curator: str | None
    guardian: str | None
    allocations: list[dict]


@dataclass
class MorphoMarketData:
    """Raw market data from subgraph."""

    id: str
    collateral_address: str
    collateral_symbol: str
    loan_address: str
    loan_symbol: str
    lltv: str
    oracle: str | None
    irm: str | None
    total_supply_assets: str
    total_borrow_assets: str
    supply_rate: str
    borrow_rate: str


@dataclass
class MorphoPositionData:
    """Raw position data from subgraph."""

    vault_id: str
    vault_name: str
    asset_symbol: str
    shares: str
    assets: str


class MorphoClient:
    """
    Morpho Protocol API client using GraphQL subgraph.

    Features:
    - MetaMorpho vault discovery
    - Morpho Blue market data
    - User position tracking
    - APY data retrieval
    """

    # Subgraph URL (Morpho Blue mainnet)
    SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/morpho-association/morpho-blue-mainnet"

    # Backup API for APY data
    MORPHO_API_URL = "https://blue-api.morpho.org"

    def __init__(
        self,
        subgraph_url: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize Morpho client.

        Args:
            subgraph_url: Custom subgraph URL (optional)
            timeout: Request timeout in seconds
        """
        self._subgraph_url = subgraph_url or self.SUBGRAPH_URL
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

    async def get_vaults(self, first: int = 100) -> list[MorphoVaultData]:
        """
        Get all MetaMorpho vaults.

        Args:
            first: Number of vaults to fetch

        Returns:
            List of vault data
        """
        query = """
        query GetVaults($first: Int!) {
            metaMorphos(first: $first, orderBy: totalAssets, orderDirection: desc) {
                id
                name
                symbol
                asset {
                    address
                    symbol
                    decimals
                }
                totalAssets
                totalShares
                fee
                curator {
                    id
                }
                guardian {
                    id
                }
                allocators {
                    id
                }
            }
        }
        """

        try:
            response = await self._client.post(
                self._subgraph_url,
                json={"query": query, "variables": {"first": first}},
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []

            vaults = data.get("data", {}).get("metaMorphos", [])
            return [self._parse_vault(v) for v in vaults]

        except Exception as e:
            logger.error(f"Error fetching Morpho vaults: {e}")
            raise

    async def get_vault(self, vault_address: str) -> MorphoVaultData | None:
        """
        Get specific vault details.

        Args:
            vault_address: Vault contract address

        Returns:
            Vault data or None if not found
        """
        query = """
        query GetVault($id: ID!) {
            metaMorpho(id: $id) {
                id
                name
                symbol
                asset {
                    address
                    symbol
                    decimals
                }
                totalAssets
                totalShares
                fee
                curator {
                    id
                }
                guardian {
                    id
                }
            }
        }
        """

        try:
            response = await self._client.post(
                self._subgraph_url,
                json={
                    "query": query,
                    "variables": {"id": vault_address.lower()},
                },
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return None

            vault = data.get("data", {}).get("metaMorpho")
            if vault:
                return self._parse_vault(vault)
            return None

        except Exception as e:
            logger.error(f"Error fetching vault {vault_address}: {e}")
            raise

    async def get_markets(self, first: int = 100) -> list[MorphoMarketData]:
        """
        Get Morpho Blue markets.

        Args:
            first: Number of markets to fetch

        Returns:
            List of market data
        """
        query = """
        query GetMarkets($first: Int!) {
            markets(first: $first, orderBy: totalSupplyAssets, orderDirection: desc) {
                id
                lltv
                collateralAsset {
                    address
                    symbol
                }
                loanAsset {
                    address
                    symbol
                }
                oracle {
                    address
                }
                irm {
                    address
                }
                totalSupplyAssets
                totalBorrowAssets
                state {
                    supplyAPY
                    borrowAPY
                }
            }
        }
        """

        try:
            response = await self._client.post(
                self._subgraph_url,
                json={"query": query, "variables": {"first": first}},
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []

            markets = data.get("data", {}).get("markets", [])
            return [self._parse_market(m) for m in markets]

        except Exception as e:
            logger.error(f"Error fetching Morpho markets: {e}")
            raise

    async def get_user_positions(
        self, user_address: str, first: int = 50
    ) -> list[MorphoPositionData]:
        """
        Get user vault positions.

        Args:
            user_address: User wallet address
            first: Number of positions to fetch

        Returns:
            List of position data
        """
        query = """
        query GetPositions($user: String!, $first: Int!) {
            metaMorphoDeposits(
                where: { user: $user }
                first: $first
                orderBy: assets
                orderDirection: desc
            ) {
                metaMorpho {
                    id
                    name
                    asset {
                        symbol
                    }
                }
                shares
                assets
            }
        }
        """

        try:
            response = await self._client.post(
                self._subgraph_url,
                json={
                    "query": query,
                    "variables": {
                        "user": user_address.lower(),
                        "first": first,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []

            deposits = data.get("data", {}).get("metaMorphoDeposits", [])
            return [self._parse_position(p) for p in deposits]

        except Exception as e:
            logger.error(f"Error fetching positions for {user_address}: {e}")
            raise

    async def get_vault_apy(self, vault_address: str) -> dict[str, Any]:
        """
        Get vault APY data.

        Uses Morpho API for APY data (more accurate than subgraph).

        Args:
            vault_address: Vault contract address

        Returns:
            APY data dictionary
        """
        # Try Morpho API first for more accurate APY
        try:
            response = await self._client.get(
                f"{self.MORPHO_API_URL}/vaults",
                params={"chainId": 1},  # Ethereum mainnet
            )
            
            if response.status_code == 200:
                vaults = response.json()
                for vault in vaults:
                    if vault.get("address", "").lower() == vault_address.lower():
                        return {
                            "base_apy": vault.get("apy", {}).get("netApy", "0"),
                            "supply_apy": vault.get("apy", {}).get("supplyApy", "0"),
                            "reward_apy": vault.get("apy", {}).get("rewardApy", "0"),
                            "fee": vault.get("fee", "0"),
                        }
        except Exception as e:
            logger.warning(f"Failed to get APY from Morpho API: {e}")

        # Fallback: return estimated APY
        return {
            "base_apy": "0",
            "supply_apy": "0",
            "reward_apy": "0",
            "fee": "0",
        }

    def _parse_vault(self, raw: dict) -> MorphoVaultData:
        """Parse raw vault data from subgraph."""
        asset = raw.get("asset", {})
        return MorphoVaultData(
            id=raw.get("id", ""),
            name=raw.get("name", "Unknown"),
            symbol=raw.get("symbol", ""),
            asset_address=asset.get("address", ""),
            asset_symbol=asset.get("symbol", ""),
            asset_decimals=int(asset.get("decimals", 18)),
            total_assets=raw.get("totalAssets", "0"),
            total_supply=raw.get("totalShares", "0"),
            performance_fee=raw.get("fee", "0"),
            curator=raw.get("curator", {}).get("id") if raw.get("curator") else None,
            guardian=raw.get("guardian", {}).get("id") if raw.get("guardian") else None,
            allocations=[],  # Would need separate query
        )

    def _parse_market(self, raw: dict) -> MorphoMarketData:
        """Parse raw market data from subgraph."""
        collateral = raw.get("collateralAsset", {})
        loan = raw.get("loanAsset", {})
        state = raw.get("state", {})
        
        return MorphoMarketData(
            id=raw.get("id", ""),
            collateral_address=collateral.get("address", ""),
            collateral_symbol=collateral.get("symbol", ""),
            loan_address=loan.get("address", ""),
            loan_symbol=loan.get("symbol", ""),
            lltv=raw.get("lltv", "0"),
            oracle=raw.get("oracle", {}).get("address") if raw.get("oracle") else None,
            irm=raw.get("irm", {}).get("address") if raw.get("irm") else None,
            total_supply_assets=raw.get("totalSupplyAssets", "0"),
            total_borrow_assets=raw.get("totalBorrowAssets", "0"),
            supply_rate=state.get("supplyAPY", "0") if state else "0",
            borrow_rate=state.get("borrowAPY", "0") if state else "0",
        )

    def _parse_position(self, raw: dict) -> MorphoPositionData:
        """Parse raw position data from subgraph."""
        vault = raw.get("metaMorpho", {})
        asset = vault.get("asset", {})
        
        return MorphoPositionData(
            vault_id=vault.get("id", ""),
            vault_name=vault.get("name", "Unknown"),
            asset_symbol=asset.get("symbol", ""),
            shares=raw.get("shares", "0"),
            assets=raw.get("assets", "0"),
        )
