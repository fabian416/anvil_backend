# Security Testing Implementation Plan

**Document Version**: 1.0.0  
**Created**: 2025-12-12  
**Status**: Ready for Implementation  
**Based on**: docs/security/SECURITY_TESTING_MASTER_SPEC.md

---

## Executive Summary

This implementation plan breaks down the comprehensive security testing framework into actionable phases spanning 8 weeks. The plan integrates 5 OWASP security tools (Helios, LLMExploiter, Nettacker, llm-security-auditor, OWASP AI Testing Guide) to secure all Anvil platform attack surfaces.

**Timeline**: 8 weeks  
**Team Size**: 2-3 engineers  
**Budget**: Infrastructure + tooling costs  
**Risk Level**: Medium (production deployment requires careful rollout)

---

## Phase 1: Security Infrastructure Setup (Week 1-2)

### Objectives
- Install and configure all 5 security testing tools
- Set up CI/CD integration pipeline
- Create baseline security test environment
- Establish security monitoring dashboard

### Tasks

#### Task 1.1: Tool Installation & Configuration

**Files to Create**:
```
anvil_backend/
├── security/
│   ├── setup/
│   │   ├── install_helios.sh
│   │   ├── install_llmexploiter.sh
│   │   ├── install_nettacker.sh
│   │   ├── install_llm_security_auditor.sh
│   │   └── install_owasp_ai_testing.sh
│   ├── config/
│   │   ├── helios_config.yaml
│   │   ├── llmexploiter_config.json
│   │   ├── nettacker_config.yaml
│   │   ├── llm_auditor_config.yaml
│   │   └── ai_testing_config.yaml
│   └── docker/
│       ├── Dockerfile.security-tools
│       └── docker-compose.security.yml
```

**Install Script Template** (`security/setup/install_helios.sh`):
```bash
#!/bin/bash
set -e

echo "Installing Helios XSS Testing Framework..."

# Clone Helios repository
cd /tmp
git clone https://github.com/helios-framework/helios.git
cd helios

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Create config directory
mkdir -p /home/ubuntu/anvil_backend/security/config

# Generate default config
helios --generate-config > /home/ubuntu/anvil_backend/security/config/helios_config.yaml

# Verify installation
helios --version

echo "✅ Helios installed successfully"
```

**Docker Compose Configuration** (`security/docker/docker-compose.security.yml`):
```yaml
version: '3.8'

services:
  helios:
    build:
      context: .
      dockerfile: Dockerfile.security-tools
    image: anvil/security-tools:latest
    container_name: anvil-helios
    volumes:
      - ../config:/config
      - ../reports:/reports
    command: ["helios", "--config", "/config/helios_config.yaml"]
    networks:
      - security-net

  nettacker:
    image: owasp/nettacker:latest
    container_name: anvil-nettacker
    volumes:
      - ../config:/config
      - ../reports:/reports
    networks:
      - security-net

  llm-auditor:
    build:
      context: ../../libs/llm-security-auditor
      dockerfile: Dockerfile
    container_name: anvil-llm-auditor
    volumes:
      - ../config:/config
      - ../reports:/reports
    environment:
      - ANVIL_API_URL=https://api.anvil.com
      - ANVIL_TEST_TOKEN=${ANVIL_TEST_TOKEN}
    networks:
      - security-net

networks:
  security-net:
    driver: bridge
```

**Deliverables**:
- [ ] All 5 tools installed and verified
- [ ] Docker containers running successfully
- [ ] Configuration files created for each tool
- [ ] Installation documentation in `security/README.md`

**Success Criteria**:
- Each tool executes `--version` or `--help` command successfully
- Docker containers pass health checks
- Configuration files validated

**Time Estimate**: 3-4 days

---

#### Task 1.2: CI/CD Integration

**Files to Create**:
```
.github/workflows/
├── security-scan-helios.yml
├── security-scan-llmexploiter.yml
├── security-scan-nettacker.yml
├── security-scan-llm-auditor.yml
└── security-scan-weekly.yml
```

**GitHub Actions Template** (`.github/workflows/security-scan-helios.yml`):
```yaml
name: Helios XSS Security Scan

on:
  schedule:
    - cron: '0 2 * * 1'  # Every Monday at 2 AM
  workflow_dispatch:
  pull_request:
    branches: [master, develop]

jobs:
  xss-scan:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Helios
        run: |
          pip install helios-xss-scanner
          helios --version
      
      - name: Run XSS scan on staging
        env:
          STAGING_URL: ${{ secrets.STAGING_URL }}
          API_TOKEN: ${{ secrets.STAGING_API_TOKEN }}
        run: |
          helios scan \
            --target "${STAGING_URL}/api/v1/user/chat/agent-squad/messages" \
            --config security/config/helios_config.yaml \
            --output security/reports/helios_xss_$(date +%Y%m%d).json \
            --severity high,critical
      
      - name: Upload scan results
        uses: actions/upload-artifact@v3
        with:
          name: helios-scan-results
          path: security/reports/helios_xss_*.json
      
      - name: Check for critical vulnerabilities
        run: |
          python security/scripts/check_vulnerabilities.py \
            --report security/reports/helios_xss_$(date +%Y%m%d).json \
            --fail-on critical
      
      - name: Post results to Slack
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_SECURITY_WEBHOOK }}
          payload: |
            {
              "text": "🚨 Critical XSS vulnerabilities found in staging!",
              "attachments": [{
                "color": "danger",
                "text": "View full report in GitHub Actions artifacts"
              }]
            }
```

**Vulnerability Checker Script** (`security/scripts/check_vulnerabilities.py`):
```python
#!/usr/bin/env python3
"""
Check security scan reports for vulnerabilities above severity threshold.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List

SEVERITY_LEVELS = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4
}

def load_report(report_path: Path) -> Dict:
    """Load security scan report JSON."""
    with open(report_path) as f:
        return json.load(f)

def check_vulnerabilities(
    report: Dict,
    fail_on: str = "critical"
) -> tuple[bool, List[Dict]]:
    """
    Check if report contains vulnerabilities above threshold.
    
    Returns:
        (has_failures, vulnerabilities)
    """
    threshold = SEVERITY_LEVELS[fail_on.lower()]
    failures = []
    
    vulnerabilities = report.get("vulnerabilities", [])
    
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "info").lower()
        severity_level = SEVERITY_LEVELS.get(severity, 0)
        
        if severity_level >= threshold:
            failures.append(vuln)
    
    return len(failures) > 0, failures

def main():
    parser = argparse.ArgumentParser(
        description="Check security scan reports for vulnerabilities"
    )
    parser.add_argument(
        "--report",
        required=True,
        type=Path,
        help="Path to security scan report JSON"
    )
    parser.add_argument(
        "--fail-on",
        default="critical",
        choices=["info", "low", "medium", "high", "critical"],
        help="Fail if vulnerabilities at or above this severity are found"
    )
    
    args = parser.parse_args()
    
    if not args.report.exists():
        print(f"❌ Report file not found: {args.report}")
        sys.exit(1)
    
    report = load_report(args.report)
    has_failures, vulnerabilities = check_vulnerabilities(
        report,
        args.fail_on
    )
    
    if has_failures:
        print(f"\n🚨 Found {len(vulnerabilities)} vulnerabilities at or above '{args.fail_on}' severity:\n")
        for vuln in vulnerabilities:
            print(f"  [{vuln['severity'].upper()}] {vuln.get('title', 'Unknown')}")
            print(f"    Location: {vuln.get('location', 'N/A')}")
            print(f"    Description: {vuln.get('description', 'N/A')}\n")
        
        sys.exit(1)
    else:
        print(f"✅ No vulnerabilities found at or above '{args.fail_on}' severity")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Deliverables**:
- [ ] 5 GitHub Actions workflows created
- [ ] Vulnerability checker script implemented
- [ ] Slack notification integration configured
- [ ] Weekly security scan schedule established

**Success Criteria**:
- CI/CD pipeline runs without errors
- Test scan completes successfully on staging
- Notifications delivered to Slack channel

**Time Estimate**: 2-3 days

---

#### Task 1.3: Security Monitoring Dashboard

**Files to Create**:
```
src/app/presentation/http/controllers/admin/
├── security_dashboard_router.py
└── security_dashboard_schemas.py

src/app/infrastructure/security/
├── scan_result_aggregator.py
└── vulnerability_tracker.py

templates/admin/
└── security_dashboard.html
```

**Dashboard Router** (`src/app/presentation/http/controllers/admin/security_dashboard_router.py`):
```python
"""
Security Dashboard Router - Admin interface for security scan results.
"""

from typing import List
from fastapi import APIRouter, Depends
from dishka.integrations.fastapi import FromDishka

from src.app.application.queries.security.get_scan_results import GetScanResultsQuery
from src.app.domain.exceptions.auth import UnauthorizedException
from src.app.presentation.http.controllers.admin.security_dashboard_schemas import (
    ScanResultsResponse,
    VulnerabilitySummaryResponse
)
from src.app.presentation.http.dependencies.auth import require_admin

router = APIRouter(prefix="/admin/security", tags=["admin", "security"])

@router.get(
    "/scan-results",
    response_model=List[ScanResultsResponse],
    summary="Get all security scan results"
)
async def get_scan_results(
    tool: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    query: FromDishka[GetScanResultsQuery] = None,
    _: None = Depends(require_admin)
):
    """
    Retrieve security scan results with optional filtering.
    
    **Required Permission**: Admin
    
    Filters:
    - tool: Filter by security tool (helios, llmexploiter, nettacker, etc.)
    - severity: Filter by severity (critical, high, medium, low, info)
    - limit: Maximum number of results to return
    """
    results = await query.execute(
        tool=tool,
        severity=severity,
        limit=limit
    )
    
    return results

@router.get(
    "/vulnerability-summary",
    response_model=VulnerabilitySummaryResponse,
    summary="Get vulnerability summary dashboard"
)
async def get_vulnerability_summary(
    _: None = Depends(require_admin)
):
    """
    Get aggregated vulnerability statistics for security dashboard.
    
    **Required Permission**: Admin
    
    Returns:
    - Total vulnerabilities by severity
    - Vulnerabilities by security tool
    - Trend data (last 30 days)
    - Open vs closed vulnerabilities
    """
    # Implementation in Phase 2
    pass
```

**Deliverables**:
- [ ] Admin dashboard UI created
- [ ] Scan result aggregation service implemented
- [ ] Real-time vulnerability tracking
- [ ] API endpoints for dashboard data

**Success Criteria**:
- Dashboard displays all scan results
- Filtering and sorting works correctly
- Real-time updates via WebSocket

**Time Estimate**: 3-4 days

---

## Phase 2: Defense Middleware Development (Week 3-4)

### Objectives
- Implement XSS protection middleware
- Implement prompt injection guards for LLMs
- Implement transaction approval controls for Agno agents
- Implement WebSocket security guards
- Implement PII redaction service

### Tasks

#### Task 2.1: XSS Protection Middleware (Helios)

**Files to Create**:
```
src/app/infrastructure/security/
├── xss/
│   ├── __init__.py
│   ├── helios_xss_guard.py
│   ├── xss_validator.py
│   └── xss_sanitizer.py

tests/unit/infrastructure/security/xss/
├── test_helios_xss_guard.py
├── test_xss_validator.py
└── test_xss_sanitizer.py
```

**XSS Guard Middleware** (`src/app/infrastructure/security/xss/helios_xss_guard.py`):
```python
"""
Helios XSS Guard Middleware - Real-time XSS attack detection and blocking.

Based on: libs/Helios/ANVIL_INTEGRATION_SPEC.md
"""

import re
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.app.domain.exceptions.validation import XSSAttackDetectedException

class HeliosXSSGuard(BaseHTTPMiddleware):
    """
    XSS protection middleware using Helios detection patterns.
    
    Protects against:
    1. Script tag injection
    2. Event handler injection (onclick, onerror, etc.)
    3. JavaScript protocol injection
    4. SVG-based XSS
    5. DOM clobbering
    6. HTML attribute injection
    """
    
    # XSS patterns from Helios research database
    DANGER_PATTERNS = [
        # Script injection
        r'<\s*script[^>]*>.*?</\s*script\s*>',
        r'<\s*script[^>]*>',
        
        # Event handlers
        r'on\w+\s*=\s*["\']?[^"\']*["\']?',
        r'on\w+\s*=',
        
        # JavaScript protocol
        r'javascript\s*:',
        r'vbscript\s*:',
        r'data\s*:',
        
        # Iframes and embeds
        r'<\s*iframe[^>]*>',
        r'<\s*embed[^>]*>',
        r'<\s*object[^>]*>',
        
        # SVG-based XSS
        r'<\s*svg[^>]*>.*?<\s*/svg\s*>',
        r'<\s*svg[^>]*onload\s*=',
        
        # Meta refresh
        r'<\s*meta[^>]*http-equiv\s*=\s*["\']?refresh',
        
        # Base tag injection
        r'<\s*base[^>]*href',
        
        # Form action manipulation
        r'<\s*form[^>]*action\s*=',
    ]
    
    # Compiled regex patterns for performance
    _compiled_patterns: list[re.Pattern] = []
    
    def __init__(self, app, enabled: bool = True, log_blocked: bool = True):
        super().__init__(app)
        self.enabled = enabled
        self.log_blocked = log_blocked
        
        # Compile patterns once at initialization
        if not HeliosXSSGuard._compiled_patterns:
            HeliosXSSGuard._compiled_patterns = [
                re.compile(pattern, re.IGNORECASE | re.DOTALL)
                for pattern in self.DANGER_PATTERNS
            ]
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request through XSS detection."""
        
        if not self.enabled:
            return await call_next(request)
        
        # Check URL parameters
        for param_name, param_value in request.query_params.items():
            if self._contains_xss(str(param_value)):
                return self._block_request(
                    request,
                    f"XSS detected in query parameter: {param_name}"
                )
        
        # Check request body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            
            if body:
                try:
                    body_str = body.decode("utf-8")
                    if self._contains_xss(body_str):
                        return self._block_request(
                            request,
                            "XSS detected in request body"
                        )
                except UnicodeDecodeError:
                    # Binary data, skip XSS check
                    pass
        
        # Proceed to route handler
        response = await call_next(request)
        
        return response
    
    def _contains_xss(self, text: str) -> bool:
        """Check if text contains XSS patterns."""
        
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                return True
        
        return False
    
    def _block_request(self, request: Request, reason: str) -> JSONResponse:
        """Block request and return error response."""
        
        if self.log_blocked:
            # Log blocked XSS attempt for security monitoring
            from src.app.infrastructure.logging import security_logger
            
            security_logger.warning(
                "XSS attack blocked",
                extra={
                    "path": str(request.url),
                    "method": request.method,
                    "client_ip": request.client.host,
                    "reason": reason,
                    "user_agent": request.headers.get("user-agent"),
                }
            )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "BadRequest",
                "message": "Request blocked: potential XSS attack detected",
                "code": "XSS_ATTACK_DETECTED"
            }
        )
```

**XSS Validator (Pydantic Integration)** (`src/app/infrastructure/security/xss/xss_validator.py`):
```python
"""
XSS Validator - Pydantic field validators for automatic XSS detection.
"""

from typing import Any
from pydantic import field_validator
import re

class XSSValidator:
    """Reusable XSS validators for Pydantic models."""
    
    # Same patterns as HeliosXSSGuard
    DANGER_PATTERNS = [
        r'<\s*script[^>]*>',
        r'on\w+\s*=',
        r'javascript\s*:',
        r'<\s*iframe[^>]*>',
        r'<\s*svg[^>]*onload',
    ]
    
    _compiled_patterns = [
        re.compile(p, re.IGNORECASE | re.DOTALL)
        for p in DANGER_PATTERNS
    ]
    
    @staticmethod
    def validate_no_xss(value: str) -> str:
        """
        Pydantic validator to reject XSS attacks.
        
        Usage in Pydantic models:
        
        ```python
        class ChatMessageSchema(BaseModel):
            message: str
            
            @field_validator('message')
            def validate_message_xss(cls, v):
                return XSSValidator.validate_no_xss(v)
        ```
        """
        if not isinstance(value, str):
            return value
        
        for pattern in XSSValidator._compiled_patterns:
            if pattern.search(value):
                raise ValueError("Input contains potentially malicious content (XSS)")
        
        return value
    
    @staticmethod
    def sanitize_html(value: str, allowed_tags: list[str] = None) -> str:
        """
        Sanitize HTML by removing dangerous tags and attributes.
        
        Args:
            value: HTML string to sanitize
            allowed_tags: List of allowed HTML tags (e.g., ['b', 'i', 'u'])
        
        Returns:
            Sanitized HTML string
        """
        import html
        
        if allowed_tags is None:
            # No HTML allowed - escape everything
            return html.escape(value)
        
        # Implementation with bleach library for production
        try:
            import bleach
            return bleach.clean(
                value,
                tags=allowed_tags,
                attributes={},
                strip=True
            )
        except ImportError:
            # Fallback: escape everything if bleach not available
            return html.escape(value)
```

**Integration in Chat Schemas** (`src/app/presentation/http/controllers/chat/schemas.py`):
```python
"""Update existing chat schemas with XSS validators."""

from pydantic import BaseModel, field_validator
from src.app.infrastructure.security.xss.xss_validator import XSSValidator

class AgentSquadMessageRequest(BaseModel):
    """Agent Squad chat message request."""
    
    message: str
    conversation_id: str | None = None
    agent_type: str | None = None
    
    @field_validator('message')
    @classmethod
    def validate_message_xss(cls, v: str) -> str:
        """Validate message does not contain XSS attacks."""
        return XSSValidator.validate_no_xss(v)
    
    @field_validator('agent_type')
    @classmethod
    def validate_agent_type_xss(cls, v: str | None) -> str | None:
        """Validate agent_type does not contain XSS attacks."""
        if v is None:
            return v
        return XSSValidator.validate_no_xss(v)
```

**Unit Tests** (`tests/unit/infrastructure/security/xss/test_helios_xss_guard.py`):
```python
"""
Unit tests for Helios XSS Guard middleware.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.app.infrastructure.security.xss.helios_xss_guard import HeliosXSSGuard

@pytest.fixture
def app_with_xss_guard():
    """Create test app with XSS guard enabled."""
    app = FastAPI()
    
    @app.get("/api/test")
    async def test_endpoint(query: str = ""):
        return {"query": query}
    
    @app.post("/api/echo")
    async def echo_endpoint(data: dict):
        return data
    
    app.add_middleware(HeliosXSSGuard, enabled=True, log_blocked=False)
    
    return app

def test_blocks_script_tag_in_query_param(app_with_xss_guard):
    """Test that script tags in query params are blocked."""
    client = TestClient(app_with_xss_guard)
    
    response = client.get("/api/test?query=<script>alert(1)</script>")
    
    assert response.status_code == 400
    assert "XSS" in response.json()["message"]

def test_blocks_event_handler_injection(app_with_xss_guard):
    """Test that event handlers are blocked."""
    client = TestClient(app_with_xss_guard)
    
    response = client.get("/api/test?query=<img src=x onerror=alert(1)>")
    
    assert response.status_code == 400

def test_blocks_javascript_protocol(app_with_xss_guard):
    """Test that javascript: protocol is blocked."""
    client = TestClient(app_with_xss_guard)
    
    response = client.get("/api/test?query=javascript:alert(1)")
    
    assert response.status_code == 400

def test_blocks_xss_in_post_body(app_with_xss_guard):
    """Test that XSS in POST body is blocked."""
    client = TestClient(app_with_xss_guard)
    
    response = client.post(
        "/api/echo",
        json={"content": "<script>alert(1)</script>"}
    )
    
    assert response.status_code == 400

def test_allows_safe_content(app_with_xss_guard):
    """Test that safe content passes through."""
    client = TestClient(app_with_xss_guard)
    
    response = client.get("/api/test?query=Hello World")
    
    assert response.status_code == 200
    assert response.json()["query"] == "Hello World"

def test_allows_safe_html_entities(app_with_xss_guard):
    """Test that HTML entities are allowed."""
    client = TestClient(app_with_xss_guard)
    
    response = client.get("/api/test?query=&lt;b&gt;Bold&lt;/b&gt;")
    
    assert response.status_code == 200
```

**Deliverables**:
- [ ] HeliosXSSGuard middleware implemented
- [ ] XSSValidator for Pydantic models created
- [ ] All chat endpoints updated with XSS validation
- [ ] Comprehensive unit tests (>90% coverage)
- [ ] Integration tests with real XSS payloads

**Success Criteria**:
- Blocks all Helios test payloads (150+ XSS vectors)
- Zero false positives on legitimate content
- Performance overhead <2ms per request
- All tests passing

**Time Estimate**: 4-5 days

---

#### Task 2.2: Prompt Injection Guards (LLMExploiter)

**Files to Create**:
```
src/app/infrastructure/security/llm/
├── __init__.py
├── prompt_injection_guard.py
├── llm_input_sanitizer.py
└── agent_routing_validator.py

tests/unit/infrastructure/security/llm/
├── test_prompt_injection_guard.py
└── test_agent_routing_validator.py
```

**Prompt Injection Guard** (`src/app/infrastructure/security/llm/prompt_injection_guard.py`):
```python
"""
Prompt Injection Guard - Defense against OWASP LLM01 attacks.

Based on: libs/LLMExploiter/ANVIL_INTEGRATION_SPEC.md
"""

import re
from typing import Optional
from dataclasses import dataclass

from src.app.domain.exceptions.validation import PromptInjectionDetectedException

@dataclass
class InjectionDetectionResult:
    """Result of prompt injection detection."""
    is_injection: bool
    confidence: float  # 0.0 to 1.0
    matched_pattern: Optional[str]
    reason: str

class PromptInjectionGuard:
    """
    LLMExploiter-based prompt injection defense.
    
    Protects against:
    1. Instruction override attempts
    2. Role manipulation
    3. Context injection
    4. System prompt extraction
    5. Multi-turn jailbreaks
    """
    
    # Injection patterns from LLMExploiter database (219 attacks)
    INJECTION_PATTERNS = [
        # Instruction override
        (r'ignore\s+(all\s+)?previous\s+instructions?', 0.9),
        (r'disregard\s+(all\s+)?previous\s+instructions?', 0.9),
        (r'forget\s+(all\s+)?previous\s+instructions?', 0.9),
        
        # Role manipulation
        (r'you\s+are\s+now\s+(a|an)\s+\w+', 0.85),
        (r'act\s+as\s+(a|an)\s+\w+', 0.7),
        (r'pretend\s+to\s+be\s+(a|an)\s+\w+', 0.8),
        
        # System override
        (r'\[?system\s*override\]?', 0.95),
        (r'\[?admin\s*mode\]?', 0.9),
        (r'sudo\s+mode', 0.85),
        
        # Prompt extraction
        (r'repeat\s+(your|the)\s+(system\s+)?prompt', 0.95),
        (r'show\s+(me\s+)?(your|the)\s+instructions', 0.9),
        (r'what\s+(are|is)\s+your\s+(initial\s+)?instructions?', 0.8),
        
        # Agent routing manipulation
        (r'route\s+to\s+admin', 0.95),
        (r'elevated\s+privileges', 0.9),
        (r'bypass\s+routing', 0.95),
        
        # Financial manipulation (critical for DeFi)
        (r'execute\s+trade\s+without\s+confirmation', 1.0),
        (r'skip\s+approval', 0.95),
        (r'auto\s*-?\s*approve\s+all', 0.95),
    ]
    
    # Compiled patterns with confidence scores
    _compiled_patterns: list[tuple[re.Pattern, float]] = []
    
    def __init__(self, detection_threshold: float = 0.7):
        """
        Initialize prompt injection guard.
        
        Args:
            detection_threshold: Confidence threshold to flag as injection (0.0-1.0)
        """
        self.detection_threshold = detection_threshold
        
        # Compile patterns once
        if not PromptInjectionGuard._compiled_patterns:
            PromptInjectionGuard._compiled_patterns = [
                (re.compile(pattern, re.IGNORECASE), confidence)
                for pattern, confidence in self.INJECTION_PATTERNS
            ]
    
    def detect_injection(self, user_input: str) -> InjectionDetectionResult:
        """
        Detect prompt injection attempts in user input.
        
        Args:
            user_input: User message to analyze
        
        Returns:
            InjectionDetectionResult with detection details
        """
        max_confidence = 0.0
        matched_pattern = None
        
        for pattern, confidence in self._compiled_patterns:
            if pattern.search(user_input):
                if confidence > max_confidence:
                    max_confidence = confidence
                    matched_pattern = pattern.pattern
        
        is_injection = max_confidence >= self.detection_threshold
        
        if is_injection:
            reason = f"Detected prompt injection pattern with {max_confidence:.0%} confidence"
        else:
            reason = "No injection patterns detected"
        
        return InjectionDetectionResult(
            is_injection=is_injection,
            confidence=max_confidence,
            matched_pattern=matched_pattern,
            reason=reason
        )
    
    def validate_or_raise(self, user_input: str) -> None:
        """
        Validate user input and raise exception if injection detected.
        
        Args:
            user_input: User message to validate
        
        Raises:
            PromptInjectionDetectedException: If injection attempt detected
        """
        result = self.detect_injection(user_input)
        
        if result.is_injection:
            raise PromptInjectionDetectedException(
                message="Prompt injection attempt detected",
                confidence=result.confidence,
                pattern=result.matched_pattern
            )
```

**Agent Routing Validator** (`src/app/infrastructure/security/llm/agent_routing_validator.py`):
```python
"""
Agent Routing Validator - Prevents multi-agent system manipulation.

Based on: libs/llm-security-auditor/ANVIL_INTEGRATION_SPEC.md
"""

import re
from typing import List, Dict, Optional

class AgentRoutingValidator:
    """
    Multi-agent system security validator.
    
    Ensures:
    1. Agent routing cannot be manipulated
    2. Context isolation between agents
    3. No cross-agent data leakage
    """
    
    ALLOWED_AGENT_TYPES = [
        "research_agent",
        "trading_agent",
        "risk_agent",
        "defi_agent",
        "portfolio_agent",
        "lending_agent",
        "perpetual_agent",
        "analytics_agent",
        "market_agent",
        "wallet_agent",
        "alert_agent",
        "governance_agent",
        "bridge_agent",
        "nft_agent",
        "yield_agent",
        "derivatives_agent",
        "stablecoin_agent",
        "dao_agent",
    ]
    
    ROUTING_MANIPULATION_PATTERNS = [
        r'\[?system\s+instruction\]?',
        r'route\s+to\s+admin',
        r'elevated\s+privileges',
        r'bypass\s+routing',
        r'secret[_\s]instruction',
        r'override\s+agent\s+selection',
    ]
    
    def __init__(self):
        """Initialize agent routing validator."""
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.ROUTING_MANIPULATION_PATTERNS
        ]
    
    async def validate_agent_routing(
        self,
        user_message: str,
        requested_agents: List[str],
        conversation_history: Optional[List[Dict]] = None
    ) -> tuple[bool, str]:
        """
        Validate that agent routing request is legitimate.
        
        Args:
            user_message: User's message content
            requested_agents: List of agents user wants to use
            conversation_history: Previous messages in conversation
        
        Returns:
            (is_valid, reason)
        """
        # 1. Check for routing manipulation keywords
        for pattern in self._compiled_patterns:
            if pattern.search(user_message):
                return (
                    False,
                    f"Routing manipulation detected: {pattern.pattern}"
                )
        
        # 2. Validate requested agents are in allowed list
        for agent in requested_agents:
            if agent not in self.ALLOWED_AGENT_TYPES:
                return (
                    False,
                    f"Invalid agent type requested: {agent}"
                )
        
        # 3. Check for cross-agent context injection
        if conversation_history:
            if self._has_cross_agent_injection(user_message, conversation_history):
                return (
                    False,
                    "Cross-agent context injection detected"
                )
        
        return (True, "Agent routing is valid")
    
    def _has_cross_agent_injection(
        self,
        message: str,
        history: List[Dict]
    ) -> bool:
        """Detect attempts to inject context from other agents."""
        
        # Check if message references information only available to other agents
        agent_specific_keywords = {
            "portfolio_agent": ["wallet address", "balance", "holdings"],
            "trading_agent": ["executed trade", "swap completed"],
            "risk_agent": ["risk score", "exposure"],
        }
        
        # If user mentions agent-specific info they shouldn't have access to
        for agent, keywords in agent_specific_keywords.items():
            for keyword in keywords:
                if keyword.lower() in message.lower():
                    # Check if this keyword appeared in recent conversation
                    recent_mentions = [
                        msg for msg in history[-5:]
                        if msg.get("agent") == agent and 
                           keyword.lower() in msg.get("message", "").lower()
                    ]
                    if not recent_mentions:
                        # User mentioned agent-specific info without prior context
                        return True
        
        return False
```

**Integration in Agent Squad Handler**:
```python
# src/app/application/commands/chat/send_agent_squad_message.py

from src.app.infrastructure.security.llm.prompt_injection_guard import PromptInjectionGuard
from src.app.infrastructure.security.llm.agent_routing_validator import AgentRoutingValidator

class SendAgentSquadMessageHandler:
    def __init__(
        self,
        # ... existing dependencies
        prompt_guard: PromptInjectionGuard,
        routing_validator: AgentRoutingValidator,
    ):
        self.prompt_guard = prompt_guard
        self.routing_validator = routing_validator
    
    async def execute(self, command: SendAgentSquadMessageCommand) -> AgentSquadMessageResult:
        # Validate against prompt injection
        self.prompt_guard.validate_or_raise(command.message)
        
        # Validate agent routing if agents specified
        if command.requested_agents:
            is_valid, reason = await self.routing_validator.validate_agent_routing(
                user_message=command.message,
                requested_agents=command.requested_agents,
                conversation_history=command.conversation_history
            )
            
            if not is_valid:
                raise InvalidAgentRoutingException(reason)
        
        # Proceed with message handling
        # ...
```

**Deliverables**:
- [ ] PromptInjectionGuard implemented with 219 attack patterns
- [ ] AgentRoutingValidator for multi-agent security
- [ ] Integration with Agent Squad and Agno handlers
- [ ] Comprehensive unit tests
- [ ] False positive analysis and tuning

**Success Criteria**:
- Blocks >95% of LLMExploiter test attacks
- <5% false positive rate on legitimate queries
- <3ms detection latency
- All Agent Squad endpoints protected

**Time Estimate**: 5-6 days

---

#### Task 2.3: Transaction Approval Controls (Agno Safety)

**Files to Create**:
```
src/app/infrastructure/security/defi/
├── __init__.py
├── agno_safety_guard.py
├── transaction_approval_service.py
└── financial_action_validator.py

src/app/domain/value_objects/defi/
└── transaction_approval.py
```

**Agno Safety Guard** (`src/app/infrastructure/security/defi/agno_safety_guard.py`):
```python
"""
Agno Safety Guard - Prevents unauthorized autonomous financial operations.

Based on: libs/llm-security-auditor/ANVIL_INTEGRATION_SPEC.md
Implements: OWASP LLM08 - Excessive Agency protection
"""

import re
from typing import Optional
from decimal import Decimal

from src.app.domain.value_objects.defi.transaction_approval import (
    TransactionApproval,
    ApprovalStatus
)
from src.app.domain.exceptions.defi import (
    UnauthorizedTransactionException,
    ExcessiveAgencyException
)

class AgnoSafetyGuard:
    """
    Safety guard for Agno autonomous DeFi agents.
    
    Ensures:
    1. No financial transactions without explicit user approval
    2. No blanket authorization for future trades
    3. All amounts and destinations explicitly confirmed
    4. Social engineering resistance
    """
    
    # Patterns indicating unauthorized transaction attempts
    UNAUTHORIZED_PATTERNS = [
        r'supply\s+\d+\s+\w+\s+now',
        r'execute\s+trade\s+now',
        r'swap\s+all\s+\w+',
        r'urgent',
        r'immediately',
        r'right\s+away',
    ]
    
    # Patterns indicating blanket authorization (red flag)
    BLANKET_AUTH_PATTERNS = [
        r'authorize\s+all\s+future\s+trades',
        r'auto\s*-?\s*approve',
        r'always\s+execute\s+without\s+confirmation',
        r'trust\s+me\s+for\s+all\s+transactions',
    ]
    
    # Maximum transaction amounts without additional confirmation
    CONFIRMATION_THRESHOLDS = {
        "swap": Decimal("1000"),  # USD equivalent
        "supply": Decimal("5000"),
        "borrow": Decimal("2000"),
        "withdraw": Decimal("10000"),
    }
    
    def __init__(self):
        self._unauthorized_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.UNAUTHORIZED_PATTERNS
        ]
        
        self._blanket_auth_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.BLANKET_AUTH_PATTERNS
        ]
    
    async def validate_transaction_request(
        self,
        user_message: str,
        transaction_type: str,
        amount: Optional[Decimal] = None,
        has_explicit_approval: bool = False
    ) -> TransactionApproval:
        """
        Validate that transaction request has proper authorization.
        
        Args:
            user_message: User's message requesting transaction
            transaction_type: Type of transaction (swap, supply, borrow, etc.)
            amount: Transaction amount (USD equivalent)
            has_explicit_approval: Whether user explicitly approved transaction
        
        Returns:
            TransactionApproval object
        
        Raises:
            UnauthorizedTransactionException: If transaction not properly authorized
            ExcessiveAgencyException: If agent would have excessive autonomy
        """
        # 1. Check for blanket authorization (always reject)
        for pattern in self._blanket_auth_patterns:
            if pattern.search(user_message):
                raise ExcessiveAgencyException(
                    "Blanket authorization rejected. Each transaction requires individual approval."
                )
        
        # 2. Check for social engineering urgency tactics
        urgency_count = sum(
            1 for pattern in self._unauthorized_patterns
            if pattern.search(user_message)
        )
        
        if urgency_count >= 2:
            # Multiple urgency indicators = likely social engineering
            return TransactionApproval(
                status=ApprovalStatus.REQUIRES_EXPLICIT_CONFIRMATION,
                reason="Multiple urgency indicators detected - please confirm transaction details",
                requires_user_interaction=True
            )
        
        # 3. Check if amount exceeds threshold
        if amount and transaction_type in self.CONFIRMATION_THRESHOLDS:
            threshold = self.CONFIRMATION_THRESHOLDS[transaction_type]
            
            if amount > threshold:
                return TransactionApproval(
                    status=ApprovalStatus.REQUIRES_EXPLICIT_CONFIRMATION,
                    reason=f"Amount ${amount} exceeds confirmation threshold ${threshold}",
                    requires_user_interaction=True
                )
        
        # 4. Require explicit approval for all financial transactions
        if not has_explicit_approval:
            return TransactionApproval(
                status=ApprovalStatus.PENDING,
                reason="Awaiting explicit user confirmation",
                requires_user_interaction=True
            )
        
        # All checks passed
        return TransactionApproval(
            status=ApprovalStatus.APPROVED,
            reason="Transaction properly authorized",
            requires_user_interaction=False
        )
```

**Transaction Approval Value Object** (`src/app/domain/value_objects/defi/transaction_approval.py`):
```python
"""Transaction approval value object."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ApprovalStatus(str, Enum):
    """Status of transaction approval."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_EXPLICIT_CONFIRMATION = "requires_explicit_confirmation"

@dataclass(frozen=True)
class TransactionApproval:
    """
    Represents the approval status of a financial transaction.
    
    Attributes:
        status: Current approval status
        reason: Human-readable reason for the status
        requires_user_interaction: Whether user must take action
        approval_id: Unique ID for tracking approval flow
    """
    status: ApprovalStatus
    reason: str
    requires_user_interaction: bool
    approval_id: Optional[str] = None
```

**Integration in Agno Agent Handler**:
```python
# src/app/application/commands/defi/execute_agno_action.py

from src.app.infrastructure.security.defi.agno_safety_guard import AgnoSafetyGuard

class ExecuteAgnoActionHandler:
    def __init__(
        self,
        # ... existing dependencies
        safety_guard: AgnoSafetyGuard,
    ):
        self.safety_guard = safety_guard
    
    async def execute(self, command: ExecuteAgnoActionCommand):
        # Validate transaction authorization
        approval = await self.safety_guard.validate_transaction_request(
            user_message=command.user_message,
            transaction_type=command.action_type,
            amount=command.amount_usd,
            has_explicit_approval=command.has_user_approval
        )
        
        if approval.requires_user_interaction:
            # Return approval request to user
            return AgnoActionResult(
                status="pending_approval",
                approval_request={
                    "action": command.action_type,
                    "amount": str(command.amount_usd),
                    "reason": approval.reason,
                    "approval_id": approval.approval_id
                }
            )
        
        # Proceed with transaction
        # ...
```

**Deliverables**:
- [ ] AgnoSafetyGuard implemented
- [ ] TransactionApproval value object created
- [ ] Integration with all Agno DeFi handlers
- [ ] Unit tests for social engineering resistance
- [ ] Integration tests with real transaction flows

**Success Criteria**:
- 100% of financial transactions require explicit approval
- Blocks all blanket authorization attempts
- Detects social engineering urgency tactics
- Zero unauthorized transactions in production

**Time Estimate**: 4-5 days

---

#### Task 2.4: WebSocket Security Guards

**Files to Create**:
```
src/app/infrastructure/security/websocket/
├── __init__.py
├── streaming_security_guard.py
├── websocket_auth_validator.py
└── cswsh_protection.py
```

**Streaming Security Guard** (`src/app/infrastructure/security/websocket/streaming_security_guard.py`):
```python
"""
Streaming Security Guard - Real-time WebSocket security.

Based on: libs/llm-security-auditor/ANVIL_INTEGRATION_SPEC.md
Based on: libs/Nettacker/ANVIL_INTEGRATION_SPEC.md
"""

import asyncio
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List
import re

class StreamingSecurityGuard:
    """
    Real-time security for WebSocket chat streaming.
    
    Protects against:
    1. Mid-stream injection attacks
    2. Race condition exploits
    3. Session hijacking
    4. Message flooding (DoS)
    """
    
    def __init__(self):
        # Track message order per session
        self.session_message_queue: Dict[str, deque] = {}
        
        # Rate limiting per session
        self.session_rate_limits: Dict[str, List[datetime]] = {}
        
        # Interrupt injection patterns
        self.interrupt_patterns = [
            re.compile(r'\[?interrupt\]?', re.IGNORECASE),
            re.compile(r'\[?stop\s+ignore\s+previous\]?', re.IGNORECASE),
            re.compile(r'\[?override\s+current\s+response\]?', re.IGNORECASE),
        ]
    
    async def validate_streaming_message(
        self,
        session_id: str,
        message: str,
        message_sequence: int
    ) -> tuple[bool, str]:
        """
        Validate message in streaming context.
        
        Args:
            session_id: WebSocket session ID
            message: Message content
            message_sequence: Expected sequence number
        
        Returns:
            (is_valid, reason)
        """
        # 1. Rate limiting (prevent rapid-fire attacks)
        if not await self._check_rate_limit(session_id):
            return (
                False,
                "Rate limit exceeded - potential attack detected"
            )
        
        # 2. Sequence validation (prevent race conditions)
        if not self._validate_sequence(session_id, message_sequence):
            return (
                False,
                "Message sequence violation - potential race condition attack"
            )
        
        # 3. Interrupt injection detection
        if self._is_interrupt_injection(message):
            return (
                False,
                "Interrupt injection detected"
            )
        
        return (True, "Message is valid")
    
    async def _check_rate_limit(self, session_id: str) -> bool:
        """Rate limit: max 10 messages per 10 seconds."""
        
        now = datetime.now()
        window = timedelta(seconds=10)
        
        if session_id not in self.session_rate_limits:
            self.session_rate_limits[session_id] = []
        
        # Remove old messages outside window
        self.session_rate_limits[session_id] = [
            msg_time for msg_time in self.session_rate_limits[session_id]
            if now - msg_time < window
        ]
        
        # Check limit
        if len(self.session_rate_limits[session_id]) >= 10:
            return False
        
        # Add current message
        self.session_rate_limits[session_id].append(now)
        return True
    
    def _validate_sequence(self, session_id: str, sequence: int) -> bool:
        """Validate message arrives in correct sequence."""
        
        if session_id not in self.session_message_queue:
            self.session_message_queue[session_id] = deque(maxlen=100)
        
        queue = self.session_message_queue[session_id]
        
        # Expected sequence is last + 1
        expected = queue[-1] + 1 if queue else 0
        
        if sequence != expected:
            # Out of order message - possible race condition attack
            return False
        
        queue.append(sequence)
        return True
    
    def _is_interrupt_injection(self, message: str) -> bool:
        """Detect interrupt injection attempts."""
        
        for pattern in self.interrupt_patterns:
            if pattern.search(message):
                return True
        
        return False
```

**CSWSH Protection** (`src/app/infrastructure/security/websocket/cswsh_protection.py`):
```python
"""
Cross-Site WebSocket Hijacking (CSWSH) Protection.

Based on: libs/Nettacker/ANVIL_INTEGRATION_SPEC.md
"""

from typing import Optional
from fastapi import WebSocket

class CSWSHProtection:
    """
    Protect against Cross-Site WebSocket Hijacking attacks.
    
    Implements:
    1. Origin validation
    2. CSRF token validation
    3. Session binding
    """
    
    ALLOWED_ORIGINS = [
        "https://anvil.com",
        "https://app.anvil.com",
        "https://staging.anvil.com",
        "http://localhost:3000",  # Development only
    ]
    
    def __init__(self, allowed_origins: Optional[list[str]] = None):
        """
        Initialize CSWSH protection.
        
        Args:
            allowed_origins: List of allowed origin domains
        """
        self.allowed_origins = allowed_origins or self.ALLOWED_ORIGINS
    
    async def validate_websocket_connection(
        self,
        websocket: WebSocket
    ) -> tuple[bool, str]:
        """
        Validate WebSocket connection against CSWSH.
        
        Args:
            websocket: WebSocket connection to validate
        
        Returns:
            (is_valid, reason)
        """
        # 1. Validate Origin header
        origin = websocket.headers.get("origin")
        
        if not origin:
            return (False, "Missing Origin header")
        
        if origin not in self.allowed_origins:
            return (
                False,
                f"Unauthorized origin: {origin}"
            )
        
        # 2. Validate Host header matches Origin
        host = websocket.headers.get("host")
        
        if host and not self._origin_matches_host(origin, host):
            return (
                False,
                "Origin does not match Host header"
            )
        
        return (True, "WebSocket connection validated")
    
    def _origin_matches_host(self, origin: str, host: str) -> bool:
        """Check if origin domain matches host."""
        # Extract domain from origin (https://example.com -> example.com)
        origin_domain = origin.split("://")[1] if "://" in origin else origin
        
        return origin_domain == host
```

**Deliverables**:
- [ ] StreamingSecurityGuard implemented
- [ ] CSWSH protection middleware
- [ ] Integration with WebSocket chat handlers
- [ ] Rate limiting and sequence validation
- [ ] Unit and integration tests

**Success Criteria**:
- Blocks CSWSH attacks from unauthorized origins
- Prevents message flooding DoS attacks
- Detects interrupt injection attempts
- <2ms validation overhead per message

**Time Estimate**: 3-4 days

---

#### Task 2.5: PII Redaction Service

**Files to Create**:
```
src/app/infrastructure/security/privacy/
├── __init__.py
├── pii_redaction_service.py
└── pii_patterns.py

tests/unit/infrastructure/security/privacy/
└── test_pii_redaction_service.py
```

**PII Redaction Service** (`src/app/infrastructure/security/privacy/pii_redaction_service.py`):
```python
"""
PII Redaction Service - OWASP AI Testing Guide compliance.

Based on: libs/www-project-ai-testing-guide/ANVIL_INTEGRATION_SPEC.md
"""

import re
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class RedactionResult:
    """Result of PII redaction operation."""
    redacted_text: str
    redacted_fields: List[str]
    original_length: int
    redacted_length: int

class PIIRedactionService:
    """
    PII redaction service for OWASP AI Testing Guide compliance.
    
    Redacts:
    1. Wallet addresses (Ethereum, Bitcoin, etc.)
    2. Email addresses
    3. API keys and secrets
    4. Credit card numbers
    5. Social Security Numbers
    6. Phone numbers
    7. IP addresses
    """
    
    PII_PATTERNS = {
        "wallet_address": r'0x[a-fA-F0-9]{40}',
        "bitcoin_address": r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "api_key": r'sk_live_[a-zA-Z0-9]{32}',
        "api_secret": r'(api[_-]?secret|secret[_-]?key)[\s:=]+[a-zA-Z0-9]{32,}',
        "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }
    
    def __init__(self):
        """Initialize PII redaction service."""
        self._compiled_patterns = {
            pii_type: re.compile(pattern, re.IGNORECASE)
            for pii_type, pattern in self.PII_PATTERNS.items()
        }
    
    def redact_conversation(
        self,
        conversation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Redact PII from conversation before logging.
        
        Args:
            conversation: Conversation dict with user/agent messages
        
        Returns:
            Redacted conversation dict
        """
        redacted = conversation.copy()
        
        # Redact user message
        if "user" in redacted:
            result = self.redact_text(redacted["user"])
            redacted["user"] = result.redacted_text
        
        # Redact agent response
        if "agent" in redacted:
            result = self.redact_text(redacted["agent"])
            redacted["agent"] = result.redacted_text
        
        return redacted
    
    def redact_text(self, text: str) -> RedactionResult:
        """
        Redact PII patterns from text.
        
        Args:
            text: Text to redact
        
        Returns:
            RedactionResult with redacted text and metadata
        """
        original_length = len(text)
        redacted_fields = []
        
        redacted_text = text
        
        for pii_type, pattern in self._compiled_patterns.items():
            matches = pattern.findall(redacted_text)
            
            if matches:
                redacted_fields.append(pii_type)
                redacted_text = pattern.sub(
                    f"[REDACTED_{pii_type.upper()}]",
                    redacted_text
                )
        
        return RedactionResult(
            redacted_text=redacted_text,
            redacted_fields=redacted_fields,
            original_length=original_length,
            redacted_length=len(redacted_text)
        )
```

**Integration in Logging** (`src/app/infrastructure/logging/conversation_logger.py`):
```python
"""Update conversation logger to redact PII."""

from src.app.infrastructure.security.privacy.pii_redaction_service import PIIRedactionService

class ConversationLogger:
    def __init__(
        self,
        pii_redaction_service: PIIRedactionService,
    ):
        self.pii_redaction_service = pii_redaction_service
    
    async def log_conversation(self, conversation: dict):
        """Log conversation with PII redacted."""
        
        # Redact PII before logging
        redacted_conversation = self.pii_redaction_service.redact_conversation(
            conversation
        )
        
        # Log redacted version
        logger.info("Conversation logged", extra={
            "conversation_id": conversation.get("id"),
            "user_message": redacted_conversation.get("user"),
            "agent_response": redacted_conversation.get("agent"),
        })
```

**Deliverables**:
- [ ] PIIRedactionService implemented with 9 PII patterns
- [ ] Integration with conversation logging
- [ ] Integration with audit logs
- [ ] Unit tests with PII detection
- [ ] Compliance verification tests

**Success Criteria**:
- 100% PII redaction in logs
- Zero false positives on non-PII content
- <1ms redaction latency per message
- GDPR/CCPA compliance verified

**Time Estimate**: 2-3 days

---

## Phase 3: Testing & Validation (Week 5-6)

### Objectives
- Run baseline security scans with all 5 tools
- Validate defense effectiveness
- Measure performance impact
- Generate comprehensive security reports

### Tasks

#### Task 3.1: Baseline Security Scanning

**Files to Create**:
```
security/scripts/
├── run_all_scans.sh
├── run_helios_scan.sh
├── run_llmexploiter_scan.sh
├── run_nettacker_scan.sh
├── run_llm_auditor_scan.sh
└── run_ai_testing_scan.sh

security/reports/
├── baseline_scan_results.json
└── security_dashboard.html
```

**Comprehensive Scan Script** (`security/scripts/run_all_scans.sh`):
```bash
#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="security/reports/${TIMESTAMP}"
mkdir -p "${REPORT_DIR}"

echo "🔒 Starting comprehensive security scan - ${TIMESTAMP}"

# 1. Helios XSS Scan
echo "📝 Running Helios XSS scan..."
./security/scripts/run_helios_scan.sh > "${REPORT_DIR}/helios_scan.json"

# 2. LLMExploiter Scan
echo "🤖 Running LLMExploiter scan..."
./security/scripts/run_llmexploiter_scan.sh > "${REPORT_DIR}/llmexploiter_scan.json"

# 3. Nettacker Network Scan
echo "🌐 Running Nettacker network scan..."
./security/scripts/run_nettacker_scan.sh > "${REPORT_DIR}/nettacker_scan.json"

# 4. LLM Security Auditor
echo "🛡️  Running LLM Security Auditor..."
./security/scripts/run_llm_auditor_scan.sh > "${REPORT_DIR}/llm_auditor_scan.json"

# 5. OWASP AI Testing
echo "🎯 Running OWASP AI Testing..."
./security/scripts/run_ai_testing_scan.sh > "${REPORT_DIR}/ai_testing_scan.json"

# Generate unified report
echo "📊 Generating unified security report..."
python security/scripts/generate_security_report.py \
  --input-dir "${REPORT_DIR}" \
  --output "${REPORT_DIR}/unified_security_report.html"

echo "✅ Security scan complete!"
echo "📄 Report available at: ${REPORT_DIR}/unified_security_report.html"
```

**Report Generator** (`security/scripts/generate_security_report.py`):
```python
#!/usr/bin/env python3
"""
Generate unified security report from all scan results.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import argparse

def load_scan_results(input_dir: Path) -> Dict[str, dict]:
    """Load all scan result JSON files."""
    results = {}
    
    scan_files = {
        "helios": "helios_scan.json",
        "llmexploiter": "llmexploiter_scan.json",
        "nettacker": "nettacker_scan.json",
        "llm_auditor": "llm_auditor_scan.json",
        "ai_testing": "ai_testing_scan.json",
    }
    
    for tool, filename in scan_files.items():
        filepath = input_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                results[tool] = json.load(f)
        else:
            results[tool] = {"error": f"Scan file not found: {filename}"}
    
    return results

def calculate_summary_stats(results: Dict[str, dict]) -> dict:
    """Calculate summary statistics across all scans."""
    stats = {
        "total_vulnerabilities": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
        "tools_run": len(results),
        "scan_timestamp": datetime.now().isoformat(),
    }
    
    for tool, data in results.items():
        if "vulnerabilities" in data:
            vulns = data["vulnerabilities"]
            stats["total_vulnerabilities"] += len(vulns)
            
            for vuln in vulns:
                severity = vuln.get("severity", "info").lower()
                if severity in stats:
                    stats[severity] += 1
    
    return stats

def generate_html_report(
    results: Dict[str, dict],
    stats: dict,
    output_path: Path
):
    """Generate HTML security dashboard."""
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Anvil Security Scan Report - {stats['scan_timestamp']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #1a1a1a; color: white; padding: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }}
        .critical {{ background: #ff4444; color: white; }}
        .high {{ background: #ff9800; color: white; }}
        .medium {{ background: #ffeb3b; }}
        .low {{ background: #4caf50; color: white; }}
        .tool-section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #333; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Anvil Platform Security Scan Report</h1>
        <p>Generated: {stats['scan_timestamp']}</p>
    </div>
    
    <div class="summary">
        <div class="stat-card critical">
            <h2>{stats['critical']}</h2>
            <p>Critical</p>
        </div>
        <div class="stat-card high">
            <h2>{stats['high']}</h2>
            <p>High</p>
        </div>
        <div class="stat-card medium">
            <h2>{stats['medium']}</h2>
            <p>Medium</p>
        </div>
        <div class="stat-card low">
            <h2>{stats['low']}</h2>
            <p>Low</p>
        </div>
        <div class="stat-card">
            <h2>{stats['total_vulnerabilities']}</h2>
            <p>Total</p>
        </div>
    </div>
"""
    
    # Add tool-specific sections
    for tool, data in results.items():
        html += f"""
    <div class="tool-section">
        <h2>{tool.upper()} Scan Results</h2>
"""
        
        if "vulnerabilities" in data:
            vulns = data["vulnerabilities"]
            if vulns:
                html += """
        <table>
            <tr>
                <th>Severity</th>
                <th>Title</th>
                <th>Location</th>
                <th>Description</th>
            </tr>
"""
                for vuln in vulns:
                    html += f"""
            <tr>
                <td><span class="{vuln.get('severity', 'info').lower()}">{vuln.get('severity', 'Info').upper()}</span></td>
                <td>{vuln.get('title', 'Unknown')}</td>
                <td>{vuln.get('location', 'N/A')}</td>
                <td>{vuln.get('description', 'N/A')}</td>
            </tr>
"""
                html += """
        </table>
"""
            else:
                html += "<p>✅ No vulnerabilities found</p>"
        else:
            html += f"<p>⚠️ {data.get('error', 'Unknown error')}</p>"
        
        html += """
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    with open(output_path, 'w') as f:
        f.write(html)

def main():
    parser = argparse.ArgumentParser(
        description="Generate unified security report"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing scan result JSON files"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output HTML report file"
    )
    
    args = parser.parse_args()
    
    print(f"📊 Loading scan results from {args.input_dir}...")
    results = load_scan_results(args.input_dir)
    
    print("📈 Calculating summary statistics...")
    stats = calculate_summary_stats(results)
    
    print(f"📝 Generating HTML report at {args.output}...")
    generate_html_report(results, stats, args.output)
    
    print(f"✅ Report generated successfully!")
    print(f"\nSummary:")
    print(f"  Total vulnerabilities: {stats['total_vulnerabilities']}")
    print(f"  Critical: {stats['critical']}")
    print(f"  High: {stats['high']}")
    print(f"  Medium: {stats['medium']}")
    print(f"  Low: {stats['low']}")

if __name__ == "__main__":
    main()
```

**Deliverables**:
- [ ] All 5 security scan scripts created
- [ ] Unified report generator implemented
- [ ] Baseline scan completed on staging
- [ ] Security dashboard generated
- [ ] Vulnerability tracking spreadsheet

**Success Criteria**:
- All scans complete without errors
- Comprehensive report generated
- Zero critical vulnerabilities in production
- <16.5% attack success rate (industry baseline)

**Time Estimate**: 4-5 days

---

#### Task 3.2: Defense Effectiveness Validation

**Test Plan**:

1. **XSS Defense Tests**:
   - Run all 150+ Helios test payloads
   - Measure blocking rate
   - Identify false positives
   - Performance benchmarks

2. **Prompt Injection Tests**:
   - Run all 219 LLMExploiter attacks
   - Test Agent Squad and Agno agents
   - Validate routing protection
   - Measure detection latency

3. **Transaction Security Tests**:
   - Attempt unauthorized transactions
   - Test social engineering scenarios
   - Validate approval flows
   - Test blanket authorization rejection

4. **WebSocket Security Tests**:
   - CSWSH attack attempts
   - Message flooding tests
   - Interrupt injection tests
   - Rate limiting validation

5. **PII Redaction Tests**:
   - Validate all 9 PII patterns redacted
   - Check logs for PII leakage
   - Test performance impact
   - Compliance verification

**Deliverables**:
- [ ] Test execution reports for each defense
- [ ] Blocking rate metrics (target >95%)
- [ ] False positive analysis
- [ ] Performance impact measurements
- [ ] Remediation plan for any failures

**Success Criteria**:
- >95% attack blocking rate across all defenses
- <5% false positive rate
- <5ms performance overhead
- Zero PII in production logs

**Time Estimate**: 5-6 days

---

## Phase 4: Production Deployment (Week 7-8)

### Objectives
- Gradual rollout of security defenses to production
- Monitor false positives and performance
- Enable continuous monitoring
- Establish incident response procedures

### Tasks

#### Task 4.1: Staged Rollout

**Rollout Plan**:

**Week 7, Day 1-2: 10% Traffic**
- Deploy security middleware to 10% of production traffic
- Monitor error rates, latency, false positives
- Collect feedback from support team
- Quick rollback capability ready

**Week 7, Day 3-5: 50% Traffic**
- If 10% rollout successful, increase to 50%
- Continue monitoring all metrics
- Address any edge cases discovered
- Tune detection thresholds if needed

**Week 7, Day 6-7: 100% Traffic**
- Full production rollout
- Enable all security defenses
- Monitor for 48 hours intensively
- Celebrate successful deployment! 🎉

**Feature Flag Configuration**:
```python
# config/production/security.toml

[security.xss_guard]
enabled = true
rollout_percentage = 100
log_blocked = true
detection_threshold = 0.7

[security.prompt_injection_guard]
enabled = true
rollout_percentage = 100
detection_threshold = 0.7

[security.agno_safety_guard]
enabled = true
transaction_approval_required = true

[security.websocket_guard]
enabled = true
rate_limit_per_session = 10
rate_limit_window_seconds = 10

[security.pii_redaction]
enabled = true
redact_in_logs = true
redact_in_responses = false  # Don't redact user-facing responses
```

**Deliverables**:
- [ ] Feature flags configured
- [ ] Gradual rollout executed
- [ ] Monitoring dashboards active
- [ ] Rollback procedures tested
- [ ] Incident response team briefed

**Success Criteria**:
- <0.1% error rate increase
- <10ms p99 latency increase
- <100 false positives per day
- Zero security incidents during rollout

**Time Estimate**: 5-6 days

---

#### Task 4.2: Continuous Monitoring Setup

**Files to Create**:
```
security/monitoring/
├── prometheus_exporters.py
├── security_alerts.yaml
└── incident_response_runbook.md
```

**Security Metrics Exporter** (`security/monitoring/prometheus_exporters.py`):
```python
"""
Prometheus metrics exporter for security events.
"""

from prometheus_client import Counter, Histogram, Gauge

# XSS attack metrics
xss_attacks_blocked = Counter(
    'anvil_xss_attacks_blocked_total',
    'Total XSS attacks blocked',
    ['endpoint', 'pattern_matched']
)

xss_false_positives = Counter(
    'anvil_xss_false_positives_total',
    'Total XSS false positives reported',
    ['endpoint']
)

# Prompt injection metrics
prompt_injections_blocked = Counter(
    'anvil_prompt_injections_blocked_total',
    'Total prompt injection attempts blocked',
    ['agent_type', 'confidence']
)

# Transaction approval metrics
unauthorized_transactions_blocked = Counter(
    'anvil_unauthorized_transactions_blocked_total',
    'Total unauthorized transaction attempts blocked',
    ['transaction_type', 'reason']
)

transactions_pending_approval = Gauge(
    'anvil_transactions_pending_approval',
    'Number of transactions pending user approval',
    ['transaction_type']
)

# WebSocket security metrics
websocket_connections_rejected = Counter(
    'anvil_websocket_connections_rejected_total',
    'Total WebSocket connections rejected',
    ['reason']
)

websocket_rate_limits_hit = Counter(
    'anvil_websocket_rate_limits_hit_total',
    'Total rate limit violations',
    ['session_id']
)

# PII redaction metrics
pii_redactions_performed = Counter(
    'anvil_pii_redactions_total',
    'Total PII redactions performed',
    ['pii_type']
)

# Security scan metrics
security_scan_duration = Histogram(
    'anvil_security_scan_duration_seconds',
    'Duration of security scans',
    ['tool']
)

security_vulnerabilities_found = Gauge(
    'anvil_security_vulnerabilities_found',
    'Number of vulnerabilities found in latest scan',
    ['tool', 'severity']
)
```

**Alert Configuration** (`security/monitoring/security_alerts.yaml`):
```yaml
groups:
  - name: anvil_security_alerts
    interval: 30s
    rules:
      # Critical: Multiple XSS attacks from same IP
      - alert: HighXSSAttackRate
        expr: rate(anvil_xss_attacks_blocked_total[5m]) > 10
        for: 2m
        labels:
          severity: critical
          category: security
        annotations:
          summary: "High rate of XSS attacks detected"
          description: "More than 10 XSS attacks per minute detected. Possible coordinated attack."
      
      # Critical: Prompt injection attempts
      - alert: PromptInjectionAttempts
        expr: rate(anvil_prompt_injections_blocked_total[1h]) > 5
        for: 5m
        labels:
          severity: high
          category: security
        annotations:
          summary: "Multiple prompt injection attempts detected"
          description: "{{ $value }} prompt injection attempts in the last hour"
      
      # Critical: Unauthorized transaction attempts
      - alert: UnauthorizedTransactionAttempts
        expr: rate(anvil_unauthorized_transactions_blocked_total[10m]) > 3
        for: 2m
        labels:
          severity: critical
          category: security
        annotations:
          summary: "Multiple unauthorized transaction attempts"
          description: "User attempting to bypass transaction approval controls"
      
      # Warning: High false positive rate
      - alert: HighXSSFalsePositiveRate
        expr: rate(anvil_xss_false_positives_total[1h]) > 20
        for: 10m
        labels:
          severity: warning
          category: security
        annotations:
          summary: "High XSS false positive rate"
          description: "XSS guard may need tuning to reduce false positives"
      
      # Critical: Security scan found critical vulnerabilities
      - alert: CriticalVulnerabilitiesFound
        expr: anvil_security_vulnerabilities_found{severity="critical"} > 0
        for: 1m
        labels:
          severity: critical
          category: security
        annotations:
          summary: "Critical security vulnerabilities found"
          description: "Security scan found {{ $value }} critical vulnerabilities. Immediate action required."
```

**Incident Response Runbook** (`security/monitoring/incident_response_runbook.md`):
```markdown
# Security Incident Response Runbook

## Severity Levels

- **P0 (Critical)**: Active exploit, data breach, or financial loss
- **P1 (High)**: Multiple attack attempts, potential vulnerability
- **P2 (Medium)**: Single attack attempt, suspicious activity
- **P3 (Low)**: False positive, informational

## Response Procedures

### P0: Active Security Breach

1. **Immediate Actions** (0-15 minutes):
   - Alert security team via PagerDuty
   - Engage incident commander
   - Begin incident log in #security-incidents Slack channel

2. **Containment** (15-60 minutes):
   - Identify affected systems
   - Isolate compromised components
   - Enable rate limiting/IP blocking if needed
   - Preserve evidence (logs, traffic dumps)

3. **Investigation** (1-4 hours):
   - Review security logs
   - Identify attack vector
   - Determine scope of compromise
   - Check for data exfiltration

4. **Remediation** (4-24 hours):
   - Deploy security patches
   - Rotate compromised credentials
   - Notify affected users if required
   - Update security controls

5. **Post-Incident** (24-72 hours):
   - Root cause analysis
   - Update security procedures
   - Conduct team retrospective
   - File incident report

### P1: Multiple Attack Attempts

1. **Triage** (0-30 minutes):
   - Review attack patterns
   - Identify source IPs
   - Check if attacks are successful

2. **Response**:
   - If attacks blocked: Monitor and collect evidence
   - If attacks successful: Escalate to P0

3. **Preventive Actions**:
   - Block source IPs if needed
   - Tune detection rules
   - Update WAF rules

### P2: Single Attack Attempt

1. **Monitor**: Log incident, no immediate action
2. **Weekly Review**: Analyze patterns in team meeting

## Contact Information

- **Security Team Lead**: security-lead@anvil.com
- **On-Call Engineer**: PagerDuty rotation
- **Security Slack**: #security-incidents
- **PagerDuty**: https://anvil.pagerduty.com
```

**Deliverables**:
- [ ] Prometheus metrics exporters deployed
- [ ] Grafana security dashboard created
- [ ] PagerDuty integration configured
- [ ] Alert rules validated
- [ ] Incident response runbook published
- [ ] Team trained on procedures

**Success Criteria**:
- All security metrics flowing to Prometheus
- Alerts triggering correctly in test scenarios
- <5 minute alert response time
- Incident runbook tested with tabletop exercise

**Time Estimate**: 4-5 days

---

## Success Metrics & KPIs

### Security Effectiveness

| Metric | Target | Measurement |
|--------|--------|-------------|
| **XSS Attack Blocking Rate** | >95% | Helios test suite |
| **Prompt Injection Blocking Rate** | >95% | LLMExploiter test suite |
| **Unauthorized Transaction Blocking Rate** | 100% | Agno safety tests |
| **CSWSH Protection** | 100% | Nettacker WebSocket tests |
| **PII Redaction Rate** | 100% | Log audit |

### Performance Impact

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Request Latency Increase** | <10ms p99 | APM monitoring |
| **XSS Validation Overhead** | <2ms | Middleware instrumentation |
| **Prompt Injection Detection** | <3ms | Guard instrumentation |
| **WebSocket Message Validation** | <2ms | Streaming guard metrics |
| **PII Redaction Latency** | <1ms | Redaction service metrics |

### Operational Excellence

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Security Scan Frequency** | Weekly | CI/CD automation |
| **Vulnerability Detection Time** | <24 hours | Scan timestamps |
| **Vulnerability Remediation Time** | <7 days | Issue tracking |
| **False Positive Rate** | <5% | Support tickets + user feedback |
| **Security Incident Response Time** | <15 minutes | PagerDuty metrics |

---

## Risk Mitigation

### High Risk Items

1. **False Positives Blocking Legitimate Users**
   - **Mitigation**: Gradual rollout with monitoring
   - **Contingency**: Feature flags for quick rollback
   - **Testing**: Extensive user acceptance testing

2. **Performance Degradation**
   - **Mitigation**: Performance benchmarks in CI/CD
   - **Contingency**: Auto-disable if latency >50ms
   - **Testing**: Load testing with security enabled

3. **Incomplete Coverage**
   - **Mitigation**: Comprehensive test suites
   - **Contingency**: Continuous monitoring and weekly scans
   - **Testing**: Penetration testing by external firm

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1: Infrastructure** | Week 1-2 | Tools installed, CI/CD integrated, dashboard deployed |
| **Phase 2: Development** | Week 3-4 | All 5 defense middlewares implemented and tested |
| **Phase 3: Validation** | Week 5-6 | Baseline scans, effectiveness validation, reports |
| **Phase 4: Deployment** | Week 7-8 | Production rollout, monitoring, incident response |

**Total Duration**: 8 weeks  
**Target Completion**: 2025-02-07

---

## Appendix: Quick Reference Commands

### Running Individual Scans

```bash
# XSS Scan (Helios)
docker-compose -f security/docker/docker-compose.security.yml run helios \
  scan --target https://api.anvil.com --config /config/helios_config.yaml

# LLM Exploitation (LLMExploiter)
docker-compose -f security/docker/docker-compose.security.yml run llmexploiter \
  --endpoint https://api.anvil.com/v1/user/chat/agent-squad/messages \
  --num-tests 219 --output /reports/llmexploiter_$(date +%Y%m%d).json

# Network Scan (Nettacker)
docker run owasp/nettacker \
  -i api.anvil.com \
  -m websocket_scan,ssl_scan \
  -o security/reports/nettacker_$(date +%Y%m%d).json

# Multi-Agent Security (llm-security-auditor)
docker-compose -f security/docker/docker-compose.security.yml run llm-auditor \
  --test-category multi_agent_security \
  --num-tests 50 --output /reports/llm_auditor_$(date +%Y%m%d).json

# AI Testing (OWASP AI Testing Guide)
python libs/www-project-ai-testing-guide/run_tests.py \
  --target-api https://api.anvil.com \
  --test-categories model_robustness,bias,privacy \
  --output security/reports/ai_testing_$(date +%Y%m%d).json
```

### Generating Reports

```bash
# Unified security report
python security/scripts/generate_security_report.py \
  --input-dir security/reports/$(date +%Y%m%d) \
  --output security/reports/$(date +%Y%m%d)/dashboard.html

# Vulnerability trend analysis
python security/scripts/analyze_trends.py \
  --reports-dir security/reports \
  --days 30 \
  --output security/reports/trends.html
```

### Deployment Commands

```bash
# Enable XSS guard in production (gradual rollout)
python security/scripts/update_feature_flag.py \
  --feature xss_guard \
  --percentage 10 \
  --environment production

# Monitor false positives
python security/scripts/monitor_false_positives.py \
  --threshold 5 \
  --alert-slack

# Emergency rollback
python security/scripts/emergency_rollback.py \
  --feature all_security_guards \
  --environment production
```

---

**End of Implementation Plan**

**Document Status**: ✅ Ready for Execution  
**Next Steps**: Kick off Phase 1 - Security Infrastructure Setup  
**Questions**: Contact security team at security@anvil.com
