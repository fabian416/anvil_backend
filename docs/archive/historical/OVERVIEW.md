# Provider Integration Overview

## Supported Providers

| Provider | Priority | Models | Strengths |
|----------|----------|--------|-----------|
| **Vertex AI** | 1 (Primary) | Gemini 1.5 Pro, Flash, 2.0 | Large context, low cost, fast |
| **DeepInfra** | 2 (Fallback) | Llama 3.1, Mixtral, Qwen2 | Open source, cost-effective |
| **AWS Bedrock** | 3 (Fallback) | Claude 3.5, Titan | Enterprise, reliability |

---

## Provider Abstraction

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List
from dataclasses import dataclass
from enum import Enum

class ProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"

@dataclass
class LLMMessage:
    role: str  # user, assistant, system
    content: str
    images: Optional[List[str]] = None  # base64 encoded

@dataclass
class LLMRequest:
    messages: List[LLMMessage]
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.7
    tools: Optional[List[dict]] = None
    stream: bool = False

@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    model_id: str
    provider: str
    latency_ms: int
    finish_reason: str
    tool_calls: Optional[List[dict]] = None

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    provider_name: str
    
    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Execute completion request."""
        pass
    
    @abstractmethod
    async def complete_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Execute streaming completion."""
        pass
    
    @abstractmethod
    async def health_check(self) -> ProviderStatus:
        """Check provider health."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Return available model IDs."""
        pass
```

---

## Vertex AI Integration

```python
# src/llm/providers/vertex_ai.py

import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part

class VertexAIProvider(BaseLLMProvider):
    provider_name = "vertex_ai"
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        vertexai.init(project=project_id, location=location)
        self.models = {
            "gemini-1.5-pro": GenerativeModel("gemini-1.5-pro"),
            "gemini-1.5-flash": GenerativeModel("gemini-1.5-flash"),
            "gemini-2.0-flash-exp": GenerativeModel("gemini-2.0-flash-exp")
        }
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        model = self.models[request.model_id]
        contents = self._convert_messages(request.messages)
        
        response = await model.generate_content_async(
            contents,
            generation_config={
                "max_output_tokens": request.max_tokens,
                "temperature": request.temperature
            }
        )
        
        return LLMResponse(
            content=response.text,
            input_tokens=response.usage_metadata.prompt_token_count,
            output_tokens=response.usage_metadata.candidates_token_count,
            model_id=request.model_id,
            provider=self.provider_name,
            latency_ms=0,  # Set by caller
            finish_reason=response.candidates[0].finish_reason.name
        )
```

---

## DeepInfra Integration

```python
# src/llm/providers/deepinfra.py

import httpx
from typing import AsyncIterator

class DeepInfraProvider(BaseLLMProvider):
    provider_name = "deepinfra"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepinfra.com/v1/openai"
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": request.model_id,
                "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
        )
        data = response.json()
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            input_tokens=data["usage"]["prompt_tokens"],
            output_tokens=data["usage"]["completion_tokens"],
            model_id=request.model_id,
            provider=self.provider_name,
            latency_ms=0,
            finish_reason=data["choices"][0]["finish_reason"]
        )
```

---

## AWS Bedrock Integration

```python
# src/llm/providers/bedrock.py

import boto3
import json

class BedrockProvider(BaseLLMProvider):
    provider_name = "bedrock"
    
    def __init__(self, region: str = "us-east-1"):
        self.client = boto3.client("bedrock-runtime", region_name=region)
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        # Format for Anthropic models on Bedrock
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": request.max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature
        }
        
        response = self.client.invoke_model(
            modelId=request.model_id,
            body=json.dumps(body)
        )
        
        data = json.loads(response["body"].read())
        
        return LLMResponse(
            content=data["content"][0]["text"],
            input_tokens=data["usage"]["input_tokens"],
            output_tokens=data["usage"]["output_tokens"],
            model_id=request.model_id,
            provider=self.provider_name,
            latency_ms=0,
            finish_reason=data["stop_reason"]
        )
```

---

## Model Catalog

| Provider | Model ID | Context | Input $/1K | Output $/1K | Tier |
|----------|----------|---------|------------|-------------|------|
| Vertex AI | gemini-1.5-pro | 1M | $0.00125 | $0.00375 | Premium |
| Vertex AI | gemini-1.5-flash | 1M | $0.000075 | $0.0003 | Standard |
| Vertex AI | gemini-2.0-flash-exp | 1M | $0.0001 | $0.0004 | Experimental |
| DeepInfra | llama-3.1-405b | 128K | $0.0027 | $0.0027 | Premium |
| DeepInfra | mixtral-8x22b | 65K | $0.00065 | $0.00065 | Standard |
| DeepInfra | qwen2-72b | 32K | $0.00035 | $0.00035 | Economy |
| Bedrock | claude-3-5-sonnet | 200K | $0.003 | $0.015 | Premium |
| Bedrock | claude-3-5-haiku | 200K | $0.0008 | $0.004 | Standard |
| Bedrock | titan-text-express | 8K | $0.0002 | $0.0006 | Economy |
