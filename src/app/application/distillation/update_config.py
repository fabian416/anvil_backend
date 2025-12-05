"""
Update distillation config interactor.
"""
from typing import Optional
from dataclasses import dataclass

from app.setup.config.distillation import DistillationSettings


@dataclass
class DistillationConfig:
    """Distillation configuration data."""
    enabled: bool
    provider: str
    fallback_provider: str
    temperature: float
    max_tokens: int
    timeout_seconds: float
    fail_open: bool


class UpdateDistillationConfig:
    """
    Update distillation configuration interactor.
    
    Updates runtime configuration for distillation system.
    
    Note: This is a simplified implementation. In production,
    you would persist changes to a database or config file
    and hot-reload the configuration.
    """
    
    def __init__(self, settings: DistillationSettings):
        """Initialize interactor."""
        self._settings = settings
    
    async def execute(
        self,
        enabled: Optional[bool] = None,
        provider: Optional[str] = None,
        fallback_provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
        fail_open: Optional[bool] = None,
    ) -> DistillationConfig:
        """
        Update distillation configuration.
        
        Args:
            enabled: Enable/disable distillation
            provider: Primary provider name
            fallback_provider: Fallback provider name
            temperature: LLM temperature
            max_tokens: Maximum tokens
            timeout_seconds: Request timeout
            fail_open: Fail-open mode
        
        Returns:
            Updated configuration
        """
        # Update settings (in-memory for now)
        if enabled is not None:
            self._settings.enabled = enabled
        if provider is not None:
            self._settings.provider = provider
        if fallback_provider is not None:
            self._settings.fallback_provider = fallback_provider
        if temperature is not None:
            self._settings.temperature = temperature
        if max_tokens is not None:
            self._settings.max_tokens = max_tokens
        if timeout_seconds is not None:
            self._settings.timeout_seconds = timeout_seconds
        if fail_open is not None:
            self._settings.fail_open = fail_open
        
        # Return updated config
        return DistillationConfig(
            enabled=self._settings.enabled,
            provider=self._settings.provider,
            fallback_provider=self._settings.fallback_provider,
            temperature=self._settings.temperature,
            max_tokens=self._settings.max_tokens,
            timeout_seconds=self._settings.timeout_seconds,
            fail_open=self._settings.fail_open,
        )
