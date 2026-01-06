"""
LLM Orchestration Configuration.

Configuration for multi-provider LLM orchestration system.
"""

from pydantic import BaseModel, Field
from typing import Optional


class VertexAIConfig(BaseModel):
    """Vertex AI configuration."""

    project_id: str = Field(..., description="GCP project ID")
    location: str = Field(default="us-central1", description="GCP region")
    credentials_path: Optional[str] = Field(
        default=None, description="Path to service account JSON"
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for Vertex AI (alternative to credentials)"
    )


class DeepInfraConfig(BaseModel):
    """DeepInfra configuration."""

    api_key: str = Field(..., description="DeepInfra API key")
    base_url: str = Field(
        default="https://api.deepinfra.com/v1/openai",
        description="API base URL",
    )


class BedrockConfig(BaseModel):
    """AWS Bedrock configuration."""

    region: str = Field(default="us-east-1", description="AWS region")
    aws_access_key_id: Optional[str] = Field(
        default=None, description="AWS access key"
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None, description="AWS secret key"
    )


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""

    api_key: str = Field(..., description="OpenAI API key")
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="API base URL",
    )
    organization: Optional[str] = Field(
        default=None, description="OpenAI organization ID"
    )
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class AnthropicConfig(BaseModel):
    """Anthropic configuration."""

    api_key: str = Field(..., description="Anthropic API key")
    base_url: str = Field(
        default="https://api.anthropic.com/v1",
        description="API base URL",
    )
    anthropic_version: str = Field(
        default="2023-06-01",
        description="API version header",
    )
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class OrchestratorConfig(BaseModel):
    """LLM Orchestrator configuration."""

    # Retry settings
    max_retries_per_provider: int = Field(
        default=2, description="Max retries per provider"
    )
    max_total_retries: int = Field(default=6, description="Max total retries")
    initial_delay_ms: int = Field(
        default=100, description="Initial retry delay (ms)"
    )
    max_delay_ms: int = Field(default=5000, description="Max retry delay (ms)")
    backoff_multiplier: float = Field(default=2.0, description="Backoff multiplier")
    jitter: bool = Field(default=True, description="Add jitter to retry delays")

    # Timeout settings
    timeout_per_attempt_ms: int = Field(
        default=30000, description="Timeout per attempt (ms)"
    )
    total_timeout_ms: int = Field(
        default=120000, description="Total request timeout (ms)"
    )
    streaming_idle_timeout_ms: int = Field(
        default=10000, description="Streaming idle timeout (ms)"
    )

    # Feature flags
    enable_caching: bool = Field(default=True, description="Enable response caching")
    enable_streaming: bool = Field(default=True, description="Enable streaming")
    enable_cost_tracking: bool = Field(
        default=True, description="Enable cost tracking"
    )
    enable_ranking: bool = Field(default=True, description="Enable adaptive ranking")

    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = Field(
        default=5, description="Failures before circuit opens"
    )
    circuit_breaker_success_threshold: int = Field(
        default=3, description="Successes to close circuit"
    )
    circuit_breaker_timeout_seconds: int = Field(
        default=60, description="Timeout before half-open"
    )

    # Failover settings
    enable_cost_fallback: bool = Field(
        default=True, description="Use cheaper models on fallback"
    )
    primary_chat_provider: str = Field(
        default="vertex_ai", description="Primary chat provider (vertex_ai, deepinfra, or anthropic)"
    )


class LLMOrchestrationConfig(BaseModel):
    """Complete LLM orchestration configuration."""

    vertex_ai: VertexAIConfig
    deepinfra: DeepInfraConfig
    bedrock: BedrockConfig
    openai: Optional[OpenAIConfig] = None
    anthropic: Optional[AnthropicConfig] = None
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)


# ============================================================================
# CONFIGURATION LOADING
# ============================================================================


def load_llm_orchestration_config() -> LLMOrchestrationConfig:
    """
    Load LLM orchestration configuration from environment.

    Returns:
        LLM orchestration configuration
    """
    import os

    # OpenAI removed - not loading OpenAI config
    # openai_config = None
    # if os.getenv("OPENAI_API_KEY"):
    #     openai_config = OpenAIConfig(...)
    openai_config = None

    # Load Anthropic config if API key is present
    anthropic_config = None
    if os.getenv("ANTHROPIC_API_KEY"):
        anthropic_config = AnthropicConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
            anthropic_version=os.getenv("ANTHROPIC_VERSION", "2023-06-01"),
            timeout=int(os.getenv("ANTHROPIC_TIMEOUT", "60")),
            max_retries=int(os.getenv("ANTHROPIC_MAX_RETRIES", "3")),
        )

    return LLMOrchestrationConfig(
        vertex_ai=VertexAIConfig(
            project_id=os.getenv("VERTEX_AI_PROJECT_ID", ""),
            location=os.getenv("VERTEX_AI_LOCATION", "us-central1"),
            credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            api_key=os.getenv("VERTEX_AI_API_KEY"),
        ),
        deepinfra=DeepInfraConfig(
            api_key=os.getenv("DEEPINFRA_API_KEY", ""),
            base_url=os.getenv(
                "DEEPINFRA_BASE_URL", "https://api.deepinfra.com/v1/openai"
            ),
        ),
        bedrock=BedrockConfig(
            region=os.getenv("AWS_BEDROCK_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        ),
        openai=openai_config,
        anthropic=anthropic_config,
        orchestrator=OrchestratorConfig(
            max_retries_per_provider=int(
                os.getenv("LLM_MAX_RETRIES_PER_PROVIDER", "2")
            ),
            max_total_retries=int(os.getenv("LLM_MAX_TOTAL_RETRIES", "6")),
            enable_ranking=os.getenv("LLM_ENABLE_RANKING", "true").lower() == "true",
            enable_caching=os.getenv("LLM_ENABLE_CACHING", "true").lower() == "true",
            enable_cost_fallback=os.getenv("LLM_ENABLE_COST_FALLBACK", "true").lower()
            == "true",
            primary_chat_provider=os.getenv("LLM_PRIMARY_CHAT_PROVIDER", "vertex_ai"),
        ),
    )
