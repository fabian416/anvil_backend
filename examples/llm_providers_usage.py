"""
Example usage of OpenAI and Anthropic LLM provider adapters.

This script demonstrates:
1. Basic completion with OpenAI
2. Streaming with Anthropic
3. Failover between providers
4. Cost estimation
5. Health monitoring
"""

import asyncio
import os
from decimal import Decimal

from app.infrastructure.adapters.ai.openai_chat_adapter import OpenAIChatAdapter
from app.infrastructure.adapters.ai.anthropic_chat_adapter import AnthropicChatAdapter
from app.infrastructure.adapters.ai.llm_provider_failover import (
    create_openai_anthropic_failover,
)
from app.domain.value_objects.llm import LLMRequest, LLMMessage


async def example_openai_completion():
    """Example: Basic OpenAI completion."""
    print("\n=== OpenAI Completion Example ===")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set, skipping")
        return

    async with OpenAIChatAdapter(api_key=api_key) as adapter:
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system", content="You are a helpful Python coding assistant."
                ),
                LLMMessage(
                    role="user",
                    content="Explain list comprehensions in one sentence.",
                ),
            ],
            model_id="gpt-3.5-turbo",
            max_tokens=100,
            temperature=Decimal("0.7"),
        )

        response = await adapter.complete(request)

        print(f"Response: {response.content}")
        print(f"Model: {response.model_id}")
        print(f"Tokens: {response.input_tokens} in / {response.output_tokens} out")
        print(f"Cost: ${response.cost_usd}")
        print(f"Latency: {response.latency_ms}ms")


async def example_anthropic_streaming():
    """Example: Streaming with Anthropic."""
    print("\n=== Anthropic Streaming Example ===")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set, skipping")
        return

    async with AnthropicChatAdapter(api_key=api_key) as adapter:
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="user", content="Write a haiku about programming in Python."
                )
            ],
            model_id="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=Decimal("0.8"),
            stream=True,
        )

        print("Streaming response: ", end="", flush=True)
        async for chunk in adapter.complete_stream(request):
            print(chunk, end="", flush=True)
        print("\n")


async def example_failover():
    """Example: Failover between providers."""
    print("\n=== Failover Example ===")

    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not openai_key or not anthropic_key:
        print("Both API keys required, skipping")
        return

    # Create failover with OpenAI as primary
    failover = create_openai_anthropic_failover(
        openai_api_key=openai_key,
        anthropic_api_key=anthropic_key,
        primary="openai",
        enable_cost_fallback=True,
    )

    request = LLMRequest(
        messages=[
            LLMMessage(
                role="user",
                content="What are the benefits of async/await in Python?",
            )
        ],
        model_id="gpt-3.5-turbo",
        max_tokens=150,
        temperature=Decimal("0.7"),
    )

    # This will use OpenAI first, fall back to Anthropic if needed
    response = await failover.complete(request)

    print(f"Response: {response.content[:200]}...")
    print(f"Provider used: {response.provider}")
    print(f"Model: {response.model_id}")
    print(f"Cost: ${response.cost_usd}")

    # Check provider status
    print("\nProvider Status:")
    status = await failover.get_provider_status()
    for provider, info in status.items():
        print(f"  {provider}:")
        print(f"    Circuit: {info['circuit_state']}")
        print(f"    Health: {info['health']['status']}")
        print(f"    Priority: {info['priority']}")


async def example_cost_estimation():
    """Example: Cost estimation."""
    print("\n=== Cost Estimation Example ===")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("OPENAI_API_KEY not set, skipping")
        return

    async with OpenAIChatAdapter(api_key=openai_key) as adapter:
        # Estimate cost for different models
        models = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4-turbo"]

        print("Cost comparison for 1000 input / 500 output tokens:")
        for model in models:
            cost = await adapter.estimate_cost(
                input_tokens=1000, output_tokens=500, model=model
            )
            print(f"  {model}: ${cost}")


async def example_health_checks():
    """Example: Health monitoring."""
    print("\n=== Health Check Example ===")

    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if openai_key:
        async with OpenAIChatAdapter(api_key=openai_key) as adapter:
            health = await adapter.health_check()
            print(f"OpenAI Status: {health['status']}")
            print(f"  Latency: {health['latency_ms']}ms")
            if health["status"] == "healthy":
                print(f"  Models: {len(health['available_models'])} available")

    if anthropic_key:
        async with AnthropicChatAdapter(api_key=anthropic_key) as adapter:
            health = await adapter.health_check()
            print(f"\nAnthropic Status: {health['status']}")
            print(f"  Latency: {health['latency_ms']}ms")
            if health["status"] == "healthy":
                print(f"  Models: {len(health['available_models'])} available")


async def example_multi_turn_conversation():
    """Example: Multi-turn conversation."""
    print("\n=== Multi-turn Conversation Example ===")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("OPENAI_API_KEY not set, skipping")
        return

    async with OpenAIChatAdapter(api_key=openai_key) as adapter:
        # Simulate a conversation
        conversation = [
            LLMMessage(role="user", content="What is 15 + 27?"),
        ]

        # First turn
        request = LLMRequest(
            messages=conversation,
            model_id="gpt-3.5-turbo",
            max_tokens=50,
            temperature=Decimal("0.0"),
        )

        response = await adapter.complete(request)
        print(f"User: {conversation[0].content}")
        print(f"Assistant: {response.content}")

        # Add to conversation
        conversation.append(LLMMessage(role="assistant", content=response.content))
        conversation.append(
            LLMMessage(role="user", content="Now multiply that by 3.")
        )

        # Second turn
        request = LLMRequest(
            messages=conversation,
            model_id="gpt-3.5-turbo",
            max_tokens=50,
            temperature=Decimal("0.0"),
        )

        response = await adapter.complete(request)
        print(f"User: {conversation[2].content}")
        print(f"Assistant: {response.content}")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("LLM Provider Adapters Usage Examples")
    print("=" * 60)

    examples = [
        example_openai_completion,
        example_anthropic_streaming,
        example_failover,
        example_cost_estimation,
        example_health_checks,
        example_multi_turn_conversation,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
