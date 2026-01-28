# MCP Client Provider Fix

**Date**: 2026-01-28  
**Status**: ✅ Fixed  
**Error**: `GraphMissingFactoryError: Cannot find factory for (MCPClient, component='')`

---

## Problem

After fixing the `MCPClient` import error, the application was still failing with:

```
dishka.exceptions.GraphMissingFactoryError: Cannot find factory for (MCPClient, component=''). 
It is missing or has invalid scope.
   │                                  ◈ Scope.APP, component='' ◈                                
   ▼   app.application.lending.tasks.PositionProvider   LendingProvider.provide_position_provider
   ╰─> app.infrastructure.mcp.mcp_client.MCPClient      ???                                      
```

The `LendingProvider.provide_position_provider` method was trying to inject `MCPClient` as a dependency, but there was no provider registered for it in the Dishka IOC container.

---

## Root Cause

The `LendingProvider` had a method that required `MCPClient`:

```python
@provide(scope=Scope.APP)
def provide_position_provider(
    self,
    mcp_client: MCPClient,  # ❌ No provider for this!
) -> PositionProvider:
    ...
```

But there was no `@provide` method to create `MCPClient` instances.

---

## Solution

Added a provider method for `MCPClient` in `LendingProvider`:

```python
@provide(scope=Scope.APP)
def provide_mcp_client(self) -> MCPClient:
    """
    Provide MCP client for calling MCP servers.
    
    Creates a shared HTTP client for making requests to MCP servers
    (Aave, Morpho, etc.) running on different ports.
    
    Returns:
        MCPClient instance configured with default timeout (30s)
    
    Scope:
        APP scope - shared across all requests for efficiency
    """
    return MCPClient(timeout=30.0)
```

---

## Files Modified

1. **`src/app/setup/ioc/lending.py`**
   - Added `provide_mcp_client()` method
   - Updated class docstring to document MCP client provider
   - Scope: `APP` (shared across all requests)

---

## Verification

```bash
# Test provider method exists
python3.12 -c "from app.setup.ioc.lending import LendingProvider; lp = LendingProvider(); print('provide_mcp_client' in dir(lp))"
# ✅ True

# Test provider creates MCPClient
python3.12 -c "from app.setup.ioc.lending import LendingProvider; lp = LendingProvider(); client = lp.provide_mcp_client(); print(type(client).__name__)"
# ✅ MCPClient
```

---

## Dependency Graph

```
LendingProvider
├── provide_mcp_client() → MCPClient (APP scope)
└── provide_position_provider(mcp_client: MCPClient) → PositionProvider (APP scope)
    └── PositionProviderAdapter
        └── Uses MCPClient to call Aave/Morpho MCP servers
```

---

## Status

✅ **Fixed**: `GraphMissingFactoryError` for `MCPClient`  
✅ **Verified**: Provider method creates `MCPClient` instances  
✅ **Ready**: Application should start without this error after restart

---

## Next Steps

1. **Restart FastAPI server** to pick up the changes
2. **Verify application starts** without `GraphMissingFactoryError`
3. **Test lending endpoints** to ensure MCP client works correctly

---

**Note**: There may be other dependency issues (e.g., `tenacity`), but those are separate from this fix. The `MCPClient` provider error is now resolved.
