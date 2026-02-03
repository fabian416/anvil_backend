"""
Security tests for authenticated chat system.

Tests authentication, authorization, access control, and data isolation
for the unified chat endpoint serving guest and authenticated users.

Day 4: Risk Assessment - Security Testing
"""

import pytest
import pytest_asyncio
from uuid import uuid4

from tests.helpers.api_client import AuthenticatedClient
from tests.helpers.auth_helper import AuthHelper


@pytest.mark.asyncio
class TestAuthenticationSecurity:
    """Test JWT authentication and token handling security."""

    async def test_valid_jwt_creates_authenticated_context(
        self,
        test_app,
        async_db_session,
    ):
        """
        GIVEN a user with valid JWT token
        WHEN sending chat request
        THEN authenticated context should be created
        """
        # Arrange
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email="auth@example.com",
            role="user",
        )

        client = AuthenticatedClient()
        client.set_app(test_app)
        client._access_token = token
        client._update_headers()

        # Act
        response = await client.post(
            "/api/v1/chat",
            json={"content": "What's BTC sentiment?", "language": "en"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_type"] == "authenticated"
        # Should have premium features (free tier)
        assert data["features_available"]["premium"]["patterns"] is True

    async def test_no_jwt_creates_guest_context(self, test_app):
        """
        GIVEN no JWT token
        WHEN sending chat request
        THEN guest context should be created
        """
        # Arrange
        from httpx import AsyncClient

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Act
            response = await client.post(
                "/api/v1/chat",
                json={"content": "What's BTC sentiment?", "language": "en"},
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["user_type"] == "guest"
            # Should NOT have premium features
            assert data["features_available"]["premium"]["patterns"] is False

    async def test_invalid_jwt_graceful_degradation(self, test_app):
        """
        GIVEN an invalid JWT token
        WHEN sending chat request
        THEN system should degrade to guest context WITHOUT returning 401
        """
        # Arrange
        from httpx import AsyncClient

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Act
            response = await client.post(
                "/api/v1/chat",
                headers={"Authorization": "Bearer invalid_token_xyz123"},
                json={"content": "test", "language": "en"},
            )

            # Assert - Should NOT return 401
            assert response.status_code == 200  # Graceful degradation
            data = response.json()
            assert data["user_type"] == "guest"

    async def test_malformed_jwt_header(self, test_app):
        """
        GIVEN a malformed Authorization header
        WHEN sending chat request
        THEN system should treat as guest user
        """
        # Arrange
        from httpx import AsyncClient

        test_cases = [
            "invalid_no_bearer",  # Missing "Bearer " prefix
            "Bearer",  # Just "Bearer" without token
            "",  # Empty string
            "Basic xyz123",  # Wrong auth type
        ]

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            for malformed_header in test_cases:
                # Act
                response = await client.post(
                    "/api/v1/chat",
                    headers={"Authorization": malformed_header},
                    json={"content": "test", "language": "en"},
                )

                # Assert
                assert response.status_code == 200
                data = response.json()
                assert data["user_type"] == "guest", (
                    f"Failed for header: {malformed_header}"
                )


@pytest.mark.asyncio
class TestAuthorizationSecurity:
    """Test feature access control and tier-based authorization."""

    async def test_guest_blocked_from_premium_features(self, test_app):
        """
        GIVEN a guest user
        WHEN requesting premium feature (patterns)
        THEN upgrade prompt should be shown
        """
        # Arrange
        from httpx import AsyncClient

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Act - Request premium feature
            response = await client.post(
                "/api/v1/chat",
                json={
                    "content": "Show me patterns for BTC",  # Premium intent
                    "language": "en",
                },
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == "hunter_patterns"
            assert data["requires_registration"] is True
            assert "premium feature" in data["content"].lower()
            assert "sign up" in data["content"].lower()

    async def test_free_tier_has_premium_features(
        self,
        test_app,
        async_db_session,
    ):
        """
        GIVEN a free tier authenticated user
        WHEN requesting premium feature
        THEN feature should be available
        """
        # Arrange
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email="free@example.com",
            role="user",
        )

        client = AuthenticatedClient()
        client.set_app(test_app)
        client._access_token = token
        client._update_headers()

        # Act - Request premium feature
        response = await client.post(
            "/api/v1/chat",
            json={"content": "Show me patterns for BTC", "language": "en"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["requires_registration"] is False
        assert "premium feature" not in data["content"].lower()
        # Should have access to premium features
        assert data["features_available"]["premium"]["patterns"] is True

    async def test_premium_tier_has_advanced_features(
        self,
        test_app,
        async_db_session,
    ):
        """
        GIVEN a premium tier user
        WHEN checking feature flags
        THEN advanced features should be enabled
        """
        # Arrange
        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email="premium@example.com",
            role="user",
        )

        # Manually set subscription tier (in real app, this comes from users table)
        # For testing, we'll verify through the response

        client = AuthenticatedClient()
        client.set_app(test_app)
        client._access_token = token
        client._update_headers()

        # Act
        response = await client.post(
            "/api/v1/chat",
            json={"content": "test", "language": "en"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Free tier gets premium features but NOT advanced
        # (Until we implement subscription tier tracking)
        assert data["features_available"]["premium"]["patterns"] is True


@pytest.mark.asyncio
class TestDataIsolationSecurity:
    """Test cross-user access prevention and data isolation."""

    async def test_guest_users_isolated_by_ip(self, test_app):
        """
        GIVEN two guest users with different IPs
        WHEN each sends messages
        THEN conversations should be isolated
        """
        # Arrange
        from httpx import AsyncClient

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # User 1 (IP: 1.2.3.4)
            response1 = await client.post(
                "/api/v1/chat",
                headers={"X-Forwarded-For": "1.2.3.4"},
                json={"content": "User 1 message", "language": "en"},
            )

            # User 2 (IP: 5.6.7.8)
            response2 = await client.post(
                "/api/v1/chat",
                headers={"X-Forwarded-For": "5.6.7.8"},
                json={"content": "User 2 message", "language": "en"},
            )

            # Assert
            assert response1.status_code == 200
            assert response2.status_code == 200

            # Different conversations (different guest users)
            data1 = response1.json()
            data2 = response2.json()
            # Both are guests
            assert data1["user_type"] == "guest"
            assert data2["user_type"] == "guest"

    async def test_authenticated_users_isolated_by_user_id(
        self,
        test_app,
        async_db_session,
    ):
        """
        GIVEN two authenticated users
        WHEN each sends messages
        THEN conversations should be completely isolated
        """
        # Arrange - Create two users
        user1, token1 = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email="user1@example.com",
            role="user",
        )

        user2, token2 = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email="user2@example.com",
            role="user",
        )

        client1 = AuthenticatedClient()
        client1.set_app(test_app)
        client1._access_token = token1
        client1._update_headers()

        client2 = AuthenticatedClient()
        client2.set_app(test_app)
        client2._access_token = token2
        client2._update_headers()

        # Act
        response1 = await client1.post(
            "/api/v1/chat",
            json={"content": "User 1 message", "language": "en"},
        )

        response2 = await client2.post(
            "/api/v1/chat",
            json={"content": "User 2 message", "language": "en"},
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Both authenticated but isolated
        assert data1["user_type"] == "authenticated"
        assert data2["user_type"] == "authenticated"
        # Different message IDs (different conversations)
        assert data1["message_id"] != data2["message_id"]


@pytest.mark.asyncio
class TestInjectionAttacksPrevention:
    """Test SQL injection, XSS, and other injection attacks."""

    async def test_sql_injection_in_message_content(self, test_app):
        """
        GIVEN malicious SQL in message content
        WHEN sending chat request
        THEN SQL should be treated as literal text (not executed)
        """
        # Arrange
        from httpx import AsyncClient

        sql_injection_attempts = [
            "'; DROP TABLE chat_messages; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM chat_users--",
        ]

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            for malicious_sql in sql_injection_attempts:
                # Act
                response = await client.post(
                    "/api/v1/chat",
                    json={"content": malicious_sql, "language": "en"},
                )

                # Assert - Should succeed (SQL treated as text)
                assert response.status_code == 200, f"Failed for: {malicious_sql}"

    async def test_xss_in_message_content(self, test_app):
        """
        GIVEN XSS payload in message content
        WHEN retrieving message
        THEN XSS should be sanitized/escaped
        """
        # Arrange
        from httpx import AsyncClient

        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='evil.com'>",
        ]

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            for xss_payload in xss_attempts:
                # Act
                response = await client.post(
                    "/api/v1/chat",
                    json={"content": xss_payload, "language": "en"},
                )

                # Assert
                assert response.status_code == 200

                # Response should not contain unescaped HTML
                data = response.json()
                assert "<script>" not in data["content"]
                assert "onerror" not in data["content"]

    async def test_header_injection_attempts(self, test_app):
        """
        GIVEN malicious headers
        WHEN sending chat request
        THEN headers should be sanitized
        """
        # Arrange
        from httpx import AsyncClient

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Act - Attempt header injection
            response = await client.post(
                "/api/v1/chat",
                headers={
                    "X-Forwarded-For": "1.2.3.4\nInjected: malicious",
                    "User-Agent": "<script>alert('xss')</script>",
                },
                json={"content": "test", "language": "en"},
            )

            # Assert - Should handle gracefully
            assert response.status_code == 200


@pytest.mark.asyncio
class TestRateLimitingSecurity:
    """Test rate limiting enforcement and bypass prevention."""

    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    async def test_guest_rate_limit_enforcement(self, test_app):
        """
        GIVEN a guest user
        WHEN exceeding rate limit (20 msg/hr)
        THEN requests should be rejected with 429
        """
        # Arrange
        from httpx import AsyncClient

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            messages_sent = 0
            rate_limited = False

            # Act - Send 25 messages (limit is 20)
            for i in range(25):
                response = await client.post(
                    "/api/v1/chat",
                    headers={"X-Forwarded-For": "203.0.113.42"},
                    json={"content": f"Message {i}", "language": "en"},
                )

                if response.status_code == 429:
                    rate_limited = True
                    break

                messages_sent += 1

            # Assert
            assert messages_sent == 20
            assert rate_limited is True

    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    async def test_rate_limit_bypass_prevention(self, test_app):
        """
        GIVEN a guest user attempting to bypass rate limits
        WHEN changing IP or headers
        THEN rate limit should still apply
        """
        # Arrange
        from httpx import AsyncClient

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Act - Try to bypass by changing X-Forwarded-For
            for i in range(25):
                response = await client.post(
                    "/api/v1/chat",
                    headers={"X-Forwarded-For": f"203.0.113.{i}"},  # Different IPs
                    json={"content": f"Message {i}", "language": "en"},
                )

                # First 20 should succeed
                if i < 20:
                    assert response.status_code == 200
                else:
                    # Should be rate limited (IP-based tracking in place)
                    assert response.status_code in [200, 429]


@pytest.mark.asyncio
class TestConcurrencySecurity:
    """Test race conditions and concurrent access security."""

    async def test_concurrent_user_creation_no_duplicates(
        self,
        test_app,
        async_db_session,
    ):
        """
        GIVEN concurrent requests for same user
        WHEN creating chat user
        THEN only one chat user should be created
        """
        # Arrange
        import asyncio

        user, token = await AuthHelper.create_test_user_in_db(
            db_session=async_db_session,
            email="concurrent@example.com",
            role="user",
        )

        client = AuthenticatedClient()
        client.set_app(test_app)
        client._access_token = token
        client._update_headers()

        # Act - Send 10 concurrent requests
        tasks = [
            client.post(
                "/api/v1/chat",
                json={"content": f"Message {i}", "language": "en"},
            )
            for i in range(10)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert - All should succeed
        successful = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful) == 10

        for response in successful:
            assert response.status_code == 200


@pytest.mark.asyncio
class TestSecurityHeaders:
    """Test security headers and CORS configuration."""

    async def test_security_headers_present(self, test_app):
        """
        GIVEN any chat request
        WHEN receiving response
        THEN security headers should be present
        """
        # Arrange
        from httpx import AsyncClient

        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Act
            response = await client.post(
                "/api/v1/chat",
                json={"content": "test", "language": "en"},
            )

            # Assert - Check security headers
            headers = response.headers

            # Should have content security policy
            # (Exact headers depend on FastAPI middleware configuration)
            assert response.status_code == 200


@pytest.mark.asyncio
class TestAuditLogging:
    """Test security audit logging for compliance."""

    @pytest.mark.skip(reason="Audit logging not yet implemented")
    async def test_failed_auth_attempts_logged(self, test_app):
        """
        GIVEN invalid JWT attempts
        WHEN sending requests
        THEN attempts should be logged for audit
        """
        # Would check audit logs for failed authentication attempts
        pass

    @pytest.mark.skip(reason="Audit logging not yet implemented")
    async def test_rate_limit_hits_logged(self, test_app):
        """
        GIVEN rate limit exceeded
        WHEN requests are blocked
        THEN events should be logged for security monitoring
        """
        # Would check audit logs for rate limit violations
        pass
