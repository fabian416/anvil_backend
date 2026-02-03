"""
Flow Cancellation Detector Service.

Detects when a user wants to exit a multi-step flow by asking an unrelated question.
Uses hybrid approach: keyword matching (fast) + intent comparison (accurate).

Architecture:
- Fast path: Check for explicit cancellation/topic-change keywords
- Backup path: Compare classified intent with expected flow intent
- Multi-language support for all 5 languages (en, es, pt, zh, fr)

Example:
    User in lending flow: "Show best lending vaults" (waiting for asset)
    User asks: "What's the price of Bitcoin?"
    → Detected: Topic change from "lending" to "prediction"
    → Action: Cancel flow, process price query
"""

import logging
from typing import Literal

logger = logging.getLogger(__name__)


# Explicit cancellation and topic-switching keywords
# Organized by language for maintainability
TOPIC_CHANGE_KEYWORDS = {
    "en": [
        # Explicit cancellation
        "cancel",
        "stop",
        "abort",
        "never mind",
        "forget it",
        "nevermind",
        "exit",
        "quit",
        "back",
        "no thanks",
        # Topic switching indicators
        "actually",
        "instead",
        "rather",
        "what about",
        "how about",
        "show me",
        "tell me",
        "what is",
        "what's",
        "give me",
        "i want to",
        "i'd like to",
        "can you",
        "could you",
    ],
    "es": [
        # Explicit cancellation
        "cancelar",
        "parar",
        "abortar",
        "no importa",
        "olvídalo",
        "olvidalo",
        "salir",
        "atrás",
        "no gracias",
        # Topic switching
        "mejor",
        "en lugar",
        "en vez",
        "qué tal",
        "que tal",
        "muéstrame",
        "dime",
        "qué es",
        "que es",
        "dame",
        "quiero",
        "quisiera",
        "puedes",
        "podrías",
    ],
    "pt": [
        # Explicit cancellation
        "cancelar",
        "parar",
        "abortar",
        "não importa",
        "esquece",
        "sair",
        "voltar",
        "não obrigado",
        # Topic switching
        "melhor",
        "ao invés",
        "ao inves",
        "que tal",
        "mostre-me",
        "me mostre",
        "me diga",
        "o que é",
        "o que e",
        "me dê",
        "quero",
        "gostaria",
        "pode",
        "poderia",
    ],
    "zh": [
        # Explicit cancellation
        "取消",
        "停止",
        "算了",
        "没关系",
        "忘了",
        "退出",
        "返回",
        "不用了",
        # Topic switching
        "换个",
        "实际上",
        "其实",
        "什么是",
        "怎么",
        "给我看",
        "告诉我",
        "我想",
        "可以",
    ],
    "fr": [
        # Explicit cancellation
        "annuler",
        "arrêter",
        "arreter",
        "abandonner",
        "peu importe",
        "oublie",
        "sortir",
        "retour",
        "non merci",
        # Topic switching
        "plutôt",
        "plutot",
        "au lieu",
        "et si",
        "qu'est-ce que",
        "montre-moi",
        "dis-moi",
        "donne-moi",
        "je veux",
        "je voudrais",
        "peux-tu",
        "pourrais-tu",
    ],
}

# Question patterns that indicate new queries (not flow continuations)
QUESTION_PATTERNS = {
    "en": [
        "what",
        "how",
        "show",
        "tell",
        "give",
        "can you",
        "where",
        "when",
        "why",
        "which",
    ],
    "es": [
        "qué",
        "que",
        "cuál",
        "cual",
        "cómo",
        "como",
        "muestra",
        "dime",
        "dame",
        "puedes",
        "dónde",
        "donde",
        "cuándo",
        "cuando",
        "por qué",
        "porque",
    ],
    "pt": [
        "o que",
        "qual",
        "como",
        "mostre",
        "diga",
        "dê",
        "pode",
        "onde",
        "quando",
        "por que",
        "porque",
    ],
    "zh": ["什么", "怎么", "如何", "哪", "为什么", "哪里", "什么时候"],
    "fr": [
        "quoi",
        "quel",
        "quelle",
        "comment",
        "montre",
        "dis",
        "donne",
        "peux",
        "où",
        "ou",
        "quand",
        "pourquoi",
    ],
}

# Map pending_action prefixes to their intent
# e.g., "lending_awaiting_asset" → "lending"
# "swap_awaiting_token" → "swap"
FLOW_TO_INTENT_MAP = {
    "lending": "lending",
    "swap": "swap",
    "buy": "buy",
    "send": "send",
    "portfolio": "portfolio",
    "balance": "balance",
    "activity": "activity",
    "receive": "receive",
    "money_market": "money_market",
}


class FlowCancellationDetector:
    """
    Detects when users want to exit multi-step flows.

    Uses two-tier detection:
    1. Keyword matching - Fast path for explicit cancellation
    2. Intent comparison - Backup path for implicit topic changes
    """

    @staticmethod
    def detect_topic_change(
        content: str,
        pending_action: str,
        current_intent: str,
        language: Literal["en", "es", "pt", "zh", "fr"] = "en",
    ) -> tuple[bool, str]:
        """
        Detect if user wants to exit the current flow.

        Args:
            content: User message content
            pending_action: Current flow state (e.g., "lending_awaiting_asset")
            current_intent: Classified intent from user message
            language: User's language

        Returns:
            Tuple of (should_cancel: bool, reason: str)

        Examples:
            >>> detector = FlowCancellationDetector()
            >>> # User in lending flow asks about price
            >>> detector.detect_topic_change(
            ...     "What's the price of Bitcoin?",
            ...     "lending_awaiting_asset",
            ...     "prediction",
            ...     "en"
            ... )
            (True, "intent_mismatch:lending→prediction")

            >>> # User continues lending flow
            >>> detector.detect_topic_change(
            ...     "USDC",
            ...     "lending_awaiting_asset",
            ...     "lending",
            ...     "en"
            ... )
            (False, "continuing_flow")
        """
        content_lower = content.lower().strip()

        # Fast path: Check for explicit cancellation keywords
        keywords = TOPIC_CHANGE_KEYWORDS.get(language, TOPIC_CHANGE_KEYWORDS["en"])
        for keyword in keywords:
            if keyword in content_lower:
                logger.info(
                    f"Topic change detected via keyword",
                    extra={
                        "keyword": keyword,
                        "language": language,
                        "pending_action": pending_action,
                    },
                )
                return (True, f"keyword_match:{keyword}")

        # Extract expected intent from pending_action
        # e.g., "lending_awaiting_asset" → "lending"
        expected_intent = pending_action.split("_")[0]

        # Check if intent changed
        if current_intent != expected_intent:
            # Additional validation: Check if it's a question (strong signal)
            question_patterns = QUESTION_PATTERNS.get(language, QUESTION_PATTERNS["en"])
            is_question = any(pattern in content_lower for pattern in question_patterns)

            if is_question:
                logger.info(
                    f"Topic change detected via intent mismatch + question pattern",
                    extra={
                        "expected_intent": expected_intent,
                        "current_intent": current_intent,
                        "language": language,
                        "is_question": is_question,
                    },
                )
                return (True, f"intent_mismatch:{expected_intent}→{current_intent}")

            # Intent changed but not a clear question - still likely a topic change
            # Examples: "lending" flow but user says "swap USDC for ETH"
            if (
                current_intent in FLOW_TO_INTENT_MAP
                and current_intent != expected_intent
            ):
                logger.info(
                    f"Topic change detected via different flow intent",
                    extra={
                        "expected_intent": expected_intent,
                        "current_intent": current_intent,
                    },
                )
                return (True, f"flow_change:{expected_intent}→{current_intent}")

        # No cancellation detected - user is continuing the flow
        logger.debug(
            f"Continuing flow",
            extra={
                "pending_action": pending_action,
                "intent": current_intent,
            },
        )
        return (False, "continuing_flow")

    @staticmethod
    def extract_post_cancellation_content(
        content: str,
        keyword: str,
        language: Literal["en", "es", "pt", "zh", "fr"] = "en",
    ) -> str | None:
        """
        Extract content after cancellation keyword for compound intents.

        Handles cases like:
        - "cancel, tell me what is bitcoin" → "tell me what is bitcoin"
        - "stop then show my portfolio" → "show my portfolio"
        - "never mind, how do I buy crypto?" → "how do I buy crypto?"
        - "cancel" → None (no remaining content)

        Args:
            content: Original user message
            keyword: The cancellation keyword that was matched
            language: User's language for separator patterns

        Returns:
            Extracted content after keyword, or None if no meaningful content

        Examples:
            >>> extract_post_cancellation_content("cancel, what is BTC?", "cancel", "en")
            "what is BTC?"

            >>> extract_post_cancellation_content("cancel", "cancel", "en")
            None
        """
        content_lower = content.lower()
        keyword_lower = keyword.lower()

        # Find keyword position
        keyword_pos = content_lower.find(keyword_lower)
        if keyword_pos == -1:
            return None

        # Extract everything after the keyword
        remaining = content[keyword_pos + len(keyword) :].strip()

        if not remaining:
            return None

        # Define separators by language
        # Common patterns: comma, period, semicolon, "then", "and"
        separators = {
            "en": [",", ".", ";", " then ", " and ", " - ", ":", " but ", " though "],
            "es": [
                ",",
                ".",
                ";",
                " entonces ",
                " y ",
                " - ",
                ":",
                " pero ",
                " aunque ",
            ],
            "pt": [",", ".", ";", " então ", " e ", " - ", ":", " mas ", " embora "],
            "zh": ["，", "。", "；", "然后", "和", "-", "：", "但是"],
            "fr": [",", ".", ";", " puis ", " et ", " - ", ":", " mais ", " bien que "],
        }

        # Get separators for language (default to English)
        lang_separators = separators.get(language, separators["en"])

        # Remove leading separator
        for sep in lang_separators:
            if remaining.lower().startswith(sep.strip()):
                remaining = remaining[len(sep) :].strip()
                break

        # Must have meaningful content (> 5 characters)
        # This filters out cases like "cancel." or "cancel, ."
        if len(remaining) <= 5:
            return None

        # Additional validation: must contain at least one letter
        # Filters out cases like "cancel, 123"
        has_letter = any(c.isalpha() for c in remaining)
        if not has_letter:
            return None

        logger.debug(
            f"Extracted post-cancellation content",
            extra={
                "original": content,
                "keyword": keyword,
                "extracted": remaining,
                "language": language,
            },
        )

        return remaining

    @staticmethod
    def clear_flow_metadata(metadata: dict) -> dict:
        """
        Clear all multi-step flow metadata from conversation.

        Args:
            metadata: Conversation metadata dict

        Returns:
            Updated metadata with flow state cleared
        """
        # List of all flow-specific keys to clear
        flow_keys = [
            "pending_action",
            "lending_info",
            "swap_info",
            "buy_info",
            "send_info",
            "portfolio_info",
            "balance_info",
            "activity_info",
            "receive_info",
            "money_market_info",
        ]

        # Create new dict without flow keys
        cleaned_metadata = {k: v for k, v in metadata.items() if k not in flow_keys}

        logger.debug(
            f"Cleared flow metadata",
            extra={
                "removed_keys": [k for k in flow_keys if k in metadata],
            },
        )

        return cleaned_metadata

    @staticmethod
    def get_cancellation_message(
        expected_intent: str,
        new_intent: str,
        language: Literal["en", "es", "pt", "zh", "fr"] = "en",
    ) -> str | None:
        """
        Get optional cancellation notification message.

        Can be used to explicitly tell users the flow was cancelled.
        Returns None if no notification needed (silent cancellation).

        Args:
            expected_intent: The flow that was cancelled
            new_intent: The new intent being processed
            language: User's language

        Returns:
            Cancellation message or None for silent cancellation
        """
        # For now, use silent cancellation (returns None)
        # This can be enabled later if users need explicit feedback

        # Example messages if we want to enable notifications:
        messages = {
            "en": f"✓ Cancelled {expected_intent} flow. Processing your request...",
            "es": f"✓ Flujo de {expected_intent} cancelado. Procesando tu solicitud...",
            "pt": f"✓ Fluxo de {expected_intent} cancelado. Processando sua solicitação...",
            "zh": f"✓ 已取消{expected_intent}流程。正在处理您的请求...",
            "fr": f"✓ Flux {expected_intent} annulé. Traitement de votre demande...",
        }

        # Return None for silent cancellation (preferred UX)
        return None

        # Uncomment to enable explicit notifications:
        # return messages.get(language, messages["en"])
