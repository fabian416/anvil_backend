# UC-GRAPHRAG: GraphRAG & Knowledge Base

**Version:** 1.0.0  
**Status:** ✅ LIVE (Production)  
**Category:** Core Platform  
**Total Use Cases:** 4

---

## 📊 **OVERVIEW**

Graph-based Retrieval Augmented Generation (GraphRAG) system using Apache AGE for knowledge representation and retrieval.

### **Business Value**
- Graph-based knowledge representation
- Entity extraction and linking
- Relationship mapping
- Context-aware retrieval
- Vector search integration

### **Technical Stack**
- **Graph Database:** Apache AGE (PostgreSQL extension)
- **Query Language:** Cypher
- **Vector Search:** pgvector
- **Embeddings:** OpenAI embeddings

---

## 🎯 **USE CASES**

### **UC-GRAPH-1: Graph-Based RAG**
- **Status:** ✅ LIVE
- **Implementation:** GraphRAG framework
- **Capabilities:** Context-aware information retrieval

### **UC-GRAPH-2: Entity Extraction**
- **Status:** ✅ LIVE
- **Database:** Apache AGE
- **Capabilities:** Extract entities from text, create graph nodes

### **UC-GRAPH-3: Relationship Mapping**
- **Status:** ✅ LIVE
- **Queries:** Cypher queries
- **Capabilities:** Map relationships between entities

### **UC-GRAPH-4: Knowledge Retrieval**
- **Status:** ✅ LIVE
- **Method:** Vector search + graph traversal
- **Capabilities:** Retrieve relevant knowledge for queries

---

## 🏗️ **ARCHITECTURE**

```
Domain Layer:
  └─ (Graph entities and relationships)

Application Layer:
  ├─ graph_analytics_interactor.py
  ├─ generate_embeddings_interactor.py
  └─ hybrid_retrieval_interactor.py

Infrastructure Layer:
  └─ adapters/
     ├─ graph_repository_age.py
     └─ embedding_service.py
```

---

## 📚 **RELATED DOCUMENTATION**

- [GraphRAG Implementation](../../LIBS_COMPLETE_INTEGRATION_PLAN.md#graphrag)
- [Apache AGE Setup](../../../src/app/infrastructure/persistence_sqla/)

---

**Status:** ✅ 100% Complete (4/4 use cases live)  
**Last Updated:** December 2, 2025
