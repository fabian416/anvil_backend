"""
Distillation configuration settings.

Provides granular control over request distillation system.
"""

from typing import Optional
from pydantic import BaseModel, Field


class DistillationRetrySettings(BaseModel):
    """Retry settings for distillation providers."""

    enabled: bool = Field(
        default=True,
        description="Enable retry for distillation requests",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts",
    )
    initial_backoff_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Initial backoff delay in seconds",
    )
    max_backoff_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=60.0,
        description="Maximum backoff delay in seconds",
    )
    exponential_base: float = Field(
        default=2.0,
        ge=1.5,
        le=3.0,
        description="Exponential backoff multiplier",
    )


class VertexAISettings(BaseModel):
    """Vertex AI provider settings."""

    project_id: str = Field(
        default="",
        description="Google Cloud project ID",
    )
    project_number: Optional[str] = Field(
        default=None,
        description="Google Cloud project number",
    )
    location: str = Field(
        default="us-central1",
        description="Google Cloud location/region",
    )
    credentials_path: Optional[str] = Field(
        default=None,
        description="Path to service account credentials JSON file",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Google Cloud API Key (alternative to service account)",
    )
    model: str = Field(
        default="meta-llama/Meta-Llama-3.1-70B-Instruct",
        description="Vertex AI model to use",
    )


class DeepInfraSettings(BaseModel):
    """DeepInfra provider settings."""

    api_key: str = Field(
        default="",
        description="DeepInfra API key",
    )
    model: str = Field(
        default="meta-llama/Llama-3.2-3B-Instruct",
        description="DeepInfra model to use",
    )
    base_url: str = Field(
        default="https://api.deepinfra.com/v1/openai",
        description="DeepInfra API base URL",
    )


class DistillationTelemetrySettings(BaseModel):
    """Telemetry settings for distillation."""

    enabled: bool = Field(
        default=True,
        description="Enable telemetry collection",
    )
    async_recording: bool = Field(
        default=True,
        description="Record telemetry asynchronously",
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Batch size for telemetry recording",
    )
    flush_interval_seconds: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Interval for flushing telemetry batches",
    )


class DistillationSettings(BaseModel):
    """
    Main distillation system settings.

    Controls all aspects of the request distillation system.
    """

    enabled: bool = Field(
        default=True,
        description="Master switch for distillation system (env: DISTILLATION_ENABLED)",
    )
    provider: str = Field(
        default="vertex_ai",
        description="Primary distillation provider (vertex_ai | deepinfra)",
    )
    fallback_provider: Optional[str] = Field(
        default="deepinfra",
        description="Fallback provider if primary fails",
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for LLM generation",
    )
    max_tokens: int = Field(
        default=200,
        ge=50,
        le=1000,
        description="Maximum tokens in distillation response",
    )
    timeout_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Timeout for distillation request",
    )
    fail_open: bool = Field(
        default=True,
        description="Allow requests if distillation fails",
    )

    # Provider-specific settings
    vertex_ai: VertexAISettings = Field(
        default_factory=VertexAISettings,
        description="Vertex AI provider configuration",
    )
    deepinfra: DeepInfraSettings = Field(
        default_factory=DeepInfraSettings,
        description="DeepInfra provider configuration",
    )

    # Retry settings
    retry: DistillationRetrySettings = Field(
        default_factory=DistillationRetrySettings,
        description="Retry configuration for providers",
    )

    # Telemetry settings
    telemetry: DistillationTelemetrySettings = Field(
        default_factory=DistillationTelemetrySettings,
        description="Telemetry configuration",
    )

    # Rate limiting (requests per minute)
    rate_limit_per_user: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Max distillation requests per user per minute",
    )
    rate_limit_global: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Max distillation requests globally per minute",
    )


class DistillationDisabledError(Exception):
    """Raised when attempting to use disabled distillation system."""

    def __init__(self, message: str = "Distillation system is disabled"):
        self.message = message
        super().__init__(self.message)
