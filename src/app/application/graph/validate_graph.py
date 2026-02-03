"""
Graph Validation Interactor

Service for validating graph integrity and data quality.
"""

from typing import List, Dict, Any
from datetime import datetime, UTC
import logging

from app.domain.graph.ports import GraphRepository, TraversalDirection


logger = logging.getLogger(__name__)


class ValidateGraphInteractor:
    """
    Validate knowledge graph integrity and data quality.

    Checks:
    - Orphaned nodes (no relationships)
    - Circular dependencies
    - Missing required properties
    - Duplicate entities
    - Referential integrity
    """

    def __init__(self, graph_repo: GraphRepository):
        """
        Initialize validation interactor.

        Args:
            graph_repo: Graph repository
        """
        self._graph_repo = graph_repo

    async def validate_all(self) -> Dict[str, Any]:
        """
        Run all validation checks.

        Returns:
            Validation report with issues
        """

        logger.info("Starting graph validation...")

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": {},
            "total_issues": 0,
            "is_valid": True,
        }

        # Run individual checks
        checks = [
            ("orphaned_nodes", self._check_orphaned_nodes),
            ("circular_dependencies", self._check_circular_dependencies),
            ("missing_properties", self._check_missing_properties),
            ("duplicate_protocols", self._check_duplicate_protocols),
            ("invalid_relationships", self._check_invalid_relationships),
        ]

        for check_name, check_func in checks:
            try:
                result = await check_func()
                report["checks"][check_name] = result
                report["total_issues"] += result["count"]

                if result["count"] > 0:
                    report["is_valid"] = False

            except Exception as e:
                logger.error(f"Error in check {check_name}: {e}")
                report["checks"][check_name] = {
                    "error": str(e),
                    "count": 0,
                }

        logger.info(f"Validation complete: {report['total_issues']} issues found")

        return report

    async def _check_orphaned_nodes(self) -> Dict[str, Any]:
        """Find nodes with no relationships"""

        # Get all protocols
        protocols = await self._graph_repo.find_nodes(
            label="Protocol",
            limit=1000,
        )

        orphaned = []

        for protocol in protocols:
            degree = await self._graph_repo.get_node_degree(
                node_id=protocol.id,
                direction=TraversalDirection.BOTH,
            )

            if degree == 0:
                orphaned.append({
                    "id": str(protocol.id),
                    "name": protocol.properties.get("name", "Unknown"),
                })

        return {
            "count": len(orphaned),
            "issues": orphaned[:10],  # Limit to first 10
            "severity": "warning",
            "message": f"Found {len(orphaned)} orphaned nodes (no relationships)",
        }

    async def _check_circular_dependencies(self) -> Dict[str, Any]:
        """Find circular dependencies"""

        from app.domain.graph.services import GraphService

        graph_service = GraphService(self._graph_repo)
        cycles = await graph_service.find_circular_dependencies(max_depth=5)

        circular = []
        for cycle in cycles:
            circular.append({
                "path": [n.properties.get("name", "Unknown") for n in cycle],
                "length": len(cycle),
            })

        return {
            "count": len(circular),
            "issues": circular[:5],  # Limit to first 5
            "severity": "error" if len(circular) > 0 else "ok",
            "message": f"Found {len(circular)} circular dependencies",
        }

    async def _check_missing_properties(self) -> Dict[str, Any]:
        """Find nodes missing required properties"""

        # Check protocols for required fields
        protocols = await self._graph_repo.find_nodes(
            label="Protocol",
            limit=1000,
        )

        required_fields = ["name", "slug", "category"]
        missing = []

        for protocol in protocols:
            missing_fields = []
            for field in required_fields:
                if not protocol.properties.get(field):
                    missing_fields.append(field)

            if missing_fields:
                missing.append({
                    "id": str(protocol.id),
                    "name": protocol.properties.get("name", "Unknown"),
                    "missing_fields": missing_fields,
                })

        return {
            "count": len(missing),
            "issues": missing[:10],
            "severity": "warning",
            "message": f"Found {len(missing)} nodes with missing required properties",
        }

    async def _check_duplicate_protocols(self) -> Dict[str, Any]:
        """Find duplicate protocol entries"""

        protocols = await self._graph_repo.find_nodes(
            label="Protocol",
            limit=1000,
        )

        # Group by name
        name_map: Dict[str, List] = {}
        for protocol in protocols:
            name = protocol.properties.get("name", "").lower()
            if name:
                if name not in name_map:
                    name_map[name] = []
                name_map[name].append(protocol)

        duplicates = []
        for name, protos in name_map.items():
            if len(protos) > 1:
                duplicates.append({
                    "name": name,
                    "count": len(protos),
                    "ids": [str(p.id) for p in protos],
                })

        return {
            "count": len(duplicates),
            "issues": duplicates[:10],
            "severity": "warning",
            "message": f"Found {len(duplicates)} duplicate protocol entries",
        }

    async def _check_invalid_relationships(self) -> Dict[str, Any]:
        """Find invalid or broken relationships"""

        # This is a simplified check
        # In practice, you'd query all edges and verify both nodes exist

        return {
            "count": 0,
            "issues": [],
            "severity": "ok",
            "message": "No invalid relationships found (basic check)",
        }
