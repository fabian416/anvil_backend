# FRONTEND_ADMIN_NETWORK_ANALYSIS

## Admin Network Analysis Tools Module

**User Type:** Admin  
**Module:** Network Analysis & Graph Algorithms  
**Route:** `/admin/network`  
**Platform:** Web (Admin Panel)  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Network Analysis** - Graph Algorithm Tools & Insights

### Description
Advanced network analysis tools for understanding protocol relationships, detecting communities, calculating centrality metrics, and simulating contagion scenarios.

### Key Capabilities
- PageRank importance calculation
- Community detection algorithms
- Centrality metrics (degree, betweenness, closeness)
- Contagion simulation
- Circular dependency detection
- Graph statistics & visualization
- Algorithm parameter tuning
- Export analysis results

---

## 🖼️ Wireframes

### View 1: Network Analysis Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Admin Home       Network Analysis         [Refresh]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Network Overview                                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Total Nodes:        450 protocols                      ││
│  │  Total Edges:        3,500 relationships                ││
│  │  Avg Degree:         7.8 connections/protocol           ││
│  │  Graph Density:      0.017 (sparse)                     ││
│  │  Diameter:           8 hops (max distance)              ││
│  │  Communities:        5 detected                         ││
│  │  Modularity:         0.78 (well-structured)             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Algorithm Tools                                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Calculate  │ │   Detect     │ │   Analyze    │        │
│  │   PageRank   │ │  Communities │ │  Centrality  │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │   Simulate   │ │   Find       │ │   Export     │        │
│  │  Contagion   │ │   Cycles     │ │   Results    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                             │
│  ┌───────────────────────────────┬───────────────────────┐ │
│  │  Top Protocols (PageRank)     │  Community Summary    │ │
│  │                               │                       │ │
│  │  #1  Aave V3         9.2/10   │  🔵 Lending: 18      │ │
│  │  #2  Uniswap V3      8.8/10   │  🟢 DEX: 24          │ │
│  │  #3  Curve           8.5/10   │  🟡 Staking: 12      │ │
│  │  #4  Lido            8.2/10   │  🟠 Bridge: 8        │ │
│  │  #5  MakerDAO        7.9/10   │  🔴 Other: 15        │ │
│  │                               │                       │ │
│  │  [View All →]                 │  [View Details →]     │ │
│  └───────────────────────────────┴───────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### View 2: Community Detection Results

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Network Analysis    Community Detection Results        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Algorithm: Label Propagation                               │
│  Detected: 5 communities  |  Modularity: 0.78               │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🔵 COMMUNITY 1: Lending & Borrowing                    ││
│  │                                                         ││
│  │  Protocols: 18  |  Avg TVL: $4.2B  |  Avg Risk: 2.4    ││
│  │  Interconnections: 142                                  ││
│  │                                                         ││
│  │  Top Protocols:                                         ││
│  │  • Aave V3 (PageRank: 9.2)                              ││
│  │  • Compound (PageRank: 8.1)                             ││
│  │  • MakerDAO (PageRank: 7.9)                             ││
│  │  • Euler Finance (PageRank: 6.2)                        ││
│  │  ... 14 more                                            ││
│  │                                                         ││
│  │  [View Graph] [Export] [Analyze]                        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  🟢 COMMUNITY 2: DEX & AMM                              ││
│  │                                                         ││
│  │  Protocols: 24  |  Avg TVL: $2.8B  |  Avg Risk: 2.8    ││
│  │  Interconnections: 238                                  ││
│  │                                                         ││
│  │  Top Protocols:                                         ││
│  │  • Uniswap V3 (PageRank: 8.8)                           ││
│  │  • Curve Finance (PageRank: 8.5)                        ││
│  │  • Balancer (PageRank: 7.2)                             ││
│  │  ... 21 more                                            ││
│  │                                                         ││
│  │  [View Graph] [Export] [Analyze]                        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  [View All 5 Communities] [Compare] [Re-run Detection]      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### View 3: Contagion Simulation

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Network Analysis    Contagion Simulation               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Simulate Protocol Failure Impact                           │
│                                                             │
│  Origin Protocol: [Chainlink          ▼]                    │
│                                                             │
│  Parameters:                                                │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Failure Probability:    [0.8  ▼]  (80%)               ││
│  │  Transmission Rate:      [0.6  ▼]  (60%)               ││
│  │  Max Cascade Hops:       [3    ▼]  (3 levels)          ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  [Run Simulation]                                       ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
│  Simulation Results                                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Origin: Chainlink (Oracle Provider)                    ││
│  │                                                         ││
│  │  Cascade Visualization:                                 ││
│  │                                                         ││
│  │      Wave 1 (Immediate)      Wave 2 (Hours)             ││
│  │                                                         ││
│  │      [CHAINLINK] 💥                                     ││
│  │       ↙   ↓   ↘                                         ││
│  │    Aave Comp Synth                                      ││
│  │      ↓    ↓    ↓                                        ││
│  │    Curve Yearn ...                                      ││
│  │                                                         ││
│  │  Wave 1: 3 protocols (Direct dependencies)              ││
│  │  Wave 2: 8 protocols (Indirect exposure)                ││
│  │  Wave 3: 14 protocols (Secondary effects)               ││
│  │                                                         ││
│  │  Total Protocols Affected: 25                           ││
│  │  Total TVL at Risk: $45B                                ││
│  │  Cascade Probability: 68%                               ││
│  │  Max Depth Reached: 3 hops                              ││
│  │                                                         ││
│  │  [Export Report] [View Detailed Flow]                   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 Admin API Endpoints

### Calculate PageRank

```typescript
// POST /api/v1/admin/ml/network/pagerank
interface PageRankRequest {
  damping_factor?: number; // Default: 0.85
  max_iterations?: number; // Default: 100
}

interface PageRankResponse {
  protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    pagerank_score: number;
    rank: number;
  }>;
  top_10: string[];
  algorithm_params: {
    damping_factor: number;
    iterations: number;
    convergence_threshold: number;
  };
}
```

### Detect Communities

```typescript
// POST /api/v1/admin/ml/network/communities
interface CommunityDetectionRequest {
  algorithm: 'label_propagation' | 'louvain';
}

interface CommunityDetectionResponse {
  communities: Array<{
    community_id: number;
    protocols: Array<{
      protocol_id: string;
      protocol_name: string;
    }>;
    total_protocols: number;
    total_tvl: number;
    average_risk: number;
    interconnections: number;
    label: string;
  }>;
  algorithm: string;
  modularity_score: number;
  total_communities: number;
}
```

### Run Contagion Simulation

```typescript
// POST /api/v1/admin/ml/network/contagion/:protocol_id
interface ContagionSimulationRequest {
  failure_probability: number; // 0-1
  transmission_rate: number; // 0-1
  max_hops: number; // 1-10
}

interface ContagionSimulationResponse {
  origin_protocol_id: string;
  cascade_waves: Array<{
    wave_number: number;
    affected_protocols: string[];
    tvl_at_risk: number;
    cascade_probability: number;
  }>;
  total_protocols_affected: number;
  total_tvl_at_risk: number;
  cascade_probability: number;
  max_depth_reached: number;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Admin Network Analysis*
