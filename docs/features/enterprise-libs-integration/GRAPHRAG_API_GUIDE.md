# GraphRAG API Usage Guide

Quick start guide for using the GraphRAG API endpoints.

---

## 🚀 Quick Start

### **Authentication**
All endpoints require Bearer token authentication:

```bash
curl -X POST http://localhost:8000/api/v1/graph/search/hybrid \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "lending protocol", "limit": 10}'
```

---

## 📋 Endpoints

### **1. Hybrid Search** 🔍

Search protocols using vector + graph hybrid retrieval.

**Endpoint**: `POST /api/v1/graph/search/hybrid`

**Request**:
```json
{
  "query": "decentralized lending protocol",
  "limit": 10,
  "include_risks": true,
  "include_dependencies": true,
  "similarity_threshold": 0.5
}
```

**Response**:
```json
{
  "query": "decentralized lending protocol",
  "results": [
    {
      "protocol_id": "uuid",
      "protocol_name": "Aave",
      "score": 0.89,
      "vector_similarity": 0.92,
      "graph_importance": 0.85,
      "context": {
        "tvl": 5000000000,
        "category": "Lending",
        "dependent_count": 15,
        "degree": 25,
        "audit_count": 5,
        "chain_count": 8,
        "dependencies": {
          "direct": ["Chainlink", "Uniswap"],
          "indirect": ["USDC"],
          "critical": ["Chainlink"]
        }
      },
      "risk_info": {
        "risk_score": 3.2,
        "direct_risks": 2,
        "systemic_risks": 5,
        "top_recommendation": "✅ LOW RISK"
      }
    }
  ],
  "total": 5
}
```

**Use Cases**:
- User searches for "best yield farming protocols"
- Agent needs DeFi protocol recommendations
- Research tool for protocol discovery

---

### **2. Find Similar Protocols** 🔗

Find protocols similar to a reference protocol.

**Endpoint**: `POST /api/v1/graph/search/similar`

**Request**:
```json
{
  "protocol_id": "aave-uuid",
  "limit": 5
}
```

**Response**: Same format as hybrid search

**Use Cases**:
- "Find alternatives to Aave"
- Protocol comparison
- Diversification recommendations

---

### **3. Contextual Search** 🎯

Search with user preferences and filtering.

**Endpoint**: `POST /api/v1/graph/search/contextual`

**Request**:
```json
{
  "query": "safe lending protocol",
  "preferences": {
    "category": "Lending",
    "max_risk_score": 5.0,
    "min_tvl": 1000000000
  },
  "limit": 5
}
```

**Response**: Same format as hybrid search

**Use Cases**:
- Risk-conscious investors
- Category-specific search
- Minimum TVL requirements

---

### **4. Graph Analytics** 📊

Get comprehensive graph statistics.

**Endpoint**: `GET /api/v1/graph/analytics/overview`

**Response**:
```json
{
  "overview": {
    "timestamp": "2025-12-02T...",
    "nodes": {
      "Protocol": 500,
      "Token": 1000,
      "Chain": 20,
      "total": 1520
    },
    "edges": {
      "DEPLOYED_ON": 2000,
      "DEPENDS_ON": 1500,
      "USES_TOKEN": 3000,
      "total": 6500
    },
    "health": {
      "avg_connections_per_node": 4.3
    }
  },
  "top_protocols": [
    {
      "name": "Aave",
      "slug": "aave",
      "tvl": 5000000000,
      "category": "Lending",
      "change_24h": 2.5
    }
  ],
  "category_distribution": {
    "Lending": 150,
    "DEX": 200,
    "Yield": 100
  },
  "chain_distribution": {
    "Ethereum": 300,
    "Polygon": 150,
    "Arbitrum": 100
  }
}
```

**Use Cases**:
- Dashboard overview
- Market analysis
- Ecosystem health monitoring

---

### **5. Validate Graph** ✅

Run integrity checks on the knowledge graph.

**Endpoint**: `POST /api/v1/graph/analytics/validate`

**Response**:
```json
{
  "timestamp": "2025-12-02T...",
  "checks": {
    "orphaned_nodes": {
      "count": 5,
      "issues": [...],
      "severity": "warning",
      "message": "Found 5 orphaned nodes"
    },
    "circular_dependencies": {
      "count": 0,
      "issues": [],
      "severity": "ok",
      "message": "No circular dependencies"
    }
  },
  "total_issues": 5,
  "is_valid": true
}
```

**Use Cases**:
- Data quality monitoring
- Debugging
- Health checks

---

### **6. Generate Embeddings** 🧠

Trigger embedding generation (admin only).

**Endpoint**: `POST /api/v1/graph/analytics/embeddings/generate`

**Request**:
```json
{
  "limit": 100,
  "force_regenerate": false
}
```

**Response**:
```json
{
  "protocols_fetched": 100,
  "embeddings_generated": 75,
  "embeddings_skipped": 25,
  "errors": 0
}
```

**Use Cases**:
- Initial setup
- Reindex after data changes
- Manual refresh

---

## 💡 Best Practices

### **1. Caching**
- Cache search results for common queries
- Use Redis for distributed caching
- Cache TTL: 5-15 minutes for search results

### **2. Rate Limiting**
- Implement per-user rate limits
- Hybrid search: 60 requests/minute
- Analytics: 120 requests/minute

### **3. Error Handling**
```python
try:
    response = await http_client.post("/graph/search/hybrid", json=request)
    response.raise_for_status()
    return response.json()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        # Handle auth error
    elif e.response.status_code == 429:
        # Handle rate limit
    elif e.response.status_code >= 500:
        # Handle server error
```

### **4. Pagination**
For large result sets, use limit parameter and implement client-side pagination.

---

## 🔧 Configuration

### **Environment Variables**:
```bash
OPENAI_API_KEY=your-key-here          # Required for embeddings
GRAPH_NAME=defi_knowledge_graph       # Default graph name
VECTOR_DIMENSIONS=1536                # OpenAI embedding dimensions
```

### **Performance Tuning**:
```python
# Adjust scoring weights
vector_weight = 0.6  # 60% semantic similarity
graph_weight = 0.4   # 40% graph importance

# Adjust similarity threshold
similarity_threshold = 0.5  # 0.0-1.0 (higher = stricter)
```

---

## 📊 Response Times

**Average response times**:
- Hybrid search: 300-500ms
- Similar protocols: 200-400ms
- Contextual search: 400-600ms
- Analytics: 100-200ms
- Validation: 1-3 seconds

**Factors affecting performance**:
- Number of protocols in graph
- Depth of dependency traversal
- Number of risk calculations
- Database query complexity

---

## 🐛 Troubleshooting

### **Issue**: No results returned
**Solution**: Lower `similarity_threshold` (try 0.3-0.4)

### **Issue**: Slow queries
**Solution**: 
- Reduce `limit` parameter
- Disable `include_dependencies`
- Check database indexes

### **Issue**: Stale data
**Solution**: 
- Trigger `generate_embeddings` endpoint
- Wait for background tasks to run
- Check Celery worker logs

---

## 📚 Additional Resources

- [Phase 3 Complete Documentation](./PHASE3_COMPLETE.md)
- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)

---

## 🎯 Common Workflows

### **Workflow 1: User Search**
```python
# 1. Get user query
query = "best yield farming protocols"

# 2. Search with hybrid retrieval
results = await search_hybrid(query, limit=10)

# 3. Display results with context
for result in results:
    print(f"{result.protocol_name} - Score: {result.score}")
    print(f"  Risk: {result.risk_info.risk_score}/10")
    print(f"  TVL: ${result.context.tvl:,.0f}")
```

### **Workflow 2: Protocol Comparison**
```python
# 1. Get protocol ID
protocol_id = get_protocol_id("Aave")

# 2. Find similar protocols
similar = await find_similar(protocol_id, limit=5)

# 3. Compare metrics
for protocol in similar:
    print(f"{protocol.protocol_name}:")
    print(f"  Similarity: {protocol.vector_similarity:.2f}")
    print(f"  Importance: {protocol.graph_importance:.2f}")
```

### **Workflow 3: Risk-Aware Discovery**
```python
# 1. Define risk tolerance
preferences = {
    "category": "Lending",
    "max_risk_score": 5.0,
    "min_tvl": 1_000_000_000
}

# 2. Search with preferences
results = await contextual_search(
    query="lending protocol",
    preferences=preferences,
    limit=5
)

# 3. Present safe options
for result in results:
    print(f"✅ {result.protocol_name} - Risk: {result.risk_info.risk_score}/10")
```

---

**Happy searching! 🚀**
