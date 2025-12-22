"""
Translation-specific domain exceptions with standardized error codes.

This module provides exceptions related to:
- Translation operations (API errors, quota exceeded)
- Language detection and validation
- Translation quality issues
- Cost tracking and limits
"""

from typing import Any
from uuid import UUID

from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode


# =============================================================================
# TRANSLATION ERRORS
# =============================================================================


class TranslationError(ApplicationError):
    """Raised when translation operation fails."""

    def __init__(
        self,
        message: str | None = None,
        source_language: str | None = None,
        target_language: str | None = None,
        provider: str | None = None,
    ) -> None:
        details = {}
        if source_language:
            details["source_language"] = source_language
        if target_language:
            details["target_language"] = target_language
        if provider:
            details["provider"] = provider
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message=message or "Translation failed",
        )


class TranslationAPIError(ApplicationError):
    """Raised when external translation API fails."""

    def __init__(
        self,
        provider: str | None = None,
        status_code: int | None = None,
        error_message: str | None = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        if status_code is not None:
            details["status_code"] = status_code
        if error_message:
            details["error_message"] = error_message
        super().__init__(
            ErrorCode.CHAT_SERVICE_OVERLOADED,
            details=details,
            override_message="Translation API error",
        )


class TranslationQuotaExceededError(ApplicationError):
    """Raised when translation quota/limit is exceeded."""

    def __init__(
        self,
        provider: str | None = None,
        quota_type: str | None = None,
        limit: int | None = None,
        current_usage: int | None = None,
        reset_time: str | None = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        if quota_type:
            details["quota_type"] = quota_type
        if limit is not None:
            details["limit"] = limit
        if current_usage is not None:
            details["current_usage"] = current_usage
        if reset_time:
            details["reset_time"] = reset_time
        super().__init__(
            ErrorCode.CHAT_RATE_LIMIT,
            details=details,
            override_message="Translation quota exceeded",
        )


class LanguageDetectionError(ApplicationError):
    """Raised when language detection fails."""

    def __init__(
        self,
        text_sample: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if text_sample:
            # Truncate for privacy
            details["text_sample"] = text_sample[:50]
        if reason:
            details["reason"] = reason
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message="Failed to detect language",
        )


class UnsupportedLanguageError(ApplicationError):
    """Raised when requested language is not supported."""

    def __init__(
        self,
        language: str | None = None,
        provider: str | None = None,
        supported_languages: list[str] | None = None,
    ) -> None:
        details = {}
        if language:
            details["language"] = language
        if provider:
            details["provider"] = provider
        if supported_languages:
            details["supported_languages_count"] = len(supported_languages)
        super().__init__(
            ErrorCode.CHAT_INVALID_AGENT_TYPE,
            details=details,
            field="language",
            override_message=f"Language '{language}' is not supported",
        )


class InvalidLanguageCodeError(ApplicationError):
    """Raised when invalid language code is provided."""

    def __init__(
        self,
        language_code: str | None = None,
        valid_format: str | None = None,
    ) -> None:
        details = {}
        if language_code:
            details["language_code"] = language_code
        if valid_format:
            details["valid_format"] = valid_format
        super().__init__(
            ErrorCode.CHAT_MESSAGE_EMPTY,
            details=details,
            field="language_code",
            override_message="Invalid language code format",
        )


# =============================================================================
# TRANSLATION QUALITY ERRORS
# =============================================================================


class TranslationQualityError(ApplicationError):
    """Raised when translation quality is below acceptable threshold."""

    def __init__(
        self,
        confidence_score: float | None = None,
        min_threshold: float | None = None,
        source_text: str | None = None,
    ) -> None:
        details = {}
        if confidence_score is not None:
            details["confidence_score"] = confidence_score
        if min_threshold is not None:
            details["min_threshold"] = min_threshold
        if source_text:
            details["text_length"] = len(source_text)
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message="Translation quality below threshold",
        )


class TextTooLongForTranslationError(ApplicationError):
    """Raised when text exceeds translation length limit."""

    def __init__(
        self,
        text_length: int | None = None,
        max_length: int | None = None,
        provider: str | None = None,
    ) -> None:
        details = {}
        if text_length is not None:
            details["text_length"] = text_length
        if max_length is not None:
            details["max_length"] = max_length
        if provider:
            details["provider"] = provider
        super().__init__(
            ErrorCode.CHAT_MESSAGE_TOO_LONG,
            details=details,
            field="text",
            override_message="Text exceeds maximum translation length",
        )


class EmptyTextError(ApplicationError):
    """Raised when attempting to translate empty text."""

    def __init__(self) -> None:
        super().__init__(
            ErrorCode.CHAT_MESSAGE_EMPTY,
            field="text",
            override_message="Cannot translate empty text",
        )


# =============================================================================
# BATCH TRANSLATION ERRORS
# =============================================================================


class BatchTranslationError(ApplicationError):
    """Raised when batch translation fails."""

    def __init__(
        self,
        total_texts: int | None = None,
        failed_count: int | None = None,
        error_message: str | None = None,
    ) -> None:
        details = {}
        if total_texts is not None:
            details["total_texts"] = total_texts
        if failed_count is not None:
            details["failed_count"] = failed_count
        if error_message:
            details["error_message"] = error_message
        super().__init__(
            ErrorCode.CHAT_AGENT_ERROR,
            details=details,
            override_message="Batch translation partially or completely failed",
        )


# =============================================================================
# COST TRACKING ERRORS
# =============================================================================


class TranslationCostLimitExceededError(ApplicationError):
    """Raised when translation cost exceeds budget limit."""

    def __init__(
        self,
        current_cost: float | None = None,
        cost_limit: float | None = None,
        currency: str | None = None,
        period: str | None = None,
    ) -> None:
        details = {}
        if current_cost is not None:
            details["current_cost"] = current_cost
        if cost_limit is not None:
            details["cost_limit"] = cost_limit
        if currency:
            details["currency"] = currency
        if period:
            details["period"] = period
        super().__init__(
            ErrorCode.CHAT_RATE_LIMIT,
            details=details,
            override_message="Translation cost limit exceeded",
        )


# =============================================================================
# GLOSSARY ERRORS
# =============================================================================


class GlossaryNotFoundError(ApplicationError):
    """Raised when requested glossary is not found."""

    def __init__(
        self,
        glossary_id: str | UUID | None = None,
        glossary_name: str | None = None,
        provider: str | None = None,
    ) -> None:
        details = {}
        if glossary_id:
            details["glossary_id"] = str(glossary_id)
        if glossary_name:
            details["glossary_name"] = glossary_name
        if provider:
            details["provider"] = provider
        super().__init__(
            ErrorCode.CHAT_CONVERSATION_NOT_FOUND,
            details=details,
            override_message="Translation glossary not found",
        )


class InvalidGlossaryError(ApplicationError):
    """Raised when glossary format or content is invalid."""

    def __init__(
        self,
        glossary_id: str | UUID | None = None,
        validation_errors: list[str] | None = None,
    ) -> None:
        details = {}
        if glossary_id:
            details["glossary_id"] = str(glossary_id)
        if validation_errors:
            details["validation_errors"] = validation_errors
        super().__init__(
            ErrorCode.CHAT_MESSAGE_EMPTY,
            details=details,
            override_message="Invalid glossary format or content",
        )


# =============================================================================
# FORMALITY ERRORS
# =============================================================================


class UnsupportedFormalityError(ApplicationError):
    """Raised when formality level is not supported for language pair."""

    def __init__(
        self,
        formality: str | None = None,
        source_language: str | None = None,
        target_language: str | None = None,
        provider: str | None = None,
    ) -> None:
        details = {}
        if formality:
            details["formality"] = formality
        if source_language:
            details["source_language"] = source_language
        if target_language:
            details["target_language"] = target_language
        if provider:
            details["provider"] = provider
        super().__init__(
            ErrorCode.CHAT_INVALID_AGENT_TYPE,
            details=details,
            override_message="Formality not supported for this language pair",
        )
