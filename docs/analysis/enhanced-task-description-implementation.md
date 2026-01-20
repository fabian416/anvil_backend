# Enhanced Task Description Implementation

## ✅ Implementation Complete

### What Was Enhanced

The `task_description` field in `agent_timings` now includes:
1. **Original task description** (what the agent was asked to do)
2. **Tools used** (Knowledge Base, Web3Client, CoinGecko API, DeFiLlama API, etc.)
3. **Data Sources** (Anvil Knowledge Base API, CoinGecko API, Database, Morpho, GraphRAG, etc.)

### Format

```
{original_task_description} | Tools: {tool1}, {tool2} | Data Sources: {source1}, {source2}
```

### Examples

#### Simple Query - Knowledge Agent
```json
{
  "agent_type": "knowledge",
  "task_description": "Fast path execution | Tools: Knowledge Base | Data Sources: Anvil Knowledge Base API, Anvil",
  "execution_time_ms": 3042,
  "status": "completed",
  "provider": "vertex_ai",
  "tools_used": ["knowledge_base"]
}
```

#### Complex Query - Multi-Agent Workflow

**Knowledge Agent:**
```json
{
  "agent_type": "knowledge",
  "task_description": "Provide information about Anvil | Tools: Knowledge Base | Data Sources: Anvil Knowledge Base API, Anvil",
  "execution_time_ms": 1835,
  "tools_used": ["knowledge_base"]
}
```

**Hunter AI Agent:**
```json
{
  "agent_type": "hunter_ai",
  "task_description": "Get the current price of BTC | Tools: Openai Api, CoinGecko API | Data Sources: CoinGecko API",
  "execution_time_ms": 824,
  "tools_used": ["openai_api", "coingecko_api"]
}
```

**Chat Agent (Aggregation):**
```json
{
  "agent_type": "chat",
  "task_description": "Aggregate and summarize the results from all previous agents, removing duplicates and creating a single coherent response",
  "execution_time_ms": 1654,
  "tools_used": []
}
```

## Tool Name Mapping

The system maps internal tool names to readable names:

| Internal Tool Name | Display Name |
|-------------------|--------------|
| `knowledge_base` | Knowledge Base |
| `web3_client` | Web3Client |
| `coingecko_api` | CoinGecko API |
| `defillama_api` | DeFiLlama API |
| `1inch_api` | 1inch API |
| `morpho` | Morpho |
| `graphrag` | GraphRAG |
| `database` | Database |
| `llm_gateway` | LLM Gateway |
| `perplexity` | Perplexity |
| `thegraph` | The Graph |

## Data Source Mapping

The system maps source types to readable names:

| Source Type | Display Name |
|-------------|--------------|
| `api` | `{source_name} API` (e.g., "CoinGecko API") |
| `database` | Database |
| `mcp_server` | MCP: {source_name} |
| `blockchain` | Blockchain ({source_name}) |
| `knowledge_base` | Knowledge Base |
| `rss_feed` | RSS Feed |
| `social_media` | Social Media ({source_name}) |

## Implementation Details

### Fast Path (Simple Queries)
**File:** `src/app/application/guest/commands/send_guest_message.py`

- Extracts `tools_used` from AgentResponse
- Extracts `sources` from AgentResponse
- Maps tools and sources to readable names
- Builds enhanced task_description

### Workflow (Complex Queries)
**File:** `src/app/domain/services/agent_squad/supervisor_coordinator.py`

- Extracts `tools_used` from each task's AgentResponse
- Extracts `sources` from each task's AgentResponse
- Maps tools and sources to readable names
- Builds enhanced task_description for each agent

## Benefits

1. **Transparency:** Users can see exactly what tools and data sources were used
2. **Debugging:** Developers can quickly identify which integrations are being used
3. **Performance Analysis:** Can correlate execution times with specific tools/data sources
4. **Reference:** Clear documentation of what was used in each agent execution

## Files Modified

1. `src/app/application/guest/commands/send_guest_message.py` - Fast path enhancement
2. `src/app/domain/services/agent_squad/supervisor_coordinator.py` - Workflow enhancement
3. `src/app/domain/value_objects/chat/source_info.py` - Added KNOWLEDGE_BASE source type

## Testing

✅ **Simple Query:**
- Enhanced task_description includes tools and data sources
- Format: "Fast path execution | Tools: Knowledge Base | Data Sources: Anvil Knowledge Base API, Anvil"

✅ **Complex Query:**
- Each agent in workflow has enhanced task_description
- Knowledge agent: Shows Knowledge Base tools and sources
- Hunter AI agent: Shows CoinGecko API tools and sources
- Chat agent: Shows aggregation task (no tools/sources)
