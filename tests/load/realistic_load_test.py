"""
Realistic Load Test with Cache Warm-up

This test simulates real-world usage patterns:
1. Warm up cache with popular tokens
2. 80% of requests use cached data (popular tokens)
3. 20% of requests cause cache misses (less popular tokens)
"""

import asyncio
import aiohttp
import time
import random
from dataclasses import dataclass, field
import statistics


@dataclass
class TestMetrics:
    """Test metrics."""

    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    timeouts: int = 0
    response_times: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    cache_hits: int = 0  # < 200ms
    cache_misses: int = 0  # >= 200ms

    def add_success(self, duration: float):
        self.total_requests += 1
        self.successful += 1
        self.response_times.append(duration)

        if duration < 0.200:  # 200ms
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def add_failure(self, error: str, is_timeout: bool = False):
        self.total_requests += 1
        self.failed += 1
        if is_timeout:
            self.timeouts += 1
        self.errors.append(error)

    def print_summary(self, phase: str = ""):
        """Print test summary."""
        title = f"LOAD TEST RESULTS - {phase}" if phase else "LOAD TEST RESULTS"
        print("\n" + "=" * 80)
        print(title)
        print("=" * 80)

        # Overall
        success_rate = (self.successful / max(self.total_requests, 1)) * 100
        error_rate = (self.failed / max(self.total_requests, 1)) * 100

        print(f"\n📊 OVERALL")
        print(f"   Total Requests:      {self.total_requests:,}")
        print(f"   Successful:          {self.successful:,} ({success_rate:.1f}%)")
        print(f"   Failed:              {self.failed:,} ({error_rate:.1f}%)")
        print(f"   Timeouts:            {self.timeouts:,}")

        # Response times
        if self.response_times:
            sorted_times = sorted(self.response_times)
            p50_idx = int(len(sorted_times) * 0.50)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)

            print(f"\n⚡ RESPONSE TIMES")
            print(
                f"   Average:             {statistics.mean(self.response_times) * 1000:.0f}ms"
            )
            print(f"   Median (P50):        {sorted_times[p50_idx] * 1000:.0f}ms")
            print(
                f"   P95:                 {sorted_times[min(p95_idx, len(sorted_times) - 1)] * 1000:.0f}ms"
            )
            print(
                f"   P99:                 {sorted_times[min(p99_idx, len(sorted_times) - 1)] * 1000:.0f}ms"
            )
            print(f"   Min:                 {min(self.response_times) * 1000:.0f}ms")
            print(f"   Max:                 {max(self.response_times) * 1000:.0f}ms")

        # Cache performance
        total_completed = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / max(total_completed, 1)) * 100

        print(f"\n💾 CACHE PERFORMANCE")
        print(f"   Cache Hits:          {self.cache_hits:,} ({cache_hit_rate:.1f}%)")
        print(f"   Cache Misses:        {self.cache_misses:,}")

        # Pass/Fail
        p95 = (
            sorted_times[min(p95_idx, len(sorted_times) - 1)] * 1000
            if self.response_times
            else 0
        )

        print(f"\n✅ PASS/FAIL CRITERIA")
        print(
            f"   Error Rate < 5%:     {'✅ PASS' if error_rate < 5.0 else '❌ FAIL'} ({error_rate:.2f}%)"
        )
        print(
            f"   P95 < 500ms:         {'✅ PASS' if p95 < 500 else '❌ FAIL'} ({p95:.0f}ms)"
        )
        print(
            f"   Cache Hit Rate > 70%: {'✅ PASS' if cache_hit_rate > 70 else '⚠️  WARN'} ({cache_hit_rate:.1f}%)"
        )

        print("\n" + "=" * 80 + "\n")


async def make_request(
    session: aiohttp.ClientSession, url: str, content: str, language: str = "en"
) -> tuple[bool, float, str]:
    """Make a single request."""
    start = time.time()

    try:
        async with session.post(
            url,
            json={"content": content, "language": language},
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            duration = time.time() - start

            if response.status == 200:
                data = await response.json()
                has_content = "agent_message" in data and "content" in data.get(
                    "agent_message", {}
                )
                return (has_content, duration, "")
            else:
                return (False, duration, f"HTTP {response.status}")

    except asyncio.TimeoutError:
        return (False, 60.0, "Timeout")
    except Exception as e:
        return (False, time.time() - start, str(e))


async def warm_up_cache(session: aiohttp.ClientSession, url: str):
    """Warm up cache with popular tokens."""
    print("\n🔥 Warming up cache...")

    tokens = ["BTC", "ETH", "SOL"]
    intents = ["sentiment", "trading_signals", "price_prediction"]
    languages = ["en"]

    tasks = []
    for token in tokens:
        for intent in intents:
            if intent == "sentiment":
                content = f"What is the sentiment for {token}?"
            elif intent == "trading_signals":
                content = f"Give me trading signals for {token}"
            else:
                content = f"Predict the price of {token}"

            for language in languages:
                tasks.append(make_request(session, url, content, language))

    # Execute warm-up requests
    results = await asyncio.gather(*tasks)

    successful = sum(1 for success, _, _ in results if success)
    print(f"   Warmed {successful}/{len(tasks)} cache entries")
    print(f"   Cache is ready! 🚀\n")


async def run_load_test():
    """Run realistic load test."""
    BASE_URL = "http://localhost:8080/api/v1/guest/chat"

    # Popular tokens (80% of requests)
    popular_tokens = ["BTC", "ETH", "SOL"]

    # Less popular tokens (20% of requests)
    other_tokens = ["USDT", "BNB", "USDC", "ADA", "DOT"]

    queries = {
        "sentiment": "What is the sentiment for {token}?",
        "trading_signals": "Give me trading signals for {token}",
        "price_prediction": "Predict the price of {token}",
        "greeting": "Hello",
        "help": "How does this work?",
    }

    metrics = TestMetrics()

    async with aiohttp.ClientSession() as session:
        # Phase 1: Warm up cache
        await warm_up_cache(session, BASE_URL)

        # Phase 2: Run load test
        print("📊 Running load test (60 seconds)...\n")

        start_time = time.time()
        duration = 60  # 1 minute

        while time.time() - start_time < duration:
            # Determine query type
            rand = random.random()

            if rand < 0.1:
                # 10% greetings/help (always fast)
                content = random.choice([queries["greeting"], queries["help"]])
            else:
                # 90% Hunter AI queries
                intent = random.choice([
                    "sentiment",
                    "trading_signals",
                    "price_prediction",
                ])

                # 80% use popular tokens (cached), 20% use other tokens
                if random.random() < 0.8:
                    token = random.choice(popular_tokens)
                else:
                    token = random.choice(other_tokens)

                content = queries[intent].format(token=token)

            # Make request
            success, duration_s, error = await make_request(session, BASE_URL, content)

            if success:
                metrics.add_success(duration_s)
            else:
                metrics.add_failure(error, is_timeout=(error == "Timeout"))

            # Progress indicator
            if metrics.total_requests % 10 == 0:
                elapsed = time.time() - start_time
                rate = metrics.total_requests / elapsed
                print(
                    f"   {metrics.total_requests:>3} requests | {rate:.1f} req/s | {metrics.successful}/{metrics.total_requests} success"
                )

            # Think time
            await asyncio.sleep(random.uniform(0.5, 1.5))

    # Print results
    metrics.print_summary("Realistic Load Test with Cache")


if __name__ == "__main__":
    asyncio.run(run_load_test())
