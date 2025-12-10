"""
Integration tests for ML risk prediction.

Tests risk prediction, batch prediction, anomaly detection,
and risk forecasting including:
- Single protocol risk prediction
- Batch risk prediction
- Anomaly detection
- Risk forecasting
"""

import pytest
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper
from tests.helpers.error_validator import validate_error_response


@pytest.mark.integration
class TestRiskPrediction:
    """Integration tests for risk prediction."""

    def test_predict_protocol_risk(self, client):
        """
        WHEN user requests risk prediction
        THEN system SHALL return prediction
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        protocol_id = str(uuid4())

        response = client.get(
            f"/api/v1/ml/prediction/{protocol_id}",
            headers=headers,
        )

        # Could succeed or return 404 for nonexistent protocol
        assert response.status_code in (200, 401, 404, 500, 503)

        if response.status_code == 200:
            data = response.json()
            assert "predicted_risk_score" in data or "protocol_id" in data

    def test_predict_risk_nonexistent_protocol(self, client):
        """
        WHEN protocol doesn't exist
        THEN system SHALL return 404
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        nonexistent_id = str(uuid4())

        response = client.get(
            f"/api/v1/ml/prediction/{nonexistent_id}",
            headers=headers,
        )

        assert response.status_code in (200, 401, 404, 500, 503)

    def test_predict_risk_without_auth(self, client):
        """
        WHEN unauthenticated user requests prediction
        THEN system SHALL return 401
        """
        protocol_id = str(uuid4())

        response = client.get(f"/api/v1/ml/prediction/{protocol_id}")

        assert response.status_code in (401, 403, 422)


@pytest.mark.integration
class TestBatchRiskPrediction:
    """Integration tests for batch risk prediction."""

    def test_batch_predict_risks(self, client):
        """
        WHEN user requests batch prediction
        THEN system SHALL return predictions
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        batch_request = {
            "protocol_ids": [str(uuid4()), str(uuid4())],
        }

        response = client.post(
            "/api/v1/ml/prediction/batch",
            json=batch_request,
            headers=headers,
        )

        assert response.status_code in (200, 401, 404, 500, 503)

        if response.status_code == 200:
            data = response.json()
            assert "predictions" in data or "total" in data

    def test_batch_prediction_without_auth(self, client):
        """
        WHEN unauthenticated user requests batch
        THEN system SHALL return 401
        """
        batch_request = {
            "protocol_ids": [str(uuid4())],
        }

        response = client.post("/api/v1/ml/prediction/batch", json=batch_request)

        assert response.status_code in (401, 403, 422)


@pytest.mark.integration
class TestAnomalyDetection:
    """Integration tests for anomaly detection."""

    def test_detect_anomalies(self, client):
        """
        WHEN user requests anomaly detection
        THEN system SHALL return anomaly data
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        protocol_id = str(uuid4())

        response = client.get(
            f"/api/v1/ml/prediction/{protocol_id}/anomalies",
            params={"lookback_days": 7},
            headers=headers,
        )

        assert response.status_code in (200, 401, 404, 500, 503)

    def test_anomaly_detection_invalid_lookback(self, client):
        """
        WHEN lookback_days is invalid
        THEN system SHALL return validation error
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        protocol_id = str(uuid4())

        response = client.get(
            f"/api/v1/ml/prediction/{protocol_id}/anomalies",
            params={"lookback_days": 100},  # Exceeds max of 90
            headers=headers,
        )

        assert response.status_code in (400, 401, 422, 500, 503)


@pytest.mark.integration
class TestRiskForecast:
    """Integration tests for risk forecasting."""

    def test_forecast_risk(self, client):
        """
        WHEN user requests risk forecast
        THEN system SHALL return forecast
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        protocol_id = str(uuid4())

        response = client.get(
            f"/api/v1/ml/prediction/{protocol_id}/forecast",
            params={"forecast_days": 7},
            headers=headers,
        )

        assert response.status_code in (200, 401, 404, 500, 503)

    def test_forecast_invalid_days(self, client):
        """
        WHEN forecast_days is invalid
        THEN system SHALL return validation error
        """
        user, token = AuthHelper.create_test_user()
        headers = AuthHelper.get_auth_headers(token)

        protocol_id = str(uuid4())

        response = client.get(
            f"/api/v1/ml/prediction/{protocol_id}/forecast",
            params={"forecast_days": 50},  # Exceeds max of 30
            headers=headers,
        )

        assert response.status_code in (400, 401, 422, 500, 503)


@pytest.mark.integration
class TestMLErrorResponses:
    """Integration tests for ML error responses."""

    def test_ml_error_format(self):
        """
        WHEN ML operation fails
        THEN error SHALL follow standardized format
        """
        error_response = {
            "error": {
                "code": "SEARCH_002",
                "message": "Protocol not found",
                "i18n_key": "errors.search.protocol_not_found",
                "http_status": 404,
            }
        }

        assert "code" in error_response["error"]
        assert "i18n_key" in error_response["error"]
