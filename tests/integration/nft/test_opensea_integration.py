"""
Integration tests for OpenSea NFT marketplace API.

Tests the structure and protocol compliance of NFT integrations.
"""

import pytest
from decimal import Decimal


@pytest.mark.integration
class TestOpenSeaRouterIntegration:
    """Integration tests for OpenSea router."""

    def test_opensea_router_exists(self):
        """Test OpenSea router can be created."""
        from app.presentation.http.controllers.nft.opensea_router import create_opensea_router
        
        router = create_opensea_router()
        assert router is not None

    def test_opensea_router_has_routes(self):
        """Test OpenSea router has expected routes."""
        from app.presentation.http.controllers.nft.opensea_router import create_opensea_router
        
        router = create_opensea_router()
        routes = [r.path for r in router.routes]
        
        assert len(routes) > 0


@pytest.mark.integration
class TestNFTGatewayIntegration:
    """Integration tests for NFTMarketplaceGateway."""

    def test_nft_gateway_port_exists(self):
        """Test NFTMarketplaceGateway port is defined."""
        from app.domain.ports.nft_marketplace_gateway import NFTMarketplaceGateway
        
        assert NFTMarketplaceGateway is not None

    def test_opensea_adapter_exists(self):
        """Test OpenSeaAdapter exists."""
        from app.infrastructure.adapters.external.opensea_adapter import OpenSeaAdapter
        
        assert OpenSeaAdapter is not None


@pytest.mark.integration
class TestNFTEntitiesIntegration:
    """Integration tests for NFT domain entities."""

    def test_nft_asset_entity_exists(self):
        """Test NFTAsset entity exists."""
        from app.domain.entities.nft.nft_asset import NFTAsset
        
        assert NFTAsset is not None

    def test_nft_collection_entity_exists(self):
        """Test NFTCollection entity exists."""
        from app.domain.entities.nft.nft_collection import NFTCollection
        
        assert NFTCollection is not None


@pytest.mark.integration
class TestNFTValueObjectsIntegration:
    """Integration tests for NFT value objects."""

    def test_collection_stats_vo_exists(self):
        """Test CollectionStats value object exists."""
        from app.domain.value_objects.nft.collection_stats import CollectionStats
        
        assert CollectionStats is not None

    def test_nft_trait_vo_exists(self):
        """Test NFTTrait value object exists."""
        from app.domain.value_objects.nft.nft_trait import NFTTrait
        
        assert NFTTrait is not None

    def test_nft_listing_vo_exists(self):
        """Test NFTListing value object exists."""
        from app.domain.value_objects.nft.nft_listing import NFTListing
        
        assert NFTListing is not None


@pytest.mark.integration
class TestNFTExceptionsIntegration:
    """Integration tests for NFT exceptions."""

    def test_nft_exceptions_defined(self):
        """Test NFT exceptions are defined."""
        from app.domain.exceptions.nft import (
            NFTError,
            CollectionNotFoundError,
            NFTNotFoundError,
            InvalidAddressError,
            OpenSeaAPIError,
            RateLimitError,
        )
        
        assert NFTError is not None
        assert CollectionNotFoundError is not None
        assert NFTNotFoundError is not None
        assert InvalidAddressError is not None
        assert OpenSeaAPIError is not None
        assert RateLimitError is not None

    def test_collection_not_found_error_code(self):
        """Test CollectionNotFoundError has correct error code."""
        from app.domain.exceptions.nft import CollectionNotFoundError
        
        error = CollectionNotFoundError("test-collection")
        
        assert error.error_code == "NFT_COLLECTION_NOT_FOUND"
        assert "test-collection" in str(error)

    def test_nft_not_found_error_code(self):
        """Test NFTNotFoundError has correct error code."""
        from app.domain.exceptions.nft import NFTNotFoundError
        
        error = NFTNotFoundError("0x123", "1234")
        
        assert error.error_code == "NFT_NOT_FOUND"

    def test_invalid_address_error_code(self):
        """Test InvalidAddressError has correct error code."""
        from app.domain.exceptions.nft import InvalidAddressError
        
        error = InvalidAddressError("invalid-address")
        
        assert error.error_code == "NFT_INVALID_ADDRESS"

    def test_rate_limit_error_code(self):
        """Test RateLimitError has correct error code."""
        from app.domain.exceptions.nft import RateLimitError
        
        error = RateLimitError(retry_after=60)
        
        assert error.error_code == "NFT_RATE_LIMIT"
        assert error.retry_after == 60
