#!/usr/bin/env python3
"""Scan remaining files to identify working vs broken files."""

import subprocess
import os

# Files already fixed
fixed_files = {
    "test_multistep_flow_cancellation.py",
    "test_guest_chat_parity.py",
    "test_guest_chat_comprehensive.py",
    "test_security_malicious_inputs.py",
    "test_security_multistep_injection.py",
    "test_rate_limiting_comprehensive.py",
    "test_security_multistep_phases34.py",
    "test_multi_step_flows.py",
    "test_intent_detection_edge_cases.py",
    "test_knowledge_source_integration.py",
    "test_knowledge_context_enrichment.py",
    "test_knowledge_error_handling.py",
    "test_intent_detection_advanced.py",
}

# Find all Python test files with agent_response bug
results = []
base_dir = "/home/ubuntu/anvil_backend/tests/integration/guest"

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(".py") and file not in fixed_files:
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                    count = content.count("agent_output=agent_response")
                    if count > 0:
                        # Check for syntax errors
                        result = subprocess.run(
                            [
                                ".venv/bin/python",
                                "-m",
                                "pytest",
                                filepath,
                                "--collect-only",
                            ],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )

                        has_syntax_error = (
                            "SyntaxError" in result.stderr
                            or "IndentationError" in result.stderr
                            or "error during collection" in result.stdout
                        )

                        results.append((count, filepath, has_syntax_error))
            except Exception as e:
                pass

# Sort by count descending
results.sort(reverse=True, key=lambda x: x[0])

print("\n" + "=" * 80)
print("WORKING FILES (No Syntax Errors)")
print("=" * 80)
working = [r for r in results if not r[2]]
for i, (count, filepath, _) in enumerate(working, 1):
    short_path = filepath.replace("/home/ubuntu/anvil_backend/", "")
    print(f"{i:2d}. {count:2d} instances - {short_path}")

print(f"\n{'=' * 80}")
print(f"Working Files: {len(working)}")
print(f"Total Instances: {sum(c for c, _, _ in working)}")

print("\n" + "=" * 80)
print("BROKEN FILES (Have Syntax Errors)")
print("=" * 80)
broken = [r for r in results if r[2]]
for i, (count, filepath, _) in enumerate(broken, 1):
    short_path = filepath.replace("/home/ubuntu/anvil_backend/", "")
    print(f"{i:2d}. {count:2d} instances - {short_path}")

print(f"\n{'=' * 80}")
print(f"Broken Files: {len(broken)}")
print(f"Total Instances: {sum(c for c, _, _ in broken)}")

print(f"\n{'=' * 80}")
print(f"GRAND TOTAL")
print(f"{'=' * 80}")
print(f"Total Files Remaining: {len(results)}")
print(f"Working: {len(working)} | Broken: {len(broken)}")
print(f"Total Instances: {sum(c for c, _, _ in results)}")
