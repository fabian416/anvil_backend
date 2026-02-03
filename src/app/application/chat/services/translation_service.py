"""
Translation service for multi-language chat support.

Natural language translation with DeFi technical term preservation.
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from datetime import datetime

from app.domain.entities.chat.message import Message
from app.domain.entities.chat.conversation import Conversation
from app.domain.value_objects.chat.translation import (
    SupportedLanguage,
    TranslationMode,
    TranslationResult,
    PreservedTermsConfig,
    TranslationQuality,
    UserLanguagePreference,
)
from app.domain.ports.translation_adapter import TranslationAdapter
from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.domain.exceptions.chat import (
    TranslationError,
    LanguageNotSupportedError,
    ConversationNotFoundError,
)

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Multi-language translation service for chat conversations.

    Features:
    - Natural language translation commands
    - Real-time translation in shared conversations
    - Technical term preservation (DeFi protocols, tokens)
    - Multiple display modes (side-by-side, inline, popup)
    - Translation quality scoring
    - Bilingual mode for learning
    """

    def __init__(
        self,
        translation_adapter: TranslationAdapter,
        conversation_repository: ConversationRepository,
    ):
        """
        Initialize translation service.

        Args:
            translation_adapter: Translation API adapter
            conversation_repository: Repository for conversations
        """
        self._translator = translation_adapter
        self._repository = conversation_repository

    async def process_translation_command(
        self,
        user_id: UUID,
        command: str,
        conversation_id: Optional[UUID] = None,
    ) -> Tuple[bool, str]:
        """
        Process natural language translation command.

        Commands:
        - "Translate this conversation to Spanish"
        - "Enable auto-translate to French"
        - "Show me this in side-by-side mode with German"
        - "Translate the last 5 messages to Japanese"
        - "Switch to bilingual mode"

        Args:
            user_id: User identifier
            command: Natural language command
            conversation_id: Conversation context

        Returns:
            Tuple of (success, response_message)
        """
        command_lower = command.lower()

        try:
            # Detect target language
            target_language = self._extract_language(command_lower)
            if not target_language:
                return False, (
                    "❌ Could not detect target language. "
                    "Please specify a language (e.g., 'Spanish', 'French', 'Japanese')."
                )

            # Check if language is supported
            if not await self._translator.is_language_supported(target_language):
                return False, (
                    f"❌ {target_language.value} is not currently supported. "
                    f"Supported languages: {await self._get_supported_languages_list()}"
                )

            # Extract translation mode
            mode = self._extract_translation_mode(command_lower)

            # Translate conversation
            if conversation_id and any(
                keyword in command_lower
                for keyword in ["conversation", "entire", "whole", "all messages"]
            ):
                return await self._translate_conversation(
                    conversation_id, user_id, target_language, mode
                )

            # Translate last N messages
            if match := re.search(r"last (\d+) messages?", command_lower):
                message_count = int(match.group(1))
                return await self._translate_recent_messages(
                    conversation_id, user_id, target_language, mode, message_count
                )

            # Enable auto-translate
            if any(
                keyword in command_lower
                for keyword in ["enable auto", "turn on auto", "activate auto"]
            ):
                return await self._enable_auto_translate(user_id, target_language, mode)

            # Disable auto-translate
            if any(
                keyword in command_lower
                for keyword in ["disable auto", "turn off auto", "deactivate auto"]
            ):
                return await self._disable_auto_translate(user_id)

            # Default: translate current context
            return False, (
                "Please specify what to translate:\n"
                "  • 'Translate this conversation to [language]'\n"
                "  • 'Translate the last N messages to [language]'\n"
                "  • 'Enable auto-translate to [language]'"
            )

        except Exception as e:
            logger.error(f"Translation command failed: {e}", exc_info=True)
            return False, f"❌ Translation failed: {str(e)}"

    async def translate_message(
        self,
        message: Message,
        target_language: SupportedLanguage,
        preserve_terms: Optional[PreservedTermsConfig] = None,
    ) -> TranslationResult:
        """
        Translate a single message.

        Args:
            message: Message to translate
            target_language: Target language
            preserve_terms: Terms to preserve during translation

        Returns:
            TranslationResult
        """
        if preserve_terms is None:
            preserve_terms = PreservedTermsConfig()

        # Pre-process: protect technical terms
        protected_text, term_map = self._protect_terms(message.content, preserve_terms)

        # Translate
        result = await self._translator.translate_text(
            text=protected_text,
            target_language=target_language,
            source_language=None,  # Auto-detect
            preserve_terms=preserve_terms,
        )

        # Post-process: restore technical terms
        final_text = self._restore_terms(result.translated_text, term_map)

        return TranslationResult(
            original_text=message.content,
            translated_text=final_text,
            source_language=result.source_language,
            target_language=target_language,
            confidence_score=result.confidence_score,
            detected_language=result.detected_language,
            preserved_terms=list(term_map.values()),
            translation_time_ms=result.translation_time_ms,
        )

    async def translate_conversation_realtime(
        self,
        conversation: Conversation,
        user_language_preferences: Dict[UUID, SupportedLanguage],
    ) -> Dict[UUID, List[TranslationResult]]:
        """
        Translate conversation for multiple users in real-time.

        For shared conversations with users speaking different languages,
        each user sees messages in their preferred language.

        Args:
            conversation: Conversation to translate
            user_language_preferences: Map of user_id to preferred language

        Returns:
            Dictionary mapping user_id to list of translation results
        """
        translations: Dict[UUID, List[TranslationResult]] = {
            user_id: [] for user_id in user_language_preferences
        }

        preserve_terms = PreservedTermsConfig()

        for message in conversation.messages:
            for user_id, target_language in user_language_preferences.items():
                # Skip translation if message is already in target language
                detected_lang = await self._translator.detect_language(message.content)
                if detected_lang == target_language:
                    continue

                # Translate for this user
                result = await self.translate_message(
                    message, target_language, preserve_terms
                )
                translations[user_id].append(result)

        return translations

    async def get_translation_quality_score(
        self, translation_result: TranslationResult
    ) -> TranslationQuality:
        """
        Evaluate translation quality using multiple metrics.

        Args:
            translation_result: Translation to evaluate

        Returns:
            TranslationQuality with scores
        """
        # Placeholder scoring logic (in production, use LLM-based evaluation)

        # Fluency: How natural the translation reads
        fluency = self._evaluate_fluency(translation_result.translated_text)

        # Adequacy: How well meaning is preserved
        adequacy = self._evaluate_adequacy(
            translation_result.original_text, translation_result.translated_text
        )

        # Terminology: How well technical terms are preserved
        terminology = self._evaluate_terminology_preservation(translation_result)

        # Context: How well context is maintained
        context = translation_result.confidence_score

        return TranslationQuality.from_scores(
            fluency=fluency,
            adequacy=adequacy,
            terminology=terminology,
            context=context,
        )

    def format_bilingual_message(
        self,
        translation_result: TranslationResult,
        mode: TranslationMode = TranslationMode.SIDE_BY_SIDE,
    ) -> str:
        """
        Format translated message for display.

        Args:
            translation_result: Translation result
            mode: Display mode

        Returns:
            Formatted markdown string
        """
        if mode == TranslationMode.REPLACE:
            return translation_result.translated_text

        elif mode == TranslationMode.SIDE_BY_SIDE:
            return (
                f"┌─ Original ({translation_result.source_language.value}) ─┐\n"
                f"{translation_result.original_text}\n"
                f"\n"
                f"└─ Translation ({translation_result.target_language.value}) ─┘\n"
                f"{translation_result.translated_text}\n"
                f"\n"
                f"_Confidence: {translation_result.confidence_score:.0%}_"
            )

        elif mode == TranslationMode.INLINE:
            return (
                f"{translation_result.original_text}\n"
                f"\n"
                f"_→ {translation_result.target_language.value}: "
                f"{translation_result.translated_text}_"
            )

        elif mode == TranslationMode.POPUP:
            # Markdown doesn't support hover, so we show it as a footnote
            return (
                f"{translation_result.original_text}[^translation]\n"
                f"\n"
                f"[^translation]: {translation_result.target_language.value}: "
                f"{translation_result.translated_text}"
            )

        return translation_result.translated_text

    # Private helper methods

    def _extract_language(self, command: str) -> Optional[SupportedLanguage]:
        """Extract target language from command."""
        language_map = {
            "spanish": SupportedLanguage.SPANISH,
            "español": SupportedLanguage.SPANISH,
            "french": SupportedLanguage.FRENCH,
            "français": SupportedLanguage.FRENCH,
            "german": SupportedLanguage.GERMAN,
            "deutsch": SupportedLanguage.GERMAN,
            "italian": SupportedLanguage.ITALIAN,
            "italiano": SupportedLanguage.ITALIAN,
            "portuguese": SupportedLanguage.PORTUGUESE,
            "português": SupportedLanguage.PORTUGUESE,
            "japanese": SupportedLanguage.JAPANESE,
            "日本語": SupportedLanguage.JAPANESE,
            "korean": SupportedLanguage.KOREAN,
            "한국어": SupportedLanguage.KOREAN,
            "chinese": SupportedLanguage.CHINESE_SIMPLIFIED,
            "中文": SupportedLanguage.CHINESE_SIMPLIFIED,
            "mandarin": SupportedLanguage.CHINESE_SIMPLIFIED,
            "traditional chinese": SupportedLanguage.CHINESE_TRADITIONAL,
            "繁體中文": SupportedLanguage.CHINESE_TRADITIONAL,
            "russian": SupportedLanguage.RUSSIAN,
            "русский": SupportedLanguage.RUSSIAN,
            "arabic": SupportedLanguage.ARABIC,
            "العربية": SupportedLanguage.ARABIC,
            "english": SupportedLanguage.ENGLISH,
        }

        for keyword, language in language_map.items():
            if keyword in command:
                return language

        return None

    def _extract_translation_mode(self, command: str) -> TranslationMode:
        """Extract translation display mode from command."""
        if any(
            keyword in command for keyword in ["side by side", "side-by-side", "both"]
        ):
            return TranslationMode.SIDE_BY_SIDE
        elif any(keyword in command for keyword in ["inline", "below"]):
            return TranslationMode.INLINE
        elif any(keyword in command for keyword in ["popup", "hover"]):
            return TranslationMode.POPUP
        elif any(keyword in command for keyword in ["replace", "only"]):
            return TranslationMode.REPLACE

        return TranslationMode.SIDE_BY_SIDE  # Default

    def _protect_terms(
        self, text: str, preserve_config: PreservedTermsConfig
    ) -> Tuple[str, Dict[str, str]]:
        """
        Protect technical terms from translation by replacing with placeholders.

        Args:
            text: Original text
            preserve_config: Configuration for term preservation

        Returns:
            Tuple of (protected_text, term_map)
        """
        term_map: Dict[str, str] = {}
        protected_text = text

        # Protect protocols
        for protocol in preserve_config.protocols:
            if protocol in text:
                placeholder = f"__PROTOCOL_{len(term_map)}__"
                term_map[placeholder] = protocol
                protected_text = protected_text.replace(protocol, placeholder)

        # Protect tokens
        for token in preserve_config.tokens:
            # Use word boundaries to avoid partial matches
            pattern = rf"\b{re.escape(token)}\b"
            if re.search(pattern, text, re.IGNORECASE):
                placeholder = f"__TOKEN_{len(term_map)}__"
                term_map[placeholder] = token
                protected_text = re.sub(
                    pattern, placeholder, protected_text, flags=re.IGNORECASE
                )

        # Protect wallet addresses
        if preserve_config.preserve_addresses:
            eth_pattern = r"\b0x[a-fA-F0-9]{40}\b"
            for match in re.finditer(eth_pattern, text):
                address = match.group(0)
                placeholder = f"__ADDRESS_{len(term_map)}__"
                term_map[placeholder] = address
                protected_text = protected_text.replace(address, placeholder)

        # Protect transaction hashes
        if preserve_config.preserve_tx_hashes:
            tx_pattern = r"\b0x[a-fA-F0-9]{64}\b"
            for match in re.finditer(tx_pattern, text):
                tx_hash = match.group(0)
                placeholder = f"__TX_{len(term_map)}__"
                term_map[placeholder] = tx_hash
                protected_text = protected_text.replace(tx_hash, placeholder)

        # Protect code blocks
        if preserve_config.preserve_code:
            code_pattern = r"`([^`]+)`"
            for match in re.finditer(code_pattern, text):
                code = match.group(1)
                placeholder = f"__CODE_{len(term_map)}__"
                term_map[placeholder] = code
                protected_text = protected_text.replace(f"`{code}`", placeholder)

        return protected_text, term_map

    def _restore_terms(self, translated_text: str, term_map: Dict[str, str]) -> str:
        """
        Restore protected technical terms after translation.

        Args:
            translated_text: Translated text with placeholders
            term_map: Map of placeholders to original terms

        Returns:
            Text with restored terms
        """
        restored_text = translated_text

        for placeholder, original_term in term_map.items():
            restored_text = restored_text.replace(placeholder, original_term)

        return restored_text

    async def _translate_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
        target_language: SupportedLanguage,
        mode: TranslationMode,
    ) -> Tuple[bool, str]:
        """Translate entire conversation."""
        conversation = await self._repository.get_by_id(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id=conversation_id)

        preserve_terms = PreservedTermsConfig()
        translations: List[str] = []

        for message in conversation.messages:
            result = await self.translate_message(
                message, target_language, preserve_terms
            )
            formatted = self.format_bilingual_message(result, mode)
            translations.append(
                f"**{message.role.value}** ({message.timestamp.strftime('%H:%M')}):\n{formatted}"
            )

        response = (
            f"✅ Translated conversation to {target_language.value}\n\n"
            + "\n\n".join(translations)
        )

        return True, response

    async def _translate_recent_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        target_language: SupportedLanguage,
        mode: TranslationMode,
        count: int,
    ) -> Tuple[bool, str]:
        """Translate last N messages."""
        conversation = await self._repository.get_by_id(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id=conversation_id)

        preserve_terms = PreservedTermsConfig()
        recent_messages = conversation.messages[-count:]
        translations: List[str] = []

        for message in recent_messages:
            result = await self.translate_message(
                message, target_language, preserve_terms
            )
            formatted = self.format_bilingual_message(result, mode)
            translations.append(f"**{message.role.value}**:\n{formatted}")

        response = (
            f"✅ Translated last {count} messages to {target_language.value}\n\n"
            + "\n\n".join(translations)
        )

        return True, response

    async def _enable_auto_translate(
        self, user_id: UUID, target_language: SupportedLanguage, mode: TranslationMode
    ) -> Tuple[bool, str]:
        """Enable automatic translation for user."""
        # TODO: Save user preference to repository
        return True, (
            f"✅ Auto-translate enabled\n"
            f"  • Language: {target_language.value}\n"
            f"  • Mode: {mode.value}\n"
            f"\nAll future messages will be automatically translated."
        )

    async def _disable_auto_translate(self, user_id: UUID) -> Tuple[bool, str]:
        """Disable automatic translation for user."""
        # TODO: Update user preference in repository
        return True, "✅ Auto-translate disabled"

    async def _get_supported_languages_list(self) -> str:
        """Get formatted list of supported languages."""
        languages = await self._translator.get_supported_languages()
        return ", ".join(lang.value for lang in languages)

    def _evaluate_fluency(self, text: str) -> float:
        """Evaluate translation fluency (0.0 to 1.0)."""
        # Placeholder: In production, use LLM-based evaluation
        # Check for basic fluency indicators
        score = 0.85

        # Penalize if text is too short
        if len(text) < 10:
            score -= 0.1

        # Penalize if excessive punctuation
        punctuation_ratio = sum(c in ".,;:!?" for c in text) / max(len(text), 1)
        if punctuation_ratio > 0.15:
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _evaluate_adequacy(self, original: str, translated: str) -> float:
        """Evaluate adequacy (meaning preservation)."""
        # Placeholder: In production, use semantic similarity models
        # Simple length-based heuristic
        length_ratio = len(translated) / max(len(original), 1)

        if 0.7 <= length_ratio <= 1.5:
            return 0.9
        elif 0.5 <= length_ratio <= 2.0:
            return 0.75
        else:
            return 0.6

    def _evaluate_terminology_preservation(
        self, translation_result: TranslationResult
    ) -> float:
        """Evaluate how well technical terms were preserved."""
        if not translation_result.preserved_terms:
            return 1.0  # No terms to preserve

        # Check if preserved terms appear in translated text
        preserved_count = sum(
            1
            for term in translation_result.preserved_terms
            if term in translation_result.translated_text
        )

        return preserved_count / len(translation_result.preserved_terms)
