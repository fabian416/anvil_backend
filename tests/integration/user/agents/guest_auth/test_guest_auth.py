"""
Guest Auth Agent Tests.

Tests restricted feature detection and registration prompts for guest users.
Based on: docs/ceo/agents/guest_auth/shortcuts.md

NOTE: These tests are primarily for the guest chat endpoint, not authenticated.
They test how the guest_auth agent responds to restricted feature requests.
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
)


GUEST_AUTH_TESTS = [
    # Restricted Features (should trigger registration prompt)
    {
        "test_id": "guest_auth_swap_001",
        "input": "swap 100 USDC to ETH",
        "expected_agent": "guest_auth",
        "category": "agent",
        "subcategory": "guest_restricted",
        "user_type": "guest",
    },
    {
        "test_id": "guest_auth_portfolio_001",
        "input": "my portfolio",
        "expected_agent": "guest_auth",
        "category": "agent",
        "subcategory": "guest_restricted",
        "user_type": "guest",
    },
    {
        "test_id": "guest_auth_wallet_001",
        "input": "my wallet",
        "expected_agent": "guest_auth",
        "category": "agent",
        "subcategory": "guest_restricted",
        "user_type": "guest",
    },
    {
        "test_id": "guest_auth_buy_001",
        "input": "buy crypto",
        "expected_agent": "guest_auth",
        "category": "agent",
        "subcategory": "guest_restricted",
        "user_type": "guest",
    },
    {
        "test_id": "guest_auth_lending_001",
        "input": "deposit 100 USDC on Aave",
        "expected_agent": "guest_auth",
        "category": "agent",
        "subcategory": "guest_restricted",
        "user_type": "guest",
    },
    {
        "test_id": "guest_auth_transfer_001",
        "input": "send ETH to 0x1234",
        "expected_agent": "guest_auth",
        "category": "agent",
        "subcategory": "guest_restricted",
        "user_type": "guest",
    },
]


@pytest.fixture(scope="module")
def guest_auth_reporter() -> CSVReporter:
    """Create CSV reporter for guest auth agent tests."""
    reporter = CSVReporter(category="agent_guest_auth")
    yield reporter
    if reporter.results:
        reporter.write_csv()
        reporter.write_summary()
        reporter.print_summary()


@pytest.mark.asyncio
class TestGuestAuthAgent:
    """Test Guest Auth agent functionality.
    
    Note: These tests require a guest client, not authenticated client.
    The tests verify that restricted features trigger registration prompts.
    """
    
    async def test_guest_restricted_features(self, guest_client, guest_auth_reporter):
        """Test that restricted features trigger registration prompts for guests."""
        import asyncio
        
        for test_case in GUEST_AUTH_TESTS:
            # For guest tests, we use the guest chat endpoint
            # POST /api/v1/guest/chat
            response = await guest_client.post(
                "/api/v1/guest/chat",
                json={
                    "message": test_case["input"],
                    "language": "en",
                },
                timeout=90.0,
            )
            
            response_time = 0  # Guest endpoint doesn't return timing
            
            if response.status_code == 200:
                data = response.json()
                parsed = {
                    "content": data.get("response", ""),
                    "agents_used": data.get("agent_type", ""),
                    "error": False,
                }
            else:
                parsed = {
                    "content": "",
                    "agents_used": "",
                    "error": True,
                    "error_message": str(response.status_code),
                }
            
            expected_agent = test_case.get("expected_agent", "")
            actual_agents = parsed.get("agents_used", "")
            has_error = parsed.get("error", False)
            
            # For guest_auth, success means the response contains registration prompt
            content = parsed.get("content", "").lower()
            has_registration_prompt = any(word in content for word in [
                "sign up", "register", "create account", "log in", "signup"
            ])
            
            if has_error:
                status = "FAIL"
            elif expected_agent and expected_agent in actual_agents:
                status = "PASS"
            elif has_registration_prompt:
                status = "PASS"  # Registration prompt shown = correct behavior
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
                user_type="guest",
                status=status,
            )
            
            guest_auth_reporter.add_result(result)
            
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)")
            
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
