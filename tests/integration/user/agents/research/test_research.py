"""
Research Agent Tests for Authenticated Users.

Tests deep protocol analysis with Perplexity integration.
Based on: docs/ceo/agents/research/shortcuts.md
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


RESEARCH_TESTS = [
    # Protocol Analysis
    {
        "test_id": "research_protocol_001",
        "input": "deep dive on Aave V3",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research_protocol",
    },
    {
        "test_id": "research_protocol_002",
        "input": "research Uniswap governance",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research_protocol",
    },
    {
        "test_id": "research_protocol_003",
        "input": "analyze Morpho protocol",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research_protocol",
    },
    # Market Research
    {
        "test_id": "research_market_001",
        "input": "research DeFi trends 2026",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research_market",
    },
    {
        "test_id": "research_market_002",
        "input": "deep analysis of L2 ecosystem",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research_market",
    },
    # Technical Analysis
    {
        "test_id": "research_technical_001",
        "input": "research liquidity dynamics in DEXes",
        "expected_agent": "research",
        "category": "agent",
        "subcategory": "research_technical",
    },
]


@pytest.fixture(scope="module")
def research_reporter() -> CSVReporter:
    """Create CSV reporter for research agent tests."""
    reporter = CSVReporter(category="agent_research")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestResearchAgent:
    """Test Research agent functionality."""

    async def test_research_queries(self, authenticated_client, research_reporter):
        """Test research queries with Perplexity integration."""
        import asyncio

        for test_case in RESEARCH_TESTS:
            conv_id = await create_conversation(
                authenticated_client, title=f"Test {test_case['test_id']}"
            )

            response_data, response_time = await send_message(
                authenticated_client,
                conv_id,
                test_case["input"],
                timeout=120.0,  # Research can take longer
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
                sources=parsed.get("sources", ""),
                response_time_ms=response_time,
                user_type="authenticated",
                status=status,
                conversation_id=conv_id,
            )

            research_reporter.add_result(result)

            status_emoji = (
                "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            )
            print(
                f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)"
            )

            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
