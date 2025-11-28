# GraphRAG Library Specification

## 1. Strategic Overview (CTO Perspective)
**GraphRAG** represents the next evolution of our retrieval architecture. While standard RAG (Vector Search) is excellent for finding *semantically similar* text, it fails to understand *structural relationships* (dependencies, causality, hierarchies).

In DeFi, everything is a graph:
-   Tokens belong to Protocols.
-   Protocols run on Chains.
-   Risks propagate through Dependencies (e.g., Aave depends on Chainlink).

By adopting GraphRAG, we move the **Research Agent** from "Text Retrieval" to "Knowledge Navigation".

## 2. Use Cases

### Primary: Systemic Risk Analysis
-   **Scenario**: "If USDT depegs, what happens to my Aave position?"
-   **Execution**:
    -   Vector RAG might miss the connection if not explicitly stated in one doc.
    -   GraphRAG traverses: `USDT --collateral_for--> Aave --used_by--> User`. It identifies the contagion path.

### Secondary: Protocol Due Diligence
-   **Scenario**: "Explain the governance structure of MakerDAO."
-   **Execution**: Retrieves the "Governance" subgraph (Proposals, Voters, Delegates) rather than just random forum posts.

## 3. Architecture & Integration

### System Fit
GraphRAG sits in the **Infrastructure Layer** as an advanced `Retriever` adapter, running alongside our existing `Agno` Knowledge Base.

### Key Components
-   **Knowledge Graph**: A Neo4j or NetworkX graph stored alongside our Vectors.
-   **Indexer**: An extraction pipeline that reads Whitepapers and extracts Entities (Nodes) and Relationships (Edges).
-   **Query Engine**: Converts user questions into Graph Traversal queries (Cypher/Gremlin) + Vector Similarity.

## 4. Implementation Strategy
1.  **Extraction**: Use LLMs to parse documents and output `(Subject, Predicate, Object)` tuples.
    -   *Example*: "Aave uses Chainlink" -> `(Aave, USES, Chainlink)`.
2.  **Storage**: Use a Graph Database (or an embedded `networkx` graph for MVP).
3.  **Hybrid Search**: Combine Vector Score + Graph Centrality (PageRank) to rank results.

## 5. Roadmap
-   [ ] **Phase 1**: Define the `DeFi Ontology` (Types of nodes/edges).
-   [ ] **Phase 2**: Build the Extraction Pipeline (LLM-based).
-   [ ] **Phase 3**: Integrate into `ResearchAgent`.
