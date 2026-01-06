"""
Risk Analyzer Agent OpenAI - Risk assessment & scoring.
"""

import time

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.domain.ports.agent_squad.llm_client_gateway import LLMClientGateway


class RiskAnalyzerAgentOpenAI:
    """
    Risk Analyzer Agent OpenAI implementation.
    
    Implements: AgentGateway
    
    Purpose: Risk assessment & scoring
    
    Capabilities:
    - Protocol risk scoring (0-100)
    - Smart contract risk analysis
    - Liquidation risk (health factor)
    - Impermanent loss calculation
    - Concentration risk
    - Market risk (volatility)
    - Counterparty risk
    
    Model: gpt-4o (advanced risk modeling)
    Temperature: 0.2 (factual, precise)
    """
    
    def __init__(
        self,
        llm_client: LLMClientGateway  # Can be Vertex AI or DeepInfra (OpenAI removed),
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ):
        """Initialize risk analyzer agent."""
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.RISK_ANALYZER
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute risk analyzer agent - Risk assessment."""
        start_time = time.time()
        
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
            create_api_source,
            create_mcp_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Add LLM source
        model_name = response.get("model", "Unknown")
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        # TODO: Add DeFiLlama source when integrated
        # sources.append(create_api_source(
        #     source_name="DeFiLlama",
        #     url="https://defillama.com/",
        #     citation_text="DeFiLlama risk analysis data",
        #     fetched_at=fetched_at,
        # ))
        
        # TODO: Add protocol sources (Aave, Morpho) when integrated
        # sources.append(create_mcp_source(
        #     mcp_server_name="Aave",
        #     tool_name="get_health_factor",
        #     citation_text="Aave V3 health factor calculation",
        #     fetched_at=fetched_at,
        # ))
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=["openai_api"],  # TODO: Add DeFiLlama, protocol APIs
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
        """Get system prompt for risk analyzer agent."""
        return """You are the Risk Analyzer, Anvil's risk assessment specialist.

Your expertise:
- Protocol risk scoring (0-100 scale)
- Smart contract risk analysis
- Liquidation risk calculation
- Impermanent loss estimation
- Concentration risk assessment
- Market risk (volatility, correlation)
- Counterparty risk

For each risk assessment, provide:
- Overall risk score (0-100)
  - 0-30: Low risk
  - 31-60: Medium risk
  - 61-80: High risk
  - 81-100: Critical risk
- Risk category breakdown
- Key risk factors
- Mitigation strategies
- Risk/reward analysis

Always include:
- Quantitative metrics (scores, percentages)
- Qualitative analysis (why this score)
- Actionable recommendations
- Risk warnings

Be conservative in risk assessments - better safe than sorry.
"""
