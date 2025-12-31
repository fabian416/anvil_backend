"""
Activity Handler for Chat - Transaction history operations.

Provides transaction history using:
- SqlaTransactionRepository for database records
- Multi-chain support
- Filtering by type, status, and chain
"""

import time
from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime, timedelta

from app.domain.transactions.ports.transaction.transaction_repository import (
    TransactionRepository,
)
from app.domain.value_objects.user_id import UserId
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType


@dataclass
class ActivityHandlerResult:
    """Result from activity handler."""

    content: str
    transactions: list[dict]
    total_count: int
    gas_spent_usd: float
    chain: Optional[str]
    latency_ms: int
    handler: str = "activity_handler"


class ActivityHandler:
    """
    Handler for activity/transaction history chat intents.

    Uses TransactionRepository to fetch real transaction data
    from the database.

    Features:
    - Transaction history retrieval
    - Filtering by chain, status, type
    - Gas cost summary
    - Explorer links
    """

    # Explorer URLs by chain
    EXPLORER_URLS = {
        "ethereum": "https://etherscan.io/tx/",
        "base": "https://basescan.org/tx/",
        "arbitrum": "https://arbiscan.io/tx/",
        "polygon": "https://polygonscan.com/tx/",
        "optimism": "https://optimistic.etherscan.io/tx/",
    }

    def __init__(self, transaction_repository: TransactionRepository):
        """
        Initialize activity handler.

        Args:
            transaction_repository: Repository for transaction data
        """
        self._tx_repo = transaction_repository

    async def get_activity(
        self,
        user_id: int,
        chain: Optional[str] = None,
        tx_type: Optional[str] = None,
        limit: int = 10,
    ) -> ActivityHandlerResult:
        """
        Get transaction activity for a user.

        Args:
            user_id: User's database ID
            chain: Filter by chain (optional)
            tx_type: Filter by transaction type (optional)
            limit: Maximum transactions to return

        Returns:
            ActivityHandlerResult with formatted content and data
        """
        start_time = time.time()

        try:
            # Fetch transactions from repository
            transactions = await self._tx_repo.get_by_user(
                user_id=UserId(user_id),
                limit=limit,
                chain=chain,
            )

            # Calculate totals
            total_count = len(transactions)
            gas_spent_usd = sum(
                float(tx.fee_usd) if tx.fee_usd else 0.0
                for tx in transactions
            )

            # Format transactions
            tx_list = [self._format_transaction(tx) for tx in transactions]

            # Generate response content
            content = self._format_activity_response(
                transactions=tx_list,
                total_count=total_count,
                gas_spent_usd=gas_spent_usd,
                chain=chain,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return ActivityHandlerResult(
                content=content,
                transactions=tx_list,
                total_count=total_count,
                gas_spent_usd=gas_spent_usd,
                chain=chain,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)

            return ActivityHandlerResult(
                content=f"⚠️ **Error Fetching Activity**\n\n{str(e)}\n\nPlease try again later.",
                transactions=[],
                total_count=0,
                gas_spent_usd=0.0,
                chain=chain,
                latency_ms=latency_ms,
            )

    def _format_transaction(self, tx: Any) -> dict:
        """Format transaction entity to dictionary."""
        # Get explorer URL
        chain_name = tx.chain.value if hasattr(tx.chain, "value") else str(tx.chain)
        explorer_base = self.EXPLORER_URLS.get(chain_name.lower(), "")
        explorer_url = f"{explorer_base}{tx.tx_hash}" if tx.tx_hash and explorer_base else None

        # Format type
        tx_type = tx.type.value if hasattr(tx.type, "value") else str(tx.type)

        # Format status
        status = tx.status.value if hasattr(tx.status, "value") else str(tx.status)

        # Format time ago
        time_ago = self._format_time_ago(tx.created_at.value if hasattr(tx.created_at, "value") else tx.created_at)

        return {
            "id": tx.id_.value if hasattr(tx.id_, "value") else tx.id_,
            "tx_hash": tx.tx_hash,
            "type": tx_type,
            "chain": chain_name,
            "status": status,
            "to_address": tx.to_address,
            "asset_in": tx.asset_in,
            "amount_in": float(tx.amount_in) if tx.amount_in else None,
            "asset_out": tx.asset_out,
            "amount_out": float(tx.amount_out) if tx.amount_out else None,
            "fee_usd": float(tx.fee_usd) if tx.fee_usd else None,
            "explorer_url": explorer_url,
            "time_ago": time_ago,
            "created_at": str(tx.created_at.value if hasattr(tx.created_at, "value") else tx.created_at),
        }

    def _format_time_ago(self, created_at: datetime) -> str:
        """Format datetime as 'X ago' string."""
        if not created_at:
            return "unknown"

        now = datetime.utcnow()
        if hasattr(created_at, "replace"):
            created_at = created_at.replace(tzinfo=None)

        diff = now - created_at

        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} min ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hours ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} days ago"
        else:
            return created_at.strftime("%Y-%m-%d")

    def _format_activity_response(
        self,
        transactions: list[dict],
        total_count: int,
        gas_spent_usd: float,
        chain: Optional[str],
    ) -> str:
        """Format activity data as chat response."""
        if not transactions:
            return self._format_no_activity_response(chain)

        chain_filter = f" on {chain.upper()}" if chain else ""
        response = f"""📜 **Recent Activity{chain_filter}**

**Last 7 Days:**

"""
        # Format each transaction
        for i, tx in enumerate(transactions[:10], 1):
            tx_type = tx.get("type", "unknown").upper()
            time_ago = tx.get("time_ago", "")
            status_emoji = "✅" if tx.get("status") == "success" else "⏳" if tx.get("status") == "pending" else "❌"

            response += f"**{i}. {tx_type}** - {time_ago} {status_emoji}\n"

            # Show amounts
            if tx.get("amount_in") and tx.get("asset_in"):
                response += f"   • {tx['amount_in']:.4f} {tx['asset_in']}"
                if tx.get("amount_out") and tx.get("asset_out"):
                    response += f" → {tx['amount_out']:.4f} {tx['asset_out']}"
                response += "\n"
            elif tx.get("to_address"):
                response += f"   • To: {tx['to_address'][:10]}...{tx['to_address'][-6:]}\n"

            # Show chain
            response += f"   • Chain: {tx.get('chain', 'unknown').capitalize()}\n"

            response += "\n"

        response += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Total Transactions:** {total_count}
**Gas Spent:** ${gas_spent_usd:.2f}

Would you like a detailed report or specific transaction details?
"""
        return response

    def _format_no_activity_response(self, chain: Optional[str]) -> str:
        """Format response when no activity found."""
        chain_text = f" on {chain.upper()}" if chain else ""
        return f"""📜 **No Recent Activity{chain_text}**

You don't have any recorded transactions yet.

**To start:**
• Deposit funds to your wallet
• Make a swap or transfer
• Earn yield in DeFi protocols

Would you like to receive funds? Say "receive" to get your deposit address.
"""
