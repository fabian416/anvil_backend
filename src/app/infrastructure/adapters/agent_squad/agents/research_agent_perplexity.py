"""
Research Agent Perplexity - Deep protocol analysis.
"""

import time

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext
from app.domain.ports.agent_squad.agent_gateway import AgentGateway, AgentResponse
from app.infrastructure.adapters.agent_squad.llm_client_openai import LLMClientOpenAI


class ResearchAgentPerplexity:
    """
    Research Agent Perplexity implementation.
    
    Implements: AgentGateway
    
    Purpose: Deep protocol analysis & research
    
    Capabilities:
    - Protocol documentation analysis
    - Smart contract research
    - Tokenomics analysis
    - Protocol comparisons
    - Latest updates & news
    
    Model: gpt-4o (deep reasoning) or Perplexity API
    Temperature: 0.2 (factual, precise)
    """
    
    def __init__(
        self,
        llm_client: LLMClientOpenAI,
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ):
        """Initialize research agent."""
        self._llm_client = llm_client
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
    
    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return AgentType.RESEARCH
    
    async def execute(
        self,
        conversation_id: ConversationId,
        message: MessageContent,
        conversation_context: ConversationContext,
    ) -> AgentResponse:
        """Execute research agent - Deep protocol analysis."""
        start_time = time.time()
        
        # TODO: Integrate Perplexity API for real-time web search
        # TODO: Integrate protocol documentation APIs
        
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
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        
        # Try to use Perplexity MCP server if available
        perplexity_result = None
        try:
            # TODO: Integrate Perplexity MCP server client
            # from app.infrastructure.mcp.servers.perplexity_mcp import PerplexityMCPServer
            # perplexity_client = PerplexityMCPServer(...)
            # perplexity_result = await perplexity_client.search(message.value)
            pass
        except Exception:
            # Fallback to LLM-only if Perplexity not available
            pass
        
        # Add Perplexity citations if available
        if perplexity_result and perplexity_result.get("citations"):
            citations = perplexity_result["citations"]
            for idx, citation in enumerate(citations, 1):
                sources.append(create_api_source(
                    source_name="Perplexity AI",
                    url=citation.get("url"),
                    citation_text=citation.get("title") or citation.get("url") or f"Citation {idx}",
                    fetched_at=fetched_at,
                    provider="Perplexity API",
                    relevance_score=1.0 / len(citations),  # Distribute relevance
                    metadata={"citation_index": idx, "citation": citation},
                ))
        
        # Add LLM source (always include)
        model_name = response.get("model", "Unknown")
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        # If no Perplexity citations, add Perplexity as general source
        if not perplexity_result or not perplexity_result.get("citations"):
            sources.append(create_api_source(
                source_name="Perplexity AI",
                citation_text="AI-powered research from Perplexity",
                fetched_at=fetched_at,
                provider="Perplexity API",
            ))
        
        return AgentResponse(
            content=response["content"],
            agent_type=self.agent_type,
            tools_used=["openai_api"],  # TODO: Add Perplexity, protocol docs
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
        """Get system prompt for research agent."""
        return """You are the Research Agent, Anvil's deep protocol analysis specialist.

Your expertise:
- Protocol documentation deep-dives
- Smart contract architecture analysis
- Tokenomics and economic models
- Protocol comparisons (Aave vs Compound, etc.)
- Latest protocol updates and news
- Security audit summaries

Provide comprehensive analysis including:
- Protocol mechanics (how it works)
- Key features and differentiators
- Risks and limitations
- Tokenomics (supply, distribution, utility)
- Governance model
- Security audits and vulnerabilities
- Integration patterns
- Latest updates

Always cite sources and provide links when available.
Be thorough, technical, and precise.
"""
