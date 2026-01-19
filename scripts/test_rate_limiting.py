#!/usr/bin/env python3
"""
Test script for rate limiting implementation.

Tests:
1. Guest user rate limiting (IP-based, 800/hour)
2. Authenticated user rate limiting (user ID-based, 1000/hour)
3. Rate limit headers
4. 429 responses when limits exceeded
"""
import asyncio
import httpx
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8080"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJ0ZXN0X3Nlc3Npb25fMjAyNl8xNzY4MDY2MDc5IiwiZXhwIjoxNzk5NjAyMDc5fQ.OUFFmZW2_QACkgrIphLFcOOB3Qb-1ckVB_RvZ-VTaF0"


async def test_guest_rate_limit():
    """Test guest user rate limiting (IP-based)."""
    print("\n" + "=" * 70)
    print("TEST 1: Guest User Rate Limiting (IP-based)")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        # Make 5 requests as guest
        for i in range(1, 6):
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={
                        "content": f"Test message {i}",
                        "language": "en"
                    },
                    timeout=30.0
                )

                print(f"\nRequest {i}:")
                print(f"  Status: {response.status_code}")

                # Check rate limit headers
                if "X-RateLimit-Limit" in response.headers:
                    print(f"  Rate Limit: {response.headers['X-RateLimit-Limit']}")
                    print(f"  Remaining: {response.headers['X-RateLimit-Remaining']}")
                    print(f"  Reset: {response.headers.get('X-RateLimit-Reset', 'N/A')}")

                if response.status_code == 200:
                    print(f"  ✅ Success")
                elif response.status_code == 429:
                    print(f"  ⚠️  Rate limit exceeded!")
                    print(f"  Message: {response.json()['detail']}")

            except Exception as e:
                print(f"  ❌ Error: {e}")


async def test_authenticated_rate_limit():
    """Test authenticated user rate limiting (user ID-based)."""
    print("\n" + "=" * 70)
    print("TEST 2: Authenticated User Rate Limiting (User ID-based)")
    print("=" * 70)

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    async with httpx.AsyncClient() as client:
        # Make 5 requests as authenticated user
        for i in range(1, 6):
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={
                        "content": f"Authenticated test message {i}",
                        "language": "en"
                    },
                    headers=headers,
                    timeout=30.0
                )

                print(f"\nRequest {i}:")
                print(f"  Status: {response.status_code}")

                # Check rate limit headers
                if "X-RateLimit-Limit" in response.headers:
                    print(f"  Rate Limit: {response.headers['X-RateLimit-Limit']}")
                    print(f"  Remaining: {response.headers['X-RateLimit-Remaining']}")
                    print(f"  Reset: {response.headers.get('X-RateLimit-Reset', 'N/A')}")

                if response.status_code == 200:
                    print(f"  ✅ Success")
                elif response.status_code == 429:
                    print(f"  ⚠️  Rate limit exceeded!")
                    print(f"  Message: {response.json()['detail']}")

            except Exception as e:
                print(f"  ❌ Error: {e}")


async def test_rate_limit_exceeded():
    """Test rate limit exceeded scenario."""
    print("\n" + "=" * 70)
    print("TEST 3: Rate Limit Exceeded (Rapid Fire)")
    print("=" * 70)

    print("\nMaking 10 rapid requests to test rate limiting...")

    async with httpx.AsyncClient() as client:
        success_count = 0
        rate_limited_count = 0

        for i in range(1, 11):
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/chat",
                    json={
                        "content": f"Rapid test {i}",
                        "language": "en"
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    success_count += 1
                    remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
                    print(f"  Request {i}: ✅ Success (Remaining: {remaining})")
                elif response.status_code == 429:
                    rate_limited_count += 1
                    print(f"  Request {i}: ⚠️  Rate limited")

            except Exception as e:
                print(f"  Request {i}: ❌ Error: {e}")

        print(f"\nResults:")
        print(f"  Successful: {success_count}")
        print(f"  Rate Limited: {rate_limited_count}")


async def main():
    """Run all rate limiting tests."""
    print("\n" + "=" * 70)
    print("RATE LIMITING TEST SUITE")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Test 1: Guest rate limiting
        await test_guest_rate_limit()

        # Wait a bit between tests
        await asyncio.sleep(2)

        # Test 2: Authenticated rate limiting
        await test_authenticated_rate_limit()

        # Wait a bit between tests
        await asyncio.sleep(2)

        # Test 3: Rate limit exceeded
        await test_rate_limit_exceeded()

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
