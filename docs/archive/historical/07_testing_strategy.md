# 🧪 Anvil Platform - Testing Strategy

## Comprehensive Testing Plan

**Version:** 1.0  
**Date:** November 2025  
**Test Coverage Target:** >80%

---

## 📊 Testing Overview

### Test Pyramid

```
                    ▲
                   ╱ ╲
                  ╱   ╲
                 ╱ E2E ╲           5% - End-to-End Tests
                ╱───────╲          (Critical user flows)
               ╱         ╲
              ╱Integration╲        15% - Integration Tests
             ╱─────────────╲       (API endpoints, external services)
            ╱               ╲
           ╱      Unit       ╲     80% - Unit Tests
          ╱───────────────────╲    (Business logic, utilities)
         ╱─────────────────────╲
```

---

## 🔬 Unit Testing

### Backend Unit Tests (Pytest)

**test_services/test_auth_service.py:**
```python
import pytest
from datetime import datetime, timedelta
from app.services.auth_service import AuthService
from app.models.user import User, UserRole, UserStatus

class TestAuthService:
    """Test authentication service"""
    
    @pytest.fixture
    def auth_service(self, db_session):
        """Create auth service instance"""
        return AuthService(db_session)
    
    @pytest.fixture
    def test_user(self, db_session):
        """Create test user"""
        user = User(
            uid="usr_test123",
            email="test@example.com",
            role=UserRole.CLIENT,
            status=UserStatus.ACTIVE,
            privy_user_id="did:privy:test123"
        )
        db_session.add(user)
        db_session.commit()
        return user
    
    def test_create_access_token(self, auth_service):
        """Test JWT access token creation"""
        data = {"sub": "123", "user_id": 123}
        token = auth_service.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_token_valid(self, auth_service):
        """Test valid token verification"""
        data = {"sub": "123", "user_id": 123}
        token = auth_service.create_access_token(data)
        
        payload = auth_service.verify_token(token)
        assert payload["user_id"] == 123
    
    def test_verify_token_expired(self, auth_service):
        """Test expired token verification"""
        from jose import jwt
        from app.config import settings
        
        # Create expired token
        expired_data = {
            "sub": "123",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(
            expired_data,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        with pytest.raises(Exception):
            auth_service.verify_token(expired_token)
    
    def test_password_hashing(self, auth_service):
        """Test password hashing and verification"""
        password = "SecurePassword123!"
        hashed = auth_service.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50
        assert auth_service.verify_password(password, hashed)
        assert not auth_service.verify_password("WrongPassword", hashed)
```

**test_services/test_trading_service.py:**
```python
import pytest
from decimal import Decimal
from app.services.trading_service import TradingService

class TestTradingService:
    """Test trading service"""
    
    @pytest.fixture
    def trading_service(self, db_session):
        return TradingService(db_session)
    
    @pytest.mark.asyncio
    async def test_get_swap_quote(self, trading_service):
        """Test getting swap quote from 1inch"""
        quote = await trading_service.get_swap_quote(
            from_asset="USDC",
            to_asset="ETH",
            amount=Decimal("50"),
            chain="arbitrum"
        )
        
        assert quote is not None
        assert "to_amount" in quote
        assert "rate" in quote
        assert "gas_estimate" in quote
    
    @pytest.mark.asyncio
    async def test_validate_swap_amount_min(self, trading_service):
        """Test minimum swap amount validation"""
        with pytest.raises(ValueError, match="Minimum amount"):
            await trading_service.validate_swap_amount(
                amount=Decimal("0.001"),
                asset="USDC"
            )
    
    @pytest.mark.asyncio
    async def test_validate_swap_amount_max(self, trading_service):
        """Test maximum swap amount validation"""
        with pytest.raises(ValueError, match="Maximum amount"):
            await trading_service.validate_swap_amount(
                amount=Decimal("1000000"),
                asset="USDC"
            )
```

**test_utils/test_validators.py:**
```python
import pytest
from app.utils.validators import (
    validate_ethereum_address,
    validate_email,
    validate_phone,
    validate_amount
)

class TestValidators:
    """Test validation utilities"""
    
    def test_validate_ethereum_address_valid(self):
        """Test valid Ethereum address"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        assert validate_ethereum_address(address) is True
    
    def test_validate_ethereum_address_invalid(self):
        """Test invalid Ethereum address"""
        assert validate_ethereum_address("0xinvalid") is False
        assert validate_ethereum_address("not_an_address") is False
    
    def test_validate_email_valid(self):
        """Test valid email"""
        assert validate_email("user@example.com") is True
        assert validate_email("test.user+tag@domain.co.uk") is True
    
    def test_validate_email_invalid(self):
        """Test invalid email"""
        assert validate_email("notanemail") is False
        assert validate_email("@example.com") is False
    
    def test_validate_phone_valid(self):
        """Test valid phone (E.164 format)"""
        assert validate_phone("+12125551234") is True
        assert validate_phone("+442071234567") is True
    
    def test_validate_phone_invalid(self):
        """Test invalid phone"""
        assert validate_phone("1234567890") is False
        assert validate_phone("+1") is False
    
    def test_validate_amount(self):
        """Test amount validation"""
        from decimal import Decimal
        
        assert validate_amount(Decimal("50"), Decimal("1"), Decimal("1000"))
        assert not validate_amount(Decimal("0.5"), Decimal("1"), Decimal("1000"))
        assert not validate_amount(Decimal("1001"), Decimal("1"), Decimal("1000"))
```

### Running Unit Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_services/test_auth_service.py

# Run specific test
pytest tests/test_services/test_auth_service.py::TestAuthService::test_create_access_token

# Run tests in parallel
pytest tests/ -n auto

# Run with verbose output
pytest tests/ -v

# Run only failed tests
pytest tests/ --lf
```

---

## 🔗 Integration Testing

### API Integration Tests

**test_api/test_auth_endpoints.py:**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    async def test_privy_login_success(self, client: AsyncClient):
        """Test successful Privy login"""
        response = await client.post(
            "/api/v1/user/auth/privy",
            json={"privy_token": "valid_test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    async def test_privy_login_invalid_token(self, client: AsyncClient):
        """Test login with invalid token"""
        response = await client.post(
            "/api/v1/user/auth/privy",
            json={"privy_token": "invalid_token"}
        )
        
        assert response.status_code == 401
    
    async def test_refresh_token(self, client: AsyncClient, test_user_tokens):
        """Test token refresh"""
        response = await client.post(
            "/api/v1/user/auth/refresh",
            json={"refresh_token": test_user_tokens["refresh_token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    async def test_logout(self, client: AsyncClient, auth_headers):
        """Test logout"""
        response = await client.post(
            "/api/v1/user/auth/logout",
            headers=auth_headers
        )
        
        assert response.status_code == 200
```

**test_api/test_trading_endpoints.py:**
```python
@pytest.mark.asyncio
class TestTradingEndpoints:
    """Test trading endpoints"""
    
    async def test_get_quote(self, client: AsyncClient, auth_headers):
        """Test getting swap quote"""
        response = await client.post(
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
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "quote_id" in data
        assert "to_amount" in data
        assert "rate" in data
    
    async def test_execute_swap(self, client: AsyncClient, auth_headers):
        """Test executing swap"""
        # First get quote
        quote_response = await client.post(
            "/api/v1/user/trade/quote",
            json={
                "from_asset": "USDC",
                "from_amount": "50",
                "to_asset": "ETH",
                "chain": "arbitrum"
            },
            headers=auth_headers
        )
        quote_id = quote_response.json()["data"]["quote_id"]
        
        # Execute swap
        response = await client.post(
            "/api/v1/user/trade/swap",
            json={
                "quote_id": quote_id,
                "from_asset": "USDC",
                "from_amount": "50",
                "to_asset": "ETH",
                "chain": "arbitrum"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "transaction_id" in data
        assert data["status"] == "pending"
```

### External Service Integration Tests

**test_integrations/test_privy.py:**
```python
@pytest.mark.asyncio
@pytest.mark.integration
class TestPrivyIntegration:
    """Test Privy service integration"""
    
    async def test_verify_valid_token(self, privy_client):
        """Test verifying valid Privy token"""
        # Requires actual Privy test token
        result = await privy_client.verify_token("test_token")
        assert result is not None
        assert "id" in result
        assert "email" in result
    
    async def test_create_wallet(self, privy_client):
        """Test creating embedded wallet"""
        result = await privy_client.create_wallet("test_user_123")
        assert "wallet_id" in result
        assert "address" in result
```

**test_integrations/test_stripe.py:**
```python
@pytest.mark.asyncio
@pytest.mark.integration
class TestStripeIntegration:
    """Test Stripe service integration"""
    
    async def test_create_payment_intent(self, stripe_client):
        """Test creating payment intent"""
        result = await stripe_client.create_payment_intent(
            amount=100.0,
            currency="usd"
        )
        assert "client_secret" in result
        assert "payment_intent_id" in result
```

---

## 🎭 End-to-End Testing

### Mobile App E2E Tests (Detox)

**e2e/user_journey.test.ts:**
```typescript
describe('User Journey', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it('should complete onboarding flow', async () => {
    // Login screen
    await expect(element(by.id('login-screen'))).toBeVisible();
    await element(by.id('login-button')).tap();
    
    // Wait for Privy auth
    await waitFor(element(by.id('home-screen')))
      .toBeVisible()
      .withTimeout(5000);
  });

  it('should execute token swap', async () => {
    // Navigate to swap
    await element(by.id('tab-swap')).tap();
    
    // Select tokens
    await element(by.id('from-token-selector')).tap();
    await element(by.text('USDC')).tap();
    
    await element(by.id('to-token-selector')).tap();
    await element(by.text('ETH')).tap();
    
    // Enter amount
    await element(by.id('amount-input')).typeText('50');
    
    // Get quote
    await element(by.id('get-quote-button')).tap();
    await waitFor(element(by.id('swap-details')))
      .toBeVisible()
      .withTimeout(3000);
    
    // Confirm swap
    await element(by.id('confirm-swap-button')).tap();
    
    // Verify success
    await waitFor(element(by.text('Swap Pending')))
      .toBeVisible()
      .withTimeout(2000);
  });

  it('should view transaction history', async () => {
    // Navigate to history
    await element(by.id('tab-history')).tap();
    
    // Verify transactions list
    await expect(element(by.id('transactions-list'))).toBeVisible();
    
    // Tap first transaction
    await element(by.id('transaction-item-0')).tap();
    
    // Verify details
    await expect(element(by.id('transaction-details'))).toBeVisible();
  });
});
```

### Admin Console E2E Tests (Playwright)

**e2e/admin/user_management.spec.ts:**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Admin User Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('https://admin.anvil.com/login');
    await page.fill('[name=email]', 'admin@anvil.com');
    await page.fill('[name=password]', 'admin_password');
    await page.click('button[type=submit]');
    
    await page.waitForURL('**/dashboard');
  });

  test('should list all users', async ({ page }) => {
    await page.goto('https://admin.anvil.com/users');
    
    // Verify users table
    await expect(page.locator('table')).toBeVisible();
    await expect(page.locator('tbody tr')).toHaveCount.greaterThan(0);
  });

  test('should approve KYC', async ({ page }) => {
    await page.goto('https://admin.anvil.com/users/kyc-pending');
    
    // Click first pending user
    await page.click('tbody tr:first-child');
    
    // View documents
    await expect(page.locator('[data-testid=kyc-documents]')).toBeVisible();
    
    // Approve
    await page.click('[data-testid=approve-button]');
    await page.fill('[name=notes]', 'All documents verified');
    await page.click('[data-testid=confirm-approve]');
    
    // Verify success message
    await expect(page.locator('.success-message')).toBeVisible();
  });
});
```

---

## 🔐 Security Testing

### Penetration Testing Checklist

```yaml
Authentication:
  - [ ] SQL injection in login form
  - [ ] Brute force protection
  - [ ] Password strength enforcement
  - [ ] Session hijacking attempts
  - [ ] JWT token manipulation
  - [ ] 2FA bypass attempts

Authorization:
  - [ ] Privilege escalation (CLIENT → ADMIN)
  - [ ] Access to other user's data
  - [ ] API endpoint authorization
  - [ ] IDOR vulnerabilities

Input Validation:
  - [ ] XSS in all input fields
  - [ ] CSRF attacks
  - [ ] File upload vulnerabilities
  - [ ] Command injection
  - [ ] Path traversal

API Security:
  - [ ] Rate limiting effectiveness
  - [ ] API key exposure
  - [ ] Excessive data exposure
  - [ ] Mass assignment
  - [ ] GraphQL injection (if used)

Business Logic:
  - [ ] Transaction replay attacks
  - [ ] Race conditions
  - [ ] Price manipulation
  - [ ] Fund withdrawal bypasses
```

### Automated Security Scanning

```bash
# OWASP Dependency Check
pip install safety
safety check --json

# Bandit (Python security linter)
bandit -r app/ -f json -o bandit-report.json

# Trivy (Container scanning)
trivy image anvil-api:latest
```

---

## ⚡ Performance Testing

### Load Testing (Locust)

**locustfile.py:**
```python
from locust import HttpUser, task, between
import random

class AnvilUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post("/api/v1/user/auth/privy", json={
            "privy_token": "test_token"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def view_wallet(self):
        """View wallet balance"""
        self.client.get(
            "/api/v1/user/wallet",
            headers=self.headers
        )
    
    @task(2)
    def get_transactions(self):
        """Get transaction history"""
        self.client.get(
            "/api/v1/user/transactions",
            headers=self.headers,
            params={"page": 1, "limit": 20}
        )
    
    @task(1)
    def get_swap_quote(self):
        """Get swap quote"""
        self.client.post(
            "/api/v1/user/trade/quote",
            headers=self.headers,
            json={
                "from_asset": "USDC",
                "from_amount": str(random.randint(10, 1000)),
                "to_asset": "ETH",
                "chain": "arbitrum"
            }
        )
```

**Run Load Test:**
```bash
# Local testing
locust -f locustfile.py --host=http://localhost:8000

# Production testing
locust -f locustfile.py \
  --host=https://api.anvil.com \
  --users=1000 \
  --spawn-rate=50 \
  --run-time=10m \
  --html=load-test-report.html
```

### Performance Benchmarks

```yaml
API Performance Targets:
  - P50 response time: < 200ms
  - P95 response time: < 500ms
  - P99 response time: < 1000ms
  - Throughput: > 1000 req/sec
  - Error rate: < 0.1%

Database Performance:
  - Query time P95: < 100ms
  - Connection pool usage: < 80%
  - Slow query rate: < 1%

External API Calls:
  - 1inch API: < 2s
  - Privy API: < 1s
  - Stripe API: < 3s
  - Blockchain RPC: < 2s
```

---

## 📱 Mobile Testing

### Device Matrix

```yaml
iOS Testing:
  - iPhone 15 Pro (iOS 17)
  - iPhone 14 (iOS 17)
  - iPhone 13 (iOS 16)
  - iPhone SE (iOS 16)
  - iPad Pro (iOS 17)

Android Testing:
  - Samsung Galaxy S23 (Android 13)
  - Google Pixel 8 (Android 14)
  - OnePlus 11 (Android 13)
  - Samsung Galaxy A54 (Android 13)
  - Low-end device (Android 11, 2GB RAM)
```

### React Native Testing

**Component Tests:**
```typescript
import { render, fireEvent } from '@testing-library/react-native';
import SwapScreen from '../screens/SwapScreen';

describe('SwapScreen', () => {
  it('should render swap form', () => {
    const { getByTestId } = render(<SwapScreen />);
    
    expect(getByTestId('from-token-selector')).toBeTruthy();
    expect(getByTestId('to-token-selector')).toBeTruthy();
    expect(getByTestId('amount-input')).toBeTruthy();
  });

  it('should validate amount input', () => {
    const { getByTestId, getByText } = render(<SwapScreen />);
    
    const input = getByTestId('amount-input');
    fireEvent.changeText(input, '0.001');
    
    expect(getByText('Minimum amount is 0.01')).toBeTruthy();
  });
});
```

---

## 🔄 Continuous Testing

### CI Pipeline Testing

```yaml
# .github/workflows/test.yml
name: Continuous Testing

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest tests/unit/
  
  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: pytest tests/integration/
  
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Security scan
        run: |
          safety check
          bandit -r app/
  
  performance-test:
    needs: integration-tests
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run load tests
        run: locust -f locustfile.py --headless --users=100
```

---

## 📊 Test Reporting

### Coverage Reports

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=xml

# View coverage in browser
open htmlcov/index.html

# Coverage badges
coverage-badge -o coverage.svg
```

### Test Metrics Dashboard

```yaml
Metrics to Track:
  - Test count (unit/integration/e2e)
  - Code coverage %
  - Test execution time
  - Test failure rate
  - Flaky test count
  - Mean time to detect (MTTD)
  - Mean time to resolve (MTTR)
```

---

## ✅ Testing Checklist

### Before Each Release
- [ ] All unit tests passing (>80% coverage)
- [ ] All integration tests passing
- [ ] E2E tests passing on all platforms
- [ ] Performance tests within targets
- [ ] Security scan completed (no critical issues)
- [ ] Load testing completed (target: 10,000 users)
- [ ] Mobile app tested on all device matrix
- [ ] API documentation tests passing
- [ ] Database migration tests completed
- [ ] Rollback procedure tested

### Test Environment Requirements
- [ ] Staging environment matching production
- [ ] Test data seeded
- [ ] External services mocked/sandboxed
- [ ] Test accounts created
- [ ] Monitoring configured

---

## 🎯 Test Automation Goals

```yaml
Q1 2026:
  - Unit test coverage: 80%
  - Integration test coverage: 60%
  - E2E test coverage: Critical paths
  - CI/CD integration: Complete

Q2 2026:
  - Unit test coverage: 85%
  - Integration test coverage: 75%
  - E2E test coverage: All major features
  - Performance testing: Automated

Q3 2026:
  - Unit test coverage: 90%
  - Integration test coverage: 85%
  - Visual regression testing: Implemented
  - Chaos engineering: Basic scenarios

Q4 2026:
  - Full test automation
  - Self-healing tests
  - Predictive test selection
  - AI-powered test generation
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Test Lead:** qa@anvil.com  
**Next Review:** Monthly
