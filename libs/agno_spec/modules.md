# Agno Module Specifications

## 1. Agent Module (`agent/`)

### Overview
The core unit of execution in Agno. An `Agent` encapsulates a Model (LLM), Tools, and Memory.

### Anvil Integration
We will subclass or instantiate `Agent` for each of our specific use cases where deep tool usage is required.

**Configuration**:
- **Model**: `OpenAIChat` (gpt-4-turbo) or `Anthropic` (Claude 3.5 Sonnet).
- **Instructions**: System prompts defined in our `prompts/` directory.
- **Structured Output**: Use Pydantic models for strict response formats (e.g., `SwapDetails`).

## 2. Tools Module (`tools/`)

### Overview
Interfaces for function calling. Agno supports native Python functions and MCP.

### Anvil Integration
We will rely heavily on **MCP Integration**.
- **`MCPTools`**: Connects our Agno Agents to our internal MCP servers (e.g., `defi-mcp`, `giga-mcp`).
- **Custom Tools**: For lightweight logic, we can use `@agent.tool` decorator.

**Example**:
```python
@agent.tool
def get_wallet_balance(chain: str, address: str) -> float:
    """Fetches the balance of a wallet."""
    # Implementation calling our WalletService
```

## 3. Knowledge Module (`knowledge/`)

### Overview
RAG pipeline. Ingests documents, chunks them, embeds them, and stores them in a Vector DB.

### Anvil Integration
- **Source**: Protocol Whitepapers, API Docs.
- **Vector DB**: `PgVector` (using our PostgreSQL instance).
- **Embedder**: `OpenAIEmbedder`.

**Workflow**:
1.  **Ingestion**: Periodic task reads PDF/MD files.
2.  **Retrieval**: Agent automatically queries Knowledge base when relevant terms appear in user query.

## 4. Memory Module (`memory/`)

### Overview
Short-term and long-term memory.

### Anvil Integration
- **Thread Memory**: Stores the current conversation context.
- **User Memory**: Stores facts about the user (e.g., "User prefers low-risk farms").
- **Persistence**: We must implement a `PostgresMemory` adapter that aligns with our `agent_sessions` table.
