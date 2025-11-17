# 📋 Anvil Platform - Product Requirements Document (PRD)

## Complete Product Specification

**Version:** 1.0  
**Date:** November 2025  
**Product Owner:** CTO  
**Target Launch:** April 2026

---

## 🎯 Executive Summary

### Vision
Anvil is a mobile-first DeFi trading platform that makes cryptocurrency trading, yield farming, and perpetual futures accessible to mainstream users through an intuitive interface powered by AI assistance.

### Mission
Democratize DeFi by removing technical barriers and providing institutional-grade trading tools in a user-friendly mobile application.

### Target Audience
- **Primary:** Crypto-curious individuals with $1K-$50K to invest
- **Secondary:** Experienced traders seeking simplified DeFi access
- **Geographic:** Global, starting with US, EU, LATAM

---

## 📊 Market Analysis

### Market Size
```yaml
Total Addressable Market (TAM):
  - Global crypto users: 420M (2024)
  - DeFi users: 7M active wallets
  - Target: Crypto-curious non-DeFi users

Serviceable Addressable Market (SAM):
  - English-speaking markets: ~150M potential users
  - Mobile-first users: ~120M

Serviceable Obtainable Market (SOM):
  - Year 1 target: 10,000 users
  - Year 3 target: 100,000 users
```

### Competition
```yaml
Direct Competitors:
  - Coinbase Wallet: Established, complex UI
  - MetaMask: Technical, not mobile-first
  - Argent: Limited features
  - Dharma: Acquired by OpenSea

Competitive Advantages:
  - AI-powered assistance
  - Simplified UX
  - Multi-protocol aggregation
  - Perpetuals in mobile
  - Automated DCA (Save feature)
```

---

## 👥 User Personas

### Persona 1: Sarah the Professional
```yaml
Demographics:
  Age: 28-35
  Occupation: Marketing Manager
  Income: $80K/year
  Crypto Experience: Owns BTC on Coinbase

Goals:
  - Earn yield on crypto holdings
  - Learn about DeFi safely
  - Diversify investments

Pain Points:
  - DeFi too complex
  - Afraid of making mistakes
  - No time to research
  - Security concerns

How Anvil Helps:
  - Simple, guided interface
  - AI explains everything
  - Built-in wallet security
  - Automated strategies
```

### Persona 2: Mike the Trader
```yaml
Demographics:
  Age: 22-28
  Occupation: Software Engineer
  Income: $120K/year
  Crypto Experience: Active trader

Goals:
  - Access DeFi protocols easily
  - Trade perpetuals on mobile
  - Maximize yields
  - Quick execution

Pain Points:
  - Fragmented DeFi landscape
  - High gas fees
  - Complex wallet management
  - No good mobile perps

How Anvil Helps:
  - One app for everything
  - L2 support (low fees)
  - Integrated wallet (Privy)
  - Hyperliquid integration
```

### Persona 3: Alex the Saver
```yaml
Demographics:
  Age: 25-40
  Occupation: Various
  Income: $50K-$100K/year
  Crypto Experience: Minimal

Goals:
  - Build crypto savings
  - Automated investing (DCA)
  - Better returns than bank
  - Long-term wealth building

Pain Points:
  - Timing the market
  - Forgetting to invest
  - Too much volatility
  - Confusion about options

How Anvil Helps:
  - Automated DCA schedules
  - Stable earning opportunities
  - Simple setup
  - AI guidance
```

---

## 🎨 Product Overview

### Core Value Propositions

**1. Simplicity**
- One tap to trade
- No seed phrases to manage (Privy)
- Plain English, no jargon
- AI explains everything

**2. Power**
- Access 20+ DeFi protocols
- Competitive rates (1inch)
- Perpetual trading (Hyperliquid)
- Professional-grade features

**3. Safety**
- Embedded wallet (Privy)
- Transparent fees
- Smart contract audits
- Insured custody

**4. Intelligence**
- AI trading assistant
- Personalized recommendations
- Market insights
- Portfolio analysis

---

## 🚀 Feature Specifications

### MVP Features (Phase 1)

#### 1. User Authentication
```yaml
Requirements:
  - Email/social login via Privy
  - Automatic wallet creation
  - Biometric authentication
  - Session management

User Stories:
  - As a new user, I want to sign up with my email
  - As a user, I want to use Face ID to login
  - As a user, I want my wallet created automatically

Acceptance Criteria:
  - Signup completes in < 2 minutes
  - Wallet created on first login
  - Biometric works on supported devices
  - Session persists 30 days
```

#### 2. Wallet Management
```yaml
Requirements:
  - Multi-chain support (Arbitrum, Base)
  - Real-time balance updates
  - Transaction history
  - Asset details

User Stories:
  - As a user, I want to see all my token balances
  - As a user, I want to view my transaction history
  - As a user, I want to switch between chains

Acceptance Criteria:
  - Balances update on pull-to-refresh
  - Transaction history shows last 100 txs
  - Supports ETH, USDC, USDT, DAI
  - Chain switching works seamlessly
```

#### 3. Token Swaps
```yaml
Requirements:
  - 1inch integration for best rates
  - Slippage tolerance settings
  - Gas estimation
  - Transaction confirmation

User Stories:
  - As a user, I want to swap USDC for ETH
  - As a user, I want to see the exchange rate
  - As a user, I want to set my max slippage

Acceptance Criteria:
  - Quote fetched in < 2 seconds
  - Displays estimated gas cost
  - Shows total cost breakdown
  - Transaction submits successfully
  - User receives confirmation
```

#### 4. Earn (Yield Farming)
```yaml
Requirements:
  - Aave V3 integration
  - APY display (real-time)
  - Deposit/withdraw flows
  - Position tracking

User Stories:
  - As a user, I want to earn yield on USDC
  - As a user, I want to see my current earnings
  - As a user, I want to withdraw anytime

Acceptance Criteria:
  - Shows current APY for each asset
  - Deposit completes in one transaction
  - Position shows accrued interest
  - Withdrawal processes in < 5 min
```

#### 5. Admin Portal (Basic)
```yaml
Requirements:
  - User management
  - KYC approval workflow
  - Transaction monitoring
  - System settings

User Stories:
  - As an admin, I want to approve KYC
  - As an admin, I want to view all users
  - As an admin, I want to monitor transactions

Acceptance Criteria:
  - Can search users by email
  - KYC documents viewable
  - Approval/rejection workflow
  - Audit trail of all actions
```

---

### Phase 2 Features

#### 6. Perpetual Trading
```yaml
Requirements:
  - Hyperliquid integration
  - Long/short positions
  - Leverage selector (up to 20x)
  - Real-time P&L
  - Liquidation alerts

User Stories:
  - As a trader, I want to go long ETH with 10x leverage
  - As a trader, I want to see my unrealized P&L
  - As a trader, I want alerts before liquidation

Acceptance Criteria:
  - Position opens in < 5 seconds
  - P&L updates every 10 seconds
  - Liquidation warning at 90% threshold
  - Can close position anytime
```

#### 7. AI Assistant
```yaml
Requirements:
  - Vertex AI (Gemini) integration
  - Natural language queries
  - Portfolio analysis
  - Market insights
  - Action recommendations

User Stories:
  - As a user, I want to ask "How's my portfolio doing?"
  - As a user, I want AI to explain DeFi terms
  - As a user, I want trading suggestions

Acceptance Criteria:
  - Responds in < 3 seconds
  - Context-aware (knows user's portfolio)
  - Can execute actions (with confirmation)
  - Conversation history saved
```

#### 8. Save (Automated DCA)
```yaml
Requirements:
  - Recurring buy schedules
  - Flexible frequency (daily, weekly, monthly)
  - Multiple assets supported
  - Automatic execution

User Stories:
  - As a user, I want to auto-buy $50 of ETH weekly
  - As a user, I want to modify my schedule
  - As a user, I want to pause/resume

Acceptance Criteria:
  - Schedule creation in < 1 minute
  - Executes on time (±1 hour)
  - Email notification on execution
  - Can pause/cancel anytime
```

#### 9. Subscriptions
```yaml
Requirements:
  - Stripe integration
  - Free and Pro tiers
  - Payment processing
  - Subscription management

Pricing:
  Free Tier:
    - Basic features
    - $100/day transaction limit
    - Standard support
    
  Pro Tier ($9.99/month):
    - All features
    - $10K/day transaction limit
    - Priority support
    - Advanced AI features
    - No transaction fees (first 30 days)

User Stories:
  - As a user, I want to upgrade to Pro
  - As a user, I want to manage my subscription
  - As a user, I want to cancel anytime

Acceptance Criteria:
  - Payment processes securely
  - Upgrade is immediate
  - Features unlock automatically
  - Can downgrade/cancel easily
```

---

## 🎨 Design Requirements

### Visual Design
```yaml
Style:
  - Modern, clean, minimal
  - Dark mode support
  - Consistent color palette
  - Clear typography

Colors:
  Primary: Blue (#3B82F6)
  Secondary: Purple (#8B5CF6)
  Success: Green (#10B981)
  Error: Red (#EF4444)
  Warning: Yellow (#F59E0B)

Typography:
  Headings: SF Pro Display / Roboto Bold
  Body: SF Pro Text / Roboto Regular
  Monospace: SF Mono / Roboto Mono (for addresses, amounts)
```

### UX Principles
```yaml
1. Progressive Disclosure:
   - Show basic info first
   - Advanced options behind "More" button
   - Complexity on demand

2. Immediate Feedback:
   - Loading states for everything
   - Success/error animations
   - Haptic feedback

3. Error Prevention:
   - Confirmation for high-value transactions
   - Clear error messages
   - Undo where possible

4. Accessibility:
   - WCAG 2.1 AA compliance
   - VoiceOver/TalkBack support
   - Minimum touch target: 44x44pt
   - Sufficient color contrast (4.5:1)
```

---

## 🔒 Security Requirements

### Authentication
```yaml
Required:
  - OAuth 2.0 with Privy
  - JWT tokens (1 hour expiry)
  - Refresh tokens (30 days)
  - Biometric authentication
  - 2FA for admins/auditors

Implementation:
  - Tokens stored in secure storage
  - Automatic token refresh
  - Session timeout after 30 min inactivity
```

### Transaction Security
```yaml
Required:
  - All transactions signed via Privy
  - Confirmation for > $100 transactions
  - Rate limiting (10 txs/min per user)
  - Transaction monitoring

Implementation:
  - Client-side validation
  - Server-side verification
  - Blockchain confirmation tracking
```

### Data Privacy
```yaml
Required:
  - GDPR compliance
  - User data encryption (at rest)
  - TLS 1.3 (in transit)
  - Right to be forgotten
  - Data export capability

Implementation:
  - AES-256 encryption
  - Regular security audits
  - Privacy policy
  - Terms of service
```

---

## 📊 Success Metrics

### Key Metrics (KPIs)

**Acquisition:**
```yaml
Target (Month 1): 1,000 signups
Target (Month 6): 10,000 signups
Measurement: New user registrations
```

**Activation:**
```yaml
Target: 60% complete first transaction within 24h
Measurement: Users who execute at least one transaction
```

**Retention:**
```yaml
Target (Day 7): 40%
Target (Day 30): 25%
Measurement: Users who return and transact
```

**Revenue:**
```yaml
Target (Month 1): $5K MRR
Target (Month 6): $50K MRR
Sources:
  - Transaction fees: 0.3%
  - Pro subscriptions: $9.99/month
  - Spread on swaps: 0.1%
```

**Engagement:**
```yaml
Target: 2.5 transactions per active user per week
Measurement: Avg transactions per WAU
```

### Product Metrics

**Performance:**
```yaml
- App launch time: < 3 seconds
- Time to first transaction: < 5 minutes
- Transaction success rate: > 95%
- API response time (P95): < 500ms
```

**Quality:**
```yaml
- Crash-free sessions: > 99.5%
- Bug reports: < 1 per 1000 sessions
- Customer support tickets: < 5%
```

---

## 🚫 Out of Scope (V1)

### Features Not Included
```yaml
Phase 1:
  - NFT trading
  - Cross-chain swaps (only L2s initially)
  - Limit orders
  - Advanced charting
  - Social features
  - Portfolio sharing
  - Multiple wallets per user

Future Consideration:
  - Fiat off-ramp
  - Credit card purchases
  - Staking
  - Governance token
  - Web application
```

---

## 🎯 Go-to-Market Strategy

### Launch Plan

**Phase 1: Closed Beta (Month 1-2)**
```yaml
Target: 100 beta testers
Goal: Validate core features
Criteria:
  - Invite-only
  - $100 transaction limit
  - Active feedback collection
  - Bug reporting
```

**Phase 2: Open Beta (Month 3-4)**
```yaml
Target: 1,000 early adopters
Goal: Test at scale
Criteria:
  - Public signup (waitlist)
  - $1K transaction limit
  - Performance testing
  - Feature refinement
```

**Phase 3: Public Launch (Month 5)**
```yaml
Target: 10,000 users
Goal: Market penetration
Strategy:
  - App store launch
  - Marketing campaign
  - Influencer partnerships
  - Referral program
```

### Marketing Channels

**Organic:**
```yaml
- Social media (Twitter, Reddit, Discord)
- Content marketing (blog, tutorials)
- SEO optimization
- Community building
```

**Paid:**
```yaml
- Social media ads (Facebook, Instagram)
- Google ads
- Influencer partnerships
- Crypto news sites
```

**Growth:**
```yaml
- Referral program ($10 credit for referrer + referee)
- App store optimization
- PR and media coverage
- Partnerships with protocols
```

---

## 💰 Business Model

### Revenue Streams

**1. Transaction Fees (Primary)**
```yaml
Structure:
  - 0.3% on swaps
  - 0.1% on earn deposits
  - Spread capture on rates

Projected:
  Month 1: $1K
  Month 6: $20K
  Month 12: $100K
```

**2. Subscription Revenue**
```yaml
Pro Tier: $9.99/month
Target:
  Month 1: 50 subs = $500
  Month 6: 500 subs = $5K
  Month 12: 2,000 subs = $20K
```

**3. Protocol Incentives**
```yaml
Source: Referral fees from protocols
Estimated: $5-10K/month at scale
```

### Cost Structure

**Fixed Costs (Monthly):**
```yaml
Infrastructure: $2,000
Third-party services: $1,000
Team: $60,000 (8 people)
Marketing: $10,000
Legal/Compliance: $5,000
Total: ~$78,000/month
```

**Variable Costs:**
```yaml
Customer acquisition: $20 per user
Support: $2 per active user
```

---

## ⚖️ Compliance & Legal

### Requirements
```yaml
KYC/AML:
  - Identity verification (Persona/Onfido)
  - $10K CTR threshold
  - Suspicious activity monitoring
  - Transaction limits for unverified

Licenses:
  - Money transmitter licenses (state-by-state)
  - FINRA registration (if needed)
  - Terms of Service
  - Privacy Policy

Insurance:
  - Cybersecurity insurance
  - Custody insurance
  - D&O insurance
```

---

## 🎯 Product Roadmap

### Q1 2026 (Launch)
- MVP features complete
- iOS and Android apps
- Admin portal
- Basic AI assistant

### Q2 2026
- Advanced AI features
- More DeFi protocols
- Improved charting
- Referral program

### Q3 2026
- NFT support
- Advanced trading features
- Social features
- Web application

### Q4 2026
- International expansion
- Fiat on/off ramps
- Institutional features
- API for developers

---

## ✅ Launch Checklist

### Pre-Launch
- [ ] All MVP features tested
- [ ] App store submissions approved
- [ ] Terms of Service finalized
- [ ] Privacy Policy finalized
- [ ] KYC provider integrated
- [ ] Payment processing set up
- [ ] Customer support ready
- [ ] Marketing materials prepared
- [ ] Legal entity established
- [ ] Insurance secured

### Launch Day
- [ ] App available in stores
- [ ] Marketing campaign live
- [ ] Support team staffed
- [ ] Monitoring active
- [ ] Social media active
- [ ] Press release distributed

### Post-Launch (Week 1)
- [ ] Monitor metrics daily
- [ ] Respond to feedback
- [ ] Fix critical bugs
- [ ] Adjust marketing based on data
- [ ] Scale infrastructure as needed

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Product Owner:** CTO  
**Next Review:** Monthly during development
