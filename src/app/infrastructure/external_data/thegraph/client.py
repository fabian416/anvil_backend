"""
The Graph Protocol Client

Integration with The Graph for on-chain DeFi data.
Provides subgraph queries for protocol metrics, transactions, and events.
"""

from typing import List, Dict, Any, Optional
import httpx
import logging
from datetime import datetime

from app.domain.ports.external_data.defi_data_provider import (
    ProtocolData,
    TokenData,
    TVLData,
)

logger = logging.getLogger(__name__)


class TheGraphClient:
    """
    The Graph Protocol client for on-chain data.
    
    Queries subgraphs for:
    - Protocol metrics (TVL, volume, fees)
    - User transactions
    - Protocol events
    - Token prices
    
    Popular Subgraphs:
    - Uniswap V3
    - Aave V3
    - Compound V3
    - Curve Finance
    """
    
    # Subgraph URLs (mainnet)
    SUBGRAPHS = {
        "uniswap-v3": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "aave-v3": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
        "compound-v3": "https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v3",
        "curve": "https://api.thegraph.com/subgraphs/name/messari/curve-finance-ethereum",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize The Graph client.
        
        Args:
            api_key: The Graph API key (for hosted service)
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def query_subgraph(
        self,
        subgraph: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute GraphQL query on subgraph.
        
        Args:
            subgraph: Subgraph name (e.g., 'uniswap-v3')
            query: GraphQL query string
            variables: Query variables
        
        Returns:
            Query result
        """
        url = self.SUBGRAPHS.get(subgraph)
        if not url:
            raise ValueError(f"Unknown subgraph: {subgraph}")
        
        # Add API key to URL if provided
        if self._api_key:
            url = url.replace(
                "api.thegraph.com",
                f"gateway.thegraph.com/api/{self._api_key}",
            )
        
        payload = {
            "query": query,
            "variables": variables or {},
        }
        
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                raise ValueError(f"GraphQL query failed: {data['errors']}")
            
            return data.get("data", {})
        
        except httpx.HTTPError as e:
            logger.error(f"The Graph request failed: {e}")
            raise
    
    async def get_protocol_tvl(
        self,
        protocol_slug: str,
    ) -> TVLData:
        """
        Get protocol TVL from subgraph.
        
        Args:
            protocol_slug: Protocol identifier
        
        Returns:
            TVL data
        """
        # Map protocol to subgraph
        subgraph_map = {
            "uniswap": "uniswap-v3",
            "aave": "aave-v3",
            "compound": "compound-v3",
            "curve": "curve",
        }
        
        subgraph = subgraph_map.get(protocol_slug)
        if not subgraph:
            raise ValueError(f"No subgraph for protocol: {protocol_slug}")
        
        # Query factory stats for TVL
        if subgraph == "uniswap-v3":
            query = """
            query GetTVL {
                factory(id: "1") {
                    totalValueLockedUSD
                    totalVolumeUSD
                    txCount
                }
            }
            """
        elif subgraph == "aave-v3":
            query = """
            query GetTVL {
                protocol(id: "1") {
                    totalValueLockedUSD
                    totalBorrowBalanceUSD
                    totalDepositBalanceUSD
                }
            }
            """
        else:
            # Generic query
            query = """
            query GetTVL {
                protocols(first: 1) {
                    totalValueLockedUSD
                }
            }
            """
        
        result = await self.query_subgraph(subgraph, query)
        
        # Parse result
        if subgraph == "uniswap-v3":
            factory = result.get("factory", {})
            tvl = float(factory.get("totalValueLockedUSD", 0))
        elif subgraph == "aave-v3":
            protocol = result.get("protocol", {})
            tvl = float(protocol.get("totalValueLockedUSD", 0))
        else:
            protocols = result.get("protocols", [])
            tvl = float(protocols[0].get("totalValueLockedUSD", 0)) if protocols else 0.0
        
        return TVLData(
            tvl=tvl,
            tvl_change_24h=0.0,  # Would need historical data
            tvl_change_7d=0.0,
            tvl_change_30d=0.0,
            timestamp=datetime.utcnow(),
        )
    
    async def get_protocol_transactions(
        self,
        protocol_slug: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get recent protocol transactions.
        
        Args:
            protocol_slug: Protocol identifier
            limit: Maximum transactions to return
        
        Returns:
            List of transactions
        """
        subgraph_map = {
            "uniswap": "uniswap-v3",
            "aave": "aave-v3",
        }
        
        subgraph = subgraph_map.get(protocol_slug)
        if not subgraph:
            raise ValueError(f"No subgraph for protocol: {protocol_slug}")
        
        if subgraph == "uniswap-v3":
            query = """
            query GetSwaps($limit: Int!) {
                swaps(first: $limit, orderBy: timestamp, orderDirection: desc) {
                    id
                    timestamp
                    amount0
                    amount1
                    amountUSD
                    sender
                    recipient
                    transaction {
                        id
                    }
                }
            }
            """
            variables = {"limit": limit}
            result = await self.query_subgraph(subgraph, query, variables)
            return result.get("swaps", [])
        
        elif subgraph == "aave-v3":
            query = """
            query GetDeposits($limit: Int!) {
                deposits(first: $limit, orderBy: timestamp, orderDirection: desc) {
                    id
                    timestamp
                    amount
                    amountUSD
                    user {
                        id
                    }
                    reserve {
                        symbol
                    }
                }
            }
            """
            variables = {"limit": limit}
            result = await self.query_subgraph(subgraph, query, variables)
            return result.get("deposits", [])
        
        return []
    
    async def get_token_data(
        self,
        token_address: str,
        subgraph: str = "uniswap-v3",
    ) -> TokenData:
        """
        Get token data from subgraph.
        
        Args:
            token_address: Token contract address
            subgraph: Subgraph to query
        
        Returns:
            Token data
        """
        query = """
        query GetToken($address: String!) {
            token(id: $address) {
                id
                symbol
                name
                decimals
                totalSupply
                volume
                volumeUSD
                priceUSD
            }
        }
        """
        
        variables = {"address": token_address.lower()}
        result = await self.query_subgraph(subgraph, query, variables)
        
        token = result.get("token", {})
        
        return TokenData(
            address=token.get("id", token_address),
            symbol=token.get("symbol", ""),
            name=token.get("name", ""),
            decimals=int(token.get("decimals", 18)),
            price_usd=float(token.get("priceUSD", 0)),
            market_cap=0.0,  # Not in subgraph
            volume_24h=float(token.get("volumeUSD", 0)),
            chain="ethereum",
        )
    
    async def close(self):
        """Close HTTP client"""
        await self._client.aclose()
