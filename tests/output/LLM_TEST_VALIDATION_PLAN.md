# LLM-Powered Test Validation & CSV Report Generation Plan

**Date**: 2026-01-15
**Methodology**: MIT Systems Thinking + Stanford Design Thinking (from cto.md)
**Objective**: Automated test validation with intelligent log analysis and CSV reporting

---

## 📚 Phase 1: Problem Decomposition & Root Cause Analysis

### 1.1 Actual Requirements

**Core Problem**:
We need an intelligent system that:
1. Runs all integration tests (guest, user, multi-step flows)
2. Uses LLM to analyze test outcomes intelligently
3. Parses FastAPI/Celery logs for failures and warnings
4. Generates structured CSV reports in appropriate directories
5. Handles complex multi-step flows with context awareness

**Unverified Assumptions to Question**:
- ❓ Are all tests currently executable without manual setup?
- ❓ Is the database running and accessible?
- ❓ Are FastAPI/Celery services logging to accessible files?
- ❓ What CSV format do we need? (check existing files)
- ❓ Should LLM validate response quality or just pass/fail?

**Root Cause Identification**:
- **Why do tests fail?** Multiple reasons: timeouts, missing services, assertion errors, validation errors
- **Why manual analysis is needed?** Logs are verbose, failures require context
- **Why CSV output?** Structured data for analysis, reporting, and tracking

### 1.2 Constraint Analysis

**Hard Constraints** (Cannot change):
- Tests require running FastAPI server
- Multi-step flows take 5-15 seconds each
- LLM context window limits (200K tokens)
- Database must be initialized

**Soft Constraints** (Can optimize):
- Test execution time (can run in parallel)
- Log parsing complexity (can batch/summarize)
- CSV format (can enhance structure)
- Failure analysis depth (can configure)

**System Invariants**:
- Test structure: Given/When/Then
- HTTP status codes: 200 = success, 4xx = client error, 5xx = server error
- CSV columns: test_id, category, input, output, status, error_message

---

## 🎯 Phase 2: Solution Generation & Trade-off Analysis

### Solution A: Pure pytest-json-report Approach

**Architecture**:
```
pytest --json-report → JSON file → Python parser → CSV generator
```

**Benefits**:
- ✅ Fast execution (no LLM overhead)
- ✅ Structured data (JSON format)
- ✅ Reliable parsing

**Drawbacks**:
- ❌ No intelligent failure analysis
- ❌ Basic error messages only
- ❌ No log context extraction

**Cost**: Low (no LLM API calls)
**Risk**: Low
**Value**: Medium

---

### Solution B: Pure LLM Log Analysis Approach

**Architecture**:
```
pytest → Raw logs → LLM analysis → Structured extraction → CSV
```

**Benefits**:
- ✅ Intelligent failure analysis
- ✅ Context-aware error interpretation
- ✅ Natural language summaries

**Drawbacks**:
- ❌ Slow (LLM API calls)
- ❌ Expensive (token costs)
- ❌ Less reliable (LLM hallucinations)

**Cost**: High ($5-10 for 424 tests)
**Risk**: Medium (API failures, rate limits)
**Value**: High

---

### Solution C: Hybrid Intelligent Approach (RECOMMENDED) ⭐

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Test Execution Layer                     │
├─────────────────────────────────────────────────────────────┤
│  pytest → JSON report + Console logs                        │
│  Captures: status codes, timings, assertions, logs          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Intelligent Analysis Layer (LLM)               │
├─────────────────────────────────────────────────────────────┤
│  For FAILED tests only:                                     │
│  • Extract relevant log context                             │
│  • Analyze error patterns                                   │
│  • Categorize failure types                                 │
│  • Generate actionable recommendations                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                CSV Generation Layer                         │
├─────────────────────────────────────────────────────────────┤
│  Generate structured CSVs:                                  │
│  • tests/output/guest/llm_validated_results.csv            │
│  • tests/output/user/llm_validated_results.csv             │
│  • tests/output/advanced/llm_validated_results.csv         │
└─────────────────────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Fast for passing tests (no LLM)
- ✅ Intelligent analysis for failures
- ✅ Cost-effective (LLM only for failures)
- ✅ Structured + natural language output

**Drawbacks**:
- ⚠️ Moderate complexity
- ⚠️ Requires log file access

**Cost**: Medium ($1-3 for typical runs)
**Risk**: Low
**Value**: Very High

**Trade-off Decision**: Solution C (Hybrid) wins
- **Why**: Optimizes for common case (most tests pass)
- **Cost**: Only analyze failures with LLM
- **Value**: Intelligent insights where they matter

---

## 🔬 Phase 3: Risk Assessment & Validation Design

### 3.1 Cognitive Limitation Analysis

**This analysis may overlook**:
- Network latency affecting test performance
- Race conditions in concurrent tests
- External service dependencies
- Memory/CPU constraints on test machine

**The solution assumes**:
- FastAPI server can be started programmatically
- Database is accessible or can be started
- Logs are written to accessible files
- Tests are idempotent (can be re-run)

**Areas requiring further validation**:
- LLM token costs for large log files
- Test execution time (may take 30-60 minutes for 424 tests)
- Log file sizes and rotation
- CSV format compatibility with existing tooling

### 3.2 Technical Debt Assessment

**Rapid Implementation Compromises**:
- Sequential test execution (not fully parallel)
- Basic log parsing (not streaming)
- Single LLM model (no fallback)

**Long-term Maintenance Costs**:
- LLM API changes requiring updates
- Log format changes from FastAPI/Celery
- CSV schema evolution

**Mitigation**:
- Modular design for easy updates
- Configuration-driven LLM selection
- Backward-compatible CSV format

### 3.3 Validation Strategy

**Success Criteria**:
- ✅ 95%+ tests execute successfully
- ✅ All failures have LLM analysis
- ✅ CSV files generated in correct directories
- ✅ Execution completes in < 60 minutes

**Failure Detection**:
- Test timeout: 30s per test
- Server failure: Check process status
- Database failure: Connection test
- LLM failure: Graceful degradation

**Rollback Mechanism**:
- Save intermediate results
- Resume from last successful batch
- Export partial CSV if interrupted

---

## 🚀 Phase 4: Implementation Architecture

### 4.1 System Components

**Component 1: Test Orchestrator**
```python
class TestOrchestrator:
    """Manages test execution and result collection."""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.server_manager = ServerManager()
        self.test_runner = PytestRunner()
        self.log_parser = LogParser()

    async def execute_test_suite(self, mode: str):
        """Execute tests and collect results."""
        # 1. Start services (DB, FastAPI, Celery)
        # 2. Run pytest with JSON reporting
        # 3. Collect logs
        # 4. Return structured results
```

**Component 2: LLM Failure Analyzer**
```python
class LLMFailureAnalyzer:
    """Analyzes test failures using LLM."""

    async def analyze_failure(self, test_result: dict, logs: str):
        """
        Given:
        - Test metadata (name, status, duration)
        - Relevant log excerpt

        Returns:
        - Failure category (timeout, assertion, server_error)
        - Root cause analysis
        - Recommended fix
        - Severity (critical, major, minor)
        """
```

**Component 3: CSV Report Generator**
```python
class CSVReportGenerator:
    """Generates structured CSV reports."""

    def generate_report(self, results: list[dict], output_path: str):
        """
        Columns:
        - test_id
        - category (guest, user, advanced)
        - scenario
        - input
        - expected_output
        - actual_output
        - status (PASS, FAIL, SKIP, ERROR)
        - execution_time_ms
        - error_message
        - llm_analysis (if failed)
        - severity (if failed)
        - recommendations (if failed)
        """
```

### 4.2 Workflow Protocol

**Phase 1: Environment Setup** (5 minutes)
```bash
# Start required services
make up.db              # PostgreSQL
alembic upgrade head    # Apply migrations
make start &            # FastAPI server
make celery.worker &    # Celery worker
```

**Phase 2: Test Execution** (30-45 minutes)
```bash
# Run tests with JSON reporting
pytest tests/integration/chat/test_guest_chat_comprehensive.py \
    --json-report \
    --json-report-file=tests/output/guest/test_results.json \
    -v --tb=short \
    2>&1 | tee tests/output/guest/pytest_output.log
```

**Phase 3: LLM Analysis** (5-10 minutes)
```python
# For each failed test:
# 1. Extract test context from JSON
# 2. Find relevant log section
# 3. Send to LLM for analysis
# 4. Parse LLM response into structured data
```

**Phase 4: CSV Generation** (1 minute)
```python
# Generate CSV reports
# - tests/output/guest/llm_validated_results.csv
# - tests/output/user/llm_validated_results.csv
# - tests/output/advanced/llm_validated_results.csv
```

---

## 📊 CSV Schema Definition

### Standard CSV Format

Based on existing `tests/output/user/week1_8_input_output.csv`:

```csv
test_id,category,scenario,input,expected_output,actual_output,status,execution_time_ms,error_message,llm_analysis,severity,recommendations,notes
guest_001,guest_chat,price_query,"What is Bitcoin?",Price information,Price: $43,500,PASS,2340,,,,
user_042,authenticated_chat,sentiment,"ETH sentiment?",Sentiment data,500 Internal Server,FAIL,5120,"Connection timeout","Database connection pool exhausted. Celery worker unable to connect to PostgreSQL.",critical,"1. Increase DB pool size 2. Check Celery worker health 3. Review connection leak",
multilang_015,multilanguage,french_price,"Prix du BTC?",French response,French response,PASS,3200,,,,
```

**Enhanced Columns**:
- `llm_analysis`: Natural language explanation of failure (only for FAIL/ERROR)
- `severity`: critical, major, minor, info
- `recommendations`: Actionable steps to fix (numbered list)

---

## 🛠️ Implementation Script

### File: `scripts/llm_test_validator.py`

```python
#!/usr/bin/env python3
"""
LLM-Powered Test Validation & CSV Report Generator

Uses hybrid approach:
- pytest-json-report for structure
- LLM for intelligent failure analysis
- CSV output for reporting

Usage:
    python scripts/llm_test_validator.py --mode guest
    python scripts/llm_test_validator.py --mode user
    python scripts/llm_test_validator.py --mode advanced
    python scripts/llm_test_validator.py --mode all
"""

import asyncio
import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# LLM client (using Vertex AI from existing setup)
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel


@dataclass
class TestResult:
    """Test result with LLM analysis."""
    test_id: str
    category: str
    scenario: str
    input: str
    expected_output: str
    actual_output: str
    status: str  # PASS, FAIL, SKIP, ERROR
    execution_time_ms: int
    error_message: str
    llm_analysis: str = ""
    severity: str = ""
    recommendations: str = ""
    notes: str = ""


class LLMTestValidator:
    """Validates tests using LLM for intelligent analysis."""

    def __init__(self, mode: str):
        self.mode = mode
        self.project_root = Path(__file__).parent.parent
        self.output_dir = self.project_root / "tests" / "output"

        # Initialize LLM
        aiplatform.init(project="your-project-id", location="us-central1")
        self.llm = GenerativeModel("gemini-2.0-flash-exp")

    async def run_tests(self, test_type: str) -> list[TestResult]:
        """Run tests and collect results."""
        print(f"\\n🧪 Running {test_type} tests...")

        # Determine test files
        test_files = self._get_test_files(test_type)

        results = []
        for test_name, test_file in test_files.items():
            print(f"\\n📋 Executing: {test_name}")

            # Run pytest with JSON report
            json_file = self.output_dir / test_type / f"{test_name}_results.json"
            log_file = self.output_dir / test_type / f"{test_name}_output.log"

            cmd = [
                "pytest",
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={json_file}",
            ]

            # Execute and capture logs
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            # Save logs
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "w") as f:
                f.write(result.stdout)
                f.write(result.stderr)

            # Parse JSON report
            if json_file.exists():
                test_results = await self._parse_json_report(
                    json_file, log_file, test_name
                )
                results.extend(test_results)

        return results

    async def _parse_json_report(
        self,
        json_file: Path,
        log_file: Path,
        test_name: str,
    ) -> list[TestResult]:
        """Parse pytest JSON report and analyze failures."""
        with open(json_file) as f:
            report = json.load(f)

        with open(log_file) as f:
            logs = f.read()

        results = []
        for idx, test in enumerate(report.get("tests", []), 1):
            # Extract test info
            test_id = f"{test_name}_{idx:03d}"
            nodeid = test.get("nodeid", "")
            outcome = test.get("outcome", "unknown").upper()
            duration_ms = int(test.get("duration", 0) * 1000)

            # Map outcome to status
            status_map = {
                "PASSED": "PASS",
                "FAILED": "FAIL",
                "SKIPPED": "SKIP",
                "ERROR": "ERROR",
            }
            status = status_map.get(outcome, "UNKNOWN")

            # Extract scenario name
            scenario = nodeid.split("::")[-1] if "::" in nodeid else nodeid

            # Basic error message
            error_message = ""
            if status in ["FAIL", "ERROR"]:
                call = test.get("call", {})
                longrepr = call.get("longrepr", "")
                if isinstance(longrepr, str):
                    error_message = longrepr[:500]  # Truncate

            # Create base result
            result = TestResult(
                test_id=test_id,
                category=self._categorize_test(scenario),
                scenario=scenario,
                input="See test code",  # Could parse from test
                expected_output="See test assertions",
                actual_output="See test logs",
                status=status,
                execution_time_ms=duration_ms,
                error_message=error_message,
            )

            # LLM analysis for failures
            if status in ["FAIL", "ERROR"]:
                await self._analyze_failure_with_llm(result, test, logs)

            results.append(result)

        return results

    async def _analyze_failure_with_llm(
        self,
        result: TestResult,
        test_data: dict,
        full_logs: str,
    ):
        """Use LLM to analyze test failure."""
        # Extract relevant log section
        test_name = result.scenario
        log_excerpt = self._extract_relevant_logs(full_logs, test_name)

        # Construct LLM prompt
        prompt = f"""Analyze this test failure and provide insights:

Test: {result.scenario}
Status: {result.status}
Error Message: {result.error_message}

Relevant Logs:
{log_excerpt}

Please provide:
1. Root cause analysis (2-3 sentences)
2. Severity level (critical, major, minor)
3. Recommended fixes (numbered list, max 3 items)

Format your response as JSON:
{{
    "analysis": "...",
    "severity": "...",
    "recommendations": ["...", "..."]
}}
"""

        try:
            # Call LLM
            response = await self.llm.generate_content_async(prompt)
            llm_output = response.text

            # Parse JSON response
            llm_data = json.loads(llm_output)

            result.llm_analysis = llm_data.get("analysis", "")
            result.severity = llm_data.get("severity", "unknown")
            result.recommendations = " | ".join(llm_data.get("recommendations", []))

        except Exception as e:
            result.llm_analysis = f"LLM analysis failed: {str(e)}"
            result.severity = "unknown"

    def _extract_relevant_logs(self, logs: str, test_name: str) -> str:
        """Extract relevant log section for a test."""
        lines = logs.split("\\n")
        relevant = []

        # Find test start
        in_test = False
        for line in lines:
            if test_name in line:
                in_test = True
            elif in_test and ("PASSED" in line or "FAILED" in line):
                break

            if in_test:
                relevant.append(line)

        # Limit to 1000 chars for LLM
        excerpt = "\\n".join(relevant)
        return excerpt[:1000]

    def _categorize_test(self, test_name: str) -> str:
        """Categorize test based on name."""
        name_lower = test_name.lower()

        if "guest" in name_lower:
            return "guest_chat"
        elif "french" in name_lower or "spanish" in name_lower or "multilang" in name_lower:
            return "multilanguage"
        elif "performance" in name_lower or "concurrent" in name_lower:
            return "performance"
        elif "security" in name_lower or "xss" in name_lower:
            return "security"
        elif "cross" in name_lower and "chain" in name_lower:
            return "cross_chain"
        else:
            return "authenticated_chat"

    def _get_test_files(self, test_type: str) -> dict[str, str]:
        """Get test files for a test type."""
        files = {
            "guest": {
                "comprehensive": "tests/integration/chat/test_guest_chat_comprehensive.py",
            },
            "user": {
                "comprehensive": "tests/integration/chat/test_authenticated_chat_comprehensive.py",
                "integration": "tests/integration/chat/test_authenticated_chat_integration.py",
            },
            "advanced": {
                "multilanguage": "tests/integration/chat/test_multilanguage_comprehensive.py",
                "performance": "tests/integration/performance/test_performance_comprehensive.py",
                "security": "tests/integration/security/test_security_comprehensive.py",
                "cross_chain": "tests/integration/chat/test_cross_chain_comprehensive.py",
            },
        }
        return files.get(test_type, {})

    def export_to_csv(self, results: list[TestResult], output_file: Path):
        """Export results to CSV."""
        print(f"\\n📊 Exporting {len(results)} results to {output_file}")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="") as f:
            fieldnames = [
                "test_id",
                "category",
                "scenario",
                "input",
                "expected_output",
                "actual_output",
                "status",
                "execution_time_ms",
                "error_message",
                "llm_analysis",
                "severity",
                "recommendations",
                "notes",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                writer.writerow({
                    "test_id": result.test_id,
                    "category": result.category,
                    "scenario": result.scenario,
                    "input": result.input,
                    "expected_output": result.expected_output,
                    "actual_output": result.actual_output,
                    "status": result.status,
                    "execution_time_ms": result.execution_time_ms,
                    "error_message": result.error_message,
                    "llm_analysis": result.llm_analysis,
                    "severity": result.severity,
                    "recommendations": result.recommendations,
                    "notes": result.notes,
                })

        # Print summary
        total = len(results)
        passed = sum(1 for r in results if r.status == "PASS")
        failed = sum(1 for r in results if r.status == "FAIL")
        errors = sum(1 for r in results if r.status == "ERROR")

        print(f"\\n✅ PASS: {passed}/{total} ({passed/total*100:.1f}%)")
        print(f"❌ FAIL: {failed}/{total} ({failed/total*100:.1f}%)")
        print(f"⚠️  ERROR: {errors}/{total}")

    async def run(self):
        """Execute test validation workflow."""
        print("\\n" + "="*80)
        print("LLM-Powered Test Validator")
        print("="*80)
        print(f"Mode: {self.mode.upper()}")
        print(f"Timestamp: {datetime.now().isoformat()}")

        if self.mode in ["guest", "all"]:
            results = await self.run_tests("guest")
            output_file = self.output_dir / "guest" / "llm_validated_results.csv"
            self.export_to_csv(results, output_file)

        if self.mode in ["user", "all"]:
            results = await self.run_tests("user")
            output_file = self.output_dir / "user" / "llm_validated_results.csv"
            self.export_to_csv(results, output_file)

        if self.mode in ["advanced", "all"]:
            results = await self.run_tests("advanced")
            output_file = self.output_dir / "advanced" / "llm_validated_results.csv"
            self.export_to_csv(results, output_file)

        print("\\n✅ Test validation complete!")


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="LLM-powered test validator with CSV reports"
    )
    parser.add_argument(
        "--mode",
        choices=["guest", "user", "advanced", "all"],
        default="all",
        help="Test mode",
    )

    args = parser.parse_args()

    validator = LLMTestValidator(mode=args.mode)
    await validator.run()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📋 Execution Checklist

### Pre-Execution Validation

- [ ] Database running: `make up.db`
- [ ] Migrations applied: `alembic upgrade head`
- [ ] FastAPI server: `make start`
- [ ] Celery worker: `make celery.worker`
- [ ] Vertex AI credentials configured
- [ ] Output directories exist: `tests/output/{guest,user,advanced}/`

### Execution Steps

```bash
# 1. Setup environment
cd /home/ubuntu/anvil_backend
source .venv/bin/activate

# 2. Start services
make up.db
alembic upgrade head
make start &         # Background
make celery.worker & # Background

# 3. Run LLM test validator
python scripts/llm_test_validator.py --mode all

# 4. Review CSVs
ls -lh tests/output/guest/llm_validated_results.csv
ls -lh tests/output/user/llm_validated_results.csv
ls -lh tests/output/advanced/llm_validated_results.csv
```

### Post-Execution Validation

- [ ] CSV files generated in correct directories
- [ ] All tests have status (PASS/FAIL/SKIP/ERROR)
- [ ] Failed tests have LLM analysis
- [ ] Severity assigned to failures
- [ ] Recommendations provided
- [ ] Execution time < 60 minutes

---

## 🎯 Success Metrics

**Quantitative**:
- ✅ Test completion rate: >95%
- ✅ LLM analysis coverage: 100% of failures
- ✅ CSV export success: 100%
- ✅ Execution time: <60 minutes

**Qualitative**:
- ✅ Actionable failure insights
- ✅ Clear severity classification
- ✅ Useful recommendations
- ✅ Maintainable architecture

---

## 🔮 Future Enhancements

1. **Real-time Dashboard**: Web UI showing test progress
2. **Trend Analysis**: Compare results over time
3. **Auto-Remediation**: Suggest code fixes, not just analysis
4. **Parallel Execution**: Run tests concurrently for speed
5. **Flaky Test Detection**: Identify non-deterministic tests

---

**Methodology Applied**: ✅ MIT Systems Thinking + Stanford Design Thinking
**Status**: Ready for implementation
**Estimated Implementation Time**: 4-6 hours
**Expected ROI**: High (automates manual test analysis)

---

**Created by**: Claude Code using CTO Methodology
**Date**: 2026-01-15
