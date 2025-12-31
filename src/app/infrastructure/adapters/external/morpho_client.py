"""
Morpho Protocol API Client.

Provides access to Morpho Protocol via official GraphQL API:
- MetaMorpho vaults (V1 and V2)
- Morpho Blue markets
- User positions
- APY data

Supports multiple chains:
- Ethereum (chainId: 1)
- Base (chainId: 8453)

API Docs: https://docs.morpho.org/api/graphql
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# Chain ID mapping
CHAIN_IDS = {
    "ethereum": 1,
    "base": 8453,
}

# Base USDC address (6 decimals)
BASE_USDC_ADDRESS = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"


@dataclass
class MorphoVaultData:
    """Raw vault data from Morpho API."""

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
    allocations: list[dict] = field(default_factory=list)
    chain_id: int = 1
    whitelisted: bool = False
    net_apy: str = "0"
    daily_apy: str = "0"


@dataclass
class MorphoMarketData:
    """Raw market data from Morpho API."""

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
    chain_id: int = 1


@dataclass
class MorphoPositionData:
    """Raw position data from Morpho API."""

    vault_id: str
    vault_name: str
    asset_symbol: str
    shares: str
    assets: str
    chain_id: int = 1


class MorphoClient:
    """
    Morpho Protocol API client using official GraphQL endpoint.

    Features:
    - Multi-chain support (Ethereum + Base)
    - MetaMorpho vault discovery (V1 and V2)
    - Morpho Blue market data
    - User position tracking
    - Real-time APY data
    
    Example:
        client = MorphoClient()
        
        # Get Base USDC vaults
        vaults = await client.get_vaults(chain_id=8453, asset_address=BASE_USDC_ADDRESS)
        
        # Get whitelisted vaults only
        vaults = await client.get_vaults(chain_id=8453, whitelisted=True)
    """

    # Official Morpho GraphQL API (supports all chains)
    MORPHO_API_URL = "https://blue-api.morpho.org/graphql"

    def __init__(
        self,
        api_url: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize Morpho client.

        Args:
            api_url: Custom API URL (optional)
            timeout: Request timeout in seconds
        """
        self._api_url = api_url or self.MORPHO_API_URL
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

    async def get_vaults(
        self,
        chain_id: int = 1,
        asset_address: str | None = None,
        whitelisted: bool | None = None,
        first: int = 100,
    ) -> list[MorphoVaultData]:
        """
        Get MetaMorpho vaults from official Morpho API.

        Uses vaultByAddress or vaults query depending on filters.
        Supports Base (8453) and Ethereum (1).

        Args:
            chain_id: Chain ID (1=Ethereum, 8453=Base)
            asset_address: Filter by underlying asset address
            whitelisted: Filter by whitelisted status (curated vaults)
            first: Number of vaults to fetch

        Returns:
            List of vault data with APY
        
        Example:
            # Get Base USDC vaults (whitelisted only)
            vaults = await client.get_vaults(
                chain_id=8453,
                asset_address="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
                whitelisted=True,
            )
        """
        # Build where clause based on filters
        where_parts = [f"chainId_in: [{chain_id}]"]
        if asset_address:
            # Use assetAddress_in for filtering by asset
            where_parts.append(f'assetAddress_in: ["{asset_address.lower()}"]')
        if whitelisted is not None:
            where_parts.append(f"whitelisted: {str(whitelisted).lower()}")
        
        where_clause = ", ".join(where_parts)

        # Use vaultByAddress query shape from Morpho docs
        query = """
        query GetVaults($first: Int!) {
            vaults(
                first: $first,
                where: {%s},
                orderBy: TotalAssetsUsd,
                orderDirection: Desc
            ) {
                items {
                    address
                    name
                    symbol
                    whitelisted
                    chain {
                        id
                    }
                    asset {
                        address
                        symbol
                        decimals
                    }
                    state {
                        totalAssets
                        totalSupply
                        fee
                        netApy
                        dailyApy
                        curator
                        guardian
                    }
                }
            }
        }
        """ % where_clause

        try:
            response = await self._client.post(
                self._api_url,
                json={"query": query, "variables": {"first": first}},
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                # Try alternative query format (vaultV2s)
                return await self._get_vaults_v2(chain_id, asset_address, whitelisted, first)

            items = data.get("data", {}).get("vaults", {}).get("items", [])
            return [self._parse_vault(v, chain_id) for v in items]

        except Exception as e:
            logger.error(f"Error fetching Morpho vaults: {e}")
            # Try fallback query
            return await self._get_vaults_v2(chain_id, asset_address, whitelisted, first)

    async def _get_vaults_v2(
        self,
        chain_id: int = 1,
        asset_address: str | None = None,
        whitelisted: bool | None = None,
        first: int = 100,
    ) -> list[MorphoVaultData]:
        """
        Fallback: Get vaults using vaultV2s query.
        
        This matches the CEO's recommended query format.
        """
        # Build where clause
        where_parts = [f"chainId_in: [{chain_id}]"]
        if asset_address:
            where_parts.append(f'assetAddress_in: ["{asset_address.lower()}"]')
        if whitelisted is not None:
            where_parts.append(f"whitelisted: {str(whitelisted).lower()}")
        
        where_clause = ", ".join(where_parts)

        query = """
        query GetVaultsV2($first: Int!) {
            vaultV2s(
                first: $first,
                where: {%s}
            ) {
                items {
                    address
                    name
                    symbol
                    whitelisted
                    chainId
                    asset {
                        address
                        symbol
                        decimals
                    }
                    metadata {
                        curators {
                            address
                        }
                    }
                    state {
                        totalAssets
                        totalSupply
                        fee
                        apy
                    }
                }
            }
        }
        """ % where_clause

        try:
            response = await self._client.post(
                self._api_url,
                json={"query": query, "variables": {"first": first}},
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors (V2): {data['errors']}")
                return []

            items = data.get("data", {}).get("vaultV2s", {}).get("items", [])
            return [self._parse_vault_v2(v, chain_id) for v in items]

        except Exception as e:
            logger.error(f"Error fetching Morpho vaults (V2): {e}")
            raise

    async def get_vault(
        self,
        vault_address: str,
        chain_id: int = 1,
    ) -> MorphoVaultData | None:
        """
        Get specific vault details by address.

        Args:
            vault_address: Vault contract address
            chain_id: Chain ID (1=Ethereum, 8453=Base)

        Returns:
            Vault data or None if not found
        """
        query = """
        query GetVault($address: String!, $chainId: Int!) {
            vaultByAddress(address: $address, chainId: $chainId) {
                address
                name
                symbol
                whitelisted
                chain {
                    id
                }
                asset {
                    address
                    symbol
                    decimals
                }
                state {
                    totalAssets
                    totalSupply
                    fee
                    netApy
                    dailyApy
                    curator
                    guardian
                }
            }
        }
        """

        try:
            response = await self._client.post(
                self._api_url,
                json={
                    "query": query,
                    "variables": {
                        "address": vault_address.lower(),
                        "chainId": chain_id,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return None

            vault = data.get("data", {}).get("vaultByAddress")
            if vault:
                return self._parse_vault(vault, chain_id)
            return None

        except Exception as e:
            logger.error(f"Error fetching vault {vault_address}: {e}")
            raise

    async def get_markets(
        self,
        chain_id: int = 1,
        first: int = 100,
    ) -> list[MorphoMarketData]:
        """
        Get Morpho Blue markets.

        Args:
            chain_id: Chain ID (1=Ethereum, 8453=Base)
            first: Number of markets to fetch

        Returns:
            List of market data
        """
        query = """
        query GetMarkets($first: Int!, $chainId: Int!) {
            markets(
                first: $first,
                where: {chainId_in: [$chainId]},
                orderBy: TotalSupplyAssetsUsd,
                orderDirection: Desc
            ) {
                items {
                    uniqueKey
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
                    irmAddress
                    state {
                        totalSupplyAssets
                        totalBorrowAssets
                        supplyApy
                        borrowApy
                    }
                }
            }
        }
        """

        try:
            response = await self._client.post(
                self._api_url,
                json={
                    "query": query,
                    "variables": {"first": first, "chainId": chain_id},
                },
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []

            items = data.get("data", {}).get("markets", {}).get("items", [])
            return [self._parse_market(m, chain_id) for m in items]

        except Exception as e:
            logger.error(f"Error fetching Morpho markets: {e}")
            raise

    async def get_user_positions(
        self,
        user_address: str,
        chain_id: int = 1,
        first: int = 50,
    ) -> list[MorphoPositionData]:
        """
        Get user vault positions.

        Args:
            user_address: User wallet address
            chain_id: Chain ID (1=Ethereum, 8453=Base)
            first: Number of positions to fetch

        Returns:
            List of position data
        """
        query = """
        query GetPositions($user: String!, $chainId: Int!, $first: Int!) {
            vaultPositions(
                where: {
                    userAddress: $user,
                    chainId_in: [$chainId]
                },
                first: $first,
                orderBy: SupplyAssetsUsd,
                orderDirection: Desc
            ) {
                items {
                    vault {
                        address
                        name
                        asset {
                            symbol
                        }
                    }
                    supplyShares
                    supplyAssets
                }
            }
        }
        """

        try:
            response = await self._client.post(
                self._api_url,
                json={
                    "query": query,
                    "variables": {
                        "user": user_address.lower(),
                        "chainId": chain_id,
                        "first": first,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []

            items = data.get("data", {}).get("vaultPositions", {}).get("items", [])
            return [self._parse_position(p, chain_id) for p in items]

        except Exception as e:
            logger.error(f"Error fetching positions for {user_address}: {e}")
            raise

    async def get_vault_apy(
        self,
        vault_address: str,
        chain_id: int = 1,
    ) -> dict[str, Any]:
        """
        Get vault APY data.

        Uses the same vault query with APY state data.

        Args:
            vault_address: Vault contract address
            chain_id: Chain ID (1=Ethereum, 8453=Base)

        Returns:
            APY data dictionary
        """
        vault = await self.get_vault(vault_address, chain_id)
        
        if vault:
            return {
                "base_apy": vault.net_apy,
                "supply_apy": vault.daily_apy,
                "reward_apy": "0",  # Would need separate rewards query
                "fee": vault.performance_fee,
            }

        # Fallback: return estimated APY
        return {
            "base_apy": "0",
            "supply_apy": "0",
            "reward_apy": "0",
            "fee": "0",
        }
    
    async def get_base_usdc_vaults(
        self,
        whitelisted: bool = True,
        first: int = 20,
    ) -> list[MorphoVaultData]:
        """
        Convenience method: Get Base USDC vaults (CEO's primary use case).

        Args:
            whitelisted: Only return curated/whitelisted vaults
            first: Number of vaults to fetch

        Returns:
            List of Base USDC vault data sorted by APY
        
        Example:
            # Get whitelisted Base USDC vaults
            vaults = await client.get_base_usdc_vaults()
            
            # Show to user:
            # "Which vault do you want: Highest yield, Lowest risk, or Recommended?"
        """
        vaults = await self.get_vaults(
            chain_id=8453,  # Base
            asset_address=BASE_USDC_ADDRESS,
            whitelisted=whitelisted,
            first=first,
        )
        
        # Sort by APY descending
        return sorted(
            vaults,
            key=lambda v: float(v.net_apy or "0"),
            reverse=True,
        )

    def _parse_vault(self, raw: dict, chain_id: int = 1) -> MorphoVaultData:
        """Parse raw vault data from Morpho API."""
        asset = raw.get("asset", {})
        state = raw.get("state", {})
        chain = raw.get("chain", {})
        
        return MorphoVaultData(
            id=raw.get("address", ""),
            name=raw.get("name", "Unknown"),
            symbol=raw.get("symbol", ""),
            asset_address=asset.get("address", ""),
            asset_symbol=asset.get("symbol", ""),
            asset_decimals=int(asset.get("decimals", 18)),
            total_assets=str(state.get("totalAssets", "0")),
            total_supply=str(state.get("totalSupply", "0")),
            performance_fee=str(state.get("fee", "0")),
            curator=state.get("curator"),
            guardian=state.get("guardian"),
            allocations=[],
            chain_id=chain.get("id", chain_id) if chain else chain_id,
            whitelisted=raw.get("whitelisted", False),
            net_apy=str(state.get("netApy", "0")),
            daily_apy=str(state.get("dailyApy", "0")),
        )
    
    def _parse_vault_v2(self, raw: dict, chain_id: int = 1) -> MorphoVaultData:
        """Parse raw vault data from V2 query."""
        asset = raw.get("asset", {})
        state = raw.get("state", {})
        metadata = raw.get("metadata", {})
        curators = metadata.get("curators", [])
        
        return MorphoVaultData(
            id=raw.get("address", ""),
            name=raw.get("name", "Unknown"),
            symbol=raw.get("symbol", ""),
            asset_address=asset.get("address", ""),
            asset_symbol=asset.get("symbol", ""),
            asset_decimals=int(asset.get("decimals", 18)),
            total_assets=str(state.get("totalAssets", "0")),
            total_supply=str(state.get("totalSupply", "0")),
            performance_fee=str(state.get("fee", "0")),
            curator=curators[0].get("address") if curators else None,
            guardian=None,
            allocations=[],
            chain_id=raw.get("chainId", chain_id),
            whitelisted=raw.get("whitelisted", False),
            net_apy=str(state.get("apy", "0")),
            daily_apy="0",
        )

    def _parse_market(self, raw: dict, chain_id: int = 1) -> MorphoMarketData:
        """Parse raw market data from Morpho API."""
        collateral = raw.get("collateralAsset", {})
        loan = raw.get("loanAsset", {})
        state = raw.get("state", {})
        oracle = raw.get("oracle", {})
        
        return MorphoMarketData(
            id=raw.get("uniqueKey", ""),
            collateral_address=collateral.get("address", ""),
            collateral_symbol=collateral.get("symbol", ""),
            loan_address=loan.get("address", ""),
            loan_symbol=loan.get("symbol", ""),
            lltv=str(raw.get("lltv", "0")),
            oracle=oracle.get("address") if oracle else None,
            irm=raw.get("irmAddress"),
            total_supply_assets=str(state.get("totalSupplyAssets", "0")),
            total_borrow_assets=str(state.get("totalBorrowAssets", "0")),
            supply_rate=str(state.get("supplyApy", "0")) if state else "0",
            borrow_rate=str(state.get("borrowApy", "0")) if state else "0",
            chain_id=chain_id,
        )

    def _parse_position(self, raw: dict, chain_id: int = 1) -> MorphoPositionData:
        """Parse raw position data from Morpho API."""
        vault = raw.get("vault", {})
        asset = vault.get("asset", {})
        
        return MorphoPositionData(
            vault_id=vault.get("address", ""),
            vault_name=vault.get("name", "Unknown"),
            asset_symbol=asset.get("symbol", ""),
            shares=str(raw.get("supplyShares", "0")),
            assets=str(raw.get("supplyAssets", "0")),
            chain_id=chain_id,
        )
