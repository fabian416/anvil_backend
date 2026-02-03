"""
Agent Squad infrastructure adapters.

Adapters implement domain ports (interfaces).
Following Hexagonal Architecture (Ports & Adapters pattern).

Adapters:
- FeatureFlagsConfig: Feature flags from TOML configuration
- LLMClientVertexAI: Google Vertex AI client (primary)
- LLMClientDeepInfra: DeepInfra API client (fallback)
- LLMClientWithFallback: Multi-provider fallback wrapper
- LLMClientGatewayAdapter: Adapter bridging LLMGateway to LLMClientGateway
- ContextStorageRedis: Redis-based conversation storage
- IntentClassifierOpenAI: Intent classification (uses LLMClientGateway)
"""

from .feature_flags_config import FeatureFlagsConfig

# OpenAI removed - using only Vertex AI and DeepInfra
# from .llm_client_openai import LLMClientGateway
from .llm_client_vertex_ai import LLMClientVertexAI
from .llm_client_deepinfra import LLMClientDeepInfra
from .llm_client_with_fallback import LLMClientWithFallback
from .llm_client_gateway_adapter import LLMClientGatewayAdapter
from .agent_llm_gateway import AgentLLMGateway
from .context_storage_redis import ContextStorageRedis
from .intent_classifier_openai import IntentClassifierOpenAI

__all__ = [
    "FeatureFlagsConfig",
    # "LLMClientGateway",  # OpenAI removed
    "LLMClientVertexAI",
    "LLMClientDeepInfra",
    "LLMClientWithFallback",
    "LLMClientGatewayAdapter",
    "AgentLLMGateway",
    "ContextStorageRedis",
    "IntentClassifierOpenAI",
]
