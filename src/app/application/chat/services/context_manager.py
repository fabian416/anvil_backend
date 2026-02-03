"""
Service for managing conversation context and agent memory.
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.domain.chat.entities.conversation_context import ConversationContext
from app.domain.chat.ports.conversation_context_repository import (
    ConversationContextRepository,
)

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages conversation context for intelligent agent interactions.

    Responsibilities:
    - Track conversation state
    - Learn user preferences
    - Recognize patterns
    - Provide context to agents
    """

    def __init__(self, repository: ConversationContextRepository):
        """
        Initialize context manager.

        Args:
            repository: Context repository
        """
        self._repository = repository

    async def get_or_create_context(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> ConversationContext:
        """
        Get existing context or create new one.

        Args:
            conversation_id: Conversation identifier
            user_id: User identifier

        Returns:
            ConversationContext
        """
        context = await self._repository.get_by_conversation_id(conversation_id)

        if not context:
            context = ConversationContext(
                conversation_id=conversation_id,
                user_id=user_id,
            )
            await self._repository.save(context)
            logger.info(f"Created new context for conversation {conversation_id}")

        return context

    async def update_context_with_message(
        self,
        context: ConversationContext,
        message: str,
        intent: str,
        extracted_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update context based on new message.

        Args:
            context: Current context
            message: User message
            intent: Classified intent
            extracted_data: Extracted entities (tokens, amounts, etc.)
        """
        # Add intent to history
        context.add_intent(intent)

        # Extract and track tokens
        if extracted_data:
            tokens = extracted_data.get("tokens", [])
            for token in tokens:
                context.add_mentioned_token(token)

            protocols = extracted_data.get("protocols", [])
            for protocol in protocols:
                context.add_mentioned_protocol(protocol)

            # Update typical trade sizes
            if "amount" in extracted_data and "token" in extracted_data:
                token = extracted_data["token"]
                amount = float(extracted_data["amount"])

                # Calculate running average
                if token in context.typical_trade_sizes:
                    current = context.typical_trade_sizes[token]
                    context.typical_trade_sizes[token] = (current + amount) / 2
                else:
                    context.typical_trade_sizes[token] = amount

        # Infer current topic from recent intents
        if len(context.recent_intents) >= 3:
            recent = context.recent_intents[-3:]
            if all(i.startswith("trade_") for i in recent):
                context.current_topic = "trading"
            elif all(i.startswith("portfolio") for i in recent):
                context.current_topic = "portfolio"
            elif "trade_swap" in recent:
                context.current_topic = "swapping"

        await self._repository.save(context)
        logger.debug(f"Updated context for conversation {context.conversation_id}")

    async def learn_preferences(
        self,
        context: ConversationContext,
        action: str,
        parameters: Dict[str, Any],
    ) -> None:
        """
        Learn user preferences from actions.

        Args:
            context: Current context
            action: Action type (e.g., "swap", "trade")
            parameters: Action parameters
        """
        # Learn slippage preference
        if "slippage" in parameters:
            slippage = float(parameters["slippage"])
            if context.preferred_slippage is None:
                context.preferred_slippage = slippage
            else:
                # Running average
                context.preferred_slippage = (context.preferred_slippage + slippage) / 2

        # Learn leverage preference
        if "leverage" in parameters:
            leverage = int(parameters["leverage"])
            if context.preferred_leverage is None:
                context.preferred_leverage = leverage
            else:
                # Most common value
                context.preferred_leverage = leverage

        # Learn risk tolerance
        if "leverage" in parameters:
            leverage = int(parameters["leverage"])
            if leverage <= 3:
                context.risk_tolerance = "low"
            elif leverage <= 10:
                context.risk_tolerance = "medium"
            else:
                context.risk_tolerance = "high"

        # Learn chain preferences
        if "chain" in parameters:
            chain = parameters["chain"]
            if chain not in context.preferred_chains:
                context.preferred_chains.append(chain)

        await self._repository.save(context)
        logger.info(f"Updated preferences for user {context.user_id}")

    def get_context_summary(self, context: ConversationContext) -> str:
        """
        Get human-readable context summary.

        Args:
            context: Conversation context

        Returns:
            Summary string
        """
        lines = ["**Conversation Context:**"]

        if context.current_topic:
            lines.append(f"• Current Topic: {context.current_topic}")

        if context.mentioned_tokens:
            lines.append(
                f"• Mentioned Tokens: {', '.join(context.mentioned_tokens[-5:])}"
            )

        if context.preferred_slippage:
            lines.append(f"• Preferred Slippage: {context.preferred_slippage:.1f}%")

        if context.preferred_leverage:
            lines.append(f"• Preferred Leverage: {context.preferred_leverage}x")

        if context.risk_tolerance:
            lines.append(f"• Risk Tolerance: {context.risk_tolerance}")

        dominant = context.get_dominant_intent()
        if dominant:
            lines.append(f"• Most Common Action: {dominant}")

        if context.is_experienced_user():
            lines.append(
                f"• Experience: {context.interaction_count} interactions (Experienced)"
            )
        else:
            lines.append(
                f"• Experience: {context.interaction_count} interactions (New)"
            )

        return "\n".join(lines)

    def get_agent_context(self, context: ConversationContext) -> Dict[str, Any]:
        """
        Prepare context data for agent consumption.

        Args:
            context: Conversation context

        Returns:
            Context dictionary for agents
        """
        return {
            "current_topic": context.current_topic,
            "recent_intents": context.recent_intents[-5:],
            "mentioned_tokens": context.mentioned_tokens[-10:],
            "mentioned_protocols": context.mentioned_protocols[-5:],
            "user_preferences": {
                "slippage": context.preferred_slippage,
                "leverage": context.preferred_leverage,
                "risk_tolerance": context.risk_tolerance,
                "chains": context.preferred_chains,
            },
            "experience_level": "experienced"
            if context.is_experienced_user()
            else "beginner",
            "dominant_action": context.get_dominant_intent(),
        }
