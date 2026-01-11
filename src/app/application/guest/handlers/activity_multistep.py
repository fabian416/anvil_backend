"""
Activity Multi-Step Handler for Guest Chat.

Provides demo transaction history for guests:
- Shows demo recent transactions
- Transaction types (swap, send, receive, buy)
- Status and amounts
- Signup CTA for real activity access

Guest experience with demo data.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class ActivityMultiStepHandler:
    """Handles activity/transaction history display for guest users."""

    # Demo transaction history
    DEMO_TRANSACTIONS = [
        {
            "type": "swap",
            "from_token": "USDC",
            "to_token": "ETH",
            "from_amount": 1000.0,
            "to_amount": 0.51,
            "status": "completed",
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "emoji": "🔄",
            "tx_hash": "0x1a2b3c...7d8e9f",
        },
        {
            "type": "receive",
            "token": "BTC",
            "amount": 0.05,
            "from": "External Wallet",
            "status": "completed",
            "timestamp": datetime.utcnow() - timedelta(hours=12),
            "emoji": "📥",
            "tx_hash": "0x2b3c4d...8e9f0a",
        },
        {
            "type": "send",
            "token": "SOL",
            "amount": 25.0,
            "to": "Friend's Wallet",
            "status": "completed",
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "emoji": "📤",
            "tx_hash": "0x3c4d5e...9f0a1b",
        },
        {
            "type": "buy",
            "token": "USDC",
            "amount": 5000.0,
            "payment_method": "Credit Card",
            "status": "completed",
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "emoji": "💳",
            "tx_hash": "0x4d5e6f...0a1b2c",
        },
        {
            "type": "swap",
            "from_token": "ETH",
            "to_token": "MATIC",
            "from_amount": 1.0,
            "to_amount": 3000.0,
            "status": "completed",
            "timestamp": datetime.utcnow() - timedelta(days=3),
            "emoji": "🔄",
            "tx_hash": "0x5e6f7a...1b2c3d",
        },
        {
            "type": "receive",
            "token": "USDC",
            "amount": 500.0,
            "from": "Airdrop",
            "status": "completed",
            "timestamp": datetime.utcnow() - timedelta(days=5),
            "emoji": "📥",
            "tx_hash": "0x6f7a8b...2c3d4e",
        },
    ]

    async def handle_flow(
        self,
        content: str,
        language: str,
        is_authenticated: bool,
    ) -> dict[str, Any]:
        """
        Handle activity display for guests.

        Shows demo transaction history with:
        - Recent transactions
        - Transaction types and statuses
        - Amounts and timestamps
        """
        return await self._show_demo_activity(language)

    async def _show_demo_activity(self, language: str) -> dict[str, Any]:
        """Show demo activity/transaction history for guests."""
        messages = {
            "en": {
                "title": "📜 Transaction History",
                "demo_notice": "Demo Mode - Sign up to see your real transactions",
                "recent_activity": "Recent Activity",
                "type": "Type",
                "amount": "Amount",
                "status": "Status",
                "time": "Time",
                "details": "Details",
                "completed": "Completed",
                "pending": "Pending",
                "failed": "Failed",
                "swapped": "Swapped",
                "for": "for",
                "received": "Received",
                "from": "from",
                "sent": "Sent",
                "to": "to",
                "bought": "Bought",
                "with": "with",
                "signup_title": "Want to see your real transactions?",
                "signup_text": "Connect your wallet to view complete transaction history with blockchain verification.",
            },
            "es": {
                "title": "📜 Historial de Transacciones",
                "demo_notice": "Modo Demo - Regístrate para ver tus transacciones reales",
                "recent_activity": "Actividad Reciente",
                "type": "Tipo",
                "amount": "Cantidad",
                "status": "Estado",
                "time": "Tiempo",
                "details": "Detalles",
                "completed": "Completado",
                "pending": "Pendiente",
                "failed": "Fallido",
                "swapped": "Intercambiado",
                "for": "por",
                "received": "Recibido",
                "from": "de",
                "sent": "Enviado",
                "to": "a",
                "bought": "Comprado",
                "with": "con",
                "signup_title": "¿Quieres ver tus transacciones reales?",
                "signup_text": "Conecta tu billetera para ver el historial completo de transacciones con verificación blockchain.",
            },
            "pt": {
                "title": "📜 Histórico de Transações",
                "demo_notice": "Modo Demo - Cadastre-se para ver suas transações reais",
                "recent_activity": "Atividade Recente",
                "type": "Tipo",
                "amount": "Quantia",
                "status": "Status",
                "time": "Tempo",
                "details": "Detalhes",
                "completed": "Concluído",
                "pending": "Pendente",
                "failed": "Falhou",
                "swapped": "Trocado",
                "for": "por",
                "received": "Recebido",
                "from": "de",
                "sent": "Enviado",
                "to": "para",
                "bought": "Comprado",
                "with": "com",
                "signup_title": "Quer ver suas transações reais?",
                "signup_text": "Conecte sua carteira para ver o histórico completo de transações com verificação blockchain.",
            },
            "zh": {
                "title": "📜 交易历史",
                "demo_notice": "演示模式 - 注册查看您的真实交易",
                "recent_activity": "最近活动",
                "type": "类型",
                "amount": "数量",
                "status": "状态",
                "time": "时间",
                "details": "详情",
                "completed": "已完成",
                "pending": "待处理",
                "failed": "失败",
                "swapped": "已交换",
                "for": "为",
                "received": "已收到",
                "from": "从",
                "sent": "已发送",
                "to": "到",
                "bought": "已购买",
                "with": "用",
                "signup_title": "想要查看您的真实交易？",
                "signup_text": "连接您的钱包以查看完整的交易历史记录和区块链验证。",
            },
        }

        msg = messages.get(language, messages["en"])

        # Build transactions list
        transactions_text = ""
        for i, tx in enumerate(self.DEMO_TRANSACTIONS, 1):
            time_ago = self._format_time_ago(tx["timestamp"], language)
            status_emoji = "✅" if tx["status"] == "completed" else "⏳" if tx["status"] == "pending" else "❌"

            # Format transaction details based on type
            if tx["type"] == "swap":
                detail = f"{msg['swapped']} {tx['from_amount']:.2f} {tx['from_token']} {msg['for']} {tx['to_amount']:.2f} {tx['to_token']}"
            elif tx["type"] == "receive":
                detail = f"{msg['received']} {tx['amount']:.2f} {tx['token']} {msg['from']} {tx.get('from', 'Unknown')}"
            elif tx["type"] == "send":
                detail = f"{msg['sent']} {tx['amount']:.2f} {tx['token']} {msg['to']} {tx.get('to', 'Unknown')}"
            elif tx["type"] == "buy":
                detail = f"{msg['bought']} {tx['amount']:.2f} {tx['token']} {msg['with']} {tx.get('payment_method', 'Card')}"
            else:
                detail = f"{tx['type'].title()} transaction"

            transactions_text += f"""
**{i}.** {tx['emoji']} **{tx['type'].upper()}** {status_emoji}
   • {detail}
   • {msg['time']}: {time_ago}
   • TX: `{tx['tx_hash']}`
"""

        content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{msg['title']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔔 **{msg['demo_notice']}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**📋 {msg['recent_activity']}** ({len(self.DEMO_TRANSACTIONS)} transactions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{transactions_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**🔗 {msg['signup_title']}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{msg['signup_text']}

👉 **Sign up now** → /signup
"""

        # Build enrichment data
        transactions = [
            {
                "type": tx["type"],
                "status": tx["status"],
                "timestamp": tx["timestamp"].isoformat(),
                "tx_hash": tx["tx_hash"],
                **({
                    "from_token": tx["from_token"],
                    "to_token": tx["to_token"],
                    "from_amount": tx["from_amount"],
                    "to_amount": tx["to_amount"],
                } if tx["type"] == "swap" else {}),
                **({
                    "token": tx["token"],
                    "amount": tx["amount"],
                } if tx["type"] in ["receive", "send", "buy"] else {}),
            }
            for tx in self.DEMO_TRANSACTIONS
        ]

        return {
            "content": content,
            "enrichment": {
                "transactions": transactions,
                "transaction_count": len(self.DEMO_TRANSACTIONS),
                "types": list(set(tx["type"] for tx in self.DEMO_TRANSACTIONS)),
            },
            "requires_registration": True,
        }

    def _format_time_ago(self, timestamp: datetime, language: str) -> str:
        """Format timestamp as relative time."""
        now = datetime.utcnow()
        delta = now - timestamp

        if delta.days > 0:
            if language == "es":
                return f"hace {delta.days} día{'s' if delta.days != 1 else ''}"
            elif language == "pt":
                return f"há {delta.days} dia{'s' if delta.days != 1 else ''}"
            elif language == "zh":
                return f"{delta.days}天前"
            else:
                return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            if language == "es":
                return f"hace {hours} hora{'s' if hours != 1 else ''}"
            elif language == "pt":
                return f"há {hours} hora{'s' if hours != 1 else ''}"
            elif language == "zh":
                return f"{hours}小时前"
            else:
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            minutes = delta.seconds // 60
            if language == "es":
                return f"hace {minutes} minuto{'s' if minutes != 1 else ''}"
            elif language == "pt":
                return f"há {minutes} minuto{'s' if minutes != 1 else ''}"
            elif language == "zh":
                return f"{minutes}分钟前"
            else:
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
