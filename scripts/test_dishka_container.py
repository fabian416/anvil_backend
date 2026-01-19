#!/usr/bin/env python3
"""Test script to check if Dishka container can be created successfully."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def test_container():
    """Test creating Dishka container with all providers."""
    try:
        from app.setup.config.settings import load_settings
        from app.setup.ioc.provider_registry import get_providers
        from dishka import make_async_container
        from app.setup.config.settings import AppSettings

        print("Loading settings...")
        settings = load_settings()
        print("✅ Settings loaded")

        print("\nCreating Dishka container...")
        container = make_async_container(
            *get_providers(),
            context={AppSettings: settings},
        )
        print("✅ Container created")

        print("\nResolving UnifiedChatHandler...")
        from app.application.chat.handlers.unified_chat_handler import UnifiedChatHandler

        async with container() as request_container:
            handler = await request_container.get(UnifiedChatHandler)
            print(f"✅ UnifiedChatHandler resolved: {handler}")
            print(f"   - hunter_service: {handler._hunter_service}")
            print(f"   - cache: {handler._cache}")

            # Check if hunter_service is None
            if handler._hunter_service is None:
                print("\n❌ ERROR: hunter_service is still None!")
                return 1
            else:
                print("\n✅ SUCCESS: hunter_service is properly injected!")
                return 0

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_container())
    sys.exit(exit_code)
