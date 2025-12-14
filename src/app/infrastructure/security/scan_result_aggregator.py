"""
Security Scan Result Aggregator

Aggregates and provides access to security scan results from multiple OWASP tools.
Used by admin dashboard to display security metrics and findings.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ScanStatus(str, Enum):
    """Status of a security scan"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class VulnerabilitySummary:
    """Summary of vulnerabilities by severity"""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0

    @property
    def total(self) -> int:
        return self.critical + self.high + self.medium + self.low + self.info

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class SecurityScanResult:
    """Represents results from a single security scan"""
    scan_id: str
    scan_date: datetime
    status: ScanStatus
    tools_executed: List[str]
    vulnerabilities: VulnerabilitySummary
    reports_path: str
    duration_seconds: Optional[float] = None
    errors: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "scan_id": self.scan_id,
            "scan_date": self.scan_date.isoformat(),
            "status": self.status.value,
            "tools_executed": self.tools_executed,
            "vulnerabilities": self.vulnerabilities.to_dict(),
            "reports_path": self.reports_path,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors or []
        }


@dataclass
class ToolScanResult:
    """Results from a single security tool"""
    tool_name: str
    scan_date: datetime
    status: str
    vulnerabilities_found: int
    report_path: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "scan_date": self.scan_date.isoformat(),
            "status": self.status,
            "vulnerabilities_found": self.vulnerabilities_found,
            "report_path": self.report_path,
            "details": self.details
        }


class ScanResultAggregator:
    """Aggregates security scan results from multiple tools"""

    def __init__(self, reports_base_dir: Path):
        """
        Initialize aggregator.

        Args:
            reports_base_dir: Base directory containing security scan reports
        """
        self.reports_base_dir = reports_base_dir

    def get_latest_scan(self) -> Optional[SecurityScanResult]:
        """Get the most recent security scan result"""
        scan_dirs = self._get_scan_directories()
        if not scan_dirs:
            return None

        latest_scan_dir = scan_dirs[0]
        return self._parse_scan_directory(latest_scan_dir)

    def get_scan_by_id(self, scan_id: str) -> Optional[SecurityScanResult]:
        """Get a specific scan by ID"""
        scan_dir = self.reports_base_dir / scan_id
        if not scan_dir.exists():
            return None

        return self._parse_scan_directory(scan_dir)

    def get_scan_history(self, limit: int = 10) -> List[SecurityScanResult]:
        """Get historical scan results"""
        scan_dirs = self._get_scan_directories()[:limit]
        results = []

        for scan_dir in scan_dirs:
            result = self._parse_scan_directory(scan_dir)
            if result:
                results.append(result)

        return results

    def get_vulnerability_trends(self, days: int = 30) -> Dict[str, List[int]]:
        """
        Get vulnerability count trends over time.

        Returns dict with severity levels as keys and lists of counts as values.
        """
        scan_dirs = self._get_scan_directories()

        trends = {
            "dates": [],
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }

        for scan_dir in scan_dirs[:days]:
            result = self._parse_scan_directory(scan_dir)
            if result:
                trends["dates"].append(result.scan_date.strftime("%Y-%m-%d"))
                trends["critical"].append(result.vulnerabilities.critical)
                trends["high"].append(result.vulnerabilities.high)
                trends["medium"].append(result.vulnerabilities.medium)
                trends["low"].append(result.vulnerabilities.low)

        return trends

    def get_tool_results(self, scan_id: str) -> List[ToolScanResult]:
        """Get individual tool results for a specific scan"""
        scan_dir = self.reports_base_dir / scan_id
        if not scan_dir.exists():
            return []

        tool_results = []

        # Map of report file patterns to tool names
        tool_patterns = {
            "bandit": "Bandit",
            "safety": "Safety",
            "helios": "Helios",
            "llmexploiter": "LLMExploiter",
            "nettacker": "Nettacker"
        }

        for pattern, tool_name in tool_patterns.items():
            report_files = list(scan_dir.glob(f"*{pattern}*.json"))
            if report_files:
                result = self._parse_tool_report(report_files[0], tool_name)
                if result:
                    tool_results.append(result)

        return tool_results

    def _get_scan_directories(self) -> List[Path]:
        """Get all scan directories sorted by date (newest first)"""
        if not self.reports_base_dir.exists():
            return []

        scan_dirs = [
            d for d in self.reports_base_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

        # Sort by modification time (newest first)
        return sorted(scan_dirs, key=lambda x: x.stat().st_mtime, reverse=True)

    def _parse_scan_directory(self, scan_dir: Path) -> Optional[SecurityScanResult]:
        """Parse a scan directory and aggregate results"""
        try:
            scan_id = scan_dir.name
            scan_date = datetime.fromtimestamp(scan_dir.stat().st_mtime)

            # Check for unified report
            unified_report = scan_dir / "unified-report.txt"

            # Aggregate vulnerabilities from all tool reports
            vulnerabilities = VulnerabilitySummary()
            tools_executed = []
            errors = []

            # Parse each tool's JSON report
            for report_file in scan_dir.glob("*.json"):
                tool_name = self._extract_tool_name(report_file.name)
                if tool_name:
                    tools_executed.append(tool_name)
                    try:
                        tool_vulns = self._count_vulnerabilities(report_file, tool_name)
                        vulnerabilities.critical += tool_vulns.get("critical", 0)
                        vulnerabilities.high += tool_vulns.get("high", 0)
                        vulnerabilities.medium += tool_vulns.get("medium", 0)
                        vulnerabilities.low += tool_vulns.get("low", 0)
                        vulnerabilities.info += tool_vulns.get("info", 0)
                    except Exception as e:
                        errors.append(f"Error parsing {tool_name}: {str(e)}")

            # Determine overall status
            if vulnerabilities.critical > 0:
                status = ScanStatus.FAIL
            elif vulnerabilities.high > 0:
                status = ScanStatus.WARNING
            elif errors:
                status = ScanStatus.ERROR
            else:
                status = ScanStatus.PASS

            return SecurityScanResult(
                scan_id=scan_id,
                scan_date=scan_date,
                status=status,
                tools_executed=tools_executed,
                vulnerabilities=vulnerabilities,
                reports_path=str(scan_dir),
                errors=errors if errors else None
            )

        except Exception as e:
            print(f"Error parsing scan directory {scan_dir}: {e}")
            return None

    def _extract_tool_name(self, filename: str) -> Optional[str]:
        """Extract tool name from report filename"""
        tool_map = {
            "bandit": "Bandit",
            "safety": "Safety",
            "helios": "Helios",
            "llmexploiter": "LLMExploiter",
            "nettacker": "Nettacker"
        }

        filename_lower = filename.lower()
        for pattern, name in tool_map.items():
            if pattern in filename_lower:
                return name

        return None

    def _count_vulnerabilities(self, report_file: Path, tool_name: str) -> Dict[str, int]:
        """Count vulnerabilities by severity from a tool report"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        try:
            with open(report_file, 'r') as f:
                data = json.load(f)

            if tool_name == "Bandit":
                for result in data.get("results", []):
                    severity = result.get("issue_severity", "LOW").upper()
                    if severity in counts:
                        counts[severity.lower()] += 1

            elif tool_name == "Safety":
                for vuln in data:
                    cvss = vuln.get("cvss", 0.0)
                    if cvss >= 9.0:
                        counts["critical"] += 1
                    elif cvss >= 7.0:
                        counts["high"] += 1
                    elif cvss >= 4.0:
                        counts["medium"] += 1
                    else:
                        counts["low"] += 1

            elif tool_name in ["Helios", "LLMExploiter", "Nettacker"]:
                for result in data.get("test_results", data.get("scan_results", [])):
                    if result.get("vulnerable", False):
                        severity = result.get("severity", "MEDIUM").lower()
                        if severity in counts:
                            counts[severity] += 1

        except Exception as e:
            print(f"Error counting vulnerabilities in {report_file}: {e}")

        return counts

    def _parse_tool_report(self, report_file: Path, tool_name: str) -> Optional[ToolScanResult]:
        """Parse individual tool report"""
        try:
            with open(report_file, 'r') as f:
                data = json.load(f)

            vuln_counts = self._count_vulnerabilities(report_file, tool_name)
            total_vulns = sum(vuln_counts.values())

            return ToolScanResult(
                tool_name=tool_name,
                scan_date=datetime.fromtimestamp(report_file.stat().st_mtime),
                status="completed",
                vulnerabilities_found=total_vulns,
                report_path=str(report_file),
                details=vuln_counts
            )

        except Exception as e:
            print(f"Error parsing tool report {report_file}: {e}")
            return None
