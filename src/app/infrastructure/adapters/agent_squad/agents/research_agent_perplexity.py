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
        perplexity_client: Any | None = None,  # PerplexityMCPServer (optional)
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ):
        """
        Initialize research agent.
        
        Args:
            llm_client: LLM client for general reasoning
            perplexity_client: Optional Perplexity MCP server for real-time web search
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
        """
        self._llm_client = llm_client
        self._perplexity_client = perplexity_client
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
        
        # Collect sources
        from datetime import datetime
        from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
            create_llm_source,
            create_api_source,
        )
        
        sources = []
        fetched_at = datetime.utcnow()
        perplexity_result = None
        tools_used = ["openai_api"]
        
        # Try to use Perplexity MCP server if available
        if self._perplexity_client:
            try:
                # Use Perplexity for real-time web search
                perplexity_result = await self._perplexity_client._search(
                    query=message.value,
                    model="sonar-medium-online",  # Good balance of quality and speed
                    max_tokens=self._max_tokens,
                )
                
                if perplexity_result and not perplexity_result.get("error"):
                    tools_used.append("perplexity_api")
                    
                    # Add Perplexity citations if available
                    citations = perplexity_result.get("citations", [])
                    if citations:
                        for idx, citation in enumerate(citations, 1):
                            # Handle different citation formats
                            if isinstance(citation, dict):
                                url = citation.get("url") or citation.get("link")
                                title = citation.get("title") or citation.get("name") or url
                            elif isinstance(citation, str):
                                url = citation
                                title = citation
                            else:
                                continue
                            
                            sources.append(create_api_source(
                                source_name="Perplexity AI",
                                url=url,
                                citation_text=title or f"Citation {idx}",
                                fetched_at=fetched_at,
                                provider="Perplexity API",
                                relevance_score=1.0 / len(citations) if citations else 1.0,
                                metadata={"citation_index": idx},
                            ))
                    
                    # Use Perplexity answer if available
                    if perplexity_result.get("answer"):
                        response_content = perplexity_result["answer"]
                    else:
                        # Fallback to LLM with Perplexity context
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
                        response_content = response["content"]
                else:
                    # Perplexity returned error, fallback to LLM-only
                    raise Exception(perplexity_result.get("error", "Perplexity search failed"))
                    
            except Exception as e:
                # Fallback to LLM-only if Perplexity fails
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Perplexity search failed, using LLM-only: {e}")
                perplexity_result = None
        
        # If Perplexity not available or failed, use LLM-only
        if not perplexity_result or perplexity_result.get("error"):
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
            response_content = response["content"]
        else:
            # Response content already set from Perplexity
            response = {"content": response_content, "model": perplexity_result.get("model", "perplexity")}
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Add LLM source (always include, even if Perplexity was used)
        model_name = response.get("model", "Unknown")
        sources.append(create_llm_source(
            model=model_name,
            fetched_at=fetched_at,
        ))
        
        # If no Perplexity citations but Perplexity was used, add general Perplexity source
        if perplexity_result and not perplexity_result.get("error") and "perplexity_api" in tools_used:
            if not any(s.source_name == "Perplexity AI" for s in sources):
                sources.append(create_api_source(
                    source_name="Perplexity AI",
                    citation_text="AI-powered research from Perplexity",
                    fetched_at=fetched_at,
                    provider="Perplexity API",
                ))
        
        return AgentResponse(
            content=response_content,
            agent_type=self.agent_type,
            tools_used=tools_used,
            sources=sources,
            metadata={
                "tokens_used": response.get("tokens_used") or perplexity_result.get("usage", {}).get("total_tokens"),
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
