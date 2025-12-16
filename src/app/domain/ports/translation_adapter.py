"""
Translation adapter port.

Domain-defined interface for external translation services.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from app.domain.value_objects.chat.translation import (
    SupportedLanguage,
    TranslationResult,
    PreservedTermsConfig,
)


class TranslationAdapter(ABC):
    """
    Port for external translation services.

    Abstracts integration with translation APIs (Google Cloud Translation,
    AWS Translate, DeepL, etc.) for language-agnostic business logic.
    """

    @abstractmethod
    async def translate_text(
        self,
        text: str,
        target_language: SupportedLanguage,
        source_language: Optional[SupportedLanguage] = None,
        preserve_terms: Optional[PreservedTermsConfig] = None,
    ) -> TranslationResult:
        """
        Translate text to target language.

        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (auto-detect if None)
            preserve_terms: Terms to preserve during translation

        Returns:
            TranslationResult with translation and metadata

        Raises:
            TranslationError: If translation fails
        """
        pass

    @abstractmethod
    async def translate_batch(
        self,
        texts: List[str],
        target_language: SupportedLanguage,
        source_language: Optional[SupportedLanguage] = None,
        preserve_terms: Optional[PreservedTermsConfig] = None,
    ) -> List[TranslationResult]:
        """
        Translate multiple texts in batch.

        Args:
            texts: Texts to translate
            target_language: Target language
            source_language: Source language (auto-detect if None)
            preserve_terms: Terms to preserve during translation

        Returns:
            List of TranslationResult

        Raises:
            TranslationError: If translation fails
        """
        pass

    @abstractmethod
    async def detect_language(self, text: str) -> SupportedLanguage:
        """
        Detect the language of text.

        Args:
            text: Text to analyze

        Returns:
            Detected SupportedLanguage

        Raises:
            LanguageDetectionError: If detection fails
        """
        pass

    @abstractmethod
    async def get_supported_languages(self) -> List[SupportedLanguage]:
        """
        Get list of supported languages.

        Returns:
            List of supported languages
        """
        pass

    @abstractmethod
    async def is_language_supported(self, language: SupportedLanguage) -> bool:
        """
        Check if language is supported.

        Args:
            language: Language to check

        Returns:
            True if supported, False otherwise
        """
        pass
