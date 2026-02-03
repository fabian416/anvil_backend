"""
Orchestrator Integration.

Connects LLM Orchestrator with existing agent infrastructure.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID

from app.domain.services.llm.orchestrator import (
    LLMOrchestrator,
    RankedModel,
    NoAvailableModelsError,
)
from app.domain.services.llm.circuit_breaker import CircuitBreakerManager
from app.domain.value_objects.llm import LLMRequest, LLMMessage
from app.infrastructure.llm.providers import (
    VertexAIAdapter,
    DeepInfraAdapter,
    BedrockAdapter,
)

logger = logging.getLogger(__name__)


class OrchestratorIntegration:
    """
    Integration layer for LLM Orchestrator.

    Provides a simplified interface for agents to use the orchestrator.
    """

    def __init__(
        self,
        vertex_ai_adapter: VertexAIAdapter,
        deepinfra_adapter: DeepInfraAdapter,
        bedrock_adapter: BedrockAdapter,
        circuit_breaker_manager: CircuitBreakerManager,
    ):
        """
        Initialize orchestrator integration.

        Args:
            vertex_ai_adapter: Vertex AI provider
            deepinfra_adapter: DeepInfra provider
            bedrock_adapter: Bedrock provider
            circuit_breaker_manager: Circuit breaker manager
        """
        # Store providers
        self.providers = {
            "vertex_ai": vertex_ai_adapter,
            "deepinfra": deepinfra_adapter,
            "bedrock": bedrock_adapter,
        }

        # Create orchestrator
        self.orchestrator = LLMOrchestrator(
            providers=self.providers,
            circuit_breaker_manager=circuit_breaker_manager,
        )

    async def execute_agent_request(
        self,
        agent_type: str,
        messages: list[str | dict],
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        tools: Optional[list] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Execute agent request through orchestrator.

        Args:
            agent_type: Type of agent (swap_agent, trading_agent, etc.)
            messages: List of messages (strings or dicts)
            user_id: User ID for tracking
            session_id: Session ID for tracking
            tools: Optional tools for function calling
            temperature: LLM temperature
            max_tokens: Max output tokens

        Returns:
            AI response content
        """
        # Convert messages to LLMMessage objects
        llm_messages = self._convert_messages(messages)

        # Create LLM request
        request = LLMRequest(
            messages=llm_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
        )

        # Get ranked models for this agent
        ranked_models = await self._get_ranked_models_for_agent(agent_type)

        # Execute through orchestrator
        try:
            response = await self.orchestrator.execute(
                request=request,
                agent_type=agent_type,
                ranked_models=ranked_models,
                user_id=user_id,
                session_id=session_id,
            )

            return response.content

        except NoAvailableModelsError as e:
            logger.error(f"No available models for {agent_type}: {e}")
            raise

        except Exception as e:
            logger.error(f"Orchestrator execution failed for {agent_type}: {e}")
            raise

    def _convert_messages(self, messages: list[str | dict]) -> list[LLMMessage]:
        """
        Convert messages to LLMMessage objects.

        Args:
            messages: List of message strings or dicts

        Returns:
            List of LLMMessage objects
        """
        llm_messages = []

        for msg in messages:
            if isinstance(msg, str):
                # Simple string message (assume user role)
                llm_messages.append(LLMMessage(role="user", content=msg))
            elif isinstance(msg, dict):
                # Dictionary with role and content
                llm_messages.append(
                    LLMMessage(
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                        name=msg.get("name"),
                        tool_calls=msg.get("tool_calls"),
                        tool_call_id=msg.get("tool_call_id"),
                    )
                )

        return llm_messages

    async def _get_ranked_models_for_agent(self, agent_type: str) -> list[RankedModel]:
        """
        Get ranked models for agent type.

        TODO: This should query the database for actual rankings.
        For now, returns hardcoded ranked models.

        Args:
            agent_type: Agent type

        Returns:
            List of ranked models
        """
        # Hardcoded rankings for now (sorted by score)
        # TODO: Replace with actual database query

        from uuid import uuid4

        return [
            # Vertex AI models
            RankedModel(
                model_id=uuid4(),
                provider_name="vertex_ai",
                model_name="gemini-1.5-pro",
                display_name="Gemini 1.5 Pro",
                ranking_score=0.8945,
                provider_adapter=self.providers["vertex_ai"],
            ),
            RankedModel(
                model_id=uuid4(),
                provider_name="vertex_ai",
                model_name="gemini-1.5-flash",
                display_name="Gemini 1.5 Flash",
                ranking_score=0.8720,
                provider_adapter=self.providers["vertex_ai"],
            ),
            RankedModel(
                model_id=uuid4(),
                provider_name="vertex_ai",
                model_name="gemini-2.0-flash-exp",
                display_name="Gemini 2.0 Flash",
                ranking_score=0.8500,
                provider_adapter=self.providers["vertex_ai"],
            ),
            # DeepInfra models
            RankedModel(
                model_id=uuid4(),
                provider_name="deepinfra",
                model_name="meta-llama/Meta-Llama-3.1-405B-Instruct",
                display_name="Llama 3.1 405B",
                ranking_score=0.8510,
                provider_adapter=self.providers["deepinfra"],
            ),
            RankedModel(
                model_id=uuid4(),
                provider_name="deepinfra",
                model_name="mistralai/Mixtral-8x22B-Instruct-v0.1",
                display_name="Mixtral 8x22B",
                ranking_score=0.8350,
                provider_adapter=self.providers["deepinfra"],
            ),
            RankedModel(
                model_id=uuid4(),
                provider_name="deepinfra",
                model_name="Qwen/Qwen2-72B-Instruct",
                display_name="Qwen2 72B",
                ranking_score=0.8200,
                provider_adapter=self.providers["deepinfra"],
            ),
            # Bedrock models
            RankedModel(
                model_id=uuid4(),
                provider_name="bedrock",
                model_name="anthropic.claude-3-5-sonnet-20241022-v2:0",
                display_name="Claude 3.5 Sonnet",
                ranking_score=0.8650,
                provider_adapter=self.providers["bedrock"],
            ),
            RankedModel(
                model_id=uuid4(),
                provider_name="bedrock",
                model_name="anthropic.claude-3-5-haiku-20241022-v1:0",
                display_name="Claude 3.5 Haiku",
                ranking_score=0.8400,
                provider_adapter=self.providers["bedrock"],
            ),
            RankedModel(
                model_id=uuid4(),
                provider_name="bedrock",
                model_name="amazon.titan-text-express-v1",
                display_name="Titan Express",
                ranking_score=0.7800,
                provider_adapter=self.providers["bedrock"],
            ),
        ]


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def create_orchestrator_integration(
    vertex_project_id: str,
    vertex_location: str,
    deepinfra_api_key: str,
    bedrock_region: str,
    vertex_api_key: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
) -> OrchestratorIntegration:
    """
    Create orchestrator integration with all providers.

    Args:
        vertex_project_id: GCP project ID
        vertex_location: GCP region
        deepinfra_api_key: DeepInfra API key
        bedrock_region: AWS region
        vertex_api_key: Vertex AI API key (optional, alternative to OAuth)
        aws_access_key_id: AWS access key (optional)
        aws_secret_access_key: AWS secret key (optional)

    Returns:
        Configured orchestrator integration
    """
    # Create provider adapters
    vertex_adapter = VertexAIAdapter(
        project_id=vertex_project_id,
        location=vertex_location,
        api_key=vertex_api_key,
    )

    deepinfra_adapter = DeepInfraAdapter(api_key=deepinfra_api_key)

    bedrock_adapter = BedrockAdapter(
        region=bedrock_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    # Create circuit breaker manager
    circuit_breaker_manager = CircuitBreakerManager()

    # Create integration
    return OrchestratorIntegration(
        vertex_ai_adapter=vertex_adapter,
        deepinfra_adapter=deepinfra_adapter,
        bedrock_adapter=bedrock_adapter,
        circuit_breaker_manager=circuit_breaker_manager,
    )
