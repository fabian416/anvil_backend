"""Intent classification service."""

import re
import logging
from typing import Tuple, Optional, List, Dict, Any

from app.domain.value_objects.distillation import Intent

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classify user intent using hybrid approach:
    1. Rule-based patterns (fast, ~90% accuracy) - for common patterns
    2. LLM-based classification (Vertex AI with DeepInfra fallback) - for complex/ambiguous queries

    LLM classification provides:
    - Better accuracy for ambiguous queries
    - Context-aware classification (uses conversation history)
    - Helps Supervisor Coordinator route correctly
    """

    def __init__(
        self,
        llm_client: Optional[
            Any
        ] = None,  # LLMClientGateway - optional for LLM-based classification
        use_llm_for_ambiguous: bool = True,  # Use LLM for ambiguous queries
        llm_confidence_threshold: float = 0.85,  # Minimum confidence to use LLM result
    ):
        """
        Initialize intent classifier.

        Args:
            llm_client: Optional LLM client gateway (Vertex AI/DeepInfra) for LLM-based classification
            use_llm_for_ambiguous: Whether to use LLM for ambiguous queries (default: True)
            llm_confidence_threshold: Minimum confidence threshold for LLM results (default: 0.85)
        """
        self._llm_client = llm_client
        self._use_llm_for_ambiguous = use_llm_for_ambiguous
        self._llm_confidence_threshold = llm_confidence_threshold

    # Intent patterns (regex) - for fast rule-based classification
    INTENT_PATTERNS = {
        # Informational
        Intent.PRICE_CHECK: [
            r"\b(price|cost|worth|value) of (\w+|ETH|BTC|USDC)",
            r"what('s| is) (\w+|ETH|BTC) (price|worth|trading at)",
            r"how much is (\w+|ETH|BTC)",
            r"(\w+|ETH|BTC) price",
        ],
        Intent.BALANCE_CHECK: [
            r"\b(my )?(balance|holdings|portfolio)\b",
            r"what do i (have|own)",
            r"show me my (assets|tokens)",
        ],
        Intent.GAS_CHECK: [
            r"\bgas (price|fee|cost)",
            r"current gas",
            r"how much gas",
        ],
        Intent.APY_CHECK: [
            r"\b(apy|yield|interest rate) (on|for)",
            r"what('s| is) the (apy|yield)",
            r"(earning|lending) rate",
        ],
        Intent.STATUS_CHECK: [
            r"is (\w+) (working|up|down|online)",
            r"(\w+) status",
            r"can i use (\w+)",
        ],
        # Educational
        Intent.EXPLAIN_CONCEPT: [
            r"what is (a |an )?(\w+)",
            r"what('s| is) (\w+)",
            r"explain (\w+)",
            r"(tell me about|define) (\w+)",
            r"how does (\w+) work",
            # Token-specific patterns (check these FIRST for crypto tokens)
            r"what is (bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
            r"what('s| is) (bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
            r"explain (bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
            r"(tell me about|define) (bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
            # Multi-language patterns
            r"(qué es|o que é|什么是) (bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
            r"(cuéntame sobre|fale sobre|告诉我关于) (bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
        ],
        Intent.HOW_TO: [
            r"how (do i|to) (\w+)",
            r"(steps|guide) (to|for) (\w+)",
            r"how can i (\w+)",
        ],
        Intent.COMPARE: [
            r"(compare|difference between) (\w+) (and|vs) (\w+)",
            r"(\w+) vs (\w+)",
            r"which is better (\w+) or (\w+)",
        ],
        # Transactional
        Intent.SWAP_REQUEST: [
            r"\b(swap|exchange|trade|convert) \d+",
            r"buy (\w+) with (\w+)",
            r"sell \d+ (\w+)",
            r"trade (\w+) for (\w+)",
        ],
        Intent.STAKE_REQUEST: [
            r"\bstake \d+",
            r"stake my (\w+)",
            r"staking (\w+)",
        ],
        Intent.LEND_REQUEST: [
            r"\b(lend|deposit|supply) \d+",
            r"(lend|deposit) (\w+) (on|to|in)",
        ],
        Intent.BORROW_REQUEST: [
            r"\bborrow \d+",
            r"borrow (\w+) (against|using)",
            r"take (a )?loan",
        ],
        Intent.BRIDGE_REQUEST: [
            r"\bbridge (\w+) (to|from)",
            r"move (\w+) to (\w+) chain",
            r"transfer to (\w+) (network|chain)",
        ],
        # Analytical
        Intent.PORTFOLIO_ANALYSIS: [
            r"(analyze|review) my portfolio",
            r"portfolio (analysis|breakdown|performance)",
            r"how('s| is) my portfolio",
        ],
        Intent.RISK_ASSESSMENT: [
            r"(risk|risky|safe) (of|is)",
            r"(assess|check) (the )?risk",
            r"is this (safe|risky)",
        ],
        Intent.YIELD_OPTIMIZATION: [
            r"best (yield|apy) for",
            r"(optimize|maximize) (yield|returns)",
            r"where (to|should i) (put|deposit|lend)",
        ],
        Intent.STRATEGY_ADVICE: [
            r"(strategy|plan) for",
            r"should i (\w+)",
            r"(advice|recommend|suggest) (for|on)",
        ],
        # Administrative
        Intent.SETTINGS_CHANGE: [
            r"(change|update|set) (my )?(settings|preferences|slippage)",
            r"set (\w+) to",
        ],
        Intent.ALERT_SETUP: [
            r"(alert|notify|tell) me (when|if)",
            r"set (up )?(an )?alert",
        ],
        # Off-topic / Other
        Intent.GREETING: [
            r"^(hello|hi|hey|greetings|good (morning|afternoon|evening)|hola|holi|hey there)",
        ],
        Intent.SMALL_TALK: [
            r"how are you",
            r"what('s| is) up",
            r"how('s| is) it going",
        ],
    }

    async def classify(
        self,
        text: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Intent, float]:
        """
        Classify intent with confidence score.

        Uses hybrid approach:
        1. Rule-based patterns (fast, high confidence)
        2. LLM-based classification (for ambiguous queries, with conversation context)

        Args:
            text: User query text
            conversation_history: Optional conversation history for context-aware classification

        Returns:
            Tuple of (Intent, confidence)
        """
        # Normalize text
        text_lower = text.lower().strip()

        # Step 1: Try rule-based patterns first (fastest, high confidence)
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    logger.debug(
                        f"✅ Rule-based classification: {intent.value} (confidence: 0.95)"
                    )
                    return intent, 0.95

        # Step 2: If no rule match and LLM available, use LLM for ambiguous queries
        if self._use_llm_for_ambiguous and self._llm_client:
            try:
                llm_intent, llm_confidence = await self._classify_with_llm(
                    text=text,
                    conversation_history=conversation_history,
                )

                # Use LLM result if confidence is above threshold
                if llm_confidence >= self._llm_confidence_threshold:
                    logger.debug(
                        f"✅ LLM-based classification: {llm_intent.value} (confidence: {llm_confidence})"
                    )
                    return llm_intent, llm_confidence
                else:
                    logger.debug(
                        f"⚠️ LLM classification confidence too low ({llm_confidence} < {self._llm_confidence_threshold}), falling back to UNCLEAR"
                    )
            except Exception as e:
                logger.warning(
                    f"⚠️ LLM classification failed: {e}, falling back to UNCLEAR"
                )

        # Step 3: Fallback to UNCLEAR if no match
        logger.debug(f"⚠️ No classification match, returning UNCLEAR (confidence: 0.5)")
        return Intent.UNCLEAR, 0.5

    async def _classify_with_llm(
        self,
        text: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Intent, float]:
        """
        Classify intent using LLM (Vertex AI with DeepInfra fallback).

        Args:
            text: User query text
            conversation_history: Optional conversation history for context

        Returns:
            Tuple of (Intent, confidence)
        """
        # Build classification prompt
        prompt = self._build_classification_prompt(text, conversation_history)

        # Call LLM for classification (Vertex AI with DeepInfra fallback)
        try:
            response = await self._llm_client.classify_intent(
                prompt=prompt,
                model="gemini-2.0-flash",  # Fast Vertex AI model (LLMClientWithFallback will handle fallback to DeepInfra if needed)
            )

            # Parse LLM response
            if isinstance(response, dict):
                intent_str = response.get("intent", "unclear")
                confidence = float(response.get("confidence", 0.5))
                reasoning = response.get("reasoning", "")

                logger.debug(
                    f"🔍 LLM classification result: intent={intent_str}, confidence={confidence}, reasoning={reasoning[:100]}"
                )

                # Map string intent to Intent enum
                try:
                    intent = Intent(intent_str.lower())
                    return intent, confidence
                except ValueError:
                    logger.warning(
                        f"⚠️ Unknown intent from LLM: {intent_str}, falling back to UNCLEAR"
                    )
                    return Intent.UNCLEAR, 0.5
            else:
                logger.warning(f"⚠️ Invalid LLM response format: {type(response)}")
                return Intent.UNCLEAR, 0.5

        except Exception as e:
            logger.error(f"❌ LLM classification error: {e}", exc_info=True)
            raise

    def _build_classification_prompt(
        self,
        text: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Build classification prompt for LLM.

        Args:
            text: User query text
            conversation_history: Optional conversation history

        Returns:
            Classification prompt string
        """
        # Build context from conversation history
        context_section = ""
        if conversation_history and len(conversation_history) > 0:
            context_section = "\n\n**Conversation History (for context):**\n"
            # Include last 3 messages for context (avoid too much history)
            recent_history = conversation_history[-3:]
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    context_section += (
                        f"- {role}: {content[:200]}\n"  # Truncate long messages
                    )

        # Build classification prompt
        prompt = f"""Classify the user's intent from this DeFi/crypto query.

**Available Intent Categories:**
- **Informational**: price_check, balance_check, apy_check, gas_check, status_check
- **Educational**: explain_concept, how_to, compare
- **Transactional**: swap_request, stake_request, lend_request, borrow_request, bridge_request
- **Analytical**: portfolio, risk_assessment, yield_optimize, strategy
- **Administrative**: settings, alert_setup
- **Other**: greeting, small_talk, off_topic, unclear

**User Query:**
{text}
{context_section}
**Classification Instructions:**
1. Analyze the user's query and conversation context
2. Identify the PRIMARY intent (most specific match)
3. Consider conversation history for context (e.g., if previous message was about swaps, "what's the price?" likely refers to swap prices)
4. Use conversation history to disambiguate ambiguous queries
5. Return intent and confidence score (0.0-1.0)
6. **CRITICAL**: This classification helps the Supervisor Coordinator route queries correctly - be precise and context-aware

**Examples:**
- "what is the price of BTC?" → {{"intent": "price_check", "confidence": 0.95, "reasoning": "User asking for token price"}}
- "swap 100 USDC for ETH" → {{"intent": "swap_request", "confidence": 0.98, "reasoning": "Explicit swap request with amount and tokens"}}
- "what type of swaps can I make?" → {{"intent": "explain_concept", "confidence": 0.90, "reasoning": "Educational query about swap types"}}
- "what is Anvil?" → {{"intent": "explain_concept", "confidence": 0.95, "reasoning": "Educational query about platform"}}

**Respond with ONLY valid JSON (no markdown, no explanations):**
{{
    "intent": "intent_name",
    "confidence": 0.95,
    "reasoning": "brief explanation"
}}
"""
        return prompt
