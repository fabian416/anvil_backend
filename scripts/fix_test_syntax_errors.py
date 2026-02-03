#!/usr/bin/env python3
"""
Fix syntax errors in test files caused by misplaced LLM validation code.

The issue: LLM validation code was incorrectly placed inside function parameter
lists instead of being in the function body. This script removes those blocks.
"""

import re
import sys
from pathlib import Path

# Files with syntax errors
FILES_TO_FIX = [
    "tests/integration/guest/general/test_agent_squad_ultra_hunter_full.py",
    "tests/integration/guest/general/test_common_informational_queries.py",
    "tests/integration/guest/general/test_cross_chain_comprehensive.py",
    "tests/integration/guest/general/test_hunter_chat_integration.py",
    "tests/integration/guest/general/test_interruption_flows.py",
    "tests/integration/guest/general/test_low_coverage_intents.py",
    "tests/integration/guest/general/test_multi_intent_end_to_end.py",
    "tests/integration/guest/general/test_multilanguage_comprehensive.py",
    "tests/integration/guest/general/test_redis_metrics_collector.py",
    "tests/integration/guest/general/test_shortcuts_edge_cases.py",
    "tests/integration/guest/general/test_unified_chat_critical_paths.py",
    "tests/integration/guest/general/test_unified_chat_with_test_data.py",
    "tests/integration/guest/general/test_user_chat_messages.py",
    "tests/integration/guest/knowledge/test_knowledge_injection_api.py",
]


def fix_file(filepath: Path) -> tuple[bool, str]:
    """
    Fix syntax error in a test file.

    Returns:
        (success, message)
    """
    try:
        content = filepath.read_text()
        original_content = content

        # Pattern: Find misplaced validation code in function parameters
        # The pattern is:
        #   async def test_something(
        #       self,
        #       some_param: Type,
        #
        #   # Optional LLM semantic validation...
        #   if llm_validator.enabled:
        #       ...
        #
        #   another_param: Type,
        #   ):

        # Strategy: Find and remove the entire validation block that's between parameters
        # Look for the pattern:
        # 1. Empty line after parameter
        # 2. Comment starting with "# Optional LLM"
        # 3. if llm_validator.enabled: block
        # 4. Another parameter follows

        # Use regex to find and remove the misplaced validation blocks
        pattern = r"\n\n    # Optional LLM semantic validation.*?\n    if llm_validator\.enabled:.*?(?=\n    \w+:)"

        # Remove all occurrences
        content = re.sub(pattern, "", content, flags=re.DOTALL)

        if content == original_content:
            return False, "No changes needed"

        # Write back
        filepath.write_text(content)

        # Try to compile to verify
        try:
            compile(content, str(filepath), "exec")
            return True, "Fixed successfully"
        except SyntaxError as e:
            # Restore original if compilation fails
            filepath.write_text(original_content)
            return False, f"Compilation failed after fix: {e}"

    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Fix all files with syntax errors."""
    print("=" * 70)
    print("Fixing Test Syntax Errors")
    print("=" * 70)

    project_root = Path(__file__).parent.parent

    fixed_count = 0
    failed_count = 0
    skipped_count = 0

    for filepath_str in FILES_TO_FIX:
        filepath = project_root / filepath_str

        if not filepath.exists():
            print(f"\n❌ {filepath_str}")
            print(f"   File not found")
            failed_count += 1
            continue

        print(f"\n📝 {filepath_str}")
        success, message = fix_file(filepath)

        if success:
            print(f"   ✅ {message}")
            fixed_count += 1
        elif "No changes needed" in message:
            print(f"   ⏭️  {message}")
            skipped_count += 1
        else:
            print(f"   ❌ {message}")
            failed_count += 1

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"✅ Fixed: {fixed_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Total: {len(FILES_TO_FIX)}")

    if fixed_count > 0:
        print("\n✅ Successfully fixed files!")
        return 0
    elif failed_count > 0:
        print("\n❌ Some files failed to fix")
        return 1
    else:
        print("\n⏭️  No files needed fixing")
        return 0


if __name__ == "__main__":
    sys.exit(main())
