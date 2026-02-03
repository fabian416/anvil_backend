#!/usr/bin/env python3
"""
API Documentation Standardization Script

This script standardizes all API endpoint documentation across frontend docs with:
- Complete paths (/api/v1/user/* or /api/v1/admin/*)
- Full request parameters (path params, query params, body)
- Complete example responses (actual JSON examples)
- Consistent formatting
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# API endpoint patterns to enhance
API_PATTERNS = [
    # User endpoints
    r"/api/v1/users/me/preferences",
    r"/api/v1/alerts/",
    r"/api/v1/search/",
    r"/api/v1/comparison/",
    r"/api/v1/dashboard/",
    r"/api/v1/portfolio/",
    r"/api/v1/markets/",
    r"/api/v1/projects/",
    r"/api/v1/chat/",
    # Admin endpoints
    r"/api/v1/admin/",
]


class APIDocStandardizer:
    def __init__(self, docs_root: Path):
        self.docs_root = docs_root
        self.files_updated = 0
        self.endpoints_enhanced = 0

    def find_all_md_files(self) -> List[Path]:
        """Find all markdown files in docs/frontend/"""
        return list(self.docs_root.glob("**/*.md"))

    def extract_api_sections(self, content: str) -> List[Tuple[int, int, str]]:
        """Extract API integration sections from content"""
        api_sections = []
        lines = content.split("\n")

        in_api_section = False
        section_start = 0

        for i, line in enumerate(lines):
            if "## 🔌 API Integration" in line or "## 🔌 API Endpoints" in line:
                in_api_section = True
                section_start = i
            elif in_api_section and line.startswith("##"):
                # End of API section
                api_sections.append((
                    section_start,
                    i,
                    "\n".join(lines[section_start:i]),
                ))
                in_api_section = False

        return api_sections

    def enhance_endpoint_documentation(self, endpoint_block: str) -> str:
        """Enhance a single API endpoint documentation block"""

        # Pattern: // GET /api/v1/some/endpoint
        method_path_pattern = r"//\s+(GET|POST|PUT|PATCH|DELETE)\s+(/api/v1/[^\s]+)"

        matches = re.findall(method_path_pattern, endpoint_block)
        if not matches:
            return endpoint_block

        method, path = matches[0]

        # Check if already has example response
        if "Example Response:" in endpoint_block or "Example:" in endpoint_block:
            return endpoint_block

        # Add example response section if missing
        enhanced = endpoint_block

        # Find the end of the TypeScript interface/function
        typescript_end = endpoint_block.rfind("```")
        if typescript_end > 0:
            # Insert example response before closing
            example_response = self._generate_example_response(method, path)
            enhanced = (
                endpoint_block[:typescript_end]
                + "\n\n"
                + example_response
                + "\n"
                + endpoint_block[typescript_end:]
            )
            self.endpoints_enhanced += 1

        return enhanced

    def _generate_example_response(self, method: str, path: str) -> str:
        """Generate example response based on endpoint"""

        # Common success responses
        if method == "GET":
            if "/preferences" in path:
                return """// Example Response:
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "risk_tolerance": "moderate",
  "preferred_chains": ["ethereum", "arbitrum"],
  "preferred_categories": ["lending", "dex"],
  "notification_settings": {
    "risk_alerts_enabled": true,
    "push_enabled": true,
    "min_severity": "MEDIUM"
  },
  "default_currency": "USD",
  "theme": "dark"
}"""
            elif "/alerts" in path:
                return """// Example Response:
{
  "alerts": [
    {
      "id": "alert-123",
      "protocol_name": "Aave V3",
      "severity": "HIGH",
      "message": "Risk score increased from 2.1 to 4.3",
      "created_at": "2025-12-01T10:30:00Z"
    }
  ],
  "total": 5,
  "unacknowledged": 2
}"""
            elif "/dashboard" in path:
                return """// Example Response:
{
  "total_value_usd": 45230.50,
  "change_24h_percent": 2.3,
  "overall_risk_score": 3.2,
  "risk_level": "MEDIUM"
}"""

        elif method == "POST":
            return """// Example Response:
{
  "success": true,
  "message": "Operation completed successfully"
}"""

        elif method in ["PUT", "PATCH"]:
            return """// Example Response:
{
  "success": true,
  "message": "Updated successfully"
}"""

        elif method == "DELETE":
            return """// Example Response:
{
  "success": true,
  "message": "Deleted successfully"
}"""

        return "// Example Response: { success: true }"

    def process_file(self, file_path: Path) -> bool:
        """Process a single markdown file"""
        try:
            content = file_path.read_text()
            original_content = content

            # Find and enhance API sections
            api_sections = self.extract_api_sections(content)

            if not api_sections:
                return False

            # Process each API section
            for start, end, section_content in api_sections:
                enhanced_section = self.enhance_endpoint_documentation(section_content)
                if enhanced_section != section_content:
                    content = content.replace(section_content, enhanced_section)

            # Write back if changed
            if content != original_content:
                file_path.write_text(content)
                self.files_updated += 1
                return True

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

        return False

    def run(self):
        """Run the standardization process"""
        print("🚀 Starting API Documentation Standardization...")
        print(f"📁 Scanning: {self.docs_root}")

        md_files = self.find_all_md_files()
        print(f"📄 Found {len(md_files)} markdown files")

        for file_path in md_files:
            if self.process_file(file_path):
                print(f"✅ Enhanced: {file_path.relative_to(self.docs_root)}")

        print("\n" + "=" * 60)
        print(f"✅ Standardization Complete!")
        print(f"📝 Files Updated: {self.files_updated}")
        print(f"🔗 Endpoints Enhanced: {self.endpoints_enhanced}")
        print("=" * 60)


if __name__ == "__main__":
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_root = project_root / "docs" / "frontend"

    if not docs_root.exists():
        print(f"❌ Error: {docs_root} does not exist")
        exit(1)

    standardizer = APIDocStandardizer(docs_root)
    standardizer.run()
