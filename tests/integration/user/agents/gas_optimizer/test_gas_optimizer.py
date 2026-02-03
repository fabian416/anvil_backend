"""
Gas Optimizer Agent Tests for Authenticated Users.

Tests gas price queries, timing optimization, and L2 recommendations.
Based on: docs/ceo/agents/gas_optimizer/shortcuts.md
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


GAS_OPTIMIZER_TESTS = [
    # Gas Prices
    {
        "test_id": "gas_price_001",
        "input": "current gas prices",
        "expected_agent": "gas_optimizer",
        "category": "agent",
        "subcategory": "gas_price",
    },
    {
        "test_id": "gas_price_002",
        "input": "what are gas fees right now",
        "expected_agent": "gas_optimizer",
        "category": "agent",
        "subcategory": "gas_price",
    },
    {
        "test_id": "gas_price_003",
        "input": "Ethereum gas price",
        "expected_agent": "gas_optimizer",
        "category": "agent",
        "subcategory": "gas_price",
    },
    # Timing
    {
        "test_id": "gas_timing_001",
        "input": "best time for gas",
        "expected_agent": "gas_optimizer",
        "category": "agent",
        "subcategory": "gas_timing",
    },
    {
        "test_id": "gas_timing_002",
        "input": "when is gas cheapest",
        "expected_agent": "gas_optimizer",
        "category": "agent",
        "subcategory": "gas_timing",
    },
    {
        "test_id": "gas_timing_003",
        "input": "should I wait for lower gas",
        "expected_agent": "gas_optimizer",
        "category": "agent",
        "subcategory": "gas_timing",
    },
    # L2 Recommendations
    {
        "test_id": "gas_l2_001",
        "input": "compare gas on L2s",
        "expected_agent": "gas_optimizer",
        "category": "agent",
        "subcategory": "gas_l2",
    },
    {
        "test_id": "gas_l2_002",
        "input": "which L2 has lowest fees",
        "expected_agent": "gas_optimizer",
        "category": "agent",
        "subcategory": "gas_l2",
    },
]


@pytest.fixture(scope="module")
def gas_reporter() -> CSVReporter:
    """Create CSV reporter for gas optimizer agent tests."""
    reporter = CSVReporter(category="agent_gas_optimizer")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestGasOptimizerAgent:
    """Test Gas Optimizer agent functionality."""

    async def test_gas_queries(self, authenticated_client, gas_reporter):
        """Test gas optimization queries."""
        import asyncio

        for test_case in GAS_OPTIMIZER_TESTS:
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

            gas_reporter.add_result(result)

            status_emoji = (
                "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            )
            print(
                f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)"
            )

            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
