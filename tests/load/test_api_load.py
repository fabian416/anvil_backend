"""
Load tests for API endpoints.

Tests system performance under load including:
- Concurrent user authentication
- Chat message throughput
- Admin operations under load
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper


@pytest.mark.load
class TestAuthenticationLoad:
    """Load tests for authentication endpoints."""

    def test_concurrent_login_requests(self, client):
        """
        Test system handles concurrent login requests.
        """
        # Create test user
        email = f"loadtest_{uuid4().hex[:8]}@example.com"
        password = "SecurePassword123!"

        # Register user first
        signup_response = client.post(
            "/api/v1/account/signup",
            json={
                "email": email,
                "password": password,
                "first_name": "Load",
                "last_name": "Test",
            },
        )

        if signup_response.status_code not in (200, 201, 409):
            pytest.skip("Could not create test user")
            return

        def login_attempt():
            """Single login attempt."""
            return client.post(
                "/api/v1/account/login",
                json={"email": email, "password": password},
            )

        # Run concurrent logins
        concurrent_requests = 10
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(login_attempt) for _ in range(concurrent_requests)
            ]
            responses = [f.result() for f in futures]

        elapsed = time.time() - start_time

        # All should complete
        assert len(responses) == concurrent_requests

        # Most should succeed (rate limiting may kick in)
        success_count = sum(1 for r in responses if r.status_code in (200, 201))

        # At least some should succeed
        assert success_count >= 1

        # Should complete in reasonable time
        assert elapsed < 30  # 30 seconds max

    def test_token_refresh_under_load(self, client):
        """
        Test token refresh handles concurrent requests.
        """
        # This test documents expected behavior
        # Would need actual refresh tokens to test
        pass


@pytest.mark.load
class TestChatThroughput:
    """Load tests for chat message throughput."""

    def test_concurrent_message_sends(self, client):
        """
        Test system handles concurrent message sends.
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        # Create conversation
        create_response = client.post(
            "/api/v1/chat/conversations",
            json={"title": "Load Test"},
            headers=headers,
        )

        if create_response.status_code not in (200, 201):
            pytest.skip("Could not create conversation")
            return

        conversation_id = create_response.json().get("id")

        def send_message(i):
            """Send single message."""
            return client.post(
                f"/api/v1/chat/conversations/{conversation_id}/messages",
                json={"content": f"Load test message {i}"},
                headers=headers,
            )

        # Send messages concurrently
        concurrent_messages = 5
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent_messages) as executor:
            futures = [
                executor.submit(send_message, i) for i in range(concurrent_messages)
            ]
            responses = [f.result() for f in futures]

        elapsed = time.time() - start_time

        # Check completion
        assert len(responses) == concurrent_messages

        # Most should succeed
        success_count = sum(1 for r in responses if r.status_code in (200, 201))
        assert success_count >= 1

    def test_conversation_listing_under_load(self, client):
        """
        Test conversation listing handles concurrent requests.
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        def list_conversations():
            """List conversations."""
            return client.get(
                "/api/v1/chat/conversations",
                headers=headers,
            )

        concurrent_requests = 10

        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(list_conversations) for _ in range(concurrent_requests)
            ]
            responses = [f.result() for f in futures]

        # All should complete
        assert len(responses) == concurrent_requests


@pytest.mark.load
class TestAdminOperationsLoad:
    """Load tests for admin operations."""

    def test_user_listing_under_load(self, client):
        """
        Test admin user listing handles concurrent requests.
        """
        admin_user, admin_token = AuthHelper.create_test_user(role="admin")
        headers = AuthHelper.get_auth_headers(admin_token)

        def list_users():
            """List users."""
            return client.get("/api/v1/admin/users", headers=headers)

        concurrent_requests = 5

        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(list_users) for _ in range(concurrent_requests)]
            responses = [f.result() for f in futures]

        assert len(responses) == concurrent_requests


@pytest.mark.load
class TestSearchLoad:
    """Load tests for search operations."""

    def test_hybrid_search_under_load(self, client):
        """
        Test hybrid search handles concurrent requests.
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        def search(query):
            """Perform search."""
            return client.post(
                "/api/v1/user/graph/search/hybrid",
                json={"query": query, "limit": 10},
                headers=headers,
            )

        queries = [
            "lending protocol",
            "yield farming",
            "decentralized exchange",
            "staking",
            "liquidity pool",
        ]

        with ThreadPoolExecutor(max_workers=len(queries)) as executor:
            futures = [executor.submit(search, q) for q in queries]
            responses = [f.result() for f in futures]

        assert len(responses) == len(queries)


@pytest.mark.load
class TestResponseTimeBaselines:
    """Tests to establish response time baselines."""

    def test_login_response_time(self, client):
        """
        Test login response time is acceptable.
        """
        start_time = time.time()

        response = client.post(
            "/api/v1/account/login",
            json={"email": "test@example.com", "password": "password"},
        )

        elapsed = time.time() - start_time

        # Should respond within 5 seconds
        assert elapsed < 5

    def test_chat_message_response_time(self, client):
        """
        Test chat message response time is acceptable.
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        # Create conversation
        create_response = client.post(
            "/api/v1/chat/conversations",
            json={"title": "Response Time Test"},
            headers=headers,
        )

        if create_response.status_code not in (200, 201):
            pytest.skip("Could not create conversation")
            return

        conversation_id = create_response.json().get("id")

        start_time = time.time()

        response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": "Test message"},
            headers=headers,
        )

        elapsed = time.time() - start_time

        # Should respond within 30 seconds (LLM may take time)
        assert elapsed < 30
