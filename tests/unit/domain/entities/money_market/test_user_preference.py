"""
Tests for MoneyMarketUserPreference entity.

Tests entity creation, validation, and rich domain properties.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.domain.entities.money_market.user_preference import (
    MoneyMarketUserPreference,
)


@pytest.mark.unit
class TestMoneyMarketUserPreference:
    """Test suite for MoneyMarketUserPreference entity."""

    def test_valid_entity_creation(self):
        """Should create valid entity with correct attributes."""
        # Arrange
        now = datetime.now(timezone.utc)
        entity_id = uuid4()
        user_id = uuid4()

        # Act
        entity = MoneyMarketUserPreference(
            id=entity_id,
            user_id=user_id,
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("0.50"),
            watched_assets=["USDC", "USDT", "DAI"],
            watched_chains=["ethereum", "polygon", "arbitrum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Assert
        assert entity.id == entity_id
        assert entity.user_id == user_id
        assert entity.rate_alerts_enabled is True
        assert entity.alert_threshold_percent == Decimal("0.50")
        assert entity.watched_assets == ["USDC", "USDT", "DAI"]
        assert entity.watched_chains == ["ethereum", "polygon", "arbitrum"]
        assert entity.preferred_protocol == "aave_v3"
        assert entity.risk_tolerance == "MODERATE"
        assert entity.sort_by == "HIGHEST_YIELD"
        assert entity.created_at == now
        assert entity.updated_at == now

    def test_valid_entity_with_defaults(self):
        """Should create valid entity with default values."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act
        entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=[],
            watched_chains=[],
            preferred_protocol=None,
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Assert
        assert entity.rate_alerts_enabled is False
        assert entity.watched_assets == []
        assert entity.watched_chains == []
        assert entity.preferred_protocol is None

    def test_validation_threshold_too_low(self):
        """Should raise error for threshold < 0.01%."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="alert_threshold_percent must be between 0.01% and 10%"):
            MoneyMarketUserPreference(
                id=uuid4(),
                user_id=uuid4(),
                rate_alerts_enabled=True,
                alert_threshold_percent=Decimal("0.005"),  # Too low
                watched_assets=["USDC"],
                watched_chains=["ethereum"],
                preferred_protocol="aave_v3",
                risk_tolerance="MODERATE",
                sort_by="HIGHEST_YIELD",
                created_at=now,
                updated_at=now,
            )

    def test_validation_threshold_too_high(self):
        """Should raise error for threshold > 10%."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="alert_threshold_percent must be between 0.01% and 10%"):
            MoneyMarketUserPreference(
                id=uuid4(),
                user_id=uuid4(),
                rate_alerts_enabled=True,
                alert_threshold_percent=Decimal("15.0"),  # Too high
                watched_assets=["USDC"],
                watched_chains=["ethereum"],
                preferred_protocol="aave_v3",
                risk_tolerance="MODERATE",
                sort_by="HIGHEST_YIELD",
                created_at=now,
                updated_at=now,
            )

    def test_validation_invalid_risk_tolerance(self):
        """Should raise error for invalid risk tolerance."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid risk_tolerance"):
            MoneyMarketUserPreference(
                id=uuid4(),
                user_id=uuid4(),
                rate_alerts_enabled=False,
                alert_threshold_percent=Decimal("1.00"),
                watched_assets=["USDC"],
                watched_chains=["ethereum"],
                preferred_protocol="aave_v3",
                risk_tolerance="INVALID_RISK",  # Invalid
                sort_by="HIGHEST_YIELD",
                created_at=now,
                updated_at=now,
            )

    def test_validation_invalid_sort_by(self):
        """Should raise error for invalid sort_by."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid sort_by"):
            MoneyMarketUserPreference(
                id=uuid4(),
                user_id=uuid4(),
                rate_alerts_enabled=False,
                alert_threshold_percent=Decimal("1.00"),
                watched_assets=["USDC"],
                watched_chains=["ethereum"],
                preferred_protocol="aave_v3",
                risk_tolerance="MODERATE",
                sort_by="INVALID_SORT",  # Invalid
                created_at=now,
                updated_at=now,
            )

    def test_validation_invalid_preferred_protocol(self):
        """Should raise error for invalid preferred protocol."""
        # Arrange
        now = datetime.now(timezone.utc)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid preferred_protocol"):
            MoneyMarketUserPreference(
                id=uuid4(),
                user_id=uuid4(),
                rate_alerts_enabled=False,
                alert_threshold_percent=Decimal("1.00"),
                watched_assets=["USDC"],
                watched_chains=["ethereum"],
                preferred_protocol="invalid_protocol",  # Invalid
                risk_tolerance="MODERATE",
                sort_by="HIGHEST_YIELD",
                created_at=now,
                updated_at=now,
            )

    def test_has_rate_alerts_property(self):
        """Should identify when rate alerts are enabled."""
        # Arrange
        now = datetime.now(timezone.utc)

        enabled_entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        disabled_entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert enabled_entity.has_rate_alerts
        assert not disabled_entity.has_rate_alerts

    def test_is_watching_asset_method(self):
        """Should check if user is watching specific asset."""
        # Arrange
        now = datetime.now(timezone.utc)

        entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC", "USDT", "DAI"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert entity.is_watching_asset("USDC")
        assert entity.is_watching_asset("USDT")
        assert entity.is_watching_asset("DAI")
        assert not entity.is_watching_asset("WETH")

    def test_is_watching_chain_method(self):
        """Should check if user is watching specific chain."""
        # Arrange
        now = datetime.now(timezone.utc)

        entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum", "polygon", "arbitrum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert entity.is_watching_chain("ethereum")
        assert entity.is_watching_chain("polygon")
        assert entity.is_watching_chain("arbitrum")
        assert not entity.is_watching_chain("optimism")

    def test_should_alert_for_change_method(self):
        """Should determine if rate change triggers alert."""
        # Arrange
        now = datetime.now(timezone.utc)

        entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("0.50"),  # 0.5% threshold
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert entity.should_alert_for_change(Decimal("0.60"))  # Above threshold
        assert entity.should_alert_for_change(Decimal("1.00"))  # Above threshold
        assert not entity.should_alert_for_change(Decimal("0.40"))  # Below threshold
        assert not entity.should_alert_for_change(Decimal("0.30"))  # Below threshold

    def test_should_alert_for_change_when_disabled(self):
        """Should not alert when rate alerts are disabled."""
        # Arrange
        now = datetime.now(timezone.utc)

        entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,  # Disabled
            alert_threshold_percent=Decimal("0.50"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert not entity.should_alert_for_change(Decimal("1.00"))  # Should not alert even if above threshold

    def test_has_preferred_protocol_property(self):
        """Should identify when user has preferred protocol."""
        # Arrange
        now = datetime.now(timezone.utc)

        with_preferred = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        without_preferred = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol=None,
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert with_preferred.has_preferred_protocol
        assert not without_preferred.has_preferred_protocol

    def test_is_watching_any_assets_property(self):
        """Should identify when user is watching any assets."""
        # Arrange
        now = datetime.now(timezone.utc)

        watching_assets = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC", "USDT"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        not_watching = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=[],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert watching_assets.is_watching_any_assets
        assert not not_watching.is_watching_any_assets

    def test_is_watching_any_chains_property(self):
        """Should identify when user is watching any chains."""
        # Arrange
        now = datetime.now(timezone.utc)

        watching_chains = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum", "polygon"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        not_watching = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=[],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert watching_chains.is_watching_any_chains
        assert not not_watching.is_watching_any_chains

    def test_num_watched_assets_property(self):
        """Should count watched assets."""
        # Arrange
        now = datetime.now(timezone.utc)

        entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC", "USDT", "DAI", "WETH"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert entity.num_watched_assets == 4

    def test_num_watched_chains_property(self):
        """Should count watched chains."""
        # Arrange
        now = datetime.now(timezone.utc)

        entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=True,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum", "polygon", "arbitrum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert entity.num_watched_chains == 3

    def test_risk_tolerance_properties(self):
        """Should identify risk tolerance levels."""
        # Arrange
        now = datetime.now(timezone.utc)

        conservative = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="CONSERVATIVE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        moderate = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        aggressive = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="AGGRESSIVE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert conservative.is_conservative_risk
        assert not conservative.is_moderate_risk
        assert not conservative.is_aggressive_risk

        assert not moderate.is_conservative_risk
        assert moderate.is_moderate_risk
        assert not moderate.is_aggressive_risk

        assert not aggressive.is_conservative_risk
        assert not aggressive.is_moderate_risk
        assert aggressive.is_aggressive_risk

    def test_sort_preference_properties(self):
        """Should identify sort preferences."""
        # Arrange
        now = datetime.now(timezone.utc)

        yield_sort = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        liquidity_sort = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_LIQUIDITY",
            created_at=now,
            updated_at=now,
        )

        rate_sort = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="LOWEST_BORROW_RATE",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert yield_sort.prefers_highest_yield
        assert not yield_sort.prefers_highest_liquidity
        assert not yield_sort.prefers_lowest_borrow_rate

        assert not liquidity_sort.prefers_highest_yield
        assert liquidity_sort.prefers_highest_liquidity
        assert not liquidity_sort.prefers_lowest_borrow_rate

        assert not rate_sort.prefers_highest_yield
        assert not rate_sort.prefers_highest_liquidity
        assert rate_sort.prefers_lowest_borrow_rate

    def test_preferred_protocol_name_property(self):
        """Should return display name for preferred protocol."""
        # Arrange
        now = datetime.now(timezone.utc)

        aave_entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        compound_entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="compound_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        no_preferred = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol=None,
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert aave_entity.preferred_protocol_name == "Aave v3"
        assert compound_entity.preferred_protocol_name == "Compound v3"
        assert no_preferred.preferred_protocol_name == "None"

    def test_time_since_last_update_property(self):
        """Should calculate time since last update."""
        # Arrange
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=2)

        entity = MoneyMarketUserPreference(
            id=uuid4(),
            user_id=uuid4(),
            rate_alerts_enabled=False,
            alert_threshold_percent=Decimal("1.00"),
            watched_assets=["USDC"],
            watched_chains=["ethereum"],
            preferred_protocol="aave_v3",
            risk_tolerance="MODERATE",
            sort_by="HIGHEST_YIELD",
            created_at=past,
            updated_at=past,
        )

        # Act
        time_since = entity.time_since_last_update

        # Assert
        assert time_since.total_seconds() >= 7190  # ~2 hours (allow small timing difference)
        assert time_since.total_seconds() <= 7210
