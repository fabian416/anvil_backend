#!/usr/bin/env python3
"""
API Coverage Validator

Validates that all backend endpoints are documented in frontend documentation.
Identifies gaps, generates reports, and tracks progress toward 100% coverage.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class ValidationResult:
    """Result of coverage validation."""

    total_backend_endpoints: int
    documented_endpoints: int
    missing_endpoints: int
    coverage_percentage: float
    undocumented: List[Dict]
    by_priority: Dict[str, Dict]
    by_module: Dict[str, Dict]


class APICoverageValidator:
    """Validates API documentation coverage."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_inventory_path = (
            project_root / "scripts" / "api_audit" / "data" / "backend_inventory.json"
        )
        self.docs_dirs = [
            project_root / "docs" / "frontend",
            project_root / "docs" / "api",
        ]

        # Priority classification
        self.critical_paths = [
            r"/account/",
            r"/auth/",
            r"/payment/",
            r"/subscription/",
            r"/ws/",
            r"/notifications/",
            r"/preferences/",
            r"/alerts/",
            r"/search/",
            r"/dashboard/",
            r"/markets/",
            r"/portfolio/",
            r"/comparison/",
            r"/chat/",
            r"/projects/",
        ]

        self.high_priority_paths = [
            r"/admin/projects",
            r"/admin/distillation",
            r"/admin/stats",
            r"/admin/agents",
            r"/atlas/",
            r"/metrics/",
        ]

    def load_backend_inventory(self) -> List[Dict]:
        """Load backend endpoint inventory."""
        if not self.backend_inventory_path.exists():
            print(f"⚠️  Backend inventory not found: {self.backend_inventory_path}")
            print("   Run: python scripts/api_audit/extract_backend_endpoints.py")
            return []

        with open(self.backend_inventory_path, "r") as f:
            data = json.load(f)
            return data.get("endpoints", [])

    def scan_documentation(self) -> Set[str]:
        """Scan all documentation for documented endpoints."""
        documented = set()

        # Patterns to match API endpoint declarations in markdown
        # Pattern 1: `GET /api/v1/path` or `/api/v1/path` (backtick enclosed)
        # Pattern 2: GET /api/v1/path (inline plain text)
        endpoint_patterns = [
            re.compile(r"`(/api/v1/[^`]*)`"),  # backtick-enclosed paths
            re.compile(r"(?:GET|POST|PUT|PATCH|DELETE|WS)\s+(/api/v1/[^\s\n`|]+)"),  # inline paths
        ]

        for docs_dir in self.docs_dirs:
            if not docs_dir.exists():
                print(f"⚠️  Documentation directory not found: {docs_dir}")
                continue

            print(f"📚 Scanning documentation in: {docs_dir}")

            # Scan all markdown files
            for md_file in docs_dir.rglob("*.md"):
                try:
                    content = md_file.read_text()
                    for pattern in endpoint_patterns:
                        matches = pattern.findall(content)
                        for match in matches:
                            # Clean up the path (remove query params, fragments)
                            clean_path = match.split("?")[0].split("#")[0].strip()
                            documented.add(clean_path)
                except Exception as e:
                    print(f"   ⚠️  Error reading {md_file.name}: {e}")

        return documented

    def classify_priority(self, path: str) -> str:
        """Classify endpoint priority based on path."""
        for pattern in self.critical_paths:
            if re.search(pattern, path):
                return "CRITICAL"

        for pattern in self.high_priority_paths:
            if re.search(pattern, path):
                return "HIGH"

        if "/admin/" in path:
            return "MEDIUM"

        return "LOW"

    def extract_module(self, path: str) -> str:
        """Extract module name from endpoint path."""
        # /api/v1/module/... -> module
        parts = path.split("/")
        if len(parts) >= 4:
            return parts[3]
        return "root"

    def validate_coverage(self) -> ValidationResult:
        """Validate API documentation coverage."""
        print("🔍 API Coverage Validation Started")
        print("=" * 60)

        # Load backend endpoints
        backend_endpoints = self.load_backend_inventory()
        if not backend_endpoints:
            print("❌ No backend endpoints found. Cannot validate.")
            return None

        print(f"📊 Backend Endpoints: {len(backend_endpoints)}")

        # Scan documentation
        documented_paths = self.scan_documentation()
        print(f"✅ Documented Endpoints Found: {len(documented_paths)}")

        # Find undocumented endpoints
        undocumented = []
        by_priority = defaultdict(lambda: {"total": 0, "documented": 0, "missing": []})
        by_module = defaultdict(lambda: {"total": 0, "documented": 0, "missing": []})

        for endpoint in backend_endpoints:
            path = endpoint.get("path", "")
            method = endpoint.get("method", "")
            priority = self.classify_priority(path)
            module = self.extract_module(path)

            # Update counts
            by_priority[priority]["total"] += 1
            by_module[module]["total"] += 1

            # Check if documented
            is_documented = path in documented_paths

            if is_documented:
                by_priority[priority]["documented"] += 1
                by_module[module]["documented"] += 1
            else:
                # Undocumented endpoint
                endpoint_info = {
                    "method": method,
                    "path": path,
                    "priority": priority,
                    "module": module,
                    "file": endpoint.get("file_path", ""),
                }
                undocumented.append(endpoint_info)
                by_priority[priority]["missing"].append(endpoint_info)
                by_module[module]["missing"].append(endpoint_info)

        # Calculate coverage
        total = len(backend_endpoints)
        documented = total - len(undocumented)
        coverage = (documented / total * 100) if total > 0 else 0

        result = ValidationResult(
            total_backend_endpoints=total,
            documented_endpoints=documented,
            missing_endpoints=len(undocumented),
            coverage_percentage=coverage,
            undocumented=undocumented,
            by_priority=dict(by_priority),
            by_module=dict(by_module),
        )

        return result

    def print_report(self, result: ValidationResult):
        """Print validation report to console."""
        print("\n" + "=" * 60)
        print("📊 API COVERAGE VALIDATION REPORT")
        print("=" * 60)

        # Overall stats
        print(f"\n📈 Overall Coverage:")
        print(f"   Backend Endpoints:     {result.total_backend_endpoints}")
        print(f"   Documented:            {result.documented_endpoints}")
        print(f"   Missing Documentation: {result.missing_endpoints}")
        print(f"   Coverage:              {result.coverage_percentage:.1f}%")

        # Status indicator
        if result.coverage_percentage >= 90:
            status = "✅ EXCELLENT"
        elif result.coverage_percentage >= 70:
            status = "⚠️  GOOD"
        elif result.coverage_percentage >= 50:
            status = "🟡 NEEDS IMPROVEMENT"
        else:
            status = "❌ CRITICAL"

        print(f"\n   Status: {status}")

        # By priority
        print(f"\n📊 Coverage by Priority:")
        for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if priority in result.by_priority:
                stats = result.by_priority[priority]
                total = stats["total"]
                documented = stats["documented"]
                pct = (documented / total * 100) if total > 0 else 0
                print(f"   {priority:10} {documented:3}/{total:3} ({pct:5.1f}%)")

        # By module
        print(f"\n📦 Coverage by Module (Top 10):")
        sorted_modules = sorted(
            result.by_module.items(), key=lambda x: x[1]["total"], reverse=True
        )[:10]

        for module, stats in sorted_modules:
            total = stats["total"]
            documented = stats["documented"]
            pct = (documented / total * 100) if total > 0 else 0
            print(f"   {module:15} {documented:3}/{total:3} ({pct:5.1f}%)")

        # Undocumented endpoints
        if result.undocumented:
            print(f"\n❌ Undocumented Endpoints ({len(result.undocumented)}):")
            print(f"   (Showing first 20)")

            for endpoint in result.undocumented[:20]:
                priority_icon = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🟢",
                }.get(endpoint["priority"], "⚪")

                print(f"   {priority_icon} {endpoint['method']:6} {endpoint['path']}")

        print("\n" + "=" * 60)

        # Next steps
        if result.coverage_percentage < 100:
            print("\n🎯 Next Steps:")
            print(f"   1. Document {result.missing_endpoints} remaining endpoints")
            print(f"   2. Focus on CRITICAL priority first")
            print(f"   3. Target: 100% coverage")
            print(f"\n   Run: python scripts/api_audit/generate_api_templates.py")
        else:
            print("\n🎉 Congratulations! 100% API coverage achieved!")

        print("=" * 60)

    def save_report(self, result: ValidationResult, output_path: Path):
        """Save validation report to JSON file."""
        report = {
            "timestamp": "2025-12-01T12:00:00Z",
            "summary": {
                "total_backend_endpoints": result.total_backend_endpoints,
                "documented_endpoints": result.documented_endpoints,
                "missing_endpoints": result.missing_endpoints,
                "coverage_percentage": result.coverage_percentage,
            },
            "by_priority": result.by_priority,
            "by_module": result.by_module,
            "undocumented_endpoints": result.undocumented,
        }

        output_path.write_text(json.dumps(report, indent=2))
        print(f"\n💾 Report saved: {output_path}")


def main():
    """Main execution."""
    import sys

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    print("🚀 API Coverage Validator")
    print(f"📁 Project: {project_root.name}")
    print()

    # Validate coverage
    validator = APICoverageValidator(project_root)
    result = validator.validate_coverage()

    if result:
        # Print report
        validator.print_report(result)

        # Save report
        output_dir = script_dir / "data"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "coverage_report.json"
        validator.save_report(result, output_path)

        # Exit code based on coverage
        if result.coverage_percentage >= 90:
            return 0
        elif result.coverage_percentage >= 70:
            return 0
        else:
            return 1
    else:
        return 1


if __name__ == "__main__":
    exit(main())
