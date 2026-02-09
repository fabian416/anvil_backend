# 🚀 Anvil Platform - Implementation Guide for Software Factory

## Complete Development Roadmap & Execution Plan

**Project:** Anvil DeFi Trading Platform  
**Timeline:** 5 months (3 phases)  
**Team Size:** 6-8 developers  
**Budget:** Provided separately

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Team Structure](#team-structure)
3. [Development Timeline](#development-timeline)
4. [Sprint Planning](#sprint-planning)
5. [Technical Setup](#technical-setup)
6. [Development Guidelines](#development-guidelines)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Process](#deployment-process)
9. [Documentation Requirements](#documentation-requirements)
10. [Success Criteria](#success-criteria)

---

## 1. Project Overview

### 1.1 Deliverables Summary

| Deliverable | Description | Deadline |
|-------------|-------------|----------|
| **Mobile App** | iOS + Android (React Native) | Phase 2 end |
| **Web Console** | Admin + Auditor portal | Phase 2 end |
| **Backend API** | 63 REST endpoints | Phase 2 end |
| **Database** | 27 tables (MySQL) | Phase 1 end |
| **Integrations** | 11 external services | Phase 2 end |
| **Documentation** | API docs, user guides | Phase 3 end |

### 1.2 Key Features

**Core Features (MVP - Phase 1):**
1. ✅ User authentication (Privy)
2. ✅ Wallet management
3. ✅ Token swaps (1inch)
4. ✅ Basic yield farming (Aave)
5. ✅ Admin user management
6. ✅ Push notifications

**Advanced Features (Phase 2):**
7. ✅ Perpetual trading (Hyperliquid)
8. ✅ DCA save schedules
9. ✅ AI chat assistant (Gemini)
10. ✅ Complete yield protocols (Aave + Compound)
11. ✅ Subscriptions (Stripe)
12. ✅ Email/SMS notifications

**Enhancement Features (Phase 3):**
13. ✅ Advanced AI features
14. ✅ Portfolio analytics
15. ✅ Referral system
16. ✅ Advanced admin tools

### 1.3 Referenced Documents

All software factory engineers should review these documents:

1. **[User Stories](./user_stories_for_devs.md)** - 30 user stories across 3 user types
2. **[API Endpoints](./api_endpoints_for_devs.md)** - 63 complete API specifications
3. **[Database Models](./sqlalchemy_models/)** - SQLAlchemy models for 27 tables
4. **[Technical Architecture](./technical_architecture.md)** - Complete system design

---

## 2. Team Structure

### 2.1 Recommended Team Composition

| Role | Count | Responsibilities |
|------|-------|------------------|
| **Project Manager** | 1 | Planning, coordination, client communication |
| **Tech Lead** | 1 | Architecture, code review, technical decisions |
| **Mobile Developers** | 2 | React Native app (iOS + Android) |
| **Backend Developers** | 2 | Python/Node.js API, integrations |
| **DevOps Engineer** | 1 | Infrastructure, CI/CD, monitoring |
| **QA Engineer** | 1 | Testing, quality assurance |
| **UI/UX Designer** | 1 | Design, user experience (Part-time OK) |

**Total: 8-9 people**

### 2.2 Team Responsibilities Matrix

| Component | Lead | Support |
|-----------|------|---------|
| Mobile App | Mobile Dev 1 | Mobile Dev 2 |
| Web Console | Backend Dev 1 | Mobile Dev 2 |
| API Server | Backend Dev 1 | Backend Dev 2 |
| Database | Backend Dev 2 | Tech Lead |
| Integrations | Backend Dev 2 | Backend Dev 1 |
| Infrastructure | DevOps | Tech Lead |
| Testing | QA Engineer | All Devs |
| Documentation | Tech Lead | All Devs |

---

## 3. Development Timeline

### 3.1 Phase Overview

```
Month 1    Month 2    Month 3    Month 4    Month 5
├──────────┼──────────┼──────────┼──────────┼──────────┤
│ Phase 1  │ Phase 1  │ Phase 2  │ Phase 2  │ Phase 3  │
│ Sprint 1 │ Sprint 2 │ Sprint 3 │ Sprint 4 │ Sprint 5 │
│ MVP      │ MVP      │ Features │ Features │ Polish   │
└──────────┴──────────┴──────────┴──────────┴──────────┘
```

### 3.2 Phase 1: MVP Foundation (Weeks 1-8)

**Goal:** Working prototype with core trading functionality

**Sprint 1 (Weeks 1-4):**
- Week 1: Setup & Infrastructure
  - Set up repositories (GitHub)
  - Configure development environments
  - Deploy database (MySQL + migrations)
  - Set up CI/CD pipelines
  - Create project documentation structure

- Week 2-3: Core Backend
  - Authentication endpoints (JWT + Privy)
  - User management endpoints
  - Wallet endpoints
  - Database models implementation
  - Redis cache setup

- Week 4: Core Mobile
  - Project setup (React Native)
  - Navigation structure
  - Authentication screens
  - Dashboard scaffold
  - Privy integration

**Sprint 2 (Weeks 5-8):**
- Week 5: Trading Features
  - Swap quote endpoint
  - Swap execution endpoint
  - 1inch integration
  - Transaction history endpoint

- Week 6: Earn Features
  - Aave integration
  - Earn opportunities endpoint
  - Deposit/withdraw endpoints
  - APY data fetching

- Week 7: Mobile Trading UI
  - Swap screen with quote preview
  - Transaction confirmation flow
  - Transaction history screen
  - Earn opportunities screen

- Week 8: Admin Portal Start
  - Admin authentication
  - User management UI
  - Basic dashboard
  - KYC approval interface

**Deliverable:** Working MVP with swaps and basic earn

---

### 3.3 Phase 2: Complete Features (Weeks 9-16)

**Goal:** Full-featured platform with all core capabilities

**Sprint 3 (Weeks 9-12):**
- Week 9: Perpetuals Backend
  - Hyperliquid API integration
  - Open/close position endpoints
  - Position monitoring
  - Real-time price updates

- Week 10: Save Schedules
  - Create/manage schedule endpoints
  - Cron job scheduler
  - Execution logic
  - Notification triggers

- Week 11: AI Assistant Backend
  - Vertex AI (Gemini) integration
  - Chat endpoint with context
  - Conversation history
  - Token tracking & costs

- Week 12: Subscriptions
  - Stripe integration
  - Subscription creation/cancellation
  - Payment webhooks
  - Pro feature gating

**Sprint 4 (Weeks 13-16):**
- Week 13: Mobile Advanced Features
  - Perpetuals trading UI
  - Position monitoring screen
  - Real-time P&L updates

- Week 14: Mobile Advanced Features (cont.)
  - Save schedule creation UI
  - Schedule management
  - AI chat interface
  - Conversation history

- Week 15: Complete Admin Portal
  - Transaction monitoring
  - System settings management
  - AI model configuration
  - Audit log viewer

- Week 16: Notifications & Polish
  - Email notifications (SendGrid)
  - SMS notifications (Twilio)
  - Push notification refinement
  - Complete Compound integration

**Deliverable:** Feature-complete platform ready for beta

---

### 3.4 Phase 3: Polish & Launch (Weeks 17-20)

**Goal:** Production-ready platform with monitoring and documentation

**Sprint 5 (Weeks 17-20):**
- Week 17: Testing & Bug Fixes
  - End-to-end testing
  - Load testing
  - Security testing
  - Bug fixes

- Week 18: Performance Optimization
  - Database query optimization
  - API response time improvements
  - Mobile app optimization
  - Caching enhancements

- Week 19: Monitoring & Documentation
  - Complete API documentation (Swagger)
  - User guides
  - Admin documentation
  - Monitoring dashboards
  - Alert configuration

- Week 20: Final Testing & Launch
  - Staging deployment
  - Final QA pass
  - Production deployment
  - Launch preparation
  - Team training

**Deliverable:** Production launch

---

## 4. Sprint Planning

### 4.1 Sprint Structure (2-week sprints)

**Week 1:**
- Monday: Sprint planning (2 hours)
- Daily: Stand-up (15 min)
- Wednesday: Mid-sprint check-in (30 min)
- Friday: Code review session (1 hour)

**Week 2:**
- Monday-Thursday: Development + testing
- Daily: Stand-up (15 min)
- Thursday: Sprint demo (1 hour)
- Friday: Sprint retrospective (1 hour) + Planning for next sprint

### 4.2 Story Point Estimation

| Complexity | Points | Example |
|------------|--------|---------|
| Trivial | 1 | Add new field to API response |
| Simple | 2 | Create new CRUD endpoint |
| Medium | 3 | Implement swap with 1inch |
| Complex | 5 | Integrate Hyperliquid |
| Very Complex | 8 | Build AI chat system |
| Epic | 13 | Complete mobile app |

### 4.3 Velocity Tracking

**Target Velocity:**
- Sprint 1: 20-25 points (team ramping up)
- Sprint 2+: 30-40 points (team at full speed)

**Capacity Calculation:**
- 8 developers × 8 hours/day × 5 days/week = 320 hours/sprint
- Subtract: meetings (10%), code review (15%), bugs (15%) = 60%
- Effective capacity: ~192 hours = ~38 story points

---

## 5. Technical Setup

### 5.1 Development Environment Setup

**Required Software:**
```bash
# Backend Development
- Python 3.11+
- Node.js 18+ (if using Node.js)
- MySQL 8.0
- Redis 7.0
- Docker 24+
- Git

# Mobile Development
- Node.js 18+
- React Native CLI
- Xcode 15+ (macOS only, for iOS)
- Android Studio (for Android)
- Cocoapods (for iOS dependencies)

# DevOps
- AWS CLI
- Terraform
- kubectl (if using Kubernetes)
```

**Local Development Stack:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: dev_password
      MYSQL_DATABASE: anvil_dev
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7.0
    ports:
      - "6379:6379"

  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: mysql://root:dev_password@mysql/anvil_dev
      REDIS_URL: redis://redis:6379
    depends_on:
      - mysql
      - redis
    volumes:
      - ./api:/app

volumes:
  mysql_data:
```

### 5.2 Repository Structure

```
anvil-platform/
├── mobile/                  # React Native mobile app
│   ├── src/
│   ├── ios/
│   ├── android/
│   └── package.json
├── web/                     # React web console
│   ├── src/
│   ├── public/
│   └── package.json
├── api/                     # Backend API
│   ├── app/
│   ├── tests/
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── infrastructure/          # Terraform IaC
│   ├── dev/
│   ├── staging/
│   └── production/
├── docs/                    # Documentation
│   ├── api/
│   ├── user-guides/
│   └── architecture/
└── .github/
    └── workflows/          # CI/CD pipelines
```

### 5.3 Environment Variables

**Backend (.env):**
```bash
# Database
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/anvil
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# External Services
PRIVY_APP_ID=your-privy-app-id
PRIVY_APP_SECRET=your-privy-secret

STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

ONEINCH_API_KEY=your-1inch-key

HYPERLIQUID_API_KEY=your-hyperliquid-key
HYPERLIQUID_API_SECRET=your-hyperliquid-secret

VERTEX_PROJECT_ID=your-gcp-project
VERTEX_LOCATION=us-central1

SENDGRID_API_KEY=your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
FCM_SERVER_KEY=your-fcm-key

ALCHEMY_API_KEY_ARBITRUM=your-alchemy-key
ALCHEMY_API_KEY_BASE=your-alchemy-key

# AWS
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=anvil-documents
AWS_REGION=us-east-1
```

**Mobile (.env):**
```bash
API_BASE_URL=http://localhost:8000/api/v1
PRIVY_APP_ID=your-privy-app-id
STRIPE_PUBLISHABLE_KEY=pk_test_...
ENVIRONMENT=development
```

---

## 6. Development Guidelines

### 6.1 Code Standards

**Python (Backend):**
```python
# Use Black for formatting
# Use isort for import sorting
# Use pylint for linting
# Type hints required

# Example:
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

router = APIRouter()

class SwapRequest(BaseModel):
    """Request schema for token swap"""
    from_asset: str = Field(..., min_length=2, max_length=10)
    from_amount: Decimal = Field(..., gt=0)
    to_asset: str = Field(..., min_length=2, max_length=10)
    chain: str = Field(...)
    slippage: Decimal = Field(default=Decimal("0.5"), ge=0.1, le=5.0)

@router.post("/swap")
async def create_swap(
    request: SwapRequest,
    current_user: User = Depends(get_current_user)
) -> SwapResponse:
    """
    Execute token swap via DEX aggregator
    
    Args:
        request: Swap parameters
        current_user: Authenticated user
        
    Returns:
        SwapResponse with transaction details
    """
    # Implementation
    pass
```

**TypeScript (Mobile/Web):**
```typescript
// Use ESLint + Prettier
// Strict TypeScript mode
// Functional components with hooks

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useQuery } from 'react-query';

interface WalletBalanceProps {
  userId: number;
  chain: 'arbitrum' | 'base' | 'hyperliquid';
}

export const WalletBalance: React.FC<WalletBalanceProps> = ({ 
  userId, 
  chain 
}) => {
  const { data, isLoading, error } = useQuery(
    ['balance', userId, chain],
    () => fetchBalance(userId, chain),
    { refetchInterval: 30000 } // Refresh every 30s
  );

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <View style={styles.container}>
      <Text style={styles.balance}>${data.balanceUsd.toFixed(2)}</Text>
      <Text style={styles.chain}>{chain}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  balance: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  chain: {
    fontSize: 14,
    color: '#666',
  },
});
```

### 6.2 Git Workflow

**Branch Strategy:**
```
main (production)
    ↓
develop (staging)
    ↓
feature/US-C01-user-registration
feature/US-C05-token-swap
bugfix/fix-balance-calculation
hotfix/critical-security-patch
```

**Commit Messages:**
```
feat: Add token swap functionality (US-C05)
fix: Correct balance calculation for multi-chain wallets
refactor: Optimize database queries for transaction history
docs: Update API documentation for perpetuals endpoints
test: Add integration tests for earn positions
chore: Update dependencies to latest versions
```

**Pull Request Template:**
```markdown
## Description
Brief description of changes

## User Story
US-C05: Token Swap

## Changes
- Added swap quote endpoint
- Integrated 1inch API
- Added transaction history

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots
[If UI changes]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings/errors
```

### 6.3 Code Review Process

**Requirements:**
- All code must be reviewed by at least 1 other developer
- Tech Lead approval required for:
  - Database schema changes
  - Security-related changes
  - External API integrations
  - Performance-critical code

**Review Checklist:**
- [ ] Code follows project standards
- [ ] No security vulnerabilities
- [ ] Tests included and passing
- [ ] Documentation updated
- [ ] No unnecessary complexity
- [ ] Error handling implemented
- [ ] Logging added where appropriate

---

## 7. Testing Strategy

### 7.1 Testing Pyramid

```
       ┌─────────────┐
       │   E2E (5%)  │  ← Slow, expensive
       ├─────────────┤
       │ Integration │
       │    (15%)    │  ← Medium speed/cost
       ├─────────────┤
       │    Unit     │
       │    (80%)    │  ← Fast, cheap
       └─────────────┘
```

### 7.2 Unit Testing

**Backend (pytest):**
```python
# tests/test_wallet_service.py
import pytest
from decimal import Decimal
from app.services.wallet_service import WalletService

@pytest.fixture
def wallet_service():
    return WalletService()

@pytest.fixture
def mock_user(db_session):
    user = User(email="test@example.com", role=2, status=1)
    db_session.add(user)
    db_session.commit()
    return user

def test_get_wallet_balance(wallet_service, mock_user):
    """Test wallet balance calculation across chains"""
    balance = wallet_service.get_total_balance(mock_user.id)
    
    assert balance.total_usd >= 0
    assert 'arbitrum' in balance.by_chain
    assert 'base' in balance.by_chain
    assert balance.total_usd == sum(
        chain.balance_usd for chain in balance.by_chain.values()
    )

def test_insufficient_balance_error(wallet_service, mock_user):
    """Test error handling for insufficient balance"""
    with pytest.raises(InsufficientBalanceError):
        wallet_service.execute_swap(
            user_id=mock_user.id,
            from_asset="USDC",
            amount=Decimal("1000000"),  # Impossibly high
            to_asset="ETH"
        )
```

**Mobile (Jest + React Native Testing Library):**
```typescript
// __tests__/WalletBalance.test.tsx
import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from 'react-query';
import { WalletBalance } from '../src/components/WalletBalance';
import * as api from '../src/services/api';

jest.mock('../src/services/api');

describe('WalletBalance', () => {
  const queryClient = new QueryClient();

  it('displays loading state initially', () => {
    const { getByTestId } = render(
      <QueryClientProvider client={queryClient}>
        <WalletBalance userId={1} chain="arbitrum" />
      </QueryClientProvider>
    );

    expect(getByTestId('loading-spinner')).toBeTruthy();
  });

  it('displays balance after loading', async () => {
    (api.fetchBalance as jest.Mock).mockResolvedValue({
      balanceUsd: 123.45,
      chain: 'arbitrum'
    });

    const { getByText } = render(
      <QueryClientProvider client={queryClient}>
        <WalletBalance userId={1} chain="arbitrum" />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(getByText('$123.45')).toBeTruthy();
      expect(getByText('arbitrum')).toBeTruthy();
    });
  });
});
```

### 7.3 Integration Testing

**API Integration Tests:**
```python
# tests/integration/test_swap_flow.py
import pytest
from decimal import Decimal
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_swap_flow(client: AsyncClient, auth_headers):
    """Test complete swap from quote to execution"""
    
    # 1. Get quote
    quote_response = await client.post(
        "/api/v1/user/trade/quote",
        json={
            "from_asset": "USDC",
            "from_amount": "50",
            "to_asset": "ETH",
            "chain": "arbitrum",
            "slippage": 0.5
        },
        headers=auth_headers
    )
    assert quote_response.status_code == 200
    quote = quote_response.json()["data"]
    assert "quote_id" in quote
    
    # 2. Execute swap
    swap_response = await client.post(
        "/api/v1/user/trade/swap",
        json={
            "quote_id": quote["quote_id"],
            "from_asset": "USDC",
            "from_amount": "50",
            "to_asset": "ETH",
            "to_amount_min": quote["to_amount_min"],
            "chain": "arbitrum"
        },
        headers=auth_headers
    )
    assert swap_response.status_code == 200
    swap = swap_response.json()["data"]
    assert swap["status"] == "pending"
    assert "tx_hash" in swap
    
    # 3. Verify transaction created
    tx_response = await client.get(
        f"/api/v1/user/transactions/{swap['id']}",
        headers=auth_headers
    )
    assert tx_response.status_code == 200
    transaction = tx_response.json()["data"]
    assert transaction["type"] == 0  # SWAP
    assert Decimal(transaction["amount_in"]) == Decimal("50")
```

### 7.4 E2E Testing

**Mobile E2E (Detox):**
```typescript
// e2e/swap.test.ts
describe('Token Swap Flow', () => {
  beforeAll(async () => {
    await device.launchApp();
    await loginTestUser();
  });

  it('should complete a token swap', async () => {
    // Navigate to swap screen
    await element(by.id('trading-tab')).tap();
    await element(by.id('swap-button')).tap();

    // Enter swap details
    await element(by.id('from-asset-input')).typeText('USDC');
    await element(by.id('from-amount-input')).typeText('50');
    await element(by.id('to-asset-input')).typeText('ETH');

    // Get quote
    await element(by.id('get-quote-button')).tap();
    await waitFor(element(by.id('quote-result')))
      .toBeVisible()
      .withTimeout(5000);

    // Execute swap
    await element(by.id('execute-swap-button')).tap();
    await element(by.id('confirm-swap-button')).tap();

    // Verify success
    await waitFor(element(by.text('Swap Confirmed')))
      .toBeVisible()
      .withTimeout(10000);
  });
});
```

### 7.5 Load Testing

**API Load Tests (Locust):**
```python
# locustfile.py
from locust import HttpUser, task, between

class AnvilUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/v1/user/auth/privy", json={
            "privy_token": "test_token",
            "privy_did": "did:privy:test"
        })
        self.token = response.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(10)
    def get_wallet_balance(self):
        self.client.get(
            "/api/v1/user/wallet/balances",
            headers=self.headers
        )
    
    @task(5)
    def get_transactions(self):
        self.client.get(
            "/api/v1/user/transactions",
            headers=self.headers,
            params={"page": 1, "limit": 20}
        )
    
    @task(3)
    def get_swap_quote(self):
        self.client.post(
            "/api/v1/user/trade/quote",
            headers=self.headers,
            json={
                "from_asset": "USDC",
                "from_amount": "50",
                "to_asset": "ETH",
                "chain": "arbitrum",
                "slippage": 0.5
            }
        )
```

**Load Test Targets:**
- Concurrent users: 1,000
- Requests per second: 500
- Response time (p95): <500ms
- Error rate: <1%

---

## 8. Deployment Process

### 8.1 CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
# .github/workflows/api-deploy.yml
name: API Deploy

on:
  push:
    branches: [develop, main]
    paths: ['api/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd api
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          cd api
          pytest tests/ --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push Docker image
        run: |
          cd api
          docker build -t anvil-api:${{ github.sha }} .
          aws ecr get-login-password | docker login --username AWS --password-stdin ${{ secrets.ECR_REGISTRY }}
          docker tag anvil-api:${{ github.sha }} ${{ secrets.ECR_REGISTRY }}/anvil-api:staging
          docker push ${{ secrets.ECR_REGISTRY }}/anvil-api:staging
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster anvil-staging \
            --service api \
            --force-new-deployment

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3
      
      # Similar to staging but with production environment
      - name: Deploy to production
        run: |
          # Production deployment steps
          echo "Deploying to production"
```

### 8.2 Deployment Checklist

**Pre-Deployment:**
- [ ] All tests passing
- [ ] Code review approved
- [ ] Database migrations ready
- [ ] Environment variables configured
- [ ] External services tested
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated

**Deployment:**
- [ ] Announce maintenance window (if needed)
- [ ] Take database backup
- [ ] Run database migrations
- [ ] Deploy new code
- [ ] Run smoke tests
- [ ] Monitor logs for errors
- [ ] Verify all endpoints working

**Post-Deployment:**
- [ ] Verify key user flows
- [ ] Check monitoring dashboards
- [ ] Review error logs
- [ ] Announce deployment complete
- [ ] Update changelog

### 8.3 Rollback Procedure

**If critical issues detected:**
1. Stop deployment immediately
2. Rollback to previous version (ECS: previous task definition)
3. Rollback database (if migrations ran)
4. Verify system stability
5. Investigate root cause
6. Fix issues
7. Re-deploy

**Rollback Command:**
```bash
# AWS ECS rollback
aws ecs update-service \
  --cluster anvil-production \
  --service api \
  --task-definition anvil-api:previous-version
```

---

## 9. Documentation Requirements

### 9.1 API Documentation

**Swagger/OpenAPI:**
```python
# FastAPI auto-generates interactive API docs

@app.get("/")
def root():
    """
    Root endpoint
    
    Returns basic API information and health status.
    """
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/v1/user/trade/swap")
async def create_swap(
    request: SwapRequest,
    current_user: User = Depends(get_current_user)
) -> SwapResponse:
    """
    Execute token swap
    
    Executes a token swap using the best available DEX route.
    
    Args:
        request: Swap parameters including assets, amount, and slippage
        current_user: Authenticated user making the request
        
    Returns:
        SwapResponse: Transaction details including tx_hash and status
        
    Raises:
        HTTPException: 400 if insufficient balance
        HTTPException: 400 if invalid quote
        HTTPException: 503 if DEX service unavailable
        
    Example:
        ```python
        {
            "quote_id": "quote_abc123",
            "from_asset": "USDC",
            "from_amount": "50",
            "to_asset": "ETH",
            "to_amount_min": "0.0203",
            "chain": "arbitrum"
        }
        ```
    """
    pass
```

**Access:** `https://api.anvil.com/docs`

### 9.2 User Documentation

**Required User Guides:**
1. Getting Started Guide
2. Wallet Setup Guide
3. Trading Guide (Swaps)
4. Earn Guide (Yield Farming)
5. Perpetuals Trading Guide
6. Save Schedules Guide
7. AI Assistant Guide
8. Subscription Guide

### 9.3 Admin Documentation

**Required Admin Docs:**
1. Admin Console User Guide
2. User Management Guide
3. KYC Approval Process
4. Transaction Monitoring Guide
5. System Settings Guide
6. Incident Response Playbook

### 9.4 Developer Documentation

**Internal Docs:**
1. Architecture Overview
2. Database Schema
3. API Integration Guide
4. Deployment Guide
5. Troubleshooting Guide
6. Code Style Guide

---

## 10. Success Criteria

### 10.1 Technical Metrics

**Performance:**
- [ ] API response time <500ms (p95)
- [ ] Mobile app load time <3s
- [ ] Database query time <100ms (p95)
- [ ] 99.9% uptime SLA

**Quality:**
- [ ] Code coverage >80%
- [ ] Zero critical security vulnerabilities
- [ ] Zero production bugs in first week
- [ ] All user stories completed

**Scale:**
- [ ] Support 10,000 concurrent users
- [ ] Handle 500 requests/second
- [ ] Process 10,000 transactions/day

### 10.2 Business Metrics

**User Engagement:**
- [ ] 100+ active users in first month
- [ ] 40% 30-day retention rate
- [ ] 5+ minutes average session duration

**Platform Activity:**
- [ ] $100,000+ trading volume in first month
- [ ] 1,000+ transactions completed
- [ ] 10+ active earn positions

**Revenue:**
- [ ] 15%+ subscription conversion rate
- [ ] $10+ revenue per user per month

### 10.3 Delivery Criteria

**Phase 1 (MVP):**
- [ ] Mobile app (iOS + Android) in TestFlight/Internal Testing
- [ ] Backend API with 20+ endpoints
- [ ] Database with 27 tables
- [ ] Basic admin portal
- [ ] Swaps and basic earn working

**Phase 2 (Complete):**
- [ ] All 30 user stories implemented
- [ ] All 63 API endpoints complete
- [ ] Full admin + auditor portals
- [ ] All integrations complete (11 services)
- [ ] Beta testing with 50+ users

**Phase 3 (Launch):**
- [ ] Public app store releases (iOS + Android)
- [ ] Complete documentation
- [ ] Monitoring and alerts configured
- [ ] 1,000+ registered users
- [ ] Zero critical bugs

---

## 📋 Final Checklist

### Pre-Development
- [ ] All team members onboarded
- [ ] Development environments set up
- [ ] Repositories created
- [ ] CI/CD pipelines configured
- [ ] Project management tools configured (Jira/Linear)
- [ ] Communication channels set up (Slack)

### During Development
- [ ] Daily stand-ups conducted
- [ ] Sprint planning completed
- [ ] Code reviews performed
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Security best practices followed

### Pre-Launch
- [ ] All features tested
- [ ] Performance testing completed
- [ ] Security audit passed
- [ ] Load testing completed
- [ ] Documentation complete
- [ ] Monitoring configured
- [ ] Backups tested
- [ ] Support processes established

### Post-Launch
- [ ] User feedback collected
- [ ] Bugs prioritized and fixed
- [ ] Performance monitored
- [ ] Continuous improvements planned

---

## 📞 Support & Communication

### Regular Meetings
- **Daily Stand-up:** 15 min, 9:00 AM
- **Sprint Planning:** 2 hours, bi-weekly
- **Sprint Demo:** 1 hour, bi-weekly
- **Sprint Retro:** 1 hour, bi-weekly
- **Tech Sync:** 1 hour, weekly (Tech Lead + Leads)

### Communication Channels
- **Slack:** Real-time chat
- **GitHub:** Code, PRs, issues
- **Jira/Linear:** Project management
- **Confluence:** Documentation
- **Email:** Formal communications

### Escalation Path
1. Developer → Tech Lead
2. Tech Lead → Project Manager
3. Project Manager → Client (Anvil CTO)

---

**Document Status:** Complete ✅  
**Version:** 1.0  
**Last Updated:** November 2025  
**Ready for:** Development Kickoff

**Next Steps:**
1. Review all documents with software factory team
2. Clarify any questions
3. Set up development environments
4. Begin Sprint 1 planning
5. Start development!

Good luck with the implementation! 🚀
