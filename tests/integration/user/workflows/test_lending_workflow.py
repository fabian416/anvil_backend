"""
Lending Workflow Tests for Authenticated Users.

Tests deposit flows, vault selection, and lending operations.
Uses LLM (Vertex AI) validation for semantic output verification.
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
    validate_with_llm,
)


LENDING_TESTS = [
    # Basic Deposits
    {
        "test_id": "lend_basic_001",
        "input": "deposit 1000 USDC",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_basic",
    },
    {
        "test_id": "lend_basic_002",
        "input": "lend 0.5 ETH",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_basic",
    },
    {
        "test_id": "lend_basic_003",
        "input": "earn yield on 500 DAI",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_basic",
    },
    {
        "test_id": "lend_basic_004",
        "input": "deposit USDT",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_basic",
    },
    {
        "test_id": "lend_basic_005",
        "input": "supply 100 USDC to earn interest",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_basic",
    },
    # Protocol-Specific
    {
        "test_id": "lend_protocol_001",
        "input": "deposit into morpho",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_protocol",
    },
    {
        "test_id": "lend_protocol_002",
        "input": "lend on aave",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_protocol",
    },
    {
        "test_id": "lend_protocol_003",
        "input": "supply USDC to compound",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_protocol",
    },
    # Vault Selection
    {
        "test_id": "lend_vault_001",
        "input": "show USDC vaults",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_vault",
    },
    {
        "test_id": "lend_vault_002",
        "input": "best vault for ETH",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_vault",
    },
    # Edge Cases
    {
        "test_id": "lend_edge_001",
        "input": "deposit",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_edge",
    },
    {
        "test_id": "lend_edge_002",
        "input": "lend",
        "expected_agent": "lending_workflow",
        "category": "workflow",
        "subcategory": "lending_edge",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestLendingWorkflow:
    """Tests for Lending workflow agent with LLM validation."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self, authenticated_client, conversation_id, csv_reporter, llm_validator
    ):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.conversation_id = conversation_id
        self.reporter = csv_reporter
        self.llm_validator = llm_validator

    @pytest.mark.parametrize("test_case", LENDING_TESTS, ids=lambda t: t["test_id"])
    async def test_lending(self, test_case: dict):
        """Test lending workflow routing and response with LLM validation."""
        response_data, response_time_ms = await send_message(
            self.client,
            self.conversation_id,
            test_case["input"],
        )

        # LLM Validation
        llm_validation = None
        if not response_data.get("error"):
            parsed = parse_response(response_data)
            llm_validation = await validate_with_llm(
                llm_validator=self.llm_validator,
                test_name=test_case["test_id"],
                user_input=test_case["input"],
                agent_output=parsed.get("content", ""),
                expected_behavior="Response should present lending/deposit details including vaults, APY rates, and confirmation or ask for clarification.",
                additional_context={
                    "test_category": "lending_workflow",
                    "subcategory": test_case.get("subcategory", ""),
                    "user_type": "authenticated",
                },
            )

        result = create_test_result(
            test_id=test_case["test_id"],
            test_case=test_case,
            response_data=response_data,
            response_time_ms=response_time_ms,
            conversation_id=self.conversation_id,
            llm_validation=llm_validation,
        )

        self.reporter.add_result(result)

        # Assertions
        assert not response_data.get("error"), f"Request failed: {response_data}"

        parsed = parse_response(response_data)
        content = parsed.get("content", "").lower()
        agents = parsed.get("agents_used", "")

        # Verify lending-related response
        assert any(
            indicator in content or indicator in agents.lower()
            for indicator in [
                "deposit",
                "lend",
                "vault",
                "apy",
                "yield",
                "earn",
                "supply",
            ]
        ), f"Lending query should return lending-related response: {content[:200]}"

    async def test_lending_full_flow(self, authenticated_client, csv_reporter):
        """Test complete lending flow with vault selection."""
        # Create fresh conversation
        response = await authenticated_client.post(
            "/api/v1/conversations",
            json={"title": "Lending Flow Test"},
        )
        assert response.status_code in (200, 201)
        conv_id = response.json().get("id")

        # Step 1: Request deposit
        response_data, time1 = await send_message(
            authenticated_client,
            conv_id,
            "deposit 1000 USDC",
        )

        result1 = create_test_result(
            test_id="lend_flow_step1",
            test_case={
                "input": "deposit 1000 USDC",
                "expected_agent": "lending_workflow",
                "category": "workflow",
                "subcategory": "lending_flow",
                "is_multi_step": True,
                "step_number": 1,
                "total_steps": 2,
            },
            response_data=response_data,
            response_time_ms=time1,
            conversation_id=conv_id,
        )
        csv_reporter.add_result(result1)

        assert not response_data.get("error")

        # Step 2: Confirm
        response_data, time2 = await send_message(
            authenticated_client,
            conv_id,
            "yes",
        )

        result2 = create_test_result(
            test_id="lend_flow_step2",
            test_case={
                "input": "yes",
                "expected_agent": "lending_workflow",
                "category": "workflow",
                "subcategory": "lending_flow",
                "is_multi_step": True,
                "step_number": 2,
                "total_steps": 2,
                "requires_execute": True,
            },
            response_data=response_data,
            response_time_ms=time2,
            conversation_id=conv_id,
        )
        csv_reporter.add_result(result2)
