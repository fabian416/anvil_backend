"""
Security Auditor Agent Tests for Authenticated Users.

Tests smart contract security analysis and vulnerability detection.
Based on: docs/ceo/agents/security_auditor/shortcuts.md
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


SECURITY_AUDITOR_TESTS = [
    # Contract Security
    {
        "test_id": "security_contract_001",
        "input": "audit this contract 0x1234",
        "expected_agent": "security_auditor",
        "category": "enterprise",
        "subcategory": "security_contract",
    },
    {
        "test_id": "security_contract_002",
        "input": "is this contract safe",
        "expected_agent": "security_auditor",
        "category": "enterprise",
        "subcategory": "security_contract",
    },
    # Vulnerability Detection
    {
        "test_id": "security_vuln_001",
        "input": "check for reentrancy vulnerabilities",
        "expected_agent": "security_auditor",
        "category": "enterprise",
        "subcategory": "security_vulnerability",
    },
    {
        "test_id": "security_vuln_002",
        "input": "smart contract security analysis",
        "expected_agent": "security_auditor",
        "category": "enterprise",
        "subcategory": "security_vulnerability",
    },
    # Best Practices
    {
        "test_id": "security_best_001",
        "input": "security best practices for DeFi",
        "expected_agent": "security_auditor",
        "category": "enterprise",
        "subcategory": "security_best_practices",
    },
]


@pytest.fixture(scope="module")
def security_reporter() -> CSVReporter:
    """Create CSV reporter for security auditor agent tests."""
    reporter = CSVReporter(category="agent_security_auditor")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestSecurityAuditorAgent:
    """Test Security Auditor agent functionality."""

    async def test_security_queries(self, authenticated_client, security_reporter):
        """Test security audit queries."""
        import asyncio

        for test_case in SECURITY_AUDITOR_TESTS:
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

            security_reporter.add_result(result)

            status_emoji = (
                "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            )
            print(
                f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)"
            )

            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
