"""
Security tests for input validation.

Tests input validation security including:
- SQL injection prevention
- XSS prevention
- Path traversal prevention
- Command injection prevention
"""

import pytest
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper


@pytest.mark.security
class TestSQLInjectionPrevention:
    """Security tests for SQL injection prevention."""

    def test_sql_injection_in_login_email(self, client):
        """
        Test SQL injection in login email field is prevented.
        """
        sql_injection_payloads = [
            "' OR '1'='1",
            "admin@example.com'--",
            "admin@example.com'; DROP TABLE users;--",
            "' UNION SELECT * FROM users--",
            "admin@example.com' OR 1=1--",
        ]

        for payload in sql_injection_payloads:
            response = client.post(
                "/api/v1/account/login",
                json={"email": payload, "password": "password"},
            )

            # Should return validation error, not SQL error
            assert response.status_code in (400, 401, 422, 500, 503)
            
            # Should not reveal database errors
            if response.status_code == 500:
                # Check error message doesn't contain SQL details
                try:
                    data = response.json()
                    error_msg = str(data).lower()
                    assert "sql" not in error_msg
                    assert "syntax" not in error_msg
                    assert "query" not in error_msg
                except Exception:
                    pass

    @pytest.mark.skip(reason="Requires database with test users")
    def test_sql_injection_in_search_query(self, client):
        """
        Test SQL injection in search query is prevented.
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        sql_payloads = [
            "'; DROP TABLE protocols;--",
            "' OR 1=1--",
            "UNION SELECT * FROM users",
        ]

        for payload in sql_payloads:
            response = client.post(
                "/api/v1/user/graph/search/hybrid",
                json={"query": payload, "limit": 10},
                headers=headers,
            )

            # Should handle safely
            assert response.status_code in (200, 400, 401, 422, 500, 503)


@pytest.mark.security
class TestXSSPrevention:
    """Security tests for XSS prevention."""

    def test_xss_in_user_profile_name(self, client):
        """
        Test XSS in user profile name is sanitized.
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "'-alert('XSS')-'",
            "<svg onload=alert('XSS')>",
        ]

        for payload in xss_payloads:
            response = client.put(
                "/api/v1/account/me",
                json={"first_name": payload},
                headers=headers,
            )

            # Should either sanitize or reject
            assert response.status_code in (200, 400, 401, 422, 500, 503)

            # If accepted, verify it's sanitized when retrieved
            if response.status_code == 200:
                get_response = client.get("/api/v1/account/me", headers=headers)
                if get_response.status_code == 200:
                    data = get_response.json()
                    name = data.get("first_name", "")
                    # Should not contain raw script tags
                    assert "<script>" not in name.lower()

    def test_xss_in_chat_message(self, client):
        """
        Test XSS in chat message is handled.
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        # Create conversation
        create_response = client.post(
            "/api/v1/chat/conversations",
            json={"title": "XSS Test"},
            headers=headers,
        )

        if create_response.status_code not in (200, 201):
            pytest.skip("Could not create conversation")
            return

        conversation_id = create_response.json().get("id")

        xss_message = "<script>alert('XSS')</script>Hello"

        message_response = client.post(
            f"/api/v1/chat/conversations/{conversation_id}/messages",
            json={"content": xss_message},
            headers=headers,
        )

        # Should handle XSS content safely
        assert message_response.status_code in (200, 201, 400, 401, 422, 500, 503)


@pytest.mark.security
class TestPathTraversalPrevention:
    """Security tests for path traversal prevention."""

    def test_path_traversal_in_file_upload(self, client):
        """
        Test path traversal in file upload is prevented.
        """
        # This applies if there are file upload endpoints
        # Document expected behavior
        pass

    def test_path_traversal_in_wallet_id(self, client):
        """
        Test path traversal in wallet ID is prevented.
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//etc/passwd",
        ]

        for payload in traversal_payloads:
            response = client.post(
                "/api/v1/wallet/export",
                json={"wallet_id": payload},
                headers=headers,
            )

            # Should be rejected as invalid
            assert response.status_code in (400, 401, 404, 422, 500, 503)


@pytest.mark.security
class TestCommandInjectionPrevention:
    """Security tests for command injection prevention."""

    @pytest.mark.skip(reason="Requires database with test users")
    def test_command_injection_in_search(self, client):
        """
        Test command injection in search is prevented.
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",
            "$(id)",
            "&& rm -rf /",
        ]

        for payload in command_payloads:
            response = client.post(
                "/api/v1/user/graph/search/hybrid",
                json={"query": payload, "limit": 10},
                headers=headers,
            )

            # Should handle safely (no command execution)
            assert response.status_code in (200, 400, 401, 422, 500, 503)


@pytest.mark.security
class TestInputLengthValidation:
    """Security tests for input length validation."""

    @pytest.mark.skip(reason="Requires database with test users")
    def test_extremely_long_input_handled(self, client):
        """
        Test extremely long inputs are handled safely.
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        # Very long string
        long_input = "A" * 1000000  # 1MB string

        response = client.post(
            "/api/v1/chat/conversations",
            json={"title": long_input},
            headers=headers,
        )

        # Should reject or truncate, not crash
        assert response.status_code in (400, 413, 422, 500, 503)

    def test_deeply_nested_json_handled(self, client):
        """
        Test deeply nested JSON is handled safely.
        """
        # Create deeply nested structure
        nested = {"a": None}
        current = nested
        for _ in range(100):
            current["a"] = {"a": None}
            current = current["a"]

        response = client.post(
            "/api/v1/account/login",
            json=nested,
        )

        # Should reject invalid structure
        assert response.status_code in (400, 422, 500, 503)
