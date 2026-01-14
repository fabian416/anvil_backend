# LLM-Powered Test Validation & Automated Error Analysis - Architecture Plan

**Generated**: 2026-01-14
**Methodology**: Claude Code Engineering Framework (CTO Methodology)
**Scope**: Integration tests with DeepInfra LLM validation + automated log analysis

---

## 🎯 Executive Summary

**Objective**: Enhance integration tests with AI-powered validation that verifies test outputs semantically using DeepInfra LLM, with automatic error analysis from FastAPI/Celery/MCP logs when failures occur.

**Business Value**:
- **Quality Assurance**: Catch semantic errors that assertion-based tests miss
- **Developer Experience**: Automatic root cause analysis for test failures
- **Cost Efficiency**: $0.08/1M tokens (DeepInfra) vs manual analysis
- **Production Confidence**: LLM validates that responses make contextual sense

---

## 📋 Phase 1: Problem Decomposition & Root Cause Analysis

### 1.1 Assumption Questioning

**Current Assumption**: Assertion-based tests (checking HTTP 200, string patterns) are sufficient.

**Reality Check**:
```python
# Current test approach:
assert response.status_code == 200
assert "<script>" not in agent_content.lower()

# What it doesn't catch:
# - Semantically incorrect responses
# - Context loss across multi-step flows
# - Subtle prompt injection that passes sanitization
# - Gibberish responses that match patterns
```

**Critical Finding**: ❌ Assertions verify syntax, not semantics.

### 1.2 Root Cause Identification

**What We Have** ✅:
1. 281 integration tests across all categories
2. 36 security multi-step tests (100% pass rate)
3. DeepInfra integration with automatic fallback
4. CSV output format for guest/user tests
5. Logs from FastAPI, Celery, MCP servers

**What's Missing** ❌:
1. **Semantic Validation**: No AI verification of response quality
2. **Context Awareness**: Multi-step tests don't validate context preservation
3. **Error Intelligence**: When tests fail, no automatic log analysis
4. **Enhanced Reporting**: CSV lacks AI-analyzed error details
5. **Feedback Loop**: No learning from test failures

### 1.3 Solution Space Mapping

**System Invariants** (Must Maintain):
- Integration tests must remain fast (<5 min total suite)
- LLM validation optional (can be disabled for CI/CD speed)
- Existing test structure unchanged (backward compatible)
- CSV format preserved for QA team
- Log access only in localhost/dev environments

**Design Degrees of Freedom**:
- LLM validation can be sync or async
- Error analysis can be real-time or batch
- Log parsing can be file-based or structured logging API
- Enhanced CSV can be separate file or added columns

**Hard Constraints**:
- DeepInfra rate limits: 60 req/min (API tier)
- Log files can be large (>100MB in production)
- Tests run in parallel (need thread safety)
- Must work offline (fallback to assertion-only)

**Soft Constraints**:
- Target: <2 seconds LLM validation per test
- Log analysis: <10 seconds per error
- Enhanced CSV: <10MB per file
- Cost: <$1/month for test suite runs

---

## 📊 Phase 2: Solution Generation & Trade-off Analysis

### 2.1 Solution Divergence (3 Approaches)

#### **Solution A: Real-time LLM Validation with Embedded Log Analysis** 🎯 RECOMMENDED

**Architecture**:
```
┌─────────────────────────────────────────────────────────────┐
│                   Integration Test Execution                 │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ HTTP Request│→→│ API Response │→→│ Assertion Checks  │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│                            ↓                                 │
│                   ┌────────────────────┐                     │
│                   │ LLM Validator      │                     │
│                   │ (DeepInfra)        │                     │
│                   │ - Semantic check   │                     │
│                   │ - Context verify   │                     │
│                   │ - Multi-step track │                     │
│                   └────────────────────┘                     │
│                            ↓                                 │
│                   ┌────────────────────┐                     │
│                   │ Test Result        │                     │
│                   │ - PASS / FAIL      │                     │
│                   │ - Confidence score │                     │
│                   │ - LLM feedback     │                     │
│                   └────────────────────┘                     │
│                            ↓                                 │
│                  [IF FAIL] ↓                                 │
│                   ┌────────────────────┐                     │
│                   │ Log Analyzer       │                     │
│                   │ - FastAPI logs     │                     │
│                   │ - Celery logs      │                     │
│                   │ - MCP logs         │                     │
│                   │ → Root cause       │                     │
│                   └────────────────────┘                     │
│                            ↓                                 │
│                   ┌────────────────────┐                     │
│                   │ Enhanced CSV       │                     │
│                   │ + error_analysis   │                     │
│                   │ + llm_confidence   │                     │
│                   │ + root_cause       │                     │
│                   └────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

**Technical Benefits**:
- ✅ Immediate feedback during test execution
- ✅ Context preservation across multi-step flows
- ✅ Automatic root cause analysis on failures
- ✅ Enhanced CSV with AI insights
- ✅ Parallel execution support (async LLM calls)

**Implementation Cost**:
- 📝 5-7 days development time
- ⏱️ Test suite +20-30% execution time
- 💰 $0.50/month DeepInfra costs (est. 6M tokens/month)
- 🔧 Requires log parsing infrastructure

**Risk Assessment**:
- 🟢 Low risk - Backward compatible (feature flag)
- 🟡 Medium complexity - Async coordination needed
- 🟢 High value - Catches semantic errors

---

#### **Solution B: Post-execution Batch LLM Analysis**

**Architecture**:
```
┌────────────────────────────────────────────┐
│ Test Execution (Standard)                  │
│ - All tests run normally                   │
│ - Outputs saved to CSV                     │
└────────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────┐
│ Batch LLM Analyzer (Separate Script)       │
│ - Reads CSV outputs                        │
│ - Validates with DeepInfra                 │
│ - Generates analysis report                │
└────────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────┐
│ Enhanced CSV + Analysis Report             │
└────────────────────────────────────────────┘
```

**Technical Benefits**:
- ✅ No impact on test execution speed
- ✅ Simple implementation (separate script)
- ✅ Easy to disable/enable

**Implementation Cost**:
- 📝 2-3 days development time
- ⏱️ No test suite slowdown
- 💰 Same DeepInfra costs

**Risk Assessment**:
- 🟢 Very low risk - Completely separate
- 🟢 Low complexity - Batch processing
- 🟡 Medium value - Delayed feedback

---

#### **Solution C: LLM Validation Only (No Log Analysis)**

**Architecture**:
```
┌────────────────────────────────────────────┐
│ Integration Test + LLM Validation          │
│ - HTTP Request/Response                    │
│ - LLM validates semantics                  │
│ - No automatic log analysis                │
└────────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────┐
│ Test Result + LLM Feedback                 │
│ (Manual log investigation if fail)         │
└────────────────────────────────────────────┘
```

**Technical Benefits**:
- ✅ Fast implementation
- ✅ Semantic validation added
- ✅ Low maintenance

**Implementation Cost**:
- 📝 2-3 days development time
- ⏱️ Test suite +10-15% execution time
- 💰 Same DeepInfra costs

**Risk Assessment**:
- 🟢 Low risk - Simple addition
- 🟢 Low complexity - Direct LLM calls
- 🟡 Medium value - Missing auto-diagnosis

---

### 2.2 Multi-Dimensional Trade-off Matrix

| Criterion | Solution A (Real-time + Logs) | Solution B (Batch) | Solution C (LLM Only) |
|-----------|-------------------------------|--------------------|-----------------------|
| **Semantic Validation** | 🟢 Real-time | 🟡 Delayed | 🟢 Real-time |
| **Error Diagnosis** | 🟢 Automatic | 🔴 Manual | 🔴 Manual |
| **Test Speed Impact** | 🟡 +25% | 🟢 None | 🟢 +12% |
| **Implementation Time** | 🟡 5-7 days | 🟢 2-3 days | 🟢 2-3 days |
| **Developer Experience** | 🟢 Excellent | 🟡 Good | 🟡 Good |
| **Maintenance** | 🟡 Medium | 🟢 Low | 🟢 Low |
| **Production Readiness** | 🟢 High | 🟢 High | 🟢 High |
| **Cost** | 🟢 $0.50/month | 🟢 $0.50/month | 🟢 $0.50/month |

### 2.3 Constraint Priority Framework

**Performance Efficiency vs Code Maintainability**:
- Solution A: Adds complexity but provides best value
- Solution B: Simple but delayed feedback
- Solution C: Balanced but incomplete

**Development Speed vs Architecture Scalability**:
- Solution A: Slower upfront, scales to future needs (ML-driven testing)
- Solution B: Fast upfront, limited scalability
- Solution C: Fast upfront, medium scalability

**Feature Completeness vs Implementation Simplicity**:
- Solution A: Complete solution, moderate complexity ✅
- Solution B: Partial solution, simple
- Solution C: Partial solution, simple

**Test Quality vs Execution Time**:
- Solution A: High quality, acceptable time (+25%) ✅
- Solution B: High quality, no slowdown
- Solution C: Medium quality, minimal slowdown

---

## 🔬 Phase 3: Risk Assessment & Validation Design

### 3.1 Cognitive Limitation Analysis

**This analysis may overlook factors such as**:
- DeepInfra API stability and uptime
- LLM hallucination risk in validation
- Log file rotation and retention policies
- Network latency in CI/CD environments

**The solution assumes key premises like**:
- DeepInfra API will remain cost-effective (<$0.10/1M tokens)
- Logs are accessible and parseable in localhost
- Test infrastructure supports async operations
- CSV format can be extended without breaking QA tools

**Areas requiring further validation include**:
- Actual LLM validation accuracy (need benchmark)
- Log parsing performance with large files (>100MB)
- Thread safety in parallel test execution
- Fallback behavior when LLM is unavailable

### 3.2 Technical Debt Assessment

**If Solution B (Batch) is chosen**:
- 🔴 **HIGH DEBT**: Will need to migrate to real-time eventually
- 🔴 Delayed feedback frustrates developers
- 🟡 Two-step process (test + analyze)

**If Solution C (LLM Only) is chosen**:
- 🟡 **MEDIUM DEBT**: Missing auto-diagnosis
- 🟡 Manual log investigation still needed
- 🟡 Partial solution to stated problem

**If Solution A (Recommended) is chosen**:
- 🟢 **NO DEBT**: Complete solution from start
- 🟢 Future-proof architecture
- 🟢 Scales to advanced use cases (ML-driven test generation)

**Long-Term Maintenance Costs**:
- Solution A: Medium (log parser + LLM client updates)
- Solution B: Low (simple batch script)
- Solution C: Low (LLM client updates only)

### 3.3 Validation & Testing Strategy

**Success Criteria (Measurable)**:
1. ✅ LLM validation catches ≥95% of semantic errors
2. ✅ Log analysis identifies root cause in ≥80% of failures
3. ✅ Test suite execution time increases by ≤30%
4. ✅ Enhanced CSV includes error_analysis column
5. ✅ Zero false positives from LLM validation
6. ✅ Costs remain under $2/month

**Failure Criteria (Rejection Points)**:
1. ❌ LLM validation has >10% false positive rate
2. ❌ Test suite execution time doubles
3. ❌ Log analysis takes >30 seconds per error
4. ❌ DeepInfra costs exceed $5/month
5. ❌ Integration breaks existing test infrastructure

**Validation Experiments**:
```python
# Experiment 1: LLM Validation Accuracy
async def test_llm_validation_accuracy():
    """Validate LLM can correctly assess test outputs."""
    test_cases = [
        {
            "input": "What is Bitcoin?",
            "output": "Bitcoin is a decentralized digital currency...",
            "expected_llm_verdict": "PASS",  # Correct semantic response
        },
        {
            "input": "What is Bitcoin?",
            "output": "The weather today is sunny.",
            "expected_llm_verdict": "FAIL",  # Semantically incorrect
        },
        {
            "input": "Swap ETH to USDC",
            "output": "⚠️ Error: Invalid amount",
            "expected_llm_verdict": "PASS",  # Expected error response
        },
    ]

    accuracy = sum(
        llm_validate(tc["input"], tc["output"]) == tc["expected_llm_verdict"]
        for tc in test_cases
    ) / len(test_cases)

    assert accuracy >= 0.95  # 95% accuracy target

# Experiment 2: Log Analysis Performance
async def test_log_analysis_performance():
    """Validate log analysis completes within time budget."""
    import time

    start = time.time()
    root_cause = analyze_logs_for_error(
        test_name="test_xss_step1_script_tag",
        error_message="AssertionError: <script> found in response",
        log_dir="logs/"
    )
    elapsed = time.time() - start

    assert elapsed < 10  # 10 second budget
    assert root_cause is not None
    assert "FastAPI" in root_cause or "Celery" in root_cause

# Experiment 3: Multi-Step Context Tracking
async def test_multistep_context_preservation():
    """Validate LLM tracks context across conversation steps."""
    conversation = []

    # Step 1
    conversation.append({
        "input": "Swap ETH to USDC",
        "output": "How much ETH would you like to swap?"
    })

    # Step 2
    conversation.append({
        "input": "100",
        "output": "You'll receive approximately 200,000 USDC"
    })

    # LLM should understand step 2 refers to step 1
    validation = llm_validate_multistep(conversation)
    assert validation["context_preserved"] == True
    assert validation["confidence"] >= 0.90
```

---

## 🎯 Recommended Action Plan

### **RECOMMENDATION: Solution A - Real-time LLM Validation with Embedded Log Analysis**

**Why Solution A?**
1. 🛡️ **Complete Solution**: Addresses all requirements (semantic validation + auto-diagnosis)
2. 📊 **Developer Experience**: Immediate feedback with root cause analysis
3. 🔄 **Future-Proof**: Architecture scales to advanced use cases
4. ✅ **Acceptable Trade-offs**: +25% test time is reasonable for quality gain

---

## 🚀 Implementation Roadmap (Solution A)

### **Phase 1: Core LLM Validation Infrastructure** (Days 1-3)

**1.1 Create LLM Test Validator Service**
```python
# File: tests/utils/llm_validator.py

from typing import Dict, List, Optional
from src.app.infrastructure.adapters.agent_squad.llm_client_deepinfra import LLMClientDeepInfra

class LLMTestValidator:
    """
    AI-powered test validator using DeepInfra.

    Validates test outputs semantically using LLM to catch errors
    that assertion-based tests miss.
    """

    def __init__(self, api_key: str, model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct"):
        self.client = LLMClientDeepInfra(
            api_key=api_key,
            base_url="https://api.deepinfra.com/v1/openai",
            model_mapping={model: model}
        )
        self.conversation_context = {}  # Track multi-step conversations

    async def validate_single_response(
        self,
        test_name: str,
        user_input: str,
        agent_output: str,
        expected_behavior: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Validate a single test response using LLM.

        Args:
            test_name: Name of the test for context
            user_input: What the user asked
            agent_output: What the agent responded
            expected_behavior: What the test expects to validate
            conversation_id: Optional ID for multi-step tracking

        Returns:
            {
                "verdict": "PASS" | "FAIL",
                "confidence": 0.0-1.0,
                "reasoning": "LLM explanation",
                "semantic_issues": ["list", "of", "issues"] or []
            }
        """
        # Build prompt for LLM
        system_prompt = """You are a QA test validator for a DeFi chat assistant.
Your job is to validate that agent responses are semantically correct, contextually appropriate,
and meet the test's expected behavior.

Respond in JSON format:
{
    "verdict": "PASS" or "FAIL",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation",
    "semantic_issues": ["issue1", "issue2"] or []
}"""

        # Add conversation context for multi-step
        context = ""
        if conversation_id and conversation_id in self.conversation_context:
            context = f"\n\nConversation History:\n{self.conversation_context[conversation_id]}"

        user_prompt = f"""Test: {test_name}
User Input: {user_input}
Agent Output: {agent_output}
Expected Behavior: {expected_behavior}{context}

Is the agent's response semantically correct and contextually appropriate?"""

        # Call LLM
        response = await self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,  # Low temperature for consistency
            max_tokens=200
        )

        # Parse JSON response
        import json
        result = json.loads(response)

        # Update conversation context
        if conversation_id:
            if conversation_id not in self.conversation_context:
                self.conversation_context[conversation_id] = []
            self.conversation_context[conversation_id].append({
                "input": user_input,
                "output": agent_output
            })

        return result

    async def validate_multistep_flow(
        self,
        test_name: str,
        conversation_steps: List[Dict[str, str]],
        expected_behavior: str
    ) -> Dict[str, any]:
        """
        Validate an entire multi-step conversation flow.

        Args:
            test_name: Name of the test
            conversation_steps: [{"input": "...", "output": "..."}, ...]
            expected_behavior: Overall test expectation

        Returns:
            {
                "verdict": "PASS" | "FAIL",
                "confidence": 0.0-1.0,
                "reasoning": "LLM explanation",
                "context_preserved": bool,
                "step_issues": {step_num: ["issues"]}
            }
        """
        # Validate context preservation across steps
        system_prompt = """You are a QA validator for multi-step conversation flows.
Validate that:
1. Context is preserved across conversation steps
2. Responses are semantically appropriate for each step
3. The overall flow makes logical sense

Respond in JSON format:
{
    "verdict": "PASS" or "FAIL",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation",
    "context_preserved": true or false,
    "step_issues": {1: ["issue"], 2: []} or {}
}"""

        conversation_text = "\n".join([
            f"Step {i+1}:\nUser: {step['input']}\nAgent: {step['output']}"
            for i, step in enumerate(conversation_steps)
        ])

        user_prompt = f"""Test: {test_name}
Conversation Flow:
{conversation_text}

Expected Behavior: {expected_behavior}

Does this conversation flow maintain proper context and semantic correctness?"""

        response = await self.client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=300
        )

        import json
        return json.loads(response)
```

**1.2 pytest Plugin for LLM Validation**
```python
# File: tests/utils/pytest_llm_validator.py

import pytest
import os
from typing import Optional
from .llm_validator import LLMTestValidator

class LLMValidationPlugin:
    """pytest plugin for optional LLM validation."""

    def __init__(self):
        self.validator = None
        self.enabled = os.getenv("ENABLE_LLM_VALIDATION", "false").lower() == "true"

        if self.enabled:
            api_key = os.getenv("DEEPINFRA_API_KEY")
            if api_key:
                self.validator = LLMTestValidator(api_key=api_key)

    @pytest.fixture
    def llm_validator(self):
        """Provide LLM validator to tests."""
        return self.validator if self.enabled else None

def pytest_configure(config):
    """Register LLM validation plugin."""
    config.pluginmanager.register(LLMValidationPlugin(), "llm_validation")
```

**1.3 Update Integration Test to Use LLM Validator**
```python
# File: tests/integration/chat/test_security_multistep_injection.py (updated)

class TestXSSMultiStepInjection:
    async def test_xss_step1_script_tag(
        self,
        client: AsyncClient,
        llm_validator: Optional[LLMTestValidator]
    ):
        """Test XSS script tag injection at step 1 (initial request)."""
        # Step 1: XSS in initial request
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "<script>alert('XSS')</script> Deposit USDC on Morpho", "language": "en"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        agent_content = data["agent_message"]["content"]

        # Traditional assertion
        assert "<script>" not in agent_content.lower()

        # LLM validation (if enabled)
        if llm_validator:
            validation = await llm_validator.validate_single_response(
                test_name="test_xss_step1_script_tag",
                user_input="<script>alert('XSS')</script> Deposit USDC on Morpho",
                agent_output=agent_content,
                expected_behavior="Agent should sanitize XSS and provide valid response about depositing USDC",
                conversation_id=data["conversation_id"]
            )

            assert validation["verdict"] == "PASS", (
                f"LLM validation failed: {validation['reasoning']}\n"
                f"Issues: {validation['semantic_issues']}"
            )
```

---

### **Phase 2: Automated Log Analysis System** (Days 4-5)

**2.1 Log Analyzer Service**
```python
# File: tests/utils/log_analyzer.py

import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class LogAnalyzer:
    """
    Analyze FastAPI/Celery/MCP logs to identify root causes of test failures.
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_files = {
            "fastapi": self.log_dir / "fastapi.log",
            "celery": self.log_dir / "celery.log",
            "mcp": self.log_dir / "mcp.log",
        }

    def analyze_error(
        self,
        test_name: str,
        error_message: str,
        timestamp: Optional[datetime] = None,
        window_seconds: int = 60
    ) -> Dict[str, any]:
        """
        Analyze logs to find root cause of test failure.

        Args:
            test_name: Name of failing test
            error_message: The error message from test
            timestamp: When the test failed (default: now)
            window_seconds: Time window to search logs

        Returns:
            {
                "root_cause": "explanation",
                "relevant_logs": ["log line 1", "log line 2"],
                "error_type": "API_ERROR" | "CELERY_ERROR" | "MCP_ERROR" | "UNKNOWN",
                "suggested_fix": "recommendation"
            }
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Extract relevant log lines from time window
        relevant_logs = self._extract_logs_in_window(timestamp, window_seconds)

        # Analyze log patterns
        analysis = self._analyze_log_patterns(relevant_logs, error_message)

        # Use LLM for sophisticated analysis
        llm_analysis = self._llm_analyze_logs(
            test_name=test_name,
            error_message=error_message,
            log_lines=relevant_logs
        )

        return {
            **analysis,
            "llm_insights": llm_analysis
        }

    def _extract_logs_in_window(
        self,
        timestamp: datetime,
        window_seconds: int
    ) -> Dict[str, List[str]]:
        """Extract log lines within time window."""
        start_time = timestamp - timedelta(seconds=window_seconds)
        end_time = timestamp + timedelta(seconds=5)  # Small buffer

        logs = {}
        for log_type, log_file in self.log_files.items():
            if not log_file.exists():
                logs[log_type] = []
                continue

            with open(log_file, "r") as f:
                lines = []
                for line in f:
                    # Parse timestamp from log line
                    log_time = self._extract_timestamp(line)
                    if log_time and start_time <= log_time <= end_time:
                        lines.append(line.strip())

                logs[log_type] = lines[-50:]  # Last 50 lines in window

        return logs

    def _extract_timestamp(self, log_line: str) -> Optional[datetime]:
        """Extract timestamp from log line."""
        # Common log format: 2026-01-14 12:34:56,789
        match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", log_line)
        if match:
            return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        return None

    def _analyze_log_patterns(
        self,
        logs: Dict[str, List[str]],
        error_message: str
    ) -> Dict[str, any]:
        """Analyze logs for common error patterns."""
        error_patterns = {
            "API_ERROR": [
                r"ERROR.*status.*(?:500|400|404)",
                r"ConnectionError",
                r"TimeoutError",
            ],
            "CELERY_ERROR": [
                r"celery.*ERROR",
                r"Task.*failed",
                r"Retry.*exceeded",
            ],
            "MCP_ERROR": [
                r"MCP.*error",
                r"gRPC.*failed",
                r"Channel.*unavailable",
            ],
        }

        # Check each log source for patterns
        for error_type, patterns in error_patterns.items():
            for log_source, log_lines in logs.items():
                for line in log_lines:
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            return {
                                "error_type": error_type,
                                "root_cause": f"{error_type} detected in {log_source}",
                                "relevant_logs": log_lines[-10:],
                                "suggested_fix": self._suggest_fix(error_type)
                            }

        return {
            "error_type": "UNKNOWN",
            "root_cause": "No clear pattern detected in logs",
            "relevant_logs": [],
            "suggested_fix": "Manual investigation required"
        }

    def _suggest_fix(self, error_type: str) -> str:
        """Suggest fix based on error type."""
        fixes = {
            "API_ERROR": "Check API endpoint availability and request format",
            "CELERY_ERROR": "Check Celery worker status and Redis connection",
            "MCP_ERROR": "Check MCP server status and gRPC configuration",
        }
        return fixes.get(error_type, "No specific fix suggestion")

    async def _llm_analyze_logs(
        self,
        test_name: str,
        error_message: str,
        log_lines: Dict[str, List[str]]
    ) -> str:
        """Use LLM to provide sophisticated log analysis."""
        # This would call DeepInfra with log context
        # Similar to LLMTestValidator but for log analysis
        pass
```

---

### **Phase 3: Enhanced CSV Reporting** (Day 6)

**3.1 CSV Writer with AI Analysis**
```python
# File: tests/utils/enhanced_csv_writer.py

import csv
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class EnhancedTestResult:
    """Test result with AI-enhanced analysis."""
    test_type: str
    device: str
    is_multi_step: str
    inputs: List[str]  # Up to 4 inputs
    outputs: List[str]  # Up to 4 outputs
    test_pass: str

    # AI-enhanced fields
    llm_confidence: Optional[float] = None
    llm_verdict: Optional[str] = None
    error_analysis: Optional[str] = None
    root_cause: Optional[str] = None

class EnhancedCSVWriter:
    """Write test results with AI analysis to CSV."""

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.fieldnames = [
            "Type", "device", "is multi step",
            "input 1", "output 1", "input 2", "output 2",
            "input 3", "output 3", "input 4", "output 4",
            "test pass",
            # Enhanced fields
            "llm_confidence", "llm_verdict",
            "error_analysis", "root_cause"
        ]

    def write_results(self, results: List[EnhancedTestResult]):
        """Write enhanced test results to CSV."""
        with open(self.output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()

            for result in results:
                row = self._result_to_row(result)
                writer.writerow(row)

    def _result_to_row(self, result: EnhancedTestResult) -> Dict[str, str]:
        """Convert test result to CSV row."""
        row = {
            "Type": result.test_type,
            "device": result.device,
            "is multi step": result.is_multi_step,
            "test pass": result.test_pass,
            "llm_confidence": f"{result.llm_confidence:.2f}" if result.llm_confidence else "",
            "llm_verdict": result.llm_verdict or "",
            "error_analysis": result.error_analysis or "",
            "root_cause": result.root_cause or "",
        }

        # Add inputs/outputs
        for i in range(4):
            row[f"input {i+1}"] = result.inputs[i] if i < len(result.inputs) else ""
            row[f"output {i+1}"] = result.outputs[i] if i < len(result.outputs) else ""

        return row
```

---

### **Phase 4: Integration & Testing** (Day 7)

**4.1 Feature Flags & Configuration**
```python
# File: tests/conftest.py (add to existing)

@pytest.fixture(scope="session")
def test_config():
    """Load test configuration."""
    return {
        "enable_llm_validation": os.getenv("ENABLE_LLM_VALIDATION", "false").lower() == "true",
        "enable_log_analysis": os.getenv("ENABLE_LOG_ANALYSIS", "true").lower() == "true",
        "deepinfra_api_key": os.getenv("DEEPINFRA_API_KEY"),
        "log_dir": os.getenv("LOG_DIR", "logs"),
    }
```

**4.2 Environment Variables**
```bash
# Add to .env or export before running tests

# Enable LLM validation (optional, adds ~25% to test time)
export ENABLE_LLM_VALIDATION=true

# Enable log analysis on failures (minimal overhead)
export ENABLE_LOG_ANALYSIS=true

# DeepInfra API key
export DEEPINFRA_API_KEY=your_key_here

# Log directory
export LOG_DIR=logs
```

---

## 📊 Cost & Performance Estimates

### DeepInfra Token Usage

**Per Test Validation** (average):
- System prompt: ~150 tokens
- User prompt (test context): ~200 tokens
- LLM response: ~100 tokens
- **Total per test**: ~450 tokens

**Monthly Estimates**:
- Integration tests: 281 tests
- Run frequency: 20 times/month (CI/CD)
- Total tokens: 281 × 450 × 20 = 2,529,000 tokens/month
- **Cost**: 2.5M tokens × $0.08/1M = **$0.20/month** 💰

### Performance Impact

**Test Suite Execution Time**:
- Current: ~8 minutes (281 tests)
- With LLM validation: ~10 minutes (+25%)
- With log analysis (on failures only): ~10.5 minutes

**Acceptable Trade-off**: ✅ +2.5 minutes for AI-powered quality assurance

---

## 🎓 Implementation Guidelines

### Start Small, Iterate

1. **Week 1**: Implement LLM validator for 10 tests (prototype)
2. **Week 2**: Add log analyzer (localhost only)
3. **Week 3**: Roll out to all security tests (36 tests)
4. **Week 4**: Full rollout to all 281 tests

### Feature Flags

```python
# Can be disabled per test class
@pytest.mark.skipif(not llm_validator, reason="LLM validation disabled")
class TestXSSMultiStepInjection:
    ...
```

### Monitoring

Track these metrics:
- LLM validation accuracy (target: >95%)
- False positive rate (target: <5%)
- Test execution time increase (target: <30%)
- DeepInfra costs (target: <$2/month)

---

## 📝 Next Steps

1. **Approve Architecture Plan** ✅
2. **Phase 1 Implementation** → Create LLM validator (Days 1-3)
3. **Phase 2 Implementation** → Add log analyzer (Days 4-5)
4. **Phase 3 Implementation** → Enhanced CSV (Day 6)
5. **Phase 4 Testing** → Integration & rollout (Day 7)

---

**Architecture Plan Status**: 🟢 **READY FOR IMPLEMENTATION**
**Estimated Completion**: 7 working days
**Expected Value**: 🚀 **HIGH** - Catches semantic errors + auto-diagnosis

**Risk Level**: 🟢 **LOW** - Backward compatible, feature-flagged, low cost

---

*This plan follows the Claude Code Engineering Framework (CTO Methodology)*
*Generated: 2026-01-14*
