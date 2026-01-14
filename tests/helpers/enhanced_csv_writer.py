"""
Enhanced CSV Writer - Writes test results with AI analysis.

Extends the standard CSV format with LLM validation results and automated error analysis.
Maintains backward compatibility with existing CSV readers.
"""

import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from tests.helpers.llm_test_validator import ValidationResult, ValidationVerdict
from tests.helpers.log_analyzer import ErrorAnalysis

logger = logging.getLogger(__name__)


@dataclass
class EnhancedTestResult:
    """Test result with AI analysis."""

    # Standard test result fields
    test_type: str
    device: str
    is_multi_step: bool
    inputs: list[str]  # Up to 4 inputs
    outputs: list[str]  # Up to 4 outputs
    test_pass: bool

    # AI analysis fields (optional)
    llm_verdict: Optional[str] = None  # PASS/FAIL/WARNING/SKIP
    llm_confidence: Optional[float] = None  # 0.0-1.0
    error_analysis: Optional[str] = None
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None

    # Metadata
    timestamp: Optional[datetime] = None


class EnhancedCSVWriter:
    """
    Write test results with AI analysis to CSV.

    Extends standard CSV format with additional columns for LLM validation
    and automated error analysis. Maintains backward compatibility.

    New Columns:
        - llm_verdict: LLM validation verdict (PASS/FAIL/WARNING/SKIP)
        - llm_confidence: LLM confidence score (0.0-1.0)
        - error_analysis: AI-generated error analysis summary
        - root_cause: Root cause identified from logs
        - suggested_fix: AI-suggested fix for the issue

    Usage:
        writer = EnhancedCSVWriter("tests/output/guest/week1_enhanced.csv")
        writer.write_results([
            EnhancedTestResult(
                test_type="test_guest_chat_bitcoin",
                device="chrome",
                is_multi_step=False,
                inputs=["What is Bitcoin?"],
                outputs=["Bitcoin is a cryptocurrency..."],
                test_pass=True,
                llm_verdict="PASS",
                llm_confidence=0.95,
            )
        ])
    """

    # Standard CSV columns (original format)
    STANDARD_COLUMNS = [
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
    ]

    # AI analysis columns (new)
    AI_ANALYSIS_COLUMNS = [
        "llm_verdict",
        "llm_confidence",
        "error_analysis",
        "root_cause",
        "suggested_fix",
    ]

    # All columns combined
    ALL_COLUMNS = STANDARD_COLUMNS + AI_ANALYSIS_COLUMNS

    def __init__(self, output_file: str, enable_ai_columns: bool = True):
        """
        Initialize enhanced CSV writer.

        Args:
            output_file: Path to output CSV file
            enable_ai_columns: Whether to include AI analysis columns (default: True)
        """
        self.output_file = Path(output_file)
        self.enable_ai_columns = enable_ai_columns

        # Create output directory if needed
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Determine columns to use
        self.columns = self.ALL_COLUMNS if enable_ai_columns else self.STANDARD_COLUMNS

    def write_results(self, results: list[EnhancedTestResult], append: bool = False):
        """
        Write test results to CSV.

        Args:
            results: List of test results to write
            append: Whether to append to existing file (default: False)
        """
        mode = "a" if append else "w"
        write_header = not append or not self.output_file.exists()

        try:
            with self.output_file.open(mode, newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)

                # Write header if needed
                if write_header:
                    writer.writeheader()

                # Write each result
                for result in results:
                    row = self._result_to_row(result)
                    writer.writerow(row)

            logger.info(f"Wrote {len(results)} test results to {self.output_file}")

        except Exception as e:
            logger.error(f"Failed to write CSV results: {e}")
            raise

    def write_single_result(self, result: EnhancedTestResult, append: bool = True):
        """
        Write a single test result to CSV.

        Args:
            result: Test result to write
            append: Whether to append to existing file (default: True)
        """
        self.write_results([result], append=append)

    def add_ai_analysis(
        self,
        result: EnhancedTestResult,
        validation_result: Optional[ValidationResult] = None,
        error_analysis: Optional[ErrorAnalysis] = None,
    ) -> EnhancedTestResult:
        """
        Add AI analysis to a test result.

        Args:
            result: Original test result
            validation_result: LLM validation result
            error_analysis: Log analysis result

        Returns:
            Enhanced test result with AI analysis
        """
        # Add LLM validation data
        if validation_result:
            result.llm_verdict = validation_result.verdict.value
            result.llm_confidence = validation_result.confidence

            # If validation found issues, add to error analysis
            if validation_result.semantic_issues:
                result.error_analysis = "; ".join(validation_result.semantic_issues)

        # Add error analysis data
        if error_analysis:
            result.root_cause = error_analysis.root_cause
            result.suggested_fix = error_analysis.suggested_fix

            # If no error analysis yet, use root cause as analysis
            if not result.error_analysis:
                result.error_analysis = f"[{error_analysis.error_type.value}] {error_analysis.root_cause}"

        return result

    def _result_to_row(self, result: EnhancedTestResult) -> dict[str, Any]:
        """Convert test result to CSV row."""
        # Build standard columns
        row = {
            "Type": result.test_type,
            "device": result.device,
            "is multi step": "YES" if result.is_multi_step else "NO",
            "test pass": "PASS" if result.test_pass else "FAIL",
        }

        # Add input/output columns (up to 4 steps)
        for i in range(4):
            input_key = f"input {i + 1}"
            output_key = f"output {i + 1}"

            if i < len(result.inputs):
                row[input_key] = self._clean_cell_value(result.inputs[i])
            else:
                row[input_key] = ""

            if i < len(result.outputs):
                row[output_key] = self._clean_cell_value(result.outputs[i])
            else:
                row[output_key] = ""

        # Add AI analysis columns if enabled
        if self.enable_ai_columns:
            row["llm_verdict"] = result.llm_verdict or ""
            row["llm_confidence"] = f"{result.llm_confidence:.2f}" if result.llm_confidence is not None else ""
            row["error_analysis"] = self._clean_cell_value(result.error_analysis or "")
            row["root_cause"] = self._clean_cell_value(result.root_cause or "")
            row["suggested_fix"] = self._clean_cell_value(result.suggested_fix or "")

        return row

    def _clean_cell_value(self, value: str) -> str:
        """Clean cell value for CSV (remove newlines, truncate long values)."""
        if not value:
            return ""

        # Replace newlines with spaces
        value = value.replace("\n", " ").replace("\r", " ")

        # Truncate very long values (keep first 500 chars)
        if len(value) > 500:
            value = value[:497] + "..."

        # Remove extra whitespace
        value = " ".join(value.split())

        return value

    @classmethod
    def from_validation_and_analysis(
        cls,
        test_type: str,
        device: str,
        is_multi_step: bool,
        inputs: list[str],
        outputs: list[str],
        test_pass: bool,
        validation_result: Optional[ValidationResult] = None,
        error_analysis: Optional[ErrorAnalysis] = None,
    ) -> EnhancedTestResult:
        """
        Create an enhanced test result from validation and analysis.

        Convenience method to build result with AI analysis in one call.

        Args:
            test_type: Test identifier
            device: Device type (chrome, firefox, etc.)
            is_multi_step: Whether test is multi-step
            inputs: List of user inputs
            outputs: List of agent outputs
            test_pass: Whether test passed
            validation_result: Optional LLM validation result
            error_analysis: Optional log analysis result

        Returns:
            EnhancedTestResult with AI analysis
        """
        result = EnhancedTestResult(
            test_type=test_type,
            device=device,
            is_multi_step=is_multi_step,
            inputs=inputs,
            outputs=outputs,
            test_pass=test_pass,
            timestamp=datetime.utcnow(),
        )

        # Add AI analysis
        if validation_result:
            result.llm_verdict = validation_result.verdict.value
            result.llm_confidence = validation_result.confidence

            if validation_result.semantic_issues:
                result.error_analysis = "; ".join(validation_result.semantic_issues)

        if error_analysis:
            result.root_cause = error_analysis.root_cause
            result.suggested_fix = error_analysis.suggested_fix

            if not result.error_analysis:
                result.error_analysis = f"[{error_analysis.error_type.value}] {error_analysis.root_cause}"

        return result


# Convenience functions for backward compatibility
def write_standard_csv(output_file: str, results: list[EnhancedTestResult]):
    """Write results in standard CSV format (no AI columns)."""
    writer = EnhancedCSVWriter(output_file, enable_ai_columns=False)
    writer.write_results(results)


def write_enhanced_csv(output_file: str, results: list[EnhancedTestResult]):
    """Write results in enhanced CSV format (with AI columns)."""
    writer = EnhancedCSVWriter(output_file, enable_ai_columns=True)
    writer.write_results(results)
