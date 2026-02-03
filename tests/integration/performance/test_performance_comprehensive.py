"""
Comprehensive Performance Testing Suite - Week 12 (P3-2)

Tests system performance, scalability, and resource usage:
- Concurrent user load testing
- Response time benchmarks
- Rate limit validation
- Database query performance
- API endpoint stress testing

Target: 12 comprehensive performance tests.

Test Classes:
1. TestConcurrentLoad (3 tests) - Concurrent user simulation
2. TestResponseTimeBenchmarks (3 tests) - Performance baselines
3. TestRateLimitValidation (3 tests) - Rate limiting enforcement
4. TestDatabasePerformance (3 tests) - Query optimization validation
"""

import asyncio
import time
from statistics import mean, median
import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.performance,
]


@pytest.mark.asyncio
class TestConcurrentLoad:
    """Concurrent user load testing (3 tests)."""

    async def test_concurrent_001_multiple_users_guest_chat(self, client: AsyncClient):
        """
        GIVEN 10 concurrent guest users
        WHEN sending chat messages simultaneously
        THEN all requests should complete within acceptable time
        """

        async def send_guest_message(user_num: int):
            start_time = time.time()
            response = await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": f"What is the price of Bitcoin? (user {user_num})",
                    "language": "en",
                },
            )
            elapsed = time.time() - start_time
            return {
                "user": user_num,
                "status": response.status_code,
                "elapsed": elapsed,
                "success": response.status_code == 200,
            }

        # Simulate 10 concurrent users
        tasks = [send_guest_message(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All requests should succeed
        successful = [r for r in results if r["success"]]
        assert len(successful) >= 8, "At least 80% requests should succeed"

        # Average response time should be reasonable
        avg_time = mean([r["elapsed"] for r in results])
        assert avg_time < 10.0, f"Average response time {avg_time:.2f}s exceeds 10s"

    async def test_concurrent_002_authenticated_users_parallel(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
        conversation_id: str,
    ):
        """
        GIVEN authenticated user sending multiple requests
        WHEN sending 5 parallel messages to same conversation
        THEN all should process without deadlocks
        """

        async def send_message(msg_num: int):
            start_time = time.time()
            response = await authenticated_client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                headers=auth_headers,
                json={
                    "content": f"Message {msg_num}",
                    "language": "en",
                },
            )
            elapsed = time.time() - start_time
            return {
                "message": msg_num,
                "status": response.status_code,
                "elapsed": elapsed,
            }

        # Send 5 parallel messages
        tasks = [send_message(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r["status"] == 200 for r in results)

        # No deadlocks (all complete in reasonable time)
        max_time = max(r["elapsed"] for r in results)
        assert max_time < 15.0, f"Max response time {max_time:.2f}s indicates deadlock"

    async def test_concurrent_003_mixed_endpoints_stress(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
    ):
        """
        GIVEN multiple endpoint types
        WHEN hitting different endpoints concurrently
        THEN system should handle mixed load
        """

        async def create_conversation():
            response = await authenticated_client.post(
                "/api/v1/conversations",
                headers=auth_headers,
                json={"language": "en"},
            )
            return response.status_code == 200

        async def get_shortcuts():
            response = await authenticated_client.get(
                "/api/v1/public/chat/shortcuts",
            )
            return response.status_code == 200

        # Mix of different operations
        tasks = []
        for i in range(3):
            tasks.append(create_conversation())
            tasks.append(get_shortcuts())

        results = await asyncio.gather(*tasks)

        # At least 80% success rate
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"Success rate {success_rate:.1%} below 80%"


@pytest.mark.asyncio
class TestResponseTimeBenchmarks:
    """Response time performance benchmarks (3 tests)."""

    async def test_benchmark_001_guest_chat_response_time(self, client: AsyncClient):
        """
        GIVEN guest chat endpoint
        WHEN measuring response times across 10 requests
        THEN median response time should be under 5 seconds
        """
        response_times = []

        for i in range(10):
            start_time = time.time()
            response = await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": "What is Bitcoin?",
                    "language": "en",
                },
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                response_times.append(elapsed)

        assert len(response_times) >= 8, "Not enough successful responses"

        median_time = median(response_times)
        avg_time = mean(response_times)
        min_time = min(response_times)
        max_time = max(response_times)

        # Performance assertions
        assert median_time < 5.0, f"Median response time {median_time:.2f}s exceeds 5s"
        assert avg_time < 6.0, f"Average response time {avg_time:.2f}s exceeds 6s"
        assert max_time < 15.0, f"Max response time {max_time:.2f}s exceeds 15s"

        print(f"\n📊 Guest Chat Performance:")
        print(f"  Min: {min_time:.2f}s")
        print(f"  Median: {median_time:.2f}s")
        print(f"  Avg: {avg_time:.2f}s")
        print(f"  Max: {max_time:.2f}s")

    async def test_benchmark_002_authenticated_message_performance(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
        conversation_id: str,
    ):
        """
        GIVEN authenticated conversation
        WHEN measuring response times across 10 messages
        THEN performance should be consistent
        """
        response_times = []

        for i in range(10):
            start_time = time.time()
            response = await authenticated_client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                headers=auth_headers,
                json={
                    "content": f"Test message {i}",
                    "language": "en",
                },
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                response_times.append(elapsed)

        assert len(response_times) >= 8

        median_time = median(response_times)
        avg_time = mean(response_times)

        assert median_time < 5.0
        assert avg_time < 6.0

        print(f"\n📊 Authenticated Message Performance:")
        print(f"  Median: {median_time:.2f}s")
        print(f"  Avg: {avg_time:.2f}s")

    async def test_benchmark_003_shortcuts_api_performance(
        self,
        authenticated_client: AsyncClient,
    ):
        """
        GIVEN shortcuts API endpoint
        WHEN measuring response times
        THEN should be fast (< 500ms median)
        """
        response_times = []

        for i in range(20):
            start_time = time.time()
            response = await authenticated_client.get(
                "/api/v1/public/chat/shortcuts",
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                response_times.append(elapsed)

        median_time = median(response_times)
        avg_time = mean(response_times)

        # Shortcuts should be very fast (read-only, cached)
        assert median_time < 0.5, f"Median {median_time:.3f}s exceeds 500ms"
        assert avg_time < 1.0, f"Average {avg_time:.3f}s exceeds 1s"

        print(f"\n📊 Shortcuts API Performance:")
        print(f"  Median: {median_time * 1000:.0f}ms")
        print(f"  Avg: {avg_time * 1000:.0f}ms")


@pytest.mark.asyncio
class TestRateLimitValidation:
    """Rate limit enforcement validation (3 tests)."""

    async def test_rate_limit_001_guest_message_limit(self, client: AsyncClient):
        """
        GIVEN guest chat endpoint with rate limiting
        WHEN exceeding rate limit (20 messages/hour)
        THEN should receive 429 Too Many Requests
        """
        # Send messages until rate limited
        success_count = 0
        rate_limited = False

        for i in range(25):
            response = await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": f"Message {i}",
                    "language": "en",
                },
            )

            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited = True
                break

        # Should hit rate limit before 25 messages
        assert rate_limited or success_count <= 20, (
            "Rate limiting not enforced (sent >20 without 429)"
        )

        print(f"\n🚦 Rate Limit: {success_count} successful before limit")

    async def test_rate_limit_002_authenticated_no_limit(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
        conversation_id: str,
    ):
        """
        GIVEN authenticated user endpoint
        WHEN sending multiple messages
        THEN should NOT be rate limited (or higher limit)
        """
        success_count = 0

        # Send 10 messages rapidly
        for i in range(10):
            response = await authenticated_client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                headers=auth_headers,
                json={
                    "content": f"Message {i}",
                    "language": "en",
                },
            )

            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                break

        # Authenticated users should handle more messages
        assert success_count >= 8, "Authenticated users rate limited too aggressively"

    async def test_rate_limit_003_concurrent_rate_limit_enforcement(
        self,
        client: AsyncClient,
    ):
        """
        GIVEN concurrent guest requests
        WHEN multiple requests from same IP
        THEN rate limit should apply globally
        """

        async def send_message(msg_num: int):
            response = await client.post(
                "/api/v1/guest/chat",
                json={
                    "content": f"Concurrent message {msg_num}",
                    "language": "en",
                },
            )
            return response.status_code

        # Send 25 concurrent requests
        tasks = [send_message(i) for i in range(25)]
        status_codes = await asyncio.gather(*tasks)

        # Count 200s and 429s
        success_count = status_codes.count(200)
        rate_limited_count = status_codes.count(429)

        # Should have some rate limiting
        assert rate_limited_count > 0 or success_count <= 20, (
            "No rate limiting on concurrent requests"
        )

        print(
            f"\n🚦 Concurrent Rate Limit: {success_count} success, {rate_limited_count} limited"
        )


@pytest.mark.asyncio
class TestDatabasePerformance:
    """Database query performance validation (3 tests)."""

    async def test_db_performance_001_conversation_creation_speed(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
    ):
        """
        GIVEN conversation creation endpoint
        WHEN creating 10 conversations
        THEN should be consistently fast
        """
        creation_times = []

        for i in range(10):
            start_time = time.time()
            response = await authenticated_client.post(
                "/api/v1/conversations",
                headers=auth_headers,
                json={"language": "en"},
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                creation_times.append(elapsed)

        avg_time = mean(creation_times)
        max_time = max(creation_times)

        # Database writes should be fast
        assert avg_time < 1.0, f"Average creation time {avg_time:.3f}s too slow"
        assert max_time < 2.0, f"Max creation time {max_time:.3f}s too slow"

        print(f"\n💾 Conversation Creation Performance:")
        print(f"  Avg: {avg_time * 1000:.0f}ms")
        print(f"  Max: {max_time * 1000:.0f}ms")

    async def test_db_performance_002_message_retrieval_speed(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
        conversation_id: str,
    ):
        """
        GIVEN conversation with messages
        WHEN retrieving conversation history
        THEN should be fast (< 500ms)
        """
        # First create some messages
        for i in range(5):
            await authenticated_client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                headers=auth_headers,
                json={"content": f"Message {i}", "language": "en"},
            )

        # Now measure retrieval speed
        retrieval_times = []
        for i in range(10):
            start_time = time.time()
            response = await authenticated_client.get(
                f"/api/v1/conversations/{conversation_id}",
                headers=auth_headers,
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                retrieval_times.append(elapsed)

        if retrieval_times:
            avg_time = mean(retrieval_times)
            assert avg_time < 0.5, f"Average retrieval {avg_time:.3f}s exceeds 500ms"

            print(f"\n💾 Message Retrieval Performance:")
            print(f"  Avg: {avg_time * 1000:.0f}ms")

    async def test_db_performance_003_no_n_plus_1_queries(
        self,
        authenticated_client: AsyncClient,
        auth_headers: dict,
    ):
        """
        GIVEN conversation list endpoint
        WHEN retrieving multiple conversations
        THEN should use efficient queries (no N+1 problem)
        """
        # Create 5 conversations
        conv_ids = []
        for i in range(5):
            response = await authenticated_client.post(
                "/api/v1/conversations",
                headers=auth_headers,
                json={"language": "en"},
            )
            if response.status_code == 200:
                conv_ids.append(response.json()["id"])

        # Measure list retrieval time
        start_time = time.time()
        response = await authenticated_client.get(
            "/api/v1/conversations",
            headers=auth_headers,
        )
        elapsed = time.time() - start_time

        assert response.status_code == 200

        # Should be fast even with multiple conversations
        assert elapsed < 1.0, f"List retrieval {elapsed:.3f}s indicates N+1 problem"

        print(f"\n💾 Conversation List Performance:")
        print(f"  {len(conv_ids)} conversations in {elapsed * 1000:.0f}ms")
