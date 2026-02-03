# Basic Usage Examples

"""
Example usage of the Multi-LLM Orchestration System.
"""

import asyncio
from llm.orchestration import LLMOrchestrator, OrchestratorConfig
from llm.providers import VertexAIProvider, DeepInfraProvider, BedrockProvider
from llm.providers.base import LLMRequest, LLMMessage
from llm.ranking import RankingEngine
from llm.orchestration.circuit_breaker import CircuitBreakerManager
from llm.telemetry import TelemetryCollector


# =============================================================================
# INITIALIZATION
# =============================================================================


async def setup_orchestrator():
    """Initialize the LLM orchestrator with all providers."""

    # Initialize providers
    providers = {
        "vertex_ai": VertexAIProvider(
            project_id="your-gcp-project", location="us-central1"
        ),
        "deepinfra": DeepInfraProvider(api_key="your-deepinfra-key"),
        "bedrock": BedrockProvider(region="us-east-1"),
    }

    # Initialize supporting services
    ranking_engine = RankingEngine(db_session=db)
    circuit_breaker_manager = CircuitBreakerManager(db_session=db)
    telemetry_collector = TelemetryCollector(db_session=db)

    # Create orchestrator
    orchestrator = LLMOrchestrator(
        providers=providers,
        ranking_engine=ranking_engine,
        circuit_breaker_manager=circuit_breaker_manager,
        telemetry_collector=telemetry_collector,
        config=OrchestratorConfig(
            max_retries_per_provider=2,
            max_total_retries=6,
            timeout_per_attempt_ms=30000,
        ),
    )

    return orchestrator


# =============================================================================
# BASIC COMPLETION
# =============================================================================


async def basic_completion_example():
    """Simple completion request."""

    orchestrator = await setup_orchestrator()

    # Create request
    request = LLMRequest(
        messages=[
            LLMMessage(role="system", content="You are a DeFi expert assistant."),
            LLMMessage(role="user", content="What is yield farming?"),
        ],
        max_tokens=1000,
        temperature=0.7,
    )

    # Execute with orchestration
    response = await orchestrator.execute(
        request=request, agent_type="researcher", user_id="user_123"
    )

    print(f"Response: {response.content}")
    print(f"Model used: {response.model_id}")
    print(f"Provider: {response.provider}")
    print(f"Latency: {response.latency_ms}ms")
    print(f"Tokens: {response.input_tokens} in, {response.output_tokens} out")


# =============================================================================
# STREAMING COMPLETION
# =============================================================================


async def streaming_example():
    """Streaming completion request."""

    orchestrator = await setup_orchestrator()

    request = LLMRequest(
        messages=[
            LLMMessage(role="user", content="Explain DeFi liquidity pools in detail.")
        ],
        max_tokens=2000,
        temperature=0.7,
        stream=True,
    )

    print("Streaming response:")
    async for chunk in orchestrator.execute_stream(
        request=request, agent_type="researcher"
    ):
        print(chunk, end="", flush=True)
    print("\n--- Stream complete ---")


# =============================================================================
# TOOL CALLING
# =============================================================================


async def tool_calling_example():
    """Completion with tool/function calling."""

    orchestrator = await setup_orchestrator()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_token_price",
                "description": "Get the current price of a cryptocurrency token",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Token symbol (e.g., ETH, BTC)",
                        },
                        "currency": {
                            "type": "string",
                            "description": "Quote currency",
                            "default": "USD",
                        },
                    },
                    "required": ["symbol"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "execute_swap",
                "description": "Execute a token swap on a DEX",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_token": {"type": "string"},
                        "to_token": {"type": "string"},
                        "amount": {"type": "number"},
                        "slippage_bps": {"type": "integer", "default": 50},
                    },
                    "required": ["from_token", "to_token", "amount"],
                },
            },
        },
    ]

    request = LLMRequest(
        messages=[
            LLMMessage(
                role="user",
                content="What's the current ETH price and swap 1 ETH to USDC",
            )
        ],
        tools=tools,
        max_tokens=1000,
        temperature=0.3,
    )

    response = await orchestrator.execute(request=request, agent_type="swap_agent")

    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"Tool: {tool_call['function']['name']}")
            print(f"Arguments: {tool_call['function']['arguments']}")
    else:
        print(f"Response: {response.content}")


# =============================================================================
# AGENT INTEGRATION
# =============================================================================


class SwapAgent:
    """Example DeFi swap agent using the orchestrator."""

    def __init__(self, orchestrator: LLMOrchestrator):
        self.orchestrator = orchestrator
        self.agent_type = "swap_agent"
        self.system_prompt = """You are a DeFi swap execution assistant. 
        Help users find the best swap routes and execute trades safely.
        Always check prices and estimate slippage before confirming swaps."""

    async def process_request(self, user_message: str, user_id: str) -> str:
        """Process a user swap request."""

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=self.system_prompt),
                LLMMessage(role="user", content=user_message),
            ],
            tools=self._get_tools(),
            max_tokens=2000,
            temperature=0.3,
        )

        response = await self.orchestrator.execute(
            request=request, agent_type=self.agent_type, user_id=user_id
        )

        # Handle tool calls if present
        if response.tool_calls:
            return await self._handle_tool_calls(response.tool_calls, user_id)

        return response.content

    def _get_tools(self):
        """Return available tools for this agent."""
        return [
            # ... tool definitions
        ]

    async def _handle_tool_calls(self, tool_calls, user_id):
        """Execute tool calls and return results."""
        results = []
        for call in tool_calls:
            result = await self._execute_tool(call)
            results.append(result)
        return str(results)


# =============================================================================
# ERROR HANDLING
# =============================================================================


async def error_handling_example():
    """Demonstrate error handling."""

    orchestrator = await setup_orchestrator()

    try:
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Test request")], max_tokens=100
        )

        response = await orchestrator.execute(request=request, agent_type="test_agent")
        print(f"Success: {response.content}")

    except AllProvidersExhaustedException as e:
        print(f"All providers failed: {e}")
        # Implement fallback logic

    except TimeoutError as e:
        print(f"Request timed out: {e}")
        # Handle timeout

    except Exception as e:
        print(f"Unexpected error: {e}")
        # Log and alert


# =============================================================================
# CUSTOM CONFIGURATION
# =============================================================================


async def custom_config_example():
    """Using custom configuration."""

    # High-reliability config for critical operations
    critical_config = OrchestratorConfig(
        max_retries_per_provider=3,
        max_total_retries=9,
        timeout_per_attempt_ms=45000,
        total_timeout_ms=180000,
        enable_caching=False,  # Always fresh for critical ops
    )

    # Cost-optimized config for bulk operations
    bulk_config = OrchestratorConfig(
        max_retries_per_provider=1,
        max_total_retries=3,
        timeout_per_attempt_ms=60000,
        enable_caching=True,
    )

    # Create specialized orchestrators
    critical_orchestrator = LLMOrchestrator(
        providers=providers,
        config=critical_config,
        # ... other dependencies
    )

    bulk_orchestrator = LLMOrchestrator(
        providers=providers,
        config=bulk_config,
        # ... other dependencies
    )


# =============================================================================
# RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":
    # Run basic example
    asyncio.run(basic_completion_example())

    # Run streaming example
    # asyncio.run(streaming_example())

    # Run tool calling example
    # asyncio.run(tool_calling_example())
