"""
LLM Response value object.

Represents a response from an LLM provider.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from decimal import Decimal


@dataclass
class ToolCall:
    """Function/tool call from LLM."""

    id: str
    type: str
    function: Dict[str, Any]


@dataclass
class LLMResponse:
    """
    Response from LLM provider.

    Contains the generated content and metadata.
    """

    content: str
    model_id: str
    provider: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    finish_reason: str  # stop, length, tool_calls, content_filter
    tool_calls: Optional[List[ToolCall]] = None
    cost_usd: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate response."""
        if self.input_tokens < 0:
            raise ValueError("input_tokens must be non-negative")

        if self.output_tokens < 0:
            raise ValueError("output_tokens must be non-negative")

        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")

    @property
    def total_tokens(self) -> int:
        """Total tokens used (input + output)."""
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "model_id": self.model_id,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "tool_calls": [
                {"id": tc.id, "type": tc.type, "function": tc.function} for tc in (self.tool_calls or [])
            ],
            "cost_usd": float(self.cost_usd) if self.cost_usd else None,
            "metadata": self.metadata,
        }
