"""
Privy Wallet Balance Sync Celery Tasks.

Background tasks for synchronizing wallet balances from Privy API
to the local database for portfolio tracking.

Task Configuration:
- Runs every 30 seconds
- Processes max 10 users per run
- Filters users by last_balance_checked_at (only if > 3 minutes ago)

This ensures wallet balances are reasonably fresh for:
- swap_workflow agent balance validation
- Portfolio state classification
- Risk assessment
"""

import asyncio
import logging
from datetime import datetime, UTC, timedelta
from decimal import Decimal
from typing import Any

import httpx

from app.infrastructure.celery.app import celery_app
from app.setup.ioc.provider_registry import get_providers
from app.setup.app_factory import create_async_ioc_container
from app.setup.config.settings import load_settings

logger = logging.getLogger(__name__)

# Task configuration
MAX_USERS_PER_RUN = 10  # Max wallets to process per run
BALANCE_CHECK_INTERVAL_SECONDS = 180  # 3 minutes cooldown between checks
PRIVY_API_TIMEOUT = 10.0  # Timeout for Privy API calls

# Chain ID mapping for Privy API
CHAIN_ID_MAP = {
    "ethereum": 1,
    "base": 8453,
    "arbitrum": 42161,
    "polygon": 137,
    "optimism": 10,
}


async def _run_task(coro_factory):
    """Helper to run async tasks with DI container using all registered providers."""
    settings = load_settings()
    container = create_async_ioc_container(
        providers=get_providers(),
        settings=settings,
    )
    try:
        async with container() as request_container:
            await coro_factory(request_container)
    finally:
        await container.close()


async def fetch_privy_wallet_balance(
    http_client: httpx.AsyncClient,
    wallet_id: str,
    chain: str,
    asset: str,
    privy_app_id: str,
    privy_app_secret: str,
) -> dict[str, Any] | None:
    """
    Fetch wallet balance from Privy API.

    API: GET /v1/wallets/{wallet_id}/balance

    Args:
        http_client: HTTP client for requests
        wallet_id: Privy wallet ID
        chain: Chain name (e.g., "ethereum", "base", "arbitrum")
        asset: Asset to check (e.g., "usdc", "eth")
        privy_app_id: Privy App ID
        privy_app_secret: Privy App Secret

    Returns:
        Balance data dict or None on error
    """
    import base64

    # Create Basic Auth credentials
    credentials = f"{privy_app_id}:{privy_app_secret}"
    basic_auth = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {basic_auth}",
        "Content-Type": "application/json",
        "privy-app-id": privy_app_id,
    }

    url = f"https://api.privy.io/v1/wallets/{wallet_id}/balance"
    params = {
        "chain": chain,
        "asset": asset,
    }

    try:
        response = await http_client.get(
            url,
            params=params,
            headers=headers,
            timeout=PRIVY_API_TIMEOUT,
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            logger.debug(f"Wallet {wallet_id} not found in Privy")
            return None
        elif response.status_code == 429:
            logger.warning(f"Privy rate limit hit for wallet {wallet_id}")
            return None
        else:
            logger.error(
                f"Privy API error for wallet {wallet_id}: "
                f"{response.status_code} - {response.text}"
            )
            return None

    except httpx.TimeoutException:
        logger.warning(f"Privy API timeout for wallet {wallet_id}")
        return None
    except Exception as e:
        logger.error(f"Privy API error for wallet {wallet_id}: {e}")
        return None


@celery_app.task(name="privy.sync_wallet_balances")
def sync_wallet_balances():
    """
    Sync wallet balances from Privy API.

    This task:
    1. Fetches wallets eligible for balance check (last_balance_checked_at > 3 min ago)
    2. Calls Privy API to get current balance
    3. Updates chain_addresses.balance_usd in database
    4. Updates wallets.last_balance_checked_at timestamp

    Configuration:
    - Runs every 30 seconds (beat schedule)
    - Processes max 10 wallets per run
    - Skips wallets checked within last 3 minutes
    """

    async def runner(container):
        from sqlalchemy import select, update, and_, or_
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.infrastructure.persistence_sqla.registry import mapping_registry
        from app.infrastructure.persistence_sqla.mappings.wallet import (
            map_wallet_tables,
        )
        from app.infrastructure.adapters.types import MainAsyncSession
        from app.setup.config.privy import PrivySettings

        start_time = datetime.now(UTC)
        logger.info(f"🔄 Starting Privy balance sync at {start_time.isoformat()}")

        processed_count = 0
        updated_count = 0
        error_count = 0

        try:
            # Get settings and session
            privy_settings = await container.get(PrivySettings)
            session: AsyncSession = await container.get(MainAsyncSession)

            # Check if Privy is configured
            if not privy_settings.app_id or not privy_settings.app_secret:
                logger.warning(
                    "Privy credentials not configured, skipping balance sync"
                )
                return

            # Ensure wallet table mappings are loaded
            map_wallet_tables()

            # Get table references
            wallets_table = mapping_registry.metadata.tables.get("wallets")
            chain_addresses_table = mapping_registry.metadata.tables.get(
                "chain_addresses"
            )

            if wallets_table is None:
                logger.warning("wallets table not found, skipping")
                return

            # Calculate cutoff time (3 minutes ago)
            cutoff_time = datetime.now(UTC) - timedelta(
                seconds=BALANCE_CHECK_INTERVAL_SECONDS
            )

            # Query wallets eligible for balance check
            # - Has privy_wallet_id (Privy-managed wallet)
            # - Status is ACTIVE (1)
            # - last_balance_checked_at is NULL or older than cutoff
            stmt = (
                select(
                    wallets_table.c.id,
                    wallets_table.c.user_id,
                    wallets_table.c.privy_wallet_id,
                    wallets_table.c.address,
                    wallets_table.c.default_chain,
                )
                .where(
                    and_(
                        wallets_table.c.privy_wallet_id.isnot(None),
                        wallets_table.c.status == 1,  # ACTIVE
                        or_(
                            wallets_table.c.last_balance_checked_at.is_(None),
                            wallets_table.c.last_balance_checked_at < cutoff_time,
                        ),
                    )
                )
                .order_by(wallets_table.c.last_balance_checked_at.nullsfirst())
                .limit(MAX_USERS_PER_RUN)
            )

            result = await session.execute(stmt)
            wallets = result.fetchall()

            if not wallets:
                logger.debug("No wallets eligible for balance check")
                return

            logger.info(f"📊 Processing {len(wallets)} wallets for balance sync")

            # Create HTTP client for Privy API calls
            async with httpx.AsyncClient() as http_client:
                for wallet_row in wallets:
                    wallet_id = wallet_row[0]
                    user_id = wallet_row[1]
                    privy_wallet_id = wallet_row[2]
                    wallet_address = wallet_row[3]
                    # Get chain value - handle enum or string
                    chain_raw = wallet_row[4]
                    if chain_raw:
                        # If it's an enum, get its value; otherwise convert to string
                        default_chain = (
                            chain_raw.value
                            if hasattr(chain_raw, "value")
                            else str(chain_raw)
                        )
                    else:
                        default_chain = "base"

                    processed_count += 1

                    try:
                        # Fetch balance from Privy (USDC)
                        balance_data = await fetch_privy_wallet_balance(
                            http_client=http_client,
                            wallet_id=privy_wallet_id,
                            chain=default_chain,  # Use chain name directly
                            asset="usdc",
                            privy_app_id=privy_settings.app_id,
                            privy_app_secret=privy_settings.app_secret,
                        )

                        if balance_data:
                            # Extract balance value from Privy response
                            # Privy returns: {"balances": [{"raw_value": "0", "raw_value_decimals": 6, ...}]}
                            balances = balance_data.get("balances", [])
                            if balances:
                                first_balance = balances[0]
                                raw_balance = first_balance.get("raw_value", "0")
                                decimals = first_balance.get("raw_value_decimals", 6)
                            else:
                                raw_balance = "0"
                                decimals = 6

                            # Convert to USD value
                            balance_usd = Decimal(raw_balance) / Decimal(10**decimals)

                            # Update chain_addresses table if exists
                            if chain_addresses_table is not None:
                                # Check if chain address exists
                                check_stmt = select(chain_addresses_table.c.id).where(
                                    and_(
                                        chain_addresses_table.c.wallet_id == wallet_id,
                                        chain_addresses_table.c.chain == default_chain,
                                    )
                                )
                                check_result = await session.execute(check_stmt)
                                existing = check_result.fetchone()

                                if existing:
                                    # Update existing chain address
                                    update_chain_stmt = (
                                        update(chain_addresses_table)
                                        .where(
                                            chain_addresses_table.c.id == existing[0]
                                        )
                                        .values(
                                            balance_usd=balance_usd,
                                            last_balance_update=datetime.now(UTC),
                                        )
                                    )
                                    await session.execute(update_chain_stmt)
                                else:
                                    # Insert new chain address
                                    from sqlalchemy import insert

                                    insert_stmt = insert(chain_addresses_table).values(
                                        wallet_id=wallet_id,
                                        chain=default_chain,
                                        address=wallet_address,
                                        is_active=True,
                                        balance_usd=balance_usd,
                                        last_balance_update=datetime.now(UTC),
                                    )
                                    await session.execute(insert_stmt)

                            updated_count += 1
                            logger.debug(
                                f"Updated balance for wallet {wallet_id}: "
                                f"${balance_usd:.2f} on {default_chain}"
                            )

                        # Always update last_balance_checked_at to prevent re-processing
                        update_wallet_stmt = (
                            update(wallets_table)
                            .where(wallets_table.c.id == wallet_id)
                            .values(last_balance_checked_at=datetime.now(UTC))
                        )
                        await session.execute(update_wallet_stmt)

                    except Exception as e:
                        error_count += 1
                        logger.error(f"Failed to sync wallet {wallet_id}: {e}")

            # Commit all changes
            await session.commit()

            # Summary
            duration = (datetime.now(UTC) - start_time).total_seconds()
            logger.info(
                f"✅ Privy balance sync complete: "
                f"processed={processed_count}, updated={updated_count}, "
                f"errors={error_count}, duration={duration:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ Privy balance sync failed: {e}")
            raise

    asyncio.run(_run_task(runner))


@celery_app.task(name="privy.sync_single_wallet_balance")
def sync_single_wallet_balance(wallet_id: int, chain: str = "base"):
    """
    Sync balance for a single wallet on-demand.

    Used for:
    - Pre-transaction balance validation
    - User-triggered refresh
    - swap_workflow agent balance check

    Args:
        wallet_id: Database wallet ID
        chain: Blockchain to check (default: base)
    """

    async def runner(container):
        from sqlalchemy import select, update, and_
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.infrastructure.persistence_sqla.registry import mapping_registry
        from app.infrastructure.persistence_sqla.mappings.wallet import (
            map_wallet_tables,
        )
        from app.infrastructure.adapters.types import MainAsyncSession
        from app.setup.config.privy import PrivySettings

        logger.info(
            f"🔄 Single wallet balance sync: wallet_id={wallet_id}, chain={chain}"
        )

        try:
            # Get settings and session
            privy_settings = await container.get(PrivySettings)
            session: AsyncSession = await container.get(MainAsyncSession)

            if not privy_settings.app_id or not privy_settings.app_secret:
                logger.warning("Privy credentials not configured")
                return

            # Ensure wallet table mappings are loaded
            map_wallet_tables()

            wallets_table = mapping_registry.metadata.tables.get("wallets")
            chain_addresses_table = mapping_registry.metadata.tables.get(
                "chain_addresses"
            )

            if wallets_table is None:
                logger.warning("wallets table not found")
                return

            # Get wallet
            stmt = select(
                wallets_table.c.privy_wallet_id,
                wallets_table.c.address,
            ).where(wallets_table.c.id == wallet_id)
            result = await session.execute(stmt)
            wallet_row = result.fetchone()

            if not wallet_row or not wallet_row[0]:
                logger.warning(f"Wallet {wallet_id} not found or no privy_wallet_id")
                return

            privy_wallet_id = wallet_row[0]
            wallet_address = wallet_row[1]

            async with httpx.AsyncClient() as http_client:
                balance_data = await fetch_privy_wallet_balance(
                    http_client=http_client,
                    wallet_id=privy_wallet_id,
                    chain=chain,  # Use chain name directly
                    asset="usdc",
                    privy_app_id=privy_settings.app_id,
                    privy_app_secret=privy_settings.app_secret,
                )

                if balance_data:
                    # Extract balance value from Privy response
                    balances = balance_data.get("balances", [])
                    if balances:
                        first_balance = balances[0]
                        raw_balance = first_balance.get("raw_value", "0")
                        decimals = first_balance.get("raw_value_decimals", 6)
                    else:
                        raw_balance = "0"
                        decimals = 6
                    balance_usd = Decimal(raw_balance) / Decimal(10**decimals)

                    if chain_addresses_table is not None:
                        check_stmt = select(chain_addresses_table.c.id).where(
                            and_(
                                chain_addresses_table.c.wallet_id == wallet_id,
                                chain_addresses_table.c.chain == chain,
                            )
                        )
                        check_result = await session.execute(check_stmt)
                        existing = check_result.fetchone()

                        if existing:
                            update_chain_stmt = (
                                update(chain_addresses_table)
                                .where(chain_addresses_table.c.id == existing[0])
                                .values(
                                    balance_usd=balance_usd,
                                    last_balance_update=datetime.now(UTC),
                                )
                            )
                            await session.execute(update_chain_stmt)
                        else:
                            from sqlalchemy import insert

                            insert_stmt = insert(chain_addresses_table).values(
                                wallet_id=wallet_id,
                                chain=chain,
                                address=wallet_address,
                                is_active=True,
                                balance_usd=balance_usd,
                                last_balance_update=datetime.now(UTC),
                            )
                            await session.execute(insert_stmt)

                    # Update wallet timestamp
                    update_wallet_stmt = (
                        update(wallets_table)
                        .where(wallets_table.c.id == wallet_id)
                        .values(last_balance_checked_at=datetime.now(UTC))
                    )
                    await session.execute(update_wallet_stmt)
                    await session.commit()

                    logger.info(f"✅ Updated wallet {wallet_id}: ${balance_usd:.2f}")
                else:
                    logger.warning(f"No balance data returned for wallet {wallet_id}")

        except Exception as e:
            logger.error(f"❌ Single wallet sync failed for {wallet_id}: {e}")
            raise

    asyncio.run(_run_task(runner))
