"""
Performance benchmarking suite.

Measures response times, throughput, and resource usage.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    median_time: float
    p95_time: float
    p99_time: float
    throughput: float  # ops/sec
    
    def __str__(self) -> str:
        """Format benchmark result."""
        return f"""
Benchmark: {self.name}
Iterations: {self.iterations}
Total Time: {self.total_time:.2f}s
Average: {self.avg_time*1000:.2f}ms
Median: {self.median_time*1000:.2f}ms
Min: {self.min_time*1000:.2f}ms
Max: {self.max_time*1000:.2f}ms
P95: {self.p95_time*1000:.2f}ms
P99: {self.p99_time*1000:.2f}ms
Throughput: {self.throughput:.2f} ops/sec
        """


class Benchmark:
    """
    Performance benchmarking utility.
    
    Usage:
        benchmark = Benchmark()
        result = await benchmark.run(
            name="Test",
            func=my_async_func,
            iterations=1000,
        )
        print(result)
    """
    
    async def run(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        warmup: int = 10,
    ) -> BenchmarkResult:
        """
        Run benchmark.
        
        Args:
            name: Benchmark name
            func: Async function to benchmark
            iterations: Number of iterations
            warmup: Warmup iterations (not measured)
        
        Returns:
            Benchmark result
        """
        # Warmup
        for _ in range(warmup):
            await func()
        
        # Benchmark
        times: List[float] = []
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            iter_start = time.perf_counter()
            await func()
            iter_end = time.perf_counter()
            times.append(iter_end - iter_start)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        
        sorted_times = sorted(times)
        p95_time = sorted_times[int(len(sorted_times) * 0.95)]
        p99_time = sorted_times[int(len(sorted_times) * 0.99)]
        
        throughput = iterations / total_time
        
        return BenchmarkResult(
            name=name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            p95_time=p95_time,
            p99_time=p99_time,
            throughput=throughput,
        )
    
    async def compare(
        self,
        benchmarks: Dict[str, Callable],
        iterations: int = 100,
    ) -> List[BenchmarkResult]:
        """
        Compare multiple benchmarks.
        
        Args:
            benchmarks: Dict of name -> function
            iterations: Iterations per benchmark
        
        Returns:
            List of results
        """
        results = []
        for name, func in benchmarks.items():
            result = await self.run(name, func, iterations)
            results.append(result)
        
        return results


# Example benchmarks

async def benchmark_message_sending():
    """Benchmark message sending performance."""
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
    
    # Benchmark
    async def send():
        await send_message.execute(
            conversation_id=uuid4(),
            content="Test message",
        )
    
    benchmark = Benchmark()
    result = await benchmark.run(
        name="Message Sending",
        func=send,
        iterations=1000,
    )
    
    print(result)


async def benchmark_cache_performance():
    """Benchmark cache read/write performance."""
    from app.infrastructure.caching.redis_cache import RedisCache
    
    cache = RedisCache()
    await cache.connect()
    
    # Benchmark write
    async def write():
        await cache.set("test_key", {"data": "value"}, category="default")
    
    # Benchmark read
    async def read():
        await cache.get("test_key")
    
    benchmark = Benchmark()
    
    results = await benchmark.compare({
        "Cache Write": write,
        "Cache Read": read,
    }, iterations=1000)
    
    for result in results:
        print(result)
    
    await cache.disconnect()


async def benchmark_rate_limiter():
    """Benchmark rate limiter performance."""
    from app.infrastructure.performance.rate_limiter import get_rate_limiter
    
    limiter = get_rate_limiter()
    
    async def acquire():
        await limiter.acquire("test_key")
    
    benchmark = Benchmark()
    result = await benchmark.run(
        name="Rate Limiter Acquire",
        func=acquire,
        iterations=1000,
    )
    
    print(result)


async def benchmark_intent_refinement():
    """Benchmark intent refinement performance."""
    from app.infrastructure.ai.intent_refiner import IntentRefiner
    
    refiner = IntentRefiner()
    
    async def refine():
        refiner.refine_intent(
            message="I want to swap BTC to ETH",
            initial_intent="trade_swap",
            initial_confidence=0.8,
            context={},
        )
    
    benchmark = Benchmark()
    result = await benchmark.run(
        name="Intent Refinement",
        func=refine,
        iterations=1000,
    )
    
    print(result)


async def run_all_benchmarks():
    """Run all benchmarks."""
    print("=" * 60)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 60)
    
    print("\n1. Message Sending")
    print("-" * 60)
    await benchmark_message_sending()
    
    print("\n2. Cache Performance")
    print("-" * 60)
    await benchmark_cache_performance()
    
    print("\n3. Rate Limiter")
    print("-" * 60)
    await benchmark_rate_limiter()
    
    print("\n4. Intent Refinement")
    print("-" * 60)
    await benchmark_intent_refinement()
    
    print("\n" + "=" * 60)
    print("BENCHMARKS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_benchmarks())
