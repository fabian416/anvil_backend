# Security Audit Guide

**Version**: 1.0  
**Last Updated**: December 1, 2025  
**Target Audience**: Security Engineers, DevOps

---

## 📋 Overview

Comprehensive security audit checklist and guidelines for the Anvil Backend platform. This guide covers authentication, authorization, data protection, API security, and infrastructure hardening.

---

## 🔐 Authentication & Authorization

### JWT Security

**Current Implementation**:
- JWT tokens for authentication
- Session-based approach with database backing
- Bearer token in Authorization header

**Security Checklist**:
- ✅ Token expiration configured (default: 15 minutes access, 7 days refresh)
- ✅ Secure token signing algorithm (RS256 or HS256 with strong secret)
- ✅ Token refresh mechanism implemented
- ⚠️ **TODO**: Implement token rotation on refresh
- ⚠️ **TODO**: Add token revocation/blacklist system
- ⚠️ **TODO**: Implement device fingerprinting for suspicious activity

**Recommendations**:
```python
# Token Configuration (verify in settings)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
JWT_ALGORITHM = "RS256"  # Use RSA for production
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Must be strong random key

# Additional security
JWT_ISSUER = "anvil-backend"
JWT_AUDIENCE = "anvil-frontend"
```

### Session Management

**Security Checklist**:
- ✅ Session cleanup task scheduled (Celery background task)
- ✅ Session expiration enforced
- ⚠️ **TODO**: Implement concurrent session limits
- ⚠️ **TODO**: Add session activity monitoring
- ⚠️ **TODO**: Log suspicious session patterns

---

## 🛡️ API Security

### Rate Limiting

**Status**: ⚠️ **NOT IMPLEMENTED**

**Required Implementation**:
```python
# Install: pip install slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to routes
@limiter.limit("5/minute")
@router.post("/api/v1/auth/login")
async def login(...):
    pass

# Per-user limits for authenticated endpoints
@limiter.limit("100/minute")
@router.get("/api/v1/graph/search")
async def search(...):
    pass
```

**Recommended Limits**:
- Authentication endpoints: 5 requests/minute/IP
- Search endpoints: 100 requests/minute/user
- Read endpoints: 300 requests/minute/user
- Write endpoints: 60 requests/minute/user
- Admin endpoints: 30 requests/minute/admin

### CORS Configuration

**Security Checklist**:
- ✅ CORS middleware configured
- ⚠️ **TODO**: Restrict allowed origins in production
- ⚠️ **TODO**: Limit allowed methods
- ⚠️ **TODO**: Disable credentials for public endpoints

**Production CORS**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.anvil.com",
        "https://admin.anvil.com"
    ],  # NO wildcards in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
```

### Input Validation

**Security Checklist**:
- ✅ Pydantic models for request validation
- ✅ Type checking with mypy
- ⚠️ **TODO**: Add length limits on all text fields
- ⚠️ **TODO**: Implement sanitization for rich text
- ⚠️ **TODO**: Validate file uploads (size, type, content)

---

## 🔒 Data Protection

### Sensitive Data Handling

**Current Practices**:
- ✅ Passwords hashed with bcrypt
- ✅ Secrets stored in `.secrets.toml` (not in git)
- ✅ Environment variables for production secrets

**Security Checklist**:
- ✅ Never log passwords, tokens, or API keys
- ✅ Mask sensitive data in error messages
- ⚠️ **TODO**: Encrypt sensitive database fields (PII)
- ⚠️ **TODO**: Implement data retention policies
- ⚠️ **TODO**: Add GDPR compliance tools (data export/deletion)

### Database Security

**Security Checklist**:
- ✅ Parameterized queries (SQLAlchemy ORM)
- ✅ Connection pooling configured
- ⚠️ **TODO**: Enable database encryption at rest
- ⚠️ **TODO**: Implement database audit logging
- ⚠️ **TODO**: Regular backup verification
- ⚠️ **TODO**: Least privilege database users

**Database Hardening**:
```sql
-- Create read-only user for analytics
CREATE USER analytics_user WITH PASSWORD 'strong_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;

-- Application user with limited permissions
CREATE USER app_user WITH PASSWORD 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- Do NOT grant DROP, CREATE, ALTER
```

---

## 🌐 Network Security

### HTTPS/TLS

**Security Checklist**:
- ⚠️ **TODO**: Enforce HTTPS in production (no HTTP)
- ⚠️ **TODO**: Configure TLS 1.3 minimum
- ⚠️ **TODO**: Implement HSTS headers
- ⚠️ **TODO**: Use valid SSL certificates (Let's Encrypt)

**Required Headers**:
```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### WebSocket Security

**Security Checklist**:
- ✅ JWT authentication on WebSocket connection
- ✅ User-specific channels
- ⚠️ **TODO**: Rate limit WebSocket messages
- ⚠️ **TODO**: Implement connection timeout
- ⚠️ **TODO**: Add message size limits

---

## 🚨 Monitoring & Incident Response

### Security Logging

**Required Logs**:
- Authentication attempts (success/failure)
- Authorization failures
- Suspicious patterns (repeated failures)
- Admin actions
- Data access patterns
- API rate limit violations

**Implementation**:
```python
import logging

security_logger = logging.getLogger("security")

# Log failed auth
security_logger.warning(
    "Failed login attempt",
    extra={
        "user_email": email,
        "ip_address": request.client.host,
        "timestamp": datetime.utcnow(),
    }
)

# Log admin actions
security_logger.info(
    "Admin action",
    extra={
        "admin_id": admin_id,
        "action": "delete_user",
        "target_id": user_id,
    }
)
```

### Intrusion Detection

**Security Checklist**:
- ⚠️ **TODO**: Implement failed login detection (5 failures = lock account)
- ⚠️ **TODO**: Add IP-based blocking for repeated violations
- ⚠️ **TODO**: Monitor for SQL injection attempts
- ⚠️ **TODO**: Detect unusual API usage patterns
- ⚠️ **TODO**: Set up alerts for critical security events

---

## 🧪 Security Testing

### Automated Testing

**Required Tests**:
- Authentication bypass attempts
- Authorization escalation attempts
- SQL injection tests
- XSS tests
- CSRF tests
- API fuzzing

**Tools**:
- OWASP ZAP for vulnerability scanning
- SQLMap for SQL injection testing
- Burp Suite for API testing
- pytest-security for unit tests

### Penetration Testing

**Recommended Schedule**:
- Before production launch
- After major feature releases
- Quarterly security audits
- After security incidents

---

## 📋 Security Checklist Summary

### Critical (Must Fix Before Production)
- [ ] Implement rate limiting on all endpoints
- [ ] Restrict CORS origins (no wildcards)
- [ ] Enforce HTTPS only
- [ ] Add security headers middleware
- [ ] Implement token rotation
- [ ] Configure database encryption at rest
- [ ] Set up security logging
- [ ] Implement failed login detection

### High Priority (Fix Within 30 Days)
- [ ] Add concurrent session limits
- [ ] Implement IP-based blocking
- [ ] Add data retention policies
- [ ] Enable database audit logging
- [ ] Set up automated security scanning
- [ ] Implement GDPR compliance tools

### Medium Priority (Fix Within 90 Days)
- [ ] Add device fingerprinting
- [ ] Implement advanced intrusion detection
- [ ] Set up security monitoring dashboard
- [ ] Conduct penetration testing
- [ ] Create incident response plan

---

## 🔧 Tools & Resources

**Security Tools**:
- `slowapi` - Rate limiting
- `python-jose` - JWT handling
- `bcrypt` - Password hashing
- `cryptography` - Encryption
- `bandit` - Security linting

**Monitoring**:
- Sentry - Error tracking
- Datadog - APM & logging
- Prometheus - Metrics
- Grafana - Dashboards

---

*Guide Version: 1.0*  
*Security Contact: security@anvil.com*  
*Last Security Audit: TBD*
