"""
Source information value object for chat message attribution.

Provides structured source information for frontend display of knowledge sources,
citations, and data provenance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class SourceType(str, Enum):
    """Type of data source."""

    API = "api"  # External API (CoinGecko, 1inch, etc.)
    DATABASE = "database"  # Internal database query
    MCP_SERVER = "mcp_server"  # MCP server tool
    RSS_FEED = "rss_feed"  # RSS news feed
    SOCIAL_MEDIA = "social_media"  # Twitter, Reddit, Discord
    BLOCKCHAIN = "blockchain"  # On-chain data (RPC calls)
    LLM = "llm"  # LLM-generated content
    AGGREGATED = "aggregated"  # Aggregated from multiple sources
    KNOWLEDGE_BASE = "knowledge_base"  # Anvil knowledge base (JSON files)


@dataclass
class SourceInfo:
    """
    Information about a data source used in agent response.

    Provides structured source attribution for frontend display.
    """

    # Source identification
    source_type: SourceType
    source_name: str  # e.g., "CoinGecko", "1inch", "Aave V3"
    source_id: Optional[str] = None  # API endpoint, contract address, etc.

    # Citation information
    url: Optional[str] = None  # Direct link to source (if available)
    citation_text: Optional[str] = None  # Human-readable citation

    # Data freshness
    fetched_at: Optional[datetime] = None  # When data was fetched
    data_age_seconds: Optional[int] = None  # Age of data in seconds

    # Source metadata
    provider: Optional[str] = None  # Provider name (e.g., "CoinGecko API")
    endpoint: Optional[str] = None  # API endpoint used
    query_params: Optional[dict] = None  # Query parameters (sanitized)

    # Relevance
    relevance_score: Optional[float] = None  # 0.0-1.0, how relevant to response
    data_points_used: Optional[int] = None  # Number of data points from this source

    # Additional context
    metadata: Optional[dict] = None  # Additional source-specific data

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "source_type": self.source_type.value,
            "source_name": self.source_name,
            "source_id": self.source_id,
            "url": self.url,
            "citation_text": self.citation_text,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "data_age_seconds": self.data_age_seconds,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "query_params": self.query_params,
            "relevance_score": self.relevance_score,
            "data_points_used": self.data_points_used,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SourceInfo":
        """Deserialize from dictionary."""
        fetched_at = None
        if data.get("fetched_at"):
            if isinstance(data["fetched_at"], str):
                fetched_at = datetime.fromisoformat(
                    data["fetched_at"].replace("Z", "+00:00")
                )
            else:
                fetched_at = data["fetched_at"]

        return cls(
            source_type=SourceType(data.get("source_type", "api")),
            source_name=data["source_name"],
            source_id=data.get("source_id"),
            url=data.get("url"),
            citation_text=data.get("citation_text"),
            fetched_at=fetched_at,
            data_age_seconds=data.get("data_age_seconds"),
            provider=data.get("provider"),
            endpoint=data.get("endpoint"),
            query_params=data.get("query_params"),
            relevance_score=data.get("relevance_score"),
            data_points_used=data.get("data_points_used"),
            metadata=data.get("metadata"),
        )


def sanitize_query_params(params: dict) -> dict:
    """
    Remove sensitive data from query params.

    Args:
        params: Query parameters dictionary

    Returns:
        Sanitized query parameters
    """
    sanitized = {}
    sensitive_keys = ["api_key", "secret", "password", "token", "private_key", "auth"]

    for key, value in params.items():
        if key.lower() in sensitive_keys:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 100:
            sanitized[key] = value[:50] + "..."
        else:
            sanitized[key] = value

    return sanitized
