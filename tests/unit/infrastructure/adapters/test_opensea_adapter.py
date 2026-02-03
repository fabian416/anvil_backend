"""
Unit tests for OpenSea NFT marketplace adapter.

Tests the OpenSeaAdapter implementation with mocked OpenSeaClient.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_opensea_client():
    """Create a mocked OpenSeaClient."""
    client = MagicMock()
    client.get_nfts_by_account = AsyncMock()
    client.get_collection = AsyncMock()
    client.get_collection_stats = AsyncMock()
    client.get_nft = AsyncMock()
    client.get_listings = AsyncMock()
    client.get_floor_price = AsyncMock()
    return client


@pytest.fixture
def mock_cache():
    """Create a mocked ExternalAPICache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.mark.unit
class TestOpenSeaAdapterStructure:
    """Tests for OpenSeaAdapter structure and protocol compliance."""

    def test_opensea_adapter_imports(self):
        """Test OpenSeaAdapter can be imported."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter

        assert OpenSeaAdapter is not None

    def test_opensea_adapter_implements_gateway(self):
        """Test OpenSeaAdapter implements NFTMarketplaceGateway protocol."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter

        # Verify it has all required methods from the protocol
        assert hasattr(OpenSeaAdapter, "get_nfts_by_owner")
        assert hasattr(OpenSeaAdapter, "get_collection")
        assert hasattr(OpenSeaAdapter, "get_collection_stats")
        assert hasattr(OpenSeaAdapter, "get_nft")
        assert hasattr(OpenSeaAdapter, "get_listings")
        assert hasattr(OpenSeaAdapter, "get_floor_price")

    def test_opensea_adapter_init(self, mock_opensea_client, mock_cache):
        """Test OpenSeaAdapter can be initialized."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter

        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)
        assert adapter is not None


@pytest.mark.unit
class TestOpenSeaAdapterGetNFTsByOwner:
    """Tests for get_nfts_by_owner method."""

    @pytest.mark.asyncio
    async def test_get_nfts_by_owner_validates_address(
        self, mock_opensea_client, mock_cache
    ):
        """Test get_nfts_by_owner validates Ethereum address format."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter
        from app.domain.exceptions.nft import InvalidAddressError

        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        with pytest.raises(InvalidAddressError):
            await adapter.get_nfts_by_owner("invalid-address")

    @pytest.mark.asyncio
    async def test_get_nfts_by_owner_returns_list(
        self, mock_opensea_client, mock_cache
    ):
        """Test get_nfts_by_owner returns a list."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter

        mock_opensea_client.get_nfts_by_account.return_value = []
        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        result = await adapter.get_nfts_by_owner(
            "0x1234567890123456789012345678901234567890"
        )

        assert isinstance(result, list)


@pytest.mark.unit
class TestOpenSeaAdapterGetCollection:
    """Tests for get_collection method."""

    @pytest.mark.asyncio
    async def test_get_collection_calls_client(self, mock_opensea_client, mock_cache):
        """Test get_collection calls the client."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter

        mock_opensea_client.get_collection.return_value = MagicMock(
            slug="boredapeyachtclub",
            name="Bored Ape Yacht Club",
            description="BAYC",
            total_supply=10000,
        )
        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        await adapter.get_collection("boredapeyachtclub")

        mock_opensea_client.get_collection.assert_called()

    @pytest.mark.asyncio
    async def test_get_collection_not_found(self, mock_opensea_client, mock_cache):
        """Test get_collection returns None for invalid slug."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter

        mock_opensea_client.get_collection.return_value = None
        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        result = await adapter.get_collection("invalid-collection")

        assert result is None


@pytest.mark.unit
class TestOpenSeaAdapterGetCollectionStats:
    """Tests for get_collection_stats method."""

    @pytest.mark.asyncio
    async def test_get_collection_stats_calls_client(
        self, mock_opensea_client, mock_cache
    ):
        """Test get_collection_stats calls the client."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter
        from app.infrastructure.adapters.external.opensea_client import CollectionStats
        from decimal import Decimal

        # Use proper CollectionStats dataclass with all required fields
        mock_opensea_client.get_collection_stats.return_value = CollectionStats(
            total_supply=10000,
            num_owners=5000,
            slug="boredapeyachtclub",
            floor_price=Decimal("25.5"),
            floor_price_usd=Decimal("51000"),
            floor_price_symbol="ETH",
            total_volume=Decimal("500000"),
            total_sales=100000,
            average_price=Decimal("5"),
            market_cap=Decimal("255000"),
            one_day_volume=Decimal("1000"),
            one_day_change=Decimal("5.5"),
            seven_day_volume=Decimal("7000"),
            seven_day_change=Decimal("2.5"),
        )
        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        await adapter.get_collection_stats("boredapeyachtclub")

        mock_opensea_client.get_collection_stats.assert_called()


@pytest.mark.unit
class TestOpenSeaAdapterGetNFT:
    """Tests for get_nft method."""

    @pytest.mark.asyncio
    async def test_get_nft_calls_client(self, mock_opensea_client, mock_cache):
        """Test get_nft calls the client."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter
        from app.infrastructure.adapters.external.opensea_client import NFTAsset
        from decimal import Decimal

        # Use proper NFTAsset dataclass with all fields
        mock_opensea_client.get_nft.return_value = NFTAsset(
            identifier="1234",
            collection="boredapeyachtclub",
            contract="0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
            token_standard="ERC721",
            name="Bored Ape #1234",
            description="A Bored Ape from the BAYC collection",
            image_url="https://example.com/ape.png",
            rarity_rank=1000,
            last_sale_price=Decimal("50.5"),
            last_sale_currency="ETH",
            traits=[],
        )
        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        await adapter.get_nft(
            "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
            "1234",
        )

        mock_opensea_client.get_nft.assert_called()

    @pytest.mark.asyncio
    async def test_get_nft_not_found(self, mock_opensea_client, mock_cache):
        """Test get_nft returns None for invalid NFT."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter

        mock_opensea_client.get_nft.return_value = None
        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        result = await adapter.get_nft("0x123", "invalid")

        assert result is None


@pytest.mark.unit
class TestOpenSeaAdapterGetListings:
    """Tests for get_listings method."""

    @pytest.mark.asyncio
    async def test_get_listings_calls_client(self, mock_opensea_client, mock_cache):
        """Test get_listings calls the client."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter

        mock_opensea_client.get_listings.return_value = []
        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        await adapter.get_listings("boredapeyachtclub")

        mock_opensea_client.get_listings.assert_called()

    @pytest.mark.asyncio
    async def test_get_listings_returns_list(self, mock_opensea_client, mock_cache):
        """Test get_listings returns a list."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter

        mock_opensea_client.get_listings.return_value = []
        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        result = await adapter.get_listings("boredapeyachtclub")

        assert isinstance(result, list)


@pytest.mark.unit
class TestOpenSeaAdapterGetFloorPrice:
    """Tests for get_floor_price method."""

    @pytest.mark.asyncio
    async def test_get_floor_price_calls_client(self, mock_opensea_client, mock_cache):
        """Test get_floor_price calls the client by first calling get_collection_stats."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter
        from app.infrastructure.adapters.external.opensea_client import CollectionStats
        from decimal import Decimal

        # get_floor_price internally calls get_collection_stats
        mock_opensea_client.get_collection_stats.return_value = CollectionStats(
            total_supply=10000,
            num_owners=5000,
            slug="boredapeyachtclub",
            floor_price=Decimal("25.5"),
            floor_price_usd=Decimal("51000"),
            floor_price_symbol="ETH",
            total_volume=Decimal("500000"),
            total_sales=100000,
            average_price=Decimal("5"),
            market_cap=Decimal("255000"),
            one_day_volume=Decimal("1000"),
            one_day_change=Decimal("0"),
            seven_day_volume=Decimal("7000"),
            seven_day_change=Decimal("0"),
        )
        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        result = await adapter.get_floor_price("boredapeyachtclub")

        # Verify get_collection_stats was called (which get_floor_price uses)
        mock_opensea_client.get_collection_stats.assert_called()
        assert result is not None


@pytest.mark.unit
class TestOpenSeaAdapterErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_client_error_wrapped(self, mock_opensea_client, mock_cache):
        """Test client errors are wrapped as OpenSeaAPIError."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter
        from app.domain.exceptions.nft import OpenSeaAPIError

        mock_opensea_client.get_collection.side_effect = Exception("API Error")
        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        with pytest.raises(OpenSeaAPIError):
            await adapter.get_collection("test")

    @pytest.mark.asyncio
    async def test_invalid_address_detected(self, mock_opensea_client, mock_cache):
        """Test invalid addresses are detected before API call."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter
        from app.domain.exceptions.nft import InvalidAddressError

        adapter = OpenSeaAdapter(client=mock_opensea_client, cache=mock_cache)

        with pytest.raises(InvalidAddressError):
            await adapter.get_nfts_by_owner("not-an-address")

        # Should not call API
        mock_opensea_client.get_nfts_by_account.assert_not_called()


@pytest.mark.unit
class TestNFTExceptions:
    """Tests for NFT exceptions."""

    def test_nft_error_has_error_code(self):
        """Test NFTError has error_code."""
        from app.domain.exceptions.nft import NFTError

        assert hasattr(NFTError, "error_code")

    def test_collection_not_found_error(self):
        """Test CollectionNotFoundError."""
        from app.domain.exceptions.nft import CollectionNotFoundError

        error = CollectionNotFoundError("invalid-collection")

        assert error.error_code == "NFT_COLLECTION_NOT_FOUND"
        assert "invalid-collection" in str(error)

    def test_invalid_address_error(self):
        """Test InvalidAddressError."""
        from app.domain.exceptions.nft import InvalidAddressError

        error = InvalidAddressError("invalid-address")

        assert error.error_code == "NFT_INVALID_ADDRESS"
        assert "invalid-address" in str(error)

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        from app.domain.exceptions.nft import RateLimitError

        error = RateLimitError(retry_after=60)

        assert error.error_code == "NFT_RATE_LIMIT"
        assert error.retry_after == 60
