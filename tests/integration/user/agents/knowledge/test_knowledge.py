"""
Knowledge Agent Tests for Authenticated Users.

Tests DeFi concepts, protocol information, and educational queries.
Based on: docs/ceo/agents/knowledge/shortcuts.md
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


KNOWLEDGE_TESTS = [
    # DeFi Concepts
    {
        "test_id": "knowledge_concept_001",
        "input": "what is defi",
        "expected_agent": "knowledge",
        "category": "agent",
        "subcategory": "knowledge_concept",
    },
    {
        "test_id": "knowledge_concept_002",
        "input": "explain impermanent loss",
        "expected_agent": "knowledge",
        "category": "agent",
        "subcategory": "knowledge_concept",
    },
    {
        "test_id": "knowledge_concept_003",
        "input": "what is a liquidity pool",
        "expected_agent": "knowledge",
        "category": "agent",
        "subcategory": "knowledge_concept",
    },
    {
        "test_id": "knowledge_concept_004",
        "input": "how does yield farming work",
        "expected_agent": "knowledge",
        "category": "agent",
        "subcategory": "knowledge_concept",
    },
    
    # Protocol Information
    {
        "test_id": "knowledge_protocol_001",
        "input": "how does Aave work",
        "expected_agent": "knowledge",
        "category": "agent",
        "subcategory": "knowledge_protocol",
    },
    {
        "test_id": "knowledge_protocol_002",
        "input": "what is Uniswap",
        "expected_agent": "knowledge",
        "category": "agent",
        "subcategory": "knowledge_protocol",
    },
    {
        "test_id": "knowledge_protocol_003",
        "input": "explain Compound protocol",
        "expected_agent": "knowledge",
        "category": "agent",
        "subcategory": "knowledge_protocol",
    },
    
    # Educational
    {
        "test_id": "knowledge_education_001",
        "input": "what is staking",
        "expected_agent": "knowledge",
        "category": "agent",
        "subcategory": "knowledge_education",
    },
    {
        "test_id": "knowledge_education_002",
        "input": "difference between CEX and DEX",
        "expected_agent": "knowledge",
        "category": "agent",
        "subcategory": "knowledge_education",
    },
]


@pytest.fixture(scope="module")
def knowledge_reporter() -> CSVReporter:
    """Create CSV reporter for knowledge agent tests."""
    reporter = CSVReporter(category="agent_knowledge")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestKnowledgeAgent:
    """Test Knowledge agent functionality."""
    
    async def test_knowledge_queries(self, authenticated_client, knowledge_reporter):
        """Test knowledge/educational queries."""
        import asyncio
        
        for test_case in KNOWLEDGE_TESTS:
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
            
            knowledge_reporter.add_result(result)
            
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)")
            
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
