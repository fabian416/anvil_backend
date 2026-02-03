"""
Portfolio Multi-Step Handler for Guest Chat.

Provides demo portfolio view for guests:
- Shows demo token holdings
- Portfolio performance metrics
- Asset allocation breakdown
- Signup CTA for real portfolio access

Guest experience with demo data.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PortfolioMultiStepHandler:
    """Handles portfolio display for guest users."""

    # Demo portfolio holdings
    DEMO_HOLDINGS = [
        {
            "token": "USDC",
            "symbol": "USDC",
            "amount": 5000.00,
            "value_usd": 5000.00,
            "emoji": "💵",
            "change_24h": 0.1,
        },
        {
            "token": "Ethereum",
            "symbol": "ETH",
            "amount": 2.5,
            "value_usd": 4875.00,
            "emoji": "Ξ",
            "change_24h": 3.2,
        },
        {
            "token": "Bitcoin",
            "symbol": "BTC",
            "amount": 0.1,
            "value_usd": 4500.00,
            "emoji": "₿",
            "change_24h": 1.8,
        },
        {
            "token": "Solana",
            "symbol": "SOL",
            "amount": 150.0,
            "value_usd": 4875.00,
            "emoji": "◎",
            "change_24h": -2.1,
        },
        {
            "token": "Polygon",
            "symbol": "MATIC",
            "amount": 3500.0,
            "value_usd": 2275.00,
            "emoji": "🔷",
            "change_24h": 5.4,
        },
    ]

    async def handle_flow(
        self,
        content: str,
        language: str,
        is_authenticated: bool,
    ) -> dict[str, Any]:
        """
        Handle portfolio display for guests.

        Shows demo portfolio with:
        - Total portfolio value
        - Token holdings breakdown
        - Performance metrics
        - Asset allocation
        """
        return await self._show_demo_portfolio(language)

    async def _show_demo_portfolio(self, language: str) -> dict[str, Any]:
        """Show demo portfolio for guests."""
        # Calculate totals
        total_value = sum(h["value_usd"] for h in self.DEMO_HOLDINGS)

        # Calculate 24h change
        total_change_24h = sum(
            h["value_usd"] * (h["change_24h"] / 100) for h in self.DEMO_HOLDINGS
        )
        change_pct_24h = (total_change_24h / total_value) * 100

        messages = {
            "en": {
                "title": "💼 Your Portfolio",
                "demo_notice": "Demo Mode - Sign up to see your real portfolio",
                "total_value": "Total Portfolio Value",
                "change_24h": "24h Change",
                "holdings_title": "Holdings",
                "allocation_title": "Asset Allocation",
                "performance_title": "Performance Highlights",
                "top_performer": "Top Performer",
                "diversification": "Diversification",
                "assets": "assets",
                "signup_title": "Want to see your real portfolio?",
                "signup_text": "Connect your wallet to view real-time balances, performance tracking, and portfolio analytics.",
            },
            "es": {
                "title": "💼 Tu Portafolio",
                "demo_notice": "Modo Demo - Regístrate para ver tu portafolio real",
                "total_value": "Valor Total del Portafolio",
                "change_24h": "Cambio 24h",
                "holdings_title": "Holdings",
                "allocation_title": "Asignación de Activos",
                "performance_title": "Destacados de Rendimiento",
                "top_performer": "Mejor Rendimiento",
                "diversification": "Diversificación",
                "assets": "activos",
                "signup_title": "¿Quieres ver tu portafolio real?",
                "signup_text": "Conecta tu billetera para ver balances en tiempo real, seguimiento de rendimiento y análisis de portafolio.",
            },
            "pt": {
                "title": "💼 Seu Portfólio",
                "demo_notice": "Modo Demo - Cadastre-se para ver seu portfólio real",
                "total_value": "Valor Total do Portfólio",
                "change_24h": "Mudança 24h",
                "holdings_title": "Holdings",
                "allocation_title": "Alocação de Ativos",
                "performance_title": "Destaques de Desempenho",
                "top_performer": "Melhor Desempenho",
                "diversification": "Diversificação",
                "assets": "ativos",
                "signup_title": "Quer ver seu portfólio real?",
                "signup_text": "Conecte sua carteira para ver saldos em tempo real, rastreamento de desempenho e análise de portfólio.",
            },
            "zh": {
                "title": "💼 您的投资组合",
                "demo_notice": "演示模式 - 注册查看您的真实投资组合",
                "total_value": "投资组合总价值",
                "change_24h": "24小时变化",
                "holdings_title": "持仓",
                "allocation_title": "资产配置",
                "performance_title": "业绩亮点",
                "top_performer": "最佳表现",
                "diversification": "多元化",
                "assets": "资产",
                "signup_title": "想要查看您的真实投资组合？",
                "signup_text": "连接您的钱包以查看实时余额、绩效跟踪和投资组合分析。",
            },
        }

        msg = messages.get(language, messages["en"])

        # Find top performer
        top_performer = max(self.DEMO_HOLDINGS, key=lambda h: h["change_24h"])

        # Build holdings list
        holdings_text = ""
        for holding in self.DEMO_HOLDINGS:
            allocation_pct = (holding["value_usd"] / total_value) * 100
            change_emoji = (
                "📈"
                if holding["change_24h"] > 0
                else "📉"
                if holding["change_24h"] < 0
                else "➡️"
            )
            change_sign = "+" if holding["change_24h"] > 0 else ""

            holdings_text += f"""
{holding["emoji"]} **{holding["token"]} ({holding["symbol"]})**
   • Amount: {holding["amount"]:,.2f} {holding["symbol"]}
   • Value: ${holding["value_usd"]:,.2f}
   • Allocation: {allocation_pct:.1f}%
   • 24h: {change_emoji} {change_sign}{holding["change_24h"]:.1f}%
"""

        change_emoji = (
            "📈" if change_pct_24h > 0 else "📉" if change_pct_24h < 0 else "➡️"
        )
        change_sign = "+" if change_pct_24h > 0 else ""

        content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{msg["title"]}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔔 **{msg["demo_notice"]}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**📊 {msg["total_value"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **${total_value:,.2f}**
{change_emoji} **{msg["change_24h"]}**: {change_sign}${abs(total_change_24h):,.2f} ({change_sign}{change_pct_24h:.2f}%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**💎 {msg["holdings_title"]}** ({len(self.DEMO_HOLDINGS)} {msg["assets"]})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{holdings_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**🎯 {msg["performance_title"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 **{msg["top_performer"]}**: {top_performer["emoji"]} {top_performer["symbol"]} (+{top_performer["change_24h"]:.1f}%)
🎲 **{msg["diversification"]}**: {len(self.DEMO_HOLDINGS)} {msg["assets"]} across stablecoins, L1s, and L2s

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**🔗 {msg["signup_title"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{msg["signup_text"]}

👉 **Sign up now**
"""

        # Build enrichment data
        balances = [
            {
                "token": h["symbol"],
                "amount": h["amount"],
                "value_usd": h["value_usd"],
                "change_24h": h["change_24h"],
            }
            for h in self.DEMO_HOLDINGS
        ]

        return {
            "content": content,
            "enrichment": {
                "portfolio": {
                    "total_value_usd": total_value,
                    "change_24h_usd": total_change_24h,
                    "change_24h_pct": change_pct_24h,
                    "holdings_count": len(self.DEMO_HOLDINGS),
                    "top_performer": {
                        "token": top_performer["symbol"],
                        "change_24h": top_performer["change_24h"],
                    },
                },
                "balances": balances,
                "total_value": total_value,
            },
            "requires_registration": True,
        }
