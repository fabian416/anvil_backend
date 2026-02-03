#!/usr/bin/env python3
"""
Documentation Linter

Validates that API documentation follows the API_DOCUMENTATION_STANDARD.md
and ensures quality, completeness, and consistency.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Lint severity levels."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class LintIssue:
    """A single lint issue."""

    severity: Severity
    file: str
    line: int
    rule: str
    message: str


class DocumentationLinter:
    """Lints API documentation for quality and standard compliance."""

    # Required sections per standard
    REQUIRED_SECTIONS = [
        "Module Overview",
        "API Integration",
        "React Hooks",
        "Error Handling",
    ]

    # Patterns to check
    PATTERNS = {
        "typescript_interface": re.compile(r"interface\s+\w+\s*\{"),
        "api_endpoint": re.compile(r"(?:GET|POST|PUT|PATCH|DELETE|WS)\s+/api/v1/"),
        "react_hook": re.compile(r"export\s+function\s+use\w+"),
        "todo_marker": re.compile(r"TODO:|FIXME:|XXX:", re.IGNORECASE),
        "example_request": re.compile(r"Example Request:", re.IGNORECASE),
        "example_response": re.compile(r"Example Response:", re.IGNORECASE),
        "auth_required": re.compile(r"Authentication:\s*(?:Required|Optional|None)"),
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_dir = project_root / "docs" / "frontend"
        self.standard_path = project_root / "docs" / "API_DOCUMENTATION_STANDARD.md"
        self.issues: List[LintIssue] = []

    def lint_file(self, file_path: Path) -> List[LintIssue]:
        """Lint a single markdown file."""
        issues = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")

            # Check for required sections
            for section in self.REQUIRED_SECTIONS:
                if section not in content:
                    issues.append(
                        LintIssue(
                            severity=Severity.WARNING,
                            file=file_path.name,
                            line=0,
                            rule="MISSING_SECTION",
                            message=f"Missing required section: {section}",
                        )
                    )

            # Check for TODO markers (should be resolved)
            for i, line in enumerate(lines, 1):
                if self.PATTERNS["todo_marker"].search(line):
                    issues.append(
                        LintIssue(
                            severity=Severity.INFO,
                            file=file_path.name,
                            line=i,
                            rule="TODO_MARKER",
                            message="Documentation contains TODO marker",
                        )
                    )

            # Check for API endpoints
            endpoint_count = len(self.PATTERNS["api_endpoint"].findall(content))
            if endpoint_count == 0:
                issues.append(
                    LintIssue(
                        severity=Severity.ERROR,
                        file=file_path.name,
                        line=0,
                        rule="NO_ENDPOINTS",
                        message="No API endpoints found in documentation",
                    )
                )

            # Check for TypeScript interfaces
            if not self.PATTERNS["typescript_interface"].search(content):
                issues.append(
                    LintIssue(
                        severity=Severity.WARNING,
                        file=file_path.name,
                        line=0,
                        rule="NO_INTERFACES",
                        message="No TypeScript interfaces defined",
                    )
                )

            # Check for React hooks
            if not self.PATTERNS["react_hook"].search(content):
                issues.append(
                    LintIssue(
                        severity=Severity.WARNING,
                        file=file_path.name,
                        line=0,
                        rule="NO_HOOKS",
                        message="No React hooks provided",
                    )
                )

            # Check for examples
            if not self.PATTERNS["example_request"].search(content):
                issues.append(
                    LintIssue(
                        severity=Severity.WARNING,
                        file=file_path.name,
                        line=0,
                        rule="NO_REQUEST_EXAMPLE",
                        message="No example request provided",
                    )
                )

            if not self.PATTERNS["example_response"].search(content):
                issues.append(
                    LintIssue(
                        severity=Severity.WARNING,
                        file=file_path.name,
                        line=0,
                        rule="NO_RESPONSE_EXAMPLE",
                        message="No example response provided",
                    )
                )

            # Check for authentication documentation
            if not self.PATTERNS["auth_required"].search(content):
                issues.append(
                    LintIssue(
                        severity=Severity.WARNING,
                        file=file_path.name,
                        line=0,
                        rule="NO_AUTH_INFO",
                        message="Authentication requirements not specified",
                    )
                )

            # Check line length (soft limit: 120 chars)
            for i, line in enumerate(lines, 1):
                if len(line) > 120 and not line.strip().startswith("http"):
                    # Allow long lines for URLs
                    if "```" not in line:  # Skip code blocks
                        issues.append(
                            LintIssue(
                                severity=Severity.INFO,
                                file=file_path.name,
                                line=i,
                                rule="LINE_TOO_LONG",
                                message=f"Line exceeds 120 characters ({len(line)} chars)",
                            )
                        )

        except Exception as e:
            issues.append(
                LintIssue(
                    severity=Severity.ERROR,
                    file=file_path.name,
                    line=0,
                    rule="FILE_ERROR",
                    message=f"Error reading file: {e}",
                )
            )

        return issues

    def lint_all(self) -> Dict:
        """Lint all documentation files."""
        print("🔍 Documentation Linter Started")
        print("=" * 60)

        if not self.docs_dir.exists():
            print(f"❌ Documentation directory not found: {self.docs_dir}")
            return None

        # Find all markdown files (excluding templates and reports)
        md_files = [
            f
            for f in self.docs_dir.rglob("*.md")
            if "_templates" not in f.parts
            and not f.name.startswith("ROADMAP")
            and not f.name.startswith("FINAL")
        ]

        print(f"📄 Found {len(md_files)} documentation files")
        print()

        # Lint each file
        all_issues = []
        files_with_issues = 0
        files_clean = 0

        for md_file in md_files:
            issues = self.lint_file(md_file)
            if issues:
                all_issues.extend(issues)
                files_with_issues += 1
            else:
                files_clean += 1

        # Count by severity
        errors = sum(1 for i in all_issues if i.severity == Severity.ERROR)
        warnings = sum(1 for i in all_issues if i.severity == Severity.WARNING)
        infos = sum(1 for i in all_issues if i.severity == Severity.INFO)

        # Print report
        print("=" * 60)
        print("📊 DOCUMENTATION LINTING REPORT")
        print("=" * 60)
        print()
        print(f"📈 Summary:")
        print(f"   Files Scanned:     {len(md_files)}")
        print(f"   Files Clean:       {files_clean}")
        print(f"   Files With Issues: {files_with_issues}")
        print()
        print(f"   🔴 Errors:         {errors}")
        print(f"   🟡 Warnings:       {warnings}")
        print(f"   ℹ️  Info:           {infos}")
        print()

        # Quality score
        if len(md_files) > 0:
            quality_score = (files_clean / len(md_files)) * 100

            if quality_score >= 90:
                quality_status = "✅ EXCELLENT"
            elif quality_score >= 70:
                quality_status = "⚠️  GOOD"
            elif quality_score >= 50:
                quality_status = "🟡 NEEDS IMPROVEMENT"
            else:
                quality_status = "❌ POOR"

            print(f"📊 Quality Score: {quality_score:.1f}% ({quality_status})")

        print()

        # Show issues by severity
        if all_issues:
            print("=" * 60)
            print("🔴 ERRORS")
            print("=" * 60)
            error_issues = [i for i in all_issues if i.severity == Severity.ERROR]
            if error_issues:
                for issue in error_issues[:10]:  # Show first 10
                    print(f"   {issue.file}:{issue.line} - {issue.message}")
            else:
                print("   None")

            print()
            print("=" * 60)
            print("🟡 WARNINGS")
            print("=" * 60)
            warning_issues = [i for i in all_issues if i.severity == Severity.WARNING]
            if warning_issues:
                for issue in warning_issues[:10]:  # Show first 10
                    print(f"   {issue.file}:{issue.line} - {issue.message}")
            else:
                print("   None")

            print()
            print("=" * 60)
            print("ℹ️  INFO")
            print("=" * 60)
            info_issues = [i for i in all_issues if i.severity == Severity.INFO]
            if info_issues:
                print(f"   {len(info_issues)} informational items")
                print(f"   (Run with --verbose to see all)")
            else:
                print("   None")

        print()
        print("=" * 60)

        # Return summary
        return {
            "total_files": len(md_files),
            "files_clean": files_clean,
            "files_with_issues": files_with_issues,
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
            "quality_score": quality_score if len(md_files) > 0 else 0,
            "issues": [
                {
                    "severity": i.severity.value,
                    "file": i.file,
                    "line": i.line,
                    "rule": i.rule,
                    "message": i.message,
                }
                for i in all_issues
            ],
        }


def main():
    """Main execution."""
    import json

    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    linter = DocumentationLinter(project_root)
    result = linter.lint_all()

    if result:
        # Save report
        output_dir = script_dir / "data"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "lint_report.json"

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"💾 Report saved: {output_path}")
        print()
        print("=" * 60)

        # Exit code based on errors
        if result["errors"] > 0:
            return 1
        elif result["warnings"] > 10:  # Allow some warnings
            return 1
        else:
            return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
