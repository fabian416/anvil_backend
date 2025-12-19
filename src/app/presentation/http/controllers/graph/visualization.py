"""Graph visualization endpoints for D3.js integration.

Provides endpoints for retrieving graph data in formats suitable for
frontend visualization libraries like D3.js.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field

from app.application.graph.query_service import GraphQueryService
from dishka.integrations.fastapi import FromDishka, inject


class GraphNode(BaseModel):
    """Graph node for visualization."""

    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display label")
    type: str = Field(..., description="Node type (protocol, token, etc.)")
    importance: float = Field(
        0.0, ge=0.0, le=1.0, description="Node importance score (0-1)"
    )
    connections: int = Field(0, ge=0, description="Number of connections")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional node metadata"
    )


class GraphEdge(BaseModel):
    """Graph edge for visualization."""

    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Relationship type")
    weight: float = Field(
        1.0, ge=0.0, le=1.0, description="Edge weight/strength (0-1)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional edge metadata"
    )


class GraphVisualizationResponse(BaseModel):
    """Complete graph visualization data."""

    nodes: List[GraphNode] = Field(..., description="List of graph nodes")
    edges: List[GraphEdge] = Field(..., description="List of graph edges")
    total_nodes: int = Field(..., description="Total number of nodes")
    total_edges: int = Field(..., description="Total number of edges")


class SubgraphResponse(BaseModel):
    """Subgraph focused on specific entity."""

    center_node: GraphNode = Field(..., description="Central node")
    nodes: List[GraphNode] = Field(..., description="Related nodes")
    edges: List[GraphEdge] = Field(..., description="Relationships")
    depth: int = Field(..., description="Traversal depth")


def create_graph_visualization_router() -> APIRouter:
    """Create graph visualization router."""
    router = APIRouter(prefix="/user/graph/visualization", tags=["graph-visualization"])

    @router.get(
        "/nodes",
        response_model=List[GraphNode],
        summary="Get all graph nodes",
        description="Retrieve all nodes in the knowledge graph for visualization",
    )
    @inject
    async def get_graph_nodes(
        query_service: FromDishka[GraphQueryService],
        node_type: Optional[str] = Query(
            None, description="Filter by node type (protocol, token, etc.)"
        ),
        min_importance: float = Query(
            0.0, ge=0.0, le=1.0, description="Minimum importance score"
        ),
        limit: int = Query(100, ge=1, le=1000, description="Maximum nodes to return"),
    ) -> List[GraphNode]:
        """Get all graph nodes for visualization.

        This endpoint returns nodes in a format suitable for D3.js force-directed graphs.

        Args:
            node_type: Filter by node type (optional)
            min_importance: Minimum importance score (0-1)
            limit: Maximum number of nodes to return
            query_service: Graph query service (injected)

        Returns:
            List of graph nodes with visualization metadata
        """
        try:
            # Query nodes from graph database
            # This is a placeholder - actual implementation depends on graph storage
            nodes: List[GraphNode] = []

            # Example nodes (replace with actual query)
            if not node_type or node_type == "protocol":
                nodes.extend(
                    [
                        GraphNode(
                            id="uniswap",
                            label="Uniswap",
                            type="protocol",
                            importance=0.95,
                            connections=150,
                            metadata={
                                "tvl": "3.2B",
                                "volume_24h": "1.1B",
                                "chain": "ethereum",
                            },
                        ),
                        GraphNode(
                            id="aave",
                            label="Aave",
                            type="protocol",
                            importance=0.92,
                            connections=120,
                            metadata={
                                "tvl": "5.8B",
                                "volume_24h": "0.8B",
                                "chain": "ethereum",
                            },
                        ),
                    ]
                )

            if not node_type or node_type == "token":
                nodes.extend(
                    [
                        GraphNode(
                            id="eth",
                            label="ETH",
                            type="token",
                            importance=1.0,
                            connections=300,
                            metadata={
                                "price": "2450",
                                "market_cap": "300B",
                                "symbol": "ETH",
                            },
                        ),
                        GraphNode(
                            id="usdc",
                            label="USDC",
                            type="token",
                            importance=0.98,
                            connections=280,
                            metadata={
                                "price": "1.0",
                                "market_cap": "25B",
                                "symbol": "USDC",
                            },
                        ),
                    ]
                )

            # Filter by importance
            nodes = [n for n in nodes if n.importance >= min_importance]

            # Apply limit
            nodes = nodes[:limit]

            return nodes

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve graph nodes: {str(e)}",
            )

    @router.get(
        "/edges",
        response_model=List[GraphEdge],
        summary="Get all graph edges",
        description="Retrieve all relationships in the knowledge graph",
    )
    @inject
    async def get_graph_edges(
        query_service: FromDishka[GraphQueryService],
        edge_type: Optional[str] = Query(
            None, description="Filter by edge type (PROVIDES_LIQUIDITY, etc.)"
        ),
        min_weight: float = Query(
            0.0, ge=0.0, le=1.0, description="Minimum edge weight"
        ),
        limit: int = Query(500, ge=1, le=5000, description="Maximum edges to return"),
    ) -> List[GraphEdge]:
        """Get all graph edges for visualization.

        This endpoint returns edges (relationships) in a format suitable for D3.js.

        Args:
            edge_type: Filter by relationship type (optional)
            min_weight: Minimum edge weight (0-1)
            limit: Maximum number of edges to return
            query_service: Graph query service (injected)

        Returns:
            List of graph edges with visualization metadata
        """
        try:
            # Query edges from graph database
            edges: List[GraphEdge] = []

            # Example edges (replace with actual query)
            if not edge_type or edge_type == "PROVIDES_LIQUIDITY":
                edges.extend(
                    [
                        GraphEdge(
                            source="uniswap",
                            target="eth",
                            type="PROVIDES_LIQUIDITY",
                            weight=0.9,
                            metadata={"pool_size": "500M"},
                        ),
                        GraphEdge(
                            source="uniswap",
                            target="usdc",
                            type="PROVIDES_LIQUIDITY",
                            weight=0.9,
                            metadata={"pool_size": "400M"},
                        ),
                    ]
                )

            if not edge_type or edge_type == "LENDS_TO":
                edges.extend(
                    [
                        GraphEdge(
                            source="aave",
                            target="eth",
                            type="LENDS_TO",
                            weight=0.85,
                            metadata={"apy": "3.5%"},
                        ),
                        GraphEdge(
                            source="aave",
                            target="usdc",
                            type="LENDS_TO",
                            weight=0.85,
                            metadata={"apy": "5.2%"},
                        ),
                    ]
                )

            # Filter by weight
            edges = [e for e in edges if e.weight >= min_weight]

            # Apply limit
            edges = edges[:limit]

            return edges

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve graph edges: {str(e)}",
            )

    @router.get(
        "/complete",
        response_model=GraphVisualizationResponse,
        summary="Get complete graph",
        description="Retrieve both nodes and edges in a single response",
    )
    @inject
    async def get_complete_graph(
        query_service: FromDishka[GraphQueryService],
        node_type: Optional[str] = Query(None, description="Filter by node type"),
        edge_type: Optional[str] = Query(None, description="Filter by edge type"),
        min_importance: float = Query(
            0.0, ge=0.0, le=1.0, description="Minimum node importance"
        ),
        max_nodes: int = Query(
            100, ge=1, le=1000, description="Maximum nodes to return"
        ),
        max_edges: int = Query(
            500, ge=1, le=5000, description="Maximum edges to return"
        ),
    ) -> GraphVisualizationResponse:
        """Get complete graph data (nodes + edges) for visualization.

        This is a convenience endpoint that combines node and edge queries.

        Args:
            node_type: Filter by node type (optional)
            edge_type: Filter by edge type (optional)
            min_importance: Minimum node importance (0-1)
            max_nodes: Maximum nodes to return
            max_edges: Maximum edges to return
            query_service: Graph query service (injected)

        Returns:
            Complete graph visualization data
        """
        try:
            nodes = await get_graph_nodes(
                node_type=node_type,
                min_importance=min_importance,
                limit=max_nodes,
                query_service=query_service,
            )

            edges = await get_graph_edges(
                edge_type=edge_type, min_weight=0.0, limit=max_edges, query_service=query_service
            )

            return GraphVisualizationResponse(
                nodes=nodes,
                edges=edges,
                total_nodes=len(nodes),
                total_edges=len(edges),
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve complete graph: {str(e)}",
            )

    @router.get(
        "/subgraph",
        response_model=SubgraphResponse,
        summary="Get subgraph around entity",
        description="Retrieve a focused subgraph centered on a specific entity",
    )
    @inject
    async def get_subgraph(
        query_service: FromDishka[GraphQueryService],
        entity: str = Query(..., description="Entity ID to focus on"),
        depth: int = Query(2, ge=1, le=3, description="Traversal depth"),
        max_nodes: int = Query(
            50, ge=1, le=200, description="Maximum nodes to include"
        ),
    ) -> SubgraphResponse:
        """Get subgraph focused on specific entity.

        This endpoint traverses the graph starting from the specified entity
        and returns a localized view of connected nodes and relationships.

        Args:
            entity: Entity ID to center the subgraph on
            depth: How many hops to traverse (1-3)
            max_nodes: Maximum nodes to include in subgraph
            query_service: Graph query service (injected)

        Returns:
            Subgraph centered on the specified entity

        Raises:
            HTTPException: If entity not found or query fails
        """
        try:
            # Query subgraph from graph database
            # This is a placeholder - actual implementation uses graph traversal

            # Example: Uniswap-centered subgraph
            if entity == "uniswap":
                center = GraphNode(
                    id="uniswap",
                    label="Uniswap",
                    type="protocol",
                    importance=0.95,
                    connections=150,
                    metadata={"tvl": "3.2B"},
                )

                nodes = [
                    GraphNode(
                        id="eth", label="ETH", type="token", importance=1.0, connections=300
                    ),
                    GraphNode(
                        id="usdc", label="USDC", type="token", importance=0.98, connections=280
                    ),
                    GraphNode(
                        id="uni", label="UNI", type="token", importance=0.85, connections=80
                    ),
                ]

                edges = [
                    GraphEdge(
                        source="uniswap",
                        target="eth",
                        type="PROVIDES_LIQUIDITY",
                        weight=0.9,
                    ),
                    GraphEdge(
                        source="uniswap",
                        target="usdc",
                        type="PROVIDES_LIQUIDITY",
                        weight=0.9,
                    ),
                    GraphEdge(
                        source="uniswap",
                        target="uni",
                        type="GOVERNANCE_TOKEN",
                        weight=1.0,
                    ),
                ]

                return SubgraphResponse(
                    center_node=center, nodes=nodes, edges=edges, depth=depth
                )

            # Entity not found
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Entity '{entity}' not found in knowledge graph",
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve subgraph: {str(e)}",
            )

    return router
