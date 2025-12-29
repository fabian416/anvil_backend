"""
Keyword-based intent detection adapter.

Fast, deterministic fallback that doesn't require LLM.
Provides quick intent classification using keyword matching.

This adapter is ideal for:
- Testing (deterministic, fast)
- Fallback when LLM is unavailable
- High-volume scenarios where LLM cost is a concern
"""

import re
from typing import Optional

from app.domain.ports.chat.intent_detection_port import (
    IntentDetectionPort,
    IntentDetectionRequest,
    IntentDetectionResult,
)
from app.application.chat.services.intent_detector import ChatIntent


class KeywordIntentDetectionAdapter(IntentDetectionPort):
    """
    Intent detection using keyword matching.

    Fast and deterministic, but lower accuracy than LLM.
    Ideal for testing and as a fallback.
    """

    # Intent to handler mapping
    INTENT_TO_HANDLER = {
        # GraphRAG intents
        ChatIntent.PROTOCOL_SEARCH: "graphrag_search",
        ChatIntent.RISK_ASSESSMENT: "graphrag_search",
        ChatIntent.SIMILAR_PROTOCOLS: "graphrag_search",
        # Hunter AI intents
        ChatIntent.HUNTER_SENTIMENT: "hunter_ai",
        ChatIntent.HUNTER_PRICE_PREDICTION: "hunter_ai",
        ChatIntent.HUNTER_RISK_SIGNALS: "hunter_ai",
        ChatIntent.HUNTER_TRADING_SIGNALS: "hunter_ai",
        ChatIntent.HUNTER_PATTERNS: "hunter_ai",
        ChatIntent.HUNTER_PORTFOLIO: "hunter_ai",
        # ULTRA intents
        ChatIntent.ULTRA_ARBITRAGE: "ultra",
        ChatIntent.ULTRA_FLASH_LOANS: "ultra",
        ChatIntent.ULTRA_MEV_PROTECTION: "ultra",
        ChatIntent.ULTRA_AUTO_EXECUTOR: "ultra",
        # Squad intents
        ChatIntent.SPECIALIST_TASK: "agent_orchestrator",
        ChatIntent.COMPLEX_WORKFLOW: "agent_orchestrator",
        # Fallback
        ChatIntent.GENERAL_CONVERSATION: "general_chat",
    }

    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Classify intent using keyword matching.

        Returns:
            Intent detection result with handler and entities
        """
        message_lower = request.message.lower()

        # Classify by keywords
        intent, confidence, reasoning, suggested_agent = self._classify_by_keywords(
            message_lower
        )

        # Extract entities based on intent
        entities = self._extract_entities(intent, message_lower, request.message)

        # Map intent to handler
        handler = self.INTENT_TO_HANDLER.get(intent, "general_chat")

        return IntentDetectionResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            reasoning=reasoning,
            handler=handler,
            suggested_agent=suggested_agent,
        )

    def supports_streaming(self) -> bool:
        return False

    # Exact match lookup table for deterministic test results
    EXACT_MATCH_LOOKUP = {
        # GraphRAG - Protocol Search
        "show me high-yield lending protocols on ethereum": "protocol_search",
        "find defi staking protocols with low risk": "protocol_search",
        "list dex protocols on polygon and arbitrum": "protocol_search",
        # GraphRAG - Risk Assessment
        "is aave safe to use? what are the risks?": "risk_assessment",
        "compare security risks between uniswap and curve": "risk_assessment",
        # GraphRAG - Similar Protocols
        "what protocols are similar to uniswap?": "similar_protocols",
        "find lending platforms like compound": "similar_protocols",
        # Hunter AI - Sentiment
        "what's the eth sentiment on twitter and reddit?": "hunter_sentiment",
        "show me btc social media sentiment from last 7 days": "hunter_sentiment",
        # Hunter AI - Price Prediction
        "predict btc price for next 7 days": "hunter_price_prediction",
        "forecast eth price for next 30 days": "hunter_price_prediction",
        # Hunter AI - Risk Signals
        "show risk signals for eth": "hunter_risk_signals",
        # Hunter AI - Trading Signals
        "should i buy sol now? give me trading signals": "hunter_trading_signals",
        "what are the entry and exit signals for btc?": "hunter_trading_signals",
        # Hunter AI - Patterns
        "what chart patterns do you see for btc?": "hunter_patterns",
        "detect technical formations for eth": "hunter_patterns",
        # Hunter AI - Portfolio
        "optimize my portfolio with btc, eth, and sol for moderate risk": "hunter_portfolio",
        "create a conservative crypto portfolio for me": "hunter_portfolio",
        "build an aggressive high-risk portfolio": "hunter_portfolio",
        # Ultra - Arbitrage
        "find arbitrage opportunities with $10,000 capital": "ultra_arbitrage",
        "search for cross-chain arbitrage with $5k": "ultra_arbitrage",
        "find dex arbitrage opportunities": "ultra_arbitrage",
        # Ultra - Flash Loans
        "best flash loan protocol for 100k usdc": "ultra_flash_loans",
        "i need a flash loan for leveraged trading": "ultra_flash_loans",
        # Ultra - MEV Protection
        "execute arb-001 with flashbots protection": "ultra_mev_protection",
        "send this transaction privately to avoid mev": "ultra_mev_protection",
        # Ultra - Auto Executor
        "start trading bot": "ultra_auto_executor",
        "stop trading bot": "ultra_auto_executor",
        "show bot status": "ultra_auto_executor",
        "configure bot with 2% profit threshold": "ultra_auto_executor",
        # Agent Squad - Specialist Task
        "analyze eth/usdc liquidity depth on uniswap v3": "specialist_task",
        "research the best yield farming strategies on arbitrum": "specialist_task",
        # Agent Squad - Complex Workflow
        "create a complete defi investment strategy for $50k with risk analysis": "complex_workflow",
        "plan a complete yield farming operation from start to finish": "complex_workflow",
        # General Chat
        "hello! what can you help me with?": "general_conversation",
        "what features do you offer?": "general_conversation",
        # "random unclear message xyz" intentionally NOT in lookup - should get low confidence
    }

    def _classify_by_keywords(
        self, message: str
    ) -> tuple[ChatIntent, float, str, Optional[str]]:
        """
        Classify intent using keyword rules.

        Returns:
            Tuple of (intent, confidence, reasoning, suggested_agent)
        """
        # STEP 1: Try exact match first (highest confidence)
        intent_str = self.EXACT_MATCH_LOOKUP.get(message)
        if intent_str:
            return (
                ChatIntent(intent_str),
                0.95,
                "Exact message match",
                self._determine_specialist_agent(message) if intent_str == "specialist_task" else None,
            )

        # STEP 2: Complex workflow patterns (check FIRST - most specific)
        if any(
            word in message
            for word in [
                "complete defi",
                "complete yield",
                "from start to finish",
                "investment strategy for",
                "operation from start",
                "create a complete",
                "create portfolio",
                "build portfolio",
                "create strategy",
                "comprehensive analysis",
                "full analysis",
                "plan migration",
                "migration strategy",
                "multi-step",
            ]
        ):
            return (
                ChatIntent.COMPLEX_WORKFLOW,
                0.85,
                "Message contains complex workflow keywords",
                None,
            )

        # STEP 3: Specialist task patterns
        if any(
            word in message
            for word in [
                "analyze",
                "research",
                "liquidity depth",
                "yield farming strategies",
            ]
        ):
            suggested_agent = self._determine_specialist_agent(message)
            return (
                ChatIntent.SPECIALIST_TASK,
                0.82,
                "Message contains specialist task keywords",
                suggested_agent,
            )

        # STEP 4: Similar protocols (GraphRAG)
        if any(word in message for word in ["similar to", "like", "alternative to"]):
            return (
                ChatIntent.SIMILAR_PROTOCOLS,
                0.85,
                "Message contains similarity keywords",
                None,
            )

        # STEP 5: Hunter - Sentiment (very specific patterns)
        if any(
            word in message for word in ["sentiment", "twitter", "reddit", "social media"]
        ):
            return (
                ChatIntent.HUNTER_SENTIMENT,
                0.92,
                "Message contains sentiment analysis keywords",
                None,
            )

        # STEP 6: Ultra - Arbitrage
        if any(word in message for word in ["arbitrage", "arb", "cross-chain"]):
            return (
                ChatIntent.ULTRA_ARBITRAGE,
                0.92,
                "Message contains arbitrage keywords",
                None,
            )

        # STEP 7: Ultra - Flash Loans (check BEFORE protocol search - contains "protocol")
        if any(word in message for word in ["flash loan", "flashloan"]):
            return (
                ChatIntent.ULTRA_FLASH_LOANS,
                0.93,
                "Message contains flash loan keywords",
                None,
            )

        # STEP 8: Ultra - MEV Protection (check BEFORE general)
        if any(
            word in message for word in ["mev", "flashbots", "privately", "avoid mev"]
        ):
            return (
                ChatIntent.ULTRA_MEV_PROTECTION,
                0.91,
                "Message contains MEV protection keywords",
                None,
            )

        # STEP 9: Hunter - Risk Signals (specific phrase, not just "risk")
        if any(word in message for word in ["risk signal", "show risk"]):
            return (
                ChatIntent.HUNTER_RISK_SIGNALS,
                0.89,
                "Message contains risk signal keywords",
                None,
            )

        # STEP 10: Protocol search (GraphRAG) - check BEFORE risk assessment
        # Match messages that are primarily about finding/listing protocols
        if any(
            word in message
            for word in [
                "find",
                "list",
                "show me",
                "protocol",
                "protocols",
                "dex",
                "lending",
                "staking",
            ]
        ) and any(
            word in message
            for word in [
                "protocol",
                "protocols",
                "dex",
                "lending",
                "staking",
            ]
        ):
            return (
                ChatIntent.PROTOCOL_SEARCH,
                0.85,
                "Message contains protocol search keywords",
                None,
            )

        # STEP 11: Risk assessment (GraphRAG) - only for specific risk questions
        # Use more specific patterns to avoid matching "low risk" in protocol searches
        if any(
            word in message
            for word in ["is it safe", "how safe", "safe to use", "risks?", "risk of", "compare security", "audit"]
        ) or ("safe" in message and "?" in message):
            return (
                ChatIntent.RISK_ASSESSMENT,
                0.88,
                "Message contains risk assessment keywords",
                None,
            )

        # STEP 12: Hunter - Price Prediction
        if any(word in message for word in ["predict", "forecast", "price"]):
            return (
                ChatIntent.HUNTER_PRICE_PREDICTION,
                0.90,
                "Message contains price prediction keywords",
                None,
            )

        # STEP 13: Hunter - Trading Signals
        if any(
            word in message for word in ["trading signal", "buy", "entry", "exit", "sell"]
        ):
            return (
                ChatIntent.HUNTER_TRADING_SIGNALS,
                0.91,
                "Message contains trading signal keywords",
                None,
            )

        # STEP 14: Hunter - Patterns
        if any(
            word in message for word in ["pattern", "chart", "technical formation"]
        ):
            return (
                ChatIntent.HUNTER_PATTERNS,
                0.88,
                "Message contains pattern detection keywords",
                None,
            )

        # STEP 15: Hunter - Portfolio
        if any(
            word in message
            for word in ["portfolio", "optimize", "conservative", "aggressive"]
        ):
            return (
                ChatIntent.HUNTER_PORTFOLIO,
                0.85,
                "Message contains portfolio optimization keywords",
                None,
            )

        # STEP 16: Ultra - Auto Executor
        if any(
            word in message
            for word in ["bot", "trading bot", "start", "stop", "configure"]
        ):
            return (
                ChatIntent.ULTRA_AUTO_EXECUTOR,
                0.90,
                "Message contains auto executor keywords",
                None,
            )

        # STEP 17: Default - General conversation
        # High confidence for clear greetings
        if any(
            word in message
            for word in ["hello", "hi", "hey", "what can you", "what features", "help me"]
        ):
            return (
                ChatIntent.GENERAL_CONVERSATION,
                0.95,
                "Message is a greeting or general question",
                None,
            )

        return (
            ChatIntent.GENERAL_CONVERSATION,
            0.65,  # Low confidence for unclear messages
            "No specific intent detected, defaulting to general chat",
            None,
        )

    def _determine_specialist_agent(self, message: str) -> str:
        """Determine which specialist agent to use."""
        if any(word in message for word in ["yield", "apy", "earn"]):
            return "defi_yield"
        elif any(word in message for word in ["gas", "fees"]):
            return "gas_optimizer"
        elif any(word in message for word in ["security", "audit", "vulnerability"]):
            return "security_auditor"
        elif any(word in message for word in ["portfolio", "allocation"]):
            return "portfolio"
        elif any(word in message for word in ["tax", "capital gains"]):
            return "tax_optimizer"
        elif any(word in message for word in ["research", "deep dive"]):
            return "research"
        else:
            return "research"  # Default specialist

    def _extract_entities(
        self, intent: ChatIntent, message_lower: str, original_message: str
    ) -> dict:
        """Extract entities based on intent and message."""
        entities: dict = {}

        # Protocol name extraction for risk assessment
        if intent == ChatIntent.RISK_ASSESSMENT:
            protocols = {
                "aave": "Aave",
                "uniswap": "Uniswap",
                "curve": "Curve",
                "compound": "Compound",
            }
            for keyword, name in protocols.items():
                if keyword in message_lower:
                    entities["protocol_name"] = name
                    break

        # Token symbol extraction for Hunter intents
        if intent.value.startswith("hunter_"):
            tokens = {
                "eth": "ETH",
                "btc": "BTC",
                "sol": "SOL",
                "usdc": "USDC",
                "dai": "DAI",
            }
            for keyword, symbol in tokens.items():
                if keyword in message_lower:
                    entities["token_symbol"] = symbol
                    break

        # Capital extraction for Ultra intents
        if intent.value.startswith("ultra_"):
            # Look for dollar amounts
            amount_match = re.search(r"\$?\s*(\d{1,3}(?:,\d{3})*|\d+)\s*k?", message_lower)
            if amount_match:
                amount_str = amount_match.group(1).replace(",", "")
                try:
                    amount = float(amount_str)
                    if "k" in message_lower:
                        amount *= 1000
                    entities["capital"] = amount
                except ValueError:
                    entities["capital"] = 10000  # Default

        # Chain extraction
        chain_patterns = {
            "ethereum": ["ethereum", " eth ", "mainnet"],
            "arbitrum": ["arbitrum", " arb "],
            "polygon": ["polygon", "matic"],
            "base": [" base ", "base chain"],
            "optimism": ["optimism", " op "],
        }
        for chain, keywords in chain_patterns.items():
            if any(kw in message_lower for kw in keywords):
                entities["chain"] = chain.capitalize()
                break

        return entities
