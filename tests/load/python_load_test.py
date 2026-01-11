"""
Python-based Load Test for Guest Chat System

Alternative to k6 that can run on any system with Python.
Tests performance under concurrent load with realistic user behavior.
"""

import asyncio
import aiohttp
import time
import random
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime
import statistics


@dataclass
class LoadTestConfig:
    """Load test configuration."""
    base_url: str = "http://localhost:8000"
    duration_seconds: int = 180  # 3 minutes
    concurrent_users: int = 50
    think_time_min: float = 1.0
    think_time_max: float = 3.0
    timeout: float = 30.0


@dataclass
class TestResult:
    """Individual request result."""
    timestamp: float
    duration: float
    status_code: int
    intent: str
    token: str
    language: str
    success: bool
    error: str = ""


@dataclass
class LoadTestResults:
    """Aggregated load test results."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration: float = 0.0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    intent_counts: Dict[str, int] = field(default_factory=dict)
    status_codes: Dict[int, int] = field(default_factory=dict)
    cache_hits: int = 0  # Responses < 150ms

    def add_result(self, result: TestResult):
        """Add a test result."""
        self.total_requests += 1

        if result.success:
            self.successful_requests += 1
            self.response_times.append(result.duration)

            # Track cache hits (fast responses)
            if result.duration < 0.150:  # 150ms
                self.cache_hits += 1
        else:
            self.failed_requests += 1
            self.errors.append(result.error)

        # Track intent
        self.intent_counts[result.intent] = self.intent_counts.get(result.intent, 0) + 1

        # Track status codes
        self.status_codes[result.status_code] = self.status_codes.get(result.status_code, 0) + 1

    def get_percentile(self, percentile: float) -> float:
        """Calculate response time percentile."""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * percentile / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]

    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 80)
        print("LOAD TEST RESULTS")
        print("=" * 80)

        # Overall metrics
        print(f"\n📊 OVERALL METRICS")
        print(f"   Total Requests:      {self.total_requests:,}")
        print(f"   Successful:          {self.successful_requests:,} ({self.successful_requests/max(self.total_requests, 1)*100:.1f}%)")
        print(f"   Failed:              {self.failed_requests:,} ({self.failed_requests/max(self.total_requests, 1)*100:.1f}%)")
        print(f"   Error Rate:          {self.failed_requests/max(self.total_requests, 1)*100:.2f}%")

        # Response times
        if self.response_times:
            print(f"\n⚡ RESPONSE TIMES")
            print(f"   Average:             {statistics.mean(self.response_times)*1000:.0f}ms")
            print(f"   Median (P50):        {self.get_percentile(50)*1000:.0f}ms")
            print(f"   P95:                 {self.get_percentile(95)*1000:.0f}ms")
            print(f"   P99:                 {self.get_percentile(99)*1000:.0f}ms")
            print(f"   Min:                 {min(self.response_times)*1000:.0f}ms")
            print(f"   Max:                 {max(self.response_times)*1000:.0f}ms")

        # Cache performance
        cache_hit_rate = (self.cache_hits / max(self.successful_requests, 1)) * 100
        print(f"\n💾 CACHE PERFORMANCE")
        print(f"   Cache Hits:          {self.cache_hits:,} ({cache_hit_rate:.1f}%)")
        print(f"   Cache Misses:        {self.successful_requests - self.cache_hits:,}")

        # Intent distribution
        print(f"\n🎯 REQUEST DISTRIBUTION")
        for intent, count in sorted(self.intent_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / max(self.total_requests, 1)) * 100
            print(f"   {intent:20s} {count:>6,} ({percentage:>5.1f}%)")

        # Status codes
        print(f"\n📈 STATUS CODES")
        for code, count in sorted(self.status_codes.items()):
            percentage = (count / max(self.total_requests, 1)) * 100
            print(f"   {code:3d}:                 {count:>6,} ({percentage:>5.1f}%)")

        # Errors
        if self.errors:
            print(f"\n❌ ERRORS (showing first 10)")
            for error in self.errors[:10]:
                print(f"   • {error}")

        # Pass/Fail criteria
        print(f"\n✅ PASS/FAIL CRITERIA")
        error_rate = (self.failed_requests / max(self.total_requests, 1)) * 100
        p95 = self.get_percentile(95) * 1000 if self.response_times else 0

        print(f"   Error Rate < 1%:     {'✅ PASS' if error_rate < 1.0 else '❌ FAIL'} ({error_rate:.2f}%)")
        print(f"   P95 < 500ms:         {'✅ PASS' if p95 < 500 else '❌ FAIL'} ({p95:.0f}ms)")
        print(f"   Cache Hit Rate > 80%: {'✅ PASS' if cache_hit_rate > 80 else '⚠️  WARN'} ({cache_hit_rate:.1f}%)")

        print("\n" + "=" * 80 + "\n")


class GuestChatLoadTest:
    """Guest chat load test runner."""

    TOKENS = ['BTC', 'ETH', 'SOL', 'USDT', 'BNB', 'USDC', 'ADA', 'DOT']
    LANGUAGES = ['en', 'es', 'pt', 'zh']

    QUERIES = {
        'sentiment': [
            'What is the sentiment for {token}?',
            'How does the market feel about {token}?',
            'Is {token} bullish or bearish?',
        ],
        'trading_signals': [
            'Give me trading signals for {token}',
            'Should I buy {token}?',
            'What are the trading signals for {token}?',
        ],
        'price_prediction': [
            'Predict the price of {token}',
            'Where is {token} going?',
            'What will {token} price be?',
        ],
        'patterns': [
            'What patterns do you see in {token}?',
            'Are there any chart patterns for {token}?',
            'Show me patterns for {token}',
        ],
        'risk': [
            'What are the risks for {token}?',
            'Is {token} risky?',
            'Show me risk analysis for {token}',
        ],
    }

    def __init__(self, config: LoadTestConfig):
        """Initialize load test."""
        self.config = config
        self.results = LoadTestResults()
        self.start_time = None
        self.session = None

    def get_random_request(self) -> tuple[str, str, str]:
        """Generate random test request."""
        # Weight intents (sentiment and trading signals more common)
        rand = random.random()
        if rand < 0.4:
            intent = 'sentiment'
        elif rand < 0.7:
            intent = 'trading_signals'
        elif rand < 0.85:
            intent = 'price_prediction'
        elif rand < 0.93:
            intent = 'patterns'
        else:
            intent = 'risk'

        token = random.choice(self.TOKENS)
        language = random.choice(self.LANGUAGES)

        query_template = random.choice(self.QUERIES[intent])
        content = query_template.format(token=token)

        return content, intent, token, language

    async def make_request(self) -> TestResult:
        """Make a single request to the guest chat API."""
        content, intent, token, language = self.get_random_request()

        payload = {
            'content': content,
            'language': language,
        }

        start_time = time.time()

        try:
            async with self.session.post(
                f"{self.config.base_url}/api/v1/guest/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            ) as response:
                duration = time.time() - start_time
                status_code = response.status

                # Try to read response
                try:
                    data = await response.json()
                    # Response has agent_message.content structure
                    has_content = (
                        'agent_message' in data and
                        'content' in data.get('agent_message', {})
                    )
                    success = (status_code == 200 and has_content)
                    error = "" if success else f"Missing agent_message.content in response"
                except Exception as e:
                    success = False
                    error = f"Failed to parse response: {e}"

                return TestResult(
                    timestamp=start_time,
                    duration=duration,
                    status_code=status_code,
                    intent=intent,
                    token=token,
                    language=language,
                    success=success,
                    error=error,
                )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return TestResult(
                timestamp=start_time,
                duration=duration,
                status_code=0,
                intent=intent,
                token=token,
                language=language,
                success=False,
                error=f"Request timeout after {self.config.timeout}s",
            )

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                timestamp=start_time,
                duration=duration,
                status_code=0,
                intent=intent,
                token=token,
                language=language,
                success=False,
                error=f"Request failed: {str(e)}",
            )

    async def user_session(self, user_id: int):
        """Simulate a single user session."""
        while time.time() - self.start_time < self.config.duration_seconds:
            # Make request
            result = await self.make_request()
            self.results.add_result(result)

            # Think time
            think_time = random.uniform(
                self.config.think_time_min,
                self.config.think_time_max
            )
            await asyncio.sleep(think_time)

    async def run(self):
        """Run the load test."""
        print(f"\n🚀 Starting Load Test")
        print(f"   Base URL: {self.config.base_url}")
        print(f"   Duration: {self.config.duration_seconds}s")
        print(f"   Concurrent Users: {self.config.concurrent_users}")
        print(f"   Think Time: {self.config.think_time_min}s - {self.config.think_time_max}s")
        print(f"\n⏱️  Test will run for {self.config.duration_seconds // 60} minutes...\n")

        self.start_time = time.time()

        # Create session
        connector = aiohttp.TCPConnector(limit=self.config.concurrent_users * 2)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            self.session = session

            # Create user tasks
            tasks = [
                self.user_session(user_id)
                for user_id in range(self.config.concurrent_users)
            ]

            # Run all users concurrently
            await asyncio.gather(*tasks)

        # Print results
        self.results.total_duration = time.time() - self.start_time
        self.results.print_summary()

        return self.results


async def main():
    """Main entry point."""
    import sys

    # Parse command line arguments
    config = LoadTestConfig()

    if '--url' in sys.argv:
        idx = sys.argv.index('--url')
        config.base_url = sys.argv[idx + 1]

    if '--duration' in sys.argv:
        idx = sys.argv.index('--duration')
        config.duration_seconds = int(sys.argv[idx + 1])

    if '--users' in sys.argv:
        idx = sys.argv.index('--users')
        config.concurrent_users = int(sys.argv[idx + 1])

    # Run test
    test = GuestChatLoadTest(config)
    results = await test.run()

    # Exit with error code if test failed
    error_rate = (results.failed_requests / max(results.total_requests, 1)) * 100
    p95 = results.get_percentile(95) * 1000 if results.response_times else 0

    if error_rate >= 1.0 or p95 >= 500:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    asyncio.run(main())
