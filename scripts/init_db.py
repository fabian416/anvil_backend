#!/usr/bin/env python3
"""
Database initialization script for the hexagonal architecture project.
This script creates all database tables using SQLAlchemy.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.infrastructure.persistence_sqla.mappings.all import map_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.setup.config.settings import load_settings
from sqlalchemy.ext.asyncio import create_async_engine


async def init_database() -> None:
    """
    Initialize the database by creating all tables.
    This function ensures all SQLAlchemy mappings are registered and tables are created.
    """
    logger = logging.getLogger(__name__)
    
    try:
        print("📋 Loading settings...")
        # Load settings
        settings = load_settings()
        print(f"📊 Database DSN: {settings.postgres.dsn}")
        
        print("🔧 Creating async engine...")
        # Create async engine
        engine = create_async_engine(
            settings.postgres.dsn,
            echo=settings.sqla.echo,
            echo_pool=settings.sqla.echo_pool,
            pool_size=settings.sqla.pool_size,
            max_overflow=settings.sqla.max_overflow,
            connect_args={'connect_timeout': 5},
            pool_pre_ping=True,
        )
        
        print("🗺️ Mapping tables...")
        # Ensure all table mappings are registered
        map_tables()
        
        # Import entities to ensure they are registered
        from app.domain.entities.user import User
        from app.domain.entities.country import Country
        from app.domain.entities.city import City
        from app.domain.entities.email_verification import EmailVerification
        from app.domain.entities.notification import Notification
        from app.domain.entities.password_reset import PasswordReset
        from app.domain.entities.payment import Payment
        from app.domain.entities.session import Session
        from app.domain.entities.subscription import Subscription
        from app.domain.entities.subscription_user import SubscriptionUser
        
        print("🧹 Dropping existing tables (local env)...")
        async with engine.begin() as conn:
            # For local/dev environment, drop all known tables first
            await conn.run_sync(mapping_registry.metadata.drop_all)

        print("🏗️ Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(mapping_registry.metadata.create_all)
        
        logger.info("Database tables created successfully")
        print("✅ Database tables created successfully")
        
        # Clean up
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


async def main():
    """Main function to run database initialization."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        print("🚀 Starting database initialization...")
        print(f"🌍 APP_ENV: {os.environ.get('APP_ENV', 'Not set')}")
        await init_database()
        print("✅ Database initialization completed successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
