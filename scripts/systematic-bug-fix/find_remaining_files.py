#!/usr/bin/env python3
"""Find remaining files with agent_response bug, sorted by count."""

import os
import subprocess

# Files we've already fixed
fixed_files = {
    "test_multistep_flow_cancellation.py",
    "test_guest_chat_parity.py",
    "test_guest_chat_comprehensive.py",
    "test_security_malicious_inputs.py",
    "test_security_multistep_injection.py",
    "test_rate_limiting_comprehensive.py",
    "test_security_multistep_phases34.py",
}

results = []

# Search in tests/integration/guest
for root, dirs, files in os.walk("/home/ubuntu/anvil_backend/tests/integration/guest"):
    for file in files:
        if file.endswith(".py") and file not in fixed_files:
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                    count = content.count("agent_output=agent_response")
                    if count > 0:
                        results.append((count, filepath))
            except:
                pass

# Sort by count descending
results.sort(reverse=True)

print(f"\nFound {len(results)} files with agent_response bug:\n")
for i, (count, filepath) in enumerate(results[:20], 1):
    short_path = filepath.replace("/home/ubuntu/anvil_backend/", "")
    print(f"{i:2d}. {count:2d} instances - {short_path}")

print(f"\n{'=' * 80}")
print(f"Total files remaining: {len(results)}")
print(f"Total instances: {sum(c for c, _ in results)}")
