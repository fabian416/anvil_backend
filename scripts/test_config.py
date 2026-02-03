#!/usr/bin/env python3
"""
Test script to debug configuration loading.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.setup.config.settings import load_settings


def main():
    try:
        print("🔍 Testing configuration loading...")
        settings = load_settings()
        print(f"✅ Settings loaded successfully!")
        print(f"📊 Database DSN: {settings.postgres.dsn}")
        print(f"🏠 Host: {settings.postgres.host}")
        print(f"👤 User: {settings.postgres.user}")
        print(f"🔑 Password: {'*' * len(settings.postgres.password)}")
        print(f"🗄️ Database: {settings.postgres.db}")
        print(f"🔌 Port: {settings.postgres.port}")
        print(f"🚗 Driver: {settings.postgres.driver}")
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
