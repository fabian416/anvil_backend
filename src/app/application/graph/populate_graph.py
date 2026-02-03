"""
Populate Graph Interactor

Service for populating the knowledge graph with DeFi data.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, UTC
import logging

from app.domain.graph.ports import GraphRepository
from app.domain.ports.external_data import DefiDataProvider, ProtocolData


logger = logging.getLogger(__name__)


class PopulateGraphInteractor:
    """
    Populate knowledge graph with DeFi data from external sources.

    Responsibilities:
    - Fetch data from external providers
    - Transform to graph schema
    - Create nodes and relationships
    - Handle updates and conflicts
    """

    def __init__(
        self,
        graph_repo: GraphRepository,
        data_provider: DefiDataProvider,
    ):
        """
        Initialize populate graph interactor.

        Args:
            graph_repo: Graph repository
            data_provider: External data provider
        """
        self._graph_repo = graph_repo
        self._data_provider = data_provider

        # Track created nodes to avoid duplicates
        self._protocol_map: Dict[str, UUID] = {}
        self._token_map: Dict[str, UUID] = {}
        self._chain_map: Dict[str, UUID] = {}

    async def populate_protocols(
        self,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Populate protocols from external data.

        Args:
            limit: Maximum number of protocols to process

        Returns:
            Statistics about the operation
        """

        logger.info(f"Starting protocol population (limit={limit})...")

        stats = {
            "protocols_fetched": 0,
            "protocols_created": 0,
            "protocols_updated": 0,
            "chains_created": 0,
            "tokens_created": 0,
            "relationships_created": 0,
            "errors": 0,
        }

        try:
            # Fetch protocols from external source
            protocols = await self._data_provider.get_all_protocols(limit=limit)
            stats["protocols_fetched"] = len(protocols)

            logger.info(f"Fetched {len(protocols)} protocols from external source")

            # Process each protocol
            for protocol in protocols:
                try:
                    await self._process_protocol(protocol, stats)
                except Exception as e:
                    logger.error(f"Error processing protocol {protocol.name}: {e}")
                    stats["errors"] += 1

            logger.info(f"Protocol population complete: {stats}")

        except Exception as e:
            logger.error(f"Failed to fetch protocols: {e}")
            stats["errors"] += 1

        return stats

    async def _process_protocol(
        self,
        protocol: ProtocolData,
        stats: Dict[str, Any],
    ) -> UUID:
        """Process a single protocol"""

        # Check if protocol already exists
        existing = await self._find_protocol_by_name(protocol.name)

        if existing:
            # Update existing protocol
            protocol_id = existing.id
            await self._update_protocol_node(protocol_id, protocol)
            stats["protocols_updated"] += 1
            logger.debug(f"Updated protocol: {protocol.name}")
        else:
            # Create new protocol
            protocol_id = await self._create_protocol_node(protocol)
            stats["protocols_created"] += 1
            logger.debug(f"Created protocol: {protocol.name}")

        # Store in map for relationships
        self._protocol_map[protocol.slug] = protocol_id

        # Process chains
        for chain_name in protocol.chains:
            try:
                chain_id = await self._ensure_chain(chain_name, stats)

                # Create DEPLOYED_ON relationship
                await self._create_relationship(
                    from_id=protocol_id,
                    to_id=chain_id,
                    rel_type="DEPLOYED_ON",
                    properties={
                        "created_at": datetime.now(UTC).isoformat(),
                    },
                )
                stats["relationships_created"] += 1
            except Exception as e:
                logger.error(f"Error processing chain {chain_name}: {e}")

        # Process token if available
        if protocol.token_symbol:
            try:
                token_id = await self._ensure_token(
                    symbol=protocol.token_symbol,
                    name=protocol.name,
                    stats=stats,
                )

                # Create USES_TOKEN relationship
                await self._create_relationship(
                    from_id=protocol_id,
                    to_id=token_id,
                    rel_type="USES_TOKEN",
                    properties={
                        "is_native": True,
                        "created_at": datetime.now(UTC).isoformat(),
                    },
                )
                stats["relationships_created"] += 1
            except Exception as e:
                logger.error(f"Error processing token {protocol.token_symbol}: {e}")

        return protocol_id

    async def _create_protocol_node(
        self,
        protocol: ProtocolData,
    ) -> UUID:
        """Create a new protocol node"""

        properties = {
            "name": protocol.name,
            "slug": protocol.slug,
            "description": protocol.description or "",
            "category": protocol.category,
            "tvl": float(protocol.tvl),
            "change_24h": protocol.change_24h or 0.0,
            "website": protocol.website or "",
            "twitter": protocol.twitter or "",
            "github": protocol.github or "",
            "logo": protocol.logo or "",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        return await self._graph_repo.create_node("Protocol", properties)

    async def _update_protocol_node(
        self,
        protocol_id: UUID,
        protocol: ProtocolData,
    ) -> None:
        """Update an existing protocol node"""

        properties = {
            "tvl": float(protocol.tvl),
            "change_24h": protocol.change_24h or 0.0,
            "description": protocol.description or "",
            "website": protocol.website or "",
            "twitter": protocol.twitter or "",
            "github": protocol.github or "",
            "logo": protocol.logo or "",
            "updated_at": datetime.now(UTC).isoformat(),
        }

        await self._graph_repo.update_node(protocol_id, properties)

    async def _find_protocol_by_name(self, name: str):
        """Find protocol by name"""

        protocols = await self._graph_repo.find_nodes(
            label="Protocol",
            filters={"name": name},
            limit=1,
        )

        return protocols[0] if protocols else None

    async def _ensure_chain(
        self,
        chain_name: str,
        stats: Dict[str, Any],
    ) -> UUID:
        """Ensure chain exists, create if not"""

        # Check cache
        if chain_name in self._chain_map:
            return self._chain_map[chain_name]

        # Check database
        existing = await self._find_chain_by_name(chain_name)

        if existing:
            chain_id = existing.id
        else:
            # Create new chain
            chain_id = await self._graph_repo.create_node(
                "Chain",
                {
                    "name": chain_name,
                    "created_at": datetime.now(UTC).isoformat(),
                },
            )
            stats["chains_created"] += 1
            logger.debug(f"Created chain: {chain_name}")

        self._chain_map[chain_name] = chain_id
        return chain_id

    async def _find_chain_by_name(self, name: str):
        """Find chain by name"""

        chains = await self._graph_repo.find_nodes(
            label="Chain",
            filters={"name": name},
            limit=1,
        )

        return chains[0] if chains else None

    async def _ensure_token(
        self,
        symbol: str,
        name: str,
        stats: Dict[str, Any],
    ) -> UUID:
        """Ensure token exists, create if not"""

        # Check cache
        if symbol in self._token_map:
            return self._token_map[symbol]

        # Check database
        existing = await self._find_token_by_symbol(symbol)

        if existing:
            token_id = existing.id
        else:
            # Create new token
            token_id = await self._graph_repo.create_node(
                "Token",
                {
                    "symbol": symbol,
                    "name": name,
                    "created_at": datetime.now(UTC).isoformat(),
                },
            )
            stats["tokens_created"] += 1
            logger.debug(f"Created token: {symbol}")

        self._token_map[symbol] = token_id
        return token_id

    async def _find_token_by_symbol(self, symbol: str):
        """Find token by symbol"""

        tokens = await self._graph_repo.find_nodes(
            label="Token",
            filters={"symbol": symbol},
            limit=1,
        )

        return tokens[0] if tokens else None

    async def _create_relationship(
        self,
        from_id: UUID,
        to_id: UUID,
        rel_type: str,
        properties: Dict[str, Any],
    ) -> None:
        """Create a relationship if it doesn't exist"""

        # Check if relationship already exists
        existing = await self._graph_repo.find_edges(
            from_id=from_id,
            to_id=to_id,
            relationship_type=rel_type,
        )

        if not existing:
            await self._graph_repo.create_edge(
                from_id=from_id,
                to_id=to_id,
                relationship_type=rel_type,
                properties=properties,
            )

    async def populate_dependencies(
        self,
        dependency_map: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        """
        Populate protocol dependencies.

        Args:
            dependency_map: Map of protocol slug -> list of dependency slugs

        Returns:
            Statistics about the operation

        Example:
            >>> await interactor.populate_dependencies({
            ...     "aave": ["chainlink", "uniswap"],
            ...     "compound": ["chainlink"],
            ... })
        """

        logger.info(f"Populating {len(dependency_map)} protocol dependencies...")

        stats = {
            "dependencies_created": 0,
            "errors": 0,
        }

        for protocol_slug, dep_slugs in dependency_map.items():
            try:
                # Get protocol ID
                if protocol_slug not in self._protocol_map:
                    protocol = await self._find_protocol_by_name(protocol_slug)
                    if not protocol:
                        logger.warning(f"Protocol not found: {protocol_slug}")
                        continue
                    self._protocol_map[protocol_slug] = protocol.id

                protocol_id = self._protocol_map[protocol_slug]

                # Create dependencies
                for dep_slug in dep_slugs:
                    try:
                        # Get dependency ID
                        if dep_slug not in self._protocol_map:
                            dep_protocol = await self._find_protocol_by_name(dep_slug)
                            if not dep_protocol:
                                logger.warning(
                                    f"Dependency protocol not found: {dep_slug}"
                                )
                                continue
                            self._protocol_map[dep_slug] = dep_protocol.id

                        dep_id = self._protocol_map[dep_slug]

                        # Create DEPENDS_ON relationship
                        await self._create_relationship(
                            from_id=protocol_id,
                            to_id=dep_id,
                            rel_type="DEPENDS_ON",
                            properties={
                                "created_at": datetime.now(UTC).isoformat(),
                            },
                        )
                        stats["dependencies_created"] += 1

                    except Exception as e:
                        logger.error(
                            f"Error creating dependency {protocol_slug} -> {dep_slug}: {e}"
                        )
                        stats["errors"] += 1

            except Exception as e:
                logger.error(f"Error processing protocol {protocol_slug}: {e}")
                stats["errors"] += 1

        logger.info(f"Dependency population complete: {stats}")
        return stats
