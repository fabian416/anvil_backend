# FRONTEND_USER_PROTOCOL_GRAPH

## User Protocol Graph Visualization Module

**User Type:** Authenticated User  
**Module:** Protocol Ecosystem Visualization  
**Route:** `/protocols/:id/graph`, `/graph`  
**Platform:** Web (D3.js) & Mobile (React Native SVG)  
**Version:** 1.0 - Interactive Graph

---

## 📋 Module Overview

### Title
**Protocol Graph** - Interactive Ecosystem Visualization

### Description
Interactive force-directed graph visualization powered by D3.js showing protocol relationships, dependencies, communities, and risk indicators. Users can explore the DeFi ecosystem visually, understand protocol connections, and identify systemic risks.

### Key Capabilities
- Force-directed graph layout
- Interactive node exploration
- Dependency chain visualization
- Community cluster highlighting
- Risk-based node coloring
- TVL-based node sizing
- Zoom and pan controls
- Search and filter nodes
- Path finding between protocols
- Export graph views

---

## 👤 User Stories

### US-USER-GRAPH-001: View Protocol Dependencies
**As a** user  
**I want to** see visual representation of protocol dependencies  
**So that** I can understand ecosystem structure

**Acceptance Criteria:**
- Protocols shown as nodes
- Dependencies shown as edges
- Clear visual hierarchy
- Interactive exploration

---

### US-USER-GRAPH-002: Explore Related Protocols
**As a** user  
**I want to** click on protocols to explore connections  
**So that** I can discover the broader ecosystem

**Acceptance Criteria:**
- Click node to focus
- Show direct connections
- Highlight connection path
- Display node details

---

### US-USER-GRAPH-003: See Community Clusters
**As a** user  
**I want to** see protocol communities visually  
**So that** I can understand protocol groupings

**Acceptance Criteria:**
- Community detection algorithm
- Visual cluster grouping
- Color-coded communities
- Community labels

---

### US-USER-GRAPH-004: Identify Risk Patterns
**As a** user  
**I want to** see risk levels visualized on the graph  
**So that** I can spot high-risk areas

**Acceptance Criteria:**
- Risk-based node coloring
- Risk gradient visualization
- High-risk highlighting
- Risk legends

---

## 🖼️ Views & Wireframes

### View 1: Full Graph View (Web)

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Protocol Ecosystem    [🔍Search] [⚙️] [Export] [Help] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Filters: [All ▼] [Risk ▼] [Chain ▼]   [Reset]    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                       │   │
│  │          ●Compound                                    │   │
│  │         (TVL: $3B)                                    │   │
│  │            ↓                                          │   │
│  │      ●──●──●──●                                       │   │
│  │     USDC ETH DAI WBTC                                 │   │
│  │         ↓                                             │   │
│  │    [AAVE V3]◉────────●Chainlink                      │   │
│  │   (TVL: $6.2B)     (Oracles)                          │   │
│  │    Risk: 2.1🟢                                        │   │
│  │      ↙  ↓  ↘                                          │   │
│  │   ●USDC ●ETH ●WBTC                                    │   │
│  │         ↓                                             │   │
│  │    ●Curve ●Balancer                                   │   │
│  │      ↓        ↓                                       │   │
│  │   ●Convex  ●Aura                                      │   │
│  │                                                       │   │
│  │  Communities:                                         │   │
│  │  🔵 Lending (Aave, Compound)                          │   │
│  │  🟢 DEX (Curve, Balancer, Uniswap)                    │   │
│  │  🟡 Staking (Lido, Rocket Pool)                       │   │
│  │                                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Legend:                                                    │
│  Node Size = TVL  │  Color = Risk  │  Arrow = Dependency   │
│  🟢 Low  🟡 Med  🟠 High  🔴 Critical                       │
│                                                             │
│  Controls: [+ Zoom] [- Zoom] [⟲ Reset] [🎯 Center]        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### View 2: Focused Node View

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Aave V3 Ecosystem              [Share] [Save] [Info]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                       │   │
│  │              Chainlink ●                              │   │
│  │              (Oracles)                                │   │
│  │                  ↓                                    │   │
│  │            ╔═══════════╗                              │   │
│  │  USDC ●────║  AAVE V3  ║────● Compound                │   │
│  │            ║           ║                              │   │
│  │  ETH  ●────║ $6.2B TVL ║────● Curve                   │   │
│  │            ║ Risk: 2.1 ║                              │   │
│  │  DAI  ●────║   🟢 LOW  ║────● MakerDAO                │   │
│  │            ╚═══════════╝                              │   │
│  │  WBTC ●────────┘  └────────● Balancer                 │   │
│  │                                                       │   │
│  │  Stats:                                               │   │
│  │  • Dependencies: 5 (oracles, tokens)                  │   │
│  │  • Dependents: 127 protocols                          │   │
│  │  • PageRank: 9.2/10 (highly important)                │   │
│  │  • Community: 🔵 Lending & Borrowing                  │   │
│  │                                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Node Details:                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Name: Aave V3                                        │   │
│  │  Category: Lending                                    │   │
│  │  Chain: Multi-chain (Ethereum, Arbitrum, Polygon)    │   │
│  │  TVL: $6.2B                                           │   │
│  │  Risk Score: 2.1/10 🟢 LOW                            │   │
│  │  Audits: 18 ✓                                         │   │
│  │  Established: 2020 (5 years)                          │   │
│  │                                                       │   │
│  │  Relationships:                                       │   │
│  │  → DEPENDS_ON: Chainlink (oracles)                    │   │
│  │  → USES_TOKEN: USDC, ETH, DAI, WBTC                   │   │
│  │  ← COMPETES_WITH: Compound, MakerDAO                  │   │
│  │  ← INTEGRATED_BY: Curve, Balancer, Yearn             │   │
│  │                                                       │   │
│  │  [View Full Details] [Compare] [Simulate Cascade]    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### View 3: Dependency Chain View

```
┌─────────────────────────────────────────────────────────────┐
│  [←] Dependency Chain: Aave → Curve                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Shortest Path: 2 hops                                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                       │   │
│  │     [AAVE V3]                                         │   │
│  │    TVL: $6.2B                                         │   │
│  │   Risk: 2.1🟢                                         │   │
│  │         │                                             │   │
│  │         │ USES_TOKEN                                  │   │
│  │         ↓                                             │   │
│  │       ●USDC                                           │   │
│  │    (Stablecoin)                                       │   │
│  │         │                                             │   │
│  │         │ USES_TOKEN                                  │   │
│  │         ↓                                             │   │
│  │    [CURVE FINANCE]                                    │   │
│  │    TVL: $3.2B                                         │   │
│  │   Risk: 2.8🟢                                         │   │
│  │                                                       │   │
│  │  Relationship Type: Indirect (via USDC)               │   │
│  │  Cascade Risk: LOW 🟢                                 │   │
│  │                                                       │   │
│  │  💡 Insight:                                          │   │
│  │  Both protocols share USDC liquidity.                 │   │
│  │  USDC depeg would affect both simultaneously.         │   │
│  │                                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Alternative Paths (2):                                     │
│  • Aave → ETH → Curve (2 hops)                             │
│  • Aave → Compound → Curve (3 hops)                        │
│                                                             │
│  [View All Paths] [Simulate Cascade] [Risk Analysis]       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### View 4: Community Cluster View (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Protocol Communities        │
│                                     │
│  Detected 5 Communities             │
│  Algorithm: Label Propagation       │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔵 LENDING & BORROWING         ││
│  │     (18 protocols)               ││
│  │                                 ││
│  │     ●Aave  ●Compound  ●MakerDAO ││
│  │     ●Euler  ●Radiant  ●...      ││
│  │                                 ││
│  │  Total TVL: $12.8B              ││
│  │  Avg Risk: 2.4/10 🟢            ││
│  │  Interconnections: 142          ││
│  │                                 ││
│  │  [Explore →]                    ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🟢 DEX & AMM                   ││
│  │     (24 protocols)               ││
│  │                                 ││
│  │     ●Uniswap  ●Curve  ●Balancer ││
│  │     ●Sushiswap  ●Pancake  ●...  ││
│  │                                 ││
│  │  Total TVL: $8.4B               ││
│  │  Avg Risk: 2.8/10 🟢            ││
│  │  Interconnections: 238          ││
│  │                                 ││
│  │  [Explore →]                    ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🟡 STAKING                     ││
│  │     (12 protocols)               ││
│  │                                 ││
│  │     ●Lido  ●RocketPool  ●Frax  ││
│  │     ●StakeWise  ●...            ││
│  │                                 ││
│  │  Total TVL: $34.2B              ││
│  │  Avg Risk: 2.6/10 🟢            ││
│  │  Interconnections: 89           ││
│  │                                 ││
│  │  [Explore →]                    ││
│  └─────────────────────────────────┘│
│                                     │
│  [View Full Graph] [Compare]        │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Protocol Dependencies

```typescript
// GET /api/v1/graph/protocols/:id/dependencies
interface ProtocolDependenciesResponse {
  protocol_id: string;
  protocol_name: string;
  dependencies: Array<{
    protocol_id: string;
    protocol_name: string;
    relationship_type: string; // DEPENDS_ON, USES_TOKEN, etc.
    criticality: 'LOW' | 'MEDIUM' | 'HIGH';
    distance: number; // Hops from origin
  }>;
  dependents: Array<{
    protocol_id: string;
    protocol_name: string;
    relationship_type: string;
    impact_if_failure: string;
  }>;
  total_dependencies: number;
  total_dependents: number;
  importance_score: number; // PageRank score
}
```

---

### Get Protocol Ecosystem

```typescript
// GET /api/v1/graph/protocols/:id/ecosystem?depth=2
interface ProtocolEcosystemResponse {
  center_protocol: {
    id: string;
    name: string;
    tvl: number;
    risk_score: number;
  };
  nodes: Array<{
    id: string;
    name: string;
    type: 'Protocol' | 'Token' | 'Chain';
    tvl?: number;
    risk_score?: number;
    category?: string;
    distance: number; // Hops from center
  }>;
  edges: Array<{
    source_id: string;
    target_id: string;
    relationship_type: string;
    properties?: Record<string, any>;
  }>;
  communities?: Array<{
    community_id: number;
    protocol_ids: string[];
    label: string;
  }>;
  statistics: {
    total_nodes: number;
    total_edges: number;
    max_depth: number;
    avg_risk: number;
  };
}
```

---

### Get Network Communities

```typescript
// GET /api/v1/ml/network/communities
interface CommunitiesResponse {
  communities: Array<{
    community_id: number;
    protocols: Array<{
      protocol_id: string;
      protocol_name: string;
      tvl: number;
      risk_score: number;
    }>;
    total_protocols: number;
    total_tvl: number;
    average_risk: number;
    interconnections: number;
    label: string;
  }>;
  algorithm: string; // "label_propagation" | "louvain"
  modularity_score: number;
  total_communities: number;
}
```

---

### Calculate PageRank (Importance)

```typescript
// GET /api/v1/ml/network/pagerank
interface PageRankResponse {
  protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    pagerank_score: number; // 0-10
    rank: number; // 1, 2, 3, ...
    interpretation: string;
  }>;
  top_10: string[]; // Protocol names
}
```

---

### Find Shortest Path

```typescript
// GET /api/v1/graph/path/:source_id/:target_id
interface ShortestPathResponse {
  source: {
    protocol_id: string;
    protocol_name: string;
  };
  target: {
    protocol_id: string;
    protocol_name: string;
  };
  path: Array<{
    node_id: string;
    node_name: string;
    node_type: string;
    position: number; // 0, 1, 2, ...
  }>;
  relationships: Array<{
    from: string;
    to: string;
    type: string;
  }>;
  path_length: number; // Number of hops
  cascade_risk: 'LOW' | 'MEDIUM' | 'HIGH';
}
```

---

## 🎨 D3.js Integration

### Force Simulation Configuration

```typescript
import * as d3 from 'd3';

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  type: 'Protocol' | 'Token' | 'Chain';
  tvl?: number;
  risk_score?: number;
  category?: string;
  community_id?: number;
}

interface GraphEdge extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode;
  target: string | GraphNode;
  relationship_type: string;
}

const createForceSimulation = (
  nodes: GraphNode[],
  edges: GraphEdge[]
) => {
  const simulation = d3.forceSimulation(nodes)
    .force(
      'link',
      d3.forceLink(edges)
        .id((d: any) => d.id)
        .distance(100)
        .strength(0.5)
    )
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => getNodeRadius(d)))
    .force('x', d3.forceX(width / 2).strength(0.1))
    .force('y', d3.forceY(height / 2).strength(0.1));
  
  return simulation;
};
```

---

### Node Sizing by TVL

```typescript
const getNodeRadius = (node: GraphNode): number => {
  if (!node.tvl) return 8; // Default size
  
  // Logarithmic scale for TVL
  const minRadius = 8;
  const maxRadius = 40;
  const minTVL = 1_000_000; // $1M
  const maxTVL = 50_000_000_000; // $50B
  
  const logScale = d3.scaleLog()
    .domain([minTVL, maxTVL])
    .range([minRadius, maxRadius])
    .clamp(true);
  
  return logScale(node.tvl);
};
```

---

### Node Coloring by Risk

```typescript
const getNodeColor = (node: GraphNode): string => {
  if (!node.risk_score) return '#94A3B8'; // Default gray
  
  // Color scale from green (low risk) to red (high risk)
  const colorScale = d3.scaleLinear<string>()
    .domain([0, 3, 5, 7, 10])
    .range([
      '#10B981', // Green (LOW)
      '#84CC16', // Lime (LOW-MED)
      '#F59E0B', // Orange (MED-HIGH)
      '#EF4444', // Red (HIGH)
      '#DC2626', // Dark Red (CRITICAL)
    ])
    .clamp(true);
  
  return colorScale(node.risk_score);
};
```

---

### Edge Styling by Relationship

```typescript
const getEdgeStyle = (edge: GraphEdge): {
  stroke: string;
  strokeWidth: number;
  strokeDasharray?: string;
} => {
  const styles: Record<string, any> = {
    DEPENDS_ON: {
      stroke: '#3B82F6',
      strokeWidth: 2,
    },
    USES_TOKEN: {
      stroke: '#10B981',
      strokeWidth: 1,
      strokeDasharray: '4 2',
    },
    COMPETES_WITH: {
      stroke: '#EF4444',
      strokeWidth: 1,
      strokeDasharray: '2 2',
    },
    INTEGRATED_BY: {
      stroke: '#8B5CF6',
      strokeWidth: 1.5,
    },
  };
  
  return styles[edge.relationship_type] || {
    stroke: '#64748B',
    strokeWidth: 1,
  };
};
```

---

### Interactive Controls

```typescript
// Zoom behavior
const zoom = d3.zoom()
  .scaleExtent([0.1, 4])
  .on('zoom', (event) => {
    svg.attr('transform', event.transform);
  });

svg.call(zoom);

// Node click handler
const handleNodeClick = (event: any, node: GraphNode) => {
  // Highlight node and connections
  highlightNode(node.id);
  
  // Show details panel
  showNodeDetails(node);
  
  // Focus on node
  focusOnNode(node);
};

// Node drag behavior
const drag = d3.drag<SVGCircleElement, GraphNode>()
  .on('start', dragStarted)
  .on('drag', dragged)
  .on('end', dragEnded);

nodeElements.call(drag);

// Search and highlight
const searchAndHighlight = (query: string) => {
  const matchedNodes = nodes.filter(n => 
    n.name.toLowerCase().includes(query.toLowerCase())
  );
  
  // Fade non-matching nodes
  nodeElements
    .style('opacity', d => matchedNodes.includes(d) ? 1 : 0.2);
};
```

---

## 🎬 Motion Design

```typescript
const graphAnimations = {
  // Initial graph load
  graphEnter: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 1 }
  },
  
  // Node enter animation
  nodeEnter: {
    initial: { scale: 0 },
    animate: { scale: 1 },
    transition: {
      type: "spring",
      stiffness: 500,
      damping: 30,
      delay: 'stagger' // Stagger by force simulation
    }
  },
  
  // Edge draw animation
  edgeDraw: {
    initial: { pathLength: 0, opacity: 0 },
    animate: { pathLength: 1, opacity: 1 },
    transition: {
      duration: 0.8,
      ease: "easeInOut"
    }
  },
  
  // Node focus (click)
  nodeFocus: {
    scale: [1, 1.3, 1.2],
    transition: {
      type: "spring",
      stiffness: 500
    }
  },
  
  // Highlight connections
  connectionHighlight: {
    strokeWidth: [1, 3, 2],
    opacity: [0.3, 1, 0.8],
    transition: { duration: 0.4 }
  },
  
  // Community pulse
  communityPulse: {
    animate: {
      scale: [1, 1.05, 1],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },
  
  // Risk indicator throb
  riskIndicator: {
    animate: {
      boxShadow: [
        '0 0 0 0 rgba(239, 68, 68, 0)',
        '0 0 0 8px rgba(239, 68, 68, 0.3)',
        '0 0 0 0 rgba(239, 68, 68, 0)'
      ],
      transition: {
        duration: 2,
        repeat: Infinity
      }
    }
  }
};
```

---

## 🎨 Component Specifications

```typescript
// Main graph component
interface ProtocolGraphProps {
  protocolId?: string; // Center on specific protocol
  depth?: number; // Graph depth (default: 2)
  width: number;
  height: number;
  showCommunities?: boolean;
  showRiskIndicators?: boolean;
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
}

// Graph controls
interface GraphControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
  onCenter: () => void;
  onExport: () => void;
  zoomLevel: number;
}

// Node detail panel
interface NodeDetailPanelProps {
  node: GraphNode | null;
  dependencies: Dependency[];
  dependents: Dependent[];
  onClose: () => void;
  onViewFull: () => void;
  onCompare: () => void;
  onSimulateCascade: () => void;
}

// Community legend
interface CommunityLegendProps {
  communities: Community[];
  onSelectCommunity: (id: number) => void;
  selectedCommunityId?: number;
}

// Risk legend
interface RiskLegendProps {
  show: boolean;
}

// Path finder
interface PathFinderProps {
  sourceId: string;
  targetId: string;
  onPathFound: (path: PathNode[]) => void;
}
```

---

## ⚠️ Error Handling

```typescript
const graphErrors = {
  GRAPH_001: 'Failed to load graph data',
  GRAPH_002: 'Protocol not found in graph',
  GRAPH_003: 'Too many nodes (>1000) - please filter',
  GRAPH_004: 'Graph rendering failed',
  
  PATH_001: 'No path found between protocols',
  PATH_002: 'Path calculation failed',
  
  COMMUNITY_001: 'Community detection failed',
  COMMUNITY_002: 'No communities detected',
  
  EXPORT_001: 'Graph export failed',
};
```

---

## 🔒 Performance Optimization

### Data Loading
- Lazy load large graphs (>500 nodes)
- Pagination for node lists
- Virtual scrolling for large datasets
- Progressive rendering

### Rendering
- Canvas rendering for >100 nodes (not SVG)
- Level of detail (LOD) based on zoom
- Occlusion culling
- Throttled force simulation updates

### Caching
- Cache graph layouts
- Store zoom/pan state
- Persist user preferences
- Cache API responses (5 min)

---

## ♿ Accessibility

- Keyboard navigation (arrow keys move focus)
- Tab through nodes
- Enter to select/activate
- Escape to deselect
- Screen reader support for node data
- High contrast mode
- Focus indicators
- Skip to node list

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Protocol Graph Visualization*
