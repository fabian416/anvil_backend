#!/usr/bin/env python3
"""
Extract all API endpoints from FastAPI routers.
Outputs a comprehensive JSON with all endpoint details.
"""

import ast
import json
import sys
from pathlib import Path
from typing import Any


class EndpointExtractor(ast.NodeVisitor):
    """Extract endpoint information from Python AST."""

    def __init__(self):
        self.endpoints = []
        self.current_function = None
        self.decorator_info = {}

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions to extract endpoint info."""
        self.current_function = node.name
        
        # Extract decorator info
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if hasattr(decorator.func, 'attr'):
                    method = decorator.func.attr  # e.g., 'get', 'post', etc.
                    
                    # Extract endpoint details from decorator arguments
                    endpoint_info = {
                        'function_name': node.name,
                        'method': method.upper(),
                        'path': None,
                        'summary': None,
                        'description': None,
                        'response_model': None,
                        'status_code': None,
                        'auth_required': False,
                        'dependencies': [],
                    }
                    
                    # Parse positional args (path)
                    if decorator.args:
                        for arg in decorator.args:
                            if isinstance(arg, ast.Constant):
                                if endpoint_info['path'] is None:
                                    endpoint_info['path'] = arg.value
                    
                    # Parse keyword args
                    for keyword in decorator.keywords:
                        key = keyword.arg
                        value = keyword.value
                        
                        if key == 'summary' and isinstance(value, ast.Constant):
                            endpoint_info['summary'] = value.value
                        elif key == 'description' and isinstance(value, ast.Constant):
                            endpoint_info['description'] = value.value
                        elif key == 'response_model':
                            endpoint_info['response_model'] = self._extract_name(value)
                        elif key == 'status_code':
                            endpoint_info['status_code'] = self._extract_value(value)
                        elif key == 'dependencies':
                            endpoint_info['auth_required'] = True
                    
                    # Extract function parameters (query/path params, request body)
                    params = self._extract_params(node)
                    endpoint_info.update(params)
                    
                    if endpoint_info['path']:
                        self.endpoints.append(endpoint_info)
        
        self.generic_visit(node)

    def _extract_name(self, node: ast.AST) -> str:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Subscript):
            return self._extract_name(node.value)
        return str(node)

    def _extract_value(self, node: ast.AST) -> Any:
        """Extract value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Attribute):
            return f"{self._extract_name(node.value)}.{node.attr}"
        return None

    def _extract_params(self, node: ast.FunctionDef) -> dict:
        """Extract parameters from function definition."""
        result = {
            'path_params': [],
            'query_params': [],
            'request_body': None,
        }
        
        for arg in node.args.args:
            arg_name = arg.arg
            
            # Skip common injected dependencies
            if arg_name in ['current_user', 'http_request', 'request', 'interactor', 
                           'service', 'handler', 'repository', 'authorization']:
                continue
            
            # Extract type annotation
            if arg.annotation:
                type_name = self._extract_name(arg.annotation)
                
                # Path params typically match {param} in the path
                # Query params are typically primitives (str, int, bool)
                # Request bodies are typically Pydantic models
                if type_name in ['str', 'int', 'bool', 'float', 'UUID']:
                    if arg_name.endswith('_id') or arg_name in ['id', 'address']:
                        result['path_params'].append({
                            'name': arg_name,
                            'type': type_name,
                        })
                    else:
                        result['query_params'].append({
                            'name': arg_name,
                            'type': type_name,
                        })
                else:
                    # Assume it's a request body model
                    if 'Request' in type_name or 'Body' in type_name:
                        result['request_body'] = type_name
        
        return result


def extract_from_file(file_path: Path) -> list[dict]:
    """Extract endpoints from a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        extractor = EndpointExtractor()
        extractor.visit(tree)
        
        return extractor.endpoints
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return []


def find_router_files(base_path: Path) -> list[Path]:
    """Find all router files in the controllers directory."""
    router_files = []
    
    # Common router file patterns
    patterns = ['*router.py', '*_router.py', 'router.py']
    
    for pattern in patterns:
        router_files.extend(base_path.rglob(pattern))
    
    # Also include specific known files
    specific_files = [
        'upgrade_to_admin.py',
        'change_role.py',
        'my_wallets.py',
        'export_wallet.py',
        'complete_swap.py',
    ]
    
    for file_name in specific_files:
        router_files.extend(base_path.rglob(file_name))
    
    return sorted(set(router_files))


def categorize_endpoints(endpoints_by_file: dict) -> dict:
    """Categorize endpoints by module."""
    categorized = {}
    
    for file_path, endpoints in endpoints_by_file.items():
        # Determine category from path
        parts = Path(file_path).parts
        
        # Find the category (folder after 'controllers')
        category = 'general'
        if 'controllers' in parts:
            idx = parts.index('controllers')
            if idx + 1 < len(parts):
                category = parts[idx + 1]
        
        if category not in categorized:
            categorized[category] = []
        
        categorized[category].extend(endpoints)
    
    return categorized


def main():
    """Main entry point."""
    # Get the controllers directory
    controllers_path = Path(__file__).parent / 'src/app/presentation/http/controllers'
    
    if not controllers_path.exists():
        print(f"Controllers path not found: {controllers_path}", file=sys.stderr)
        sys.exit(1)
    
    # Find all router files
    router_files = find_router_files(controllers_path)
    
    print(f"Found {len(router_files)} router files", file=sys.stderr)
    
    # Extract endpoints from all files
    all_endpoints = {}
    for router_file in router_files:
        endpoints = extract_from_file(router_file)
        if endpoints:
            rel_path = router_file.relative_to(controllers_path)
            all_endpoints[str(rel_path)] = endpoints
    
    # Categorize by module
    categorized = categorize_endpoints(all_endpoints)
    
    # Output JSON
    output = {
        'total_endpoints': sum(len(eps) for eps in categorized.values()),
        'categories': len(categorized),
        'endpoints': categorized,
    }
    
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
