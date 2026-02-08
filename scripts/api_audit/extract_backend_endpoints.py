#!/usr/bin/env python3
"""
Backend Endpoint Extractor

Extracts all API endpoints from FastAPI routers and generates
a comprehensive JSON inventory.
"""

import ast
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Set


@dataclass
class EndpointMetadata:
    """Metadata for a single API endpoint."""

    method: str  # GET, POST, PUT, PATCH, DELETE
    path: str  # /api/v1/users/me/preferences
    function_name: str  # get_preferences
    path_params: List[str]  # ["user_id"]
    query_params: List[str]  # ["limit", "offset"]
    request_body: Optional[str]  # "UpdatePreferencesRequest"
    response_model: Optional[str]  # "UserPreferencesResponse"
    auth_required: bool  # True
    description: str  # From docstring
    file_path: str  # Relative to project root
    line_number: int  # Location in file
    router_prefix: str  # /preferences


class BackendEndpointExtractor:
    """Extracts all API endpoints from FastAPI routers."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.controllers_dir = (
            project_root / "src" / "app" / "presentation" / "http" / "controllers"
        )
        self.endpoints: List[EndpointMetadata] = []

    def extract_all_endpoints(self) -> List[EndpointMetadata]:
        """Scan all router files and extract metadata."""
        router_files = list(self.controllers_dir.rglob("*router.py"))

        print(f"🔍 Found {len(router_files)} router files")

        for router_file in router_files:
            print(f"   📄 Processing: {router_file.relative_to(self.project_root)}")
            endpoints = self.parse_router_file(router_file)
            self.endpoints.extend(endpoints)
            print(f"      ✅ Found {len(endpoints)} endpoints")

        return self.endpoints

    def parse_router_file(self, file_path: Path) -> List[EndpointMetadata]:
        """Parse a single router file."""
        try:
            content = file_path.read_text()
            endpoints = []

            # Extract router prefix
            router_prefix = self._extract_router_prefix(content)

            # Find all route decorators
            # Pattern: @router.{method}("path", ...)
            route_pattern = (
                r'@router\.(get|post|put|patch|delete)\s*\([\'"]([^\'"]+)[\'"]'
            )

            lines = content.split("\n")
            for i, line in enumerate(lines):
                match = re.search(route_pattern, line)
                if match:
                    method = match.group(1).upper()
                    path = match.group(2)

                    # Get function definition on next non-decorator line
                    func_line_idx = i + 1
                    while func_line_idx < len(lines) and lines[
                        func_line_idx
                    ].strip().startswith("@"):
                        func_line_idx += 1

                    if func_line_idx < len(lines):
                        func_line = lines[func_line_idx]
                        func_name_match = re.search(
                            r"async\s+def\s+(\w+)\s*\(", func_line
                        )
                        if func_name_match:
                            func_name = func_name_match.group(1)

                            # Extract function details
                            func_start = func_line_idx
                            func_block = self._extract_function_block(lines, func_start)

                            # Create endpoint metadata
                            endpoint = EndpointMetadata(
                                method=method,
                                path=self._build_full_path(router_prefix, path),
                                function_name=func_name,
                                path_params=self._extract_path_params(path),
                                query_params=self._extract_query_params(func_block),
                                request_body=self._extract_request_body(func_block),
                                response_model=self._extract_response_model(line),
                                auth_required=self._check_auth_required(lines, i),
                                description=self._extract_docstring(func_block),
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=i + 1,
                                router_prefix=router_prefix,
                            )
                            endpoints.append(endpoint)

            return endpoints

        except Exception as e:
            print(f"      ⚠️ Error parsing {file_path.name}: {e}")
            return []

    def _extract_router_prefix(self, content: str) -> str:
        """Extract router prefix from router definition."""
        # Pattern: prefix="/api/v1/some-path"
        match = re.search(r'prefix\s*=\s*[\'"]([^\'"]+)[\'"]', content)
        return match.group(1) if match else ""

    def _build_full_path(self, prefix: str, path: str) -> str:
        """Build full API path with /api/v1 prefix."""
        # Remove trailing slash from prefix
        prefix = prefix.rstrip("/")
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path

        # If path is already complete with /api/v1/
        if path.startswith("/api/v1/"):
            return path

        # Build the path with prefix
        if prefix:
            full_path = prefix + path
        else:
            full_path = path

        # If prefix already includes /api/v1, return as-is
        if full_path.startswith("/api/v1/"):
            return full_path

        # Handle special prefixes that map to /api/v1/user/ or /api/v1/admin/
        # Check if this is a user-facing endpoint (markets, chat, etc.)
        user_prefixes = ["/user/", "/markets", "/chat", "/portfolio", "/alerts"]
        admin_prefixes = ["/admin"]

        for admin_prefix in admin_prefixes:
            if full_path.startswith(admin_prefix):
                return "/api/v1" + full_path

        for user_prefix in user_prefixes:
            if full_path.startswith(user_prefix):
                return "/api/v1" + full_path

        # Default: add /api/v1 prefix
        return "/api/v1" + full_path

    def _extract_path_params(self, path: str) -> List[str]:
        """Extract path parameters from route path."""
        # Pattern: {param_name}
        return re.findall(r"\{([^\}]+)\}", path)

    def _extract_query_params(self, func_block: str) -> List[str]:
        """Extract query parameters from function signature."""
        params = []
        # Pattern: param_name: ... = Query(...)
        query_matches = re.findall(r"(\w+):\s*[^=]*=\s*Query\(", func_block)
        params.extend(query_matches)
        return params

    def _extract_request_body(self, func_block: str) -> Optional[str]:
        """Extract request body type from function signature."""
        # Pattern: request: SomeRequest
        # Look for Pydantic model parameters
        lines = func_block.split("\n")
        for line in lines:
            if "Request" in line and ":" in line and "=" not in line:
                match = re.search(r":\s*(\w+Request)\s*[,\)]", line)
                if match:
                    return match.group(1)
        return None

    def _extract_response_model(self, decorator_line: str) -> Optional[str]:
        """Extract response model from route decorator."""
        # Pattern: response_model=SomeResponse
        match = re.search(r"response_model\s*=\s*(\w+)", decorator_line)
        return match.group(1) if match else None

    def _check_auth_required(self, lines: List[str], route_idx: int) -> bool:
        """Check if endpoint requires authentication."""
        # Look for Security or dependencies in decorator
        for i in range(max(0, route_idx - 5), min(len(lines), route_idx + 5)):
            line = lines[i]
            if "Security(" in line or "bearer_scheme" in line:
                return True
            if "dependencies=" in line and "Security" in line:
                return True
        return False

    def _extract_docstring(self, func_block: str) -> str:
        """Extract docstring from function block."""
        lines = func_block.split("\n")
        in_docstring = False
        docstring_lines = []

        for line in lines:
            stripped = line.strip()
            if '"""' in stripped:
                if in_docstring:
                    break
                in_docstring = True
                # Handle single-line docstring
                if stripped.count('"""') == 2:
                    return stripped.replace('"""', "").strip()
                continue
            if in_docstring:
                docstring_lines.append(stripped)

        return " ".join(docstring_lines).strip()

    def _extract_function_block(self, lines: List[str], start_idx: int) -> str:
        """Extract complete function block."""
        block_lines = []
        indent_level = None

        for i in range(start_idx, min(len(lines), start_idx + 50)):
            line = lines[i]

            # Determine base indent level
            if indent_level is None and line.strip():
                indent_level = len(line) - len(line.lstrip())

            # Stop at next function or class definition at same level
            if (
                i > start_idx
                and line.strip()
                and not line.startswith(" " * (indent_level + 1))
            ):
                if (
                    line.strip().startswith("def ")
                    or line.strip().startswith("async def ")
                    or line.strip().startswith("@")
                ):
                    break

            block_lines.append(line)

        return "\n".join(block_lines)

    def save_inventory(self, output_path: Path):
        """Save endpoint inventory to JSON file."""
        data = {
            "total_endpoints": len(self.endpoints),
            "endpoints": [asdict(e) for e in self.endpoints],
            "by_method": self._group_by_method(),
            "by_module": self._group_by_module(),
        }

        output_path.write_text(json.dumps(data, indent=2))
        print(f"\n✅ Saved inventory to: {output_path}")

    def _group_by_method(self) -> Dict[str, int]:
        """Group endpoints by HTTP method."""
        counts = {}
        for endpoint in self.endpoints:
            counts[endpoint.method] = counts.get(endpoint.method, 0) + 1
        return counts

    def _group_by_module(self) -> Dict[str, int]:
        """Group endpoints by module."""
        counts = {}
        for endpoint in self.endpoints:
            # Extract module from file path
            parts = Path(endpoint.file_path).parts
            if len(parts) >= 7:  # src/app/presentation/http/controllers/{module}
                module = parts[6]
            else:
                module = "root"
            counts[module] = counts.get(module, 0) + 1
        return counts

    def print_summary(self):
        """Print extraction summary."""
        print("\n" + "=" * 60)
        print("📊 BACKEND ENDPOINT EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"Total Endpoints: {len(self.endpoints)}")
        print(f"\nBy HTTP Method:")
        for method, count in sorted(self._group_by_method().items()):
            print(f"  {method}: {count}")
        print(f"\nBy Module:")
        for module, count in sorted(self._group_by_module().items()):
            print(f"  {module}: {count}")
        print("=" * 60)


def main():
    """Main execution."""
    import sys

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    print("🚀 Backend Endpoint Extraction Started")
    print(f"📁 Project Root: {project_root}")

    # Extract endpoints
    extractor = BackendEndpointExtractor(project_root)
    endpoints = extractor.extract_all_endpoints()

    # Save inventory
    output_dir = script_dir / "data"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "backend_inventory.json"
    extractor.save_inventory(output_path)

    # Print summary
    extractor.print_summary()

    return 0


if __name__ == "__main__":
    exit(main())
