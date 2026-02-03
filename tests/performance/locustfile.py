"""
Load testing with Locust.

Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import json
from uuid import uuid4


class ChatUser(HttpUser):
    """
    Simulates a user interacting with the DeFi chat platform.

    Usage:
        # Run with 100 users, spawn rate 10/sec
        locust -f tests/performance/locustfile.py --users 100 --spawn-rate 10

        # Run headless with results
        locust -f tests/performance/locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m
    """

    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    def on_start(self):
        """Called when a user starts."""
        # Simulate login/signup (if needed)
        self.user_id = str(uuid4())
        self.conversation_id = None
        self.token = "test_token_" + self.user_id[:8]

    @task(5)
    def create_conversation(self):
        """Create a new conversation (high frequency)."""
        response = self.client.post(
            "/api/v1/chat/conversations",
            json={},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        if response.status_code == 201:
            data = response.json()
            self.conversation_id = data.get("id")

    @task(20)
    def send_swap_message(self):
        """Send swap-related message (highest frequency)."""
        if not self.conversation_id:
            self.create_conversation()

        messages = [
            "What's the price of BTC?",
            "Swap 100 USDC to ETH",
            "How much ETH can I get for 1000 USDC?",
            "Show me swap quote for 50 USDC to DAI",
            "What's the gas cost for swapping?",
        ]

        import random

        message = random.choice(messages)

        self.client.post(
            f"/api/v1/chat/conversations/{self.conversation_id}/messages",
            json={"content": message},
            headers={"Authorization": f"Bearer {self.token}"},
        )

    @task(10)
    def send_trading_message(self):
        """Send trading-related message (medium frequency)."""
        if not self.conversation_id:
            self.create_conversation()

        messages = [
            "Open 10x long BTC",
            "What's the liquidation price for 5x ETH long?",
            "Show me BTC funding rate",
            "Calculate PnL for my position",
            "Close my BTC position",
        ]

        import random

        message = random.choice(messages)

        self.client.post(
            f"/api/v1/chat/conversations/{self.conversation_id}/messages",
            json={"content": message},
            headers={"Authorization": f"Bearer {self.token}"},
        )

    @task(8)
    def send_portfolio_message(self):
        """Send portfolio-related message (medium frequency)."""
        if not self.conversation_id:
            self.create_conversation()

        messages = [
            "Show my portfolio for 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "What's the top DeFi protocol by TVL?",
            "Show me yield opportunities on Aave",
            "Get price of ETH",
            "Show market overview",
        ]

        import random

        message = random.choice(messages)

        self.client.post(
            f"/api/v1/chat/conversations/{self.conversation_id}/messages",
            json={"content": message},
            headers={"Authorization": f"Bearer {self.token}"},
        )

    @task(3)
    def get_conversations(self):
        """Get user conversations (low frequency)."""
        self.client.get(
            "/api/v1/chat/conversations",
            headers={"Authorization": f"Bearer {self.token}"},
        )

    @task(2)
    def get_conversation_messages(self):
        """Get conversation messages (low frequency)."""
        if not self.conversation_id:
            return

        self.client.get(
            f"/api/v1/chat/conversations/{self.conversation_id}",
            headers={"Authorization": f"Bearer {self.token}"},
        )


class WebSocketChatUser(HttpUser):
    """
    Simulates WebSocket connections.

    Note: Locust doesn't natively support WebSocket well.
    Use separate WebSocket load testing tool like Artillery or custom script.
    """

    wait_time = between(2, 8)

    @task
    def connect_websocket(self):
        """Simulate WebSocket connection check."""
        # This is a placeholder - use dedicated WebSocket testing
        response = self.client.get(
            "/api/v1/chat/ws/health",
            headers={"Authorization": f"Bearer test_token"},
        )


class CachingPerformanceUser(HttpUser):
    """
    Tests caching performance.

    Measures cache hit rates and response times.
    """

    wait_time = between(0.1, 0.5)  # Fast requests to test cache

    @task
    def get_cached_price(self):
        """Repeatedly request same price (should hit cache)."""
        self.client.get("/api/v1/prices/BTC")

    @task
    def get_cached_quote(self):
        """Repeatedly request same quote (should hit cache)."""
        self.client.get("/api/v1/quotes/USDC-ETH/100")

    @task
    def get_cached_protocol(self):
        """Repeatedly request protocol info (should hit cache)."""
        self.client.get("/api/v1/defi/protocols/aave")
