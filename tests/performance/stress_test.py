"""
Stress testing scenarios.

Tests system behavior under extreme load.
"""

import asyncio
import time
from typing import List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class StressTestResult:
    """Result of stress test."""

    name: str
    total_requests: int
    successful: int
    failed: int
    total_time: float
    avg_response_time: float
    requests_per_second: float
    error_rate: float

    def __str__(self) -> str:
        """Format stress test result."""
        return f"""
Stress Test: {self.name}
Total Requests: {self.total_requests}
Successful: {self.successful} ({self.successful / self.total_requests * 100:.1f}%)
Failed: {self.failed} ({self.error_rate * 100:.1f}%)
Total Time: {self.total_time:.2f}s
Avg Response: {self.avg_response_time * 1000:.2f}ms
Throughput: {self.requests_per_second:.2f} req/s
        """


class StressTest:
    """
    Stress testing utility.

    Tests system under high concurrent load.
    """

    async def run(
        self,
        name: str,
        func,
        concurrent_users: int = 100,
        requests_per_user: int = 10,
    ) -> StressTestResult:
        """
        Run stress test.

        Args:
            name: Test name
            func: Async function to test
            concurrent_users: Number of concurrent users
            requests_per_user: Requests per user

        Returns:
            Stress test result
        """
        total_requests = concurrent_users * requests_per_user
        successful = 0
        failed = 0
        response_times = []

        async def user_simulation():
            """Simulate single user."""
            nonlocal successful, failed

            for _ in range(requests_per_user):
                start = time.perf_counter()
                try:
                    await func()
                    successful += 1
                    elapsed = time.perf_counter() - start
                    response_times.append(elapsed)
                except Exception as e:
                    failed += 1
                    logger.error(f"Request failed: {e}")

        # Run concurrent users
        start_time = time.perf_counter()

        tasks = [user_simulation() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks)

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Calculate stats
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )
        requests_per_second = total_requests / total_time
        error_rate = failed / total_requests if total_requests > 0 else 0

        return StressTestResult(
            name=name,
            total_requests=total_requests,
            successful=successful,
            failed=failed,
            total_time=total_time,
            avg_response_time=avg_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
        )


# Example stress tests


async def stress_test_message_sending():
    """Stress test message sending."""
    from unittest.mock import AsyncMock
    from uuid import uuid4
    from app.application.chat.commands.send_message import SendMessage

    # Setup mocks
    mock_repo = AsyncMock()
    mock_agent = AsyncMock()
    mock_context = AsyncMock()

    mock_agent.process_message.return_value = "Response"
    mock_context.get_or_create_context.return_value = AsyncMock()
    mock_context.get_agent_context.return_value = {}

    send_message = SendMessage(
        repository=mock_repo,
        agent_gateway=mock_agent,
        context_manager=mock_context,
    )

    # Stress test
    async def send():
        await send_message.execute(
            conversation_id=uuid4(),
            content="Test message",
        )

    stress = StressTest()
    result = await stress.run(
        name="Message Sending Under Load",
        func=send,
        concurrent_users=100,
        requests_per_user=10,
    )

    print(result)


async def stress_test_cache_concurrent():
    """Stress test concurrent cache access."""
    from app.infrastructure.caching.redis_cache import RedisCache

    cache = RedisCache()
    await cache.connect()

    # Pre-populate cache
    await cache.set("stress_test_key", {"data": "value"}, category="default")

    # Stress test concurrent reads
    async def read():
        await cache.get("stress_test_key")

    stress = StressTest()
    result = await stress.run(
        name="Concurrent Cache Reads",
        func=read,
        concurrent_users=500,
        requests_per_user=20,
    )

    print(result)

    await cache.disconnect()


async def stress_test_rate_limiter_enforcement():
    """Stress test rate limiter under abuse."""
    from app.infrastructure.performance.rate_limiter import get_rate_limiter

    limiter = get_rate_limiter()

    # Configure aggressive limit
    limiter.configure("stress_test", max_tokens=100, refill_rate=10)

    # Try to exceed limit
    async def acquire():
        acquired = await limiter.acquire("stress_test", tokens=1, timeout=0.1)
        if not acquired:
            raise Exception("Rate limited")

    stress = StressTest()
    result = await stress.run(
        name="Rate Limiter Enforcement",
        func=acquire,
        concurrent_users=50,
        requests_per_user=10,
    )

    print(result)
    print(f"Rate limit successfully blocked {result.failed} requests")


async def stress_test_batch_processor():
    """Stress test batch processor throughput."""
    from app.infrastructure.performance.batch_processor import BatchProcessor

    processed_count = 0

    async def process_batch(items):
        nonlocal processed_count
        processed_count += len(items)
        await asyncio.sleep(0.01)  # Simulate processing

    processor = BatchProcessor(
        batch_size=50,
        max_wait_time=0.5,
        processor_func=process_batch,
    )

    # Stress test
    async def add_item():
        await processor.add("test_item")

    stress = StressTest()
    result = await stress.run(
        name="Batch Processor Throughput",
        func=add_item,
        concurrent_users=100,
        requests_per_user=20,
    )

    # Flush remaining
    await processor.flush()

    print(result)
    print(f"Processed {processed_count} items in batches")


async def run_all_stress_tests():
    """Run all stress tests."""
    print("=" * 60)
    print("STRESS TESTS")
    print("=" * 60)

    print("\n1. Message Sending Under Load")
    print("-" * 60)
    await stress_test_message_sending()

    print("\n2. Concurrent Cache Access")
    print("-" * 60)
    await stress_test_cache_concurrent()

    print("\n3. Rate Limiter Enforcement")
    print("-" * 60)
    await stress_test_rate_limiter_enforcement()

    print("\n4. Batch Processor Throughput")
    print("-" * 60)
    await stress_test_batch_processor()

    print("\n" + "=" * 60)
    print("STRESS TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_stress_tests())
