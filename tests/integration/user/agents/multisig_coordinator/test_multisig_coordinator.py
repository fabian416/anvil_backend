"""
Multi-Sig Coordinator Agent Tests for Authenticated Users.

Tests treasury management and Gnosis Safe proposal workflows.
Based on: docs/ceo/agents/multisig_coordinator/shortcuts.md
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


MULTISIG_COORDINATOR_TESTS = [
    # Create Proposals
    {
        "test_id": "multisig_proposal_001",
        "input": "send 10000 USDC to 0x1234 for marketing",
        "expected_agent": "multisig_coordinator",
        "category": "enterprise",
        "subcategory": "multisig_proposal",
    },
    {
        "test_id": "multisig_proposal_002",
        "input": "create treasury proposal for 50000 USDC",
        "expected_agent": "multisig_coordinator",
        "category": "enterprise",
        "subcategory": "multisig_proposal",
    },
    
    # Check Status
    {
        "test_id": "multisig_status_001",
        "input": "check pending approvals",
        "expected_agent": "multisig_coordinator",
        "category": "enterprise",
        "subcategory": "multisig_status",
    },
    {
        "test_id": "multisig_status_002",
        "input": "show my proposals",
        "expected_agent": "multisig_coordinator",
        "category": "enterprise",
        "subcategory": "multisig_status",
    },
    
    # Treasury Management
    {
        "test_id": "multisig_treasury_001",
        "input": "show treasury balance",
        "expected_agent": "multisig_coordinator",
        "category": "enterprise",
        "subcategory": "multisig_treasury",
    },
    {
        "test_id": "multisig_treasury_002",
        "input": "list recent treasury transactions",
        "expected_agent": "multisig_coordinator",
        "category": "enterprise",
        "subcategory": "multisig_treasury",
    },
    
    # Budget Management
    {
        "test_id": "multisig_budget_001",
        "input": "what's our marketing budget",
        "expected_agent": "multisig_coordinator",
        "category": "enterprise",
        "subcategory": "multisig_budget",
    },
]


@pytest.fixture(scope="module")
def multisig_reporter() -> CSVReporter:
    """Create CSV reporter for multisig coordinator agent tests."""
    reporter = CSVReporter(category="agent_multisig_coordinator")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestMultiSigCoordinatorAgent:
    """Test Multi-Sig Coordinator agent functionality."""
    
    async def test_multisig_queries(self, authenticated_client, multisig_reporter):
        """Test multi-sig treasury management queries."""
        import asyncio
        
        for test_case in MULTISIG_COORDINATOR_TESTS:
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
            
            multisig_reporter.add_result(result)
            
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)")
            
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
