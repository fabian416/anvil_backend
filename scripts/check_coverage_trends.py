#!/usr/bin/env python3
"""
Check coverage trends over time.

Compares current coverage with historical data to detect regressions.
Used by coverage-report.yml workflow.
"""

import json
import sys
from pathlib import Path


def load_coverage_json(path: str = "coverage.json") -> dict | None:
    """Load coverage JSON report."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Coverage file not found: {path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in coverage file: {e}")
        return None


def get_total_coverage(data: dict) -> float:
    """Extract total coverage percentage from coverage data."""
    if not data:
        return 0.0

    totals = data.get("totals", {})
    covered = totals.get("covered_lines", 0)
    total = totals.get("num_statements", 1)  # Avoid division by zero

    return (covered / total) * 100 if total > 0 else 0.0


def check_coverage_threshold(coverage: float, threshold: float = 60.0) -> bool:
    """Check if coverage meets minimum threshold."""
    return coverage >= threshold


def main():
    """Main entry point."""
    print("=" * 60)
    print("Coverage Trend Analysis")
    print("=" * 60)

    # Load current coverage
    coverage_data = load_coverage_json()
    if not coverage_data:
        print("\n⚠️  Could not load coverage data. Skipping trend check.")
        sys.exit(0)  # Don't fail workflow if no coverage data

    current_coverage = get_total_coverage(coverage_data)
    print(f"\n📊 Current Coverage: {current_coverage:.2f}%")

    # Check minimum threshold
    min_threshold = 60.0
    if check_coverage_threshold(current_coverage, min_threshold):
        print(f"✅ Coverage meets minimum threshold ({min_threshold}%)")
    else:
        print(f"❌ Coverage below minimum threshold ({min_threshold}%)")
        print(f"   Current: {current_coverage:.2f}% < Required: {min_threshold}%")
        sys.exit(1)

    # Check for coverage regression (if historical data exists)
    history_file = Path(".coverage_history.json")
    if history_file.exists():
        try:
            with open(history_file) as f:
                history = json.load(f)

            last_coverage = history.get("last_coverage", 0)
            if current_coverage < last_coverage - 2.0:  # Allow 2% variance
                print(f"⚠️  Coverage regression detected!")
                print(f"   Previous: {last_coverage:.2f}%")
                print(f"   Current: {current_coverage:.2f}%")
                print(f"   Difference: {current_coverage - last_coverage:.2f}%")
        except (json.JSONDecodeError, KeyError):
            pass

    # Save current coverage to history
    try:
        with open(history_file, "w") as f:
            json.dump({"last_coverage": current_coverage}, f)
    except IOError:
        pass  # Non-critical

    print("\n" + "=" * 60)
    print("Coverage trend check completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
