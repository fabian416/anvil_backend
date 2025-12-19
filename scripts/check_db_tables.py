#!/usr/bin/env python3
"""
Script to check which tables exist in the database.
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
from app.infrastructure.persistence_sqla.mappings.all import map_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry


async def check_tables() -> None:
    """
    Check which tables exist in the database and compare with expected tables.
    """
    logger = logging.getLogger(__name__)
    
    try:
        print("📋 Loading settings...")
        settings = load_settings()
        print(f"📊 Database DSN: {settings.postgres.dsn}")
        
        print("🗺️ Mapping tables...")
        map_tables()
        
        # Get expected tables from metadata
        expected_tables = set(mapping_registry.metadata.tables.keys())
        print(f"\n📋 Expected tables ({len(expected_tables)}):")
        for table_name in sorted(expected_tables):
            print(f"  - {table_name}")
        
        print("\n🔧 Creating connection to database...")
        engine = create_async_engine(
            settings.postgres.dsn,
            echo=False,
            connect_args={'connect_timeout': 5},
            pool_pre_ping=True,
        )
        
        print("🔍 Querying database for existing tables...")
        
        # Query PostgreSQL for all tables in the public schema
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
            )
            existing_tables = {row[0] for row in result.fetchall()}
        
        print(f"\n📊 Existing tables in database ({len(existing_tables)}):")
        for table_name in sorted(existing_tables):
            print(f"  - {table_name}")
        
        # Compare
        missing_tables = expected_tables - existing_tables
        extra_tables = existing_tables - expected_tables
        
        print(f"\n{'='*60}")
        if not missing_tables and not extra_tables:
            print("✅ All expected tables are present in the database!")
        else:
            if missing_tables:
                print(f"❌ Missing tables ({len(missing_tables)}):")
                for table_name in sorted(missing_tables):
                    print(f"  - {table_name}")
            
            if extra_tables:
                print(f"⚠️  Extra tables in database ({len(extra_tables)}):")
                for table_name in sorted(extra_tables):
                    print(f"  - {table_name}")
        
        print(f"{'='*60}")
        print(f"📈 Summary:")
        print(f"  Expected: {len(expected_tables)}")
        print(f"  Found: {len(existing_tables)}")
        print(f"  Missing: {len(missing_tables)}")
        print(f"  Extra: {len(extra_tables)}")
        
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Error checking tables: {str(e)}")
        raise


async def main():
    """Main function to check database tables."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        print("🚀 Starting database table check...")
        print(f"🌍 APP_ENV: {os.environ.get('APP_ENV', 'Not set')}")
        await check_tables()
        print("\n✅ Database table check completed successfully!")
    except Exception as e:
        print(f"❌ Database table check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

