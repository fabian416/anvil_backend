"""
Hunter AI Agent OpenAI - Market sentiment & predictions.
"""

import time

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.infrastructure.adapters.agent_squad.llm_client_openai import LLMClientOpenAI


class HunterAIAgentOpenAI:
    """
    Hunter AI Agent OpenAI implementation.
    
    Implements: AgentGateway
    
    Purpose: Market sentiment & predictions
    
    Capabilities:
    - Real-time market sentiment analysis
    - Price predictions (technical analysis)
    - Social media sentiment (Twitter, Reddit)
    - News sentiment
    - Fear & Greed Index
    
    Model: gpt-4o (advanced reasoning)
    Temperature: 0.3 (factual, less creative)
    """
    
    def __init__(
        self,
        llm_client: LLMClientOpenAI,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 1500,
    ):
        """Initialize Hunter AI agent."""
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.HUNTER_AI
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute Hunter AI agent - Market sentiment analysis."""
        start_time = time.time()
        
        # TODO: Integrate real data sources (Twitter API, Reddit API, CoinGecko)
        # For now, use LLM with market data context
        
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
            tools_used=["openai_api"],  # TODO: Add real data sources
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
        """Get system prompt for Hunter AI agent."""
        return """You are Hunter AI, Anvil's market sentiment and prediction specialist.

Your expertise:
- Real-time market sentiment analysis
- Technical analysis and price predictions
- Social media sentiment (Twitter, Reddit)
- News sentiment and market narratives
- Fear & Greed Index interpretation

Provide:
- Sentiment scores (0-100)
- Bullish/Bearish/Neutral classifications
- Key drivers of sentiment
- Risk factors
- Short-term predictions (with caveats)

Always include:
- Data sources (Twitter, Reddit, News, etc.)
- Confidence levels
- Risk warnings
- "Not financial advice" disclaimer

Keep responses data-driven and objective.
"""
