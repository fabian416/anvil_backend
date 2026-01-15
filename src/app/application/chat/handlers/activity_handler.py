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
from datetime import datetime, timedelta, UTC

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
    language: str = "en"
    handler: str = "activity_handler"
    pending_action: str | None = None  # For multi-turn flows


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
        language: str = "en",
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
                language=language,
            )

            latency_ms = int((time.time() - start_time) * 1000)
            
            # Set pending_action if no transactions found
            pending_action = None
            if not tx_list:
                pending_action = "activity_no_activity"

            return ActivityHandlerResult(
                content=content,
                transactions=tx_list,
                total_count=total_count,
                gas_spent_usd=gas_spent_usd,
                chain=chain,
                latency_ms=latency_ms,
                language=language,
                pending_action=pending_action,
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
                language=language,
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

        now = datetime.now(UTC)
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
        language: str = "en",
    ) -> str:
        """Format activity data as chat response with improved formatting."""
        if not transactions:
            return self._format_no_activity_response(chain, language)

        activity_msgs = {
            "en": {
                "title": "Recent Activity",
                "last_7_days": "Last 7 Days",
                "total_transactions": "Total Transactions",
                "gas_spent": "Gas Spent",
                "question": "Would you like a detailed report or specific transaction details?",
            },
            "es": {
                "title": "Actividad Reciente",
                "last_7_days": "Últimos 7 Días",
                "total_transactions": "Total de Transacciones",
                "gas_spent": "Gas Gastado",
                "question": "¿Te gustaría un reporte detallado o detalles de una transacción específica?",
            },
            "pt": {
                "title": "Atividade Recente",
                "last_7_days": "Últimos 7 Dias",
                "total_transactions": "Total de Transações",
                "gas_spent": "Gas Gasto",
                "question": "Gostaria de um relatório detalhado ou detalhes de uma transação específica?",
            },
            "zh": {
                "title": "最近活动",
                "last_7_days": "最近7天",
                "total_transactions": "总交易数",
                "gas_spent": "Gas 花费",
                "question": "您想要详细报告还是特定交易的详细信息？",
            },
        }
        
        msgs = activity_msgs.get(language, activity_msgs["en"])
        chain_filter = f" on {chain.upper()}" if chain else ""
        
        response = f"""📜 **{msgs["title"]}{chain_filter}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msgs["last_7_days"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

**{msgs["total_transactions"]}:** {total_count}
**{msgs["gas_spent"]}:** ${gas_spent_usd:.2f}

💡 {msgs["question"]}
"""
        return response

    def _format_no_activity_response(self, chain: Optional[str], language: str = "en") -> str:
        """Format response when no activity found with improved formatting."""
        no_activity_msgs = {
            "en": {
                "title": "No Recent Activity",
                "message": "You don't have any recorded transactions yet.",
                "header": "To get started:",
                "options": [
                    ("📥", "Receive funds", "Get your deposit address to start"),
                    ("🔄", "Make a swap", "Exchange tokens via DEX aggregators"),
                    ("💎", "Earn yield", "Deposit into DeFi protocols for yield")
                ]
            },
            "es": {
                "title": "Sin Actividad Reciente",
                "message": "Aún no tienes transacciones registradas.",
                "header": "Para comenzar:",
                "options": [
                    ("📥", "Recibir fondos", "Obtén tu dirección de depósito para comenzar"),
                    ("🔄", "Hacer un swap", "Intercambia tokens vía agregadores DEX"),
                    ("💎", "Ganar rendimiento", "Deposita en protocolos DeFi para obtener rendimiento")
                ]
            },
            "pt": {
                "title": "Sem Atividade Recente",
                "message": "Você ainda não tem transações registradas.",
                "header": "Para começar:",
                "options": [
                    ("📥", "Receber fundos", "Obtenha seu endereço de depósito para começar"),
                    ("🔄", "Fazer um swap", "Troque tokens via agregadores DEX"),
                    ("💎", "Ganhar rendimento", "Deposite em protocolos DeFi para obter rendimento")
                ]
            },
            "zh": {
                "title": "无最近活动",
                "message": "您还没有任何已记录的交易。",
                "header": "开始使用:",
                "options": [
                    ("📥", "接收资金", "获取您的存款地址以开始"),
                    ("🔄", "进行交换", "通过 DEX 聚合器交换代币"),
                    ("💎", "赚取收益", "存入 DeFi 协议以获得收益")
                ]
            },
        }
        
        msgs = no_activity_msgs.get(language, no_activity_msgs["en"])
        chain_text = f" on {chain.upper()}" if chain else ""
        options_text = "\n".join([
            f"**{i}.** {emoji} **{title}**\n   {details}" 
            for i, (emoji, title, details) in enumerate(msgs["options"], 1)
        ])
        
        return f"""📜 **{msgs["title"]}{chain_text}**

{msgs["message"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msgs["header"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{options_text}

💬 **Reply with the number (1, 2, or 3) to continue.**
"""
