# FastAPI Error Fix Summary

**Date**: January 28, 2026
**Status**: ⚠️ PARTIAL FIX - Server still not starting

---

## ✅ Errors Fixed

### 1. Missing `crontab` Import ✅ FIXED
**File**: `src/app/infrastructure/celery/app.py`

**Error**:
```python
NameError: name 'crontab' is not defined
```

**Fix Applied** (Line 3):
```python
from celery import Celery
from celery.schedules import crontab  # ADDED
```

---

### 2. `AsyncSession` vs `MainAsyncSession` in Money Market ✅ FIXED

Updated all money market adapters and provider to use `MainAsyncSession` instead of `AsyncSession`.

**Files Fixed**:
1. `src/app/setup/ioc/money_market.py` - Provider
2. `src/app/infrastructure/adapters/money_market/money_market_cache_adapter_sqla.py`
3. `src/app/infrastructure/adapters/money_market/money_market_comparison_adapter_sqla.py`
4. `src/app/infrastructure/adapters/money_market/money_market_preference_adapter_sqla.py`
5. `src/app/infrastructure/adapters/money_market/money_market_alert_adapter_sqla.py`

**Changes Made**:
```python
# OLD
from sqlalchemy.ext.asyncio import AsyncSession

def __init__(self, session: AsyncSession):
    self._session = session

# NEW
from app.infrastructure.adapters.types import MainAsyncSession

def __init__(self, session: MainAsyncSession):
    self._session = session
```

---

## ❌ Remaining Issue: Dishka Dependency Injection Error

**Current Status**: Server STILL NOT STARTING

**Error**:
```
dishka.exceptions.GraphMissingFactoryError: Cannot find factory for (AsyncSession, component=''). It is missing or has invalid scope.
   │                                                 ◈ Scope.REQUEST, component='' ◈
   ▼   app.domain.ports.money_market.money_market_cache_gateway.MoneyMarketCacheGateway   MoneyMarketProvider.provide_cache_gateway
   ╰─> sqlalchemy.ext.asyncio.session.AsyncSession                                        ???
```

---

## 🔍 Root Cause Analysis

### The Problem

Even though all code has been updated to use `MainAsyncSession`, Dishka is still trying to resolve `AsyncSession` at runtime.

### Why This Happens

`MainAsyncSession` is defined as a `NewType`:

```python
# src/app/infrastructure/adapters/types.py
from typing import NewType
from sqlalchemy.ext.asyncio import AsyncSession

MainAsyncSession = NewType("MainAsyncSession", AsyncSession)
```

**`NewType` Behavior**:
- **At type-checking time** (static analysis): Creates a distinct type
- **At runtime**: Just an alias - Python sees it as `AsyncSession`
- **Dishka behavior**: Resolves the actual runtime type (`AsyncSession`), not the NewType

---

## 🛠️ Possible Solutions

### Option 1: Remove Money Market Provider Temporarily ❌ NOT WORKING

Tried disabling `MoneyMarketProvider()` in `provider_registry.py`, but error persists because:
- `MoneyMarketHandler` is used in `ChatPhase2Provider` and `GuestProvider`
- `MoneyMarketWorkflowAgent` is used in `AgentSquadInfrastructureProvider`
- These may have transitive dependencies on money market gateways

### Option 2: Verify MainAsyncSession Provider (NEEDS INVESTIGATION)

**Theory**: Maybe `MainAsyncSession` provider isn't registered correctly?

**Check**:
```python
# src/app/infrastructure/persistence_sqla/provider.py:66
async def get_main_async_session(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[MainAsyncSession]:
    async with async_session_factory() as session:
        yield cast(MainAsyncSession, session)  # Cast to MainAsyncSession

# src/app/setup/ioc/infrastructure.py
provider.provide(
    source=get_main_async_session,
    scope=Scope.REQUEST,
)
```

This looks correct - `get_main_async_session` IS provided at REQUEST scope and returns `MainAsyncSession`.

### Option 3: Create Real Class Instead of NewType (RECOMMENDED) ⭐

Instead of `NewType`, create an actual wrapper class:

```python
# src/app/infrastructure/adapters/types.py
from sqlalchemy.ext.asyncio import AsyncSession

class MainAsyncSession(AsyncSession):
    """
    Main database session type.

    This is a wrapper around AsyncSession to enable Dishka
    to distinguish between different session types.
    """
    pass
```

**Problem**: This would require changing the `get_main_async_session` function to actually instantiate `MainAsyncSession` instead of casting.

### Option 4: Use Different Dishka Pattern (NEEDS RESEARCH)

Maybe Dishka has a way to explicitly map `MainAsyncSession` to `get_main_async_session` provider?

---

## 📋 Next Steps

**Recommended Approach**:

1. **Investigate How Other Adapters Work**
   - Check if `ChatProvider` adapters also use `MainAsyncSession`
   - Verify they work correctly
   - Compare with money market setup

2. **Test Without Money Market Features**
   - Temporarily remove money market handlers from other providers
   - See if server starts without money market dependencies

3. **Contact Dishka Expert / Check Documentation**
   - This might be a known issue with `NewType` and Dishka
   - There might be a specific pattern for handling type aliases

---

## 🔄 Files Modified

### Fixed Files ✅
1. `src/app/infrastructure/celery/app.py` - Added crontab import
2. `src/app/setup/ioc/money_market.py` - Use MainAsyncSession
3. `src/app/infrastructure/adapters/money_market/*.py` (4 files) - Use MainAsyncSession

### Current State
- ✅ `crontab` error: FIXED
- ❌ Dishka dependency injection: BLOCKED
- ❌ Server startup: FAILING

---

## 🚀 Temporary Workaround

To get the server running immediately, you could:

1. **Disable Money Market Features Temporarily**
   - Comment out money market workflow agent registration
   - Comment out money market handler usage
   - This would allow rest of app to work

2. **Use Different Session Type**
   - Make money market adapters accept regular `AsyncSession`
   - Provide `AsyncSession` directly (not MainAsyncSession)
   - This breaks the type separation pattern but would work

---

## Summary

**What's Working**:
- ✅ Celery configuration (crontab import fixed)
- ✅ Guest supervisor with lending/money market routing
- ✅ Code structure and type hints updated

**What's Broken**:
- ❌ Server won't start due to Dishka DI error
- ❌ `MainAsyncSession` NewType not resolving correctly at runtime
- ❌ Money market gateways can't be injected

**Root Cause**:
- `NewType` is compile-time only, Dishka sees runtime `AsyncSession`
- Need either real class or different Dishka configuration pattern

---

**Status**: Awaiting decision on how to proceed with Dishka configuration.
