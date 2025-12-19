"""
Graph Repository Port

This port defines the interface for graph database operations,
abstracting away the specific graph database implementation (Apache AGE, Neo4j, etc.).

Following the Hexagonal Architecture pattern, this interface is defined in the domain layer,
while implementations live in the infrastructure layer.
"""

from typing import Protocol, List, Dict, Any, Optional, Union
from uuid import UUID
from dataclasses import dataclass
from enum import Enum


class TraversalDirection(Enum):
    """Direction for graph traversal"""
    OUTGOING = "outgoing"  # Follow edges from source to target
    INCOMING = "incoming"  # Follow edges from target to source
    BOTH = "both"          # Follow edges in both directions


@dataclass
class GraphNode:
    """Represents a node in the graph"""
    id: UUID
    label: str  # Entity type (e.g., "Protocol", "Token")
    properties: Dict[str, Any]


@dataclass
class GraphEdge:
    """Represents an edge (relationship) in the graph"""
    id: UUID
    from_id: UUID
    to_id: UUID
    relationship_type: str  # e.g., "DEPENDS_ON", "USES_TOKEN"
    properties: Optional[Dict[str, Any]] = None


@dataclass
class GraphPath:
    """Represents a path through the graph"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    length: int  # Number of hops
    
    def __post_init__(self):
        if self.length == 0:
            self.length = len(self.edges)


class GraphRepository(Protocol):
    """
    Port for graph database operations.
    
    This interface defines all graph operations needed by the domain layer.
    Infrastructure layer provides concrete implementations (e.g., for Apache AGE).
    """
    
    # =========================================================================
    # Node Operations
    # =========================================================================
    
    async def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
    ) -> UUID:
        """
        Create a new node in the graph.
        
        Args:
            label: Node label (entity type), e.g., "Protocol", "Token"
            properties: Dictionary of properties for the node
            
        Returns:
            UUID of the created node
            
        Raises:
            ValueError: If label or properties are invalid
            DatabaseError: If creation fails
            
        Example:
            >>> node_id = await graph_repo.create_node(
            ...     label="Protocol",
            ...     properties={"name": "Aave", "tvl": 5000000000.0}
            ... )
        """
        ...
    
    async def get_node(
        self,
        node_id: UUID,
    ) -> Optional[GraphNode]:
        """
        Get a node by its ID.
        
        Args:
            node_id: UUID of the node
            
        Returns:
            GraphNode if found, None otherwise
            
        Example:
            >>> node = await graph_repo.get_node(node_id)
            >>> if node:
            ...     print(f"Found {node.label}: {node.properties['name']}")
        """
        ...
    
    async def find_nodes(
        self,
        label: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[GraphNode]:
        """
        Find nodes by label and optional property filters.
        
        Args:
            label: Node label to search for
            filters: Dictionary of property filters (exact match)
            limit: Maximum number of nodes to return
            offset: Number of nodes to skip (for pagination)
            
        Returns:
            List of matching GraphNode objects
            
        Example:
            >>> # Find all lending protocols
            >>> protocols = await graph_repo.find_nodes(
            ...     label="Protocol",
            ...     filters={"category": "lending"},
            ...     limit=10
            ... )
        """
        ...
    
    async def update_node(
        self,
        node_id: UUID,
        properties: Dict[str, Any],
        merge: bool = True,
    ) -> bool:
        """
        Update a node's properties.
        
        Args:
            node_id: UUID of the node to update
            properties: Properties to update
            merge: If True, merge with existing properties. If False, replace all properties.
            
        Returns:
            True if update successful, False if node not found
            
        Example:
            >>> await graph_repo.update_node(
            ...     node_id=protocol_id,
            ...     properties={"tvl": 6000000000.0},
            ...     merge=True
            ... )
        """
        ...
    
    async def delete_node(
        self,
        node_id: UUID,
        delete_edges: bool = True,
    ) -> bool:
        """
        Delete a node from the graph.
        
        Args:
            node_id: UUID of the node to delete
            delete_edges: If True, also delete all edges connected to this node
            
        Returns:
            True if deletion successful, False if node not found
            
        Raises:
            DatabaseError: If node has edges and delete_edges=False
            
        Example:
            >>> await graph_repo.delete_node(node_id, delete_edges=True)
        """
        ...
    
    # =========================================================================
    # Edge Operations
    # =========================================================================
    
    async def create_edge(
        self,
        from_id: UUID,
        to_id: UUID,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Create an edge (relationship) between two nodes.
        
        Args:
            from_id: UUID of the source node
            to_id: UUID of the target node
            relationship_type: Type of relationship, e.g., "DEPENDS_ON"
            properties: Optional properties for the edge
            
        Returns:
            UUID of the created edge
            
        Raises:
            ValueError: If either node doesn't exist
            DatabaseError: If creation fails
            
        Example:
            >>> edge_id = await graph_repo.create_edge(
            ...     from_id=aave_id,
            ...     to_id=chainlink_id,
            ...     relationship_type="DEPENDS_ON",
            ...     properties={"dependency_type": "oracle", "criticality": "high"}
            ... )
        """
        ...
    
    async def get_edge(
        self,
        edge_id: UUID,
    ) -> Optional[GraphEdge]:
        """
        Get an edge by its ID.
        
        Args:
            edge_id: UUID of the edge
            
        Returns:
            GraphEdge if found, None otherwise
        """
        ...
    
    async def find_edges(
        self,
        from_id: Optional[UUID] = None,
        to_id: Optional[UUID] = None,
        relationship_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[GraphEdge]:
        """
        Find edges by various criteria.
        
        Args:
            from_id: Filter by source node (optional)
            to_id: Filter by target node (optional)
            relationship_type: Filter by relationship type (optional)
            filters: Additional property filters (optional)
            limit: Maximum number of edges to return
            
        Returns:
            List of matching GraphEdge objects
            
        Example:
            >>> # Find all dependencies of Aave
            >>> edges = await graph_repo.find_edges(
            ...     from_id=aave_id,
            ...     relationship_type="DEPENDS_ON"
            ... )
        """
        ...
    
    async def delete_edge(
        self,
        edge_id: UUID,
    ) -> bool:
        """
        Delete an edge from the graph.
        
        Args:
            edge_id: UUID of the edge to delete
            
        Returns:
            True if deletion successful, False if edge not found
        """
        ...
    
    # =========================================================================
    # Traversal Operations
    # =========================================================================
    
    async def traverse(
        self,
        start_node_id: UUID,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 3,
        direction: TraversalDirection = TraversalDirection.OUTGOING,
        node_label_filter: Optional[str] = None,
    ) -> List[GraphPath]:
        """
        Traverse the graph from a starting node.
        
        Args:
            start_node_id: UUID of the starting node
            relationship_types: Filter by relationship types (None = all types)
            max_depth: Maximum depth to traverse (number of hops)
            direction: Direction of traversal
            node_label_filter: Only include nodes with this label (optional)
            
        Returns:
            List of GraphPath objects representing paths found
            
        Example:
            >>> # Find all protocols that Aave depends on (up to 3 hops)
            >>> paths = await graph_repo.traverse(
            ...     start_node_id=aave_id,
            ...     relationship_types=["DEPENDS_ON"],
            ...     max_depth=3,
            ...     direction=TraversalDirection.OUTGOING
            ... )
        """
        ...
    
    async def shortest_path(
        self,
        from_id: UUID,
        to_id: UUID,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 10,
    ) -> Optional[GraphPath]:
        """
        Find the shortest path between two nodes.
        
        Args:
            from_id: UUID of the start node
            to_id: UUID of the end node
            relationship_types: Only traverse these relationship types (None = all)
            max_depth: Maximum path length to consider
            
        Returns:
            GraphPath if path found, None otherwise
            
        Example:
            >>> # Find shortest dependency chain from Aave to USDC
            >>> path = await graph_repo.shortest_path(
            ...     from_id=aave_id,
            ...     to_id=usdc_id,
            ...     relationship_types=["DEPENDS_ON", "USES_TOKEN"]
            ... )
        """
        ...
    
    async def get_neighbors(
        self,
        node_id: UUID,
        relationship_type: Optional[str] = None,
        direction: TraversalDirection = TraversalDirection.OUTGOING,
    ) -> List[GraphNode]:
        """
        Get immediate neighbors of a node (1-hop traversal).
        
        Args:
            node_id: UUID of the node
            relationship_type: Filter by relationship type (optional)
            direction: Direction of relationships to follow
            
        Returns:
            List of neighboring GraphNode objects
            
        Example:
            >>> # Get all protocols that depend on Chainlink
            >>> dependents = await graph_repo.get_neighbors(
            ...     node_id=chainlink_id,
            ...     relationship_type="DEPENDS_ON",
            ...     direction=TraversalDirection.INCOMING
            ... )
        """
        ...
    
    # =========================================================================
    # Aggregation & Analytics
    # =========================================================================
    
    async def count_nodes(
        self,
        label: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count nodes matching criteria.
        
        Args:
            label: Filter by node label (optional)
            filters: Property filters (optional)
            
        Returns:
            Number of matching nodes
            
        Example:
            >>> # Count all protocols
            >>> protocol_count = await graph_repo.count_nodes(label="Protocol")
        """
        ...
    
    async def count_edges(
        self,
        relationship_type: Optional[str] = None,
    ) -> int:
        """
        Count edges matching criteria.
        
        Args:
            relationship_type: Filter by relationship type (optional)
            
        Returns:
            Number of matching edges
        """
        ...
    
    async def get_node_degree(
        self,
        node_id: UUID,
        direction: TraversalDirection = TraversalDirection.BOTH,
    ) -> int:
        """
        Get the degree (number of connections) of a node.
        
        Args:
            node_id: UUID of the node
            direction: Count outgoing, incoming, or both
            
        Returns:
            Number of edges connected to the node
            
        Example:
            >>> # How many protocols depend on Chainlink?
            >>> degree = await graph_repo.get_node_degree(
            ...     node_id=chainlink_id,
            ...     direction=TraversalDirection.INCOMING
            ... )
        """
        ...
    
    # =========================================================================
    # Batch Operations
    # =========================================================================
    
    async def create_nodes_batch(
        self,
        nodes: List[tuple[str, Dict[str, Any]]],  # [(label, properties), ...]
    ) -> List[UUID]:
        """
        Create multiple nodes in a single transaction.
        
        Args:
            nodes: List of (label, properties) tuples
            
        Returns:
            List of UUIDs for created nodes (in same order)
            
        Example:
            >>> node_ids = await graph_repo.create_nodes_batch([
            ...     ("Protocol", {"name": "Aave", "tvl": 5000000000.0}),
            ...     ("Protocol", {"name": "Compound", "tvl": 3000000000.0}),
            ... ])
        """
        ...
    
    async def create_edges_batch(
        self,
        edges: List[tuple[UUID, UUID, str, Optional[Dict[str, Any]]]],
    ) -> List[UUID]:
        """
        Create multiple edges in a single transaction.
        
        Args:
            edges: List of (from_id, to_id, relationship_type, properties) tuples
            
        Returns:
            List of UUIDs for created edges (in same order)
            
        Example:
            >>> edge_ids = await graph_repo.create_edges_batch([
            ...     (aave_id, chainlink_id, "DEPENDS_ON", {"type": "oracle"}),
            ...     (aave_id, usdc_id, "USES_TOKEN", {"role": "collateral"}),
            ... ])
        """
        ...
    
    # =========================================================================
    # Cypher Query (Advanced)
    # =========================================================================
    
    async def execute_cypher(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a raw Cypher query (for advanced use cases).
        
        Args:
            query: Cypher query string
            parameters: Query parameters (for parameterized queries)
            
        Returns:
            List of result records as dictionaries
            
        Warning:
            Use with caution. Prefer using the type-safe methods above.
            This is provided for complex queries not covered by the standard API.
            
        Example:
            >>> results = await graph_repo.execute_cypher(
            ...     query=\"""
            ...         MATCH (p:Protocol)-[d:DEPENDS_ON]->(dep:Protocol)
            ...         WHERE d.criticality = $criticality
            ...         RETURN p.name, dep.name, d.dependency_type
            ...     \""",
            ...     parameters={"criticality": "high"}
            ... )
        """
        ...
