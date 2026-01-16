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
    """Test execution data for CSV tracking."""

    test_id: str                    # Unique test identifier
    s_multistep: bool               # Is this a multi-turn conversation
    input: str                      # User query/input
    output: str                     # Agent response/output
    test_label_sequence: str        # Agent flow (e.g., "hunter→ultra", "shortcut_swap_step1->step2")
    output_expected: str            # Expected behavior description
    status: str                     # PASS/FAIL
    date: str                       # ISO timestamp
    quality: Optional[float]        # LLM confidence score (0.0-1.0)
    qa_status: Optional[str]        # LLM validation verdict (PASS/FAIL/WARN/SKIPPED)
    qa_output: Optional[str]        # LLM reasoning/explanation


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

    def __init__(self, base_path: str = "tests/output"):
        """
        Initialize CSV test tracker.

        Args:
            base_path: Base directory for output files (default: tests/output)
        """
        self.base_path = Path(base_path)

    def track(self, user_type: str, category: str, data: TestExecutionData):
        """
        Track a test execution to the appropriate CSV file.

        Args:
            user_type: "guest" or "user"
            category: Test category (hunter, ultra, agent_squad, etc.)
            data: Test execution data to record
        """
        # Determine output file path
        output_dir = self.base_path / user_type
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{category}.csv"

        # Check if file exists to determine if we need header
        file_exists = output_file.exists()

        try:
            # Append row to CSV
            with output_file.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.COLUMNS)

                # Write header if new file
                if not file_exists:
                    writer.writeheader()

                # Write data row
                row = self._data_to_row(data)
                writer.writerow(row)

            logger.debug(
                f"Tracked test execution: {data.test_id} -> "
                f"{output_file} ({data.status})"
            )

        except Exception as e:
            logger.error(f"Failed to track test execution to CSV: {e}")
            # Don't raise - tracking failures shouldn't break tests

    def _data_to_row(self, data: TestExecutionData) -> dict:
        """Convert test execution data to CSV row."""
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
