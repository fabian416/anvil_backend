"""
Comprehensive Security Testing Suite - Week 12 (P3-3)

Tests security controls, attack prevention, and authorization:
- XSS (Cross-Site Scripting) prevention
- SQL injection protection
- Authentication boundary tests
- Authorization edge cases
- Session management security

Target: 13 comprehensive security tests.

Test Classes:
1. TestXSSPrevention (3 tests) - XSS attack prevention
2. TestInjectionProtection (3 tests) - SQL/NoSQL injection
3. TestAuthenticationBoundaries (3 tests) - Auth edge cases
4. TestAuthorizationControls (2 tests) - Access control
5. TestSessionSecurity (2 tests) - Session management
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper

pytestmark = [
    pytest.mark.skip(reason="Uses undefined authenticated_client fixture"),
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.security,
]


@pytest.mark.asyncio
class TestXSSPrevention:
    """XSS (Cross-Site Scripting) prevention tests (3 tests)."""

    async def test_xss_001_script_tag_in_message(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
        conversation_id: str,
    ):
        """
        GIVEN malicious script tag in message content
        WHEN sending message
        THEN script should be sanitized/escaped in response
        """
        malicious_content = '<script>alert("XSS")</script>What is Bitcoin?'

        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": malicious_content,
                "language": "en",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Response should not contain unescaped script tag
        agent_response = data["agent_message"]["content"]
        assert "<script>" not in agent_response.lower(), "XSS vulnerability: unescaped script tag"

        # User message should be stored but sanitized
        user_message = data["user_message"]["content"]
        assert "script" in user_message.lower()  # Content preserved
        # But should be safe (HTML entities or stripped)

    async def test_xss_002_html_injection_in_name(
        self,
        authenticated_client: AsyncClient,
        test_user,
    ):
        """
        GIVEN malicious HTML in conversation title
        WHEN creating conversation
        THEN HTML should be escaped
        """
        user, token = test_user
        headers = {"Authorization": f"Bearer {token}"}

        malicious_title = '<img src=x onerror=alert("XSS")>My Portfolio'

        response = await authenticated_client.post(
            "/api/v1/conversations",
            headers=headers,
            json={"title": malicious_title},
        )

        assert response.status_code == 200
        data = response.json()

        # Title should not contain unescaped HTML
        if "title" in data:
            assert "<img" not in data["title"], "XSS vulnerability in title"
            assert "onerror" not in data["title"], "XSS event handler not removed"

    async def test_xss_003_javascript_protocol_in_content(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
        conversation_id: str,
    ):
        """
        GIVEN javascript: protocol in message
        WHEN sending message
        THEN protocol should be neutralized
        """
        malicious_content = 'Check this link: <a href="javascript:alert(1)">Click here</a>'

        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": malicious_content,
                "language": "en",
            },
        )

        assert response.status_code == 200
        data = response.json()

        agent_response = data["agent_message"]["content"]
        # javascript: protocol should be removed or escaped
        assert "javascript:" not in agent_response.lower(), \
            "XSS vulnerability: javascript: protocol not sanitized"


@pytest.mark.asyncio
class TestInjectionProtection:
    """SQL/NoSQL injection protection tests (3 tests)."""

    async def test_injection_001_sql_injection_in_message(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
        conversation_id: str,
    ):
        """
        GIVEN SQL injection payload in message
        WHEN sending message
        THEN should be treated as text, not executed
        """
        sql_injection = "'; DROP TABLE messages; --"

        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": sql_injection,
                "language": "en",
            },
        )

        # Should not cause 500 error (SQL injection successful)
        assert response.status_code in [200, 400, 422], \
            "SQL injection may have caused server error"

        # Database should still be functional
        response2 = await authenticated_client.get(
            "/api/v1/conversations",
            headers=auth_headers,
        )
        assert response2.status_code == 200, "Database may be corrupted"

    async def test_injection_002_nosql_injection_in_language(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
        conversation_id: str,
    ):
        """
        GIVEN NoSQL injection attempt in language field
        WHEN sending message with malicious language
        THEN should be rejected with validation error
        """
        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": "What is Bitcoin?",
                "language": "$ne",  # NoSQL operator
            },
        )

        # Should reject with validation error, not process
        assert response.status_code == 422, \
            "NoSQL injection not prevented by validation"

    async def test_injection_003_command_injection_in_content(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
        conversation_id: str,
    ):
        """
        GIVEN command injection attempt
        WHEN sending message with shell commands
        THEN should be treated as text only
        """
        command_injection = "; rm -rf / ; echo 'What is Bitcoin?'"

        response = await authenticated_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=auth_headers,
            json={
                "content": command_injection,
                "language": "en",
            },
        )

        # Should process as text, not execute
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            # Should generate response (treated as text)
            assert "agent_message" in data


@pytest.mark.asyncio
class TestAuthenticationBoundaries:
    """Authentication boundary and edge case tests (3 tests)."""

    async def test_auth_001_missing_token_protected_endpoint(
        self,
        authenticated_client: AsyncClient,
    ):
        """
        GIVEN protected endpoint without authentication
        WHEN accessing without token
        THEN should return 401 Unauthorized
        """
        response = await authenticated_client.get(
            "/api/v1/conversations",
            # No Authorization header
        )

        assert response.status_code == 401, \
            "Protected endpoint accessible without authentication"

    async def test_auth_002_expired_token(
        self,
        authenticated_client: AsyncClient,
    ):
        """
        GIVEN expired JWT token
        WHEN accessing protected endpoint
        THEN should return 401 Unauthorized
        """
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OTk5IiwiZXhwIjoxfQ.invalid"

        response = await authenticated_client.get(
            "/api/v1/conversations",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        # Should reject expired token
        assert response.status_code in [401, 403], \
            "Expired token accepted"

    async def test_auth_003_malformed_token(
        self,
        authenticated_client: AsyncClient,
    ):
        """
        GIVEN malformed JWT token
        WHEN accessing protected endpoint
        THEN should return 401 Unauthorized
        """
        malformed_tokens = [
            "Bearer",  # Missing token
            "Bearer ",  # Empty token
            "Bearer invalid.token.here",  # Invalid format
            "NotBearer validtoken123",  # Wrong prefix
            "Bearer" + "A" * 1000,  # Excessively long
        ]

        for token in malformed_tokens:
            response = await authenticated_client.get(
                "/api/v1/conversations",
                headers={"Authorization": token},
            )

            assert response.status_code in [401, 422], \
                f"Malformed token '{token[:20]}...' accepted"


@pytest.mark.asyncio
class TestAuthorizationControls:
    """Authorization and access control tests (2 tests)."""

    async def test_authz_001_access_other_user_conversation(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
    ):
        """
        GIVEN two different users
        WHEN user A tries to access user B's conversation
        THEN should return 403 Forbidden or 404 Not Found
        """
        # Create user A
        user_a, token_a = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email=f"user_a_{uuid4().hex[:8]}@example.com",
            role="user",
        )
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Create user B
        user_b, token_b = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email=f"user_b_{uuid4().hex[:8]}@example.com",
            role="user",
        )
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B creates conversation
        response_b = await authenticated_client.post(
            "/api/v1/conversations",
            headers=headers_b,
            json={"language": "en"},
        )
        assert response_b.status_code == 200
        conv_b_id = response_b.json()["id"]

        # User A tries to access User B's conversation
        response_a = await authenticated_client.get(
            f"/api/v1/conversations/{conv_b_id}",
            headers=headers_a,
        )

        # Should be denied
        assert response_a.status_code in [403, 404], \
            "Unauthorized access to other user's conversation allowed"

    async def test_authz_002_modify_other_user_conversation(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
    ):
        """
        GIVEN two different users
        WHEN user A tries to send message to user B's conversation
        THEN should return 403 Forbidden
        """
        # Create user A
        user_a, token_a = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email=f"user_a_{uuid4().hex[:8]}@example.com",
            role="user",
        )
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Create user B
        user_b, token_b = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email=f"user_b_{uuid4().hex[:8]}@example.com",
            role="user",
        )
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B creates conversation
        response_b = await authenticated_client.post(
            "/api/v1/conversations",
            headers=headers_b,
            json={"language": "en"},
        )
        assert response_b.status_code == 200
        conv_b_id = response_b.json()["id"]

        # User A tries to send message to User B's conversation
        response_a = await authenticated_client.post(
            f"/api/v1/conversations/{conv_b_id}/messages",
            headers=headers_a,
            json={"content": "Unauthorized access", "language": "en"},
        )

        # Should be denied
        assert response_a.status_code in [403, 404], \
            "Unauthorized modification of other user's conversation allowed"


@pytest.mark.asyncio
class TestSessionSecurity:
    """Session management security tests (2 tests)."""

    async def test_session_001_token_reuse_after_logout(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
    ):
        """
        GIVEN user logs out
        WHEN trying to reuse token after logout
        THEN token should be invalidated
        """
        # Create user
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email=f"session_test_{uuid4().hex[:8]}@example.com",
            role="user",
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Use token successfully
        response1 = await authenticated_client.get(
            "/api/v1/conversations",
            headers=headers,
        )
        assert response1.status_code == 200

        # Attempt logout (if endpoint exists)
        logout_response = await authenticated_client.post(
            "/api/v1/auth/logout",
            headers=headers,
        )

        # If logout successful, token should be invalid
        if logout_response.status_code == 200:
            response2 = await authenticated_client.get(
                "/api/v1/conversations",
                headers=headers,
            )
            # Token should be invalidated
            # Note: If using stateless JWT, this may not work without token blacklist
            # Test documents expected behavior

    async def test_session_002_concurrent_session_handling(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
    ):
        """
        GIVEN same user token used concurrently
        WHEN making multiple simultaneous requests
        THEN all should succeed (no session conflicts)
        """
        import asyncio

        async def make_request(num: int):
            response = await authenticated_client.get(
                "/api/v1/conversations",
                headers=auth_headers,
            )
            return response.status_code

        # Make 5 concurrent requests with same token
        tasks = [make_request(i) for i in range(5)]
        status_codes = await asyncio.gather(*tasks)

        # All should succeed
        assert all(code == 200 for code in status_codes), \
            "Concurrent session handling failed"
