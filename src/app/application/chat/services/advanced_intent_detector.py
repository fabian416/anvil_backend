"""
Advanced intent detection service with real-time suggestions.

Uses unified chat system for conversation history queries.
"""

import re
import logging
from typing import List, Optional, Dict, Any, Protocol
from uuid import UUID
from datetime import datetime, timedelta, UTC

from app.domain.value_objects.chat import (
    IntentPrediction,
    IntentType,
    AgentSuggestion,
    AutocompleteSuggestion,
    ConversationMatch,
)
from app.domain.chat.entities.message import Message
from app.domain.chat.entities.chat_message import ChatMessage

logger = logging.getLogger(__name__)


class ChatMessageRepositoryProtocol(Protocol):
    """Protocol for chat message repository (unified chat system)."""
    
    async def list_for_conversation(
        self,
        conversation_id: UUID,
        limit: int = 50,
    ) -> list[ChatMessage]: ...
    
    async def search_user_messages(
        self,
        user_id: UUID,
        query: str,
        limit: int = 10,
    ) -> list[ChatMessage]: ...


class AdvancedIntentDetector:
    """
    Advanced intent detection with auto-suggestions and agent recommendations.

    Provides real-time intent classification, autocomplete suggestions,
    and similar conversation detection.
    """

    # Intent detection patterns
    INTENT_PATTERNS = {
        IntentType.SHOW_ANALYTICS: [
            r"show.*analytics",
            r"my.*statistics",
            r"chat.*metrics",
            r"conversation.*trends",
            r"show.*stats",
            r"how.*am I using",
        ],
        IntentType.RISK_ANALYSIS: [
            r"risk.*analysis",
            r"what.*risk",
            r"how.*risky",
            r"analyze.*risk",
            r"risk.*assessment",
            r"check.*risk",
        ],
        IntentType.YIELD_OPTIMIZATION: [
            r"yield.*optimization",
            r"better.*yield",
            r"optimize.*APY",
            r"find.*yield",
            r"higher.*returns",
            r"best.*yield",
        ],
        IntentType.PORTFOLIO_REVIEW: [
            r"portfolio.*review",
            r"check.*portfolio",
            r"analyze.*portfolio",
            r"portfolio.*health",
            r"my.*positions",
        ],
        IntentType.EXECUTE_TRADE: [
            r"execute.*trade",
            r"make.*swap",
            r"buy.*token",
            r"sell.*token",
            r"trade.*for",
        ],
        IntentType.EXECUTE_TEMPLATE: [
            r"run.*template",
            r"execute.*workflow",
            r"start.*template",
            r"run.*health check",
        ],
        IntentType.UPDATE_PREFERENCES: [
            r"make.*brief",
            r"make.*detailed",
            r"always.*use",
            r"prefer.*agent",
            r"set.*preference",
            r"update.*settings",
            r"auto.*delete",
        ],
        IntentType.EXPORT_CONVERSATION: [
            r"export.*conversation",
            r"export.*to PDF",
            r"download.*chat",
            r"save.*conversation",
        ],
        IntentType.TRANSLATE_CONTENT: [
            r"translate.*to",
            r"in.*Spanish",
            r"enable.*translation",
            r"show.*in.*language",
        ],
    }

    # Agent mappings for intents
    INTENT_TO_AGENT = {
        IntentType.RISK_ANALYSIS: "risk_analyzer",
        IntentType.YIELD_OPTIMIZATION: "yield_optimizer",
        IntentType.PORTFOLIO_REVIEW: "portfolio_manager",
        IntentType.MARKET_ANALYSIS: "hunter_ai",
        IntentType.EXECUTE_TRADE: "transaction_executor",
    }

    # Common DeFi protocols for autocomplete
    DEFI_PROTOCOLS = [
        "Aave",
        "Curve",
        "Morpho",
        "Uniswap",
        "Compound",
        "MakerDAO",
        "Lido",
        "Balancer",
        "Convex",
        "Yearn",
    ]

    # Common tokens
    TOKENS = [
        "ETH",
        "WETH",
        "USDC",
        "USDT",
        "DAI",
        "stETH",
        "wstETH",
        "WBTC",
        "CRV",
        "AAVE",
    ]

    # Common actions for autocomplete
    ACTIONS = [
        "analyze risk",
        "optimize yield",
        "check portfolio",
        "find opportunities",
        "execute trade",
        "review positions",
        "check analytics",
    ]

    def __init__(
        self,
        message_repository: Optional[ChatMessageRepositoryProtocol] = None,
    ):
        """
        Initialize intent detector.
        
        Args:
            message_repository: Optional unified chat message repository for
                               finding similar conversations
        """
        self._message_repository = message_repository

    async def detect_intent_while_typing(
        self,
        partial_message: str,
        conversation_context: Optional[List[Message]] = None,
    ) -> IntentPrediction:
        """
        Detect intent from partial user input (as they type).

        Args:
            partial_message: Partial message being typed
            conversation_context: Recent messages for context

        Returns:
            IntentPrediction with confidence score
        """
        if not partial_message or len(partial_message) < 3:
            return IntentPrediction.create(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                reasoning="Input too short",
            )

        message_lower = partial_message.lower()

        # Pattern-based detection
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        alternatives = []

        for intent_type, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    # Calculate confidence based on match quality
                    match_length = len(pattern)
                    total_length = len(message_lower)
                    confidence = min(0.95, match_length / total_length * 1.2)

                    if confidence > best_confidence:
                        if best_confidence > 0.4:  # Add previous best as alternative
                            alternatives.append((best_intent, best_confidence))
                        best_intent = intent_type
                        best_confidence = confidence
                    elif confidence > 0.4:
                        alternatives.append((intent_type, confidence))

        # Get suggested agent
        suggested_agent = self.INTENT_TO_AGENT.get(best_intent)

        # Extract entities
        entities = self._extract_entities(partial_message)

        return IntentPrediction.create(
            intent_type=best_intent,
            confidence=best_confidence,
            suggested_agent=suggested_agent,
            extracted_entities=entities,
            reasoning=f"Pattern match for '{best_intent.value}'" if best_confidence > 0 else "No clear intent detected",
            alternative_intents=alternatives,
        )

    async def suggest_completions(
        self,
        partial_message: str,
        user_id: UUID,
        limit: int = 5,
    ) -> List[AutocompleteSuggestion]:
        """
        Generate autocomplete suggestions for partial input.

        Args:
            partial_message: Partial message being typed
            user_id: User identifier for personalized suggestions
            limit: Maximum number of suggestions

        Returns:
            List of autocomplete suggestions
        """
        if not partial_message or len(partial_message) < 2:
            return []

        suggestions = []
        partial_lower = partial_message.lower()

        # Suggest DeFi protocols
        for protocol in self.DEFI_PROTOCOLS:
            if protocol.lower().startswith(partial_lower) or partial_lower in protocol.lower():
                completion = partial_message + protocol[len(partial_message):]
                suggestions.append(
                    AutocompleteSuggestion.create(
                        completion_text=completion,
                        display_text=f"What's the risk of {protocol}?",
                        confidence=0.9,
                        suggestion_type="protocol",
                        icon="🏦",
                        metadata={"protocol": protocol},
                    )
                )

        # Suggest tokens
        for token in self.TOKENS:
            if token.lower().startswith(partial_lower):
                suggestions.append(
                    AutocompleteSuggestion.create(
                        completion_text=f"{partial_message}{token[len(partial_message):]}",
                        display_text=f"Analyze {token} position",
                        confidence=0.85,
                        suggestion_type="token",
                        icon="🪙",
                        metadata={"token": token},
                    )
                )

        # Suggest common actions
        for action in self.ACTIONS:
            if action.startswith(partial_lower):
                suggestions.append(
                    AutocompleteSuggestion.create(
                        completion_text=action,
                        display_text=action.capitalize(),
                        confidence=0.8,
                        suggestion_type="action",
                        icon="⚡",
                        metadata={"action": action},
                    )
                )

        # Sort by confidence and limit
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:limit]

    async def suggest_agents(
        self,
        detected_intent: IntentPrediction,
    ) -> List[AgentSuggestion]:
        """
        Suggest appropriate agents for detected intent.

        Args:
            detected_intent: Detected intent prediction

        Returns:
            List of agent suggestions
        """
        suggestions = []

        # Primary agent from intent
        primary_agent = self.INTENT_TO_AGENT.get(detected_intent.intent_type)
        if primary_agent:
            suggestions.append(
                AgentSuggestion.create(
                    agent_name=primary_agent,
                    confidence=detected_intent.confidence,
                    reasoning=f"Best agent for {detected_intent.intent_type.value}",
                    agent_description=self._get_agent_description(primary_agent),
                    estimated_response_time_seconds=self._estimate_response_time(primary_agent),
                )
            )

        # Suggest alternative agents for ambiguous intents
        if detected_intent.is_ambiguous and detected_intent.alternative_intents:
            for alt_intent, alt_conf in detected_intent.alternative_intents[:2]:
                alt_agent = self.INTENT_TO_AGENT.get(alt_intent)
                if alt_agent and alt_agent != primary_agent:
                    suggestions.append(
                        AgentSuggestion.create(
                            agent_name=alt_agent,
                            confidence=alt_conf,
                            reasoning=f"Alternative for {alt_intent.value}",
                            agent_description=self._get_agent_description(alt_agent),
                            estimated_response_time_seconds=self._estimate_response_time(alt_agent),
                        )
                    )

        return suggestions

    async def find_similar_conversations(
        self,
        current_message: str,
        user_id: UUID,
        limit: int = 3,
        similarity_threshold: float = 0.7,
    ) -> List[ConversationMatch]:
        """
        Find similar past conversations using unified chat system.

        Args:
            current_message: Current user message
            user_id: User identifier
            limit: Maximum number of matches
            similarity_threshold: Minimum similarity score

        Returns:
            List of conversation matches
        """
        if not self._message_repository:
            logger.debug("Message repository not available for similarity search")
            return []
        
        # Extract key terms from current message for keyword-based matching
        keywords = self._extract_search_keywords(current_message)
        if not keywords:
            return []
        
        matches = []
        
        try:
            # Search user's past messages for similar content
            # Note: For better results, implement semantic search with embeddings
            for keyword in keywords[:3]:  # Limit to top 3 keywords
                if hasattr(self._message_repository, 'search_user_messages'):
                    results = await self._message_repository.search_user_messages(
                        user_id=user_id,
                        query=keyword,
                        limit=limit,
                    )
                    
                    for msg in results:
                        # Calculate simple keyword similarity score
                        similarity = self._calculate_keyword_similarity(
                            current_message, msg.content
                        )
                        
                        if similarity >= similarity_threshold:
                            matches.append(
                                ConversationMatch.create(
                                    conversation_id=msg.conversation_id,
                                    similarity_score=similarity,
                                    matching_query=keyword,
                                    preview_text=msg.content[:200],
                                    message_count=1,  # Would need additional query
                                    created_at=msg.created_at,
                                )
                            )
        except Exception as e:
            logger.warning(f"Error searching similar conversations: {e}")
            return []
        
        # Deduplicate by conversation_id and sort by similarity
        seen_convs = set()
        unique_matches = []
        for match in sorted(matches, key=lambda m: m.similarity_score, reverse=True):
            if match.conversation_id not in seen_convs:
                seen_convs.add(match.conversation_id)
                unique_matches.append(match)
                if len(unique_matches) >= limit:
                    break
        
        return unique_matches
    
    def _extract_search_keywords(self, message: str) -> List[str]:
        """
        Extract meaningful keywords from message for search.
        
        Args:
            message: User message
            
        Returns:
            List of keywords
        """
        # Remove common words and extract meaningful terms
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
            'from', 'as', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why',
            'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 'just', 'i', 'me', 'my', 'myself',
            'we', 'our', 'you', 'your', 'he', 'she', 'it', 'they', 'what',
        }
        
        # Tokenize and filter
        words = re.findall(r'\b[a-zA-Z]{3,}\b', message.lower())
        keywords = [w for w in words if w not in stopwords]
        
        # Add extracted entities (protocols, tokens) as high-priority keywords
        entities = self._extract_entities(message)
        if 'protocols' in entities:
            keywords = entities['protocols'] + keywords
        if 'tokens' in entities:
            keywords = entities['tokens'] + keywords
        
        return keywords[:10]  # Limit keywords
    
    def _calculate_keyword_similarity(
        self,
        message1: str,
        message2: str,
    ) -> float:
        """
        Calculate simple keyword-based similarity between messages.
        
        Args:
            message1: First message
            message2: Second message
            
        Returns:
            Similarity score between 0 and 1
        """
        keywords1 = set(self._extract_search_keywords(message1))
        keywords2 = set(self._extract_search_keywords(message2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        return intersection / union if union > 0 else 0.0

    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """
        Extract entities from message (protocols, tokens, amounts).

        Args:
            message: User message

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        # Extract protocols
        found_protocols = [
            protocol
            for protocol in self.DEFI_PROTOCOLS
            if protocol.lower() in message.lower()
        ]
        if found_protocols:
            entities["protocols"] = found_protocols

        # Extract tokens
        found_tokens = [
            token for token in self.TOKENS if token.lower() in message.lower()
        ]
        if found_tokens:
            entities["tokens"] = found_tokens

        # Extract amounts (simple regex)
        amount_match = re.search(r"(\$?[\d,]+\.?\d*)\s*(USD|ETH|BTC)?", message)
        if amount_match:
            entities["amount"] = amount_match.group(1).replace(",", "")
            if amount_match.group(2):
                entities["currency"] = amount_match.group(2)

        return entities

    def _get_agent_description(self, agent_name: str) -> str:
        """
        Get human-readable description of agent.

        Args:
            agent_name: Agent identifier

        Returns:
            Agent description
        """
        descriptions = {
            "risk_analyzer": "Analyzes portfolio risk and identifies vulnerabilities",
            "yield_optimizer": "Finds better yield opportunities with similar risk",
            "portfolio_manager": "Reviews overall portfolio health and allocation",
            "hunter_ai": "Discovers new DeFi opportunities and market trends",
            "transaction_executor": "Executes trades and on-chain transactions",
        }
        return descriptions.get(agent_name, "AI agent")

    def _estimate_response_time(self, agent_name: str) -> int:
        """
        Estimate response time for agent in seconds.

        Args:
            agent_name: Agent identifier

        Returns:
            Estimated seconds for response
        """
        # Simple estimates - can be refined based on real metrics
        estimates = {
            "risk_analyzer": 8,
            "yield_optimizer": 12,
            "portfolio_manager": 15,
            "hunter_ai": 20,
            "transaction_executor": 10,
        }
        return estimates.get(agent_name, 10)
