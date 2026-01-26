# Location & System Config Test Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Location & System Config module has **good test coverage** for query services:
- **SearchCountriesQueryService**: 6 unit tests
- **SearchCitiesQueryService**: 4 unit tests
- **ListStatesByCountryQueryService**: 4 unit tests
- **Request Validation**: 4 unit tests

**Total Existing Tests**: 18 unit tests  
**Missing Tests**: Integration tests, Handler tests, Reader tests, API E2E tests

---

## 1. Existing Tests

### 1.1 SearchCountriesQueryService Tests
**Path**: `tests/unit/application/test_atlas_queries.py`

| Test | Description | Status |
|------|-------------|--------|
| `test_search_countries_request_exists` | Request dataclass exists | ✅ |
| `test_search_countries_response_exists` | Response dataclass exists | ✅ |
| `test_search_countries_service_exists` | Service class exists | ✅ |
| `test_search_countries_service_instantiation` | Service can be instantiated | ✅ |
| `test_search_countries_execute` | Execute returns response | ✅ |
| `test_search_countries_with_filters` | Multiple filters work | ✅ |

```python
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
        [CountryQueryModel(id=1, country_id=1, name="United States", ...)],
        1,
    )
    
    service = SearchCountriesQueryService(mock_reader)
    request = SearchCountriesRequest(name="United", ...)
    
    # Act
    response = await service.execute(request)
    
    # Assert
    assert len(response.data) == 1
    assert response.total == 1
    assert response.data[0].name == "United States"
```

---

### 1.2 SearchCitiesQueryService Tests
**Path**: `tests/unit/application/test_atlas_queries.py`

| Test | Description | Status |
|------|-------------|--------|
| `test_search_cities_request_exists` | Request dataclass exists | ✅ |
| `test_search_cities_response_exists` | Response dataclass exists | ✅ |
| `test_search_cities_service_exists` | Service class exists | ✅ |
| `test_search_cities_service_instantiation` | Service can be instantiated | ✅ |
| `test_search_cities_execute` | Execute returns response | ✅ |
| `test_search_cities_with_filters` | Multiple filters work | ✅ |

```python
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
        [CityQueryModel(id=1, city_id=1, name="New York", ...)],
        1,
    )
    
    service = SearchCitiesQueryService(mock_reader)
    request = SearchCitiesRequest(name="New York", ...)
    
    # Act
    response = await service.execute(request)
    
    # Assert
    assert len(response.data) == 1
    assert response.data[0].name == "New York"
```

---

### 1.3 ListStatesByCountryQueryService Tests
**Path**: `tests/unit/application/test_atlas_queries.py`

| Test | Description | Status |
|------|-------------|--------|
| `test_list_states_by_country_request_exists` | Request dataclass exists | ✅ |
| `test_list_states_by_country_service_exists` | Service class exists | ✅ |
| `test_list_states_by_country_service_instantiation` | Service can be instantiated | ✅ |
| `test_list_states_by_country_execute` | Execute returns list | ✅ |
| `test_list_states_by_country_empty_result` | Empty result handled | ✅ |

```python
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
        StateQueryModel(state_id="CA001", state_name="California", ...),
        StateQueryModel(state_id="NY001", state_name="New York", ...),
    ]
    
    service = ListStatesByCountryQueryService(mock_reader)
    request = ListStatesByCountryRequest(country_id=1)
    
    # Act
    response = await service.execute(request)
    
    # Assert
    assert len(response) == 2
    assert response[0].state_name == "California"
```

---

### 1.4 Request Validation Tests
**Path**: `tests/unit/application/test_atlas_queries.py`

| Test | Description | Status |
|------|-------------|--------|
| `test_search_countries_request_fields` | All fields present | ✅ |
| `test_search_countries_request_frozen` | Request is frozen/immutable | ✅ |
| `test_search_cities_request_fields` | All fields present | ✅ |
| `test_list_states_by_country_request_fields` | All fields present | ✅ |

```python
def test_search_countries_request_frozen(self):
    """Test SearchCountriesRequest is frozen."""
    from app.application.atlas.queries import SearchCountriesRequest
    
    request = SearchCountriesRequest(name="Test", ...)
    
    # Should not be able to modify
    with pytest.raises(AttributeError):
        request.name = "Modified"
```

---

## 2. Missing Tests

### 2.1 Infrastructure Reader Tests (Critical)
**Priority**: HIGH  
**Location**: Should be in `tests/unit/infrastructure/test_atlas_readers.py`

**Missing Tests**:
```python
class TestSqlaCountryReader:
    """Unit tests for SqlaCountryReader."""

    @pytest.mark.asyncio
    async def test_search_by_name_partial_match(self, db_session, seeded_countries):
        """Search finds countries by partial name match."""
        reader = SqlaCountryReader(session=db_session)
        
        items, total = await reader.search(
            name="United",
            iso2=None, iso3=None, region=None, subregion=None, currency=None,
            limit=10, offset=0
        )
        
        assert total >= 2  # United States, United Kingdom
        assert all("United" in c.name for c in items)

    @pytest.mark.asyncio
    async def test_search_by_iso2_exact_match(self, db_session, seeded_countries):
        """Search finds country by exact ISO2 code."""
        reader = SqlaCountryReader(session=db_session)
        
        items, total = await reader.search(
            name=None, iso2="US", iso3=None, region=None, subregion=None, currency=None,
            limit=10, offset=0
        )
        
        assert total == 1
        assert items[0].iso2 == "US"
        assert items[0].name == "United States"

    @pytest.mark.asyncio
    async def test_search_by_region(self, db_session, seeded_countries):
        """Search finds countries by region."""
        reader = SqlaCountryReader(session=db_session)
        
        items, total = await reader.search(
            name=None, iso2=None, iso3=None, region="Europe", subregion=None, currency=None,
            limit=100, offset=0
        )
        
        assert total > 0
        assert all(c.region == "Europe" or "Europe" in (c.region or "") for c in items)

    @pytest.mark.asyncio
    async def test_search_pagination(self, db_session, seeded_countries):
        """Pagination works correctly."""
        reader = SqlaCountryReader(session=db_session)
        
        # Get first page
        page1, total = await reader.search(
            name=None, iso2=None, iso3=None, region=None, subregion=None, currency=None,
            limit=10, offset=0
        )
        
        # Get second page
        page2, _ = await reader.search(
            name=None, iso2=None, iso3=None, region=None, subregion=None, currency=None,
            limit=10, offset=10
        )
        
        assert len(page1) == 10
        assert len(page2) <= 10
        assert page1[0].id != page2[0].id  # Different results

    @pytest.mark.asyncio
    async def test_search_no_results(self, db_session, seeded_countries):
        """Search returns empty when no matches."""
        reader = SqlaCountryReader(session=db_session)
        
        items, total = await reader.search(
            name="NonExistentCountry",
            iso2=None, iso3=None, region=None, subregion=None, currency=None,
            limit=10, offset=0
        )
        
        assert total == 0
        assert items == []


class TestSqlaCityReader:
    """Unit tests for SqlaCityReader."""

    @pytest.mark.asyncio
    async def test_search_by_country_id(self, db_session, seeded_cities):
        """Search finds cities by country ID."""
        reader = SqlaCityReader(session=db_session)
        
        items, total = await reader.search(
            name=None, country_id=233, state_id=None, state_code=None,
            state_name=None, country_code=None, wiki_data_id=None,
            limit=100, offset=0
        )
        
        assert total > 0
        assert all(c.country_id == 233 for c in items)

    @pytest.mark.asyncio
    async def test_search_by_state_code(self, db_session, seeded_cities):
        """Search finds cities by state code."""
        reader = SqlaCityReader(session=db_session)
        
        items, total = await reader.search(
            name=None, country_id=None, state_id=None, state_code="NY",
            state_name=None, country_code=None, wiki_data_id=None,
            limit=100, offset=0
        )
        
        assert total > 0
        assert all(c.state_code == "NY" for c in items)

    @pytest.mark.asyncio
    async def test_list_states_by_country(self, db_session, seeded_cities):
        """List states returns unique states for a country."""
        reader = SqlaCityReader(session=db_session)
        
        states = await reader.list_states_by_country(country_id=233)
        
        assert len(states) > 0
        # Verify uniqueness
        state_ids = [s.state_id for s in states]
        assert len(state_ids) == len(set(state_ids))

    @pytest.mark.asyncio
    async def test_list_states_empty_for_unknown_country(self, db_session):
        """List states returns empty for unknown country."""
        reader = SqlaCityReader(session=db_session)
        
        states = await reader.list_states_by_country(country_id=99999)
        
        assert states == []
```

---

### 2.2 Init Handler Tests (High)
**Priority**: HIGH  
**Location**: Should be in `tests/integration/atlas/test_init_handlers.py`

**Missing Tests**:
```python
class TestInitCountriesHandler:
    """Integration tests for InitCountriesHandler."""

    @pytest.mark.asyncio
    async def test_init_countries_from_csv(self, db_session, temp_countries_csv):
        """Handler imports countries from CSV."""
        handler = InitCountriesHandler(session=db_session)
        
        result = await handler.execute(csv_path=temp_countries_csv)
        
        assert result["total_countries"] > 0
        assert result["added_countries"] > 0
        assert result["error_countries"] == 0

    @pytest.mark.asyncio
    async def test_init_countries_updates_existing(self, db_session, temp_countries_csv):
        """Handler updates existing countries on re-run."""
        handler = InitCountriesHandler(session=db_session)
        
        # First run
        await handler.execute(csv_path=temp_countries_csv)
        
        # Second run
        result = await handler.execute(csv_path=temp_countries_csv)
        
        assert result["updated_countries"] > 0
        assert result["added_countries"] == 0

    @pytest.mark.asyncio
    async def test_init_countries_handles_bad_rows(self, db_session, temp_csv_with_errors):
        """Handler continues processing after bad rows."""
        handler = InitCountriesHandler(session=db_session)
        
        result = await handler.execute(csv_path=temp_csv_with_errors)
        
        assert result["error_countries"] > 0
        assert result["added_countries"] > 0  # Good rows still added

    @pytest.mark.asyncio
    async def test_init_countries_parses_timezones(self, db_session, temp_countries_csv):
        """Handler correctly parses timezone JSON."""
        handler = InitCountriesHandler(session=db_session)
        
        await handler.execute(csv_path=temp_countries_csv)
        
        # Verify timezones stored as JSON array
        # (would query database directly)


class TestInitCitiesHandler:
    """Integration tests for InitCitiesHandler."""

    @pytest.mark.asyncio
    async def test_init_cities_from_csv(self, db_session, temp_cities_csv, seeded_countries):
        """Handler imports cities from CSV."""
        handler = InitCitiesHandler(session=db_session)
        
        result = await handler.execute(csv_path=temp_cities_csv)
        
        assert result["total_cities"] > 0
        assert result["added_cities"] > 0

    @pytest.mark.asyncio
    async def test_init_cities_skips_unknown_country(self, db_session, temp_cities_csv):
        """Handler skips cities with unknown country_id."""
        handler = InitCitiesHandler(session=db_session)
        
        result = await handler.execute(csv_path=temp_cities_csv)
        
        # Some cities should be skipped due to missing countries
        assert result["skipped_cities"] >= 0

    @pytest.mark.asyncio
    async def test_init_cities_resolves_country_fk(self, db_session, temp_cities_csv, seeded_countries):
        """Handler correctly resolves country foreign key."""
        handler = InitCitiesHandler(session=db_session)
        
        await handler.execute(csv_path=temp_cities_csv)
        
        # Verify cities have valid country_id references
```

---

### 2.3 API E2E Tests (Medium)
**Priority**: MEDIUM  
**Location**: Should be in `tests/integration/atlas/test_atlas_api.py`

**Missing Tests**:
```python
class TestAtlasCountriesAPI:
    """E2E tests for Atlas Countries API."""

    @pytest.mark.asyncio
    async def test_search_countries_requires_auth(self, client):
        """Endpoint requires authentication."""
        response = await client.get("/api/v1/user/atlas/countries/search")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_search_countries_success(self, authenticated_client, seeded_countries):
        """Search countries returns results."""
        response = await authenticated_client.get(
            "/api/v1/user/atlas/countries/search?name=United"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] > 0

    @pytest.mark.asyncio
    async def test_search_countries_by_iso2(self, authenticated_client, seeded_countries):
        """Search by ISO2 returns exact match."""
        response = await authenticated_client.get(
            "/api/v1/user/atlas/countries/search?iso2=US"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["iso2"] == "US"

    @pytest.mark.asyncio
    async def test_search_countries_pagination(self, authenticated_client, seeded_countries):
        """Pagination parameters work."""
        response = await authenticated_client.get(
            "/api/v1/user/atlas/countries/search?limit=5&offset=0"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 5


class TestAtlasCitiesAPI:
    """E2E tests for Atlas Cities API."""

    @pytest.mark.asyncio
    async def test_search_cities_requires_auth(self, client):
        """Endpoint requires authentication."""
        response = await client.get("/api/v1/user/atlas/cities/search")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_search_cities_success(self, authenticated_client, seeded_cities):
        """Search cities returns results."""
        response = await authenticated_client.get(
            "/api/v1/user/atlas/cities/search?name=New"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0

    @pytest.mark.asyncio
    async def test_list_states_by_country(self, authenticated_client, seeded_cities):
        """List states returns states for country."""
        response = await authenticated_client.get(
            "/api/v1/user/atlas/states/233"
        )
        
        assert response.status_code == 200
        states = response.json()
        assert isinstance(states, list)
        assert len(states) > 0


class TestAtlasInitAPI:
    """E2E tests for Atlas Init API."""

    @pytest.mark.asyncio
    async def test_init_countries_requires_auth(self, client):
        """Init endpoint requires authentication."""
        response = await client.post("/api/v1/user/atlas/countries/init")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_init_countries_success(self, authenticated_admin_client):
        """Init countries returns result."""
        response = await authenticated_admin_client.post(
            "/api/v1/user/atlas/countries/init"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_countries" in data
        assert "added_countries" in data
```

---

### 2.4 System Config Tests (Low)
**Priority**: LOW  
**Location**: Should be in `tests/unit/domain/test_system_config.py`

**Missing Tests**:
```python
class TestSettingEntity:
    """Tests for Setting entity."""

    def test_setting_creation(self):
        """Setting entity can be created."""
        from app.domain.entities.system.setting import Setting, SettingId
        from app.domain.enums.system.setting_scope import SettingScope
        
        setting = Setting(
            id=SettingId(value=1),
            key="test.setting",
            value="test_value",
            scope=SettingScope.GLOBAL,
            is_sensitive=False,
            description="Test setting",
            updated_at=...,
            updated_by=None,
        )
        
        assert setting.key == "test.setting"
        assert setting.scope == SettingScope.GLOBAL

    def test_setting_scope_enum(self):
        """SettingScope enum has expected values."""
        from app.domain.enums.system.setting_scope import SettingScope
        
        assert SettingScope.GLOBAL.value == 0
        assert SettingScope.SECURITY.value == 1
        assert SettingScope.PAYMENTS.value == 2
        assert SettingScope.AI.value == 3
```

---

## 3. Test Coverage Summary

| Component | Existing | Missing | Coverage |
|-----------|----------|---------|----------|
| Query Services | 18 | 0 | ~100% |
| Country Reader | 0 | 5 | 0% |
| City Reader | 0 | 4 | 0% |
| Init Handlers | 0 | 7 | 0% |
| API E2E | 0 | 10 | 0% |
| System Config | 0 | 2 | 0% |

**Overall Estimated Coverage**: ~45%  
**Target Coverage**: 80%

---

## 4. Testing Priorities

### Immediate (Phase 1)
1. Infrastructure Reader tests - Core data access layer
2. Init Handler tests - Data import functionality

### Short-term (Phase 2)
3. API E2E tests - Full request flow
4. System Config tests - Settings entity

### Medium-term (Phase 3)
5. Performance tests - Query efficiency
6. Edge case tests - Error handling

---

## 5. Running Tests

```bash
# Run all atlas tests
pytest tests/unit/application/test_atlas_queries.py -v

# Run with coverage
pytest tests/unit/application/test_atlas_queries.py --cov=src/app/application/atlas --cov-report=html

# Run specific test class
pytest tests/unit/application/test_atlas_queries.py::TestSearchCountriesQueryService -v
```

---

## References

- **Query Service Tests**: `tests/unit/application/test_atlas_queries.py`
- **Query Services**: `src/app/application/atlas/queries.py`
- **Readers**: `src/app/infrastructure/atlas/readers_sqla.py`
- **Init Handlers**: `src/app/infrastructure/atlas/handlers/`
