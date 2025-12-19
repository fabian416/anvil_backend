# 📋 Anvil Complete User Flows - Summary & Index

## Overview

This document provides a complete index of all user flows for the Anvil platform, organized by user type. All flows document the "happy path" - successful completion of tasks with expected outcomes.

**Total User Types:** 3  
**Total Flows Documented:** 28  
**Documentation Status:** Complete ✅

---

## User Types & Access Levels

| User Type | Role | Platform | Access Level | Primary Use Cases |
|-----------|------|----------|--------------|-------------------|
| **CLIENT** | role=2 | Mobile App | Personal wallet, trading, DeFi | Trading, saving, earning, portfolio management |
| **ADMIN** | role=0 | Web Console | Full CRUD access | User management, system config, support |
| **AUDITOR** | role=1 | Compliance Console | Read-only access | Audit trails, compliance monitoring, reporting |

---

## CLIENT User Flows (10 Flows)

**Platform:** Mobile App (iOS/Android)  
**Documents:** 
- `anvil_user_flows_client_part1.md` (Flows 1-5)
- `anvil_user_flows_client_part2.md` (Flows 6-10)

### Flow Index

#### 1. Onboarding & Authentication ⏱️ 2-3 minutes
**Goal:** Create account and access Anvil app

**Key Steps:**
- App launch and welcome screen
- Email input and Privy magic link
- Privy authentication and wallet creation
- Backend user creation
- Profile setup
- Terms & conditions acceptance
- First view of dashboard

**Database Tables:**
- `users` (INSERT)
- `wallets` (INSERT)
- `chain_addresses` (INSERT × 3)

**External Services:**
- Privy (authentication + wallet creation)

**Success Criteria:**
- User record created with status=ACTIVE
- Wallet created with MPC security
- User can access home dashboard
- Welcome email sent

---

#### 2. Wallet Setup & Funding ⏱️ 3-5 minutes
**Goal:** Deposit $100 USD to buy USDC on Arbitrum

**Key Steps:**
- Initiate funding request
- Configure amount, asset, and chain
- Create Stripe PaymentIntent
- Complete payment via Stripe
- Webhook processing
- On-chain USDC purchase
- Transaction monitoring
- Balance update and notification

**Database Tables:**
- `funding_transactions` (INSERT)
- `transactions` (INSERT)
- `chain_addresses` (UPDATE)
- `notifications` (INSERT)

**External Services:**
- Stripe (payment processing)
- 1inch/0x (DEX aggregation)
- Arbitrum RPC (blockchain)

**Success Criteria:**
- Payment processed: $103.70
- USDC received: 100 USDC
- Balance updated in UI
- User notified via push

---

#### 3. Token Swap Flow ⏱️ 1-2 minutes
**Goal:** Swap 50 USDC for ETH on Arbitrum

**Key Steps:**
- Navigate to Trade tab
- Configure swap (50 USDC → ETH)
- AI agent fetches DEX quote
- User reviews quote and fees
- Execute swap transaction
- Monitor confirmation
- Update balances
- Success notification

**Database Tables:**
- `transactions` (INSERT)
- `chain_addresses` (UPDATE)
- `llm_conversations` (INSERT)
- `agent_executions` (INSERT)
- `agent_tasks` (INSERT)
- `agent_tools_usage` (INSERT)
- `notifications` (INSERT)

**External Services:**
- 1inch (DEX aggregator)
- Vertex AI (AI agent)
- Privy (transaction signing)
- Arbitrum RPC

**Success Criteria:**
- Swap executed: 50 USDC → 0.0204 ETH
- Transaction confirmed on-chain
- Balances updated correctly
- Transaction in activity feed

---

#### 4. Yield Farming (Earn) Flow ⏱️ 1-2 minutes
**Goal:** Deposit 50 USDC into Aave for 4.2% APY

**Key Steps:**
- Navigate to Earn tab
- Browse Aave opportunity
- AI risk analysis
- Review deposit details
- Execute Aave deposit
- Monitor confirmation
- Position tracking starts
- Background job updates earnings

**Database Tables:**
- `earn_positions` (INSERT)
- `transactions` (INSERT)
- `chain_addresses` (UPDATE)
- `llm_conversations` (INSERT)
- `agent_executions` (INSERT)
- `notifications` (INSERT)

**External Services:**
- Aave V3 (protocol)
- Vertex AI (risk analysis)
- Privy (signing)
- Arbitrum RPC

**Success Criteria:**
- 50 USDC deposited to Aave
- Position earning 4.2% APY
- Hourly earnings updates
- Position visible in Earn tab

---

#### 5. Recurring Savings Setup ⏱️ 2 minutes + automatic
**Goal:** Auto-save $20 weekly to Aave every Monday

**Key Steps:**
- Navigate to Auto-Save
- Configure schedule (weekly, Monday, $20, Aave)
- AI projection analysis
- Review schedule and projections
- Create schedule
- Success confirmation
- Automatic execution (every Monday)

**Database Tables:**
- `save_schedules` (INSERT)
- `earn_positions` (UPDATE on execution)
- `transactions` (INSERT on execution)
- `notifications` (INSERT)

**External Services:**
- Vertex AI (projections)
- Aave V3 (deposits)
- Privy (signing)

**Success Criteria:**
- Schedule created and active
- First execution on next Monday
- User notified of each save
- Compound earnings in Aave

---

#### 6. Perpetual Trading (Hyperliquid) ⏱️ 2-3 minutes + monitoring
**Goal:** Open 5x leveraged long position on ETH-USD

**Key Steps:**
- Navigate to Perpetuals
- Configure position via AI chat
- AI risk assessment
- Review position details
- Confirm with risk warnings
- Execute on Hyperliquid
- Real-time PnL monitoring
- Liquidation alerts (if needed)

**Database Tables:**
- `hyperliquid_positions` (INSERT)
- `transactions` (INSERT)
- `llm_conversations` (INSERT)
- `agent_executions` (INSERT)
- `notifications` (INSERT)

**External Services:**
- Hyperliquid API (perpetual trading)
- Vertex AI (risk analysis)

**Success Criteria:**
- Position opened: 0.102 ETH at 5x
- Entry price: $2,450.50
- Liquidation price: $1,960.40
- Real-time PnL updates
- Liquidation monitoring active

---

#### 7. AI Chat & Recommendations ⏱️ 3-5 seconds per message
**Goal:** Get personalized investment recommendations

**Key Steps:**
- Open AI chat
- Ask for recommendations
- Multi-agent workflow executes:
  - Portfolio analysis
  - Market research
  - Recommendation generation
- Receive actionable recommendations
- Execute recommendations directly

**Database Tables:**
- `llm_conversations` (INSERT)
- `agent_executions` (INSERT)
- `agent_tasks` (INSERT)
- `agent_tools_usage` (INSERT)

**External Services:**
- Vertex AI / Bedrock (LLM)
- Market data APIs

**Success Criteria:**
- Portfolio analyzed comprehensively
- Personalized recommendations generated
- Actionable buttons for execution
- Natural conversation flow

---

#### 8. Subscription Upgrade Flow ⏱️ 2-3 minutes
**Goal:** Upgrade from Free to Pro ($9.99/month)

**Key Steps:**
- Hit free plan limit (10 messages/day)
- View upgrade prompt
- Start 7-day free trial
- Add payment method via Stripe
- Trial activated
- Automatic billing after 7 days

**Database Tables:**
- `subscriptions` (INSERT)
- `subscription_payments` (INSERT on billing)
- `notifications` (INSERT)
- `audit_logs` (INSERT)

**External Services:**
- Stripe (subscription + payments)

**Success Criteria:**
- Trial started with no charge
- Payment method saved
- Unlimited conversations enabled
- Auto-billing after trial

---

#### 9. Portfolio Management ⏱️ Instant
**Goal:** View complete portfolio overview

**Key Steps:**
- Load home dashboard
- View total portfolio value
- See asset allocation
- Review all positions (spot, earn, perps)
- Check recent activity
- Quick actions available

**Database Tables:**
- `users` (SELECT)
- `chain_addresses` (SELECT)
- `transactions` (SELECT)
- `earn_positions` (SELECT)
- `hyperliquid_positions` (SELECT)

**Success Criteria:**
- Real-time portfolio value
- All positions visible
- Performance metrics shown
- Activity feed updated

---

#### 10. Notifications & Alerts ⏱️ Instant to 1 minute
**Goal:** Receive timely notifications about account activity

**Key Steps:**
- Notification created in database
- Background worker picks up
- Sent via appropriate channel:
  - Push (FCM)
  - Email (SendGrid)
  - SMS (Twilio) for urgent
- User receives and opens
- Read status tracked

**Database Tables:**
- `notifications` (INSERT, UPDATE)

**External Services:**
- FCM (push notifications)
- SendGrid (email)
- Twilio (SMS)

**Success Criteria:**
- Notifications delivered on time
- Priority routing works
- User can read in-app
- Urgent alerts via multiple channels

---

## ADMIN User Flows (10 Flows)

**Platform:** Web Admin Console  
**Document:** `anvil_user_flows_admin.md`

### Flow Index

#### 1. Admin Login & Dashboard ⏱️ 30 seconds
**Goal:** Securely access admin console

**Key Steps:**
- Navigate to admin.anvil.com
- Enter credentials + 2FA
- Authenticate and log
- Load system dashboard
- View platform statistics
- Check pending actions

**Database Tables:**
- `users` (SELECT, UPDATE)
- `audit_logs` (INSERT)

**Success Criteria:**
- Secure login with 2FA
- Login logged in audit trail
- Dashboard shows real-time stats
- IP address recorded

---

#### 2. User Management & KYC Approval ⏱️ 3-5 minutes
**Goal:** Review and approve user KYC

**Key Steps:**
- Navigate to KYC queue
- Select pending application
- Review documents and info
- Verify identity
- Approve or reject KYC
- Log admin action
- Notify user of decision

**Database Tables:**
- `users` (SELECT, UPDATE)
- `audit_logs` (INSERT)
- `notifications` (INSERT)

**Success Criteria:**
- KYC status updated
- Admin action audited
- User notified
- Compliance documented

---

#### 3. Transaction Monitoring & Support ⏱️ 5-10 minutes
**Goal:** Investigate and retry failed transaction

**Key Steps:**
- Monitor failed transactions
- Investigate root cause
- Diagnose issue
- Retry with correct parameters
- Monitor retry success
- Notify user of resolution
- Log admin action

**Database Tables:**
- `transactions` (SELECT, INSERT, UPDATE)
- `audit_logs` (INSERT)
- `notifications` (INSERT)

**Success Criteria:**
- Failed transaction identified
- Issue diagnosed and fixed
- Transaction retried successfully
- User notified

---

#### 4. System Configuration Management ⏱️ 2 minutes
**Goal:** Update system setting

**Key Steps:**
- Navigate to settings
- Select setting to modify
- Enter new value and reason
- Confirm change
- Update database
- Log admin action
- Clear cache
- Notify team

**Database Tables:**
- `settings` (SELECT, UPDATE)
- `audit_logs` (INSERT)

**Success Criteria:**
- Setting updated
- Change logged
- Cache cleared
- Takes effect immediately

---

#### 5. AI Model Configuration ⏱️ 3 minutes
**Goal:** Configure AI model availability

**Success Criteria:**
- Model configuration updated
- Costs tracked
- Failover rules set

---

#### 6. Cost Monitoring & Alerts ⏱️ 5 minutes
**Goal:** Monitor and optimize AI costs

**Success Criteria:**
- Costs monitored in real-time
- Alerts configured
- Reports generated

---

#### 7. Emergency Position Management ⏱️ 10 minutes
**Goal:** Emergency withdraw from compromised protocol

**Success Criteria:**
- Position force-closed
- User funds secured
- Action logged

---

#### 8. Subscription Management ⏱️ 5 minutes
**Goal:** Manage user subscriptions

**Success Criteria:**
- Subscription status managed
- Refunds processed
- Actions logged

---

#### 9. Audit Log Review ⏱️ 10 minutes
**Goal:** Review admin action history

**Success Criteria:**
- All actions visible
- Filterable and exportable
- Compliance ready

---

#### 10. Analytics & Reporting ⏱️ 5 minutes
**Goal:** Generate platform analytics

**Success Criteria:**
- Reports generated
- Metrics accurate
- Exportable formats

---

## AUDITOR User Flows (8 Flows)

**Platform:** Web Compliance Console  
**Document:** `anvil_user_flows_auditor.md`

### Flow Index

#### 1. Auditor Login & Dashboard ⏱️ 30 seconds
**Goal:** Access compliance console

**Key Characteristics:**
- Read-only access
- Compliance-focused metrics
- All actions logged

---

#### 2. Audit Log Exploration ⏱️ 5 minutes
**Goal:** Review admin action trail

**Key Features:**
- Complete audit history
- Filter and search
- Export for compliance

---

#### 3. Transaction Compliance Review ⏱️ 3-5 minutes
**Goal:** Monitor for AML compliance

**Key Checks:**
- Large transactions (>$10k CTR)
- Suspicious patterns
- Risk assessments

---

#### 4. User Activity Monitoring ⏱️ 5 minutes
**Goal:** Detect unusual activity patterns

**Key Features:**
- Anomaly detection
- Pattern analysis
- Risk flagging

---

#### 5. Financial Reporting ⏱️ 2-5 minutes
**Goal:** Generate financial reports

**Key Reports:**
- Monthly summaries
- Revenue breakdowns
- Cost analysis

---

#### 6. KYC Compliance Review ⏱️ 3 minutes
**Goal:** Verify KYC processes

**Key Reviews:**
- KYC approval history
- Document verification
- Compliance checks

---

#### 7. System Health Monitoring ⏱️ 2 minutes
**Goal:** Monitor system status

**Key Metrics:**
- Uptime
- Transaction success rates
- Error rates

---

#### 8. Export Compliance Reports ⏱️ 3 minutes
**Goal:** Export data for audits

**Key Exports:**
- Audit trails
- Transaction reports
- User data (GDPR)

---

## Database Coverage

### Tables by User Type

#### CLIENT Users Access:
✅ `users` (own record)  
✅ `wallets` (own wallet)  
✅ `chain_addresses` (own addresses)  
✅ `transactions` (own transactions)  
✅ `hyperliquid_positions` (own positions)  
✅ `earn_positions` (own positions)  
✅ `save_schedules` (own schedules)  
✅ `funding_transactions` (own funding)  
✅ `subscriptions` (own subscription)  
✅ `subscription_payments` (own payments)  
✅ `llm_conversations` (own conversations)  
✅ `agent_executions` (own executions)  
✅ `notifications` (own notifications)  

#### ADMIN Users Access:
✅ All 27 tables (FULL CRUD)

#### AUDITOR Users Access:
✅ All 27 tables (READ-ONLY)

---

## External Service Integration

### By Flow Type

**Authentication & Wallet:**
- Privy (all CLIENT flows)

**Payments:**
- Stripe (funding, subscriptions)

**Blockchain:**
- Arbitrum RPC (most transactions)
- Base RPC (cross-chain)
- Hyperliquid API (perpetuals)

**DeFi Protocols:**
- Aave V3 (earning)
- Compound (earning)
- Uniswap V3 (swaps)
- 1inch (aggregation)
- 0x (aggregation)

**AI & ML:**
- Google Cloud Vertex AI (primary LLM)
- AWS Bedrock (failover LLM)

**Notifications:**
- Firebase Cloud Messaging (push)
- SendGrid (email)
- Twilio (SMS)

---

## Performance Metrics

### Average Completion Times

| Flow Type | Time Range | Complexity |
|-----------|------------|------------|
| Authentication | 30s - 3min | Low |
| Wallet Operations | 1-5min | Medium |
| Trading | 1-3min | Medium |
| DeFi Operations | 1-2min | Medium |
| AI Interactions | 3-5s | Low |
| Admin Actions | 2-10min | Medium-High |
| Auditor Reviews | 3-10min | Medium |

### Database Operations Per Flow

| Flow Type | SELECT | INSERT | UPDATE | DELETE |
|-----------|--------|--------|--------|--------|
| CLIENT (avg) | 5-10 | 3-5 | 2-3 | 0 |
| ADMIN (avg) | 10-20 | 2-4 | 1-3 | 0-1 |
| AUDITOR (avg) | 20-50 | 0 | 0 | 0 |

---

## Security & Compliance

### All User Flows Include:

✅ **Authentication:**
- JWT tokens with expiry
- Role-based access control
- 2FA for ADMIN/AUDITOR

✅ **Audit Trails:**
- All actions logged in `audit_logs`
- IP address tracking
- Timestamp precision

✅ **Data Protection:**
- Encrypted sensitive fields
- PII handling per GDPR
- Secure API communication

✅ **Compliance:**
- AML/CTR monitoring
- KYC verification
- Transaction limits

---

## Success Criteria Summary

### CLIENT Flows Success Metrics:
- ✅ Transaction completion rate >98%
- ✅ Average swap time <2 minutes
- ✅ AI response time <5 seconds
- ✅ Notification delivery <1 minute
- ✅ User satisfaction >4.5/5

### ADMIN Flows Success Metrics:
- ✅ All actions audited 100%
- ✅ KYC review time <5 minutes
- ✅ Support response time <15 minutes
- ✅ System uptime >99.9%

### AUDITOR Flows Success Metrics:
- ✅ Complete audit trail access
- ✅ Report generation <5 minutes
- ✅ Zero data modification capability
- ✅ Export success rate 100%

---

## Error Handling

### All Flows Include:

1. **Validation:**
   - Input validation before submission
   - Balance checks before transactions
   - Permission verification

2. **Error Recovery:**
   - Retry mechanisms for failed transactions
   - Fallback providers (Vertex → Bedrock)
   - User-friendly error messages

3. **Monitoring:**
   - Real-time transaction monitoring
   - Background jobs for confirmation
   - Automated alerts for failures

4. **Logging:**
   - All errors logged with context
   - Stack traces for debugging
   - User impact assessment

---

## Testing Checklist

### Per User Flow:

- [ ] Happy path completes successfully
- [ ] All database records created correctly
- [ ] External API calls succeed
- [ ] User receives appropriate notifications
- [ ] Audit trail created
- [ ] UI updates reflect changes
- [ ] Error handling works as expected
- [ ] Performance within SLA
- [ ] Security checks pass
- [ ] Compliance requirements met

---

## Implementation Priority

### Phase 1: MVP (Weeks 1-4)
1. CLIENT: Onboarding & Authentication
2. CLIENT: Wallet Setup & Funding
3. CLIENT: Token Swap Flow
4. ADMIN: Login & Dashboard
5. ADMIN: User Management

### Phase 2: Core Features (Weeks 5-6)
6. CLIENT: Yield Farming
7. CLIENT: AI Chat & Recommendations
8. ADMIN: Transaction Monitoring
9. AUDITOR: Login & Audit Logs

### Phase 3: Advanced Features (Weeks 7-8)
10. CLIENT: Perpetual Trading
11. CLIENT: Recurring Savings
12. CLIENT: Portfolio Management
13. ADMIN: System Configuration
14. AUDITOR: Compliance Monitoring

---

## Documentation Index

| Document | User Type | Flows | Pages |
|----------|-----------|-------|-------|
| `anvil_user_flows_client_part1.md` | CLIENT | 1-5 | ~50 |
| `anvil_user_flows_client_part2.md` | CLIENT | 6-10 | ~40 |
| `anvil_user_flows_admin.md` | ADMIN | 1-10 | ~60 |
| `anvil_user_flows_auditor.md` | AUDITOR | 1-8 | ~35 |
| **Total** | **All** | **28** | **~185** |

---

## Next Steps

1. **Review & Validate:** 
   - Technical team reviews flows
   - Product team validates UX
   - Security team checks compliance

2. **Implementation:**
   - Backend API development
   - Frontend UI/UX implementation
   - Testing & QA

3. **Documentation:**
   - API documentation
   - User guides
   - Admin manuals

4. **Launch:**
   - Beta testing
   - Production deployment
   - User onboarding

---

**Version:** 1.0  
**Last Updated:** November 16, 2025  
**Status:** Complete ✅  
**Total Documentation:** 185 pages

**All user flows are production-ready and implementation-ready!** 🚀
