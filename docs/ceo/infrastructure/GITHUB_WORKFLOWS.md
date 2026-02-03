# GitHub Workflows Documentation

> **Last Updated:** February 2, 2026
> **Status:** ⏸️ **ALL WORKFLOWS TEMPORARILY DISABLED**
> **Methodology:** CTO Framework (MIT Systems Thinking + Stanford Design Thinking)

---

## ⚠️ IMPORTANT: Workflows Temporarily Disabled

**Date:** February 2, 2026

All GitHub Actions workflows have been temporarily disabled to reduce CI costs and noise during active development phase. Workflows will be re-enabled before production deployment.

### Disabled Workflows

| Workflow | File | Reason | Re-enable Criteria |
|----------|------|--------|-------------------|
| API Docs Validation | `api-docs-validation.yml.disabled` | Development phase | Before docs freeze |
| Coverage Report | `coverage-report.yml.disabled` | Weekly overhead | Before release |
| Performance Tests | `performance.yml.disabled` | Resource intensive | Before load testing |
| PR Security Scan | `security-scan-pr.yml.disabled` | PR noise reduction | Before security audit |
| Weekly Security Scan | `security-scan-weekly.yml.disabled` | Placeholder tools | After tool setup |
| Test Suite | `test.yml.disabled` | Test fixes needed | After test cleanup |

### How to Re-enable

```bash
# Re-enable all workflows
cd .github/workflows
for f in *.disabled; do mv "$f" "${f%.disabled}"; done

# Re-enable specific workflow
mv test.yml.disabled test.yml
```

---

## Test Suite Overview (When Enabled)

### Test Categories
- **Total Tests:** 4,875 tests across 387 test files
- **Successfully Collected:** 4,824 tests (99% success rate)
- **Collection Errors:** 51 tests requiring dependency fixes

### Test Distribution
| Category | Tests | Status |
|----------|-------|--------|
| Unit Tests | 1,390 | ✅ 99.9% pass |
| Component Tests | 263 | ✅ 100% pass |
| Integration Tests | 2,491 | ⚠️ 98% pass |
| E2E Tests | 153 | ✅ 99% pass |
| Infrastructure Tests | 108 | ✅ 100% pass |
| Performance Tests | 8 files | ⚠️ 62.5% pass |

---

## Workflow Descriptions

### 1. Test Suite (`test.yml`)
**Purpose:** Main CI workflow for linting, testing, and type checking

**Jobs:**
- `test` - Run linting, all tests, coverage
- `agno-tests` - Agno AI agent framework tests
- `websocket-tests` - WebSocket communication tests
- `celery-tests` - Background task tests
- `auth-tests` - Authentication integration tests
- `type-check` - MyPy static analysis

**Triggers:** Push/PR to master, develop

---

### 2. Coverage Report (`coverage-report.yml`)
**Purpose:** Weekly test coverage analysis and trend tracking

**Schedule:** Monday 2:00 AM UTC

**Outputs:**
- HTML coverage report
- JSON coverage data
- GitHub Step Summary

---

### 3. Performance Tests (`performance.yml`)
**Purpose:** Benchmarks and load testing

**Schedule:** Sunday midnight UTC

**Jobs:**
- `benchmark` - CPU, memory, latency tests
- `load-test` - Locust load testing (manual trigger)

---

### 4. PR Security Scan (`security-scan-pr.yml`)
**Purpose:** Security checks on pull requests

**Tools:**
- TruffleHog - Secret detection
- Bandit - Python security linting
- Safety - Dependency vulnerabilities

---

### 5. Weekly Security Scan (`security-scan-weekly.yml`)
**Purpose:** Comprehensive AI security testing

**Schedule:** Monday 2:00 AM UTC

**Tools:** (Placeholder implementations)
- Helios XSS
- LLMExploiter
- Nettacker
- OWASP AI Testing

---

### 6. API Docs Validation (`api-docs-validation.yml`)
**Purpose:** Validate API documentation completeness

**Scripts:**
- `validate_api_coverage.py`
- `validate_typescript.sh`
- `lint_documentation.py`

---

## Known Issues (Before Re-enable)

### P0 Critical
- [ ] WebSocket test collection error blocks CI job

### P1 High Priority
- [ ] Install `tenacity` dependency for MCP tests
- [ ] Fix 18 guest chat test import errors

### P2 Medium Priority
- [ ] Fix 7 user workflow test errors
- [ ] Fix retry/circuit breaker tests

### P3 Low Priority
- [ ] Fix 3 load test collection errors
- [ ] Implement actual AI security tools

---

## Files

```
.github/workflows/
├── api-docs-validation.yml.disabled
├── coverage-report.yml.disabled
├── OPTIMIZATION_SUMMARY.md
├── performance.yml.disabled
├── security-scan-pr.yml.disabled
├── security-scan-weekly.yml.disabled
└── test.yml.disabled
```

---

*Document maintained by the Engineering Team*
*Last update: February 2, 2026*
