# Frontend Integration Overview

## Architecture Overview

The Anvil Backend follows a **Hexagonal Architecture** with a RESTful API layer. Frontend applications interact with the backend exclusively through HTTP endpoints.

```
┌─────────────────┐
│                 │
│   Frontend      │
│   (React/Vue)   │
│                 │
└────────┬────────┘
         │ HTTPS/WSS
         │
┌────────▼────────┐
│                 │
│  FastAPI Layer  │
│  (REST + WS)    │
│                 │
└────────┬────────┘
         │
┌────────▼────────┐
│                 │
│  Application    │
│  Layer          │
│                 │
└────────┬────────┘
         │
┌────────▼────────┐
│                 │
│  Domain Layer   │
│                 │
└─────────────────┘
```

---

## Base URL

**Production:** `https://api.anvil.com`
**Staging:** `https://staging-api.anvil.com`
**Local Development:** `http://localhost:8000`

---

## Authentication Flow

### 1. Registration
```typescript
POST /api/v1/account/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}

Response (201):
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 2. Login
```typescript
POST /api/v1/account/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response (200):
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

### 3. Authenticated Requests
```typescript
GET /api/v1/account/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

Response (200):
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "subscription_tier": "premium"
}
```

---

## API Client Setup

### React Example (Axios)

```typescript
// src/api/client.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

class ApiClient {
  private client: AxiosInstance;
  
  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Request interceptor (add auth token)
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor (handle errors)
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired, redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }
  
  // Authentication
  async login(email: string, password: string) {
    const response = await this.client.post('/api/v1/account/login', {
      email,
      password,
    });
    localStorage.setItem('access_token', response.data.access_token);
    return response.data;
  }
  
  async logout() {
    await this.client.delete('/api/v1/account/logout');
    localStorage.removeItem('access_token');
  }
  
  async getCurrentUser() {
    const response = await this.client.get('/api/v1/account/me');
    return response.data;
  }
  
  // Generic methods
  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get(url, { params });
    return response.data;
  }
  
  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post(url, data);
    return response.data;
  }
  
  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put(url, data);
    return response.data;
  }
  
  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete(url);
    return response.data;
  }
}

export const apiClient = new ApiClient(
  process.env.REACT_APP_API_URL || 'http://localhost:8000'
);
```

### Vue 3 Example (Fetch)

```typescript
// src/composables/useApi.ts
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useApi() {
  const loading = ref(false);
  const error = ref<string | null>(null);
  const router = useRouter();
  
  const getAuthHeader = () => {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };
  
  const handleResponse = async (response: Response) => {
    if (response.status === 401) {
      localStorage.removeItem('access_token');
      router.push('/login');
      throw new Error('Unauthorized');
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    return response.json();
  };
  
  const request = async <T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> => {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await fetch(`${BASE_URL}${url}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader(),
          ...options.headers,
        },
      });
      
      return await handleResponse(response);
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      loading.value = false;
    }
  };
  
  return {
    loading,
    error,
    get: <T>(url: string) => request<T>(url),
    post: <T>(url: string, data: any) => 
      request<T>(url, { method: 'POST', body: JSON.stringify(data) }),
    put: <T>(url: string, data: any) => 
      request<T>(url, { method: 'PUT', body: JSON.stringify(data) }),
    delete: <T>(url: string) => 
      request<T>(url, { method: 'DELETE' }),
  };
}
```

---

## Error Handling

### Standard Error Response

```typescript
{
  "detail": "Error message",
  "status_code": 400,
  "error_code": "INVALID_INPUT"
}
```

### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid data format |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

### Error Handling Example

```typescript
try {
  const data = await apiClient.post('/api/v1/endpoint', payload);
  // Success
} catch (error) {
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        showError('Invalid input. Please check your data.');
        break;
      case 401:
        redirectToLogin();
        break;
      case 403:
        showError('You don\'t have permission for this action.');
        break;
      case 404:
        showError('Resource not found.');
        break;
      case 429:
        showError('Too many requests. Please try again later.');
        break;
      default:
        showError('An error occurred. Please try again.');
    }
  }
}
```

---

## Rate Limiting

**Limits:**
- **Public endpoints:** 100 requests/minute/IP
- **Authenticated endpoints:** 1000 requests/minute/user
- **Premium users:** 5000 requests/minute/user

**Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

**Handle Rate Limits:**
```typescript
if (error.response?.status === 429) {
  const resetTime = error.response.headers['x-ratelimit-reset'];
  const waitSeconds = resetTime - Math.floor(Date.now() / 1000);
  
  showError(`Rate limit exceeded. Try again in ${waitSeconds} seconds.`);
}
```

---

## WebSocket Integration

### Connection

```typescript
// src/services/websocket.ts
class WebSocketService {
  private ws: WebSocket | null = null;
  
  connect(token: string) {
    const url = `wss://api.anvil.com/ws?token=${token}`;
    
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Reconnect logic
      setTimeout(() => this.connect(token), 5000);
    };
  }
  
  subscribe(channel: string) {
    this.send({
      action: 'subscribe',
      channel,
    });
  }
  
  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
  
  private handleMessage(data: any) {
    // Handle different message types
    switch (data.type) {
      case 'price_update':
        // Update price display
        break;
      case 'arbitrage_opportunity':
        // Show notification
        break;
      case 'trade_executed':
        // Update portfolio
        break;
    }
  }
  
  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}

export const wsService = new WebSocketService();
```

---

## State Management

### React Context Example

```typescript
// src/context/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface User {
  id: string;
  email: string;
  full_name: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Check if user is logged in on mount
    const initAuth = async () => {
      try {
        const userData = await apiClient.getCurrentUser();
        setUser(userData);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    
    initAuth();
  }, []);
  
  const login = async (email: string, password: string) => {
    const response = await apiClient.login(email, password);
    setUser(response.user);
  };
  
  const logout = async () => {
    await apiClient.logout();
    setUser(null);
  };
  
  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

---

## Pagination

### Request

```typescript
GET /api/v1/endpoint?page=1&per_page=20
```

### Response

```typescript
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

### Pagination Hook

```typescript
function usePagination<T>(endpoint: string, perPage: number = 20) {
  const [data, setData] = useState<T[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  
  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(endpoint, {
        page,
        per_page: perPage,
      });
      
      setData(response.items);
      setTotalPages(response.total_pages);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchData();
  }, [page]);
  
  return {
    data,
    loading,
    page,
    totalPages,
    nextPage: () => setPage(p => Math.min(p + 1, totalPages)),
    prevPage: () => setPage(p => Math.max(p - 1, 1)),
    goToPage: setPage,
  };
}
```

---

## Next Steps

1. **Read feature-specific integration guides:**
   - [Hunter AI Integration](./HUNTER_AI_INTEGRATION.md)
   - [ULTRA Arbitrage Integration](./ULTRA_ARBITRAGE_INTEGRATION.md)
   - [Subscription Integration](./SUBSCRIPTION_INTEGRATION.md)
   - [Wallet Integration](./WALLET_INTEGRATION.md)

2. **Test API endpoints:** Use the interactive docs at `/docs`

3. **Join developer community:** Slack channel for support

4. **Report issues:** GitHub issues or support@anvil.com
