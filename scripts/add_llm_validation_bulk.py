#!/usr/bin/env python3
"""
Bulk LLM Validation Addition Script

Systematically adds LLM validation to integration tests following the Phase 1 pattern.
Processes test files and adds llm_validator fixture + validation logic to async test functions.

Usage:
    python scripts/add_llm_validation_bulk.py <test_file_path>
    python scripts/add_llm_validation_bulk.py tests/integration/chat/test_common_informational_queries.py
"""

import argparse
import re
from pathlib import Path
from typing import List, Dict, Tuple


class LLMValidationAdder:
    """Adds LLM validation to integration tests."""

    # Pattern for test function definition
    TEST_FUNC_PATTERN = r"(\s*@pytest\.mark\.\w+\s*\n)*\s*async def (test_\w+)\(self,\s*client:\s*AsyncClient(,\s*\w+:\s*\w+)?\):"

    # Common validation templates by test category
    VALIDATION_TEMPLATES = {
        "price_query": {
            "expected_behavior": (
                "Should provide accurate {token} price information in a clear format. "
                "Response must reference {token} specifically (not other cryptocurrencies) "
                "and include current price data with USD denomination."
            ),
            "context": {"test_category": "price_query", "token": "{token}"},
        },
        "info_query": {
            "expected_behavior": (
                "Should provide accurate and relevant information about {topic}. "
                "Response must focus on {topic} specifically and provide clear, "
                "educational content appropriate for the query."
            ),
            "context": {"test_category": "info_query", "topic": "{topic}"},
        },
        "sentiment_query": {
            "expected_behavior": (
                "Should provide market sentiment analysis for {token}. "
                "Response should include relevant market indicators, community sentiment, "
                "or price trends without making specific investment recommendations."
            ),
            "context": {"test_category": "sentiment_query", "token": "{token}"},
        },
        "defi_protocol": {
            "expected_behavior": (
                "Should provide accurate information about {protocol} protocol. "
                "Response must explain what the protocol does, its key features, "
                "and relevant DeFi concepts in an accessible way."
            ),
            "context": {"test_category": "defi_protocol", "protocol": "{protocol}"},
        },
    }

    def __init__(self, file_path: str):
        """Initialize with test file path."""
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Test file not found: {file_path}")

        with open(self.file_path, "r") as f:
            self.content = f.read()

        self.lines = self.content.splitlines()
        self.modified_content = self.content

    def detect_test_category(self, test_name: str, test_body: str) -> Tuple[str, Dict]:
        """
        Detect test category and extract relevant information.

        Returns:
            (category, info_dict) where info_dict contains extracted information
        """
        name_lower = test_name.lower()
        body_lower = test_body.lower()

        # Price queries
        if any(word in name_lower for word in ["price", "cost", "worth"]):
            # Extract token from test name or body
            tokens = ["bitcoin", "btc", "ethereum", "eth", "usdc", "usdt", "ada", "sol"]
            for token in tokens:
                if token in name_lower or token in body_lower:
                    return "price_query", {
                        "token": token.upper() if len(token) <= 4 else token.title()
                    }
            return "price_query", {"token": "cryptocurrency"}

        # Sentiment queries
        if any(
            word in name_lower for word in ["sentiment", "think", "opinion", "market"]
        ):
            tokens = ["bitcoin", "btc", "ethereum", "eth"]
            for token in tokens:
                if token in name_lower or token in body_lower:
                    return "sentiment_query", {
                        "token": token.upper() if len(token) <= 4 else token.title()
                    }
            return "sentiment_query", {"token": "crypto"}

        # DeFi protocol queries
        if any(
            word in name_lower
            for word in ["protocol", "aave", "morpho", "compound", "uniswap"]
        ):
            protocols = ["aave", "morpho", "compound", "uniswap", "curve"]
            for protocol in protocols:
                if protocol in name_lower or protocol in body_lower:
                    return "defi_protocol", {"protocol": protocol.title()}
            return "defi_protocol", {"protocol": "DeFi"}

        # Information queries (default)
        if any(word in name_lower for word in ["what_is", "info", "explain"]):
            topics = ["bitcoin", "ethereum", "defi", "usdc", "nft", "dao", "staking"]
            for topic in topics:
                if topic in name_lower or topic in body_lower:
                    return "info_query", {
                        "topic": topic.upper() if len(topic) <= 4 else topic.title()
                    }
            return "info_query", {"topic": "crypto"}

        # Default to info query
        return "info_query", {"topic": "crypto/DeFi"}

    def extract_user_input_variable(self, test_body: str) -> str:
        """Extract the user input variable name or create one."""
        # Look for existing user_input variable
        match = re.search(r'user_input\s*=\s*["\'](.+?)["\']', test_body)
        if match:
            return "user_input"

        # Look for content in json payload
        match = re.search(r'"content":\s*["\'](.+?)["\']', test_body)
        if match:
            return f'"{match.group(1)}"'

        return '"query"'

    def generate_llm_validation_code(
        self, test_name: str, test_body: str, indent: str = "        "
    ) -> str:
        """Generate LLM validation code for a test."""
        category, info = self.detect_test_category(test_name, test_body)
        template = self.VALIDATION_TEMPLATES[category]

        # Format expected behavior and context
        expected_behavior = template["expected_behavior"].format(**info)
        context = {k: v.format(**info) for k, v in template["context"].items()}

        # Extract user input variable
        user_input_var = self.extract_user_input_variable(test_body)

        validation_code = f'''
{indent}# Optional LLM semantic validation (environment-gated)
{indent}if llm_validator.enabled:
{indent}    validation = await llm_validator.validate_single_response(
{indent}        test_name="{test_name}",
{indent}        user_input={user_input_var},
{indent}        agent_output=content,
{indent}        expected_behavior=(
{indent}            "{expected_behavior}"
{indent}        ),
{indent}        additional_context={context}
{indent}    )
{indent}    if validation.verdict != "PASS":
{indent}        pytest.warn(UserWarning(
{indent}            f"LLM validation concern (confidence={{validation.confidence:.2f}}): "
{indent}            f"{{validation.reasoning}}"
{indent}        ))
'''
        return validation_code

    def add_llm_validation_marker(self, line_num: int) -> int:
        """Add @pytest.mark.llm_validation marker before test function."""
        # Find the line with async def
        while line_num > 0 and not self.lines[line_num].strip().startswith("async def"):
            line_num -= 1

        # Find decorators before function
        decorator_start = line_num
        while decorator_start > 0 and (
            self.lines[decorator_start - 1].strip().startswith("@")
            or self.lines[decorator_start - 1].strip() == ""
        ):
            decorator_start -= 1
            if self.lines[decorator_start].strip().startswith("@"):
                break

        # Check if llm_validation marker already exists
        for i in range(decorator_start, line_num):
            if "@pytest.mark.llm_validation" in self.lines[i]:
                return line_num  # Already has marker

        # Add marker
        indent = re.match(r"(\s*)", self.lines[line_num]).group(1)
        self.lines.insert(line_num, f"{indent}@pytest.mark.llm_validation")
        return line_num + 1

    def add_llm_validator_fixture(self, line_num: int) -> int:
        """Add llm_validator fixture to function parameters."""
        line = self.lines[line_num]

        # Check if llm_validator already in parameters
        if "llm_validator" in line:
            return line_num

        # Add llm_validator to parameters
        # Pattern: async def test_name(self, client: AsyncClient):
        # Replace with: async def test_name(self, client: AsyncClient, llm_validator):
        modified_line = line.replace(
            "AsyncClient):", "AsyncClient, llm_validator):"
        ).replace("AsyncClient,", "AsyncClient, llm_validator,")

        if modified_line != line:
            self.lines[line_num] = modified_line

        return line_num

    def find_test_functions(self) -> List[Dict]:
        """Find all test functions in the file."""
        tests = []
        for i, line in enumerate(self.lines):
            if re.match(r"\s*async def test_\w+", line):
                # Extract test name
                match = re.match(r"\s*async def (test_\w+)", line)
                if match:
                    test_name = match.group(1)

                    # Find test body (until next test or end of class)
                    body_start = i + 1
                    body_end = i + 1
                    indent_level = len(re.match(r"(\s*)", line).group(1))

                    while body_end < len(self.lines):
                        next_line = self.lines[body_end]
                        if next_line.strip() and not next_line.startswith(
                            " " * (indent_level + 1)
                        ):
                            break
                        body_end += 1

                    test_body = "\n".join(self.lines[body_start:body_end])

                    tests.append({
                        "name": test_name,
                        "line_num": i,
                        "body": test_body,
                        "body_end": body_end,
                    })

        return tests

    def process_tests(self) -> int:
        """Process all tests and add LLM validation."""
        tests = self.find_test_functions()
        modifications = 0

        # Process in reverse order to avoid line number shifts
        for test in reversed(tests):
            # Check if test already has LLM validation
            if "if llm_validator.enabled:" in test["body"]:
                print(f"  ⏭️  Skipping {test['name']} (already has LLM validation)")
                continue

            # Check if test already has llm_validator fixture
            line = self.lines[test["line_num"]]
            has_fixture = "llm_validator" in line

            # Add marker
            new_line_num = self.add_llm_validation_marker(test["line_num"])

            # Add fixture if needed
            if not has_fixture:
                self.add_llm_validator_fixture(new_line_num)

            # Find where to insert LLM validation (before function end)
            # Look for the last assert or last meaningful line in test
            insert_line = test["body_end"] - 1
            while (
                insert_line > test["line_num"] and self.lines[insert_line].strip() == ""
            ):
                insert_line -= 1

            # Generate validation code
            validation_code = self.generate_llm_validation_code(
                test["name"], test["body"], indent="        "
            )

            # Insert validation code
            self.lines.insert(insert_line + 1, validation_code)

            print(f"  ✅ Added LLM validation to {test['name']}")
            modifications += 1

        # Rebuild content
        self.modified_content = "\n".join(self.lines)
        return modifications

    def save(self, output_path: str = None):
        """Save modified content to file."""
        output_path = output_path or self.file_path
        with open(output_path, "w") as f:
            f.write(self.modified_content)
        print(f"\n💾 Saved to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add LLM validation to integration tests"
    )
    parser.add_argument("test_file", help="Path to test file")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without saving"
    )
    parser.add_argument("--output", help="Output file path (default: overwrite input)")

    args = parser.parse_args()

    print(f"\n📝 Processing: {args.test_file}")

    try:
        adder = LLMValidationAdder(args.test_file)
        modifications = adder.process_tests()

        print(f"\n📊 Summary:")
        print(f"   Tests modified: {modifications}")

        if modifications > 0 and not args.dry_run:
            adder.save(args.output)
            print(f"   ✅ Complete!")
        elif modifications == 0:
            print(f"   ℹ️  No changes needed - all tests already have LLM validation")
        else:
            print(f"   🔍 Dry run - no files modified")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
