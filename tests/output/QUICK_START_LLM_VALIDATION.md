# Quick Start: LLM Test Validation System

**Last Updated**: 2026-01-15

---

## 🚀 Fastest Way to Run

### Option 1: Basic Mode (No LLM Required)

```bash
# Start services
make up.db
make start

# Run validator (works without Vertex AI)
python scripts/llm_test_validator.py --mode guest

# View results
cat tests/output/guest/llm_validated_results.csv
```

**Time**: ~15 minutes
**Cost**: $0 (no LLM calls)
**Output**: CSV with test results (no LLM analysis)

---

### Option 2: Full LLM Analysis

```bash
# 1. Install dependencies
pip install google-cloud-aiplatform vertexai

# 2. Authenticate
gcloud auth application-default login

# 3. Configure (edit config/local/.secrets.toml)
[vertex_ai]
project_id = "your-gcp-project-id"
location = "us-central1"

# 4. Run with LLM analysis
python scripts/llm_test_validator.py --mode all

# 5. View results with LLM insights
cat tests/output/guest/llm_validated_results.csv
```

**Time**: ~2-3 hours (all 424+ tests)
**Cost**: <$0.01
**Output**: CSV with intelligent failure analysis

---

## 📊 Run Specific Test Suites

### Guest Tests Only (~15 min)
```bash
python scripts/llm_test_validator.py --mode guest
# Output: tests/output/guest/llm_validated_results.csv
```

### User Tests Only (~20 min)
```bash
python scripts/llm_test_validator.py --mode user
# Output: tests/output/user/llm_validated_results.csv
```

### Advanced Tests Only (~90-120 min)
```bash
python scripts/llm_test_validator.py --mode advanced
# Output: tests/output/advanced/llm_validated_results.csv
```

---

## 📋 What You Get

### CSV Columns

```
test_id              | guest_001
category             | guest_chat
scenario             | test_guest_price_query
status               | PASS | FAIL | SKIP | ERROR
execution_time_ms    | 3456
error_message        | (if failed)
llm_analysis         | (root cause - LLM only)
severity             | critical | major | minor | trivial
recommendations      | (actionable fixes - LLM only)
```

### Example Output

**PASS** (basic):
```csv
guest_001,guest_chat,test_price_query,PASS,3456,"","","",""
```

**FAIL** (with LLM):
```csv
user_042,security,test_xss_prevention,FAIL,2100,"AssertionError...","XSS vulnerability due to insufficient sanitization","major","Add HTML encoding | Use CSP headers"
```

---

## ⏱️ Estimated Run Times

| Suite | Tests | Time | Cost |
|-------|-------|------|------|
| **guest** | 75+ | 15 min | <$0.001 |
| **user** | 52+ | 20 min | <$0.001 |
| **advanced** | 297+ | 120 min | <$0.008 |
| **all** | 424+ | 150 min | <$0.01 |

---

## 🔍 Analyzing Results

### View Pass/Fail Summary
```bash
# Count by status
awk -F',' 'NR>1 {print $7}' tests/output/guest/llm_validated_results.csv | sort | uniq -c

# Example output:
#  65 PASS
#   8 FAIL
#   2 SKIP
```

### Extract Failed Tests
```bash
# Get all failures
grep ",FAIL," tests/output/guest/llm_validated_results.csv

# Get critical failures only
grep ",FAIL," tests/output/guest/llm_validated_results.csv | grep ",critical,"
```

### View LLM Recommendations
```bash
# Extract recommendations for failures
awk -F',' 'NR>1 && $7=="FAIL" {print $3": "$12}' tests/output/guest/llm_validated_results.csv
```

---

## ⚠️ Troubleshooting

### "LLM not available" Warning

**Message**:
```
⚠️  LLM not available: No module named 'google.cloud'
   Continuing with basic analysis only
```

**Fix**:
```bash
pip install google-cloud-aiplatform vertexai
```

**Or** just continue - system works without LLM (no failure analysis)

---

### Tests Timing Out

**Issue**: Tests take too long

**Solutions**:
1. Run specific suites instead of --mode all
2. Increase timeout in script (line 109)
3. Check if services are responding:
   ```bash
   curl http://localhost:8080/health
   ```

---

### No CSV Generated

**Issue**: CSV file empty or missing

**Check**:
```bash
# Verify services running
make status-dev

# Check logs
tail -f logs/fastapi.log

# Verify database
psql -U postgres -d anvil_test -c "SELECT 1;"
```

---

## 📈 Success Criteria

✅ **System working if**:
- CSV files generated in tests/output/
- Status column has PASS/FAIL/SKIP/ERROR values
- test_id and scenario columns populated
- Execution times > 0

✅ **LLM working if**:
- llm_analysis column has text for failures
- severity column has critical/major/minor/trivial
- recommendations column has actionable fixes

---

## 🎯 Next Steps After Running

### 1. Review Critical Failures
```bash
# Extract critical issues
grep "critical" tests/output/*/llm_validated_results.csv > critical_failures.txt
```

### 2. Fix Issues
- Read LLM recommendations
- Implement fixes
- Re-run affected tests

### 3. Track Over Time
```bash
# Save results with timestamp
cp tests/output/guest/llm_validated_results.csv \
   tests/output/guest/results_$(date +%Y%m%d).csv
```

### 4. Generate Report
```bash
# Create summary
echo "Test Run: $(date)" > test_report.txt
echo "Total: $(wc -l < tests/output/guest/llm_validated_results.csv) tests" >> test_report.txt
echo "Passed: $(grep ',PASS,' tests/output/guest/llm_validated_results.csv | wc -l)" >> test_report.txt
echo "Failed: $(grep ',FAIL,' tests/output/guest/llm_validated_results.csv | wc -l)" >> test_report.txt
```

---

## 📚 Related Documentation

- **Full Implementation Guide**: `tests/output/LLM_TEST_VALIDATION_IMPLEMENTATION_SUMMARY.md`
- **Planning Document**: `tests/output/LLM_TEST_VALIDATION_PLAN.md`
- **Script Source**: `scripts/llm_test_validator.py`

---

## 💡 Tips

### Run in Background
```bash
# Run in background (takes hours)
nohup python scripts/llm_test_validator.py --mode all > test_run.log 2>&1 &

# Check progress
tail -f test_run.log
```

### Run Subset First
```bash
# Test the system with guest tests first
python scripts/llm_test_validator.py --mode guest

# If successful, run full suite
python scripts/llm_test_validator.py --mode all
```

### Save Costs (No LLM)
```bash
# Run without Vertex AI (still generates CSV)
# Just don't configure Vertex AI in secrets.toml
python scripts/llm_test_validator.py --mode all
```

---

**Status**: ✅ Ready to use
**Total Time**: ~2-3 hours for full validation
**Total Cost**: <$0.01
**Value**: Automated intelligent test analysis
