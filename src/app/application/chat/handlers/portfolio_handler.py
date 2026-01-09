"""
Portfolio Handler for Chat - User portfolio and balance operations.

Provides real-time portfolio data using:
- PortfolioService for on-chain balance fetching
- DeFiLlama for USD pricing
- Multi-chain support (Ethereum, Base, Arbitrum, etc.)
"""

import time
from dataclasses import dataclass
from typing import Optional

from app.application.portfolio.portfolio_service import PortfolioService, PortfolioDTO
from app.domain.enums.chain_type import ChainType


@dataclass
class PortfolioHandlerResult:
    """Result from portfolio handler."""

    content: str
    portfolio: Optional[dict]
    total_usd: float
    chain: str
    latency_ms: int
    language: str = "en"
    handler: str = "portfolio_handler"
    pending_action: str | None = None  # For multi-turn flows


@dataclass
class BalanceHandlerResult:
    """Result from balance handler."""

    content: str
    total_usd: float
    tokens: list[dict]
    native_balance: float
    native_symbol: str
    chain: str
    latency_ms: int
    language: str = "en"
    handler: str = "balance_handler"
    pending_action: str | None = None  # For multi-turn flows


class PortfolioHandler:
    """
    Handler for portfolio-related chat intents.

    Uses PortfolioService to fetch real on-chain balances
    and USD prices from DeFiLlama.

    Features:
    - Real-time balance fetching via RPC
    - Multi-chain support
    - USD value calculation
    - Token breakdown
    """

    def __init__(self, portfolio_service: PortfolioService):
        """
        Initialize portfolio handler.

        Args:
            portfolio_service: Service for fetching portfolio data
        """
        self._portfolio_service = portfolio_service

    async def get_portfolio(
        self,
        wallet_address: str,
        chain: str = "base",
        language: str = "en",
    ) -> PortfolioHandlerResult:
        """
        Get full portfolio for a wallet address.

        Args:
            wallet_address: User's wallet address
            chain: Blockchain (ethereum, base, etc.)

        Returns:
            PortfolioHandlerResult with formatted content and data
        """
        start_time = time.time()

        # Map chain string to ChainType
        chain_type = self._get_chain_type(chain)

        # Fetch portfolio from service
        portfolio = await self._portfolio_service.get_portfolio_by_address(
            address=wallet_address,
            chain=chain_type,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        if not portfolio:
            return PortfolioHandlerResult(
                content=self._format_no_portfolio_response(wallet_address, chain, language),
                portfolio=None,
                total_usd=0.0,
                chain=chain,
                latency_ms=latency_ms,
                language=language,
                pending_action="portfolio_no_portfolio",
            )

        # Format response
        content = self._format_portfolio_response(portfolio, language)

        return PortfolioHandlerResult(
            content=content,
            portfolio=self._portfolio_to_dict(portfolio),
            total_usd=portfolio.total_usd,
            chain=portfolio.chain,
            latency_ms=latency_ms,
            language=language,
        )

    async def get_balance(
        self,
        wallet_address: str,
        chain: str = "base",
        language: str = "en",
    ) -> BalanceHandlerResult:
        """
        Get balance summary for a wallet address.

        Args:
            wallet_address: User's wallet address
            chain: Blockchain (ethereum, base, etc.)

        Returns:
            BalanceHandlerResult with formatted content and data
        """
        start_time = time.time()

        chain_type = self._get_chain_type(chain)

        portfolio = await self._portfolio_service.get_portfolio_by_address(
            address=wallet_address,
            chain=chain_type,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        if not portfolio:
            return BalanceHandlerResult(
                content=self._format_no_balance_response(wallet_address, chain, language),
                total_usd=0.0,
                tokens=[],
                native_balance=0.0,
                native_symbol="ETH",
                chain=chain,
                latency_ms=latency_ms,
                language=language,
                pending_action="balance_no_balance",
            )

        content = self._format_balance_response(portfolio, language)

        return BalanceHandlerResult(
            content=content,
            total_usd=portfolio.total_usd,
            tokens=portfolio.tokens,
            native_balance=portfolio.native_balance,
            native_symbol=portfolio.native_symbol,
            chain=portfolio.chain,
            latency_ms=latency_ms,
            language=language,
        )

    def _get_chain_type(self, chain: str) -> ChainType:
        """Convert chain string to ChainType enum."""
        chain_map = {
            "ethereum": ChainType.ETHEREUM,
            "base": ChainType.BASE,
            "arbitrum": ChainType.ARBITRUM,
            "polygon": ChainType.POLYGON,
            "optimism": ChainType.OPTIMISM,
        }
        return chain_map.get(chain.lower(), ChainType.BASE)

    def _format_portfolio_response(self, portfolio: PortfolioDTO, language: str = "en") -> str:
        """Format portfolio data as chat response with improved formatting."""
        chain_emoji = self._get_chain_emoji(portfolio.chain)
        
        portfolio_msgs = {
            "en": {
                "title": f"Your Portfolio on {portfolio.chain.upper()}",
                "total_value": "Total Value",
                "tokens": "TOKENS",
                "wallet": "Wallet",
                "last_updated": "Last Updated",
                "question": "Would you like portfolio optimization recommendations?",
            },
            "es": {
                "title": f"Tu Portafolio en {portfolio.chain.upper()}",
                "total_value": "Valor Total",
                "tokens": "TOKENS",
                "wallet": "Billetera",
                "last_updated": "Última Actualización",
                "question": "¿Te gustaría recibir recomendaciones de optimización de portafolio?",
            },
            "pt": {
                "title": f"Seu Portfólio em {portfolio.chain.upper()}",
                "total_value": "Valor Total",
                "tokens": "TOKENS",
                "wallet": "Carteira",
                "last_updated": "Última Atualização",
                "question": "Gostaria de recomendações de otimização de portfólio?",
            },
            "zh": {
                "title": f"您在 {portfolio.chain.upper()} 上的投资组合",
                "total_value": "总价值",
                "tokens": "代币",
                "wallet": "钱包",
                "last_updated": "最后更新",
                "question": "您想要投资组合优化建议吗？",
            },
        }
        
        msgs = portfolio_msgs.get(language, portfolio_msgs["en"])

        response = f"""{chain_emoji} **{msgs["title"]}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msgs["total_value"]}:** ${portfolio.total_usd:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs["tokens"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        # Native token
        if portfolio.native_balance > 0:
            native_usd = portfolio.native_usd_value or 0
            pct = (native_usd / portfolio.total_usd * 100) if portfolio.total_usd > 0 else 0
            response += f"• **{portfolio.native_symbol}**: {portfolio.native_balance:.4f} (${native_usd:,.2f}) - {pct:.1f}%\n"

        # ERC-20 tokens
        for token in sorted(portfolio.tokens, key=lambda t: t.get("usd_value", 0) or 0, reverse=True):
            amount = token.get("amount", 0)
            usd_value = token.get("usd_value", 0) or 0
            symbol = token.get("symbol", "???")
            pct = token.get("percentage", 0)

            if usd_value > 0.01:  # Only show tokens worth more than $0.01
                response += f"• **{symbol}**: {amount:,.4f} (${usd_value:,.2f}) - {pct:.1f}%\n"

        response += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs["wallet"]}:** `{portfolio.wallet_address[:8]}...{portfolio.wallet_address[-6:]}`
**{msgs["last_updated"]}:** {portfolio.captured_at[:19].replace('T', ' ')} UTC

💡 {msgs["question"]}
"""
        return response

    def _format_balance_response(self, portfolio: PortfolioDTO, language: str = "en") -> str:
        """Format balance data as chat response with improved formatting."""
        chain_emoji = self._get_chain_emoji(portfolio.chain)
        
        balance_msgs = {
            "en": {
                "title": "Your Balance",
                "total_value": "Total Value",
                "assets": "Assets",
                "last_updated": "Last updated",
                "question": "Would you like to see your full portfolio or transaction history?",
            },
            "es": {
                "title": "Tu Balance",
                "total_value": "Valor Total",
                "assets": "Activos",
                "last_updated": "Última actualización",
                "question": "¿Te gustaría ver tu portafolio completo o historial de transacciones?",
            },
            "pt": {
                "title": "Seu Saldo",
                "total_value": "Valor Total",
                "assets": "Ativos",
                "last_updated": "Última atualização",
                "question": "Gostaria de ver seu portfólio completo ou histórico de transações?",
            },
            "zh": {
                "title": "您的余额",
                "total_value": "总价值",
                "assets": "资产",
                "last_updated": "最后更新",
                "question": "您想查看完整的投资组合或交易历史吗？",
            },
        }
        
        msgs = balance_msgs.get(language, balance_msgs["en"])

        response = f"""{chain_emoji} **{msgs["title"]}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msgs["total_value"]}:** ${portfolio.total_usd:,.2f} USD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**{msgs["assets"]}:**
"""
        # Native token
        if portfolio.native_balance > 0:
            native_usd = portfolio.native_usd_value or 0
            response += f"• {portfolio.native_balance:.4f} {portfolio.native_symbol} (${native_usd:,.2f})\n"

        # Top tokens by value
        for token in sorted(portfolio.tokens, key=lambda t: t.get("usd_value", 0) or 0, reverse=True)[:5]:
            amount = token.get("amount", 0)
            usd_value = token.get("usd_value", 0) or 0
            symbol = token.get("symbol", "???")

            if usd_value > 0.01:
                response += f"• {amount:,.2f} {symbol} (${usd_value:,.2f})\n"

        response += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*{msgs["last_updated"]}: just now*

💡 {msgs["question"]}
"""
        return response

    def _format_no_portfolio_response(self, wallet_address: str, chain: str, language: str = "en") -> str:
        """Format response when no portfolio found with improved formatting."""
        no_portfolio_msgs = {
            "en": {
                "title": "Portfolio Not Found",
                "message": f"I couldn't find any assets for wallet `{wallet_address[:10]}...` on {chain.upper()}.",
                "header": "What would you like to try?",
                "options": [
                    ("🌐", "Try a different chain", "Ethereum, Base, Arbitrum, Polygon, Optimism"),
                    ("📥", "Receive funds", "Get your deposit address to start"),
                    ("💡", "Check back later", "Assets may appear after transactions")
                ]
            },
            "es": {
                "title": "Portafolio No Encontrado",
                "message": f"No pude encontrar activos para la billetera `{wallet_address[:10]}...` en {chain.upper()}.",
                "header": "¿Qué te gustaría intentar?",
                "options": [
                    ("🌐", "Probar otra cadena", "Ethereum, Base, Arbitrum, Polygon, Optimism"),
                    ("📥", "Recibir fondos", "Obtén tu dirección de depósito para comenzar"),
                    ("💡", "Verificar más tarde", "Los activos pueden aparecer después de transacciones")
                ]
            },
            "pt": {
                "title": "Portfólio Não Encontrado",
                "message": f"Não consegui encontrar ativos para a carteira `{wallet_address[:10]}...` em {chain.upper()}.",
                "header": "O que você gostaria de tentar?",
                "options": [
                    ("🌐", "Tentar outra rede", "Ethereum, Base, Arbitrum, Polygon, Optimism"),
                    ("📥", "Receber fundos", "Obtenha seu endereço de depósito para começar"),
                    ("💡", "Verificar mais tarde", "Os ativos podem aparecer após transações")
                ]
            },
            "zh": {
                "title": "未找到投资组合",
                "message": f"在 {chain.upper()} 上找不到钱包 `{wallet_address[:10]}...` 的任何资产。",
                "header": "您想尝试什么？",
                "options": [
                    ("🌐", "尝试其他链", "Ethereum, Base, Arbitrum, Polygon, Optimism"),
                    ("📥", "接收资金", "获取您的存款地址以开始"),
                    ("💡", "稍后查看", "资产可能在交易后出现")
                ]
            },
        }
        
        msgs = no_portfolio_msgs.get(language, no_portfolio_msgs["en"])
        options_text = "\n".join([
            f"**{i}.** {emoji} **{title}**\n   {details}" 
            for i, (emoji, title, details) in enumerate(msgs["options"], 1)
        ])
        
        return f"""📊 **{msgs["title"]}**

{msgs["message"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msgs["header"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{options_text}

💬 **Reply with the number (1, 2, or 3) to continue.**
"""

    def _format_no_balance_response(self, wallet_address: str, chain: str, language: str = "en") -> str:
        """Format response when no balance found with improved formatting."""
        no_balance_msgs = {
            "en": {
                "title": "No Balance Found",
                "message": f"I couldn't find any balance for wallet `{wallet_address[:10]}...` on {chain.upper()}.",
                "header": "What would you like to do?",
                "options": [
                    ("🌐", "Try a different chain", "Ethereum, Base, Arbitrum, Polygon, Optimism"),
                    ("📥", "Receive funds", "Get your deposit address to start receiving"),
                    ("💡", "Check back later", "Balance may appear after transactions")
                ]
            },
            "es": {
                "title": "Balance No Encontrado",
                "message": f"No pude encontrar balance para la billetera `{wallet_address[:10]}...` en {chain.upper()}.",
                "header": "¿Qué te gustaría hacer?",
                "options": [
                    ("🌐", "Probar otra cadena", "Ethereum, Base, Arbitrum, Polygon, Optimism"),
                    ("📥", "Recibir fondos", "Obtén tu dirección de depósito para comenzar a recibir"),
                    ("💡", "Verificar más tarde", "El balance puede aparecer después de transacciones")
                ]
            },
            "pt": {
                "title": "Saldo Não Encontrado",
                "message": f"Não consegui encontrar saldo para a carteira `{wallet_address[:10]}...` em {chain.upper()}.",
                "header": "O que você gostaria de fazer?",
                "options": [
                    ("🌐", "Tentar outra rede", "Ethereum, Base, Arbitrum, Polygon, Optimism"),
                    ("📥", "Receber fundos", "Obtenha seu endereço de depósito para começar a receber"),
                    ("💡", "Verificar mais tarde", "O saldo pode aparecer após transações")
                ]
            },
            "zh": {
                "title": "未找到余额",
                "message": f"在 {chain.upper()} 上找不到钱包 `{wallet_address[:10]}...` 的余额。",
                "header": "您想做什么？",
                "options": [
                    ("🌐", "尝试其他链", "Ethereum, Base, Arbitrum, Polygon, Optimism"),
                    ("📥", "接收资金", "获取您的存款地址以开始接收"),
                    ("💡", "稍后查看", "余额可能在交易后出现")
                ]
            },
        }
        
        msgs = no_balance_msgs.get(language, no_balance_msgs["en"])
        options_text = "\n".join([
            f"**{i}.** {emoji} **{title}**\n   {details}" 
            for i, (emoji, title, details) in enumerate(msgs["options"], 1)
        ])
        
        return f"""💰 **{msgs["title"]}**

{msgs["message"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**{msgs["header"]}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{options_text}

💬 **Reply with the number (1, 2, or 3) to continue.**
"""

    def _get_chain_emoji(self, chain: str) -> str:
        """Get emoji for chain."""
        emojis = {
            "ethereum": "⟠",
            "base": "🔵",
            "arbitrum": "🔷",
            "polygon": "💜",
            "optimism": "🔴",
        }
        return emojis.get(chain.lower(), "🔗")

    def _portfolio_to_dict(self, portfolio: PortfolioDTO) -> dict:
        """Convert portfolio DTO to dictionary."""
        return {
            "wallet_address": portfolio.wallet_address,
            "chain": portfolio.chain,
            "total_usd": portfolio.total_usd,
            "native_balance": portfolio.native_balance,
            "native_usd_value": portfolio.native_usd_value,
            "native_symbol": portfolio.native_symbol,
            "tokens": portfolio.tokens,
            "captured_at": portfolio.captured_at,
            "has_value": portfolio.has_value,
        }
