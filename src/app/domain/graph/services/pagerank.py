"""PageRank algorithm for protocol importance ranking.

Implements the PageRank algorithm to calculate the importance of protocols
in the DeFi ecosystem based on their connections and relationships.
"""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class PageRankConfig:
    """Configuration for PageRank computation."""

    damping_factor: float = 0.85
    max_iterations: int = 20
    convergence_threshold: float = 0.0001
    min_importance: float = 0.0


@dataclass
class PageRankResult:
    """Result of PageRank computation."""

    node_id: str
    pagerank: float
    rank: int
    connections: int


class PageRankService:
    """Service for computing PageRank of graph nodes."""

    def __init__(self, config: PageRankConfig = None):
        """Initialize PageRank service.

        Args:
            config: PageRank configuration (uses defaults if None)
        """
        self.config = config or PageRankConfig()

    def compute_pagerank(
        self,
        nodes: Set[str],
        edges: List[Tuple[str, str]],
    ) -> Dict[str, float]:
        """Compute PageRank for all nodes in the graph.

        Args:
            nodes: Set of all node IDs
            edges: List of directed edges (source, target)

        Returns:
            Dictionary mapping node ID to PageRank score

        Algorithm:
            PR(A) = (1-d)/N + d * sum(PR(Ti)/C(Ti))
            where:
            - d = damping factor (0.85)
            - N = total number of nodes
            - Ti = nodes that link to A
            - C(Ti) = number of outbound links from Ti

        Example:
            >>> service = PageRankService()
            >>> nodes = {"uniswap", "eth", "usdc", "aave"}
            >>> edges = [
            ...     ("uniswap", "eth"),
            ...     ("uniswap", "usdc"),
            ...     ("aave", "eth"),
            ...     ("aave", "usdc"),
            ... ]
            >>> scores = service.compute_pagerank(nodes, edges)
            >>> # scores = {
            >>> #   "uniswap": 0.0234,
            >>> #   "eth": 0.0312,
            >>> #   "usdc": 0.0312,
            >>> #   "aave": 0.0234
            >>> # }
        """
        if not nodes:
            return {}

        # Initialize PageRank scores (equal distribution)
        num_nodes = len(nodes)
        pagerank: Dict[str, float] = {node: 1.0 / num_nodes for node in nodes}

        # Build adjacency structures
        outbound: Dict[str, List[str]] = {node: [] for node in nodes}
        inbound: Dict[str, List[str]] = {node: [] for node in nodes}

        for source, target in edges:
            if source in nodes and target in nodes:
                outbound[source].append(target)
                inbound[target].append(source)

        # Iterative computation
        d = self.config.damping_factor
        for iteration in range(self.config.max_iterations):
            new_pagerank: Dict[str, float] = {}
            max_diff = 0.0

            for node in nodes:
                # Random jump probability
                rank = (1 - d) / num_nodes

                # Sum contributions from inbound links
                for source in inbound[node]:
                    out_count = len(outbound[source])
                    if out_count > 0:
                        rank += d * (pagerank[source] / out_count)

                new_pagerank[node] = rank

                # Track convergence
                diff = abs(new_pagerank[node] - pagerank[node])
                max_diff = max(max_diff, diff)

            pagerank = new_pagerank

            # Check convergence
            if max_diff < self.config.convergence_threshold:
                break

        return pagerank

    def rank_nodes(
        self,
        pagerank_scores: Dict[str, float],
        connections: Dict[str, int] = None,
    ) -> List[PageRankResult]:
        """Rank nodes by PageRank score.

        Args:
            pagerank_scores: Dictionary of node ID to PageRank score
            connections: Optional dictionary of node ID to connection count

        Returns:
            Sorted list of PageRank results

        Example:
            >>> service = PageRankService()
            >>> scores = {"eth": 0.0312, "uniswap": 0.0234, "aave": 0.0234}
            >>> connections = {"eth": 300, "uniswap": 150, "aave": 120}
            >>> results = service.rank_nodes(scores, connections)
            >>> # results[0].node_id == "eth" (highest PageRank)
            >>> # results[0].rank == 1
        """
        if not pagerank_scores:
            return []

        # Sort by PageRank descending
        sorted_items = sorted(
            pagerank_scores.items(), key=lambda x: x[1], reverse=True
        )

        results: List[PageRankResult] = []
        for rank, (node_id, score) in enumerate(sorted_items, start=1):
            conn_count = connections.get(node_id, 0) if connections else 0
            results.append(
                PageRankResult(
                    node_id=node_id,
                    pagerank=score,
                    rank=rank,
                    connections=conn_count,
                )
            )

        return results

    def compute_protocol_importance(
        self,
        protocols: Dict[str, List[str]],
    ) -> List[PageRankResult]:
        """Compute importance ranking for DeFi protocols.

        Args:
            protocols: Dictionary mapping protocol ID to list of connected protocol IDs

        Returns:
            Ranked list of protocols by importance

        Example:
            >>> service = PageRankService()
            >>> protocols = {
            ...     "uniswap": ["aave", "compound", "curve"],
            ...     "aave": ["uniswap", "compound"],
            ...     "compound": ["uniswap", "aave"],
            ...     "curve": ["uniswap"],
            ... }
            >>> ranking = service.compute_protocol_importance(protocols)
            >>> # ranking[0].node_id == "uniswap" (most important)
        """
        # Extract nodes and edges
        nodes = set(protocols.keys())
        edges: List[Tuple[str, str]] = []

        for source, targets in protocols.items():
            for target in targets:
                edges.append((source, target))

        # Compute PageRank
        pagerank_scores = self.compute_pagerank(nodes, edges)

        # Count connections
        connections = {node: len(targets) for node, targets in protocols.items()}

        # Rank protocols
        results = self.rank_nodes(pagerank_scores, connections)

        return results

    def identify_hub_protocols(
        self,
        pagerank_results: List[PageRankResult],
        top_n: int = 10,
    ) -> List[PageRankResult]:
        """Identify hub protocols (most important/connected).

        Args:
            pagerank_results: List of PageRank results
            top_n: Number of top protocols to return

        Returns:
            Top N hub protocols by importance

        Example:
            >>> service = PageRankService()
            >>> results = [...]  # from compute_protocol_importance
            >>> hubs = service.identify_hub_protocols(results, top_n=5)
            >>> # hubs = [Uniswap, Aave, Curve, Compound, MakerDAO]
        """
        return pagerank_results[:top_n]

    def compute_centrality_risk(
        self,
        pagerank_results: List[PageRankResult],
        threshold: float = 0.05,
    ) -> List[PageRankResult]:
        """Identify protocols with high centrality risk.

        Protocols with high PageRank represent systemic risk points -
        their failure could cascade through the ecosystem.

        Args:
            pagerank_results: List of PageRank results
            threshold: Minimum PageRank score for risk consideration

        Returns:
            Protocols with high centrality risk

        Example:
            >>> service = PageRankService()
            >>> results = [...]
            >>> risky = service.compute_centrality_risk(results, threshold=0.05)
            >>> # risky = protocols with PageRank > 0.05
            >>> # These are critical infrastructure that need monitoring
        """
        risky_protocols = [r for r in pagerank_results if r.pagerank >= threshold]
        return risky_protocols


def compute_node_importance(
    nodes: Set[str],
    edges: List[Tuple[str, str]],
    damping: float = 0.85,
    max_iterations: int = 20,
) -> Dict[str, float]:
    """Convenience function to compute PageRank.

    Args:
        nodes: Set of node IDs
        edges: List of directed edges
        damping: Damping factor (default: 0.85)
        max_iterations: Maximum iterations (default: 20)

    Returns:
        Dictionary mapping node ID to PageRank score

    Example:
        >>> scores = compute_node_importance(
        ...     nodes={"A", "B", "C"},
        ...     edges=[("A", "B"), ("B", "C"), ("C", "A")]
        ... )
    """
    config = PageRankConfig(
        damping_factor=damping,
        max_iterations=max_iterations,
    )
    service = PageRankService(config)
    return service.compute_pagerank(nodes, edges)
