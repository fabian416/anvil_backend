#!/usr/bin/env python3
"""
Clean orphaned llm_validator blocks from test files.

This script removes validation blocks that were left orphaned when llm_validator
parameters were removed from test function signatures.

Usage:
    python scripts/clean_llm_validator_blocks.py <filepath>
"""

import sys
import re


def clean_file(filepath: str) -> tuple[int, int]:
    """
    Clean orphaned llm_validator blocks from a file.
    
    Returns:
        Tuple of (blocks_removed, lines_changed)
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_lines = len(content.split('\n'))
    blocks_removed = 0
    
    # Pattern to match orphaned llm_validator blocks
    # These appear between function parameters or after ): 
    # and contain the characteristic validation code
    
    # First, count blocks before cleaning
    blocks_before = content.count('if llm_validator.enabled:')
    
    # Pattern 1: Block inside function signature
    # async def test_something(
    #     self,
    #     param1,
    # 
    # # Optional LLM semantic validation (environment-gated)
    # if llm_validator.enabled:
    #     ...
    #
    # param2,
    # ):
    
    # Remove the entire validation block including comment and all nested lines
    pattern = (
        r'\n\s*# Optional LLM semantic validation \(environment-gated\)\s*\n'
        r'\s*if llm_validator\.enabled:\s*\n'
        r'(?:.*\n)*?'  # Match any lines
        r'\s*\)\s*\)\s*\n'  # End with ))
    )
    
    content = re.sub(pattern, '\n', content)
    
    # Pattern 2: Simpler - just look for the block structure
    # Sometimes blocks end differently
    lines = content.split('\n')
    result = []
    skip_block = False
    paren_depth = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Start skipping when we see the comment
        if '# Optional LLM semantic validation (environment-gated)' in line:
            skip_block = True
            i += 1
            continue
        
        if skip_block:
            # Skip the if llm_validator.enabled: line
            if 'if llm_validator.enabled:' in line:
                i += 1
                continue
            
            # Count parentheses to know when block ends
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                i += 1
                continue
            
            # Check if we've exited the block
            # Block ends when we hit a line that:
            # 1. Is a parameter (ends with ,)
            # 2. Is a decorator (@)
            # 3. Is a function def
            # 4. Is ): (end of function signature)
            # 5. Has lower indent than the if block
            
            if (stripped.endswith(',') and ':' in stripped and '(' not in stripped or
                stripped.startswith('@pytest') or
                stripped.startswith('async def ') or
                stripped.startswith('def ') or
                stripped == '):'):
                skip_block = False
                blocks_removed += 1
                result.append(line)
                i += 1
                continue
            
            # Still in block, skip this line
            i += 1
            continue
        
        result.append(line)
        i += 1
    
    new_content = '\n'.join(result)
    new_lines = len(new_content.split('\n'))
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    blocks_after = new_content.count('if llm_validator.enabled:')
    
    return blocks_before - blocks_after, original_lines - new_lines


def check_syntax(filepath: str) -> tuple[bool, str]:
    """Check if file has valid Python syntax."""
    import ast
    try:
        with open(filepath) as f:
            ast.parse(f.read())
        return True, "Valid"
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python clean_llm_validator_blocks.py <filepath>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    print(f"Processing: {filepath}")
    blocks_removed, lines_changed = clean_file(filepath)
    print(f"  Blocks removed: {blocks_removed}")
    print(f"  Lines changed: {lines_changed}")
    
    valid, msg = check_syntax(filepath)
    print(f"  Syntax: {msg}")
    
    if not valid:
        print("\n  WARNING: File still has syntax errors. Manual fix required.")


if __name__ == "__main__":
    main()
