# ML Prediction API Reference

**Version**: 1.0  
**Base URL**: `https://api.anvil.com/api/v1`  
**Authentication**: Bearer Token (JWT)  
**Last Updated**: December 1, 2025

---

## 🎯 Overview

Complete API reference for ML (Machine Learning) prediction and network analysis endpoints. All endpoints require authentication.

---

## 🔮 Risk Prediction Endpoints

### Predict Protocol Risk

Get ML-powered risk prediction for a protocol.

```http
GET /ml/prediction/{protocol_id}
Authorization: Bearer {token}
```

**Path Parameters**:
- `protocol_id` (required): Protocol UUID

**Response** (200 OK):
```json
{
  "protocol_id": "uuid-123",
  "protocol_name": "Aave V3",
  "risk_score": 2.1,
  "risk_level": "LOW",
  "confidence": 0.92,
  "risk_trend": "STABLE",
  "contributing_factors": [
    {
      "feature": "high_tvl_stability",
      "impact": -0.8,
      "explanation": "TVL stable at $6.2B for 90+ days"
    },
    {
      "feature": "strong_audit_history",
      "impact": -0.6,
      "explanation": "18 audits by top firms, no critical issues"
    }
  ],
  "recommendations": [
    "Continue monitoring",
    "Maintain current position",
    "Review new audits when available"
  ],
  "model_version": "v1.0.0",
  "predicted_at": "2025-12-01T10:00:00Z"
}
```

**Error Responses**:
- `404`: Protocol not found
- `503`: ML service unavailable

**Rate Limit**: 120 requests/minute

---

### Batch Risk Prediction

Get risk predictions for multiple protocols.

```http
POST /ml/prediction/batch
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body**:
```json
{
  "protocol_ids": [
    "uuid-123",
    "uuid-456",
    "uuid-789"
  ]
}
```

**Response** (200 OK):
```json
{
  "predictions": [
    {
      "protocol_id": "uuid-123",
      "protocol_name": "Aave V3",
      "risk_score": 2.1,
      "risk_level": "LOW",
      // ... full prediction
    }
  ],
  "summary": {
    "total_protocols": 3,
    "average_risk": 2.8,
    "highest_risk": {
      "protocol_id": "uuid-789",
      "protocol_name": "Protocol X",
      "risk_score": 5.2
    },
    "lowest_risk": {
      "protocol_id": "uuid-123",
      "protocol_name": "Aave V3",
      "risk_score": 2.1
    }
  }
}
```

**Rate Limit**: 30 requests/minute

---

### Detect Anomalies

Detect anomalies in protocol metrics.

```http
GET /ml/prediction/{protocol_id}/anomalies
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "protocol_id": "uuid-123",
  "protocol_name": "Euler Finance",
  "is_anomalous": true,
  "confidence": 0.87,
  "anomalies": [
    {
      "feature": "tvl_change_rate",
      "current_value": -15.0,
      "expected_value": 2.0,
      "deviation": 17.0,
      "z_score": 4.2,
      "is_anomalous": true,
      "severity": "HIGH"
    }
  ],
  "overall_severity": "HIGH",
  "recommendations": [
    "Monitor official channels",
    "Review security updates",
    "Consider reducing exposure"
  ],
  "detected_at": "2025-12-01T10:00:00Z"
}
```

**Rate Limit**: 60 requests/minute

---

### Forecast Risk

Get risk forecast for next 7-30 days.

```http
GET /ml/prediction/{protocol_id}/forecast?days=30
Authorization: Bearer {token}
```

**Query Parameters**:
- `days` (optional): Forecast days ahead (default: 7, max: 30)

**Response** (200 OK):
```json
{
  "protocol_id": "uuid-123",
  "protocol_name": "Lido Finance",
  "current_risk": 2.3,
  "forecasts": [
    {
      "days_ahead": 7,
      "predicted_risk": 2.5,
      "confidence_lower": 2.2,
      "confidence_upper": 2.8,
      "trend": "STABLE"
    },
    {
      "days_ahead": 14,
      "predicted_risk": 2.8,
      "confidence_lower": 2.4,
      "confidence_upper": 3.2,
      "trend": "INCREASING"
    }
  ],
  "overall_trend": "INCREASING",
  "driving_factors": [
    "Upcoming protocol upgrade",
    "Increased market volatility"
  ],
  "recommendations": [
    "Monitor position over next 30 days",
    "Set risk alert at 3.5/10"
  ],
  "forecast_generated_at": "2025-12-01T10:00:00Z"
}
```

**Rate Limit**: 60 requests/minute

---

## 🕸️ Network Analysis Endpoints

### Calculate PageRank

Get protocol importance scores using PageRank algorithm.

```http
GET /ml/network/pagerank?damping_factor=0.85
Authorization: Bearer {token}
```

**Query Parameters**:
- `damping_factor` (optional): PageRank damping (default: 0.85, range: 0.5-0.95)
- `max_iterations` (optional): Max iterations (default: 100)

**Response** (200 OK):
```json
{
  "protocols": [
    {
      "protocol_id": "uuid-123",
      "protocol_name": "Aave V3",
      "pagerank_score": 9.2,
      "rank": 1,
      "interpretation": "Highly central protocol with many dependencies"
    }
  ],
  "top_10": [
    "Aave V3",
    "Uniswap V3",
    "Curve Finance",
    "Lido Finance",
    "MakerDAO"
  ],
  "algorithm_params": {
    "damping_factor": 0.85,
    "iterations": 47,
    "convergence_threshold": 0.0001
  }
}
```

**Rate Limit**: 30 requests/minute

---

### Detect Communities

Detect protocol communities using graph algorithms.

```http
GET /ml/network/communities?algorithm=label_propagation
Authorization: Bearer {token}
```

**Query Parameters**:
- `algorithm` (optional): Algorithm (default: "label_propagation")
  - `label_propagation`
  - `louvain`

**Response** (200 OK):
```json
{
  "communities": [
    {
      "community_id": 1,
      "protocols": [
        {
          "protocol_id": "uuid-123",
          "protocol_name": "Aave V3",
          "tvl": 6200000000,
          "risk_score": 2.1
        }
      ],
      "total_protocols": 18,
      "total_tvl": 12800000000,
      "average_risk": 2.4,
      "interconnections": 142,
      "label": "Lending & Borrowing"
    }
  ],
  "algorithm": "label_propagation",
  "modularity_score": 0.78,
  "total_communities": 5
}
```

**Rate Limit**: 30 requests/minute

---

### Calculate Centrality

Calculate centrality metrics for protocols.

```http
GET /ml/network/centrality?metric=betweenness&protocol_id={id}
Authorization: Bearer {token}
```

**Query Parameters**:
- `metric` (required): Centrality type
  - `degree` - Connection count
  - `betweenness` - Bridge importance
  - `closeness` - Average distance
  - `eigenvector` - Influence score
- `protocol_id` (optional): Specific protocol (or all)

**Response** (200 OK):
```json
{
  "metric_type": "betweenness",
  "protocols": [
    {
      "protocol_id": "uuid-123",
      "protocol_name": "Aave V3",
      "centrality_value": 0.28,
      "normalized_value": 8.4,
      "rank": 2,
      "interpretation": "Critical bridge in the network"
    }
  ],
  "network_statistics": {
    "total_protocols": 450,
    "average_centrality": 0.15,
    "max_centrality": 0.35
  }
}
```

**Rate Limit**: 30 requests/minute

---

### Simulate Contagion

Simulate cascade failure from a protocol.

```http
POST /ml/network/contagion/{protocol_id}
Content-Type: application/json
Authorization: Bearer {token}
```

**Path Parameters**:
- `protocol_id` (required): Origin protocol UUID

**Request Body**:
```json
{
  "failure_probability": 0.8,
  "transmission_rate": 0.6,
  "max_hops": 3
}
```

**Response** (200 OK):
```json
{
  "origin_protocol_id": "uuid-123",
  "origin_protocol_name": "Chainlink",
  "cascade_waves": [
    {
      "wave_number": 1,
      "affected_protocols": ["uuid-456", "uuid-789"],
      "tvl_at_risk": 15000000000,
      "cascade_probability": 0.48
    }
  ],
  "total_protocols_affected": 25,
  "total_tvl_at_risk": 45000000000,
  "cascade_probability": 0.68,
  "max_depth_reached": 3
}
```

**Rate Limit**: 20 requests/minute

---

## 📚 Complete Endpoint List

### GraphRAG Endpoints (6)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/graph/search/hybrid` | Hybrid search |
| POST | `/graph/search/similar-protocols` | Find similar |
| POST | `/graph/search/contextual` | Preference-based search |
| GET | `/graph/analytics` | Graph statistics |
| POST | `/graph/validate` | Validate integrity (admin) |
| POST | `/graph/generate-embeddings` | Generate embeddings (admin) |

### ML Prediction Endpoints (4)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/ml/prediction/:id` | Risk prediction |
| POST | `/ml/prediction/batch` | Batch prediction |
| GET | `/ml/prediction/:id/anomalies` | Anomaly detection |
| GET | `/ml/prediction/:id/forecast` | Risk forecast |

### Network Analysis Endpoints (4)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/ml/network/pagerank` | Protocol importance |
| GET | `/ml/network/communities` | Community detection |
| GET | `/ml/network/centrality` | Centrality metrics |
| POST | `/ml/network/contagion/:id` | Cascade simulation |

### Monitoring Endpoints (2)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/graph/monitoring/cache-stats` | Cache statistics |
| DELETE | `/graph/monitoring/cache` | Clear cache (admin) |

**Total**: 16 GraphRAG + ML endpoints

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Complete ML API Reference*
