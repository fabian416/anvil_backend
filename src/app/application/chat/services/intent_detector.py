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
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class ChatIntent(Enum):
    """Chat intent types for routing."""

    PROTOCOL_SEARCH = "protocol_search"
    RISK_ASSESSMENT = "risk_assessment"
    SIMILAR_PROTOCOLS = "similar_protocols"
    SPECIALIST_TASK = "specialist_task"
    COMPLEX_WORKFLOW = "complex_workflow"
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

    def __init__(self, llm_client: Optional[LLMClientGateway] = None):
        """
        Initialize intent detector.

        Args:
            llm_client: Optional LLM client for AI-powered classification
        """
        self._llm_client = llm_client

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
        if self._llm_client:
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

1. PROTOCOL_SEARCH - User wants to find/search for protocols
   Examples: "find staking protocols", "search for low-risk DEXs", "show me lending protocols on Ethereum"

2. RISK_ASSESSMENT - User wants risk analysis for a specific protocol
   Examples: "is Aave safe?", "analyze risk of Uniswap", "should I use Curve?"

3. SIMILAR_PROTOCOLS - User wants alternatives to a specific protocol
   Examples: "similar to Uniswap", "alternatives to Aave", "protocols like Curve"

4. SPECIALIST_TASK - User needs specialist agent (yield, gas, security, portfolio, etc.)
   Examples: "best USDC yield", "optimize gas", "tax implications", "create portfolio"

5. COMPLEX_WORKFLOW - User needs multi-step analysis or strategy
   Examples: "create a balanced portfolio", "comprehensive analysis of DeFi", "migration strategy"

6. GENERAL_CONVERSATION - General questions, education, explanations
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
        response = await self._llm_client.generate(
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
        if any(kw in message_lower for kw in [
            "find protocol", "search protocol", "show protocol",
            "list protocol", "what protocols", "which protocol",
            "protocol for", "protocols that", "protocols with",
            "recommend protocol", "suggest protocol"
        ]):
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
            confidence=0.75,
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
