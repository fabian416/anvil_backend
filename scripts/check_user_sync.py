#!/usr/bin/env python3
"""
Check a user's sync eligibility and related data (privy_user_id or email).

Usage:
    PYTHONPATH=src python scripts/check_user_sync.py "did:privy:cml15tigy02bul70compgthrd"
    PYTHONPATH=src python scripts/check_user_sync.py ops@anvilcrypto.com
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.setup.config.settings import load_settings
from app.infrastructure.persistence_sqla.mappings.all import map_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry


async def check_user(identifier: str) -> None:
    """Look up user by privy_user_id or email and print sync-related data."""
    settings = load_settings()
    map_tables()
    engine = create_async_engine(
        settings.postgres.dsn,
        echo=False,
        connect_args={"connect_timeout": 5},
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    users_table = mapping_registry.metadata.tables.get("users")
    wallets_table = mapping_registry.metadata.tables.get("wallets")
    schedule_table = mapping_registry.metadata.tables.get("user_sync_schedule")
    swap_intents_table = mapping_registry.metadata.tables.get("swap_intents")
    transactions_table = mapping_registry.metadata.tables.get("transactions")

    if users_table is None:
        print("❌ users table not mapped")
        return

    async with async_session() as session:
        # Resolve identifier: privy_user_id or email
        if identifier.startswith("did:privy:"):
            stmt = select(users_table).where(
                users_table.c.privy_user_id == identifier
            )
        else:
            stmt = select(users_table).where(
                users_table.c.email == identifier
            )
        result = await session.execute(stmt)
        row = result.first()
        if row is None:
            print(f"❌ No user found for: {identifier}")
            return

        user_id = row.id
        email = row.email
        privy_user_id = row.privy_user_id
        primary_wallet_address = row.primary_wallet_address
        auth_provider = row.auth_provider

        print("=" * 60)
        print("USER")
        print("=" * 60)
        print(f"  id:                  {user_id}")
        print(f"  email:               {email}")
        print(f"  privy_user_id:       {privy_user_id}")
        print(f"  primary_wallet:      {primary_wallet_address}")
        print(f"  auth_provider:       {auth_provider}")

        if wallets_table is not None:
            w_stmt = select(wallets_table).where(wallets_table.c.user_id == user_id)
            w_res = await session.execute(w_stmt)
            wallets = w_res.fetchall()
            print(f"\n  wallets:             {len(wallets)}")
            for w in wallets:
                print(f"    - id={w.id} address={w.address} status={w.status}")

        if schedule_table is not None:
            s_stmt = select(schedule_table).where(schedule_table.c.user_id == user_id)
            s_res = await session.execute(s_stmt)
            s_row = s_res.first()
            if s_row:
                print("\n" + "=" * 60)
                print("USER_SYNC_SCHEDULE (eligible for recent-user incremental sync)")
                print("=" * 60)
                print(f"  next_sync_at:        {s_row.next_sync_at}")
                print(f"  interval_index:     {s_row.interval_index}")
                print(f"  last_synced_at:     {s_row.last_synced_at}")
            else:
                print("\n  user_sync_schedule:  (no row – will be seeded from auth_sessions or on next privy-login)")

        if swap_intents_table is not None:
            pending = 0
            completed = 0
            for status in ("pending", "completed"):
                c_stmt = select(func.count()).select_from(swap_intents_table).where(
                    swap_intents_table.c.user_id == user_id,
                    swap_intents_table.c.status == status,
                )
                c_res = await session.execute(c_stmt)
                cnt = c_res.scalar() or 0
                if status == "pending":
                    pending = cnt
                else:
                    completed = cnt
            print("\n" + "=" * 60)
            print("SWAP_INTENTS")
            print("=" * 60)
            print(f"  pending:             {pending}")
            print(f"  completed:          {completed}")

        if transactions_table is not None:
            tx_stmt = select(func.count()).select_from(transactions_table).where(
                transactions_table.c.user_id == user_id,
                transactions_table.c.type == 0,  # SWAP
            )
            tx_res = await session.execute(tx_stmt)
            swap_count = tx_res.scalar() or 0
            total_stmt = select(func.count()).select_from(transactions_table).where(
                transactions_table.c.user_id == user_id,
            )
            total_res = await session.execute(total_stmt)
            total_tx = total_res.scalar() or 0
            print("\n" + "=" * 60)
            print("TRANSACTIONS")
            print("=" * 60)
            print(f"  swap count:          {swap_count}")
            print(f"  total count:         {total_tx}")
            print("\n  ('My swaps' shows rows with type=SWAP)")

    await engine.dispose()
    print("\n✅ Done.")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: PYTHONPATH=src python scripts/check_user_sync.py <privy_user_id|email>")
        print('  e.g.  python scripts/check_user_sync.py "did:privy:cml15tigy02bul70compgthrd"')
        print("  e.g.  python scripts/check_user_sync.py ops@anvilcrypto.com")
        sys.exit(1)
    asyncio.run(check_user(sys.argv[1].strip()))


if __name__ == "__main__":
    main()
