# Python Toon Implementation Spec

## 1. Implementation Goal
Integrate `python-toon` as the standard serialization format for **LLM Context Injection**.

## 2. The `ContextSerializer` Service

We will create a domain service that handles data formatting.

### Interface
```python
class ContextSerializer(Protocol):
    def serialize(self, data: Any, format: Literal["json", "toon"] = "toon") -> str:
        ...
```

### Implementation (`ContextSerializerImpl`)
- **Location**: `src/app/infrastructure/serialization/context_serializer.py`
- **Logic**:
    - If `format == "json"`: Use `orjson.dumps`.
    - If `format == "toon"`: Use `libs.python_toon.encode`.

## 3. Integration Points

### 1. Message History Retrieval
When fetching the last N messages to send to the LLM:
- **Current**: JSON list of dicts.
- **New**: Convert the list of `Message` entities to a TOON string.
- **Prompt Adjustment**: Add system instruction: *"Context is provided in TOON format. Parse accordingly."*

### 2. Tool Outputs
When a tool (e.g., `get_token_prices`) returns a large list of data:
- **Strategy**: The tool implementation should return a Python dict.
- **Agent Layer**: The Agent (Agno/Squad) converts this dict to TOON before appending it to the chat history as a `TOOL_OUTPUT`.

## 4. Migration Steps
1.  **Install**: Ensure `libs/python-toon` is installed/accessible in the python path.
2.  **Service**: Create the `ContextSerializer`.
3.  **Refactor**: Update `AgentGateway` to use the serializer when constructing the `messages` payload for the LLM.
4.  **Test**: Verify LLM comprehension with TOON formatted context (Benchmarks showed high comprehension for GPT-4/Claude 3, verify for our models).
