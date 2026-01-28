"""
Tests for MoneyMarketRateComparison entity.

Tests entity creation, XOR validation, and rich domain properties.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.domain.entities.money_market.rate_comparison import (
    MoneyMarketRateComparison,
)


@pytest.mark.unit
class TestMoneyMarketRateComparison:
    """Test suite for MoneyMarketRateComparison entity."""

    def test_valid_user_comparison_creation(self):
        """Should create valid user comparison with correct attributes."""
        # Arrange
        now = datetime.now(timezone.utc)
        entity_id = uuid4()
        user_id = uuid4()

        # Act
        entity = MoneyMarketRateComparison(
            id=entity_id,
            user_id=user_id,
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=3,
            cache_hits=2,
            rpc_calls=1,
            response_time_ms=150,
            language="en",
            full_results={"protocols": ["aave_v3", "compound_v3", "morpho"]},
            created_at=now,
        )

        # Assert
        assert entity.id == entity_id
        assert entity.user_id == user_id
        assert entity.guest_session_id is None
        assert entity.chain == "ethereum"
        assert entity.asset == "USDC"
        assert entity.comparison_type == "SUPPLY"
        assert entity.num_protocols_compared == 3
        assert entity.cache_hits == 2
        assert entity.rpc_calls == 1
        assert entity.response_time_ms == 150
        assert entity.language == "en"
        assert entity.full_results == {"protocols": ["aave_v3", "compound_v3", "morpho"]}
        assert entity.created_at == now

    def test_valid_guest_comparison_creation(self):
        """Should create valid guest comparison with session ID."""
        # Arrange
        now = datetime.now(timezone.utc)
        session_id = "guest_abc123"

        # Act
        entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=None,
            guest_session_id=session_id,
            chain="polygon",
            asset="USDT",
            comparison_type="BORROW",
            num_protocols_compared=2,
            cache_hits=0,
            rpc_calls=2,
            response_time_ms=450,
            language="es",
            full_results={"protocols": ["aave_v3", "compound_v3"]},
            created_at=now,
        )

        # Assert
        assert entity.user_id is None
        assert entity.guest_session_id == session_id
        assert entity.chain == "polygon"
        assert entity.comparison_type == "BORROW"
        assert entity.language == "es"

    def test_validation_xor_both_ids_present(self):
        """Should raise error when both user_id and guest_session_id are present."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Exactly one of user_id or guest_session_id must be provided"):
            MoneyMarketRateComparison(
                id=uuid4(),
                user_id=uuid4(),  # Both present (invalid)
                guest_session_id="guest_123",  # Both present (invalid)
                chain="ethereum",
                asset="USDC",
                comparison_type="SUPPLY",
                num_protocols_compared=2,
                cache_hits=1,
                rpc_calls=1,
                response_time_ms=200,
                language="en",
                full_results={},
                created_at=datetime.now(timezone.utc),
            )

    def test_validation_xor_neither_id_present(self):
        """Should raise error when neither user_id nor guest_session_id are present."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Exactly one of user_id or guest_session_id must be provided"):
            MoneyMarketRateComparison(
                id=uuid4(),
                user_id=None,  # Neither present (invalid)
                guest_session_id=None,  # Neither present (invalid)
                chain="ethereum",
                asset="USDC",
                comparison_type="SUPPLY",
                num_protocols_compared=2,
                cache_hits=1,
                rpc_calls=1,
                response_time_ms=200,
                language="en",
                full_results={},
                created_at=datetime.now(timezone.utc),
            )

    def test_validation_invalid_comparison_type(self):
        """Should raise error for invalid comparison type."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Invalid comparison_type"):
            MoneyMarketRateComparison(
                id=uuid4(),
                user_id=uuid4(),
                guest_session_id=None,
                chain="ethereum",
                asset="USDC",
                comparison_type="INVALID_TYPE",  # Invalid
                num_protocols_compared=2,
                cache_hits=1,
                rpc_calls=1,
                response_time_ms=200,
                language="en",
                full_results={},
                created_at=datetime.now(timezone.utc),
            )

    def test_validation_negative_num_protocols(self):
        """Should raise error for negative protocol count."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="num_protocols_compared must be positive"):
            MoneyMarketRateComparison(
                id=uuid4(),
                user_id=uuid4(),
                guest_session_id=None,
                chain="ethereum",
                asset="USDC",
                comparison_type="SUPPLY",
                num_protocols_compared=-1,  # Negative
                cache_hits=1,
                rpc_calls=1,
                response_time_ms=200,
                language="en",
                full_results={},
                created_at=datetime.now(timezone.utc),
            )

    def test_validation_negative_cache_hits(self):
        """Should raise error for negative cache hits."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="cache_hits cannot be negative"):
            MoneyMarketRateComparison(
                id=uuid4(),
                user_id=uuid4(),
                guest_session_id=None,
                chain="ethereum",
                asset="USDC",
                comparison_type="SUPPLY",
                num_protocols_compared=2,
                cache_hits=-1,  # Negative
                rpc_calls=1,
                response_time_ms=200,
                language="en",
                full_results={},
                created_at=datetime.now(timezone.utc),
            )

    def test_validation_negative_rpc_calls(self):
        """Should raise error for negative RPC calls."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="rpc_calls cannot be negative"):
            MoneyMarketRateComparison(
                id=uuid4(),
                user_id=uuid4(),
                guest_session_id=None,
                chain="ethereum",
                asset="USDC",
                comparison_type="SUPPLY",
                num_protocols_compared=2,
                cache_hits=1,
                rpc_calls=-1,  # Negative
                response_time_ms=200,
                language="en",
                full_results={},
                created_at=datetime.now(timezone.utc),
            )

    def test_validation_negative_response_time(self):
        """Should raise error for negative response time."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="response_time_ms cannot be negative"):
            MoneyMarketRateComparison(
                id=uuid4(),
                user_id=uuid4(),
                guest_session_id=None,
                chain="ethereum",
                asset="USDC",
                comparison_type="SUPPLY",
                num_protocols_compared=2,
                cache_hits=1,
                rpc_calls=1,
                response_time_ms=-50,  # Negative
                language="en",
                full_results={},
                created_at=datetime.now(timezone.utc),
            )

    def test_validation_invalid_language_code(self):
        """Should raise error for invalid language code."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Invalid language code"):
            MoneyMarketRateComparison(
                id=uuid4(),
                user_id=uuid4(),
                guest_session_id=None,
                chain="ethereum",
                asset="USDC",
                comparison_type="SUPPLY",
                num_protocols_compared=2,
                cache_hits=1,
                rpc_calls=1,
                response_time_ms=200,
                language="invalid",  # Invalid
                full_results={},
                created_at=datetime.now(timezone.utc),
            )

    def test_is_guest_comparison_property(self):
        """Should identify guest comparisons."""
        # Arrange
        user_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=1,
            rpc_calls=1,
            response_time_ms=200,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        guest_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=None,
            guest_session_id="guest_123",
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=1,
            rpc_calls=1,
            response_time_ms=200,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert not user_entity.is_guest_comparison
        assert guest_entity.is_guest_comparison

    def test_cache_hit_rate_property(self):
        """Should calculate cache hit rate percentage."""
        # Arrange
        entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=4,
            cache_hits=3,
            rpc_calls=1,
            response_time_ms=150,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert entity.cache_hit_rate == Decimal("75.0")  # 3/4 = 75%

    def test_cache_hit_rate_zero_total(self):
        """Should return 0% cache hit rate when no operations."""
        # Arrange
        entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=0,
            cache_hits=0,
            rpc_calls=0,
            response_time_ms=0,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert entity.cache_hit_rate == Decimal("0")

    def test_is_fast_response_property(self):
        """Should identify fast responses (< 200ms)."""
        # Arrange
        fast_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=2,
            rpc_calls=0,
            response_time_ms=150,  # Fast
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        slow_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=0,
            rpc_calls=2,
            response_time_ms=500,  # Slow
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert fast_entity.is_fast_response
        assert not slow_entity.is_fast_response

    def test_is_slow_response_property(self):
        """Should identify slow responses (> 1000ms)."""
        # Arrange
        fast_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=2,
            rpc_calls=0,
            response_time_ms=150,  # Not slow
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        slow_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=3,
            cache_hits=0,
            rpc_calls=3,
            response_time_ms=1500,  # Slow
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert not fast_entity.is_slow_response
        assert slow_entity.is_slow_response

    def test_is_fully_cached_property(self):
        """Should identify fully cached responses."""
        # Arrange
        fully_cached = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=3,
            cache_hits=3,
            rpc_calls=0,  # No RPC calls
            response_time_ms=100,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        partially_cached = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=3,
            cache_hits=2,
            rpc_calls=1,  # Had RPC calls
            response_time_ms=200,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert fully_cached.is_fully_cached
        assert not partially_cached.is_fully_cached

    def test_is_stablecoin_property(self):
        """Should identify stablecoin comparisons."""
        # Arrange
        stablecoin_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",  # Stablecoin
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=1,
            rpc_calls=1,
            response_time_ms=200,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        non_stablecoin_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="WETH",  # Not stablecoin
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=1,
            rpc_calls=1,
            response_time_ms=200,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert stablecoin_entity.is_stablecoin
        assert not non_stablecoin_entity.is_stablecoin

    def test_is_supply_comparison_property(self):
        """Should identify supply comparisons."""
        # Arrange
        supply_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=1,
            rpc_calls=1,
            response_time_ms=200,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        borrow_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="BORROW",
            num_protocols_compared=2,
            cache_hits=1,
            rpc_calls=1,
            response_time_ms=200,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert supply_entity.is_supply_comparison
        assert not borrow_entity.is_supply_comparison

    def test_is_borrow_comparison_property(self):
        """Should identify borrow comparisons."""
        # Arrange
        supply_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=1,
            rpc_calls=1,
            response_time_ms=200,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        borrow_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="BORROW",
            num_protocols_compared=2,
            cache_hits=1,
            rpc_calls=1,
            response_time_ms=200,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert not supply_entity.is_borrow_comparison
        assert borrow_entity.is_borrow_comparison

    def test_language_display_name_property(self):
        """Should return display name for language code."""
        # Arrange
        en_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=1,
            rpc_calls=1,
            response_time_ms=200,
            language="en",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        es_entity = MoneyMarketRateComparison(
            id=uuid4(),
            user_id=uuid4(),
            guest_session_id=None,
            chain="ethereum",
            asset="USDC",
            comparison_type="SUPPLY",
            num_protocols_compared=2,
            cache_hits=1,
            rpc_calls=1,
            response_time_ms=200,
            language="es",
            full_results={},
            created_at=datetime.now(timezone.utc),
        )

        # Act & Assert
        assert en_entity.language_display_name == "English"
        assert es_entity.language_display_name == "Spanish"
