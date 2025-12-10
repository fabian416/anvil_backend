"""
Conftest for template tests - skip all template tests.

Templates are reference files, not actual tests.
"""

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip all tests in the templates directory."""
    skip_templates = pytest.mark.skip(reason="Template file - not a real test")
    for item in items:
        if "/templates/" in str(item.fspath):
            item.add_marker(skip_templates)


# Alternatively, mark all tests in this directory as skip
pytestmark = pytest.mark.skip(reason="Template files - not actual tests")
