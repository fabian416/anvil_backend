"""
Send Guest Message Command.

Handles guest chat messages with:
- Auto-create guest user by IP
- Auto-create conversation if new/archived
- Intent detection and routing
- Registration prompts for restricted actions
- Rate limiting
- Telemetry logging
- Conversational memory (context from previous messages)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from typing import Any
from uuid import UUID

from app.application.chat.services.intent_detector import (
    ChatIntent,
    IntentDetectorService,
)
from app.application.guest.i18n.translations import (
    GUEST_CTA_MESSAGES,
    get_cta_message,
    get_demo_disclaimer,
    get_rate_limit_message,
    get_reason_for_intent,
    get_registration_message,
)
from app.application.guest.handlers.guest_handler_service import GuestHandlerService
from app.domain.guest.entities.guest_conversation import GuestConversation
from app.domain.guest.entities.guest_message import GuestMessage
from app.domain.guest.entities.guest_user import GuestUser
from app.domain.guest.ports.guest_repository import GuestRepository
from app.domain.services.distillation.engine import DistillationEngine
from app.domain.value_objects.distillation import RouteType
from app.domain.ports.chat.intent_detection_port import IntentDetectionResult

# Type hints for Agent Squad (optional dependencies)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.agent_squad.supervisor_coordinator import SupervisorCoordinator
    from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)

# ========================================
# Conversational Memory Configuration
# ========================================

MAX_CONTEXT_MESSAGES = 10  # Number of recent messages to use for context

# Intents that use real handlers (not demo responses)
REAL_HANDLER_INTENTS = {
    # GraphRAG - Protocol Search (demo mode with protocol data)
    ChatIntent.PROTOCOL_SEARCH,
    ChatIntent.RISK_ASSESSMENT,
    ChatIntent.SIMILAR_PROTOCOLS,
    # Hunter AI
    ChatIntent.HUNTER_SENTIMENT,
    ChatIntent.HUNTER_PRICE_PREDICTION,
    ChatIntent.HUNTER_RISK_SIGNALS,
    ChatIntent.HUNTER_TRADING_SIGNALS,
    ChatIntent.HUNTER_PATTERNS,
    ChatIntent.HUNTER_PORTFOLIO,
    # ULTRA
    ChatIntent.ULTRA_ARBITRAGE,
    ChatIntent.ULTRA_FLASH_LOANS,
    ChatIntent.ULTRA_MEV_PROTECTION,
    ChatIntent.ULTRA_AUTO_EXECUTOR,
    # DeFi (with handlers)
    ChatIntent.LENDING,
    ChatIntent.MONEY_MARKET,
    ChatIntent.SWAP,
    ChatIntent.SWAP_MOONPAY,
    ChatIntent.BUY,
    # Agent Squad
    ChatIntent.SPECIALIST_TASK,
    ChatIntent.COMPLEX_WORKFLOW,
}


# ========================================
# Rate Limiting Configuration
# ========================================

# Increased for testing: allows comprehensive test suite execution
# Production: 20/hour, 50/day
# Testing: 5000/hour, 10000/day
RATE_LIMIT_MESSAGES_PER_HOUR = 5000
RATE_LIMIT_MESSAGES_PER_DAY = 10000
MAX_MESSAGE_LENGTH = 500

# ========================================
# Restricted Intents (require registration)
# ========================================

RESTRICTED_INTENTS = {
    ChatIntent.PORTFOLIO,
    ChatIntent.BALANCE,
    ChatIntent.ACTIVITY,
    ChatIntent.RECEIVE,
    ChatIntent.BUY,
    ChatIntent.SEND,
}

# Intents that require confirmation (only restricted when confirmed=true)
EXECUTION_INTENTS = {
    ChatIntent.SWAP,
    ChatIntent.LENDING,  # Deposit action
    ChatIntent.MONEY_MARKET,  # Deposit action
}


@dataclass
class GuestMessageResult:
    """Result from sending a guest message."""

    conversation_id: UUID
    message_id: UUID
    user_message: dict[str, Any]
    agent_message: dict[str, Any]
    routing: dict[str, Any]
    enrichment: dict[str, Any] | None = None
    sources: list[dict[str, Any]] | None = None  # NEW: Source attribution
    registration_required: dict[str, Any] | None = None
    guest_info: dict[str, Any] | None = None
    rate_limited: bool = False


class SendGuestMessage:
    """
    Command to send a guest chat message.

    Flow:
    1. Get or create guest user by IP
    2. Check rate limits
    3. Get or create active conversation
    4. Detect intent
    5. Check if action is restricted
    6. Process message (demo mode)
    7. Save messages
    8. Log telemetry
    9. Return response
    """

    def __init__(
        self,
        guest_repository: GuestRepository,
        intent_detector: IntentDetectorService | None = None,
        handler_service: GuestHandlerService | None = None,
        distillation_engine: DistillationEngine | None = None,
        supervisor_coordinator: Any | None = None,  # SupervisorCoordinator - injected manually
        agent_orchestrator: Any | None = None,  # AgentOrchestrator - injected manually
    ):
        self._guest_repo = guest_repository
        self._intent_detector = intent_detector
        self._handler_service = handler_service or GuestHandlerService()
        self._distillation_engine = distillation_engine
        self._supervisor_coordinator = supervisor_coordinator
        self._agent_orchestrator = agent_orchestrator

    async def execute(
        self,
        ip_address: str,
        content: str,
        language: str = "en",
        user_agent: str | None = None,
        referer: str | None = None,
        fingerprint: str | None = None,
    ) -> GuestMessageResult:
        """Execute guest message command."""

        # Validate language
        if language not in ("en", "es", "pt", "zh"):
            language = "en"

        # Validate message length
        if len(content) > MAX_MESSAGE_LENGTH:
            content = content[:MAX_MESSAGE_LENGTH]

        # 1. Get or create guest user
        guest = await self._get_or_create_guest(ip_address, language, fingerprint)

        # Check if blocked
        if guest.is_blocked:
            return self._blocked_response(guest, language)

        # 2. Check rate limits
        is_rate_limited, messages_remaining = await self._check_rate_limit(guest)
        if is_rate_limited:
            return self._rate_limited_response(guest, language)

        # 3. Get or create active conversation
        conversation = await self._get_or_create_conversation(guest, language)

        # 4. Get conversation history for context (conversational memory)
        context = await self._build_conversation_context(conversation.id)

        # ✨ FAST PATH CHECK (BEFORE CONTINUATION) ✨
        # Simple informational queries should bypass continuation flows and workflow planning
        # Check this FIRST to avoid continuation flow interference
        content_lower = content.lower().strip()
        simple_info_patterns = [
            content_lower.startswith("what is "),
            content_lower.startswith("what are "),
            content_lower.startswith("explain "),
            content_lower.startswith("tell me about "),
            content_lower.startswith("describe "),
        ]
        
        # If it's a simple informational query (and not asking for price), use fast path
        is_simple_info_query = (
            any(simple_info_patterns) and 
            not any([
                "price" in content_lower,
                "cost" in content_lower,
                "how much" in content_lower,
                "current price" in content_lower,
            ])
        )
        
        # 4a. Get continuation state from last message (for multi-step flows)
        # BUT: If it's a simple info query, skip continuation check (will cancel it anyway)
        if not is_simple_info_query:
            continuation_step, previous_swap_info, previous_lending_info, previous_send_info, previous_buy_info = await self._get_continuation_state(
                conversation.id
            )
        else:
            # Fast path: Skip continuation check, clear any existing state
            # Also clear continuation state in database to prevent future interference
            continuation_step = None
            previous_swap_info = None
            previous_lending_info = None
            previous_send_info = None
            previous_buy_info = None
            
            # Clear continuation state in database (if needed)
            # Note: Continuation state is cleared by setting variables to None above
            # Database cleanup can be done in a background task if needed

        # 4b. ✨ EARLY RESTRICTED INTENT CHECK ✨
        # Check if this is a restricted intent BEFORE Agent Squad processing
        # This ensures custom messages from translations.py are used instead of Agent Squad
        # Detect intent early to check if restricted
        early_intent, early_confidence, early_handler = await self._detect_intent_with_context(
            content, context, language, None
        )
        is_restricted_early, reason_early = self._is_restricted_action(early_intent)
        
        # 4b.1. ✨ COMPOUND INTENT DETECTION ✨
        # Check if user wants to cancel current flow and start a new query
        # Example: "cancel, tell me the price of btc" while in a swap flow
        if continuation_step:
            from app.application.chat.services.flow_cancellation_detector import FlowCancellationDetector

            detector = FlowCancellationDetector()

            # Check for explicit cancellation keywords (cancel, stop, abort, etc.)
            # These keywords indicate user wants to exit current flow
            cancellation_keywords = {
                "en": ["cancel", "stop", "abort", "forget it", "never mind", "quit"],
                "es": ["cancelar", "parar", "abortar", "olvidalo", "déjalo"],
                "pt": ["cancelar", "parar", "abortar", "esquecer"],
                "zh": ["取消", "停止", "放弃"],
            }

            keywords_for_lang = cancellation_keywords.get(language, cancellation_keywords["en"])
            content_lower = content.lower().strip()

            matched_keyword = None
            for keyword in keywords_for_lang:
                if keyword in content_lower:
                    matched_keyword = keyword
                    break

            if matched_keyword:
                # Extract content after cancellation keyword
                remaining_content = FlowCancellationDetector.extract_post_cancellation_content(
                    content,
                    matched_keyword,
                    language,
                )

                if remaining_content:
                    # Compound intent detected: "cancel, [new query]"
                    logger.info(
                        "🔄 Compound intent detected - cancelling flow and processing new query",
                        extra={
                            "ip_address": ip_address,
                            "conversation_id": str(conversation.id),
                            "original_content": content[:100],
                            "extracted_content": remaining_content[:100],
                            "cancelled_flow": continuation_step,
                            "keyword": matched_keyword,
                        }
                    )

                    # Clear the flow state
                    continuation_step = None
                    previous_swap_info = None
                    previous_lending_info = None
                    previous_send_info = None
                    previous_buy_info = None

                    # Update content to just the extracted query
                    content = remaining_content

                    logger.info(
                        "🔄 Flow cancelled - detecting intent for new query",
                        extra={
                            "new_content": content[:100],
                        }
                    )
                else:
                    # Just cancellation, no new query
                    logger.info(
                        "🔄 Flow cancelled by user",
                        extra={
                            "ip_address": ip_address,
                            "conversation_id": str(conversation.id),
                            "cancelled_flow": continuation_step,
                            "keyword": matched_keyword,
                        }
                    )

                    # Clear the flow state
                    continuation_step = None
                    previous_swap_info = None
                    previous_lending_info = None
                    previous_send_info = None
                    previous_buy_info = None

        # 4c. ✨ AGENT SQUAD SUPERVISOR (PRIMARY HANDLER FOR ALL QUERIES) ✨
        # SupervisorCoordinator handles ALL routing responsibilities:
        # - Price queries → Hunter AI agent (via market_sentiment intent)
        # - Anvil knowledge → Chat agent (via general_chat intent with knowledge base)
        # - General questions → Chat agent (via general_chat intent)
        # - Shortcuts → Multi-step workflows (via appropriate intents: swap_tokens, lending, etc.)
        # - Multi-step operations → SupervisorCoordinator workflows
        # 
        # No manual pattern matching needed - fully LLM-based and context-aware
        # BUT: Skip Agent Squad for restricted intents (handled with custom messages in step 8)
        
        supervisor_coordinator = self._supervisor_coordinator
        
        # Verify it's actually a SupervisorCoordinator instance
        # Note: is_simple_info_query is already calculated above (before continuation check)
        # Skip Agent Squad for restricted intents - use custom registration messages instead
        # (is_restricted will be checked in step 6, but we check here to skip Agent Squad early)
        if supervisor_coordinator and hasattr(supervisor_coordinator, "create_workflow_plan") and not continuation_step:
            try:
                # ✨ FAST PATH: Simple informational queries go directly to Chat agent (no workflow planning) ✨
                if is_simple_info_query:
                    logger.info(
                        "⚡ Fast path: Simple informational query → Chat agent (bypassing workflow planning)",
                        extra={
                            "ip_address": ip_address,
                            "conversation_id": str(conversation.id),
                            "query_text": content[:100],
                        }
                    )
                    
                    # Execute Chat agent directly (fast path)
                    from app.domain.value_objects.conversation_id import ConversationId
                    from app.domain.value_objects.message_content import MessageContent
                    from app.domain.value_objects.agent_squad.conversation_context import (
                        ConversationContext as AgentSquadContext,
                    )
                    from app.domain.enums.agent_type import AgentType
                    from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator
                    
                    # Build minimal context
                    messages = await self._guest_repo.get_messages(conversation.id, limit=5)
                    conversation_history = [
                        {
                            "role": msg.role.value,
                            "content": msg.content,
                            "timestamp": msg.created_at.isoformat() if hasattr(msg.created_at, "isoformat") else str(msg.created_at),
                        }
                        for msg in messages
                    ]
                    conversation_history.append({
                        "role": "user",
                        "content": content,
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                    
                    agent_squad_context = AgentSquadContext(
                        conversation_history=conversation_history,
                        user_metadata={"language": language, "is_guest": True},
                        session_metadata={"ip_address": ip_address},
                    )
                    
                    # Execute Chat agent directly via orchestrator
                    if not self._agent_orchestrator:
                        logger.warning("Agent orchestrator not available, falling back to SupervisorCoordinator")
                        # Fall through to SupervisorCoordinator path below
                    else:
                        try:
                            import time
                            fast_path_start_time = time.time()
                            
                            response = await self._agent_orchestrator.execute_agent(
                                agent_type=AgentType.CHAT,
                                message=content,
                                conversation_context=agent_squad_context,
                            )
                            
                            # Calculate execution time (after agent execution completes)
                            fast_path_execution_time_ms = int((time.time() - fast_path_start_time) * 1000)
                            
                            # Create user message
                            user_message = GuestMessage.create_user_message(
                                conversation_id=conversation.id,
                                content=content,
                                language=language,
                            )
                            await self._guest_repo.create_message(user_message)
                            
                            # Create agent message
                            agent_message = GuestMessage.create_assistant_message(
                                conversation_id=conversation.id,
                                content=response.content if hasattr(response, "content") else str(response),
                                intent="COMPLEX_WORKFLOW",
                                handler="agent_squad_chat_fast",
                                confidence=0.95,
                                language=language,
                                is_restricted_action=False,
                            )
                            await self._guest_repo.create_message(agent_message)
                            
                            # Update counters
                            guest.increment_messages()
                            conversation.increment_messages()
                            await self._guest_repo.update_guest(guest)
                            await self._guest_repo.update_conversation(conversation)
                            
                            # Get sources from response
                            sources = []
                            if hasattr(response, "sources") and response.sources:
                                sources = [s.to_dict() for s in response.sources]
                            
                            # Check if debug timing is enabled
                            from app.setup.config.settings import load_settings
                            settings = load_settings()
                            debug_timing_enabled = getattr(settings.agent_squad, 'debug_agent_timing', False)
                            
                            # Build enrichment with optional timing
                            enrichment = {
                                "agent_squad": True,
                                "workflow_type": "fast_path",
                                "task_count": 1,
                                "disclaimer": get_demo_disclaimer(language),
                                "agents_used": ["chat"],
                            }
                            
                            # Add timing if debug enabled
                            if debug_timing_enabled:
                                # Get provider info from response metadata if available
                                provider_info = None
                                if hasattr(response, 'metadata') and isinstance(response.metadata, dict):
                                    provider_info = response.metadata.get('provider')
                                # Fallback: check if response has provider attribute directly
                                if not provider_info and hasattr(response, 'provider'):
                                    provider_info = response.provider
                                
                                enrichment["agent_timings"] = [{
                                    "agent_type": "chat",
                                    "task_description": "Fast path execution",
                                    "execution_time_ms": fast_path_execution_time_ms,
                                    "status": "completed",
                                    "provider": provider_info,  # Include LLM provider for debugging
                                }]
                            
                            # Calculate remaining messages
                            hour_ago = datetime.now(UTC) - timedelta(hours=1)
                            messages_this_hour = await self._guest_repo.get_message_count_since(
                                guest.id, hour_ago
                            )
                            messages_remaining = max(0, RATE_LIMIT_MESSAGES_PER_HOUR - messages_this_hour)
                            
                            return GuestMessageResult(
                                conversation_id=conversation.id,
                                message_id=agent_message.id,
                                user_message={
                                    "id": str(user_message.id),
                                    "role": user_message.role.value,
                                    "content": user_message.content,
                                    "created_at": user_message.created_at.isoformat(),
                                },
                                agent_message={
                                    "id": str(agent_message.id),
                                    "role": agent_message.role.value,
                                    "content": response.content if hasattr(response, "content") else str(response),
                                    "created_at": agent_message.created_at.isoformat(),
                                    "sources": sources,
                                },
                                routing={
                                    "intent": "COMPLEX_WORKFLOW",
                                    "confidence": 0.95,
                                    "handler": "agent_squad_chat_fast",
                                    "language": language,
                                    "is_demo_mode": False,
                                    "is_live_data": False,
                                },
                                enrichment=enrichment,
                                sources=sources if sources else None,
                                registration_required=None,
                                guest_info={
                                    "messages_remaining": messages_remaining,
                                    "session_active": True,
                                },
                            )
                        except Exception as e:
                            logger.error(f"Fast path execution failed: {e}, falling back to SupervisorCoordinator", exc_info=True)
                            # Fall through to SupervisorCoordinator path below
                
                # Standard path: Use SupervisorCoordinator for complex queries
                logger.info(
                    "🎭 Routing to Agent Squad Supervisor (primary handler)",
                    extra={
                        "ip_address": ip_address,
                        "conversation_id": str(conversation.id),
                        "query_text": content[:100],  # Changed from "message" to avoid LogRecord conflict
                    }
                )
                
                agent_squad_result = await self._handle_with_agent_squad(
                    content=content,
                    language=language,
                    conversation=conversation,
                    guest=guest,
                    context=context,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    referer=referer,
                )
                
                if agent_squad_result is not None:
                    logger.info(
                        "✅ Agent Squad Supervisor handled query successfully",
                        extra={"conversation_id": str(conversation.id)}
                    )
                    return agent_squad_result
                else:
                    logger.info(
                        "⚠️ Agent Squad Supervisor returned None, falling back to normal flow",
                        extra={"conversation_id": str(conversation.id)}
                    )
            except Exception as e:
                logger.warning(
                    f"Agent Squad Supervisor failed: {e}, falling back to normal flow",
                    exc_info=True,
                    extra={
                        "ip_address": ip_address,
                        "conversation_id": str(conversation.id),
                    }
                )

        # 4e. ✨ DISTILLATION CHECK ✨
        # Check if distillation can handle this query (educational questions, static responses)
        distillation_result = None
        if self._distillation_engine and not continuation_step:
            try:
                distillation_result = await self._distillation_engine.distill(
                    query=content,
                    user_id=None,  # Guest users don't have UUID
                    user_context={"language": language},
                )
                
                # If distillation routed to STATIC response, use it directly
                if (
                    distillation_result.route_type == RouteType.STATIC
                    and distillation_result.static_response
                ):
                    logger.info(
                        "✨ Distillation static response used",
                        extra={
                            "ip_address": ip_address,
                            "conversation_id": str(conversation.id),
                            "intent": distillation_result.intent.value,
                            "route_type": distillation_result.route_type.value,
                        }
                    )
                    
                    # Create user message
                    user_message = GuestMessage.create_user_message(
                        conversation_id=conversation.id,
                        content=content,
                        language=language,
                    )
                    await self._guest_repo.create_message(user_message)
                    
                    # Create agent message with static response
                    agent_message = GuestMessage.create_assistant_message(
                        conversation_id=conversation.id,
                        content=distillation_result.static_response,
                        intent=distillation_result.intent.value,
                        handler="distillation_static",
                        confidence=distillation_result.classification_confidence or 0.95,
                        language=language,
                        is_restricted_action=False,
                    )
                    await self._guest_repo.create_message(agent_message)
                    
                    # Update counters
                    guest.increment_messages()
                    conversation.increment_messages()
                    await self._guest_repo.update_guest(guest)
                    await self._guest_repo.update_conversation(conversation)
                    
                    # Log telemetry
                    await self._guest_repo.log_telemetry(
                        guest_user_id=guest.id,
                        conversation_id=conversation.id,
                        event_type="message_sent",
                        event_data={
                            "intent": distillation_result.intent.value,
                            "handler": "distillation_static",
                            "route_type": distillation_result.route_type.value,
                            "message_length": len(content),
                        },
                        ip_address=ip_address,
                        user_agent=user_agent,
                        referer=referer,
                        language=language,
                    )
                    
                    # Calculate remaining messages
                    hour_ago = datetime.now(UTC) - timedelta(hours=1)
                    messages_this_hour = await self._guest_repo.get_message_count_since(
                        guest.id, hour_ago
                    )
                    messages_remaining = max(0, RATE_LIMIT_MESSAGES_PER_HOUR - messages_this_hour)
                    
                    return GuestMessageResult(
                        conversation_id=conversation.id,
                        message_id=agent_message.id,
                        user_message={
                            "id": str(user_message.id),
                            "role": user_message.role.value,
                            "content": user_message.content,
                            "created_at": user_message.created_at.isoformat(),
                        },
                        agent_message={
                            "id": str(agent_message.id),
                            "role": agent_message.role.value,
                            "content": agent_message.content,
                            "created_at": agent_message.created_at.isoformat(),
                        },
                        routing={
                            "intent": distillation_result.intent.value,
                            "confidence": distillation_result.classification_confidence or 0.95,
                            "handler": "distillation_static",
                            "language": language,
                            "is_demo_mode": False,
                            "is_live_data": False,
                            "distillation_route": distillation_result.route_type.value,
                        },
                        enrichment={"disclaimer": get_demo_disclaimer(language)},
                        sources=None,
                        registration_required=None,
                        guest_info={
                            "messages_remaining": messages_remaining,
                            "session_active": True,
                        },
                    )
            except Exception as e:
                # If distillation fails, continue with normal flow
                logger.warning(
                    f"Distillation check failed, continuing with normal flow: {e}",
                    extra={
                        "ip_address": ip_address,
                        "conversation_id": str(conversation.id),
                        "error": str(e),
                    }
                )
                distillation_result = None

        # 5. Detect intent with context
        # If we have a continuation_step, we're in the middle of a multi-step flow
        # Use the intent from that flow instead of detecting a new one
        if continuation_step:
            # Determine intent from continuation step
            if "swap" in continuation_step:
                intent = ChatIntent.SWAP_MOONPAY
                handler = "moonpay_swap"
                confidence = 1.0
                logger.info(f"[Continuation] Using swap intent from pending action: {continuation_step}")
            elif "lending" in continuation_step:
                intent = ChatIntent.LENDING
                handler = "lending"
                confidence = 1.0
                logger.info(f"[Continuation] Using lending intent from pending action: {continuation_step}")
            elif "buy" in continuation_step:
                intent = ChatIntent.BUY
                handler = "buy"
                confidence = 1.0
                logger.info(f"[Continuation] Using buy intent from pending action: {continuation_step}")
            else:
                # Unknown continuation step, fall back to intent detection
                intent, confidence, handler = await self._detect_intent_with_context(
                    content, context, language, None
                )
        else:
            # No continuation, detect intent normally
            # Detect intent using context-based detection
            intent, confidence, handler = await self._detect_intent_with_context(
                content, context, language, None
            )

        # 6. Check if restricted
        is_restricted, reason = self._is_restricted_action(intent)

        # 7. Create user message
        user_message = GuestMessage.create_user_message(
            conversation_id=conversation.id,
            content=content,
            language=language,
        )
        await self._guest_repo.create_message(user_message)

        # 8. Generate response
        handler_result = None  # Initialize to avoid UnboundLocalError
        if is_restricted:
            agent_content = self._build_registration_response(reason, language)
            agent_message = GuestMessage.create_assistant_message(
                conversation_id=conversation.id,
                content=agent_content,
                intent=intent.value if intent else None,
                handler=handler,
                confidence=confidence,
                language=language,
                is_restricted_action=True,
            )
            registration_required = self._build_registration_required(reason, language)
            enrichment = None
        elif intent in REAL_HANDLER_INTENTS:
            # Use real handlers for Hunter AI, ULTRA, and DeFi intents
            # Pass context for conversational memory and continuation state for multi-step flows
            handler_result = await self._handler_service.handle_intent(
                intent,
                content,
                language,
                context=context,
                continuation_step=continuation_step,
                previous_swap_info=previous_swap_info,
                previous_lending_info=previous_lending_info,
                previous_send_info=previous_send_info,
                previous_buy_info=previous_buy_info,
            )
            agent_content = handler_result.get("content", "")
            enrichment = handler_result.get("enrichment")

            # Check if handler requires registration for action
            if handler_result.get("requires_registration"):
                registration_required = {
                    "required": True,
                    "reason": "action_required",
                    "message": {
                        "en": "Sign up to execute this action.",
                        "es": "Regístrate para ejecutar esta acción.",
                        "pt": "Cadastre-se para executar esta ação.",
                        "zh": "注册以执行此操作。",
                    },
                    "cta": GUEST_CTA_MESSAGES,
                    "signup_url": "/signup",
                }
            else:
                registration_required = None

            # Build metadata for continuation state (multi-step flows)
            message_metadata = {}
            if handler_result.get("pending_action"):
                message_metadata["pending_action"] = handler_result["pending_action"]
            if "swap_info" in handler_result:
                message_metadata["swap_info"] = handler_result["swap_info"]
            if "lending_info" in handler_result:
                message_metadata["lending_info"] = handler_result["lending_info"]
            if "send_info" in handler_result:
                message_metadata["send_info"] = handler_result["send_info"]
            if "buy_info" in handler_result:
                message_metadata["buy_info"] = handler_result["buy_info"]

            agent_message = GuestMessage.create_assistant_message(
                conversation_id=conversation.id,
                content=agent_content,
                intent=intent.value if intent else None,
                handler=handler,
                confidence=confidence,
                language=language,
                is_restricted_action=handler_result.get("requires_registration", False),
                metadata=message_metadata if message_metadata else None,
            )
        else:
            # Fallback to demo response for other intents
            # Note: Informational queries are already handled earlier in the flow
            agent_content = await self._generate_demo_response(
                content, intent, language
            )
            agent_message = GuestMessage.create_assistant_message(
                conversation_id=conversation.id,
                content=agent_content,
                intent=intent.value if intent else None,
                handler=handler,
                confidence=confidence,
                language=language,
                is_restricted_action=False,
            )
            registration_required = None
            enrichment = None

        await self._guest_repo.create_message(agent_message)

        # 8. Update counters
        guest.increment_messages()
        conversation.increment_messages()
        await self._guest_repo.update_guest(guest)
        await self._guest_repo.update_conversation(conversation)

        # 9. Log telemetry
        await self._guest_repo.log_telemetry(
            guest_user_id=guest.id,
            conversation_id=conversation.id,
            event_type="message_sent" if not is_restricted else "registration_prompt",
            event_data={
                "intent": intent.value if intent else None,
                "is_restricted": is_restricted,
                "message_length": len(content),
            },
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            language=language,
        )

        # 10. Calculate remaining messages
        hour_ago = datetime.now(UTC) - timedelta(hours=1)
        messages_this_hour = await self._guest_repo.get_message_count_since(
            guest.id, hour_ago
        )
        messages_remaining = max(0, RATE_LIMIT_MESSAGES_PER_HOUR - messages_this_hour)

        # Build enrichment - use handler enrichment if available, otherwise disclaimer
        final_enrichment = enrichment if enrichment else {}
        final_enrichment["disclaimer"] = get_demo_disclaimer(language)

        # Extract sources from handler result
        sources = []
        if handler_result and "sources" in handler_result:
            sources = handler_result["sources"]

        # Determine if using real handler or demo mode
        is_real_handler = intent in REAL_HANDLER_INTENTS and enrichment is not None

        agent_message_dict = {
            "id": str(agent_message.id),
            "role": agent_message.role.value,
            "content": agent_message.content,
            "created_at": agent_message.created_at.isoformat(),
        }
        
        # Add sources if available
        if sources:
            agent_message_dict["sources"] = sources

        return GuestMessageResult(
            conversation_id=conversation.id,
            message_id=agent_message.id,
            user_message={
                "id": str(user_message.id),
                "role": user_message.role.value,
                "content": user_message.content,
                "created_at": user_message.created_at.isoformat(),
            },
            agent_message=agent_message_dict,
            routing={
                "intent": intent.value if intent else "GENERAL_CONVERSATION",
                "confidence": confidence or 0.5,
                "handler": handler or "demo_handler",
                "language": language,
                "is_demo_mode": not is_real_handler,
                "is_live_data": is_real_handler,
            },
            enrichment=final_enrichment,
            sources=sources,  # NEW: Sources from handler
            registration_required=registration_required,
            guest_info={
                "messages_remaining": messages_remaining,
                "session_active": True,
            },
        )

    async def _get_or_create_guest(
        self,
        ip_address: str,
        language: str,
        fingerprint: str | None,
    ) -> GuestUser:
        """Get existing guest or create new one."""
        guest = await self._guest_repo.get_guest_by_ip(ip_address)

        if guest:
            guest.update_last_seen()
            if language != guest.language:
                guest.language = language
            await self._guest_repo.update_guest(guest)
            return guest

        # Create new guest
        new_guest = GuestUser(
            ip_address=ip_address,
            fingerprint=fingerprint,
            language=language,
        )
        return await self._guest_repo.create_guest(new_guest)

    async def _get_or_create_conversation(
        self,
        guest: GuestUser,
        language: str,
    ) -> GuestConversation:
        """Get active conversation or create new one."""
        conversation = await self._guest_repo.get_active_conversation(guest.id)

        if conversation:
            return conversation

        # Create new conversation
        new_conversation = GuestConversation(
            guest_user_id=guest.id,
            language=language,
        )
        return await self._guest_repo.create_conversation(new_conversation)

    async def _check_rate_limit(self, guest: GuestUser) -> tuple[bool, int]:
        """Check if guest is rate limited."""
        hour_ago = datetime.now(UTC) - timedelta(hours=1)
        messages_this_hour = await self._guest_repo.get_message_count_since(
            guest.id, hour_ago
        )

        if messages_this_hour >= RATE_LIMIT_MESSAGES_PER_HOUR:
            return True, 0

        return False, RATE_LIMIT_MESSAGES_PER_HOUR - messages_this_hour

    # ========================================
    # Conversational Memory
    # ========================================

    async def _build_conversation_context(self, conversation_id: UUID) -> str:
        """
        Build conversation context from recent messages.

        Returns a formatted string of recent messages for use in intent detection
        and response generation.
        """
        try:
            messages = await self._guest_repo.get_messages(
                conversation_id, limit=MAX_CONTEXT_MESSAGES
            )

            if not messages:
                return ""

            context_lines = []
            for msg in messages:
                role = "User" if msg.role.value == "user" else "Assistant"
                # Truncate long messages in context
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                context_lines.append(f"{role}: {content}")

            return "\n".join(context_lines)
        except Exception as e:
            logger.warning(f"Failed to build conversation context: {e}")
            return ""

    async def _get_continuation_state(self, conversation_id: UUID) -> tuple[str | None, dict | None, dict | None, dict | None, dict | None]:
        """
        Get continuation state from the last assistant message.

        Returns:
            (continuation_step, previous_swap_info, previous_lending_info, previous_send_info, previous_buy_info)
        """
        try:
            # Get recent messages (ordered newest to oldest - DESC)
            # We need the MOST RECENT message, so take the first one
            messages = await self._guest_repo.get_messages(conversation_id, limit=10)

            if not messages:
                return None, None, None, None, None

            # Get the most recent assistant message (first in DESC order)
            last_assistant_message = None
            for msg in messages:  # No need to reverse - already in DESC order
                if msg.role.value == "assistant":
                    last_assistant_message = msg
                    break

            if not last_assistant_message:
                return None, None, None, None, None

            metadata = last_assistant_message.metadata or {}

            continuation_step = metadata.get("pending_action")
            previous_swap_info = metadata.get("swap_info")
            previous_lending_info = metadata.get("lending_info")
            previous_send_info = metadata.get("send_info")
            previous_buy_info = metadata.get("buy_info")

            logger.info(f"[Continuation] Found state: step={continuation_step}, swap_info={previous_swap_info}, send_info={previous_send_info}, buy_info={previous_buy_info}")
            return continuation_step, previous_swap_info, previous_lending_info, previous_send_info, previous_buy_info
        except Exception as e:
            logger.warning(f"Failed to get continuation state: {e}")
            return None, None, None, None, None

    async def _detect_intent_with_context(
        self, content: str, context: str, language: str, intent_result: "IntentDetectionResult | None" = None
    ) -> tuple[ChatIntent | None, float | None, str | None]:
        """
        Detect intent from message content with conversational context.
        
        Uses context to:
        1. Resolve follow-up references (e.g., "And what about Bitcoin?")
        2. Complete partial commands (e.g., "de USDC" after "quiero swap")
        3. Maintain topic continuity
        """
        # If context exists, check for follow-up patterns FIRST (before external detector)
        # This ensures follow-ups are detected even if external detector returns general_conversation
        if context:
            context_lower = context.lower()
            content_lower = content.lower()
            
            # Detect follow-up patterns
            follow_up_patterns = [
                "and what about", "what about", "how about", "and for",
                "y qué hay de", "qué tal", "y para", "y sobre",  # Spanish
            ]
            
            for pattern in follow_up_patterns:
                if pattern in content_lower:
                    # Check if previous context was about price/sentiment
                    if any(kw in context_lower for kw in ["price", "precio", "sentiment", "sentimiento"]):
                        # Extract token and return same intent type
                        if any(kw in context_lower for kw in ["sentiment", "sentimiento"]):
                            logger.info(f"Detected sentiment follow-up: {content}")
                            return ChatIntent.HUNTER_SENTIMENT, 0.90, "hunter_sentiment_handler"
                        if any(kw in context_lower for kw in ["price", "precio", "prediction", "predecir"]):
                            logger.info(f"Detected price prediction follow-up: {content}")
                            return ChatIntent.HUNTER_PRICE_PREDICTION, 0.90, "hunter_prediction_handler"
        
        # Try external intent detector (but follow-ups already handled above)
        # Reuse intent_result if already detected (from compound intent check)
        if intent_result:
            handler = self._get_handler_for_intent(intent_result.intent)
            return intent_result.intent, intent_result.confidence, handler
        
        if self._intent_detector:
            try:
                result = await self._intent_detector.detect_intent(content)
                # If external detector returns general_conversation but we have context with sentiment/price,
                # prefer the context-based detection
                if result.intent == ChatIntent.GENERAL_CONVERSATION and context:
                    context_lower = context.lower()
                    content_lower = content.lower()
                    
                    # Check for follow-up patterns
                    follow_up_patterns = [
                        "and what about", "what about", "how about", "and for",
                        "y qué hay de", "qué tal", "y para", "y sobre",
                    ]
                    
                    is_follow_up = any(pattern in content_lower for pattern in follow_up_patterns)
                    
                    if is_follow_up:
                        if any(kw in context_lower for kw in ["sentiment", "sentimiento"]):
                            logger.info(f"Overriding general_conversation with sentiment follow-up: {content}")
                            return ChatIntent.HUNTER_SENTIMENT, 0.90, "hunter_sentiment_handler"
                        if any(kw in context_lower for kw in ["price", "precio", "prediction", "predecir"]):
                            logger.info(f"Overriding general_conversation with price prediction follow-up: {content}")
                            return ChatIntent.HUNTER_PRICE_PREDICTION, 0.90, "hunter_prediction_handler"
                
                handler = self._get_handler_for_intent(result.intent)
                return result.intent, result.confidence, handler
            except Exception as e:
                logger.warning(f"Intent detection failed: {e}")

        # Use context-aware keyword detection
        return self._detect_intent_by_keywords_with_context(content, context, language)

    async def _detect_intent(
        self, content: str
    ) -> tuple[ChatIntent | None, float | None, str | None]:
        """Detect intent from message content (legacy method for compatibility)."""
        # Try external intent detector first
        if self._intent_detector:
            try:
                result = await self._intent_detector.detect_intent(content)
                handler = self._get_handler_for_intent(result.intent)
                return result.intent, result.confidence, handler
            except Exception as e:
                logger.warning(f"Intent detection failed: {e}")

        # Fallback to keyword-based detection for guest chat
        return self._detect_intent_by_keywords(content)

    def _detect_intent_by_keywords(
        self, content: str
    ) -> tuple[ChatIntent, float, str]:
        """Simple keyword-based intent detection for guest chat."""
        return self._detect_intent_by_keywords_with_context(content, "", "en")
    
    def _detect_intent_by_keywords_with_context(
        self, content: str, context: str, language: str
    ) -> tuple[ChatIntent, float, str]:
        """
        Context-aware keyword-based intent detection for guest chat.
        
        Supports:
        - English and Spanish keywords
        - Context-based intent resolution for follow-up messages
        - Partial command completion (e.g., "de USDC" after "quiero swap")
        """
        import re

        content_lower = content.lower()
        context_lower = context.lower() if context else ""

        # ========================================
        # Restricted action patterns (check FIRST for guests)
        # ========================================
        restricted_patterns = {
            ChatIntent.BALANCE: [
                # English
                "my balance", "show balance", "check balance", "wallet balance",
                "how much do i have", "my portfolio value", "total value",
                "show my wallet", "what's in my wallet", "my funds",
                "how much money do i have", "what's my balance", "check my balance",
                "show my usdc balance", "my usdc balance", "usdc balance",
                # Spanish
                "mi saldo", "ver saldo", "mostrar saldo", "mi balance",
                "cuánto tengo", "mis fondos", "mi cartera",
                "cuánto dinero tengo", "cuál es mi saldo", "verificar mi saldo",
                "mostrar mi saldo usdc", "mi saldo usdc",
                # Portuguese
                "meu saldo", "ver saldo", "mostrar saldo", "minha carteira",
                "quanto eu tenho", "quanto dinheiro eu tenho", "qual é meu saldo",
                "mostrar meu saldo usdc", "meu saldo usdc",
                # Chinese
                "我的余额", "查看余额", "我的钱包", "我有多少钱", "显示我的USDC余额",
            ],
            ChatIntent.PORTFOLIO: [
                # English
                "my portfolio", "show portfolio", "portfolio performance",
                "my positions", "my investments", "my assets",
                "what tokens do i have", "what tokens do i own", "list my tokens",
                "list my holdings", "show my holdings", "my holdings",
                "what do i own", "what assets do i have", "show my assets",
                "my token holdings", "token portfolio", "all my tokens",
                # Spanish
                "mi portafolio", "ver portafolio", "mis posiciones",
                "mis inversiones", "rendimiento de mi cartera",
                "qué tokens tengo", "qué tokens poseo", "lista mis tokens",
                "lista mis holdings", "mostrar mis holdings", "mis holdings",
                "qué poseo", "qué activos tengo", "mostrar mis activos",
                # Portuguese
                "meu portfólio", "ver portfólio", "minhas posições",
                "quais tokens eu tenho", "quais tokens eu possuo", "listar meus tokens",
                "listar meus holdings", "mostrar meus holdings", "meus holdings",
                "o que eu possuo", "quais ativos eu tenho", "mostrar meus ativos",
                # Chinese
                "我的投资组合", "显示我的投资组合", "我的持仓",
                "我有什么代币", "列出我的代币", "我的资产",
            ],
            ChatIntent.ACTIVITY: [
                # English
                "my activity", "transaction history", "my transactions",
                "my trades", "trade history", "my swaps",
                "recent activity", "activity history", "show activity",
                "what did i do", "what did i do today", "my history",
                # Spanish
                "mi actividad", "historial de transacciones", "mis transacciones",
                "mis intercambios", "historial de trades",
                "actividad reciente", "historial de actividad", "mostrar actividad",
                "qué hice", "qué hice hoy", "mi historial",
                # Portuguese
                "minha atividade", "histórico de transações", "minhas transações",
                "atividade recente", "histórico de atividade",
                # Chinese
                "我的活动", "交易历史", "最近活动", "活动历史",
            ],
            ChatIntent.RECEIVE: [
                # English
                "receive address", "my address", "deposit address",
                "wallet address", "receive crypto",
                "give me my qr code", "my qr code", "qr code",
                "show qr", "get qr", "qr code address",
                # Spanish
                "dirección de recepción", "mi dirección", "dirección de depósito",
                "recibir cripto", "dame mi código qr", "mi código qr",
                # Portuguese
                "endereço de recebimento", "meu endereço", "receber cripto",
                "me dê meu código qr", "meu código qr",
                # Chinese
                "接收地址", "我的地址", "接收加密货币", "给我二维码", "我的二维码",
            ],
            ChatIntent.BUY: [
                # English
                "buy crypto", "buy bitcoin", "buy eth", "buy ethereum",
                "buy usdc", "buy tokens", "purchase crypto", "purchase bitcoin",
                "buy with card", "buy with fiat", "on-ramp", "onramp",
                "i want to buy", "how to buy", "where to buy",
                # Spanish
                "comprar cripto", "comprar bitcoin", "comprar eth", "comprar ethereum",
                "comprar usdc", "comprar tokens", "quiero comprar",
                "comprar con tarjeta", "cómo comprar", "dónde comprar",
                # Portuguese
                "comprar cripto", "comprar bitcoin", "comprar eth",
                "quero comprar", "como comprar", "onde comprar",
                # Chinese
                "购买加密货币", "购买比特币", "购买以太坊", "我想买",
            ],
            ChatIntent.SEND: [
                # English
                "send crypto", "send bitcoin", "send eth", "send usdc",
                "send tokens", "transfer to", "send to wallet",
                "i want to send", "how to send", "transfer crypto",
                "transfer eth to", "transfer to another wallet", "send to another",
                "transfer to wallet", "send to address",
                # Spanish
                "enviar cripto", "enviar bitcoin", "enviar eth", "enviar usdc",
                "enviar tokens", "transferir a", "enviar a billetera",
                "quiero enviar", "cómo enviar", "transferir cripto",
                "transferir eth a", "transferir a otra billetera",
                # Portuguese
                "enviar cripto", "enviar bitcoin", "enviar eth",
                "quero enviar", "como enviar", "transferir para",
                "transferir eth para", "transferir para outra carteira",
                # Chinese
                "发送加密货币", "发送比特币", "发送以太坊", "我想发送", "转账",
                "转账ETH到", "转账到另一个钱包",
            ],
        }

        # Check restricted patterns first
        for intent, keywords in restricted_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    handler = self._get_handler_for_intent(intent)
                    return intent, 0.95, handler

        # ========================================
        # Context-based follow-up detection
        # ========================================
        # Check if this is a follow-up to a previous intent
        if context_lower:
            # Detect follow-up price queries: "And what about Bitcoin?"
            follow_up_patterns = [
                "and what about", "what about", "how about", "and for",
                "y qué hay de", "qué tal", "y para", "y sobre",  # Spanish
            ]
            for pattern in follow_up_patterns:
                if pattern in content_lower:
                    # Check if previous context was about price/sentiment
                    if any(kw in context_lower for kw in ["price", "precio", "sentiment", "sentimiento"]):
                        # Extract token and return same intent type
                        if any(kw in context_lower for kw in ["sentiment", "sentimiento"]):
                            return ChatIntent.HUNTER_SENTIMENT, 0.85, "hunter_sentiment_handler"
                        return ChatIntent.HUNTER_PRICE_PREDICTION, 0.85, "hunter_prediction_handler"
            
            # Detect multi-turn swap flow: "quiero swap" → "de USDC" → "a ETH" → "100"
            swap_context_keywords = ["swap", "cambiar", "intercambiar", "exchange"]
            if any(kw in context_lower for kw in swap_context_keywords):
                # Enterprise fix: don't treat clear new questions (e.g. price/sentiment)
                # as swap continuation just because they contain common prepositions like "de"
                # (e.g. "precio de bitcoin" includes "de").
                new_intent_breakers = [
                    # Price (ES/EN/PT)
                    "precio", "cuál es el precio", "precio de", "precio actual", "cuánto vale", "cuánto cuesta",
                    "price", "current price", "price of", "how much is", "what is the price", "what's the price",
                    "preço", "qual é o preço", "preço de", "preço atual", "quanto vale", "quanto custa",
                    # Sentiment (ES/EN/PT)
                    "sentimiento", "sentimiento de", "sentimiento del mercado", "alcista", "bajista",
                    "sentiment", "market sentiment", "bullish", "bearish", "mood",
                    "sentimento", "altista", "baixista", "humor",
                    # Risk / protocol search (common question-y breakers)
                    "riesgo", "risk", "protocol", "protocolo", "protocolos",
                ]
                if any(breaker in content_lower for breaker in new_intent_breakers):
                    # Let normal detection below decide the real intent
                    pass
                else:
                # This is a follow-up to a swap request
                    # Only treat as swap continuation if it looks like an explicit swap field answer,
                    # not a generic phrase containing "de"/"a"/"to" somewhere in the middle.
                    token_words = r"(usdc|eth|btc|usdt|dai|weth|wbtc|sol|matic|arb|op)\b"
                    partial_swap_patterns = [
                        rf"^(?:de|from|del)\s+{token_words}",           # Source token
                        rf"^(?:a|to|hacia|por|for)\s+{token_words}",     # Target token
                    ]
                    for pattern in partial_swap_patterns:
                        if re.match(pattern, content_lower, re.IGNORECASE):
                            return ChatIntent.SWAP, 0.90, "swap_handler"
                
                    # Check for amount only (number at start)
                    if content_lower.strip().replace(".", "").replace(",", "").isdigit():
                        return ChatIntent.SWAP, 0.90, "swap_handler"
                
                    # Check for token symbols as standalone message (e.g. "USDC", "ETH")
                    tokens = ["usdc", "eth", "btc", "usdt", "dai", "weth", "wbtc", "sol", "matic", "arb", "op"]
                    if content_lower.strip() in tokens:
                        return ChatIntent.SWAP, 0.90, "swap_handler"

        # ========================================
        # Hunter AI patterns (English + Spanish)
        # ========================================
        hunter_patterns = {
            ChatIntent.HUNTER_SENTIMENT: [
                # English
                "sentiment", "feeling", "mood", "bullish", "bearish",
                "twitter", "reddit", "social", "news", "hype",
                "what do people think", "market mood", "community sentiment",
                # Spanish
                "sentimiento", "opinión", "opiniones", "alcista", "bajista",
                "qué opina", "qué piensan", "clima del mercado", "percepción",
                "sentimiento de mercado", "sentimiento para",
            ],
            ChatIntent.HUNTER_PRICE_PREDICTION: [
                # English
                "predict", "prediction", "forecast", "price target",
                "will go", "where will", "price tomorrow", "future price",
                "price of", "what's the price", "current price", "how much is",
                "what is the price", "price for",
                # Spanish
                "predecir", "predicción", "pronóstico", "objetivo de precio",
                "a dónde irá", "precio de", "cuál es el precio", "precio actual",
                "precio futuro", "va a subir", "va a bajar", "cuánto vale",
                "cuánto cuesta",
            ],
            ChatIntent.HUNTER_RISK_SIGNALS: [
                # English
                "risk signal", "market risk", "whale", "liquidation",
                "danger", "warning", "alert", "crash",
                # Spanish
                "señal de riesgo", "riesgo de mercado", "ballena", "liquidación",
                "peligro", "advertencia", "alerta", "caída",
            ],
            ChatIntent.HUNTER_TRADING_SIGNALS: [
                # English
                "trading signal", "buy signal", "sell signal",
                "should i buy", "should i sell", "entry point", "exit point",
                # Spanish
                "señal de trading", "señal de compra", "señal de venta",
                "debería comprar", "debería vender", "punto de entrada", "punto de salida",
            ],
            ChatIntent.HUNTER_PATTERNS: [
                # English
                "chart pattern", "head and shoulders", "double bottom",
                "flag pattern", "triangle", "breakout", "technical analysis",
                "what patterns", "patterns do you see", "patterns in",
                "see in.*chart", "chart patterns", "pattern recognition",
                "detect pattern", "identify pattern", "find pattern",
                "pattern", "patterns", "chart", "technical pattern",
                # Spanish
                "patrón de gráfico", "hombro cabeza hombro", "doble suelo",
                "patrón de bandera", "triángulo", "ruptura", "análisis técnico",
                "qué patrones", "patrones ves", "patrones en",
                "patrón", "patrones", "gráfico", "patrón técnico",
            ],
            ChatIntent.HUNTER_PORTFOLIO: [
                # English
                "optimize portfolio", "optimize my portfolio", "portfolio allocation",
                "rebalance", "diversify", "risk adjusted", "sharpe ratio",
                "portfolio optimization", "best allocation",
                # Spanish
                "optimizar portafolio", "optimizar mi portafolio", "asignación de portafolio",
                "rebalancear", "diversificar", "ajustado al riesgo",
                "optimización de portafolio", "mejor asignación",
            ],
        }

        # ========================================
        # ULTRA patterns (English + Spanish)
        # ========================================
        ultra_patterns = {
            ChatIntent.ULTRA_ARBITRAGE: [
                # English
                "arbitrage", "arb", "price difference", "spread",
                "profit opportunity", "cross dex",
                # Spanish
                "arbitraje", "diferencia de precio", "oportunidad de ganancia",
            ],
            ChatIntent.ULTRA_FLASH_LOANS: [
                # English
                "flash loan", "flashloan", "flash borrow",
                "instant loan", "uncollateralized",
                # Spanish
                "préstamo flash", "préstamo instantáneo", "sin colateral",
            ],
            ChatIntent.ULTRA_MEV_PROTECTION: [
                # English
                "mev", "front run", "frontrun", "sandwich",
                "flashbots", "private transaction", "protected",
                # Spanish
                "protección mev", "transacción privada", "protegido",
            ],
            ChatIntent.ULTRA_AUTO_EXECUTOR: [
                # English
                "auto execute", "automated trading", "trading bot",
                "dca", "limit order", "stop loss", "auto trade",
                # Spanish
                "ejecución automática", "trading automatizado", "bot de trading",
                "orden límite", "stop loss", "trade automático",
            ],
        }

        # ========================================
        # GraphRAG patterns (check FIRST - exploration queries)
        # ========================================
        graphrag_patterns = {
            ChatIntent.PROTOCOL_SEARCH: [
                # English
                "find protocols", "find defi", "list protocols", "show protocols",
                "search protocols", "discover protocols", "explore protocols",
                "best protocols", "top protocols", "safest protocols",
                "compare protocols", "protocol comparison",
                "protocols on ethereum", "protocols on arbitrum", "protocols on base",
                "protocols on polygon", "protocols on optimism",
                "lending protocols", "dex protocols", "staking protocols",
                "bridge protocols", "yield protocols", "cdp protocols",
                "low risk protocols", "high tvl protocols",
                # Spanish
                "buscar protocolos", "encontrar protocolos", "listar protocolos",
                "mostrar protocolos", "mejores protocolos", "protocolos seguros",
                "comparar protocolos", "protocolos de préstamo", "protocolos de staking",
                "protocolos de bajo riesgo",
            ],
            ChatIntent.RISK_ASSESSMENT: [
                # English
                "is it safe", "how safe", "safe to use",
                "what are the risks", "risks of", "risk assessment",
                "is aave safe", "is uniswap safe", "is compound safe",
                "is morpho safe", "is curve safe", "is lido safe",
                # Spanish
                "es seguro", "es seguro usar", "qué tan seguro",
                "cuáles son los riesgos", "riesgos de", "evaluación de riesgo",
                # Portuguese
                "é seguro", "é seguro usar",
                # Chinese
                "安全吗", "安全使用",
            ],
            ChatIntent.SIMILAR_PROTOCOLS: [
                # English
                "similar to", "like", "alternative to", "alternatives for",
                "protocols like", "similar protocols",
                # Spanish
                "similar a", "parecido a", "alternativa a", "alternativas para",
                "protocolos como", "protocolos similares",
            ],
        }

        # ========================================
        # DeFi shortcut patterns (English + Spanish)
        # ========================================
        defi_patterns = {
            ChatIntent.LENDING: [
                # English
                "deposit usdc", "deposit eth", "earn on morpho",
                "supply to aave", "lend my", "earn yield",
                "lending vault", "lending vaults", "best vault", "best vaults",
                "show vault", "show vaults", "morpho vault", "morpho vaults",
                # Spanish
                "depositar usdc", "depositar eth", "ganar en morpho",
                "prestar en aave", "prestar mi", "ganar rendimiento",
                "bóveda de préstamo", "bóvedas de préstamo", "mejor bóveda", "mejores bóvedas",
            ],
            ChatIntent.MONEY_MARKET: [
                # English
                "money market", "compare aave", "compound vs aave",
                "borrow rate", "lending rate",
                "where should i supply", "where to supply", "where can i supply",
                "best place to supply", "where to deposit", "where should i deposit",
                "supply eth", "supply usdc", "supply dai", "supply usdt",
                "compare rates", "best rates", "best lending rates",
                "aave vs compound", "compound vs aave", "compare aave compound",
                "where supply", "where deposit", "best supply", "best deposit",
                # Spanish
                "mercado de dinero", "comparar aave", "compound vs aave",
                "tasa de préstamo", "tasa de interés",
                "dónde debería depositar", "dónde depositar", "dónde puedo depositar",
                "mejor lugar para depositar", "dónde suministrar", "dónde debería suministrar",
                "suministrar eth", "suministrar usdc", "suministrar dai",
                "comparar tasas", "mejores tasas", "mejores tasas de préstamo",
                "aave vs compound", "compound vs aave", "comparar aave compound",
                # Portuguese
                "onde devo depositar", "onde depositar", "onde posso depositar",
                "melhor lugar para depositar", "onde fornecer", "onde devo fornecer",
                "fornecer eth", "fornecer usdc", "fornecer dai",
                "comparar taxas", "melhores taxas", "melhores taxas de empréstimo",
                # Chinese
                "在哪里供应", "应该在哪里供应", "在哪里存款",
                "最佳供应地点", "比较利率", "最佳利率",
            ],
            ChatIntent.SWAP_MOONPAY: [
                # This pattern should be checked by external detector (keyword_intent_detection_adapter.py)
                # which properly handles: swap_action + 2 MoonPay tokens (btc/eth/sol/usdc) + direction
                # These keywords force explicit MoonPay routing
                "moonpay swap", "swap via moonpay", "via moonpay",
                "moonpay", "moon pay",
                # Spanish
                "intercambio moonpay", "swap cripto a cripto",
                # Portuguese
                "troca moonpay", "trocar cripto por cripto",
                # French
                "échange moonpay", "échanger crypto contre crypto",
                # Chinese
                "moonpay交换", "加密货币互换",
            ],
            ChatIntent.SWAP: [
                # English
                "swap", "exchange", "trade", "convert",
                "1inch", "uniswap", "lifi", "hyperliquid",
                "swap.*for", "swap.*to", "exchange.*for", "exchange.*to",
                "convert.*to", "convert.*for", "trade.*for", "trade.*to",
                "bridge", "bridge.*from", "bridge.*to", "cross.*chain",
                "best swap rate", "best rate", "swap rate", "exchange rate",
                "swap.*usdc.*eth", "swap.*eth.*usdc", "swap.*usdt.*eth",
                "bridge.*ethereum.*base", "bridge.*base.*ethereum",
                "bridge.*arbitrum", "bridge.*optimism", "bridge.*polygon",
                # Spanish
                "cambiar", "intercambiar", "convertir", "canjear",
                "quiero swap", "hacer swap", "swap de",
                "puente", "hacer puente", "cruzar.*cadena",
                "mejor tasa", "tasa de cambio", "cotización",
                # Portuguese
                "trocar", "troca", "converter", "câmbio",
                "ponte", "fazer ponte", "cruzar.*cadeia",
                "melhor taxa", "taxa de câmbio", "cotação",
                # Chinese
                "交换", "兑换", "交易", "桥接",
                "最佳汇率", "汇率", "报价",
            ],
        }

        # Check GraphRAG patterns FIRST (exploration > action)
        for intent, keywords in graphrag_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    handler = self._get_handler_for_intent(intent)
                    return intent, 0.90, handler

        # Check Hunter AI patterns SECOND (market intelligence > actions)
        for intent, keywords in hunter_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    handler = self._get_handler_for_intent(intent)
                    return intent, 0.85, handler

        # Check ULTRA patterns THIRD (DeFi automation)
        for intent, keywords in ultra_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    handler = self._get_handler_for_intent(intent)
                    return intent, 0.80, handler

        # Check DeFi patterns LAST (action intents)
        for intent, keywords in defi_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    handler = self._get_handler_for_intent(intent)
                    return intent, 0.75, handler

        return ChatIntent.GENERAL_CONVERSATION, 0.5, "demo_handler"

    def _get_handler_for_intent(self, intent: ChatIntent) -> str:
        """Get handler name for intent."""
        handler_map = {
            # Hunter AI
            ChatIntent.HUNTER_SENTIMENT: "hunter_sentiment_handler",
            ChatIntent.HUNTER_PRICE_PREDICTION: "hunter_prediction_handler",
            ChatIntent.HUNTER_RISK_SIGNALS: "hunter_risk_handler",
            ChatIntent.HUNTER_TRADING_SIGNALS: "hunter_signals_handler",
            ChatIntent.HUNTER_PATTERNS: "hunter_patterns_handler",
            ChatIntent.HUNTER_PORTFOLIO: "hunter_portfolio_handler",
            # ULTRA
            ChatIntent.ULTRA_ARBITRAGE: "ultra_arbitrage_handler",
            ChatIntent.ULTRA_FLASH_LOANS: "ultra_flashloan_handler",
            ChatIntent.ULTRA_MEV_PROTECTION: "ultra_mev_handler",
            ChatIntent.ULTRA_AUTO_EXECUTOR: "ultra_executor_handler",
            # DeFi
            ChatIntent.LENDING: "lending_handler",
            ChatIntent.MONEY_MARKET: "money_market_handler",
            ChatIntent.SWAP: "swap_handler",
            ChatIntent.SWAP_MOONPAY: "moonpay_swap_handler",
            ChatIntent.PROTOCOL_SEARCH: "graphrag_handler",
            ChatIntent.RISK_ASSESSMENT: "graphrag_handler",
            ChatIntent.SIMILAR_PROTOCOLS: "graphrag_handler",
        }
        return handler_map.get(intent, "demo_handler")

    def _is_restricted_action(
        self, intent: ChatIntent | None
    ) -> tuple[bool, str | None]:
        """
        Check if intent requires registration.
        
        Restricted intents are actions that require a connected wallet:
        - BALANCE: Viewing wallet balance
        - PORTFOLIO: Viewing portfolio positions
        - ACTIVITY: Viewing transaction history
        - RECEIVE: Getting deposit address
        - BUY: Buying crypto with fiat
        - SEND: Sending tokens to another wallet
        """
        if not intent:
            return False, None

        if intent in RESTRICTED_INTENTS:
            # Map intent to specific reason
            reason_map = {
                ChatIntent.BALANCE: "wallet_access",
                ChatIntent.PORTFOLIO: "portfolio_access",
                ChatIntent.ACTIVITY: "transaction_history",
                ChatIntent.RECEIVE: "wallet_address",
                ChatIntent.BUY: "buy_crypto",
                ChatIntent.SEND: "send_crypto",
            }
            reason = reason_map.get(intent, get_reason_for_intent(intent.value))
            return True, reason

        return False, None

    def _build_registration_required(
        self, reason: str, language: str
    ) -> dict[str, Any]:
        """Build registration_required response object."""
        messages = get_registration_message(reason, language)

        return {
            "required": True,
            "reason": reason,
            "message": messages,
            "cta": GUEST_CTA_MESSAGES,
            "signup_url": "/signup",
        }

    def _build_registration_response(self, reason: str, language: str) -> str:
        """Build text response for registration required."""
        messages = get_registration_message(reason, language)
        message = messages.get(language, messages.get("en", ""))
        cta = get_cta_message(language)

        return f"{message}\n\n👉 {cta}: /signup"

    # NOTE: Manual pattern detection methods removed
    # Compound intent detection is now handled by LLM-based AgentSquadIntentAdapter
    # These methods are no longer needed:
    # - _needs_agent_squad() - Replaced by LLM compound intent detection
    # - _detect_sequential_intents() - Replaced by LLM compound intent detection
    # - _classify_part_intent() - Replaced by LLM intent classification

    async def _handle_with_agent_squad(
        self,
        content: str,
        language: str,
        conversation: GuestConversation,
        guest: GuestUser,
        context: list,
        ip_address: str,
        user_agent: str | None = None,
        referer: str | None = None,
    ) -> GuestMessageResult:
        """
        Handle complex query with Agent Squad SupervisorCoordinator.
        
        This method:
        1. Creates a workflow plan using SupervisorCoordinator
        2. Executes the workflow with multiple agents
        3. Aggregates results into a structured response
        4. Saves messages and logs telemetry
        
        Args:
            content: User message content
            language: Language code
            conversation: Guest conversation
            guest: Guest user
            context: Conversation context
            ip_address: User IP address
            user_agent: User agent string
            referer: Referer header
            
        Returns:
            GuestMessageResult with Agent Squad response, or None if should fallback
        """
        if not self._supervisor_coordinator:
            # Fallback to single intent if Agent Squad not available
            logger.warning("Agent Squad not available, falling back to single intent")
            return None  # type: ignore
        
        # Type guard: Ensure it's actually a SupervisorCoordinator
        if not hasattr(self._supervisor_coordinator, "create_workflow_plan"):
            logger.warning(
                "SupervisorCoordinator has wrong type, skipping Agent Squad",
                extra={"type": type(self._supervisor_coordinator).__name__}
            )
            return None
        
        logger.info(
            "🎭 Agent Squad Supervisor: Creating workflow plan",
            extra={
                "conversation_id": str(conversation.id),
                "message_length": len(content),
            }
        )
        
        try:
            from app.domain.value_objects.conversation_id import ConversationId
            from app.domain.value_objects.message_content import MessageContent
            from app.domain.value_objects.agent_squad.conversation_context import (
                ConversationContext as AgentSquadContext,
            )
            from app.domain.enums.agent_type import AgentType
            
            # Guest-accessible agents (read-only, no execution)
            # NOTE: PORTFOLIO is NOT accessible to guests - requires authentication
            GUEST_ACCESSIBLE_AGENTS = [
                AgentType.CHAT,
                AgentType.RESEARCH,
                AgentType.RISK_ANALYZER,
                AgentType.HUNTER_AI,  # Market analysis
                AgentType.DEFI_YIELD,  # Lending rates (read-only)
            ]
            
            # Build Agent Squad conversation context
            # Get actual message objects from repository (context is a string)
            messages = await self._guest_repo.get_messages(
                conversation.id, limit=10
            )
            
            # Build conversation history with current message included
            conversation_history = [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if hasattr(msg.created_at, "isoformat") else str(msg.created_at),
                }
                for msg in messages
            ]
            
            # Add current user message to history for context
            conversation_history.append({
                "role": "user",
                "content": content,
                "timestamp": datetime.now(UTC).isoformat(),
            })
            
            agent_squad_context = AgentSquadContext(
                conversation_history=conversation_history,
                user_metadata={"language": language, "is_guest": True},
                session_metadata={"ip_address": ip_address},
            )
            
            # Create workflow plan
            workflow_plan = await self._supervisor_coordinator.create_workflow_plan(
                conversation_id=ConversationId(conversation.id),
                message=MessageContent(content),
                conversation_context=agent_squad_context,
                available_agents=GUEST_ACCESSIBLE_AGENTS,
            )
            
            logger.info(
                "🎭 Agent Squad workflow plan created",
                extra={
                    "ip_address": ip_address,
                    "conversation_id": str(conversation.id),
                    "task_count": len(workflow_plan.tasks),
                    "estimated_time": workflow_plan.estimated_time_seconds,
                }
            )
            
            # Execute workflow
            aggregated_response, sources, agent_timings = await self._supervisor_coordinator.execute_workflow(
                conversation_id=ConversationId(conversation.id),
                workflow_plan=workflow_plan,
                conversation_context=agent_squad_context,
            )
            
            # Create user message
            user_message = GuestMessage.create_user_message(
                conversation_id=conversation.id,
                content=content,
                language=language,
            )
            await self._guest_repo.create_message(user_message)
            
            # Check if debug timing is enabled
            from app.setup.config.settings import load_settings
            settings = load_settings()
            debug_timing_enabled = getattr(settings.agent_squad, 'debug_agent_timing', False)
            
            # Build enrichment with optional timing
            enrichment = {
                "agent_squad": True,
                "workflow_type": "supervisor_coordinator",
                "task_count": len(workflow_plan.tasks),
                "disclaimer": get_demo_disclaimer(language),
                "agents_used": [task.agent_type.value for task in workflow_plan.tasks],
            }
            
            # Add timing if debug enabled
            if debug_timing_enabled and agent_timings:
                enrichment["agent_timings"] = agent_timings
            
            # Create agent message with aggregated response
            agent_message = GuestMessage.create_assistant_message(
                conversation_id=conversation.id,
                content=aggregated_response,
                intent="COMPLEX_WORKFLOW",
                handler="agent_squad_supervisor",
                confidence=0.95,
                language=language,
                is_restricted_action=False,
            )
            await self._guest_repo.create_message(agent_message)
            
            # Update counters
            guest.increment_messages()
            conversation.increment_messages()
            await self._guest_repo.update_guest(guest)
            await self._guest_repo.update_conversation(conversation)
            
            # Log telemetry
            await self._guest_repo.log_telemetry(
                guest_user_id=guest.id,
                conversation_id=conversation.id,
                event_type="message_sent",
                event_data={
                    "intent": "COMPLEX_WORKFLOW",
                    "handler": "agent_squad_supervisor",
                    "task_count": len(workflow_plan.tasks),
                    "message_length": len(content),
                },
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                language=language,
            )
            
            # Calculate remaining messages
            hour_ago = datetime.now(UTC) - timedelta(hours=1)
            messages_this_hour = await self._guest_repo.get_message_count_since(
                guest.id, hour_ago
            )
            messages_remaining = max(0, RATE_LIMIT_MESSAGES_PER_HOUR - messages_this_hour)
            
            return GuestMessageResult(
                conversation_id=conversation.id,
                message_id=agent_message.id,
                user_message={
                    "id": str(user_message.id),
                    "role": user_message.role.value,
                    "content": user_message.content,
                    "created_at": user_message.created_at.isoformat(),
                },
                agent_message={
                    "id": str(agent_message.id),
                    "role": agent_message.role.value,
                    "content": agent_message.content,
                    "created_at": agent_message.created_at.isoformat(),
                    "sources": sources,  # Include sources from agent execution
                },
                routing={
                    "intent": "COMPLEX_WORKFLOW",
                    "confidence": 0.95,
                    "handler": "agent_squad_supervisor",
                    "language": language,
                    "is_demo_mode": False,
                    "is_live_data": True,
                    "workflow_tasks": len(workflow_plan.tasks),
                },
                enrichment=enrichment,
                sources=None,
                registration_required=None,
                guest_info={
                    "messages_remaining": messages_remaining,
                    "rate_limit": RATE_LIMIT_MESSAGES_PER_HOUR,
                },
                rate_limited=False,
            )
            
        except Exception as e:
            logger.error(
                "❌ Agent Squad workflow execution failed",
                extra={
                    "ip_address": ip_address,
                    "conversation_id": str(conversation.id),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            # Fallback to single intent processing
            # Return None to signal continuation with normal flow
            # The normal flow will handle it as a single intent
            return None  # type: ignore

    def _check_informational_query(self, content: str, language: str) -> str | None:
        """
        Check if query is an informational question and return educational response.
        
        This is a fallback for queries that might have been missed by distillation.
        Handles patterns like "what is btc?", "what is bitcoin?", "whats btc and eth", etc.
        Supports both single and compound queries (multiple tokens).
        
        Args:
            content: User query text
            language: Language code
            
        Returns:
            Educational response if found, None otherwise
        """
        from app.infrastructure.distillation.educational_responses import get_educational_response
        import re
        
        content_lower = content.lower().strip()
        
        # Known tokens for validation
        known_tokens = ["btc", "eth", "usdc", "usdt", "dai", "sol", "bitcoin", "ethereum", "defi", "nft", "dao", "stablecoin", "solana"]
        
        # ✨ COMPOUND QUERY DETECTION ✨
        # Check for multiple tokens in query (e.g., "whats btc and eth", "what is bitcoin and ethereum")
        compound_patterns = [
            r"what(?:'s|s| is) (.+?)(?:\s+and\s+|\s*,\s*|\s+&\s+)(.+?)(?:\?|$)",  # "whats btc and eth", "what is btc and eth"
            r"what(?:'s|s| is) (.+?)\s+(?:and|,|&)\s+(.+?)(?:\?|$)",  # "what is bitcoin and ethereum"
            r"^(.+?)(?:\s+and\s+|\s*,\s*|\s+&\s+)(.+?)(?:\?|$)",  # "btc and eth"
        ]
        
        found_tokens = []
        for pattern in compound_patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                token1 = match.group(1).strip().lower()
                token2 = match.group(2).strip().lower()
                
                # Normalize tokens (remove common words)
                token1 = re.sub(r"^(?:a |an |the )", "", token1)
                token2 = re.sub(r"^(?:a |an |the )", "", token2)
                
                # Check if both are known tokens
                if token1 in known_tokens:
                    found_tokens.append(token1)
                if token2 in known_tokens:
                    found_tokens.append(token2)
                
                if len(found_tokens) >= 2:
                    # Build compound response
                    responses = []
                    for token in found_tokens:
                        response = get_educational_response(token, language)
                        if response:
                            responses.append(response)
                    
                    if len(responses) >= 2:
                        # Combine responses with separator
                        separator = "\n\n---\n\n"
                        combined = separator.join(responses)
                        return combined
        
        # ✨ SINGLE TOKEN QUERIES ✨
        # Patterns for informational queries (single token)
        informational_patterns = {
            "en": [
                r"what is (?:a |an )?(bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
                r"what's (?:a |an )?(bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
                r"explain (?:a |an )?(bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
                r"(?:tell me about|define) (?:a |an )?(bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
            ],
            "es": [
                r"(?:qué es|qué es) (?:un |una )?(bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
                r"(?:cuéntame sobre|explica) (?:un |una )?(bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
            ],
            "pt": [
                r"(?:o que é|o que é) (?:um |uma )?(bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
                r"(?:me conte sobre|explique) (?:um |uma )?(bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
            ],
            "zh": [
                r"什么是(?:一个 )?(bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
                r"(?:告诉我关于|解释)(?:一个 )?(bitcoin|btc|ethereum|eth|usdc|usdt|dai|solana|sol|defi|nft|dao|stablecoin)",
            ],
        }
        
        # Get patterns for language (fallback to English)
        patterns = informational_patterns.get(language, informational_patterns["en"])
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                # Extract the token/term
                token = match.group(1).lower()
                
                # Get educational response
                response = get_educational_response(token, language)
                if response:
                    return response
        
        # Also check for simple "what is X" where X might be a token
        # This catches cases like "what is btc" (without the word "bitcoin")
        simple_pattern = r"what (?:is|'s) (\w+)"
        match = re.search(simple_pattern, content_lower, re.IGNORECASE)
        if match:
            potential_token = match.group(1).lower()
            # Check if it's a known token
            if potential_token in known_tokens:
                response = get_educational_response(potential_token, language)
                if response:
                    return response
        
        return None

    async def _generate_demo_response(
        self,
        content: str,
        intent: ChatIntent | None,
        language: str,
    ) -> str:
        """Generate demo response for allowed intents."""
        # For demo mode, we provide helpful but limited responses
        # In production, this would integrate with the actual handlers

        responses = {
            # ========================================
            # GraphRAG Intents
            # ========================================
            ChatIntent.PROTOCOL_SEARCH: {
                "en": "I can help you find DeFi protocols! In demo mode, try asking about popular protocols like Aave, Uniswap, or Compound. Sign up for full search capabilities.",
                "es": "¡Puedo ayudarte a encontrar protocolos DeFi! En modo demo, pregunta sobre protocolos populares como Aave, Uniswap o Compound. Regístrate para búsquedas completas.",
                "pt": "Posso ajudá-lo a encontrar protocolos DeFi! No modo demo, pergunte sobre protocolos populares como Aave, Uniswap ou Compound. Cadastre-se para pesquisas completas.",
                "zh": "我可以帮您找到 DeFi 协议！在演示模式下，尝试询问 Aave、Uniswap 或 Compound 等热门协议。注册以获得完整搜索功能。",
            },
            ChatIntent.RISK_ASSESSMENT: {
                "en": "Risk assessment is available! I analyze protocol safety, audit history, and TVL trends. Sign up to get detailed risk reports for your positions.",
                "es": "¡La evaluación de riesgos está disponible! Analizo seguridad de protocolos, historial de auditorías y tendencias de TVL. Regístrate para informes detallados.",
                "pt": "Avaliação de risco disponível! Analiso segurança de protocolos, histórico de auditorias e tendências de TVL. Cadastre-se para relatórios detalhados.",
                "zh": "风险评估可用！我分析协议安全性、审计历史和 TVL 趋势。注册以获取详细的风险报告。",
            },
            ChatIntent.SIMILAR_PROTOCOLS: {
                "en": "I can find similar protocols for you! Looking for alternatives to your favorite DeFi apps? Sign up to discover protocols with similar features and better yields.",
                "es": "¡Puedo encontrar protocolos similares! ¿Buscas alternativas a tus apps DeFi favoritas? Regístrate para descubrir protocolos con características similares y mejores rendimientos.",
                "pt": "Posso encontrar protocolos similares! Procurando alternativas aos seus apps DeFi favoritos? Cadastre-se para descobrir protocolos com recursos semelhantes e melhores rendimentos.",
                "zh": "我可以为您找到类似的协议！正在寻找您喜爱的 DeFi 应用的替代品？注册以发现具有类似功能和更高收益的协议。",
            },
            # ========================================
            # DeFi Shortcuts
            # ========================================
            ChatIntent.LENDING: {
                "en": "I can show you the best lending rates! Top Morpho vaults currently offer 5-15% APY on stablecoins. Sign up to deposit and earn.",
                "es": "¡Puedo mostrarte las mejores tasas de préstamo! Las bóvedas top de Morpho ofrecen 5-15% APY en stablecoins. Regístrate para depositar y ganar.",
                "pt": "Posso mostrar as melhores taxas de empréstimo! Os melhores cofres Morpho oferecem 5-15% APY em stablecoins. Cadastre-se para depositar e ganhar.",
                "zh": "我可以向您展示最佳借贷利率！顶级 Morpho 金库目前在稳定币上提供 5-15% APY。注册以存款并赚取收益。",
            },
            ChatIntent.MONEY_MARKET: {
                "en": "Comparing money market rates: Aave offers ~3-5% on USDC, Compound offers ~4-6%. Sign up to deposit and start earning.",
                "es": "Comparando tasas de mercado monetario: Aave ofrece ~3-5% en USDC, Compound ofrece ~4-6%. Regístrate para depositar y ganar.",
                "pt": "Comparando taxas do mercado monetário: Aave oferece ~3-5% em USDC, Compound oferece ~4-6%. Cadastre-se para depositar e começar a ganhar.",
                "zh": "比较货币市场利率：Aave 在 USDC 上提供 ~3-5%，Compound 提供 ~4-6%。注册以存款并开始赚取收益。",
            },
            ChatIntent.SWAP: {
                "en": "I can get swap quotes for you! We aggregate prices from 1inch, LiFi, and more for best rates. Sign up to execute swaps.",
                "es": "¡Puedo obtener cotizaciones de swap! Agregamos precios de 1inch, LiFi y más para las mejores tasas. Regístrate para ejecutar swaps.",
                "pt": "Posso obter cotações de swap! Agregamos preços de 1inch, LiFi e mais para as melhores taxas. Cadastre-se para executar swaps.",
                "zh": "我可以为您获取交换报价！我们汇总来自 1inch、LiFi 等的价格以获得最佳利率。注册以执行交换。",
            },
            # ========================================
            # Hunter AI Intents (Market Intelligence)
            # ========================================
            ChatIntent.HUNTER_SENTIMENT: {
                "en": "🎯 Hunter AI can analyze market sentiment from Twitter, Reddit, Discord, and news sources in real-time! Currently tracking 50+ tokens with sentiment scores. Sign up to get live sentiment alerts and trading signals.",
                "es": "🎯 ¡Hunter AI puede analizar el sentimiento del mercado de Twitter, Reddit, Discord y noticias en tiempo real! Actualmente rastreando 50+ tokens con puntuaciones de sentimiento. Regístrate para recibir alertas de sentimiento en vivo.",
                "pt": "🎯 Hunter AI pode analisar o sentimento do mercado do Twitter, Reddit, Discord e notícias em tempo real! Atualmente rastreando 50+ tokens com pontuações de sentimento. Cadastre-se para receber alertas de sentimento ao vivo.",
                "zh": "🎯 Hunter AI 可以实时分析来自 Twitter、Reddit、Discord 和新闻来源的市场情绪！目前正在跟踪 50+ 代币的情绪评分。注册以获取实时情绪警报。",
            },
            ChatIntent.HUNTER_PRICE_PREDICTION: {
                "en": "📈 Hunter AI uses ML models for price predictions! Our models analyze on-chain data, social sentiment, and technical indicators. Current accuracy: 72% on 24h predictions. Sign up for personalized price forecasts.",
                "es": "📈 ¡Hunter AI usa modelos ML para predicciones de precios! Nuestros modelos analizan datos on-chain, sentimiento social e indicadores técnicos. Precisión actual: 72% en predicciones de 24h. Regístrate para pronósticos personalizados.",
                "pt": "📈 Hunter AI usa modelos ML para previsões de preços! Nossos modelos analisam dados on-chain, sentimento social e indicadores técnicos. Precisão atual: 72% em previsões de 24h. Cadastre-se para previsões personalizadas.",
                "zh": "📈 Hunter AI 使用 ML 模型进行价格预测！我们的模型分析链上数据、社交情绪和技术指标。当前准确率：24 小时预测 72%。注册以获取个性化价格预测。",
            },
            ChatIntent.HUNTER_RISK_SIGNALS: {
                "en": "⚠️ Hunter AI monitors market risk signals 24/7! We track whale movements, liquidation risks, and anomaly detection. Current market risk level: MODERATE. Sign up for real-time risk alerts.",
                "es": "⚠️ ¡Hunter AI monitorea señales de riesgo del mercado 24/7! Rastreamos movimientos de ballenas, riesgos de liquidación y detección de anomalías. Nivel de riesgo actual: MODERADO. Regístrate para alertas de riesgo en tiempo real.",
                "pt": "⚠️ Hunter AI monitora sinais de risco do mercado 24/7! Rastreamos movimentos de baleias, riscos de liquidação e detecção de anomalias. Nível de risco atual: MODERADO. Cadastre-se para alertas de risco em tempo real.",
                "zh": "⚠️ Hunter AI 全天候监控市场风险信号！我们跟踪鲸鱼动向、清算风险和异常检测。当前市场风险级别：中等。注册以获取实时风险警报。",
            },
            ChatIntent.HUNTER_TRADING_SIGNALS: {
                "en": "💹 Hunter AI generates trading signals based on technical analysis and AI! Recent signals: BTC bullish divergence, ETH support at $3,200. Win rate: 68%. Sign up to receive personalized trading signals.",
                "es": "💹 ¡Hunter AI genera señales de trading basadas en análisis técnico e IA! Señales recientes: divergencia alcista BTC, soporte ETH en $3,200. Tasa de éxito: 68%. Regístrate para recibir señales personalizadas.",
                "pt": "💹 Hunter AI gera sinais de trading baseados em análise técnica e IA! Sinais recentes: divergência de alta BTC, suporte ETH em $3.200. Taxa de sucesso: 68%. Cadastre-se para receber sinais personalizados.",
                "zh": "💹 Hunter AI 基于技术分析和 AI 生成交易信号！最近信号：BTC 看涨背离，ETH 支撑位 $3,200。胜率：68%。注册以接收个性化交易信号。",
            },
            ChatIntent.HUNTER_PATTERNS: {
                "en": "📊 Hunter AI detects chart patterns automatically! Currently tracking: head & shoulders, double bottoms, flag patterns across 100+ pairs. Sign up to get pattern alerts before breakouts.",
                "es": "📊 ¡Hunter AI detecta patrones de gráficos automáticamente! Actualmente rastreando: hombro-cabeza-hombro, doble suelo, banderas en 100+ pares. Regístrate para recibir alertas de patrones antes de los breakouts.",
                "pt": "📊 Hunter AI detecta padrões de gráficos automaticamente! Atualmente rastreando: ombro-cabeça-ombro, fundo duplo, bandeiras em 100+ pares. Cadastre-se para receber alertas de padrões antes dos rompimentos.",
                "zh": "📊 Hunter AI 自动检测图表模式！目前正在跟踪：头肩顶、双底、旗形模式，涵盖 100+ 交易对。注册以在突破前获取模式警报。",
            },
            ChatIntent.HUNTER_PORTFOLIO: {
                "en": "💼 Hunter AI optimizes portfolios using Modern Portfolio Theory! We analyze risk-adjusted returns and suggest optimal allocations. Sign up to get AI-powered portfolio recommendations.",
                "es": "💼 ¡Hunter AI optimiza portfolios usando la Teoría Moderna de Portafolios! Analizamos retornos ajustados por riesgo y sugerimos asignaciones óptimas. Regístrate para recomendaciones de portfolio con IA.",
                "pt": "💼 Hunter AI otimiza portfólios usando a Teoria Moderna de Portfólios! Analisamos retornos ajustados ao risco e sugerimos alocações ótimas. Cadastre-se para recomendações de portfólio com IA.",
                "zh": "💼 Hunter AI 使用现代投资组合理论优化投资组合！我们分析风险调整后的回报并建议最佳配置。注册以获取 AI 驱动的投资组合建议。",
            },
            # ========================================
            # ULTRA Intents (DeFi Automation & MEV)
            # ========================================
            ChatIntent.ULTRA_ARBITRAGE: {
                "en": "🔄 ULTRA detects arbitrage opportunities across DEXs in real-time! Current opportunities: 0.3% ETH/USDC spread between Uniswap and Curve. Sign up to execute arbitrage trades automatically.",
                "es": "🔄 ¡ULTRA detecta oportunidades de arbitraje entre DEXs en tiempo real! Oportunidades actuales: 0.3% spread ETH/USDC entre Uniswap y Curve. Regístrate para ejecutar trades de arbitraje automáticamente.",
                "pt": "🔄 ULTRA detecta oportunidades de arbitragem entre DEXs em tempo real! Oportunidades atuais: 0.3% spread ETH/USDC entre Uniswap e Curve. Cadastre-se para executar trades de arbitragem automaticamente.",
                "zh": "🔄 ULTRA 实时检测跨 DEX 套利机会！当前机会：Uniswap 和 Curve 之间 ETH/USDC 价差 0.3%。注册以自动执行套利交易。",
            },
            ChatIntent.ULTRA_FLASH_LOANS: {
                "en": "⚡ ULTRA supports flash loans from Aave, dYdX, and Balancer! Execute complex DeFi strategies with zero upfront capital. Sign up to access flash loan protocols and strategy builder.",
                "es": "⚡ ¡ULTRA soporta flash loans de Aave, dYdX y Balancer! Ejecuta estrategias DeFi complejas sin capital inicial. Regístrate para acceder a protocolos de flash loan y constructor de estrategias.",
                "pt": "⚡ ULTRA suporta flash loans de Aave, dYdX e Balancer! Execute estratégias DeFi complexas sem capital inicial. Cadastre-se para acessar protocolos de flash loan e construtor de estratégias.",
                "zh": "⚡ ULTRA 支持来自 Aave、dYdX 和 Balancer 的闪电贷！无需前期资金即可执行复杂的 DeFi 策略。注册以访问闪电贷协议和策略构建器。",
            },
            ChatIntent.ULTRA_MEV_PROTECTION: {
                "en": "🛡️ ULTRA provides MEV protection via Flashbots! Protect your trades from sandwich attacks and front-running. Your transactions are routed through private mempools. Sign up for MEV-protected execution.",
                "es": "🛡️ ¡ULTRA proporciona protección MEV vía Flashbots! Protege tus trades de ataques sandwich y front-running. Tus transacciones se enrutan por mempools privados. Regístrate para ejecución protegida de MEV.",
                "pt": "🛡️ ULTRA fornece proteção MEV via Flashbots! Proteja seus trades de ataques sandwich e front-running. Suas transações são roteadas por mempools privados. Cadastre-se para execução protegida de MEV.",
                "zh": "🛡️ ULTRA 通过 Flashbots 提供 MEV 保护！保护您的交易免受三明治攻击和抢跑。您的交易通过私有内存池路由。注册以获得 MEV 保护执行。",
            },
            ChatIntent.ULTRA_AUTO_EXECUTOR: {
                "en": "🤖 ULTRA Auto-Executor runs your trading strategies 24/7! Set up DCA, limit orders, stop-losses, and conditional trades. Currently executing 1,000+ strategies for users. Sign up to automate your trading.",
                "es": "🤖 ¡ULTRA Auto-Executor ejecuta tus estrategias de trading 24/7! Configura DCA, órdenes límite, stop-losses y trades condicionales. Actualmente ejecutando 1,000+ estrategias. Regístrate para automatizar tu trading.",
                "pt": "🤖 ULTRA Auto-Executor executa suas estratégias de trading 24/7! Configure DCA, ordens limite, stop-losses e trades condicionais. Atualmente executando 1.000+ estratégias. Cadastre-se para automatizar seu trading.",
                "zh": "🤖 ULTRA Auto-Executor 全天候运行您的交易策略！设置 DCA、限价单、止损和条件交易。目前正在为用户执行 1,000+ 策略。注册以自动化您的交易。",
            },
            # ========================================
            # General Conversation (Fallback)
            # ========================================
            ChatIntent.GENERAL_CONVERSATION: {
                "en": "I'm your AI assistant for DeFi! I can help with market analysis (Hunter AI), automated trading (ULTRA), lending rates, swaps, and more. Ask me about protocols, yields, risks, or how to get started. Sign up for full access to all features.",
                "es": "¡Soy tu asistente de IA para DeFi! Puedo ayudar con análisis de mercado (Hunter AI), trading automatizado (ULTRA), tasas de préstamo, swaps y más. Pregúntame sobre protocolos, rendimientos, riesgos o cómo empezar. Regístrate para acceso completo.",
                "pt": "Sou seu assistente de IA para DeFi! Posso ajudar com análise de mercado (Hunter AI), trading automatizado (ULTRA), taxas de empréstimo, swaps e mais. Pergunte-me sobre protocolos, rendimentos, riscos ou como começar. Cadastre-se para acesso completo.",
                "zh": "我是您的 DeFi AI 助手！我可以帮助进行市场分析（Hunter AI）、自动交易（ULTRA）、借贷利率、交换等。问我关于协议、收益、风险或如何开始。注册以获得完整功能访问。",
            },
        }

        intent_responses = responses.get(
            intent, responses[ChatIntent.GENERAL_CONVERSATION]
        )
        return intent_responses.get(language, intent_responses["en"])

    def _blocked_response(self, guest: GuestUser, language: str) -> GuestMessageResult:
        """Return response for blocked guest."""
        messages = {
            "en": "Your access has been restricted. Please contact support.",
            "es": "Tu acceso ha sido restringido. Por favor contacta a soporte.",
            "pt": "Seu acesso foi restrito. Por favor, entre em contato com o suporte.",
            "zh": "您的访问已被限制。请联系支持。",
        }

        return GuestMessageResult(
            conversation_id=UUID("00000000-0000-0000-0000-000000000000"),
            message_id=UUID("00000000-0000-0000-0000-000000000000"),
            user_message={},
            agent_message={
                "content": messages.get(language, messages["en"]),
                "role": "assistant",
            },
            routing={
                "intent": "BLOCKED",
                "is_demo_mode": True,
            },
            rate_limited=True,
        )

    def _rate_limited_response(
        self, guest: GuestUser, language: str
    ) -> GuestMessageResult:
        """Return response for rate limited guest."""
        return GuestMessageResult(
            conversation_id=UUID("00000000-0000-0000-0000-000000000000"),
            message_id=UUID("00000000-0000-0000-0000-000000000000"),
            user_message={},
            agent_message={
                "content": get_rate_limit_message(language),
                "role": "assistant",
            },
            routing={
                "intent": "RATE_LIMITED",
                "is_demo_mode": True,
            },
            registration_required={
                "required": True,
                "reason": "rate_limit",
                "message": {
                    "en": "You've reached the demo limit. Sign up for unlimited access.",
                    "es": "Has alcanzado el límite demo. Regístrate para acceso ilimitado.",
                    "pt": "Você atingiu o limite demo. Cadastre-se para acesso ilimitado.",
                    "zh": "您已达到演示限制。注册以获得无限访问。",
                },
                "cta": GUEST_CTA_MESSAGES,
                "signup_url": "/signup",
            },
            rate_limited=True,
        )
