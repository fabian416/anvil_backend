#!/usr/bin/env python3
"""
Database creation script for the hexagonal architecture project.
This script creates the database if it doesn't exist, then initializes tables.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.setup.config.settings import load_settings


async def create_database() -> None:
    """
    Create the database if it doesn't exist.
    """
    logger = logging.getLogger(__name__)
    
    try:
        print("📋 Loading settings...")
        settings = load_settings()
        print(f"📊 Database DSN: {settings.postgres.dsn}")
        
        # Create connection string to postgres database (default database)
        postgres_dsn = f"postgresql+psycopg://{settings.postgres.user}:{settings.postgres.password}@{settings.postgres.host}:{settings.postgres.port}/postgres"
        
        print("🔧 Creating connection to postgres database...")
        engine = create_async_engine(
            postgres_dsn,
            echo=False,
            connect_args={'connect_timeout': 5},
            pool_pre_ping=True,
        )
        
        print(f"🏗️ Creating database '{settings.postgres.db}'...")
        
        # Check if database exists
        async with engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{settings.postgres.db}'")
            )
            db_exists = result.fetchone() is not None
        
        if not db_exists:
            # Create database (must be outside transaction)
            async with engine.connect() as conn:
                # Set autocommit for this connection
                conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
                await conn.execute(text(f"CREATE DATABASE {settings.postgres.db}"))
            print(f"✅ Database '{settings.postgres.db}' created successfully!")
        else:
            print(f"ℹ️ Database '{settings.postgres.db}' already exists.")
        
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise


async def main():
    """Main function to create database."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        print("🚀 Starting database creation...")
        print(f"🌍 APP_ENV: {os.environ.get('APP_ENV', 'Not set')}")
        await create_database()
        print("✅ Database creation completed successfully!")
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
