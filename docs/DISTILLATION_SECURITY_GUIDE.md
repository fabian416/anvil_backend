# Request Distillation System - Security Guide

## Overview

This document covers security features, rate limiting, PII anonymization, and security best practices for the Request Distillation System.

**Document Version**: 1.0  
**Last Updated**: 2025-12-01  
**Status**: Complete

---

## Table of Contents

1. [Prompt Injection Detection](#prompt-injection-detection)
2. [Rate Limiting](#rate-limiting)
3. [PII Anonymization](#pii-anonymization)
4. [Security Best Practices](#security-best-practices)
5. [Monitoring & Alerts](#monitoring--alerts)

---

## Prompt Injection Detection

### Overview

The distillation system includes comprehensive prompt injection detection to block malicious requests before they reach your main LLM.

### Detection Patterns

**Implemented** (20+ patterns):
- Direct instruction manipulation (`ignore previous instructions`)
- System role manipulation (`you are now a...`)
- Prompt leaking (`show me your prompt`)
- Code execution attempts (`eval()`, `<script>`)
- SQL injection patterns
- Admin/privilege escalation
- Token manipulation
- Jailbreak patterns (DAN mode, developer mode)

### Detection Method

**File**: `src/app/domain/services/distillation/prompt_injection_detector.py`

```python
from app.domain.services.distillation.prompt_injection_detector import PromptInjectionDetector

detector = PromptInjectionDetector()

# Basic detection
is_malicious, confidence, patterns = detector.detect(user_message)

# Comprehensive analysis
result = detector.detect_suspicious_patterns(user_message)
# Returns: {
#     "is_malicious": bool,
#     "confidence": float,
#     "matched_patterns": List[str],
#     "entropy": float,
#     "has_excessive_special_chars": bool,
#     "has_unusual_structure": bool,
# }
```

### Confidence Scoring

**Calculation**:
- Base: `0.3 * pattern_count + 0.4`
- Critical keywords: `+0.15` each
- High entropy (>0.9): `+0.1`
- Excessive special chars (>30%): `+0.1`
- Unusual structure: `+0.05`
- **Threshold**: `0.6` (60% confidence)

### Entropy Analysis

Shannon entropy calculation to detect random/malicious input:
- Normal English text: ~4-5 bits
- Random/malicious: >5 bits
- Normalized to 0-1 range

### Heuristics

**Special Characters**:
- Triggers if >30% of message is special characters
- Common in code injection attempts

**Structure Analysis**:
- Very long words (avg >15 chars)
- Excessive capitalization
- Repeated characters (5+ in a row)
- Excessive newlines (>10)

---

## Rate Limiting

### Implementation Guide

#### Redis-Based Rate Limiter

**File**: `src/app/infrastructure/distillation/rate_limiter.py` (create this)

```python
import redis
from typing import Optional
from datetime import timedelta

class DistillationRateLimiter:
    """
    Redis-backed rate limiter for distillation requests.
    
    Implements sliding window algorithm with both per-user
    and global rate limits.
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        per_user_limit: int = 100,  # per hour
        global_limit: int = 10000,  # per hour
        window_seconds: int = 3600,
    ):
        self._redis = redis_client
        self._per_user_limit = per_user_limit
        self._global_limit = global_limit
        self._window = window_seconds
    
    async def check_user_limit(self, user_id: str) -> bool:
        """Check if user is within rate limit."""
        key = f"distillation:ratelimit:user:{user_id}"
        count = await self._redis.incr(key)
        
        if count == 1:
            await self._redis.expire(key, self._window)
        
        return count <= self._per_user_limit
    
    async def check_global_limit(self) -> bool:
        """Check if system is within global rate limit."""
        key = "distillation:ratelimit:global"
        count = await self._redis.incr(key)
        
        if count == 1:
            await self._redis.expire(key, self._window)
        
        return count <= self._global_limit
    
    async def check_limits(self, user_id: str) -> tuple[bool, str]:
        """
        Check both user and global limits.
        
        Returns:
            (allowed: bool, reason: str)
        """
        # Check global limit first (cheaper)
        if not await self.check_global_limit():
            return (False, "Global rate limit exceeded")
        
        # Check user limit
        if not await self.check_user_limit(user_id):
            return (False, "User rate limit exceeded")
        
        return (True, "")
    
    async def get_user_remaining(self, user_id: str) -> int:
        """Get remaining requests for user."""
        key = f"distillation:ratelimit:user:{user_id}"
        count = await self._redis.get(key)
        
        if count is None:
            return self._per_user_limit
        
        return max(0, self._per_user_limit - int(count))
```

#### Integration

**In orchestrator** (`request_distillator.py`):

```python
async def validate(self, user_message: str, ...) -> DistillationResult:
    # 1. Check rate limits
    if self._rate_limiter:
        allowed, reason = await self._rate_limiter.check_limits(str(user_id))
        if not allowed:
            return DistillationResult(
                success=False,
                message=f"Rate limit exceeded: {reason}",
                reason="rate_limit",
                confidence=1.0,
                ...
            )
    
    # 2. Continue with normal validation
    ...
```

### Configuration

**In `config.toml`**:

```toml
[distillation.rate_limiting]
enabled = true
per_user_limit = 100      # requests per hour
global_limit = 10000      # requests per hour
window_seconds = 3600     # 1 hour
```

### Response Headers

Add rate limit info to responses:

```python
response.headers["X-RateLimit-Limit"] = str(per_user_limit)
response.headers["X-RateLimit-Remaining"] = str(remaining)
response.headers["X-RateLimit-Reset"] = str(reset_timestamp)
```

---

## PII Anonymization

### Overview

Anonymize personally identifiable information before storing in telemetry.

### Implementation

**File**: `src/app/infrastructure/distillation/pii_anonymizer.py` (create this)

```python
import re
import hashlib
from typing import Dict, List

class PIIAnonymizer:
    """
    Anonymize PII in user messages.
    
    Uses pattern matching and hashing to protect sensitive data.
    """
    
    # PII patterns
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b'
    SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
    CREDIT_CARD_PATTERN = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    WALLET_ADDRESS_PATTERN = r'\b0x[a-fA-F0-9]{40}\b'
    
    def __init__(self, hash_salt: str = "distillation-pii"):
        self._salt = hash_salt
    
    def anonymize(self, text: str) -> tuple[str, Dict[str, List[str]]]:
        """
        Anonymize PII in text.
        
        Returns:
            (anonymized_text, pii_found)
        """
        pii_found = {}
        anonymized = text
        
        # Email addresses
        emails = re.findall(self.EMAIL_PATTERN, text)
        if emails:
            pii_found["emails"] = emails
            for email in emails:
                anonymized = anonymized.replace(email, "[EMAIL]")
        
        # Phone numbers
        phones = re.findall(self.PHONE_PATTERN, text)
        if phones:
            pii_found["phones"] = phones
            for phone in phones:
                anonymized = anonymized.replace(phone, "[PHONE]")
        
        # SSN
        ssns = re.findall(self.SSN_PATTERN, text)
        if ssns:
            pii_found["ssns"] = ["[REDACTED]"] * len(ssns)
            for ssn in ssns:
                anonymized = anonymized.replace(ssn, "[SSN]")
        
        # Credit cards
        cards = re.findall(self.CREDIT_CARD_PATTERN, text)
        if cards:
            pii_found["credit_cards"] = ["[REDACTED]"] * len(cards)
            for card in cards:
                anonymized = anonymized.replace(card, "[CARD]")
        
        # Wallet addresses
        wallets = re.findall(self.WALLET_ADDRESS_PATTERN, text)
        if wallets:
            pii_found["wallets"] = wallets  # OK to log (public)
            for wallet in wallets:
                # Hash wallet for anonymity
                hashed = self._hash_value(wallet)
                anonymized = anonymized.replace(wallet, f"[WALLET:{hashed[:8]}]")
        
        return (anonymized, pii_found)
    
    def _hash_value(self, value: str) -> str:
        """Hash a value with salt."""
        return hashlib.sha256(f"{self._salt}{value}".encode()).hexdigest()
```

### Integration

**In telemetry collector**:

```python
async def record(self, result: DistillationResult):
    # Anonymize message before hashing
    if self._anonymizer:
        anonymized_message, pii_found = self._anonymizer.anonymize(
            result.user_message
        )
        request_hash = self._hash_message(anonymized_message)
        
        # Log PII detection
        if pii_found:
            logger.warning(
                f"PII detected in distillation request: {pii_found.keys()}"
            )
    else:
        request_hash = self._hash_message(result.user_message)
    
    # Record telemetry with anonymized hash
    ...
```

### GDPR/CCPA Compliance

**Data Retention**:
- Messages: SHA-256 hashed only (irreversible)
- Telemetry: 90-day retention (configurable)
- PII: Never stored in plaintext

**Right to Erasure**:
```sql
-- Delete user's distillation data
DELETE FROM distillation_telemetry WHERE user_id = '<user_id>';
```

**Data Export**:
```sql
-- Export user's distillation data
SELECT * FROM distillation_telemetry WHERE user_id = '<user_id>';
```

---

## Security Best Practices

### 1. API Key Management

**DO**:
- ✅ Store in environment variables or secrets manager
- ✅ Rotate keys regularly (quarterly)
- ✅ Use different keys for dev/staging/prod
- ✅ Limit key permissions (principle of least privilege)

**DON'T**:
- ❌ Hardcode in source code
- ❌ Commit to version control
- ❌ Share between environments
- ❌ Use root/admin keys

### 2. Input Validation

**Always validate**:
- Message length (1-10K chars)
- Character encoding (UTF-8)
- Content type (text only)
- Rate limits

### 3. Error Handling

**Never expose**:
- Internal error messages
- Stack traces
- API keys
- Database queries

**Instead**:
- Generic user messages
- Internal error logging
- Error codes for debugging

### 4. Logging

**DO log**:
- Request metadata (timestamp, user_id, provider)
- Performance metrics (latency, tokens)
- Security events (injection attempts, rate limits)
- System health (provider status, errors)

**DON'T log**:
- User messages (plaintext)
- API keys
- Passwords
- PII (emails, phones, etc.)

### 5. Network Security

**Use**:
- HTTPS only for all API calls
- TLS 1.2+ for database connections
- VPC/private networks where possible
- IP allowlisting for admin endpoints

### 6. Authentication

**Admin endpoints**:
- Require authentication (JWT tokens)
- Check admin role/permissions
- Log admin actions
- Rate limit admin API

**User endpoints**:
- Require user authentication
- Validate user_id matches token
- Check subscription/permissions

---

## Monitoring & Alerts

### Security Metrics

**Monitor**:
1. **Injection attempts**: Count blocked requests per hour
2. **Rate limit hits**: Track user/global limit exceeds
3. **PII detection**: Log PII found in requests
4. **Provider errors**: Track authentication failures
5. **Unusual patterns**: High entropy, excessive special chars

### Alert Thresholds

**Critical**:
- Injection attempts: >100/hour
- Rate limit hits: >1000/hour
- Provider errors: >50/hour
- PII detection: >10/hour

**Warning**:
- Injection attempts: >50/hour
- Rate limit hits: >500/hour
- Provider errors: >20/hour
- PII detection: >5/hour

### SQL Queries

**Injection attempts (last hour)**:
```sql
SELECT
    COUNT(*) as injection_attempts,
    COUNT(DISTINCT user_id) as unique_users
FROM distillation_telemetry
WHERE timestamp > NOW() - INTERVAL '1 hour'
  AND reason = 'malicious';
```

**Rate limit hits (last hour)**:
```sql
SELECT
    COUNT(*) as rate_limit_hits,
    reason,
    COUNT(DISTINCT user_id) as unique_users
FROM distillation_telemetry
WHERE timestamp > NOW() - INTERVAL '1 hour'
  AND reason = 'rate_limit'
GROUP BY reason;
```

**PII detection (last 24 hours)**:
```sql
-- Note: PII is anonymized, this tracks detection events
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as pii_detected_count
FROM distillation_telemetry
WHERE timestamp > NOW() - INTERVAL '24 hours'
  AND error LIKE '%PII detected%'
GROUP BY hour
ORDER BY hour DESC;
```

---

## Implementation Checklist

### Phase 5 Security Tasks

- [x] **Task 5.1**: Prompt injection detection (implemented)
- [ ] **Task 5.2**: Rate limiting (guide provided, implement as needed)
- [ ] **Task 5.3**: PII anonymization (guide provided, implement as needed)
- [x] **Task 5.4**: Security best practices (documented)

### Production Readiness

- [ ] Deploy rate limiter (Redis required)
- [ ] Enable PII anonymization
- [ ] Configure security alerts
- [ ] Set up monitoring dashboards
- [ ] Review and test all security features
- [ ] Penetration testing (recommended)
- [ ] Security audit (recommended)

---

## References

- Prompt injection detector: `src/app/domain/services/distillation/prompt_injection_detector.py`
- Integration guide: `docs/DISTILLATION_INTEGRATION_GUIDE.md`
- System spec: `docs/specs/REQUEST_DISTILLATION_SPEC.md`

---

**Document Status**: ✅ Complete  
**Implementation Status**: ⏳ Guides provided, optional features pending
