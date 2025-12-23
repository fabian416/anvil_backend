# FRONTEND_USER_GRAPH_VISUALIZATION

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/graph/visualization.py`

## 1. Module Overview
The **Graph Visualization** module provides data endpoints optimized for **D3.js** or **Sigma.js** frontend libraries. It exposes the underlying knowledge graph of protocols and tokens.

**Base URL**: `/api/v1/user/graph/visualization`

---

## 2. Endpoints

### 2.1 Get Complete Graph
**GET** `/api/v1/user/graph/visualization/complete`

Returns both nodes and edges for rendering.

*   **Query Params**: `node_type`, `min_importance`, `max_nodes`.

**Response (200 OK):**
```json
{
  "nodes": [
    {
      "id": "uniswap",
      "label": "Uniswap",
      "type": "protocol",
      "importance": 0.95,
      "metadata": { "tvl": "3.2B" }
    }
  ],
  "edges": [
    {
      "source": "uniswap",
      "target": "eth",
      "type": "PROVIDES_LIQUIDITY",
      "weight": 0.9
    }
  ],
  "total_nodes": 1,
  "total_edges": 1
}
```

### 2.2 Get Subgraph
**GET** `/api/v1/user/graph/visualization/subgraph`

Focuses on a specific entity and its neighbors.

*   **Query**: `entity` (e.g., `uniswap`), `depth` (1-3).

---

## 3. Data Structure
*   **Nodes**: `id`, `label`, `type` (protocol, token), `importance` (0-1 for sizing).
*   **Edges**: `source`, `target`, `type` (relationship), `weight` (0-1 for line thickness).
