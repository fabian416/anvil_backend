"""
Agent Squad Intent Detection Adapter.

Uses Agent Squad's IntentClassifier for generic LLM-based intent detection.
No manual patterns required - fully generic and context-aware.
"""

import json
import logging
from typing import TYPE_CHECKING, Optional

from app.domain.ports.chat.intent_detection_port import (
    IntentDetectionPort,
    IntentDetectionRequest,
    IntentDetectionResult,
)
from app.application.chat.services.intent_detector import ChatIntent
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import (
    ConversationContext as AgentSquadContext,
)

if TYPE_CHECKING:
    from app.domain.services.agent_squad.intent_classifier import IntentClassifier
    from app.domain.services.agent_squad.supervisor_coordinator import SupervisorCoordinator

logger = logging.getLogger(__name__)


class AgentSquadIntentAdapter(IntentDetectionPort):
    """
    LLM-based intent detection using Agent Squad's IntentClassifier.
    
    Advantages:
    - Generic: No hardcoded patterns
    - Context-aware: Understands conversation history
    - Detects compound/sequential intents
    - Automatic agent mapping
    - Language-agnostic (via LLM)
    """

    # Map Agent Squad intents to ChatIntent enum
    INTENT_MAP = {
        # Core intents
        "general_chat": ChatIntent.GENERAL_CONVERSATION,
        "market_sentiment": ChatIntent.HUNTER_SENTIMENT,
        "research_protocol": ChatIntent.PROTOCOL_SEARCH,
        "swap_tokens": ChatIntent.SWAP,
        "execute_transaction": ChatIntent.SWAP,
        "analyze_risk": ChatIntent.RISK_ASSESSMENT,
        "risk_assessment": ChatIntent.RISK_ASSESSMENT,
        "optimize_portfolio": ChatIntent.PORTFOLIO,
        "rebalance_portfolio": ChatIntent.PORTFOLIO,
        "tax_optimization": ChatIntent.SPECIALIST_TASK,
        "tax_loss_harvesting": ChatIntent.SPECIALIST_TASK,
        "find_yield": ChatIntent.LENDING,
        "yield_farming": ChatIntent.LENDING,
        "audit_contract": ChatIntent.SPECIALIST_TASK,
        "security_audit": ChatIntent.SPECIALIST_TASK,
        "optimize_gas": ChatIntent.SPECIALIST_TASK,
        "gas_estimation": ChatIntent.SPECIALIST_TASK,
        
        # Enterprise intents
        "check_compliance": ChatIntent.SPECIALIST_TASK,
        "screen_wallet": ChatIntent.SPECIALIST_TASK,
        "manage_multisig": ChatIntent.SPECIALIST_TASK,
        "treasury_management": ChatIntent.SPECIALIST_TASK,
        "setup_alerts": ChatIntent.SPECIALIST_TASK,
        "monitor_portfolio": ChatIntent.SPECIALIST_TASK,
        "crisis_response": ChatIntent.SPECIALIST_TASK,
        "emergency_withdrawal": ChatIntent.SPECIALIST_TASK,
        "bridge_tokens": ChatIntent.SPECIALIST_TASK,
        "cross_chain": ChatIntent.SPECIALIST_TASK,
        "borrow_assets": ChatIntent.LENDING,
        "leverage_position": ChatIntent.LENDING,
        "manage_nfts": ChatIntent.SPECIALIST_TASK,
        "nft_valuation": ChatIntent.SPECIALIST_TASK,
        "dao_voting": ChatIntent.SPECIALIST_TASK,
        "governance_proposal": ChatIntent.SPECIALIST_TASK,
    }

    # Intent to handler mapping
    INTENT_TO_HANDLER = {
        ChatIntent.PROTOCOL_SEARCH: "graphrag_search",
        ChatIntent.RISK_ASSESSMENT: "graphrag_search",
        ChatIntent.SIMILAR_PROTOCOLS: "graphrag_search",
        ChatIntent.HUNTER_SENTIMENT: "hunter_ai",
        ChatIntent.HUNTER_PRICE_PREDICTION: "hunter_ai",
        ChatIntent.HUNTER_RISK_SIGNALS: "hunter_ai",
        ChatIntent.HUNTER_TRADING_SIGNALS: "hunter_ai",
        ChatIntent.HUNTER_PATTERNS: "hunter_ai",
        ChatIntent.HUNTER_PORTFOLIO: "hunter_ai",
        ChatIntent.ULTRA_ARBITRAGE: "ultra",
        ChatIntent.ULTRA_FLASH_LOANS: "ultra",
        ChatIntent.ULTRA_MEV_PROTECTION: "ultra",
        ChatIntent.ULTRA_AUTO_EXECUTOR: "ultra",
        ChatIntent.LENDING: "lending_handler",
        ChatIntent.MONEY_MARKET: "money_market_handler",
        ChatIntent.SWAP: "swap_handler",
        ChatIntent.SWAP_MOONPAY: "moonpay_swap_handler",
        ChatIntent.BALANCE: "balance_handler",
        ChatIntent.PORTFOLIO: "portfolio_handler",
        ChatIntent.ACTIVITY: "activity_handler",
        ChatIntent.RECEIVE: "receive_handler",
        ChatIntent.BUY: "buy_handler",
        ChatIntent.SEND: "send_handler",
        ChatIntent.SPECIALIST_TASK: "agent_orchestrator",
        ChatIntent.COMPLEX_WORKFLOW: "agent_orchestrator",
        ChatIntent.GENERAL_CONVERSATION: "general_chat",
    }

    def __init__(
        self,
        intent_classifier: "IntentClassifier",
        supervisor_coordinator: "SupervisorCoordinator | None" = None,
    ):
        """
        Initialize Agent Squad intent adapter.
        
        Args:
            intent_classifier: Agent Squad's IntentClassifier (LLM-based)
            supervisor_coordinator: Optional supervisor for compound intents
        """
        self._intent_classifier = intent_classifier
        self._supervisor = supervisor_coordinator

    async def detect_intent(
        self,
        request: IntentDetectionRequest,
    ) -> IntentDetectionResult:
        """
        Detect intent using Agent Squad's IntentClassifier.
        
        Flow:
        1. Check for compound intents (multiple queries)
        2. If compound → Return COMPLEX_WORKFLOW intent
        3. If single → Use IntentClassifier
        4. Map Agent Squad intent to ChatIntent
        """
        try:
            # Build Agent Squad conversation context
            context = self._build_agent_squad_context(request)
            
            # Check for compound intents first
            is_compound = await self._detect_compound_intent(
                request.message, context
            )
            
            if is_compound:
                logger.info(
                    "🔀 Compound intent detected",
                    extra={
                        "query": request.message[:100],
                        "intent": "COMPLEX_WORKFLOW",
                    }
                )
                return IntentDetectionResult(
                    intent=ChatIntent.COMPLEX_WORKFLOW,
                    confidence=0.95,
                    entities={},
                    reasoning="Detected multiple intents in query - requires multi-agent workflow",
                    handler="agent_orchestrator",
                )
            
            # Single intent → Use IntentClassifier
            classification = await self._intent_classifier.classify(
                message=MessageContent(request.message),
                conversation_context=context,
            )
            
            # Map Agent Squad intent to ChatIntent
            chat_intent = self._map_to_chat_intent(classification.intent)
            
            # Extract entities using LLM (if needed)
            entities = await self._extract_entities_llm(
                request.message, chat_intent, context
            )
            
            # Get handler
            handler = self.INTENT_TO_HANDLER.get(
                chat_intent, "general_chat"
            )
            
            # Get suggested agent from classification
            suggested_agent = (
                classification.agent_type.value
                if hasattr(classification, "agent_type")
                else None
            )
            
            logger.debug(
                "✅ Intent classified",
                extra={
                    "intent": chat_intent.value,
                    "confidence": classification.confidence,
                    "agent": suggested_agent,
                }
            )
            
            return IntentDetectionResult(
                intent=chat_intent,
                confidence=classification.confidence,
                entities=entities,
                reasoning=classification.reasoning,
                handler=handler,
                suggested_agent=suggested_agent,
            )
            
        except Exception as e:
            logger.error(
                "❌ Intent detection failed",
                extra={"error": str(e), "message": request.message[:100]},
                exc_info=True,
            )
            # Fallback to general conversation
            return IntentDetectionResult(
                intent=ChatIntent.GENERAL_CONVERSATION,
                confidence=0.5,
                entities={},
                reasoning=f"Intent detection failed: {e}",
                handler="general_chat",
            )

    def _build_agent_squad_context(
        self, request: IntentDetectionRequest
    ) -> AgentSquadContext:
        """Build Agent Squad conversation context from request."""
        conversation_history = []
        
        if request.conversation_history:
            for msg in request.conversation_history[-10:]:  # Last 10 messages
                role = "user"
                content = ""
                if hasattr(msg, "role"):
                    role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
                if hasattr(msg, "content"):
                    content = msg.content
                elif isinstance(msg, str):
                    content = msg
                
                conversation_history.append({
                    "role": role,
                    "content": content,
                })
        
        return AgentSquadContext(
            conversation_history=conversation_history,
            user_metadata=request.user_context or {},
            session_metadata={},
        )

    async def _detect_compound_intent(
        self,
        message: str,
        context: AgentSquadContext,
    ) -> bool:
        """
        Detect if query contains multiple intents using LLM.
        
        Examples:
        - "what's the price of btc, and what swaps you can make?"
        - "analyze risk and optimize portfolio"
        """
        # First, try simple pattern matching (fast, reliable)
        compound_indicators = [
            " and ",
            ", and ",
            " then ",
            " also ",
            ", then ",
            ", also ",
            " and what ",
            " and show ",
            " and tell ",
            " and make ",
            " and get ",
        ]
        
        message_lower = message.lower()
        has_compound_pattern = any(indicator in message_lower for indicator in compound_indicators)
        
        # If no pattern, likely single intent
        if not has_compound_pattern:
            return False
        
        # Pattern found → Use LLM to confirm it's actually compound (not just "BTC and ETH" in single swap)
        try:
            # Build prompt for compound intent detection
            prompt = f"""
Analyze this user query and determine if it contains MULTIPLE distinct intents that require separate handling.

Query: {message}

Respond with JSON:
{{
    "is_compound": true/false,
    "intents": ["intent1", "intent2", ...],
    "reasoning": "explanation"
}}

Examples:
- "what's the price of btc, and what swaps you can make?"
  → {{"is_compound": true, "intents": ["price_query", "swap_query"], "reasoning": "Two distinct queries"}}
- "analyze risk and optimize portfolio"
  → {{"is_compound": true, "intents": ["risk_analysis", "portfolio_optimization"], "reasoning": "Two distinct tasks"}}
- "swap BTC and ETH to USDC"
  → {{"is_compound": false, "intents": ["swap"], "reasoning": "Single swap intent with multiple tokens"}}
- "swap ETH to USDC"
  → {{"is_compound": false, "intents": ["swap"], "reasoning": "Single clear intent"}}

Guidelines:
- Compound = Multiple distinct queries/tasks in one message
- Single intent with multiple entities is NOT compound
"""
            
            # Use IntentClassifier's LLM client for compound detection
            # Access the LLM client safely
            llm_client = getattr(self._intent_classifier, "_llm_client", None)
            
            if llm_client and hasattr(llm_client, "classify_intent"):
                try:
                    # Use classify_intent method
                    llm_response = await llm_client.classify_intent(
                        prompt=prompt,
                        model=self._intent_classifier._classification_model,
                    )
                    
                    # Parse response
                    if isinstance(llm_response, dict):
                        is_compound = llm_response.get("is_compound", False)
                        if is_compound:
                            logger.info(
                                "🔀 LLM confirmed compound intent",
                                extra={
                                    "intents": llm_response.get("intents", []),
                                    "reasoning": llm_response.get("reasoning", ""),
                                }
                            )
                            return True
                        
                        # Check reasoning for compound indicators
                        reasoning = llm_response.get("reasoning", "").lower()
                        if any(word in reasoning for word in ["multiple", "compound", "two", "both", "separate"]):
                            logger.info("🔀 LLM reasoning indicates compound intent")
                            return True
                    
                    # LLM didn't confirm compound → Trust LLM (it understands context better)
                    # But if pattern is very clear, still consider it compound
                    if has_compound_pattern and any(clear_indicator in message_lower for clear_indicator in [", and ", " and what ", " and show "]):
                        logger.info("🔀 Pattern-based compound detection (LLM unavailable or unclear)")
                        return True
                    
                    return False
                except Exception as llm_error:
                    logger.warning(f"LLM compound detection call failed: {llm_error}, using pattern-based")
                    # Fall through to pattern-based
            else:
                # LLM client not available or doesn't support classify_intent
                logger.debug("LLM client not available for compound detection, using pattern-based")
            
            # Fallback: use pattern-based detection
            # If pattern is clear (has "and" with query words), consider it compound
            if has_compound_pattern:
                # Check for clear compound patterns (not just "BTC and ETH" in single swap)
                clear_compound_patterns = [
                    " and what ",
                    " and show ",
                    " and tell ",
                    " and make ",
                    " and get ",
                    ", and what ",
                    ", and show ",
                ]
                if any(pattern in message_lower for pattern in clear_compound_patterns):
                    logger.info("🔀 Pattern-based compound detection (clear compound pattern)")
                    return True
                
                # For " and " pattern, be more conservative
                # Only consider compound if it looks like two distinct queries
                if " and " in message_lower:
                    # Check if it's likely two queries (has question words or action verbs)
                    query_indicators = ["what", "how", "show", "tell", "make", "get", "find", "analyze"]
                    parts = message_lower.split(" and ")
                    if len(parts) == 2:
                        part1_has_query = any(indicator in parts[0] for indicator in query_indicators)
                        part2_has_query = any(indicator in parts[1] for indicator in query_indicators)
                        if part1_has_query and part2_has_query:
                            logger.info("🔀 Pattern-based compound detection (two distinct query parts)")
                            return True
            
            return False
                    
        except Exception as e:
            logger.warning(
                f"LLM compound detection failed: {e}, using pattern-based result",
                exc_info=True,
            )
            # Fallback: use pattern-based detection
            return has_compound_pattern
            
            is_compound = result.get("is_compound", False)
            
            if is_compound:
                logger.info(
                    "🔀 Compound intent detected by LLM",
                    extra={
                        "intents": result.get("intents", []),
                        "reasoning": result.get("reasoning", ""),
                    }
                )
            
            return is_compound
            
        except Exception as e:
            logger.warning(
                "⚠️ Compound intent detection failed, using fallback",
                extra={"error": str(e)},
            )
            # Fallback: simple pattern matching
            compound_indicators = [
                " and ",
                ", and ",
                " then ",
                " also ",
                ", then ",
                ", also ",
            ]
            return any(indicator in message.lower() for indicator in compound_indicators)

    def _format_context(self, context: AgentSquadContext) -> str:
        """Format context for prompt."""
        if not context.has_history:
            return "(No previous context)"
        
        recent = context.last_n_messages(3)
        return "\n".join([
            f"- {msg.get('role', 'user')}: {msg.get('content', '')[:100]}"
            for msg in recent
        ])

    def _map_to_chat_intent(self, agent_squad_intent: str) -> ChatIntent:
        """
        Map Agent Squad intent to ChatIntent enum.
        
        Agent Squad uses generic intents like "swap_tokens", "analyze_risk"
        ChatIntent uses specific intents like "SWAP", "RISK_ASSESSMENT"
        """
        # Direct mapping
        mapped = self.INTENT_MAP.get(agent_squad_intent)
        if mapped:
            return mapped
        
        # Try case-insensitive match
        intent_lower = agent_squad_intent.lower()
        for key, value in self.INTENT_MAP.items():
            if key.lower() == intent_lower:
                return value
        
        # Try partial match (e.g., "swap" matches "swap_tokens")
        for key, value in self.INTENT_MAP.items():
            if intent_lower in key.lower() or key.lower() in intent_lower:
                return value
        
        # Default to general conversation
        logger.warning(
            f"Unknown Agent Squad intent: {agent_squad_intent}, defaulting to GENERAL_CONVERSATION"
        )
        return ChatIntent.GENERAL_CONVERSATION

    async def _extract_entities_llm(
        self,
        message: str,
        intent: ChatIntent,
        context: AgentSquadContext,
    ) -> dict:
        """
        Extract entities using LLM.
        
        Entities: protocol names, token symbols, amounts, chains, etc.
        """
        # For now, use simple extraction
        # Can be enhanced with LLM-based extraction if needed
        entities = {}
        
        # Token extraction
        tokens = ["BTC", "ETH", "SOL", "USDC", "USDT", "DAI", "WBTC", "WETH"]
        message_upper = message.upper()
        for token in tokens:
            if token in message_upper:
                entities["token_symbol"] = token
                break
        
        # Protocol extraction
        protocols = ["Aave", "Uniswap", "Curve", "Compound", "Morpho"]
        message_lower = message.lower()
        for protocol in protocols:
            if protocol.lower() in message_lower:
                entities["protocol_name"] = protocol
                break
        
        # Amount extraction
        import re
        amount_match = re.search(r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:k|K)?", message)
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            try:
                amount = float(amount_str)
                if "k" in message.lower() or "K" in message.lower():
                    amount *= 1000
                entities["amount"] = amount
            except ValueError:
                pass
        
        return entities

    def supports_streaming(self) -> bool:
        """Intent detection doesn't support streaming."""
        return False
