"""
Translation service configuration.

Configuration for DeepL and Google Cloud Translation services.
"""

from enum import Enum

from pydantic import BaseModel, Field


class TranslationProvider(str, Enum):
    """Available translation providers."""

    DEEPL = "deepl"
    GOOGLE = "google"
    FALLBACK = "fallback"  # Fallback chain: DeepL -> Google


class TranslationSettings(BaseModel):
    """
    Translation service configuration.

    Controls translation provider selection, API keys, and behavior.
    """

    # Provider selection
    default_provider: TranslationProvider = Field(
        default=TranslationProvider.DEEPL,
        description="Default translation provider (deepl, google, or fallback)",
    )

    # DeepL configuration
    deepl_api_key: str | None = Field(
        default=None,
        description="DeepL API authentication key",
    )

    deepl_formality: str = Field(
        default="default",
        description="Default formality level (default, more, less, prefer_more, prefer_less)",
    )

    # Google Cloud Translation configuration
    google_project_id: str | None = Field(
        default=None,
        description="Google Cloud project ID",
    )

    google_location: str = Field(
        default="global",
        description="Google Cloud Translation location (global, us-central1, etc.)",
    )

    google_credentials_path: str | None = Field(
        default=None,
        description="Path to Google Cloud service account credentials JSON",
    )

    google_enable_html: bool = Field(
        default=True,
        description="Enable HTML translation support in Google Translate",
    )

    # Cache configuration
    cache_ttl: int = Field(
        default=300,
        description="Translation cache TTL in seconds",
        ge=0,
    )

    # Cost tracking
    enable_cost_tracking: bool = Field(
        default=True,
        description="Track translation costs and usage",
    )

    cost_limit_usd: float | None = Field(
        default=None,
        description="Monthly cost limit in USD (None = no limit)",
        ge=0,
    )

    # Quality settings
    min_confidence_score: float = Field(
        default=0.7,
        description="Minimum acceptable translation confidence score",
        ge=0.0,
        le=1.0,
    )

    # Feature flags
    enabled: bool = Field(
        default=True,
        description="Master switch for translation features",
    )

    auto_detect_language: bool = Field(
        default=True,
        description="Enable automatic language detection when source not specified",
    )

    preserve_technical_terms: bool = Field(
        default=True,
        description="Preserve DeFi protocols, tokens, and technical terms",
    )
