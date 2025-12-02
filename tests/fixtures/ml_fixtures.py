"""
Machine Learning fixtures for tests.

Provides mock ML predictions, risk scores, and
ML-related test data.
"""

import pytest
from uuid import uuid4


@pytest.fixture
def mock_risk_prediction():
    """Mock ML risk prediction result."""
    return {
        "protocol_id": str(uuid4()),
        "protocol_name": "Lido Finance",
        "predicted_risk_score": 2.3,
        "confidence": 0.92,
        "risk_level": "LOW",
        "risk_trend": "STABLE",
        "contributing_factors": [
            {
                "factor": "high_tvl_stability",
                "impact": -0.8,
                "description": "TVL stable at $28.4B for 90+ days",
                "is_positive": True,
            },
            {
                "factor": "audit_coverage",
                "impact": -0.5,
                "description": "15+ audits from top firms",
                "is_positive": True,
            },
            {
                "factor": "dependency_complexity",
                "impact": 0.3,
                "description": "Moderate dependency on external oracles",
                "is_positive": False,
            },
        ],
        "recommendations": [
            "Monitor oracle health regularly",
            "Watch for sudden TVL changes > 20%",
            "Review smart contract upgrades",
        ],
        "prediction_timestamp": "2025-12-02T10:00:00Z",
        "model_version": "v2.1.0",
    }


@pytest.fixture
def mock_batch_risk_predictions():
    """Mock batch risk prediction results."""
    return {
        "predictions": [
            {
                "protocol_id": str(uuid4()),
                "protocol_name": "Aave V3",
                "predicted_risk_score": 2.1,
                "confidence": 0.94,
                "risk_level": "LOW",
            },
            {
                "protocol_id": str(uuid4()),
                "protocol_name": "Compound",
                "predicted_risk_score": 2.5,
                "confidence": 0.91,
                "risk_level": "LOW",
            },
            {
                "protocol_id": str(uuid4()),
                "protocol_name": "Euler Finance",
                "predicted_risk_score": 7.8,
                "confidence": 0.87,
                "risk_level": "HIGH",
            },
        ],
        "total": 3,
    }


@pytest.fixture
def mock_anomaly_detection():
    """Mock anomaly detection results."""
    return {
        "protocol_id": str(uuid4()),
        "protocol_name": "Euler Finance",
        "anomalies_detected": True,
        "anomaly_count": 2,
        "anomalies": [
            {
                "timestamp": "2025-11-28T14:30:00Z",
                "risk_score": 8.5,
                "expected_range": [3.0, 5.0],
                "deviation_magnitude": 3.5,
                "severity": "HIGH",
                "description": "Sudden risk score spike - significantly above expected range",
            },
            {
                "timestamp": "2025-11-29T09:15:00Z",
                "risk_score": 7.2,
                "expected_range": [3.0, 5.0],
                "deviation_magnitude": 2.2,
                "severity": "MEDIUM",
                "description": "Risk score remains elevated above normal patterns",
            },
        ],
        "lookback_days": 7,
        "analysis_timestamp": "2025-12-02T10:00:00Z",
    }


@pytest.fixture
def mock_risk_forecast():
    """Mock risk forecast results."""
    return {
        "protocol_id": str(uuid4()),
        "protocol_name": "Aave V3",
        "forecast": [
            {
                "date": "2025-12-03",
                "predicted_risk_score": 2.2,
                "confidence_lower": 1.8,
                "confidence_upper": 2.6,
                "trend": "STABLE",
            },
            {
                "date": "2025-12-04",
                "predicted_risk_score": 2.3,
                "confidence_lower": 1.7,
                "confidence_upper": 2.9,
                "trend": "STABLE",
            },
            {
                "date": "2025-12-05",
                "predicted_risk_score": 2.1,
                "confidence_lower": 1.6,
                "confidence_upper": 2.6,
                "trend": "STABLE",
            },
        ],
        "forecast_days": 3,
    }


@pytest.fixture
def mock_pagerank_results():
    """Mock PageRank calculation results."""
    return {
        "results": [
            {
                "protocol_id": str(uuid4()),
                "protocol_name": "Aave V3",
                "pagerank_score": 0.0245,
                "rank": 1,
                "in_degree": 45,
                "out_degree": 12,
            },
            {
                "protocol_id": str(uuid4()),
                "protocol_name": "Uniswap V3",
                "pagerank_score": 0.0198,
                "rank": 2,
                "in_degree": 38,
                "out_degree": 8,
            },
        ],
        "total": 2,
    }


@pytest.fixture
def mock_community_detection():
    """Mock community detection results."""
    return {
        "communities": [
            {
                "community_id": 1,
                "protocols": [str(uuid4()) for _ in range(5)],
                "size": 5,
                "density": 0.75,
                "description": "Lending protocols cluster",
            },
            {
                "community_id": 2,
                "protocols": [str(uuid4()) for _ in range(8)],
                "size": 8,
                "density": 0.68,
                "description": "DEX protocols cluster",
            },
        ],
        "total_communities": 2,
    }
