# API Documentation Standard

**Version:** 1.0  
**Last Updated:** December 1, 2025  
**Status:** ✅ Official Standard for All Frontend Documentation

---

## 📋 Overview

This document defines the official API documentation standard for all frontend documentation in `docs/frontend/`. Every API endpoint must follow this format to ensure consistency, clarity, and developer experience excellence.

---

## 🎯 Standard Format

### Complete API Endpoint Documentation Template

```typescript
// {METHOD} /api/v1/{scope}/{resource}/{action}
// Description: {Clear, one-sentence description of what this endpoint does}
// Authentication: {Required/Optional} ({Bearer token/API key/None})
// Rate Limit: {X requests per minute} (if applicable)
//
// Path Parameters:
//   - {param_name}: {type} - {description}
//
// Query Parameters:
//   - {param_name}?: {type} - {description} (optional)
//   - {param_name}: {type} - {description} (required)
//
// Request Body:
interface {EndpointName}Request {
  {field_name}: {type}; // {description}
  {field_name}?: {type}; // {description} (optional)
}

// Response:
interface {EndpointName}Response {
  {field_name}: {type}; // {description}
}

// TypeScript Implementation:
const {functionName} = async (
  {params}
): Promise<{EndpointName}Response> => {
  const response = await api.{method}('/api/v1/{path}', {body});
  return response.data;
};

// Example Request:
{
  "{field}": "{example_value}",
  "{field}": {example_value}
}

// Example Response (Success - 200):
{
  "{field}": "{example_value}",
  "{field}": {example_value},
  "{nested}": {
    "{field}": "{value}"
  }
}

// Example Response (Error - 400/401/403/404/500):
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

---

## 📐 Path Structure Standards

### User Endpoints
```
/api/v1/users/{resource}
/api/v1/{feature}              (user-scoped features)
```

**Examples:**
- `/api/v1/users/me/preferences`
- `/api/v1/chat/messages`
- `/api/v1/portfolio/`
- `/api/v1/dashboard/insights`

### Admin Endpoints
```
/api/v1/admin/{resource}
```

**Examples:**
- `/api/v1/admin/users`
- `/api/v1/admin/projects/{project_id}`
- `/api/v1/admin/system/health`

---

## 🔑 Authentication Documentation

### Required Authentication
```typescript
// Authentication: Required (Bearer token)
// Header: Authorization: Bearer {jwt_token}
```

### Optional Authentication
```typescript
// Authentication: Optional (Enhanced features with token)
```

### No Authentication
```typescript
// Authentication: None (Public endpoint)
```

---

## 📊 Complete Examples by Endpoint Type

### 1. GET Endpoint (Fetch Data)

```typescript
// GET /api/v1/users/me/preferences
// Description: Retrieve all user preference settings
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None

interface UserPreferencesResponse {
  user_id: string;
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  preferred_chains: string[];
  notification_settings: NotificationSettings;
  default_currency: string;
  theme: 'dark' | 'light';
}

const getPreferences = async (): Promise<UserPreferencesResponse> => {
  const response = await api.get('/api/v1/users/me/preferences');
  return response.data;
};

// Example Response (200 OK):
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "risk_tolerance": "moderate",
  "preferred_chains": ["ethereum", "arbitrum"],
  "notification_settings": {
    "push_enabled": true,
    "email_enabled": false
  },
  "default_currency": "USD",
  "theme": "dark"
}
```

---

### 2. POST Endpoint (Create Resource)

```typescript
// POST /api/v1/users/me/preferences/search/saved
// Description: Save a new search preset for quick access
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface SaveSearchRequest {
  name: string; // Display name for the saved search
  query: string; // Search query string
  filters: Record<string, any>; // Applied filters
}

// Response:
interface SavedSearchResponse {
  id: string;
  name: string;
  query: string;
  filters: Record<string, any>;
  created_at: string;
}

const saveSearch = async (
  search: SaveSearchRequest
): Promise<SavedSearchResponse> => {
  const response = await api.post(
    '/api/v1/users/me/preferences/search/saved',
    search
  );
  return response.data;
};

// Example Request:
{
  "name": "High Yield Stablecoins",
  "query": "stablecoin lending",
  "filters": {
    "min_apy": 5.0,
    "chains": ["ethereum", "arbitrum"],
    "risk_level": "LOW"
  }
}

// Example Response (201 Created):
{
  "id": "search-550e8400-e29b-41d4-a716-446655440000",
  "name": "High Yield Stablecoins",
  "query": "stablecoin lending",
  "filters": {
    "min_apy": 5.0,
    "chains": ["ethereum", "arbitrum"],
    "risk_level": "LOW"
  },
  "created_at": "2025-12-01T10:30:00Z"
}

// Example Error Response (400 Bad Request):
{
  "error": {
    "code": "INVALID_SEARCH_NAME",
    "message": "Search name must be between 1 and 50 characters",
    "details": {
      "field": "name",
      "provided_length": 0
    }
  }
}
```

---

### 3. PUT Endpoint (Update Resource)

```typescript
// PUT /api/v1/users/me/preferences/risk-tolerance
// Description: Update user's risk tolerance setting
// Authentication: Required (Bearer token)
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface UpdateRiskToleranceRequest {
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
}

// Response:
interface UserPreferencesResponse {
  user_id: string;
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  // ... other preference fields
}

const updateRiskTolerance = async (
  riskTolerance: string
): Promise<UserPreferencesResponse> => {
  const response = await api.put(
    '/api/v1/users/me/preferences/risk-tolerance',
    { risk_tolerance: riskTolerance }
  );
  return response.data;
};

// Example Request:
{
  "risk_tolerance": "aggressive"
}

// Example Response (200 OK):
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "risk_tolerance": "aggressive",
  "preferred_chains": ["ethereum", "arbitrum"],
  "notification_settings": {
    "push_enabled": true
  }
}
```

---

### 4. DELETE Endpoint (Remove Resource)

```typescript
// DELETE /api/v1/users/me/preferences/search/saved/{search_id}
// Description: Delete a saved search preset
// Authentication: Required (Bearer token)
//
// Path Parameters:
//   - search_id: string (UUID) - ID of the saved search to delete
//
// Query Parameters: None

interface DeleteResponse {
  success: boolean;
  message: string;
}

const deleteSavedSearch = async (
  searchId: string
): Promise<DeleteResponse> => {
  const response = await api.delete(
    `/api/v1/users/me/preferences/search/saved/${searchId}`
  );
  return response.data;
};

// Example Response (200 OK):
{
  "success": true,
  "message": "Saved search deleted successfully"
}

// Example Error Response (404 Not Found):
{
  "error": {
    "code": "SEARCH_NOT_FOUND",
    "message": "Saved search with ID 'search-123' not found",
    "details": {
      "search_id": "search-123"
    }
  }
}
```

---

### 5. Endpoint with Query Parameters

```typescript
// GET /api/v1/search/history
// Description: Retrieve user's recent search history with optional filtering
// Authentication: Required (Bearer token)
//
// Path Parameters: None
//
// Query Parameters:
//   - limit?: number - Maximum number of entries to return (default: 10, max: 50)
//   - search_type?: string - Filter by search type (graphrag|protocol|token|general)
//   - offset?: number - Pagination offset (default: 0)

interface SearchHistoryResponse {
  history: SearchHistoryEntry[];
  total: number;
  limit: number;
  offset: number;
}

interface SearchHistoryEntry {
  id: string;
  query: string;
  type: 'graphrag' | 'protocol' | 'token' | 'general';
  results_count: number;
  filters: Record<string, any>;
  created_at: string;
}

const getSearchHistory = async (
  filters?: {
    limit?: number;
    search_type?: string;
    offset?: number;
  }
): Promise<SearchHistoryResponse> => {
  const response = await api.get('/api/v1/search/history', { 
    params: filters 
  });
  return response.data;
};

// Example Request:
// GET /api/v1/search/history?limit=5&search_type=graphrag&offset=0

// Example Response (200 OK):
{
  "history": [
    {
      "id": "hist-550e8400",
      "query": "Aave V3 security analysis",
      "type": "graphrag",
      "results_count": 12,
      "filters": {
        "risk_level": "HIGH"
      },
      "created_at": "2025-12-01T10:25:00Z"
    },
    {
      "id": "hist-660e8400",
      "query": "best yield farming pools",
      "type": "protocol",
      "results_count": 8,
      "filters": {},
      "created_at": "2025-12-01T09:15:00Z"
    }
  ],
  "total": 28,
  "limit": 5,
  "offset": 0
}
```

---

### 6. Complex POST with Multiple Data Types

```typescript
// POST /api/v1/comparison/protocols
// Description: Compare 2-5 protocols across multiple dimensions
// Authentication: Required (Bearer token)
// Rate Limit: 10 requests per minute
//
// Path Parameters: None
// Query Parameters: None
//
// Request Body:
interface CompareProtocolsRequest {
  protocol_ids: string[]; // 2-5 protocol UUIDs (min: 2, max: 5)
  dimensions?: string[]; // Optional: ['risk', 'yield', 'security', 'network']
}

// Response:
interface ComparisonResponse {
  protocols: ProtocolDetail[];
  comparison_matrix: ComparisonMatrix;
  winner_by_dimension: Winners;
  trade_offs: TradeOff[];
  recommendation: AIRecommendation;
}

const compareProtocols = async (
  protocolIds: string[],
  dimensions?: string[]
): Promise<ComparisonResponse> => {
  const response = await api.post('/api/v1/comparison/protocols', {
    protocol_ids: protocolIds,
    dimensions,
  });
  return response.data;
};

// Example Request:
{
  "protocol_ids": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002",
    "550e8400-e29b-41d4-a716-446655440003"
  ],
  "dimensions": ["risk", "yield", "security"]
}

// Example Response (200 OK):
{
  "protocols": [
    {
      "protocol_id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Aave V3",
      "risk_score": 2.1,
      "apy_supply": 3.2,
      "audit_count": 8
    },
    {
      "protocol_id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Compound V3",
      "risk_score": 3.5,
      "apy_supply": 4.1,
      "audit_count": 6
    },
    {
      "protocol_id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "Morpho",
      "risk_score": 1.8,
      "apy_supply": 3.8,
      "audit_count": 4
    }
  ],
  "comparison_matrix": {
    "risk": {
      "metric": "Risk Score",
      "lower_is_better": true,
      "best": "Morpho",
      "worst": "Compound V3"
    },
    "yield": {
      "metric": "Supply APY",
      "lower_is_better": false,
      "best": "Compound V3",
      "worst": "Aave V3"
    }
  },
  "winner_by_dimension": {
    "safest": "Morpho",
    "highest_yield": "Compound V3",
    "most_secure": "Aave V3",
    "balanced": "Morpho"
  },
  "trade_offs": [
    {
      "dimension": "Risk vs Yield",
      "description": "Morpho is safest (1.8) but Compound offers higher yield (4.1% vs 3.8%)"
    }
  ],
  "recommendation": {
    "recommended_protocol": "Morpho",
    "reason": "Best balance of safety, yield, and security",
    "confidence": 0.85,
    "alternatives": ["Aave V3", "Compound V3"]
  }
}
```

---

## 🚨 Error Response Standards

### Standard Error Format
```typescript
interface ErrorResponse {
  error: {
    code: string; // Machine-readable error code
    message: string; // Human-readable error message
    details?: Record<string, any>; // Additional error context
    timestamp?: string; // ISO 8601 timestamp
  };
}
```

### Common HTTP Status Codes

**200 OK**: Successful GET, PUT, PATCH  
**201 Created**: Successful POST (resource created)  
**204 No Content**: Successful DELETE  
**400 Bad Request**: Invalid request parameters/body  
**401 Unauthorized**: Missing or invalid authentication  
**403 Forbidden**: Authenticated but insufficient permissions  
**404 Not Found**: Resource not found  
**422 Unprocessable Entity**: Validation error  
**429 Too Many Requests**: Rate limit exceeded  
**500 Internal Server Error**: Server error  
**503 Service Unavailable**: Temporary service unavailable  

### Error Code Naming Convention
```
{FEATURE}_{ERROR_TYPE}

Examples:
- PREFERENCES_INVALID_RISK_TOLERANCE
- SEARCH_NOT_FOUND
- ALERT_SUBSCRIPTION_LIMIT_EXCEEDED
- COMPARISON_TOO_MANY_PROTOCOLS
```

---

## ✅ Documentation Checklist

Every API endpoint documentation MUST include:

- [ ] HTTP Method (GET, POST, PUT, PATCH, DELETE)
- [ ] Complete path with `/api/v1/` prefix
- [ ] Clear one-sentence description
- [ ] Authentication requirements
- [ ] Path parameters (if any) with types and descriptions
- [ ] Query parameters (if any) with types, descriptions, and required/optional
- [ ] Request body interface (for POST/PUT/PATCH)
- [ ] Response interface with all fields documented
- [ ] TypeScript implementation example
- [ ] Example request body (for POST/PUT/PATCH)
- [ ] Example success response (with realistic data)
- [ ] Example error response (at least one common error)
- [ ] Rate limits (if applicable)

---

## 📚 Reference Examples

### Files Following This Standard
- ✅ `docs/frontend/user-modules/user/settings/FRONTEND_USER_SETTINGS_PREFERENCES.md`
- ✅ `docs/frontend/user-modules/user/alerts/FRONTEND_USER_RISK_ALERTS.md`
- ✅ `docs/frontend/user-modules/user/search/FRONTEND_USER_SEARCH_HISTORY.md`
- ✅ `docs/frontend/user-modules/user/comparison/FRONTEND_USER_PROTOCOL_COMPARISON.md`
- ✅ `docs/frontend/user-modules/user/dashboard/FRONTEND_USER_DASHBOARD.md`
- ✅ `docs/frontend/user-modules/user/markets/FRONTEND_USER_MARKETS.md`
- ✅ `docs/frontend/user-modules/user/portfolio/FRONTEND_USER_PORTFOLIO.md`
- ✅ `docs/frontend/user-modules/user/chat/FRONTEND_USER_CHAT_MAIN_V2.md`

---

## 🎯 Benefits of This Standard

### For Frontend Developers
- ✅ Copy-paste ready code examples
- ✅ Complete request/response types
- ✅ Clear error handling guidance
- ✅ Realistic example data
- ✅ No guesswork on parameter formats

### For Backend Developers
- ✅ Clear contract specification
- ✅ Documented error codes
- ✅ Validation requirements visible
- ✅ Example responses to match

### For Product/QA
- ✅ Testable specifications
- ✅ Clear success/error scenarios
- ✅ Documented edge cases
- ✅ Performance expectations (rate limits)

---

**Version**: 1.0  
**Status**: ✅ Official Standard  
**Compliance**: All new API documentation must follow this standard  
**Review**: Quarterly review for updates  

---

*This standard ensures world-class developer experience and eliminates ambiguity in API integration.*
