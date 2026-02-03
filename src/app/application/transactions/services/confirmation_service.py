"""
Transaction Confirmation Service.

Background service that monitors pending transactions and updates their status
when they are confirmed on-chain.

Optionally creates portfolio snapshots when transactions are confirmed.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Callable, Awaitable

from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.entities.wallet import WalletId
from app.domain.transactions.ports.transaction.transaction_repository import (
    TransactionRepository,
)

logger = logging.getLogger(__name__)

# Type alias for portfolio snapshot callback
PortfolioSnapshotCallback = Callable[[WalletId], Awaitable[None]]


# RPC endpoints by chain type
RPC_ENDPOINTS: dict[ChainType, str] = {
    ChainType.ETHEREUM: "https://eth.llamarpc.com",
    ChainType.BASE: "https://mainnet.base.org",
    ChainType.ARBITRUM: "https://arb1.arbitrum.io/rpc",
    ChainType.POLYGON: "https://polygon-rpc.com",
    ChainType.OPTIMISM: "https://mainnet.optimism.io",
}

# Testnet RPC endpoints (for development)
TESTNET_RPC_ENDPOINTS: dict[ChainType, str] = {
    ChainType.ETHEREUM: "https://rpc.sepolia.org",  # Sepolia
    ChainType.BASE: "https://sepolia.base.org",  # Base Sepolia
}


@dataclass
class TransactionReceipt:
    """Simplified transaction receipt from blockchain."""

    status: bool  # True = success, False = reverted
    block_number: int
    gas_used: int
    effective_gas_price: int  # in wei
    block_timestamp: datetime | None = None


@dataclass
class ConfirmationResult:
    """Result of confirming a single transaction."""

    transaction_id: int
    tx_hash: str
    success: bool
    status: TransactionStatus
    block_number: int | None = None
    confirmed_at: datetime | None = None
    fee_wei: int | None = None
    error: str | None = None


class TransactionConfirmationService:
    """
    Service for confirming pending transactions on-chain.

    This service:
    1. Fetches pending transactions from the database
    2. Queries the blockchain for transaction receipts
    3. Updates transaction status based on confirmation

    Can be run as:
    - A periodic background task (asyncio loop)
    - A one-off command (CLI)
    - A scheduled job (cron/celery)
    """

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        *,
        use_testnet: bool = False,
        http_timeout: int = 30,
        on_transaction_confirmed: PortfolioSnapshotCallback | None = None,
    ):
        """
        Initialize the confirmation service.

        Args:
            transaction_repository: Repository for transaction persistence.
            use_testnet: Whether to use testnet RPC endpoints.
            http_timeout: HTTP timeout for RPC calls in seconds.
            on_transaction_confirmed: Optional callback to create portfolio snapshot
                                      when a transaction is confirmed.
        """
        self._transaction_repository = transaction_repository
        self._use_testnet = use_testnet
        self._http_timeout = http_timeout
        self._rpc_endpoints = TESTNET_RPC_ENDPOINTS if use_testnet else RPC_ENDPOINTS
        self._on_transaction_confirmed = on_transaction_confirmed

    def _get_rpc_url(self, chain: ChainType) -> str | None:
        """Get RPC URL for a chain."""
        return self._rpc_endpoints.get(chain)

    async def _fetch_receipt_via_rpc(
        self,
        rpc_url: str,
        tx_hash: str,
    ) -> TransactionReceipt | None:
        """
        Fetch transaction receipt via JSON-RPC.

        Args:
            rpc_url: RPC endpoint URL.
            tx_hash: Transaction hash to query.

        Returns:
            TransactionReceipt if found, None otherwise.
        """
        import aiohttp

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getTransactionReceipt",
            "params": [tx_hash],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    rpc_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._http_timeout),
                ) as response:
                    if response.status != 200:
                        logger.warning(f"RPC request failed: {response.status}")
                        return None

                    data = await response.json()

                    if "error" in data:
                        logger.warning(f"RPC error: {data['error']}")
                        return None

                    result = data.get("result")
                    if result is None:
                        # Transaction not yet mined
                        return None

                    # Parse receipt
                    status_hex = result.get("status", "0x0")
                    status = int(status_hex, 16) == 1

                    block_number = int(result.get("blockNumber", "0x0"), 16)
                    gas_used = int(result.get("gasUsed", "0x0"), 16)
                    effective_gas_price = int(
                        result.get("effectiveGasPrice", "0x0"), 16
                    )

                    return TransactionReceipt(
                        status=status,
                        block_number=block_number,
                        gas_used=gas_used,
                        effective_gas_price=effective_gas_price,
                    )

        except asyncio.TimeoutError:
            logger.warning(f"RPC timeout for {tx_hash[:16]}...")
            return None
        except Exception as e:
            logger.error(f"RPC error for {tx_hash[:16]}...: {e}")
            return None

    async def confirm_transaction(
        self,
        transaction_id: int,
        tx_hash: str,
        chain: ChainType,
    ) -> ConfirmationResult:
        """
        Confirm a single transaction on-chain.

        Args:
            transaction_id: Database ID of the transaction.
            tx_hash: Transaction hash to check.
            chain: Blockchain where the transaction was sent.

        Returns:
            ConfirmationResult with status and details.
        """
        rpc_url = self._get_rpc_url(chain)
        if not rpc_url:
            return ConfirmationResult(
                transaction_id=transaction_id,
                tx_hash=tx_hash,
                success=False,
                status=TransactionStatus.PENDING,
                error=f"No RPC endpoint for chain {chain.value}",
            )

        logger.debug(f"Checking transaction {tx_hash[:16]}... on {chain.value}")

        receipt = await self._fetch_receipt_via_rpc(rpc_url, tx_hash)

        if receipt is None:
            # Not yet mined
            return ConfirmationResult(
                transaction_id=transaction_id,
                tx_hash=tx_hash,
                success=True,
                status=TransactionStatus.PENDING,
            )

        # Transaction is mined
        confirmed_at = datetime.now(UTC)
        fee_wei = receipt.gas_used * receipt.effective_gas_price

        if receipt.status:
            # Success
            return ConfirmationResult(
                transaction_id=transaction_id,
                tx_hash=tx_hash,
                success=True,
                status=TransactionStatus.SUCCESS,
                block_number=receipt.block_number,
                confirmed_at=confirmed_at,
                fee_wei=fee_wei,
            )
        else:
            # Reverted
            return ConfirmationResult(
                transaction_id=transaction_id,
                tx_hash=tx_hash,
                success=True,
                status=TransactionStatus.FAILED,
                block_number=receipt.block_number,
                confirmed_at=confirmed_at,
                fee_wei=fee_wei,
                error="Transaction reverted",
            )

    async def process_pending_transactions(
        self,
        *,
        limit: int = 50,
        older_than_seconds: int | None = 10,
    ) -> list[ConfirmationResult]:
        """
        Process all pending transactions.

        Args:
            limit: Maximum number of transactions to process.
            older_than_seconds: Only process transactions older than this.

        Returns:
            List of confirmation results.
        """
        logger.info("Processing pending transactions...")

        # Fetch pending transactions
        pending = await self._transaction_repository.get_pending_transactions(
            limit=limit,
            older_than_seconds=older_than_seconds,
        )

        if not pending:
            logger.info("No pending transactions to process")
            return []

        logger.info(f"Found {len(pending)} pending transactions")

        results: list[ConfirmationResult] = []

        for tx in pending:
            if not tx.tx_hash:
                continue

            result = await self.confirm_transaction(
                transaction_id=tx.id_.value,
                tx_hash=tx.tx_hash,
                chain=tx.chain,
            )

            results.append(result)

            # If status changed, update in database
            if result.status != TransactionStatus.PENDING:
                try:
                    # Convert fee from wei to native token (for display, we use Decimal)
                    fee = None
                    if result.fee_wei:
                        fee = Decimal(result.fee_wei) / Decimal(10**18)

                    await self._transaction_repository.update_status(
                        transaction_id=tx.id_,
                        status=result.status,
                        block_number=result.block_number,
                        confirmed_at=result.confirmed_at,
                        error_message=result.error,
                    )

                    logger.info(
                        f"Transaction {tx.tx_hash[:16]}... "
                        f"confirmed: {result.status.name}"
                    )

                    # Create portfolio snapshot for confirmed transactions
                    if (
                        result.status == TransactionStatus.SUCCESS
                        and self._on_transaction_confirmed is not None
                    ):
                        try:
                            await self._on_transaction_confirmed(tx.wallet_id)
                            logger.info(
                                f"Portfolio snapshot created for wallet {tx.wallet_id.value}"
                            )
                        except Exception as snapshot_error:
                            # Don't fail the confirmation if snapshot fails
                            logger.warning(
                                f"Failed to create portfolio snapshot: {snapshot_error}"
                            )

                except Exception as e:
                    logger.error(
                        f"Failed to update transaction {tx.tx_hash[:16]}...: {e}"
                    )

        # Summary
        confirmed = sum(1 for r in results if r.status == TransactionStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == TransactionStatus.FAILED)
        pending_count = sum(1 for r in results if r.status == TransactionStatus.PENDING)

        logger.info(
            f"Processed {len(results)} transactions: "
            f"{confirmed} confirmed, {failed} failed, {pending_count} still pending"
        )

        return results

    async def run_loop(
        self,
        *,
        interval_seconds: int = 30,
        limit_per_batch: int = 50,
    ) -> None:
        """
        Run continuous confirmation loop.

        Args:
            interval_seconds: Seconds between processing batches.
            limit_per_batch: Max transactions per batch.
        """
        logger.info(
            f"Starting transaction confirmation loop "
            f"(interval: {interval_seconds}s, batch: {limit_per_batch})"
        )

        while True:
            try:
                await self.process_pending_transactions(
                    limit=limit_per_batch,
                    older_than_seconds=10,
                )
            except Exception as e:
                logger.error(f"Error in confirmation loop: {e}")

            await asyncio.sleep(interval_seconds)
