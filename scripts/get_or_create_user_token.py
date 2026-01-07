#!/usr/bin/env python3
"""
Script to get or create access token for a user by email.

If user has active session, returns existing token.
Otherwise, creates a new session and returns new token.

Usage:
    python scripts/get_or_create_user_token.py ops@anvilcrypto.com
"""

import asyncio
import sys
import os
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime, timedelta

from app.infrastructure.persistence_sqla.mappings.user import map_users_table
from app.infrastructure.persistence_sqla.mappings.session import map_sessions_table
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.setup.config.settings import load_settings
from app.infrastructure.auth.session.service import AuthSessionService
from app.infrastructure.auth.session.id_generator_str import StrAuthSessionIdGenerator
from app.infrastructure.auth.session.timer_utc import UtcAuthSessionTimer
from app.infrastructure.auth.refresh_token.generator import RefreshTokenGenerator
from app.infrastructure.auth.adapters.data_mapper_sqla import SqlaAuthSessionDataMapper
from app.infrastructure.auth.adapters.access_token_processor_jwt import JwtAccessTokenProcessor
from app.infrastructure.auth.session.model import AuthSession
from app.domain.value_objects.user_id import UserId
from app.setup.config.security import SecuritySettings


async def get_or_create_user_token(email: str) -> str | None:
    """
    Get or create access token for user by email.
    
    Args:
        email: User email address
        
    Returns:
        Access token or None if not found
    """
    # Load settings
    settings = load_settings()
    database_url = settings.postgres.dsn
    
    # Map tables
    map_users_table()
    map_sessions_table()
    
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
        
        # Try to get existing active session
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
        
        if token_row:
            access_token = token_row.access_token
            print(f"✓ Found existing access token: {access_token[:30]}...")
            await engine.dispose()
            return access_token
        
        # No active session found - create new one
        print("⚠️  No active session found, creating new session...")
        
        # Create auth session service components
        from app.infrastructure.auth.adapters.access_token_processor_jwt import JwtAccessTokenProcessor
        from app.setup.config.security import SecuritySettings
        
        security_settings = SecuritySettings()
        jwt_processor = JwtAccessTokenProcessor(security_settings)
        
        # Create session
        session_id_generator = StrAuthSessionIdGenerator()
        session_timer = UtcAuthSessionTimer(
            auth_session_ttl_min=security_settings.auth_session_ttl_min,
            auth_session_refresh_threshold=security_settings.auth_session_refresh_threshold,
        )
        refresh_token_generator = RefreshTokenGenerator()
        
        # Create auth session
        session_id = session_id_generator()
        expiration = session_timer.auth_session_expiration()
        refresh_token = refresh_token_generator()
        
        auth_session = AuthSession(
            id_=session_id,
            user_id=UserId(value=user_id),
            expiration=expiration,
            refresh_token=refresh_token,
        )
        
        # Create JWT access token
        access_token = jwt_processor.create_token(
            session_id=session_id,
            user_id=user_id,
            email=email,
        )
        
        # Save session to database
        from app.infrastructure.auth.adapters.data_mapper_sqla import SqlaAuthSessionDataMapper
        auth_mapper = SqlaAuthSessionDataMapper(session)
        auth_mapper.add(auth_session)
        await session.commit()
        
        # Also save to sessions table (legacy)
        from datetime import datetime, timedelta
        expires_at = expiration
        
        insert_stmt = sessions_table.insert().values(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_at=expires_at,
            is_active=True,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )
        await session.execute(insert_stmt)
        await session.commit()
        
        print(f"✓ Created new access token: {access_token[:30]}...")
        await engine.dispose()
        return access_token


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/get_or_create_user_token.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    print(f"Searching for user: {email}")
    
    token = await get_or_create_user_token(email)
    
    if token:
        print(f"\n✅ Access Token:")
        print(token)
        return token
    else:
        print("\n❌ Could not retrieve or create access token")
        sys.exit(1)


if __name__ == "__main__":
    token = asyncio.run(main())
