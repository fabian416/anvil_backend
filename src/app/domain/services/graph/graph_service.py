"""
Graph Service

Core domain service for graph operations.
Orchestrates complex graph queries and analysis.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from dataclasses import dataclass

from app.domain.ports.graph import (
    GraphRepository,
    GraphNode,
    GraphPath,
    TraversalDirection,
)


@dataclass
class ProtocolDependencies:
    """Result of protocol dependency analysis"""
    protocol: GraphNode
    direct: List[GraphNode]
    indirect: List[GraphNode]
    critical: List[GraphNode]
    depth_map: Dict[str, int]  # protocol_id -> depth


@dataclass
class RiskAnalysisResult:
    """Result of systemic risk analysis"""
    protocol: GraphNode
    direct_risks: List[GraphNode]
    systemic_risks: List[GraphNode]
    risk_score: float  # 0.0-10.0
    risk_breakdown: Dict[str, float]


class GraphService:
    """
    Domain service for graph operations.
    
    Provides high-level graph analysis and queries for the domain layer.
    """
    
    def __init__(self, graph_repo: GraphRepository):
        """
        Initialize graph service.
        
        Args:
            graph_repo: Graph repository implementation
        """
        self._graph_repo = graph_repo
    
    async def get_protocol_dependencies(
        self,
        protocol_id: UUID,
        max_depth: int = 3,
    ) -> ProtocolDependencies:
        """
        Get all dependencies of a protocol.
        
        Args:
            protocol_id: UUID of the protocol
            max_depth: Maximum depth to traverse
            
        Returns:
            ProtocolDependencies with categorized dependencies
            
        Example:
            >>> deps = await graph_service.get_protocol_dependencies(aave_id)
            >>> print(f"Aave has {len(deps.direct)} direct dependencies")
            >>> print(f"Critical: {[d.properties['name'] for d in deps.critical]}")
        """
        
        # Get protocol node
        protocol = await self._graph_repo.get_node(protocol_id)
        if not protocol:
            raise ValueError(f"Protocol {protocol_id} not found")
        
        # Traverse DEPENDS_ON relationships
        paths = await self._graph_repo.traverse(
            start_node_id=protocol_id,
            relationship_types=["DEPENDS_ON"],
            max_depth=max_depth,
            direction=TraversalDirection.OUTGOING,
        )
        
        # Organize dependencies by depth
        direct = []
        indirect = []
        critical = []
        depth_map = {}
        
        for path in paths:
            if len(path.edges) == 0:
                continue
            
            # Last node in path is the dependency
            dep = path.nodes[-1]
            depth = len(path.edges)
            
            # Track depth
            dep_id = str(dep.id)
            if dep_id not in depth_map:
                depth_map[dep_id] = depth
            else:
                # Keep shortest path
                depth_map[dep_id] = min(depth_map[dep_id], depth)
            
            # Categorize
            if depth == 1:
                if dep not in direct:
                    direct.append(dep)
            else:
                if dep not in indirect:
                    indirect.append(dep)
            
            # Check if any edge is marked critical
            for edge in path.edges:
                if edge.properties and edge.properties.get("criticality") == "critical":
                    if dep not in critical:
                        critical.append(dep)
                    break
        
        return ProtocolDependencies(
            protocol=protocol,
            direct=direct,
            indirect=indirect,
            critical=critical,
            depth_map=depth_map,
        )
    
    async def get_protocol_dependents(
        self,
        protocol_id: UUID,
        max_depth: int = 2,
    ) -> List[GraphNode]:
        """
        Get all protocols that depend on this protocol.
        
        Args:
            protocol_id: UUID of the protocol
            max_depth: Maximum depth to traverse
            
        Returns:
            List of dependent protocols
            
        Example:
            >>> dependents = await graph_service.get_protocol_dependents(chainlink_id)
            >>> print(f"{len(dependents)} protocols depend on Chainlink")
        """
        
        # Traverse DEPENDS_ON relationships in reverse
        paths = await self._graph_repo.traverse(
            start_node_id=protocol_id,
            relationship_types=["DEPENDS_ON"],
            max_depth=max_depth,
            direction=TraversalDirection.INCOMING,
        )
        
        dependents = []
        seen = set()
        
        for path in paths:
            if len(path.nodes) > 1:
                # First node is the dependent (since we're going incoming)
                dependent = path.nodes[0]
                if str(dependent.id) not in seen:
                    dependents.append(dependent)
                    seen.add(str(dependent.id))
        
        return dependents
    
    async def find_dependency_chain(
        self,
        from_protocol_id: UUID,
        to_protocol_id: UUID,
    ) -> Optional[GraphPath]:
        """
        Find dependency chain between two protocols.
        
        Args:
            from_protocol_id: Source protocol
            to_protocol_id: Target protocol
            
        Returns:
            GraphPath if chain exists, None otherwise
            
        Example:
            >>> chain = await graph_service.find_dependency_chain(aave_id, usdc_id)
            >>> if chain:
            ...     print(f"Aave depends on USDC via {chain.length} hops")
        """
        
        return await self._graph_repo.shortest_path(
            from_id=from_protocol_id,
            to_id=to_protocol_id,
            relationship_types=["DEPENDS_ON", "USES_TOKEN"],
        )
    
    async def get_protocol_ecosystem(
        self,
        protocol_id: UUID,
        max_depth: int = 2,
    ) -> Dict[str, List[GraphNode]]:
        """
        Get complete ecosystem around a protocol.
        
        Returns dependencies, dependents, competitors, and related protocols.
        
        Args:
            protocol_id: UUID of the protocol
            max_depth: Maximum depth for traversal
            
        Returns:
            Dictionary with categorized related protocols
            
        Example:
            >>> ecosystem = await graph_service.get_protocol_ecosystem(aave_id)
            >>> print(f"Dependencies: {len(ecosystem['dependencies'])}")
            >>> print(f"Dependents: {len(ecosystem['dependents'])}")
            >>> print(f"Competitors: {len(ecosystem['competitors'])}")
        """
        
        # Get dependencies
        deps = await self.get_protocol_dependencies(protocol_id, max_depth)
        
        # Get dependents
        dependents = await self.get_protocol_dependents(protocol_id, max_depth)
        
        # Get competitors
        competitors = await self._graph_repo.get_neighbors(
            node_id=protocol_id,
            relationship_type="COMPETES_WITH",
            direction=TraversalDirection.BOTH,
        )
        
        # Get protocols using same tokens
        related_protocols = []
        
        # Get tokens used by this protocol
        tokens = await self._graph_repo.get_neighbors(
            node_id=protocol_id,
            relationship_type="USES_TOKEN",
            direction=TraversalDirection.OUTGOING,
        )
        
        # For each token, find other protocols using it
        for token in tokens:
            other_protocols = await self._graph_repo.get_neighbors(
                node_id=token.id,
                relationship_type="USES_TOKEN",
                direction=TraversalDirection.INCOMING,
            )
            
            for proto in other_protocols:
                if proto.id != protocol_id and proto not in related_protocols:
                    related_protocols.append(proto)
        
        return {
            "dependencies": deps.direct + deps.indirect,
            "dependents": dependents,
            "competitors": competitors,
            "related_protocols": related_protocols,
        }
    
    async def calculate_protocol_importance(
        self,
        protocol_id: UUID,
    ) -> Dict[str, Any]:
        """
        Calculate importance score of a protocol in the ecosystem.
        
        Based on:
        - Number of dependents (protocols depending on it)
        - TVL (if available)
        - Number of audits
        - Number of chains deployed on
        
        Args:
            protocol_id: UUID of the protocol
            
        Returns:
            Dictionary with importance metrics and score
            
        Example:
            >>> importance = await graph_service.calculate_protocol_importance(chainlink_id)
            >>> print(f"Importance score: {importance['score']}/10")
            >>> print(f"Dependents: {importance['dependent_count']}")
        """
        
        # Get protocol
        protocol = await self._graph_repo.get_node(protocol_id)
        if not protocol:
            raise ValueError(f"Protocol {protocol_id} not found")
        
        # Get dependents
        dependents = await self.get_protocol_dependents(protocol_id, max_depth=1)
        dependent_count = len(dependents)
        
        # Get degree (total connections)
        degree = await self._graph_repo.get_node_degree(
            node_id=protocol_id,
            direction=TraversalDirection.BOTH,
        )
        
        # Get audits
        audits = await self._graph_repo.get_neighbors(
            node_id=protocol_id,
            relationship_type="AUDITED_BY",
            direction=TraversalDirection.OUTGOING,
        )
        audit_count = len(audits)
        
        # Get chains
        chains = await self._graph_repo.get_neighbors(
            node_id=protocol_id,
            relationship_type="DEPLOYED_ON",
            direction=TraversalDirection.OUTGOING,
        )
        chain_count = len(chains)
        
        # Calculate score (0-10)
        score = 0.0
        
        # Dependent weight (40%)
        score += min(dependent_count / 10.0, 1.0) * 4.0
        
        # Degree weight (20%)
        score += min(degree / 20.0, 1.0) * 2.0
        
        # Audit weight (20%)
        score += min(audit_count / 5.0, 1.0) * 2.0
        
        # Chain weight (10%)
        score += min(chain_count / 5.0, 1.0) * 1.0
        
        # TVL weight (10%)
        tvl = protocol.properties.get("tvl", 0)
        if tvl > 0:
            # Normalize TVL (1B = max score)
            score += min(tvl / 1_000_000_000, 1.0) * 1.0
        
        return {
            "score": round(score, 2),
            "dependent_count": dependent_count,
            "degree": degree,
            "audit_count": audit_count,
            "chain_count": chain_count,
            "tvl": tvl,
            "category": protocol.properties.get("category", "unknown"),
        }
    
    async def find_circular_dependencies(
        self,
        max_depth: int = 5,
    ) -> List[List[GraphNode]]:
        """
        Find circular dependencies in the graph.
        
        Args:
            max_depth: Maximum cycle length to detect
            
        Returns:
            List of circular dependency chains
            
        Note:
            This is a potentially expensive operation on large graphs.
            Consider running as a background task.
        """
        
        # Get all protocols
        protocols = await self._graph_repo.find_nodes(
            label="Protocol",
            limit=1000,
        )
        
        cycles = []
        
        for protocol in protocols:
            # Try to find a path back to itself
            path = await self._graph_repo.shortest_path(
                from_id=protocol.id,
                to_id=protocol.id,
                relationship_types=["DEPENDS_ON"],
                max_depth=max_depth,
            )
            
            if path and len(path.nodes) > 1:
                # Found a cycle
                cycles.append(path.nodes)
        
        return cycles
