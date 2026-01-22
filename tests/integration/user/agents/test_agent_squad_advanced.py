"""
Agent Squad Advanced Tests for Authenticated Users.

Tests multi-agent coordination, context preservation, and agent handoffs.

Migrated from test_user_agent_squad_advanced.py to use new test infrastructure.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ..conftest import (
    CSVReporter,
    TestResult,
    send_message,
    parse_response,
    create_test_result,
    create_conversation,
)


AGENT_SQUAD_SINGLE_TURN = [
    {
        "test_id": "squad_handoff_001",
        "input": "What's the current ETH price and should I buy or provide liquidity?",
        "expected_agent": "",  # Multi-agent
        "category": "agent_squad",
        "subcategory": "handoff_transition",
    },
    {
        "test_id": "squad_parallel_001",
        "input": "Analyze Bitcoin from technical, fundamental, and sentiment perspectives",
        "expected_agent": "",  # Multi-agent
        "category": "agent_squad",
        "subcategory": "parallel_coordination",
    },
    {
        "test_id": "squad_routing_001",
        "input": "I want to explore DeFi yields but I'm worried about smart contract risks. What should I consider for Curve vs Convex?",
        "expected_agent": "",  # Multi-agent (yield + risk)
        "category": "agent_squad",
        "subcategory": "specialization_routing",
    },
    {
        "test_id": "squad_fallback_001",
        "input": "What's happening with crypto today?",
        "expected_agent": "hunter_ai",
        "category": "agent_squad",
        "subcategory": "fallback_handling",
    },
]


CONTEXT_PRESERVATION_FLOWS = [
    {
        "test_id": "squad_context_001",
        "name": "Aave Discussion Context",
        "steps": [
            {"input": "Tell me about Aave lending protocol"},
            {"input": "What are its main risks?"},
            {"input": "Compare it to Compound"},
        ],
        "category": "agent_squad",
        "subcategory": "context_preservation",
    },
    {
        "test_id": "squad_memory_001",
        "name": "Uniswap Long Context",
        "steps": [
            {"input": "Tell me about Uniswap V3"},
            {"input": "How does concentrated liquidity work?"},
            {"input": "What are the fee tiers?"},
            {"input": "Compare it to V2"},
            {"input": "What about capital efficiency?"},
            {"input": "Based on everything we discussed, should a beginner start with V2 or V3?"},
        ],
        "category": "agent_squad",
        "subcategory": "long_context_memory",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestAgentSquadSingleTurn:
    """Tests for single-turn agent squad coordination."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, conversation_id, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("test_case", AGENT_SQUAD_SINGLE_TURN, ids=lambda t: t["test_id"])
    async def test_agent_squad_coordination(self, test_case: dict):
        """Test agent squad routing and coordination."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
        )
        
        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
        )
        
        self.reporter.add_result(result)
        
        # Assertions
        assert not response_data.get("error"), f"Request failed: {response_data}"
        
        parsed = parse_response(response_data)
        content = parsed.get("content", "")
        
        # Agent squad responses should be comprehensive
        assert len(content) > 80, f"Agent squad response too short: {content[:200]}"


@pytest.mark.asyncio
@pytest.mark.integration
class TestAgentSquadContextPreservation:
    """Tests for context preservation across agent handoffs."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, csv_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = csv_reporter
    
    @pytest.mark.parametrize("flow", CONTEXT_PRESERVATION_FLOWS, ids=lambda f: f["test_id"])
    async def test_context_preservation(self, flow: dict):
        """Test context is preserved across multiple turns."""
        conv_id = await create_conversation(
            self.client,
            title=f"Context Test: {flow['name']}"
        )
        
        steps = flow["steps"]
        total_steps = len(steps)
        
        for step_num, step in enumerate(steps, 1):
            response_data, response_time_ms = await send_message(
                self.client,
                conv_id,
                step["input"],
            )
            
            step_test_case = {
                "input": step["input"],
                "expected_agent": "",
                "category": flow["category"],
                "subcategory": flow["subcategory"],
                "is_multi_step": True,
                "step_number": step_num,
                "total_steps": total_steps,
            }
            
            result = create_test_result(
                test_id=f"{flow['test_id']}_step{step_num}",
                test_case=step_test_case,
                response_data=response_data,
                response_time_ms=response_time_ms,
                conversation_id=conv_id,
            )
            
            self.reporter.add_result(result)
            
            assert not response_data.get("error"), f"Step {step_num} failed: {response_data}"
            
            parsed = parse_response(response_data)
            content = parsed.get("content", "")
            
            # Each response should be meaningful
            assert len(content) > 50, f"Step {step_num} response too short: {content[:200]}"
        
        # Final response should demonstrate context awareness
        final_content = parsed.get("content", "").lower()
        
        if "uniswap" in flow["name"].lower():
            # Should reference V2/V3 comparison from earlier turns
            assert any(
                word in final_content
                for word in ["v2", "v3", "beginner", "recommend", "suggest", "start"]
            ), "Final response should provide recommendation based on context"
