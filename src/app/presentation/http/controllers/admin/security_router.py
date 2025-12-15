"""
Security Dashboard API Router

Provides endpoints for security monitoring and dashboard.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from src.app.infrastructure.security.dashboard_service import SecurityDashboardService


router = APIRouter(prefix="/security", tags=["admin-security"])

# Initialize dashboard service
dashboard_service = SecurityDashboardService()


@router.get("/dashboard")
async def get_security_dashboard():
    """
    Get comprehensive security dashboard summary.

    Returns complete security posture including:
    - Attack statistics (XSS, Prompt Injection)
    - Transaction approval metrics
    - PII protection stats
    - Agent isolation violations
    - Latest scan results
    - Overall security score

    **Example Response:**
    ```json
    {
      "timestamp": "2025-12-15T10:30:00Z",
      "security_posture": {
        "overall_score": 92,
        "level": "EXCELLENT"
      },
      "attack_statistics": {
        "xss_attempts": {"total": 127, "blocked": 127},
        "prompt_injections": {"total": 43, "blocked": 43}
      }
    }
    ```
    """
    try:
        return dashboard_service.get_dashboard_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@router.get("/scans/latest")
async def get_latest_scan():
    """
    Get latest security scan results.

    Returns most recent scan from weekly automated security scans
    (Monday 2AM UTC via GitHub Actions).

    **Scan Tools:**
    - Helios (XSS testing)
    - LLMExploiter (Prompt injection)
    - Nettacker (Network scanning)
    - llm-security-auditor (Multi-agent)
    - OWASP AI Testing Guide
    """
    try:
        scan_results = dashboard_service._get_latest_scan_results()
        if not scan_results:
            raise HTTPException(status_code=404, detail="No scan results found")
        return scan_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan retrieval error: {str(e)}")


@router.get("/scans/{scan_id}")
async def get_scan_details(scan_id: str):
    """
    Get detailed results for a specific security scan.

    **Parameters:**
    - scan_id: Scan identifier (e.g., "scan_20251215_020000")
    """
    try:
        scan_details = dashboard_service.get_scan_details(scan_id)
        if not scan_details:
            raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
        return scan_details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan details error: {str(e)}")


@router.get("/trends")
async def get_vulnerability_trends(
    days: int = Query(default=30, ge=1, le=90, description="Number of days to analyze")
):
    """
    Get vulnerability trends over time.

    Shows how vulnerabilities have changed over the specified time period.

    **Parameters:**
    - days: Number of days to analyze (1-90, default: 30)

    **Returns:**
    - Daily vulnerability counts by severity
    - Trend analysis (improving/degrading)
    - Projected resolution timeline
    """
    try:
        return dashboard_service.get_vulnerability_trends(days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trends error: {str(e)}")


@router.get("/posture")
async def get_security_posture():
    """
    Get current security posture score and level.

    **Score Calculation (0-100):**
    - Base: 100
    - -10 per critical vulnerability
    - -5 per high severity vulnerability
    - -2 per medium severity vulnerability
    - +5 for high block rate (>95%)

    **Levels:**
    - EXCELLENT: 90-100
    - GOOD: 75-89
    - FAIR: 60-74
    - POOR: 40-59
    - CRITICAL: 0-39
    """
    try:
        return dashboard_service._get_security_posture()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Posture error: {str(e)}")


@router.get("/attacks")
async def get_attack_statistics():
    """
    Get 24-hour attack detection and blocking statistics.

    **Metrics:**
    - XSS attempts (150+ patterns detected)
    - Prompt injection attempts (219 patterns detected)
    - Block rates
    - Top attack patterns
    """
    try:
        return dashboard_service._get_attack_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Attack stats error: {str(e)}")


@router.get("/approvals")
async def get_transaction_approvals():
    """
    Get transaction approval statistics.

    Shows metrics for human-in-the-loop approval system
    (OWASP LLM08 protection).

    **Metrics:**
    - Total approval requests
    - Approved vs denied
    - Pending approvals
    - Average response time
    - Breakdown by transaction type
    """
    try:
        return dashboard_service._get_transaction_approval_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval stats error: {str(e)}")


@router.get("/pii-protection")
async def get_pii_protection():
    """
    Get PII detection and redaction statistics.

    **Protected PII Types:**
    - Email addresses
    - Phone numbers
    - SSN
    - Credit cards
    - Wallet addresses
    - API keys
    - JWT tokens

    **Compliance:** GDPR, CCPA
    """
    try:
        return dashboard_service._get_pii_protection_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PII stats error: {str(e)}")


@router.get("/agent-isolation")
async def get_agent_isolation():
    """
    Get agent isolation and permission statistics.

    Shows multi-agent system security metrics:
    - Permission checks
    - Access denials
    - Isolation violations
    - Active agents by role
    """
    try:
        return dashboard_service._get_agent_isolation_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent stats error: {str(e)}")


@router.get("/tools")
async def get_active_tools():
    """
    Get status of active security tools.

    **5 OWASP Security Tools:**
    1. Helios - XSS testing (150+ patterns)
    2. LLMExploiter - LLM security (219 patterns)
    3. Nettacker - Network scanning
    4. llm-security-auditor - Multi-agent security
    5. OWASP AI Testing Guide - Best practices

    Shows last run time, version, and status for each tool.
    """
    try:
        return dashboard_service._get_active_security_tools()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tools status error: {str(e)}")
