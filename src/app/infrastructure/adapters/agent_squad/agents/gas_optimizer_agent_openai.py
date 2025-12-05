"""
Gas Optimizer Agent OpenAI - Gas fee optimization & timing.
"""

import time

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.infrastructure.adapters.agent_squad.llm_client_openai import LLMClientOpenAI


class GasOptimizerAgentOpenAI:
    """
    Gas Optimizer Agent OpenAI implementation.
    
    Implements: AgentGateway
    
    Purpose: Gas fee optimization & timing
    
    Capabilities:
    - Current gas price analysis
    - Gas price predictions (next hour, day)
    - Optimal transaction timing
    - Layer 2 migration recommendations
    - Batch transaction suggestions
    - Gas-efficient alternatives
    
    Model: gpt-4o-mini (fast, cost-effective)
    Temperature: 0.2 (factual)
    """
    
    def __init__(
        self,
        llm_client: LLMClientOpenAI,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ):
        """Initialize gas optimizer agent."""
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.GAS_OPTIMIZER
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute gas optimizer agent - Gas optimization."""
        start_time = time.time()
        
        # TODO: Integrate gas price oracle (Blocknative, EthGasStation)
        # TODO: Get real-time gas prices
        # TODO: Predict gas price trends
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": message.value},
        ]
        
        response = await self._llm_client.chat(
            messages=messages,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=["openai_api"],  # TODO: Add gas oracle
            metadata={
                "tokens_used": response.get("tokens_used"),
                "latency_ms": latency_ms,
                "model": response.get("model"),
            },
        )
    
    async def is_available(self) -> bool:
        """Check if agent is available."""
        return True
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for gas optimizer agent."""
        return """You are the Gas Optimizer, Anvil's gas fee optimization specialist.

Your expertise:
- Real-time gas price analysis
- Gas price predictions (hourly, daily trends)
- Optimal transaction timing
- Layer 2 migration recommendations (Arbitrum, Optimism, 90% savings)
- Batch transaction optimization
- Gas-efficient alternatives

For gas optimization, provide:
- Current gas prices (low, standard, fast)
- Gas price trends (rising, falling, stable)
- Timing recommendations (send now vs wait)
- Cost estimates (USD)
- Layer 2 alternatives (if applicable)
- Batch transaction suggestions

Gas Price Levels:
- Low: 10-30 gwei (30+ min wait)
- Standard: 30-50 gwei (5-10 min)
- Fast: 50-100 gwei (< 2 min)
- Urgent: 100+ gwei (next block)

Layer 2 Savings:
- Arbitrum: ~90% cheaper
- Optimism: ~85% cheaper
- Polygon: ~95% cheaper

Always include:
- Current gas prices (gwei)
- USD cost estimates
- Time estimates
- Layer 2 recommendations (if high gas)
- Timing strategy (urgent vs can wait)
"""
