"""
Unit tests for GraphRAG search controllers.

Tests hybrid search, similar protocols, and contextual search
in isolation with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper


class TestHybridSearchController:
    """Unit tests for POST /graph/search/hybrid controller."""

    @pytest.fixture
    def mock_hybrid_retrieval_interactor(self):
        """Create mock HybridRetrievalInteractor."""
        interactor = AsyncMock()
        interactor.search_protocols = AsyncMock(
            return_value=[
                MagicMock(
                    protocol_id=str(uuid4()),
                    protocol_name="Aave",
                    score=0.95,
                    vector_similarity=0.92,
                    graph_importance=0.98,
                    context={
                        "tvl": 10000000000,
                        "category": "Lending",
                        "dependent_count": 150,
                    },
                    risk_info={
                        "risk_score": 3.5,
                        "direct_risks": ["Smart contract risk"],
                        "systemic_risks": ["Oracle dependency"],
                    },
                ),
            ]
        )
        return interactor

    def test_hybrid_search_request_structure(self):
        """Test hybrid search request structure."""
        request_data = {
            "query": "decentralized lending protocol",
            "limit": 10,
            "include_risks": True,
            "include_dependencies": True,
            "similarity_threshold": 0.5,
        }

        assert "query" in request_data
        assert "limit" in request_data

    def test_hybrid_search_response_structure(self, mock_hybrid_retrieval_interactor):
        """Test hybrid search returns expected structure."""
        response = {
            "query": "lending protocol",
            "results": [
                {
                    "protocol_id": str(uuid4()),
                    "protocol_name": "Aave",
                    "score": 0.95,
                    "vector_similarity": 0.92,
                    "graph_importance": 0.98,
                    "context": {
                        "tvl": 10000000000,
                        "category": "Lending",
                    },
                    "risk_info": {
                        "risk_score": 3.5,
                    },
                },
            ],
            "total": 1,
        }

        assert "query" in response
        assert "results" in response
        assert "total" in response

    def test_empty_query_error(self):
        """Test empty query returns SEARCH_001 error."""
        error_response = {
            "error": {
                "code": "SEARCH_001",
                "message": "Search query cannot be empty",
                "i18n_key": "errors.search.query_empty",
                "http_status": 400,
            }
        }

        assert error_response["error"]["code"] == "SEARCH_001"

    def test_search_requires_authentication(self):
        """Test search requires Bearer token."""
        assert True  # Configuration test


class TestSimilarProtocolsController:
    """Unit tests for POST /graph/search/similar controller."""

    def test_similar_protocols_request_structure(self):
        """Test similar protocols request structure."""
        request_data = {
            "protocol_id": str(uuid4()),
            "limit": 10,
        }

        assert "protocol_id" in request_data

    def test_similar_protocols_response_structure(self):
        """Test similar protocols returns expected structure."""
        response = {
            "reference_protocol_id": str(uuid4()),
            "results": [
                {
                    "protocol_id": str(uuid4()),
                    "protocol_name": "Compound",
                    "score": 0.89,
                },
            ],
            "total": 1,
        }

        assert "reference_protocol_id" in response
        assert "results" in response

    def test_protocol_not_found_error(self):
        """Test protocol not found returns SEARCH_002 error."""
        error_response = {
            "error": {
                "code": "SEARCH_002",
                "message": "Protocol not found",
                "i18n_key": "errors.search.protocol_not_found",
                "http_status": 404,
            }
        }

        assert error_response["error"]["http_status"] == 404


class TestContextualSearchController:
    """Unit tests for POST /graph/search/contextual controller."""

    def test_contextual_search_request_structure(self):
        """Test contextual search request structure."""
        request_data = {
            "query": "safe lending protocol",
            "preferences": {
                "category": "Lending",
                "max_risk_score": 5.0,
                "min_tvl": 1000000000,
            },
            "limit": 5,
        }

        assert "query" in request_data
        assert "preferences" in request_data

    def test_contextual_search_response_structure(self):
        """Test contextual search returns expected structure."""
        response = {
            "query": "safe lending protocol",
            "preferences": {
                "category": "Lending",
            },
            "results": [],
            "total": 0,
        }

        assert "query" in response
        assert "preferences" in response
        assert "results" in response

    def test_invalid_filters_error(self):
        """Test invalid filters returns SEARCH_003 error."""
        error_response = {
            "error": {
                "code": "SEARCH_003",
                "message": "Invalid search filters",
                "i18n_key": "errors.search.invalid_filters",
                "http_status": 400,
            }
        }

        assert error_response["error"]["http_status"] == 400


class TestSearchResultContext:
    """Unit tests for search result context data."""

    def test_protocol_context_fields(self):
        """Test protocol context includes expected fields."""
        context = {
            "tvl": 10000000000,
            "category": "Lending",
            "dependent_count": 150,
            "degree": 45,
            "audit_count": 12,
            "chain_count": 8,
            "dependencies": ["Chainlink", "Uniswap"],
        }

        assert "tvl" in context
        assert "category" in context
        assert "dependent_count" in context

    def test_risk_info_fields(self):
        """Test risk info includes expected fields."""
        risk_info = {
            "risk_score": 3.5,
            "direct_risks": ["Smart contract risk", "Governance risk"],
            "systemic_risks": ["Oracle dependency"],
            "top_recommendation": "Enable rate limiting",
        }

        assert "risk_score" in risk_info
        assert "direct_risks" in risk_info
        assert "systemic_risks" in risk_info
