#!/usr/bin/env python3
"""
Phase 4 Test Updater - Automated test file updates for enhanced validation.

Updates test files with:
1. Required imports (json, warnings, datetime)
2. test_func parameter for LLM validation
3. Enhanced CSV tracking (12 new fields)
4. Proper warning handling
"""

import re
import sys
from pathlib import Path
from typing import Optional


class Phase4TestUpdater:
    """Automates Phase 4 test file updates."""

    def __init__(self, test_file_path: str):
        self.test_file_path = Path(test_file_path)
        self.content = ""
        self.updated = False

    def read_file(self) -> bool:
        """Read the test file content."""
        try:
            self.content = self.test_file_path.read_text(encoding="utf-8")
            return True
        except Exception as e:
            print(f"Error reading {self.test_file_path}: {e}")
            return False

    def check_already_updated(self) -> bool:
        """Check if file already has Phase 3/4 updates."""
        # Check for Phase 3 markers
        markers = [
            "# PHASE 3:",
            "# Enhanced 12 fields (PHASE 3)",
            "test_func=self.",
            "import json",
            "import warnings",
        ]

        found_markers = sum(1 for marker in markers if marker in self.content)

        if found_markers >= 3:
            print(
                f"✓ {self.test_file_path.name} already updated (found {found_markers}/5 markers)"
            )
            return True

        return False

    def add_imports(self) -> bool:
        """Add required imports if not present."""
        changed = False

        # Check if imports already exist
        has_json = "import json" in self.content
        has_warnings = "import warnings" in self.content
        has_datetime = "from datetime import datetime" in self.content

        if has_json and has_warnings:
            return False  # Already has imports

        # Find the import section (after docstring, before class/function definitions)
        import_pattern = r'(""".*?"""\s*\n\n)(import\s+)'
        match = re.search(import_pattern, self.content, re.DOTALL)

        if match:
            # Insert after docstring, before other imports
            insert_pos = match.end(1)
            new_imports = []

            if not has_json:
                new_imports.append("import json")
            if not has_warnings:
                new_imports.append("import warnings")
            if not has_datetime:
                new_imports.append("from datetime import datetime")

            if new_imports:
                imports_text = "\n".join(new_imports) + "\n\n"
                self.content = (
                    self.content[:insert_pos] + imports_text + self.content[insert_pos:]
                )
                changed = True
                print(f"  + Added imports: {', '.join(new_imports)}")

        return changed

    def update_llm_validation_calls(self) -> int:
        """Update LLM validation calls to add test_func parameter."""
        count = 0

        # Pattern: await llm_validator.validate_single_response(
        #   test_name="...",
        #   ...
        #   additional_context={...}
        # )
        # WITHOUT test_func parameter

        pattern = r'(await llm_validator\.validate_single_response\([^)]+?test_name="([^"]+)"[^)]+?)(additional_context=)'

        def replace_validation(match):
            nonlocal count
            full_match = match.group(0)

            # Check if already has test_func
            if "test_func=" in full_match:
                return full_match

            test_name = match.group(2)
            before = match.group(1)
            additional = match.group(3)

            # Extract method name from test_name
            # test_name like "test_sentiment_basic" -> method "test_sentiment_basic"
            method_name = test_name

            # Add test_func parameter before additional_context
            replacement = (
                f"{before}"
                f"test_func=self.{method_name},  # PHASE 3: Custom prompt generation\n"
                f"                {additional}"
            )

            count += 1
            return replacement

        self.content = re.sub(pattern, replace_validation, self.content)

        if count > 0:
            print(
                f"  + Updated {count} LLM validation call(s) with test_func parameter"
            )

        return count

    def update_pytest_warn_to_warnings(self) -> int:
        """Replace pytest.warn with warnings.warn."""
        count = 0

        # Pattern: pytest.warn(UserWarning(...))
        pattern = r"pytest\.warn\(UserWarning\((.*?)\)\)"

        def replace_warn(match):
            nonlocal count
            content = match.group(1)
            count += 1
            return f"warnings.warn({content})"

        self.content = re.sub(pattern, replace_warn, self.content, flags=re.DOTALL)

        if count > 0:
            print(f"  + Replaced {count} pytest.warn with warnings.warn")

        return count

    def update_csv_tracking(self) -> int:
        """Update CSV tracking to use enhanced validation fields."""
        count = 0

        # Pattern: await csv_tracker("...", "...", {
        #   ...
        #   "quality": validation.confidence if validation else None,
        #   "qa_status": validation.verdict if validation else "SKIPPED",
        #   "qa_output": validation.reasoning if validation else None,
        # })

        # Look for old-style CSV tracking (without enhanced fields)
        pattern = r'(await csv_tracker\([^{]+?\{[^}]+?)"quality":\s*validation\.confidence[^}]+?"qa_output":\s*validation\.reasoning[^}]+?\}'

        def replace_csv(match):
            nonlocal count
            before = match.group(1)

            # Check if already has enhanced fields
            if "accuracy_score" in before or "# Enhanced 12 fields" in before:
                return match.group(0)

            # Build replacement with enhanced fields
            replacement = (
                before
                + """"quality": validation.scoring.overall_score if validation and validation.scoring else None,
            "qa_status": validation.verdict.value if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            # Enhanced 12 fields (PHASE 3)
            "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
            "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
            "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
            "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
            "test_category": validation.metadata.test_category if validation and validation.metadata else None,
            "test_type": validation.metadata.test_type if validation and validation.metadata else None,
            "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
            "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
            "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
            "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
            "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
            "model_used": validation.metadata.model_used if validation and validation.metadata else None,
        })"""
            )

            count += 1
            return replacement

        self.content = re.sub(pattern, replace_csv, self.content, flags=re.DOTALL)

        if count > 0:
            print(f"  + Updated {count} CSV tracking call(s) with enhanced fields")

        return count

    def write_file(self) -> bool:
        """Write updated content back to file."""
        try:
            self.test_file_path.write_text(self.content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"Error writing {self.test_file_path}: {e}")
            return False

    def update(self) -> bool:
        """Perform full update on test file."""
        print(f"\n📝 Processing: {self.test_file_path.name}")

        if not self.read_file():
            return False

        if self.check_already_updated():
            return True

        changes = 0

        # Apply updates
        if self.add_imports():
            changes += 1

        changes += self.update_llm_validation_calls()
        changes += self.update_pytest_warn_to_warnings()
        changes += self.update_csv_tracking()

        if changes > 0:
            if self.write_file():
                print(
                    f"✅ Updated {self.test_file_path.name} ({changes} change groups)"
                )
                self.updated = True
                return True
            else:
                print(f"❌ Failed to write {self.test_file_path.name}")
                return False
        else:
            print(f"⚠️  No changes needed for {self.test_file_path.name}")
            return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python phase4_test_updater.py <test_file_or_directory>")
        print("\nExample:")
        print("  python phase4_test_updater.py tests/integration/guest/hunter/")
        print(
            "  python phase4_test_updater.py tests/integration/guest/hunter/test_*.py"
        )
        sys.exit(1)

    target = Path(sys.argv[1])

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(target.glob("test_*.py"))
    else:
        # Glob pattern
        files = sorted(Path(".").glob(str(target)))

    if not files:
        print(f"No test files found: {target}")
        sys.exit(1)

    print(f"🚀 Phase 4 Test Updater")
    print(f"📂 Found {len(files)} test file(s)")

    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for test_file in files:
        updater = Phase4TestUpdater(str(test_file))
        if updater.update():
            if updater.updated:
                updated_count += 1
            else:
                skipped_count += 1
        else:
            failed_count += 1

    print(f"\n📊 Summary:")
    print(f"   ✅ Updated: {updated_count}")
    print(f"   ⏭️  Skipped: {skipped_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📝 Total: {len(files)}")


if __name__ == "__main__":
    main()
