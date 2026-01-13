# Test Scripts

This directory contains utility scripts for generating comprehensive test results.

## generate_comprehensive_test_csvs.py

Generates CSV test results for all chat features across guest and authenticated users.

### Test Coverage

**Guest Users (47 tests):**
- General informational queries (What is Bitcoin?, DeFi, etc.)
- Hunter AI price predictions and sentiment analysis
- All 9 shortcuts (lending, swap, portfolio, balance, activity, receive, buy, send, money_market)
- Multi-language support (English, Spanish, Portuguese, Chinese, French)
- Edge cases and error handling

**Authenticated Users (46 tests):**
- Same coverage as guest users
- Premium features (no signup prompts, real data, higher rate limits)
- Multi-step flows for lending, swap, buy, send

### Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the script
python tests/scripts/generate_comprehensive_test_csvs.py
```

### Output

CSV files are generated in `docs/output/`:
- `guest.csv` - Guest user test results
- `log-user.csv` - Authenticated user test results

### CSV Format

```
Type, device, is multi step, input 1, output 1, input 2, output 2, input 3, output 3, input 4, output 4, test pass
```

- **Type**: query type (always "query")
- **device**: test device (always "pytest")
- **is multi step**: YES for multi-step flows, NO for single queries
- **input 1-4**: User input messages
- **output 1-4**: Agent response messages
- **test pass**: PASS or FAIL

### Expected Results

- **Guest**: ~46/47 tests should PASS (1 validation error expected)
- **Auth**: ~20/46 tests should PASS (rate limit errors expected after ~20 queries)

Rate limit errors (HTTP 429) are expected behavior showing the system is working correctly.
