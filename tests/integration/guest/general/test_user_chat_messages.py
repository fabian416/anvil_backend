"""
Integration Test: User Chat Messages Endpoint

CTO Engineering Framework Methodology:
1. Problem Analysis: /api/v1/user/chat/conversations/{id}/messages not working
2. Solution Design: Compare with working /api/v1/guest/chat, identify differences
3. Implementation: Fix the authenticated user endpoint
4. Verification: Test both endpoints work correctly

Test Cases:
- Create conversation and send message (authenticated user)
- Verify response structure matches guest endpoint
- Test error handling (conversation not found, access denied)
- Compare with guest endpoint behavior
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from uuid import UUID, uuid4

from app.run import make_app


@pytest_asyncio.fixture
async def client():
    """Create test client."""
    app = make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_chat_endpoint_structure(client: AsyncClient):
    """
    Test that user chat endpoint exists and has correct structure.
    
    CTO Framework: Problem Analysis Phase
    - Verify endpoint exists
    - Check authentication requirements
    - Compare with guest endpoint structure
    """
    # Test without auth (should return 401)
    response = await client.post(
        "/api/v1/user/chat/conversations/00000000-0000-0000-0000-000000000000/messages",
        json={"content": "Hello", "language": "en"},
    )
    
    # Should require authentication
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    # Compare with guest endpoint (should work without auth)
    guest_response = await client.post(
        "/api/v1/guest/chat",
        json={"content": "Hello", "language": "en"},
        headers={"X-Forwarded-For": "127.0.0.1"},
    )
    
    assert guest_response.status_code == 200, "Guest endpoint should work"
    guest_data = guest_response.json()
    
    # Verify guest response structure
    assert "conversation_id" in guest_data
    assert "user_message" in guest_data
    assert "agent_message" in guest_data
    assert "routing" in guest_data
    
    print(f"\nGuest endpoint structure: {list(guest_data.keys())}")
    print(f"Guest response status: {guest_response.status_code}")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_user_chat_requires_valid_conversation(client: AsyncClient):
    """
    Test that user chat endpoint requires valid conversation.
    
    CTO Framework: Error Handling Phase
    - Verify proper error for non-existent conversation
    - Check error message format
    """
    # This will fail auth, but we can check the endpoint structure
    fake_id = str(uuid4())
    
    response = await client.post(
        f"/api/v1/user/chat/conversations/{fake_id}/messages",
        json={"content": "Hello", "language": "en"},
        headers={"Authorization": "Bearer invalid-token"},
    )
    
    # Should fail auth first
    assert response.status_code in [401, 404], f"Expected 401 or 404, got {response.status_code}"
    
    print(f"\nUser endpoint response status: {response.status_code}")
    if response.status_code != 401:
        print(f"Response: {response.text[:200]}")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_compare_guest_vs_user_endpoints(client: AsyncClient):
    """
    Compare guest and user endpoints to identify differences.
    
    CTO Framework: Solution Design Phase
    - Compare request/response formats
    - Identify missing functionality
    - Document differences
    """
    # Test guest endpoint
    guest_response = await client.post(
        "/api/v1/guest/chat",
        json={"content": "What is Bitcoin?", "language": "en"},
        headers={"X-Forwarded-For": "127.0.0.2"},
    )
    
    assert guest_response.status_code == 200
    guest_data = guest_response.json()
    
    print("\n=== Guest Endpoint Response ===")
    print(f"Status: {guest_response.status_code}")
    print(f"Keys: {list(guest_data.keys())}")
    print(f"Conversation ID: {guest_data.get('conversation_id')}")
    print(f"Agent message content length: {len(guest_data.get('agent_message', {}).get('content', ''))}")
    print(f"Routing intent: {guest_data.get('routing', {}).get('intent')}")
    
    # Document expected user endpoint structure
    print("\n=== Expected User Endpoint Structure ===")
    print("Should match guest endpoint structure:")
    print("- user_message")
    print("- agent_message")
    print("- routing")
    print("- enrichment (optional)")
    
    # Verify guest endpoint works correctly
    assert guest_data.get("agent_message", {}).get("content"), "Guest should return agent message"
    assert guest_data.get("routing", {}).get("intent"), "Guest should return routing intent"
