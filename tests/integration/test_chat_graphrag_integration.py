"""
Integration tests for Chat GraphRAG integration.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.graphrag
class TestChatGraphRAGIntegration:
    """Test Chat GraphRAG endpoints."""

    def test_search_protocols_from_chat(self, client: TestClient, mock_auth_token):
        """Test searching protocols via chat interface."""
        # Arrange
        headers = {"Authorization": f"Bearer {mock_auth_token}"}
        payload = {
            "query": "safe staking protocols on Ethereum",
            "user_preferences": {
                "risk_tolerance": "conservative",
                "preferred_chains": ["Ethereum"],
            },
        }
        
        # Act
        # response = client.post(
        #     "/api/v1/chat/search-protocols",
        #     json=payload,
        #     headers=headers,
        # )
        
        # Assert
        # assert response.status_code == 200
        # data = response.json()
        # assert "results" in data
        # assert len(data["results"]) > 0
        # assert all(r["risk_level"] == "LOW" for r in data["results"])
        pass  # TODO: Enable once auth is properly mocked

    def test_analyze_risk_from_chat(self, client: TestClient, mock_auth_token):
        """Test risk analysis via chat interface."""
        # Arrange
        headers = {"Authorization": f"Bearer {mock_auth_token}"}
        payload = {
            "protocol_name": "Euler Finance",
            "conversation_id": "test-conversation",
        }
        
        # Act
        # response = client.post(
        #     "/api/v1/chat/analyze-risk",
        #     json=payload,
        #     headers=headers,
        # )
        
        # Assert
        # assert response.status_code == 200
        # data = response.json()
        # assert "risk_analysis" in data
        # assert "alternatives" in data
        pass  # TODO: Enable

    def test_find_similar_protocols(self, client: TestClient, mock_auth_token):
        """Test finding similar protocols via chat."""
        # Arrange
        headers = {"Authorization": f"Bearer {mock_auth_token}"}
        payload = {
            "protocol_name": "Lido Finance",
            "limit": 5,
        }
        
        # Act
        # response = client.post(
        #     "/api/v1/chat/similar-protocols",
        #     json=payload,
        #     headers=headers,
        # )
        
        # Assert
        # assert response.status_code == 200
        # data = response.json()
        # assert "similar_protocols" in data
        # assert len(data["similar_protocols"]) <= 5
        pass  # TODO: Enable


@pytest.mark.integration
@pytest.mark.slow
class TestGraphRAGPerformance:
    """Test GraphRAG performance."""

    def test_hybrid_search_performance(self, client: TestClient):
        """Test that hybrid search completes within acceptable time."""
        # TODO: Implement performance test
        # Target: < 200ms for cached, < 1000ms for uncached
        pass

    def test_batch_prediction_performance(self, client: TestClient):
        """Test batch risk prediction performance."""
        # TODO: Implement
        # Target: < 100ms per protocol
        pass
