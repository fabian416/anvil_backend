#!/usr/bin/env python3
"""
Fix Alembic migration enum duplication issue.

Problem: sa.Enum() in PostgreSQL tries to create the type automatically,
causing "DuplicateObject" errors when ENUMs are already created at the top.

Solution: Replace all sa.Enum(..., name="xyz") with postgresql.ENUM(..., name="xyz", create_type=False)
in table definitions (but NOT in the initial .create() calls).
"""

import re
import sys
from pathlib import Path


def fix_migration_file(file_path: Path) -> bool:
    """Fix enum definitions in migration file."""
    print(f"Reading {file_path}")
    content = file_path.read_text()

    # Pattern to match sa.Enum(..., name="something") inside table definitions
    # We want to replace ONLY the ones used in columns, NOT the .create() ones
    pattern = r'sa\.Enum\((.*?name="[^"]+)"[^)]*\)(?!\.create|\.drop)'

    def replacement(match: re.Match) -> str:
        """Replace sa.Enum with postgresql.ENUM and add create_type=False."""
        inner = match.group(1)
        # Add create_type=False if not already there
        if "create_type" not in inner:
            return f"postgresql.ENUM({inner}, create_type=False)"
        return match.group(0)

    # Count matches before replacement
    matches_before = len(re.findall(pattern, content))
    print(f"Found {matches_before} sa.Enum() calls in table definitions")

    if matches_before == 0:
        print("✅ No changes needed!")
        return False

    # Replace
    new_content = re.sub(pattern, replacement, content)

    # Verify replacement worked
    matches_after = len(re.findall(r'sa\.Enum\((.*?name="[^"]+)"[^)]*\)(?!\.create|\.drop)', new_content))
    print(f"Remaining sa.Enum() calls after fix: {matches_after}")

    if matches_after == 0:
        # Write back
        file_path.write_text(new_content)
        print(f"✅ Fixed {matches_before} enum definitions")
        return True
    else:
        print(f"⚠️ Warning: {matches_after} enum calls still remain (might be false positives)")
        file_path.write_text(new_content)
        return True


def main():
    """Main entry point."""
    # Find the initial_schema migration
    alembic_dir = Path("src/app/infrastructure/persistence_sqla/alembic/versions")
    migration_file = None

    for file in alembic_dir.glob("*_initial_schema.py"):
        migration_file = file
        break

    if not migration_file:
        print("❌ Could not find initial_schema migration file")
        sys.exit(1)

    print(f"📝 Processing: {migration_file.name}")
    changed = fix_migration_file(migration_file)

    if changed:
        print("\n✅ Migration fixed! Now rebuild and restart:")
        print("   docker-compose down")
        print("   docker-compose up --build")
    else:
        print("\n✅ No changes needed")


if __name__ == "__main__":
    main()
