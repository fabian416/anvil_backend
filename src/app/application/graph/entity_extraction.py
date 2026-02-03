"""Entity extraction service for GraphRAG knowledge graph.

This module provides LLM-based entity extraction from user conversations
to automatically populate the knowledge graph with DeFi entities.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from app.domain.ports.ai.llm_gateway import LLMGateway


class EntityType(str, Enum):
    """Types of entities that can be extracted."""

    PROTOCOL = "protocol"
    TOKEN = "token"
    ADDRESS = "address"
    POOL = "pool"
    CHAIN = "chain"
    EXCHANGE = "exchange"
    LENDING_PLATFORM = "lending_platform"
    YIELD_AGGREGATOR = "yield_aggregator"


@dataclass
class ExtractedEntity:
    """Represents an entity extracted from text."""

    name: str
    type: EntityType
    confidence: float
    context: str
    metadata: Dict[str, str]


class EntityExtractor:
    """Extracts DeFi entities from text using LLM."""

    def __init__(self, llm_gateway: LLMGateway):
        """Initialize entity extractor.

        Args:
            llm_gateway: LLM gateway for entity extraction
        """
        self._llm = llm_gateway

    async def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract entities from text using LLM.

        Args:
            text: Input text (user message, conversation)

        Returns:
            List of extracted entities with confidence scores

        Example:
            >>> extractor = EntityExtractor(llm_client)
            >>> entities = await extractor.extract_entities(
            ...     "What's the APY for Uniswap ETH-USDC pool?"
            ... )
            >>> # Returns:
            >>> # [
            >>> #   ExtractedEntity(
            >>> #     name="Uniswap",
            >>> #     type=EntityType.PROTOCOL,
            >>> #     confidence=0.95,
            >>> #     ...
            >>> #   ),
            >>> #   ExtractedEntity(
            >>> #     name="ETH",
            >>> #     type=EntityType.TOKEN,
            >>> #     confidence=0.99,
            >>> #     ...
            >>> #   ),
            >>> #   ...
            >>> # ]
        """
        if not text or len(text.strip()) < 3:
            return []

        prompt = self._build_extraction_prompt(text)
        messages = [{"role": "user", "content": prompt}]
        response = await self._llm.generate(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct",
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
        )
        entities = self._parse_entities(response, text)

        return entities

    def _build_extraction_prompt(self, text: str) -> str:
        """Build LLM prompt for entity extraction.

        Args:
            text: Input text

        Returns:
            Formatted prompt for LLM
        """
        return f"""You are a DeFi entity extraction system. Extract all relevant DeFi entities from the following text.

For each entity, identify:
1. Entity name (exact match from text)
2. Entity type (protocol, token, address, pool, chain, exchange, lending_platform, yield_aggregator)
3. Confidence score (0.0 to 1.0)

Text: "{text}"

Return entities in JSON format:
{{
  "entities": [
    {{
      "name": "Uniswap",
      "type": "protocol",
      "confidence": 0.95,
      "context": "mentioned in relation to liquidity pool"
    }},
    ...
  ]
}}

Rules:
- Only extract entities explicitly mentioned in the text
- Use exact names from text (preserve capitalization)
- Assign high confidence (>0.9) for well-known entities
- Assign medium confidence (0.7-0.9) for context-based inferences
- Assign low confidence (<0.7) for ambiguous entities
- Include brief context for each entity

Extract entities now:"""

    def _parse_entities(
        self, llm_response: str, original_text: str
    ) -> List[ExtractedEntity]:
        """Parse LLM response into structured entities.

        Args:
            llm_response: Raw LLM response
            original_text: Original input text

        Returns:
            List of extracted entities
        """
        import json
        import re

        entities: List[ExtractedEntity] = []

        try:
            # Try to parse as JSON first
            # Extract JSON from markdown code blocks if present
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", llm_response, re.DOTALL
            )
            if json_match:
                llm_response = json_match.group(1)

            data = json.loads(llm_response)
            entities_data = data.get("entities", [])

            for entity_data in entities_data:
                try:
                    entity = ExtractedEntity(
                        name=entity_data["name"],
                        type=EntityType(entity_data["type"]),
                        confidence=float(entity_data["confidence"]),
                        context=entity_data.get("context", ""),
                        metadata={},
                    )
                    entities.append(entity)
                except (KeyError, ValueError) as e:
                    # Skip malformed entities
                    continue

        except json.JSONDecodeError:
            # Fallback: use simple pattern matching
            entities = self._fallback_extraction(original_text)

        return entities

    def _fallback_extraction(self, text: str) -> List[ExtractedEntity]:
        """Fallback entity extraction using pattern matching.

        Args:
            text: Input text

        Returns:
            List of extracted entities
        """
        entities: List[ExtractedEntity] = []

        # Common DeFi protocols
        protocols = [
            "uniswap",
            "aave",
            "compound",
            "curve",
            "sushiswap",
            "balancer",
            "yearn",
            "maker",
            "lido",
            "convex",
        ]

        # Common tokens
        tokens = [
            "eth",
            "btc",
            "usdc",
            "usdt",
            "dai",
            "weth",
            "wbtc",
            "link",
            "uni",
            "aave",
        ]

        text_lower = text.lower()

        # Extract protocols
        for protocol in protocols:
            if protocol in text_lower:
                entities.append(
                    ExtractedEntity(
                        name=protocol.capitalize(),
                        type=EntityType.PROTOCOL,
                        confidence=0.85,
                        context=f"found in text: {text[:50]}...",
                        metadata={},
                    )
                )

        # Extract tokens
        for token in tokens:
            if token in text_lower:
                entities.append(
                    ExtractedEntity(
                        name=token.upper(),
                        type=EntityType.TOKEN,
                        confidence=0.90,
                        context=f"found in text: {text[:50]}...",
                        metadata={},
                    )
                )

        return entities

    async def extract_and_validate(
        self, text: str, min_confidence: float = 0.7
    ) -> List[ExtractedEntity]:
        """Extract entities and filter by confidence threshold.

        Args:
            text: Input text
            min_confidence: Minimum confidence threshold (0.0-1.0)

        Returns:
            List of validated entities above confidence threshold
        """
        entities = await self.extract_entities(text)
        validated = [e for e in entities if e.confidence >= min_confidence]
        return validated

    async def extract_relationships(
        self, text: str, entities: List[ExtractedEntity]
    ) -> List[Dict[str, str]]:
        """Extract relationships between entities.

        Args:
            text: Input text
            entities: Previously extracted entities

        Returns:
            List of relationships between entities

        Example:
            >>> relationships = await extractor.extract_relationships(
            ...     "Uniswap provides liquidity for ETH-USDC",
            ...     [uniswap_entity, eth_entity, usdc_entity]
            ... )
            >>> # Returns:
            >>> # [
            >>> #   {
            >>> #     "source": "Uniswap",
            >>> #     "target": "ETH",
            >>> #     "type": "PROVIDES_LIQUIDITY",
            >>> #     "confidence": 0.88
            >>> #   },
            >>> #   ...
            >>> # ]
        """
        if len(entities) < 2:
            return []

        entity_names = [e.name for e in entities]
        prompt = self._build_relationship_prompt(text, entity_names)
        messages = [{"role": "user", "content": prompt}]
        response = await self._llm.generate(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct",
            messages=messages,
            temperature=0.3,
            max_tokens=800,
        )
        relationships = self._parse_relationships(response)

        return relationships

    def _build_relationship_prompt(self, text: str, entity_names: List[str]) -> str:
        """Build prompt for relationship extraction.

        Args:
            text: Input text
            entity_names: List of entity names

        Returns:
            Formatted prompt
        """
        entities_str = ", ".join(entity_names)
        return f"""You are a DeFi relationship extraction system. Identify relationships between the following entities based on the text.

Entities: {entities_str}

Text: "{text}"

Return relationships in JSON format:
{{
  "relationships": [
    {{
      "source": "Uniswap",
      "target": "ETH",
      "type": "PROVIDES_LIQUIDITY",
      "confidence": 0.88
    }},
    ...
  ]
}}

Relationship types:
- PROVIDES_LIQUIDITY
- TRADES_ON
- LENDS_TO
- BORROWS_FROM
- POOLS_WITH
- BUILT_ON (for chain relationships)
- INTEGRATES_WITH

Extract relationships now:"""

    def _parse_relationships(self, llm_response: str) -> List[Dict[str, str]]:
        """Parse relationship extraction response.

        Args:
            llm_response: Raw LLM response

        Returns:
            List of relationships
        """
        import json
        import re

        relationships: List[Dict[str, str]] = []

        try:
            # Extract JSON from markdown
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", llm_response, re.DOTALL
            )
            if json_match:
                llm_response = json_match.group(1)

            data = json.loads(llm_response)
            relationships = data.get("relationships", [])

        except json.JSONDecodeError:
            pass

        return relationships
