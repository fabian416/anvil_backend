"""
Agent Squad infrastructure adapters.

Adapters implement domain ports (interfaces).
Following Hexagonal Architecture (Ports & Adapters pattern).

Adapters:
- FeatureFlagsConfig: Feature flags from TOML configuration
- LLMClientOpenAI: OpenAI API client
- ContextStorageRedis: Redis-based conversation storage
- IntentClassifierOpenAI: OpenAI-powered intent classification
- AgentExecutorFactory: Creates agent instances
"""

from .feature_flags_config import FeatureFlagsConfig
from .llm_client_openai import LLMClientOpenAI
from .context_storage_redis import ContextStorageRedis
from .intent_classifier_openai import IntentClassifierOpenAI

__all__ = [
    "FeatureFlagsConfig",
    "LLMClientOpenAI",
    "ContextStorageRedis",
    "IntentClassifierOpenAI",
]
