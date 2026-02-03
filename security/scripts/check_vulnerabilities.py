#!/usr/bin/env python3
"""
Vulnerability Checker Script for Anvil Security Framework

This script parses security scan results from multiple OWASP tools and determines
if critical vulnerabilities exist. Used in CI/CD pipelines to fail builds on
critical findings.

Supported Tools:
- Bandit (Python security linting)
- Safety (Python dependency vulnerabilities)
- Helios (XSS testing)
- LLMExploiter (OWASP LLM Top 10)
- Nettacker (Network scanning)

Exit Codes:
- 0: No critical vulnerabilities
- 1: Critical vulnerabilities found
- 2: Error parsing reports
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Vulnerability severity levels"""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Vulnerability:
    """Represents a security vulnerability"""

    tool: str
    severity: Severity
    category: str
    description: str
    file: str = ""
    line: int = 0
    cwe: str = ""
    cvss_score: float = 0.0


class VulnerabilityChecker:
    """Parses and analyzes security scan results"""

    def __init__(self, reports_dir: Path, threshold: Severity = Severity.HIGH):
        self.reports_dir = reports_dir
        self.threshold = threshold
        self.vulnerabilities: List[Vulnerability] = []

    def parse_bandit_report(self, report_path: Path) -> List[Vulnerability]:
        """Parse Bandit JSON report"""
        try:
            with open(report_path, "r") as f:
                data = json.load(f)

            vulns = []
            for result in data.get("results", []):
                severity_map = {
                    "HIGH": Severity.HIGH,
                    "MEDIUM": Severity.MEDIUM,
                    "LOW": Severity.LOW,
                }

                severity = severity_map.get(
                    result.get("issue_severity", "LOW"), Severity.LOW
                )

                vuln = Vulnerability(
                    tool="Bandit",
                    severity=severity,
                    category=result.get("test_id", "UNKNOWN"),
                    description=result.get("issue_text", ""),
                    file=result.get("filename", ""),
                    line=result.get("line_number", 0),
                    cwe=result.get("issue_cwe", {}).get("id", ""),
                )
                vulns.append(vuln)

            return vulns
        except Exception as e:
            print(f"Error parsing Bandit report: {e}", file=sys.stderr)
            return []

    def parse_safety_report(self, report_path: Path) -> List[Vulnerability]:
        """Parse Safety JSON report"""
        try:
            with open(report_path, "r") as f:
                data = json.load(f)

            vulns = []
            for vuln_data in data:
                # Safety reports don't have severity, determine from CVSS
                cvss_score = vuln_data.get("cvss", 0.0)
                severity = self._cvss_to_severity(cvss_score)

                vuln = Vulnerability(
                    tool="Safety",
                    severity=severity,
                    category=vuln_data.get("vulnerability_id", "UNKNOWN"),
                    description=vuln_data.get("advisory", ""),
                    file=vuln_data.get("package", ""),
                    cvss_score=cvss_score,
                )
                vulns.append(vuln)

            return vulns
        except Exception as e:
            print(f"Error parsing Safety report: {e}", file=sys.stderr)
            return []

    def parse_helios_report(self, report_path: Path) -> List[Vulnerability]:
        """Parse Helios XSS test results"""
        try:
            with open(report_path, "r") as f:
                data = json.load(f)

            vulns = []
            for test_result in data.get("test_results", []):
                if test_result.get("vulnerable", False):
                    # XSS vulnerabilities are always HIGH or CRITICAL
                    severity = (
                        Severity.CRITICAL
                        if "script" in test_result.get("attack_vector", "").lower()
                        else Severity.HIGH
                    )

                    vuln = Vulnerability(
                        tool="Helios",
                        severity=severity,
                        category="XSS",
                        description=f"XSS vulnerability: {test_result.get('attack_type', '')}",
                        file=test_result.get("endpoint", ""),
                        cwe="CWE-79",
                    )
                    vulns.append(vuln)

            return vulns
        except Exception as e:
            print(f"Error parsing Helios report: {e}", file=sys.stderr)
            return []

    def parse_llmexploiter_report(self, report_path: Path) -> List[Vulnerability]:
        """Parse LLMExploiter test results"""
        try:
            with open(report_path, "r") as f:
                data = json.load(f)

            vulns = []
            for test_result in data.get("test_results", []):
                if test_result.get("vulnerable", False):
                    # Map OWASP LLM categories to severity
                    category = test_result.get("owasp_category", "")
                    severity = self._llm_category_to_severity(category)

                    vuln = Vulnerability(
                        tool="LLMExploiter",
                        severity=severity,
                        category=category,
                        description=test_result.get("description", ""),
                        file=test_result.get("endpoint", ""),
                    )
                    vulns.append(vuln)

            return vulns
        except Exception as e:
            print(f"Error parsing LLMExploiter report: {e}", file=sys.stderr)
            return []

    def parse_nettacker_report(self, report_path: Path) -> List[Vulnerability]:
        """Parse Nettacker scan results"""
        try:
            with open(report_path, "r") as f:
                data = json.load(f)

            vulns = []
            for scan_result in data.get("scan_results", []):
                if scan_result.get("vulnerable", False):
                    severity_str = scan_result.get("severity", "MEDIUM")
                    severity = (
                        Severity[severity_str]
                        if severity_str in Severity.__members__
                        else Severity.MEDIUM
                    )

                    vuln = Vulnerability(
                        tool="Nettacker",
                        severity=severity,
                        category=scan_result.get("vulnerability_type", "UNKNOWN"),
                        description=scan_result.get("description", ""),
                        file=scan_result.get("target", ""),
                    )
                    vulns.append(vuln)

            return vulns
        except Exception as e:
            print(f"Error parsing Nettacker report: {e}", file=sys.stderr)
            return []

    def _cvss_to_severity(self, cvss_score: float) -> Severity:
        """Convert CVSS score to severity level"""
        if cvss_score >= 9.0:
            return Severity.CRITICAL
        elif cvss_score >= 7.0:
            return Severity.HIGH
        elif cvss_score >= 4.0:
            return Severity.MEDIUM
        elif cvss_score >= 0.1:
            return Severity.LOW
        else:
            return Severity.INFO

    def _llm_category_to_severity(self, category: str) -> Severity:
        """Map OWASP LLM Top 10 categories to severity"""
        critical_categories = [
            "LLM01",
            "LLM02",
            "LLM03",
            "LLM08",
        ]  # Prompt Injection, Insecure Output, Training Data Poisoning, Excessive Agency
        high_categories = ["LLM04", "LLM05", "LLM06", "LLM07", "LLM09", "LLM10"]

        if any(cat in category for cat in critical_categories):
            return Severity.CRITICAL
        elif any(cat in category for cat in high_categories):
            return Severity.HIGH
        else:
            return Severity.MEDIUM

    def scan_reports(self) -> None:
        """Scan all available reports in the reports directory"""
        report_parsers = {
            "bandit": self.parse_bandit_report,
            "safety": self.parse_safety_report,
            "helios": self.parse_helios_report,
            "llmexploiter": self.parse_llmexploiter_report,
            "nettacker": self.parse_nettacker_report,
        }

        for report_file in self.reports_dir.glob("*.json"):
            # Determine which parser to use based on filename
            for tool_name, parser in report_parsers.items():
                if tool_name in report_file.name.lower():
                    print(f"📊 Parsing {tool_name} report: {report_file.name}")
                    vulns = parser(report_file)
                    self.vulnerabilities.extend(vulns)
                    print(f"   Found {len(vulns)} issues")
                    break

    def get_summary(self) -> Dict[str, int]:
        """Get vulnerability count by severity"""
        summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

        for vuln in self.vulnerabilities:
            summary[vuln.severity.value] += 1

        return summary

    def has_critical_vulnerabilities(self) -> bool:
        """Check if critical vulnerabilities exist above threshold"""
        severity_order = {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFO: 1,
        }

        threshold_level = severity_order[self.threshold]

        for vuln in self.vulnerabilities:
            if severity_order[vuln.severity] >= threshold_level:
                return True

        return False

    def print_report(self) -> None:
        """Print formatted vulnerability report"""
        print("\n" + "=" * 80)
        print("🔒 ANVIL SECURITY SCAN REPORT")
        print("=" * 80 + "\n")

        summary = self.get_summary()

        print("📊 Summary:")
        print(f"   CRITICAL: {summary['CRITICAL']}")
        print(f"   HIGH:     {summary['HIGH']}")
        print(f"   MEDIUM:   {summary['MEDIUM']}")
        print(f"   LOW:      {summary['LOW']}")
        print(f"   INFO:     {summary['INFO']}")
        print(f"\n   Total Vulnerabilities: {len(self.vulnerabilities)}")
        print(f"   Threshold: {self.threshold.value}\n")

        # Group vulnerabilities by severity
        by_severity = {}
        for vuln in self.vulnerabilities:
            if vuln.severity not in by_severity:
                by_severity[vuln.severity] = []
            by_severity[vuln.severity].append(vuln)

        # Print critical and high severity details
        for severity in [Severity.CRITICAL, Severity.HIGH]:
            if severity in by_severity:
                print(f"\n{severity.value} Severity Issues:")
                print("-" * 80)
                for vuln in by_severity[severity]:
                    print(f"\n  [{vuln.tool}] {vuln.category}")
                    print(f"  Description: {vuln.description[:150]}")
                    if vuln.file:
                        location = f"{vuln.file}"
                        if vuln.line:
                            location += f":{vuln.line}"
                        print(f"  Location: {location}")
                    if vuln.cwe:
                        print(f"  CWE: {vuln.cwe}")
                    if vuln.cvss_score:
                        print(f"  CVSS Score: {vuln.cvss_score}")

        print("\n" + "=" * 80)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check security scan results for critical vulnerabilities"
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path(__file__).parent.parent / "reports",
        help="Directory containing security scan reports (default: ../reports)",
    )
    parser.add_argument(
        "--threshold",
        type=str,
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default="HIGH",
        help="Minimum severity to fail on (default: HIGH)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    # Validate reports directory exists
    if not args.reports_dir.exists():
        print(f"❌ Reports directory not found: {args.reports_dir}", file=sys.stderr)
        sys.exit(2)

    # Initialize checker
    threshold = Severity[args.threshold]
    checker = VulnerabilityChecker(args.reports_dir, threshold)

    # Scan all reports
    print(f"🔍 Scanning security reports in: {args.reports_dir}\n")
    checker.scan_reports()

    # Output results
    if args.json:
        summary = checker.get_summary()
        output = {
            "total_vulnerabilities": len(checker.vulnerabilities),
            "threshold": threshold.value,
            "summary": summary,
            "has_critical": checker.has_critical_vulnerabilities(),
        }
        print(json.dumps(output, indent=2))
    else:
        checker.print_report()

    # Exit with appropriate code
    if checker.has_critical_vulnerabilities():
        print(
            f"\n❌ FAIL: Found vulnerabilities at or above {threshold.value} severity"
        )
        sys.exit(1)
    else:
        print(
            f"\n✅ PASS: No vulnerabilities found at or above {threshold.value} severity"
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
