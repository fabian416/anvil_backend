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
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


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
        self.llm_provider = None  # "deepinfra" or "vertex_ai"

        # Try DeepInfra first (already configured)
        self.llm = None
        self.llm_available = False

        if self._init_deepinfra():
            return

        # Fallback to Vertex AI
        if self._init_vertex_ai():
            return

        print("⚠️  No LLM provider available")
        print("   Continuing with basic analysis only")

    def _init_deepinfra(self) -> bool:
        """Try to initialize DeepInfra."""
        try:
            import toml
            import httpx

            # Load API key from config
            secrets_file = self.project_root / "config" / "local" / ".secrets.toml"
            if not secrets_file.exists():
                return False

            config = toml.load(secrets_file)
            deepinfra_config = config.get("deepinfra", {})

            api_key = deepinfra_config.get("API_KEY")
            base_url = deepinfra_config.get("BASE_URL", "https://api.deepinfra.com/v1/openai")

            if not api_key:
                return False

            # Initialize HTTP client for OpenAI-compatible API
            self.llm = httpx.AsyncClient(
                base_url=base_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
            self.llm_provider = "deepinfra"
            self.llm_available = True
            print("✅ LLM (DeepInfra) initialized")
            print(f"   Model: meta-llama/Meta-Llama-3.1-70B-Instruct")
            print(f"   Cost: $0.08/1M tokens")
            return True

        except Exception as e:
            print(f"   DeepInfra init failed: {e}")
            return False

    def _init_vertex_ai(self) -> bool:
        """Try to initialize Vertex AI."""
        try:
            from google.cloud import aiplatform
            from vertexai.generative_models import GenerativeModel

            aiplatform.init(project="your-project-id", location="us-central1")
            self.llm = GenerativeModel("gemini-2.0-flash-exp")
            self.llm_provider = "vertex_ai"
            self.llm_available = True
            print("✅ LLM (Vertex AI) initialized")
            return True
        except Exception as e:
            print(f"   Vertex AI init failed: {e}")
            return False

    async def run_tests(self, test_type: str) -> list[TestResult]:
        """Run tests and collect results."""
        print(f"\n🧪 Running {test_type} tests...")

        # Determine test files
        test_files = self._get_test_files(test_type)

        results = []
        for test_name, test_file in test_files.items():
            print(f"\n📋 Executing: {test_name}")

            # Check if test file exists
            if not (self.project_root / test_file).exists():
                print(f"   ⚠️  Test file not found: {test_file}")
                continue

            # Run pytest with JSON report
            json_file = self.output_dir / test_type / f"{test_name}_results.json"
            log_file = self.output_dir / test_type / f"{test_name}_output.log"

            # Ensure output directory exists
            json_file.parent.mkdir(parents=True, exist_ok=True)

            cmd = [
                "pytest",
                test_file,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={json_file}",
                "-x",  # Stop on first failure (optional)
            ]

            # Execute and capture logs
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=1800,  # 30 minute timeout
                )

                # Save logs
                with open(log_file, "w") as f:
                    f.write(result.stdout)
                    f.write("\n=== STDERR ===\n")
                    f.write(result.stderr)

                print(f"   Exit code: {result.returncode}")

            except subprocess.TimeoutExpired:
                print(f"   ⏱️  Timeout after 30 minutes")
                continue
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

            # Parse JSON report
            if json_file.exists():
                test_results = await self._parse_json_report(
                    json_file, log_file, test_name
                )
                results.extend(test_results)
                print(f"   ✅ Parsed {len(test_results)} test results")

        return results

    async def _parse_json_report(
        self,
        json_file: Path,
        log_file: Path,
        test_name: str,
    ) -> list[TestResult]:
        """Parse pytest JSON report and analyze failures."""
        try:
            with open(json_file) as f:
                report = json.load(f)
        except Exception as e:
            print(f"   ❌ Error parsing JSON: {e}")
            return []

        try:
            with open(log_file) as f:
                logs = f.read()
        except Exception as e:
            print(f"   ⚠️  Could not read logs: {e}")
            logs = ""

        results = []
        tests = report.get("tests", [])

        print(f"   📊 Processing {len(tests)} tests")

        for idx, test in enumerate(tests, 1):
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
                    error_message = longrepr[:500]  # Truncate for CSV
                elif isinstance(longrepr, list):
                    error_message = str(longrepr[0])[:500] if longrepr else ""

            # Create base result
            result = TestResult(
                test_id=test_id,
                category=self._categorize_test(scenario),
                scenario=scenario,
                input="See test code",
                expected_output="See test assertions",
                actual_output="See test logs" if status == "PASS" else error_message[:200],
                status=status,
                execution_time_ms=duration_ms,
                error_message=error_message,
            )

            # LLM analysis for failures
            if status in ["FAIL", "ERROR"] and self.llm_available:
                try:
                    await self._analyze_failure_with_llm(result, test, logs)
                except Exception as e:
                    print(f"     ⚠️  LLM analysis failed for {test_id}: {e}")
                    result.llm_analysis = f"LLM analysis error: {str(e)}"

            results.append(result)

        return results

    async def _analyze_failure_with_llm(
        self,
        result: TestResult,
        test_data: dict,
        full_logs: str,
    ):
        """Use LLM to analyze test failure."""
        if not self.llm:
            return

        # Extract relevant log section
        log_excerpt = self._extract_relevant_logs(full_logs, result.scenario)

        # Construct LLM prompt
        prompt = f"""Analyze this pytest test failure and provide actionable insights:

Test Scenario: {result.scenario}
Status: {result.status}
Execution Time: {result.execution_time_ms}ms

Error Message:
{result.error_message}

Relevant Logs (excerpt):
{log_excerpt}

Please provide a JSON response with:
1. "analysis": Root cause analysis (2-3 sentences, focus on technical cause)
2. "severity": One of: critical, major, minor, trivial
3. "recommendations": Array of 1-3 specific, actionable fixes

Example:
{{
    "analysis": "Test failed due to database connection timeout. The connection pool was exhausted, likely from previous tests not cleaning up connections properly.",
    "severity": "major",
    "recommendations": [
        "Increase database connection pool size in test configuration",
        "Add connection cleanup in test teardown fixtures",
        "Check for connection leaks in async database operations"
    ]
}}

IMPORTANT: Respond ONLY with valid JSON, no markdown formatting."""

        try:
            # Call LLM based on provider
            if self.llm_provider == "deepinfra":
                llm_output = await self._call_deepinfra(prompt)
            elif self.llm_provider == "vertex_ai":
                response = await self.llm.generate_content_async(prompt)
                llm_output = response.text.strip()
            else:
                return

            # Remove markdown code blocks if present
            if llm_output.startswith("```json"):
                llm_output = llm_output[7:]
            if llm_output.startswith("```"):
                llm_output = llm_output[3:]
            if llm_output.endswith("```"):
                llm_output = llm_output[:-3]
            llm_output = llm_output.strip()

            # Parse JSON response
            llm_data = json.loads(llm_output)

            result.llm_analysis = llm_data.get("analysis", "")
            result.severity = llm_data.get("severity", "unknown")

            # Format recommendations as pipe-separated string
            recs = llm_data.get("recommendations", [])
            if isinstance(recs, list):
                result.recommendations = " | ".join(recs)
            else:
                result.recommendations = str(recs)

        except json.JSONDecodeError as e:
            result.llm_analysis = f"LLM response parsing failed: {str(e)}"
            result.severity = "unknown"
        except Exception as e:
            result.llm_analysis = f"LLM analysis failed: {str(e)}"
            result.severity = "unknown"

    async def _call_deepinfra(self, prompt: str) -> str:
        """Call DeepInfra API (OpenAI-compatible)."""
        response = await self.llm.post(
            "/chat/completions",
            json={
                "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                "messages": [
                    {"role": "system", "content": "You are a helpful test analysis assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 1000,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _extract_relevant_logs(self, logs: str, test_name: str) -> str:
        """Extract relevant log section for a test."""
        lines = logs.split("\n")
        relevant = []

        # Find test start
        in_test = False
        context_lines = 0

        for line in lines:
            # Start capturing when we see the test name
            if test_name in line:
                in_test = True
                context_lines = 0

            # Stop after test completes (max 50 lines of context)
            if in_test:
                relevant.append(line)
                context_lines += 1

                if context_lines > 50:
                    break

                # Stop on next test or section marker
                if context_lines > 5 and any(marker in line for marker in ["PASSED", "FAILED", "ERROR", "::test_"]):
                    if not test_name in line:
                        break

        # Limit to 2000 chars for LLM context
        excerpt = "\n".join(relevant)
        return excerpt[:2000]

    def _categorize_test(self, test_name: str) -> str:
        """Categorize test based on name."""
        name_lower = test_name.lower()

        if "guest" in name_lower:
            return "guest_chat"
        elif any(lang in name_lower for lang in ["french", "spanish", "portuguese", "chinese", "multilang"]):
            return "multilanguage"
        elif "performance" in name_lower or "concurrent" in name_lower or "benchmark" in name_lower:
            return "performance"
        elif "security" in name_lower or "xss" in name_lower or "injection" in name_lower or "auth" in name_lower:
            return "security"
        elif "cross" in name_lower and "chain" in name_lower:
            return "cross_chain"
        elif "knowledge" in name_lower:
            return "knowledge_database"
        else:
            return "authenticated_chat"

    def _get_test_files(self, test_type: str) -> dict[str, str]:
        """Get test files for a test type."""
        files = {
            "guest": {
                "guest_comprehensive": "tests/integration/chat/test_guest_chat_comprehensive.py",
                "guest_parity": "tests/integration/chat/test_guest_chat_parity.py",
            },
            "user": {
                "authenticated_comprehensive": "tests/integration/chat/test_authenticated_chat_comprehensive.py",
                "authenticated_integration": "tests/integration/chat/test_authenticated_chat_integration.py",
            },
            "advanced": {
                "multilanguage": "tests/integration/chat/test_multilanguage_comprehensive.py",
                "performance": "tests/integration/performance/test_performance_comprehensive.py",
                "security": "tests/integration/security/test_security_comprehensive.py",
                "cross_chain": "tests/integration/chat/test_cross_chain_comprehensive.py",
                "agent_squad": "tests/integration/chat/test_agent_squad_ultra_hunter_full.py",
            },
        }
        return files.get(test_type, {})

    def export_to_csv(self, results: list[TestResult], output_file: Path):
        """Export results to CSV."""
        print(f"\n📊 Exporting {len(results)} results to {output_file}")

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
                writer.writerow(asdict(result))

        # Print summary
        total = len(results)
        passed = sum(1 for r in results if r.status == "PASS")
        failed = sum(1 for r in results if r.status == "FAIL")
        errors = sum(1 for r in results if r.status == "ERROR")
        skipped = sum(1 for r in results if r.status == "SKIP")

        print(f"\n{'='*60}")
        print(f"Test Summary - {output_file.parent.name.upper()}")
        print(f"{'='*60}")
        print(f"✅ PASS:    {passed}/{total} ({passed/total*100:.1f}%)")
        print(f"❌ FAIL:    {failed}/{total} ({failed/total*100:.1f}%)")
        print(f"⚠️  ERROR:   {errors}/{total}")
        print(f"⏭️  SKIPPED: {skipped}/{total}")
        print(f"{'='*60}\n")

        # Print critical failures
        critical = [r for r in results if r.severity == "critical"]
        if critical:
            print(f"🚨 CRITICAL FAILURES ({len(critical)}):")
            for r in critical:
                print(f"   • {r.scenario}")
                print(f"     {r.llm_analysis[:100]}...")
            print()

    async def run(self):
        """Execute test validation workflow."""
        print("\n" + "="*80)
        print("🧪 LLM-Powered Test Validator")
        print("="*80)
        print(f"Mode: {self.mode.upper()}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Output Directory: {self.output_dir}")
        print("="*80)

        if self.mode in ["guest", "all"]:
            print("\n🎭 Running GUEST tests...")
            results = await self.run_tests("guest")
            output_file = self.output_dir / "guest" / "llm_validated_results.csv"
            self.export_to_csv(results, output_file)

        if self.mode in ["user", "all"]:
            print("\n👤 Running USER tests...")
            results = await self.run_tests("user")
            output_file = self.output_dir / "user" / "llm_validated_results.csv"
            self.export_to_csv(results, output_file)

        if self.mode in ["advanced", "all"]:
            print("\n🚀 Running ADVANCED tests...")
            results = await self.run_tests("advanced")
            output_file = self.output_dir / "advanced" / "llm_validated_results.csv"
            self.export_to_csv(results, output_file)

        print("\n✅ Test validation complete!")
        print(f"\n📁 CSV reports available in:")
        print(f"   - tests/output/guest/llm_validated_results.csv")
        print(f"   - tests/output/user/llm_validated_results.csv")
        print(f"   - tests/output/advanced/llm_validated_results.csv")


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="LLM-powered test validator with CSV reports"
    )
    parser.add_argument(
        "--mode",
        choices=["guest", "user", "advanced", "all"],
        default="all",
        help="Test mode: guest, user, advanced, or all (default: all)",
    )

    args = parser.parse_args()

    validator = LLMTestValidator(mode=args.mode)
    await validator.run()


if __name__ == "__main__":
    asyncio.run(main())
