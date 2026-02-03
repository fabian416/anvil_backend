"""Test metadata extractor using AST parsing.

This module extracts test metadata from test functions using Python's Abstract Syntax Tree (AST)
parsing to automatically generate custom validation prompts.
"""

import ast
import inspect
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


class TestType(Enum):
    """Classification of test types for prompt strategy selection."""

    SIMPLE_QUERY = "simple_query"  # Single request/response
    MULTI_STEP = "multi_step"  # 5-step flow conversation
    INTENT_DETECTION = "intent_detection"  # Router/intent tests
    SECURITY = "security"  # XSS, injection, edge cases
    ERROR_HANDLING = "error_handling"  # Error response validation
    KNOWLEDGE_QUERY = "knowledge_query"  # RAG/knowledge tests


@dataclass
class ExtractedAssertion:
    """Parsed assertion from test code."""

    line_number: int
    assertion_type: str  # e.g., "status_code", "content_keyword", "json_field"
    expected_value: str
    actual_expression: str
    full_assertion: str


@dataclass
class TestMetadata:
    """Extracted test metadata from AST parsing."""

    test_name: str
    test_file: str
    test_type: TestType
    test_category: str  # e.g., "hunter", "flows", "errors"

    # Extracted from assertions
    assertions: list[ExtractedAssertion] = field(default_factory=list)
    expected_status_code: Optional[int] = 200
    required_keywords: list[str] = field(default_factory=list)
    expected_intents: list[str] = field(default_factory=list)
    expected_json_fields: list[str] = field(default_factory=list)

    # Performance hints
    is_slow_test: bool = False  # Has @pytest.mark.slow
    requires_external_api: bool = False  # Calls external services


class TestMetadataExtractor:
    """Extract test metadata using Python AST parsing."""

    def __init__(self):
        """Initialize the metadata extractor."""
        self._metadata_cache: dict[str, TestMetadata] = {}

    def extract_metadata(self, test_func: Callable) -> TestMetadata:
        """Main entry point: extract all metadata from test function.

        Args:
            test_func: The test function to analyze

        Returns:
            TestMetadata containing all extracted information
        """
        # Check cache first
        func_id = f"{test_func.__module__}.{test_func.__qualname__}"
        if func_id in self._metadata_cache:
            return self._metadata_cache[func_id]

        try:
            # Get source code and parse AST
            source_code = inspect.getsource(test_func)
            tree = ast.parse(source_code)

            # Extract components
            assertions = self._extract_assertions(tree)
            test_type = self._classify_test_type(test_func, source_code, assertions)
            test_category = self._extract_category(test_func)

            # Build metadata
            metadata = TestMetadata(
                test_name=test_func.__name__,
                test_file=inspect.getfile(test_func),
                test_type=test_type,
                test_category=test_category,
                assertions=assertions,
                expected_status_code=self._extract_status_code(assertions),
                required_keywords=self._extract_keywords(assertions),
                expected_intents=self._extract_intents(
                    test_func, source_code, assertions
                ),
                expected_json_fields=self._extract_json_fields(assertions),
                is_slow_test=self._has_slow_marker(test_func),
                requires_external_api=self._requires_external_api(source_code),
            )

            # Cache and return
            self._metadata_cache[func_id] = metadata
            return metadata

        except Exception as e:
            # Fallback to minimal metadata if extraction fails
            return self._create_fallback_metadata(test_func, str(e))

    def _extract_assertions(self, tree: ast.AST) -> list[ExtractedAssertion]:
        """Extract all assert statements from AST.

        Args:
            tree: AST tree to analyze

        Returns:
            List of extracted assertions
        """
        assertions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                assertion = self._parse_assertion(node)
                if assertion:
                    assertions.append(assertion)

        return assertions

    def _parse_assertion(self, node: ast.Assert) -> Optional[ExtractedAssertion]:
        """Parse a single assertion node.

        Args:
            node: AST Assert node

        Returns:
            ExtractedAssertion or None if parsing fails
        """
        try:
            # Get the full assertion as string
            full_assertion = ast.unparse(node)

            # Parse the test expression
            test_expr = node.test

            # Determine assertion type and extract details
            if isinstance(test_expr, ast.Compare):
                return self._parse_compare_assertion(
                    test_expr, full_assertion, node.lineno
                )
            elif isinstance(test_expr, ast.Compare) and any(
                isinstance(op, ast.In) for op in test_expr.ops
            ):
                return self._parse_in_assertion(test_expr, full_assertion, node.lineno)
            elif isinstance(test_expr, ast.Call):
                return self._parse_call_assertion(
                    test_expr, full_assertion, node.lineno
                )
            else:
                # Generic assertion
                return ExtractedAssertion(
                    line_number=node.lineno,
                    assertion_type="generic",
                    expected_value="",
                    actual_expression=ast.unparse(test_expr),
                    full_assertion=full_assertion,
                )

        except Exception:
            return None

    def _parse_compare_assertion(
        self, test_expr: ast.Compare, full_assertion: str, lineno: int
    ) -> Optional[ExtractedAssertion]:
        """Parse comparison assertions like 'a == b' or 'x in y'.

        Args:
            test_expr: Compare expression
            full_assertion: Full assertion string
            lineno: Line number

        Returns:
            ExtractedAssertion or None
        """
        left = ast.unparse(test_expr.left)
        comparators = [ast.unparse(comp) for comp in test_expr.comparators]
        ops = test_expr.ops

        # Check for 'in' operator (keyword checks)
        if any(isinstance(op, ast.In) for op in ops):
            # Pattern: assert "keyword" in content
            if len(comparators) > 0:
                return ExtractedAssertion(
                    line_number=lineno,
                    assertion_type="content_keyword",
                    expected_value=left.strip("\"'"),
                    actual_expression=comparators[0],
                    full_assertion=full_assertion,
                )

        # Check for status code comparison
        if "status_code" in left:
            return ExtractedAssertion(
                line_number=lineno,
                assertion_type="status_code",
                expected_value=comparators[0] if comparators else "",
                actual_expression=left,
                full_assertion=full_assertion,
            )

        # Check for JSON field comparison
        if "[" in left and "]" in left:
            # Pattern: assert response_data["field"] == value
            return ExtractedAssertion(
                line_number=lineno,
                assertion_type="json_field",
                expected_value=comparators[0].strip("\"'") if comparators else "",
                actual_expression=left,
                full_assertion=full_assertion,
            )

        # Generic comparison
        return ExtractedAssertion(
            line_number=lineno,
            assertion_type="comparison",
            expected_value=comparators[0] if comparators else "",
            actual_expression=left,
            full_assertion=full_assertion,
        )

    def _parse_in_assertion(
        self, test_expr: ast.Compare, full_assertion: str, lineno: int
    ) -> ExtractedAssertion:
        """Parse 'in' assertions for keyword checking.

        Args:
            test_expr: Compare expression with 'in' operator
            full_assertion: Full assertion string
            lineno: Line number

        Returns:
            ExtractedAssertion
        """
        left = ast.unparse(test_expr.left)
        comparators = [ast.unparse(comp) for comp in test_expr.comparators]

        return ExtractedAssertion(
            line_number=lineno,
            assertion_type="content_keyword",
            expected_value=left.strip("\"'"),
            actual_expression=comparators[0] if comparators else "",
            full_assertion=full_assertion,
        )

    def _parse_call_assertion(
        self, test_expr: ast.Call, full_assertion: str, lineno: int
    ) -> ExtractedAssertion:
        """Parse function call assertions.

        Args:
            test_expr: Call expression
            full_assertion: Full assertion string
            lineno: Line number

        Returns:
            ExtractedAssertion
        """
        func_name = ast.unparse(test_expr.func)

        return ExtractedAssertion(
            line_number=lineno,
            assertion_type="function_call",
            expected_value="",
            actual_expression=func_name,
            full_assertion=full_assertion,
        )

    def _classify_test_type(
        self,
        test_func: Callable,
        source_code: str,
        assertions: list[ExtractedAssertion],
    ) -> TestType:
        """Classify test based on patterns.

        Args:
            test_func: Test function
            source_code: Source code string
            assertions: Extracted assertions

        Returns:
            TestType classification
        """
        # Multi-step: has multiple POST calls or numbered steps
        post_count = source_code.count("await client.post")
        if post_count > 2:
            return TestType.MULTI_STEP

        # Intent detection: checks "intent" field
        if any("intent" in a.full_assertion for a in assertions):
            return TestType.INTENT_DETECTION

        # Security: has XSS/injection patterns
        security_patterns = [
            "<script>",
            "DROP TABLE",
            "OR 1=1",
            "'; DROP",
            "../",
            "..\\",
        ]
        if any(pattern in source_code for pattern in security_patterns):
            return TestType.SECURITY

        # Error handling: expects 4xx/5xx status
        error_statuses = ["400", "401", "403", "404", "422", "500", "502", "503"]
        if any(
            a.expected_value in error_statuses
            for a in assertions
            if a.assertion_type == "status_code"
        ):
            return TestType.ERROR_HANDLING

        # Knowledge query: mentions GraphRAG or knowledge
        if any(keyword in source_code for keyword in ["graphrag", "knowledge", "rag"]):
            return TestType.KNOWLEDGE_QUERY

        # Default: simple query
        return TestType.SIMPLE_QUERY

    def _extract_category(self, test_func: Callable) -> str:
        """Extract test category from file path.

        Args:
            test_func: Test function

        Returns:
            Category string (e.g., "hunter", "flows", "errors")
        """
        try:
            file_path = Path(inspect.getfile(test_func))

            # Extract from path like tests/integration/guest/hunter/test_...
            parts = file_path.parts

            # Look for category after 'guest' or 'user'
            for i, part in enumerate(parts):
                if part in ["guest", "user"] and i + 1 < len(parts):
                    category = parts[i + 1]
                    # Remove test_ prefix if present
                    if category.startswith("test_"):
                        category = category[5:]
                    return category

            # Fallback: extract from filename
            filename = file_path.stem
            if "hunter" in filename:
                return "hunter"
            elif "flow" in filename:
                return "flows"
            elif "error" in filename:
                return "errors"
            elif "knowledge" in filename:
                return "knowledge"
            else:
                return "general"

        except Exception:
            return "general"

    def _extract_status_code(
        self, assertions: list[ExtractedAssertion]
    ) -> Optional[int]:
        """Extract expected status code from assertions.

        Args:
            assertions: List of assertions

        Returns:
            Expected status code or 200 as default
        """
        for assertion in assertions:
            if assertion.assertion_type == "status_code":
                try:
                    return int(assertion.expected_value)
                except ValueError:
                    pass

        return 200

    def _extract_keywords(self, assertions: list[ExtractedAssertion]) -> list[str]:
        """Extract required keywords from content assertions.

        Args:
            assertions: List of assertions

        Returns:
            List of required keywords
        """
        keywords = []

        for assertion in assertions:
            if assertion.assertion_type == "content_keyword":
                keyword = assertion.expected_value.strip().lower()
                if keyword and keyword not in keywords:
                    keywords.append(keyword)

        return keywords

    def _extract_intents(
        self,
        test_func: Callable,
        source_code: str,
        assertions: list[ExtractedAssertion],
    ) -> list[str]:
        """Extract expected intents from test.

        Args:
            test_func: Test function
            source_code: Source code string
            assertions: List of assertions

        Returns:
            List of expected intents
        """
        intents = []

        # Extract from assertions
        for assertion in assertions:
            if "intent" in assertion.full_assertion:
                # Extract value from assertion like: assert data["intent"] == "price_prediction"
                intent_match = re.search(r'"(\w+)"', assertion.expected_value)
                if intent_match:
                    intents.append(intent_match.group(1))
                elif assertion.expected_value:
                    intents.append(assertion.expected_value.strip("\"'"))

        # Extract from test name
        test_name = test_func.__name__
        if "sentiment" in test_name:
            intents.append("sentiment_analysis")
        elif "price" in test_name or "prediction" in test_name:
            intents.append("price_prediction")
        elif "risk" in test_name:
            intents.append("risk_analysis")
        elif "pattern" in test_name:
            intents.append("pattern_detection")
        elif "portfolio" in test_name:
            intents.append("portfolio_optimization")
        elif "trading" in test_name:
            intents.append("trading_signals")

        return list(set(intents))  # Remove duplicates

    def _extract_json_fields(self, assertions: list[ExtractedAssertion]) -> list[str]:
        """Extract expected JSON fields from assertions.

        Args:
            assertions: List of assertions

        Returns:
            List of expected JSON field names
        """
        fields = []

        for assertion in assertions:
            if assertion.assertion_type == "json_field":
                # Extract field name from expression like: response_data["field"]
                field_match = re.search(r'\["(\w+)"\]', assertion.actual_expression)
                if field_match:
                    fields.append(field_match.group(1))

        return fields

    def _has_slow_marker(self, test_func: Callable) -> bool:
        """Check if test has @pytest.mark.slow decorator.

        Args:
            test_func: Test function

        Returns:
            True if has slow marker
        """
        return hasattr(test_func, "pytestmark") and any(
            getattr(mark, "name", "") == "slow" for mark in test_func.pytestmark
        )

    def _requires_external_api(self, source_code: str) -> bool:
        """Check if test requires external API calls.

        Args:
            source_code: Source code string

        Returns:
            True if requires external APIs
        """
        external_indicators = [
            "coingecko",
            "deepinfra",
            "openai",
            "anthropic",
            "external_api",
            "http://",
            "https://",
        ]

        return any(
            indicator in source_code.lower() for indicator in external_indicators
        )

    def _create_fallback_metadata(
        self, test_func: Callable, error: str
    ) -> TestMetadata:
        """Create fallback metadata when extraction fails.

        Args:
            test_func: Test function
            error: Error message

        Returns:
            Minimal TestMetadata
        """
        return TestMetadata(
            test_name=test_func.__name__,
            test_file=inspect.getfile(test_func)
            if hasattr(test_func, "__code__")
            else "unknown",
            test_type=TestType.SIMPLE_QUERY,
            test_category=self._extract_category(test_func),
            assertions=[],
            expected_status_code=200,
            required_keywords=[],
            expected_intents=[],
            expected_json_fields=[],
            is_slow_test=False,
            requires_external_api=False,
        )
