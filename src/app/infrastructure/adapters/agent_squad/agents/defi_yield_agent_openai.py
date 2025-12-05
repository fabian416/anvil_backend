"""
DeFi Yield Agent OpenAI - Yield farming & APY optimization.
"""

import time

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.infrastructure.adapters.agent_squad.llm_client_openai import LLMClientOpenAI


class DefiYieldAgentOpenAI:
    """
    DeFi Yield Agent OpenAI implementation.
    
    Implements: AgentGateway
    
    Purpose: Yield farming & APY optimization
    
    Capabilities:
    - Find best yield opportunities
    - APY comparison (Aave, Compound, Curve, Convex)
    - Liquidity pool analysis
    - Impermanent loss calculation
    - Yield farming strategies
    - Auto-compounding recommendations
    
    Model: gpt-4o (complex DeFi reasoning)
    Temperature: 0.3 (balanced)
    """
    
    def __init__(
        self,
        llm_client: LLMClientOpenAI,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        """Initialize DeFi yield agent."""
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.DEFI_YIELD
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute DeFi yield agent - Yield optimization."""
        start_time = time.time()
        
        # TODO: Integrate DeFiLlama API (real APY data)
        # TODO: Calculate impermanent loss
        # TODO: Analyze liquidity pools
        
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
            tools_used=["openai_api"],  # TODO: Add DeFiLlama, protocol APIs
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
        """Get system prompt for DeFi yield agent."""
        return """You are the DeFi Yield Optimizer, Anvil's yield farming specialist.

Your expertise:
- Yield opportunity discovery
- APY comparison (across protocols)
- Liquidity pool analysis
- Impermanent loss calculation
- Yield farming strategies
- Auto-compounding optimization
- Risk-adjusted yield (APY vs risk)

For yield recommendations, provide:
- Top opportunities (sorted by APY)
- Protocol comparison table
  - Protocol name
  - APY (base + rewards)
  - TVL (liquidity depth)
  - Risk score (0-100)
  - Impermanent loss risk
- Risk-adjusted ranking
- Entry/exit strategies

Analysis includes:
- Current APY (base rate + rewards)
- Impermanent loss risk
- Pool composition (50/50, 80/20, etc.)
- Reward tokens (value, vesting)
- Protocol risk (audit, TVL, age)
- Gas costs (entry, exit, compound)

Always provide:
- Quantitative comparison (APY table)
- Risk assessment
- Gas cost estimates
- IL scenarios (if pools)
- Recommendations (best for your risk profile)
"""
