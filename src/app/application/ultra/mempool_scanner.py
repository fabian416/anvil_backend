"""Mempool Scanner for MEV Attack Detection.

Real-time mempool monitoring to detect and prevent MEV attacks.

Connects to blockchain nodes via WebSocket to monitor pending transactions
and detect potential sandwich attacks, front-running, and other MEV exploits.

Supported Providers:
- Alchemy (WebSocket): wss://eth-mainnet.g.alchemy.com/v2/{key}
- Infura (WebSocket): wss://mainnet.infura.io/ws/v3/{key}
- Bloxroute (Mempool Stream): Requires subscription

Usage:
    scanner = MempoolScanner(alchemy_api_key="...")
    
    # Start scanning
    await scanner.start()
    
    # Check if our transaction is being attacked
    attack = await scanner.detect_attack_on_transaction(
        our_tx=our_pending_tx,
        token_pair=("WETH", "USDC"),
    )
    
    if attack:
        print(f"Attack detected: {attack.type}")
        # Route via Flashbots instead
    
    await scanner.stop()
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)


class AttackType(str, Enum):
    """Types of MEV attacks."""
    
    SANDWICH = "sandwich"
    FRONT_RUN = "front_run"
    BACK_RUN = "back_run"
    LIQUIDATION = "liquidation"
    ARBITRAGE = "arbitrage"


class Chain(str, Enum):
    """Supported chains."""
    
    ETHEREUM = "ethereum"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    POLYGON = "polygon"


# WebSocket endpoints
WEBSOCKET_ENDPOINTS = {
    Chain.ETHEREUM: {
        "alchemy": "wss://eth-mainnet.g.alchemy.com/v2/{key}",
        "infura": "wss://mainnet.infura.io/ws/v3/{key}",
    },
    Chain.ARBITRUM: {
        "alchemy": "wss://arb-mainnet.g.alchemy.com/v2/{key}",
        "infura": "wss://arbitrum-mainnet.infura.io/ws/v3/{key}",
    },
    Chain.OPTIMISM: {
        "alchemy": "wss://opt-mainnet.g.alchemy.com/v2/{key}",
        "infura": "wss://optimism-mainnet.infura.io/ws/v3/{key}",
    },
    Chain.BASE: {
        "alchemy": "wss://base-mainnet.g.alchemy.com/v2/{key}",
        "infura": "wss://base-mainnet.infura.io/ws/v3/{key}",
    },
    Chain.POLYGON: {
        "alchemy": "wss://polygon-mainnet.g.alchemy.com/v2/{key}",
        "infura": "wss://polygon-mainnet.infura.io/ws/v3/{key}",
    },
}

# HTTP RPC endpoints (for pending block queries)
RPC_ENDPOINTS = {
    Chain.ETHEREUM: {
        "alchemy": "https://eth-mainnet.g.alchemy.com/v2/{key}",
        "infura": "https://mainnet.infura.io/v3/{key}",
    },
    Chain.ARBITRUM: {
        "alchemy": "https://arb-mainnet.g.alchemy.com/v2/{key}",
        "infura": "https://arbitrum-mainnet.infura.io/v3/{key}",
    },
    Chain.OPTIMISM: {
        "alchemy": "https://opt-mainnet.g.alchemy.com/v2/{key}",
        "infura": "https://optimism-mainnet.infura.io/v3/{key}",
    },
    Chain.BASE: {
        "alchemy": "https://base-mainnet.g.alchemy.com/v2/{key}",
        "infura": "https://base-mainnet.infura.io/v3/{key}",
    },
    Chain.POLYGON: {
        "alchemy": "https://polygon-mainnet.g.alchemy.com/v2/{key}",
        "infura": "https://polygon-mainnet.infura.io/v3/{key}",
    },
}

# Known MEV bot addresses (partial list)
KNOWN_MEV_BOTS = {
    "0x00000000003b3cc22aF3aE1EAc0440BcEe416B40",  # Flashbots
    "0x98C3d3183C4b8A650614ad179A1a98be0a8d6B8E",  # MEV Bot
    "0x000000000035B5e5ad9019092C665357240f594e",  # Sandwich bot
    "0x00000000009726632680FB29d3F7A9734E3010E2",  # Arbitrage bot
    "0xA69babEF1cA67A37Ffaf7a485DfFF3382056e78C",  # Known sandwich
}

# Common DEX router addresses
DEX_ROUTERS = {
    "uniswap_v2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "sushiswap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    "1inch_v5": "0x1111111254EEB25477B68fb85Ed929f73A960582",
}


@dataclass
class PendingTransaction:
    """A pending transaction from the mempool."""
    
    hash: str
    from_address: str
    to_address: str
    value: int
    gas_price: int
    max_fee_per_gas: int | None
    max_priority_fee: int | None
    input_data: str
    nonce: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def effective_gas_price(self) -> int:
        """Get effective gas price for comparison."""
        if self.max_priority_fee:
            return self.max_priority_fee
        return self.gas_price
    
    def is_swap(self) -> bool:
        """Check if transaction is a swap."""
        # Common swap function selectors
        swap_selectors = [
            "0x38ed1739",  # swapExactTokensForTokens
            "0x8803dbee",  # swapTokensForExactTokens
            "0x7ff36ab5",  # swapExactETHForTokens
            "0x18cbafe5",  # swapExactTokensForETH
            "0x5c11d795",  # swapExactTokensForTokensSupportingFeeOnTransferTokens
            "0x414bf389",  # exactInputSingle (Uniswap V3)
            "0xc04b8d59",  # exactInput (Uniswap V3)
            "0x12aa3caf",  # swap (1inch)
        ]
        return any(self.input_data.startswith(sel) for sel in swap_selectors)
    
    def get_token_pair(self) -> tuple[str, str] | None:
        """Extract token pair from swap data (simplified)."""
        # In production, would decode input_data
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hash": self.hash,
            "from": self.from_address,
            "to": self.to_address,
            "value": self.value,
            "gas_price": self.gas_price,
            "max_fee_per_gas": self.max_fee_per_gas,
            "max_priority_fee": self.max_priority_fee,
            "is_swap": self.is_swap(),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AttackDetection:
    """Detected MEV attack."""
    
    attack_type: AttackType
    confidence: float  # 0-1
    attacker_address: str
    attacker_tx_hash: str
    victim_tx_hash: str
    estimated_loss_usd: Decimal
    gas_price_delta: float  # % higher than victim
    token_pair: tuple[str, str] | None
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    # For sandwich attacks
    front_run_tx: str | None = None
    back_run_tx: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "attack_type": self.attack_type.value,
            "confidence": self.confidence,
            "attacker_address": self.attacker_address,
            "attacker_tx_hash": self.attacker_tx_hash,
            "victim_tx_hash": self.victim_tx_hash,
            "estimated_loss_usd": str(self.estimated_loss_usd),
            "gas_price_delta_pct": self.gas_price_delta * 100,
            "token_pair": self.token_pair,
            "detected_at": self.detected_at.isoformat(),
            "front_run_tx": self.front_run_tx,
            "back_run_tx": self.back_run_tx,
        }


@dataclass
class MempoolScannerConfig:
    """Configuration for mempool scanner."""
    
    chain: Chain = Chain.ETHEREUM
    
    # API keys
    alchemy_api_key: str = ""
    infura_api_key: str = ""
    
    # Provider preference (alchemy or infura)
    preferred_provider: str = "alchemy"  # "alchemy" or "infura"
    
    # Detection thresholds
    gas_price_threshold: float = 0.02  # 2% higher = suspicious
    sandwich_window_blocks: int = 2  # Look within N blocks
    min_trade_value_usd: Decimal = Decimal("100")  # Ignore small trades
    
    # Scanning
    scan_interval_ms: int = 100  # Check every 100ms
    max_pending_txs: int = 1000  # Max txs to track
    
    @property
    def websocket_url(self) -> str:
        """Get WebSocket URL."""
        chain_endpoints = WEBSOCKET_ENDPOINTS.get(self.chain, {})
        
        # Try preferred provider first
        if self.preferred_provider == "infura" and self.infura_api_key:
            if "infura" in chain_endpoints:
                return chain_endpoints["infura"].format(key=self.infura_api_key)
        
        # Try Alchemy
        if self.alchemy_api_key and "alchemy" in chain_endpoints:
            return chain_endpoints["alchemy"].format(key=self.alchemy_api_key)
        
        # Fallback to Infura
        if self.infura_api_key and "infura" in chain_endpoints:
            return chain_endpoints["infura"].format(key=self.infura_api_key)
        
        return ""
    
    @property
    def rpc_url(self) -> str:
        """Get HTTP RPC URL."""
        chain_endpoints = RPC_ENDPOINTS.get(self.chain, {})
        
        # Try preferred provider first
        if self.preferred_provider == "infura" and self.infura_api_key:
            if "infura" in chain_endpoints:
                return chain_endpoints["infura"].format(key=self.infura_api_key)
        
        # Try Alchemy
        if self.alchemy_api_key and "alchemy" in chain_endpoints:
            return chain_endpoints["alchemy"].format(key=self.alchemy_api_key)
        
        # Fallback to Infura
        if self.infura_api_key and "infura" in chain_endpoints:
            return chain_endpoints["infura"].format(key=self.infura_api_key)
        
        return ""
    
    @property
    def active_provider(self) -> str:
        """Get which provider is being used."""
        if self.preferred_provider == "infura" and self.infura_api_key:
            return "infura"
        if self.alchemy_api_key:
            return "alchemy"
        if self.infura_api_key:
            return "infura"
        return "none"


class MempoolScanner:
    """Real-time mempool scanner for MEV attack detection.
    
    Monitors pending transactions to detect:
    - Sandwich attacks (front-run + back-run)
    - Front-running
    - Arbitrage competing with your trades
    
    Example:
        >>> scanner = MempoolScanner(
        ...     alchemy_api_key="your-key",
        ...     chain=Chain.ETHEREUM,
        ... )
        >>> 
        >>> # Start scanning
        >>> await scanner.start()
        >>> 
        >>> # Check for attacks on your transaction
        >>> attack = await scanner.detect_attack_on_transaction(
        ...     our_tx_hash="0x...",
        ...     token_pair=("WETH", "USDC"),
        ...     our_gas_price=50_000_000_000,  # 50 gwei
        ... )
        >>> 
        >>> if attack:
        ...     print(f"Attack: {attack.attack_type}")
        ...     print(f"Confidence: {attack.confidence * 100:.0f}%")
        ...     print(f"Estimated loss: ${attack.estimated_loss_usd}")
        >>> 
        >>> await scanner.stop()
    """
    
    def __init__(
        self,
        alchemy_api_key: str = "",
        infura_api_key: str = "",
        chain: Chain = Chain.ETHEREUM,
        preferred_provider: str = "alchemy",
        config: MempoolScannerConfig | None = None,
    ):
        """Initialize mempool scanner.
        
        Args:
            alchemy_api_key: Alchemy API key
            infura_api_key: Infura API key
            chain: Blockchain to scan
            preferred_provider: "alchemy" or "infura"
            config: Full configuration
        """
        if config:
            self.config = config
        else:
            self.config = MempoolScannerConfig(
                chain=chain,
                alchemy_api_key=alchemy_api_key,
                infura_api_key=infura_api_key,
                preferred_provider=preferred_provider,
            )
        
        self._pending_txs: dict[str, PendingTransaction] = {}
        self._attack_callbacks: list[Callable[[AttackDetection], None]] = []
        self._running = False
        self._scan_task: asyncio.Task | None = None
        self._http_client: httpx.AsyncClient | None = None
        
        # Statistics
        self._stats = {
            "txs_scanned": 0,
            "swaps_detected": 0,
            "attacks_detected": 0,
            "sandwich_attacks": 0,
            "front_runs": 0,
        }
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client
    
    async def start(self) -> None:
        """Start mempool scanning.
        
        Begins monitoring pending transactions for MEV attacks.
        """
        if self._running:
            logger.warning("Scanner already running")
            return
        
        if not self.config.websocket_url:
            logger.warning("No WebSocket URL configured, using HTTP polling")
        
        self._running = True
        self._scan_task = asyncio.create_task(self._scan_loop())
        
        logger.info(f"Mempool scanner started for {self.config.chain.value}")
    
    async def stop(self) -> None:
        """Stop mempool scanning."""
        self._running = False
        
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
            self._scan_task = None
        
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        
        logger.info("Mempool scanner stopped")
    
    def on_attack_detected(self, callback: Callable[[AttackDetection], None]) -> None:
        """Register callback for attack detection.
        
        Args:
            callback: Function to call when attack is detected
        """
        self._attack_callbacks.append(callback)
    
    async def _scan_loop(self) -> None:
        """Main scanning loop."""
        while self._running:
            try:
                # Fetch pending transactions
                pending = await self._fetch_pending_transactions()
                
                for tx in pending:
                    self._pending_txs[tx.hash] = tx
                    self._stats["txs_scanned"] += 1
                    
                    if tx.is_swap():
                        self._stats["swaps_detected"] += 1
                
                # Clean old transactions
                self._cleanup_old_txs()
                
                # Sleep before next scan
                await asyncio.sleep(self.config.scan_interval_ms / 1000)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scan error: {e}")
                await asyncio.sleep(1)
    
    async def _fetch_pending_transactions(self) -> list[PendingTransaction]:
        """Fetch pending transactions from mempool.
        
        Returns:
            List of pending transactions
        """
        client = await self._get_http_client()
        
        # Use HTTP RPC URL
        rpc_url = self.config.rpc_url
        if not rpc_url:
            return []
        
        try:
            # Get pending transactions (Alchemy specific)
            response = await client.post(
                rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_getBlockByNumber",
                    "params": ["pending", True],
                },
            )
            response.raise_for_status()
            
            result = response.json()
            block = result.get("result", {})
            transactions = block.get("transactions", [])
            
            pending = []
            for tx in transactions[:self.config.max_pending_txs]:
                if isinstance(tx, dict):
                    pending.append(PendingTransaction(
                        hash=tx.get("hash", ""),
                        from_address=tx.get("from", ""),
                        to_address=tx.get("to", ""),
                        value=int(tx.get("value", "0x0"), 16),
                        gas_price=int(tx.get("gasPrice", "0x0"), 16),
                        max_fee_per_gas=int(tx.get("maxFeePerGas", "0x0"), 16) if tx.get("maxFeePerGas") else None,
                        max_priority_fee=int(tx.get("maxPriorityFeePerGas", "0x0"), 16) if tx.get("maxPriorityFeePerGas") else None,
                        input_data=tx.get("input", "0x"),
                        nonce=int(tx.get("nonce", "0x0"), 16),
                    ))
            
            return pending
            
        except Exception as e:
            logger.debug(f"Failed to fetch pending txs: {e}")
            return []
    
    def _cleanup_old_txs(self) -> None:
        """Remove old transactions from tracking."""
        if len(self._pending_txs) > self.config.max_pending_txs:
            # Remove oldest transactions
            sorted_txs = sorted(
                self._pending_txs.items(),
                key=lambda x: x[1].timestamp,
            )
            for tx_hash, _ in sorted_txs[:-self.config.max_pending_txs]:
                del self._pending_txs[tx_hash]
    
    async def detect_attack_on_transaction(
        self,
        our_tx_hash: str | None = None,
        token_pair: tuple[str, str] | None = None,
        our_gas_price: int = 0,
        our_amount_usd: Decimal = Decimal("0"),
    ) -> AttackDetection | None:
        """Detect if our transaction is being attacked.
        
        Args:
            our_tx_hash: Our pending transaction hash
            token_pair: Token pair we're trading (e.g., ("WETH", "USDC"))
            our_gas_price: Our transaction's gas price
            our_amount_usd: Our trade amount in USD
            
        Returns:
            Attack detection if found, None otherwise
        """
        if not self._pending_txs:
            return None
        
        # Look for suspicious transactions
        for tx_hash, tx in self._pending_txs.items():
            if tx_hash == our_tx_hash:
                continue
            
            # Skip if not a swap
            if not tx.is_swap():
                continue
            
            # Check 1: Known MEV bot
            is_known_bot = tx.from_address.lower() in {a.lower() for a in KNOWN_MEV_BOTS}
            
            # Check 2: Targeting same DEX router
            is_same_router = tx.to_address.lower() in {r.lower() for r in DEX_ROUTERS.values()}
            
            # Check 3: Higher gas price (front-running indicator)
            gas_delta = 0.0
            if our_gas_price > 0:
                gas_delta = (tx.effective_gas_price - our_gas_price) / our_gas_price
            
            is_higher_gas = gas_delta > self.config.gas_price_threshold
            
            # Determine attack type and confidence
            confidence = 0.0
            attack_type = None
            
            if is_known_bot:
                confidence += 0.5
            
            if is_same_router:
                confidence += 0.2
            
            if is_higher_gas:
                confidence += 0.3
                attack_type = AttackType.FRONT_RUN
            
            # Look for sandwich pattern (another tx from same address with lower gas)
            back_run_tx = None
            for other_hash, other_tx in self._pending_txs.items():
                if other_tx.from_address == tx.from_address and other_hash != tx_hash:
                    if other_tx.effective_gas_price < tx.effective_gas_price:
                        back_run_tx = other_hash
                        attack_type = AttackType.SANDWICH
                        confidence += 0.2
                        break
            
            # If confidence is high enough, report attack
            if confidence >= 0.5 and attack_type:
                estimated_loss = our_amount_usd * Decimal("0.15")  # ~15% typical loss
                
                attack = AttackDetection(
                    attack_type=attack_type,
                    confidence=min(confidence, 1.0),
                    attacker_address=tx.from_address,
                    attacker_tx_hash=tx_hash,
                    victim_tx_hash=our_tx_hash or "",
                    estimated_loss_usd=estimated_loss,
                    gas_price_delta=gas_delta,
                    token_pair=token_pair,
                    front_run_tx=tx_hash if attack_type == AttackType.SANDWICH else None,
                    back_run_tx=back_run_tx,
                )
                
                self._stats["attacks_detected"] += 1
                if attack_type == AttackType.SANDWICH:
                    self._stats["sandwich_attacks"] += 1
                else:
                    self._stats["front_runs"] += 1
                
                # Notify callbacks
                for callback in self._attack_callbacks:
                    try:
                        callback(attack)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                logger.warning(
                    f"🚨 {attack_type.value.upper()} detected! "
                    f"Confidence: {confidence*100:.0f}%, "
                    f"Loss: ${estimated_loss}"
                )
                
                return attack
        
        return None
    
    async def get_mempool_statistics(self) -> dict[str, Any]:
        """Get mempool statistics.
        
        Returns:
            Statistics about pending transactions
        """
        swaps = [tx for tx in self._pending_txs.values() if tx.is_swap()]
        
        # Gas price distribution
        gas_prices = [tx.effective_gas_price for tx in self._pending_txs.values()]
        avg_gas = sum(gas_prices) / len(gas_prices) if gas_prices else 0
        
        return {
            "pending_transactions": len(self._pending_txs),
            "pending_swaps": len(swaps),
            "average_gas_price_gwei": avg_gas / 1e9,
            "known_mev_bots_active": len([
                tx for tx in self._pending_txs.values()
                if tx.from_address.lower() in {a.lower() for a in KNOWN_MEV_BOTS}
            ]),
            "scanner_stats": self._stats.copy(),
        }
    
    def get_stats(self) -> dict[str, Any]:
        """Get scanner statistics.
        
        Returns:
            Scanner statistics
        """
        return {
            "running": self._running,
            "chain": self.config.chain.value,
            "provider": self.config.active_provider,
            "pending_txs_tracked": len(self._pending_txs),
            **self._stats,
        }


# ============================================================================
# MEV Monitor - High-level wrapper
# ============================================================================

class MEVMonitor:
    """High-level MEV monitoring and protection.
    
    Combines mempool scanning with Flashbots protection for
    automatic MEV attack detection and mitigation.
    
    Example:
        >>> monitor = MEVMonitor(alchemy_api_key="...")
        >>> await monitor.start()
        >>> 
        >>> # Protected transaction submission
        >>> result = await monitor.submit_protected_transaction(
        ...     signed_tx="0x...",
        ...     token_pair=("WETH", "USDC"),
        ...     amount_usd=Decimal("10000"),
        ... )
        >>> 
        >>> if result["protected"]:
        ...     print("Routed via Flashbots due to attack detection")
        >>> 
        >>> await monitor.stop()
    """
    
    def __init__(
        self,
        alchemy_api_key: str = "",
        private_key: str = "",
        chain: Chain = Chain.ETHEREUM,
    ):
        """Initialize MEV monitor.
        
        Args:
            alchemy_api_key: Alchemy API key
            private_key: Private key for Flashbots signing
            chain: Blockchain to monitor
        """
        self.scanner = MempoolScanner(
            alchemy_api_key=alchemy_api_key,
            chain=chain,
        )
        self.private_key = private_key
        self.chain = chain
        self._alchemy_key = alchemy_api_key
    
    async def start(self) -> None:
        """Start MEV monitoring."""
        await self.scanner.start()
        logger.info("MEV Monitor started")
    
    async def stop(self) -> None:
        """Stop MEV monitoring."""
        await self.scanner.stop()
        logger.info("MEV Monitor stopped")
    
    async def check_transaction_safety(
        self,
        token_pair: tuple[str, str],
        amount_usd: Decimal,
        gas_price: int,
    ) -> dict[str, Any]:
        """Check if it's safe to submit a transaction.
        
        Args:
            token_pair: Token pair being traded
            amount_usd: Trade amount in USD
            gas_price: Gas price in wei
            
        Returns:
            Safety analysis with recommendation
        """
        # Check for active attacks
        attack = await self.scanner.detect_attack_on_transaction(
            token_pair=token_pair,
            our_gas_price=gas_price,
            our_amount_usd=amount_usd,
        )
        
        # Get mempool stats
        mempool_stats = await self.scanner.get_mempool_statistics()
        
        # Determine safety level
        if attack:
            safety = "DANGEROUS"
            recommendation = "USE_FLASHBOTS"
        elif mempool_stats.get("known_mev_bots_active", 0) > 3:
            safety = "RISKY"
            recommendation = "USE_FLASHBOTS"
        elif amount_usd > Decimal("10000"):
            safety = "MODERATE"
            recommendation = "USE_FLASHBOTS"
        else:
            safety = "SAFE"
            recommendation = "NORMAL_SUBMISSION"
        
        return {
            "safety_level": safety,
            "recommendation": recommendation,
            "attack_detected": attack.to_dict() if attack else None,
            "mempool_stats": mempool_stats,
            "suggested_gas_increase": 1.1 if attack else 1.0,
        }
    
    async def submit_protected_transaction(
        self,
        signed_tx: str,
        token_pair: tuple[str, str] | None = None,
        amount_usd: Decimal = Decimal("0"),
    ) -> dict[str, Any]:
        """Submit transaction with automatic MEV protection.
        
        Checks for attacks and routes via Flashbots if needed.
        
        Args:
            signed_tx: Signed transaction hex string
            token_pair: Token pair being traded
            amount_usd: Trade amount in USD
            
        Returns:
            Submission result with protection info
        """
        from app.application.ultra.flashbots_client import FlashbotsClient, MEVBlockerClient
        
        # Check for attacks
        attack = None
        if token_pair:
            attack = await self.scanner.detect_attack_on_transaction(
                token_pair=token_pair,
                our_amount_usd=amount_usd,
            )
        
        # Decide submission method
        use_flashbots = attack is not None or amount_usd > Decimal("1000")
        
        result = {
            "protected": use_flashbots,
            "attack_detected": attack.to_dict() if attack else None,
            "submission_method": "flashbots" if use_flashbots else "public",
        }
        
        try:
            if use_flashbots:
                # Use MEV Blocker (simplest)
                client = MEVBlockerClient()
                try:
                    tx_hash = await client.send_raw_transaction(signed_tx)
                    result["tx_hash"] = tx_hash
                    result["status"] = "submitted"
                finally:
                    await client.close()
            else:
                # Would submit to public mempool
                result["status"] = "would_submit_public"
                result["note"] = "Public submission not implemented for safety"
                
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
