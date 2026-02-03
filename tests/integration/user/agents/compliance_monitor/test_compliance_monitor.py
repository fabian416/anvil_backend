"""
Compliance Monitor Agent Tests for Authenticated Users.

Tests AML/KYC wallet screening and OFAC sanctions checking.
Based on: docs/ceo/agents/compliance_monitor/shortcuts.md
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


COMPLIANCE_MONITOR_TESTS = [
    # Wallet Screening
    {
        "test_id": "compliance_screen_001",
        "input": "screen wallet 0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "expected_agent": "compliance_monitor",
        "category": "enterprise",
        "subcategory": "compliance_screening",
    },
    {
        "test_id": "compliance_screen_002",
        "input": "check compliance for 0x1234567890abcdef",
        "expected_agent": "compliance_monitor",
        "category": "enterprise",
        "subcategory": "compliance_screening",
    },
    {
        "test_id": "compliance_screen_003",
        "input": "is this address sanctioned 0xABC",
        "expected_agent": "compliance_monitor",
        "category": "enterprise",
        "subcategory": "compliance_screening",
    },
    # AML/KYC
    {
        "test_id": "compliance_aml_001",
        "input": "run AML check on 0x1234",
        "expected_agent": "compliance_monitor",
        "category": "enterprise",
        "subcategory": "compliance_aml",
    },
    {
        "test_id": "compliance_aml_002",
        "input": "KYC status for wallet",
        "expected_agent": "compliance_monitor",
        "category": "enterprise",
        "subcategory": "compliance_aml",
    },
    # Risk Scoring
    {
        "test_id": "compliance_risk_001",
        "input": "what's the risk score for 0x1234",
        "expected_agent": "compliance_monitor",
        "category": "enterprise",
        "subcategory": "compliance_risk",
    },
    {
        "test_id": "compliance_risk_002",
        "input": "is 0x1234 safe to transact with",
        "expected_agent": "compliance_monitor",
        "category": "enterprise",
        "subcategory": "compliance_risk",
    },
]


@pytest.fixture(scope="module")
def compliance_reporter() -> CSVReporter:
    """Create CSV reporter for compliance monitor agent tests."""
    reporter = CSVReporter(category="agent_compliance_monitor")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestComplianceMonitorAgent:
    """Test Compliance Monitor agent functionality."""

    async def test_compliance_queries(self, authenticated_client, compliance_reporter):
        """Test compliance monitoring queries."""
        import asyncio

        for test_case in COMPLIANCE_MONITOR_TESTS:
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

            compliance_reporter.add_result(result)

            status_emoji = (
                "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            )
            print(
                f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)"
            )

            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
