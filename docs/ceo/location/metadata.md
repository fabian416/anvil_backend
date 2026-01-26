# Location & System Config Module Metadata

> **Last Updated**: 2026-01-25  
> **Status**: Production (Atlas) / Partial (System Config)  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## 1. Module Overview

### Location (Atlas) System
**Purpose**: Provide geographic data (countries, cities, states) for user-facing features.

**Status**: ✅ Production Ready
- 3 user endpoints operational
- 2 admin init endpoints operational
- Unit tests for query services
- ~250 countries, ~150,000 cities supported

### System Config System
**Purpose**: Store application-wide settings and audit administrative actions.

**Status**: ⚠️ Partial Implementation
- Database tables created
- Domain entities defined
- No REST API exposed
- No admin dashboard integration

---

## 2. File Reference Index

### Domain Layer
| File | Description | Status |
|------|-------------|--------|
| `src/app/domain/entities/country.py` | Country entity (DDD) | ✅ |
| `src/app/domain/entities/city.py` | City entity (DDD) | ✅ |
| `src/app/domain/entities/system/setting.py` | Setting entity | ✅ |
| `src/app/domain/enums/system/setting_scope.py` | SettingScope enum | ✅ |
| `src/app/domain/value_objects/country_id.py` | CountryId value object | ✅ |
| `src/app/domain/value_objects/country_name.py` | CountryName value object | ✅ |
| `src/app/domain/value_objects/country_code.py` | CountryCode value object | ✅ |
| `src/app/domain/value_objects/city_id.py` | CityId value object | ✅ |
| `src/app/domain/value_objects/city_name.py` | CityName value object | ✅ |
| `src/app/domain/value_objects/coordinates.py` | Coordinates value object | ✅ |
| `src/app/domain/value_objects/iso_code.py` | IsoCode value object | ✅ |
| `src/app/domain/value_objects/state_id.py` | StateId value object | ✅ |
| `src/app/domain/value_objects/state_code.py` | StateCode value object | ✅ |
| `src/app/domain/value_objects/state_name.py` | StateName value object | ✅ |
| `src/app/domain/value_objects/wiki_data_id.py` | WikiDataId value object | ✅ |
| `src/app/domain/exceptions/location.py` | Location exceptions | ✅ |
| `src/app/domain/atlas/entities/country.py` | Alternate country entity | ⚠️ Duplicate |
| `src/app/domain/atlas/entities/city.py` | Alternate city entity | ⚠️ Duplicate |

### Application Layer
| File | Description | Status |
|------|-------------|--------|
| `src/app/application/atlas/queries.py` | Query services | ✅ |
| `src/app/application/atlas/query_models.py` | Query DTOs | ✅ |
| `src/app/application/atlas/ports.py` | Reader protocols | ✅ |
| `src/app/application/common/ports/country_query_gateway.py` | Country gateway | ✅ |
| `src/app/application/common/ports/city_query_gateway.py` | City gateway | ✅ |

### Infrastructure Layer
| File | Description | Status |
|------|-------------|--------|
| `src/app/infrastructure/atlas/readers_sqla.py` | SQLAlchemy readers | ✅ |
| `src/app/infrastructure/atlas/handlers/init_countries.py` | Country init handler | ✅ |
| `src/app/infrastructure/atlas/handlers/init_cities.py` | City init handler | ✅ |
| `src/app/infrastructure/adapters/country_reader_sqla.py` | Country adapter | ⚠️ Alternate |
| `src/app/infrastructure/adapters/city_reader_sqla.py` | City adapter | ⚠️ Alternate |
| `src/app/infrastructure/persistence_sqla/mappings/country.py` | Country table mapping | ✅ |
| `src/app/infrastructure/persistence_sqla/mappings/city.py` | City table mapping | ✅ |
| `src/app/infrastructure/persistence_sqla/mappings/system_config.py` | Settings/Audit mapping | ✅ |

### Presentation Layer
| File | Description | Status |
|------|-------------|--------|
| `src/app/presentation/http/controllers/atlas/router.py` | Atlas main router | ✅ |
| `src/app/presentation/http/controllers/atlas/countries.py` | Countries endpoint | ✅ |
| `src/app/presentation/http/controllers/atlas/cities.py` | Cities/States endpoint | ✅ |
| `src/app/presentation/http/controllers/atlas/init.py` | Init endpoints | ✅ |

### Database Migrations
| File | Description | Status |
|------|-------------|--------|
| `src/app/infrastructure/persistence_sqla/alembic/versions/2025_11_27_0500-e5f6g7h8i9j0_add_system_config_tables.py` | Settings & Audit tables | ✅ |

### Tests
| File | Description | Status |
|------|-------------|--------|
| `tests/unit/application/test_atlas_queries.py` | Query service tests | ✅ 18 tests |

### Data Files
| File | Description | Status |
|------|-------------|--------|
| `dump/countries.csv` | Country seed data (~250) | ✅ |
| `dump/cities.csv` | City seed data (~150K) | ✅ |

---

## 3. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              LOCATION & SYSTEM CONFIG MODULE                             │
│                                                                                          │
│ ┌──────────────────────────────────────────────────────────────────────────────────────┐│
│ │                               PRESENTATION LAYER                                      ││
│ │                                                                                       ││
│ │  ┌─────────────────────────────────────────────────────────────────────────────────┐ ││
│ │  │                    Atlas Router (/api/v1/user/atlas)                            │ ││
│ │  │                                                                                  │ ││
│ │  │  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────────────────┐ │ ││
│ │  │  │ Countries Router │  │  Cities Router   │  │        Init Router            │ │ ││
│ │  │  │                  │  │                  │  │                               │ │ ││
│ │  │  │ GET /search      │  │ GET /search      │  │ POST /countries/init (Admin)  │ │ ││
│ │  │  │                  │  │ GET /states/:id  │  │ POST /cities/init (Admin)     │ │ ││
│ │  │  │ Auth: User ✅     │  │ Auth: User ✅     │  │ Auth: User (should be Admin) │ │ ││
│ │  │  └────────┬─────────┘  └────────┬─────────┘  └──────────────┬────────────────┘ │ ││
│ │  └───────────┼──────────────────────┼──────────────────────────┼──────────────────┘ ││
│ └──────────────┼──────────────────────┼──────────────────────────┼──────────────────────┘│
│                │                      │                          │                       │
│                ▼                      ▼                          ▼                       │
│ ┌──────────────────────────────────────────────────────────────────────────────────────┐│
│ │                              APPLICATION LAYER                                        ││
│ │                                                                                       ││
│ │  ┌────────────────────────────────────────────────────────────────────────────────┐  ││
│ │  │                           Query Services                                        │  ││
│ │  │                                                                                 │  ││
│ │  │  ┌─────────────────────────────┐  ┌─────────────────────────────────────────┐ │  ││
│ │  │  │ SearchCountriesQueryService │  │       SearchCitiesQueryService          │ │  ││
│ │  │  │                             │  │                                          │ │  ││
│ │  │  │ Filters:                    │  │ Filters:                                 │ │  ││
│ │  │  │ • name (partial)            │  │ • name (partial)                         │ │  ││
│ │  │  │ • iso2, iso3 (exact)        │  │ • country_id, state_id                   │ │  ││
│ │  │  │ • region, subregion         │  │ • state_code, country_code               │ │  ││
│ │  │  │ • currency                  │  │ • wiki_data_id                           │ │  ││
│ │  │  │ • pagination                │  │ • pagination                             │ │  ││
│ │  │  └─────────────────────────────┘  └─────────────────────────────────────────┘ │  ││
│ │  │                                                                                 │  ││
│ │  │                    ┌──────────────────────────────────────┐                    │  ││
│ │  │                    │ ListStatesByCountryQueryService      │                    │  ││
│ │  │                    │                                      │                    │  ││
│ │  │                    │ Returns: DISTINCT states by country  │                    │  ││
│ │  │                    └──────────────────────────────────────┘                    │  ││
│ │  └────────────────────────────────────────────────────────────────────────────────┘  ││
│ │                                                                                       ││
│ │  ┌────────────────────────────────────────────────────────────────────────────────┐  ││
│ │  │                           Ports (Protocols)                                     │  ││
│ │  │                                                                                 │  ││
│ │  │  ┌─────────────────────────────┐  ┌─────────────────────────────────────────┐ │  ││
│ │  │  │      CountryReader          │  │            CityReader                    │ │  ││
│ │  │  │                             │  │                                          │ │  ││
│ │  │  │ • search() → Countries[]    │  │ • search() → Cities[]                    │ │  ││
│ │  │  │                             │  │ • list_states_by_country() → States[]    │ │  ││
│ │  │  └─────────────────────────────┘  └─────────────────────────────────────────┘ │  ││
│ │  └────────────────────────────────────────────────────────────────────────────────┘  ││
│ └──────────────────────────────────────────────────────────────────────────────────────┘│
│                │                      │                          │                       │
│                ▼                      ▼                          ▼                       │
│ ┌──────────────────────────────────────────────────────────────────────────────────────┐│
│ │                             INFRASTRUCTURE LAYER                                      ││
│ │                                                                                       ││
│ │  ┌────────────────────────────────────────────────────────────────────────────────┐  ││
│ │  │                        SQLAlchemy Readers                                       │  ││
│ │  │                                                                                 │  ││
│ │  │  ┌─────────────────────────────┐  ┌─────────────────────────────────────────┐ │  ││
│ │  │  │     SqlaCountryReader       │  │          SqlaCityReader                  │ │  ││
│ │  │  │                             │  │                                          │ │  ││
│ │  │  │ • Dynamic WHERE builder     │  │ • Dynamic WHERE builder                  │ │  ││
│ │  │  │ • LIKE for text fields      │  │ • LIKE for text fields                   │ │  ││
│ │  │  │ • COUNT for pagination      │  │ • DISTINCT for states                    │ │  ││
│ │  │  │ • ORDER BY name             │  │ • ORDER BY name                          │ │  ││
│ │  │  └─────────────────────────────┘  └─────────────────────────────────────────┘ │  ││
│ │  └────────────────────────────────────────────────────────────────────────────────┘  ││
│ │                                                                                       ││
│ │  ┌────────────────────────────────────────────────────────────────────────────────┐  ││
│ │  │                       Init Handlers (Data Import)                               │  ││
│ │  │                                                                                 │  ││
│ │  │  ┌─────────────────────────────┐  ┌─────────────────────────────────────────┐ │  ││
│ │  │  │    InitCountriesHandler     │  │         InitCitiesHandler               │ │  ││
│ │  │  │                             │  │                                          │ │  ││
│ │  │  │ • Parse CSV (22 columns)    │  │ • Parse CSV (11 columns)                 │ │  ││
│ │  │  │ • Upsert on country_id      │  │ • Resolve country FK                     │ │  ││
│ │  │  │ • Timezone JSON parsing     │  │ • Upsert on (city_id, country_id)        │ │  ││
│ │  │  │ • Coordinate validation     │  │ • Skip unknown countries                 │ │  ││
│ │  │  └─────────────────────────────┘  └─────────────────────────────────────────┘ │  ││
│ │  └────────────────────────────────────────────────────────────────────────────────┘  ││
│ │                                                                                       ││
│ │  ┌────────────────────────────────────────────────────────────────────────────────┐  ││
│ │  │                      SQLAlchemy Table Mappings                                  │  ││
│ │  │                                                                                 │  ││
│ │  │  ┌─────────────────────────────┐  ┌─────────────────────────────────────────┐ │  ││
│ │  │  │     countries table         │  │           cities table                   │ │  ││
│ │  │  │                             │  │                                          │ │  ││
│ │  │  │ • 20+ columns               │  │ • 11 columns                             │ │  ││
│ │  │  │ • Timezones as JSON         │  │ • FK to countries                        │ │  ││
│ │  │  │ • Indexed: name, iso2,      │  │ • Unique: (city_id, country_id)          │ │  ││
│ │  │  │   iso3, region              │  │ • Indexed: name, state, country          │ │  ││
│ │  │  └─────────────────────────────┘  └─────────────────────────────────────────┘ │  ││
│ │  │                                                                                 │  ││
│ │  │  ┌───────────────────────────────────────────────────────────────────────────┐│  ││
│ │  │  │                      System Config Tables                                  ││  ││
│ │  │  │                                                                            ││  ││
│ │  │  │  ┌─────────────────────────┐  ┌─────────────────────────────────────┐    ││  ││
│ │  │  │  │     settings table      │  │        audit_logs table             │    ││  ││
│ │  │  │  │                         │  │                                     │    ││  ││
│ │  │  │  │ • key (unique)          │  │ • actor_user_id                     │    ││  ││
│ │  │  │  │ • value                 │  │ • action, entity, entity_id         │    ││  ││
│ │  │  │  │ • scope (enum)          │  │ • payload_json                      │    ││  ││
│ │  │  │  │ • is_sensitive          │  │ • ip_address, user_agent            │    ││  ││
│ │  │  │  │ • updated_by            │  │ • created_at                        │    ││  ││
│ │  │  │  │                         │  │                                     │    ││  ││
│ │  │  │  │ STATUS: No API ⚠️        │  │ STATUS: No API ⚠️                    │    ││  ││
│ │  │  │  └─────────────────────────┘  └─────────────────────────────────────┘    ││  ││
│ │  │  └───────────────────────────────────────────────────────────────────────────┘│  ││
│ │  └────────────────────────────────────────────────────────────────────────────────┘  ││
│ └──────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                          │
│                │                      │                                                  │
│                ▼                      ▼                                                  │
│ ┌──────────────────────────────────────────────────────────────────────────────────────┐│
│ │                               DOMAIN LAYER                                            ││
│ │                                                                                       ││
│ │  ┌────────────────────────────────────────────────────────────────────────────────┐  ││
│ │  │                              Entities                                           │  ││
│ │  │                                                                                 │  ││
│ │  │  ┌────────────────────┐  ┌────────────────────┐  ┌──────────────────────────┐ │  ││
│ │  │  │   Country Entity   │  │    City Entity     │  │     Setting Entity       │ │  ││
│ │  │  │                    │  │                    │  │                          │ │  ││
│ │  │  │ • CountryId        │  │ • CityId           │  │ • SettingId              │ │  ││
│ │  │  │ • CountryName      │  │ • CityName         │  │ • key                    │ │  ││
│ │  │  │ • IsoCode (2,3)    │  │ • StateId          │  │ • value                  │ │  ││
│ │  │  │ • Coordinates      │  │ • CountryId        │  │ • SettingScope           │ │  ││
│ │  │  │ • region, currency │  │ • Coordinates      │  │ • is_sensitive           │ │  ││
│ │  │  │ • timezones        │  │ • WikiDataId       │  │ • updated_by             │ │  ││
│ │  │  └────────────────────┘  └────────────────────┘  └──────────────────────────┘ │  ││
│ │  └────────────────────────────────────────────────────────────────────────────────┘  ││
│ │                                                                                       ││
│ │  ┌────────────────────────────────────────────────────────────────────────────────┐  ││
│ │  │                           Value Objects                                         │  ││
│ │  │                                                                                 │  ││
│ │  │  CountryId • CountryName • CountryCode • IsoCode • Coordinates                 │  ││
│ │  │  CityId • CityName • StateId • StateCode • StateName • WikiDataId              │  ││
│ │  └────────────────────────────────────────────────────────────────────────────────┘  ││
│ └──────────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                          │
│                                          │                                               │
│                                          ▼                                               │
│ ┌──────────────────────────────────────────────────────────────────────────────────────┐│
│ │                               DATA SOURCES                                            ││
│ │                                                                                       ││
│ │  ┌──────────────────────────────┐  ┌──────────────────────────────────────────────┐ ││
│ │  │     dump/countries.csv       │  │           dump/cities.csv                    │ ││
│ │  │                              │  │                                               │ ││
│ │  │  ~250 countries              │  │  ~150,000 cities                              │ ││
│ │  │  22 columns per row          │  │  11 columns per row                           │ ││
│ │  │  Source: BaseAPI             │  │  Source: BaseAPI                              │ ││
│ │  └──────────────────────────────┘  └──────────────────────────────────────────────┘ ││
│ └──────────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

### Countries Table
```sql
CREATE TABLE countries (
    id INTEGER PRIMARY KEY,
    country_id INTEGER NOT NULL INDEX,
    name VARCHAR(100) NOT NULL INDEX,
    iso3 VARCHAR(3) UNIQUE NOT NULL INDEX,
    iso2 VARCHAR(2) INDEX,
    numeric_code VARCHAR(3),
    phonecode VARCHAR(20),
    capital VARCHAR(100),
    currency VARCHAR(3),
    currency_name VARCHAR(50),
    currency_symbol VARCHAR(10),
    tld VARCHAR(10),
    native VARCHAR(100),
    nationality VARCHAR(100),
    timezones JSON,
    latitude FLOAT CHECK (latitude >= -90 AND latitude <= 90),
    longitude FLOAT CHECK (longitude >= -180 AND longitude <= 180),
    emoji VARCHAR(10),
    emojiU VARCHAR(20),
    region VARCHAR(50) INDEX,
    subregion VARCHAR(50) INDEX
);
```

### Cities Table
```sql
CREATE TABLE cities (
    id INTEGER PRIMARY KEY,
    city_id INTEGER NOT NULL INDEX,
    name VARCHAR(100) NOT NULL INDEX,
    state_id VARCHAR(20) INDEX,
    state_code VARCHAR(10) INDEX,
    state_name VARCHAR(100),
    country_id INTEGER NOT NULL INDEX REFERENCES countries(id),
    country_code VARCHAR(2) INDEX,
    country_name VARCHAR(100),
    latitude FLOAT CHECK (latitude >= -90 AND latitude <= 90),
    longitude FLOAT CHECK (longitude >= -180 AND longitude <= 180),
    wikiDataId VARCHAR(50) INDEX,
    UNIQUE (city_id, country_id)
);
```

### Settings Table
```sql
CREATE TABLE settings (
    id INTEGER PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL INDEX,
    value TEXT,
    scope INTEGER DEFAULT 0 NOT NULL INDEX,
    is_sensitive BOOLEAN DEFAULT FALSE INDEX,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);
```

### Audit Logs Table
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    actor_user_id INTEGER NOT NULL INDEX REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL INDEX,
    entity VARCHAR(100) NOT NULL INDEX,
    entity_id VARCHAR(100),
    payload_json JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP INDEX
);
```

---

## 5. Current Status

### Atlas System
| Feature | Status | Notes |
|---------|--------|-------|
| Country search | ✅ Production | All filters working |
| City search | ✅ Production | All filters working |
| State listing | ✅ Production | Distinct from cities |
| Country init | ✅ Production | CSV import working |
| City init | ✅ Production | CSV import working |
| Unit tests | ✅ Production | 18 tests passing |
| Integration tests | ❌ Missing | Need to implement |
| Admin auth | ⚠️ Partial | Init uses user auth |

### System Config System
| Feature | Status | Notes |
|---------|--------|-------|
| Settings table | ✅ Created | Migration applied |
| Audit logs table | ✅ Created | Migration applied |
| Settings API | ❌ Missing | No REST endpoints |
| Audit API | ❌ Missing | No REST endpoints |
| Admin dashboard | ❌ Missing | No integration |
| Celery tasks | ❌ Missing | No background tasks |

---

## 6. Improvements Roadmap

### Phase 1: Security (High Priority)
1. **Restrict init endpoints to admin only**
   - Add admin role check
   - Separate admin router
   - Audit initialization actions

### Phase 2: System Config API (Medium Priority)
2. **Implement Settings API**
   - GET /admin/settings - List all settings
   - GET /admin/settings/{key} - Get setting
   - PUT /admin/settings/{key} - Update setting
   - Mask sensitive values in responses

3. **Implement Audit Logs API**
   - GET /admin/audit-logs - List with filters
   - GET /admin/audit-logs/{id} - Get details
   - Export to CSV/JSON

### Phase 3: Automation (Medium Priority)
4. **Celery Tasks**
   - Geographic data refresh
   - Audit log cleanup
   - Settings cache sync

### Phase 4: Testing (Lower Priority)
5. **Add missing tests**
   - Infrastructure reader tests
   - Init handler tests
   - API E2E tests

### Phase 5: Data Quality (Lower Priority)
6. **Enhancements**
   - Country flag images
   - Currency exchange rates integration
   - Timezone lookup by coordinates

---

## 7. Configuration

### Environment Variables
No specific environment variables for this module.

### CSV Data Location
```python
# Default data paths
COUNTRIES_CSV = "dump/countries.csv"
CITIES_CSV = "dump/cities.csv"

# Fallback paths
COUNTRIES_CSV_ALT = "src/app/infrastructure/persistence_sqla/dump/countries.csv"
CITIES_CSV_ALT = "src/app/infrastructure/persistence_sqla/dump/cities.csv"
```

### Setting Scope Enum
```python
class SettingScope(Enum):
    GLOBAL = 0      # System-wide settings
    SECURITY = 1    # Security configuration
    PAYMENTS = 2    # Payment settings
    AI = 3          # AI/LLM settings
```

---

## 8. Related Modules

| Module | Relationship |
|--------|--------------|
| Auth | User identity for audit logs |
| Admin | Admin dashboard integration (future) |
| Subscription | Payment settings storage |
| LLM/AI | AI model configuration storage |
| Security | Security settings storage |

---

## References

- **Database Architecture Spec**: `docs/ceo/database-architecture-spec.md` (Section 14)
- **Atlas Router**: `src/app/presentation/http/controllers/atlas/`
- **System Config Migration**: `src/app/infrastructure/persistence_sqla/alembic/versions/2025_11_27_0500-e5f6g7h8i9j0_add_system_config_tables.py`
