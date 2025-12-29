"""
Test data loader utilities for unified chat tests.

Provides helper functions to load and filter test cases from test_data.json,
shared between integration and component test suites.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


TEST_DATA_PATH = Path(__file__).parent.parent.parent / "docs" / "api" / "examples" / "test_data.json"


def load_test_data() -> Dict[str, Any]:
    """
    Load test data from JSON file.

    Returns:
        Dictionary containing all test data
    """
    with open(TEST_DATA_PATH, "r") as f:
        return json.load(f)


def get_all_test_cases() -> List[Dict[str, Any]]:
    """
    Extract all test cases from test_data.json.

    Returns:
        List of all test case dictionaries with _category and _subcategory added
    """
    data = load_test_data()
    test_cases = []

    test_cases_data = data.get("test_cases", {})
    if not isinstance(test_cases_data, dict):
        return test_cases

    for category, category_data in test_cases_data.items():
        if not isinstance(category_data, dict):
            continue

        for subcategory, subcategory_data in category_data.items():
            if not isinstance(subcategory_data, list):
                continue

            for test_case in subcategory_data:
                if not isinstance(test_case, dict):
                    continue
                # Create a copy to avoid modifying original
                test_case_copy = test_case.copy()
                test_case_copy["_category"] = category
                test_case_copy["_subcategory"] = subcategory
                test_cases.append(test_case_copy)

    return test_cases


def get_test_cases_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get all test cases for a specific category.

    Args:
        category: Category name (e.g., "graphrag", "hunter_ai", "ultra")

    Returns:
        List of test cases for the category
    """
    all_cases = get_all_test_cases()
    return [tc for tc in all_cases if tc.get("_category") == category]


def get_test_cases_by_subcategory(category: str, subcategory: str) -> List[Dict[str, Any]]:
    """
    Get all test cases for a specific subcategory.

    Args:
        category: Category name (e.g., "graphrag")
        subcategory: Subcategory name (e.g., "protocol_search")

    Returns:
        List of test cases for the subcategory
    """
    all_cases = get_all_test_cases()
    return [
        tc for tc in all_cases
        if tc.get("_category") == category and tc.get("_subcategory") == subcategory
    ]


def get_test_case_by_id(test_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific test case by ID.

    Args:
        test_id: Test case ID (e.g., "graphrag_ps_001")

    Returns:
        Test case dictionary or None if not found
    """
    all_cases = get_all_test_cases()
    for tc in all_cases:
        if tc.get("id") == test_id:
            return tc
    return None


def get_graphrag_test_cases() -> List[Dict[str, Any]]:
    """Get all GraphRAG test cases."""
    return get_test_cases_by_category("graphrag")


def get_hunter_test_cases() -> List[Dict[str, Any]]:
    """Get all Hunter AI test cases."""
    return get_test_cases_by_category("hunter_ai")


def get_ultra_test_cases() -> List[Dict[str, Any]]:
    """Get all ULTRA test cases."""
    return get_test_cases_by_category("ultra")


def get_squad_test_cases() -> List[Dict[str, Any]]:
    """Get all Agent Squad test cases."""
    return get_test_cases_by_category("agent_squad")


def get_chat_test_cases() -> List[Dict[str, Any]]:
    """Get all Chat (general conversation) test cases."""
    return get_test_cases_by_category("chat")


def get_critical_integration_test_ids() -> List[str]:
    """
    Get list of critical test case IDs for integration testing.

    Returns sample test cases from each category for end-to-end validation.
    """
    return [
        # GraphRAG samples (2 tests)
        "graphrag_ps_001",      # Protocol search
        "graphrag_ra_001",      # Risk assessment

        # Hunter AI samples (2 tests)
        "hunter_sent_001",      # Sentiment
        "hunter_pp_001",        # Price prediction

        # ULTRA samples (2 tests)
        "ultra_arb_001",        # Arbitrage
        "ultra_fl_001",         # Flash loans

        # Agent Squad samples (2 tests)
        "squad_spec_001",       # Specialist task
        "squad_work_001",       # Complex workflow

        # Chat samples (2 tests)
        "chat_gen_001",         # General chat
        "chat_gen_003",         # General chat variation (if exists)
    ]
