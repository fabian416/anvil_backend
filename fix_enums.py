#!/usr/bin/env python3
"""Drop money market enums before migration."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.setup.config import get_config


async def drop_enums():
    config = get_config()
    engine = create_async_engine(
        config.database.url.replace("postgresql://", "postgresql+psycopg://")
    )

    async with engine.begin() as conn:
        await conn.execute(
            text("DROP TYPE IF EXISTS money_market_protocol_enum CASCADE;")
        )
        await conn.execute(
            text("DROP TYPE IF EXISTS money_market_data_source_enum CASCADE;")
        )
        await conn.execute(
            text("DROP TYPE IF EXISTS money_market_comparison_type_enum CASCADE;")
        )
        await conn.execute(
            text("DROP TYPE IF EXISTS money_market_alert_condition_enum CASCADE;")
        )
        await conn.execute(
            text("DROP TYPE IF EXISTS money_market_notification_channel_enum CASCADE;")
        )
        print("✅ Dropped all money_market ENUMs")

    await engine.dispose()


if __name__ == "__main__":
    from sqlalchemy import text

    asyncio.run(drop_enums())
