"""
Tax Optimizer Agent Tests for Authenticated Users.

Tests tax-loss harvesting, capital gains, and cost basis calculations.
Based on: docs/ceo/agents/tax_optimizer/shortcuts.md
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


TAX_OPTIMIZER_TESTS = [
    # Tax-Loss Harvesting
    {
        "test_id": "tax_harvest_001",
        "input": "tax loss harvesting opportunities",
        "expected_agent": "tax_optimizer",
        "category": "agent",
        "subcategory": "tax_harvest",
    },
    {
        "test_id": "tax_harvest_002",
        "input": "find tax loss positions",
        "expected_agent": "tax_optimizer",
        "category": "agent",
        "subcategory": "tax_harvest",
    },
    
    # Capital Gains
    {
        "test_id": "tax_gains_001",
        "input": "calculate my capital gains",
        "expected_agent": "tax_optimizer",
        "category": "agent",
        "subcategory": "tax_gains",
    },
    {
        "test_id": "tax_gains_002",
        "input": "show my unrealized gains",
        "expected_agent": "tax_optimizer",
        "category": "agent",
        "subcategory": "tax_gains",
    },
    {
        "test_id": "tax_gains_003",
        "input": "short term vs long term gains",
        "expected_agent": "tax_optimizer",
        "category": "agent",
        "subcategory": "tax_gains",
    },
    
    # Cost Basis
    {
        "test_id": "tax_basis_001",
        "input": "what cost basis method should I use",
        "expected_agent": "tax_optimizer",
        "category": "agent",
        "subcategory": "tax_basis",
    },
    {
        "test_id": "tax_basis_002",
        "input": "FIFO vs LIFO for taxes",
        "expected_agent": "tax_optimizer",
        "category": "agent",
        "subcategory": "tax_basis",
    },
    
    # Tax Strategy
    {
        "test_id": "tax_strategy_001",
        "input": "optimize my taxes",
        "expected_agent": "tax_optimizer",
        "category": "agent",
        "subcategory": "tax_strategy",
    },
    {
        "test_id": "tax_strategy_002",
        "input": "year end tax planning",
        "expected_agent": "tax_optimizer",
        "category": "agent",
        "subcategory": "tax_strategy",
    },
]


@pytest.fixture(scope="module")
def tax_reporter() -> CSVReporter:
    """Create CSV reporter for tax optimizer agent tests."""
    reporter = CSVReporter(category="agent_tax_optimizer")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestTaxOptimizerAgent:
    """Test Tax Optimizer agent functionality."""
    
    async def test_tax_queries(self, authenticated_client, tax_reporter):
        """Test tax optimization queries."""
        import asyncio
        
        for test_case in TAX_OPTIMIZER_TESTS:
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
            
            tax_reporter.add_result(result)
            
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)")
            
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
