"""
Anvil Unified Chat API - Python SDK Examples

Complete examples showing how to interact with all 16 unified chat intent types
using Python and the requests library.

Installation:
    pip install requests

Usage:
    python python_sdk_examples.py
"""

import requests
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class ChatConfig:
    """Configuration for Chat API client."""
    base_url: str = "http://localhost:8080/api/v1"
    email: str = "user@example.com"
    password: str = "password"


class AnvilChatClient:
    """Client for Anvil Unified Chat API."""

    def __init__(self, config: ChatConfig):
        self.config = config
        self.token: Optional[str] = None
        self.conversation_id: Optional[str] = None
        self.session = requests.Session()

    def login(self) -> Dict:
        """Authenticate and get access token."""
        response = self.session.post(
            f"{self.config.base_url}/account/login",
            json={
                "email": self.config.email,
                "password": self.config.password
            }
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return data

    def create_conversation(self, title: str = "Python SDK Conversation") -> Dict:
        """Create a new conversation."""
        response = self.session.post(
            f"{self.config.base_url}/user/chat/conversations",
            json={"title": title}
        )
        response.raise_for_status()
        data = response.json()
        self.conversation_id = data["id"]
        return data

    def send_message(self, content: str, conversation_id: Optional[str] = None) -> Dict:
        """Send a message to the unified chat endpoint."""
        conv_id = conversation_id or self.conversation_id
        if not conv_id:
            raise ValueError("No conversation_id set. Call create_conversation() first.")

        response = self.session.post(
            f"{self.config.base_url}/user/chat/conversations/{conv_id}/messages",
            json={"content": content}
        )
        response.raise_for_status()
        return response.json()

    def get_messages(self, conversation_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get conversation message history."""
        conv_id = conversation_id or self.conversation_id
        response = self.session.get(
            f"{self.config.base_url}/user/chat/conversations/{conv_id}/messages",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()


# ============================================================================
# Example Usage for All 16 Intent Types
# ============================================================================

def example_graphrag_intents(client: AnvilChatClient):
    """Examples for GraphRAG intent types (3)."""

    print("\n" + "="*80)
    print("GRAPHRAG INTENTS")
    print("="*80)

    # 1. Protocol Search
    print("\n1. Protocol Search")
    print("-" * 40)
    response = client.send_message(
        "Show me high-yield staking protocols on Ethereum with low risk"
    )
    print(f"Intent: {response['routing']['intent']}")
    print(f"Confidence: {response['routing']['confidence']}")
    print(f"Handler: {response['routing']['handler']}")
    print(f"Response: {response['agent_message']['content'][:200]}...")

    # 2. Risk Assessment
    print("\n2. Risk Assessment")
    print("-" * 40)
    response = client.send_message("Is Aave safe to use? What are the risks?")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Risk Score: {response['enrichment'].get('risk_analysis', {}).get('overall_risk_score', 'N/A')}")

    # 3. Similar Protocols
    print("\n3. Similar Protocols")
    print("-" * 40)
    response = client.send_message("What protocols are similar to Uniswap?")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Similar Protocols Found: {len(response['enrichment'].get('similar_protocols', []))}")


def example_hunter_ai_intents(client: AnvilChatClient):
    """Examples for Hunter AI intent types (6)."""

    print("\n" + "="*80)
    print("HUNTER AI INTENTS")
    print("="*80)

    # 1. Sentiment Analysis
    print("\n1. Sentiment Analysis")
    print("-" * 40)
    response = client.send_message("What's the ETH sentiment on Twitter and Reddit?")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Token: {response['enrichment'].get('token_symbol')}")
    print(f"Sources: {response['enrichment'].get('sources')}")
    print(f"Tool: {response['enrichment'].get('hunter_tool')}")

    # 2. Price Prediction
    print("\n2. Price Prediction")
    print("-" * 40)
    response = client.send_message("Predict BTC price for next 7 days")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Token: {response['enrichment'].get('token_symbol')}")
    print(f"Time Horizon: {response['enrichment'].get('time_horizon')}")

    # 3. Risk Signals
    print("\n3. Risk Signals")
    print("-" * 40)
    response = client.send_message("Show risk signals for ETH")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Tool: {response['enrichment'].get('hunter_tool')}")

    # 4. Trading Signals
    print("\n4. Trading Signals")
    print("-" * 40)
    response = client.send_message("Should I buy SOL now? Give me trading signals")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Token: {response['enrichment'].get('token_symbol')}")

    # 5. Pattern Detection
    print("\n5. Pattern Detection")
    print("-" * 40)
    response = client.send_message("What chart patterns do you see for BTC?")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Token: {response['enrichment'].get('token_symbol')}")

    # 6. Portfolio Optimization
    print("\n6. Portfolio Optimization")
    print("-" * 40)
    response = client.send_message(
        "Optimize my portfolio with BTC, ETH, and SOL for moderate risk"
    )
    print(f"Intent: {response['routing']['intent']}")
    print(f"Tokens: {response['enrichment'].get('tokens')}")
    print(f"Risk Tolerance: {response['enrichment'].get('risk_tolerance')}")


def example_ultra_intents(client: AnvilChatClient):
    """Examples for ULTRA intent types (4)."""

    print("\n" + "="*80)
    print("ULTRA INTENTS")
    print("="*80)

    # 1. Arbitrage Discovery
    print("\n1. Arbitrage Discovery")
    print("-" * 40)
    response = client.send_message("Find arbitrage opportunities with $10,000 capital")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Capital: ${response['enrichment'].get('capital'):,.2f}")
    print(f"Arb Type: {response['enrichment'].get('arb_type')}")
    print(f"Tool: {response['enrichment'].get('ultra_tool')}")

    # 2. Flash Loan Selection
    print("\n2. Flash Loan Selection")
    print("-" * 40)
    response = client.send_message("Best flash loan protocol for 100k USDC")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Token: {response['enrichment'].get('token_symbol')}")
    print(f"Amount: ${response['enrichment'].get('amount'):,.2f}")
    print(f"Protocol: {response['enrichment'].get('protocol') or 'Auto-selected'}")

    # 3. MEV Protection
    print("\n3. MEV Protection")
    print("-" * 40)
    response = client.send_message("Execute ARB-001 with Flashbots protection")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Opportunity ID: {response['enrichment'].get('opportunity_id')}")
    print(f"Tool: {response['enrichment'].get('ultra_tool')}")

    # 4. Auto Executor Control
    print("\n4. Auto Executor Control")
    print("-" * 40)

    # Start bot
    response = client.send_message("Start trading bot")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Action: {response['enrichment'].get('action')}")

    # Check status
    response = client.send_message("Show bot status")
    print(f"Action: {response['enrichment'].get('action')}")

    # Stop bot
    response = client.send_message("Stop trading bot")
    print(f"Action: {response['enrichment'].get('action')}")


def example_agent_squad_intents(client: AnvilChatClient):
    """Examples for Agent Squad and Chat intent types (3)."""

    print("\n" + "="*80)
    print("AGENT SQUAD & CHAT INTENTS")
    print("="*80)

    # 1. Specialist Task
    print("\n1. Specialist Task")
    print("-" * 40)
    response = client.send_message(
        "Analyze ETH/USDC liquidity depth on Uniswap V3"
    )
    print(f"Intent: {response['routing']['intent']}")
    print(f"Handler: {response['routing']['handler']}")
    print(f"Tools Used: {response['enrichment'].get('tools_used', [])}")

    # 2. Complex Workflow
    print("\n2. Complex Workflow")
    print("-" * 40)
    response = client.send_message(
        "Create a complete DeFi investment strategy for $50k with risk analysis"
    )
    print(f"Intent: {response['routing']['intent']}")
    print(f"Handler: {response['routing']['handler']}")
    print(f"Workflow ID: {response['enrichment'].get('workflow_id')}")
    print(f"Agents Involved: {response['enrichment'].get('agents_involved', [])}")

    # 3. General Conversation
    print("\n3. General Conversation")
    print("-" * 40)
    response = client.send_message("Hello! What can you help me with?")
    print(f"Intent: {response['routing']['intent']}")
    print(f"Handler: {response['routing']['handler']}")


def example_advanced_usage(client: AnvilChatClient):
    """Advanced usage patterns."""

    print("\n" + "="*80)
    print("ADVANCED USAGE PATTERNS")
    print("="*80)

    # Multi-turn conversation
    print("\n1. Multi-turn Conversation")
    print("-" * 40)

    # First message
    response1 = client.send_message("Find safe lending protocols")
    print(f"User: Find safe lending protocols")
    print(f"Intent: {response1['routing']['intent']}")

    # Follow-up question
    response2 = client.send_message("What about the risks of the first one?")
    print(f"User: What about the risks of the first one?")
    print(f"Intent: {response2['routing']['intent']}")

    # Batch multiple queries
    print("\n2. Batch Processing")
    print("-" * 40)

    queries = [
        "ETH sentiment",
        "BTC price prediction",
        "SOL trading signals",
    ]

    for query in queries:
        response = client.send_message(query)
        print(f"Query: {query}")
        print(f"  Intent: {response['routing']['intent']}")
        print(f"  Latency: {response['routing']['total_latency_ms']}ms")

    # Message history
    print("\n3. Retrieve Message History")
    print("-" * 40)

    messages = client.get_messages(limit=10)
    print(f"Total messages in conversation: {len(messages)}")
    for msg in messages[:3]:
        print(f"  - {msg['role']}: {msg['content'][:50]}...")


def example_error_handling(client: AnvilChatClient):
    """Error handling examples."""

    print("\n" + "="*80)
    print("ERROR HANDLING")
    print("="*80)

    # Invalid conversation ID
    print("\n1. Invalid Conversation ID")
    print("-" * 40)
    try:
        client.send_message("Test message", conversation_id="invalid-id")
    except requests.HTTPError as e:
        print(f"Error: {e.response.status_code} - {e.response.json()}")

    # Empty message
    print("\n2. Empty Message")
    print("-" * 40)
    try:
        client.send_message("")
    except requests.HTTPError as e:
        print(f"Error: {e.response.status_code} - {e.response.json()}")

    # Rate limiting (if applicable)
    print("\n3. Rate Limiting Handling")
    print("-" * 40)
    for i in range(5):
        try:
            response = client.send_message(f"Test message {i}")
            print(f"Message {i}: Success")
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                print(f"Rate limited. Retry-After: {e.response.headers.get('Retry-After')}")
                break


# ============================================================================
# Utility Functions
# ============================================================================

def print_response_summary(response: Dict):
    """Print a formatted summary of the response."""
    print("\nResponse Summary:")
    print("-" * 80)
    print(f"Intent:     {response['routing']['intent']}")
    print(f"Confidence: {response['routing']['confidence']:.2f}")
    print(f"Handler:    {response['routing']['handler']}")
    print(f"Latency:    {response['routing']['total_latency_ms']}ms")

    if response.get('enrichment'):
        print(f"\nEnrichment Data:")
        for key, value in response['enrichment'].items():
            print(f"  {key}: {value}")

    print(f"\nAgent Response:")
    print("-" * 80)
    print(response['agent_message']['content'][:500])
    if len(response['agent_message']['content']) > 500:
        print("...")
    print("-" * 80)


def save_conversation_history(client: AnvilChatClient, filename: str = "conversation_history.json"):
    """Save conversation history to JSON file."""
    import json

    messages = client.get_messages()
    with open(filename, 'w') as f:
        json.dump(messages, f, indent=2)
    print(f"Saved {len(messages)} messages to {filename}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run all examples."""

    # Initialize client
    config = ChatConfig(
        base_url="http://localhost:8080/api/v1",
        email="user@example.com",
        password="password"
    )

    client = AnvilChatClient(config)

    # Authenticate
    print("Authenticating...")
    client.login()
    print(f"✓ Logged in successfully")

    # Create conversation
    print("\nCreating conversation...")
    client.create_conversation(title="Python SDK Examples")
    print(f"✓ Conversation created: {client.conversation_id}")

    # Run all examples
    try:
        example_graphrag_intents(client)
        example_hunter_ai_intents(client)
        example_ultra_intents(client)
        example_agent_squad_intents(client)
        example_advanced_usage(client)
        example_error_handling(client)

        # Save conversation history
        save_conversation_history(client)

    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETED")
    print("="*80)


if __name__ == "__main__":
    main()


# ============================================================================
# Quick Start Examples
# ============================================================================

def quick_start_protocol_search():
    """Quick start: Find protocols."""
    config = ChatConfig()
    client = AnvilChatClient(config)
    client.login()
    client.create_conversation()

    response = client.send_message("Show me DeFi lending protocols")
    print_response_summary(response)


def quick_start_sentiment_analysis():
    """Quick start: Get sentiment."""
    config = ChatConfig()
    client = AnvilChatClient(config)
    client.login()
    client.create_conversation()

    response = client.send_message("What's BTC sentiment?")
    print_response_summary(response)


def quick_start_arbitrage():
    """Quick start: Find arbitrage."""
    config = ChatConfig()
    client = AnvilChatClient(config)
    client.login()
    client.create_conversation()

    response = client.send_message("Find arbitrage with $5000")
    print_response_summary(response)


# Uncomment to run quick start examples:
# quick_start_protocol_search()
# quick_start_sentiment_analysis()
# quick_start_arbitrage()
