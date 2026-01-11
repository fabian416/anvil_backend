#!/usr/bin/env python3
"""
Simple test for multi-step swap flow logic.

Tests the state machine transitions without external dependencies.
"""

import re


class SimpleMoonPayTester:
    """Simple tester for MoonPay multi-step flow logic."""

    MOONPAY_TOKENS = {
        "btc": "btc",
        "bitcoin": "btc",
        "eth": "eth",
        "ethereum": "eth",
        "ether": "eth",
        "sol": "sol",
        "solana": "sol",
        "usdc": "usdc",
    }

    def _extract_token(self, content: str) -> str | None:
        """Extract token from content."""
        content_lower = content.lower().strip()
        for alias, symbol in self.MOONPAY_TOKENS.items():
            if alias in content_lower:
                return symbol
        return None

    def _extract_amount(self, content: str) -> str | None:
        """Extract amount from content."""
        match = re.search(r'(\d+\.?\d*)', content)
        return match.group(1) if match else None

    def handle_flow(
        self,
        content: str,
        continuation_step: str | None = None,
        previous_swap_info: dict | None = None,
    ) -> dict:
        """Handle multi-step flow."""
        content_lower = content.lower().strip()
        swap_info = previous_swap_info or {}

        # Handle continuation steps
        if continuation_step == "swap_awaiting_from_token":
            from_token = self._extract_token(content)
            if from_token:
                swap_info["from_token"] = from_token
                return {
                    "pending_action": "swap_awaiting_to_token",
                    "swap_info": swap_info,
                    "message": f"FROM token set to {from_token.upper()}",
                }
            return {"error": "Invalid FROM token"}

        elif continuation_step == "swap_awaiting_to_token":
            to_token = self._extract_token(content)
            if to_token:
                swap_info["to_token"] = to_token
                return {
                    "pending_action": "swap_awaiting_amount",
                    "swap_info": swap_info,
                    "message": f"TO token set to {to_token.upper()}",
                }
            return {"error": "Invalid TO token"}

        elif continuation_step == "swap_awaiting_amount":
            amount = self._extract_amount(content)
            if amount:
                swap_info["amount"] = amount
                return {
                    "pending_action": "swap_awaiting_confirmation",
                    "swap_info": swap_info,
                    "message": f"Amount set to {amount}. Quote would be shown here.",
                }
            return {"error": "Invalid amount"}

        elif continuation_step == "swap_awaiting_confirmation":
            if any(kw in content_lower for kw in ["confirm", "yes", "ok"]):
                return {
                    "pending_action": None,
                    "swap_info": swap_info,
                    "message": "Swap confirmed! Registration required.",
                    "requires_registration": True,
                }
            return {"error": "Confirmation not detected"}

        # Initial "swap" command
        if "swap" in content_lower:
            return {
                "pending_action": "swap_awaiting_from_token",
                "swap_info": {},
                "message": "Which token do you want to swap FROM?",
            }

        return {"error": "Unknown command"}


def test_flow():
    """Test the multi-step swap flow."""
    tester = SimpleMoonPayTester()

    print("=" * 60)
    print("TESTING MULTI-STEP SWAP FLOW STATE MACHINE")
    print("=" * 60)

    # Step 1: User says "swap"
    print("\n1. User: 'swap'")
    result = tester.handle_flow(content="swap")
    print(f"   Bot: {result.get('message')}")
    print(f"   Next state: {result.get('pending_action')}")
    print(f"   Swap info: {result.get('swap_info')}")

    # Step 2: User says "BTC"
    print("\n2. User: 'BTC'")
    result = tester.handle_flow(
        content="BTC",
        continuation_step=result.get('pending_action'),
        previous_swap_info=result.get('swap_info'),
    )
    print(f"   Bot: {result.get('message')}")
    print(f"   Next state: {result.get('pending_action')}")
    print(f"   Swap info: {result.get('swap_info')}")

    # Step 3: User says "ETH"
    print("\n3. User: 'ETH'")
    result = tester.handle_flow(
        content="ETH",
        continuation_step=result.get('pending_action'),
        previous_swap_info=result.get('swap_info'),
    )
    print(f"   Bot: {result.get('message')}")
    print(f"   Next state: {result.get('pending_action')}")
    print(f"   Swap info: {result.get('swap_info')}")

    # Step 4: User says "1"
    print("\n4. User: '1'")
    result = tester.handle_flow(
        content="1",
        continuation_step=result.get('pending_action'),
        previous_swap_info=result.get('swap_info'),
    )
    print(f"   Bot: {result.get('message')}")
    print(f"   Next state: {result.get('pending_action')}")
    print(f"   Swap info: {result.get('swap_info')}")

    # Step 5: User says "confirm"
    print("\n5. User: 'confirm'")
    result = tester.handle_flow(
        content="confirm",
        continuation_step=result.get('pending_action'),
        previous_swap_info=result.get('swap_info'),
    )
    print(f"   Bot: {result.get('message')}")
    print(f"   Requires registration: {result.get('requires_registration')}")
    print(f"   Final swap info: {result.get('swap_info')}")

    print("\n" + "=" * 60)
    print("✅ STATE MACHINE TEST COMPLETE!")
    print("=" * 60)

    print("\n" + "=" * 60)
    print("KEY IMPLEMENTATION POINTS:")
    print("=" * 60)
    print("✓ State persistence via pending_action and swap_info")
    print("✓ Continuation from previous state using metadata")
    print("✓ Step-by-step parameter collection (from → to → amount)")
    print("✓ Confirmation before execution")
    print("✓ Registration requirement for execution")


if __name__ == "__main__":
    test_flow()
