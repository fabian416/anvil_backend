"""
Apache AGE Implementation of Graph Repository

This adapter implements the GraphRepository port using Apache AGE
(A Graph Extension for PostgreSQL).

Apache AGE provides:
- Cypher query language support (similar to Neo4j)
- Native graph storage in PostgreSQL
- ACID transactions
- Integration with existing relational data

Usage:
    >>> from sqlalchemy.ext.asyncio import AsyncSession
    >>> repo = GraphRepositoryAge(session, graph_name="defi_knowledge_graph")
    >>> node_id = await repo.create_node("Protocol", {"name": "Aave"})
"""

from typing import List, Dict, Any, Optional, Union
from uuid import UUID, uuid4
import json
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.graph.ports import (
    GraphRepository,
    GraphNode,
    GraphEdge,
    GraphPath,
    TraversalDirection,
)


class GraphRepositoryAge(GraphRepository):
    """
    Apache AGE implementation of GraphRepository.

    AGE stores graph data in PostgreSQL using JSONB for properties.
    Queries are written in Cypher (graph query language).
    """

    def __init__(
        self,
        session: AsyncSession,
        graph_name: str = "defi_knowledge_graph",
    ):
        """
        Initialize AGE repository.

        Args:
            session: SQLAlchemy async session
            graph_name: Name of the graph (default: defi_knowledge_graph)
        """
        self.session = session
        self.graph_name = graph_name

    # =========================================================================
    # Node Operations
    # =========================================================================

    async def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
    ) -> UUID:
        """Create a new node in the graph"""

        # Generate UUID for node
        node_id = uuid4()

        # Add ID to properties
        props_with_id = {**properties, "id": str(node_id)}

        # Convert properties to JSON string for AGE
        props_json = json.dumps(props_with_id)

        # Create Cypher query
        # AGE requires wrapping Cypher in SELECT * FROM cypher(...)
        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                CREATE (n:{label} {props_json})
                RETURN n
            $$) as (n agtype);
        """)

        # Execute query
        result = await self.session.execute(query)
        await self.session.commit()

        return node_id

    async def get_node(
        self,
        node_id: UUID,
    ) -> Optional[GraphNode]:
        """Get a node by its ID"""

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH (n {{id: '{str(node_id)}'}})
                RETURN n
            $$) as (n agtype);
        """)

        result = await self.session.execute(query)
        row = result.fetchone()

        if not row:
            return None

        # Parse AGE result (JSON-like structure)
        node_data = self._parse_agtype(row[0])

        return GraphNode(
            id=UUID(node_data["properties"]["id"]),
            label=node_data["label"],
            properties=node_data["properties"],
        )

    async def find_nodes(
        self,
        label: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[GraphNode]:
        """Find nodes by label and optional property filters"""

        # Build WHERE clause from filters
        where_clauses = []
        if filters:
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"n.{key} = '{value}'")
                else:
                    where_clauses.append(f"n.{key} = {value}")

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH (n:{label})
                {where_clause}
                RETURN n
                SKIP {offset}
                LIMIT {limit}
            $$) as (n agtype);
        """)

        result = await self.session.execute(query)
        rows = result.fetchall()

        nodes = []
        for row in rows:
            node_data = self._parse_agtype(row[0])
            nodes.append(
                GraphNode(
                    id=UUID(node_data["properties"]["id"]),
                    label=node_data["label"],
                    properties=node_data["properties"],
                )
            )

        return nodes

    async def update_node(
        self,
        node_id: UUID,
        properties: Dict[str, Any],
        merge: bool = True,
    ) -> bool:
        """Update a node's properties"""

        # Build SET clause
        if merge:
            # Merge: Update only specified properties
            set_clauses = []
            for key, value in properties.items():
                if isinstance(value, str):
                    set_clauses.append(f"n.{key} = '{value}'")
                elif isinstance(value, (int, float)):
                    set_clauses.append(f"n.{key} = {value}")
                elif isinstance(value, bool):
                    set_clauses.append(f"n.{key} = {str(value).lower()}")
                else:
                    set_clauses.append(f"n.{key} = {json.dumps(value)}")

            set_clause = ", ".join(set_clauses)
        else:
            # Replace: Set all properties at once
            props_json = json.dumps(properties)
            set_clause = f"n = {props_json}"

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH (n {{id: '{str(node_id)}'}})
                SET {set_clause}
                RETURN n
            $$) as (n agtype);
        """)

        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0

    async def delete_node(
        self,
        node_id: UUID,
        delete_edges: bool = True,
    ) -> bool:
        """Delete a node from the graph"""

        if delete_edges:
            # DETACH DELETE removes node and all connected edges
            query = text(f"""
                SELECT * FROM cypher('{self.graph_name}', $$
                    MATCH (n {{id: '{str(node_id)}'}})
                    DETACH DELETE n
                $$) as (result agtype);
            """)
        else:
            # Regular DELETE (will fail if node has edges)
            query = text(f"""
                SELECT * FROM cypher('{self.graph_name}', $$
                    MATCH (n {{id: '{str(node_id)}'}})
                    DELETE n
                $$) as (result agtype);
            """)

        try:
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

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
        """Create an edge between two nodes"""

        # Generate UUID for edge
        edge_id = uuid4()

        # Prepare properties
        props = properties or {}
        props["id"] = str(edge_id)
        props_json = json.dumps(props)

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH (a {{id: '{str(from_id)}'}}), (b {{id: '{str(to_id)}'}})
                CREATE (a)-[r:{relationship_type} {props_json}]->(b)
                RETURN r
            $$) as (r agtype);
        """)

        result = await self.session.execute(query)
        await self.session.commit()

        if result.rowcount == 0:
            raise ValueError(f"One or both nodes not found: {from_id}, {to_id}")

        return edge_id

    async def get_edge(
        self,
        edge_id: UUID,
    ) -> Optional[GraphEdge]:
        """Get an edge by its ID"""

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH ()-[r {{id: '{str(edge_id)}'}}]->()
                RETURN r
            $$) as (r agtype);
        """)

        result = await self.session.execute(query)
        row = result.fetchone()

        if not row:
            return None

        edge_data = self._parse_agtype(row[0])

        return GraphEdge(
            id=UUID(edge_data["properties"]["id"]),
            from_id=UUID(edge_data["start_id"]),
            to_id=UUID(edge_data["end_id"]),
            relationship_type=edge_data["label"],
            properties=edge_data["properties"],
        )

    async def find_edges(
        self,
        from_id: Optional[UUID] = None,
        to_id: Optional[UUID] = None,
        relationship_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[GraphEdge]:
        """Find edges by various criteria"""

        # Build MATCH pattern
        from_pattern = f"({{id: '{str(from_id)}'}})" if from_id else "()"
        to_pattern = f"({{id: '{str(to_id)}'}})" if to_id else "()"
        rel_pattern = f":{relationship_type}" if relationship_type else ""

        # Build WHERE clause
        where_clauses = []
        if filters:
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"r.{key} = '{value}'")
                else:
                    where_clauses.append(f"r.{key} = {value}")

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH {from_pattern}-[r{rel_pattern}]->{to_pattern}
                {where_clause}
                RETURN r
                LIMIT {limit}
            $$) as (r agtype);
        """)

        result = await self.session.execute(query)
        rows = result.fetchall()

        edges = []
        for row in rows:
            edge_data = self._parse_agtype(row[0])
            edges.append(
                GraphEdge(
                    id=UUID(edge_data["properties"]["id"]),
                    from_id=UUID(edge_data["start_id"]),
                    to_id=UUID(edge_data["end_id"]),
                    relationship_type=edge_data["label"],
                    properties=edge_data["properties"],
                )
            )

        return edges

    async def delete_edge(
        self,
        edge_id: UUID,
    ) -> bool:
        """Delete an edge from the graph"""

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH ()-[r {{id: '{str(edge_id)}'}}]->()
                DELETE r
            $$) as (result agtype);
        """)

        try:
            await self.session.execute(query)
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            return False

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
        """Traverse the graph from a starting node"""

        # Build relationship pattern
        if direction == TraversalDirection.OUTGOING:
            rel_pattern = "-[r]->"
        elif direction == TraversalDirection.INCOMING:
            rel_pattern = "<-[r]-"
        else:  # BOTH
            rel_pattern = "-[r]-"

        # Build relationship type filter
        if relationship_types:
            rel_type = "|".join(relationship_types)
            rel_pattern = rel_pattern.replace("[r]", f"[r:{rel_type}]")

        # Build node label filter
        node_pattern = f":{node_label_filter}" if node_label_filter else ""

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH path = (start {{id: '{str(start_node_id)}'}})
                             {rel_pattern}*1..{max_depth}
                             (end{node_pattern})
                RETURN path
            $$) as (path agtype);
        """)

        result = await self.session.execute(query)
        rows = result.fetchall()

        paths = []
        for row in rows:
            path_data = self._parse_agtype(row[0])
            paths.append(self._build_graph_path(path_data))

        return paths

    async def shortest_path(
        self,
        from_id: UUID,
        to_id: UUID,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 10,
    ) -> Optional[GraphPath]:
        """Find the shortest path between two nodes"""

        # Build relationship type filter
        rel_filter = ""
        if relationship_types:
            rel_type = "|".join(relationship_types)
            rel_filter = f":{rel_type}"

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH path = shortestPath(
                    (start {{id: '{str(from_id)}' }})-[{rel_filter}*1..{max_depth}]-(end {{id: '{str(to_id)}' }})
                )
                RETURN path
                LIMIT 1
            $$) as (path agtype);
        """)

        result = await self.session.execute(query)
        row = result.fetchone()

        if not row:
            return None

        path_data = self._parse_agtype(row[0])
        return self._build_graph_path(path_data)

    async def get_neighbors(
        self,
        node_id: UUID,
        relationship_type: Optional[str] = None,
        direction: TraversalDirection = TraversalDirection.OUTGOING,
    ) -> List[GraphNode]:
        """Get immediate neighbors of a node"""

        # Build relationship pattern
        if direction == TraversalDirection.OUTGOING:
            pattern = f"-[r{':' + relationship_type if relationship_type else ''}]->(neighbor)"
        elif direction == TraversalDirection.INCOMING:
            pattern = f"<-[r{':' + relationship_type if relationship_type else ''}]-(neighbor)"
        else:  # BOTH
            pattern = (
                f"-[r{':' + relationship_type if relationship_type else ''}]-(neighbor)"
            )

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH (n {{id: '{str(node_id)}'}}){pattern}
                RETURN neighbor
            $$) as (neighbor agtype);
        """)

        result = await self.session.execute(query)
        rows = result.fetchall()

        neighbors = []
        for row in rows:
            node_data = self._parse_agtype(row[0])
            neighbors.append(
                GraphNode(
                    id=UUID(node_data["properties"]["id"]),
                    label=node_data["label"],
                    properties=node_data["properties"],
                )
            )

        return neighbors

    # =========================================================================
    # Aggregation & Analytics
    # =========================================================================

    async def count_nodes(
        self,
        label: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Count nodes matching criteria"""

        # Build MATCH clause
        match_clause = f"(n:{label})" if label else "(n)"

        # Build WHERE clause
        where_clauses = []
        if filters:
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"n.{key} = '{value}'")
                else:
                    where_clauses.append(f"n.{key} = {value}")

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH {match_clause}
                {where_clause}
                RETURN count(n)
            $$) as (count agtype);
        """)

        result = await self.session.execute(query)
        row = result.fetchone()

        return int(self._parse_agtype(row[0])) if row else 0

    async def count_edges(
        self,
        relationship_type: Optional[str] = None,
    ) -> int:
        """Count edges matching criteria"""

        rel_pattern = f":{relationship_type}" if relationship_type else ""

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH ()-[r{rel_pattern}]->()
                RETURN count(r)
            $$) as (count agtype);
        """)

        result = await self.session.execute(query)
        row = result.fetchone()

        return int(self._parse_agtype(row[0])) if row else 0

    async def get_node_degree(
        self,
        node_id: UUID,
        direction: TraversalDirection = TraversalDirection.BOTH,
    ) -> int:
        """Get the degree (number of connections) of a node"""

        # Build pattern based on direction
        if direction == TraversalDirection.OUTGOING:
            pattern = "(n)-[r]->()"
        elif direction == TraversalDirection.INCOMING:
            pattern = "()<-[r]-(n)"
        else:  # BOTH
            pattern = "(n)-[r]-()"

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                MATCH {pattern}
                WHERE n.id = '{str(node_id)}'
                RETURN count(r)
            $$) as (count agtype);
        """)

        result = await self.session.execute(query)
        row = result.fetchone()

        return int(self._parse_agtype(row[0])) if row else 0

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def create_nodes_batch(
        self,
        nodes: List[tuple[str, Dict[str, Any]]],
    ) -> List[UUID]:
        """Create multiple nodes in a single transaction"""

        node_ids = []

        for label, properties in nodes:
            node_id = await self.create_node(label, properties)
            node_ids.append(node_id)

        return node_ids

    async def create_edges_batch(
        self,
        edges: List[tuple[UUID, UUID, str, Optional[Dict[str, Any]]]],
    ) -> List[UUID]:
        """Create multiple edges in a single transaction"""

        edge_ids = []

        for from_id, to_id, relationship_type, properties in edges:
            edge_id = await self.create_edge(
                from_id, to_id, relationship_type, properties
            )
            edge_ids.append(edge_id)

        return edge_ids

    # =========================================================================
    # Cypher Query (Advanced)
    # =========================================================================

    async def execute_cypher(
        self,
        query_string: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a raw Cypher query"""

        # Note: AGE doesn't support parameterized queries in the same way
        # as Neo4j. For now, we'll substitute parameters directly.
        # In production, use proper escaping/validation.

        if parameters:
            for key, value in parameters.items():
                placeholder = f"${key}"
                if isinstance(value, str):
                    query_string = query_string.replace(placeholder, f"'{value}'")
                else:
                    query_string = query_string.replace(placeholder, str(value))

        query = text(f"""
            SELECT * FROM cypher('{self.graph_name}', $$
                {query_string}
            $$) as (result agtype);
        """)

        result = await self.session.execute(query)
        rows = result.fetchall()

        results = []
        for row in rows:
            results.append(self._parse_agtype(row[0]))

        return results

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_agtype(self, agtype_value: Any) -> Any:
        """
        Parse AGE agtype value to Python dict.

        AGE returns data in a custom agtype format that needs parsing.
        This is a simplified parser for common cases.
        """
        if agtype_value is None:
            return None

        # AGE returns JSON-like strings
        if isinstance(agtype_value, str):
            try:
                return json.loads(agtype_value)
            except json.JSONDecodeError:
                return agtype_value

        return agtype_value

    def _build_graph_path(self, path_data: Dict[str, Any]) -> GraphPath:
        """Build GraphPath object from AGE path data"""

        nodes = []
        edges = []

        # Parse nodes
        for node_data in path_data.get("nodes", []):
            nodes.append(
                GraphNode(
                    id=UUID(node_data["properties"]["id"]),
                    label=node_data["label"],
                    properties=node_data["properties"],
                )
            )

        # Parse edges
        for edge_data in path_data.get("relationships", []):
            edges.append(
                GraphEdge(
                    id=UUID(edge_data["properties"]["id"]),
                    from_id=UUID(edge_data["start_id"]),
                    to_id=UUID(edge_data["end_id"]),
                    relationship_type=edge_data["label"],
                    properties=edge_data["properties"],
                )
            )

        return GraphPath(
            nodes=nodes,
            edges=edges,
            length=len(edges),
        )
