"""
Translation Providers for Dependency Injection.

Provides configured translation services:
- DeepLTranslationAdapter for high-quality translation
- GoogleTranslateAdapter for comprehensive language support
- Fallback chain support
"""

import logging

from dishka import Provider, Scope, provide

from app.domain.ports.translation_adapter import TranslationAdapter
from app.infrastructure.adapters.external.deepl_translation_adapter import (
    DeepLTranslationAdapter,
    FormalityLevel,
)
from app.infrastructure.adapters.external.google_translate_adapter import (
    GoogleTranslateAdapter,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache
from app.setup.config.settings import AppSettings
from app.setup.config.translation import TranslationProvider

logger = logging.getLogger(__name__)


class TranslationAdapterProvider(Provider):
    """Provider for translation adapter services."""

    scope = Scope.APP

    @provide
    def provide_translation_adapter(
        self,
        cache: ExternalAPICache,
        settings: AppSettings,
    ) -> TranslationAdapter:
        """
        Provide TranslationAdapter implementation based on configuration.

        Returns the appropriate adapter based on settings.translation.default_provider:
        - "deepl": DeepL adapter (high quality, 30+ languages, formality support)
        - "google": Google Cloud Translation (100+ languages, HTML support)
        - "fallback": Try DeepL first, fall back to Google if unavailable

        Args:
            cache: External API cache for caching translations
            settings: Application settings with translation configuration

        Returns:
            Configured TranslationAdapter instance

        Raises:
            ValueError: If required API keys are missing for selected provider
        """
        translation_config = settings.translation

        if not translation_config.enabled:
            logger.warning("Translation features are disabled in configuration")
            # Return a dummy adapter or raise an error
            raise ValueError("Translation features are disabled")

        provider = translation_config.default_provider

        # DeepL adapter
        if provider == TranslationProvider.DEEPL:
            if not translation_config.deepl_api_key:
                raise ValueError(
                    "DeepL API key is required when using DeepL as translation provider. "
                    "Set 'translation.deepl_api_key' in configuration."
                )

            # Convert formality string to enum
            formality = FormalityLevel.DEFAULT
            try:
                formality = FormalityLevel(translation_config.deepl_formality)
            except ValueError:
                logger.warning(
                    f"Invalid formality level '{translation_config.deepl_formality}', "
                    f"using default"
                )

            logger.info("Initializing DeepL translation adapter")
            return DeepLTranslationAdapter(
                api_key=translation_config.deepl_api_key,
                cache=cache,
                formality_level=formality,
                enable_cost_tracking=translation_config.enable_cost_tracking,
                cache_ttl=translation_config.cache_ttl,
            )

        # Google Cloud Translation adapter
        if provider == TranslationProvider.GOOGLE:
            if not translation_config.google_project_id:
                raise ValueError(
                    "Google Cloud project ID is required when using Google as translation provider. "
                    "Set 'translation.google_project_id' in configuration."
                )

            logger.info("Initializing Google Cloud Translation adapter")
            return GoogleTranslateAdapter(
                project_id=translation_config.google_project_id,
                location=translation_config.google_location,
                cache=cache,
                credentials_path=translation_config.google_credentials_path,
                enable_html_support=translation_config.google_enable_html,
                enable_cost_tracking=translation_config.enable_cost_tracking,
                cache_ttl=translation_config.cache_ttl,
            )

        # Fallback mode (not implemented in this version, but can be added)
        if provider == TranslationProvider.FALLBACK:
            logger.info(
                "Fallback mode requested, using DeepL with Google fallback (not implemented yet)"
            )
            # For now, just use DeepL
            if translation_config.deepl_api_key:
                formality = FormalityLevel.DEFAULT
                try:
                    formality = FormalityLevel(translation_config.deepl_formality)
                except ValueError:
                    pass

                return DeepLTranslationAdapter(
                    api_key=translation_config.deepl_api_key,
                    cache=cache,
                    formality_level=formality,
                    enable_cost_tracking=translation_config.enable_cost_tracking,
                    cache_ttl=translation_config.cache_ttl,
                )
            elif translation_config.google_project_id:
                return GoogleTranslateAdapter(
                    project_id=translation_config.google_project_id,
                    location=translation_config.google_location,
                    cache=cache,
                    credentials_path=translation_config.google_credentials_path,
                    enable_html_support=translation_config.google_enable_html,
                    enable_cost_tracking=translation_config.enable_cost_tracking,
                    cache_ttl=translation_config.cache_ttl,
                )
            else:
                raise ValueError(
                    "Fallback mode requires either DeepL or Google Cloud Translation API keys"
                )

        raise ValueError(f"Unknown translation provider: {provider}")
