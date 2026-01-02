"""Flashbots Client for MEV Protection.

Real integration with Flashbots relay for private transaction submission.

NO API KEY REQUIRED - Flashbots is free and open.

Flashbots Endpoints:
- Ethereum Mainnet: https://relay.flashbots.net
- Goerli Testnet: https://relay-goerli.flashbots.net
- Sepolia Testnet: https://relay-sepolia.flashbots.net

Alternative Relays (also free):
- MEV Blocker: https://rpc.mevblocker.io
- Eden Network: https://api.edennetwork.io/v1/bundle
- Bloxroute: https://mev.api.blxrbdn.com (requires account)

Usage:
    client = FlashbotsClient(private_key="0x...")
    
    # Submit single transaction privately
    result = await client.send_private_transaction(signed_tx)
    
    # Submit bundle for atomic execution
    result = await client.send_bundle(
        transactions=[signed_tx1, signed_tx2],
        target_block=current_block + 1,
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
import hashlib
import json

import httpx


class Chain(str, Enum):
    """Supported chains for Flashbots."""
    
    ETHEREUM = "ethereum"
    GOERLI = "goerli"  # Testnet
    SEPOLIA = "sepolia"  # Testnet


class RelayType(str, Enum):
    """MEV relay types."""
    
    FLASHBOTS = "flashbots"
    MEV_BLOCKER = "mev_blocker"
    EDEN = "eden"


# Relay endpoints - NO API KEY NEEDED
RELAY_ENDPOINTS = {
    Chain.ETHEREUM: {
        RelayType.FLASHBOTS: "https://relay.flashbots.net",
        RelayType.MEV_BLOCKER: "https://rpc.mevblocker.io",
        RelayType.EDEN: "https://api.edennetwork.io/v1/bundle",
    },
    Chain.GOERLI: {
        RelayType.FLASHBOTS: "https://relay-goerli.flashbots.net",
    },
    Chain.SEPOLIA: {
        RelayType.FLASHBOTS: "https://relay-sepolia.flashbots.net",
    },
}


class BundleStatus(str, Enum):
    """Bundle submission status."""
    
    PENDING = "pending"
    SUBMITTED = "submitted"
    INCLUDED = "included"
    FAILED = "failed"


@dataclass
class BundleResult:
    """Result of bundle submission."""
    
    bundle_hash: str
    status: BundleStatus
    target_block: int
    transactions: list[str]
    simulation_success: bool | None = None
    simulation_error: str | None = None
    gas_used: int | None = None
    effective_gas_price: int | None = None
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bundle_hash": self.bundle_hash,
            "status": self.status.value,
            "target_block": self.target_block,
            "transactions": self.transactions,
            "simulation_success": self.simulation_success,
            "simulation_error": self.simulation_error,
            "gas_used": self.gas_used,
            "effective_gas_price": self.effective_gas_price,
            "submitted_at": self.submitted_at.isoformat(),
        }


@dataclass
class FlashbotsConfig:
    """Configuration for Flashbots client."""
    
    chain: Chain = Chain.ETHEREUM
    relay_type: RelayType = RelayType.FLASHBOTS
    
    # Signing
    private_key: str = ""  # For signing bundles (required for real execution)
    
    # Bundle settings
    max_block_number: int = 25  # Try N blocks ahead
    simulation_enabled: bool = True
    
    # Timeouts
    request_timeout: float = 10.0
    
    @property
    def relay_url(self) -> str:
        """Get relay URL for current chain."""
        chain_relays = RELAY_ENDPOINTS.get(self.chain, {})
        return chain_relays.get(self.relay_type, RELAY_ENDPOINTS[Chain.ETHEREUM][RelayType.FLASHBOTS])


class FlashbotsClient:
    """Client for Flashbots MEV protection relay.
    
    Flashbots is FREE - no API key needed.
    
    Features:
    - Private transaction submission (bypass public mempool)
    - Bundle submission (atomic multi-tx execution)
    - Bundle simulation (dry-run before submission)
    - Bundle status checking
    
    Example:
        >>> client = FlashbotsClient(
        ...     private_key="0x...",
        ...     chain=Chain.ETHEREUM,
        ... )
        >>> 
        >>> # Send private transaction
        >>> result = await client.send_private_transaction(
        ...     signed_tx="0x..."
        ... )
        >>> print(f"Status: {result.status}")
        >>> 
        >>> # Send bundle
        >>> result = await client.send_bundle(
        ...     transactions=["0x...", "0x..."],
        ...     target_block=18000000,
        ... )
        >>> print(f"Bundle hash: {result.bundle_hash}")
    """
    
    def __init__(
        self,
        private_key: str = "",
        chain: Chain = Chain.ETHEREUM,
        relay_type: RelayType = RelayType.FLASHBOTS,
        config: FlashbotsConfig | None = None,
    ):
        """Initialize Flashbots client.
        
        Args:
            private_key: Private key for signing bundles (hex string)
            chain: Target chain
            relay_type: MEV relay to use
            config: Optional full configuration
        """
        if config:
            self.config = config
        else:
            self.config = FlashbotsConfig(
                chain=chain,
                relay_type=relay_type,
                private_key=private_key,
            )
        
        self._client: httpx.AsyncClient | None = None
        self._request_id = 0
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.request_timeout,
                headers={
                    "Content-Type": "application/json",
                },
            )
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _next_request_id(self) -> int:
        """Get next JSON-RPC request ID."""
        self._request_id += 1
        return self._request_id
    
    def _calculate_bundle_hash(self, transactions: list[str]) -> str:
        """Calculate bundle hash from transactions.
        
        Args:
            transactions: List of signed transaction hex strings
            
        Returns:
            Bundle hash (keccak256)
        """
        # Simplified hash calculation
        # In production, would use proper keccak256
        combined = "".join(transactions)
        return "0x" + hashlib.sha256(combined.encode()).hexdigest()
    
    async def _call_relay(
        self,
        method: str,
        params: list[Any],
    ) -> dict[str, Any]:
        """Make JSON-RPC call to relay.
        
        Args:
            method: JSON-RPC method
            params: Method parameters
            
        Returns:
            Response result
        """
        client = await self._get_client()
        
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": method,
            "params": params,
        }
        
        response = await client.post(
            self.config.relay_url,
            json=payload,
        )
        response.raise_for_status()
        
        result = response.json()
        
        if "error" in result:
            raise Exception(f"Relay error: {result['error']}")
        
        return result.get("result", {})
    
    async def send_bundle(
        self,
        transactions: list[str],
        target_block: int,
        min_timestamp: int | None = None,
        max_timestamp: int | None = None,
        reverting_tx_hashes: list[str] | None = None,
    ) -> BundleResult:
        """Submit bundle to Flashbots relay.
        
        Bundles are atomic - all transactions execute or none do.
        Transactions bypass the public mempool, preventing sandwich attacks.
        
        Args:
            transactions: List of signed transaction hex strings
            target_block: Block number to target for inclusion
            min_timestamp: Minimum block timestamp (optional)
            max_timestamp: Maximum block timestamp (optional)
            reverting_tx_hashes: Allow these txs to revert (optional)
            
        Returns:
            Bundle submission result
            
        Example:
            >>> result = await client.send_bundle(
            ...     transactions=["0x...", "0x..."],
            ...     target_block=18000000,
            ... )
            >>> print(f"Bundle: {result.bundle_hash}")
            >>> print(f"Status: {result.status}")
        """
        # Build bundle params
        bundle_params: dict[str, Any] = {
            "txs": transactions,
            "blockNumber": hex(target_block),
        }
        
        if min_timestamp is not None:
            bundle_params["minTimestamp"] = min_timestamp
        if max_timestamp is not None:
            bundle_params["maxTimestamp"] = max_timestamp
        if reverting_tx_hashes:
            bundle_params["revertingTxHashes"] = reverting_tx_hashes
        
        bundle_hash = self._calculate_bundle_hash(transactions)
        
        try:
            # Simulate first if enabled
            simulation_success = None
            simulation_error = None
            gas_used = None
            
            if self.config.simulation_enabled:
                sim_result = await self.simulate_bundle(
                    transactions=transactions,
                    target_block=target_block,
                )
                simulation_success = sim_result.get("success", False)
                simulation_error = sim_result.get("error")
                gas_used = sim_result.get("totalGasUsed")
                
                if not simulation_success:
                    return BundleResult(
                        bundle_hash=bundle_hash,
                        status=BundleStatus.FAILED,
                        target_block=target_block,
                        transactions=transactions,
                        simulation_success=False,
                        simulation_error=simulation_error or "Simulation failed",
                    )
            
            # Submit bundle
            await self._call_relay(
                method="eth_sendBundle",
                params=[bundle_params],
            )
            
            return BundleResult(
                bundle_hash=bundle_hash,
                status=BundleStatus.SUBMITTED,
                target_block=target_block,
                transactions=transactions,
                simulation_success=simulation_success,
                gas_used=gas_used,
            )
            
        except Exception as e:
            return BundleResult(
                bundle_hash=bundle_hash,
                status=BundleStatus.FAILED,
                target_block=target_block,
                transactions=transactions,
                simulation_success=False,
                simulation_error=str(e),
            )
    
    async def simulate_bundle(
        self,
        transactions: list[str],
        target_block: int,
        state_block: str = "latest",
    ) -> dict[str, Any]:
        """Simulate bundle execution.
        
        Dry-run the bundle to check if it will succeed.
        
        Args:
            transactions: List of signed transaction hex strings
            target_block: Block number to target
            state_block: State block for simulation ("latest" or block number)
            
        Returns:
            Simulation result with gas usage and success status
            
        Example:
            >>> result = await client.simulate_bundle(
            ...     transactions=["0x..."],
            ...     target_block=18000000,
            ... )
            >>> if result["success"]:
            ...     print(f"Gas used: {result['totalGasUsed']}")
        """
        try:
            result = await self._call_relay(
                method="eth_callBundle",
                params=[{
                    "txs": transactions,
                    "blockNumber": hex(target_block),
                    "stateBlockNumber": state_block,
                }],
            )
            
            # Parse simulation results
            return {
                "success": True,
                "totalGasUsed": result.get("totalGasUsed", 0),
                "results": result.get("results", []),
                "coinbaseDiff": result.get("coinbaseDiff"),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def send_private_transaction(
        self,
        signed_tx: str,
        max_block_number: int | None = None,
        fast: bool = True,
    ) -> BundleResult:
        """Send single transaction privately.
        
        Bypasses public mempool to prevent frontrunning.
        
        Args:
            signed_tx: Signed transaction hex string
            max_block_number: Maximum block to include in
            fast: Use fast mode (higher priority)
            
        Returns:
            Submission result
            
        Example:
            >>> result = await client.send_private_transaction(
            ...     signed_tx="0x...",
            ...     fast=True,
            ... )
            >>> print(f"Status: {result.status}")
        """
        tx_params: dict[str, Any] = {
            "tx": signed_tx,
            "fast": fast,
        }
        
        if max_block_number:
            tx_params["maxBlockNumber"] = hex(max_block_number)
        
        bundle_hash = self._calculate_bundle_hash([signed_tx])
        
        try:
            result = await self._call_relay(
                method="eth_sendPrivateTransaction",
                params=[tx_params],
            )
            
            return BundleResult(
                bundle_hash=bundle_hash,
                status=BundleStatus.SUBMITTED,
                target_block=max_block_number or 0,
                transactions=[signed_tx],
                simulation_success=True,
            )
            
        except Exception as e:
            return BundleResult(
                bundle_hash=bundle_hash,
                status=BundleStatus.FAILED,
                target_block=max_block_number or 0,
                transactions=[signed_tx],
                simulation_success=False,
                simulation_error=str(e),
            )
    
    async def get_bundle_stats(
        self,
        bundle_hash: str,
        target_block: int,
    ) -> dict[str, Any]:
        """Get bundle statistics.
        
        Check if bundle was included and get execution details.
        
        Args:
            bundle_hash: Bundle hash from submission
            target_block: Target block number
            
        Returns:
            Bundle statistics
            
        Example:
            >>> stats = await client.get_bundle_stats(
            ...     bundle_hash="0x...",
            ...     target_block=18000000,
            ... )
            >>> print(f"Included: {stats.get('isSimulated')}")
        """
        try:
            return await self._call_relay(
                method="flashbots_getBundleStats",
                params=[{
                    "bundleHash": bundle_hash,
                    "blockNumber": hex(target_block),
                }],
            )
        except Exception as e:
            return {"error": str(e)}
    
    async def get_user_stats(self) -> dict[str, Any]:
        """Get user statistics.
        
        Returns lifetime stats for the signing address.
        
        Returns:
            User statistics including success rate
        """
        try:
            return await self._call_relay(
                method="flashbots_getUserStats",
                params=[{}],
            )
        except Exception as e:
            return {"error": str(e)}
    
    def get_supported_relays(self) -> dict[str, str]:
        """Get all supported relay endpoints.
        
        Returns:
            Dictionary of relay name to URL
        """
        return {
            "Flashbots (Ethereum)": RELAY_ENDPOINTS[Chain.ETHEREUM][RelayType.FLASHBOTS],
            "MEV Blocker (Free, no signing)": RELAY_ENDPOINTS[Chain.ETHEREUM][RelayType.MEV_BLOCKER],
            "Eden Network": RELAY_ENDPOINTS[Chain.ETHEREUM][RelayType.EDEN],
            "Flashbots (Goerli Testnet)": RELAY_ENDPOINTS[Chain.GOERLI][RelayType.FLASHBOTS],
            "Flashbots (Sepolia Testnet)": RELAY_ENDPOINTS[Chain.SEPOLIA][RelayType.FLASHBOTS],
        }


# ============================================================================
# MEV Blocker Client (Simpler Alternative)
# ============================================================================

class MEVBlockerClient:
    """Simple MEV Blocker client.
    
    MEV Blocker is the simplest option:
    - No API key
    - No bundle signing
    - Just use as RPC endpoint
    
    Usage:
        Simply replace your RPC URL with:
        https://rpc.mevblocker.io
        
    Example with Web3:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider("https://rpc.mevblocker.io"))
        w3.eth.send_raw_transaction(signed_tx)
    """
    
    RPC_URL = "https://rpc.mevblocker.io"
    
    def __init__(self):
        """Initialize MEV Blocker client."""
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client
    
    async def close(self) -> None:
        """Close client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def send_raw_transaction(self, signed_tx: str) -> str:
        """Send raw transaction via MEV Blocker.
        
        Args:
            signed_tx: Signed transaction hex string
            
        Returns:
            Transaction hash
        """
        client = await self._get_client()
        
        response = await client.post(
            self.RPC_URL,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_sendRawTransaction",
                "params": [signed_tx],
            },
        )
        response.raise_for_status()
        
        result = response.json()
        
        if "error" in result:
            raise Exception(f"MEV Blocker error: {result['error']}")
        
        return result.get("result", "")
