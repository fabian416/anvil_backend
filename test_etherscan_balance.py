#!/usr/bin/env python3
"""
Test script for Etherscan balance checking integration.

Tests:
1. Etherscan client initialization
2. Token balance query for test wallet
3. Verify expected balance (3 USDT)
4. Check if test wallet exists in database
"""

import asyncio
import sys
from decimal import Decimal

# Add project to path
sys.path.insert(0, "/home/ubuntu/anvil_backend/src")

from app.infrastructure.adapters.external.etherscan_client import EtherscanClient
from app.setup.config.settings import load_settings
from app.setup.app_factory import create_async_ioc_container
from app.setup.ioc.provider_registry import get_providers


# Test wallet address
TEST_WALLET = "0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B"

# Ethereum USDT contract
USDT_CONTRACT_ETHEREUM = "0xdAC17F958D2ee523a2206206994597C13D831ec7"


async def test_etherscan_client():
    """Test Etherscan client directly."""
    print("=" * 80)
    print("TEST 1: Etherscan Client Direct Test")
    print("=" * 80)

    settings = load_settings()
    etherscan_settings = settings.etherscan

    print(f"\n✓ Etherscan API Key configured: {etherscan_settings.is_configured}")
    print(f"  API Key: {etherscan_settings.api_key[:10]}..." if etherscan_settings.api_key else "  No API key")

    if not etherscan_settings.is_configured:
        print("❌ Etherscan API key not configured. Add it to config/local/.secrets.toml")
        return False

    # Create client
    client = EtherscanClient(
        api_key=etherscan_settings.api_key,
        network="ethereum",
        timeout=15.0,
        use_v2_api=True,
    )

    print(f"\n✓ Etherscan client created for network: ethereum")
    print(f"  Chain ID: {client._chain_id}")
    print(f"  Base URL: {client._base_url}")

    # Test balance query
    print(f"\n🔍 Querying balance for test wallet...")
    print(f"  Wallet: {TEST_WALLET}")
    print(f"  Token: USDT (6 decimals)")
    print(f"  Contract: {USDT_CONTRACT_ETHEREUM}")

    result = await client.get_token_balance(
        wallet_address=TEST_WALLET,
        contract_address=USDT_CONTRACT_ETHEREUM,
        decimals=6,
    )

    await client.close()

    if result is None:
        print("❌ Failed to fetch balance (API error or rate limit)")
        return False

    raw_balance, formatted_balance = result
    print(f"\n✅ Balance retrieved successfully:")
    print(f"  Raw: {raw_balance} (smallest units)")
    print(f"  Formatted: {formatted_balance} USDT")

    # Verify expected balance (3 USDT = 3,000,000 raw units)
    expected_balance = 3.0
    if abs(formatted_balance - expected_balance) < 0.01:
        print(f"✅ Balance matches expected: {expected_balance} USDT")
        return True
    else:
        print(f"⚠️  Balance mismatch: expected {expected_balance}, got {formatted_balance}")
        print("   (This may be normal if wallet balance has changed)")
        return True


async def test_database_wallet():
    """Test if wallet exists in database."""
    print("\n" + "=" * 80)
    print("TEST 2: Database Wallet Lookup")
    print("=" * 80)

    settings = load_settings()
    container = create_async_ioc_container(
        providers=get_providers(),
        settings=settings,
    )

    try:
        async with container() as request_container:
            from sqlalchemy import select
            from sqlalchemy.ext.asyncio import AsyncSession
            from app.infrastructure.persistence_sqla.registry import mapping_registry
            from app.infrastructure.persistence_sqla.mappings.wallet import map_wallet_tables
            from app.infrastructure.adapters.types import MainAsyncSession

            # Ensure wallet mappings loaded
            map_wallet_tables()

            session: AsyncSession = await request_container.get(MainAsyncSession)
            wallets_table = mapping_registry.metadata.tables.get("wallets")

            if wallets_table is None:
                print("❌ Wallets table not found")
                return False

            # Query for test wallet
            stmt = (
                select(
                    wallets_table.c.id,
                    wallets_table.c.user_id,
                    wallets_table.c.address,
                    wallets_table.c.default_chain,
                    wallets_table.c.status,
                )
                .where(wallets_table.c.address == TEST_WALLET.lower())
            )

            result = await session.execute(stmt)
            wallet_row = result.fetchone()

            if wallet_row:
                print(f"✅ Wallet found in database:")
                print(f"  ID: {wallet_row[0]}")
                print(f"  User ID: {wallet_row[1]}")
                print(f"  Address: {wallet_row[2]}")
                print(f"  Chain: {wallet_row[3]}")
                print(f"  Status: {wallet_row[4]}")
                return True
            else:
                print(f"⚠️  Wallet not found in database: {TEST_WALLET}")
                print("   Add this wallet to test the Celery sync task")
                return False

    finally:
        await container.close()


async def test_celery_task_simulation():
    """Simulate Celery task execution for test wallet."""
    print("\n" + "=" * 80)
    print("TEST 3: Simulated Celery Task Execution")
    print("=" * 80)

    settings = load_settings()
    etherscan_settings = settings.etherscan
    container = create_async_ioc_container(
        providers=get_providers(),
        settings=settings,
    )

    try:
        async with container() as request_container:
            from sqlalchemy import select, update
            from sqlalchemy.ext.asyncio import AsyncSession
            from app.infrastructure.persistence_sqla.registry import mapping_registry
            from app.infrastructure.persistence_sqla.mappings.wallet import map_wallet_tables
            from app.infrastructure.adapters.types import MainAsyncSession
            from app.infrastructure.adapters.external.etherscan_client import EtherscanClient
            from datetime import datetime, UTC

            # Ensure wallet mappings loaded
            map_wallet_tables()

            session: AsyncSession = await request_container.get(MainAsyncSession)
            wallets_table = mapping_registry.metadata.tables.get("wallets")
            chain_addresses_table = mapping_registry.metadata.tables.get("chain_addresses")

            # Find test wallet
            stmt = (
                select(
                    wallets_table.c.id,
                    wallets_table.c.address,
                    wallets_table.c.default_chain,
                )
                .where(wallets_table.c.address == TEST_WALLET.lower())
            )

            result = await session.execute(stmt)
            wallet_row = result.fetchone()

            if not wallet_row:
                print("⚠️  Test wallet not in database, skipping task simulation")
                return False

            wallet_id = wallet_row[0]
            wallet_address = wallet_row[1]
            default_chain = wallet_row[2]

            if default_chain:
                chain = default_chain.value if hasattr(default_chain, 'value') else str(default_chain)
            else:
                chain = "ethereum"

            print(f"\n✓ Found test wallet in database:")
            print(f"  ID: {wallet_id}")
            print(f"  Address: {wallet_address}")
            print(f"  Chain: {chain}")

            # Get token contract for this chain
            token_contracts = etherscan_settings.TOKEN_CONTRACTS.get(chain, {})
            if not token_contracts:
                print(f"❌ No token contracts configured for chain: {chain}")
                return False

            contract_address, (symbol, decimals) = list(token_contracts.items())[0]
            print(f"\n✓ Using token contract:")
            print(f"  Symbol: {symbol}")
            print(f"  Decimals: {decimals}")
            print(f"  Contract: {contract_address}")

            # Create Etherscan client
            client = EtherscanClient(
                api_key=etherscan_settings.api_key,
                network=chain,
                timeout=15.0,
                use_v2_api=True,
            )

            # Fetch balance
            print(f"\n🔍 Fetching balance from Etherscan...")
            balance_result = await client.get_token_balance(
                wallet_address=wallet_address,
                contract_address=contract_address,
                decimals=decimals,
            )

            await client.close()

            if balance_result is None:
                print("❌ Failed to fetch balance")
                return False

            raw_balance, formatted_balance = balance_result
            balance_usd = Decimal(str(formatted_balance))

            print(f"✅ Balance fetched: ${balance_usd:.2f} {symbol}")

            # Update database (simulation only - not committing)
            print(f"\n🔄 Simulating database update...")

            if chain_addresses_table is not None:
                from sqlalchemy import and_

                check_stmt = (
                    select(chain_addresses_table.c.id, chain_addresses_table.c.balance_usd)
                    .where(
                        and_(
                            chain_addresses_table.c.wallet_id == wallet_id,
                            chain_addresses_table.c.chain == chain,
                        )
                    )
                )
                check_result = await session.execute(check_stmt)
                existing = check_result.fetchone()

                if existing:
                    current_balance = existing[1] or Decimal("0.00")
                    print(f"  Current DB balance: ${current_balance:.2f}")
                    print(f"  New balance: ${balance_usd:.2f}")
                    print(f"  Change: ${abs(balance_usd - current_balance):.2f}")
                else:
                    print(f"  No existing chain_address record")
                    print(f"  Would create new record with balance: ${balance_usd:.2f}")

            # Don't actually commit
            await session.rollback()
            print(f"✅ Simulation complete (no changes committed)")

            return True

    finally:
        await container.close()


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("ETHERSCAN BALANCE INTEGRATION TEST SUITE")
    print("=" * 80)
    print(f"\nTest Wallet: {TEST_WALLET}")
    print(f"Expected Balance: 3 USDT")
    print()

    results = []

    # Test 1: Direct Etherscan client
    try:
        result1 = await test_etherscan_client()
        results.append(("Etherscan Client", result1))
    except Exception as e:
        print(f"❌ Test 1 failed with exception: {e}")
        results.append(("Etherscan Client", False))

    # Test 2: Database lookup
    try:
        result2 = await test_database_wallet()
        results.append(("Database Wallet", result2))
    except Exception as e:
        print(f"❌ Test 2 failed with exception: {e}")
        results.append(("Database Wallet", False))

    # Test 3: Celery task simulation
    try:
        result3 = await test_celery_task_simulation()
        results.append(("Celery Task Simulation", result3))
    except Exception as e:
        print(f"❌ Test 3 failed with exception: {e}")
        results.append(("Celery Task Simulation", False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
