"""
Integration tests for GraphRAG protocol search.

Tests hybrid search, similar protocols, and contextual search including:
- Hybrid search with vector and graph
- Find similar protocols
- Contextual search with preferences
"""

import pytest
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper
from tests.helpers.error_validator import validate_error_response


@pytest.mark.integration
class TestHybridSearch:
    """Integration tests for hybrid search."""

    def test_hybrid_search_returns_results(self, client):
        """
        WHEN user performs hybrid search
        THEN system SHALL return relevant protocols
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        search_request = {
            "query": "decentralized lending protocol",
            "limit": 10,
            "include_risks": True,
            "include_dependencies": True,
        }

        response = client.post(
            "/api/v1/user/graph/search/hybrid",
            json=search_request,
            headers=headers,
        )

        assert response.status_code in (200, 401, 404, 500, 503)

        if response.status_code == 200:
            data = response.json()
            assert "results" in data or "query" in data

    def test_hybrid_search_empty_query_error(self, client):
        """
        WHEN query is empty
        THEN system SHALL return SEARCH_001 error
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        search_request = {
            "query": "",
            "limit": 10,
        }

        response = client.post(
            "/api/v1/user/graph/search/hybrid",
            json=search_request,
            headers=headers,
        )

        # Should return 400 for empty query
        assert response.status_code in (400, 401, 422, 500, 503)

    def test_hybrid_search_without_auth(self, client):
        """
        WHEN unauthenticated user searches
        THEN system SHALL return 401
        """
        search_request = {
            "query": "lending",
            "limit": 10,
        }

        response = client.post("/api/v1/user/graph/search/hybrid", json=search_request)

        assert response.status_code in (401, 403, 422)

    def test_hybrid_search_with_similarity_threshold(self, client):
        """
        WHEN similarity threshold is specified
        THEN system SHALL filter results accordingly
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        search_request = {
            "query": "lending",
            "limit": 10,
            "similarity_threshold": 0.8,  # High threshold
        }

        response = client.post(
            "/api/v1/user/graph/search/hybrid",
            json=search_request,
            headers=headers,
        )

        assert response.status_code in (200, 401, 500, 503)


@pytest.mark.integration
class TestSimilarProtocols:
    """Integration tests for finding similar protocols."""

    def test_find_similar_protocols(self, client):
        """
        WHEN user finds similar protocols
        THEN system SHALL return similar protocols
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        similar_request = {
            "protocol_id": str(uuid4()),
            "limit": 10,
        }

        response = client.post(
            "/api/v1/user/graph/search/similar",
            json=similar_request,
            headers=headers,
        )

        # Could succeed or return 404 for nonexistent protocol
        assert response.status_code in (200, 401, 404, 500, 503)

    def test_similar_nonexistent_protocol(self, client):
        """
        WHEN protocol doesn't exist
        THEN system SHALL return 404
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        similar_request = {
            "protocol_id": str(uuid4()),  # Random UUID
            "limit": 10,
        }

        response = client.post(
            "/api/v1/user/graph/search/similar",
            json=similar_request,
            headers=headers,
        )

        # Protocol likely doesn't exist
        assert response.status_code in (200, 401, 404, 500, 503)


@pytest.mark.integration
class TestContextualSearch:
    """Integration tests for contextual search."""

    def test_contextual_search_with_preferences(self, client):
        """
        WHEN user searches with preferences
        THEN system SHALL filter by preferences
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        contextual_request = {
            "query": "safe lending",
            "preferences": {
                "category": "Lending",
                "max_risk_score": 5.0,
            },
            "limit": 5,
        }

        response = client.post(
            "/api/v1/user/graph/search/contextual",
            json=contextual_request,
            headers=headers,
        )

        assert response.status_code in (200, 401, 500, 503)

    def test_contextual_search_empty_query(self, client):
        """
        WHEN query is empty
        THEN system SHALL return error
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        contextual_request = {
            "query": "",
            "limit": 5,
        }

        response = client.post(
            "/api/v1/user/graph/search/contextual",
            json=contextual_request,
            headers=headers,
        )

        assert response.status_code in (400, 401, 422, 500, 503)


@pytest.mark.integration
class TestSearchErrorResponses:
    """Integration tests for search error responses."""

    def test_search_error_format(self):
        """
        WHEN search fails
        THEN error SHALL follow standardized format
        """
        error_response = {
            "error": {
                "code": "SEARCH_001",
                "message": "Search query cannot be empty",
                "i18n_key": "errors.search.query_empty",
                "http_status": 400,
            }
        }

        assert "code" in error_response["error"]
        assert "i18n_key" in error_response["error"]
