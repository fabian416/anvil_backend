"""
Shared fixtures for agent tests.

This module provides common fixtures and utilities for testing all agents.
"""

import pytest
import pytest_asyncio
from typing import Any

# Re-export from parent conftest
from ..conftest import (
    CSVReporter,
    TestResult,
    TokenManager,
    send_message,
    create_conversation,
    parse_response,
    create_test_result,
    validate_with_llm,
    OUTPUT_DIR,
)


@pytest.fixture(scope="module")
def agent_reporter(request) -> CSVReporter:
    """Create CSV reporter for agent-specific test suite."""
    # Get the agent name from the test module path
    module_path = request.fspath.strpath
    if "/agents/" in module_path:
        agent_name = module_path.split("/agents/")[-1].split("/")[0]
    else:
        agent_name = "unknown"
    
    reporter = CSVReporter(category=f"agent_{agent_name}")
    yield reporter
    
    if reporter.results:
        csv_path = reporter.write_csv()
        summary_path = reporter.write_summary()
        reporter.print_summary()
        print(f"\nCSV output: {csv_path}")
        print(f"Summary: {summary_path}")


def run_agent_tests(test_cases: list[dict], authenticated_client, reporter: CSVReporter):
    """
    Run a list of agent test cases.
    
    Args:
        test_cases: List of test case dictionaries with keys:
            - test_id: Unique test identifier
            - input: User query
            - expected_agent: Expected agent to handle the query
            - category: Test category (e.g., "agent", "workflow")
            - subcategory: Test subcategory
        authenticated_client: Authenticated HTTP client
        reporter: CSV reporter for results
    """
    import asyncio
    
    async def _run():
        for test_case in test_cases:
            # Create new conversation for each test
            conv_id = await create_conversation(
                authenticated_client, 
                title=f"Test {test_case['test_id']}"
            )
            
            # Send message
            language = test_case.get("language", "en")
            response_data, response_time = await send_message(
                authenticated_client,
                conv_id,
                test_case["input"],
                language=language,
                timeout=90.0,
            )
            
            # Parse response
            parsed = parse_response(response_data)
            
            # Determine status
            expected_agent = test_case.get("expected_agent", "")
            actual_agents = parsed.get("agents_used", "")
            has_error = parsed.get("error", False)
            
            if has_error:
                status = "FAIL"
            elif expected_agent and expected_agent in actual_agents:
                status = "PASS"
            elif actual_agents:
                status = "PARTIAL"
            else:
                status = "FAIL"
            
            # Create result
            result = TestResult(
                test_id=test_case["test_id"],
                category=test_case.get("category", ""),
                subcategory=test_case.get("subcategory", ""),
                input=test_case["input"],
                output=parsed.get("content", "")[:500],
                expected_agent=expected_agent,
                actual_agents=actual_agents,
                sources=parsed.get("sources", ""),
                handler=parsed.get("handler", ""),
                response_time_ms=response_time,
                has_execute_data="YES" if parsed.get("execute_data") else "NO",
                user_type="authenticated",
                language=language,
                status=status,
                error_message=parsed.get("error_message", ""),
                conversation_id=conv_id,
            )
            
            reporter.add_result(result)
            
            # Print progress
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"{status_emoji} {test_case['test_id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)")
            
            await asyncio.sleep(0.5)
    
    asyncio.run(_run())
