#!/usr/bin/env python3
"""
Fix orphaned llm_validator blocks in test files.

These blocks were left behind when llm_validator parameters were removed from test functions,
causing syntax errors because the validation code is now outside the function body.

Usage:
    python scripts/fix_orphaned_llm_validator.py <file_path>
    python scripts/fix_orphaned_llm_validator.py --all
"""

import re
import sys
from pathlib import Path


def remove_llm_validator_blocks(content: str) -> str:
    """Remove all orphaned llm_validator blocks from content."""

    # Pattern to match the orphaned validation blocks
    # They start with "# Optional LLM semantic validation" and end with the closing parenthesis
    patterns = [
        # Pattern 1: Block inside function signature (most common)
        r"\n\s*# Optional LLM semantic validation \(environment-gated\)\s*\n\s*if llm_validator\.enabled:.*?(?=\n\s*(?:async def|def|class|@pytest|\Z))",
        # Pattern 2: Standalone validation block at wrong indent
        r"\n    # Optional LLM semantic validation \(environment-gated\)\s*\n    if llm_validator\.enabled:\s*\n(?:        .*\n)*?(?:    (?:if validation\.verdict|$).*\n(?:        .*\n)*)?",
    ]

    # Remove blocks using simpler approach - line by line
    lines = content.split("\n")
    result_lines = []
    skip_mode = False
    skip_indent = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect start of orphaned block
        if (
            "# Optional LLM semantic validation" in line
            and "if llm_validator.enabled" not in line
        ):
            # Check next line for the if statement
            if i + 1 < len(lines) and "if llm_validator.enabled:" in lines[i + 1]:
                # Get indent level of this block
                skip_indent = len(line) - len(line.lstrip())
                skip_mode = True
                i += 1  # Skip comment line
                continue

        # Detect standalone if llm_validator.enabled
        if "if llm_validator.enabled:" in line and not skip_mode:
            skip_indent = len(line) - len(line.lstrip())
            skip_mode = True
            i += 1
            continue

        # In skip mode, skip lines that are indented more than the start
        if skip_mode:
            current_indent = (
                len(line) - len(line.lstrip()) if line.strip() else skip_indent + 4
            )

            # Empty lines maintain skip mode
            if not line.strip():
                i += 1
                continue

            # Lines at same or less indent end skip mode
            if current_indent <= skip_indent:
                skip_mode = False
                result_lines.append(line)
            # Skip lines at deeper indent
            i += 1
            continue

        result_lines.append(line)
        i += 1

    return "\n".join(result_lines)


def fix_indentation(content: str) -> str:
    """Fix common indentation issues in test files."""
    lines = content.split("\n")
    result_lines = []

    for i, line in enumerate(lines):
        # Fix test_cases list at wrong indent (4 spaces instead of 8)
        if line.startswith("    test_cases = [") or line.startswith(
            "    test_phrases = ["
        ):
            # Check if we're inside a function (should be 8 spaces)
            # Look back for function definition
            for j in range(i - 1, max(0, i - 20), -1):
                if lines[j].strip().startswith("async def ") or lines[
                    j
                ].strip().startswith("def "):
                    # We're inside a function, fix indent
                    line = "    " + line
                    break

        # Fix for loop at wrong indent
        if line.startswith("    for ") and "in test_" in line:
            for j in range(i - 1, max(0, i - 20), -1):
                if lines[j].strip().startswith("async def ") or lines[
                    j
                ].strip().startswith("def "):
                    line = "    " + line
                    break

        result_lines.append(line)

    return "\n".join(result_lines)


def process_file(filepath: Path) -> tuple[bool, str]:
    """Process a single file and return (success, message)."""
    try:
        content = filepath.read_text()
        original_content = content

        # Remove orphaned blocks
        content = remove_llm_validator_blocks(content)

        # Fix indentation
        content = fix_indentation(content)

        # Only write if changed
        if content != original_content:
            filepath.write_text(content)
            return True, f"Fixed {filepath}"
        else:
            return True, f"No changes needed for {filepath}"

    except Exception as e:
        return False, f"Error processing {filepath}: {e}"


def get_broken_files() -> list[Path]:
    """Get list of broken test files."""
    return [
        Path("tests/integration/agent_squad_tests/test_agents.py"),
        Path("tests/integration/guest/general/test_agent_squad_ultra_hunter_full.py"),
        Path("tests/integration/guest/general/test_buy_intent.py"),
        Path("tests/integration/guest/general/test_common_informational_queries.py"),
        Path("tests/integration/guest/general/test_cross_chain_comprehensive.py"),
        Path("tests/integration/guest/general/test_hunter_chat_integration.py"),
        Path("tests/integration/guest/general/test_interruption_flows.py"),
        Path("tests/integration/guest/general/test_low_coverage_intents.py"),
        Path("tests/integration/guest/general/test_multi_intent_end_to_end.py"),
        Path("tests/integration/guest/general/test_multilanguage_comprehensive.py"),
        Path("tests/integration/guest/general/test_redis_metrics_collector.py"),
        Path("tests/integration/guest/general/test_shortcuts_edge_cases.py"),
        Path("tests/integration/guest/general/test_unified_chat_critical_paths.py"),
        Path("tests/integration/guest/general/test_unified_chat_with_test_data.py"),
        Path("tests/integration/guest/general/test_user_chat_messages.py"),
        Path("tests/integration/guest/knowledge/test_knowledge_injection_api.py"),
        Path("tests/integration/user/workflows/test_swap_workflow_hyperliquid.py"),
    ]


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_orphaned_llm_validator.py <file_path> | --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        files = get_broken_files()
    else:
        files = [Path(sys.argv[1])]

    success_count = 0
    for filepath in files:
        if filepath.exists():
            success, message = process_file(filepath)
            print(message)
            if success:
                success_count += 1
        else:
            print(f"File not found: {filepath}")

    print(f"\nProcessed {success_count}/{len(files)} files")


if __name__ == "__main__":
    main()
