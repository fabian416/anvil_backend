"""
Risk Analyzer Agent Tests for Authenticated Users.

Tests protocol risk analysis, portfolio risk, and DeFi risk assessment.
Based on: docs/ceo/agents/risk_analyzer/shortcuts.md
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


RISK_ANALYZER_TESTS = [
    # Protocol Risk
    {
        "test_id": "risk_protocol_001",
        "input": "analyze risk of Aave",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk_protocol",
    },
    {
        "test_id": "risk_protocol_002",
        "input": "is Compound safe",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk_protocol",
    },
    {
        "test_id": "risk_protocol_003",
        "input": "Uniswap risk assessment",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk_protocol",
    },
    
    # DeFi Risk
    {
        "test_id": "risk_defi_001",
        "input": "risk of yield farming",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk_defi",
    },
    {
        "test_id": "risk_defi_002",
        "input": "liquidity mining risks",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk_defi",
    },
    
    # Portfolio Risk
    {
        "test_id": "risk_portfolio_001",
        "input": "analyze my portfolio risk",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk_portfolio",
    },
    {
        "test_id": "risk_portfolio_002",
        "input": "how risky is my portfolio",
        "expected_agent": "risk_analyzer",
        "category": "agent",
        "subcategory": "risk_portfolio",
    },
]


@pytest.fixture(scope="module")
def risk_reporter() -> CSVReporter:
    """Create CSV reporter for risk analyzer agent tests."""
    reporter = CSVReporter(category="agent_risk_analyzer")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestRiskAnalyzerAgent:
    """Test Risk Analyzer agent functionality."""
    
    async def test_risk_queries(self, authenticated_client, risk_reporter):
        """Test risk analysis queries."""
        import asyncio
        
        for test_case in RISK_ANALYZER_TESTS:
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
            
            risk_reporter.add_result(result)
            
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)")
            
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
