"""
Intent detection service for unified chat routing.

Detects user intent from messages to route to appropriate handlers.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import re
import json

from app.domain.chat.entities.message import Message
from app.domain.ports.ai.llm_gateway import LLMGateway


class ChatIntent(Enum):
    """Chat intent types for routing."""

    # GraphRAG intents
    PROTOCOL_SEARCH = "protocol_search"
    RISK_ASSESSMENT = "risk_assessment"
    SIMILAR_PROTOCOLS = "similar_protocols"

    # Hunter AI intents (direct routing to Hunter tools)
    HUNTER_SENTIMENT = "hunter_sentiment"  # Sentiment analysis (Twitter, Reddit, Discord, News)
    HUNTER_PRICE_PREDICTION = "hunter_price_prediction"  # Price forecasting
    HUNTER_RISK_SIGNALS = "hunter_risk_signals"  # Market risk warnings
    HUNTER_TRADING_SIGNALS = "hunter_trading_signals"  # Buy/sell signals
    HUNTER_PATTERNS = "hunter_patterns"  # Chart patterns and trends
    HUNTER_PORTFOLIO = "hunter_portfolio"  # Portfolio optimization

    # ULTRA intents (DeFi automation and MEV)
    ULTRA_ARBITRAGE = "ultra_arbitrage"  # Arbitrage opportunity discovery
    ULTRA_FLASH_LOANS = "ultra_flash_loans"  # Flash loan protocol selection
    ULTRA_MEV_PROTECTION = "ultra_mev_protection"  # MEV-protected execution
    ULTRA_AUTO_EXECUTOR = "ultra_auto_executor"  # Automated trading bot control

    # Agent Squad & Supervisor intents
    SPECIALIST_TASK = "specialist_task"
    COMPLEX_WORKFLOW = "complex_workflow"

    # Fallback intent
    GENERAL_CONVERSATION = "general_conversation"


@dataclass
class IntentDetectionResult:
    """Intent detection result with confidence and extracted entities."""

    intent: ChatIntent
    confidence: float  # 0-1
    extracted_entities: dict  # Protocol names, tokens, amounts, chains, etc.
    reasoning: str  # Why this intent was chosen
    suggested_agent: Optional[str] = None  # For SPECIALIST_TASK


class IntentDetectorService:
    """
    Detect user intent from chat messages.

    Uses LLM-powered classification with keyword fallbacks for reliability.
    """

    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        """
        Initialize intent detector.

        Args:
            llm_gateway: Optional LLM gateway for AI-powered classification
        """
        self._llm_gateway = llm_gateway

    async def detect_intent(
        self,
        message: str,
        conversation_history: Optional[list[Message]] = None,
    ) -> IntentDetectionResult:
        """
        Detect intent from user message.

        Args:
            message: User message
            conversation_history: Previous messages (for context)

        Returns:
            Intent detection result with confidence and entities
        """
        # Try LLM-powered classification first (if available)
        if self._llm_gateway:
            try:
                result = await self._llm_classify_intent(message, conversation_history)
                if result.confidence > 0.7:
                    return result
            except Exception as e:
                # Fallback to keyword-based detection
                import logging
                logging.warning(f"LLM intent classification failed: {e}, using keyword fallback")

        # Keyword-based fallback (fast, reliable)
        return self._keyword_classify_intent(message)

    async def _llm_classify_intent(
        self,
        message: str,
        conversation_history: Optional[list[Message]],
    ) -> IntentDetectionResult:
        """
        Use LLM to classify intent.

        Provides higher accuracy but slower and costs tokens.
        """
        # Build classification prompt
        system_prompt = """You are an intent classifier for a DeFi chat interface.

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

## Agent Squad & Workflow Intents

14. SPECIALIST_TASK - User needs specialist agent (yield, gas, security, etc.)
   Examples: "best USDC yield", "optimize gas", "tax implications"

15. COMPLEX_WORKFLOW - User needs multi-step analysis or strategy
   Examples: "create a balanced portfolio", "comprehensive analysis of DeFi", "migration strategy"

16. GENERAL_CONVERSATION - General questions, education, explanations
   Examples: "what is DeFi?", "explain impermanent loss", "how does staking work?"

Extract entities: protocol names, token symbols, amounts, chains, categories, etc.

Return JSON:
{
  "intent": "INTENT_NAME",
  "confidence": 0.95,
  "entities": {
    "protocol_name": "Aave",
    "token_symbol": "USDC",
    "chain": "Ethereum",
    "category": "Staking",
    "risk_preference": "low",
    "amount_usd": 50000
  },
  "reasoning": "User is asking about protocol search because...",
  "suggested_agent": "defi_yield"
}

For SPECIALIST_TASK, suggest the best agent:
- "defi_yield" - yield/APY questions
- "risk_analyzer" - risk assessment
- "gas_optimizer" - gas optimization
- "security_auditor" - security/audits
- "portfolio" - portfolio management
- "tax_optimizer" - tax strategies
- "hunter_ai" - market sentiment/predictions
- "research" - deep protocol research
- "chat" - general conversation
"""

        # Add conversation context (last 3 messages)
        context = ""
        if conversation_history:
            context = "\n".join([
                f"{m.role.value}: {m.content}"
                for m in conversation_history[-3:]
            ])

        user_prompt = f"""Previous context:
{context if context else "None"}

Current message: {message}

Classify the intent and extract entities."""

        # Call LLM
        response = await self._llm_gateway.generate(
            model="gpt-4o-mini",  # Fast, cheap for classification
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=300,
        )

        # Parse JSON response
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                raise ValueError("Failed to parse LLM response as JSON")

        return IntentDetectionResult(
            intent=ChatIntent(data["intent"].lower()),
            confidence=data["confidence"],
            extracted_entities=data.get("entities", {}),
            reasoning=data.get("reasoning", ""),
            suggested_agent=data.get("suggested_agent"),
        )

    def _keyword_classify_intent(self, message: str) -> IntentDetectionResult:
        """
        Keyword-based intent classification (fast fallback).

        Uses pattern matching to detect intent with high confidence.
        """
        message_lower = message.lower()

        # Protocol search patterns (highest priority)
        # Match flexible patterns: "show me protocols", "find protocols", "safe protocols on ethereum", etc.
        if any(kw in message_lower for kw in [
            "find protocol", "search protocol", "show protocol",
            "list protocol", "what protocols", "which protocol",
            "protocol for", "protocols that", "protocols with",
            "recommend protocol", "suggest protocol",
            "show me protocol", "give me protocol", "find me protocol",
        ]) or re.search(r'\b(show|find|list|give|suggest|recommend)\b.*\bprotocols?\b', message_lower):
            return IntentDetectionResult(
                intent=ChatIntent.PROTOCOL_SEARCH,
                confidence=0.90,
                extracted_entities=self._extract_search_entities(message),
                reasoning="Message contains protocol search keywords",
            )

        # Risk assessment patterns
        if any(kw in message_lower for kw in [
            "is it safe", "how safe", "safe to", "safety of",
            "analyze risk", "risk analysis", "risk assessment",
            "should i use", "should i supply", "should i stake",
            "is [a-z]+ safe", "how risky", "risk of"
        ]) or re.search(r'\b(is|how)\s+\w+\s+(safe|risky)', message_lower):
            return IntentDetectionResult(
                intent=ChatIntent.RISK_ASSESSMENT,
                confidence=0.88,
                extracted_entities=self._extract_risk_entities(message),
                reasoning="Message contains risk assessment keywords",
            )

        # Similar protocols patterns
        if any(kw in message_lower for kw in [
            "similar to", "alternative to", "alternatives to",
            "like [a-z]+", "protocols like", "similar protocols",
            "competitors", "other options", "what else",
            "compare to", "compared to"
        ]) or re.search(r'\b(similar|alternative|like)\s+(to\s+)?[A-Z][a-z]+', message):
            return IntentDetectionResult(
                intent=ChatIntent.SIMILAR_PROTOCOLS,
                confidence=0.85,
                extracted_entities=self._extract_protocol_name(message),
                reasoning="Message contains similarity/alternative keywords",
            )

        # Hunter AI: Sentiment Analysis patterns
        if any(kw in message_lower for kw in [
            "sentiment", "social sentiment", "market sentiment",
            "twitter sentiment", "reddit sentiment", "discord sentiment",
            "news sentiment", "bullish", "bearish", "market mood",
            "community sentiment", "how people feel", "what people think"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.HUNTER_SENTIMENT,
                confidence=0.92,
                extracted_entities=self._extract_hunter_entities(message),
                reasoning="Message contains sentiment analysis keywords",
            )

        # Hunter AI: Price Prediction patterns
        if any(kw in message_lower for kw in [
            "price prediction", "predict price", "price forecast",
            "will price", "price go", "price movement", "price target",
            "future price", "price outlook", "where price", "price heading"
        ]) or re.search(r'\bprice\s+(for|of|in)\b', message_lower):
            return IntentDetectionResult(
                intent=ChatIntent.HUNTER_PRICE_PREDICTION,
                confidence=0.90,
                extracted_entities=self._extract_hunter_entities(message),
                reasoning="Message contains price prediction keywords",
            )

        # Hunter AI: Risk Signals patterns
        if any(kw in message_lower for kw in [
            "risk signal", "market risk", "warning sign", "red flag",
            "risk indicator", "risk metric", "danger sign", "market warning",
            "risk level", "risk alert", "liquidation risk"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.HUNTER_RISK_SIGNALS,
                confidence=0.89,
                extracted_entities=self._extract_hunter_entities(message),
                reasoning="Message contains risk signal keywords",
            )

        # Hunter AI: Trading Signals patterns
        if any(kw in message_lower for kw in [
            "trading signal", "buy signal", "sell signal", "trade signal",
            "entry point", "exit point", "should i buy", "should i sell",
            "when to buy", "when to sell", "buy now", "sell now",
            "technical signal", "trade recommendation"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.HUNTER_TRADING_SIGNALS,
                confidence=0.91,
                extracted_entities=self._extract_hunter_entities(message),
                reasoning="Message contains trading signal keywords",
            )

        # Hunter AI: Pattern Detection patterns
        if any(kw in message_lower for kw in [
            "chart pattern", "price pattern", "trading pattern",
            "technical pattern", "pattern detected", "pattern analysis",
            "head and shoulders", "double top", "double bottom", "triangle",
            "support level", "resistance level", "trend line"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.HUNTER_PATTERNS,
                confidence=0.88,
                extracted_entities=self._extract_hunter_entities(message),
                reasoning="Message contains pattern detection keywords",
            )

        # Hunter AI: Portfolio Optimization patterns
        if any(kw in message_lower for kw in [
            "optimize portfolio", "portfolio allocation", "rebalance portfolio",
            "portfolio weights", "asset mix", "diversify portfolio",
            "portfolio strategy", "efficient frontier", "sharpe ratio"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.HUNTER_PORTFOLIO,
                confidence=0.90,
                extracted_entities=self._extract_hunter_entities(message),
                reasoning="Message contains portfolio optimization keywords",
            )

        # ULTRA: Arbitrage Discovery patterns
        if any(kw in message_lower for kw in [
            "arbitrage", "arbitrage opportunity", "find arbitrage",
            "arb opportunity", "cross-dex", "price difference",
            "triangular arbitrage", "2-hop", "3-hop",
            "profitable trade", "arbitrage profit"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.ULTRA_ARBITRAGE,
                confidence=0.92,
                extracted_entities=self._extract_ultra_entities(message),
                reasoning="Message contains arbitrage discovery keywords",
            )

        # ULTRA: Flash Loans patterns
        if any(kw in message_lower for kw in [
            "flash loan", "flash borrow", "uncollateralized loan",
            "aave flash", "balancer flash", "flash loan protocol",
            "best flash loan", "flash loan fee", "flash loan liquidity"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.ULTRA_FLASH_LOANS,
                confidence=0.93,
                extracted_entities=self._extract_ultra_entities(message),
                reasoning="Message contains flash loan keywords",
            )

        # ULTRA: MEV Protection patterns
        if any(kw in message_lower for kw in [
            "mev protect", "mev protection", "flashbots",
            "private relay", "bundle transaction", "mev shield",
            "frontrun protect", "sandwich protect", "execute arbitrage"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.ULTRA_MEV_PROTECTION,
                confidence=0.91,
                extracted_entities=self._extract_ultra_entities(message),
                reasoning="Message contains MEV protection keywords",
            )

        # ULTRA: Auto Executor patterns
        if any(kw in message_lower for kw in [
            "auto executor", "automated trading", "trading bot",
            "start bot", "stop bot", "pause bot", "resume bot",
            "auto trade", "automated execution", "bot status"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.ULTRA_AUTO_EXECUTOR,
                confidence=0.94,
                extracted_entities=self._extract_ultra_entities(message),
                reasoning="Message contains auto executor keywords",
            )

        # Specialist task patterns (yield optimization)
        if any(kw in message_lower for kw in [
            "best yield", "highest yield", "best apy", "highest apy",
            "yield for", "apy for", "earn on", "returns on"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.SPECIALIST_TASK,
                confidence=0.92,
                extracted_entities=self._extract_specialist_entities(message),
                reasoning="Message contains yield optimization keywords",
                suggested_agent="defi_yield",
            )

        # Specialist task patterns (gas optimization)
        if any(kw in message_lower for kw in [
            "optimize gas", "gas optimization", "reduce gas", "lower gas",
            "gas fee", "gas cost", "cheaper gas"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.SPECIALIST_TASK,
                confidence=0.90,
                extracted_entities=self._extract_specialist_entities(message),
                reasoning="Message contains gas optimization keywords",
                suggested_agent="gas_optimizer",
            )

        # Specialist task patterns (security/audits)
        if any(kw in message_lower for kw in [
            "security audit", "audit contract", "is contract safe",
            "smart contract security", "code review", "vulnerability"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.SPECIALIST_TASK,
                confidence=0.88,
                extracted_entities=self._extract_specialist_entities(message),
                reasoning="Message contains security audit keywords",
                suggested_agent="security_auditor",
            )

        # Specialist task patterns (portfolio)
        if any(kw in message_lower for kw in [
            "portfolio strategy", "rebalance portfolio", "diversify",
            "asset allocation", "portfolio optimization"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.SPECIALIST_TASK,
                confidence=0.85,
                extracted_entities=self._extract_specialist_entities(message),
                reasoning="Message contains portfolio management keywords",
                suggested_agent="portfolio",
            )

        # Specialist task patterns (tax)
        if any(kw in message_lower for kw in [
            "tax implications", "tax strategy", "tax loss", "tax harvest",
            "capital gains", "tax optimization"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.SPECIALIST_TASK,
                confidence=0.87,
                extracted_entities=self._extract_specialist_entities(message),
                reasoning="Message contains tax optimization keywords",
                suggested_agent="tax_optimizer",
            )

        # Complex workflow patterns
        if any(kw in message_lower for kw in [
            "create portfolio", "build portfolio", "create strategy",
            "build strategy", "comprehensive analysis", "full analysis",
            "plan migration", "migration strategy", "multi-step",
            "analyze and recommend", "compare and suggest"
        ]):
            return IntentDetectionResult(
                intent=ChatIntent.COMPLEX_WORKFLOW,
                confidence=0.82,
                extracted_entities=self._extract_workflow_entities(message),
                reasoning="Message contains complex workflow keywords",
            )

        # Default: General conversation
        return IntentDetectionResult(
            intent=ChatIntent.GENERAL_CONVERSATION,
            confidence=0.65,  # Low confidence for unclear messages
            extracted_entities={},
            reasoning="No specific intent detected, defaulting to general chat",
        )

    def _extract_search_entities(self, message: str) -> dict:
        """Extract entities for protocol search."""
        entities = {}
        message_lower = message.lower()

        # Extract chain
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

        # Extract category
        category_patterns = {
            "DEX": ["dex", "swap", "exchange", "trading"],
            "Lending": ["lending", "borrow", "supply"],
            "Staking": ["staking", "stake", "validator"],
            "Bridge": ["bridge", "cross-chain"],
            "Yield": ["yield", "farming", "liquidity"],
        }
        for category, keywords in category_patterns.items():
            if any(kw in message_lower for kw in keywords):
                entities["category"] = category
                break

        # Extract risk preference
        if any(kw in message_lower for kw in ["low-risk", "low risk", "safe", "conservative", "secure"]):
            entities["risk_preference"] = "low"
        elif any(kw in message_lower for kw in ["high-risk", "high risk", "risky", "aggressive"]):
            entities["risk_preference"] = "high"

        # Extract TVL preference
        if any(kw in message_lower for kw in ["high tvl", "large tvl", "big tvl"]):
            entities["tvl_preference"] = "high"

        return entities

    def _extract_risk_entities(self, message: str) -> dict:
        """Extract entities for risk assessment."""
        entities = {}

        # Extract protocol name (capitalized words)
        protocol_match = re.search(r'\b([A-Z][a-z]+(?:\s+V\d+)?)\b', message)
        if protocol_match:
            entities["protocol_name"] = protocol_match.group(1)

        # Extract amount
        amount_match = re.search(r'\$?([\d,]+)k?', message)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            amount = float(amount_str)
            if 'k' in message.lower():
                amount *= 1000
            entities["amount_usd"] = amount

        # Extract operation type
        operation_patterns = {
            "supply": ["supply", "deposit", "lend"],
            "borrow": ["borrow", "loan"],
            "swap": ["swap", "trade", "exchange"],
            "stake": ["stake", "staking"],
            "bridge": ["bridge", "transfer"],
        }
        for operation, keywords in operation_patterns.items():
            if any(kw in message.lower() for kw in keywords):
                entities["operation_type"] = operation
                break

        return entities

    def _extract_protocol_name(self, message: str) -> dict:
        """Extract protocol name from message."""
        # Look for capitalized protocol names
        protocol_match = re.search(r'\b([A-Z][a-z]+(?:\s+V\d+)?)\b', message)
        if protocol_match:
            return {"protocol_name": protocol_match.group(1)}
        return {}

    def _extract_specialist_entities(self, message: str) -> dict:
        """Extract entities for specialist tasks."""
        entities = {}

        # Extract token symbol
        token_match = re.search(
            r'\b(BTC|ETH|UNI|AAVE|LINK|MATIC|SOL|AVAX|ARB|OP|USDC|USDT|DAI|WBTC|WETH)\b',
            message.upper()
        )
        if token_match:
            entities["token_symbol"] = token_match.group(1)

        # Extract chain
        chain_patterns = {
            "ethereum": ["ethereum", " eth "],
            "arbitrum": ["arbitrum", " arb "],
            "polygon": ["polygon", "matic"],
            "base": [" base "],
            "optimism": ["optimism", " op "],
        }
        for chain, keywords in chain_patterns.items():
            if any(kw in message.lower() for kw in keywords):
                entities["chain"] = chain.capitalize()
                break

        # Extract protocol name
        protocol_match = re.search(r'\b([A-Z][a-z]+(?:\s+V\d+)?)\b', message)
        if protocol_match:
            entities["protocol_name"] = protocol_match.group(1)

        return entities

    def _extract_workflow_entities(self, message: str) -> dict:
        """Extract entities for complex workflows."""
        entities = {}

        # Extract amount
        amount_match = re.search(r'\$?([\d,]+)k?', message)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            amount = float(amount_str)
            if 'k' in message.lower():
                amount *= 1000
            entities["amount_usd"] = amount

        # Extract task type
        if "portfolio" in message.lower():
            entities["task_type"] = "portfolio_creation"
        elif "migration" in message.lower():
            entities["task_type"] = "migration_strategy"
        elif "analysis" in message.lower():
            entities["task_type"] = "comprehensive_analysis"

        return entities

    def _extract_hunter_entities(self, message: str) -> dict:
        """Extract entities for Hunter AI tasks."""
        entities = {}

        # Extract token symbols (BTC, ETH, SOL, etc.)
        token_pattern = r'\b([A-Z]{2,10})\b'
        token_matches = re.findall(token_pattern, message)
        if token_matches:
            # Filter out common words that match pattern
            common_words = {'USD', 'TVL', 'APY', 'DeFi', 'NFT', 'DAO', 'DEX'}
            tokens = [t for t in token_matches if t not in common_words]
            if tokens:
                entities["tokens"] = tokens
                entities["token_symbol"] = tokens[0]  # Primary token

        # Extract time horizon
        if any(kw in message.lower() for kw in ['24h', '24 hours', 'today', 'daily']):
            entities["time_horizon"] = "24h"
        elif any(kw in message.lower() for kw in ['7d', '7 days', 'week', 'weekly']):
            entities["time_horizon"] = "7d"
        elif any(kw in message.lower() for kw in ['30d', '30 days', 'month', 'monthly']):
            entities["time_horizon"] = "30d"
        else:
            entities["time_horizon"] = "24h"  # Default

        # Extract risk tolerance for portfolio optimization
        if "conservative" in message.lower() or "low risk" in message.lower():
            entities["risk_tolerance"] = 0.2
        elif "moderate" in message.lower() or "balanced" in message.lower():
            entities["risk_tolerance"] = 0.5
        elif "aggressive" in message.lower() or "high risk" in message.lower():
            entities["risk_tolerance"] = 0.8
        else:
            entities["risk_tolerance"] = 0.5  # Default moderate

        # Extract data sources for sentiment analysis
        sources = []
        if "twitter" in message.lower():
            sources.append("twitter")
        if "reddit" in message.lower():
            sources.append("reddit")
        if "discord" in message.lower():
            sources.append("discord")
        if "news" in message.lower():
            sources.append("news")
        if sources:
            entities["sources"] = sources

        return entities

    def _extract_ultra_entities(self, message: str) -> dict:
        """Extract entities for ULTRA tasks."""
        entities = {}

        # Extract capital/amount for arbitrage
        amount_pattern = r'\$?\s*(\d{1,3}(?:,\d{3})*|\d+)\s*(?:usd|dollars)?'
        amount_matches = re.findall(amount_pattern, message.lower())
        if amount_matches:
            # Clean and convert to float
            amount_str = amount_matches[0].replace(',', '')
            try:
                entities["capital"] = float(amount_str)
            except:
                entities["capital"] = 10000  # Default

        # Extract arbitrage type
        if "2-hop" in message.lower() or "2hop" in message.lower():
            entities["arb_type"] = "2hop"
        elif "3-hop" in message.lower() or "3hop" in message.lower():
            entities["arb_type"] = "3hop"
        elif "triangle" in message.lower() or "triangular" in message.lower():
            entities["arb_type"] = "triangle"

        # Extract flash loan protocol
        if "aave" in message.lower():
            entities["flash_loan_protocol"] = "aave_v3"
        elif "balancer" in message.lower():
            entities["flash_loan_protocol"] = "balancer"
        elif "uniswap" in message.lower():
            entities["flash_loan_protocol"] = "uniswap_v3"

        # Extract token for flash loans
        token_pattern = r'\b([A-Z]{2,10})\b'
        token_matches = re.findall(token_pattern, message)
        if token_matches:
            common_words = {'USD', 'MEV', 'TVL', 'APY', 'DeFi', 'NFT', 'DAO', 'DEX'}
            tokens = [t for t in token_matches if t not in common_words]
            if tokens:
                entities["token"] = tokens[0]

        # Extract bot action (for auto executor)
        if "start" in message.lower():
            entities["action"] = "start"
        elif "stop" in message.lower():
            entities["action"] = "stop"
        elif "pause" in message.lower():
            entities["action"] = "pause"
        elif "resume" in message.lower():
            entities["action"] = "resume"
        elif "status" in message.lower():
            entities["action"] = "status"

        # Extract opportunity ID for execution
        opp_id_pattern = r'(ARB-\d+-\d+)'
        opp_matches = re.findall(opp_id_pattern, message)
        if opp_matches:
            entities["opportunity_id"] = opp_matches[0]

        return entities
