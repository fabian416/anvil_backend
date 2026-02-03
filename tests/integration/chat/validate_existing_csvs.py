#!/usr/bin/env python3
"""
Validate Existing CSV Test Results with LLM.

Reads existing CSV test results and validates each row with the LLM,
adding AI analysis columns.

Usage:
    # Validate all tests (expensive - ~$2.29 for 3,582 tests)
    python tests/integration/chat/validate_existing_csvs.py --mode full

    # Validate only failed tests
    python tests/integration/chat/validate_existing_csvs.py --mode failed

    # Sample validation (every 10th test)
    python tests/integration/chat/validate_existing_csvs.py --mode sample --sample-rate 10

    # Dry run (count tests without validating)
    python tests/integration/chat/validate_existing_csvs.py --mode dry-run
"""

import asyncio
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add project to path
sys.path.insert(0, "/home/ubuntu/anvil_backend")

# Configure environment
os.environ["DEEPINFRA_API_KEY"] = "ur1aITAnOmIXK0LTT1zCBDGnk3elzsVA"
os.environ["ENABLE_LLM_VALIDATION"] = "true"
os.environ["ENABLE_LOG_ANALYSIS"] = "false"  # Not needed for CSV validation

from tests.helpers.llm_test_validator import LLMTestValidator, ValidationVerdict
from tests.helpers.enhanced_csv_writer import EnhancedCSVWriter, EnhancedTestResult


class CSVValidator:
    """Validate existing CSV test results with LLM."""

    def __init__(self, mode: str = "failed", sample_rate: int = 10):
        """
        Initialize CSV validator.

        Args:
            mode: Validation mode (full, failed, sample, dry-run)
            sample_rate: Sample rate for sample mode (validate every Nth test)
        """
        self.mode = mode
        self.sample_rate = sample_rate
        self.validator = LLMTestValidator()

        # File paths
        self.guest_csv = Path(
            "/home/ubuntu/anvil_backend/tests/output/guest/week1_8_input_output.csv"
        )
        self.user_csv = Path(
            "/home/ubuntu/anvil_backend/tests/output/user/week1_8_input_output.csv"
        )

        # Output paths
        self.guest_output = Path(
            "/home/ubuntu/anvil_backend/tests/output/guest/week1_8_input_output_validated.csv"
        )
        self.user_output = Path(
            "/home/ubuntu/anvil_backend/tests/output/user/week1_8_input_output_validated.csv"
        )

        # Statistics
        self.stats = {
            "total_rows": 0,
            "validated": 0,
            "skipped": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "total_tokens": 0,
            "total_time_ms": 0,
        }

    async def validate_csv_file(self, input_csv: Path, output_csv: Path, csv_type: str):
        """
        Validate a single CSV file.

        Args:
            input_csv: Input CSV file path
            output_csv: Output CSV file path
            csv_type: Type of CSV (guest or user)
        """
        print(f"\n{'=' * 70}")
        print(f"Validating {csv_type.upper()} CSV: {input_csv.name}")
        print(f"{'=' * 70}")

        # Read existing CSV
        with input_csv.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"Total rows: {len(rows)}")
        self.stats["total_rows"] += len(rows)

        # Determine which rows to validate based on mode
        rows_to_validate = self._select_rows_to_validate(rows)
        print(f"Rows to validate: {len(rows_to_validate)} ({self.mode} mode)")

        if self.mode == "dry-run":
            print("\n✅ Dry run complete - no validation performed")
            return

        # Estimate cost
        estimated_tokens = len(rows_to_validate) * 8000
        estimated_cost = estimated_tokens / 1_000_000 * 0.08
        print(f"\nEstimated cost: ${estimated_cost:.2f} ({estimated_tokens:,} tokens)")

        # Ask for confirmation if cost > $0.50
        if estimated_cost > 0.50:
            response = input(
                f"\n⚠️  This will cost approximately ${estimated_cost:.2f}. Continue? (y/n): "
            )
            if response.lower() != "y":
                print("❌ Validation cancelled")
                return

        # Validate each row
        validated_rows = []
        for i, row in enumerate(rows, 1):
            if row not in rows_to_validate:
                # Keep row unchanged
                validated_rows.append(row)
                self.stats["skipped"] += 1
            else:
                # Validate row
                print(f"\n[{i}/{len(rows)}] Validating: {row['Type'][:60]}...")
                validated_row = await self._validate_row(row, csv_type)
                validated_rows.append(validated_row)
                self.stats["validated"] += 1

                # Progress indicator
                if i % 10 == 0:
                    print(f"\n📊 Progress: {i}/{len(rows)} rows processed")
                    print(
                        f"   Validated: {self.stats['validated']}, Skipped: {self.stats['skipped']}"
                    )
                    print(
                        f"   Total tokens: {self.stats['total_tokens']:,}, Cost: ${self.stats['total_tokens'] / 1_000_000 * 0.08:.4f}"
                    )

        # Write validated CSV
        self._write_validated_csv(validated_rows, output_csv)
        print(f"\n✅ Validated CSV written to: {output_csv}")

    def _select_rows_to_validate(
        self, rows: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Select which rows to validate based on mode."""
        if self.mode == "full":
            return rows

        elif self.mode == "failed":
            # Only validate rows where test_pass is FAIL or empty
            return [row for row in rows if row.get("test pass", "").upper() != "PASS"]

        elif self.mode == "sample":
            # Validate every Nth row
            return [rows[i] for i in range(0, len(rows), self.sample_rate)]

        elif self.mode == "dry-run":
            return []

        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    async def _validate_row(self, row: Dict[str, str], csv_type: str) -> Dict[str, str]:
        """
        Validate a single CSV row.

        Args:
            row: CSV row as dict
            csv_type: Type of CSV (guest or user)

        Returns:
            Updated row with AI validation columns
        """
        # Extract test data
        test_type = row["Type"]
        is_multi_step = row.get("is multi step", "NO").upper() == "YES"

        # Extract inputs and outputs (up to 4 steps)
        inputs = []
        outputs = []
        for i in range(1, 5):
            input_key = f"input {i}"
            output_key = f"output {i}"

            if input_key in row and row[input_key]:
                inputs.append(row[input_key])
            if output_key in row and row[output_key]:
                outputs.append(row[output_key])

        # Skip if no data
        if not inputs or not outputs:
            row["llm_verdict"] = "SKIP"
            row["llm_confidence"] = "0.00"
            row["error_analysis"] = "No input/output data"
            return row

        # Determine expected behavior based on test type
        expected_behavior = self._get_expected_behavior(test_type, is_multi_step)

        try:
            if is_multi_step and len(inputs) > 1:
                # Multi-step validation
                steps = [
                    {
                        "user_input": inputs[i],
                        "agent_output": outputs[i],
                        "expected_behavior": f"Step {i + 1} of {test_type}",
                    }
                    for i in range(min(len(inputs), len(outputs)))
                ]

                flow_result = await self.validator.validate_multistep_flow(
                    test_name=test_type,
                    steps=steps,
                    expected_flow_behavior=expected_behavior,
                )

                # Update stats
                self.stats["total_tokens"] += flow_result.tokens_used
                self.stats["total_time_ms"] += flow_result.validation_time_ms

                # Update row
                row["llm_verdict"] = flow_result.verdict.value
                row["llm_confidence"] = f"{flow_result.confidence:.2f}"
                row["error_analysis"] = flow_result.reasoning[:500]  # Truncate
                row["root_cause"] = ""
                row["suggested_fix"] = ""

                # Update verdict stats
                if flow_result.verdict == ValidationVerdict.PASS:
                    self.stats["passed"] += 1
                elif flow_result.verdict == ValidationVerdict.FAIL:
                    self.stats["failed"] += 1
                else:
                    self.stats["warnings"] += 1

                print(
                    f"   AI: {flow_result.verdict.value} ({flow_result.confidence:.2f})"
                )

            else:
                # Single-step validation
                validation_result = await self.validator.validate_single_response(
                    test_name=test_type,
                    user_input=inputs[0] if inputs else "",
                    agent_output=outputs[0] if outputs else "",
                    expected_behavior=expected_behavior,
                )

                # Update stats
                self.stats["total_tokens"] += validation_result.tokens_used
                self.stats["total_time_ms"] += validation_result.validation_time_ms

                # Update row
                row["llm_verdict"] = validation_result.verdict.value
                row["llm_confidence"] = f"{validation_result.confidence:.2f}"
                row["error_analysis"] = (
                    "; ".join(validation_result.semantic_issues)
                    if validation_result.semantic_issues
                    else validation_result.reasoning[:500]
                )
                row["root_cause"] = ""
                row["suggested_fix"] = ""

                # Update verdict stats
                if validation_result.verdict == ValidationVerdict.PASS:
                    self.stats["passed"] += 1
                elif validation_result.verdict == ValidationVerdict.FAIL:
                    self.stats["failed"] += 1
                else:
                    self.stats["warnings"] += 1

                print(
                    f"   AI: {validation_result.verdict.value} ({validation_result.confidence:.2f})"
                )

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")
            row["llm_verdict"] = "ERROR"
            row["llm_confidence"] = "0.00"
            row["error_analysis"] = f"Validation error: {str(e)[:200]}"
            row["root_cause"] = ""
            row["suggested_fix"] = ""

        return row

    def _get_expected_behavior(self, test_type: str, is_multi_step: bool) -> str:
        """Get expected behavior description based on test type."""
        test_type_lower = test_type.lower()

        # Security tests
        if (
            "xss" in test_type_lower
            or "sql" in test_type_lower
            or "injection" in test_type_lower
        ):
            return "Should safely handle malicious input without executing or exposing the injection attempt"

        if "command" in test_type_lower or "prompt" in test_type_lower:
            return "Should sanitize command injection attempts and maintain appropriate responses"

        if "rate_limit" in test_type_lower:
            return "Should enforce rate limiting and provide appropriate error messages"

        # Functional tests
        if "swap" in test_type_lower:
            return (
                "Should guide user through token swap process with accurate information"
                if is_multi_step
                else "Should provide swap information"
            )

        if (
            "price" in test_type_lower
            or "bitcoin" in test_type_lower
            or "ethereum" in test_type_lower
        ):
            return "Should provide accurate cryptocurrency price information"

        if "balance" in test_type_lower or "portfolio" in test_type_lower:
            return "Should provide balance or portfolio information"

        if "send" in test_type_lower or "transfer" in test_type_lower:
            return "Should guide through send/transfer process"

        if "buy" in test_type_lower or "purchase" in test_type_lower:
            return "Should guide through purchase process"

        if "lending" in test_type_lower or "borrow" in test_type_lower:
            return "Should provide lending/borrowing information"

        # Hunter AI tests
        if "hunter" in test_type_lower:
            return "Should provide AI-powered market analysis and insights"

        # Default
        return "Should provide appropriate and accurate response to user query"

    def _write_validated_csv(self, rows: List[Dict[str, str]], output_csv: Path):
        """Write validated rows to CSV with AI columns."""
        # Ensure all rows have AI columns
        ai_columns = [
            "llm_verdict",
            "llm_confidence",
            "error_analysis",
            "root_cause",
            "suggested_fix",
        ]

        # Get all column names (original + AI columns)
        if rows:
            original_columns = list(rows[0].keys())
            # Add AI columns if not present
            all_columns = original_columns.copy()
            for col in ai_columns:
                if col not in all_columns:
                    all_columns.append(col)
        else:
            all_columns = [
                "Type",
                "device",
                "is multi step",
                "input 1",
                "output 1",
                "input 2",
                "output 2",
                "input 3",
                "output 3",
                "input 4",
                "output 4",
                "test pass",
            ] + ai_columns

        # Write CSV
        with output_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_columns)
            writer.writeheader()

            for row in rows:
                # Ensure all AI columns exist
                for col in ai_columns:
                    if col not in row:
                        row[col] = ""
                writer.writerow(row)

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"\nTotal rows: {self.stats['total_rows']}")
        print(f"Validated: {self.stats['validated']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"\nAI Verdicts:")
        print(f"  ✅ PASS: {self.stats['passed']}")
        print(f"  ❌ FAIL: {self.stats['failed']}")
        print(f"  ⚠️  WARNING: {self.stats['warnings']}")
        print(f"\nAPI Usage:")
        print(f"  Tokens used: {self.stats['total_tokens']:,}")
        print(f"  Total time: {self.stats['total_time_ms'] / 1000:.1f}s")
        print(f"  Cost: ${self.stats['total_tokens'] / 1_000_000 * 0.08:.4f}")
        print(f"\nOutput files:")
        print(f"  Guest: {self.guest_output}")
        print(f"  User: {self.user_output}")


async def main():
    """Main validation function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate existing CSV test results with LLM"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "failed", "sample", "dry-run"],
        default="failed",
        help="Validation mode (default: failed)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=10,
        help="Sample rate for sample mode (default: 10)",
    )
    parser.add_argument(
        "--csv-type",
        choices=["guest", "user", "both"],
        default="both",
        help="Which CSV to validate (default: both)",
    )

    args = parser.parse_args()

    # Create validator
    validator = CSVValidator(mode=args.mode, sample_rate=args.sample_rate)

    # Validate CSVs
    if args.csv_type in ["guest", "both"]:
        await validator.validate_csv_file(
            validator.guest_csv, validator.guest_output, "guest"
        )

    if args.csv_type in ["user", "both"]:
        await validator.validate_csv_file(
            validator.user_csv, validator.user_output, "user"
        )

    # Print summary
    validator.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
