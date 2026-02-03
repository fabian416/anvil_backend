#!/usr/bin/env python3
"""
Script to upgrade a user to admin role.

Usage:
    python scripts/upgrade_user_to_admin.py <email>
"""

import asyncio
import sys
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.infrastructure.persistence_sqla.mappings.all import map_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.setup.config.settings import load_settings


async def upgrade_user_to_admin(email: str):
    """Upgrade user to admin role."""
    settings = load_settings()
    engine = create_async_engine(settings.postgres.dsn)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        map_tables()
        users_table = mapping_registry.metadata.tables.get("users")

        if users_table is None:
            print("❌ Users table not found")
            await engine.dispose()
            return False

        # Find user
        stmt = select(users_table).where(users_table.c.email == email)
        result = await session.execute(stmt)
        user_row = result.first()

        if not user_row:
            print(f"❌ User {email} not found")
            await engine.dispose()
            return False

        print(f"✓ Found user: {user_row.email} (ID: {user_row.id})")
        print(f"  Current role: {user_row.role}")

        # Update role to ADMIN
        stmt = (
            update(users_table)
            .where(users_table.c.id == user_row.id)
            .values(role="admin")
        )
        await session.execute(stmt)
        await session.commit()

        # Verify
        result = await session.execute(
            select(users_table).where(users_table.c.id == user_row.id)
        )
        updated_user = result.first()

        if updated_user.role == "admin":
            print(f"✅ User upgraded to admin successfully")
            print(f"  New role: {updated_user.role}")
            await engine.dispose()
            return True
        else:
            print(f"❌ Failed to upgrade user. Role is still: {updated_user.role}")
            await engine.dispose()
            return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/upgrade_user_to_admin.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    success = asyncio.run(upgrade_user_to_admin(email))
    sys.exit(0 if success else 1)
