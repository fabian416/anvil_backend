"""
MCP integration tests configuration.

This module provides fixtures and configuration for MCP server tests.
"""

import sys
import os

# Ensure the src directory is in the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest


@pytest.fixture
def skip_mcp_test():
    """Fixture to skip MCP tests that require external services."""
    pytest.skip("MCP test requires external service")
