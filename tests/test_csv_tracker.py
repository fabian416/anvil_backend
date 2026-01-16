"""
Test CSV tracker functionality.

Verifies CSV tracking system works correctly.
"""

import pytest
from datetime import datetime
from pathlib import Path

from tests.helpers.csv_tracker import CSVTestTracker, TestExecutionData


# Skip database cleanup for unit tests
pytestmark = pytest.mark.no_db


@pytest.mark.unit
def test_csv_tracker_creates_file(tmp_path):
    """Test CSV tracker creates file correctly."""
    tracker = CSVTestTracker(base_path=str(tmp_path))

    data = TestExecutionData(
        test_id="test_001",
        s_multistep=False,
        input="What is Bitcoin?",
        output="Bitcoin is a decentralized cryptocurrency...",
        test_label_sequence="hunter_ai",
        output_expected="Bitcoin explanation",
        status="PASS",
        date=datetime.utcnow().isoformat(),
        quality=0.95,
        qa_status="PASS",
        qa_output="Response is accurate and informative",
    )

    tracker.track("guest", "hunter", data)

    # Verify file created
    output_file = tmp_path / "guest" / "hunter.csv"
    assert output_file.exists()

    # Verify content
    content = output_file.read_text()
    assert "test_001" in content
    assert "What is Bitcoin?" in content
    assert "PASS" in content


@pytest.mark.unit
def test_csv_tracker_appends_rows(tmp_path):
    """Test CSV tracker appends to existing file."""
    tracker = CSVTestTracker(base_path=str(tmp_path))

    # Track first execution
    data1 = TestExecutionData(
        test_id="test_001",
        s_multistep=False,
        input="Query 1",
        output="Response 1",
        test_label_sequence="hunter_ai",
        output_expected="Expected 1",
        status="PASS",
        date=datetime.utcnow().isoformat(),
        quality=0.9,
        qa_status="PASS",
        qa_output="Good",
    )
    tracker.track("guest", "hunter", data1)

    # Track second execution
    data2 = TestExecutionData(
        test_id="test_002",
        s_multistep=True,
        input="Query 2",
        output="Response 2",
        test_label_sequence="hunter→ultra",
        output_expected="Expected 2",
        status="PASS",
        date=datetime.utcnow().isoformat(),
        quality=0.85,
        qa_status="PASS",
        qa_output="Acceptable",
    )
    tracker.track("guest", "hunter", data2)

    # Verify both rows present
    output_file = tmp_path / "guest" / "hunter.csv"
    content = output_file.read_text()
    assert "test_001" in content
    assert "test_002" in content
    assert "Query 1" in content
    assert "Query 2" in content


@pytest.mark.unit
def test_csv_tracker_truncates_long_text(tmp_path):
    """Test CSV tracker truncates long text."""
    tracker = CSVTestTracker(base_path=str(tmp_path))

    # Create very long output
    long_output = "A" * 500  # 500 characters

    data = TestExecutionData(
        test_id="test_001",
        s_multistep=False,
        input="Query",
        output=long_output,
        test_label_sequence="hunter_ai",
        output_expected="Expected",
        status="PASS",
        date=datetime.utcnow().isoformat(),
        quality=0.9,
        qa_status="PASS",
        qa_output="Good",
    )

    tracker.track("guest", "hunter", data)

    # Verify truncation
    output_file = tmp_path / "guest" / "hunter.csv"
    content = output_file.read_text()
    # Output should be truncated to ~200 chars + "..."
    assert "..." in content
    assert len(content) < 1000  # Should be much shorter than original


@pytest.mark.unit
def test_csv_tracker_handles_missing_optional_fields(tmp_path):
    """Test CSV tracker handles missing optional fields."""
    tracker = CSVTestTracker(base_path=str(tmp_path))

    data = TestExecutionData(
        test_id="test_001",
        s_multistep=False,
        input="Query",
        output="Response",
        test_label_sequence="hunter_ai",
        output_expected="Expected",
        status="PASS",
        date=datetime.utcnow().isoformat(),
        quality=None,  # Missing
        qa_status=None,  # Missing
        qa_output=None,  # Missing
    )

    # Should not raise exception
    tracker.track("guest", "hunter", data)

    # Verify file created
    output_file = tmp_path / "guest" / "hunter.csv"
    assert output_file.exists()
