"""
Graph Analytics Interactor

Service for analyzing graph statistics and insights.
"""

from typing import Dict, Any, List
from datetime import datetime
import logging

from app.domain.ports.graph import GraphRepository, TraversalDirection


logger = logging.getLogger(__name__)


class GraphAnalyticsInteractor:
    """
    Analyze graph statistics and generate insights.
    
    Provides:
    - Node/edge counts by type
    - Top protocols by TVL
    - Most connected protocols
    - Risk distribution
    - Growth metrics
    """
    
    def __init__(self, graph_repo: GraphRepository):
        """
        Initialize analytics interactor.
        
        Args:
            graph_repo: Graph repository
        """
        self._graph_repo = graph_repo
    
    async def get_overview_stats(self) -> Dict[str, Any]:
        """
        Get overview statistics of the knowledge graph.
        
        Returns:
            Overview statistics
        """
        
        logger.info("Generating graph overview statistics...")
        
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "nodes": {},
            "edges": {},
            "health": {},
        }
        
        # Node counts by label
        labels = ["Protocol", "Token", "Chain", "Audit", "Risk", "Incident", "Developer"]
        
        for label in labels:
            count = await self._graph_repo.count_nodes(label=label)
            stats["nodes"][label] = count
        
        stats["nodes"]["total"] = sum(stats["nodes"].values())
        
        # Edge counts by type
        rel_types = [
            "DEPLOYED_ON",
            "DEPENDS_ON",
            "USES_TOKEN",
            "AUDITED_BY",
            "HAS_RISK",
            "EXPERIENCED_INCIDENT",
            "COMPETES_WITH",
        ]
        
        for rel_type in rel_types:
            count = await self._graph_repo.count_edges(relationship_type=rel_type)
            stats["edges"][rel_type] = count
        
        stats["edges"]["total"] = sum(stats["edges"].values())
        
        # Health metrics
        if stats["nodes"]["total"] > 0:
            stats["health"]["avg_connections_per_node"] = round(
                stats["edges"]["total"] / stats["nodes"]["total"], 2
            )
        else:
            stats["health"]["avg_connections_per_node"] = 0
        
        logger.info(f"Overview stats: {stats['nodes']['total']} nodes, {stats['edges']['total']} edges")
        
        return stats
    
    async def get_top_protocols(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top protocols by TVL.
        
        Args:
            limit: Number of protocols to return
            
        Returns:
            List of top protocols
        """
        
        protocols = await self._graph_repo.find_nodes(
            label="Protocol",
            limit=limit * 2,  # Fetch more to sort
        )
        
        # Sort by TVL
        sorted_protocols = sorted(
            protocols,
            key=lambda p: p.properties.get("tvl", 0),
            reverse=True,
        )[:limit]
        
        result = []
        for protocol in sorted_protocols:
            result.append({
                "name": protocol.properties.get("name", "Unknown"),
                "slug": protocol.properties.get("slug", ""),
                "tvl": protocol.properties.get("tvl", 0),
                "category": protocol.properties.get("category", "Other"),
                "change_24h": protocol.properties.get("change_24h", 0),
            })
        
        return result
    
    async def get_most_connected_protocols(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get protocols with most connections.
        
        Args:
            limit: Number of protocols to return
            
        Returns:
            List of most connected protocols
        """
        
        protocols = await self._graph_repo.find_nodes(
            label="Protocol",
            limit=100,
        )
        
        protocol_degrees = []
        
        for protocol in protocols:
            degree = await self._graph_repo.get_node_degree(
                node_id=protocol.id,
                direction=TraversalDirection.BOTH,
            )
            
            protocol_degrees.append({
                "name": protocol.properties.get("name", "Unknown"),
                "slug": protocol.properties.get("slug", ""),
                "connections": degree,
                "category": protocol.properties.get("category", "Other"),
            })
        
        # Sort by connections
        protocol_degrees.sort(key=lambda x: x["connections"], reverse=True)
        
        return protocol_degrees[:limit]
    
    async def get_category_distribution(self) -> Dict[str, int]:
        """
        Get distribution of protocols by category.
        
        Returns:
            Category counts
        """
        
        protocols = await self._graph_repo.find_nodes(
            label="Protocol",
            limit=1000,
        )
        
        distribution: Dict[str, int] = {}
        
        for protocol in protocols:
            category = protocol.properties.get("category", "Other")
            distribution[category] = distribution.get(category, 0) + 1
        
        # Sort by count
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
    
    async def get_chain_distribution(self) -> Dict[str, int]:
        """
        Get distribution of protocols by chain.
        
        Returns:
            Chain counts
        """
        
        # Count DEPLOYED_ON relationships per chain
        chains = await self._graph_repo.find_nodes(
            label="Chain",
            limit=100,
        )
        
        distribution: Dict[str, int] = {}
        
        for chain in chains:
            # Count protocols deployed on this chain
            protocols = await self._graph_repo.get_neighbors(
                node_id=chain.id,
                relationship_type="DEPLOYED_ON",
                direction=TraversalDirection.INCOMING,
            )
            
            chain_name = chain.properties.get("name", "Unknown")
            distribution[chain_name] = len(protocols)
        
        # Sort by count
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
    
    async def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get summary of risks in the graph.
        
        Returns:
            Risk statistics
        """
        
        risks = await self._graph_repo.find_nodes(
            label="Risk",
            limit=1000,
        )
        
        summary = {
            "total_risks": len(risks),
            "by_severity": {},
            "by_type": {},
            "active_risks": 0,
        }
        
        for risk in risks:
            # By severity
            severity = risk.properties.get("severity", "low")
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # By type
            risk_type = risk.properties.get("type", "other")
            summary["by_type"][risk_type] = summary["by_type"].get(risk_type, 0) + 1
            
            # Active risks
            if risk.properties.get("is_active", True):
                summary["active_risks"] += 1
        
        return summary
    
    async def get_dependency_stats(self) -> Dict[str, Any]:
        """
        Get dependency relationship statistics.
        
        Returns:
            Dependency statistics
        """
        
        protocols = await self._graph_repo.find_nodes(
            label="Protocol",
            limit=100,
        )
        
        stats = {
            "total_dependencies": 0,
            "protocols_with_deps": 0,
            "protocols_as_deps": 0,
            "avg_deps_per_protocol": 0,
        }
        
        total_deps = 0
        has_deps = 0
        is_dep = 0
        
        for protocol in protocols:
            # Count outgoing DEPENDS_ON
            deps = await self._graph_repo.get_neighbors(
                node_id=protocol.id,
                relationship_type="DEPENDS_ON",
                direction=TraversalDirection.OUTGOING,
            )
            
            if len(deps) > 0:
                has_deps += 1
                total_deps += len(deps)
            
            # Count incoming DEPENDS_ON
            dependents = await self._graph_repo.get_neighbors(
                node_id=protocol.id,
                relationship_type="DEPENDS_ON",
                direction=TraversalDirection.INCOMING,
            )
            
            if len(dependents) > 0:
                is_dep += 1
        
        stats["total_dependencies"] = total_deps
        stats["protocols_with_deps"] = has_deps
        stats["protocols_as_deps"] = is_dep
        
        if has_deps > 0:
            stats["avg_deps_per_protocol"] = round(total_deps / has_deps, 2)
        
        return stats
