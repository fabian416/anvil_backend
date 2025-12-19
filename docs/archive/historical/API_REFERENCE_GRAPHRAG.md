# GraphRAG API Reference

**Version**: 1.0  
**Base URL**: `https://api.anvil.com/api/v1`  
**Authentication**: Bearer Token (JWT)  
**Last Updated**: December 1, 2025

---

## 🎯 Overview

Complete API reference for GraphRAG (Graph-based Retrieval Augmented Generation) endpoints. All endpoints require authentication via Bearer token in the Authorization header.

```http
Authorization: Bearer {jwt_token}
```

---

## 🔍 Search Endpoints

### Hybrid Protocol Search

Search protocols using hybrid semantic + graph retrieval.

```http
POST /graph/search/hybrid
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body**:
```json
{
  "query": "safe staking protocols on Ethereum",
  "limit": 10,
  "similarity_threshold": 0.7,
  "include_risks": true
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "protocol_id": "uuid-123",
      "protocol_name": "Lido Finance",
      "description": "Liquid staking protocol for Ethereum",
      "similarity_score": 0.95,
      "vector_score": 0.92,
      "graph_score": 0.89,
      "combined_score": 0.91,
      "risk_score": 2.3,
      "risk_level": "LOW",
      "tvl": 28400000000,
      "category": "Staking",
      "chain": "Ethereum",
      "audit_count": 15,
      "incident_count": 0
    }
  ],
  "total_results": 8,
  "search_time_ms": 45
}
```

**Query Parameters**:
- `query` (required): Search query string
- `limit` (optional): Max results (default: 10, max: 50)
- `similarity_threshold` (optional): Min similarity (default: 0.7, range: 0-1)
- `include_risks` (optional): Include risk scores (default: true)

**Error Responses**:
- `400`: Invalid query or parameters
- `401`: Unauthorized (invalid token)
- `429`: Rate limit exceeded
- `503`: GraphRAG service unavailable

**Rate Limit**: 60 requests/minute per user

---

### Find Similar Protocols

Find protocols similar to a given protocol.

```http
POST /graph/search/similar-protocols
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body**:
```json
{
  "protocol_id": "uuid-123",
  "limit": 10,
  "similarity_threshold": 0.6
}
```

**Response** (200 OK):
```json
{
  "base_protocol": {
    "protocol_id": "uuid-123",
    "protocol_name": "Lido Finance",
    "category": "Staking",
    "tvl": 28400000000,
    "risk_score": 2.3
  },
  "similar_protocols": [
    {
      "protocol_id": "uuid-456",
      "protocol_name": "Rocket Pool",
      "similarity_score": 0.94,
      "combined_score": 0.89,
      "risk_score": 2.8,
      "tvl": 4200000000,
      "category": "Staking",
      "why_similar": "Both are liquid staking protocols on Ethereum with similar mechanisms"
    }
  ]
}
```

**Rate Limit**: 60 requests/minute

---

### Contextual Search with User Preferences

Search with user preference filtering.

```http
POST /graph/search/contextual
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body**:
```json
{
  "query": "staking protocols",
  "user_preferences": {
    "risk_tolerance": "conservative",
    "preferred_chains": ["Ethereum", "Arbitrum"],
    "preferred_categories": ["Staking"],
    "min_tvl": 1000000000
  },
  "limit": 10
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "protocol_id": "uuid-123",
      "protocol_name": "Lido Finance",
      "relevance_score": 0.95,
      "matches_preferences": true,
      "preference_match_reasons": [
        "Risk level matches 'conservative' preference",
        "Deployed on preferred chain (Ethereum)",
        "Category matches preference (Staking)",
        "TVL exceeds minimum ($28.4B > $1B)"
      ],
      // ... other fields
    }
  ],
  "personalization_applied": true,
  "filters_applied": ["risk_tolerance", "preferred_chains", "min_tvl"]
}
```

**Rate Limit**: 60 requests/minute

---

## 📊 Analytics Endpoints

### Get Graph Analytics

Get overall graph statistics and insights.

```http
GET /graph/analytics
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "overview": {
    "total_protocols": 450,
    "total_tokens": 1250,
    "total_chains": 15,
    "total_relationships": 3500,
    "last_updated": "2025-12-01T10:00:00Z"
  },
  "top_protocols_by_tvl": [
    {
      "protocol_id": "uuid-123",
      "protocol_name": "Lido Finance",
      "tvl": 28400000000,
      "category": "Staking"
    }
  ],
  "category_distribution": {
    "Lending": 125,
    "DEX": 180,
    "Staking": 45,
    "Bridge": 30,
    "Derivatives": 70
  },
  "chain_distribution": {
    "Ethereum": 280,
    "Arbitrum": 85,
    "Polygon": 45,
    "Base": 40
  },
  "risk_summary": {
    "average_risk": 3.2,
    "low_risk_count": 320,
    "medium_risk_count": 95,
    "high_risk_count": 25,
    "critical_risk_count": 10
  }
}
```

**Rate Limit**: 30 requests/minute

---

### Validate Graph Integrity

Validate graph data quality (Admin only).

```http
POST /graph/validate
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "is_valid": false,
  "issues": [
    {
      "issue_type": "orphaned_nodes",
      "severity": "MEDIUM",
      "count": 5,
      "details": "5 protocols have no relationships",
      "affected_entities": ["Protocol A", "Protocol B"]
    },
    {
      "issue_type": "missing_properties",
      "severity": "LOW",
      "count": 12,
      "details": "12 nodes missing optional properties"
    }
  ],
  "summary": {
    "total_issues": 2,
    "critical_issues": 0,
    "warnings": 2
  }
}
```

**Rate Limit**: 10 requests/minute (Admin only)

---

## 🧬 Graph Structure Endpoints

### Get Protocol Dependencies

Get direct and transitive dependencies for a protocol.

```http
GET /graph/protocols/{protocol_id}/dependencies?depth=2
Authorization: Bearer {token}
```

**Path Parameters**:
- `protocol_id` (required): Protocol UUID

**Query Parameters**:
- `depth` (optional): Dependency depth (default: 2, max: 5)

**Response** (200 OK):
```json
{
  "protocol_id": "uuid-123",
  "protocol_name": "Aave V3",
  "dependencies": [
    {
      "protocol_id": "uuid-456",
      "protocol_name": "Chainlink",
      "relationship_type": "DEPENDS_ON",
      "criticality": "HIGH",
      "distance": 1
    }
  ],
  "dependents": [
    {
      "protocol_id": "uuid-789",
      "protocol_name": "Yearn Finance",
      "relationship_type": "USES_PROTOCOL",
      "impact_if_failure": "MEDIUM"
    }
  ],
  "total_dependencies": 5,
  "total_dependents": 127
}
```

**Rate Limit**: 120 requests/minute

---

### Get Protocol Ecosystem

Get full ecosystem map around a protocol.

```http
GET /graph/protocols/{protocol_id}/ecosystem?depth=2
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "center_protocol": {
    "id": "uuid-123",
    "name": "Aave V3",
    "tvl": 6200000000,
    "risk_score": 2.1
  },
  "nodes": [
    {
      "id": "uuid-456",
      "name": "Chainlink",
      "type": "Protocol",
      "tvl": 15000000000,
      "risk_score": 1.8,
      "category": "Oracle",
      "distance": 1
    }
  ],
  "edges": [
    {
      "source_id": "uuid-123",
      "target_id": "uuid-456",
      "relationship_type": "DEPENDS_ON",
      "properties": {
        "criticality": "HIGH"
      }
    }
  ],
  "communities": [
    {
      "community_id": 1,
      "protocol_ids": ["uuid-123", "uuid-789"],
      "label": "Lending & Borrowing"
    }
  ],
  "statistics": {
    "total_nodes": 25,
    "total_edges": 48,
    "max_depth": 2,
    "avg_risk": 2.8
  }
}
```

**Rate Limit**: 60 requests/minute

---

## 🎲 Vector & Embedding Endpoints

### Generate Embeddings (Admin Only)

Trigger embedding generation for protocols.

```http
POST /graph/generate-embeddings
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body**:
```json
{
  "protocol_ids": ["uuid-123", "uuid-456"],
  "force_regenerate": false
}
```

**Response** (200 OK):
```json
{
  "generated": 50,
  "updated": 10,
  "failed": 2,
  "total_processed": 62,
  "processing_time_seconds": 15.3
}
```

**Rate Limit**: 5 requests/minute (Admin only)

---

## 📈 Monitoring Endpoints

### Get Cache Statistics

Get query cache performance metrics.

```http
GET /graph/monitoring/cache-stats
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "hit_rate": 0.78,
  "miss_rate": 0.22,
  "total_hits": 15420,
  "total_misses": 4350,
  "avg_latency_cached_ms": 8.5,
  "avg_latency_uncached_ms": 145.2,
  "cache_size_mb": 128.5,
  "evictions": 450
}
```

**Rate Limit**: 30 requests/minute

---

### Clear Query Cache (Admin Only)

Clear GraphRAG query cache.

```http
DELETE /graph/monitoring/cache
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "success": true,
  "keys_deleted": 1234,
  "message": "Cache cleared successfully"
}
```

**Rate Limit**: 5 requests/minute (Admin only)

---

## 🔐 Authentication & Authorization

### Required Headers
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### Token Scopes
- `user`: Access to search and read endpoints
- `admin`: Access to validate, generate, and cache management

### Token Expiration
- Access tokens valid for 1 hour
- Refresh before expiry
- Use `/api/v1/account/refresh-token` to refresh

---

## ⚠️ Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| 400 | Bad Request | Check request body/parameters |
| 401 | Unauthorized | Provide valid Bearer token |
| 403 | Forbidden | Insufficient permissions (need admin) |
| 404 | Not Found | Protocol/entity doesn't exist |
| 422 | Validation Error | Fix validation errors in request |
| 429 | Rate Limit | Wait before retrying |
| 500 | Server Error | Contact support if persists |
| 503 | Service Unavailable | GraphRAG service temporarily down |

---

## 📊 Rate Limits

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Search | 60 req/min | Per user |
| Analytics | 30 req/min | Per user |
| Monitoring | 30 req/min | Per user |
| Admin (Validate) | 10 req/min | Per admin |
| Admin (Cache) | 5 req/min | Per admin |
| Admin (Generate) | 5 req/min | Per admin |

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1701388800
```

---

## 🚀 Best Practices

### Caching
- Search results cached for 5 minutes
- Dependencies cached for 1 hour
- Analytics cached for 15 minutes
- Use conditional requests (ETag)

### Pagination
- Use `limit` parameter (max: 50)
- Implement infinite scroll
- Cache previous pages

### Error Handling
- Always handle 503 (service unavailable)
- Implement exponential backoff for retries
- Show user-friendly error messages
- Log errors for debugging

### Performance
- Batch requests where possible
- Use similarity thresholds to reduce results
- Implement request debouncing
- Cache responses locally

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Complete GraphRAG API Reference*
