# 📚 Anvil API Documentation - Complete Index

## Overview

Complete API endpoint documentation for all three user types in the Anvil platform.

**Base URL:** `https://api.anvil.com/v1`  
**API Version:** v1.0  
**Authentication:** JWT Bearer Token  
**Content-Type:** `application/json`  
**Last Updated:** November 16, 2025

---

## Documentation Files

### CLIENT API (role=2)
**Platform:** Mobile App (iOS/Android)  
**Files:** 2 documents

1. **`anvil_api_client_part1.md`** (~60 pages)
   - Authentication (3 endpoints)
   - User Profile (2 endpoints)
   - Wallet Operations (4 endpoints)
   - Transactions (2 endpoints)
   
2. **`anvil_api_client_part2.md`** (~50 pages)
   - Trading & Swaps (2 endpoints)
   - Earn (Yield Farming) (4 endpoints)
   - Save Schedules (4 endpoints)
   - Perpetuals (3 endpoints)
   - AI Chat (2 endpoints)
   - Subscriptions (3 endpoints)
   - Notifications (3 endpoints)
   - Funding (2 endpoints)

### ADMIN API (role=0)
**Platform:** Web Admin Console  
**File:** 1 document

3. **`anvil_api_admin.md`** (~40 pages)
   - Authentication (1 endpoint)
   - Dashboard & Analytics (1 endpoint)
   - User Management (4 endpoints)
   - Transaction Management (2 endpoints)
   - Settings Management (2 endpoints)
   - AI & Model Configuration (2 endpoints)
   - Subscription Management (2 endpoints)
   - Audit Logs (1 endpoint)

### AUDITOR API (role=1)
**Platform:** Web Compliance Console  
**File:** 1 document

4. **`anvil_api_auditor.md`** (~35 pages)
   - Authentication (1 endpoint)
   - Dashboard & Compliance Overview (1 endpoint)
   - Audit Logs (2 endpoints)
   - User Data Access (3 endpoints)
   - Transaction Review (2 endpoints)
   - Financial Reporting (1 endpoint)
   - Export Operations (3 endpoints)

---

## Total Endpoints Summary

| User Type | HTTP Methods | Total Endpoints | Access Level |
|-----------|--------------|-----------------|--------------|
| **CLIENT** | GET, POST, PATCH, DELETE | 35 | Personal data only |
| **ADMIN** | GET, POST, PATCH, DELETE | 15 | Full CRUD access |
| **AUDITOR** | GET, POST (exports) | 13 | Read-only access |
| **TOTAL** | - | **63** | - |

---

## CLIENT Endpoints (35 total)

### Authentication (3)
- `POST /api/v1/user/auth/privy` - Login with Privy
- `POST /api/v1/user/auth/refresh` - Refresh access token
- `POST /api/v1/user/auth/logout` - Logout

### User Profile (2)
- `GET /api/v1/user/profile` - Get profile
- `PATCH /api/v1/user/profile` - Update profile

### Wallet Operations (4)
- `GET /api/v1/user/wallet` - Get wallet info
- `GET /api/v1/user/wallet/balances` - Get token balances
- `GET /api/v1/user/wallet/addresses` - Get chain addresses
- `POST /api/v1/user/wallet/refresh-balances` - Force refresh

### Transactions (2)
- `GET /api/v1/user/transactions` - Get transaction history
- `GET /api/v1/user/transactions/:id` - Get transaction details

### Trading & Swaps (2)
- `POST /api/v1/user/trade/quote` - Get swap quote
- `POST /api/v1/user/trade/swap` - Execute swap

### Earn - Yield Farming (4)
- `GET /api/v1/user/earn/opportunities` - List yield opportunities
- `POST /api/v1/user/earn/deposit` - Deposit to protocol
- `GET /api/v1/user/earn/positions` - Get active positions
- `POST /api/v1/user/earn/positions/:id/withdraw` - Withdraw

### Save Schedules (4)
- `GET /api/v1/user/save/schedules` - Get save schedules
- `POST /api/v1/user/save/schedule` - Create schedule
- `PATCH /api/v1/user/save/schedules/:id` - Update schedule
- `DELETE /api/v1/user/save/schedules/:id` - Delete schedule

### Perpetuals (3)
- `POST /api/v1/user/perpetuals/open` - Open position
- `GET /api/v1/user/perpetuals/positions` - Get positions
- `POST /api/v1/user/perpetuals/positions/:id/close` - Close position

### AI Chat (2)
- `POST /api/v1/user/chat/message` - Send message to AI
- `GET /api/v1/user/chat/history` - Get chat history

### Subscriptions (3)
- `GET /api/v1/user/subscription` - Get subscription status
- `POST /api/v1/user/subscription/create-checkout` - Create checkout
- `POST /api/v1/user/subscription/cancel` - Cancel subscription

### Notifications (3)
- `GET /api/v1/user/notifications` - Get notifications
- `POST /api/v1/user/notifications/:id/read` - Mark as read
- `POST /api/v1/user/notifications/read-all` - Mark all as read

### Funding (2)
- `POST /api/v1/user/funding/create` - Create funding transaction
- `GET /api/v1/user/funding/history` - Get funding history

---

## ADMIN Endpoints (15 total)

### Authentication (1)
- `POST /api/v1/admin/auth/login` - Admin login

### Dashboard (1)
- `GET /api/v1/admin/dashboard/stats` - Get platform stats

### User Management (4)
- `GET /api/v1/admin/users` - List users
- `GET /api/v1/admin/users/:id` - Get user details
- `PATCH /api/v1/admin/users/:id/kyc` - Approve/reject KYC
- `PATCH /api/v1/admin/users/:id/status` - Update user status

### Transaction Management (2)
- `GET /api/v1/admin/transactions` - List all transactions
- `POST /api/v1/admin/transactions/:id/retry` - Retry failed transaction

### Settings Management (2)
- `GET /api/v1/admin/settings` - Get all settings
- `PATCH /api/v1/admin/settings/:id` - Update setting

### AI & Model Configuration (2)
- `GET /api/v1/admin/ai/models` - Get AI models
- `PATCH /api/v1/admin/ai/models/:id` - Update model config

### Subscription Management (2)
- `GET /api/v1/admin/subscriptions` - List subscriptions
- `POST /api/v1/admin/subscriptions/:id/refund` - Process refund

### Audit Logs (1)
- `GET /api/v1/admin/audit-logs` - Get audit trail

---

## AUDITOR Endpoints (13 total)

### Authentication (1)
- `POST /api/v1/admin/auth/login` - Auditor login

### Dashboard (1)
- `GET /api/v1/admin/dashboard/stats` - Get compliance stats

### Audit Logs (2)
- `GET /api/v1/admin/audit-logs` - Get audit trail (read-only)
- `GET /api/v1/admin/audit-logs/:id` - Get log details

### User Data Access (3)
- `GET /api/v1/admin/users` - List users (read-only)
- `GET /api/v1/admin/users/:id` - Get user details (read-only)
- `GET /api/v1/admin/users/:id/activity` - Get user activity

### Transaction Review (2)
- `GET /api/v1/admin/transactions` - List transactions (read-only)
- `GET /api/v1/admin/transactions/:id/compliance` - Get compliance analysis

### Financial Reporting (1)
- `POST /api/v1/admin/reports/financial` - Generate financial report

### Export Operations (3)
- `POST /api/v1/admin/export/audit-logs` - Export audit logs
- `POST /api/v1/admin/export/transactions` - Export transactions
- `POST /api/v1/admin/export/users` - Export user data

---

## Request/Response Standards

### Authentication Header
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Success Response Format
```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { ... },
    "timestamp": "2025-11-16T20:00:00Z",
    "request_id": "req_xyz789"
  }
}
```

### Pagination Format
```json
{
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Rate Limits

### CLIENT Endpoints
| Endpoint Type | Rate Limit |
|---------------|------------|
| Authentication | 5/min per IP |
| General queries (GET) | 60/min |
| Profile updates (PATCH) | 20/min |
| Trading operations | 10/min |
| Wallet refresh | 5/min |
| AI chat (Free) | 10/day |
| AI chat (Pro) | 20/min |

### ADMIN Endpoints
| Endpoint Type | Rate Limit |
|---------------|------------|
| Authentication | 5/min per IP |
| Read operations (GET) | 60/min |
| Write operations | 20/min |
| Critical operations | 10/min |

### AUDITOR Endpoints
| Endpoint Type | Rate Limit |
|---------------|------------|
| Authentication | 5/min per IP |
| Read operations (GET) | 60/min |
| Export operations | 5/min |
| Report generation | 10/min |

---

## Rate Limit Headers

All responses include:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700000000
```

---

## Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or expired token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INSUFFICIENT_BALANCE` | 400 | Not enough funds |
| `DAILY_LIMIT_EXCEEDED` | 429 | Daily limit reached |
| `SERVER_ERROR` | 500 | Internal server error |

---

## External Service Dependencies

### CLIENT Endpoints Require:
- **Privy:** Wallet authentication and management
- **Stripe:** Payment processing for funding
- **1inch/0x:** DEX aggregation for swaps
- **Aave/Compound:** Yield farming protocols
- **Hyperliquid:** Perpetual trading
- **Vertex AI / Bedrock:** AI chat functionality
- **Arbitrum/Base RPC:** Blockchain operations
- **FCM/SendGrid/Twilio:** Notifications

### ADMIN Endpoints Require:
- **All CLIENT dependencies** (can perform operations on behalf of users)
- **Stripe:** Refund processing
- **Internal services:** Settings cache, audit logging

### AUDITOR Endpoints Require:
- **None** (read-only access to database)
- **Export storage:** Temporary file storage for exports

---

## Database Tables Used

### CLIENT Endpoints Access:
- `users` (own record)
- `wallets` (own wallet)
- `chain_addresses` (own addresses)
- `transactions` (own transactions)
- `hyperliquid_positions` (own positions)
- `earn_positions` (own positions)
- `save_schedules` (own schedules)
- `funding_transactions` (own funding)
- `subscriptions` (own subscription)
- `subscription_payments` (own payments)
- `llm_conversations` (own conversations)
- `agent_executions` (own executions)
- `notifications` (own notifications)

### ADMIN Endpoints Access:
- **All 27 tables** (full CRUD access)

### AUDITOR Endpoints Access:
- **All 27 tables** (read-only SELECT access)

---

## Security Features

### All Endpoints:
- ✅ JWT authentication
- ✅ Role-based access control (RBAC)
- ✅ Rate limiting
- ✅ Request validation
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ CORS configuration

### ADMIN/AUDITOR Only:
- ✅ 2FA/TOTP required
- ✅ IP allowlist (optional)
- ✅ All actions logged to `audit_logs`
- ✅ Session timeout (8 hours)

---

## Testing

### Test Environment
**Base URL:** `https://api-sandbox.anvil.com/v1`

### Test Accounts
- CLIENT: Use Privy test mode
- ADMIN: Contact dev team
- AUDITOR: Contact dev team

### Test Data
- Mock blockchain transactions
- Simulated AI responses
- Test payment methods (Stripe test mode)

---

## API Changelog

### v1.0 (2025-11-16)
- ✅ Initial release
- ✅ 63 endpoints across 3 user types
- ✅ Complete CRUD operations
- ✅ Real-time blockchain integration
- ✅ AI-powered features
- ✅ Comprehensive audit logging

---

## Support & Documentation

### For Developers
- **Full API Docs:** This repository
- **Postman Collection:** Available on request
- **Code Examples:** See individual endpoint docs
- **SDK:** Coming soon

### For Support
- **Email:** developers@anvil.com
- **Slack:** #api-support
- **Status Page:** status.anvil.com

---

## Best Practices

### For CLIENT Developers
1. **Always handle rate limits gracefully**
2. **Cache balance data when possible**
3. **Use webhooks for transaction updates**
4. **Implement exponential backoff for retries**
5. **Validate user input before API calls**

### For ADMIN Developers
1. **Always log admin actions**
2. **Require confirmation for destructive operations**
3. **Validate permissions before every action**
4. **Use audit logs for compliance**
5. **Implement IP allowlisting**

### For AUDITOR Developers
1. **Use export APIs for large datasets**
2. **Cache frequently accessed data**
3. **Implement pagination for large result sets**
4. **Schedule reports during off-peak hours**
5. **Verify data integrity before audits**

---

## Quick Start Examples

### CLIENT - Login & Get Balance
```javascript
// 1. Login with Privy
const loginResponse = await fetch('https://api.anvil.com/v1/user/auth/privy', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    privy_token: privyToken,
    privy_user_id: privyUserId
  })
});
const {access_token} = await loginResponse.json();

// 2. Get balance
const balanceResponse = await fetch('https://api.anvil.com/v1/user/wallet/balances', {
  headers: {'Authorization': `Bearer ${access_token}`}
});
const {data} = await balanceResponse.json();
console.log(`Total balance: $${data.total_usd}`);
```

### ADMIN - Approve KYC
```javascript
const response = await fetch('https://api.anvil.com/v1/admin/users/12345/kyc', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${adminToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    action: 'approve',
    notes: 'All documents verified'
  })
});
```

### AUDITOR - Export Audit Logs
```javascript
const response = await fetch('https://api.anvil.com/v1/admin/export/audit-logs', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${auditorToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    date_from: '2025-11-01T00:00:00Z',
    date_to: '2025-11-30T23:59:59Z',
    format: 'csv'
  })
});
const {file_url} = await response.json();
// Download file from file_url
```

---

## Files to Download

### Complete API Documentation

1. **CLIENT Part 1** - `anvil_api_client_part1.md`
   - Authentication, Profile, Wallet, Transactions
   - [Download](computer:///mnt/user-data/outputs/anvil_api_client_part1.md)

2. **CLIENT Part 2** - `anvil_api_client_part2.md`
   - Trading, Earn, Save, Perpetuals, AI, Subscriptions, Notifications, Funding
   - [Download](computer:///mnt/user-data/outputs/anvil_api_client_part2.md)

3. **ADMIN** - `anvil_api_admin.md`
   - Complete admin console API
   - [Download](computer:///mnt/user-data/outputs/anvil_api_admin.md)

4. **AUDITOR** - `anvil_api_auditor.md`
   - Read-only compliance API
   - [Download](computer:///mnt/user-data/outputs/anvil_api_auditor.md)

5. **This Index** - `anvil_api_documentation_index.md`
   - Complete API overview and index
   - [Download](computer:///mnt/user-data/outputs/anvil_api_documentation_index.md)

---

## Statistics

**Total Documentation:** ~185 pages  
**Total Endpoints:** 63  
**Total Request/Response Examples:** 126+  
**Total Database Operations:** 63+  
**Total Error Scenarios:** 100+  

**Status:** Production Ready ✅  
**Version:** v1.0  
**Last Updated:** November 16, 2025

---

**🎉 All API documentation is complete and ready for implementation!**
