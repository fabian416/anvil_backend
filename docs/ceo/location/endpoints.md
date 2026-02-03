# Location & System Config Endpoints Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Location & System Config module provides:
1. **Atlas API** - Geographic data (countries, cities, states) for user-facing features
2. **System Config** - Application settings and audit logging for admin management

**Base Paths**:
- Atlas: `/api/v1/user/atlas`
- System Config: Database tables (no REST API currently)

> **Note**: All atlas endpoints require authentication.

---

## 1. Atlas User Endpoints

### GET /user/atlas/countries/search

Search countries with filters.

**Authentication**: Required (Bearer Token)

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Filter by country name (partial match) |
| `iso2` | string | Filter by ISO 3166-1 alpha-2 code |
| `iso3` | string | Filter by ISO 3166-1 alpha-3 code |
| `region` | string | Filter by region (partial match) |
| `subregion` | string | Filter by subregion (partial match) |
| `currency` | string | Filter by currency code (partial match) |
| `limit` | int | Max results (default: 10) |
| `offset` | int | Pagination offset (default: 0) |

**Response** (`SearchCountriesResponse`):
```json
{
  "data": [
    {
      "id": 1,
      "country_id": 233,
      "name": "United States",
      "iso2": "US",
      "iso3": "USA",
      "region": "Americas",
      "subregion": "Northern America",
      "currency": "USD"
    },
    {
      "id": 2,
      "country_id": 40,
      "name": "Canada",
      "iso2": "CA",
      "iso3": "CAN",
      "region": "Americas",
      "subregion": "Northern America",
      "currency": "CAD"
    }
  ],
  "total": 2
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/user/atlas/countries/search?region=Americas&limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /user/atlas/cities/search

Search cities with filters.

**Authentication**: Required (Bearer Token)

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Filter by city name (partial match) |
| `country_id` | int | Filter by country ID |
| `state_id` | string | Filter by state ID |
| `state_code` | string | Filter by state code |
| `state_name` | string | Filter by state name (partial match) |
| `country_code` | string | Filter by country ISO code |
| `wikiDataId` | string | Filter by Wikidata ID |
| `limit` | int | Max results (default: 10) |
| `offset` | int | Pagination offset (default: 0) |

**Response** (`SearchCitiesResponse`):
```json
{
  "data": [
    {
      "id": 1,
      "city_id": 127394,
      "name": "New York",
      "country_id": 233,
      "country_code": "US",
      "country_name": "United States",
      "state_id": "NY001",
      "state_code": "NY",
      "state_name": "New York"
    },
    {
      "id": 2,
      "city_id": 112345,
      "name": "Los Angeles",
      "country_id": 233,
      "country_code": "US",
      "country_name": "United States",
      "state_id": "CA001",
      "state_code": "CA",
      "state_name": "California"
    }
  ],
  "total": 2
}
```

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/user/atlas/cities/search?country_code=US&state_code=NY&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /user/atlas/states/{country_id}

List all states for a specific country.

**Authentication**: Required (Bearer Token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `country_id` | int | Country ID to get states for |

**Response** (`List[StateQueryModel]`):
```json
[
  {
    "state_id": "CA001",
    "state_name": "California",
    "state_code": "CA",
    "country_id": 233,
    "country_code": "US",
    "country_name": "United States"
  },
  {
    "state_id": "NY001",
    "state_name": "New York",
    "state_code": "NY",
    "country_id": 233,
    "country_code": "US",
    "country_name": "United States"
  },
  {
    "state_id": "TX001",
    "state_name": "Texas",
    "state_code": "TX",
    "country_id": 233,
    "country_code": "US",
    "country_name": "United States"
  }
]
```

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/user/atlas/states/233" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 2. Atlas Admin Endpoints

### POST /user/atlas/countries/init

Initialize countries from CSV data. **Should be admin-only.**

**Authentication**: Required (Bearer Token)

**Response** (`InitCountriesResult`):
```json
{
  "total_countries": 250,
  "added_countries": 250,
  "updated_countries": 0,
  "error_countries": 0
}
```

**Data Source**: `dump/countries.csv`

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/user/atlas/countries/init" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

### POST /user/atlas/cities/init

Initialize cities from CSV data. **Should be admin-only.**

**Authentication**: Required (Bearer Token)

**Response** (`InitCitiesResult`):
```json
{
  "total_cities": 150000,
  "added_cities": 148500,
  "updated_cities": 0,
  "skipped_cities": 1200,
  "error_cities": 300
}
```

**Data Source**: `dump/cities.csv`

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/user/atlas/cities/init" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 3. System Config (Database Only)

The System Config module has **no REST API endpoints**. It stores system-wide settings in the database.

### Settings Table

Stores application-wide configuration settings.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `key` | String(100) | Unique setting key |
| `value` | Text | Setting value |
| `scope` | Integer | Setting scope (0=GLOBAL, 1=SECURITY, 2=PAYMENTS, 3=AI) |
| `is_sensitive` | Boolean | Whether value should be masked |
| `description` | Text | Human-readable description |
| `updated_at` | DateTime | Last update timestamp |
| `updated_by` | Integer | User ID who last updated |

**Setting Scopes**:
| Scope | Value | Description |
|-------|-------|-------------|
| GLOBAL | 0 | System-wide settings |
| SECURITY | 1 | Security-related settings |
| PAYMENTS | 2 | Payment configuration |
| AI | 3 | AI/LLM configuration |

### Audit Logs Table

Tracks administrative actions for compliance.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `actor_user_id` | Integer | User who performed action |
| `action` | String(100) | Action type (e.g., "UPDATE", "DELETE") |
| `entity` | String(100) | Entity type (e.g., "settings", "user") |
| `entity_id` | String(100) | Entity identifier |
| `payload_json` | JSON | Change details |
| `ip_address` | String(45) | Client IP address |
| `user_agent` | Text | Client user agent |
| `created_at` | DateTime | When action occurred |

---

## 4. Endpoint Summary

### User Endpoints
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/user/atlas/countries/search` | Search countries | ✅ User |
| GET | `/user/atlas/cities/search` | Search cities | ✅ User |
| GET | `/user/atlas/states/{country_id}` | List states by country | ✅ User |

### Admin Endpoints
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/user/atlas/countries/init` | Initialize countries | ⚠️ User* |
| POST | `/user/atlas/cities/init` | Initialize cities | ⚠️ User* |

> *Note: Init endpoints currently require user auth but should be restricted to admin only.

### System Config (No API)
| Feature | Description | Status |
|---------|-------------|--------|
| Settings | Application configuration | Database Only |
| Audit Logs | Administrative action tracking | Database Only |

---

## 5. Country Data Fields

The `countries` table stores comprehensive country data:

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Country name | "United States" |
| `iso3` | ISO 3166-1 alpha-3 | "USA" |
| `iso2` | ISO 3166-1 alpha-2 | "US" |
| `numeric_code` | ISO 3166-1 numeric | "840" |
| `phonecode` | Phone prefix | "+1" |
| `capital` | Capital city | "Washington" |
| `currency` | Currency code | "USD" |
| `currency_name` | Currency name | "United States dollar" |
| `currency_symbol` | Currency symbol | "$" |
| `tld` | Top-level domain | ".us" |
| `native` | Native name | "United States" |
| `nationality` | Nationality | "American" |
| `timezones` | JSON array of timezones | See below |
| `latitude` | Latitude | 38.0 |
| `longitude` | Longitude | -97.0 |
| `emoji` | Flag emoji | "🇺🇸" |
| `emojiU` | Unicode emoji | "U+1F1FA U+1F1F8" |
| `region` | Continent/region | "Americas" |
| `subregion` | Subregion | "Northern America" |

**Timezone JSON Format**:
```json
[
  {
    "zoneName": "America/New_York",
    "gmtOffset": -18000,
    "gmtOffsetName": "UTC-05:00",
    "abbreviation": "EST",
    "tzName": "Eastern Standard Time"
  }
]
```

---

## 6. API Client Examples

### Search Countries by Region
```bash
curl -X GET "http://localhost:8000/api/v1/user/atlas/countries/search?region=Europe&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

### Search Countries by Currency
```bash
curl -X GET "http://localhost:8000/api/v1/user/atlas/countries/search?currency=EUR" \
  -H "Authorization: Bearer $TOKEN"
```

### Search Cities in Country
```bash
curl -X GET "http://localhost:8000/api/v1/user/atlas/cities/search?country_id=233&name=New&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Get All States in USA
```bash
curl -X GET "http://localhost:8000/api/v1/user/atlas/states/233" \
  -H "Authorization: Bearer $TOKEN"
```

### Initialize Country Data (Admin)
```bash
curl -X POST "http://localhost:8000/api/v1/user/atlas/countries/init" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## References

- **Atlas Router**: `src/app/presentation/http/controllers/atlas/router.py`
- **Countries Endpoint**: `src/app/presentation/http/controllers/atlas/countries.py`
- **Cities Endpoint**: `src/app/presentation/http/controllers/atlas/cities.py`
- **Init Endpoint**: `src/app/presentation/http/controllers/atlas/init.py`
- **Query Services**: `src/app/application/atlas/queries.py`
- **System Config Mapping**: `src/app/infrastructure/persistence_sqla/mappings/system_config.py`
