"""
LLM-based intent detection adapter.

Uses LLM gateway for high-accuracy intent classification.
Provides detailed entity extraction and reasoning.

This adapter is ideal for:
- Production use (high accuracy)
- Complex messages requiring context understanding
- Entity extraction with confidence
"""

import json
import re
from typing import Optional

from app.domain.ports.chat.intent_detection_port import (
    IntentDetectionPort,
    IntentDetectionRequest,
    IntentDetectionResult,
)
from app.domain.ports.ai.llm_gateway import LLMGateway
from app.application.chat.services.intent_detector import ChatIntent


class IntentDetectionError(Exception):
    """Raised when intent detection fails critically."""

    pass


class LLMIntentDetectionAdapter(IntentDetectionPort):
    """
    Intent detection using LLM classification.

    Provides high accuracy but slower and costs tokens.
    """

    # Intent to handler mapping
    INTENT_TO_HANDLER = {
        # GraphRAG intents
        "protocol_search": "graphrag_search",
        "risk_assessment": "graphrag_search",
        "similar_protocols": "graphrag_search",
        # Hunter AI intents
        "hunter_sentiment": "hunter_ai",
        "hunter_price_prediction": "hunter_ai",
        "hunter_risk_signals": "hunter_ai",
        "hunter_trading_signals": "hunter_ai",
        "hunter_patterns": "hunter_ai",
        "hunter_portfolio": "hunter_ai",
        # ULTRA intents
        "ultra_arbitrage": "ultra",
        "ultra_flash_loans": "ultra",
        "ultra_mev_protection": "ultra",
        "ultra_auto_executor": "ultra",
        # DeFi Shortcut intents
        "lending": "lending_handler",
        "money_market": "money_market_handler",
        "swap": "swap_handler",
        "balance": "balance_handler",
        "portfolio": "portfolio_handler",
        "activity": "activity_handler",
        "receive": "receive_handler",
        # Squad intents
        "specialist_task": "agent_orchestrator",
        "complex_workflow": "agent_orchestrator",
        # Fallback
        "general_conversation": "general_chat",
    }

    def __init__(self, llm_gateway: LLMGateway):
        """
        Initialize with LLM gateway.

        Args:
            llm_gateway: LLM gateway for generating classifications
        """
        self._llm = llm_gateway

    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Use LLM to classify intent.

        Returns:
            High-confidence intent detection result
        """
        # Build classification prompt
        system_prompt = self._build_classification_prompt()
        user_prompt = self._build_user_prompt(request)

        # Call LLM
        try:
            response = await self._llm.generate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low for consistent classification
                max_tokens=300,
            )
        except Exception as e:
            raise IntentDetectionError(f"LLM call failed: {e}") from e

        # Parse JSON response
        try:
            data = self._parse_llm_response(response)
        except Exception as e:
            raise IntentDetectionError(f"Failed to parse LLM response: {e}") from e

        # Map intent to handler
        intent_str = data["intent"].lower()
        handler = self.INTENT_TO_HANDLER.get(intent_str, "general_chat")

        # Build result
        return IntentDetectionResult(
            intent=ChatIntent(intent_str),
            confidence=data["confidence"],
            entities=data.get("entities", {}),
            reasoning=data.get("reasoning", "LLM classification"),
            handler=handler,
            suggested_agent=data.get("suggested_agent"),
        )

    def supports_streaming(self) -> bool:
        return False  # Classification needs full response

    def _build_classification_prompt(self) -> str:
        """Build system prompt for intent classification."""
        return """You are an intent classifier for a DeFi chat interface.

Classify the user's message into ONE of these intents:

## GraphRAG Intents (Protocol Discovery & Analysis)

1. PROTOCOL_SEARCH - User wants to find/search for protocols
   Examples: "find staking protocols", "search for low-risk DEXs", "show me lending protocols on Ethereum"

2. RISK_ASSESSMENT - User wants risk analysis for a specific protocol
   Examples: "is Aave safe?", "analyze risk of Uniswap", "should I use Curve?"

3. SIMILAR_PROTOCOLS - User wants alternatives to a specific protocol
   Examples: "similar to Uniswap", "alternatives to Aave", "protocols like Curve"

## Hunter AI Intents (Market Intelligence & Trading)

4. HUNTER_SENTIMENT - User wants sentiment analysis from social/news sources
   Examples: "ETH sentiment", "what's the market mood for BTC?", "Twitter sentiment for SOL"

5. HUNTER_PRICE_PREDICTION - User wants price forecasts/predictions
   Examples: "predict ETH price", "where is BTC heading?", "price forecast for SOL"

6. HUNTER_RISK_SIGNALS - User wants market risk warnings/signals
   Examples: "risk signals for ETH", "any red flags for BTC?", "market warnings"

7. HUNTER_TRADING_SIGNALS - User wants buy/sell signals
   Examples: "should I buy ETH?", "trading signals for BTC", "entry point for SOL"

8. HUNTER_PATTERNS - User wants chart pattern analysis
   Examples: "chart patterns for ETH", "technical analysis BTC", "support/resistance levels"

9. HUNTER_PORTFOLIO - User wants portfolio optimization (MPT-based)
   Examples: "optimize my portfolio", "efficient frontier for BTC,ETH,SOL", "portfolio allocation"

## ULTRA Intents (DeFi Automation & MEV)

10. ULTRA_ARBITRAGE - User wants to discover arbitrage opportunities
   Examples: "find arbitrage opportunities", "2-hop arbitrage", "profitable cross-DEX trades"

11. ULTRA_FLASH_LOANS - User wants flash loan protocol selection or info
   Examples: "best flash loan for USDC", "Aave vs Balancer flash loans", "flash loan fees"

12. ULTRA_MEV_PROTECTION - User wants MEV-protected execution
   Examples: "execute with flashbots", "MEV protection", "bundle transaction privately"

13. ULTRA_AUTO_EXECUTOR - User wants to control automated trading bot
   Examples: "start trading bot", "pause auto executor", "bot status"

## DeFi Shortcut Intents (Quick Actions)

14. LENDING - User wants to deposit/earn/supply into lending protocols (Morpho, Aave, Compound)
    Examples: "deposit USDC on Morpho", "earn yield on my USDC", "supply ETH to Aave", "best Morpho vault on Base"

15. MONEY_MARKET - User wants to compare lending/supply rates across protocols
    Examples: "compare lending rates", "Aave vs Compound vs Morpho", "which has best supply APY"

16. SWAP - User wants to swap/exchange tokens
    Examples: "swap ETH for USDC", "exchange my tokens", "trade BTC for ETH"

17. BALANCE - User wants to check their balance (shows value in USDC)
    Examples: "show my balance", "how much do I have", "check wallet balance"

18. PORTFOLIO - User wants to see their full portfolio
    Examples: "show my portfolio", "list my assets", "what's in my wallet"

19. ACTIVITY - User wants transaction history
    Examples: "show my activity", "transaction history", "recent transactions"

20. RECEIVE - User wants to receive funds (show QR, address, handle)
    Examples: "receive crypto", "show my address", "deposit address", "QR code"

## Agent Squad & Workflow Intents

21. SPECIALIST_TASK - User needs specialist agent (yield, gas, security, etc.)
   Examples: "best USDC yield", "optimize gas", "tax implications"

22. COMPLEX_WORKFLOW - User needs multi-step analysis or strategy
   Examples: "create a balanced portfolio", "comprehensive analysis of DeFi", "migration strategy"

23. GENERAL_CONVERSATION - General questions, education, explanations
   Examples: "what is DeFi?", "explain impermanent loss", "how does staking work?"

Extract entities: protocol names, token symbols, amounts, chains, categories, etc.

Return JSON:
{
  "intent": "INTENT_NAME",
  "confidence": 0.95,
  "entities": {
    "protocol_name": "Aave",
    "token_symbol": "USDC",
    "chain": "Ethereum"
  },
  "reasoning": "User is asking about...",
  "suggested_agent": "defi_yield"
}

For SPECIALIST_TASK, suggest the best agent:
- "defi_yield" - yield/APY questions
- "risk_analyzer" - risk assessment
- "gas_optimizer" - gas optimization
- "security_auditor" - security/audits
- "portfolio" - portfolio management
- "tax_optimizer" - tax strategies
- "research" - deep protocol research
"""

    def _build_user_prompt(self, request: IntentDetectionRequest) -> str:
        """Build user prompt with message and context."""
        context = ""
        if request.conversation_history:
            context = self._format_conversation_history(request.conversation_history)

        return f"""Previous context:
{context if context else "None"}

Current message: {request.message}

Classify the intent and extract entities."""

    def _format_conversation_history(self, history: list) -> str:
        """Format conversation history for prompt."""
        # Take last 3 messages for context
        recent = history[-3:] if len(history) > 3 else history
        lines = []
        for msg in recent:
            role = getattr(msg, "role", "user")
            content = getattr(msg, "content", str(msg))
            if hasattr(role, "value"):
                role = role.value
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _parse_llm_response(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError("No valid JSON in response")
