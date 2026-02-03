"""
Generate Embeddings Interactor

Service for generating and storing embeddings for graph entities.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

from app.domain.graph.ports import GraphRepository
from app.domain.ports.embeddings import EmbeddingService
from app.domain.ports.vector import VectorRepository


logger = logging.getLogger(__name__)


class GenerateEmbeddingsInteractor:
    """
    Generate and store embeddings for graph entities.

    Responsibilities:
    - Generate embeddings for protocols
    - Generate embeddings for other entities
    - Store in vector database
    - Track statistics
    """

    def __init__(
        self,
        graph_repo: GraphRepository,
        embedding_service: EmbeddingService,
        vector_repo: VectorRepository,
    ):
        """
        Initialize generate embeddings interactor.

        Args:
            graph_repo: Graph repository
            embedding_service: Embedding service
            vector_repo: Vector repository
        """
        self._graph_repo = graph_repo
        self._embedding_service = embedding_service
        self._vector_repo = vector_repo

    async def generate_protocol_embeddings(
        self,
        limit: Optional[int] = None,
        force_regenerate: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate embeddings for all protocols.

        Args:
            limit: Maximum number of protocols to process
            force_regenerate: Regenerate even if embedding exists

        Returns:
            Statistics about the operation
        """

        logger.info(
            f"Generating protocol embeddings (limit={limit}, force={force_regenerate})..."
        )

        stats = {
            "protocols_fetched": 0,
            "embeddings_generated": 0,
            "embeddings_skipped": 0,
            "errors": 0,
        }

        try:
            # Fetch protocols from graph
            protocols = await self._graph_repo.find_nodes(
                label="Protocol",
                limit=limit or 1000,
            )

            stats["protocols_fetched"] = len(protocols)
            logger.info(f"Fetched {len(protocols)} protocols")

            # Process each protocol
            for protocol in protocols:
                try:
                    await self._process_protocol_embedding(
                        protocol,
                        force_regenerate,
                        stats,
                    )
                except Exception as e:
                    logger.error(f"Error processing protocol {protocol.id}: {e}")
                    stats["errors"] += 1

            logger.info(f"Embedding generation complete: {stats}")

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            stats["errors"] += 1

        return stats

    async def _process_protocol_embedding(
        self,
        protocol,
        force_regenerate: bool,
        stats: Dict[str, Any],
    ) -> None:
        """Process embedding for a single protocol"""

        # Check if embedding already exists
        if not force_regenerate:
            existing = await self._vector_repo.get_embedding(protocol.id)
            if existing:
                logger.debug(
                    f"Skipping protocol {protocol.properties.get('name')} (already exists)"
                )
                stats["embeddings_skipped"] += 1
                return

        # Generate text content for embedding
        text_content = self._generate_protocol_text(protocol)

        # Generate embedding
        embedding = await self._embedding_service.embed_text(text_content)

        # Store embedding
        await self._vector_repo.store_embedding(
            entity_id=protocol.id,
            entity_type="Protocol",
            entity_name=protocol.properties.get("name", "Unknown"),
            text_content=text_content,
            embedding=embedding,
            model="text-embedding-3-small",
        )

        stats["embeddings_generated"] += 1
        logger.debug(
            f"Generated embedding for protocol {protocol.properties.get('name')}"
        )

    def _generate_protocol_text(self, protocol) -> str:
        """
        Generate text content for protocol embedding.

        Combines name, category, description for rich semantic representation.
        """

        parts = []

        # Name
        name = protocol.properties.get("name", "")
        if name:
            parts.append(f"Protocol: {name}")

        # Category
        category = protocol.properties.get("category", "")
        if category:
            parts.append(f"Category: {category}")

        # Description
        description = protocol.properties.get("description", "")
        if description:
            parts.append(f"Description: {description}")

        # Additional metadata
        if protocol.properties.get("website"):
            parts.append(f"Website: {protocol.properties['website']}")

        return " | ".join(parts) if parts else "Unknown protocol"

    async def generate_batch_embeddings(
        self,
        entity_ids: List[UUID],
        entity_type: str = "Protocol",
    ) -> Dict[str, Any]:
        """
        Generate embeddings for a batch of entities.

        Args:
            entity_ids: List of entity IDs
            entity_type: Type of entities

        Returns:
            Statistics about the operation
        """

        logger.info(
            f"Generating {len(entity_ids)} {entity_type} embeddings in batch..."
        )

        stats = {
            "total": len(entity_ids),
            "generated": 0,
            "errors": 0,
        }

        # Fetch entities
        entities = []
        for entity_id in entity_ids:
            entity = await self._graph_repo.get_node(entity_id)
            if entity:
                entities.append(entity)

        # Generate texts
        texts = []
        for entity in entities:
            if entity_type == "Protocol":
                text = self._generate_protocol_text(entity)
            else:
                text = entity.properties.get("name", "Unknown")
            texts.append(text)

        # Batch embed
        try:
            embeddings = await self._embedding_service.embed_texts(texts)

            # Store all embeddings
            for entity, text, embedding in zip(entities, texts, embeddings):
                try:
                    await self._vector_repo.store_embedding(
                        entity_id=entity.id,
                        entity_type=entity_type,
                        entity_name=entity.properties.get("name", "Unknown"),
                        text_content=text,
                        embedding=embedding,
                        model="text-embedding-3-small",
                    )
                    stats["generated"] += 1
                except Exception as e:
                    logger.error(f"Error storing embedding for {entity.id}: {e}")
                    stats["errors"] += 1

        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            stats["errors"] += len(entity_ids)

        logger.info(f"Batch embedding complete: {stats}")
        return stats

    async def regenerate_embedding(
        self,
        entity_id: UUID,
    ) -> bool:
        """
        Regenerate embedding for a single entity.

        Args:
            entity_id: Entity ID

        Returns:
            True if successful
        """

        try:
            # Get entity from graph
            entity = await self._graph_repo.get_node(entity_id)
            if not entity:
                logger.warning(f"Entity {entity_id} not found")
                return False

            # Determine entity type from labels
            entity_type = entity.labels[0] if entity.labels else "Unknown"

            # Generate text
            if entity_type == "Protocol":
                text = self._generate_protocol_text(entity)
            else:
                text = entity.properties.get("name", "Unknown")

            # Generate embedding
            embedding = await self._embedding_service.embed_text(text)

            # Store
            await self._vector_repo.store_embedding(
                entity_id=entity.id,
                entity_type=entity_type,
                entity_name=entity.properties.get("name", "Unknown"),
                text_content=text,
                embedding=embedding,
                model="text-embedding-3-small",
            )

            logger.info(f"Regenerated embedding for {entity_type} {entity.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to regenerate embedding: {e}")
            return False
