# 📝 Anvil Platform - Code Style & Development Standards

## Coding Standards and Best Practices

**Version:** 1.0  
**Date:** November 2025  
**Status:** Mandatory for all code

---

## 🎯 Philosophy

```
Code is read more often than it is written.
Write code for humans first, computers second.
Consistency is more important than personal preference.
```

---

## 🐍 Python Backend Standards

### Code Formatting

**Use Black formatter (line length: 88)**

```python
# ✅ GOOD
def calculate_apy(
    principal: Decimal,
    rate: Decimal,
    time_years: int
) -> Decimal:
    """Calculate APY with compound interest."""
    return principal * (1 + rate) ** time_years - principal


# ❌ BAD
def calculate_apy(principal: Decimal, rate: Decimal, time_years: int) -> Decimal:
    return principal*(1+rate)**time_years-principal
```

### Imports

**Order: Standard library → Third-party → Local**

```python
# ✅ GOOD
import json
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth_service import AuthService
from app.core.security import get_current_user


# ❌ BAD - Mixed order
from app.models.user import User
import json
from fastapi import HTTPException
from app.services.auth_service import AuthService
from datetime import datetime
```

### Naming Conventions

```python
# Classes: PascalCase
class UserService:
    pass

class EarnPosition:
    pass


# Functions and variables: snake_case
def get_user_balance(user_id: int) -> Decimal:
    pass

user_wallet = get_user_wallet()


# Constants: UPPER_SNAKE_CASE
MAX_TRANSACTION_AMOUNT = Decimal("1000000")
DEFAULT_SLIPPAGE = 0.5


# Private methods: leading underscore
class MyClass:
    def _internal_method(self):
        pass
    
    def __very_private_method(self):
        pass


# Type hints: Always use them
def process_transaction(
    user_id: int,
    amount: Decimal,
    asset: str
) -> Transaction:
    pass
```

### Docstrings (Google Style)

```python
def execute_swap(
    user_id: int,
    from_asset: str,
    to_asset: str,
    amount: Decimal,
    slippage: float = 0.5
) -> Transaction:
    """Execute token swap via 1inch aggregator.
    
    This function creates a swap transaction, gets the best rate from
    1inch, signs the transaction via Privy, and submits it to the blockchain.
    
    Args:
        user_id: The ID of the user executing the swap.
        from_asset: Token symbol to swap from (e.g., "USDC").
        to_asset: Token symbol to swap to (e.g., "ETH").
        amount: Amount of from_asset to swap.
        slippage: Maximum acceptable slippage as percentage (default: 0.5%).
    
    Returns:
        Transaction object with status and tx_hash.
    
    Raises:
        ValueError: If amount is below minimum or assets are invalid.
        HTTPException: If external API calls fail.
    
    Example:
        >>> tx = execute_swap(
        ...     user_id=123,
        ...     from_asset="USDC",
        ...     to_asset="ETH",
        ...     amount=Decimal("50")
        ... )
        >>> print(tx.status)
        TransactionStatus.PENDING
    """
    # Implementation
    pass
```

### Error Handling

```python
# ✅ GOOD - Specific exceptions, proper logging
from fastapi import HTTPException
import structlog

logger = structlog.get_logger()

def get_user(user_id: int) -> User:
    """Get user by ID."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning("user_not_found", user_id=user_id)
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not found"
            )
        return user
    except SQLAlchemyError as e:
        logger.error("database_error", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=500,
            detail="Database error occurred"
        )


# ❌ BAD - Generic exceptions, no logging
def get_user(user_id: int):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception("Not found")
        return user
    except:
        raise Exception("Error")
```

### Async/Await

```python
# ✅ GOOD - Proper async usage
async def get_token_price(token: str, chain: str) -> Decimal:
    """Fetch current token price."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.example.com/price/{token}",
            params={"chain": chain}
        )
        response.raise_for_status()
        data = response.json()
        return Decimal(data["price"])


# ❌ BAD - Mixing sync and async
async def get_token_price(token: str, chain: str):
    # Don't use requests (sync) in async function
    response = requests.get(f"https://api.example.com/price/{token}")
    return response.json()["price"]
```

### SQL Queries (SQLAlchemy)

```python
from sqlalchemy import select, func
from sqlalchemy.orm import Session

# ✅ GOOD - Use ORM, avoid raw SQL
def get_active_users(db: Session, limit: int = 100) -> List[User]:
    """Get active users with recent activity."""
    return (
        db.query(User)
        .filter(User.status == UserStatus.ACTIVE)
        .filter(User.last_login_at > datetime.utcnow() - timedelta(days=30))
        .order_by(User.last_login_at.desc())
        .limit(limit)
        .all()
    )


# ✅ GOOD - When you need raw SQL, use parameters
def get_user_stats(db: Session, user_id: int) -> dict:
    """Get user statistics."""
    result = db.execute(
        """
        SELECT 
            COUNT(DISTINCT t.id) as tx_count,
            SUM(t.amount_in_usd) as total_volume
        FROM transactions t
        WHERE t.user_id = :user_id
          AND t.status = 'success'
        """,
        {"user_id": user_id}
    ).fetchone()
    
    return {
        "transaction_count": result.tx_count,
        "total_volume": result.total_volume
    }


# ❌ BAD - SQL injection vulnerability
def get_user_by_email(db: Session, email: str):
    query = f"SELECT * FROM users WHERE email = '{email}'"
    return db.execute(query).fetchone()
```

### Testing Standards

```python
# ✅ GOOD - Descriptive test names, AAA pattern
def test_swap_execution_creates_pending_transaction():
    """Test that executing a swap creates a transaction with PENDING status."""
    # Arrange
    user = create_test_user()
    from_asset = "USDC"
    to_asset = "ETH"
    amount = Decimal("50")
    
    # Act
    transaction = execute_swap(
        user_id=user.id,
        from_asset=from_asset,
        to_asset=to_asset,
        amount=amount
    )
    
    # Assert
    assert transaction.status == TransactionStatus.PENDING
    assert transaction.from_asset == from_asset
    assert transaction.to_asset == to_asset
    assert transaction.amount == amount


# ❌ BAD - Unclear test name, no structure
def test_swap():
    user = create_test_user()
    tx = execute_swap(user.id, "USDC", "ETH", 50)
    assert tx
```

---

## 📱 TypeScript/React Native Standards

### Code Formatting

**Use Prettier (no semicolons, single quotes)**

```typescript
// ✅ GOOD
const calculateApy = (
  principal: number,
  rate: number,
  timeYears: number
): number => {
  return principal * Math.pow(1 + rate, timeYears) - principal
}


// ❌ BAD
const calculateApy = (principal: number, rate: number, timeYears: number): number => {
    return principal*Math.pow(1+rate,timeYears)-principal;
};
```

### Naming Conventions

```typescript
// Components: PascalCase
const SwapScreen: React.FC = () => {
  return <View />
}

const TokenSelector: React.FC<Props> = ({ tokens, onSelect }) => {
  return <FlatList />
}


// Functions and variables: camelCase
const getUserBalance = async (userId: number): Promise<Balance> => {
  // Implementation
}

const userWallet = await getUserWallet()


// Constants: UPPER_SNAKE_CASE
const MAX_SLIPPAGE = 5.0
const DEFAULT_CHAIN = 'arbitrum'


// Types/Interfaces: PascalCase
interface UserProfile {
  id: number
  email: string
  firstName: string
}

type TransactionStatus = 'pending' | 'success' | 'failed'


// Hooks: use prefix
const useUserBalance = (userId: number) => {
  const [balance, setBalance] = useState<Balance | null>(null)
  // Implementation
  return balance
}
```

### Component Structure

```typescript
// ✅ GOOD - Organized component structure
import React, { useState, useEffect } from 'react'
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native'
import { useNavigation } from '@react-navigation/native'

// Types
interface SwapScreenProps {
  userId: number
}

// Component
export const SwapScreen: React.FC<SwapScreenProps> = ({ userId }) => {
  // Hooks
  const navigation = useNavigation()
  
  // State
  const [fromAsset, setFromAsset] = useState<string>('USDC')
  const [toAsset, setToAsset] = useState<string>('ETH')
  const [amount, setAmount] = useState<string>('')
  
  // Effects
  useEffect(() => {
    loadUserBalance()
  }, [userId])
  
  // Handlers
  const handleSwap = async () => {
    try {
      await executeSwap(fromAsset, toAsset, amount)
      navigation.navigate('TransactionSuccess')
    } catch (error) {
      console.error('Swap failed:', error)
    }
  }
  
  // Helper functions
  const loadUserBalance = async () => {
    // Implementation
  }
  
  // Render
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Swap Tokens</Text>
      <TouchableOpacity onPress={handleSwap}>
        <Text>Execute Swap</Text>
      </TouchableOpacity>
    </View>
  )
}

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
})
```

### State Management (Zustand)

```typescript
// ✅ GOOD - Clean store structure
import { create } from 'zustand'

interface UserStore {
  user: User | null
  balance: Balance | null
  setUser: (user: User) => void
  setBalance: (balance: Balance) => void
  logout: () => void
}

export const useUserStore = create<UserStore>((set) => ({
  user: null,
  balance: null,
  
  setUser: (user) => set({ user }),
  
  setBalance: (balance) => set({ balance }),
  
  logout: () => set({ user: null, balance: null }),
}))
```

### API Calls

```typescript
// ✅ GOOD - Typed API client
import axios, { AxiosInstance } from 'axios'

class ApiClient {
  private client: AxiosInstance
  
  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    this.setupInterceptors()
  }
  
  private setupInterceptors() {
    this.client.interceptors.request.use((config) => {
      const token = getStoredToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })
    
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          logout()
        }
        return Promise.reject(error)
      }
    )
  }
  
  async getSwapQuote(params: SwapQuoteParams): Promise<SwapQuote> {
    const response = await this.client.post<ApiResponse<SwapQuote>>(
      '/user/trade/quote',
      params
    )
    return response.data.data
  }
}

export const api = new ApiClient(Config.API_URL)
```

---

## 🎨 UI/UX Standards

### Design Tokens

```typescript
// colors.ts
export const colors = {
  primary: '#3B82F6',
  secondary: '#8B5CF6',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  
  background: '#FFFFFF',
  surface: '#F9FAFB',
  
  text: {
    primary: '#111827',
    secondary: '#6B7280',
    disabled: '#9CA3AF',
  },
}

// spacing.ts
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
}

// typography.ts
export const typography = {
  h1: {
    fontSize: 32,
    fontWeight: '700',
    lineHeight: 40,
  },
  h2: {
    fontSize: 24,
    fontWeight: '700',
    lineHeight: 32,
  },
  body: {
    fontSize: 16,
    fontWeight: '400',
    lineHeight: 24,
  },
  caption: {
    fontSize: 12,
    fontWeight: '400',
    lineHeight: 16,
  },
}
```

### Accessibility

```typescript
// ✅ GOOD - Accessible components
<TouchableOpacity
  accessible={true}
  accessibilityLabel="Execute swap"
  accessibilityRole="button"
  accessibilityState={{ disabled: !isValid }}
  onPress={handleSwap}
>
  <Text>Swap</Text>
</TouchableOpacity>

<TextInput
  accessible={true}
  accessibilityLabel="Amount to swap"
  accessibilityHint="Enter the amount you want to swap"
  placeholder="0.00"
  value={amount}
  onChangeText={setAmount}
/>
```

---

## 📏 Git Commit Standards

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

```
feat:     New feature
fix:      Bug fix
docs:     Documentation only
style:    Code style (formatting, semicolons, etc.)
refactor: Code refactoring
test:     Adding tests
chore:    Build process or auxiliary tool changes
perf:     Performance improvement
ci:       CI configuration changes
```

### Examples

```bash
# ✅ GOOD
feat(swap): add slippage tolerance selector

Allow users to customize slippage tolerance when executing swaps.
Default remains at 0.5% but users can adjust between 0.1% and 5%.

Closes #123

# ✅ GOOD
fix(auth): prevent token refresh loop

Fixed infinite loop when refresh token expires by adding proper
error handling and redirecting to login screen.

Fixes #456

# ✅ GOOD
refactor(api): extract common API client logic

Moved common axios configuration, interceptors, and error handling
into a base ApiClient class to reduce code duplication.

# ❌ BAD
fixed stuff

# ❌ BAD
Updated files
```

---

## 🔍 Code Review Standards

### Before Submitting PR

```yaml
Checklist:
  - [ ] Code follows style guide
  - [ ] All tests pass locally
  - [ ] New tests added for new features
  - [ ] Documentation updated
  - [ ] No console.log or debug code
  - [ ] Environment variables used (no hardcoded secrets)
  - [ ] Error handling implemented
  - [ ] Type hints/types added
  - [ ] Comments added for complex logic
  - [ ] Self-reviewed the changes
```

### PR Description Template

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce them.

## Screenshots (if applicable)
Add screenshots for UI changes.

## Checklist
- [ ] My code follows the style guide
- [ ] I have performed a self-review
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Related Issues
Closes #(issue number)
```

### Review Guidelines

**For Reviewers:**

```yaml
Focus on:
  - Logic errors and bugs
  - Security vulnerabilities
  - Performance issues
  - Code readability
  - Test coverage
  - Documentation

Nice to have:
  - Style suggestions (if not caught by linter)
  - Alternative approaches
  - Learning opportunities

Avoid:
  - Nitpicking on style (use linters)
  - Personal preference debates
  - Scope creep
```

---

## 📊 Performance Standards

### API Response Times

```yaml
Target Latency:
  - P50: < 200ms
  - P95: < 500ms
  - P99: < 1000ms

Query Optimization:
  - N+1 queries: Avoid with eager loading
  - Large datasets: Use pagination
  - Heavy computations: Move to background workers
```

### Mobile Performance

```yaml
Target Metrics:
  - Time to Interactive: < 3 seconds
  - Frame rate: 60 FPS
  - Bundle size: < 50MB
  - Memory usage: < 200MB

Optimization:
  - Image optimization: WebP format, lazy loading
  - Code splitting: Dynamic imports
  - Memoization: Use React.memo, useMemo
  - Avoid re-renders: Proper state management
```

---

## 🔒 Security Standards

### Never Commit

```yaml
❌ DO NOT COMMIT:
  - API keys or secrets
  - Private keys or mnemonics
  - Passwords
  - Personal information
  - .env files
  - credentials.json files
```

### Input Validation

```python
# ✅ GOOD - Validate all inputs
from pydantic import BaseModel, validator, Field

class SwapRequest(BaseModel):
    from_asset: str = Field(..., regex="^[A-Z]{3,10}$")
    to_asset: str = Field(..., regex="^[A-Z]{3,10}$")
    amount: Decimal = Field(..., gt=0, le=1000000)
    
    @validator("from_asset", "to_asset")
    def validate_asset(cls, v):
        allowed = ["USDC", "ETH", "USDT", "DAI"]
        if v not in allowed:
            raise ValueError(f"Asset must be one of {allowed}")
        return v
```

---

## ✅ Daily Development Checklist

### Morning
- [ ] Pull latest changes from main
- [ ] Check for any blocking issues
- [ ] Review assigned tasks
- [ ] Update task status

### During Development
- [ ] Write tests alongside code
- [ ] Run tests frequently
- [ ] Commit often with clear messages
- [ ] Keep PRs small and focused

### Before Committing
- [ ] Run linter: `black . && flake8`
- [ ] Run tests: `pytest`
- [ ] Remove debug code
- [ ] Review your own changes

### End of Day
- [ ] Push all commits
- [ ] Update task status
- [ ] Document any blockers
- [ ] Plan tomorrow's work

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** Tech Lead  
**Questions:** tech-lead@anvil.com
