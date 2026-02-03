"""Tool Call Batching.

Batches multiple tool calls for parallel execution to improve performance.

Features:
    - Parallel tool execution
    - Request batching
    - Error handling per tool
    - Timeout management
    - Result aggregation
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

import httpx


logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a single tool call."""

    tool_name: str
    parameters: Dict[str, Any]
    tool_id: Optional[str] = None

    def __post_init__(self):
        """Generate tool_id if not provided."""
        if not self.tool_id:
            self.tool_id = f"{self.tool_name}_{id(self)}"


@dataclass
class ToolResult:
    """Represents a tool call result."""

    tool_call: ToolCall
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    success: bool = False


class ToolCallBatcher:
    """
    Batches and executes multiple tool calls in parallel.

    Improves performance by executing multiple tool calls concurrently
    instead of sequentially.

    Usage:
        batcher = ToolCallBatcher(mcp_manager_url="http://localhost:8080")

        calls = [
            ToolCall("get_swap_quote", {"chain_id": 1, ...}),
            ToolCall("get_token_price", {"token": "ETH"}),
            ToolCall("get_market_data", {"chain_id": 1}),
        ]

        results = await batcher.execute_batch(calls)
    """

    def __init__(
        self,
        mcp_manager_url: str = "http://localhost:8080",
        max_parallel: int = 10,
        timeout_seconds: float = 30.0,
    ):
        """
        Initialize batcher.

        Args:
            mcp_manager_url: MCP Manager URL
            max_parallel: Max parallel executions
            timeout_seconds: Timeout per tool call
        """
        self.mcp_manager_url = mcp_manager_url
        self.max_parallel = max_parallel
        self.timeout_seconds = timeout_seconds

    async def execute_single(
        self,
        tool_call: ToolCall,
        client: httpx.AsyncClient,
    ) -> ToolResult:
        """
        Execute a single tool call.

        Args:
            tool_call: Tool call to execute
            client: HTTP client

        Returns:
            Tool result
        """
        start_time = datetime.now()

        try:
            response = await client.post(
                f"{self.mcp_manager_url}/tools/{tool_call.tool_name}",
                json={"parameters": tool_call.parameters},
                timeout=self.timeout_seconds,
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                result_data = response.json()
                return ToolResult(
                    tool_call=tool_call,
                    result=result_data.get("result"),
                    duration_ms=duration_ms,
                    success=True,
                )
            else:
                return ToolResult(
                    tool_call=tool_call,
                    error=f"HTTP {response.status_code}: {response.text}",
                    duration_ms=duration_ms,
                    success=False,
                )

        except asyncio.TimeoutError:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            return ToolResult(
                tool_call=tool_call,
                error=f"Timeout after {self.timeout_seconds}s",
                duration_ms=duration_ms,
                success=False,
            )

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Tool call error ({tool_call.tool_name}): {e}")
            return ToolResult(
                tool_call=tool_call,
                error=str(e),
                duration_ms=duration_ms,
                success=False,
            )

    async def execute_batch(
        self,
        tool_calls: List[ToolCall],
        on_result: Optional[Callable[[ToolResult], None]] = None,
    ) -> List[ToolResult]:
        """
        Execute multiple tool calls in parallel.

        Args:
            tool_calls: List of tool calls
            on_result: Optional callback for each result

        Returns:
            List of tool results (in same order as input)
        """
        if not tool_calls:
            return []

        logger.info(f"Executing batch of {len(tool_calls)} tool calls")

        async with httpx.AsyncClient() as client:
            # Create tasks with semaphore for max parallel limit
            semaphore = asyncio.Semaphore(self.max_parallel)

            async def execute_with_semaphore(call):
                async with semaphore:
                    result = await self.execute_single(call, client)
                    if on_result:
                        on_result(result)
                    return result

            # Execute all in parallel
            results = await asyncio.gather(
                *[execute_with_semaphore(call) for call in tool_calls],
                return_exceptions=False,
            )

        # Log summary
        successes = sum(1 for r in results if r.success)
        total_duration = sum(r.duration_ms for r in results)

        logger.info(
            f"Batch complete: {successes}/{len(results)} successful, "
            f"total time: {total_duration:.0f}ms"
        )

        return results

    async def execute_batch_with_retry(
        self,
        tool_calls: List[ToolCall],
        max_retries: int = 2,
    ) -> List[ToolResult]:
        """
        Execute batch with automatic retry for failed calls.

        Args:
            tool_calls: List of tool calls
            max_retries: Max retry attempts

        Returns:
            List of tool results
        """
        results = await self.execute_batch(tool_calls)

        # Retry failed calls
        for retry in range(max_retries):
            failed_calls = [r.tool_call for r in results if not r.success]

            if not failed_calls:
                break

            logger.info(
                f"Retrying {len(failed_calls)} failed calls (attempt {retry + 1})"
            )
            retry_results = await self.execute_batch(failed_calls)

            # Update results
            retry_idx = 0
            for i, result in enumerate(results):
                if not result.success:
                    results[i] = retry_results[retry_idx]
                    retry_idx += 1

        return results


# Example usage
if __name__ == "__main__":

    async def test_batching():
        """Test tool call batching."""
        batcher = ToolCallBatcher()

        # Create multiple tool calls
        calls = [
            ToolCall(
                "portfolio__get_user_balance", {"user_id": "user_1", "chain_id": 1}
            ),
            ToolCall(
                "portfolio__get_user_balance", {"user_id": "user_2", "chain_id": 1}
            ),
            ToolCall(
                "portfolio__get_user_balance", {"user_id": "user_3", "chain_id": 1}
            ),
            ToolCall("1inch__get_token_price", {"chain_id": 1, "token": "ETH"}),
            ToolCall("1inch__get_token_price", {"chain_id": 1, "token": "USDC"}),
            ToolCall("aave__get_market_data", {"chain_id": 1}),
            ToolCall("defillama__get_protocol_tvl", {"protocol": "aave"}),
        ]

        print(f"\n🚀 Executing batch of {len(calls)} tool calls...")

        # Execute batch
        results = await batcher.execute_batch(calls)

        # Print results
        print("\n📊 Results:")
        for i, result in enumerate(results, 1):
            status = "✅" if result.success else "❌"
            print(
                f"{status} {i}. {result.tool_call.tool_name} "
                f"({result.duration_ms:.0f}ms)"
            )
            if result.error:
                print(f"   Error: {result.error}")

        # Summary
        successes = sum(1 for r in results if r.success)
        total_duration = sum(r.duration_ms for r in results)
        avg_duration = total_duration / len(results)

        print(f"\n📈 Summary:")
        print(f"   Total calls: {len(results)}")
        print(f"   Successful: {successes}")
        print(f"   Failed: {len(results) - successes}")
        print(f"   Total time: {total_duration:.0f}ms")
        print(f"   Avg time: {avg_duration:.0f}ms")

    asyncio.run(test_batching())
