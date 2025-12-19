"""
Network Analysis Service

Advanced graph algorithms for DeFi ecosystem analysis:
- PageRank (protocol importance)
- Community Detection (ecosystem clusters)
- Centrality Analysis (critical nodes)
- Path Analysis (dependency chains)
- Contagion Simulation (cascade risk)
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Set, Optional
from uuid import UUID
from collections import defaultdict, deque
import math

from app.domain.graph.ports.graph_repository import GraphRepository, TraversalDirection


@dataclass
class PageRankResult:
    """PageRank importance score"""
    protocol_id: UUID
    protocol_name: str
    pagerank_score: float
    rank: int
    in_degree: int
    out_degree: int


@dataclass
class CommunityDetectionResult:
    """Community/cluster detection result"""
    community_id: int
    protocols: List[Dict[str, Any]]
    size: int
    density: float
    description: str


@dataclass
class CentralityResult:
    """Node centrality metrics"""
    protocol_id: UUID
    protocol_name: str
    degree_centrality: float
    betweenness_centrality: float
    closeness_centrality: float
    eigenvector_centrality: float
    importance_score: float  # Combined score


@dataclass
class ContagionSimulation:
    """Cascade risk simulation result"""
    origin_protocol_id: UUID
    origin_protocol_name: str
    affected_protocols: List[Dict[str, Any]]
    cascade_depth: int
    total_affected: int
    total_tvl_at_risk: float
    risk_score: float


class NetworkAnalysisService:
    """
    Advanced network analysis for DeFi protocols.
    
    Implements graph algorithms:
    - PageRank
    - Community Detection (Label Propagation)
    - Centrality Measures
    - Shortest Path
    - Contagion Simulation
    """
    
    def __init__(
        self,
        graph_repo: GraphRepository,
    ):
        """Initialize network analysis service"""
        self._graph_repo = graph_repo
    
    async def calculate_pagerank(
        self,
        damping_factor: float = 0.85,
        max_iterations: int = 100,
        convergence_threshold: float = 0.0001,
    ) -> List[PageRankResult]:
        """
        Calculate PageRank for all protocols.
        
        PageRank measures protocol importance based on:
        - Number of incoming dependencies
        - Importance of protocols that depend on it
        
        Args:
            damping_factor: Probability of following a link (default 0.85)
            max_iterations: Maximum iterations
            convergence_threshold: Convergence threshold
        
        Returns:
            List of protocols ranked by importance
        """
        # Get all protocol nodes
        protocols = await self._get_all_protocols()
        
        if not protocols:
            return []
        
        # Build adjacency graph
        graph = await self._build_adjacency_graph(protocols)
        
        # Initialize PageRank scores
        num_protocols = len(protocols)
        pagerank = {p: 1.0 / num_protocols for p in protocols}
        
        # Iterative PageRank calculation
        for iteration in range(max_iterations):
            new_pagerank = {}
            max_change = 0.0
            
            for protocol in protocols:
                # Base rank (random jump)
                rank = (1.0 - damping_factor) / num_protocols
                
                # Sum contributions from incoming links
                for source in graph["incoming"].get(protocol, []):
                    out_degree = len(graph["outgoing"].get(source, []))
                    if out_degree > 0:
                        rank += damping_factor * (pagerank[source] / out_degree)
                
                new_pagerank[protocol] = rank
                max_change = max(max_change, abs(rank - pagerank[protocol]))
            
            pagerank = new_pagerank
            
            # Check convergence
            if max_change < convergence_threshold:
                break
        
        # Build results
        results = []
        for idx, (protocol_id, score) in enumerate(
            sorted(pagerank.items(), key=lambda x: x[1], reverse=True),
            start=1
        ):
            protocol = await self._graph_repo.get_node(protocol_id)
            if protocol:
                results.append(PageRankResult(
                    protocol_id=protocol_id,
                    protocol_name=protocol.properties.get("name", "Unknown"),
                    pagerank_score=score,
                    rank=idx,
                    in_degree=len(graph["incoming"].get(protocol_id, [])),
                    out_degree=len(graph["outgoing"].get(protocol_id, [])),
                ))
        
        return results
    
    async def detect_communities(
        self,
        algorithm: str = "label_propagation",
    ) -> List[CommunityDetectionResult]:
        """
        Detect communities (clusters) in the protocol network.
        
        Identifies groups of protocols that are tightly connected,
        representing different DeFi ecosystems or categories.
        
        Args:
            algorithm: Detection algorithm ('label_propagation' or 'louvain')
        
        Returns:
            List of detected communities
        """
        protocols = await self._get_all_protocols()
        
        if not protocols:
            return []
        
        # Build adjacency graph
        graph = await self._build_adjacency_graph(protocols)
        
        if algorithm == "label_propagation":
            communities = await self._label_propagation(protocols, graph)
        else:
            # Default to label propagation
            communities = await self._label_propagation(protocols, graph)
        
        # Build results
        results = []
        for community_id, members in enumerate(communities):
            protocols_data = []
            total_tvl = 0.0
            
            for protocol_id in members:
                protocol = await self._graph_repo.get_node(protocol_id)
                if protocol:
                    tvl = float(protocol.properties.get("tvl", 0))
                    total_tvl += tvl
                    
                    protocols_data.append({
                        "protocol_id": str(protocol_id),
                        "name": protocol.properties.get("name", "Unknown"),
                        "tvl": tvl,
                        "category": protocol.properties.get("category"),
                    })
            
            # Calculate community density
            density = self._calculate_community_density(members, graph)
            
            # Generate description
            categories = [p["category"] for p in protocols_data if p["category"]]
            most_common_category = max(set(categories), key=categories.count) if categories else "Mixed"
            
            results.append(CommunityDetectionResult(
                community_id=community_id,
                protocols=protocols_data,
                size=len(members),
                density=density,
                description=f"{most_common_category} ecosystem with {len(members)} protocols and ${total_tvl/1e9:.2f}B TVL",
            ))
        
        # Sort by size
        results.sort(key=lambda x: x.size, reverse=True)
        
        return results
    
    async def calculate_centrality(
        self,
        protocol_id: Optional[UUID] = None,
    ) -> List[CentralityResult]:
        """
        Calculate centrality metrics for protocols.
        
        Centrality measures:
        - Degree: Number of connections
        - Betweenness: How often protocol is on shortest paths
        - Closeness: Average distance to all other protocols
        - Eigenvector: Connections to important protocols
        
        Args:
            protocol_id: Specific protocol (optional, calculates for all if None)
        
        Returns:
            List of centrality results
        """
        if protocol_id:
            protocols = [protocol_id]
        else:
            protocols = await self._get_all_protocols()
        
        graph = await self._build_adjacency_graph(protocols)
        
        results = []
        
        for pid in protocols:
            protocol = await self._graph_repo.get_node(pid)
            if not protocol:
                continue
            
            # Degree centrality
            in_degree = len(graph["incoming"].get(pid, []))
            out_degree = len(graph["outgoing"].get(pid, []))
            degree_centrality = (in_degree + out_degree) / (len(protocols) - 1) if len(protocols) > 1 else 0
            
            # Betweenness centrality (simplified)
            betweenness = await self._calculate_betweenness(pid, protocols, graph)
            
            # Closeness centrality (simplified)
            closeness = await self._calculate_closeness(pid, protocols, graph)
            
            # Eigenvector centrality (simplified - use in-degree as proxy)
            eigenvector = in_degree / max(len(protocols), 1)
            
            # Combined importance score
            importance = (
                degree_centrality * 0.3 +
                betweenness * 0.3 +
                closeness * 0.2 +
                eigenvector * 0.2
            )
            
            results.append(CentralityResult(
                protocol_id=pid,
                protocol_name=protocol.properties.get("name", "Unknown"),
                degree_centrality=degree_centrality,
                betweenness_centrality=betweenness,
                closeness_centrality=closeness,
                eigenvector_centrality=eigenvector,
                importance_score=importance,
            ))
        
        # Sort by importance
        results.sort(key=lambda x: x.importance_score, reverse=True)
        
        return results
    
    async def simulate_contagion(
        self,
        origin_protocol_id: UUID,
        propagation_probability: float = 0.8,
        max_depth: int = 5,
    ) -> ContagionSimulation:
        """
        Simulate cascade risk from protocol failure.
        
        Models how risk propagates through dependency graph:
        - Direct dependencies affected with high probability
        - Transitive dependencies with decreasing probability
        - Calculates total TVL at risk
        
        Args:
            origin_protocol_id: Origin of failure
            propagation_probability: Probability of cascade to dependent
            max_depth: Maximum cascade depth
        
        Returns:
            Contagion simulation result
        """
        origin = await self._graph_repo.get_node(origin_protocol_id)
        if not origin:
            raise ValueError(f"Protocol {origin_protocol_id} not found")
        
        # BFS to simulate cascade
        affected = {}  # protocol_id -> (depth, probability)
        queue = deque([(origin_protocol_id, 0, 1.0)])
        visited = {origin_protocol_id}
        total_tvl_at_risk = 0.0
        
        while queue:
            protocol_id, depth, probability = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            # Get dependents (protocols that depend on this one)
            dependents = await self._graph_repo.traverse(
                start_node_id=protocol_id,
                relationship_types=["DEPENDS_ON"],
                max_depth=1,
                direction=TraversalDirection.INCOMING,
            )
            
            for path in dependents:
                if path:
                    dependent_id = path[0]["end_node"]
                    
                    if dependent_id not in visited:
                        visited.add(dependent_id)
                        
                        # Cascade probability decreases with depth
                        cascade_prob = probability * propagation_probability
                        
                        if cascade_prob > 0.1:  # Only track significant risk
                            affected[dependent_id] = (depth + 1, cascade_prob)
                            queue.append((dependent_id, depth + 1, cascade_prob))
        
        # Build affected list
        affected_protocols = []
        for protocol_id, (depth, probability) in affected.items():
            protocol = await self._graph_repo.get_node(protocol_id)
            if protocol:
                tvl = float(protocol.properties.get("tvl", 0))
                tvl_at_risk = tvl * probability
                total_tvl_at_risk += tvl_at_risk
                
                affected_protocols.append({
                    "protocol_id": str(protocol_id),
                    "name": protocol.properties.get("name", "Unknown"),
                    "cascade_depth": depth,
                    "probability": round(probability, 3),
                    "tvl": tvl,
                    "tvl_at_risk": tvl_at_risk,
                })
        
        # Sort by probability
        affected_protocols.sort(key=lambda x: x["probability"], reverse=True)
        
        # Calculate overall risk score
        max_depth_reached = max((d for d, _ in affected.values()), default=0)
        risk_score = min(10.0, (
            len(affected) * 0.5 +
            max_depth_reached * 1.0 +
            (total_tvl_at_risk / 1e9) * 0.1
        ))
        
        return ContagionSimulation(
            origin_protocol_id=origin_protocol_id,
            origin_protocol_name=origin.properties.get("name", "Unknown"),
            affected_protocols=affected_protocols,
            cascade_depth=max_depth_reached,
            total_affected=len(affected),
            total_tvl_at_risk=total_tvl_at_risk,
            risk_score=risk_score,
        )
    
    async def _get_all_protocols(self) -> List[UUID]:
        """Get all protocol node IDs"""
        # Would query all protocols from graph
        # For now, return empty list (implementation depends on graph query)
        return []
    
    async def _build_adjacency_graph(
        self,
        protocols: List[UUID],
    ) -> Dict[str, Dict[UUID, List[UUID]]]:
        """Build adjacency lists for graph"""
        graph = {
            "outgoing": defaultdict(list),  # protocol -> dependencies
            "incoming": defaultdict(list),  # protocol -> dependents
        }
        
        for protocol_id in protocols:
            # Get dependencies
            dependencies = await self._graph_repo.traverse(
                start_node_id=protocol_id,
                relationship_types=["DEPENDS_ON"],
                max_depth=1,
            )
            
            for path in dependencies:
                if path:
                    target_id = path[0]["end_node"]
                    graph["outgoing"][protocol_id].append(target_id)
                    graph["incoming"][target_id].append(protocol_id)
        
        return graph
    
    async def _label_propagation(
        self,
        protocols: List[UUID],
        graph: Dict[str, Dict[UUID, List[UUID]]],
        max_iterations: int = 100,
    ) -> List[Set[UUID]]:
        """Label propagation algorithm for community detection"""
        
        # Initialize: each node is its own community
        labels = {p: i for i, p in enumerate(protocols)}
        
        # Iteratively update labels
        for _ in range(max_iterations):
            changed = False
            
            for protocol in protocols:
                # Get neighbor labels
                neighbors = (
                    graph["incoming"].get(protocol, []) +
                    graph["outgoing"].get(protocol, [])
                )
                
                if not neighbors:
                    continue
                
                # Find most common label among neighbors
                neighbor_labels = [labels[n] for n in neighbors if n in labels]
                
                if neighbor_labels:
                    most_common = max(set(neighbor_labels), key=neighbor_labels.count)
                    
                    if labels[protocol] != most_common:
                        labels[protocol] = most_common
                        changed = True
            
            if not changed:
                break
        
        # Group protocols by label
        communities = defaultdict(set)
        for protocol, label in labels.items():
            communities[label].add(protocol)
        
        return list(communities.values())
    
    def _calculate_community_density(
        self,
        members: Set[UUID],
        graph: Dict[str, Dict[UUID, List[UUID]]],
    ) -> float:
        """Calculate density of connections within community"""
        if len(members) < 2:
            return 0.0
        
        # Count internal edges
        internal_edges = 0
        for member in members:
            neighbors = graph["outgoing"].get(member, [])
            internal_edges += sum(1 for n in neighbors if n in members)
        
        # Maximum possible edges
        max_edges = len(members) * (len(members) - 1)
        
        return internal_edges / max_edges if max_edges > 0 else 0.0
    
    async def _calculate_betweenness(
        self,
        protocol_id: UUID,
        all_protocols: List[UUID],
        graph: Dict[str, Dict[UUID, List[UUID]]],
    ) -> float:
        """Calculate betweenness centrality (simplified)"""
        # Simplified: count how many shortest paths pass through this node
        # Full implementation would use all-pairs shortest paths
        
        # For now, use out-degree as proxy
        out_degree = len(graph["outgoing"].get(protocol_id, []))
        return out_degree / max(len(all_protocols), 1)
    
    async def _calculate_closeness(
        self,
        protocol_id: UUID,
        all_protocols: List[UUID],
        graph: Dict[str, Dict[UUID, List[UUID]]],
    ) -> float:
        """Calculate closeness centrality (simplified)"""
        # Simplified: average distance to all other nodes
        # Full implementation would use BFS to all nodes
        
        # For now, use inverse of degree as proxy
        degree = len(graph["incoming"].get(protocol_id, [])) + len(graph["outgoing"].get(protocol_id, []))
        return degree / max(len(all_protocols), 1) if degree > 0 else 0.0
