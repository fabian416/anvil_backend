#!/usr/bin/env python3
"""Batch fix all 23 working files with agent_response bug."""

import subprocess


def get_line_numbers(filepath):
    """Get line numbers where agent_output=agent_response appears."""
    result = subprocess.run(
        ["grep", "-n", "agent_output=agent_response", filepath],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return [int(line.split(":")[0]) for line in result.stdout.strip().split("\n")]
    return []


def apply_fixes(file_path, lines_to_fix):
    """Apply fixes to a single file."""
    with open(file_path, "r") as f:
        lines = f.readlines()

    lines_to_fix_0 = [l - 1 for l in lines_to_fix]
    insertions = []

    for line_idx in lines_to_fix_0:
        for i in range(line_idx, max(0, line_idx - 30), -1):
            if "if llm_validator.enabled:" in lines[i]:
                indent = len(lines[i]) - len(lines[i].lstrip())
                insertion_text = (
                    " " * indent
                    + "# Extract response data\n"
                    + " " * indent
                    + "data = response.json()\n"
                    + " " * indent
                    + 'agent_response = data["agent_message"]["content"]\n\n'
                )
                insertions.append((i, insertion_text))
                break

    insertions.sort(reverse=True)

    for insert_line, insert_text in insertions:
        lines.insert(insert_line, insert_text)

    with open(file_path, "w") as f:
        f.writelines(lines)

    return len(insertions)


# All 23 working files
working_files = [
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_historical_chat_edge_cases.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_intent_all_languages.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_multistep_flow_orchestration.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_intent_all_protocols.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_intent_complex_combinations.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_ultra_chat_integration.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_historical_chat_advanced_scenarios.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_intent_edge_cases.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_rate_limiting_advanced_scenarios.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_multistep_flow_advanced.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/knowledge/test_knowledge_advanced_scenarios.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_multistep_flow_error_recovery.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_shortcuts_edge_cases_comprehensive.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_security_advanced_xss_prevention.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_llm_integration_advanced.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_multistep_flow_edge_cases.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_historical_chat_data_integrity.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_shortcuts_advanced_combinations.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/knowledge/test_knowledge_quality_assurance.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_historical_chat_advanced.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_llm_integration_edge_cases.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_security_input_sanitization.py",
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_rate_limiting_edge_cases.py",
]

total_fixes = 0

print("=" * 80)
print("BATCH FIXING 23 WORKING FILES")
print("=" * 80)

for i, filepath in enumerate(working_files, 1):
    short_path = filepath.replace("/home/ubuntu/anvil_backend/", "")
    lines = get_line_numbers(filepath)

    if lines:
        count = apply_fixes(filepath, lines)
        total_fixes += count
        print(f"{i:2d}. [{count:2d} fixes] {short_path}")
    else:
        print(f"{i:2d}. [NO MATCHES] {short_path}")

print("=" * 80)
print(f"TOTAL: {total_fixes} fixes applied across {len(working_files)} files")
print("=" * 80)
