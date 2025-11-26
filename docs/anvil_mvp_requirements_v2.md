# Anvil MVP - Minimum Requirements Specification

## Executive Overview

**Product Name:** Anvil  
**Type:** Chat-first DeFi Assistant  
**Target Users:** Non-expert crypto users  
**Timeline:** 10-12 weeks  
**Core Value:** Democratize DeFi through conversational interface

## 🎯 MVP Goals

Deliver a chat-first investing experience that allows users to:

### End Users (Mobile App)
1. Create accounts with social/email login via **Privy**
2. Automatically receive secure MPC wallets
3. Fund accounts with fiat (card)
4. Execute DeFi operations via chat
5. Track portfolio and activity
6. Manage subscriptions

### Admin Users (Admin Console)
1. Access internal admin panel with **separate traditional authentication**
2. Manage users, wallets, and transactions
3. Monitor system health and operations
4. Configure system settings

## 📋 Core Requirements

### 1. Authentication Systems

#### 1.1 End User Authentication (Mobile App)

##### Privy Integration (Users Only)
- **Social Login Options**
  - Google authentication
  - Apple authentication
  - Email/password authentication
- **Automatic Features**
  - MPC wallet creation on signup
  - No seed phrase exposure
  - Secure key management
  - Wallet recovery mechanism

##### User Flow
1. User opens mobile app
2. Selects login method (Google/Apple/Email)
3. Authenticates via Privy SDK
4. Wallet automatically created/retrieved
5. Access granted to chat interface

#### 1.2 Admin Authentication (Admin Console)

##### Traditional Auth System (Admins Only)
- **Separate from Privy - Custom Implementation**
  - Email/password registration
  - Login functionality
  - Forgot password flow
  - Password reset via email
  - 2FA support (future enhancement)

##### Admin Auth Features
- **Registration Flow**
  - Admin invitation system
  - Email verification required
  - Strong password requirements
  - Role assignment (ADMIN/AUDITOR)

- **Login System**
  - Email/password authentication
  - Session management (JWT)
  - Remember me option
  - Failed attempt lockout

- **Password Recovery**
  - Forgot password link
  - Email verification
  - Secure reset token
  - Time-limited reset links

##### Admin Access Control
- **Role-based permissions**
  - ADMIN: Full CRUD operations
  - AUDITOR: Read-only access
- **Session security**
  - JWT tokens with expiry
  - Refresh token mechanism
  - Activity timeout
  - Audit logging

### 2. User Onboarding Flow (Mobile App)

#### Required Steps
1. Welcome screens with value proposition
2. **Privy-powered** sign-up (Email/Google/Apple)
3. Automatic MPC wallet creation via Privy
4. Initial funding prompt
5. Chat interface introduction

#### Success Criteria
- Complete onboarding in < 2 minutes
- Zero technical jargon
- Immediate wallet availability
- No seed phrase management

### 3. Admin Onboarding Flow (Admin Console)

#### Required Steps
1. Receive invitation email from super admin
2. Click registration link
3. Complete registration form
   - Full name
   - Email (pre-filled from invitation)
   - Password (with strength requirements)
   - Role confirmation
4. Email verification
5. First login with temporary password
6. Dashboard orientation

#### Security Requirements
- Invitation links expire in 48 hours
- Email domain whitelist (optional)
- IP address logging
- Failed attempt monitoring

### 4. Chat Interface (Mobile App)

#### Core Functionality
- **Natural Language Processing**
  - Understand swap intents
  - Parse amounts and tokens
  - Identify earn/save requests
  
- **Micro-Components (In-Chat Cards)**
  - Funding Card
  - Swap Preview Card
  - Earn Option Card
  - Save Card
  - Receipt Card
  - Network Selector

- **Confirmation Flow**
  - Show preview with fees
  - Confirm/Cancel actions
  - Display transaction receipts

#### Supported Commands
```
Examples:
- "Swap 100 USDC to ETH"
- "Buy $100 of ETH on Arbitrum"
- "Show best APY for USDC"
- "Stake 1 ETH"
- "What's my portfolio worth?"
```

### 5. DeFi Operations

#### Swapping (via 1inch)
- **Required Features**
  - Best price discovery
  - Route optimization
  - Slippage protection (default 0.5%)
  - Gas estimation
  - Transaction preview
  
- **Supported Chains**
  - Arbitrum (L2)
  - Base (L2)

#### Earning (via Aave)
- **Single Provider MVP**
  - Deposit/withdraw functionality
  - APY display
  - Risk tooltips
  - Position tracking

#### Funding
- **Fiat On-ramp**
  - Card payments via Stripe
  - Clear fee disclosure
  - ETA display
  - Receipt generation

### 6. Portfolio Management

#### Required Views
- **Portfolio Overview**
  - Total value in USD
  - Token balances
  - Active DeFi positions
  - Quick actions

- **Activity History**
  - Transaction list
  - Filterable by type (swap, earn, fund)
  - Status indicators
  - Export capability

### 7. AI & Agent System

#### Model Router
- **Primary:** Vertex AI (Gemini Flash/Pro)
- **Fallback:** AWS Bedrock (Claude/Mistral)
- **Automatic failover on rate limits**

#### Agent Architecture (CrewAI-style)
1. **Research Agent**
   - Fetch market prices
   - Get protocol data
   - Find best routes

2. **Risk Agent**
   - Validate operations
   - Check balances
   - Verify limits
   - Assess safety

3. **Execution Agent**
   - Build transactions
   - Request signatures
   - Broadcast to chain
   - Monitor confirmation

### 8. Admin Console (Internal Only)

#### Authentication Pages
- **Login Page** (`/admin/login`)
  - Email/password fields
  - Remember me checkbox
  - Forgot password link
  - Failed attempt warnings

- **Registration Page** (`/admin/register`)
  - Invitation code field
  - Registration form
  - Password strength meter
  - Terms acceptance

- **Forgot Password** (`/admin/forgot-password`)
  - Email input
  - Security verification
  - Reset email trigger

- **Reset Password** (`/admin/reset-password/:token`)
  - New password fields
  - Confirmation field
  - Token validation

#### Admin Dashboard Modules
- **Dashboard**
  - Active users count
  - Transaction volume
  - System health
  - Recent failures

- **User Management**
  - List/detail views
  - Status control (active/suspended)
  - Wallet information (from Privy)
  - Activity logs

- **Admin Management**
  - Admin user list
  - Role management
  - Access logs
  - Session management

- **Transaction Management**
  - Complete transaction list
  - Filtering capabilities
  - CSV export
  - Audit trail

- **Subscription Management**
  - Plan management
  - Billing status
  - Stripe webhook handling

- **System Configuration**
  - Model availability toggles
  - Default provider settings
  - Global settings management

### 9. Technical Infrastructure

#### Core Stack
- **Backend:** API Gateway pattern
- **Database:** MySQL
- **Cache:** Redis
- **Queue:** Background job processing
- **Mobile:** React Native
- **Admin:** React/Next.js

#### Authentication Infrastructure
| Component | User Auth | Admin Auth |
|-----------|-----------|------------|
| Provider | Privy SDK | Custom JWT |
| Storage | Privy Cloud | MySQL DB |
| Sessions | Privy Managed | Redis + JWT |
| Recovery | Privy Built-in | Email-based |
| 2FA | Via Privy | Future (TOTP) |

#### Required Integrations
| Service | Purpose | Used By |
|---------|---------|---------|
| Privy | User Auth & Wallets | Mobile App |
| Custom Auth | Admin Authentication | Admin Panel |
| Stripe | Payments | Both |
| 1inch | DEX Aggregation | Mobile App |
| Aave | Earning/Lending | Mobile App |
| Arbitrum RPC | L2 Execution | Mobile App |
| Base RPC | L2 Execution | Mobile App |
| Vertex AI | Primary LLM | Backend |
| AWS Bedrock | Fallback LLM | Backend |

### 10. Security Requirements

#### User Security (Mobile App)
- **Privy-Managed Security**
  - MPC key management
  - Social auth security
  - Wallet recovery
  - No private key exposure

#### Admin Security (Admin Console)
- **Custom Auth Security**
  - Strong password policy (min 12 chars, mixed case, numbers, symbols)
  - Failed login lockout (5 attempts)
  - Session timeout (30 minutes inactive)
  - Password expiry (90 days)
  - Audit logging all actions
  - IP whitelist (optional)

#### System Security
- **API Security**
  - Different auth middleware for user/admin
  - Rate limiting per endpoint
  - Request validation
  - SQL injection prevention

- **Data Protection**
  - Sensitive data encryption
  - Separate user/admin databases
  - Role-based data access
  - PII protection

## 🗄️ Database Schema (Core Tables)

### User Tables (Privy-Managed + Local)
- **users**: Privy user references and metadata
- **wallets**: User wallet addresses from Privy
- **transactions**: Blockchain transactions
- **conversations**: Chat history
- **messages**: Chat messages
- **subscriptions**: Stripe subscriptions

### Admin Tables (Separate Schema)
- **admin_users**: Admin accounts
- **admin_sessions**: Active sessions
- **admin_roles**: Role definitions
- **admin_permissions**: Permission mappings
- **password_resets**: Reset tokens
- **admin_audit_logs**: Admin action logs

### Shared Tables
- **settings**: Global configuration
- **system_logs**: System events

## 🔐 Access Control Matrix

| Feature | End User | Admin | Auditor |
|---------|----------|--------|---------|
| Mobile App Access | ✅ | ❌ | ❌ |
| Chat Interface | ✅ | ❌ | ❌ |
| Execute Swaps | ✅ | ❌ | ❌ |
| View Own Portfolio | ✅ | ❌ | ❌ |
| Admin Login | ❌ | ✅ | ✅ |
| View All Users | ❌ | ✅ | ✅ |
| Modify Users | ❌ | ✅ | ❌ |
| View Transactions | ❌ | ✅ | ✅ |
| System Config | ❌ | ✅ | ❌ |
| Export Data | ❌ | ✅ | ✅ |

## ❌ Out of Scope for MVP

The following features are explicitly excluded from MVP:
- Single sign-on (SSO) for admin panel
- Biometric authentication for admin
- Complex KYC flows (placeholder banners only)
- Multiple earn providers (Aave only)
- Telemetry dashboards
- Agent monitoring module
- Multi-venue yield routing
- Advanced bridges
- Deep analytics in admin panel
- Automated DCA strategies
- Auto-save systems
- P2P transfers
- Push trading alerts
- Custom designer UX
- Custodial services

## 📊 Success Metrics

### Authentication Metrics
- User signup success rate: > 90%
- Admin login success rate: > 95%
- Password reset completion: > 80%
- Session security incidents: 0

### Launch Criteria
- [ ] Privy auth working for users
- [ ] Admin auth system functional
- [ ] All happy paths tested and working
- [ ] 99% uptime on testnet
- [ ] < 3 second response time for chat
- [ ] Successful audit of smart contract interactions
- [ ] Admin panel fully functional with separate auth

### User Metrics (Post-Launch)
- Time to first transaction: < 5 minutes
- Swap success rate: > 95%
- User retention (7-day): > 60%
- Support ticket rate: < 5%

## 🚢 Delivery Phases

### Phase 1: Foundation (Weeks 1-4)
- **User Auth**: Privy SDK integration
- **Admin Auth**: Custom auth system build
  - Registration flow
  - Login system
  - Password recovery
  - Session management
- Wallet creation flow (Privy)
- Basic chat interface
- Database schema (separate user/admin)
- Admin panel skeleton

### Phase 2: Core Features (Weeks 5-8)
- Swap functionality (1inch)
- Earn integration (Aave)
- Portfolio views
- Fiat funding (Stripe)
- Agent system implementation
- Admin dashboard modules

### Phase 3: Polish & Testing (Weeks 9-12)
- End-to-end testing (both auth systems)
- Security audit (especially admin auth)
- Performance optimization
- Bug fixes
- Documentation
- Deployment preparation

## 👥 Team Composition

- **Backend + DevOps:** 1.5 FTE
  - User auth (Privy integration)
  - Admin auth (custom build)
  - API development
- **Mobile Development:** 1 FTE
- **Admin Panel:** 1 FTE
- **Tech Lead:** 0.5 FTE (architecture + integration)
- **Total:** 4 FTE

## 🔄 User Stories (Happy Paths)

### End User Stories

#### UC-1: User Sign Up → Wallet Creation
1. User opens mobile app
2. Selects sign-up method (Google/Apple/Email)
3. Authenticates via Privy
4. System creates MPC wallet automatically
5. Display wallet address & chain
6. Chat greets user and proposes funding

### Admin User Stories

#### AC-1: Admin Registration
1. Admin receives invitation email
2. Clicks registration link
3. Fills registration form
4. Sets strong password
5. Verifies email
6. Logs in to admin panel

#### AC-2: Admin Login
1. Navigate to `/admin/login`
2. Enter email and password
3. System validates credentials
4. Generate JWT token
5. Redirect to dashboard
6. Show role-appropriate interface

#### AC-3: Admin Password Recovery
1. Click "Forgot Password"
2. Enter registered email
3. Receive reset email
4. Click reset link
5. Set new password
6. Login with new password

### Shared User Stories

#### UC-2: Fund Wallet
1. User selects "Fund wallet" in chat
2. Inline card captures amount & method
3. Show fees and ETA
4. Process payment via Stripe
5. Display receipt card

#### UC-3: Execute Swap
1. User types "Swap 100 USDC to ETH"
2. Show preview card with route & fees
3. User confirms
4. Execute trade via 1inch
5. Display receipt with tx hash

## 🏗️ Architecture Summary

```
┌──────────────────────────────────────────────────┐
│                  FRONTEND LAYER                   │
├────────────────────┬──────────────────────────────┤
│    Mobile App      │       Admin Console          │
│  (React Native)    │      (React/Next.js)         │
└────────┬───────────┴─────────────┬────────────────┘
         │                         │
    ┌────▼─────┐            ┌─────▼──────┐
    │  Privy   │            │  Custom    │
    │   Auth   │            │    Auth    │
    └────┬─────┘            └─────┬──────┘
         │                         │
         └───────────┬─────────────┘
                     │
           ┌─────────▼──────────┐
           │    API Gateway     │
           └─────────┬──────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
│ AI Brain  │ │  CrewAI   │ │   DeFi    │
│  Router   │ │  Agents   │ │  Services │
└───────────┘ └───────────┘ └───────────┘
```

## 📝 API Endpoints Structure

### Public Endpoints (No Auth)
```
POST   /api/v1/admin/login
POST   /api/v1/admin/forgot-password
POST   /api/v1/admin/reset-password
GET    /api/v1/health
```

### User Endpoints (Privy Auth)
```
GET    /api/v1/user/profile
GET    /api/v1/user/portfolio
POST   /api/v1/chat/message
POST   /api/v1/swap/quote
POST   /api/v1/swap/execute
POST   /api/v1/earn/deposit
POST   /api/v1/earn/withdraw
```

### Admin Endpoints (JWT Auth)
```
POST   /api/v1/admin/register (with invitation)
GET    /api/v1/admin/users
GET    /api/v1/admin/users/:id
PUT    /api/v1/admin/users/:id/status
GET    /api/v1/admin/transactions
GET    /api/v1/admin/dashboard/stats
GET    /api/v1/admin/audit-logs
POST   /api/v1/admin/settings
```

## ✅ Definition of Done

A feature is considered complete when:
1. Functionality works end-to-end
2. Both auth systems tested (Privy + Custom)
3. Unit tests written and passing
4. Integration tests passing
5. Security review completed (especially admin auth)
6. Documentation updated
7. Code reviewed and approved
8. Deployed to staging environment
9. Product owner acceptance

## 🚨 Risk Mitigation

### Technical Risks
- **Dual Auth Systems**: Clear separation, different middleware
- **LLM Rate Limits**: Multi-provider fallback system
- **Chain Congestion**: L2 focus (Arbitrum/Base)
- **Wallet Security**: MPC via Privy, no key exposure

### Security Risks
- **Admin Access**: Separate auth, strong passwords, audit logs
- **Session Hijacking**: JWT expiry, refresh tokens, HTTPS only
- **Brute Force**: Rate limiting, account lockout
- **Data Breach**: Encryption, separate databases

## 📋 Acceptance Criteria

The MVP is considered successful when:
- [ ] Privy auth working for mobile users
- [ ] Custom auth system working for admins
- [ ] Password recovery functional for admins
- [ ] All 5 user happy paths complete
- [ ] All 3 admin happy paths complete
- [ ] Mobile app functional on iOS and Android
- [ ] Admin panel operational with role-based access
- [ ] Swaps execute successfully on Arbitrum and Base
- [ ] Aave deposits/withdrawals working
- [ ] Stripe payments processing
- [ ] Chat understands basic DeFi intents
- [ ] Portfolio tracking accurate
- [ ] System handles 100 concurrent users
- [ ] Admin audit logs capturing all actions
- [ ] Documentation complete for both systems

---

**Version:** 2.0  
**Last Updated:** November 2024  
**Status:** Ready for Development  
**Key Change:** Separated user authentication (Privy) from admin authentication (custom system)
