# 📋 Anvil Platform - User Stories for Development Team

## Project Overview
**Platform:** Anvil DeFi Trading Platform  
**Target:** Mobile app (React Native) + Web admin console  
**Timeline:** 5 months (3 phases)

---

## User Types

| Type | Role | Platform | Count |
|------|------|----------|-------|
| CLIENT | End Users | Mobile App | 20 stories |
| ADMIN | Administrators | Web Console | 7 stories |
| AUDITOR | Compliance | Web Console | 3 stories |

**Total:** 30 user stories

---

## CLIENT User Stories (Mobile App)

### 1. Authentication & Onboarding

**US-C01: Register with Privy**
- Email or social login (Google/Apple)
- Auto-create embedded wallet
- Email verification
- Multi-chain addresses (Arbitrum, Base, Hyperliquid)

**US-C02: KYC Verification**  
- Upload ID documents
- Selfie for liveness
- Admin approval required
- Required for >$1,000 transactions

---

### 2. Wallet Management

**US-C03: View Portfolio Balance**
- Total USD value
- Breakdown by chain
- Token balances with prices
- Pull-to-refresh from blockchain

**US-C04: Fund Wallet**
- Credit card payment (Stripe)
- $10 minimum
- 3% + $0.30 fee
- Email receipt

---

### 3. Trading

**US-C05: Token Swap**
- DEX aggregator (1inch/0x)
- Slippage tolerance
- Gas estimation
- Transaction history

**US-C06: Price Alerts**
- Set alerts for any token
- Above/below threshold
- Push notifications

---

### 4. Earn (Yield Farming)

**US-C07: Browse Opportunities**
- List Aave, Compound opportunities
- Show APY, TVL, risk level
- Filter and sort

**US-C08: Deposit to Earn**
- Select protocol and amount
- See earnings projections
- Receive confirmation notification

**US-C09: Withdraw from Earn**
- Withdraw principal + rewards
- Full or partial withdrawal
- Update position status

---

### 5. Save (Automated DCA)

**US-C10: Create Save Schedule**
- Choose asset
- Set amount and frequency
- Daily/weekly/biweekly/monthly
- Optional auto-deposit to earn

**US-C11: Manage Schedules**
- Pause/resume/cancel
- View execution history
- Track total saved

---

### 6. Perpetual Trading

**US-C12: Open Position**
- Long/short with leverage (1x-20x)
- Set margin amount
- Show liquidation price
- Warning for high leverage

**US-C13: Monitor Positions**
- Real-time P&L updates
- Liquidation distance
- Funding rate tracking

**US-C14: Close Position**
- Market order close
- Realize P&L
- Return margin to wallet

---

### 7. AI Assistant

**US-C15: Chat with AI**
- Natural language questions
- Portfolio context included
- Market insights
- Free: 10/day, Pro: unlimited

**US-C16: Execute AI Recommendations**
- One-tap execution
- Pre-filled transaction forms
- User confirmation required

---

### 8. Notifications

**US-C17: Transaction Notifications**
- Push for confirmations/failures
- Email for important events
- In-app notification center

**US-C18: Notification Preferences**
- Enable/disable by channel
- Enable/disable by category
- Quiet hours setting

---

### 9. Subscription

**US-C19: Subscribe to Pro**
- 7-day free trial
- $9.99/month
- Stripe payment
- Unlimited AI conversations

**US-C20: Cancel Subscription**
- Cancel anytime
- Access until period end
- Confirmation email

---

## ADMIN User Stories (Web Console)

### 10. User Management

**US-A01: View All Users**
- Paginated list (50/page)
- Search and filters
- User metrics displayed

**US-A02: Approve/Reject KYC**
- View pending submissions
- Review documents
- Approve/reject with reason
- Logged to audit trail

**US-A03: Suspend/Activate Users**
- Change user status
- Provide suspension reason
- Email notification
- Logged to audit

---

### 11. Transaction Management

**US-A04: Monitor Transactions**
- All platform transactions
- Filter by type, status, chain
- Export to CSV

**US-A05: Retry Failed Transactions**
- View failure details
- Retry with updated gas
- Notify user
- Log to audit

---

### 12. Configuration

**US-A06: Manage Settings**
- Edit system settings
- Provide change reason
- Immediate effect
- Redis cache update

**US-A07: Configure AI Models**
- Enable/disable models
- Set daily quotas
- View usage and costs

---

## AUDITOR User Stories (Web Console)

### 13. Compliance

**US-AU01: View Audit Logs**
- Complete action history
- Filter by action/date/admin
- Read-only access
- Export to CSV

**US-AU02: Generate Reports**
- Financial reports by date range
- Revenue, volume, fees
- Export to CSV/XLSX

**US-AU03: Review Flagged Transactions**
- Transactions >$10k (CTR threshold)
- Suspicious pattern detection
- Compliance notes
- FinCEN export

---

## Technical Requirements

### Performance
- API response: <500ms (p95)
- App load time: <3 seconds
- Real-time updates: <10 seconds
- Support: 10,000 concurrent users

### Security
- Encryption: AES-256 (rest), TLS 1.3 (transit)
- API rate limiting
- 2FA for ADMIN/AUDITOR
- Complete audit logging

### Scalability
- Horizontal API scaling
- Database read replicas
- Redis caching layer
- CDN for static assets

### Compliance
- GDPR compliant
- AML/CTR monitoring (>$10k)
- Complete audit trail
- 7-year data retention

### Availability
- 99.9% uptime SLA
- Backups every 6 hours
- 4-hour RTO
- Health monitoring

---

## Technology Stack

### Frontend
- **Mobile:** React Native (iOS + Android)
- **Web:** React or Next.js
- **State:** Redux/Zustand

### Backend
- **API:** Node.js + Express OR Python + FastAPI
- **Database:** MySQL 8.0
- **Cache:** Redis
- **Queue:** Celery or Bull

### Blockchain
- **Wallet:** Privy SDK
- **Web3:** Ethers.js or Web3.js
- **RPCs:** Alchemy

### AI
- **LLM:** Google Vertex AI (Gemini 1.5 Flash)
- **Fallback:** AWS Bedrock (Claude)

### Third-Party Services
- **Payments:** Stripe
- **KYC:** Persona or Onfido
- **Email:** SendGrid
- **SMS:** Twilio
- **Push:** Firebase Cloud Messaging

### DeFi Integrations
- **DEX:** 1inch API, 0x Protocol
- **Lending:** Aave V3, Compound V3
- **Perps:** Hyperliquid API
- **Prices:** Chainlink, CoinGecko

---

## Development Phases

### Phase 1: MVP (2 months)
**Goal:** Core functionality for trading

**Features:**
- Authentication with Privy
- Wallet management and viewing
- Token swaps via 1inch
- Basic earn (Aave only)
- Admin user management
- Push notifications

**Deliverables:**
- iOS app (TestFlight)
- Android app (Internal testing)
- Admin web console
- API backend
- Database schema

---

### Phase 2: Full Features (2 months)
**Goal:** Complete platform with advanced features

**Features:**
- Perpetual trading (Hyperliquid)
- Save schedules (DCA automation)
- AI assistant (Gemini integration)
- Complete earn (Aave + Compound)
- Admin transaction management
- Subscriptions (Stripe)
- Email/SMS notifications

**Deliverables:**
- Public app release
- Full admin console
- Auditor console
- Complete API
- Documentation

---

### Phase 3: Enhancement (1 month)
**Goal:** Polish and advanced features

**Features:**
- Advanced AI features
- Portfolio analytics
- Social features (referrals)
- Advanced admin tools
- Performance optimization

**Deliverables:**
- Optimized production release
- Marketing materials
- User documentation
- Admin training

---

## API Endpoints Summary

### CLIENT (35 endpoints)
- Authentication: 3 endpoints
- Profile: 2 endpoints
- Wallet: 4 endpoints
- Transactions: 2 endpoints
- Trading: 2 endpoints
- Earn: 4 endpoints
- Save: 4 endpoints
- Perpetuals: 3 endpoints
- AI Chat: 2 endpoints
- Subscriptions: 3 endpoints
- Notifications: 3 endpoints
- Funding: 2 endpoints

### ADMIN (15 endpoints)
- Dashboard: 1 endpoint
- Users: 4 endpoints
- Transactions: 2 endpoints
- Settings: 2 endpoints
- AI Models: 2 endpoints
- Subscriptions: 2 endpoints
- Audit Logs: 1 endpoint

### AUDITOR (13 endpoints)
- Dashboard: 1 endpoint
- Audit Logs: 2 endpoints
- Users: 3 endpoints
- Transactions: 2 endpoints
- Reports: 1 endpoint
- Exports: 3 endpoints

**Total: 63 endpoints**

---

## Database Schema

### Tables (27 total)
1. users
2. user_profiles
3. wallets
4. chain_addresses
5. token_balances
6. transactions
7. funding_transactions
8. earn_positions
9. save_schedules
10. hyperliquid_positions
11. hyperliquid_orders
12. llm_conversations
13. agent_executions
14. ai_models
15. subscriptions
16. subscription_payments
17. notifications
18. notification_preferences
19. settings
20. audit_logs
21. security_events
22-27. (Additional support tables)

---

## Success Metrics

### User Engagement
- Daily Active Users (DAU)
- Monthly Active Users (MAU)
- Session duration: >5 minutes
- 30-day retention: >40%

### Financial
- Total Value Locked (TVL)
- Daily trading volume
- Revenue per user: >$10/month
- Subscription conversion: >15%

### Platform Health
- Transaction success rate: >98%
- API availability: >99.9%
- Average response time: <500ms
- Zero security breaches

---

## Acceptance Criteria Template

Each user story includes:
- ✅ Clear acceptance criteria
- ✅ Technical implementation notes
- ✅ External dependencies identified
- ✅ Database operations specified
- ✅ Error handling defined
- ✅ Rate limits specified

---

## Next Steps for Development Team

1. **Review this document** with product owner
2. **Review API endpoints document** (separate file)
3. **Review database schema** (SQLAlchemy models provided)
4. **Set up development environment**
5. **Create sprint backlog** from user stories
6. **Begin Phase 1 development**

---

**Document Status:** Ready for Development ✅  
**Version:** 1.0  
**Last Updated:** November 2025  
**Contact:** CTO@Anvil

---

**Note:** Complete API documentation and database models are provided in separate documents.
