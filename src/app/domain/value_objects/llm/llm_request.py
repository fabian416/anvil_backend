"""
LLM Request value object.

Represents a request to an LLM provider.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from decimal import Decimal


@dataclass
class LLMMessage:
    """Single message in LLM conversation."""

    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class LLMRequest:
    """
    Request to LLM provider.

    Represents a complete LLM request with all parameters.
    """

    messages: List[LLMMessage]
    max_tokens: int = 2000
    temperature: Decimal = Decimal("0.7")
    top_p: Optional[Decimal] = None
    stop: Optional[List[str]] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    response_format: Optional[Dict[str, str]] = None
    model_id: Optional[str] = None
    user: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate request."""
        if not self.messages:
            raise ValueError("Request must have at least one message")

        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        if not (0 <= self.temperature <= 2):
            raise ValueError("temperature must be between 0 and 2")

        if self.top_p is not None and not (0 <= self.top_p <= 1):
            raise ValueError("top_p must be between 0 and 1")

    @property
    def input_tokens(self) -> int:
        """
        Estimate input tokens.

        Rough estimate: 4 characters per token.
        """
        total_chars = sum(len(msg.content) for msg in self.messages)
        return total_chars // 4

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "name": msg.name,
                    "tool_calls": msg.tool_calls,
                    "tool_call_id": msg.tool_call_id,
                }
                for msg in self.messages
            ],
            "max_tokens": self.max_tokens,
            "temperature": float(self.temperature),
            "top_p": float(self.top_p) if self.top_p else None,
            "stop": self.stop,
            "stream": self.stream,
            "tools": self.tools,
            "tool_choice": self.tool_choice,
            "response_format": self.response_format,
            "model_id": self.model_id,
            "user": self.user,
            "metadata": self.metadata,
        }
