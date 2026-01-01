"""
Send Guest Message Command.

Handles guest chat messages with:
- Auto-create guest user by IP
- Auto-create conversation if new/archived
- Intent detection and routing
- Registration prompts for restricted actions
- Rate limiting
- Telemetry logging
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
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
from app.domain.guest.entities.guest_conversation import GuestConversation
from app.domain.guest.entities.guest_message import GuestMessage
from app.domain.guest.entities.guest_user import GuestUser
from app.domain.guest.ports.guest_repository import GuestRepository

logger = logging.getLogger(__name__)


# ========================================
# Rate Limiting Configuration
# ========================================

RATE_LIMIT_MESSAGES_PER_HOUR = 20
RATE_LIMIT_MESSAGES_PER_DAY = 50
MAX_MESSAGE_LENGTH = 500

# ========================================
# Restricted Intents (require registration)
# ========================================

RESTRICTED_INTENTS = {
    ChatIntent.PORTFOLIO,
    ChatIntent.BALANCE,
    ChatIntent.ACTIVITY,
    ChatIntent.RECEIVE,
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
    ):
        self._guest_repo = guest_repository
        self._intent_detector = intent_detector

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

        # 4. Detect intent
        intent, confidence, handler = await self._detect_intent(content)

        # 5. Check if restricted
        is_restricted, reason = self._is_restricted_action(intent)

        # 6. Create user message
        user_message = GuestMessage.create_user_message(
            conversation_id=conversation.id,
            content=content,
            language=language,
        )
        await self._guest_repo.create_message(user_message)

        # 7. Generate response
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
        else:
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
        hour_ago = datetime.utcnow() - timedelta(hours=1)
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
                "intent": intent.value if intent else "GENERAL_CONVERSATION",
                "confidence": confidence or 0.5,
                "handler": handler or "demo_handler",
                "language": language,
                "is_demo_mode": True,
            },
            enrichment={
                "disclaimer": get_demo_disclaimer(language),
            },
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
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        messages_this_hour = await self._guest_repo.get_message_count_since(
            guest.id, hour_ago
        )

        if messages_this_hour >= RATE_LIMIT_MESSAGES_PER_HOUR:
            return True, 0

        return False, RATE_LIMIT_MESSAGES_PER_HOUR - messages_this_hour

    async def _detect_intent(
        self, content: str
    ) -> tuple[ChatIntent | None, float | None, str | None]:
        """Detect intent from message content."""
        if not self._intent_detector:
            return ChatIntent.GENERAL_CONVERSATION, 0.5, "demo_handler"

        try:
            result = await self._intent_detector.detect_intent(content)
            return result.intent, result.confidence, result.handler
        except Exception as e:
            logger.warning(f"Intent detection failed: {e}")
            return ChatIntent.GENERAL_CONVERSATION, 0.5, "demo_handler"

    def _is_restricted_action(
        self, intent: ChatIntent | None
    ) -> tuple[bool, str | None]:
        """Check if intent requires registration."""
        if not intent:
            return False, None

        if intent in RESTRICTED_INTENTS:
            reason = get_reason_for_intent(intent.value)
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
            ChatIntent.GENERAL_CONVERSATION: {
                "en": "I'm your AI assistant for DeFi! Ask me about protocols, yields, risks, or how to get started. Sign up for full access to all features.",
                "es": "¡Soy tu asistente de IA para DeFi! Pregúntame sobre protocolos, rendimientos, riesgos o cómo empezar. Regístrate para acceso completo.",
                "pt": "Sou seu assistente de IA para DeFi! Pergunte-me sobre protocolos, rendimentos, riscos ou como começar. Cadastre-se para acesso completo.",
                "zh": "我是您的 DeFi AI 助手！问我关于协议、收益、风险或如何开始。注册以获得完整功能访问。",
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
