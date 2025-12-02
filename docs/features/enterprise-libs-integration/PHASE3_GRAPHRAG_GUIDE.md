# 🧠 Phase 3: GraphRAG Knowledge Evolution - Implementation Guide

**Duration**: 10 weeks  
**Status**: Planning  
**Dependencies**: Phase 2 Complete ✅  
**Goal**: Transform knowledge retrieval from flat vector search to intelligent graph-based contextual understanding

---

## 📋 Executive Summary

### What We're Building

A **hybrid knowledge retrieval system** that combines:
- ✅ **Vector search** (existing pgvector) - "What documents mention Aave?"
- 🆕 **Graph traversal** (new GraphRAG) - "What protocols depend on Aave? What are their risks?"
- 🆕 **Relationship-aware retrieval** - Understanding connections between protocols, chains, risks, audits, etc.

### Why It Matters

**Current State (Phase 2)**:
```
User: "Is Aave safe?"
Vector Search: [doc1: "Aave has audits", doc2: "Aave TVL is $5B"]
Agent Response: "Aave is audited and has $5B TVL"
```

**Target State (Phase 3)**:
```
User: "Is Aave safe?"
GraphRAG Retrieval:
  ├─ Direct: "Aave audited by Trail of Bits, OpenZeppelin"
  ├─ Dependencies: "Uses Chainlink oracles (oracle risk)"
  ├─ Coverage: "Has $12M Nexus Mutual coverage"
  ├─ Historical: "No major exploits in 3 years"
  └─ Systemic: "83% of positions use stablecoins (depeg risk)"

Agent Response: "Aave is considered safe with multiple audits, 
but has oracle dependency on Chainlink and exposure to 
stablecoin depeg risks..."
```

**Key Benefits**:
- 🎯 **60% more comprehensive answers** - Surface non-obvious relationships
- 🚀 **40% faster complex queries** - Pre-computed graph traversals
- 🧠 **Systemic risk analysis** - No competitor has this
- 📊 **Competitive moat** - Unique knowledge graph of DeFi ecosystem

---

## 🏗️ Architecture Overview

### Current Architecture (Phase 2)

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                           │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Agent Router   │ (Intent classification)
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │  Agno Agent    │ (TradingAgent, LendingAgent, etc.)
         └────────┬───────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌──────────────┐    ┌──────────────┐
│  MCP Tools   │    │ Vector RAG   │
│  (27 tools)  │    │  (pgvector)  │
└──────────────┘    └──────┬───────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Knowledge   │
                    │   Chunks    │
                    └─────────────┘
```

### Target Architecture (Phase 3)

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                           │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Agent Router   │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │  Agno Agent    │
         └────────┬───────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌──────────────┐    ┌──────────────────┐
│  MCP Tools   │    │ Hybrid Retriever │ ✨ NEW
└──────────────┘    └─────────┬────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌──────────────┐    ┌──────────────┐
            │ Vector RAG   │    │  Graph RAG   │ ✨ NEW
            │  (pgvector)  │    │ (Neo4j/Age)  │
            └──────┬───────┘    └──────┬───────┘
                   │                   │
                   ▼                   ▼
            ┌─────────────┐    ┌──────────────┐
            │  Chunks     │    │  Knowledge   │
            │ (existing)  │    │    Graph     │ ✨ NEW
            └─────────────┘    └──────────────┘
                                       │
                                       ▼
                        ┌──────────────────────────┐
                        │ Entities & Relationships │
                        │  - Protocols             │
                        │  - Tokens                │
                        │  - Chains                │
                        │  - Audits                │
                        │  - Risks                 │
                        │  - Dependencies          │
                        └──────────────────────────┘
```

---

## 📅 10-Week Implementation Plan

### Week 1-2: Foundation & Ontology Design

#### Week 1: DeFi Ontology & Graph Schema

**Goal**: Define the knowledge graph structure for DeFi ecosystem

**Deliverables**:

1. **DeFi Ontology Document** (`docs/ontology/defi_ontology.yaml`):
```yaml
# Entity Types (Nodes)
entities:
  Protocol:
    properties:
      - id: UUID
      - name: string
      - tvl: decimal
      - chains: string[]
      - category: string  # lending, dex, yield, etc.
    
  Token:
    properties:
      - id: UUID
      - symbol: string
      - address: string
      - chain: string
      - price_usd: decimal
  
  Chain:
    properties:
      - id: UUID
      - name: string
      - tvl: decimal
      - native_token: string
  
  Audit:
    properties:
      - id: UUID
      - auditor: string
      - protocol_id: UUID
      - date: date
      - report_url: string
  
  Risk:
    properties:
      - id: UUID
      - type: string  # smart_contract, oracle, admin_key, etc.
      - severity: string  # low, medium, high, critical
      - description: text

# Relationship Types (Edges)
relationships:
  DEPLOYED_ON:
    from: Protocol
    to: Chain
    properties:
      - deployment_date: date
  
  DEPENDS_ON:
    from: Protocol
    to: Protocol
    properties:
      - dependency_type: string  # oracle, liquidity, collateral
      - criticality: string  # low, medium, high
  
  USES_TOKEN:
    from: Protocol
    to: Token
    properties:
      - role: string  # collateral, reward, governance
  
  AUDITED_BY:
    from: Protocol
    to: Audit
    properties:
      - findings_count: integer
  
  HAS_RISK:
    from: Protocol
    to: Risk
    properties:
      - mitigation: text
  
  COMPETES_WITH:
    from: Protocol
    to: Protocol
    properties:
      - market_overlap: decimal  # 0.0-1.0
```

2. **Graph Database Selection** (`docs/decisions/ADR-005-graph-database.md`):
   - **Option A**: Apache AGE (PostgreSQL extension) ✅ RECOMMENDED
     - Pros: Same database as existing PostgreSQL, easier ops
     - Cons: Less mature than Neo4j
   - **Option B**: Neo4j
     - Pros: Industry standard, robust
     - Cons: Separate database to manage
   
   **Decision**: Start with Apache AGE for Phase 3

3. **Database Schema** (`src/app/infrastructure/persistence_sqla/migrations/versions/20251202_003_add_graph_schema.py`):
```python
"""Add graph schema for GraphRAG

Revision ID: 20251202_003
Revises: 20251201_002
Create Date: 2025-12-02 10:00:00.000000
"""

def upgrade():
    # Create AGE extension
    op.execute("CREATE EXTENSION IF NOT EXISTS age;")
    op.execute("LOAD 'age';")
    op.execute("SET search_path = ag_catalog, '$user', public;")
    
    # Create graph
    op.execute("SELECT create_graph('defi_knowledge_graph');")
    
    # Note: AGE nodes/edges are schema-less (JSON-based)
    # We'll define structure in application layer
    
    # Create indexes for common queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_protocol_name 
        ON ag_catalog.ag_vertex ((properties->>'name'))
        WHERE label = 'Protocol';
    """)
```

**Success Criteria**:
- ✅ Ontology document complete and reviewed
- ✅ Graph database installed (Apache AGE)
- ✅ Migration applied successfully
- ✅ Can create test nodes/edges via SQL

---

#### Week 2: Graph Infrastructure

**Goal**: Build core graph operations layer

**Deliverables**:

1. **Graph Repository Port** (`src/app/domain/ports/graph_repository.py`):
```python
from typing import Protocol, List, Dict, Any, Optional
from uuid import UUID

class GraphRepository(Protocol):
    """Port for graph database operations"""
    
    async def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
    ) -> UUID:
        """Create a node in the graph"""
        ...
    
    async def create_edge(
        self,
        from_id: UUID,
        to_id: UUID,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """Create an edge between two nodes"""
        ...
    
    async def find_nodes(
        self,
        label: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Find nodes by label and properties"""
        ...
    
    async def traverse(
        self,
        start_node_id: UUID,
        relationship_types: List[str],
        max_depth: int = 3,
        direction: str = "outgoing",  # outgoing, incoming, both
    ) -> List[Dict[str, Any]]:
        """Traverse graph from a starting node"""
        ...
    
    async def shortest_path(
        self,
        from_id: UUID,
        to_id: UUID,
        relationship_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Find shortest path between two nodes"""
        ...
```

2. **AGE Repository Implementation** (`src/app/infrastructure/persistence_age/graph_repository_age.py`):
```python
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import json
from sqlalchemy import text
from app.domain.ports.graph_repository import GraphRepository

class GraphRepositoryAge(GraphRepository):
    """Apache AGE implementation of GraphRepository"""
    
    def __init__(self, session):
        self.session = session
        self.graph_name = "defi_knowledge_graph"
    
    async def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
    ) -> UUID:
        node_id = uuid4()
        properties_with_id = {**properties, "id": str(node_id)}
        
        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                CREATE (n:{label} {{properties}})
                RETURN n
            $$) as (n agtype);
        """)
        
        await self.session.execute(
            query,
            {"properties": json.dumps(properties_with_id)}
        )
        await self.session.commit()
        
        return node_id
    
    async def traverse(
        self,
        start_node_id: UUID,
        relationship_types: List[str],
        max_depth: int = 3,
        direction: str = "outgoing",
    ) -> List[Dict[str, Any]]:
        # Build relationship pattern
        if direction == "outgoing":
            rel_pattern = "-[r]->"
        elif direction == "incoming":
            rel_pattern = "<-[r]-"
        else:
            rel_pattern = "-[r]-"
        
        # Build type filter
        type_filter = "|".join(relationship_types) if relationship_types else ""
        
        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH path = (start {{id: '{start_node_id}'}}){rel_pattern}*1..{max_depth}(end)
                WHERE type(r) IN [{type_filter}]
                RETURN path
            $$) as (path agtype);
        """)
        
        result = await self.session.execute(query)
        rows = result.fetchall()
        
        # Parse AGE results into Python dicts
        paths = []
        for row in rows:
            # AGE returns JSON-like structures
            path_data = json.loads(row[0])
            paths.append(path_data)
        
        return paths
```

3. **Graph Service** (`src/app/domain/services/graph/graph_service.py`):
```python
from typing import List, Dict, Any, Optional
from uuid import UUID
from app.domain.ports.graph_repository import GraphRepository

class GraphService:
    """Domain service for graph operations"""
    
    def __init__(self, graph_repo: GraphRepository):
        self._graph_repo = graph_repo
    
    async def get_protocol_dependencies(
        self,
        protocol_id: UUID,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """Get all dependencies of a protocol"""
        
        # Traverse DEPENDS_ON relationships
        dependencies = await self._graph_repo.traverse(
            start_node_id=protocol_id,
            relationship_types=["DEPENDS_ON"],
            max_depth=max_depth,
            direction="outgoing",
        )
        
        # Organize by dependency type
        result = {
            "direct": [],
            "indirect": [],
            "critical": [],
        }
        
        for path in dependencies:
            depth = len(path["edges"])
            dep = path["end_node"]
            
            if depth == 1:
                result["direct"].append(dep)
            else:
                result["indirect"].append(dep)
            
            # Check if any edge is marked critical
            if any(e.get("criticality") == "high" for e in path["edges"]):
                result["critical"].append(dep)
        
        return result
    
    async def analyze_systemic_risk(
        self,
        protocol_id: UUID,
    ) -> Dict[str, Any]:
        """Analyze systemic risks for a protocol"""
        
        # Get protocol node
        protocols = await self._graph_repo.find_nodes(
            label="Protocol",
            filters={"id": str(protocol_id)},
            limit=1,
        )
        
        if not protocols:
            raise ValueError(f"Protocol {protocol_id} not found")
        
        protocol = protocols[0]
        
        # Get all risks
        risks = await self._graph_repo.traverse(
            start_node_id=protocol_id,
            relationship_types=["HAS_RISK"],
            max_depth=1,
            direction="outgoing",
        )
        
        # Get dependencies and their risks (systemic)
        deps = await self.get_protocol_dependencies(protocol_id, max_depth=2)
        systemic_risks = []
        
        for dep in deps["direct"] + deps["indirect"]:
            dep_risks = await self._graph_repo.traverse(
                start_node_id=UUID(dep["id"]),
                relationship_types=["HAS_RISK"],
                max_depth=1,
                direction="outgoing",
            )
            systemic_risks.extend(dep_risks)
        
        return {
            "protocol": protocol,
            "direct_risks": [r["end_node"] for r in risks],
            "systemic_risks": [r["end_node"] for r in systemic_risks],
            "risk_score": self._calculate_risk_score(risks, systemic_risks),
        }
    
    def _calculate_risk_score(
        self,
        direct_risks: List[Dict],
        systemic_risks: List[Dict],
    ) -> float:
        """Calculate overall risk score (0.0-10.0)"""
        
        severity_weights = {
            "low": 1.0,
            "medium": 3.0,
            "high": 7.0,
            "critical": 10.0,
        }
        
        direct_score = sum(
            severity_weights.get(r["end_node"].get("severity", "low"), 1.0)
            for r in direct_risks
        )
        
        systemic_score = sum(
            severity_weights.get(r["end_node"].get("severity", "low"), 1.0) * 0.5  # 50% weight
            for r in systemic_risks
        )
        
        total = direct_score + systemic_score
        
        # Normalize to 0-10 scale
        return min(total / 10.0, 10.0)
```

**Success Criteria**:
- ✅ Can create nodes and edges programmatically
- ✅ Can traverse graph relationships
- ✅ Can query graph via Cypher-like syntax
- ✅ GraphService passes unit tests

---

### Week 3-4: Data Ingestion & Graph Population

#### Week 3: Protocol Data Crawler

**Goal**: Build automated pipeline to populate graph from external sources

**Deliverables**:

1. **Protocol Crawler** (`src/app/infrastructure/crawlers/protocol_crawler.py`):
```python
import asyncio
import httpx
from typing import List, Dict, Any
from app.domain.ports.graph_repository import GraphRepository

class ProtocolCrawler:
    """Crawl DeFi protocols and populate graph"""
    
    def __init__(
        self,
        graph_repo: GraphRepository,
        defillama_api_key: str,
    ):
        self._graph_repo = graph_repo
        self._defillama_key = defillama_api_key
        self._http_client = httpx.AsyncClient()
    
    async def crawl_all_protocols(self) -> int:
        """Crawl all protocols from DeFiLlama"""
        
        # Get protocol list
        protocols = await self._fetch_protocols()
        
        count = 0
        for proto in protocols:
            try:
                await self._ingest_protocol(proto)
                count += 1
            except Exception as e:
                print(f"Failed to ingest {proto['name']}: {e}")
        
        return count
    
    async def _fetch_protocols(self) -> List[Dict[str, Any]]:
        """Fetch all protocols from DeFiLlama"""
        response = await self._http_client.get(
            "https://api.llama.fi/protocols"
        )
        return response.json()
    
    async def _ingest_protocol(self, proto_data: Dict[str, Any]):
        """Ingest a single protocol into graph"""
        
        # Create protocol node
        proto_id = await self._graph_repo.create_node(
            label="Protocol",
            properties={
                "name": proto_data["name"],
                "tvl": proto_data.get("tvl", 0),
                "category": proto_data.get("category", "unknown"),
                "chains": proto_data.get("chains", []),
                "slug": proto_data.get("slug", ""),
            }
        )
        
        # Create chain relationships
        for chain_name in proto_data.get("chains", []):
            chain_id = await self._get_or_create_chain(chain_name)
            await self._graph_repo.create_edge(
                from_id=proto_id,
                to_id=chain_id,
                relationship_type="DEPLOYED_ON",
            )
        
        # Fetch and add audit data
        audits = await self._fetch_audits(proto_data["slug"])
        for audit in audits:
            audit_id = await self._graph_repo.create_node(
                label="Audit",
                properties=audit,
            )
            await self._graph_repo.create_edge(
                from_id=proto_id,
                to_id=audit_id,
                relationship_type="AUDITED_BY",
            )
    
    async def _get_or_create_chain(self, chain_name: str) -> UUID:
        """Get existing chain node or create new one"""
        existing = await self._graph_repo.find_nodes(
            label="Chain",
            filters={"name": chain_name},
            limit=1,
        )
        
        if existing:
            return UUID(existing[0]["id"])
        
        return await self._graph_repo.create_node(
            label="Chain",
            properties={"name": chain_name}
        )
```

2. **Celery Task for Crawling** (`src/app/infrastructure/celery/tasks/graph_tasks.py`):
```python
from app.infrastructure.celery.app import celery_app
from app.infrastructure.crawlers.protocol_crawler import ProtocolCrawler

@celery_app.task(name="crawl_protocols")
def crawl_protocols():
    """Periodic task to update protocol graph"""
    async def runner(container):
        from app.domain.ports.graph_repository import GraphRepository
        
        graph_repo = await container.get(GraphRepository)
        crawler = ProtocolCrawler(
            graph_repo=graph_repo,
            defillama_api_key=settings.defillama_api_key,
        )
        
        count = await crawler.crawl_all_protocols()
        print(f"Crawled {count} protocols")
    
    asyncio.run(_run_task(runner))

# Schedule: Daily at 2 AM
celery_app.conf.beat_schedule["crawl-protocols"] = {
    "task": "crawl_protocols",
    "schedule": crontab(hour=2, minute=0),
}
```

**Success Criteria**:
- ✅ Crawler fetches 500+ protocols from DeFiLlama
- ✅ Protocols inserted into graph with properties
- ✅ Chain relationships created
- ✅ Celery task runs successfully

---

#### Week 4: Relationship Inference

**Goal**: Infer implicit relationships between entities

**Deliverables**:

1. **Dependency Inference Service** (`src/app/domain/services/graph/inference_service.py`):
```python
class InferenceService:
    """Infer relationships between graph entities"""
    
    async def infer_dependencies(self):
        """Infer DEPENDS_ON relationships"""
        
        # Example: If Protocol A uses Token X as collateral,
        # and Protocol B is the primary liquidity source for Token X,
        # then A DEPENDS_ON B (liquidity dependency)
        
        protocols = await self._graph_repo.find_nodes(label="Protocol")
        
        for proto in protocols:
            # Get tokens used by protocol
            tokens = await self._graph_repo.traverse(
                start_node_id=UUID(proto["id"]),
                relationship_types=["USES_TOKEN"],
                max_depth=1,
            )
            
            for token_path in tokens:
                token = token_path["end_node"]
                
                # Find protocols providing liquidity for this token
                liquidity_providers = await self._find_liquidity_providers(token)
                
                for provider in liquidity_providers:
                    if provider["id"] != proto["id"]:
                        # Create dependency relationship
                        await self._graph_repo.create_edge(
                            from_id=UUID(proto["id"]),
                            to_id=UUID(provider["id"]),
                            relationship_type="DEPENDS_ON",
                            properties={
                                "dependency_type": "liquidity",
                                "criticality": "medium",
                            }
                        )
```

2. **Risk Analysis Service** (`src/app/domain/services/graph/risk_analysis_service.py`):
```python
class RiskAnalysisService:
    """Analyze and assign risk scores"""
    
    async def analyze_all_protocols(self):
        """Analyze risk for all protocols"""
        
        protocols = await self._graph_repo.find_nodes(label="Protocol")
        
        for proto in protocols:
            risk_data = await self._analyze_protocol(UUID(proto["id"]))
            
            # Create risk nodes
            for risk in risk_data:
                risk_id = await self._graph_repo.create_node(
                    label="Risk",
                    properties=risk,
                )
                
                await self._graph_repo.create_edge(
                    from_id=UUID(proto["id"]),
                    to_id=risk_id,
                    relationship_type="HAS_RISK",
                )
    
    async def _analyze_protocol(self, proto_id: UUID) -> List[Dict]:
        """Analyze a single protocol for risks"""
        
        risks = []
        
        # Check for audit risks
        audits = await self._graph_repo.traverse(
            start_node_id=proto_id,
            relationship_types=["AUDITED_BY"],
            max_depth=1,
        )
        
        if len(audits) == 0:
            risks.append({
                "type": "smart_contract",
                "severity": "high",
                "description": "No audits found",
            })
        
        # Check for oracle dependencies
        deps = await self._graph_repo.traverse(
            start_node_id=proto_id,
            relationship_types=["DEPENDS_ON"],
            max_depth=1,
        )
        
        for dep in deps:
            if dep["edge"].get("dependency_type") == "oracle":
                risks.append({
                    "type": "oracle",
                    "severity": "medium",
                    "description": f"Depends on {dep['end_node']['name']} oracle",
                })
        
        return risks
```

**Success Criteria**:
- ✅ Dependency relationships inferred (100+ new edges)
- ✅ Risk nodes created for all protocols
- ✅ Risk scores calculated accurately

---

### Week 5-7: Hybrid Retrieval System

#### Week 5: Graph-Enhanced Retrieval

**Goal**: Combine vector search with graph traversal

**Deliverables**:

1. **Hybrid Retriever** (`src/app/domain/services/knowledge/hybrid_retriever.py`):
```python
from typing import List, Dict, Any
from app.domain.services.knowledge.retriever import KnowledgeRetriever
from app.domain.services.graph.graph_service import GraphService

class HybridRetriever:
    """Combine vector search with graph traversal"""
    
    def __init__(
        self,
        vector_retriever: KnowledgeRetriever,
        graph_service: GraphService,
    ):
        self._vector = vector_retriever
        self._graph = graph_service
    
    async def retrieve(
        self,
        query: str,
        knowledge_base_id: UUID,
        limit: int = 5,
        graph_depth: int = 2,
    ) -> Dict[str, Any]:
        """Retrieve using both vector and graph"""
        
        # 1. Vector search (existing)
        vector_results = await self._vector.retrieve(
            knowledge_base_id=knowledge_base_id,
            query=query,
            limit=limit,
        )
        
        # 2. Extract entities from vector results
        entities = self._extract_entities(vector_results)
        
        # 3. Graph traversal from entities
        graph_results = []
        for entity in entities:
            if entity["type"] == "Protocol":
                # Get dependencies
                deps = await self._graph.get_protocol_dependencies(
                    protocol_id=UUID(entity["id"]),
                    max_depth=graph_depth,
                )
                graph_results.append(deps)
                
                # Get risks
                risks = await self._graph.analyze_systemic_risk(
                    protocol_id=UUID(entity["id"]),
                )
                graph_results.append(risks)
        
        # 4. Combine results
        return {
            "vector_results": vector_results,
            "graph_results": graph_results,
            "entities": entities,
        }
    
    def _extract_entities(self, vector_results: List[Dict]) -> List[Dict]:
        """Extract named entities from vector search results"""
        
        # Use NER or simple pattern matching
        entities = []
        
        for result in vector_results:
            text = result["content"]
            
            # Example: Extract protocol names (in production, use NER)
            protocols = self._extract_protocol_names(text)
            for proto_name in protocols:
                entities.append({
                    "type": "Protocol",
                    "name": proto_name,
                    "source": result["id"],
                })
        
        return entities
```

2. **Update Agent to Use Hybrid Retrieval** (`src/app/infrastructure/agno/base_agent.py`):
```python
# Modify DeFiAgentBase to use hybrid retrieval
class DeFiAgentBase:
    def __init__(
        self,
        name: str,
        role: str,
        config: AgnoConfig,
        mcp_servers: List[str],
        hybrid_retriever: HybridRetriever,  # NEW
        instructions: Optional[List[str]] = None,
        debug_mode: bool = False,
    ):
        # ... existing code ...
        self.hybrid_retriever = hybrid_retriever
    
    async def _enrich_context(self, query: str) -> str:
        """Enrich query with graph knowledge"""
        
        # Use hybrid retrieval
        results = await self.hybrid_retriever.retrieve(
            query=query,
            knowledge_base_id=self.knowledge_base_id,
            limit=5,
            graph_depth=2,
        )
        
        # Format results for LLM
        context = "## Relevant Knowledge\n\n"
        
        # Vector results
        context += "### Direct Information:\n"
        for r in results["vector_results"]:
            context += f"- {r['content']}\n"
        
        # Graph results
        context += "\n### Related Context:\n"
        for g in results["graph_results"]:
            if "dependencies" in g:
                context += f"- Dependencies: {', '.join([d['name'] for d in g['direct']])}\n"
            if "risk_score" in g:
                context += f"- Risk Score: {g['risk_score']}/10\n"
        
        return context
```

**Success Criteria**:
- ✅ Hybrid retrieval returns both vector and graph results
- ✅ Agents use graph context in responses
- ✅ Responses are 30%+ more comprehensive

---

#### Week 6-7: Optimization & Caching

**Goal**: Make hybrid retrieval fast

**Deliverables**:

1. **Graph Query Optimization**:
   - Add indexes on frequently traversed relationships
   - Cache common graph queries in Redis
   - Implement query result pagination

2. **Pre-computation of Common Paths**:
   - Pre-compute dependency chains (store in cache)
   - Pre-compute risk scores (update nightly)
   - Materialize frequently accessed subgraphs

3. **Incremental Updates**:
   - Only re-crawl changed protocols
   - Only re-compute affected subgraphs
   - Implement change detection

**Success Criteria**:
- ✅ Hybrid retrieval < 500ms (p95)
- ✅ Graph queries < 200ms (p95)
- ✅ Cache hit rate > 60%

---

### Week 8-9: Integration & Testing

#### Week 8: End-to-End Integration

**Goal**: Integrate GraphRAG into all agents

**Deliverables**:

1. Update all 4 agents to use hybrid retrieval
2. Add graph-specific tools to MCP servers
3. Update WebSocket streaming to show graph insights
4. Create admin UI for graph visualization (optional)

**Success Criteria**:
- ✅ All agents use GraphRAG
- ✅ Graph insights visible in responses
- ✅ No performance regression

---

#### Week 9: Testing & Benchmarking

**Goal**: Comprehensive testing

**Deliverables**:

1. **Unit Tests**:
   - Graph repository operations
   - Inference service logic
   - Hybrid retrieval

2. **Integration Tests**:
   - End-to-end graph population
   - End-to-end hybrid retrieval
   - Agent responses with graph context

3. **Performance Tests**:
   - Graph query performance
   - Hybrid retrieval latency
   - Memory usage under load

4. **Quality Tests**:
   - A/B test responses (with vs without GraphRAG)
   - Measure comprehensiveness improvement
   - Measure accuracy improvement

**Success Criteria**:
- ✅ 90%+ test coverage
- ✅ All performance benchmarks met
- ✅ 40%+ improvement in answer quality

---

### Week 10: Documentation & Deployment

#### Week 10: Documentation & Production Readiness

**Goal**: Ship Phase 3 to production

**Deliverables**:

1. **Documentation**:
   - GraphRAG architecture guide
   - Ontology documentation
   - API documentation updates
   - Deployment guide updates

2. **Deployment**:
   - Production database migration
   - Initial graph population (seed data)
   - Monitoring dashboards for graph queries
   - Alerts for graph staleness

3. **Training**:
   - Internal team training on GraphRAG
   - User-facing changelog
   - Marketing materials (competitive advantage)

**Success Criteria**:
- ✅ All documentation complete
- ✅ Production deployment successful
- ✅ Team trained on new system
- ✅ Users see improved responses

---

## 📊 Success Metrics

### Technical Metrics

**Performance**:
- ✅ Hybrid retrieval < 500ms (p95)
- ✅ Graph queries < 200ms (p95)
- ✅ No regression in vector search performance
- ✅ Memory usage < 2GB for graph cache

**Quality**:
- ✅ 40%+ improvement in answer comprehensiveness
- ✅ 30%+ reduction in follow-up questions
- ✅ 95%+ accuracy in dependency detection
- ✅ 90%+ accuracy in risk analysis

### Business Metrics

**User Engagement**:
- ✅ 25%+ increase in session duration
- ✅ 30%+ increase in queries per session
- ✅ 20%+ increase in user satisfaction (CSAT)

**Competitive Moat**:
- ✅ Only platform with systemic risk analysis
- ✅ Only platform with protocol dependency mapping
- ✅ Unique knowledge graph of DeFi ecosystem

---

## 🚀 Getting Started

### Prerequisites

- ✅ Phase 2 complete (Agno + MCP)
- ✅ PostgreSQL 14+ with AGE extension
- ✅ Redis for caching
- ✅ DeFiLlama API access

### Quick Start

```bash
# Week 1: Setup
# 1. Install Apache AGE
sudo apt-get install postgresql-14-age

# 2. Run migration
alembic upgrade head

# 3. Verify graph setup
psql -U postgres -d anvil_backend -c "SELECT * FROM ag_graph WHERE name = 'defi_knowledge_graph';"

# Week 3: Populate graph
python -m app.infrastructure.crawlers.protocol_crawler

# Week 5: Test hybrid retrieval
python -m app.domain.services.knowledge.hybrid_retriever
```

---

## 📚 References

- **Apache AGE Documentation**: https://age.apache.org/
- **DeFi Protocol List**: https://defillama.com/protocols
- **Graph Database Patterns**: https://neo4j.com/developer/guide-data-modeling/
- **Knowledge Graph Construction**: https://arxiv.org/abs/2003.02320

---

## 🎯 Phase 3 Complete!

After 10 weeks, you'll have:
- ✅ 500+ protocols in knowledge graph
- ✅ 1000+ relationships mapped
- ✅ Hybrid vector + graph retrieval
- ✅ Systemic risk analysis
- ✅ 40%+ improvement in answer quality
- ✅ Unique competitive moat

**Next**: Phase 4 - Recommenders & Personalization! 🎁
