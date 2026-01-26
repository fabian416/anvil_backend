# Location & System Config Services Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Location & System Config module provides:
- **Atlas Query Services** - Country, city, and state search functionality
- **Atlas Infrastructure Handlers** - Data initialization from CSV files
- **Atlas Readers** - SQLAlchemy-based data access layer
- **System Config Entities** - Settings and audit log domain models

**Total Service Components**: 12+ Python modules

---

## 1. Application Layer Services

### 1.1 SearchCountriesQueryService
**Path**: `src/app/application/atlas/queries.py`

Query service for searching countries with flexible filters.

```python
@dataclass(frozen=True, slots=True)
class SearchCountriesRequest:
    name: str | None
    iso2: str | None
    iso3: str | None
    region: str | None
    subregion: str | None
    currency: str | None
    limit: int
    offset: int

@dataclass(frozen=True)
class SearchCountriesResponse:
    data: list[CountryQueryModel]
    total: int

class SearchCountriesQueryService:
    """Search countries with flexible filters."""
    
    def __init__(self, country_reader: CountryReader):
        self._country_reader = country_reader

    async def execute(self, request: SearchCountriesRequest) -> SearchCountriesResponse:
        items, total = await self._country_reader.search(
            name=request.name,
            iso2=request.iso2,
            iso3=request.iso3,
            region=request.region,
            subregion=request.subregion,
            currency=request.currency,
            limit=request.limit,
            offset=request.offset,
        )
        return SearchCountriesResponse(data=items, total=total)
```

**Features**:
- Case-insensitive partial matching for name, region, subregion
- Exact matching for ISO codes (uppercase normalized)
- Pagination with limit/offset

---

### 1.2 SearchCitiesQueryService
**Path**: `src/app/application/atlas/queries.py`

Query service for searching cities with multiple filter options.

```python
@dataclass(frozen=True, slots=True)
class SearchCitiesRequest:
    name: str | None
    country_id: int | None
    state_id: str | None
    state_code: str | None
    state_name: str | None
    country_code: str | None
    wiki_data_id: str | None
    limit: int
    offset: int

@dataclass(frozen=True)
class SearchCitiesResponse:
    data: list[CityQueryModel]
    total: int

class SearchCitiesQueryService:
    """Search cities with flexible filters."""
    
    def __init__(self, city_reader: CityReader):
        self._city_reader = city_reader

    async def execute(self, request: SearchCitiesRequest) -> SearchCitiesResponse:
        items, total = await self._city_reader.search(
            name=request.name,
            country_id=request.country_id,
            state_id=request.state_id,
            state_code=request.state_code,
            state_name=request.state_name,
            country_code=request.country_code,
            wiki_data_id=request.wiki_data_id,
            limit=request.limit,
            offset=request.offset,
        )
        return SearchCitiesResponse(data=items, total=total)
```

**Features**:
- Filter by country, state, or any combination
- Wikidata ID support for external linking
- Case-insensitive partial matching for names

---

### 1.3 ListStatesByCountryQueryService
**Path**: `src/app/application/atlas/queries.py`

Query service for listing all states within a country.

```python
@dataclass(frozen=True, slots=True)
class ListStatesByCountryRequest:
    country_id: int

class ListStatesByCountryQueryService:
    """List all states within a country."""
    
    def __init__(self, city_reader: CityReader):
        self._city_reader = city_reader

    async def execute(self, request: ListStatesByCountryRequest) -> list[StateQueryModel]:
        return await self._city_reader.list_states_by_country(request.country_id)
```

**Features**:
- Extracts unique states from cities table
- Returns distinct state_id values
- Ordered alphabetically by state name

---

## 2. Infrastructure Layer Services

### 2.1 InitCountriesHandler
**Path**: `src/app/infrastructure/atlas/handlers/init_countries.py`

Handler for initializing country data from CSV files.

```python
class InitCountriesResult(TypedDict):
    total_countries: int
    added_countries: int
    updated_countries: int
    error_countries: int

@dataclass
class InitCountriesHandler:
    session: MainAsyncSession

    async def execute(self, csv_path: Path | None = None) -> InitCountriesResult:
        """
        Initialize countries from CSV data.
        
        CSV Columns:
        - country_id, name, iso3, iso2, numeric_code, phonecode
        - capital, currency, currency_name, currency_symbol, tld
        - native, region, subregion, nationality, timezones
        - latitude, longitude, emoji, emojiU
        """
```

**Data Processing**:
- Parses CSV with 22 columns
- Handles timezone JSON parsing with fallback normalization
- Upserts (insert or update) based on country_id
- Validates coordinate ranges
- Normalizes phone codes with "+" prefix

**Data Source**: `dump/countries.csv` (~250 countries)

---

### 2.2 InitCitiesHandler
**Path**: `src/app/infrastructure/atlas/handlers/init_cities.py`

Handler for initializing city data from CSV files.

```python
class InitCitiesResult(TypedDict):
    total_cities: int
    added_cities: int
    updated_cities: int
    skipped_cities: int
    error_cities: int

@dataclass
class InitCitiesHandler:
    session: MainAsyncSession

    async def execute(self, csv_path: Path | None = None) -> InitCitiesResult:
        """
        Initialize cities from CSV data.
        
        CSV Columns:
        - city_id, name, state_id, state_code, state_name
        - country_id, country_code, country_name
        - latitude, longitude, wikiDataId
        """
```

**Data Processing**:
- Parses CSV with 11 columns
- Resolves internal country_id from external country_id
- Skips cities with unknown countries
- Upserts based on (city_id, country_id) composite key
- Validates coordinate ranges

**Data Source**: `dump/cities.csv` (~150,000 cities)

---

### 2.3 SqlaCountryReader
**Path**: `src/app/infrastructure/atlas/readers_sqla.py`

SQLAlchemy-based reader for country data.

```python
class SqlaCountryReader(CountryReader):
    """
    SQLAlchemy implementation of CountryReader protocol.
    """
    
    def __init__(self, session: MainAsyncSession):
        map_countries_table()
        self._session = session

    async def search(
        self,
        *,
        name: str | None,
        iso2: str | None,
        iso3: str | None,
        region: str | None,
        subregion: str | None,
        currency: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[CountryQueryModel], int]:
        """Search countries with filters."""
```

**Query Features**:
- Dynamic WHERE clause building
- Case-insensitive LIKE matching for text fields
- Exact match for ISO codes (normalized to uppercase)
- Total count query for pagination
- Results ordered by name

---

### 2.4 SqlaCityReader
**Path**: `src/app/infrastructure/atlas/readers_sqla.py`

SQLAlchemy-based reader for city and state data.

```python
class SqlaCityReader(CityReader):
    """
    SQLAlchemy implementation of CityReader protocol.
    """
    
    def __init__(self, session: MainAsyncSession):
        map_cities_table()
        self._session = session

    async def search(
        self,
        *,
        name: str | None,
        country_id: int | None,
        state_id: str | None,
        state_code: str | None,
        state_name: str | None,
        country_code: str | None,
        wiki_data_id: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[CityQueryModel], int]:
        """Search cities with filters."""

    async def list_states_by_country(self, country_id: int) -> list[StateQueryModel]:
        """List unique states for a country."""
```

**Query Features**:
- Multiple filter combinations
- Distinct state extraction from cities
- Results ordered by name/state_name

---

## 3. Domain Layer

### 3.1 Country Entity
**Path**: `src/app/domain/entities/country.py`

Domain entity representing a country.

```python
@dataclass(eq=False, kw_only=True)
class Country(Entity[CountryId]):
    """
    Country entity following DDD principles.
    """
    name: CountryName
    iso3: IsoCode
    iso2: Optional[IsoCode]
    numeric_code: Optional[str]
    phonecode: Optional[str]
    capital: Optional[str]
    currency: Optional[str]
    currency_name: Optional[str]
    currency_symbol: Optional[str]
    tld: Optional[str]
    native: Optional[str]
    nationality: Optional[str]
    timezones: Optional[List[str]]
    coordinates: Optional[Coordinates]
    emoji: Optional[str]
    emojiU: Optional[str]
    region: Optional[str]
    subregion: Optional[str]
```

---

### 3.2 City Entity
**Path**: `src/app/domain/entities/city.py`

Domain entity representing a city.

```python
@dataclass(eq=False, kw_only=True)
class City(Entity[CityId]):
    """
    City entity following DDD principles.
    """
    name: CityName
    state_id: StateId
    state_code: Optional[StateCode]
    state_name: StateName
    country_id: CountryId
    country_code: CountryCode
    country_name: CountryName
    coordinates: Optional[Coordinates]
    wiki_data_id: Optional[WikiDataId]
```

---

### 3.3 Setting Entity
**Path**: `src/app/domain/entities/system/setting.py`

Domain entity for application settings.

```python
@dataclass(frozen=True, repr=False)
class SettingId(ValueObject):
    value: int

@dataclass(eq=False, kw_only=True)
class Setting(Entity[SettingId]):
    """
    System setting entity.
    """
    key: str
    value: Optional[str]
    scope: SettingScope
    is_sensitive: bool
    description: Optional[str]
    updated_at: UpdatedAt
    updated_by: Optional[UserId]
```

**Setting Scopes**:
```python
class SettingScope(Enum):
    GLOBAL = 0
    SECURITY = 1
    PAYMENTS = 2
    AI = 3
```

---

## 4. Application Ports (Protocols)

### 4.1 CountryReader Protocol
**Path**: `src/app/application/atlas/ports.py`

```python
class CountryReader(Protocol):
    @abstractmethod
    async def search(
        self,
        *,
        name: str | None,
        iso2: str | None,
        iso3: str | None,
        region: str | None,
        subregion: str | None,
        currency: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[CountryQueryModel], int]: ...
```

---

### 4.2 CityReader Protocol
**Path**: `src/app/application/atlas/ports.py`

```python
class CityReader(Protocol):
    @abstractmethod
    async def search(
        self,
        *,
        name: str | None,
        country_id: int | None,
        state_id: str | None,
        state_code: str | None,
        state_name: str | None,
        country_code: str | None,
        wiki_data_id: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[CityQueryModel], int]: ...

    @abstractmethod
    async def list_states_by_country(self, country_id: int) -> list[StateQueryModel]: ...
```

---

## 5. Query Models

**Path**: `src/app/application/atlas/query_models.py`

```python
@dataclass(frozen=True)
class CountryQueryModel:
    id: int
    country_id: int
    name: str
    iso2: Optional[str]
    iso3: str
    region: Optional[str]
    subregion: Optional[str]
    currency: Optional[str]

@dataclass(frozen=True)
class CityQueryModel:
    id: int
    city_id: int
    name: str
    country_id: int
    country_code: Optional[str]
    country_name: Optional[str]
    state_id: Optional[str]
    state_code: Optional[str]
    state_name: Optional[str]

@dataclass(frozen=True)
class StateQueryModel:
    state_id: Optional[str]
    state_name: Optional[str]
    state_code: Optional[str]
    country_id: int
    country_code: Optional[str]
    country_name: Optional[str]
```

---

## 6. Service Dependencies Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Atlas Router                                  │  │
│  │                     /api/v1/user/atlas                                │  │
│  │                                                                        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │
│  │  │ Countries Router│  │  Cities Router  │  │    Init Router      │   │  │
│  │  │                 │  │                 │  │                     │   │  │
│  │  │ GET /search     │  │ GET /search     │  │ POST /countries/init│   │  │
│  │  └────────┬────────┘  │ GET /states/:id │  │ POST /cities/init   │   │  │
│  │           │           └────────┬────────┘  └──────────┬──────────┘   │  │
│  └───────────┼────────────────────┼──────────────────────┼──────────────┘  │
└──────────────┼────────────────────┼──────────────────────┼──────────────────┘
               │                    │                      │
               ▼                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         Query Services                                   ││
│  │                                                                          ││
│  │  ┌─────────────────────────┐  ┌─────────────────────────────────────┐  ││
│  │  │SearchCountriesQuerySvc  │  │     SearchCitiesQueryService        │  ││
│  │  │                         │  │                                      │  ││
│  │  │ • name filter           │  │ • name filter                        │  ││
│  │  │ • iso2/iso3 filter      │  │ • country_id filter                  │  ││
│  │  │ • region filter         │  │ • state_id/code filter               │  ││
│  │  │ • currency filter       │  │ • country_code filter                │  ││
│  │  │ • pagination            │  │ • wiki_data_id filter                │  ││
│  │  └───────────┬─────────────┘  │ • pagination                         │  ││
│  │              │                └────────────────┬──────────────────────┘  ││
│  │              │                                 │                         ││
│  │              │  ┌─────────────────────────────┐│                         ││
│  │              │  │ListStatesByCountryQuerySvc  ││                         ││
│  │              │  │                             ││                         ││
│  │              │  │ • country_id lookup         ││                         ││
│  │              │  │ • distinct states           ││                         ││
│  │              │  └──────────────┬──────────────┘│                         ││
│  └──────────────┼─────────────────┼───────────────┼─────────────────────────┘│
│                 │                 │               │                          │
│                 ▼                 ▼               ▼                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                           Ports (Protocols)                              ││
│  │                                                                          ││
│  │  ┌─────────────────────────┐  ┌─────────────────────────────────────┐  ││
│  │  │    CountryReader        │  │          CityReader                  │  ││
│  │  │                         │  │                                      │  ││
│  │  │  search(filters) →      │  │  search(filters) →                   │  ││
│  │  │    CountryQueryModel[]  │  │    CityQueryModel[]                  │  ││
│  │  └─────────────────────────┘  │  list_states_by_country() →          │  ││
│  │                                │    StateQueryModel[]                 │  ││
│  │                                └─────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INFRASTRUCTURE LAYER                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        SQLAlchemy Readers                                ││
│  │                                                                          ││
│  │  ┌─────────────────────────┐  ┌─────────────────────────────────────┐  ││
│  │  │   SqlaCountryReader     │  │        SqlaCityReader                │  ││
│  │  │                         │  │                                      │  ││
│  │  │ • Dynamic WHERE builder │  │ • Dynamic WHERE builder              │  ││
│  │  │ • LIKE for text fields  │  │ • LIKE for text fields               │  ││
│  │  │ • Exact match for ISO   │  │ • DISTINCT for states                │  ││
│  │  │ • COUNT for pagination  │  │ • COUNT for pagination               │  ││
│  │  └───────────┬─────────────┘  └─────────────────┬────────────────────┘  ││
│  │              │                                  │                        ││
│  └──────────────┼──────────────────────────────────┼────────────────────────┘│
│                 │                                  │                         │
│  ┌──────────────┼──────────────────────────────────┼────────────────────────┐│
│  │              ▼                                  ▼                        ││
│  │                    Data Initialization Handlers                          ││
│  │                                                                          ││
│  │  ┌─────────────────────────┐  ┌─────────────────────────────────────┐  ││
│  │  │  InitCountriesHandler   │  │       InitCitiesHandler              │  ││
│  │  │                         │  │                                      │  ││
│  │  │ • CSV parsing           │  │ • CSV parsing                        │  ││
│  │  │ • Timezone JSON fix     │  │ • Country FK resolution              │  ││
│  │  │ • Upsert logic          │  │ • Upsert logic                       │  ││
│  │  │ • Coordinate validation │  │ • Coordinate validation              │  ││
│  │  └─────────────────────────┘  └─────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      SQLAlchemy Table Mappings                           ││
│  │                                                                          ││
│  │  ┌─────────────────────────┐  ┌─────────────────────────────────────┐  ││
│  │  │   map_countries_table() │  │       map_cities_table()             │  ││
│  │  │                         │  │                                      │  ││
│  │  │ • 20+ columns           │  │ • 11 columns                         │  ││
│  │  │ • Coordinate constraints│  │ • Coordinate constraints             │  ││
│  │  │ • Indexed on: name,     │  │ • Unique: (city_id, country_id)      │  ││
│  │  │   iso2, iso3, region    │  │ • Indexed on: name, state, country   │  ││
│  │  └─────────────────────────┘  └─────────────────────────────────────┘  ││
│  │                                                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────┐   ││
│  │  │                  map_system_config_tables()                      │   ││
│  │  │                                                                  │   ││
│  │  │  ┌─────────────────────┐  ┌─────────────────────────────────┐  │   ││
│  │  │  │   settings table    │  │      audit_logs table           │  │   ││
│  │  │  │                     │  │                                 │  │   ││
│  │  │  │ • key (unique)      │  │ • actor_user_id                 │  │   ││
│  │  │  │ • value             │  │ • action                        │  │   ││
│  │  │  │ • scope             │  │ • entity                        │  │   ││
│  │  │  │ • is_sensitive      │  │ • payload_json                  │  │   ││
│  │  │  │ • updated_by        │  │ • ip_address                    │  │   ││
│  │  │  └─────────────────────┘  └─────────────────────────────────┘  │   ││
│  │  └─────────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOMAIN LAYER                                       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                            Entities                                      ││
│  │                                                                          ││
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  ││
│  │  │  Country Entity  │  │   City Entity    │  │   Setting Entity     │  ││
│  │  │                  │  │                  │  │                      │  ││
│  │  │ • CountryId      │  │ • CityId         │  │ • SettingId          │  ││
│  │  │ • CountryName    │  │ • CityName       │  │ • key, value         │  ││
│  │  │ • IsoCode        │  │ • StateId        │  │ • SettingScope       │  ││
│  │  │ • Coordinates    │  │ • CountryId      │  │ • is_sensitive       │  ││
│  │  │ • region, etc.   │  │ • Coordinates    │  │ • updated_by         │  ││
│  │  └──────────────────┘  └──────────────────┘  └──────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         Value Objects                                    ││
│  │                                                                          ││
│  │  CountryId • CountryName • CountryCode • IsoCode • Coordinates          ││
│  │  CityId • CityName • StateId • StateCode • StateName • WikiDataId       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         CSV Data Files                                   ││
│  │                                                                          ││
│  │  dump/countries.csv (~250 countries, 22 columns)                        ││
│  │  dump/cities.csv (~150,000 cities, 11 columns)                          ││
│  │                                                                          ││
│  │  Source: BaseAPI geographic data                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## References

- **Query Services**: `src/app/application/atlas/queries.py`
- **Query Models**: `src/app/application/atlas/query_models.py`
- **Ports**: `src/app/application/atlas/ports.py`
- **Country Reader**: `src/app/infrastructure/atlas/readers_sqla.py`
- **City Reader**: `src/app/infrastructure/atlas/readers_sqla.py`
- **Init Countries Handler**: `src/app/infrastructure/atlas/handlers/init_countries.py`
- **Init Cities Handler**: `src/app/infrastructure/atlas/handlers/init_cities.py`
- **Country Mapping**: `src/app/infrastructure/persistence_sqla/mappings/country.py`
- **City Mapping**: `src/app/infrastructure/persistence_sqla/mappings/city.py`
- **System Config Mapping**: `src/app/infrastructure/persistence_sqla/mappings/system_config.py`
- **Country Entity**: `src/app/domain/entities/country.py`
- **City Entity**: `src/app/domain/entities/city.py`
- **Setting Entity**: `src/app/domain/entities/system/setting.py`
