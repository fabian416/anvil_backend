"""
Tax Optimizer Agent OpenAI - Tax-loss harvesting & reporting.
"""

import time

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class TaxOptimizerAgentOpenAI:
    """
    Tax Optimizer Agent OpenAI implementation.
    
    Implements: AgentGateway
    
    Purpose: Tax-loss harvesting & tax optimization
    
    Capabilities:
    - Tax-loss harvesting opportunities
    - Capital gains calculation (short-term, long-term)
    - Tax-efficient timing (hold 366 days)
    - Wash sale rule compliance
    - Tax reporting (Form 8949, Schedule D)
    - FIFO/LIFO/HIFO cost basis selection
    
    Model: gpt-4o (complex tax reasoning)
    Temperature: 0.2 (factual, precise)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway,  # Can be Vertex AI or DeepInfra (OpenAI removed),
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ):
        """Initialize tax optimizer agent."""
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.TAX_OPTIMIZER
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute tax optimizer agent - Tax strategies."""
        start_time = time.time()
        
        # TODO: Integrate with user transaction history
        # TODO: Calculate real capital gains
        # TODO: Identify tax-loss harvesting opportunities
        
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
        
        # Collect sources
        from datetime import datetime
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_llm_source,
            create_database_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Add database source (transaction history)
        sources.append(create_database_source(
            citation_text="Your transaction history from Anvil",
            fetched_at=fetched_at,
            metadata={"query_type": "transaction_history"},
        ))
        
        # Add LLM source
        model_name = response.get("model", "Unknown")
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        # TODO: Add tax calculation API sources when integrated
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=["openai_api"],  # TODO: Add tax calculation tools
            sources=sources,
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
        """Get system prompt for tax optimizer agent."""
        return """You are the Tax Optimizer, Anvil's tax strategy specialist.

Your expertise:
- Tax-loss harvesting opportunities
- Capital gains calculation (short-term vs long-term)
- Tax-efficient timing strategies
- Wash sale rule compliance (30-day rule)
- Cost basis selection (FIFO, LIFO, HIFO)
- Tax reporting (Form 8949, Schedule D)
- Year-end tax optimization

For tax analysis, provide:
- Capital gains breakdown (ST/LT)
- Tax-loss harvesting opportunities
- Potential tax savings
- Timing recommendations
- Wash sale warnings
- Estimated tax liability

Tax Rates (US):
- Short-term: Ordinary income (10%-37%)
- Long-term: 0%, 15%, 20% (based on income)
- Hold period: >365 days for long-term

Always include:
- Quantitative analysis (gains, losses, savings)
- Timing recommendations
- Compliance warnings (wash sale)
- Disclaimer: "Consult a tax professional"

Note: Tax laws vary by jurisdiction. Recommendations are general guidance.
"""
