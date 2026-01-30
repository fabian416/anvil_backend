# GitHub Workflows Documentation

> Last Updated: January 30, 2026
> All tests verified locally and passing

This document provides a comprehensive overview of all GitHub Actions workflows in the Anvil Backend project, including their purpose, triggers, jobs, and test coverage.

## Table of Contents

1. [Test Suite (`test.yml`)](#1-test-suite-testyml)
2. [Coverage Report (`coverage-report.yml`)](#2-coverage-report-coverage-reportyml)
3. [PR Security Scan (`security-scan-pr.yml`)](#3-pr-security-scan-security-scan-pryml)
4. [Weekly Security Scan (`security-scan-weekly.yml`)](#4-weekly-security-scan-security-scan-weeklyyml)
5. [Performance Tests (`performance.yml`)](#5-performance-tests-performanceyml)
6. [API Docs Validation (`api-docs-validation.yml`)](#6-api-docs-validation-api-docs-validationyml)
7. [Test Results Summary](#7-test-results-summary)

---

## 1. Test Suite (`test.yml`)

### Purpose
The main CI workflow that runs on every push and pull request to ensure code quality, run tests, and verify type safety.

### Triggers
- **Push** to `master` or `develop` branches
- **Pull Request** to `master` or `develop` branches
- Only runs when relevant files change: `src/**`, `tests/**`, `pyproject.toml`, `alembic/**`

### Jobs

#### 1.1 `test` - Main Test Suite
**Purpose**: Run linting, all tests, and generate coverage reports.

| Step | Command | Description |
|------|---------|-------------|
| Linting | `make code.lint` | Runs ruff, slotscheck, mypy |
| Unit Tests | `make code.test` | Runs all pytest tests |
| Coverage | `make code.cov` | Generates coverage.xml |

**Services Required**:
- PostgreSQL 15 (port 5432)
- Redis 7 (port 6379)

**Test Status**: ✅ Pass

---

#### 1.2 `agno-tests` - Agno Agent Tests
**Purpose**: Test the Agno AI agent framework and MCP (Model Context Protocol) server integration.

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/infrastructure/agno/test_agents.py` | 19 | ✅ Pass |
| `tests/infrastructure/mcp/test_mcp_servers.py` | 15 | ✅ Pass |

**Why We Need It**:
- Validates AI agent configuration and initialization
- Tests intent classification for different user queries
- Verifies MCP server tools and endpoints
- Ensures agent session management works correctly

**Key Tests**:
- `TestAgnoConfig` - Configuration initialization and defaults
- `TestIntentClassification` - Trading, lending, analytics intent keywords
- `TestMCPToolIntegration` - MCP tool response structure
- `TestPortfolioMCP`, `TestOneInchMCP`, `TestAaveMCP`, `TestDeFiLlamaMCP` - MCP servers

---

#### 1.3 `websocket-tests` - WebSocket Tests
**Purpose**: Test real-time WebSocket communication for chat and notifications.

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/presentation/websocket/test_websocket.py` | 13 | ✅ Pass |

**Why We Need It**:
- Validates connection manager for multi-user sessions
- Tests message broadcasting and targeted messages
- Verifies authentication via JWT tokens
- Ensures graceful handling of broken connections

**Key Tests**:
- `TestConnectionManager` - Connect, disconnect, send_to_user, broadcast
- `TestWebSocketChat` - Valid/invalid token handling
- `TestWebSocketIntegration` - Message flow, concurrent users
- `TestWebSocketPerformance` - Broadcast and targeted message performance

---

#### 1.4 `celery-tests` - Celery Task Tests
**Purpose**: Test background task infrastructure and scheduled jobs.

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/integration/celery/test_celery_tasks.py` | 21 (18 pass, 3 skip) | ✅ Pass |

**Why We Need It**:
- Validates Celery app configuration
- Tests task registration and beat schedule
- Verifies Privy wallet balance sync tasks
- Ensures error handling in background jobs

**Key Tests**:
- `TestCeleryTaskStructure` - App exists, tasks module, beat schedule
- `TestPrivyBalanceTasks` - Wallet balance sync, task registration
- `TestTaskExecution` - Async task patterns
- `TestTaskErrorHandling` - Database and DI error handling

---

#### 1.5 `auth-tests` - Auth Integration Tests
**Purpose**: Test authentication flows including Privy login and traditional login.

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/integration/auth/test_privy_login.py` | 10 | ✅ Pass |
| `tests/integration/auth/test_login_flow.py` | 13 | ✅ Pass |

**Why We Need It**:
- Validates Privy API client initialization
- Tests wallet ID fetching from Privy
- Verifies login endpoint error handling
- Ensures rate limiting works correctly

**Key Tests**:
- `TestPrivyApiClient` - Import, initialization, headers
- `TestPrivyWalletSync` - Wallet and user data classes
- `TestPrivyBalanceSyncTask` - Task existence and registration
- `TestLoginFlow` - Valid/invalid credentials, error responses

---

#### 1.6 `type-check` - Type Checking
**Purpose**: Run mypy static type analysis on critical modules.

| Module | Status |
|--------|--------|
| `src/app/infrastructure/agno/` | ✅ Checked |
| `src/app/infrastructure/mcp/` | ✅ Checked |
| `src/app/presentation/http/websocket/` | ✅ Checked |
| `src/app/infrastructure/celery/tasks/` | ✅ Checked |
| `src/app/infrastructure/adapters/privy/` | ✅ Checked |

**Why We Need It**:
- Catches type errors before runtime
- Enforces type annotations
- Improves code quality and documentation

---

## 2. Coverage Report (`coverage-report.yml`)

### Purpose
Generate comprehensive test coverage reports on a weekly basis.

### Triggers
- **Schedule**: Weekly on Monday at 2:00 AM UTC
- **Manual**: `workflow_dispatch`

### Jobs

#### 2.1 `coverage` - Coverage Analysis
**Purpose**: Run all tests with coverage and generate reports.

| Step | Output | Description |
|------|--------|-------------|
| Run tests | HTML, JSON, terminal | Full test suite with coverage |
| Generate summary | GitHub Step Summary | Markdown coverage table |
| Check trends | `.coverage_history.json` | Compare with previous runs |

**Script**: `scripts/check_coverage_trends.py`

**Why We Need It**:
- Track test coverage over time
- Identify coverage regressions
- Maintain minimum 60% threshold
- Archive reports for 90 days

---

## 3. PR Security Scan (`security-scan-pr.yml`)

### Purpose
Run security checks on every pull request to catch vulnerabilities before merge.

### Triggers
- **Pull Request** to `master` or `develop` branches
- Only runs when relevant files change

### Jobs

#### 3.1 `security-check` - Security Analysis
**Purpose**: Scan for security vulnerabilities and hardcoded secrets.

| Tool | Purpose | Output |
|------|---------|--------|
| TruffleHog | Detect hardcoded secrets | PR diff scan |
| Bandit | Python security linting | `bandit-pr.json` |
| Safety | Dependency vulnerabilities | `safety-pr.json` |

**Why We Need It**:
- Prevent secrets from being committed
- Catch SQL injection, XSS vulnerabilities
- Identify vulnerable dependencies
- Auto-comment on PRs with findings

---

## 4. Weekly Security Scan (`security-scan-weekly.yml`)

### Purpose
Comprehensive security scan including AI-specific vulnerability testing.

### Triggers
- **Schedule**: Weekly on Monday at 2:00 AM UTC
- **Manual**: `workflow_dispatch`

### Jobs

#### 4.1 `comprehensive-security-scan` - Full Security Audit
**Purpose**: Run all security tools including AI-specific scanners.

| Tool | Purpose | Status |
|------|---------|--------|
| Helios XSS | XSS vulnerability scan | ⚠️ Placeholder |
| LLMExploiter | LLM prompt injection | ⚠️ Placeholder |
| Nettacker | Network vulnerability scan | ⚠️ Placeholder |
| LLM Security Auditor | AI model security | ⚠️ Placeholder |
| OWASP AI Testing | AI-specific OWASP tests | ⚠️ Placeholder |

**Script**: `security/setup/install_all.sh`

**Why We Need It**:
- AI-specific security testing
- Network vulnerability scanning
- Unified security reporting
- Slack alerts for critical issues

---

## 5. Performance Tests (`performance.yml`)

### Purpose
Run performance benchmarks and load tests to ensure system scalability.

### Triggers
- **Schedule**: Weekly on Sunday at midnight UTC
- **Manual**: `workflow_dispatch`

### Jobs

#### 5.1 `benchmark` - Performance Benchmarks
**Purpose**: Run CPU, memory, and response time benchmarks.

| Script | Output | Description |
|--------|--------|-------------|
| `tests/performance/benchmark.py` | `benchmark-results.txt` | Core benchmarks |
| `tests/performance/stress_test.py` | `stress-test-results.txt` | Stress testing |

**Services Required**:
- PostgreSQL 14
- Redis 7

#### 5.2 `load-test` - Load Testing (Manual Only)
**Purpose**: Run Locust load tests against staging environment.

| Parameter | Value |
|-----------|-------|
| Users | 100 |
| Spawn Rate | 10/s |
| Duration | 5 minutes |

**Script**: `tests/performance/locustfile.py`

**Why We Need It**:
- Identify performance regressions
- Test system under load
- Measure response times
- Validate scalability

---

## 6. API Docs Validation (`api-docs-validation.yml`)

### Purpose
Validate API documentation completeness and TypeScript type accuracy.

### Triggers
- **Push** to `master` or `main` when docs change
- **Pull Request** when API controllers or docs change

### Jobs

#### 6.1 `validate-api-docs` - Documentation Validation
**Purpose**: Ensure API documentation matches implementation.

| Script | Output | Description |
|--------|--------|-------------|
| `validate_api_coverage.py` | `coverage_report.json` | Endpoint coverage |
| `validate_typescript.sh` | `typescript_validation_report.json` | TS type checking |
| `lint_documentation.py` | `lint_report.json` | Doc quality check |

**Why We Need It**:
- Keep frontend types in sync with backend
- Ensure all endpoints are documented
- Maintain documentation quality
- Auto-comment on PRs with results

---

## 7. Test Results Summary

### All Workflows Status

| Workflow | Trigger | Status | Last Verified |
|----------|---------|--------|---------------|
| `test.yml` | Push/PR | ✅ All jobs pass | Jan 30, 2026 |
| `coverage-report.yml` | Weekly | ✅ Script ready | Jan 30, 2026 |
| `security-scan-pr.yml` | PR | ✅ Tools configured | Jan 30, 2026 |
| `security-scan-weekly.yml` | Weekly | ⚠️ Placeholders | - |
| `performance.yml` | Weekly | ✅ Scripts exist | Jan 30, 2026 |
| `api-docs-validation.yml` | Push/PR | ✅ Scripts exist | Jan 30, 2026 |

### Test Suite Summary

| Test Category | Tests | Passed | Skipped | Status |
|---------------|-------|--------|---------|--------|
| Agno Agents | 19 | 19 | 0 | ✅ |
| MCP Servers | 15 | 15 | 0 | ✅ |
| WebSocket | 13 | 13 | 0 | ✅ |
| Celery Tasks | 21 | 18 | 3 | ✅ |
| Privy Login | 10 | 10 | 0 | ✅ |
| Login Flow | 13 | 13 | 0 | ✅ |
| **Total** | **91** | **88** | **3** | ✅ |

### Files Referenced

```
.github/workflows/
├── api-docs-validation.yml
├── coverage-report.yml
├── performance.yml
├── security-scan-pr.yml
├── security-scan-weekly.yml
└── test.yml

tests/
├── infrastructure/
│   ├── agno/test_agents.py
│   └── mcp/test_mcp_servers.py
├── integration/
│   ├── auth/
│   │   ├── test_login_flow.py
│   │   └── test_privy_login.py
│   └── celery/test_celery_tasks.py
├── performance/
│   ├── benchmark.py
│   ├── locustfile.py
│   └── stress_test.py
└── presentation/
    └── websocket/test_websocket.py

scripts/
├── api_audit/
│   ├── lint_documentation.py
│   ├── validate_api_coverage.py
│   └── validate_typescript.sh
└── check_coverage_trends.py
```

---

## Recommendations

### Immediate Actions
1. ✅ All test.yml jobs are passing
2. ✅ Coverage script created
3. ⚠️ Implement actual security tools in weekly scan

### Future Improvements
1. Add integration tests for more API endpoints
2. Expand type-check coverage to more modules
3. Add contract testing for external APIs
4. Implement actual AI security scanning tools

---

*Document maintained by the Engineering Team*
