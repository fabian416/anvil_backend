# FRONTEND_UTILITIES_ATLAS

## Atlas Location Services Module

**User Type:** Authenticated User  
**Module:** Atlas - Geographic Data Services  
**Route:** `/atlas`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Atlas Location Services** - Countries, Cities, States, and Geographic Data

### Description
Comprehensive geographic data API providing access to countries, cities, states/provinces, and location-based services for user profile management and localization features.

### Key Capabilities
- ✅ Search countries with filters
- ✅ Search cities by country/state
- ✅ List states/provinces by country
- ✅ ISO code lookups (ISO2, ISO3)
- ✅ Currency and region filtering
- ✅ Pagination support
- ✅ Multi-language support

---

## 🔌 API Integration

### 1. Search Countries

```typescript
// GET /api/v1/atlas/countries/search
// Description: Search and filter countries with pagination
// Authentication: Required (Bearer token)
//
// Query Parameters:
//   - name?: string - Country name (partial match)
//   - iso2?: string - ISO 3166-1 alpha-2 code (e.g., "US", "GB")
//   - iso3?: string - ISO 3166-1 alpha-3 code (e.g., "USA", "GBR")
//   - region?: string - Geographic region (e.g., "Americas", "Europe", "Asia")
//   - subregion?: string - Geographic subregion (e.g., "Northern America", "Western Europe")
//   - currency?: string - Currency code (e.g., "USD", "EUR", "GBP")
//   - limit?: number - Results per page (default: 10, max: 100)
//   - offset?: number - Pagination offset (default: 0)

interface SearchCountriesRequest {
  name?: string;
  iso2?: string;
  iso3?: string;
  region?: string;
  subregion?: string;
  currency?: string;
  limit?: number;
  offset?: number;
}

interface Country {
  id: number;
  name: string;
  iso2: string; // "US"
  iso3: string; // "USA"
  numeric_code: string; // "840"
  phone_code: string; // "+1"
  capital: string;
  currency: string; // "USD"
  currency_name: string; // "United States dollar"
  currency_symbol: string; // "$"
  tld: string; // ".us"
  native: string; // Native name
  region: string; // "Americas"
  subregion: string; // "Northern America"
  nationality: string; // "American"
  timezones: Timezone[];
  latitude: number;
  longitude: number;
  emoji: string; // "🇺🇸"
  emojiU: string; // Unicode
}

interface Timezone {
  zoneName: string; // "America/New_York"
  gmtOffset: number; // -18000
  gmtOffsetName: string; // "UTC-05:00"
  abbreviation: string; // "EST"
  tzName: string; // "Eastern Standard Time"
}

interface SearchCountriesResponse {
  countries: Country[];
  total: number;
  limit: number;
  offset: number;
}

const searchCountries = async (
  filters: SearchCountriesRequest
): Promise<SearchCountriesResponse> => {
  const response = await api.get('/api/v1/atlas/countries/search', {
    params: filters,
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/atlas/countries/search?region=Americas&currency=USD&limit=5

// Example Response (200 OK):
{
  "countries": [
    {
      "id": 1,
      "name": "United States",
      "iso2": "US",
      "iso3": "USA",
      "numeric_code": "840",
      "phone_code": "+1",
      "capital": "Washington",
      "currency": "USD",
      "currency_name": "United States dollar",
      "currency_symbol": "$",
      "tld": ".us",
      "native": "United States",
      "region": "Americas",
      "subregion": "Northern America",
      "nationality": "American",
      "timezones": [
        {
          "zoneName": "America/New_York",
          "gmtOffset": -18000,
          "gmtOffsetName": "UTC-05:00",
          "abbreviation": "EST",
          "tzName": "Eastern Standard Time"
        },
        {
          "zoneName": "America/Chicago",
          "gmtOffset": -21600,
          "gmtOffsetName": "UTC-06:00",
          "abbreviation": "CST",
          "tzName": "Central Standard Time"
        }
      ],
      "latitude": 38.0,
      "longitude": -97.0,
      "emoji": "🇺🇸",
      "emojiU": "U+1F1FA U+1F1F8"
    }
  ],
  "total": 1,
  "limit": 5,
  "offset": 0
}

// Example Error Response (401 Unauthorized):
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Valid authentication token required",
    "details": {}
  }
}
```

---

### 2. Search Cities

```typescript
// GET /api/v1/atlas/cities/search
// Description: Search cities with multiple filter options
// Authentication: Required (Bearer token)
//
// Query Parameters:
//   - name?: string - City name (partial match)
//   - country_id?: number - Country ID
//   - state_id?: string - State/province ID
//   - state_code?: string - State code (e.g., "CA", "TX")
//   - state_name?: string - State name (e.g., "California")
//   - country_code?: string - Country ISO2 code (e.g., "US")
//   - wikiDataId?: string - WikiData identifier
//   - limit?: number - Results per page (default: 10, max: 100)
//   - offset?: number - Pagination offset (default: 0)

interface SearchCitiesRequest {
  name?: string;
  country_id?: number;
  state_id?: string;
  state_code?: string;
  state_name?: string;
  country_code?: string;
  wikiDataId?: string;
  limit?: number;
  offset?: number;
}

interface City {
  id: number;
  name: string;
  state_id: string;
  state_code: string;
  state_name: string;
  country_id: number;
  country_code: string;
  country_name: string;
  latitude: number;
  longitude: number;
  wikiDataId: string;
}

interface SearchCitiesResponse {
  cities: City[];
  total: number;
  limit: number;
  offset: number;
}

const searchCities = async (
  filters: SearchCitiesRequest
): Promise<SearchCitiesResponse> => {
  const response = await api.get('/api/v1/atlas/cities/search', {
    params: filters,
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/atlas/cities/search?country_code=US&state_code=CA&name=San&limit=5

// Example Response (200 OK):
{
  "cities": [
    {
      "id": 111968,
      "name": "San Francisco",
      "state_id": "1416",
      "state_code": "CA",
      "state_name": "California",
      "country_id": 233,
      "country_code": "US",
      "country_name": "United States",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "wikiDataId": "Q62"
    },
    {
      "id": 111969,
      "name": "San Diego",
      "state_id": "1416",
      "state_code": "CA",
      "state_name": "California",
      "country_id": 233,
      "country_code": "US",
      "country_name": "United States",
      "latitude": 32.7157,
      "longitude": -117.1611,
      "wikiDataId": "Q16552"
    },
    {
      "id": 111970,
      "name": "San Jose",
      "state_id": "1416",
      "state_code": "CA",
      "state_name": "California",
      "country_id": 233,
      "country_code": "US",
      "country_name": "United States",
      "latitude": 37.3382,
      "longitude": -121.8863,
      "wikiDataId": "Q16553"
    }
  ],
  "total": 15,
  "limit": 5,
  "offset": 0
}
```

---

### 3. List States by Country

```typescript
// GET /api/v1/atlas/states/{country_id}
// Description: Get all states/provinces for a specific country
// Authentication: Required (Bearer token)
//
// Path Parameters:
//   - country_id: number - Country ID (e.g., 233 for USA)

interface State {
  id: number;
  name: string;
  country_id: number;
  country_code: string;
  country_name: string;
  state_code: string;
  type: string; // "state", "province", "territory", etc.
  latitude: number;
  longitude: number;
}

const listStatesByCountry = async (
  countryId: number
): Promise<State[]> => {
  const response = await api.get(`/api/v1/atlas/states/${countryId}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/atlas/states/233

// Example Response (200 OK):
[
  {
    "id": 1416,
    "name": "California",
    "country_id": 233,
    "country_code": "US",
    "country_name": "United States",
    "state_code": "CA",
    "type": "state",
    "latitude": 36.7783,
    "longitude": -119.4179
  },
  {
    "id": 1417,
    "name": "Texas",
    "country_id": 233,
    "country_code": "US",
    "country_name": "United States",
    "state_code": "TX",
    "type": "state",
    "latitude": 31.9686,
    "longitude": -99.9018
  }
]

// Example Error Response (404 Not Found):
{
  "error": {
    "code": "COUNTRY_NOT_FOUND",
    "message": "Country with ID 9999 not found",
    "details": {
      "country_id": 9999
    }
  }
}
```

---

## 🔗 React Hooks

### useCountries Hook

```typescript
export function useCountries(filters?: SearchCountriesRequest) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['countries', filters],
    queryFn: async () => {
      const response = await api.get('/api/v1/atlas/countries/search', {
        params: filters
      });
      return response.data;
    },
  });
  
  return {
    countries: data?.countries || [],
    total: data?.total || 0,
    isLoading,
    error,
  };
}

// Usage:
const { countries, isLoading } = useCountries({ region: 'Americas' });
```

### useCities Hook

```typescript
export function useCities(filters?: SearchCitiesRequest) {
  const { data, isLoading } = useQuery({
    queryKey: ['cities', filters],
    queryFn: async () => {
      const response = await api.get('/api/v1/atlas/cities/search', {
        params: filters
      });
      return response.data;
    },
    enabled: !!filters?.country_id || !!filters?.country_code,
  });
  
  return {
    cities: data?.cities || [],
    total: data?.total || 0,
    isLoading,
  };
}

// Usage:
const { cities } = useCities({ country_code: 'US', state_code: 'CA' });
```

### useStates Hook

```typescript
export function useStates(countryId?: number) {
  const { data, isLoading } = useQuery({
    queryKey: ['states', countryId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/atlas/states/${countryId}`);
      return response.data;
    },
    enabled: !!countryId,
  });
  
  return {
    states: data || [],
    isLoading,
  };
}

// Usage:
const { states } = useStates(233); // USA
```

---

## 🎨 React Components

### CountrySelector Component

```typescript
export function CountrySelector({ 
  value, 
  onChange 
}: { 
  value?: number; 
  onChange: (countryId: number) => void;
}) {
  const { countries, isLoading } = useCountries({ limit: 250 });
  
  return (
    <select 
      value={value} 
      onChange={(e) => onChange(Number(e.target.value))}
      disabled={isLoading}
    >
      <option value="">Select Country</option>
      {countries.map(country => (
        <option key={country.id} value={country.id}>
          {country.emoji} {country.name}
        </option>
      ))}
    </select>
  );
}
```

### CityAutocomplete Component

```typescript
export function CityAutocomplete({ 
  countryId,
  onSelect 
}: { 
  countryId: number;
  onSelect: (city: City) => void;
}) {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  
  const { cities, isLoading } = useCities({
    country_id: countryId,
    name: debouncedSearch,
    limit: 10,
  });
  
  return (
    <div className="autocomplete">
      <input 
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search city..."
      />
      
      {isLoading && <div>Loading...</div>}
      
      <ul>
        {cities.map(city => (
          <li 
            key={city.id}
            onClick={() => onSelect(city)}
          >
            {city.name}, {city.state_code}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 🎭 User Flows

### Flow 1: User Profile Location Setup

```
1. User navigates to Profile Settings
   ↓
2. Sees Country dropdown
   ↓
3. GET /api/v1/atlas/countries/search?limit=250
   ↓
4. User selects "United States" (id: 233)
   ↓
5. State dropdown becomes enabled
   ↓
6. GET /api/v1/atlas/states/233
   ↓
7. User selects "California" (state_code: CA)
   ↓
8. City autocomplete becomes enabled
   ↓
9. User types "San F" in city search
   ↓
10. GET /api/v1/atlas/cities/search?country_id=233&state_code=CA&name=San F
   ↓
11. User selects "San Francisco"
   ↓
12. PUT /api/v1/account/me (save location to profile)
```

---

## ⚠️ Error Handling

```typescript
const handleLocationError = (error: any) => {
  switch (error.code) {
    case 'COUNTRY_NOT_FOUND':
      toast.error('Country not found. Please select from the list.');
      break;
      
    case 'AUTHENTICATION_REQUIRED':
      toast.error('Please log in to access location services.');
      redirectToLogin();
      break;
      
    default:
      toast.error('Unable to load location data. Please try again.');
  }
};
```

---

## 🌍 Use Cases

### 1. User Registration
- Country/city selection during signup
- Timezone detection
- Currency preference

### 2. User Profile
- Update location information
- Display local time
- Show relevant content by region

### 3. DeFi Platform Features
- Regional protocol availability
- Compliance restrictions by country
- Localized content and pricing

### 4. Analytics
- User distribution by country/city
- Regional engagement metrics
- Market expansion insights

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Atlas Location Services*  
*Backend Status: ✅ 100% Implemented (3 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
