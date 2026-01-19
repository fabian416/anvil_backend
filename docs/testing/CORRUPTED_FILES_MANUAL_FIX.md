# Corrupted Test Files - Manual Fix Guide

## Overview

20 integration test files have severe syntax errors from an earlier phase where LLM validation blocks were incorrectly inserted into function signatures instead of function bodies. These files require manual intervention before Phase 4 updates can be applied.

## Corrupted Files List

### Knowledge Tests (1 file)
- `tests/integration/guest/knowledge/test_knowledge_injection_api.py`

### General Tests (16 files)  
- `tests/integration/guest/general/test_agent_squad_ultra_hunter_full.py`
- `tests/integration/guest/general/test_buy_intent.py`
- `tests/integration/guest/general/test_common_informational_queries.py`
- `tests/integration/guest/general/test_cross_chain_comprehensive.py`
- `tests/integration/guest/general/test_hunter_chat_integration.py`
- `tests/integration/guest/general/test_interruption_flows.py`
- `tests/integration/guest/general/test_low_coverage_intents.py`
- `tests/integration/guest/general/test_multi_intent_end_to_end.py`
- `tests/integration/guest/general/test_multi_step_flows.py`
- `tests/integration/guest/general/test_multilanguage_comprehensive.py`
- `tests/integration/guest/general/test_redis_metrics_collector.py`
- `tests/integration/guest/general/test_shortcuts_edge_cases.py`
- `tests/integration/guest/general/test_ultra_chat_integration.py`
- `tests/integration/guest/general/test_unified_chat_critical_paths.py`
- `tests/integration/guest/general/test_unified_chat_with_test_data.py`
- `tests/integration/guest/general/test_user_chat_messages.py`

### User Tests (3 files)
- `tests/integration/user/authenticated/test_archive_conversation.py`
- `tests/integration/user/authenticated/test_authenticated_chat_comprehensive.py`
- `tests/integration/user/authenticated/test_authenticated_chat_integration.py`

## Problem Description

The corruption follows this pattern:

```python
# CORRECT Structure (what it should be):
async def test_example(
    self,
    client: AsyncClient,
    llm_validator,
    csv_tracker
):
    """Test description."""
    response = await client.post(...)
    content = response.json()["choices"][0]["message"]["content"]
    
    # LLM validation INSIDE function body (CORRECT)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(...)

# CORRUPTED Structure (what these files have):
async def test_example(
    self,
    client: AsyncClient,
    llm_validator,
    
    # LLM validation block INSIDE function signature (WRONG!)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(...)
    
    csv_tracker  # <- signature continues after LLM block!
):
    """Test description."""
    response = await client.post(...)
```

## Manual Fix Procedure

For each corrupted file, follow these steps:

### Step 1: Identify the Corruption

1. Open the file in an editor
2. Find the function with syntax error (usually first test method)
3. Look for LLM validation block between function parameters

### Step 2: Extract the LLM Block

1. Cut the entire LLM validation block (from `# Optional LLM...` to the closing `)`)
2. Note any parameters that appear after the block
3. Reconstruct the correct function signature with all parameters

### Step 3: Fix the Function Signature

```python
# Before (corrupted):
async def test_example(
    self,
    param1: str,
    
# Optional LLM semantic validation...
if llm_validator.enabled:
    ...
    
param2: int
):

# After (fixed):
async def test_example(
    self,
    param1: str,
    param2: int
):
```

### Step 4: Place LLM Block in Correct Location

The LLM validation block should go:
1. AFTER the API call that generates the response
2. AFTER extracting `content` from the response
3. BEFORE the CSV tracking (if present)

```python
async def test_example(
    self,
    param1: str,
    param2: int
):
    """Test description."""
    
    # Make API call
    response = await client.post(...)
    
    # Extract content
    content = response.json()["choices"][0]["message"]["content"]
    
    # NOW place LLM validation here (CORRECT location)
    if llm_validator.enabled:
        validation = await llm_validator.validate_single_response(
            test_name="test_example",
            user_input="...",
            agent_output=content,
            expected_behavior="...",
            additional_context={...}
        )
        if validation.verdict != "PASS":
            pytest.warn(UserWarning(f"LLM validation concern: {validation.reasoning}"))
```

### Step 5: Verify Syntax

```bash
python3 -c "import py_compile; py_compile.compile('path/to/file.py', doraise=True)"
```

### Step 6: Apply Phase 4 Updates

Once syntax is fixed, run the Phase 4 updater:

```bash
python3 /tmp/phase4_ast_updater.py path/to/file.py
```

This will:
- Add required imports
- Add `test_func` parameter to LLM validation
- Replace `pytest.warn` with `warnings.warn`
- Add enhanced CSV tracking fields

## Batch Fix Script (Optional)

For efficiency, you can fix multiple files at once:

```bash
#!/bin/bash
# fix_corrupted_files.sh

CORRUPTED_FILES=(
    "tests/integration/guest/knowledge/test_knowledge_injection_api.py"
    "tests/integration/guest/general/test_buy_intent.py"
    # ... add all 20 files
)

for file in "${CORRUPTED_FILES[@]}"; do
    echo "Fixing: $file"
    
    # Step 1: Manual editing required - open in editor
    vim "$file"  # or your preferred editor
    
    # Step 2: Verify syntax
    if python3 -c "import py_compile; py_compile.compile('$file', doraise=True)" 2>/dev/null; then
        echo "✅ Syntax OK"
        
        # Step 3: Apply Phase 4 updates
        python3 /tmp/phase4_ast_updater.py "$file"
        
        # Step 4: Final verification
        python3 -c "import py_compile; py_compile.compile('$file', doraise=True)"
    else
        echo "❌ Syntax error - manual fix needed"
    fi
done
```

## Testing After Fix

After fixing all files:

```bash
# Run a sample test from each batch
python3 -m pytest tests/integration/guest/knowledge/test_knowledge_injection_api.py::TestAuthenticatedUserKnowledgeInjection::test_what_can_you_do_authenticated -v

# If successful, run full test suite
python3 -m pytest tests/integration/ -v
```

## Prevention

To prevent future corruption:

1. **Pre-commit Hooks**: Add syntax checking
   ```bash
   # .git/hooks/pre-commit
   find tests -name "*.py" -exec python3 -m py_compile {} \;
   ```

2. **CI/CD Checks**: Add syntax validation to pipeline
   ```yaml
   - name: Validate Python Syntax
     run: find tests -name "*.py" | xargs python3 -m py_compile
   ```

3. **Code Review**: Require review for test file changes

## Timeline Estimate

- **Per File**: 5-10 minutes manual fix
- **Batch of 20 files**: 2-3 hours total
- **Verification**: 30 minutes
- **Total Effort**: ~3-4 hours

## Priority

**Medium-High**: These files don't currently work (syntax errors), so fixing them will restore 20 test files to working condition and enable Phase 4 enhancements.
