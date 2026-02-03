# Tenacity Dependency Fix

**Date**: 2026-01-28  
**Status**: ✅ Fixed  
**Issue**: Scripts using system Python instead of venv Python

---

## Problem

The FastAPI server was failing with:
```
ModuleNotFoundError: No module named 'tenacity'
```

Even though `tenacity>=8.0.0` is listed in `pyproject.toml` and installed in the virtual environment.

---

## Root Cause

The `scripts/start_dev.sh` script was using `python3.12` directly, which resolved to the system Python instead of the venv Python, even after activating the virtual environment.

**Issue**: Background processes spawned from the script don't inherit the venv PATH modifications properly.

---

## Solution

Updated scripts to use the venv Python explicitly:

### 1. Updated `scripts/start_dev.sh`

**Before**:
```bash
source env/bin/activate
PYTHONPATH=src python3.12 -m uvicorn app.run:make_app ...
```

**After**:
```bash
source env/bin/activate
VENV_PYTHON="./env/bin/python3.12"
PYTHONPATH=src $VENV_PYTHON -m uvicorn app.run:make_app ...
```

### 2. Updated `Makefile`

**Before**:
```makefile
start:
	. env/bin/activate && PYTHONPATH=src python3.12 -m uvicorn ...
```

**After**:
```makefile
start:
	. env/bin/activate && PYTHONPATH=src ./env/bin/python3.12 -m uvicorn ...
```

---

## Files Modified

1. **`scripts/start_dev.sh`**
   - Added `VENV_PYTHON="./env/bin/python3.12"` variable
   - Updated FastAPI startup to use `$VENV_PYTHON`
   - Updated MCP server startup to use `$VENV_PYTHON`

2. **`Makefile`**
   - Updated `start` target to use `./env/bin/python3.12` explicitly

---

## Verification

```bash
# Check tenacity is in pyproject.toml
grep tenacity pyproject.toml
# ✅ "tenacity>=8.0.0"

# Check tenacity is installed in venv
./env/bin/python3.12 -m pip show tenacity
# ✅ Version: 9.1.2

# Test import with venv Python
./env/bin/python3.12 -c "import tenacity; print('✅ Success')"
# ✅ Success
```

---

## Status

✅ **Fixed**: Scripts now use venv Python explicitly  
✅ **Verified**: `tenacity` is available in venv  
✅ **Ready**: Server should start without `tenacity` import errors after restart

---

## Next Steps

1. **Restart FastAPI server** using `make stop-dev && make start-dev`
2. **Verify** no more `tenacity` import errors in logs
3. **Check** that all dependencies are accessible

---

**Note**: The issue was not that `tenacity` was missing from `pyproject.toml` (it's there), but that the scripts weren't using the venv Python that has `tenacity` installed.
