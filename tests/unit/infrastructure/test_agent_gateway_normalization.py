"""
Unit tests: AgentGatewayImpl._normalize_agent_response

Ensures that agent outputs of various shapes (tuples, dicts, custom objects)
are consistently transformed to strings, preventing [object Object] rendering
in the frontend.
"""

import pytest


@pytest.fixture
def agent_gateway():
    """Create an AgentGatewayImpl with mocked dependencies."""
    from unittest.mock import MagicMock, AsyncMock

    from app.infrastructure.adapters.ai.agent_gateway_impl import AgentGatewayImpl

    storage_mock = MagicMock()
    llm_gateway_mock = MagicMock()

    gateway = AgentGatewayImpl(storage=storage_mock, llm_gateway=llm_gateway_mock)
    return gateway


# ---------------------------------------------------------------------------
# String passthrough
# ---------------------------------------------------------------------------


def test_normalize_string_passthrough(agent_gateway):
    """Plain string should pass through unchanged."""
    text = "Hello, world!"
    assert agent_gateway._normalize_agent_response(text) == text


def test_normalize_empty_string(agent_gateway):
    """Empty string should return empty string."""
    assert agent_gateway._normalize_agent_response("") == ""


# ---------------------------------------------------------------------------
# None handling
# ---------------------------------------------------------------------------


def test_normalize_none_returns_empty(agent_gateway):
    """None should return empty string (prevents 'None' rendering)."""
    assert agent_gateway._normalize_agent_response(None) == ""


# ---------------------------------------------------------------------------
# Tuple handling (common LLM pattern: (text, metadata))
# ---------------------------------------------------------------------------


def test_normalize_tuple_extracts_first_string(agent_gateway):
    """Tuple like ('response text', {...}) should return first element."""
    resp = ("Here is the answer", {"meta": "data"})
    assert agent_gateway._normalize_agent_response(resp) == "Here is the answer"


def test_normalize_nested_tuple(agent_gateway):
    """Nested tuples should recursively extract first string."""
    resp = (("deep nested answer", {}), {"outer": True})
    assert agent_gateway._normalize_agent_response(resp) == "deep nested answer"


def test_normalize_list_extracts_first_string(agent_gateway):
    """List should behave like tuple, extracting first string."""
    resp = ["First message", "Second message"]
    assert agent_gateway._normalize_agent_response(resp) == "First message"


# ---------------------------------------------------------------------------
# Dict handling (common for structured LLM outputs)
# ---------------------------------------------------------------------------


def test_normalize_dict_with_output_key(agent_gateway):
    """Dict with 'output' key should extract that value."""
    resp = {"output": "The output text", "metadata": {}}
    assert agent_gateway._normalize_agent_response(resp) == "The output text"


def test_normalize_dict_with_content_key(agent_gateway):
    """Dict with 'content' key (OpenAI style) should extract that value."""
    resp = {"role": "assistant", "content": "Content text"}
    assert agent_gateway._normalize_agent_response(resp) == "Content text"


def test_normalize_dict_with_text_key(agent_gateway):
    """Dict with 'text' key should extract that value."""
    resp = {"text": "Text value", "other": 123}
    assert agent_gateway._normalize_agent_response(resp) == "Text value"


def test_normalize_dict_with_message_key(agent_gateway):
    """Dict with 'message' key should extract that value."""
    resp = {"message": "Message value"}
    assert agent_gateway._normalize_agent_response(resp) == "Message value"


def test_normalize_dict_without_known_keys_falls_back_to_str(agent_gateway):
    """Dict without recognized keys should fall back to str()."""
    resp = {"unknown_key": "value", "another": 42}
    result = agent_gateway._normalize_agent_response(resp)
    # Should be stringified dict
    assert "unknown_key" in result


# ---------------------------------------------------------------------------
# Object with .output attribute
# ---------------------------------------------------------------------------


def test_normalize_object_with_output_attribute(agent_gateway):
    """Custom object with .output attribute should use that value."""

    class LLMResponse:
        def __init__(self, output: str):
            self.output = output

    resp = LLMResponse(output="Response from LLM")
    assert agent_gateway._normalize_agent_response(resp) == "Response from LLM"


def test_normalize_nested_object_with_output(agent_gateway):
    """Nested .output should be recursively resolved."""

    class Inner:
        def __init__(self, output: str):
            self.output = output

    class Outer:
        def __init__(self, inner):
            self.output = inner

    resp = Outer(Inner("Final text"))
    assert agent_gateway._normalize_agent_response(resp) == "Final text"


# ---------------------------------------------------------------------------
# Fallback to str()
# ---------------------------------------------------------------------------


def test_normalize_number_falls_back_to_str(agent_gateway):
    """Numbers should be converted via str()."""
    assert agent_gateway._normalize_agent_response(42) == "42"
    assert agent_gateway._normalize_agent_response(3.14) == "3.14"


def test_normalize_bool_falls_back_to_str(agent_gateway):
    """Booleans should be converted via str()."""
    assert agent_gateway._normalize_agent_response(True) == "True"
