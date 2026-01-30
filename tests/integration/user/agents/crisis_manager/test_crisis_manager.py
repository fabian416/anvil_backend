"""
Crisis Manager Agent Tests for Authenticated Users.

Tests emergency response and auto-exit functionality.
Based on: docs/ceo/agents/crisis_manager/shortcuts.md
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


CRISIS_MANAGER_TESTS = [
    # Crisis Status
    {
        "test_id": "crisis_status_001",
        "input": "am I affected by any exploits",
        "expected_agent": "crisis_manager",
        "category": "enterprise",
        "subcategory": "crisis_status",
    },
    {
        "test_id": "crisis_status_002",
        "input": "show active crises",
        "expected_agent": "crisis_manager",
        "category": "enterprise",
        "subcategory": "crisis_status",
    },
    {
        "test_id": "crisis_status_003",
        "input": "what's my crisis status",
        "expected_agent": "crisis_manager",
        "category": "enterprise",
        "subcategory": "crisis_status",
    },
    
    # Emergency Actions
    {
        "test_id": "crisis_emergency_001",
        "input": "emergency withdraw from Aave",
        "expected_agent": "crisis_manager",
        "category": "enterprise",
        "subcategory": "crisis_emergency",
    },
    {
        "test_id": "crisis_emergency_002",
        "input": "exit all positions now",
        "expected_agent": "crisis_manager",
        "category": "enterprise",
        "subcategory": "crisis_emergency",
    },
    
    # Auto-Exit Configuration
    {
        "test_id": "crisis_autoexit_001",
        "input": "enable auto-exit for my positions",
        "expected_agent": "crisis_manager",
        "category": "enterprise",
        "subcategory": "crisis_autoexit",
    },
    {
        "test_id": "crisis_autoexit_002",
        "input": "set auto-exit threshold to $5000",
        "expected_agent": "crisis_manager",
        "category": "enterprise",
        "subcategory": "crisis_autoexit",
    },
    
    # Crisis History
    {
        "test_id": "crisis_history_001",
        "input": "show crisis history",
        "expected_agent": "crisis_manager",
        "category": "enterprise",
        "subcategory": "crisis_history",
    },
]


@pytest.fixture(scope="module")
def crisis_reporter() -> CSVReporter:
    """Create CSV reporter for crisis manager agent tests."""
    reporter = CSVReporter(category="agent_crisis_manager")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestCrisisManagerAgent:
    """Test Crisis Manager agent functionality."""
    
    async def test_crisis_queries(self, authenticated_client, crisis_reporter):
        """Test crisis management queries."""
        import asyncio
        
        for test_case in CRISIS_MANAGER_TESTS:
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
            
            crisis_reporter.add_result(result)
            
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)")
            
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
