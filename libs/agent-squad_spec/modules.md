# Agent Squad Module Specifications

## 1. Orchestrator Module (`orchestrator.py`)

### Overview
The `AgentSquad` class acts as the central nervous system. It receives user input, invokes the classifier, and delegates execution to the selected agent.

### Anvil Integration
We will not modify the core `AgentSquad` class but will wrap it in a Domain Service `AgentGatewayImpl`.

**Key Responsibilities:**
- **Session Management**: Retrieve `conversation_id` history from our DB before passing to Squad.
- **Routing**: Call `route_request`.
- **Response Handling**: Stream tokens back to the client via SSE (Server-Sent Events).

### Configuration
```python
options = AgentSquadOptions(
    storage=AnvilSQLStorage(), # Custom storage adapter
    classifier=AnvilClassifier() # Custom or configured classifier
)
```

## 2. Agents Module (`agents/`)

### Overview
Defines the specific workers. We will primarily use `BedrockLLMAgent` (AWS) or `OpenAIAgent` depending on our model provider config.

### Key Agents for Anvil
1.  **Trading Agent (`trading`)**:
    -   **Role**: Execute swaps, limit orders.
    -   **Tools**: `1inch_quote`, `1inch_swap`, `approve_token`.
    -   **Base Class**: `OpenAIAgent` (or Bedrock equivalent).
2.  **Research Agent (`research`)**:
    -   **Role**: Fetch market data, news, sentiment.
    -   **Tools**: `defillama_tvl`, `tavily_search`.
3.  **Supervisor Agent (`supervisor`)**:
    -   **Role**: Break down complex requests ("Rebalance my portfolio").
    -   **Logic**: Decomposes task -> Calls Research -> Calls Trading -> Aggregates.

## 3. Classifiers Module (`classifiers/`)

### Overview
Determines user intent.

### Anvil Integration
We will use a **Custom Classifier** prompt to distinguish between subtle DeFi intents.
- **Input**: User query + Conversation History.
- **Output**: `AgentId` (e.g., "trading", "research") + `Confidence`.

**Categories**:
- `TRADING`: Intent to move assets.
- `RESEARCH`: Intent to query data.
- `GENERAL`: Chit-chat.

## 4. Storage Module (`storage/`)

### Overview
Persists conversation history.

### Anvil Implementation
The library provides `SQLChatStorage`, but it likely doesn't match our schema exactly.
**Task**: Implement `AnvilChatStorage` extending `ChatStorage`.
- **Methods**: `save_message`, `get_chat_history`.
- **Mapping**: Map Squad's `Message` object to our `Message` entity and save via `ConversationRepository`.

## 5. Retrievers Module (`retrievers/`) (Optional)
Used for RAG. We might delegate this to **Agno** instead, keeping Agent Squad focused purely on routing.
