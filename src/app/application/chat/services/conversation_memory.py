"""
Conversation Memory Service.

Provides real conversational context from previous messages.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID

from app.domain.chat.entities.chat_message import ChatMessage

logger = logging.getLogger(__name__)

# Maximum messages to use for context
MAX_CONTEXT_MESSAGES = 10


class MessageRepositoryProtocol(Protocol):
    """Protocol for message repository."""
    
    async def get_recent_messages(
        self,
        conversation_id: UUID,
        limit: int = MAX_CONTEXT_MESSAGES,
    ) -> list[ChatMessage]:
        """Get recent messages from conversation."""
        ...


@dataclass
class ConversationContext:
    """Container for conversation context."""
    
    messages: list[ChatMessage] = field(default_factory=list)
    summary: str = ""
    detected_entities: dict[str, Any] = field(default_factory=dict)
    pending_intent: str | None = None
    pending_swap_info: dict[str, Any] | None = None
    pending_moonpay_swap_info: dict[str, Any] | None = None  # MoonPay swap flow
    pending_lending_info: dict[str, Any] | None = None
    pending_portfolio_info: dict[str, Any] | None = None
    pending_activity_info: dict[str, Any] | None = None
    pending_money_market_info: dict[str, Any] | None = None
    pending_buy_info: dict[str, Any] | None = None
    
    @property
    def has_context(self) -> bool:
        """Check if there's any context."""
        return len(self.messages) > 0
    
    @property
    def message_count(self) -> int:
        """Number of messages in context."""
        return len(self.messages)


class ConversationMemory:
    """
    Service for managing conversational memory.
    
    Retrieves context from previous messages for multi-turn conversations.
    """
    
    def __init__(
        self,
        message_repository: MessageRepositoryProtocol,
        max_context_messages: int = MAX_CONTEXT_MESSAGES,
    ):
        self._message_repo = message_repository
        self._max_messages = max_context_messages
    
    async def get_context(self, conversation_id: UUID) -> ConversationContext:
        """
        Get conversation context from recent messages.
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            ConversationContext with messages, summary, entities, and pending intent
        """
        try:
            messages = await self._message_repo.get_recent_messages(
                conversation_id=conversation_id,
                limit=self._max_messages,
            )
            
            return ConversationContext(
                messages=messages,
                summary=self._build_summary(messages),
                detected_entities=self._extract_entities(messages),
                pending_intent=self._get_pending_intent(messages),
                pending_swap_info=self._get_pending_swap_info(messages),
                pending_moonpay_swap_info=self._get_pending_moonpay_swap_info(messages),
                pending_lending_info=self._get_pending_lending_info(messages),
                pending_portfolio_info=self._get_pending_portfolio_info(messages),
                pending_activity_info=self._get_pending_activity_info(messages),
                pending_money_market_info=self._get_pending_money_market_info(messages),
                pending_buy_info=self._get_pending_buy_info(messages),
            )
        except Exception as e:
            logger.warning(f"Failed to get conversation context: {e}")
            return ConversationContext()
    
    def _build_summary(self, messages: list[ChatMessage]) -> str:
        """
        Build text summary for context.
        
        Creates a formatted string of recent messages for use in
        intent detection and response generation.
        """
        if not messages:
            return ""
        
        lines = []
        for msg in messages:
            role = "User" if msg.role.value == "user" else "Assistant"
            intent_info = f" [{msg.intent}]" if msg.intent else ""
            # Truncate long messages
            content = msg.content[:200]
            if len(msg.content) > 200:
                content += "..."
            lines.append(f"{role}{intent_info}: {content}")
        
        return "\n".join(lines)
    
    def _extract_entities(self, messages: list[ChatMessage]) -> dict[str, Any]:
        """
        Extract entities mentioned in conversation.
        
        Collects tokens, amounts, protocols, and other entities
        from message metadata.
        """
        entities: dict[str, Any] = {
            "tokens": set(),
            "amounts": [],
            "protocols": set(),
            "chains": set(),
        }
        
        for msg in messages:
            if not msg.metadata:
                continue
            
            msg_entities = msg.get_extracted_entities()
            
            # Collect tokens
            if "token" in msg_entities:
                entities["tokens"].add(msg_entities["token"])
            if "tokens" in msg_entities:
                for token in msg_entities["tokens"]:
                    entities["tokens"].add(token)
            
            # Collect amounts
            if "amount" in msg_entities:
                entities["amounts"].append(msg_entities["amount"])
            
            # Collect protocols
            if "protocol" in msg_entities:
                entities["protocols"].add(msg_entities["protocol"])
            if "protocols" in msg_entities:
                for protocol in msg_entities["protocols"]:
                    entities["protocols"].add(protocol)
            
            # Collect chains
            if "chain" in msg_entities:
                entities["chains"].add(msg_entities["chain"])
        
        # Convert sets to lists for JSON serialization
        return {
            "tokens": list(entities["tokens"]),
            "amounts": entities["amounts"],
            "protocols": list(entities["protocols"]),
            "chains": list(entities["chains"]),
        }
    
    def _get_pending_intent(self, messages: list[ChatMessage]) -> str | None:
        """
        Detect if there's a pending/incomplete flow.

        Checks the last assistant message for pending_action metadata
        (e.g., swap awaiting confirmation).
        """
        if not messages:
            logger.debug("[CONV_MEM] No messages, pending_intent = None")
            return None

        # Find the most recent assistant message (messages are newest-first)
        for msg in messages:
            if msg.is_assistant_message:
                pending = msg.get_pending_action()
                logger.debug(f"[CONV_MEM] Found assistant message, pending_action = {pending}, metadata = {msg.metadata}")
                if pending:
                    logger.info(f"[CONV_MEM] Returning pending_intent: {pending}")
                    return pending
                break

        logger.debug("[CONV_MEM] No pending_intent found")
        return None
    
    def _get_pending_swap_info(self, messages: list[ChatMessage]) -> dict[str, Any] | None:
        """
        Get swap info from the last assistant message if there's a pending swap flow or complete swap.

        This preserves the state of multi-turn swap conversations
        (e.g., from_token, to_token already collected) and also detects complete swaps waiting for confirmation.
        """
        if not messages:
            return None

        # Find the most recent assistant message with swap info (messages are newest-first)
        for msg in messages:
            if msg.is_assistant_message:
                # Check for pending swap action
                pending = msg.get_pending_action()
                if pending and pending.startswith("swap_"):
                    swap_info = msg.get_swap_info()
                    if swap_info:
                        return swap_info

                # Also check for complete swap in metadata (when quote was shown)
                swap_info = msg.get_swap_info()
                if swap_info and swap_info.get("is_complete"):
                    return swap_info
                break

        return None
    
    def _get_pending_buy_info(self, messages: list[ChatMessage]) -> dict[str, Any] | None:
        """
        Get buy info from the last assistant message if there's a pending buy flow.

        This preserves the state of multi-turn buy conversations
        (e.g., amount already collected, awaiting crypto selection).
        """
        if not messages:
            return None

        # Find the most recent assistant message with buy info (messages are newest-first)
        for msg in messages:
            if msg.is_assistant_message:
                # Check for pending buy action
                pending = msg.get_pending_action()
                if pending and pending.startswith("buy_"):
                    buy_info = msg.get_buy_info()
                    if buy_info:
                        return buy_info
                break

        return None
    
    def _get_pending_moonpay_swap_info(self, messages: list[ChatMessage]) -> dict[str, Any] | None:
        """
        Get MoonPay swap info from the last assistant message if there's a pending swap flow.

        This preserves the state of multi-turn MoonPay swap conversations
        (e.g., from_token, to_token already collected).
        """
        if not messages:
            return None

        # Find the most recent assistant message with MoonPay swap info (messages are newest-first)
        for msg in messages:
            if msg.is_assistant_message:
                # Check for pending MoonPay swap action
                pending = msg.get_pending_action()
                if pending and pending.startswith("moonpay_swap_"):
                    # Get swap info from metadata
                    moonpay_swap_info = msg.metadata.get("moonpay_swap_info") if msg.metadata else None
                    if moonpay_swap_info:
                        return moonpay_swap_info
                    # Also check for swap_info in metadata (fallback)
                    swap_info = msg.get_swap_info()
                    if swap_info:
                        return swap_info

                # Also check for complete MoonPay swap in metadata (when quote was shown)
                swap_info = msg.get_swap_info()
                if swap_info and swap_info.get("is_complete"):
                    return swap_info
                break

        return None

    def _get_pending_lending_info(self, messages: list[ChatMessage]) -> dict[str, Any] | None:
        """
        Get lending info from the last assistant message if there's a pending lending flow.

        This preserves the state of multi-turn lending conversations.
        """
        if not messages:
            logger.debug("[CONV_MEM] No messages for lending_info")
            return None

        # Find the most recent assistant message with lending info (messages are newest-first)
        for msg in messages:
            if msg.is_assistant_message:
                pending = msg.get_pending_action()
                logger.debug(f"[CONV_MEM] Checking lending_info - pending_action: {pending}, metadata keys: {list(msg.metadata.keys())}")
                if pending and pending.startswith("lending_"):
                    lending_info = msg.metadata.get("lending_info")
                    logger.info(f"[CONV_MEM] Found lending_info: {lending_info}")
                    if lending_info:
                        return lending_info
                break

        logger.debug("[CONV_MEM] No lending_info found")
        return None

    def _get_pending_portfolio_info(self, messages: list[ChatMessage]) -> dict[str, Any] | None:
        """
        Get portfolio info from the last assistant message if there's a pending portfolio flow.

        This preserves the state of multi-turn portfolio conversations.
        """
        if not messages:
            return None

        # Find the most recent assistant message with portfolio info (messages are newest-first)
        for msg in messages:
            if msg.is_assistant_message:
                pending = msg.get_pending_action()
                if pending and pending.startswith("portfolio_"):
                    portfolio_info = msg.metadata.get("portfolio_info")
                    if portfolio_info:
                        return portfolio_info
                break

        return None

    def _get_pending_activity_info(self, messages: list[ChatMessage]) -> dict[str, Any] | None:
        """
        Get activity info from the last assistant message if there's a pending activity flow.

        This preserves the state of multi-turn activity conversations.
        """
        if not messages:
            return None

        # Find the most recent assistant message with activity info (messages are newest-first)
        for msg in messages:
            if msg.is_assistant_message:
                pending = msg.get_pending_action()
                if pending and pending.startswith("activity_"):
                    activity_info = msg.metadata.get("activity_info")
                    if activity_info:
                        return activity_info
                break

        return None

    def _get_pending_money_market_info(self, messages: list[ChatMessage]) -> dict[str, Any] | None:
        """
        Get money market info from the last assistant message if there's a pending money market flow.

        This preserves the state of multi-turn money market conversations.
        """
        if not messages:
            return None

        # Find the most recent assistant message with money market info (messages are newest-first)
        for msg in messages:
            if msg.is_assistant_message:
                pending = msg.get_pending_action()
                if pending and pending.startswith("money_market_"):
                    money_market_info = msg.metadata.get("money_market_info")
                    if money_market_info:
                        return money_market_info
                break

        return None
    
    def build_context_string(self, context: ConversationContext) -> str:
        """
        Build a context string for handlers.
        
        Combines summary and entity information.
        """
        parts = []
        
        if context.summary:
            parts.append(context.summary)
        
        if context.detected_entities.get("tokens"):
            tokens = ", ".join(context.detected_entities["tokens"])
            parts.append(f"[Mentioned tokens: {tokens}]")
        
        if context.pending_intent:
            parts.append(f"[Pending action: {context.pending_intent}]")
        
        return "\n".join(parts)

