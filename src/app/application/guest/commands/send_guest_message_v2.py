"""
Send Guest Message Command V2 - Pure LLM-Based Action Detection.

NO INTENTS. NO REGEX PATTERNS. NO FAST-PATHS.

The SupervisorCoordinator uses LLM to understand the user's input and
determines what actions/agents are needed. This is the architecture
the CEO requested.

Flow:
1. Basic validation (rate limits, blocked users)
2. Security check (harmful content patterns only)
3. Send EVERYTHING to SupervisorCoordinator
4. Supervisor uses LLM to plan workflow based on semantic understanding
5. Execute workflow and return response
"""

import logging
import time
from datetime import datetime, UTC
from typing import Any
from uuid import UUID

from app.domain.guest.entities.guest_conversation import GuestConversation
from app.domain.guest.entities.guest_message import GuestMessage
from app.domain.guest.entities.guest_user import GuestUser
from app.domain.guest.ports.guest_repository import GuestRepository

logger = logging.getLogger(__name__)

# Constants
MAX_MESSAGE_LENGTH = 10000
MESSAGES_PER_HOUR = 20


class SendGuestMessageV2:
    """
    Send Guest Message Command - Pure LLM-Based.

    Architecture:
    - NO intent classification
    - NO regex-based fast paths
    - ALL queries go to SupervisorCoordinator
    - LLM decides what agents/actions are needed

    The only "patterns" we check are security-related (harmful content).
    Everything else is understood by LLM.
    """

    def __init__(
        self,
        guest_repository: GuestRepository,
        supervisor_coordinator: Any,  # SupervisorCoordinator
        agent_orchestrator: Any,  # AgentOrchestrator
    ):
        self._guest_repo = guest_repository
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
    ) -> dict:
        """
        Execute guest message command.

        Flow:
        1. Validate input & check rate limits
        2. Security check (harmful content only)
        3. Send to SupervisorCoordinator (LLM-based action detection)
        4. Return response
        """
        start_time = time.time()

        # === STEP 1: Basic Validation ===
        if language not in ("en", "es", "pt", "zh"):
            language = "en"

        if len(content) > MAX_MESSAGE_LENGTH:
            content = content[:MAX_MESSAGE_LENGTH]

        # Get or create guest
        guest = await self._get_or_create_guest(ip_address, language, fingerprint)

        if guest.is_blocked:
            return self._blocked_response(language)

        # Rate limit check
        is_rate_limited, messages_remaining = await self._check_rate_limit(guest)
        if is_rate_limited:
            return self._rate_limited_response(language, messages_remaining)

        # Get or create conversation
        conversation = await self._get_or_create_conversation(guest, language)

        # === STEP 2: Security Check (Harmful Content Only) ===
        if self._is_harmful_content(content):
            return self._harmful_content_response(language, conversation.id)

        # === STEP 3: Build Context ===
        context = await self._build_conversation_context(conversation.id)

        # === STEP 4: Send to SupervisorCoordinator (LLM-Based) ===
        # The Supervisor will use LLM to understand the query and plan workflow
        try:
            logger.info(
                "🎯 LLM-based routing: Sending to SupervisorCoordinator",
                extra={
                    "ip_address": ip_address,
                    "conversation_id": str(conversation.id),
                    "content_preview": content[:100],
                },
            )

            result = await self._process_with_supervisor(
                content=content,
                language=language,
                conversation=conversation,
                context=context,
                ip_address=ip_address,
            )

            # Calculate total time
            total_time_ms = int((time.time() - start_time) * 1000)

            # Update counters
            guest.increment_messages()
            conversation.increment_messages()
            await self._guest_repo.update_guest(guest)
            await self._guest_repo.update_conversation(conversation)

            # Add timing to result
            result["total_time_ms"] = total_time_ms
            result["messages_remaining"] = messages_remaining - 1

            return result

        except Exception as e:
            logger.error(f"SupervisorCoordinator failed: {e}", exc_info=True)
            return self._error_response(language, str(e))

    async def _process_with_supervisor(
        self,
        content: str,
        language: str,
        conversation: GuestConversation,
        context: list[dict],
        ip_address: str,
    ) -> dict:
        """
        Process message with SupervisorCoordinator.

        The Supervisor uses LLM to:
        1. Understand the user's request (semantic understanding)
        2. Determine what agents/actions are needed
        3. Create and execute workflow plan

        NO INTENTS. Pure LLM comprehension.
        """
        from app.domain.value_objects.conversation_id import ConversationId
        from app.domain.value_objects.message_content import MessageContent
        from app.domain.value_objects.agent_squad.conversation_context import (
            ConversationContext as AgentSquadContext,
        )
        from app.domain.enums.agent_type import AgentType

        # Build conversation context for agents
        messages = await self._guest_repo.get_messages(conversation.id, limit=10)
        conversation_history = [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
                if hasattr(msg.created_at, "isoformat")
                else str(msg.created_at),
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

        # Get available agents
        available_agents = [
            AgentType.CHAT,
            AgentType.HUNTER_AI,
            AgentType.KNOWLEDGE,
            AgentType.DEFI_YIELD,
            AgentType.RISK_ANALYZER,
            AgentType.GAS_OPTIMIZER,
            AgentType.GUEST_AUTH,  # For restricted features
        ]

        # === LLM-BASED WORKFLOW PLANNING ===
        # The Supervisor uses LLM to understand the query and create workflow
        workflow_plan = await self._supervisor_coordinator.create_workflow_plan(
            conversation_id=ConversationId(conversation.id),
            message=MessageContent(content),
            conversation_context=agent_squad_context,
            available_agents=available_agents,
        )

        logger.info(
            f"📋 Workflow plan created: {len(workflow_plan.tasks)} tasks",
            extra={
                "tasks": [t.agent_type.value for t in workflow_plan.tasks],
                "conversation_id": str(conversation.id),
            },
        )

        # === EXECUTE WORKFLOW ===
        # Pass original_message explicitly to prevent conversation context pollution
        (
            response_content,
            sources_raw,
            agent_timings,
        ) = await self._supervisor_coordinator.execute_workflow(
            conversation_id=ConversationId(conversation.id),
            workflow_plan=workflow_plan,
            conversation_context=agent_squad_context,
            original_message=content,  # Explicitly pass current user message
        )

        # Convert sources to serializable format
        sources = []
        if sources_raw:
            for s in sources_raw:
                if hasattr(s, "to_dict"):
                    sources.append(s.to_dict())
                elif isinstance(s, dict):
                    sources.append(s)
                else:
                    sources.append(str(s))

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
            content=response_content,
            intent="LLM_WORKFLOW",  # No specific intent - LLM decided
            handler="supervisor_coordinator",
            confidence=1.0,  # LLM-based, no classification confidence
            language=language,
            is_restricted_action=False,
        )
        await self._guest_repo.create_message(agent_message)

        # Build result
        return {
            "conversation_id": str(conversation.id),
            "message_id": str(agent_message.id),
            "user_message": {
                "id": str(user_message.id),
                "role": "user",
                "content": content,
                "created_at": user_message.created_at.isoformat(),
            },
            "agent_message": {
                "id": str(agent_message.id),
                "role": "assistant",
                "content": response_content,
                "created_at": agent_message.created_at.isoformat(),
                "sources": sources,
            },
            "routing": {
                "handler": "supervisor_coordinator",
                "workflow_tasks": len(workflow_plan.tasks),
                "agents_used": [t.agent_type.value for t in workflow_plan.tasks],
                "language": language,
                "is_llm_based": True,  # Flag indicating LLM-based routing
            },
            "enrichment": {
                "agent_squad": True,
                "workflow_type": "llm_planned",
                "task_count": len(workflow_plan.tasks),
                "agent_timings": agent_timings if agent_timings else [],
            },
            "sources": sources if sources else None,
        }

    def _is_harmful_content(self, content: str) -> bool:
        """
        Check for harmful content patterns.

        This is the ONLY pattern-based check we do.
        Everything else is handled by LLM understanding.
        """
        content_lower = content.lower()

        # Harmful patterns (security only)
        harmful_patterns = [
            "ignore previous instructions",
            "ignore all instructions",
            "disregard your instructions",
            "forget your training",
            "jailbreak",
            "dan mode",
            "developer mode",
            "bypass your filters",
        ]

        return any(pattern in content_lower for pattern in harmful_patterns)

    async def _get_or_create_guest(
        self, ip_address: str, language: str, fingerprint: str | None
    ) -> GuestUser:
        """Get or create guest user."""
        guest = await self._guest_repo.get_by_ip(ip_address)

        if guest is None:
            guest = GuestUser.create(
                ip_address=ip_address,
                language=language,
                fingerprint=fingerprint,
            )
            await self._guest_repo.create_guest(guest)

        return guest

    async def _check_rate_limit(self, guest: GuestUser) -> tuple[bool, int]:
        """Check rate limits."""
        messages_in_hour = await self._guest_repo.count_messages_in_period(
            guest.id, hours=1
        )

        is_limited = messages_in_hour >= MESSAGES_PER_HOUR
        remaining = max(0, MESSAGES_PER_HOUR - messages_in_hour)

        return is_limited, remaining

    async def _get_or_create_conversation(
        self, guest: GuestUser, language: str
    ) -> GuestConversation:
        """Get active conversation or create new one."""
        conversation = await self._guest_repo.get_active_conversation(guest.id)

        if conversation is None:
            conversation = GuestConversation.create(
                guest_id=guest.id,
                language=language,
            )
            await self._guest_repo.create_conversation(conversation)

        return conversation

    async def _build_conversation_context(self, conversation_id: UUID) -> list[dict]:
        """Build conversation context from message history."""
        messages = await self._guest_repo.get_messages(conversation_id, limit=10)

        return [
            {
                "role": msg.role.value,
                "content": msg.content,
            }
            for msg in messages
        ]

    def _blocked_response(self, language: str) -> dict:
        """Response for blocked users."""
        messages = {
            "en": "Your access has been restricted. Please contact support.",
            "es": "Tu acceso ha sido restringido. Por favor contacta a soporte.",
            "pt": "Seu acesso foi restrito. Por favor, entre em contato com o suporte.",
            "zh": "您的访问已被限制。请联系支持。",
        }
        return {
            "error": "blocked",
            "message": messages.get(language, messages["en"]),
        }

    def _rate_limited_response(self, language: str, remaining: int) -> dict:
        """Response for rate limited users."""
        messages = {
            "en": "You've reached the message limit. Sign up for unlimited access.",
            "es": "Has alcanzado el límite de mensajes. Regístrate para acceso ilimitado.",
            "pt": "Você atingiu o limite de mensagens. Cadastre-se para acesso ilimitado.",
            "zh": "您已达到消息限制。注册以获得无限访问。",
        }
        return {
            "error": "rate_limited",
            "message": messages.get(language, messages["en"]),
            "messages_remaining": remaining,
        }

    def _harmful_content_response(self, language: str, conversation_id: UUID) -> dict:
        """Response for harmful content."""
        messages = {
            "en": "I can't help with that request. How can I assist you with DeFi?",
            "es": "No puedo ayudar con esa solicitud. ¿Cómo puedo asistirte con DeFi?",
            "pt": "Não posso ajudar com essa solicitação. Como posso ajudá-lo com DeFi?",
            "zh": "我无法帮助处理该请求。我能如何帮助您了解 DeFi？",
        }
        return {
            "conversation_id": str(conversation_id),
            "agent_message": {
                "content": messages.get(language, messages["en"]),
                "role": "assistant",
            },
            "routing": {
                "handler": "security_filter",
                "is_llm_based": False,
            },
        }

    def _error_response(self, language: str, error: str) -> dict:
        """Response for errors."""
        messages = {
            "en": "Sorry, something went wrong. Please try again.",
            "es": "Lo siento, algo salió mal. Por favor intenta de nuevo.",
            "pt": "Desculpe, algo deu errado. Por favor, tente novamente.",
            "zh": "抱歉，出了点问题。请重试。",
        }
        return {
            "error": "processing_error",
            "message": messages.get(language, messages["en"]),
            "details": error if logger.isEnabledFor(logging.DEBUG) else None,
        }
