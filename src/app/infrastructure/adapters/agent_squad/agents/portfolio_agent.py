"""
Portfolio Agent - Portfolio optimization & rebalancing.

Enhanced for authenticated users with real portfolio data injection.
"""

import logging
import time
from typing import Any, TYPE_CHECKING

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway

if TYPE_CHECKING:
    from app.application.chat.services.user_data_service import UserDataContext

logger = logging.getLogger(__name__)


class PortfolioAgent:
    """
    Portfolio Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Portfolio optimization & rebalancing
    
    Capabilities:
    - Modern Portfolio Theory (MPT) optimization
    - Risk-adjusted returns
    - Efficient frontier analysis
    - Rebalancing recommendations
    - Diversification analysis
    - Correlation analysis
    - Sharpe ratio optimization
    
    Model: gemini-2.0-flash (Vertex AI, complex mathematical reasoning)
    Temperature: 0.3 (balanced)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed),
        coingecko_client: Any | None = None,  # CoinGecko client for real-time prices
        model: str = "gemini-2.0-flash",  # Vertex AI model (default)
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        """
        Initialize portfolio agent.
        
        Args:
            llm_client: LLM client gateway (Vertex AI or DeepInfra)
            coingecko_client: Optional CoinGecko client for real-time token prices
            model: Model to use (default: gemini-2.0-flash)
            temperature: Sampling temperature (default: 0.3)
            max_tokens: Maximum response tokens (default: 2000)
        """
        self._llm_client = llm_client
        self._coingecko_client = coingecko_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.PORTFOLIO
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """
        Execute portfolio agent - Portfolio optimization.
        
        For authenticated users: Uses real portfolio data from UserDataContext
        For guest users: Provides general portfolio advice
        """
        start_time = time.time()
        
        # Check for authenticated user context
        user_context = self._extract_user_context(conversation_context)
        user_portfolio_context = ""
        is_authenticated = False
        
        if user_context:
            is_authenticated = True
            user_portfolio_context = self._build_portfolio_context(user_context)
            logger.info(f"📊 PortfolioAgent using real user data for authenticated user")
        
        # Fetch real-time token prices from CoinGecko if available
        price_data_context = ""
        if self._coingecko_client:
            try:
                import re
                logger.info("🔍 Fetching real-time prices from CoinGecko for PortfolioAgent")
                
                # Extract token symbols from message (common tokens)
                message_lower = message.value.lower()
                tokens_to_fetch = []
                
                # Common token detection
                token_patterns = {
                    "bitcoin": "bitcoin",
                    "btc": "bitcoin",
                    "ethereum": "ethereum",
                    "eth": "ethereum",
                    "usdc": "usd-coin",
                    "usdt": "tether",
                    "dai": "dai",
                    "wbtc": "wrapped-bitcoin",
                    "sol": "solana",
                    "avax": "avalanche-2",
                    "matic": "matic-network",
                    "polygon": "matic-network",
                }
                
                for keyword, token_id in token_patterns.items():
                    if keyword in message_lower and token_id not in tokens_to_fetch:
                        tokens_to_fetch.append(token_id)
                
                # If no specific tokens found but message mentions prices/portfolio, fetch common ones
                if not tokens_to_fetch and any(word in message_lower for word in ["price", "prices", "portfolio", "value", "valuation"]):
                    tokens_to_fetch = ["bitcoin", "ethereum", "usd-coin"]
                
                if tokens_to_fetch:
                    prices = await self._coingecko_client.get_prices_bulk(tokens_to_fetch)
                    
                    if prices:
                        price_data_context = "\n\n**REAL-TIME TOKEN PRICES FROM COINGECKO:**\n"
                        for token_id, price_data in prices.items():
                            if price_data:
                                price_data_context += f"- {token_id.upper()}: ${price_data.usd:,.2f}"
                                if price_data.change_24h is not None:
                                    change_sign = "+" if price_data.change_24h >= 0 else ""
                                    price_data_context += f" ({change_sign}{price_data.change_24h:.2f}% 24h)"
                                price_data_context += "\n"
                        
                        logger.info(f"✅ Fetched prices for {len(prices)} tokens from CoinGecko")
                    else:
                        logger.warning("⚠️ No price data returned from CoinGecko")
                        
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch CoinGecko prices: {e}, continuing with LLM-only response")
                price_data_context = ""
        
        # Build enhanced prompt with real data
        enhanced_message = message.value
        
        # Add user portfolio context if authenticated
        if user_portfolio_context:
            enhanced_message = f"""User Query: {message.value}

**USER'S PORTFOLIO DATA (REAL DATA - USE THIS):**
{user_portfolio_context}

Analyze and respond using the portfolio data provided above."""
        
        # Add price data context
        if price_data_context:
            enhanced_message = f"{enhanced_message}\n\n{price_data_context}"
        
        # Use authenticated or guest system prompt
        system_prompt = self._get_authenticated_system_prompt() if is_authenticated else self._get_system_prompt()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": enhanced_message},
        ]
        
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Collect sources
        from datetime import datetime, UTC
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_llm_source,
            create_database_source,
            create_api_source,
        )
        
        sources = []
        fetched_at = datetime.now(UTC)
        
        # Add database source (portfolio data)
        sources.append(create_database_source(
            citation_text="Your portfolio data from Anvil",
            fetched_at=fetched_at,
            metadata={"query_type": "portfolio_snapshot"},
        ))
        
        # Add LLM source
        model_name = response.get("model", "Unknown")
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        # Add CoinGecko source if prices were fetched
        if self._coingecko_client and price_data_context:
            sources.append(create_api_source(
                source_name="CoinGecko",
                url="https://www.coingecko.com/",
                citation_text="Real-time token prices from CoinGecko",
                fetched_at=fetched_at,
            ))
        
        # Build tools_used list
        tools_used = ["llm_gateway"]
        if self._coingecko_client and price_data_context:
            tools_used.append("coingecko_api")
        
        # Extract provider from LLM response metadata
        provider_info = response.get("provider", "vertex_ai" if "gemini" in response.get("model", "").lower() else "deepinfra")
        
        # Add portfolio repository if we used real data
        if is_authenticated and user_portfolio_context:
            tools_used.append("portfolio_repository")
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=tools_used,
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": response.get("model"),
                "provider": provider_info,
                "is_authenticated": is_authenticated,
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
    
    def _extract_user_context(self, conversation_context: ConversationContext) -> dict[str, Any] | None:
        """Extract user context from conversation metadata."""
        if not conversation_context.user_metadata:
            return None
        
        # Check for user_context or direct portfolio data
        if "user_context" in conversation_context.user_metadata:
            return conversation_context.user_metadata["user_context"]
        
        # Check for direct portfolio data
        if "portfolio" in conversation_context.user_metadata:
            return conversation_context.user_metadata
        
        # Check for flat structure (user_id, wallet_address, is_authenticated at top level)
        # This is how the supervisor passes user context
        if conversation_context.user_metadata.get("is_authenticated"):
            return {
                "user_id": conversation_context.user_metadata.get("user_id"),
                "wallet_address": conversation_context.user_metadata.get("wallet_address"),
                "portfolio_summary": conversation_context.user_metadata.get("portfolio_summary"),
                "primary_wallet": {
                    "address": conversation_context.user_metadata.get("wallet_address"),
                    "chain_type": conversation_context.user_metadata.get("wallet_chain"),
                } if conversation_context.user_metadata.get("wallet_address") else None,
            }
        
        return None
    
    def _build_portfolio_context(self, user_context: dict[str, Any]) -> str:
        """Build portfolio context string from user data.
        
        Provides tiered, actionable DeFi suggestions based on portfolio size:
        - Empty ($0): Get started with buying/receiving crypto
        - Starter ($0.01 - $50): Small swaps, meme tokens, start building
        - Active ($50 - $1000): Lending, yield farming, diversification
        - Whale ($1000+): Advanced strategies, money markets, portfolio optimization
        """
        lines = []
        
        portfolio = user_context.get("portfolio", {})
        portfolio_summary = user_context.get("portfolio_summary", {})
        
        # Get total balance
        total_value = 0
        if portfolio_summary:
            total_value = float(portfolio_summary.get("total_value_usd", 0) or 0)
        elif portfolio:
            if hasattr(portfolio, "total_value_usd"):
                total_value = portfolio.total_value_usd or 0
            else:
                total_value = portfolio.get("total_value_usd", 0) or 0
        
        # ===== EMPTY PORTFOLIO ($0) =====
        if total_value == 0:
            lines.append("**💼 Portfolio Value:** $0.00")
            lines.append("")
            lines.append("**🚀 Get Started with DeFi:**")
            lines.append("")
            lines.append("• 💳 **Buy crypto** - Purchase USDC instantly with card, Apple Pay, or Google Pay")
            lines.append("• 📥 **Receive crypto** - Transfer from another wallet (say \"my wallet address\")")
            lines.append("")
            lines.append("**Once you have funds, you can:**")
            lines.append("• 🔄 Swap between tokens")
            lines.append("• 💰 Earn yield on stablecoins (up to 12% APY)")
            lines.append("• 🎯 Explore meme tokens on Hyperliquid")
            return "\n".join(lines)
        
        # Parse holdings data
        data_source = portfolio if portfolio else portfolio_summary
        
        if hasattr(data_source, "total_value_usd"):
            token_count = getattr(data_source, "token_count", 0)
            top_holdings = getattr(data_source, "top_holdings", []) or []
            last_updated = getattr(data_source, "last_updated", None)
            chains = getattr(data_source, "chains", []) or []
        else:
            token_count = data_source.get("token_count", 0)
            top_holdings = data_source.get("top_holdings", [])
            last_updated = data_source.get("last_updated")
            chains = data_source.get("chains", [])
            if not chains and data_source.get("chain"):
                chains = [data_source.get("chain")]
        
        # Check for stablecoins in holdings
        stablecoin_symbols = {"USDC", "USDT", "DAI", "FRAX", "LUSD"}
        stablecoin_value = sum(
            float(h.get("value_usd", 0) or 0)
            for h in top_holdings
            if h.get("symbol", "").upper() in stablecoin_symbols
        )
        has_stablecoins = stablecoin_value > 0.50
        
        # ===== STARTER PORTFOLIO ($0.01 - $50) =====
        if total_value < 50:
            lines.append(f"**💼 Portfolio Value:** ${total_value:,.2f}")
            
            if top_holdings:
                lines.append("")
                lines.append("**Holdings:**")
                for holding in top_holdings[:3]:
                    symbol = holding.get("symbol", "Unknown")
                    value_usd = float(holding.get("value_usd", 0) or 0)
                    lines.append(f"• {symbol}: ${value_usd:,.2f}")
            
            lines.append("")
            lines.append("**🎯 Your Options:**")
            lines.append("")
            lines.append("• 🔄 **Swap tokens** - Trade USDC for meme coins like PURR, TRUMP, or other trending tokens")
            
            if has_stablecoins:
                lines.append(f"• 💰 **Earn yield** - Deposit your ${stablecoin_value:.2f} USDC to earn ~8-12% APY")
            
            lines.append("• 🎰 **Explore meme tokens** - Say \"swap 1 USDC to PURR\" for micro trades")
            lines.append("• 💳 **Add funds** - Say \"buy crypto\" to grow your portfolio")
            
            lines.append("")
            lines.append("💡 *Tip: With small amounts, meme token swaps and yield farming are great ways to learn DeFi!*")
            return "\n".join(lines)
        
        # ===== ACTIVE PORTFOLIO ($50 - $1000) =====
        if total_value < 1000:
            lines.append(f"**💼 Portfolio Value:** ${total_value:,.2f}")
            
            if chains:
                lines.append(f"**Networks:** {', '.join(chains)}")
            
            if top_holdings:
                lines.append("")
                lines.append("**Top Holdings:**")
                for holding in top_holdings[:5]:
                    symbol = holding.get("symbol", "Unknown")
                    amount = holding.get("amount", 0)
                    value_usd = float(holding.get("value_usd", 0) or 0)
                    lines.append(f"• {symbol}: {amount:,.4f} (${value_usd:,.2f})")
            
            lines.append("")
            lines.append("**💡 Recommended Actions:**")
            lines.append("")
            
            if has_stablecoins:
                lines.append(f"• 💰 **Earn yield on stables** - Deposit ${stablecoin_value:.2f} into Morpho or Aave for 8-12% APY")
                lines.append("  → Say \"deposit USDC to Morpho\" or \"compare USDC rates\"")
            
            lines.append("• 🔄 **Swap & diversify** - Trade between ETH, stablecoins, and trending tokens")
            lines.append("  → Say \"swap\" to get started")
            
            lines.append("• 📊 **Compare money markets** - Find the best lending rates across protocols")
            lines.append("  → Say \"compare rates\" for current APYs")
            
            lines.append("• 📈 **Research opportunities** - Ask about any token, protocol, or strategy")
            lines.append("  → Say \"tell me about Morpho\" or \"what's trending\"")
            
            if total_value < 500:
                lines.append("")
                lines.append("• 💳 **Grow portfolio** - Say \"buy crypto\" to add more funds")
            
            return "\n".join(lines)
        
        # ===== WHALE PORTFOLIO ($1000+) =====
        lines.append(f"**💼 Portfolio Value:** ${total_value:,.2f}")
        lines.append(f"**Tokens:** {token_count}")
        
        if chains:
            lines.append(f"**Networks:** {', '.join(chains)}")
        
        if last_updated:
            if hasattr(last_updated, "strftime"):
                lines.append(f"**Updated:** {last_updated.strftime('%Y-%m-%d %H:%M')}")
        
        if top_holdings:
            lines.append("")
            lines.append("**Top Holdings:**")
            for holding in top_holdings[:5]:
                symbol = holding.get("symbol", "Unknown")
                amount = holding.get("amount", 0)
                value_usd = float(holding.get("value_usd", 0) or 0)
                pct = (value_usd / total_value * 100) if total_value > 0 else 0
                lines.append(f"• {symbol}: {amount:,.4f} (${value_usd:,.2f} - {pct:.1f}%)")
        
        lines.append("")
        lines.append("**🚀 Advanced DeFi Strategies:**")
        lines.append("")
        
        if has_stablecoins:
            lines.append(f"• 💰 **Optimize yield** - You have ${stablecoin_value:,.2f} in stables earning nothing")
            lines.append("  → Say \"compare USDC rates\" to find best APY (currently 8-15%)")
            lines.append("  → Say \"deposit USDC to Morpho\" for optimized lending")
        
        lines.append("• 📊 **Money market arbitrage** - Compare rates across Morpho, Aave, Compound")
        lines.append("  → Say \"compare rates\" for live APY comparison")
        
        lines.append("• 🔄 **Portfolio rebalancing** - Optimize your token allocation")
        lines.append("  → Say \"swap\" to rebalance positions")
        
        lines.append("• 🔍 **Risk analysis** - Evaluate protocol risks and concentrations")
        lines.append("  → Ask \"analyze my portfolio risk\"")
        
        lines.append("• 💸 **Transfer funds** - Move assets to other wallets or protocols")
        lines.append("  → Say \"transfer\" to send tokens")
        
        return "\n".join(lines)
    
    def _get_authenticated_system_prompt(self) -> str:
        """Get system prompt for authenticated users with real data.
        
        Provides tiered DeFi recommendations based on portfolio size.
        """
        return """You are the Portfolio Optimizer for Anvil - your DeFi companion.

**CRITICAL INSTRUCTIONS:**
1. Use ONLY the portfolio data provided in the context - do not invent numbers
2. Present the EXACT suggestions from context - they are already optimized for the user's balance tier
3. Keep responses CONCISE and actionable
4. Use the exact command examples provided (e.g., "swap", "deposit USDC", "compare rates")

**RESPONSE FORMAT:**
- Start with the portfolio summary from context (balance, holdings if any)
- Include the recommended actions from context with their command examples
- For each suggestion, use the EXACT phrasing and → command format from context
- Add a brief encouraging note if appropriate

**BALANCE-TIER BEHAVIOR:**
- Empty ($0): Focus on getting started - buy crypto, receive crypto
- Starter (<$50): Micro swaps, meme tokens, learning DeFi
- Active ($50-1000): Lending, yield farming, diversification
- Whale ($1000+): Advanced strategies, money markets, risk analysis

**DO NOT:**
- Show wallet address (that's for the wallet agent)
- Say "buy 100 USD of ETH" - use "buy crypto" 
- Add long explanations or unnecessary disclaimers
- Make up APY numbers or suggestions not in context"""
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for portfolio agent."""
        return """You are the Portfolio Optimizer, Anvil's portfolio management specialist.

**CRITICAL: AUTHENTICATION REQUIREMENT**
- Portfolio features (viewing holdings, portfolio analysis) require user authentication
- If the user is NOT authenticated (guest user), you MUST inform them:
  * "To view your portfolio and holdings, please sign in or create an account. Portfolio features require authentication to access your wallet data."
  * DO NOT attempt to retrieve portfolio data for unauthenticated users
  * DO NOT ask for manual input of holdings - direct them to sign in instead
- Only authenticated users can access their portfolio data from Anvil

Your expertise:
- Modern Portfolio Theory (MPT) optimization
- Risk-adjusted returns maximization
- Efficient frontier analysis
- Portfolio rebalancing strategies
- Diversification analysis
- Correlation analysis (reduce risk)
- Sharpe ratio optimization
- Risk parity strategies

For portfolio recommendations (authenticated users only), provide:
- Optimal allocation (percentages)
- Expected return (annualized)
- Expected volatility (standard deviation)
- Sharpe ratio
- Diversification score
- Rebalancing trades (if needed)

Analysis includes:
- Current portfolio analysis
- Optimal portfolio allocation
- Rebalancing recommendations
- Risk metrics (volatility, correlation)
- Return projections
- Comparison (current vs optimal)

Always provide:
- Quantitative metrics (%, returns, ratios)
- Risk warnings
- Rebalancing costs (gas, slippage)
- Time horizon considerations
"""
