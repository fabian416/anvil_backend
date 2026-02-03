"""Seed initial data for production deployment."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.setup.config.settings import load_settings
from app.setup.app_factory import create_async_ioc_container
from app.setup.ioc.provider_registry import get_providers


async def seed_distillation_config():
    """Seed default distillation configuration."""
    print("🌱 Seeding distillation configuration...")

    from app.infrastructure.persistence_sqla.repositories.distillation_config_repository import (
        DistillationConfigRepositorySqla,
    )
    from app.domain.value_objects.distillation import DistillationConfig

    settings = load_settings()
    container = create_async_ioc_container(
        providers=get_providers(),
        settings=settings,
    )

    try:
        async with container() as request_container:
            config_repo = await request_container.get(DistillationConfigRepositorySqla)

            # Try to get existing config
            try:
                existing_config = await config_repo.get_config()
                print("  ✅ Distillation config already exists, skipping...")
                return
            except:
                # Config doesn't exist, create it
                pass

            # Create default config
            default_config = DistillationConfig(
                enabled=True,
                cache_enabled=True,
                static_responses_enabled=True,
                semantic_cache_enabled=True,
                min_confidence_threshold=0.7,
                semantic_similarity_threshold=0.85,
                max_classification_latency_ms=500,
                exact_cache_ttl_hours=24,
                semantic_cache_ttl_hours=48,
                static_response_ttl_hours=168,  # 1 week
            )

            await config_repo.update_config(default_config)
            print("  ✅ Created default distillation configuration")

    finally:
        await container.close()


async def seed_static_responses():
    """Seed default static response templates."""
    print("🌱 Seeding static response templates...")

    from app.infrastructure.persistence_sqla.repositories.distillation_static_repository import (
        DistillationStaticRepositorySqla,
    )
    from app.domain.entities.distillation import StaticResponse
    from app.domain.value_objects.distillation import Intent
    from uuid import uuid4
    from datetime import datetime

    settings = load_settings()
    container = create_async_ioc_container(
        providers=get_providers(),
        settings=settings,
    )

    # Define default static responses
    default_responses = [
        {
            "intent": Intent.GENERAL_GREETING,
            "variant": "default",
            "response_template": "Hello! I'm your DeFi assistant. I can help you with trading, lending, portfolio management, and market research. What would you like to do today?",
            "template_variables": [],
            "priority": 1,
        },
        {
            "intent": Intent.GENERAL_HELP,
            "variant": "default",
            "response_template": "I can assist you with:\n- 💱 **Trading**: Swap tokens, get quotes\n- 💰 **Lending**: Supply or borrow assets\n- 📊 **Portfolio**: View your balances and positions\n- 📈 **Research**: Get market data and protocol info\n\nWhat would you like help with?",
            "template_variables": [],
            "priority": 1,
        },
        {
            "intent": Intent.OFF_TOPIC,
            "variant": "default",
            "response_template": "I'm specialized in DeFi operations and can't help with that topic. Please ask me about trading, lending, portfolio management, or DeFi market research.",
            "template_variables": [],
            "priority": 1,
        },
    ]

    try:
        async with container() as request_container:
            static_repo = await request_container.get(DistillationStaticRepositorySqla)

            # Check if responses already exist
            existing = await static_repo.list_responses()
            if existing:
                print(
                    f"  ✅ {len(existing)} static responses already exist, skipping..."
                )
                return

            # Create default responses
            for response_data in default_responses:
                response = StaticResponse(
                    id=uuid4(),
                    intent=response_data["intent"],
                    variant=response_data["variant"],
                    response_template=response_data["response_template"],
                    template_variables=response_data["template_variables"],
                    data_source=None,
                    conditions={},
                    priority=response_data["priority"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                await static_repo.add_response(response)

            print(f"  ✅ Created {len(default_responses)} static response templates")

    finally:
        await container.close()


async def verify_projects():
    """Verify that default projects exist (created by migration)."""
    print("🔍 Verifying default projects...")

    from app.infrastructure.persistence_sqla.repositories.project_repository import (
        ProjectRepositorySqla,
    )

    settings = load_settings()
    container = create_async_ioc_container(
        providers=get_providers(),
        settings=settings,
    )

    try:
        async with container() as request_container:
            project_repo = await request_container.get(ProjectRepositorySqla)

            # List all projects
            projects = await project_repo.list_projects(limit=100)

            if not projects:
                print(
                    "  ⚠️  No projects found! Run migration 20251201_002_add_projects_system.py"
                )
                print("      Command: alembic upgrade head")
            else:
                print(f"  ✅ Found {len(projects)} projects:")
                for project in projects[:5]:  # Show first 5
                    print(f"      - {project.name} ({project.slug}) [{project.status}]")
                if len(projects) > 5:
                    print(f"      ... and {len(projects) - 5} more")

    finally:
        await container.close()


async def main():
    """Run all seed operations."""
    print("\n🚀 Starting seed data script...\n")

    try:
        # Seed distillation configuration
        await seed_distillation_config()
        print()

        # Seed static responses
        await seed_static_responses()
        print()

        # Verify projects
        await verify_projects()
        print()

        print("✅ Seed data complete!\n")

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║           Anvil Backend - Seed Data Script              ║
╚══════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())

    print("""
╔══════════════════════════════════════════════════════════╗
║                    Next Steps:                           ║
║  1. Start FastAPI:     make start                        ║
║  2. Start Celery:      make celery.worker                ║
║  3. Start Celery Beat: make celery.beat                  ║
║  4. Start Flower:      make celery.flower                ║
║  5. Visit docs:        http://localhost:8000/docs        ║
╚══════════════════════════════════════════════════════════╝
    """)
