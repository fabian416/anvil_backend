# Distillation Pass API Documentation

## Overview

The Distillation API provides endpoints for managing the intelligent request routing system.

---

## User-Facing Integration

The distillation pass is **transparent** to users - it happens automatically when they send messages. However, developers can access distillation metadata in responses.

### Response Metadata

Every chat response includes distillation information:

```json
{
  "content": "The current price of ETH is $2,150 (+2.5% 24h).",
  "distillation": {
    "route_type": "static",
    "intent": "price_check",
    "complexity": "trivial",
    "classification_latency_ms": 12,
    "cache_hit": false,
    "cost_saved_usd": 0.008
  }
}
```

---

## Admin API Endpoints

### GET /admin/distillation/config

Get distillation configuration.

**Permission**: `distillation.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "feature_flags": {
      "enabled": true,
      "cache_enabled": true,
      "static_responses_enabled": true,
      "semantic_cache_enabled": true
    },
    "thresholds": {
      "min_confidence": 0.7,
      "semantic_similarity": 0.95,
      "max_latency_ms": 100
    },
    "routing_rules": {
      "force_full_llm_intents": ["swap_request", "borrow_request"],
      "cache_ttl_by_intent": {
        "price_check": 60,
        "explain_concept": 3600
      }
    }
  }
}
```

### PUT /admin/distillation/config

Update distillation configuration.

**Permission**: `distillation.config.write`

**Request**:
```json
{
  "config_key": "thresholds",
  "config_value": {
    "min_confidence": 0.8,
    "semantic_similarity": 0.9,
    "max_latency_ms": 150
  },
  "reason": "Increasing confidence threshold"
}
```

---

### Static Responses Management

### GET /admin/distillation/static-responses

List all static responses.

**Permission**: `distillation.read`

**Query Parameters**:
- `intent`: Filter by intent
- `is_active`: Filter by active status

**Response**:
```json
{
  "success": true,
  "data": {
    "responses": [
      {
        "id": "uuid",
        "intent": "greeting",
        "variant": "default",
        "response_template": "Hello! I'm Anvil...",
        "template_variables": [],
        "data_source": null,
        "priority": 1,
        "is_active": true
      },
      {
        "id": "uuid",
        "intent": "price_check",
        "variant": "default",
        "response_template": "The current price of {token} is ${price}...",
        "template_variables": ["token", "price", "change_24h"],
        "data_source": "coingecko_api",
        "priority": 1,
        "is_active": true
      }
    ]
  }
}
```

### POST /admin/distillation/static-responses

Create new static response.

**Permission**: `distillation.config.write`

**Request**:
```json
{
  "intent": "apy_check",
  "variant": "aave_specific",
  "response_template": "Current APY for {token} on Aave:\n• Supply: {supply_apy}%\n• Borrow: {borrow_apy}%",
  "template_variables": ["token", "supply_apy", "borrow_apy"],
  "data_source": "aave_api",
  "conditions": {
    "protocol_mentioned": "aave"
  },
  "priority": 2
}
```

### PUT /admin/distillation/static-responses/{id}

Update static response.

### DELETE /admin/distillation/static-responses/{id}

Delete static response.

---

### Cache Management

### GET /admin/distillation/cache/stats

Get cache statistics.

**Permission**: `distillation.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "exact_cache": {
      "total_entries": 15420,
      "size_mb": 45.2,
      "hit_rate_24h": 0.18,
      "avg_ttl_seconds": 1800
    },
    "semantic_cache": {
      "total_entries": 8500,
      "size_mb": 120.5,
      "hit_rate_24h": 0.22,
      "avg_similarity": 0.97
    },
    "combined_hit_rate": 0.35,
    "estimated_cost_saved_24h_usd": 125.50
  }
}
```

### POST /admin/distillation/cache/invalidate

Invalidate cache entries.

**Permission**: `distillation.admin`

**Request**:
```json
{
  "cache_type": "exact",  // or "semantic" or "all"
  "filter": {
    "intent": "price_check",
    "older_than_hours": 1
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "invalidated_count": 1250,
    "cache_type": "exact"
  }
}
```

### POST /admin/distillation/cache/warm

Pre-warm cache with common queries.

**Permission**: `distillation.admin`

**Request**:
```json
{
  "queries": [
    "What is the price of ETH?",
    "What is yield farming?",
    "How do I stake ETH?"
  ],
  "force_refresh": true
}
```

---

### Telemetry

### GET /admin/distillation/telemetry/overview

Get distillation telemetry overview.

**Permission**: `distillation.read`

**Query Parameters**:
- `period`: 1h, 24h, 7d, 30d

**Response**:
```json
{
  "success": true,
  "data": {
    "period": "24h",
    "total_requests": 45231,
    "route_breakdown": {
      "reject": 125,
      "cache": 15420,
      "static": 8900,
      "light_llm": 12500,
      "full_llm": 8286
    },
    "route_percentages": {
      "reject": 0.3,
      "cache": 34.1,
      "static": 19.7,
      "light_llm": 27.6,
      "full_llm": 18.3
    },
    "cache_metrics": {
      "exact_hit_rate": 0.18,
      "semantic_hit_rate": 0.16,
      "combined_hit_rate": 0.34
    },
    "classification_metrics": {
      "avg_latency_ms": 15,
      "p95_latency_ms": 35,
      "avg_confidence": 0.87
    },
    "cost_savings": {
      "estimated_saved_usd": 352.40,
      "requests_avoided": 24320
    }
  }
}
```

### GET /admin/distillation/telemetry/intents

Get intent distribution.

**Permission**: `distillation.read`

**Response**:
```json
{
  "success": true,
  "data": {
    "period": "24h",
    "intents": [
      {"intent": "price_check", "count": 12500, "percentage": 27.6},
      {"intent": "swap_request", "count": 8200, "percentage": 18.1},
      {"intent": "explain_concept", "count": 5400, "percentage": 11.9},
      {"intent": "balance_check", "count": 4800, "percentage": 10.6}
    ],
    "avg_confidence_by_intent": {
      "price_check": 0.95,
      "swap_request": 0.88,
      "explain_concept": 0.82
    }
  }
}
```

### GET /admin/distillation/telemetry/timeseries

Get time-series metrics.

**Permission**: `distillation.read`

**Query Parameters**:
- `metric`: requests, cache_hits, cost_saved, latency
- `period`: 1h, 24h, 7d
- `group_by`: route_type, intent

**Response**:
```json
{
  "success": true,
  "data": {
    "metric": "requests",
    "period": "24h",
    "interval": "1h",
    "data": [
      {
        "timestamp": "2025-12-01T00:00:00Z",
        "value": 1850,
        "breakdown": {
          "cache": 650,
          "static": 380,
          "light_llm": 520,
          "full_llm": 300
        }
      }
    ]
  }
}
```

---

### Diagnostics

### POST /admin/distillation/test

Test distillation on a query.

**Permission**: `distillation.admin`

**Request**:
```json
{
  "query": "What's the current ETH price?",
  "include_cache_check": true,
  "include_static_check": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "What's the current ETH price?",
    "normalized_query": "what is the current eth price",
    
    "classification": {
      "intent": "price_check",
      "confidence": 0.97,
      "complexity": "trivial",
      "latency_ms": 8
    },
    
    "entities": {
      "tokens": ["ETH"],
      "protocols": [],
      "chains": [],
      "amounts": []
    },
    
    "routing_decision": {
      "route_type": "static",
      "reason": "Static response available for price_check with token entity",
      "suggested_model_tier": null
    },
    
    "cache_check": {
      "exact_hit": false,
      "semantic_hit": false,
      "semantic_best_match": {
        "query": "eth price now",
        "similarity": 0.92
      }
    },
    
    "static_check": {
      "available": true,
      "template": "The current price of {token} is ${price}...",
      "data_source": "coingecko_api"
    },
    
    "expected_response_time_ms": 50,
    "expected_cost_usd": 0
  }
}
```

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `DISTILL_DISABLED` | 503 | Distillation system disabled |
| `DISTILL_TIMEOUT` | 504 | Classification timed out |
| `DISTILL_CONFIG_INVALID` | 400 | Invalid configuration |
| `DISTILL_CACHE_ERROR` | 500 | Cache operation failed |
