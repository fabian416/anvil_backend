# Research Agent Implementation

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## File Structure

```
src/app/
├── domain/
│   ├── enums/
│   │   └── agent_type.py                 # AgentType.RESEARCH
│   └── services/
│       └── agent_squad/
│           └── intent_classifier.py      # Intent classification
│
├── infrastructure/
│   ├── adapters/
│   │   └── agent_squad/
│   │       └── agents/
│   │           └── research_agent_perplexity.py  # Main agent
│   └── mcp/
│       └── servers/
│           └── perplexity_mcp.py         # Perplexity MCP server
│
└── setup/
    └── ioc/
        └── agent_squad_infrastructure.py  # DI registration
```

---

## Core Files

### 1. ResearchAgentPerplexity

**File**: `src/app/infrastructure/adapters/agent_squad/agents/research_agent_perplexity.py`
**Lines**: ~239

#### Class Definition

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

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 35-57 | Initialize with clients |
| `agent_type` | 59-62 | Return AgentType.RESEARCH |
| `execute` | 64-196 | Main entry point |
| `is_available` | 198-200 | Availability check |
| `_get_system_prompt` | 202-238 | Research analysis prompt |

#### Constructor

```python
def __init__(
    self,
    llm_client: LLMClientGateway,
    perplexity_client: Any | None = None,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.2,
    max_tokens: int = 2000,
):
    self._llm_client = llm_client
    self._perplexity_client = perplexity_client
    self._model = model
    self._temperature = temperature
    self._max_tokens = max_tokens
```

---

### 2. PerplexityMCPServer

**File**: `src/app/infrastructure/mcp/servers/perplexity_mcp.py`
**Lines**: ~316

#### Class Definition

```python
class PerplexityMCPServer(MCPServer):
    """
    MCP server for Perplexity AI API.
    
    Provides intelligent search and research capabilities with retry support.
    """
```

#### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 21-64 | Initialize with API key |
| `_register_tools` | 70-126 | Register search and chat tools |
| `_search` | 128-194 | Execute web search |
| `_chat` | 196-249 | Conversational search |
| `call_tool` | 251-277 | Tool dispatcher |
| `close` | 279-281 | Close HTTP client |

---

### 3. DI Registration

**File**: `src/app/setup/ioc/agent_squad_infrastructure.py`

```python
@provide
def provide_research_agent(
    self,
    llm_client: LLMClientGateway,
    settings: AppSettings,
) -> ResearchAgentPerplexity:
    """Provide Research agent with optional Perplexity integration."""
    import os
    from app.infrastructure.mcp.servers.perplexity_mcp import PerplexityMCPServer
    from app.setup.config.mcp import MCPSettings
    
    perplexity_client = None
    
    # Check if Perplexity is enabled and API key is available
    if settings.mcp and settings.mcp.servers.perplexity_enabled:
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if perplexity_api_key:
            try:
                mcp_settings = MCPSettings(
                    enabled=True,
                    retry=settings.mcp.retry if settings.mcp else None,
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

## Execute Method Implementation

### Main Flow

```python
# Lines 64-196
async def execute(
    self,
    conversation_id: ConversationId,
    message: MessageContent,
    conversation_context: ConversationContext,
) -> AgentResponse:
    start_time = time.time()
    
    sources = []
    fetched_at = datetime.now(UTC)
    perplexity_result = None
    tools_used = ["openai_api"]
```

### Perplexity Search

```python
# Lines 86-147
if self._perplexity_client:
    try:
        # Use Perplexity for real-time web search
        perplexity_result = await self._perplexity_client._search(
            query=message.value,
            model="sonar-medium-online",
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
                        relevance_score=1.0 / len(citations),
                        metadata={"citation_index": idx},
                    ))
            
            # Use Perplexity answer if available
            if perplexity_result.get("answer"):
                response_content = perplexity_result["answer"]
```

### LLM Fallback

```python
# Lines 149-165
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
```

### Source Building

```python
# Lines 169-184
# Add LLM source (always include)
model_name = response.get("model", "Unknown")
sources.append(create_llm_source(
    model=model_name,
    fetched_at=fetched_at,
))

# If no Perplexity citations but Perplexity was used
if perplexity_result and not perplexity_result.get("error") and "perplexity_api" in tools_used:
    if not any(s.source_name == "Perplexity AI" for s in sources):
        sources.append(create_api_source(
            source_name="Perplexity AI",
            citation_text="AI-powered research from Perplexity",
            fetched_at=fetched_at,
            provider="Perplexity API",
        ))
```

---

## Perplexity MCP Implementation

### Search Method

```python
# Lines 128-194
async def _search(
    self,
    query: str,
    model: str = "sonar-small-online",
    max_tokens: int = 1024,
    **kwargs,
) -> Dict[str, Any]:
    @self._retry
    async def _fetch():
        response = await self.client.post(
            "/chat/completions",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        return response.json()
    
    try:
        data = await _fetch()
        
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content", "")
            citations = data.get("citations", [])
            
            return {
                "query": query,
                "answer": content,
                "citations": citations,
                "model": model,
                "usage": data.get("usage", {}),
            }
        else:
            return {
                "error": "No results found",
                "query": query,
            }
    
    except httpx.HTTPError as e:
        return {
            "error": f"Perplexity API error: {str(e)}",
            "query": query,
        }
```

### Retry Configuration

```python
# Lines 52-62
retry_config = settings.retry if settings else None
max_retries = retry_config.max_retries if retry_config and retry_config.enabled else 3
initial_backoff = retry_config.initial_backoff_seconds if retry_config else 2.0
max_backoff = retry_config.max_backoff_seconds if retry_config else 10.0

self._retry = retry(
    stop=stop_after_attempt(max_retries),
    wait=wait_exponential(multiplier=1, min=initial_backoff, max=max_backoff),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    reraise=True,
)
```

---

## System Prompt

```python
# Lines 202-238
def _get_system_prompt(self) -> str:
    return """You are the Research Agent, Anvil's deep protocol analysis specialist.

**CRITICAL: OFF-TOPIC QUERY HANDLING**
- You ONLY research DeFi, crypto, blockchain, Web3, and Anvil platform topics
- If asked about cooking, recipes, general knowledge, or non-crypto topics:
  * DO NOT provide research or information
  * Respond: "I'm specialized in DeFi and crypto research..."
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

## Response Structure

### AgentResponse

```python
# Lines 186-196
return AgentResponse(
    content=response_content,
    agent_type=self.agent_type,
    tools_used=tools_used,  # ["openai_api", "perplexity_api"]
    sources=sources,
    metadata={
        "tokens_used": response.get("tokens_used") or perplexity_result.get("usage", {}).get("total_tokens"),
        "latency_ms": latency_ms,
        "model": response.get("model"),
    },
)
```

---

## Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/agents/test_research_agent.py -v

# Integration tests
pytest tests/integration/test_research_agent.py -v

# All research tests
pytest tests/ -k research -v
```

### Test Cases

```python
# Perplexity search
def test_perplexity_search():
    result = await server._search("Aave V3 protocol")
    assert "answer" in result
    assert not result.get("error")

# Citation extraction
def test_citation_extraction():
    result = {"citations": [
        {"url": "https://docs.aave.com", "title": "Aave Docs"},
    ]}
    sources = extract_citations(result)
    assert len(sources) == 1
    assert sources[0].url == "https://docs.aave.com"

# LLM fallback
def test_llm_fallback_when_no_perplexity():
    agent = ResearchAgentPerplexity(
        llm_client=mock_llm,
        perplexity_client=None,
    )
    response = await agent.execute(
        message=MessageContent("Research Uniswap")
    )
    assert response.content
    assert "openai_api" in response.tools_used

# Off-topic rejection
def test_off_topic_rejection():
    response = await agent.execute(
        message=MessageContent("How to make cookies")
    )
    assert "specialized in DeFi" in response.content
```

---

## Performance

### Metrics

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Perplexity API | < 2000ms | HTTP with retry |
| LLM Fallback | < 1500ms | Vertex AI |
| Citation processing | < 100ms | JSON parsing |
| Total | < 3s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added Perplexity MCP integration |
| 2026-01-29 | Added citation support |
| 2026-01-29 | Added retry configuration |
