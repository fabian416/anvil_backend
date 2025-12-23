# System Health API Documentation

> **Complete API Documentation**  
> **Base URLs**: `/api/admin/metrics`, `/api/admin/stats`, `/api/v1/admin/retry`

---

## 📊 Metrics Endpoints

- **GET** `/api/admin/metrics` - Get system metrics

---

## 📈 Stats Endpoints

- **GET** `/api/admin/stats/` - Get system statistics

---

## 🔄 Retry System Endpoints

### Services
- **GET** `/api/v1/admin/retry/services` - List services
- **GET** `/api/v1/admin/retry/services/{service_name}` - Get service status
- **POST** `/api/v1/admin/retry/services/{service_name}/disable` - Disable service
- **POST** `/api/v1/admin/retry/services/{service_name}/enable` - Enable service

### Circuit Breakers
- **GET** `/api/v1/admin/retry/circuit-breakers` - Get circuit breakers
- **POST** `/api/v1/admin/retry/circuit-breakers/{service_name}/reset` - Reset circuit breaker

### Metrics
- **GET** `/api/v1/admin/retry/metrics/{service_name}` - Get service metrics

---

## ⚠️ Error Handling

| Status | Error Code | Description |
|--------|------------|-------------|
| `401` | `AuthenticationError` | Not authenticated |
| `403` | `AuthorizationError` | Not authorized |
| `404` | `NotFoundError` | Service not found |
| `503` | `DataMapperError` | Service unavailable |

---

## 🔐 Authentication

All endpoints require admin authentication with Bearer token.
