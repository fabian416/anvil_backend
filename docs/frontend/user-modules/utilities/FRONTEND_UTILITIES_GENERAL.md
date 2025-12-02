# FRONTEND_UTILITIES_GENERAL

## General Utilities Module

**User Type:** Public/Authenticated  
**Module:** General Utilities - Health, Status, Version  
**Route:** `/`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**General Utilities** - Health Checks, Version Info, and System Status

### Description
Essential utility endpoints for monitoring application health, version information, and system status checks.

### Key Capabilities
- ✅ Health check endpoint
- ✅ API version information
- ✅ System status monitoring
- ✅ Service availability checks

---

## 🔌 API Integration

### 1. Health Check

```typescript
// GET /api/v1/health
// Description: Check API health status
// Authentication: None (Public)

interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  services: {
    database: 'up' | 'down';
    redis: 'up' | 'down';
    celery: 'up' | 'down';
  };
}

const checkHealth = async (): Promise<HealthCheckResponse> => {
  const response = await api.get('/api/v1/health');
  return response.data;
};

// Example Response (200 OK):
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-01T12:00:00Z",
  "services": {
    "database": "up",
    "redis": "up",
    "celery": "up"
  }
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: General Utilities*
