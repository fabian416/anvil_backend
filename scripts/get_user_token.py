#!/usr/bin/env python3
"""
Script to get access token for a user by email.

Usage:
    python scripts/get_user_token.py ops@anvilcrypto.com
"""

import asyncio
import sys
import os
from sqlalchemy import select, text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.infrastructure.persistence_sqla.mappings.all import map_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.setup.config.settings import load_settings


async def get_user_token(email: str) -> str | None:
    """
    Get access token for user by email.
    
    Args:
        email: User email address
        
    Returns:
        Access token or None if not found
    """
    # Load settings to get database URL
    settings = load_settings()
    database_url = settings.postgres.dsn
    
    # Map all tables
    map_tables()
    
    # Create async engine and session
    engine = create_async_engine(database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # Get users table
        users_table = mapping_registry.metadata.tables.get("users")
        if users_table is None:
            print("❌ Users table not found")
            await engine.dispose()
            return None
        
        # Get sessions table
        sessions_table = mapping_registry.metadata.tables.get("sessions")
        if sessions_table is None:
            print("❌ Sessions table not found")
            await engine.dispose()
            return None
        
        # Find user by email
        stmt = select(users_table.c.id).where(users_table.c.email == email)
        result = await session.execute(stmt)
        user_row = result.first()
        
        if not user_row:
            print(f"❌ User with email {email} not found")
            await engine.dispose()
            return None
        
        user_id = user_row.id
        print(f"✓ Found user: {email} (ID: {user_id})")
        
        # Get most recent active session for user
        stmt = (
            select(sessions_table.c.access_token)
            .where(sessions_table.c.user_id == user_id)
            .where(sessions_table.c.is_active == True)
            .where(sessions_table.c.expires_at > text("CURRENT_TIMESTAMP"))
            .order_by(sessions_table.c.expires_at.desc())
            .limit(1)
        )
        
        result = await session.execute(stmt)
        token_row = result.first()
        
        if not token_row:
            print(f"❌ No active session found for user {email}")
            await engine.dispose()
            return None
        
        access_token = token_row.access_token
        print(f"✓ Found access token: {access_token[:30]}...")
        
        await engine.dispose()
        return access_token


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/get_user_token.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    print(f"Searching for user: {email}")
    
    token = await get_user_token(email)
    
    if token:
        print(f"\n✅ Access Token:")
        print(token)
        return token
    else:
        print("\n❌ Could not retrieve access token")
        sys.exit(1)


if __name__ == "__main__":
    token = asyncio.run(main())
