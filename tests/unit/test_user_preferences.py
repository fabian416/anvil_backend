"""
Unit tests for User Preferences Service.

Tests user personalization, saved searches, favorites,
and notification preferences.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.application.preferences.user_preferences_service import (
    UserPreferencesService,
)
from app.domain.entities.user_preferences import UserPreferences


@pytest.fixture
def preferences_service():
    """Create user preferences service."""
    return UserPreferencesService()


@pytest.fixture
def user_id():
    """Sample user ID."""
    return uuid4()


class TestUserPreferences:
    """Test suite for User Preferences Service."""

    @pytest.mark.asyncio
    async def test_get_default_preferences(self, preferences_service, user_id):
        """Test retrieving default preferences for new user."""
        prefs = await preferences_service.get_user_preferences(user_id)
        
        # Should return default preferences
        assert prefs.user_id == user_id
        assert prefs.risk_tolerance == "moderate"
        assert prefs.default_currency == "USD"
        assert prefs.theme == "dark"

    @pytest.mark.asyncio
    async def test_update_risk_tolerance(self, preferences_service, user_id):
        """Test updating risk tolerance."""
        await preferences_service.update_risk_tolerance(user_id, "aggressive")
        
        prefs = await preferences_service.get_user_preferences(user_id)
        assert prefs.risk_tolerance == "aggressive"

    @pytest.mark.asyncio
    async def test_risk_tolerance_validation(self, preferences_service, user_id):
        """Test that invalid risk tolerance is rejected."""
        with pytest.raises(ValueError):
            await preferences_service.update_risk_tolerance(user_id, "invalid")

    @pytest.mark.asyncio
    async def test_update_chain_preferences(self, preferences_service, user_id):
        """Test updating preferred chains."""
        chains = ["ethereum", "arbitrum", "optimism"]
        await preferences_service.update_chain_preferences(user_id, chains)
        
        prefs = await preferences_service.get_user_preferences(user_id)
        assert set(prefs.preferred_chains) == set(chains)

    @pytest.mark.asyncio
    async def test_exclude_protocol(self, preferences_service, user_id):
        """Test excluding protocols from recommendations."""
        protocol_id = uuid4()
        await preferences_service.exclude_protocol(user_id, protocol_id)
        
        prefs = await preferences_service.get_user_preferences(user_id)
        assert protocol_id in prefs.excluded_protocols

    @pytest.mark.asyncio
    async def test_include_excluded_protocol(self, preferences_service, user_id):
        """Test re-including a previously excluded protocol."""
        protocol_id = uuid4()
        
        # First exclude
        await preferences_service.exclude_protocol(user_id, protocol_id)
        prefs = await preferences_service.get_user_preferences(user_id)
        assert protocol_id in prefs.excluded_protocols
        
        # Then include
        await preferences_service.include_protocol(user_id, protocol_id)
        prefs = await preferences_service.get_user_preferences(user_id)
        assert protocol_id not in prefs.excluded_protocols

    @pytest.mark.asyncio
    async def test_add_favorite_protocol(self, preferences_service, user_id):
        """Test adding protocol to favorites."""
        protocol_id = uuid4()
        await preferences_service.add_favorite_protocol(user_id, protocol_id)
        
        prefs = await preferences_service.get_user_preferences(user_id)
        assert protocol_id in prefs.favorite_protocols

    @pytest.mark.asyncio
    async def test_remove_favorite_protocol(self, preferences_service, user_id):
        """Test removing protocol from favorites."""
        protocol_id = uuid4()
        
        # Add then remove
        await preferences_service.add_favorite_protocol(user_id, protocol_id)
        await preferences_service.remove_favorite_protocol(user_id, protocol_id)
        
        prefs = await preferences_service.get_user_preferences(user_id)
        assert protocol_id not in prefs.favorite_protocols

    @pytest.mark.asyncio
    async def test_save_search(self, preferences_service, user_id):
        """Test saving a search query."""
        search = await preferences_service.save_search(
            user_id=user_id,
            name="My Safe Protocols",
            query="safe staking protocols",
            filters={"risk_levels": ["LOW", "MEDIUM"]},
        )
        
        assert search.name == "My Safe Protocols"
        assert search.query == "safe staking protocols"
        
        prefs = await preferences_service.get_user_preferences(user_id)
        assert len(prefs.search_settings.saved_searches) == 1

    @pytest.mark.asyncio
    async def test_delete_saved_search(self, preferences_service, user_id):
        """Test deleting a saved search."""
        # Save search
        search = await preferences_service.save_search(
            user_id, "Test", "test query", {}
        )
        
        # Delete it
        await preferences_service.delete_saved_search(user_id, search.id)
        
        prefs = await preferences_service.get_user_preferences(user_id)
        assert len(prefs.search_settings.saved_searches) == 0

    @pytest.mark.asyncio
    async def test_notification_preferences(self, preferences_service, user_id):
        """Test updating notification preferences."""
        await preferences_service.update_notification_preferences(
            user_id=user_id,
            email_enabled=True,
            push_enabled=False,
            risk_alerts=True,
            price_alerts=False,
        )
        
        prefs = await preferences_service.get_user_preferences(user_id)
        assert prefs.notification_settings.email_enabled is True
        assert prefs.notification_settings.push_enabled is False
        assert prefs.notification_settings.risk_alerts is True
        assert prefs.notification_settings.price_alerts is False

    @pytest.mark.asyncio
    async def test_multiple_saved_searches(self, preferences_service, user_id):
        """Test saving multiple searches."""
        searches = [
            ("Safe Protocols", "safe protocols"),
            ("High Yield", "high yield farming"),
            ("Ethereum Only", "ethereum protocols"),
        ]
        
        for name, query in searches:
            await preferences_service.save_search(user_id, name, query, {})
        
        prefs = await preferences_service.get_user_preferences(user_id)
        assert len(prefs.search_settings.saved_searches) == 3
