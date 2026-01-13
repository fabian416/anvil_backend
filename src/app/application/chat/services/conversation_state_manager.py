"""
Conversation State Manager - Auto-clearing stale flows

Prevents state corruption by automatically detecting and clearing:
1. Timed-out flows (inactivity > 5 minutes)
2. Off-topic message sequences (2+ consecutive unrelated messages)
3. Explicit cancellation keywords

Part of the resilient intent detection system.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

# Import moved to avoid circular dependency
# ConversationContext will be imported from conversation_memory at runtime

logger = logging.getLogger(__name__)


class ConversationStateManager:
    """
    Manages conversation flow state with automatic cleanup.

    Prevents stuck flows and state corruption by:
    - Timeout detection (5 min inactivity)
    - Off-topic counter (2+ consecutive)
    - Cancellation keyword detection
    """

    # Flow timeout: Clear if no activity for 5 minutes
    FLOW_TIMEOUT = timedelta(minutes=5)

    # Off-topic threshold: Clear after 2 consecutive unrelated messages
    MAX_OFF_TOPIC_MESSAGES = 2

    # Cancellation keywords (multi-language)
    CANCELLATION_KEYWORDS = {
        "en": ["cancel", "stop", "abort", "forget it", "never mind", "quit", "exit"],
        "es": ["cancelar", "parar", "abortar", "olvidalo", "déjalo", "salir"],
        "pt": ["cancelar", "parar", "abortar", "esquecer", "sair"],
        "zh": ["取消", "停止", "放弃", "退出"],
    }

    # Flow-related keywords (to detect relevance)
    FLOW_KEYWORDS = {
        "swap": ["swap", "exchange", "trade", "cambiar", "trocar", "兌換"],
        "moonpay_swap": ["moonpay", "buy", "sell", "comprar", "vender", "購買"],
        "lending": ["lend", "deposit", "supply", "prestar", "depositar", "存入"],
        "buy": ["buy", "purchase", "comprar", "購買"],
    }

    def should_clear_pending_flow(
        self,
        context: "ConversationContext",
        current_message: str,
        language: str = "en",
    ) -> tuple[bool, str]:
        """
        Determine if pending flow should be automatically cleared.

        Returns:
            (should_clear: bool, reason: str)

        Clearing conditions:
        1. Flow timeout (5 min inactivity)
        2. Consecutive off-topic messages (2+)
        3. Explicit cancellation keywords

        Args:
            context: Conversation context with flow state
            current_message: User's current message
            language: Language code (en, es, pt, zh)
        """
        if not context.pending_intent:
            return False, "no_pending_flow"

        message_lower = current_message.lower().strip()

        # 1. Check for explicit cancellation keywords
        cancellation_keywords = self.CANCELLATION_KEYWORDS.get(
            language, self.CANCELLATION_KEYWORDS["en"]
        )

        for keyword in cancellation_keywords:
            if keyword in message_lower:
                logger.info(
                    f"Auto-clearing flow: cancellation keyword '{keyword}' detected",
                    extra={
                        "pending_intent": context.pending_intent,
                        "keyword": keyword,
                        "message": current_message[:100],
                    },
                )
                return True, f"cancellation_keyword:{keyword}"

        # 2. Check for flow timeout
        if hasattr(context, "pending_intent_timestamp") and context.pending_intent_timestamp:
            elapsed = datetime.now() - context.pending_intent_timestamp
            if elapsed > self.FLOW_TIMEOUT:
                logger.info(
                    f"Auto-clearing flow: timeout exceeded ({elapsed.total_seconds():.0f}s)",
                    extra={
                        "pending_intent": context.pending_intent,
                        "elapsed_seconds": elapsed.total_seconds(),
                        "timeout_seconds": self.FLOW_TIMEOUT.total_seconds(),
                    },
                )
                return True, f"timeout:{elapsed.total_seconds():.0f}s"

        # 3. Check for consecutive off-topic messages
        if hasattr(context, "off_topic_message_count") and context.off_topic_message_count:
            if context.off_topic_message_count >= self.MAX_OFF_TOPIC_MESSAGES:
                logger.info(
                    f"Auto-clearing flow: too many off-topic messages ({context.off_topic_message_count})",
                    extra={
                        "pending_intent": context.pending_intent,
                        "off_topic_count": context.off_topic_message_count,
                        "threshold": self.MAX_OFF_TOPIC_MESSAGES,
                    },
                )
                return True, f"off_topic_count:{context.off_topic_message_count}"

        return False, "flow_active"

    def track_message_relevance(
        self,
        context: "ConversationContext",
        current_message: str,
    ) -> None:
        """
        Track if current message is relevant to pending flow.

        Updates context.off_topic_message_count:
        - Increment if message is off-topic
        - Reset to 0 if message is on-topic

        This enables automatic flow clearing after 2+ consecutive
        off-topic messages.

        Args:
            context: Conversation context with flow state
            current_message: User's current message
        """
        if not context.pending_intent:
            return

        # Check if message is relevant to current flow
        is_relevant = self._is_relevant_to_flow(current_message, context.pending_intent)

        # Initialize counter if not present
        if not hasattr(context, "off_topic_message_count"):
            context.off_topic_message_count = 0

        if not is_relevant:
            context.off_topic_message_count += 1
            logger.debug(
                f"Off-topic message detected (count: {context.off_topic_message_count})",
                extra={
                    "pending_intent": context.pending_intent,
                    "message": current_message[:100],
                },
            )
        else:
            # Reset counter on relevant message
            if context.off_topic_message_count > 0:
                logger.debug(
                    "Resetting off-topic counter (relevant message)",
                    extra={
                        "pending_intent": context.pending_intent,
                        "previous_count": context.off_topic_message_count,
                    },
                )
            context.off_topic_message_count = 0

    def _is_relevant_to_flow(self, message: str, pending_intent: str) -> bool:
        """
        Check if message is relevant to the pending flow.

        Uses flow-specific keywords to determine relevance.

        Args:
            message: User message
            pending_intent: Current pending flow (e.g., "swap_awaiting_from_token")

        Returns:
            True if message is relevant to the flow
        """
        message_lower = message.lower().strip()

        # Extract base flow type (remove "_awaiting_..." suffix)
        base_flow = pending_intent.split("_awaiting")[0]

        # Get keywords for this flow type
        flow_keywords = self.FLOW_KEYWORDS.get(base_flow, [])

        # Check if any flow keyword is in message
        for keyword in flow_keywords:
            if keyword in message_lower:
                return True

        # Check if message looks like a token/amount (for swap/buy/lending)
        if self._looks_like_flow_continuation(message_lower, base_flow):
            return True

        return False

    def _looks_like_flow_continuation(self, message: str, flow_type: str) -> bool:
        """
        Check if message looks like a flow continuation value.

        For example:
        - Swap: token names (BTC, ETH), amounts
        - Lending: amounts, asset names
        - Buy: amounts, crypto names

        Args:
            message: Lowercased message
            flow_type: Base flow type

        Returns:
            True if message looks like a continuation value
        """
        # Common crypto tokens
        crypto_tokens = [
            "btc", "eth", "usdt", "usdc", "bnb", "ada", "sol", "xrp",
            "dot", "doge", "avax", "matic", "link", "uni", "dai",
        ]

        # Check for token names
        for token in crypto_tokens:
            if token in message:
                return True

        # Check for numeric amounts (e.g., "100", "1000", "0.5")
        import re
        if re.search(r"\b\d+\.?\d*\b", message):
            return True

        return False

    def clear_flow_state(self, context: "ConversationContext") -> None:
        """
        Clear all flow-related state from context.

        This includes:
        - pending_intent
        - pending_swap_info
        - pending_moonpay_swap_info
        - pending_lending_info
        - pending_buy_info
        - pending_portfolio_info
        - pending_activity_info
        - pending_money_market_info
        - off_topic_message_count
        - pending_intent_timestamp

        Args:
            context: Conversation context to clear
        """
        logger.info(
            "Clearing flow state",
            extra={
                "pending_intent": context.pending_intent,
                "had_swap_info": bool(getattr(context, "pending_swap_info", None)),
                "had_lending_info": bool(getattr(context, "pending_lending_info", None)),
            },
        )

        # Clear all flow state
        context.pending_intent = None
        context.pending_swap_info = None
        context.pending_moonpay_swap_info = None
        context.pending_lending_info = None
        context.pending_buy_info = None
        context.pending_portfolio_info = None
        context.pending_activity_info = None
        context.pending_money_market_info = None

        # Clear tracking counters
        if hasattr(context, "off_topic_message_count"):
            context.off_topic_message_count = 0
        if hasattr(context, "pending_intent_timestamp"):
            context.pending_intent_timestamp = None

    def init_flow_state(self, context: "ConversationContext") -> None:
        """
        Initialize flow tracking state when a new flow starts.

        Sets:
        - pending_intent_timestamp = now
        - off_topic_message_count = 0

        Args:
            context: Conversation context
        """
        if not hasattr(context, "pending_intent_timestamp"):
            context.pending_intent_timestamp = None
        if not hasattr(context, "off_topic_message_count"):
            context.off_topic_message_count = 0

        # Update timestamp when flow starts
        if context.pending_intent:
            context.pending_intent_timestamp = datetime.now()
            context.off_topic_message_count = 0

            logger.debug(
                "Initialized flow state tracking",
                extra={
                    "pending_intent": context.pending_intent,
                    "timestamp": context.pending_intent_timestamp.isoformat(),
                },
            )
