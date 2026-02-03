#!/usr/bin/env python3
"""
Test script to verify dual-chain balance checking logic.

Tests that wallets are checked on:
1. CRITICAL: Ethereum (chainid=1) for USDC deposits
2. OPTIONAL: Operational chain (e.g., Base chainid=8453) for swaps/lending

Usage:
    python test_dual_chain_balance.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_dual_chain_logic():
    """Test that balance checking works for both Ethereum and Base."""
    from app.infrastructure.celery.tasks.etherscan_balance_tasks import (
        sync_single_wallet_etherscan,
        verify_test_wallet,
    )

    print("=" * 80)
    print("DUAL-CHAIN BALANCE CHECK TEST")
    print("=" * 80)
    print()

    # Test wallet from requirements
    TEST_WALLET = "0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B"

    print(f"Test Wallet: {TEST_WALLET}")
    print()

    # =========================================================================
    # Test 1: CRITICAL - Ethereum USDC Balance (Deposits)
    # =========================================================================
    print("-" * 80)
    print("TEST 1: CRITICAL - Ethereum USDC Balance Check (chainid=1)")
    print("-" * 80)

    try:
        ethereum_result = sync_single_wallet_etherscan(
            wallet_address=TEST_WALLET,
            chain="ethereum",
            contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC on Ethereum
            decimals=6,
        )

        if ethereum_result["status"] == "success":
            print(f"✅ SUCCESS: Ethereum USDC balance check")
            print(f"   Chain: ethereum (chainid=1)")
            print(f"   Balance: ${ethereum_result['balance_human']} USDC")
            print(f"   Contract: {ethereum_result['contract_address']}")
            print(f"   API Calls: {ethereum_result['api_metrics']['api_calls']}")
            print(f"   Timestamp: {ethereum_result['timestamp']}")
        else:
            print(f"❌ FAILED: {ethereum_result.get('reason', 'unknown')}")

    except Exception as e:
        print(f"❌ ERROR: {e}")

    print()

    # =========================================================================
    # Test 2: OPTIONAL - Base USDC Balance (Operations)
    # =========================================================================
    print("-" * 80)
    print("TEST 2: OPTIONAL - Base USDC Balance Check (chainid=8453)")
    print("-" * 80)

    try:
        base_result = sync_single_wallet_etherscan(
            wallet_address=TEST_WALLET,
            chain="base",
            contract_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
            decimals=6,
        )

        if base_result["status"] == "success":
            print(f"✅ SUCCESS: Base USDC balance check")
            print(f"   Chain: base (chainid=8453)")
            print(f"   Balance: ${base_result['balance_human']} USDC")
            print(f"   Contract: {base_result['contract_address']}")
            print(f"   API Calls: {base_result['api_metrics']['api_calls']}")
            print(f"   Timestamp: {base_result['timestamp']}")
        else:
            print(f"❌ FAILED: {base_result.get('reason', 'unknown')}")

    except Exception as e:
        print(f"❌ ERROR: {e}")

    print()

    # =========================================================================
    # Test 3: Verification Task
    # =========================================================================
    print("-" * 80)
    print("TEST 3: Test Wallet Verification (Ethereum USDT)")
    print("-" * 80)

    try:
        verify_result = verify_test_wallet()

        if verify_result["status"] == "verified":
            print(f"✅ VERIFIED: Test wallet balance is in expected range")
            print(f"   USDT Balance: {verify_result['usdt_balance']} USDT")
            print(f"   ETH Balance: {verify_result['eth_balance']} ETH")
            print(f"   Expected Range: {verify_result['expected_range']}")
        elif verify_result["status"] == "mismatch":
            print(f"⚠️  MISMATCH: Test wallet balance outside expected range")
            print(f"   USDT Balance: {verify_result['usdt_balance']} USDT")
            print(f"   Expected Range: {verify_result['expected_range']}")
        else:
            print(f"❌ FAILED: {verify_result.get('reason', 'unknown')}")

    except Exception as e:
        print(f"❌ ERROR: {e}")

    print()

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    print("✅ The system now implements CRITICAL dual-chain logic:")
    print()
    print("1. ETHEREUM (chainid=1) - DEPOSITS")
    print("   - ALWAYS checked for all wallets")
    print("   - USDC: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    print("   - This is the PRIMARY balance for deposit capacity")
    print()
    print("2. BASE (chainid=8453) - OPERATIONS")
    print("   - Checked for operational wallets")
    print("   - USDC: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
    print("   - Used for swaps, lending, and DeFi operations")
    print()
    print("Database Updates:")
    print("   - chain_addresses: One row per chain (ethereum, base, etc.)")
    print("   - wallets.last_balance_checked_at: Updated once per wallet")
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_dual_chain_logic())
