"""
Agent Squad domain ports (interfaces).

Ports define contracts that infrastructure adapters must implement.
Following Hexagonal Architecture (Ports & Adapters pattern).

Ports:
- AgentGateway: Base agent execution interface
- IntentClassifierGateway: Intent classification
- FeatureFlagsGateway: Agent enable/disable checks
- ContextStorageGateway: Conversation history storage
- LLMClientGateway: LLM API calls
"""

from .agent_gateway import AgentGateway, AgentResponse
from .intent_classifier_gateway import IntentClassifierGateway
from .feature_flags_gateway import FeatureFlagsGateway
from .context_storage_gateway import ContextStorageGateway
from .llm_client_gateway import LLMClientGateway

__all__ = [
    "AgentGateway",
    "AgentResponse",
    "IntentClassifierGateway",
    "FeatureFlagsGateway",
    "ContextStorageGateway",
    "LLMClientGateway",
]
