"""
Context-aware intent refinement.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RefinedIntent:
    """Refined intent with confidence and context."""
    intent: str
    confidence: float
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    extracted_entities: Dict[str, Any] = None
    context_used: Dict[str, Any] = None


class IntentRefiner:
    """
    Context-aware intent refinement system.
    
    Improves intent classification using:
    - Conversation history
    - User preferences
    - Recent patterns
    - Ambiguity detection
    """
    
    # Ambiguous patterns that require clarification
    AMBIGUOUS_PATTERNS = {
        "trade": ["trade_swap", "trade_perp_open", "trade_perp_close"],
        "position": ["trade_perp_open", "portfolio_view"],
        "price": ["portfolio_view", "trade_swap"],
        "balance": ["portfolio_view"],
    }
    
    # Intent refinement rules based on context
    REFINEMENT_RULES = {
        # If user recently swapped, "trade" likely means swap
        "trade_swap": {
            "recent_intents": ["trade_swap"],
            "boost": 0.3,
        },
        # If user recently traded perps, "trade" likely means perp
        "trade_perp_open": {
            "recent_intents": ["trade_perp_open", "trade_perp_close"],
            "boost": 0.3,
        },
        # If topic is portfolio, "show" means portfolio
        "portfolio_view": {
            "current_topic": "portfolio",
            "boost": 0.2,
        },
    }
    
    def __init__(self):
        """Initialize intent refiner."""
        pass
    
    def refine_intent(
        self,
        message: str,
        initial_intent: str,
        initial_confidence: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> RefinedIntent:
        """
        Refine intent using context.
        
        Args:
            message: User message
            initial_intent: Initial classified intent
            initial_confidence: Initial confidence score
            context: Conversation context
        
        Returns:
            RefinedIntent with improved classification
        """
        context = context or {}
        
        # Start with initial values
        refined_intent = initial_intent
        confidence = initial_confidence
        requires_clarification = False
        clarification_question = None
        extracted_entities = {}
        context_used = {}
        
        # Check for ambiguity
        message_lower = message.lower()
        for pattern, possible_intents in self.AMBIGUOUS_PATTERNS.items():
            if pattern in message_lower and initial_confidence < 0.7:
                # Ambiguous - try to resolve with context
                resolved = self._resolve_ambiguity(
                    message,
                    possible_intents,
                    context,
                )
                
                if resolved:
                    refined_intent = resolved["intent"]
                    confidence = resolved["confidence"]
                    context_used = resolved["context_used"]
                else:
                    # Can't resolve - need clarification
                    requires_clarification = True
                    clarification_question = self._generate_clarification(
                        pattern,
                        possible_intents,
                    )
                
                break
        
        # Apply refinement rules
        if not requires_clarification and context:
            boost = self._calculate_context_boost(refined_intent, context)
            confidence = min(1.0, confidence + boost)
            
            if boost > 0:
                context_used["refinement_boost"] = boost
        
        # Extract entities from message
        extracted_entities = self._extract_entities(message, refined_intent)
        
        return RefinedIntent(
            intent=refined_intent,
            confidence=confidence,
            requires_clarification=requires_clarification,
            clarification_question=clarification_question,
            extracted_entities=extracted_entities,
            context_used=context_used,
        )
    
    def _resolve_ambiguity(
        self,
        message: str,
        possible_intents: List[str],
        context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve ambiguous intent using context.
        
        Args:
            message: User message
            possible_intents: Possible intent types
            context: Conversation context
        
        Returns:
            Resolved intent or None if can't resolve
        """
        # Check recent intents
        recent_intents = context.get("recent_intents", [])
        if recent_intents:
            for intent in possible_intents:
                if intent in recent_intents[-3:]:
                    return {
                        "intent": intent,
                        "confidence": 0.8,
                        "context_used": {"recent_intents": recent_intents[-3:]},
                    }
        
        # Check current topic
        current_topic = context.get("current_topic")
        if current_topic:
            topic_intent_map = {
                "swapping": "trade_swap",
                "trading": "trade_perp_open",
                "portfolio": "portfolio_view",
            }
            
            resolved_intent = topic_intent_map.get(current_topic)
            if resolved_intent and resolved_intent in possible_intents:
                return {
                    "intent": resolved_intent,
                    "confidence": 0.75,
                    "context_used": {"current_topic": current_topic},
                }
        
        # Check dominant action
        dominant = context.get("dominant_action")
        if dominant and dominant in possible_intents:
            return {
                "intent": dominant,
                "confidence": 0.7,
                "context_used": {"dominant_action": dominant},
            }
        
        return None
    
    def _calculate_context_boost(
        self,
        intent: str,
        context: Dict[str, Any],
    ) -> float:
        """
        Calculate confidence boost from context.
        
        Args:
            intent: Intent to boost
            context: Conversation context
        
        Returns:
            Boost amount (0-0.3)
        """
        if intent not in self.REFINEMENT_RULES:
            return 0.0
        
        rule = self.REFINEMENT_RULES[intent]
        boost = 0.0
        
        # Check recent intents
        if "recent_intents" in rule:
            user_recent = context.get("recent_intents", [])
            for required in rule["recent_intents"]:
                if required in user_recent[-5:]:
                    boost += rule["boost"]
                    break
        
        # Check current topic
        if "current_topic" in rule:
            if context.get("current_topic") == rule["current_topic"]:
                boost += rule["boost"]
        
        return boost
    
    def _generate_clarification(
        self,
        pattern: str,
        possible_intents: List[str],
    ) -> str:
        """
        Generate clarification question.
        
        Args:
            pattern: Ambiguous pattern
            possible_intents: Possible intents
        
        Returns:
            Clarification question
        """
        intent_questions = {
            "trade_swap": "swap tokens",
            "trade_perp_open": "open a perpetual position",
            "trade_perp_close": "close a position",
            "portfolio_view": "view your portfolio",
        }
        
        options = [intent_questions.get(i, i) for i in possible_intents]
        
        if len(options) == 2:
            return f"Do you want to {options[0]} or {options[1]}?"
        else:
            options_str = ", ".join(options[:-1]) + f", or {options[-1]}"
            return f"Do you want to {options_str}?"
    
    def _extract_entities(
        self,
        message: str,
        intent: str,
    ) -> Dict[str, Any]:
        """
        Extract entities from message based on intent.
        
        Args:
            message: User message
            intent: Classified intent
        
        Returns:
            Extracted entities
        """
        entities = {}
        message_lower = message.lower()
        
        # Extract common tokens
        common_tokens = ["BTC", "ETH", "USDC", "USDT", "DAI", "WBTC"]
        for token in common_tokens:
            if token.lower() in message_lower:
                if "tokens" not in entities:
                    entities["tokens"] = []
                entities["tokens"].append(token)
        
        # Extract amounts (simple regex-like)
        words = message.split()
        for i, word in enumerate(words):
            try:
                amount = float(word.replace(",", ""))
                if amount > 0:
                    entities["amount"] = str(amount)
                    # Try to get unit
                    if i + 1 < len(words):
                        next_word = words[i + 1].upper()
                        if next_word in common_tokens:
                            entities["token"] = next_word
                    break
            except ValueError:
                continue
        
        # Extract leverage for trading
        if intent.startswith("trade_perp"):
            for word in words:
                if word.endswith("x") and len(word) > 1:
                    try:
                        leverage = int(word[:-1])
                        if 1 <= leverage <= 100:
                            entities["leverage"] = leverage
                            break
                    except ValueError:
                        continue
        
        # Extract direction for trading
        if intent.startswith("trade_perp"):
            if "long" in message_lower:
                entities["is_long"] = True
            elif "short" in message_lower:
                entities["is_long"] = False
        
        return entities
