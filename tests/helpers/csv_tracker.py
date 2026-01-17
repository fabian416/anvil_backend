"""
CSV Test Tracker - Track test execution with LLM validation results.

Writes test execution data to CSV files organized by user type and category.
Provides historical tracking of test inputs, outputs, and quality metrics.
"""

import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TestExecutionData:
    """Test execution data for CSV tracking (11 standard + 12 enhanced fields)."""

    # Standard 11 columns (existing)
    test_id: str                    # Unique test identifier
    s_multistep: bool               # Is this a multi-turn conversation
    input: str                      # User query/input
    output: str                     # Agent response/output
    test_label_sequence: str        # Agent flow (e.g., "hunter→ultra", "shortcut_swap_step1->step2")
    output_expected: str            # Expected behavior description
    status: str                     # PASS/FAIL
    date: str                       # ISO timestamp
    quality: Optional[float]        # LLM confidence score (0.0-1.0) / overall_score
    qa_status: Optional[str]        # LLM validation verdict (PASS/FAIL/WARN/SKIPPED)
    qa_output: Optional[str]        # LLM reasoning/explanation

    # NEW: Granular scores (4 columns)
    accuracy_score: Optional[float] = None          # Factual correctness (0.0-1.0)
    relevance_score: Optional[float] = None         # Query relevance (0.0-1.0)
    safety_score: Optional[float] = None            # Security/disclaimers (0.0-1.0)
    coherence_score: Optional[float] = None         # Logical consistency (0.0-1.0)

    # NEW: Test metadata (4 columns)
    test_category: Optional[str] = None             # e.g., "hunter", "flows", "errors"
    test_type: Optional[str] = None                 # e.g., "simple_query", "multi_step"
    expected_intents: Optional[str] = None          # JSON array as string
    token_usage: Optional[int] = None               # LLM tokens consumed

    # NEW: Recommendations (4 columns)
    improvement_suggestions: Optional[str] = None   # JSON array as string
    critical_issues: Optional[str] = None           # JSON array as string
    next_steps: Optional[str] = None                # JSON array as string
    model_used: Optional[str] = None                # e.g., "meta-llama/Meta-Llama-3.1-70B-Instruct"


class CSVTestTracker:
    """
    Track test execution to CSV files organized by user type and category.

    File Structure:
        tests/output/{guest,user}/{category}.csv

    Columns:
        - test_id: Unique test identifier
        - s_multistep: Boolean for multi-turn conversations
        - input: User query text
        - output: Agent response text (truncated to 200 chars)
        - test_label_sequence: Agent flow sequence
        - output_expected: Expected behavior description
        - status: PASS/FAIL
        - date: ISO timestamp
        - quality: LLM confidence (0.0-1.0)
        - qa_status: LLM verdict (PASS/FAIL/WARN/SKIPPED)
        - qa_output: LLM reasoning (truncated to 200 chars)

    Usage:
        tracker = CSVTestTracker()
        tracker.track("guest", "hunter", TestExecutionData(...))
    """

    # Standard 11 columns (backward compatible)
    COLUMNS = [
        "test_id",
        "s_multistep",
        "input",
        "output",
        "test_label_sequence",
        "output_expected",
        "status",
        "date",
        "quality",
        "qa_status",
        "qa_output",
    ]

    # Enhanced 23 columns (standard + 12 new)
    ENHANCED_COLUMNS = [
        # Standard 11
        "test_id",
        "s_multistep",
        "input",
        "output",
        "test_label_sequence",
        "output_expected",
        "status",
        "date",
        "quality",
        "qa_status",
        "qa_output",
        # Granular scores (4)
        "accuracy_score",
        "relevance_score",
        "safety_score",
        "coherence_score",
        # Test metadata (4)
        "test_category",
        "test_type",
        "expected_intents",
        "token_usage",
        # Recommendations (4)
        "improvement_suggestions",
        "critical_issues",
        "next_steps",
        "model_used",
    ]

    def __init__(self, base_path: str = "tests/output"):
        """
        Initialize CSV test tracker.

        Args:
            base_path: Base directory for output files (default: tests/output)
        """
        import os

        self.base_path = Path(base_path)
        # NEW: Check if enhanced CSV export is enabled
        self.write_enhanced = os.getenv("WRITE_ENHANCED_CSV", "false").lower() == "true"

        if self.write_enhanced:
            logger.info("Enhanced CSV export ENABLED (23 columns)")
        else:
            logger.info("Standard CSV export (11 columns) - Set WRITE_ENHANCED_CSV=true for enhanced")

    def track(self, user_type: str, category: str, data: TestExecutionData):
        """
        Track a test execution to CSV file(s) - standard and optionally enhanced.

        Args:
            user_type: "guest" or "user"
            category: Test category (hunter, ultra, agent_squad, etc.)
            data: Test execution data to record
        """
        # Determine output directory
        output_dir = self.base_path / user_type
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write to standard CSV (11 columns) - always
        self._write_standard_csv(output_dir, category, data)

        # Write to enhanced CSV (23 columns) - if enabled
        if self.write_enhanced:
            self._write_enhanced_csv(output_dir, category, data)

    def _write_standard_csv(self, output_dir: Path, category: str, data: TestExecutionData):
        """Write to standard 11-column CSV (backward compatible)."""
        output_file = output_dir / f"{category}.csv"
        file_exists = output_file.exists()

        try:
            with output_file.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.COLUMNS)

                if not file_exists:
                    writer.writeheader()

                row = self._data_to_row(data)
                writer.writerow(row)

            logger.debug(
                f"Tracked test execution: {data.test_id} -> "
                f"{output_file} ({data.status})"
            )

        except Exception as e:
            logger.error(f"Failed to track test execution to standard CSV: {e}")

    def _write_enhanced_csv(self, output_dir: Path, category: str, data: TestExecutionData):
        """Write to enhanced 23-column CSV."""
        output_file = output_dir / f"{category}_enhanced.csv"
        file_exists = output_file.exists()

        try:
            with output_file.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.ENHANCED_COLUMNS)

                if not file_exists:
                    writer.writeheader()

                row = self._data_to_enhanced_row(data)
                writer.writerow(row)

            logger.debug(
                f"Tracked enhanced test execution: {data.test_id} -> "
                f"{output_file} ({data.status})"
            )

        except Exception as e:
            logger.error(f"Failed to track test execution to enhanced CSV: {e}")

    def _data_to_row(self, data: TestExecutionData) -> dict:
        """Convert test execution data to standard CSV row (11 columns)."""
        return {
            "test_id": data.test_id,
            "s_multistep": "true" if data.s_multistep else "false",
            "input": self._truncate(data.input, 200),
            "output": self._truncate(data.output, 200),
            "test_label_sequence": data.test_label_sequence,
            "output_expected": self._truncate(data.output_expected, 200),
            "status": data.status,
            "date": data.date,
            "quality": f"{data.quality:.2f}" if data.quality is not None else "",
            "qa_status": data.qa_status or "",
            "qa_output": self._truncate(data.qa_output or "", 200),
        }

    def _data_to_enhanced_row(self, data: TestExecutionData) -> dict:
        """Convert test execution data to enhanced CSV row (23 columns)."""
        return {
            # Standard 11 columns
            "test_id": data.test_id,
            "s_multistep": "true" if data.s_multistep else "false",
            "input": self._truncate(data.input, 200),
            "output": self._truncate(data.output, 200),
            "test_label_sequence": data.test_label_sequence,
            "output_expected": self._truncate(data.output_expected, 200),
            "status": data.status,
            "date": data.date,
            "quality": f"{data.quality:.2f}" if data.quality is not None else "",
            "qa_status": data.qa_status or "",
            "qa_output": self._truncate(data.qa_output or "", 200),
            # Granular scores (4 columns)
            "accuracy_score": f"{data.accuracy_score:.2f}" if data.accuracy_score is not None else "",
            "relevance_score": f"{data.relevance_score:.2f}" if data.relevance_score is not None else "",
            "safety_score": f"{data.safety_score:.2f}" if data.safety_score is not None else "",
            "coherence_score": f"{data.coherence_score:.2f}" if data.coherence_score is not None else "",
            # Test metadata (4 columns)
            "test_category": data.test_category or "",
            "test_type": data.test_type or "",
            "expected_intents": data.expected_intents or "",
            "token_usage": str(data.token_usage) if data.token_usage is not None else "",
            # Recommendations (4 columns)
            "improvement_suggestions": self._truncate(data.improvement_suggestions or "", 200),
            "critical_issues": self._truncate(data.critical_issues or "", 200),
            "next_steps": self._truncate(data.next_steps or "", 200),
            "model_used": data.model_used or "",
        }

    def _truncate(self, text: str, max_length: int = 200) -> str:
        """Truncate text and clean for CSV."""
        if not text:
            return ""

        # Replace newlines with spaces
        text = text.replace("\n", " ").replace("\r", " ")

        # Remove extra whitespace
        text = " ".join(text.split())

        # Truncate if too long
        if len(text) > max_length:
            return text[:max_length - 3] + "..."

        return text


# Convenience function for tracking from test fixtures
def track_test_execution(
    user_type: str,
    category: str,
    test_id: str,
    input_text: str,
    output_text: str,
    test_label_sequence: str,
    output_expected: str,
    status: str,
    s_multistep: bool = False,
    quality: Optional[float] = None,
    qa_status: Optional[str] = None,
    qa_output: Optional[str] = None,
):
    """
    Convenience function to track test execution.

    Args:
        user_type: "guest" or "user"
        category: Test category (hunter, ultra, agent_squad, etc.)
        test_id: Unique test identifier
        input_text: User query/input
        output_text: Agent response/output
        test_label_sequence: Agent flow sequence
        output_expected: Expected behavior description
        status: PASS/FAIL
        s_multistep: Is multi-turn conversation (default: False)
        quality: LLM confidence score (0.0-1.0)
        qa_status: LLM validation verdict
        qa_output: LLM reasoning
    """
    tracker = CSVTestTracker()
    data = TestExecutionData(
        test_id=test_id,
        s_multistep=s_multistep,
        input=input_text,
        output=output_text,
        test_label_sequence=test_label_sequence,
        output_expected=output_expected,
        status=status,
        date=datetime.utcnow().isoformat(),
        quality=quality,
        qa_status=qa_status,
        qa_output=qa_output,
    )
    tracker.track(user_type, category, data)
