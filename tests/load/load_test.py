#!/usr/bin/env python
"""
Load testing script for Anvil Chat API.

Tests three scenarios:
1. Normal Load: 100 concurrent users, 1000 requests over 10 minutes
2. Peak Load: 1000 concurrent users, 10000 requests over 10 minutes
3. Burst Traffic: 5000 concurrent users, as many requests as possible in 2 minutes

Measures:
- Response times (min, max, avg, p50, p95, p99)
- Success rate
- Errors
- Requests per second
"""

import asyncio
import time
import statistics
import sys
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
import httpx

# Test configuration
API_BASE_URL = "http://localhost:8080"
GUEST_CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/guest/chat"


class LoadTestResult:
    """Container for load test results."""

    def __init__(self, scenario_name: str):
        self.scenario_name = scenario_name
        self.response_times: List[float] = []
        self.status_codes: List[int] = []
        self.errors: List[str] = []
        self.start_time: float = 0
        self.end_time: float = 0

    def add_result(self, response_time: float, status_code: int, error: str = None):
        """Add a test result."""
        self.response_times.append(response_time)
        self.status_codes.append(status_code)
        if error:
            self.errors.append(error)

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from results."""
        if not self.response_times:
            return {"error": "No results collected"}

        duration = self.end_time - self.start_time
        total_requests = len(self.response_times)
        successful_requests = sum(1 for code in self.status_codes if 200 <= code < 300)
        failed_requests = total_requests - successful_requests

        sorted_times = sorted(self.response_times)

        return {
            "scenario": self.scenario_name,
            "duration_seconds": round(duration, 2),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": round(successful_requests / total_requests * 100, 2),
            "requests_per_second": round(total_requests / duration, 2),
            "response_times": {
                "min_ms": round(min(self.response_times) * 1000, 2),
                "max_ms": round(max(self.response_times) * 1000, 2),
                "avg_ms": round(statistics.mean(self.response_times) * 1000, 2),
                "median_ms": round(statistics.median(self.response_times) * 1000, 2),
                "p95_ms": round(sorted_times[int(len(sorted_times) * 0.95)] * 1000, 2),
                "p99_ms": round(sorted_times[int(len(sorted_times) * 0.99)] * 1000, 2),
            },
            "status_code_distribution": dict(
                sorted(
                    ((code, count) for code, count in
                     defaultdict(int, ((c, self.status_codes.count(c)) for c in set(self.status_codes))).items()),
                    key=lambda x: x[0]
                )
            ),
            "error_count": len(self.errors),
            "unique_errors": len(set(self.errors)),
        }

    def print_summary(self):
        """Print formatted test summary."""
        stats = self.get_statistics()

        print(f"\n{'='*80}")
        print(f"LOAD TEST RESULTS: {stats['scenario']}")
        print(f"{'='*80}")
        print(f"\n📊 Overall Performance:")
        print(f"  Duration: {stats['duration_seconds']}s")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Successful: {stats['successful_requests']} ({stats['success_rate']}%)")
        print(f"  Failed: {stats['failed_requests']}")
        print(f"  Requests/sec: {stats['requests_per_second']}")

        rt = stats['response_times']
        print(f"\n⏱️  Response Times:")
        print(f"  Min: {rt['min_ms']}ms")
        print(f"  Avg: {rt['avg_ms']}ms")
        print(f"  Median: {rt['median_ms']}ms")
        print(f"  P95: {rt['p95_ms']}ms")
        print(f"  P99: {rt['p99_ms']}ms")
        print(f"  Max: {rt['max_ms']}ms")

        print(f"\n📈 Status Codes:")
        for code, count in stats['status_code_distribution'].items():
            print(f"  {code}: {count} requests")

        if stats['error_count'] > 0:
            print(f"\n❌ Errors:")
            print(f"  Total: {stats['error_count']}")
            print(f"  Unique: {stats['unique_errors']}")

        # Performance verdict
        print(f"\n🎯 Performance Verdict:")
        if rt['p95_ms'] < 500 and stats['success_rate'] > 99:
            print(f"  ✅ EXCELLENT - P95 < 500ms and >99% success rate")
        elif rt['p95_ms'] < 1000 and stats['success_rate'] > 95:
            print(f"  ✅ GOOD - P95 < 1000ms and >95% success rate")
        elif rt['p95_ms'] < 2000 and stats['success_rate'] > 90:
            print(f"  ⚠️  ACCEPTABLE - P95 < 2000ms and >90% success rate")
        else:
            print(f"  ❌ NEEDS IMPROVEMENT - High latency or low success rate")

        print(f"\n{'='*80}\n")


async def make_request(client: httpx.AsyncClient, request_data: Dict[str, Any]) -> tuple[float, int, str]:
    """Make a single HTTP request and measure response time."""
    start_time = time.time()
    try:
        response = await client.post(
            GUEST_CHAT_ENDPOINT,
            json=request_data,
            timeout=30.0,
        )
        response_time = time.time() - start_time
        return response_time, response.status_code, None
    except Exception as e:
        response_time = time.time() - start_time
        return response_time, 0, str(e)


async def run_user_session(
    user_id: int,
    num_requests: int,
    delay_between_requests: float,
    result: LoadTestResult,
):
    """Simulate a single user making requests."""
    async with httpx.AsyncClient() as client:
        for i in range(num_requests):
            # Vary the requests to avoid cache hits
            request_data = {
                "content": f"What's the sentiment for ETH? (user {user_id}, req {i})",
                "language": "en",
            }

            response_time, status_code, error = await make_request(client, request_data)
            result.add_result(response_time, status_code, error)

            if delay_between_requests > 0:
                await asyncio.sleep(delay_between_requests)


async def scenario_normal_load() -> LoadTestResult:
    """
    Scenario 1: Normal Load
    - 100 concurrent users
    - 1000 total requests
    - 10 requests per user
    - Evenly distributed over 10 minutes
    """
    print("\n🔄 Running Scenario 1: Normal Load (100 users, 1000 requests, 10 min)")

    result = LoadTestResult("Normal Load")
    result.start_time = time.time()

    num_users = 100
    requests_per_user = 10
    total_duration = 600  # 10 minutes
    delay_between_requests = total_duration / requests_per_user

    # Create tasks for all users
    tasks = [
        run_user_session(user_id, requests_per_user, delay_between_requests, result)
        for user_id in range(num_users)
    ]

    # Run all users concurrently
    await asyncio.gather(*tasks)

    result.end_time = time.time()
    return result


async def scenario_peak_load() -> LoadTestResult:
    """
    Scenario 2: Peak Load
    - 1000 concurrent users
    - 10000 total requests
    - 10 requests per user
    - Distributed over 10 minutes
    """
    print("\n🔄 Running Scenario 2: Peak Load (1000 users, 10000 requests, 10 min)")

    result = LoadTestResult("Peak Load")
    result.start_time = time.time()

    num_users = 1000
    requests_per_user = 10
    total_duration = 600  # 10 minutes
    delay_between_requests = total_duration / requests_per_user

    tasks = [
        run_user_session(user_id, requests_per_user, delay_between_requests, result)
        for user_id in range(num_users)
    ]

    await asyncio.gather(*tasks)

    result.end_time = time.time()
    return result


async def scenario_burst_traffic() -> LoadTestResult:
    """
    Scenario 3: Burst Traffic
    - 5000 concurrent users
    - As many requests as possible in 2 minutes
    - 5 requests per user (25000 total max)
    - No delay between requests (stress test)
    """
    print("\n🔄 Running Scenario 3: Burst Traffic (5000 users, max requests, 2 min)")

    result = LoadTestResult("Burst Traffic")
    result.start_time = time.time()

    num_users = 5000
    requests_per_user = 5  # Keep reasonable to avoid overwhelming system
    delay_between_requests = 0  # No delay - maximum burst

    tasks = [
        run_user_session(user_id, requests_per_user, delay_between_requests, result)
        for user_id in range(num_users)
    ]

    await asyncio.gather(*tasks)

    result.end_time = time.time()
    return result


async def main():
    """Run all load test scenarios."""
    print("\n" + "="*80)
    print("ANVIL CHAT API LOAD TESTING")
    print("="*80)
    print(f"\nTarget API: {API_BASE_URL}")
    print(f"Test Endpoint: {GUEST_CHAT_ENDPOINT}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if API is accessible
    print("\n🔍 Checking API accessibility...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health", timeout=10.0)
            if response.status_code == 200:
                print("✅ API is accessible")
            else:
                print(f"⚠️  API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        print("⚠️  Make sure the FastAPI server is running on port 8080")
        return

    # Run scenarios based on command line args
    scenarios = []
    if len(sys.argv) > 1:
        scenario_arg = sys.argv[1].lower()
        if scenario_arg == "normal":
            scenarios = [scenario_normal_load]
        elif scenario_arg == "peak":
            scenarios = [scenario_peak_load]
        elif scenario_arg == "burst":
            scenarios = [scenario_burst_traffic]
        elif scenario_arg == "all":
            scenarios = [scenario_normal_load, scenario_peak_load, scenario_burst_traffic]
        else:
            print(f"❌ Unknown scenario: {scenario_arg}")
            print("Usage: python load_test.py [normal|peak|burst|all]")
            return
    else:
        # Default: run normal load only
        print("\n📌 Running default scenario (normal load)")
        print("   Use: python load_test.py [normal|peak|burst|all] to select scenarios")
        scenarios = [scenario_normal_load]

    # Execute scenarios
    for scenario_func in scenarios:
        try:
            result = await scenario_func()
            result.print_summary()
        except KeyboardInterrupt:
            print("\n\n⚠️  Load test interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error running scenario: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n✅ Load testing complete")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
