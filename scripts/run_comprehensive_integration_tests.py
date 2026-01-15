#!/usr/bin/env python3
"""
Comprehensive Integration Test Runner with CSV Export

Executes all integration tests and exports results to CSV format:
- Guest tests: Week 1-8 comprehensive guest testing
- User tests: Week 1-8 authenticated user testing
- Advanced tests: Agent Squad and Knowledge Database testing (Week 9+)

Usage:
    python scripts/run_comprehensive_integration_tests.py --mode guest
    python scripts/run_comprehensive_integration_tests.py --mode user
    python scripts/run_comprehensive_integration_tests.py --mode advanced
    python scripts/run_comprehensive_integration_tests.py --mode all

Output:
    - tests/output/guest/week1_8_input_output.csv
    - tests/output/user/week1_8_input_output.csv
    - tests/output/advanced/advanced_tests_output.csv
"""

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class TestRunner:
    """Execute integration tests and export results to CSV."""

    def __init__(self, mode: str):
        """Initialize test runner.

        Args:
            mode: 'guest', 'user', or 'all'
        """
        self.mode = mode
        self.project_root = Path(__file__).parent.parent
        self.output_dir = self.project_root / "tests" / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Define test files
        self.test_files = {
            "guest": {
                "comprehensive": "tests/integration/chat/test_guest_chat_comprehensive.py",
                "parity": "tests/integration/chat/test_guest_chat_parity.py",
                "shortcuts": "tests/integration/chat/test_shortcuts_edge_cases_comprehensive.py",
            },
            "user": {
                "comprehensive": "tests/integration/chat/test_authenticated_chat_comprehensive.py",
                "integration": "tests/integration/chat/test_authenticated_chat_integration.py",
            },
            "advanced": {
                "agent_squad": "tests/integration/chat/test_agent_squad_ultra_hunter_full.py",
                "cross_chain": "tests/integration/chat/test_cross_chain_comprehensive.py",
                "multilanguage": "tests/integration/chat/test_multilanguage_comprehensive.py",
                "performance": "tests/integration/performance/test_performance_comprehensive.py",
                "security": "tests/integration/security/test_security_comprehensive.py",
                "knowledge_injection": "tests/integration/chat/test_knowledge_injection.py",
                "knowledge_compression": "tests/integration/chat/test_knowledge_compression.py",
                "knowledge_quality": "tests/integration/chat/test_knowledge_quality_assurance.py",
                "knowledge_context": "tests/integration/chat/test_knowledge_context_enrichment.py",
                "knowledge_errors": "tests/integration/chat/test_knowledge_error_handling.py",
                "knowledge_advanced": "tests/integration/chat/test_knowledge_advanced_scenarios.py",
                "knowledge_sources": "tests/integration/chat/test_knowledge_source_integration.py",
            },
        }

    def run_tests(self, test_type: str) -> Dict[str, Any]:
        """Run tests for guest or user.

        Args:
            test_type: 'guest' or 'user'

        Returns:
            Dictionary with test results
        """
        print(f"\n{'='*80}")
        print(f"Running {test_type.upper()} Integration Tests")
        print(f"{'='*80}\n")

        test_files = self.test_files.get(test_type, {})
        all_results = []

        for test_name, test_file in test_files.items():
            print(f"\n📋 Executing: {test_name}")
            print(f"   File: {test_file}")

            # Run pytest with JSON report
            cmd = [
                "pytest",
                test_file,
                "-v",
                "--tb=short",
                f"--json-report",
                f"--json-report-file=tests/output/{test_type}_{test_name}_report.json",
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                )

                # Parse JSON report
                report_file = (
                    self.project_root
                    / "tests"
                    / "output"
                    / f"{test_type}_{test_name}_report.json"
                )

                if report_file.exists():
                    with open(report_file, "r") as f:
                        report_data = json.load(f)
                        all_results.extend(self._parse_json_report(report_data, test_name))
                else:
                    print(f"⚠️  Warning: Report file not found: {report_file}")

                # Print summary
                if result.returncode == 0:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED (see logs)")

            except Exception as e:
                print(f"❌ Error running {test_name}: {e}")
                all_results.append({
                    "test_id": f"{test_type}_{test_name}_error",
                    "category": "error",
                    "scenario": test_name,
                    "input": "N/A",
                    "expected_output": "N/A",
                    "actual_output": str(e),
                    "status": "ERROR",
                    "execution_time_ms": 0,
                    "error_message": str(e),
                    "notes": "Test execution failed",
                })

        return {
            "test_type": test_type,
            "results": all_results,
            "total_tests": len(all_results),
            "passed": sum(1 for r in all_results if r["status"] == "PASS"),
            "failed": sum(1 for r in all_results if r["status"] == "FAIL"),
            "errors": sum(1 for r in all_results if r["status"] == "ERROR"),
        }

    def _parse_json_report(self, report_data: Dict, test_suite_name: str) -> List[Dict]:
        """Parse pytest JSON report into CSV format.

        Args:
            report_data: JSON report from pytest-json-report
            test_suite_name: Name of test suite

        Returns:
            List of test result dictionaries
        """
        results = []
        tests = report_data.get("tests", [])

        for idx, test in enumerate(tests, 1):
            # Extract test information
            test_id = f"{test_suite_name}_{idx}"
            nodeid = test.get("nodeid", "")
            outcome = test.get("outcome", "unknown").upper()

            # Map outcome to status
            status_map = {
                "PASSED": "PASS",
                "FAILED": "FAIL",
                "SKIPPED": "SKIP",
                "ERROR": "ERROR",
            }
            status = status_map.get(outcome, "UNKNOWN")

            # Extract test details
            test_name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
            duration_ms = int(test.get("duration", 0) * 1000)

            # Extract error message if failed
            error_message = ""
            if status == "FAIL":
                call = test.get("call", {})
                longrepr = call.get("longrepr", "")
                if isinstance(longrepr, str):
                    error_message = longrepr[:200]  # Truncate for CSV

            # Categorize test
            category = self._categorize_test(test_name)

            results.append({
                "test_id": test_id,
                "category": category,
                "scenario": test_name,
                "input": "See test code",  # Would need to parse test code
                "expected_output": "See test assertions",
                "actual_output": "See test logs",
                "status": status,
                "execution_time_ms": duration_ms,
                "error_message": error_message,
                "notes": f"Test suite: {test_suite_name}",
            })

        return results

    def _categorize_test(self, test_name: str) -> str:
        """Categorize test based on name.

        Args:
            test_name: Test function name

        Returns:
            Category string
        """
        name_lower = test_name.lower()

        if any(x in name_lower for x in ["lending", "deposit", "vault"]):
            return "shortcut_lending"
        elif any(x in name_lower for x in ["swap", "exchange", "trade"]):
            return "shortcut_swap"
        elif any(x in name_lower for x in ["portfolio", "holdings"]):
            return "shortcut_portfolio"
        elif "balance" in name_lower:
            return "shortcut_balance"
        elif "activity" in name_lower:
            return "shortcut_activity"
        elif "receive" in name_lower:
            return "shortcut_receive"
        elif "buy" in name_lower:
            return "shortcut_buy"
        elif "send" in name_lower:
            return "shortcut_send"
        elif any(x in name_lower for x in ["multistep", "multi_step", "flow"]):
            return "multistep_flow"
        elif any(x in name_lower for x in ["cancel", "cancellation"]):
            return "multistep_cancellation"
        elif any(x in name_lower for x in ["interrupt", "interruption"]):
            return "multistep_interruption"
        elif any(x in name_lower for x in ["ultra", "hunter", "price", "sentiment"]):
            return "ultra_hunter"
        elif any(x in name_lower for x in ["agent", "squad", "research"]):
            return "agent_squad"
        elif any(x in name_lower for x in ["knowledge", "database", "kb"]):
            return "knowledge_database"
        elif any(x in name_lower for x in ["info", "general", "help", "greeting"]):
            return "general_informational"
        else:
            return "other"

    def export_to_csv(self, results: Dict[str, Any], output_file: Path):
        """Export test results to CSV.

        Args:
            results: Test results dictionary
            output_file: Path to CSV output file
        """
        print(f"\n📊 Exporting results to CSV: {output_file}")

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
                "notes",
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in results["results"]:
                writer.writerow(result)

        print(f"✅ Exported {len(results['results'])} test results")

        # Print summary
        print(f"\n{'='*80}")
        print(f"Test Summary ({results['test_type'].upper()})")
        print(f"{'='*80}")
        print(f"Total Tests:  {results['total_tests']}")
        print(f"✅ Passed:    {results['passed']} ({results['passed']/results['total_tests']*100:.1f}%)")
        print(f"❌ Failed:    {results['failed']} ({results['failed']/results['total_tests']*100:.1f}%)")
        print(f"⚠️  Errors:    {results['errors']}")
        print(f"{'='*80}\n")

    def run(self):
        """Execute test runner."""
        print("\n" + "="*80)
        print("Comprehensive Integration Test Runner")
        print("="*80)
        print(f"Mode: {self.mode.upper()}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("="*80)

        if self.mode in ["guest", "all"]:
            guest_results = self.run_tests("guest")
            guest_output = self.output_dir / "guest" / "week1_8_input_output.csv"
            guest_output.parent.mkdir(parents=True, exist_ok=True)
            self.export_to_csv(guest_results, guest_output)

        if self.mode in ["user", "all"]:
            user_results = self.run_tests("user")
            user_output = self.output_dir / "user" / "week1_8_input_output.csv"
            user_output.parent.mkdir(parents=True, exist_ok=True)
            self.export_to_csv(user_results, user_output)

        if self.mode in ["advanced", "all"]:
            advanced_results = self.run_tests("advanced")
            advanced_output = self.output_dir / "advanced" / "advanced_tests_output.csv"
            advanced_output.parent.mkdir(parents=True, exist_ok=True)
            self.export_to_csv(advanced_results, advanced_output)

        print("\n✅ Test execution complete!")
        print(f"\nOutput files:")
        if self.mode in ["guest", "all"]:
            print(f"  - tests/output/guest/week1_8_input_output.csv")
        if self.mode in ["user", "all"]:
            print(f"  - tests/output/user/week1_8_input_output.csv")
        if self.mode in ["advanced", "all"]:
            print(f"  - tests/output/advanced/advanced_tests_output.csv")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive integration tests with CSV export"
    )
    parser.add_argument(
        "--mode",
        choices=["guest", "user", "advanced", "all"],
        default="all",
        help="Test mode: guest, user, advanced, or all (default: all)",
    )

    args = parser.parse_args()

    runner = TestRunner(mode=args.mode)
    runner.run()


if __name__ == "__main__":
    main()
