"""
Mock gateway implementations for component tests.

These gateways mock external API calls (LLM, GraphRAG, etc.) for fast,
deterministic testing without network overhead.

Design Principles:
- Configurable responses (default + queue for multi-turn)
- Call history tracking (for test assertions)
- Helper assertions (assert_called_once, assert_called_with)
- No network calls (pure in-memory)

Performance:
- ~0.001ms per call (vs ~500-2000ms for real API)
- No rate limiting
- Deterministic output
"""

from typing import Optional, List, Dict, Any
from uuid import uuid4


class MockLLMGateway:
    """
    Mock LLM gateway for testing.

    Allows configuring responses without making actual API calls.
    Tracks call history for verification in tests.

    Usage:
        >>> gateway = MockLLMGateway()
        >>> gateway.set_default_response("Hello! I'm a mock assistant.")
        >>> response = await gateway.generate(
        ...     model="gpt-4o-mini",
        ...     messages=[{"role": "user", "content": "Hi"}],
        ... )
        >>> gateway.assert_called_once()
    """

    def __init__(self):
        """Initialize with default response."""
        self._default_response = "This is a mock LLM response."
        self._default_metadata = {
            "tokens_used": 50,
            "model": "mock-model-v1",
            "latency_ms": 100,
            "finish_reason": "stop",
        }
        self._response_queue: List[str] = []
        self._call_history: List[Dict[str, Any]] = []

    def set_default_response(self, response: str) -> None:
        """
        Set the default response for all calls.

        Args:
            response: Text response to return

        Example:
            >>> gateway.set_default_response("DeFi is decentralized finance...")
        """
        self._default_response = response

    def queue_response(self, response: str) -> None:
        """
        Queue a response (FIFO).

        Used for multi-turn scenarios where different responses are needed.

        Args:
            response: Text response to queue

        Example:
            >>> gateway.queue_response("First response")
            >>> gateway.queue_response("Second response")
            >>> # First call gets "First response", second gets "Second response"
        """
        self._response_queue.append(response)

    async def generate(
        self,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[List[Dict]] = None,
    ) -> str:
        """
        Generate mock text completion.

        Args:
            model: Model identifier (recorded but ignored)
            messages: Conversation messages (recorded for assertions)
            temperature: Sampling temperature (recorded but ignored)
            max_tokens: Maximum response tokens (recorded but ignored)
            tools: Optional tool definitions (recorded but ignored)

        Returns:
            Mock text response

        Note: Records call parameters for later assertions
        """
        # Record call for assertions
        self._call_history.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": tools,
        })

        # Return queued response or default
        if self._response_queue:
            return self._response_queue.pop(0)
        return self._default_response

    async def generate_with_metadata(
        self,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[List[Dict]] = None,
    ) -> tuple[str, Dict]:
        """
        Generate with usage metadata.

        Args:
            model: Model identifier
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            tools: Optional tool definitions

        Returns:
            Tuple of (response_text, metadata)

        Note: Metadata is mock data, not real token counts
        """
        # Get response (also records call)
        response = await self.generate(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )

        return response, self._default_metadata

    def get_call_history(self) -> List[Dict[str, Any]]:
        """
        Get history of all calls.

        Returns:
            List of call dictionaries with parameters

        Example:
            >>> history = gateway.get_call_history()
            >>> assert len(history) == 2
            >>> assert history[0]["model"] == "gpt-4o-mini"
        """
        return self._call_history

    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent call.

        Returns:
            Last call dictionary or None if no calls

        Example:
            >>> last_call = gateway.get_last_call()
            >>> assert last_call["model"] == "gpt-4o-mini"
        """
        return self._call_history[-1] if self._call_history else None

    def assert_called_once(self):
        """
        Assert gateway was called exactly once.

        Raises:
            AssertionError: If not called exactly once

        Example:
            >>> gateway.assert_called_once()
        """
        count = len(self._call_history)
        assert count == 1, f"Expected 1 call, got {count}"

    def assert_called_with(self, **kwargs):
        """
        Assert last call had specific parameters.

        Args:
            **kwargs: Parameter names and expected values

        Raises:
            AssertionError: If last call doesn't match expected parameters

        Example:
            >>> gateway.assert_called_with(model="gpt-4o-mini", temperature=0.7)
        """
        assert len(self._call_history) > 0, "Gateway was not called"
        last_call = self._call_history[-1]

        for key, expected_value in kwargs.items():
            assert key in last_call, f"Parameter '{key}' not found in call"
            actual_value = last_call[key]
            assert actual_value == expected_value, \
                f"Expected {key}={expected_value}, got {actual_value}"

    def assert_not_called(self):
        """
        Assert gateway was never called.

        Raises:
            AssertionError: If gateway was called

        Example:
            >>> gateway.assert_not_called()
        """
        count = len(self._call_history)
        assert count == 0, f"Expected 0 calls, got {count}"

    def reset(self):
        """
        Reset call history and response queue.

        Utility method for test cleanup.
        Does not reset default response.

        Example:
            >>> gateway.reset()  # Clear history between tests
        """
        self._call_history.clear()
        self._response_queue.clear()


class MockIntentDetectionGateway:
    """
    Mock intent detection gateway.

    Provides deterministic intent classification for testing.

    Usage:
        >>> gateway = MockIntentDetectionGateway()
        >>> gateway.set_default_intent({
        ...     "agent_type": "CHAT",
        ...     "confidence": 0.95,
        ...     "reasoning": "General conversation",
        ... })
        >>> result = await gateway.classify("Hello")
        >>> assert result["agent_type"] == "CHAT"
    """

    def __init__(self):
        """Initialize with default intent."""
        self._default_intent = {
            "agent_type": "CHAT",
            "confidence": 0.95,
            "reasoning": "Default mock intent",
        }
        self._intent_queue: List[Dict[str, Any]] = []

    def set_default_intent(self, intent: Dict[str, Any]) -> None:
        """
        Set default intent classification result.

        Args:
            intent: Intent dictionary with agent_type, confidence, reasoning

        Example:
            >>> gateway.set_default_intent({
            ...     "agent_type": "HUNTER_AI",
            ...     "confidence": 0.92,
            ...     "reasoning": "Market sentiment query",
            ... })
        """
        self._default_intent = intent

    def queue_intent(self, intent: Dict[str, Any]) -> None:
        """
        Queue an intent result (FIFO).

        Args:
            intent: Intent dictionary to queue

        Example:
            >>> gateway.queue_intent({"agent_type": "CHAT", "confidence": 0.9})
            >>> gateway.queue_intent({"agent_type": "HUNTER_AI", "confidence": 0.95})
        """
        self._intent_queue.append(intent)

    async def classify(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Classify intent (mock).

        Args:
            content: Message content
            context: Optional conversation context

        Returns:
            Intent classification result

        Note: Returns queued intent or default, ignores actual content
        """
        # Return queued intent or default
        if self._intent_queue:
            return self._intent_queue.pop(0)
        return self._default_intent
