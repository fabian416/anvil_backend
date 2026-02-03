"""
Chat Agent Tests for Authenticated Users.

Tests greetings, off-topic handling, and fallback behavior.
Based on: docs/ceo/agents/chat/shortcuts.md
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ...conftest import (
    CSVReporter,
    TestResult,
    send_message,
    parse_response,
    create_test_result,
    create_conversation,
)


CHAT_TESTS = [
    # Greetings
    {
        "test_id": "chat_greeting_001",
        "input": "hi",
        "expected_agent": "chat",
        "category": "agent",
        "subcategory": "chat_greeting",
    },
    {
        "test_id": "chat_greeting_002",
        "input": "hello",
        "expected_agent": "chat",
        "category": "agent",
        "subcategory": "chat_greeting",
    },
    {
        "test_id": "chat_greeting_003",
        "input": "hey there",
        "expected_agent": "chat",
        "category": "agent",
        "subcategory": "chat_greeting",
    },
    {
        "test_id": "chat_greeting_004",
        "input": "good morning",
        "expected_agent": "chat",
        "category": "agent",
        "subcategory": "chat_greeting",
    },
    # Off-Topic
    {
        "test_id": "chat_offtopic_001",
        "input": "write a poem about ethereum",
        "expected_agent": "chat",
        "category": "agent",
        "subcategory": "chat_offtopic",
    },
    {
        "test_id": "chat_offtopic_002",
        "input": "tell me a joke",
        "expected_agent": "chat",
        "category": "agent",
        "subcategory": "chat_offtopic",
    },
    {
        "test_id": "chat_offtopic_003",
        "input": "what's the weather",
        "expected_agent": "chat",
        "category": "agent",
        "subcategory": "chat_offtopic",
    },
    # General Queries
    {
        "test_id": "chat_general_001",
        "input": "how can you help me",
        "expected_agent": "chat",
        "category": "agent",
        "subcategory": "chat_general",
    },
    {
        "test_id": "chat_general_002",
        "input": "what can you do",
        "expected_agent": "chat",
        "category": "agent",
        "subcategory": "chat_general",
    },
]


@pytest.fixture(scope="module")
def chat_reporter() -> CSVReporter:
    """Create CSV reporter for chat agent tests."""
    reporter = CSVReporter(category="agent_chat")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestChatAgent:
    """Test Chat agent functionality."""

    async def test_chat_queries(self, authenticated_client, chat_reporter):
        """Test chat agent queries."""
        import asyncio

        for test_case in CHAT_TESTS:
            conv_id = await create_conversation(
                authenticated_client, title=f"Test {test_case['test_id']}"
            )

            response_data, response_time = await send_message(
                authenticated_client,
                conv_id,
                test_case["input"],
                timeout=90.0,
            )

            parsed = parse_response(response_data)

            expected_agent = test_case.get("expected_agent", "")
            actual_agents = parsed.get("agents_used", "")
            has_error = parsed.get("error", False)

            if has_error:
                status = "FAIL"
            elif expected_agent and expected_agent in actual_agents:
                status = "PASS"
            elif actual_agents:
                status = "PARTIAL"
            else:
                status = "FAIL"

            result = TestResult(
                test_id=test_case["test_id"],
                category=test_case.get("category", ""),
                subcategory=test_case.get("subcategory", ""),
                input=test_case["input"],
                output=parsed.get("content", "")[:500],
                expected_agent=expected_agent,
                actual_agents=actual_agents,
                response_time_ms=response_time,
                user_type="authenticated",
                status=status,
                conversation_id=conv_id,
            )

            chat_reporter.add_result(result)

            status_emoji = (
                "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            )
            print(
                f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)"
            )

            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
