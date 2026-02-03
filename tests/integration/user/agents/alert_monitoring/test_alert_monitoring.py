"""
Alert Monitoring Agent Tests for Authenticated Users.

Tests real-time security alerts and Forta Network integration.
Based on: docs/ceo/agents/alert_monitoring/shortcuts.md
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


ALERT_MONITORING_TESTS = [
    # Alert Queries
    {
        "test_id": "alert_query_001",
        "input": "show security alerts",
        "expected_agent": "alert_monitoring",
        "category": "enterprise",
        "subcategory": "alert_query",
    },
    {
        "test_id": "alert_query_002",
        "input": "recent DeFi exploits",
        "expected_agent": "alert_monitoring",
        "category": "enterprise",
        "subcategory": "alert_query",
    },
    {
        "test_id": "alert_query_003",
        "input": "any protocol hacks today",
        "expected_agent": "alert_monitoring",
        "category": "enterprise",
        "subcategory": "alert_query",
    },
    # Alert Setup
    {
        "test_id": "alert_setup_001",
        "input": "set up alerts for my positions",
        "expected_agent": "alert_monitoring",
        "category": "enterprise",
        "subcategory": "alert_setup",
    },
    {
        "test_id": "alert_setup_002",
        "input": "notify me if Aave gets exploited",
        "expected_agent": "alert_monitoring",
        "category": "enterprise",
        "subcategory": "alert_setup",
    },
    # Severity Levels
    {
        "test_id": "alert_severity_001",
        "input": "show critical alerts only",
        "expected_agent": "alert_monitoring",
        "category": "enterprise",
        "subcategory": "alert_severity",
    },
]


@pytest.fixture(scope="module")
def alert_reporter() -> CSVReporter:
    """Create CSV reporter for alert monitoring agent tests."""
    reporter = CSVReporter(category="agent_alert_monitoring")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestAlertMonitoringAgent:
    """Test Alert Monitoring agent functionality."""

    async def test_alert_queries(self, authenticated_client, alert_reporter):
        """Test alert monitoring queries."""
        import asyncio

        for test_case in ALERT_MONITORING_TESTS:
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

            alert_reporter.add_result(result)

            status_emoji = (
                "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            )
            print(
                f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)"
            )

            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
