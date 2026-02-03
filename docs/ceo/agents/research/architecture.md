# Research Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **RESEARCH** agent, providing deep protocol analysis using Perplexity AI for real-time web search with citations.

### Key Components

- **ResearchAgentPerplexity**: Agent Squad implementation
- **PerplexityMCPServer**: MCP server for web search
- **LLM Fallback**: Vertex AI when Perplexity unavailable

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RESEARCH AGENT ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Supervisor Coordinator  │
                    │  (Routing Logic)         │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  ResearchAgentPerplexity │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                                     │
              ▼                                     ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│  PerplexityMCPServer    │           │      Vertex AI LLM      │
│  (Real-time Search)     │           │   (Fallback Analysis)   │
└─────────────────────────┘           └─────────────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core Agents
    RESEARCH = "research"  # Deep protocol analysis
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
AGENT_MAPPING = {
    "research_protocol": AgentType.RESEARCH,
}
```

---

## Infrastructure Layer

### ResearchAgentPerplexity

**File**: `src/app/infrastructure/adapters/agent_squad/agents/research_agent_perplexity.py`
**Lines**: ~239

```python
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
    
    Model: gemini-2.0-flash (fallback) or Perplexity API
    Temperature: 0.2 (factual, precise)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `execute()` | 64-196 | Main entry point |
| `is_available()` | 198-200 | Availability check |
| `_get_system_prompt()` | 202-238 | Research analysis prompt |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,      # Vertex AI / DeepInfra
    perplexity_client: Any | None = None,  # PerplexityMCPServer
    model: str = "gemini-2.0-flash",
    temperature: float = 0.2,           # Factual, precise
    max_tokens: int = 2000,
):
```

---

## Perplexity MCP Server

### Server Implementation

**File**: `src/app/infrastructure/mcp/servers/perplexity_mcp.py`
**Lines**: ~316

```python
class PerplexityMCPServer(MCPServer):
    """
    MCP server for Perplexity AI API.
    
    Provides intelligent search and research capabilities with retry support.
    """
```

### Registered Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search` | Web search with AI | query, model, max_tokens |
| `chat` | Conversational search | messages, model |

### Models Available

| Model | Description |
|-------|-------------|
| `sonar-small-online` | Fast, basic search |
| `sonar-medium-online` | Balanced (default) |
| `sonar-large-online` | Deep, comprehensive |

---

## Execution Flow

### Main Execute Method

```python
async def execute(self, conversation_id, message, conversation_context):
    sources = []
    perplexity_result = None
    tools_used = ["openai_api"]
    
    # Try Perplexity if available
    if self._perplexity_client:
        try:
            perplexity_result = await self._perplexity_client._search(
                query=message.value,
                model="sonar-medium-online",
                max_tokens=self._max_tokens,
            )
            
            if perplexity_result and not perplexity_result.get("error"):
                tools_used.append("perplexity_api")
                
                # Extract citations
                citations = perplexity_result.get("citations", [])
                for idx, citation in enumerate(citations, 1):
                    sources.append(create_api_source(
                        source_name="Perplexity AI",
                        url=citation.get("url"),
                        citation_text=citation.get("title"),
                        fetched_at=fetched_at,
                    ))
                
                # Use Perplexity answer
                response_content = perplexity_result["answer"]
                
        except Exception as e:
            logger.warning(f"Perplexity failed, using LLM-only: {e}")
            perplexity_result = None
    
    # Fallback to LLM if Perplexity unavailable
    if not perplexity_result:
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": message.value},
        ]
        response = await self._llm_client.chat(...)
        response_content = response["content"]
    
    return AgentResponse(
        content=response_content,
        sources=sources,
        tools_used=tools_used,
    )
```

---

## Citation Handling

### Citation Extraction

```python
# Perplexity returns citations in response
citations = perplexity_result.get("citations", [])

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
        relevance_score=1.0 / len(citations),
        metadata={"citation_index": idx},
    ))
```

### Source Types

| Source | When Added |
|--------|------------|
| Perplexity Citations | When Perplexity returns citations |
| Perplexity General | When Perplexity used but no specific citations |
| LLM Source | Always (fallback or primary) |

---

## Perplexity API Integration

### Search Method

```python
async def _search(
    self,
    query: str,
    model: str = "sonar-small-online",
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    @self._retry
    async def _fetch():
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": query}
                ],
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        return response.json()
    
    data = await _fetch()
    
    return {
        "query": query,
        "answer": data["choices"][0]["message"]["content"],
        "citations": data.get("citations", []),
        "model": model,
        "usage": data.get("usage", {}),
    }
```

### Retry Configuration

```python
# From PerplexityMCPServer.__init__

max_retries = 3
initial_backoff = 2.0
max_backoff = 10.0

self._retry = retry(
    stop=stop_after_attempt(max_retries),
    wait=wait_exponential(multiplier=1, min=initial_backoff, max=max_backoff),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
```

---

## System Prompt

```python
def _get_system_prompt(self) -> str:
    return """You are the Research Agent, Anvil's deep protocol analysis specialist.

**CRITICAL: OFF-TOPIC QUERY HANDLING**
- You ONLY research DeFi, crypto, blockchain, Web3, and Anvil platform topics
- If asked about cooking, recipes, general knowledge, or non-crypto topics:
  * DO NOT provide research or information
  * Respond: "I'm specialized in DeFi and crypto research. I can't help with [topic]..."
  * Redirect to DeFi topics

Your expertise (DeFi/crypto topics ONLY):
- Protocol documentation deep-dives
- Smart contract architecture analysis
- Tokenomics and economic models
- Protocol comparisons
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
```

---

## DI Registration

### Provider Method

```python
# From agent_squad_infrastructure.py

@provide
def provide_research_agent(
    self,
    llm_client: LLMClientGateway,
    settings: AppSettings,
) -> ResearchAgentPerplexity:
    """Provide Research agent with optional Perplexity integration."""
    
    perplexity_client = None
    
    # Check if Perplexity is enabled
    if settings.mcp and settings.mcp.servers.perplexity_enabled:
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if perplexity_api_key:
            try:
                mcp_settings = MCPSettings(
                    enabled=True,
                    retry=settings.mcp.retry,
                )
                perplexity_client = PerplexityMCPServer(
                    api_key=perplexity_api_key,
                    settings=mcp_settings,
                )
            except Exception:
                perplexity_client = None
    
    return ResearchAgentPerplexity(
        llm_client=llm_client,
        perplexity_client=perplexity_client,
    )
```

---

## Testing

### Test Cases

```python
# Perplexity search
def test_perplexity_search():
    result = await perplexity._search("Aave V3")
    assert result.get("answer")
    assert not result.get("error")

# Citation extraction
def test_citation_extraction():
    citations = extract_citations(perplexity_result)
    assert len(citations) > 0
    assert all(c.url for c in citations)

# LLM fallback
def test_llm_fallback():
    agent = ResearchAgentPerplexity(
        llm_client=mock_llm,
        perplexity_client=None,  # No Perplexity
    )
    response = await agent.execute(...)
    assert response.content  # Should still work

# Off-topic rejection
def test_off_topic_rejection():
    response = await agent.execute(
        message=MessageContent("How to make a cake")
    )
    assert "specialized in DeFi" in response.content
```

---

## Performance

### Targets

| Operation | Target | Current |
|-----------|--------|---------|
| Perplexity API | < 2000ms | ~1500ms |
| LLM Fallback | < 1500ms | ~1200ms |
| Citation processing | < 100ms | ~50ms |
| Total | < 3s | ~2.5s |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added Perplexity MCP integration |
| 2026-01-29 | Added citation support |
| 2026-01-29 | Added off-topic handling |
