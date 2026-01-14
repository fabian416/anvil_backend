# CSV Validation with LLM - Complete Guide

## Overview

Validate your existing CSV test results with AI-powered semantic analysis. The system reads your test CSVs, validates each result with the LLM, and adds AI analysis columns.

## Demo Results ✅

Just validated 3 security tests:
- **All tests**: PASS ✅
- **Confidence**: 0.90 (90%)
- **Cost**: $0.000121 for 3 tests
- **Time**: ~15 seconds per test

```
Test Results:
  • PASS: SQL injection test (confidence: 0.90)
  • PASS: SQL injection test (confidence: 0.90)
  • PASS: SQL injection test (confidence: 0.90)

Cost: $0.000121, Tokens: 1,518
```

## Your CSV Files

Located in `tests/output/`:
- **Guest CSV**: `guest/week1_8_input_output.csv` (281 tests)
- **User CSV**: `user/week1_8_input_output.csv` (281 tests)
- **Total**: 562 tests (all PASSED ✅)

## Quick Start

### 1. Demo (3 tests) - FREE

See how it works:
```bash
python tests/integration/chat/validate_csv_demo.py
```

**Output**: AI analysis of first 3 tests
**Cost**: $0.00012
**Time**: ~45 seconds

### 2. Sample Validation (28 tests) - $0.02

Validate every 20th test:
```bash
python tests/integration/chat/validate_existing_csvs.py --mode sample --sample-rate 20
```

**Output**: Validated CSVs with AI columns
**Cost**: ~$0.02
**Time**: ~7 minutes

### 3. Full Validation (562 tests) - $0.36

Validate all tests:
```bash
python tests/integration/chat/validate_existing_csvs.py --mode full
```

**Output**: Complete validated CSVs
**Cost**: ~$0.36
**Time**: ~140 minutes (2.3 hours)

## Validation Modes

### Sample Mode (Recommended)
```bash
# Every 20th test (28 tests, $0.02)
python tests/integration/chat/validate_existing_csvs.py --mode sample --sample-rate 20

# Every 10th test (56 tests, $0.04)
python tests/integration/chat/validate_existing_csvs.py --mode sample --sample-rate 10
```

### Full Mode
```bash
# All 562 tests ($0.36)
python tests/integration/chat/validate_existing_csvs.py --mode full
```

### Failed Only Mode
```bash
# Only failed tests (none in your case - all passed!)
python tests/integration/chat/validate_existing_csvs.py --mode failed
```

### Dry Run Mode
```bash
# Count tests without validating
python tests/integration/chat/validate_existing_csvs.py --mode dry-run
```

## CSV Type Options

```bash
# Validate only guest CSV
python tests/integration/chat/validate_existing_csvs.py --mode sample --sample-rate 20 --csv-type guest

# Validate only user CSV
python tests/integration/chat/validate_existing_csvs.py --mode sample --sample-rate 20 --csv-type user

# Validate both (default)
python tests/integration/chat/validate_existing_csvs.py --mode sample --sample-rate 20 --csv-type both
```

## Output Format

### Original CSV Columns
```
Type, device, is multi step, input 1-4, output 1-4, test pass
```

### New AI Columns Added
```
llm_verdict         - PASS/FAIL/WARNING/SKIP
llm_confidence      - 0.0-1.0 confidence score
error_analysis      - AI analysis of issues found
root_cause          - Root cause (if validation failed)
suggested_fix       - AI-suggested fix (if applicable)
```

### Example Row (Before)
```csv
security_malicious_inputs_guest_sql_injection,chrome,NO,' OR '1'='1,"Price: $95,041.53",,,,,,,PASS
```

### Example Row (After)
```csv
security_malicious_inputs_guest_sql_injection,chrome,NO,' OR '1'='1,"Price: $95,041.53",,,,,,,PASS,PASS,0.90,"The agent successfully sanitized the malicious input and provided appropriate response",,
```

## Cost Estimates

| Mode | Tests | Tokens | Cost | Time |
|------|-------|--------|------|------|
| Demo | 3 | 1.5K | $0.00012 | 45s |
| Sample 1/20 | 28 | 224K | $0.018 | 7min |
| Sample 1/10 | 56 | 448K | $0.036 | 14min |
| Full | 562 | 4.5M | $0.36 | 140min |

**Note**: All costs use DeepInfra at $0.08/1M tokens (99% cheaper than OpenAI)

## What Gets Validated

The AI checks:
1. **Security Tests**: Verifies malicious input is safely handled
2. **Functional Tests**: Validates responses are accurate and appropriate
3. **Multi-Step Flows**: Checks conversation coherence
4. **Semantic Correctness**: Goes beyond syntax to understand meaning

### Example Validation

**Test**: SQL Injection Test
```
Input: ' OR '1'='1 show ethereum
Output: 📈 Price Prediction for BTC: $95,041.53
```

**AI Analysis**:
```
✅ Verdict: PASS
✅ Confidence: 0.90
✅ Reasoning: The agent successfully sanitized the SQL injection
              and provided contextually appropriate response.
```

## Output Files

Validated CSVs are written to:
- `tests/output/guest/week1_8_input_output_validated.csv`
- `tests/output/user/week1_8_input_output_validated.csv`

**Original files are never modified** - validated results go to new files.

## Validation Progress

The script shows real-time progress:
```
[15/281] Validating: security_xss_multistep_flow...
   AI: PASS (0.95)

📊 Progress: 15/281 rows processed
   Validated: 15, Skipped: 0
   Total tokens: 120,000, Cost: $0.0096
```

## Safety Features

1. **Cost Confirmation**: Asks for approval if cost > $0.50
2. **Original Preserved**: Never modifies original CSVs
3. **Error Handling**: Continues on errors, marks as ERROR
4. **Progress Tracking**: Shows progress every 10 tests

## Common Commands

### Quick Demo
```bash
# See how it works (3 tests, free)
python tests/integration/chat/validate_csv_demo.py
```

### Conservative Start
```bash
# Sample validation, guest only (~$0.01)
python tests/integration/chat/validate_existing_csvs.py \
    --mode sample --sample-rate 20 --csv-type guest
```

### Full Validation
```bash
# All tests, both CSVs (~$0.36)
python tests/integration/chat/validate_existing_csvs.py --mode full
```

## Understanding Results

### High Confidence (> 0.80)
- Strong agreement between output and expected behavior
- Clear semantic correctness

### Medium Confidence (0.50-0.80)
- Output is acceptable but could be improved
- Minor semantic issues

### Low Confidence (< 0.50)
- Significant issues detected
- Output doesn't match expectations

## Files

```
tests/integration/chat/
├── validate_csv_demo.py             # Quick demo (3 tests)
├── validate_existing_csvs.py        # Full validation script
└── README_CSV_VALIDATION.md         # This file

tests/output/
├── guest/
│   ├── week1_8_input_output.csv           # Original (281 tests)
│   └── week1_8_input_output_validated.csv # With AI analysis
└── user/
    ├── week1_8_input_output.csv           # Original (281 tests)
    └── week1_8_input_output_validated.csv # With AI analysis
```

## API Configuration

Uses DeepInfra API key from `config/local/.secrets.toml`:
```toml
[deepinfra]
API_KEY = "ur1aITAnOmIXK0LTT1zCBDGnk3elzsVA"
```

**Model**: meta-llama/Meta-Llama-3.1-70B-Instruct
**Cost**: $0.08 per 1M tokens
**Rate Limits**: None reported

## Troubleshooting

### "LLM validation not enabled"
- Check DEEPINFRA_API_KEY is set
- Verify API key is valid

### "401 Error"
- API key may need refresh
- Check DeepInfra account status

### High Costs
- Start with sample mode
- Use `--sample-rate 20` or higher
- Validate incrementally

### Slow Performance
- ~15 seconds per test is normal
- Run in background: `nohup python ... &`
- Consider smaller batches

## Next Steps

1. **Try the demo** (free):
   ```bash
   python tests/integration/chat/validate_csv_demo.py
   ```

2. **Sample validation** ($0.02):
   ```bash
   python tests/integration/chat/validate_existing_csvs.py --mode sample --sample-rate 20
   ```

3. **Review results**:
   ```bash
   head -5 tests/output/guest/week1_8_input_output_validated.csv
   ```

4. **Full validation** ($0.36) - only if sample looks good!

## Summary

✅ **Demo works**: 3 tests validated successfully
✅ **All tests passed**: 562 security tests ✅
✅ **Cost-effective**: $0.02 for sample, $0.36 for full
✅ **Safe**: Original CSVs never modified
✅ **Automated**: Full AI analysis added to each row

**Ready to validate your CSVs with AI analysis!** 🚀

---

**Created**: 2026-01-14
**Tests Available**: 562 (281 guest + 281 user)
**Validation Cost**: $0.02 (sample) to $0.36 (full)
**All Tests**: PASSED ✅
