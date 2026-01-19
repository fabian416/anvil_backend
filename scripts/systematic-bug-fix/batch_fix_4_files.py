#!/usr/bin/env python3
"""Batch fix script for 4 knowledge/intent files"""

def apply_fixes(file_path, lines_to_fix):
    """Apply fixes to a single file."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    lines_to_fix_0 = [l - 1 for l in lines_to_fix]
    insertions = []

    for line_idx in lines_to_fix_0:
        for i in range(line_idx, max(0, line_idx - 30), -1):
            if "if llm_validator.enabled:" in lines[i]:
                indent = len(lines[i]) - len(lines[i].lstrip())
                insertion_text = " " * indent + "# Extract response data\n" + " " * indent + "data = response.json()\n" + " " * indent + "agent_response = data[\"agent_message\"][\"content\"]\n\n"
                insertions.append((i, insertion_text))
                break

    insertions.sort(reverse=True)

    for insert_line, insert_text in insertions:
        lines.insert(insert_line, insert_text)

    with open(file_path, 'w') as f:
        f.writelines(lines)

    return len(insertions)

# File 1: test_knowledge_source_integration.py (8 instances)
count1 = apply_fixes(
    "/home/ubuntu/anvil_backend/tests/integration/guest/knowledge/test_knowledge_source_integration.py",
    [62, 111, 156, 204, 248, 297, 350, 397]
)
print(f"File 1: Applied {count1} fixes to test_knowledge_source_integration.py")

# File 2: test_knowledge_context_enrichment.py (7 instances)
count2 = apply_fixes(
    "/home/ubuntu/anvil_backend/tests/integration/guest/knowledge/test_knowledge_context_enrichment.py",
    [67, 117, 167, 212, 285, 330, 392]
)
print(f"File 2: Applied {count2} fixes to test_knowledge_context_enrichment.py")

# File 3: test_knowledge_error_handling.py (6 instances)
count3 = apply_fixes(
    "/home/ubuntu/anvil_backend/tests/integration/guest/knowledge/test_knowledge_error_handling.py",
    [60, 105, 150, 195, 248, 292]
)
print(f"File 3: Applied {count3} fixes to test_knowledge_error_handling.py")

# File 4: test_intent_detection_advanced.py (10 instances)
count4 = apply_fixes(
    "/home/ubuntu/anvil_backend/tests/integration/guest/general/test_intent_detection_advanced.py",
    [72, 124, 175, 225, 271, 317, 367, 437, 492, 543]
)
print(f"File 4: Applied {count4} fixes to test_intent_detection_advanced.py")

print(f"\nTotal: {count1 + count2 + count3 + count4} fixes applied across 4 files")
