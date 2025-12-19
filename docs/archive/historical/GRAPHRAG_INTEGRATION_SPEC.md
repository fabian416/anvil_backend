# GraphRAG Integration - Enterprise Specification

**Document**: GraphRAG-001  
**Version**: 1.0.0  
**Date**: December 1, 2025  
**Status**: 🟡 **Priority 1** - Ready for Implementation  
**Owner**: CTO

---

## 🎯 Executive Summary

**GraphRAG** combines knowledge graphs with RAG (Retrieval-Augmented Generation) to enable systemic analysis, risk propagation tracking, and deep reasoning about structural relationships in DeFi protocols.

### Business Value

- **40% Analysis Quality Improvement**: Systemic understanding vs keyword matching
- **Deep Risk Assessment**: Track dependency chains and contagion risks
- **Relationship Discovery**: Find non-obvious protocol connections
- **Expert-Level Insights**: Answer "what-if" scenarios with confidence

### Timeline & Investment

- **Timeline**: 6 weeks (240 hours)
- **Complexity**: ⚠️⚠️⚠️ Very High
- **Investment**: $36,000
- **ROI**: 180 days (user retention, premium tier value)

---

## 1. Feature Control & Configuration

### 1.1 Environment Variables

**Required Configuration** (`.env` / `config.toml`):

```toml
[graphrag]
# Feature toggle
enabled = true

# Graph database
graph_db_url = "neo4j://localhost:7687"
graph_db_user = "neo4j"
graph_db_password = "${NEO4J_PASSWORD}"

# Extraction settings
extraction_model = "gpt-4o"
extraction_batch_size = 50
extraction_max_retries = 3

# Query settings
query_model = "gpt-4o"
vector_model = "text-embedding-3-large"
hybrid_search_weight_vector = 0.4
hybrid_search_weight_graph = 0.6

# Graph construction
entity_types = ["protocol", "token", "chain", "risk", "governance", "oracle"]
relationship_types = ["uses_oracle", "accepts_collateral", "depends_on", "competes_with"]

# Performance
max_graph_depth = 3
query_timeout_seconds = 10
cache_ttl_seconds = 3600

# Telemetry
telemetry_enabled = true
```

**Environment Variables**:
```bash
GRAPHRAG_ENABLED=true
GRAPHRAG_GRAPH_DB_URL=neo4j://localhost:7687
GRAPHRAG_GRAPH_DB_USER=neo4j
GRAPHRAG_GRAPH_DB_PASSWORD=secret
GRAPHRAG_EXTRACTION_MODEL=gpt-4o
GRAPHRAG_QUERY_MODEL=gpt-4o
```

---

## 2. Use Cases

### 2.1 Risk Propagation Analysis

**Query**: "If USDT depegs, what happens to my Aave position?"

**GraphRAG Process**:
1. Find USDT entity
2. Traverse: USDT --[COLLATERAL_IN]--> Aave
3. Traverse: Aave --[USES_ORACLE]--> Chainlink
4. Analyze impact: USDT depeg → Bad oracle data → Liquidations

**Response**: "If USDT depegs, Chainlink oracles will report the depeg. This triggers mass liquidations on Aave for USDT collateral positions. Your position has $X exposure."

### 2.2 Protocol Dependency Mapping

**Query**: "What protocols depend on Chainlink?"

**GraphRAG Process**:
1. Find Chainlink entity
2. Find all --[USES_ORACLE]--> relationships
3. Return protocol list with criticality scores

**Response**: "12 major protocols depend on Chainlink: Aave (critical), Compound (critical), MakerDAO (high), ..."

### 2.3 Comparative Protocol Analysis

**Query**: "Compare Aave v2 vs v3 risk parameters"

**GraphRAG Process**:
1. Find Aave v2 and v3 entities
2. Extract risk-related attributes
3. Find relationship differences
4. Generate comparison

**Response**: "Aave v3 introduces isolation mode (lower systemic risk), eMode (higher capital efficiency), but removes some v2 safeguards..."

---

## 3. API Endpoints

### 3.1 User Endpoints

#### **POST /api/v1/research/graph-query**

Query knowledge graph with natural language.

**Request**:
```json
{
  "query": "If USDT depegs, what happens to my Aave position?",
  "query_type": "local",
  "max_depth": 3
}
```

**Response**:
```json
{
  "query_id": "uuid",
  "answer": "If USDT depegs, Chainlink oracles will report...",
  "entities_found": [
    {"id": "usdt", "type": "token", "relevance": 1.0},
    {"id": "aave", "type": "protocol", "relevance": 0.95},
    {"id": "chainlink", "type": "oracle", "relevance": 0.85}
  ],
  "relationships": [
    {"source": "aave", "target": "usdt", "type": "accepts_collateral"},
    {"source": "aave", "target": "chainlink", "type": "uses_oracle"}
  ],
  "subgraph": {...},
  "confidence": 0.92,
  "latency_ms": 1850
}
```

#### **GET /api/v1/research/entity/{entity_id}**

Get entity details and relationships.

**Response**:
```json
{
  "entity_id": "aave",
  "type": "protocol",
  "properties": {
    "name": "Aave",
    "version": "v3",
    "tvl_usd": 5400000000,
    "deployed_chains": ["ethereum", "polygon", "arbitrum"]
  },
  "relationships": {
    "uses_oracle": ["chainlink"],
    "accepts_collateral": ["usdt", "usdc", "dai", "eth"],
    "competes_with": ["compound", "maker"]
  }
}
```

---

### 3.2 Admin Endpoints

#### **GET /api/v1/admin/graphrag/status**

**Response**:
```json
{
  "enabled": true,
  "graph_db": {
    "connected": true,
    "node_count": 1250,
    "relationship_count": 4800,
    "last_updated": "2025-12-01T08:00:00Z"
  },
  "extraction": {
    "documents_processed": 450,
    "entities_extracted": 1250,
    "relationships_extracted": 4800
  },
  "query_performance": {
    "avg_query_time_ms": 1200,
    "cache_hit_rate": 0.65
  }
}
```

#### **POST /api/v1/admin/graphrag/extract**

Trigger entity extraction from documents.

**Request**:
```json
{
  "documents": ["aave_whitepaper.pdf", "compound_audit.pdf"],
  "document_type": "whitepaper"
}
```

#### **POST /api/v1/admin/graphrag/rebuild**

Rebuild entire knowledge graph.

---

## 4. Database Schema

### 4.1 Neo4j Graph Schema

**Nodes** (Entity Types):
- `(:Protocol {name, version, tvl_usd, deployed_chains})`
- `(:Token {symbol, name, price_usd, market_cap})`
- `(:Chain {name, native_token, l1_or_l2})`
- `(:Risk {category, severity, description})`
- `(:Oracle {provider, assets_covered})`

**Relationships**:
- `(Protocol)-[:USES_ORACLE]->(Oracle)`
- `(Protocol)-[:ACCEPTS_COLLATERAL]->(Token)`
- `(Protocol)-[:DEPENDS_ON]->(Protocol)`
- `(Protocol)-[:COMPETES_WITH]->(Protocol)`
- `(Protocol)-[:DEPLOYED_ON]->(Chain)`

### 4.2 PostgreSQL Tables

#### **graphrag_extraction_jobs**

Track document extraction jobs.

```sql
CREATE TABLE graphrag_extraction_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_path TEXT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    entities_extracted INTEGER DEFAULT 0,
    relationships_extracted INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

#### **graphrag_query_telemetry**

Query performance tracking.

```sql
CREATE TABLE graphrag_query_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    query TEXT NOT NULL,
    query_type VARCHAR(20) NOT NULL,
    entities_found INTEGER,
    relationships_traversed INTEGER,
    confidence NUMERIC(5, 4),
    latency_ms INTEGER,
    cache_hit BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

---

## 5. Celery Background Tasks

### 5.1 Extraction Tasks

#### **Task: graphrag_extract_documents**

Process new documents and extract entities.

**Schedule**: Triggered manually or via webhook

```python
@celery_app.task(name="graphrag.extract_documents")
def graphrag_extract_documents(document_paths: List[str]):
    """Extract entities and relationships from documents."""
    # Implementation
    pass
```

#### **Task: graphrag_update_entity_properties**

Update entity properties from live data sources.

**Schedule**: Daily at 01:00 UTC

```python
@celery_app.task(name="graphrag.update_entity_properties")
def graphrag_update_entity_properties():
    """Update protocol TVLs, token prices, etc."""
    pass
```

---

## 6. Integration with Existing Solution

**Integration Point**: Research Agent (Agent Squad)

```python
# Research Agent uses GraphRAG for deep analysis

class ResearchAgent:
    def __init__(self, graphrag_engine: GraphRAGQueryEngine):
        self._graphrag = graphrag_engine
    
    async def execute(self, message: str) -> str:
        # Check if query benefits from graph
        if self._needs_graph_reasoning(message):
            result = await self._graphrag.query(message, query_type="local")
            return result.answer
        else:
            # Use standard LLM
            return await self._llm.execute(message)
```

---

## 7. Success Criteria

- ✅ Graph size: >1,000 entities, >5,000 relationships
- ✅ Query latency: <2s (p95)
- ✅ Extraction accuracy: >90%
- ✅ Analysis quality: +40% (user ratings)

---

**Document Status**: ✅ Ready for Implementation  
**Timeline**: 6 weeks (240 hours)  
**Investment**: $36,000
