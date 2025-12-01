"""
Wallet balance provider using multiple blockchain RPCs.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


# Common ERC-20 token addresses on Ethereum
TOKEN_ADDRESSES = {
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
}


class WalletProvider:
    """
    Multi-chain wallet balance provider.
    
    Supports Ethereum, Polygon, Arbitrum, Optimism via RPC.
    """
    
    # RPC endpoints (can be configured via env)
    RPC_ENDPOINTS = {
        "ethereum": "https://eth.llamarpc.com",
        "polygon": "https://polygon.llamarpc.com",
        "arbitrum": "https://arbitrum.llamarpc.com",
        "optimism": "https://optimism.llamarpc.com",
    }
    
    def __init__(self, custom_rpc: Optional[Dict[str, str]] = None):
        """
        Initialize wallet provider.
        
        Args:
            custom_rpc: Custom RPC endpoints (network -> url)
        """
        self.rpc_endpoints = custom_rpc or self.RPC_ENDPOINTS
        self._clients = {
            network: httpx.AsyncClient(
                base_url=url,
                timeout=30.0,
            )
            for network, url in self.rpc_endpoints.items()
        }
    
    async def get_native_balance(
        self,
        address: str,
        network: str = "ethereum",
    ) -> Dict[str, Any]:
        """
        Get native token balance (ETH, MATIC, etc.).
        
        Args:
            address: Wallet address
            network: Network name (ethereum, polygon, arbitrum, optimism)
        
        Returns:
            Balance data with amount in wei and formatted
        """
        try:
            client = self._clients.get(network)
            if not client:
                raise ValueError(f"Unsupported network: {network}")
            
            # eth_getBalance RPC call
            response = await client.post(
                "/",
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1,
                }
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "error" in data:
                raise ValueError(f"RPC error: {data['error']}")
            
            # Convert hex to decimal
            balance_wei = int(data["result"], 16)
            balance_eth = Decimal(balance_wei) / Decimal(10**18)
            
            return {
                "address": address,
                "network": network,
                "token": "ETH" if network == "ethereum" else network.upper(),
                "balance_wei": str(balance_wei),
                "balance": str(balance_eth),
                "formatted": f"{balance_eth:.6f}",
            }
        
        except Exception as e:
            logger.error(f"Error getting native balance: {e}")
            raise
    
    async def get_token_balance(
        self,
        address: str,
        token_address: str,
        network: str = "ethereum",
        decimals: int = 18,
    ) -> Dict[str, Any]:
        """
        Get ERC-20 token balance.
        
        Args:
            address: Wallet address
            token_address: Token contract address
            network: Network name
            decimals: Token decimals (default 18)
        
        Returns:
            Token balance data
        """
        try:
            client = self._clients.get(network)
            if not client:
                raise ValueError(f"Unsupported network: {network}")
            
            # ERC-20 balanceOf(address) function signature
            # Function selector: 0x70a08231
            # Padded address parameter
            data = f"0x70a08231000000000000000000000000{address[2:].lower()}"
            
            # eth_call RPC
            response = await client.post(
                "/",
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_call",
                    "params": [
                        {
                            "to": token_address,
                            "data": data,
                        },
                        "latest"
                    ],
                    "id": 1,
                }
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                raise ValueError(f"RPC error: {result['error']}")
            
            # Convert hex result to decimal
            balance_raw = int(result["result"], 16)
            balance = Decimal(balance_raw) / Decimal(10**decimals)
            
            return {
                "address": address,
                "network": network,
                "token_address": token_address,
                "balance_raw": str(balance_raw),
                "balance": str(balance),
                "formatted": f"{balance:.6f}",
                "decimals": decimals,
            }
        
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            raise
    
    async def get_portfolio_balances(
        self,
        address: str,
        network: str = "ethereum",
        tokens: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get complete portfolio balances for an address.
        
        Args:
            address: Wallet address
            network: Network name
            tokens: Token symbols to check (defaults to common tokens)
        
        Returns:
            Portfolio data with all balances
        """
        try:
            # Default to checking common tokens
            if tokens is None:
                tokens = ["USDC", "USDT", "DAI", "WETH", "WBTC"]
            
            # Get native balance
            native = await self.get_native_balance(address, network)
            
            # Get token balances
            token_balances = []
            for token_symbol in tokens:
                token_address = TOKEN_ADDRESSES.get(token_symbol)
                if not token_address:
                    continue
                
                try:
                    # Determine decimals
                    decimals = 6 if token_symbol in ["USDC", "USDT"] else 18
                    
                    balance = await self.get_token_balance(
                        address=address,
                        token_address=token_address,
                        network=network,
                        decimals=decimals,
                    )
                    
                    # Only include if balance > 0
                    if Decimal(balance["balance"]) > 0:
                        token_balances.append({
                            "symbol": token_symbol,
                            **balance
                        })
                
                except Exception as e:
                    logger.warning(f"Failed to get {token_symbol} balance: {e}")
                    continue
            
            return {
                "address": address,
                "network": network,
                "native": native,
                "tokens": token_balances,
                "total_tokens": len(token_balances),
            }
        
        except Exception as e:
            logger.error(f"Error getting portfolio balances: {e}")
            raise
    
    async def close(self):
        """Close all HTTP clients."""
        for client in self._clients.values():
            await client.aclose()


class WalletProviderError(Exception):
    """Wallet provider error."""
    pass
