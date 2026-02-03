#!/usr/bin/env python3
"""
API Template Generator

Generates documentation templates for undocumented backend endpoints.
Uses the API_DOCUMENTATION_STANDARD.md template and fills in known information.
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class APITemplateGenerator:
    """Generates API documentation templates."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.coverage_report_path = (
            project_root / "scripts" / "api_audit" / "data" / "coverage_report.json"
        )
        self.templates_dir = project_root / "docs" / "frontend" / "_templates"
        self.standard_path = project_root / "docs" / "API_DOCUMENTATION_STANDARD.md"

    def load_coverage_report(self) -> Dict:
        """Load the coverage report to find undocumented endpoints."""
        if not self.coverage_report_path.exists():
            print(f"⚠️  Coverage report not found: {self.coverage_report_path}")
            print("   Run: python scripts/api_audit/validate_api_coverage.py")
            return None

        with open(self.coverage_report_path, "r") as f:
            return json.load(f)

    def generate_template(self, endpoint: Dict) -> str:
        """Generate documentation template for an endpoint."""
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "")
        priority = endpoint.get("priority", "MEDIUM")
        module = endpoint.get("module", "general")

        # Extract readable name from path
        # /api/v1/some/path -> Some Path
        path_parts = path.split("/")
        endpoint_name = " ".join(
            part.title() for part in path_parts[3:] if part and not part.startswith("{")
        )
        if not endpoint_name:
            endpoint_name = "Endpoint"

        # Determine authentication requirement
        auth_required = priority in ["CRITICAL", "HIGH"]

        template = f"""# FRONTEND API: {endpoint_name}

**Priority:** {priority}  
**Module:** {module}  
**Authentication:** {"Required" if auth_required else "Optional"}  
**Status:** ⏳ To Be Documented

---

## 📋 Endpoint Details

### {method} `{path}`

**Description:**  
[TODO: Describe what this endpoint does]

**Authentication:** {"Bearer token required" if auth_required else "Optional"}

---

## 🔌 TypeScript Integration

### Request Interface

```typescript
// {method} {path}

interface {endpoint_name.replace(" ", "")}Request {{
  // TODO: Define request parameters
}}
```

### Response Interface

```typescript
interface {endpoint_name.replace(" ", "")}Response {{
  // TODO: Define response structure
}}
```

### API Function

```typescript
const {self._to_camel_case(endpoint_name)} = async (
  request: {endpoint_name.replace(" ", "")}Request
): Promise<{endpoint_name.replace(" ", "")}Response> => {{
  const response = await api.{method.lower()}('{path}', {{
    // TODO: Add request configuration
  }});
  return response.data;
}};
```

---

## 🔗 React Hook

```typescript
export function use{endpoint_name.replace(" ", "")}() {{
  const {{ data, isLoading, error }} = useQuery({{
    queryKey: ['{module}', '{self._to_camel_case(endpoint_name)}'],
    queryFn: async () => {{
      // TODO: Implement query function
    }},
  }});
  
  return {{
    data,
    isLoading,
    error,
  }};
}}
```

---

## ⚠️ Error Handling

```typescript
// TODO: Define error cases

// Example:
// - 400 Bad Request: Invalid parameters
// - 401 Unauthorized: Authentication required
// - 404 Not Found: Resource not found
// - 500 Internal Server Error: Server error
```

---

## 🎯 Use Cases

**TODO:** Describe when and how this endpoint should be used

---

*Template Generated: {datetime.now().strftime("%Y-%m-%d")}*  
*Backend File: `{endpoint.get("file", "")}`*  
*Priority: {priority}*
"""
        return template

    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase."""
        words = text.split()
        if not words:
            return ""
        return words[0].lower() + "".join(w.title() for w in words[1:])

    def generate_all_templates(self):
        """Generate templates for all undocumented endpoints."""
        print("🚀 API Template Generator")
        print("=" * 60)

        # Load coverage report
        report = self.load_coverage_report()
        if not report:
            return

        undocumented = report.get("undocumented_endpoints", [])
        if not undocumented:
            print("✅ All endpoints are documented!")
            return

        print(f"📊 Found {len(undocumented)} undocumented endpoints")
        print()

        # Create templates directory
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Group by priority
        by_priority = {}
        for endpoint in undocumented:
            priority = endpoint.get("priority", "MEDIUM")
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(endpoint)

        # Generate templates by priority
        total_generated = 0
        for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if priority not in by_priority:
                continue

            endpoints = by_priority[priority]
            print(f"📝 Generating {len(endpoints)} {priority} priority templates...")

            priority_dir = self.templates_dir / priority.lower()
            priority_dir.mkdir(exist_ok=True)

            for endpoint in endpoints:
                # Create filename from path
                path = endpoint.get("path", "")
                method = endpoint.get("method", "GET")

                # /api/v1/some/path -> some-path
                filename = "-".join(
                    part
                    for part in path.split("/")[3:]
                    if part and not part.startswith("{")
                )
                if not filename:
                    filename = "root"

                filename = f"{method.lower()}-{filename}.md"
                filepath = priority_dir / filename

                # Generate template
                template = self.generate_template(endpoint)

                # Write file
                filepath.write_text(template)
                total_generated += 1

                print(f"   ✅ {filepath.name}")

        print()
        print("=" * 60)
        print(f"✅ Generated {total_generated} templates")
        print(f"📁 Location: {self.templates_dir}")
        print()
        print("🎯 Next Steps:")
        print("   1. Review generated templates")
        print("   2. Fill in TODO sections with actual data")
        print("   3. Move completed docs to appropriate module folders")
        print("   4. Re-run coverage validator to track progress")
        print()
        print("=" * 60)


def main():
    """Main execution."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    generator = APITemplateGenerator(project_root)
    generator.generate_all_templates()


if __name__ == "__main__":
    main()
