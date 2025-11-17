# 🔒 Anvil Platform - Security & Compliance Document

## Security Architecture and Regulatory Compliance

**Version:** 1.0  
**Date:** November 2025  
**Classification:** Internal - Development Team

---

## 🎯 Security Overview

### Security Principles
1. **Defense in Depth**: Multiple layers of security
2. **Least Privilege**: Minimal access rights
3. **Zero Trust**: Never trust, always verify
4. **Encryption Everywhere**: Data at rest and in transit
5. **Audit Everything**: Complete audit trail

### Threat Model
```
┌────────────────────────────────────────┐
│           THREAT ACTORS                │
├────────────────────────────────────────┤
│ • External Hackers                     │
│ • Malicious Insiders                   │
│ • Social Engineers                     │
│ • State-sponsored Actors               │
│ • Competitors                          │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│          ATTACK VECTORS                │
├────────────────────────────────────────┤
│ • API Exploitation                     │
│ • SQL Injection                        │
│ • XSS/CSRF                            │
│ • Man-in-the-Middle                   │
│ • Phishing                            │
│ • DDoS                                │
│ • Smart Contract Exploits             │
│ • Private Key Theft                   │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│        SECURITY CONTROLS               │
├────────────────────────────────────────┤
│ • WAF (CloudFlare/AWS)                │
│ • Input Validation                     │
│ • Output Encoding                      │
│ • TLS 1.3                             │
│ • 2FA/MFA                             │
│ • Rate Limiting                        │
│ • Code Audits                         │
│ • Hardware Security Modules           │
└────────────────────────────────────────┘
```

---

## 🔐 Authentication & Authorization

### JWT Token Structure

**Access Token (1 hour):**
```json
{
  "sub": "12345",
  "user_id": 12345,
  "uid": "usr_abc123",
  "email": "user@example.com",
  "role": 2,
  "privy_user_id": "did:privy:clk1abc123",
  "iat": 1699876543,
  "exp": 1699880143,
  "type": "access"
}
```

**Refresh Token (30 days):**
```json
{
  "sub": "12345",
  "user_id": 12345,
  "iat": 1699876543,
  "exp": 1702468543,
  "type": "refresh"
}
```

### Token Security
```python
# app/core/security.py
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config import settings

class SecurityManager:
    @staticmethod
    def create_token(data: dict, expires_delta: timedelta) -> str:
        """Create signed JWT token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            raise HTTPException(401, f"Invalid token: {str(e)}")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Verify password against hash"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain, hashed)
```

### 2FA/TOTP Implementation (Admin/Auditor)
```python
import pyotp
import qrcode
from io import BytesIO

class TwoFactorAuth:
    @staticmethod
    def generate_secret() -> str:
        """Generate TOTP secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp_uri(secret: str, email: str) -> str:
        """Get TOTP provisioning URI"""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name="Anvil Platform"
        )
    
    @staticmethod
    def verify_totp(secret: str, code: str) -> bool:
        """Verify TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    @staticmethod
    def generate_qr_code(uri: str) -> bytes:
        """Generate QR code for TOTP setup"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
```

### Role-Based Access Control (RBAC)
```python
from enum import IntEnum
from fastapi import Depends, HTTPException

class UserRole(IntEnum):
    ADMIN = 0
    AUDITOR = 1
    CLIENT = 2

def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role > required_role:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return role_checker

# Usage
@router.get("/admin/users")
async def list_users(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    # Only admins can access
    pass
```

---

## 🛡️ Data Protection

### Encryption at Rest

**Database Encryption:**
```yaml
# RDS MySQL Configuration
Storage: Encrypted (AES-256)
Key Management: AWS KMS
Automated Backups: Encrypted
Snapshots: Encrypted
```

**Sensitive Data in Database:**
```python
from cryptography.fernet import Fernet
from app.config import settings

class DataEncryption:
    def __init__(self):
        self.cipher = Fernet(settings.ENCRYPTION_KEY)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(ciphertext.encode()).decode()

# Example: Encrypt API keys
setting = Setting(
    key="stripe_secret_key",
    value=encryption.encrypt(api_key),
    is_encrypted=True,
    is_sensitive=True
)
```

**S3 Encryption:**
```yaml
Bucket Encryption: AES-256 (S3-managed keys)
Objects: Server-side encryption enabled
KYC Documents: Client-side encryption before upload
Access: IAM roles only, no public access
```

### Encryption in Transit

**TLS Configuration:**
```yaml
Protocol: TLS 1.3
Ciphers: 
  - TLS_AES_128_GCM_SHA256
  - TLS_AES_256_GCM_SHA384
  - TLS_CHACHA20_POLY1305_SHA256
Certificate: AWS Certificate Manager (ACM)
HSTS: Enabled (max-age=31536000)
```

**API Client Configuration:**
```python
# Force HTTPS
@app.middleware("http")
async def force_https(request: Request, call_next):
    if request.url.scheme != "https" and settings.ENVIRONMENT == "production":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url=url, status_code=301)
    return await call_next(request)
```

---

## 🚨 Input Validation & Sanitization

### Pydantic Schemas for Validation
```python
from pydantic import BaseModel, EmailStr, validator, Field
from decimal import Decimal

class SwapRequest(BaseModel):
    from_asset: str = Field(..., regex="^[A-Z]{3,10}$")
    from_amount: Decimal = Field(..., gt=0, le=1000000)
    to_asset: str = Field(..., regex="^[A-Z]{3,10}$")
    chain: str = Field(..., regex="^(arbitrum|base)$")
    slippage: float = Field(0.5, ge=0.1, le=5.0)
    
    @validator("from_asset", "to_asset")
    def validate_asset(cls, v):
        allowed_assets = ["USDC", "ETH", "USDT", "DAI"]
        if v not in allowed_assets:
            raise ValueError(f"Asset must be one of {allowed_assets}")
        return v
    
    @validator("from_amount")
    def validate_amount(cls, v):
        if v < Decimal("0.01"):
            raise ValueError("Minimum amount is 0.01")
        return v

class UserProfileUpdate(BaseModel):
    firstname: Optional[str] = Field(None, max_length=100)
    lastname: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, regex="^\+[1-9]\d{1,14}$")
    
    @validator("firstname", "lastname")
    def sanitize_name(cls, v):
        if v:
            # Remove any HTML/script tags
            import bleach
            return bleach.clean(v, strip=True)
        return v
```

### SQL Injection Prevention
```python
# ✅ GOOD: Using SQLAlchemy ORM
users = db.query(User).filter(User.email == email).all()

# ✅ GOOD: Using parameterized queries
users = db.execute(
    "SELECT * FROM users WHERE email = :email",
    {"email": email}
).fetchall()

# ❌ BAD: String concatenation
users = db.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

### XSS Prevention
```python
from markupsafe import escape

def sanitize_output(data: str) -> str:
    """Escape HTML to prevent XSS"""
    return escape(data)

# In responses
return {
    "message": sanitize_output(user_input)
}
```

---

## 🔥 Rate Limiting & DDoS Protection

### Redis-Based Rate Limiting
```python
# app/api/middleware/rate_limit.py
import redis
from fastapi import Request, HTTPException
from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL)

class RateLimiter:
    @staticmethod
    def check_rate_limit(
        key: str,
        limit: int = 60,
        window: int = 60
    ) -> bool:
        """Check if rate limit exceeded"""
        current = redis_client.get(key)
        
        if current is None:
            redis_client.setex(key, window, 1)
            return True
        
        if int(current) >= limit:
            return False
        
        redis_client.incr(key)
        return True

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Global rate limiting"""
    if settings.RATE_LIMIT_ENABLED:
        # Get identifier (user_id or IP)
        user_id = getattr(request.state, "user_id", None)
        identifier = user_id or request.client.host
        
        key = f"rate_limit:{identifier}:{request.url.path}"
        
        if not RateLimiter.check_rate_limit(key):
            raise HTTPException(429, "Rate limit exceeded")
    
    response = await call_next(request)
    return response
```

### Endpoint-Specific Limits
```python
# Different limits for different endpoints
RATE_LIMITS = {
    "/api/v1/user/auth/login": (5, 60),      # 5 per minute
    "/api/v1/user/trade/swap": (10, 60),     # 10 per minute
    "/api/v1/user/chat/message": (20, 60),   # 20 per minute
    "default": (60, 60)                       # 60 per minute
}
```

### WAF Configuration (AWS/CloudFlare)
```yaml
Rules:
  - Block requests from known bad IPs
  - Rate limit by IP (10,000 req/5min)
  - Block SQL injection patterns
  - Block XSS patterns
  - Block common attack patterns
  - Geographic restrictions (if needed)
  - Size limits (10MB max request)
```

---

## 🔍 Audit Logging

### Comprehensive Audit Trail
```python
# app/services/audit_service.py
from app.models.audit import AuditLog
from sqlalchemy.orm import Session
import json

class AuditService:
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        actor_user_id: int,
        action: str,
        entity: str,
        entity_id: str,
        payload: dict,
        success: bool = True,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Log administrative action"""
        actor = self.db.query(User).get(actor_user_id)
        
        log = AuditLog(
            actor_user_id=actor_user_id,
            actor_email=actor.email if actor else None,
            actor_role=actor.role if actor else None,
            action=action,
            action_category=self._get_category(action),
            entity=entity,
            entity_id=entity_id,
            payload_json=json.dumps(payload),
            success=success,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log)
        self.db.commit()
    
    def _get_category(self, action: str) -> str:
        """Determine action category"""
        if "user" in action:
            return "user_management"
        elif "transaction" in action:
            return "transactions"
        elif "setting" in action:
            return "configuration"
        return "other"

# Usage in endpoints
@router.patch("/admin/users/{user_id}/kyc")
async def approve_kyc(
    user_id: int,
    approval: KYCApproval,
    current_user: User = Depends(get_current_admin),
    request: Request = None,
    audit: AuditService = Depends(get_audit_service)
):
    # Perform action
    user = db.query(User).get(user_id)
    user.kyc_status = "approved"
    db.commit()
    
    # Log to audit trail
    audit.log_action(
        actor_user_id=current_user.id,
        action="kyc_approved",
        entity="user",
        entity_id=str(user_id),
        payload={
            "previous_status": "pending",
            "new_status": "approved",
            "notes": approval.notes
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    return {"success": True}
```

### Security Event Logging
```python
# Log security-sensitive events
def log_security_event(
    event_type: str,
    severity: str,
    description: str,
    user_id: int = None,
    ip_address: str = None
):
    """Log security event"""
    event = SecurityEvent(
        user_id=user_id,
        event_type=event_type,
        severity=severity,
        description=description,
        ip_address=ip_address
    )
    db.add(event)
    db.commit()
    
    # Alert on critical events
    if severity == "critical":
        send_security_alert(event)

# Examples
log_security_event(
    event_type="failed_login",
    severity="medium",
    description="3 failed login attempts",
    ip_address="192.168.1.100"
)

log_security_event(
    event_type="suspicious_transaction",
    severity="high",
    description="Large withdrawal after account takeover indicators",
    user_id=12345
)
```

---

## 💰 Financial Security

### Transaction Signing
```python
# All blockchain transactions must be signed
from eth_account import Account

class TransactionSigner:
    @staticmethod
    def sign_transaction(private_key: str, transaction: dict) -> str:
        """Sign transaction with private key"""
        account = Account.from_key(private_key)
        signed = account.sign_transaction(transaction)
        return signed.rawTransaction.hex()
    
    @staticmethod
    def verify_signature(message: str, signature: str, address: str) -> bool:
        """Verify message signature"""
        from eth_account.messages import encode_defunct
        message_hash = encode_defunct(text=message)
        recovered_address = Account.recover_message(message_hash, signature=signature)
        return recovered_address.lower() == address.lower()
```

### Transaction Limits
```python
# Implement transaction limits
TRANSACTION_LIMITS = {
    "unverified_kyc": {
        "daily_limit_usd": 100,
        "transaction_limit_usd": 50
    },
    "verified_kyc": {
        "daily_limit_usd": 10000,
        "transaction_limit_usd": 5000
    },
    "premium": {
        "daily_limit_usd": 100000,
        "transaction_limit_usd": 50000
    }
}

def check_transaction_limit(user: User, amount_usd: Decimal) -> bool:
    """Check if transaction within limits"""
    tier = "verified_kyc" if user.is_kyc_approved else "unverified_kyc"
    limits = TRANSACTION_LIMITS[tier]
    
    # Check single transaction limit
    if amount_usd > limits["transaction_limit_usd"]:
        return False
    
    # Check daily limit
    today_volume = get_user_daily_volume(user.id)
    if today_volume + amount_usd > limits["daily_limit_usd"]:
        return False
    
    return True
```

### Wallet Security
```python
# Private keys NEVER stored in database
# Always use Privy for key management

class WalletSecurity:
    @staticmethod
    def validate_address(address: str, chain: str = "ethereum") -> bool:
        """Validate blockchain address"""
        if chain == "ethereum":
            from web3 import Web3
            return Web3.is_address(address)
        return False
    
    @staticmethod
    def check_address_risk(address: str) -> dict:
        """Check address against blacklists"""
        # Check OFAC SDN list
        # Check known scam addresses
        # Check mixer addresses
        return {
            "is_sanctioned": False,
            "is_mixer": False,
            "risk_score": 0
        }
```

---

## 🏛️ Regulatory Compliance

### AML/CTR Compliance

**Currency Transaction Report (CTR) - $10,000 Threshold:**
```python
# Automatic flagging of large transactions
@celery_app.task
def check_ctr_threshold():
    """Check for CTR-reportable transactions"""
    # Get transactions > $10,000 in last 24h
    large_txs = db.query(Transaction).filter(
        Transaction.amount_in_usd > 10000,
        Transaction.created_at > datetime.utcnow() - timedelta(days=1),
        Transaction.status == TransactionStatus.SUCCESS
    ).all()
    
    for tx in large_txs:
        # Flag for review
        flag_for_compliance_review(tx)
        
        # Generate CTR report
        generate_ctr_report(tx)
```

**Suspicious Activity Report (SAR):**
```python
# Pattern detection for suspicious activity
SUSPICIOUS_PATTERNS = {
    "structuring": {
        "description": "Multiple transactions just below $10k",
        "detection": lambda txs: detect_structuring(txs)
    },
    "rapid_movement": {
        "description": "Large deposit followed by immediate withdrawal",
        "detection": lambda txs: detect_rapid_movement(txs)
    },
    "unusual_volume": {
        "description": "Volume 10x higher than user average",
        "detection": lambda txs: detect_unusual_volume(txs)
    }
}

def detect_suspicious_activity(user_id: int):
    """Detect suspicious patterns"""
    recent_txs = get_user_recent_transactions(user_id, days=30)
    
    for pattern_name, pattern in SUSPICIOUS_PATTERNS.items():
        if pattern["detection"](recent_txs):
            # File SAR
            file_sar(user_id, pattern_name, pattern["description"])
            
            # Alert compliance team
            notify_compliance_team(user_id, pattern_name)
```

### KYC/AML Verification
```python
# Integration with KYC provider
class KYCService:
    def __init__(self):
        self.provider = PersonaClient()  # or OnfidoClient()
    
    async def verify_identity(self, user_id: int, documents: list):
        """Submit KYC verification"""
        # Upload documents
        inquiry_id = await self.provider.create_inquiry(
            user_id=user_id,
            documents=documents
        )
        
        # Update user record
        user = db.query(User).get(user_id)
        user.kyc_status = "pending"
        user.kyc_provider = "persona"
        user.kyc_provider_id = inquiry_id
        user.kyc_submitted_at = datetime.utcnow()
        db.commit()
        
        return inquiry_id
    
    async def check_sanctions(self, user: User) -> dict:
        """Check against OFAC SDN list"""
        # Check name against sanctions lists
        result = await self.provider.screen_individual(
            full_name=f"{user.firstname} {user.lastname}",
            date_of_birth=user.date_of_birth,
            country=user.country
        )
        
        return {
            "is_sanctioned": result.match_found,
            "match_details": result.matches if result.match_found else None
        }
```

### GDPR Compliance

**Right to Access:**
```python
@router.get("/api/v1/user/data-export")
async def export_user_data(
    current_user: User = Depends(get_current_user)
):
    """Export all user data (GDPR Article 15)"""
    data = {
        "profile": {
            "email": current_user.email,
            "name": current_user.full_name,
            "created_at": current_user.created_at.isoformat()
        },
        "transactions": [tx.to_dict() for tx in current_user.transactions],
        "positions": [pos.to_dict() for pos in current_user.earn_positions],
        "conversations": [conv.to_dict() for conv in current_user.llm_conversations]
    }
    
    # Generate downloadable file
    return JSONResponse(content=data)
```

**Right to Erasure ("Right to be Forgotten"):**
```python
@router.delete("/api/v1/user/account")
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    confirmation: str = Body(...)
):
    """Delete user account (GDPR Article 17)"""
    if confirmation != current_user.email:
        raise HTTPException(400, "Confirmation doesn't match")
    
    # Cannot delete if active positions or pending transactions
    if has_active_positions(current_user.id):
        raise HTTPException(400, "Close all positions before deleting")
    
    # Anonymize user data (keep for compliance, 7 years)
    current_user.email = f"deleted_{current_user.id}@anvil.com"
    current_user.firstname = "Deleted"
    current_user.lastname = "User"
    current_user.phone = None
    current_user.status = UserStatus.DELETED
    current_user.privy_user_id = None
    
    db.commit()
    
    # Log deletion
    log_audit_action(
        action="user_deleted",
        entity="user",
        entity_id=str(current_user.id)
    )
    
    return {"success": True, "message": "Account deleted"}
```

### Data Retention Policy
```python
# Retention periods
RETENTION_POLICY = {
    "user_data": 7 * 365,           # 7 years (regulatory requirement)
    "transactions": 7 * 365,         # 7 years
    "audit_logs": 7 * 365,          # 7 years
    "llm_conversations": 90,         # 90 days
    "notifications": 30,             # 30 days
    "security_events": 2 * 365       # 2 years
}

@celery_app.task
def cleanup_old_data():
    """Clean up data per retention policy"""
    cutoff_dates = {
        key: datetime.utcnow() - timedelta(days=days)
        for key, days in RETENTION_POLICY.items()
    }
    
    # Delete old LLM conversations
    db.query(LLMConversation).filter(
        LLMConversation.created_at < cutoff_dates["llm_conversations"]
    ).delete()
    
    # Delete old notifications
    db.query(Notification).filter(
        Notification.created_at < cutoff_dates["notifications"]
    ).delete()
    
    db.commit()
```

---

## 🔒 Smart Contract Security

### Audit Requirements
```yaml
Before Production:
  - Professional audit by reputable firm (CertiK, Trail of Bits)
  - Automated analysis (Slither, Mythril)
  - Bug bounty program
  - Gradual rollout with limits
```

### Safe Contract Interaction
```python
# Always use try/catch for contract calls
from web3.exceptions import ContractLogicError

async def call_contract_safely(contract, function_name, *args):
    """Safely call contract function"""
    try:
        result = getattr(contract.functions, function_name)(*args).call()
        return result
    except ContractLogicError as e:
        logger.error(f"Contract error: {str(e)}")
        raise HTTPException(400, "Smart contract rejected transaction")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(500, "Transaction failed")
```

---

## 🚨 Incident Response Plan

### Incident Severity Levels
```yaml
P0 (Critical):
  - Data breach
  - System-wide outage
  - Private key compromise
  - Large-scale fund loss
  Response Time: Immediate
  Escalation: CTO, CEO, Board

P1 (High):
  - API downtime
  - Security vulnerability
  - Significant bug
  Response Time: 1 hour
  Escalation: CTO, Engineering Lead

P2 (Medium):
  - Performance degradation
  - Minor security issue
  - Feature malfunction
  Response Time: 4 hours
  Escalation: Engineering Lead

P3 (Low):
  - UI bugs
  - Minor issues
  Response Time: 24 hours
  Escalation: Team Lead
```

### Incident Response Process
```
1. DETECT
   └─> Monitoring alert or user report

2. ASSESS
   └─> Determine severity (P0-P3)
   └─> Activate incident response team

3. CONTAIN
   └─> Stop the bleeding
   └─> Isolate affected systems
   └─> Preserve evidence

4. ERADICATE
   └─> Fix root cause
   └─> Deploy patches

5. RECOVER
   └─> Restore normal operations
   └─> Verify fix

6. LEARN
   └─> Post-mortem report
   └─> Update procedures
   └─> Implement preventive measures
```

### Security Contacts
```yaml
Security Team:
  - CTO: cto@anvil.com
  - Security Lead: security@anvil.com
  - DevOps Lead: devops@anvil.com

External:
  - Incident Response Firm: [TBD]
  - Legal Counsel: [TBD]
  - PR Agency: [TBD]

Bug Bounty: security@anvil.com
```

---

## ✅ Security Checklist

### Pre-Production
- [ ] All secrets in environment variables
- [ ] TLS 1.3 configured
- [ ] WAF enabled
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] XSS prevention implemented
- [ ] CSRF protection enabled
- [ ] Authentication tested
- [ ] Authorization tested
- [ ] 2FA for admin/auditor
- [ ] Audit logging enabled
- [ ] Encryption at rest configured
- [ ] Secure session management
- [ ] Password policy enforced
- [ ] Security headers configured
- [ ] Dependency scanning automated
- [ ] Code review process established
- [ ] Penetration testing completed
- [ ] Incident response plan documented

### Production
- [ ] Security monitoring active
- [ ] Automated vulnerability scanning
- [ ] Regular security audits scheduled
- [ ] Bug bounty program launched
- [ ] Backup and recovery tested
- [ ] Disaster recovery plan tested
- [ ] Compliance requirements met
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] Security training for team

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Classification:** Internal Use Only  
**Next Review:** Quarterly

**Security Inquiries:** security@anvil.com
