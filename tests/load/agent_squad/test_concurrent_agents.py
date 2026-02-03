"""
Load tests for concurrent agent execution.
"""

import pytest
import asyncio
from uuid import uuid4
import time

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import (
    ConversationContext,
)


@pytest.mark.load
@pytest.mark.asyncio
class TestConcurrentAgentLoad:
    """Load tests for concurrent agent execution."""

    async def test_100_concurrent_chat_agents(self, chat_agent, benchmark):
        """Test 100 concurrent chat agent requests."""

        async def execute_agent():
            conversation_id = ConversationId(uuid4())
            message = MessageContent("Hello, how are you?")
            context = ConversationContext()

            response = await chat_agent.execute(conversation_id, message, context)
            return response

        # Run 100 concurrent requests
        tasks = [execute_agent() for _ in range(100)]

        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # Assertions
        assert len(responses) == 100
        assert all(r.agent_type == AgentType.CHAT for r in responses)

        # Performance benchmarks
        avg_latency = elapsed / 100
        requests_per_second = 100 / elapsed

        print(f"\n100 Concurrent Agents:")
        print(f"  Total Time: {elapsed:.2f}s")
        print(f"  Avg Latency: {avg_latency * 1000:.0f}ms")
        print(f"  Throughput: {requests_per_second:.1f} req/s")

        # Performance targets
        assert elapsed < 30  # Should complete in under 30s
        assert avg_latency < 0.5  # Avg latency under 500ms

    async def test_1000_concurrent_agents(self, chat_agent):
        """Test 1000 concurrent agent requests (stress test)."""

        async def execute_agent():
            conversation_id = ConversationId(uuid4())
            message = MessageContent(f"Test message {uuid4()}")
            context = ConversationContext()

            try:
                response = await chat_agent.execute(conversation_id, message, context)
                return {"success": True, "latency": response.metadata["latency_ms"]}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Run 1000 concurrent requests
        tasks = [execute_agent() for _ in range(1000)]

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time

        # Analyze results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed = len(results) - successful

        if successful > 0:
            latencies = [
                r["latency"]
                for r in results
                if isinstance(r, dict) and r.get("success")
            ]
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
            p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
        else:
            avg_latency = p95_latency = p99_latency = 0

        print(f"\n1000 Concurrent Agents (Stress Test):")
        print(f"  Total Time: {elapsed:.2f}s")
        print(f"  Successful: {successful}/1000")
        print(f"  Failed: {failed}/1000")
        print(f"  Avg Latency: {avg_latency:.0f}ms")
        print(f"  P95 Latency: {p95_latency:.0f}ms")
        print(f"  P99 Latency: {p99_latency:.0f}ms")
        print(f"  Throughput: {successful / elapsed:.1f} req/s")

        # Stress test targets (more lenient)
        assert successful >= 950  # 95% success rate
        assert elapsed < 120  # Complete in under 2 minutes


@pytest.fixture
def chat_agent(mocker):
    """Mock chat agent for load testing."""
    from app.infrastructure.adapters.agent_squad.agents.chat_agent_openai import (
        ChatAgentOpenAI,
    )

    llm_client = mocker.AsyncMock()
    llm_client.chat.return_value = {
        "content": "Test response",
        "tokens_used": 100,
        "model": "gpt-4o-mini",
        "finish_reason": "stop",
    }

    return ChatAgentOpenAI(llm_client=llm_client)
