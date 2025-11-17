# 🚀 Anvil API - Complete Documentation Package

## Package Contents

This package contains **complete API endpoint documentation** for the Anvil DeFi platform, covering all three user types with detailed specifications for 63 endpoints.

---

## 📦 What's Included

### Documentation Files (5 total)

1. **`anvil_api_documentation_index.md`** - Start here!
   - Complete API overview and index
   - Quick start examples
   - Best practices
   - ~25 pages

2. **`anvil_api_client_part1.md`** - CLIENT API Part 1
   - Authentication (3 endpoints)
   - User Profile (2 endpoints)
   - Wallet Operations (4 endpoints)
   - Transactions (2 endpoints)
   - ~60 pages

3. **`anvil_api_client_part2.md`** - CLIENT API Part 2
   - Trading & Swaps (2 endpoints)
   - Earn/Yield Farming (4 endpoints)
   - Save Schedules (4 endpoints)
   - Perpetuals (3 endpoints)
   - AI Chat (2 endpoints)
   - Subscriptions (3 endpoints)
   - Notifications (3 endpoints)
   - Funding (2 endpoints)
   - ~50 pages

4. **`anvil_api_admin.md`** - ADMIN API
   - Dashboard & Analytics
   - User Management (4 endpoints)
   - Transaction Management (2 endpoints)
   - Settings Management (2 endpoints)
   - AI Configuration (2 endpoints)
   - Subscription Management (2 endpoints)
   - Audit Logs
   - ~40 pages

5. **`anvil_api_auditor.md`** - AUDITOR API
   - Compliance Dashboard
   - Audit Logs (2 endpoints)
   - User Data Access (3 endpoints)
   - Transaction Review (2 endpoints)
   - Financial Reporting
   - Export Operations (3 endpoints)
   - ~35 pages

---

## 📊 Documentation Statistics

```
Total Pages:           ~185 pages
Total Endpoints:       63 endpoints
Request Examples:      126+
Response Examples:     126+
Database Queries:      63+
Error Scenarios:       100+
Business Logic Rules:  200+
```

---

## 🎯 Quick Navigation

### By User Type

**CLIENT (role=2) - Mobile App Users**
- Start with: `anvil_api_client_part1.md`
- 35 endpoints total
- Full CRUD on personal data
- Integrations: Privy, Stripe, DEX aggregators, DeFi protocols

**ADMIN (role=0) - Platform Administrators**
- Start with: `anvil_api_admin.md`
- 15 endpoints total
- Full CRUD on all platform data
- Manage users, transactions, settings

**AUDITOR (role=1) - Compliance Officers**
- Start with: `anvil_api_auditor.md`
- 13 endpoints total
- Read-only access for compliance
- Export and reporting capabilities

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  ANVIL API (v1)                     │
│              https://api.anvil.com/v1               │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐     ┌─────────┐     ┌──────────┐
   │ CLIENT  │     │  ADMIN  │     │ AUDITOR  │
   │ role=2  │     │ role=0  │     │  role=1  │
   └─────────┘     └─────────┘     └──────────┘
        │                │                │
        │                │                │
   35 endpoints    15 endpoints    13 endpoints
   Read/Write      Read/Write      Read-Only
```

---

## 📖 How to Use This Documentation

### For Frontend Developers (Mobile App)
1. Read `anvil_api_documentation_index.md` for overview
2. Start with `anvil_api_client_part1.md` for auth & wallet
3. Continue with `anvil_api_client_part2.md` for trading features
4. Each endpoint includes:
   - Request/response examples
   - Error handling
   - Business logic
   - Rate limits

### For Backend Developers
1. Use as reference for implementing endpoints
2. Database queries are included for each endpoint
3. Business logic is documented
4. External service dependencies listed

### For Admin Panel Developers
1. Read `anvil_api_admin.md`
2. All CRUD operations documented
3. Audit logging included
4. Permission checks specified

### For Compliance/Auditors
1. Read `anvil_api_auditor.md`
2. Read-only access patterns
3. Export formats specified
4. Compliance reporting details

---

## 🔑 Key Features

### Authentication
- JWT Bearer Token (all endpoints)
- Privy integration (CLIENT)
- Email/password + 2FA (ADMIN/AUDITOR)
- 8-hour token expiry
- Refresh token support

### Rate Limiting
- Per-user rate limits
- Per-IP rate limits for auth
- Headers in all responses
- Graceful degradation

### Error Handling
- Consistent error format
- Detailed error codes
- Actionable error messages
- Debug information included

### Pagination
- Standard pagination format
- Configurable page size
- Total count included
- Navigation helpers

### Audit Logging
- All ADMIN actions logged
- All AUDITOR views logged
- Immutable audit trail
- Complete context captured

---

## 🔧 Tech Stack Integration

### Blockchain
- **Arbitrum** - Primary L2 chain
- **Base** - Secondary L2 chain
- **Hyperliquid** - Perpetual trading
- **Privy** - Wallet management

### DeFi Protocols
- **Aave V3** - Lending/borrowing
- **Compound V3** - Yield farming
- **1inch** - DEX aggregation
- **0x Protocol** - Swap routing

### AI Services
- **Vertex AI** - Primary LLM (Gemini 1.5)
- **AWS Bedrock** - Fallback LLM (Claude)
- **Custom agents** - Specialized workflows

### Payment Processing
- **Stripe** - Fiat on/off ramp
- **Credit card** processing
- **Subscription** billing
- **Refund** handling

### Notifications
- **FCM** - Push notifications
- **SendGrid** - Email
- **Twilio** - SMS
- **In-app** notifications

---

## 📋 API Standards

### Request Format
```http
POST /api/v1/endpoint HTTP/1.1
Host: api.anvil.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "field": "value"
}
```

### Success Response
```json
{
  "success": true,
  "data": {
    "id": 123,
    "field": "value"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "additional context"
    },
    "timestamp": "2025-11-16T20:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

### Pagination
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

## 🚦 Testing

### Sandbox Environment
```
Base URL: https://api-sandbox.anvil.com/v1
```

### Test Credentials
- **CLIENT**: Use Privy test mode
- **ADMIN**: Contact dev team for test account
- **AUDITOR**: Contact dev team for test account

### Test Data
- Mock blockchain transactions
- Simulated AI responses
- Stripe test cards
- Sandbox wallets

---

## 📈 Rate Limits Summary

| User Type | Auth | Reads | Writes | Special |
|-----------|------|-------|--------|---------|
| **CLIENT** | 5/min | 60/min | 20/min | AI: 10/day (free) |
| **ADMIN** | 5/min | 60/min | 20/min | Critical: 10/min |
| **AUDITOR** | 5/min | 60/min | N/A | Exports: 5/min |

---

## 🔒 Security

### All Endpoints
✅ JWT authentication  
✅ Role-based access control  
✅ Rate limiting  
✅ Input validation  
✅ SQL injection prevention  
✅ XSS protection  
✅ CORS configuration  

### ADMIN/AUDITOR Only
✅ 2FA/TOTP required  
✅ IP allowlist (optional)  
✅ Audit logging  
✅ Session timeout (8h)  

---

## 🎓 Learning Path

### Beginner
1. Read the index (`anvil_api_documentation_index.md`)
2. Try CLIENT authentication endpoint
3. Get user profile
4. Fetch wallet balance

### Intermediate
1. Implement swap functionality
2. Add earn positions
3. Set up notifications
4. Handle errors gracefully

### Advanced
1. Build admin dashboard
2. Implement compliance exports
3. Create background jobs
4. Optimize for rate limits

---

## 💡 Code Examples

### JavaScript/TypeScript (React Native)
```javascript
// Login
const login = async (privyToken, privyUserId) => {
  const response = await fetch('https://api.anvil.com/v1/user/auth/privy', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      privy_token: privyToken,
      privy_user_id: privyUserId
    })
  });
  const {data} = await response.json();
  return data.access_token;
};

// Get balance
const getBalance = async (token) => {
  const response = await fetch('https://api.anvil.com/v1/user/wallet/balances', {
    headers: {'Authorization': `Bearer ${token}`}
  });
  const {data} = await response.json();
  return data.total_usd;
};
```

### Python (Admin Dashboard)
```python
import requests

# Admin login
def admin_login(email, password, totp_code):
    response = requests.post(
        'https://api.anvil.com/v1/admin/auth/login',
        json={
            'email': email,
            'password': password,
            'totp_code': totp_code
        }
    )
    return response.json()['data']['access_token']

# Get dashboard stats
def get_stats(token, period='24h'):
    response = requests.get(
        f'https://api.anvil.com/v1/admin/dashboard/stats?period={period}',
        headers={'Authorization': f'Bearer {token}'}
    )
    return response.json()['data']
```

---

## 🐛 Common Issues & Solutions

### Issue: 401 Unauthorized
**Solution**: Check if token is expired, refresh with `/auth/refresh`

### Issue: 429 Rate Limited
**Solution**: Implement exponential backoff, cache responses

### Issue: 400 Validation Error
**Solution**: Check request schema, validate input client-side

### Issue: 503 Service Unavailable
**Solution**: Retry with exponential backoff, check status page

---

## 📞 Support

### For Developers
- **Email**: developers@anvil.com
- **Slack**: #api-support
- **GitHub**: github.com/anvil/api-docs

### For Issues
- **Bug Reports**: issues@anvil.com
- **Feature Requests**: features@anvil.com
- **Security**: security@anvil.com

### Resources
- **API Status**: status.anvil.com
- **Changelog**: changelog.anvil.com
- **Blog**: blog.anvil.com

---

## 📅 Version History

### v1.0 (November 16, 2025)
✅ Initial release  
✅ 63 endpoints documented  
✅ Complete request/response examples  
✅ Database operations included  
✅ Business logic documented  
✅ Error scenarios covered  
✅ Rate limiting specified  
✅ Security guidelines included  

---

## 🎯 Next Steps

1. **Download all 5 documentation files**
2. **Read the index first** (`anvil_api_documentation_index.md`)
3. **Choose your user type** (CLIENT, ADMIN, or AUDITOR)
4. **Read the relevant documentation**
5. **Start implementing endpoints**
6. **Test in sandbox environment**
7. **Deploy to production**

---

## ✅ Checklist for Implementation

### Frontend Team
- [ ] Read CLIENT Part 1 & 2
- [ ] Implement authentication flow
- [ ] Add wallet integration
- [ ] Build trading features
- [ ] Implement error handling
- [ ] Add loading states
- [ ] Test all flows

### Backend Team
- [ ] Review database schema
- [ ] Implement authentication
- [ ] Add rate limiting
- [ ] Set up audit logging
- [ ] Configure external services
- [ ] Write unit tests
- [ ] Deploy to staging

### QA Team
- [ ] Test all endpoints
- [ ] Verify error responses
- [ ] Check rate limits
- [ ] Test edge cases
- [ ] Security testing
- [ ] Load testing
- [ ] Documentation review

---

## 📝 License & Usage

This documentation is proprietary and confidential.

**© 2025 Anvil Technologies Inc. All rights reserved.**

For internal use only. Do not distribute outside the organization without authorization.

---

## 🎉 You're Ready!

All API documentation is complete and production-ready. The endpoints are designed to be:

- **Easy to use** - Clear examples and patterns
- **Robust** - Comprehensive error handling
- **Secure** - Authentication and authorization
- **Scalable** - Rate limiting and caching
- **Compliant** - Audit logging and reporting

Happy coding! 🚀

---

**Package Status**: ✅ Complete  
**Total Files**: 5 documents (~185 pages)  
**Last Updated**: November 16, 2025  
**Version**: 1.0.0
