"""
Activity Agent Tests (Transaction History) for Authenticated Users.

Tests transaction history queries and recent activity.
Based on: docs/ceo/agents/activity/shortcuts.md
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


ACTIVITY_TESTS = [
    # Transaction History
    {
        "test_id": "activity_001",
        "input": "my transactions",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "activity_transactions",
    },
    {
        "test_id": "activity_002",
        "input": "show my recent activity",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "activity_recent",
    },
    {
        "test_id": "activity_003",
        "input": "transaction history",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "activity_transactions",
    },
    {
        "test_id": "activity_004",
        "input": "my activity",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "activity_recent",
    },
    {
        "test_id": "activity_005",
        "input": "what did I do last week",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "activity_historical",
    },
    {
        "test_id": "activity_006",
        "input": "show my swaps",
        "expected_agent": "transaction_history",
        "category": "agent",
        "subcategory": "activity_filtered",
    },
]


@pytest.fixture(scope="module")
def activity_reporter() -> CSVReporter:
    """Create CSV reporter for activity agent tests."""
    reporter = CSVReporter(category="agent_activity")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestActivityAgent:
    """Test Activity (Transaction History) agent functionality."""
    
    async def test_activity_queries(self, authenticated_client, activity_reporter):
        """Test activity/transaction history queries."""
        import asyncio
        
        for test_case in ACTIVITY_TESTS:
            conv_id = await create_conversation(
                authenticated_client,
                title=f"Test {test_case['test_id']}"
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
            
            activity_reporter.add_result(result)
            
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)")
            
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
