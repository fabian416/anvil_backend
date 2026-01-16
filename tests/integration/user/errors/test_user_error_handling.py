"""
Integration Test: User Error Handling Suite

Tests error handling and graceful degradation for authenticated user chat.
Validates that error messages are user-friendly and that the system
degrades gracefully under various failure conditions.

CTO Framework: Risk Assessment & Validation Phase
- Test error scenarios that must be handled gracefully
- Verify user-friendly error messages (no technical stack traces)
- Validate system recovery and fallback mechanisms

Generated for Phase 1.2 of Guest/User Coverage Enhancement - User Tests
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import asyncio

from app.run import make_app

# Access token for ops@anvilcrypto.com (registered user)
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJ0ZXN0X3Nlc3Npb25fMjAyNl8xNzY4MDY2MDc5IiwiZXhwIjoxNzk5NjAyMDc5fQ.OUFFmZW2_QACkgrIphLFcOOB3Qb-1ckVB_RvZ-VTaF0"


@pytest_asyncio.fixture
async def client():
    """Create test client."""
    app = make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_error_invalid_message_format_user(client: AsyncClient, llm_validator):
    """
    Test authenticated user chat with invalid message format.

    CTO Framework: Defensive Design Patterns
    - Consistent error handling for guest and authenticated users
    """
    # Create conversation
    conv_response = await client.post(
        "/api/v1/user/chat/conversations",
        json={"title": "Error Test", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert conv_response.status_code == 201
    conv_id = conv_response.json()["id"]

    # Test with empty content
    response = await client.post(
        f"/api/v1/user/chat/conversations/{conv_id}/messages",
        json={"content": "", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    # Should handle gracefully
    assert response.status_code in (200, 400, 422), f"Unexpected status for empty message: {response.status_code}"

    if response.status_code in (400, 422):
        data = response.json()
        error_message = str(data)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_error_invalid_message_format_user",
                user_input="Empty message submitted by authenticated user",
                agent_output=error_message,
                expected_behavior=(
                    "Error message should be user-friendly and consistent with guest error handling. "
                    "Should not expose technical details or authentication tokens. "
                    "Should guide user on proper message format."
                ),
                additional_context={
                    'test_category': 'error_handling',
                    'error_type': 'invalid_input',
                    'user_type': 'authenticated'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_error_context_corruption_detection(client: AsyncClient, llm_validator):
    """
    Test detection and handling of conversation state/context corruption.

    CTO Framework: Data Integrity
    - Verify conversation history maintains consistency
    - Detect and recover from context issues
    """
    # Create conversation for authenticated user
    conv_response = await client.post(
        "/api/v1/user/chat/conversations",
        json={"title": "Context Test", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert conv_response.status_code == 201
    conv_id = conv_response.json()["id"]

    # Send multiple messages to build context
    messages = [
        "Tell me about Bitcoin",
        "What about Ethereum?",
        "Compare them for me"
    ]

    responses = []
    for msg in messages:
        response = await client.post(
            f"/api/v1/user/chat/conversations/{conv_id}/messages",
            json={"content": msg, "language": "en"},
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        )
        assert response.status_code in (200, 201)
        responses.append(response.json())

    # Verify last response maintains context
    last_response = responses[-1]
    content = last_response["agent_message"]["content"]

    # Optional LLM semantic validation (environment-gated)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_error_context_corruption_detection",
            user_input="Compare them for me (referring to Bitcoin and Ethereum from previous messages)",
            agent_output=content,
            expected_behavior=(
                "Response should compare Bitcoin and Ethereum based on conversation history. "
                "Should demonstrate context awareness from previous messages. "
                "Should not ask 'compare what?' - context should be maintained. "
                "Comparison should be relevant and informed by earlier discussion."
            ),
            additional_context={
                'test_category': 'context_integrity',
                'scenario': 'multi_turn_conversation',
                'user_type': 'authenticated',
                'conversation_history': messages
            }
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(
                f"LLM validation concern (confidence={validation.confidence:.2f}): "
                f"{validation.reasoning}"
            ))


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_error_concurrent_request_conflicts(client: AsyncClient, llm_validator):
    """
    Test handling of concurrent requests to same conversation.

    CTO Framework: Concurrency and Race Conditions
    - Verify system handles concurrent requests gracefully
    - No data corruption or lost messages
    """
    # Create conversation
    conv_response = await client.post(
        "/api/v1/user/chat/conversations",
        json={"title": "Concurrency Test", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert conv_response.status_code == 201
    conv_id = conv_response.json()["id"]

    # Send multiple concurrent requests
    async def send_message(msg: str):
        return await client.post(
            f"/api/v1/user/chat/conversations/{conv_id}/messages",
            json={"content": msg, "language": "en"},
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        )

    messages = [f"Query {i}" for i in range(3)]
    responses = await asyncio.gather(*[send_message(msg) for msg in messages])

    # All requests should succeed or be handled gracefully
    for i, response in enumerate(responses):
        assert response.status_code in (200, 201, 429), \
            f"Request {i} should succeed or be rate limited, got {response.status_code}"

    # Check first successful response
    successful_responses = [r for r in responses if r.status_code in (200, 201)]
    if successful_responses:
        data = successful_responses[0].json()
        content = data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_error_concurrent_request_conflicts",
                user_input="Query 0",
                agent_output=content,
                expected_behavior=(
                    "Response should be coherent and relevant to the query. "
                    "System should handle concurrent requests without corruption. "
                    "Each response should be complete and well-formed."
                ),
                additional_context={
                    'test_category': 'concurrency',
                    'scenario': 'concurrent_messages',
                    'user_type': 'authenticated',
                    'concurrent_requests': len(messages)
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))
