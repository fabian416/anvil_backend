"""User preferences domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass
class SavedSearch:
    """Saved search preset."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    query: str = ""
    filters: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SearchPreferences:
    """User's GraphRAG search preferences."""

    default_similarity_threshold: float = 0.7
    default_risk_filter: Optional[str] = None  # LOW/MEDIUM/HIGH/CRITICAL
    saved_searches: List[SavedSearch] = field(default_factory=list)
    search_history_enabled: bool = True
    max_history_entries: int = 100

    def add_saved_search(self, name: str, query: str, filters: dict) -> SavedSearch:
        """Add a new saved search."""
        search = SavedSearch(name=name, query=query, filters=filters)
        self.saved_searches.append(search)
        return search

    def remove_saved_search(self, search_id: UUID) -> bool:
        """Remove a saved search."""
        initial_len = len(self.saved_searches)
        self.saved_searches = [s for s in self.saved_searches if s.id != search_id]
        return len(self.saved_searches) < initial_len

    def get_saved_search(self, search_id: UUID) -> Optional[SavedSearch]:
        """Get a specific saved search."""
        for search in self.saved_searches:
            if search.id == search_id:
                return search
        return None


@dataclass
class NotificationPreferences:
    """User's notification preferences."""

    # Alert types
    risk_alerts_enabled: bool = True
    protocol_updates_enabled: bool = True
    price_alerts_enabled: bool = True
    transaction_alerts_enabled: bool = True

    # Channels
    push_enabled: bool = True
    email_enabled: bool = False
    websocket_enabled: bool = True

    # Severity threshold
    min_severity: str = "MEDIUM"  # Only notify for MEDIUM and above

    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[int] = None  # Hour (0-23)
    quiet_hours_end: Optional[int] = None

    def should_notify(self, severity: str, hour: int) -> bool:
        """Check if should send notification."""
        # Check quiet hours
        if self.quiet_hours_enabled and self.quiet_hours_start and self.quiet_hours_end:
            if self.quiet_hours_start <= hour < self.quiet_hours_end:
                # Only critical alerts during quiet hours
                return severity == "CRITICAL"

        # Check severity threshold
        severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        try:
            min_idx = severity_order.index(self.min_severity)
            alert_idx = severity_order.index(severity)
            return alert_idx >= min_idx
        except ValueError:
            return True


@dataclass
class UserPreferences:
    """Complete user preferences entity."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default=None)

    # Risk preferences
    risk_tolerance: str = "moderate"  # conservative/moderate/aggressive

    # Chain preferences
    preferred_chains: List[str] = field(default_factory=list)

    # Category preferences
    preferred_categories: List[str] = field(default_factory=list)

    # Protocol preferences
    excluded_protocols: List[UUID] = field(default_factory=list)
    favorite_protocols: List[UUID] = field(default_factory=list)

    # Search preferences
    search_settings: SearchPreferences = field(default_factory=SearchPreferences)

    # Notification preferences
    notification_settings: NotificationPreferences = field(
        default_factory=NotificationPreferences
    )

    # Display preferences
    default_currency: str = "USD"
    theme: str = "dark"  # light/dark/system
    compact_mode: bool = False

    # Privacy preferences
    analytics_enabled: bool = True
    personalization_enabled: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update_risk_tolerance(self, tolerance: str) -> None:
        """Update risk tolerance level."""
        valid_levels = ["conservative", "moderate", "aggressive"]
        if tolerance not in valid_levels:
            raise ValueError(f"Invalid risk tolerance: {tolerance}")
        self.risk_tolerance = tolerance
        self.updated_at = datetime.utcnow()

    def add_preferred_chain(self, chain: str) -> None:
        """Add a preferred chain."""
        if chain not in self.preferred_chains:
            self.preferred_chains.append(chain)
            self.updated_at = datetime.utcnow()

    def remove_preferred_chain(self, chain: str) -> bool:
        """Remove a preferred chain."""
        if chain in self.preferred_chains:
            self.preferred_chains.remove(chain)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def exclude_protocol(self, protocol_id: UUID) -> None:
        """Add protocol to exclusion list."""
        if protocol_id not in self.excluded_protocols:
            self.excluded_protocols.append(protocol_id)
            self.updated_at = datetime.utcnow()

    def include_protocol(self, protocol_id: UUID) -> bool:
        """Remove protocol from exclusion list."""
        if protocol_id in self.excluded_protocols:
            self.excluded_protocols.remove(protocol_id)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def add_favorite(self, protocol_id: UUID) -> None:
        """Add protocol to favorites."""
        if protocol_id not in self.favorite_protocols:
            self.favorite_protocols.append(protocol_id)
            self.updated_at = datetime.utcnow()

    def remove_favorite(self, protocol_id: UUID) -> bool:
        """Remove protocol from favorites."""
        if protocol_id in self.favorite_protocols:
            self.favorite_protocols.remove(protocol_id)
            self.updated_at = datetime.utcnow()
            return True
        return False
