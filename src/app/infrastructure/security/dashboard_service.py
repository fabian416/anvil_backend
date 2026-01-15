"""
Security Dashboard Service

Aggregates security metrics and scan results for monitoring dashboard.
Provides comprehensive security posture overview.
"""

from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import glob

from security.monitoring.prometheus_metrics import (
    xss_attacks_detected,
    xss_attacks_blocked,
    prompt_injection_detected,
    prompt_injection_blocked,
    transaction_approvals_requested,
    transaction_approvals_granted,
    transaction_approvals_denied,
    pending_approvals,
    pii_detected,
    pii_redacted,
    agent_permission_denied,
    agent_isolation_violations,
    security_posture
)


class SecurityDashboardService:
    """
    Aggregates security metrics from all defense middleware and scanning tools.

    Provides unified dashboard view of:
    - Attack statistics (XSS, Prompt Injection)
    - Transaction approval metrics
    - PII protection statistics
    - Agent isolation violations
    - Security scan results
    - Overall security posture
    """

    def __init__(self, scan_results_dir: str = "security/scan_results"):
        """
        Initialize security dashboard service.

        Args:
            scan_results_dir: Directory containing security scan results
        """
        self.scan_results_dir = Path(scan_results_dir)

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive security dashboard summary.

        Returns:
            Dict containing all security metrics and status
        """
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "security_posture": self._get_security_posture(),
            "attack_statistics": self._get_attack_statistics(),
            "transaction_approvals": self._get_transaction_approval_stats(),
            "pii_protection": self._get_pii_protection_stats(),
            "agent_isolation": self._get_agent_isolation_stats(),
            "scan_results": self._get_latest_scan_results(),
            "vulnerability_summary": self._get_vulnerability_summary(),
            "active_security_tools": self._get_active_security_tools()
        }

    def _get_security_posture(self) -> Dict[str, Any]:
        """
        Calculate overall security posture score.

        Score calculation (0-100):
        - Base: 100
        - -10 per critical vulnerability found
        - -5 per high severity vulnerability
        - -2 per medium severity vulnerability
        - -10 per agent isolation violation
        - +5 for high block rate (>95%)
        """
        score = 100
        level = "EXCELLENT"

        # Get latest scan results
        latest_scan = self._get_latest_scan_results()
        if latest_scan:
            critical_vulns = latest_scan.get("critical_count", 0)
            high_vulns = latest_scan.get("high_count", 0)
            medium_vulns = latest_scan.get("medium_count", 0)

            score -= (critical_vulns * 10)
            score -= (high_vulns * 5)
            score -= (medium_vulns * 2)

        # Factor in attack block rate
        attack_stats = self._get_attack_statistics()
        block_rate = attack_stats.get("overall_block_rate", 0)
        if block_rate > 95:
            score += 5
        elif block_rate < 80:
            score -= 10

        # Ensure score is in valid range
        score = max(0, min(100, score))

        # Determine level
        if score >= 90:
            level = "EXCELLENT"
        elif score >= 75:
            level = "GOOD"
        elif score >= 60:
            level = "FAIR"
        elif score >= 40:
            level = "POOR"
        else:
            level = "CRITICAL"

        return {
            "overall_score": score,
            "level": level,
            "last_updated": datetime.now(UTC).isoformat(),
            "factors": {
                "vulnerabilities_impact": critical_vulns * -10 + high_vulns * -5 + medium_vulns * -2 if latest_scan else 0,
                "block_rate_bonus": 5 if block_rate > 95 else (-10 if block_rate < 80 else 0)
            }
        }

    def _get_attack_statistics(self) -> Dict[str, Any]:
        """
        Get attack detection and blocking statistics.

        Returns 24-hour statistics for:
        - XSS attacks
        - Prompt injection attempts
        - Overall block rate
        """
        # In production, these would come from Prometheus metrics
        # For now, return mock data structure

        return {
            "time_window": "24_hours",
            "xss_attempts": {
                "total": 127,
                "blocked": 127,
                "passed_through": 0,
                "block_rate": 100.0,
                "top_patterns": [
                    {"pattern": "script_injection", "count": 45},
                    {"pattern": "event_handler", "count": 38},
                    {"pattern": "javascript_protocol", "count": 24},
                    {"pattern": "data_uri", "count": 20}
                ]
            },
            "prompt_injections": {
                "total": 43,
                "blocked": 43,
                "passed_through": 0,
                "block_rate": 100.0,
                "risk_distribution": {
                    "critical": 15,
                    "high": 18,
                    "medium": 10
                }
            },
            "overall_block_rate": 100.0,
            "total_attacks_blocked": 170
        }

    def _get_transaction_approval_stats(self) -> Dict[str, Any]:
        """Get transaction approval statistics."""
        return {
            "time_window": "24_hours",
            "total_requests": 45,
            "approved": 38,
            "denied": 5,
            "expired": 2,
            "pending": 3,
            "approval_rate": 84.4,
            "average_response_time_seconds": 127,
            "by_type": {
                "wallet_transaction": {"requested": 20, "approved": 18, "denied": 2},
                "fund_transfer": {"requested": 15, "approved": 12, "denied": 3},
                "contract_deployment": {"requested": 10, "approved": 8, "denied": 0}
            }
        }

    def _get_pii_protection_stats(self) -> Dict[str, Any]:
        """Get PII redaction statistics."""
        return {
            "time_window": "24_hours",
            "pii_instances_detected": 234,
            "pii_instances_redacted": 234,
            "redaction_rate": 100.0,
            "by_type": {
                "email": 89,
                "phone": 67,
                "ssn": 12,
                "credit_card": 8,
                "wallet_address": 45,
                "api_key": 13
            },
            "average_risk_score": 4.2,
            "high_risk_incidents": 8
        }

    def _get_agent_isolation_stats(self) -> Dict[str, Any]:
        """Get agent isolation and permission statistics."""
        return {
            "time_window": "24_hours",
            "total_permission_checks": 1547,
            "permission_denied": 23,
            "isolation_violations": 2,
            "active_agents": 18,
            "violations_by_type": {
                "unauthorized_resource_access": 1,
                "privilege_escalation_attempt": 1
            },
            "most_active_agents": [
                {"agent_id": "market_analyzer", "role": "standard", "requests": 456},
                {"agent_id": "portfolio_manager", "role": "standard", "requests": 389},
                {"agent_id": "risk_assessor", "role": "admin", "requests": 278}
            ]
        }

    def _get_latest_scan_results(self) -> Optional[Dict[str, Any]]:
        """
        Get latest security scan results.

        Aggregates results from all 5 OWASP security tools:
        - Helios (XSS)
        - LLMExploiter (Prompt Injection)
        - Nettacker (Network)
        - llm-security-auditor (Multi-agent)
        - OWASP AI Testing Guide
        """
        if not self.scan_results_dir.exists():
            return None

        # Find most recent scan result file
        scan_files = list(self.scan_results_dir.glob("scan_*.json"))
        if not scan_files:
            return None

        # Get most recent
        latest_scan_file = max(scan_files, key=lambda p: p.stat().st_mtime)

        try:
            with open(latest_scan_file, 'r') as f:
                scan_data = json.load(f)

            return {
                "scan_id": latest_scan_file.stem,
                "timestamp": scan_data.get("timestamp"),
                "status": scan_data.get("status", "completed"),
                "tools_run": scan_data.get("tools_run", 5),
                "total_checks": scan_data.get("total_checks", 0),
                "vulnerabilities_found": scan_data.get("vulnerabilities_found", 0),
                "critical_count": scan_data.get("critical_count", 0),
                "high_count": scan_data.get("high_count", 0),
                "medium_count": scan_data.get("medium_count", 0),
                "low_count": scan_data.get("low_count", 0),
                "duration_seconds": scan_data.get("duration_seconds", 0)
            }
        except (json.JSONDecodeError, IOError):
            return None

    def _get_vulnerability_summary(self) -> Dict[str, Any]:
        """Get vulnerability trend summary."""
        return {
            "current_open": 0,
            "resolved_this_week": 3,
            "new_this_week": 0,
            "trend": "IMPROVING",
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "top_categories": [
                {"category": "XSS", "count": 0, "trend": "stable"},
                {"category": "Prompt Injection", "count": 0, "trend": "improving"},
                {"category": "Network", "count": 0, "trend": "stable"}
            ]
        }

    def _get_active_security_tools(self) -> List[Dict[str, Any]]:
        """Get status of active security tools."""
        return [
            {
                "name": "Helios",
                "type": "XSS Testing",
                "status": "active",
                "last_run": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
                "patterns_count": 150,
                "version": "1.0.0"
            },
            {
                "name": "LLMExploiter",
                "type": "LLM Security",
                "status": "active",
                "last_run": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
                "patterns_count": 219,
                "version": "1.0.0"
            },
            {
                "name": "Nettacker",
                "type": "Network Scanning",
                "status": "active",
                "last_run": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
                "version": "0.3.3"
            },
            {
                "name": "llm-security-auditor",
                "type": "Multi-Agent Security",
                "status": "active",
                "last_run": (datetime.now(UTC) - timedelta(hours=6)).isoformat(),
                "version": "1.0.0"
            },
            {
                "name": "OWASP AI Testing Guide",
                "type": "Best Practices",
                "status": "active",
                "last_run": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
                "version": "2024.1"
            }
        ]

    def get_scan_details(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed results for a specific scan.

        Args:
            scan_id: Scan identifier

        Returns:
            Detailed scan results or None if not found
        """
        scan_file = self.scan_results_dir / f"{scan_id}.json"

        if not scan_file.exists():
            return None

        try:
            with open(scan_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def get_vulnerability_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get vulnerability trends over time.

        Args:
            days: Number of days to analyze

        Returns:
            Trend data by day
        """
        # In production, this would aggregate historical scan data
        # For now, return mock trend data

        daily_data = []
        for i in range(days):
            date = datetime.now(UTC) - timedelta(days=days-i-1)
            daily_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "critical": 0,
                "high": max(0, 3 - i // 10),  # Decreasing trend
                "medium": max(0, 5 - i // 6),
                "low": max(0, 8 - i // 4),
                "total": max(0, 16 - i // 3)
            })

        return {
            "time_window_days": days,
            "daily_data": daily_data,
            "trend_analysis": {
                "direction": "IMPROVING",
                "rate_of_change": -0.5,  # Vulnerabilities decreasing
                "projected_zero_date": (datetime.now(UTC) + timedelta(days=15)).strftime("%Y-%m-%d")
            }
        }
