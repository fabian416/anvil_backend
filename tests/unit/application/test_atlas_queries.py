"""
Unit tests for atlas query services.

Tests country, city, and state search query services.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4


@pytest.mark.unit
class TestSearchCountriesQueryService:
    """Tests for SearchCountriesQueryService."""

    def test_search_countries_request_exists(self):
        """Test SearchCountriesRequest dataclass exists."""
        from app.application.atlas.queries import SearchCountriesRequest

        assert SearchCountriesRequest is not None

    def test_search_countries_response_exists(self):
        """Test SearchCountriesResponse dataclass exists."""
        from app.application.atlas.queries import SearchCountriesResponse

        assert SearchCountriesResponse is not None

    def test_search_countries_service_exists(self):
        """Test SearchCountriesQueryService exists."""
        from app.application.atlas.queries import SearchCountriesQueryService

        assert SearchCountriesQueryService is not None

    def test_search_countries_service_instantiation(self):
        """Test service can be instantiated."""
        from app.application.atlas.queries import SearchCountriesQueryService

        mock_reader = AsyncMock()
        service = SearchCountriesQueryService(mock_reader)

        assert service is not None
        assert service._country_reader is mock_reader

    @pytest.mark.asyncio
    async def test_search_countries_execute(self):
        """Test execute returns SearchCountriesResponse."""
        from app.application.atlas.queries import (
            SearchCountriesQueryService,
            SearchCountriesRequest,
        )
        from app.application.atlas.query_models import CountryQueryModel

        # Arrange
        mock_reader = AsyncMock()
        mock_reader.search.return_value = (
            [
                CountryQueryModel(
                    id=1,
                    country_id=1,
                    name="United States",
                    iso2="US",
                    iso3="USA",
                    currency="USD",
                    region="Americas",
                    subregion="Northern America",
                )
            ],
            1,
        )

        service = SearchCountriesQueryService(mock_reader)
        request = SearchCountriesRequest(
            name="United",
            iso2=None,
            iso3=None,
            region=None,
            subregion=None,
            currency=None,
            limit=10,
            offset=0,
        )

        # Act
        response = await service.execute(request)

        # Assert
        assert response is not None
        assert len(response.data) == 1
        assert response.total == 1
        assert response.data[0].name == "United States"
        mock_reader.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_countries_with_filters(self):
        """Test search with multiple filters."""
        from app.application.atlas.queries import (
            SearchCountriesQueryService,
            SearchCountriesRequest,
        )

        # Arrange
        mock_reader = AsyncMock()
        mock_reader.search.return_value = ([], 0)

        service = SearchCountriesQueryService(mock_reader)
        request = SearchCountriesRequest(
            name="France",
            iso2="FR",
            iso3="FRA",
            region="Europe",
            subregion="Western Europe",
            currency="EUR",
            limit=5,
            offset=0,
        )

        # Act
        response = await service.execute(request)

        # Assert
        mock_reader.search.assert_called_once_with(
            name="France",
            iso2="FR",
            iso3="FRA",
            region="Europe",
            subregion="Western Europe",
            currency="EUR",
            limit=5,
            offset=0,
        )
        assert response.data == []
        assert response.total == 0


@pytest.mark.unit
class TestSearchCitiesQueryService:
    """Tests for SearchCitiesQueryService."""

    def test_search_cities_request_exists(self):
        """Test SearchCitiesRequest dataclass exists."""
        from app.application.atlas.queries import SearchCitiesRequest

        assert SearchCitiesRequest is not None

    def test_search_cities_response_exists(self):
        """Test SearchCitiesResponse dataclass exists."""
        from app.application.atlas.queries import SearchCitiesResponse

        assert SearchCitiesResponse is not None

    def test_search_cities_service_exists(self):
        """Test SearchCitiesQueryService exists."""
        from app.application.atlas.queries import SearchCitiesQueryService

        assert SearchCitiesQueryService is not None

    def test_search_cities_service_instantiation(self):
        """Test service can be instantiated."""
        from app.application.atlas.queries import SearchCitiesQueryService

        mock_reader = AsyncMock()
        service = SearchCitiesQueryService(mock_reader)

        assert service is not None
        assert service._city_reader is mock_reader

    @pytest.mark.asyncio
    async def test_search_cities_execute(self):
        """Test execute returns SearchCitiesResponse."""
        from app.application.atlas.queries import (
            SearchCitiesQueryService,
            SearchCitiesRequest,
        )
        from app.application.atlas.query_models import CityQueryModel

        # Arrange
        mock_reader = AsyncMock()
        mock_reader.search.return_value = (
            [
                CityQueryModel(
                    id=1,
                    city_id=1,
                    name="New York",
                    state_code="NY",
                    state_name="New York",
                    state_id="NY001",
                    country_id=1,
                    country_code="US",
                    country_name="United States",
                )
            ],
            1,
        )

        service = SearchCitiesQueryService(mock_reader)
        request = SearchCitiesRequest(
            name="New York",
            country_id=None,
            state_id=None,
            state_code=None,
            state_name=None,
            country_code=None,
            wiki_data_id=None,
            limit=10,
            offset=0,
        )

        # Act
        response = await service.execute(request)

        # Assert
        assert response is not None
        assert len(response.data) == 1
        assert response.total == 1
        assert response.data[0].name == "New York"
        mock_reader.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_cities_with_filters(self):
        """Test search cities with multiple filters."""
        from app.application.atlas.queries import (
            SearchCitiesQueryService,
            SearchCitiesRequest,
        )

        # Arrange
        mock_reader = AsyncMock()
        mock_reader.search.return_value = ([], 0)

        service = SearchCitiesQueryService(mock_reader)
        request = SearchCitiesRequest(
            name="Paris",
            country_id=1,
            state_id="75",
            state_code="IDF",
            state_name="Île-de-France",
            country_code="FR",
            wiki_data_id="Q90",
            limit=20,
            offset=10,
        )

        # Act
        response = await service.execute(request)

        # Assert
        mock_reader.search.assert_called_once_with(
            name="Paris",
            country_id=1,
            state_id="75",
            state_code="IDF",
            state_name="Île-de-France",
            country_code="FR",
            wiki_data_id="Q90",
            limit=20,
            offset=10,
        )


@pytest.mark.unit
class TestListStatesByCountryQueryService:
    """Tests for ListStatesByCountryQueryService."""

    def test_list_states_by_country_request_exists(self):
        """Test ListStatesByCountryRequest dataclass exists."""
        from app.application.atlas.queries import ListStatesByCountryRequest

        assert ListStatesByCountryRequest is not None

    def test_list_states_by_country_service_exists(self):
        """Test ListStatesByCountryQueryService exists."""
        from app.application.atlas.queries import ListStatesByCountryQueryService

        assert ListStatesByCountryQueryService is not None

    def test_list_states_by_country_service_instantiation(self):
        """Test service can be instantiated."""
        from app.application.atlas.queries import ListStatesByCountryQueryService

        mock_reader = AsyncMock()
        service = ListStatesByCountryQueryService(mock_reader)

        assert service is not None
        assert service._city_reader is mock_reader

    @pytest.mark.asyncio
    async def test_list_states_by_country_execute(self):
        """Test execute returns list of StateQueryModel."""
        from app.application.atlas.queries import (
            ListStatesByCountryQueryService,
            ListStatesByCountryRequest,
        )
        from app.application.atlas.query_models import StateQueryModel

        # Arrange
        mock_reader = AsyncMock()
        mock_reader.list_states_by_country.return_value = [
            StateQueryModel(
                state_id="CA001",
                state_name="California",
                state_code="CA",
                country_id=1,
                country_code="US",
                country_name="United States",
            ),
            StateQueryModel(
                state_id="NY001",
                state_name="New York",
                state_code="NY",
                country_id=1,
                country_code="US",
                country_name="United States",
            ),
        ]

        service = ListStatesByCountryQueryService(mock_reader)
        request = ListStatesByCountryRequest(country_id=1)

        # Act
        response = await service.execute(request)

        # Assert
        assert response is not None
        assert len(response) == 2
        assert response[0].state_name == "California"
        assert response[1].state_name == "New York"
        mock_reader.list_states_by_country.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_states_by_country_empty_result(self):
        """Test execute with country having no states."""
        from app.application.atlas.queries import (
            ListStatesByCountryQueryService,
            ListStatesByCountryRequest,
        )

        # Arrange
        mock_reader = AsyncMock()
        mock_reader.list_states_by_country.return_value = []

        service = ListStatesByCountryQueryService(mock_reader)
        request = ListStatesByCountryRequest(country_id=999)

        # Act
        response = await service.execute(request)

        # Assert
        assert response == []
        mock_reader.list_states_by_country.assert_called_once_with(999)


@pytest.mark.unit
class TestAtlasRequestValidation:
    """Tests for atlas request validation and structure."""

    def test_search_countries_request_fields(self):
        """Test SearchCountriesRequest has correct fields."""
        from app.application.atlas.queries import SearchCountriesRequest

        request = SearchCountriesRequest(
            name="Test",
            iso2="TS",
            iso3="TST",
            region="Test Region",
            subregion="Test Subregion",
            currency="TSD",
            limit=10,
            offset=0,
        )

        assert request.name == "Test"
        assert request.iso2 == "TS"
        assert request.iso3 == "TST"
        assert request.region == "Test Region"
        assert request.subregion == "Test Subregion"
        assert request.currency == "TSD"
        assert request.limit == 10
        assert request.offset == 0

    def test_search_countries_request_frozen(self):
        """Test SearchCountriesRequest is frozen."""
        from app.application.atlas.queries import SearchCountriesRequest

        request = SearchCountriesRequest(
            name="Test",
            iso2=None,
            iso3=None,
            region=None,
            subregion=None,
            currency=None,
            limit=10,
            offset=0,
        )

        # Should not be able to modify
        with pytest.raises(AttributeError):
            request.name = "Modified"

    def test_search_cities_request_fields(self):
        """Test SearchCitiesRequest has correct fields."""
        from app.application.atlas.queries import SearchCitiesRequest

        request = SearchCitiesRequest(
            name="Test City",
            country_id=1,
            state_id="123",
            state_code="TC",
            state_name="Test State",
            country_code="TS",
            wiki_data_id="Q123",
            limit=20,
            offset=5,
        )

        assert request.name == "Test City"
        assert request.country_id == 1
        assert request.state_id == "123"
        assert request.state_code == "TC"
        assert request.state_name == "Test State"
        assert request.country_code == "TS"
        assert request.wiki_data_id == "Q123"
        assert request.limit == 20
        assert request.offset == 5

    def test_list_states_by_country_request_fields(self):
        """Test ListStatesByCountryRequest has correct fields."""
        from app.application.atlas.queries import ListStatesByCountryRequest

        request = ListStatesByCountryRequest(country_id=42)

        assert request.country_id == 42
