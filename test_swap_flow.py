#!/usr/bin/env python3
"""
Test script for multi-step swap flow.

Tests the complete conversational swap flow:
1. User: "swap" → Ask for FROM token
2. User: "BTC" → Ask for TO token
3. User: "ETH" → Ask for amount
4. User: "1" → Show quote, ask confirmation
5. User: "confirm" → Execute (requires auth)
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from app.application.guest.handlers.moonpay_swap_multistep import (
    MoonPaySwapMultiStepHandler,
)
from app.application.guest.handlers.moonpay_swap import MoonPaySwapHandler


async def test_flow():
    """Test the multi-step swap flow."""

    # Create handlers
    moonpay_handler = MoonPaySwapHandler()
    multistep_handler = MoonPaySwapMultiStepHandler(moonpay_handler)

    print("=" * 60)
    print("TESTING MULTI-STEP SWAP FLOW")
    print("=" * 60)

    # Step 1: User says "swap"
    print("\n1. User: 'swap'")
    result = await multistep_handler.handle_flow(
        content="swap",
        language="en",
        is_authenticated=False,
        continuation_step=None,
        previous_swap_info=None,
    )
    print(f"Bot: {result['content'][:100]}...")
    print(f"Pending action: {result.get('pending_action')}")
    print(f"Swap info: {result.get('swap_info')}")

    # Step 2: User says "BTC"
    print("\n2. User: 'BTC'")
    result = await multistep_handler.handle_flow(
        content="BTC",
        language="en",
        is_authenticated=False,
        continuation_step=result.get("pending_action"),
        previous_swap_info=result.get("swap_info"),
    )
    print(f"Bot: {result['content'][:100]}...")
    print(f"Pending action: {result.get('pending_action')}")
    print(f"Swap info: {result.get('swap_info')}")

    # Step 3: User says "ETH"
    print("\n3. User: 'ETH'")
    result = await multistep_handler.handle_flow(
        content="ETH",
        language="en",
        is_authenticated=False,
        continuation_step=result.get("pending_action"),
        previous_swap_info=result.get("swap_info"),
    )
    print(f"Bot: {result['content'][:100]}...")
    print(f"Pending action: {result.get('pending_action')}")
    print(f"Swap info: {result.get('swap_info')}")

    # Step 4: User says "1"
    print("\n4. User: '1'")
    result = await multistep_handler.handle_flow(
        content="1",
        language="en",
        is_authenticated=False,
        continuation_step=result.get("pending_action"),
        previous_swap_info=result.get("swap_info"),
    )
    print(f"Bot: {result['content'][:150]}...")
    print(f"Pending action: {result.get('pending_action')}")
    print(f"Swap info: {result.get('swap_info')}")

    # Step 5: User says "confirm"
    print("\n5. User: 'confirm'")
    result = await multistep_handler.handle_flow(
        content="confirm",
        language="en",
        is_authenticated=False,
        continuation_step=result.get("pending_action"),
        previous_swap_info=result.get("swap_info"),
    )
    print(f"Bot: {result['content']}")
    print(f"Requires registration: {result.get('requires_registration')}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_flow())
