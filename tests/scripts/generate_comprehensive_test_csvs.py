#!/usr/bin/env python3
"""
Generate comprehensive CSV test results by running real API calls through the test app.
Covers: shortcuts, Hunter AI, ULTRA, Agent Squad, general questions, multi-step flows.
"""
import asyncio
import sys
import os
import csv
from typing import List, Dict, Any
from time import time

# Setup path
sys.path.insert(0, '/home/ubuntu/anvil_backend')
os.chdir('/home/ubuntu/anvil_backend')

from httpx import AsyncClient, ASGITransport
from app.setup.config.settings import load_settings, AppSettings
from app.setup.config.database import PostgresSettings
from app.setup.ioc.provider_registry import get_providers
from app.setup.ioc.testing import get_integration_test_providers
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from app.setup.app_factory import create_app, configure_app
from app.presentation.http.controllers.root_router import create_root_router


async def create_test_app():
    """Create test app instance with database schema initialization."""
    # Set API keys
    os.environ["VERTEX_AI_API_KEY"] = "test_vertex_key"
    os.environ["DEEPINFRA_API_KEY"] = "test_deepinfra_key"
    os.environ["OPENAI_API_KEY"] = "test_openai_key"
    os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key"

    # Initialize SQLAlchemy mappings for domain entities
    from app.infrastructure.persistence_sqla.mappings.all import map_tables
    from app.infrastructure.persistence_sqla.registry import mapping_registry
    from sqlalchemy import create_engine

    # Map all domain entities to database tables
    map_tables()

    # Create PostgreSQL test database engine and create all tables
    engine = create_engine(
        "postgresql+psycopg://postgres:changethis@localhost:5432/anvil_test",
        pool_pre_ping=True,
        echo=False
    )

    # Create all tables from SQLAlchemy mappings
    mapping_registry.metadata.create_all(engine)
    print("✓ Database schema created from SQLAlchemy mappings")

    # Load settings
    original_settings = load_settings()

    # Create test database settings
    test_postgres = PostgresSettings(
        USER=original_settings.postgres.user,
        PASSWORD=original_settings.postgres.password,
        DB="anvil_test",  # Use test database
        HOST=original_settings.postgres.host,
        PORT=original_settings.postgres.port,
        DRIVER=original_settings.postgres.driver,
    )

    # Create test app settings
    test_settings = AppSettings(
        postgres=test_postgres,
        sqla=original_settings.sqla,
        security=original_settings.security,
        logs=original_settings.logs,
        admin=original_settings.admin,
        mailgun=original_settings.mailgun,
        stripe=original_settings.stripe,
        privy=original_settings.privy,
        integrations=original_settings.integrations,
        mcp=original_settings.mcp,
        agno=original_settings.agno,
        projects=original_settings.projects,
        distillation=original_settings.distillation,
        agent_squad=original_settings.agent_squad,
        transaction_confirmation=original_settings.transaction_confirmation,
        translation=original_settings.translation,
    )

    # Create app
    app = create_app()
    configure_app(app=app, root_router=create_root_router())

    # Create container with test providers
    container = make_async_container(
        *get_providers(),
        *get_integration_test_providers(),
        context={AppSettings: test_settings},
    )

    setup_dishka(container=container, app=app)

    return app, container


# Test data definitions
GUEST_TEST_QUERIES = [
    # === GENERAL INFORMATIONAL QUERIES ===
    ("What is Bitcoin?", "en", "NO"),
    ("What is Ethereum?", "en", "NO"),
    ("What is DeFi?", "en", "NO"),
    ("What is USDC?", "en", "NO"),

    # === HUNTER AI - PRICE PREDICTIONS ===
    ("What is the price of Bitcoin?", "en", "NO"),
    ("How much is Ethereum?", "en", "NO"),
    ("ETH price", "en", "NO"),
    ("BTC price prediction", "en", "NO"),
    ("What are the prices of BTC and ETH?", "en", "NO"),

    # === HUNTER AI - SENTIMENT ANALYSIS ===
    ("What do people think about Bitcoin?", "en", "NO"),
    ("Bitcoin sentiment", "en", "NO"),
    ("ETH sentiment analysis", "en", "NO"),

    # === SHORTCUTS - LENDING ===
    ("Deposit USDC on Morpho", "en", "YES"),
    ("Show best lending vaults", "en", "NO"),
    ("Earn yield on my ETH", "en", "YES"),
    ("Best lending vaults", "en", "NO"),

    # === SHORTCUTS - SWAP ===
    ("Swap 100 USDC for ETH", "en", "YES"),
    ("Swap USDC from Ethereum to Base", "en", "YES"),
    ("Best swap rate for ETH to USDC", "en", "NO"),
    ("Swap BTC to ETH", "en", "YES"),

    # === SHORTCUTS - PORTFOLIO ===
    ("Show my portfolio", "en", "NO"),
    ("What tokens do I have?", "en", "NO"),
    ("List my holdings", "en", "NO"),

    # === SHORTCUTS - BALANCE ===
    ("What's my balance?", "en", "NO"),
    ("Check my balance", "en", "NO"),
    ("Show my USDC balance", "en", "NO"),

    # === SHORTCUTS - ACTIVITY ===
    ("Show my transactions", "en", "NO"),
    ("Recent activity", "en", "NO"),
    ("Transaction history", "en", "NO"),

    # === SHORTCUTS - RECEIVE ===
    ("I want to receive crypto", "en", "NO"),
    ("My wallet address", "en", "NO"),
    ("Give me my QR code", "en", "NO"),

    # === SHORTCUTS - BUY ===
    ("I want to buy crypto", "en", "YES"),
    ("Buy Bitcoin with card", "en", "YES"),
    ("How to buy ETH", "en", "YES"),

    # === SHORTCUTS - SEND ===
    ("Send crypto to a friend", "en", "YES"),
    ("Transfer ETH to another wallet", "en", "YES"),
    ("I want to send USDC", "en", "YES"),

    # === MULTI-LANGUAGE SUPPORT ===
    ("¿Cuál es el precio de Bitcoin?", "es", "NO"),
    ("O que é Ethereum?", "pt", "NO"),
    ("什么是比特币?", "zh", "NO"),
    ("Échanger 100 USDC contre ETH", "fr", "YES"),

    # === EDGE CASES ===
    ("What is UNKNOWNTOKEN123?", "en", "NO"),
    ("what is BITCOIN?", "en", "NO"),
    ("Waht is Etherem?", "en", "NO"),

    # === OUT OF SCOPE ===
    ("What's the weather today?", "en", "NO"),
    ("Tell me a joke", "en", "NO"),
]

AUTH_TEST_QUERIES = [
    # === GENERAL INFORMATIONAL QUERIES ===
    ("What is Bitcoin?", "en", "NO"),
    ("What is Ethereum?", "en", "NO"),
    ("What is DeFi?", "en", "NO"),
    ("What is USDC?", "en", "NO"),

    # === HUNTER AI - PRICE PREDICTIONS ===
    ("What is the price of Bitcoin?", "en", "NO"),
    ("How much is Ethereum?", "en", "NO"),
    ("ETH price", "en", "NO"),
    ("BTC price prediction", "en", "NO"),
    ("What are the prices of BTC and ETH?", "en", "NO"),

    # === HUNTER AI - SENTIMENT ANALYSIS ===
    ("What do people think about Bitcoin?", "en", "NO"),
    ("Bitcoin sentiment", "en", "NO"),
    ("ETH sentiment analysis", "en", "NO"),

    # === SHORTCUTS - LENDING (MULTI-STEP) ===
    ("Deposit USDC on Morpho", "en", "YES"),
    ("Show best lending vaults", "en", "NO"),
    ("Earn yield on my ETH", "en", "YES"),

    # === SHORTCUTS - SWAP (MULTI-STEP) ===
    ("Swap 100 USDC for ETH", "en", "YES"),
    ("Swap USDC from Ethereum to Base", "en", "YES"),
    ("Best swap rate for ETH to USDC", "en", "NO"),

    # === SHORTCUTS - PORTFOLIO ===
    ("Show my portfolio", "en", "NO"),
    ("What tokens do I have?", "en", "NO"),
    ("List my holdings", "en", "NO"),

    # === SHORTCUTS - BALANCE ===
    ("What's my balance?", "en", "NO"),
    ("Check my balance", "en", "NO"),
    ("Show my USDC balance", "en", "NO"),

    # === SHORTCUTS - ACTIVITY ===
    ("Show my transactions", "en", "NO"),
    ("Recent activity", "en", "NO"),
    ("Transaction history", "en", "NO"),

    # === SHORTCUTS - RECEIVE ===
    ("I want to receive crypto", "en", "NO"),
    ("My wallet address", "en", "NO"),
    ("Give me my QR code", "en", "NO"),

    # === SHORTCUTS - BUY (MULTI-STEP) ===
    ("I want to buy crypto", "en", "YES"),
    ("Buy Bitcoin with card", "en", "YES"),
    ("How to buy ETH", "en", "YES"),

    # === SHORTCUTS - SEND (MULTI-STEP) ===
    ("Send crypto to a friend", "en", "YES"),
    ("Transfer ETH to another wallet", "en", "YES"),
    ("I want to send USDC", "en", "YES"),

    # === SHORTCUTS - MONEY MARKET ===
    ("Compare Aave vs Compound", "en", "NO"),
    ("Best money market rates for USDC", "en", "NO"),
    ("Compare lending rates for ETH", "en", "NO"),

    # === MULTI-LANGUAGE SUPPORT ===
    ("¿Cuál es el precio de Bitcoin?", "es", "NO"),
    ("O que é Ethereum?", "pt", "NO"),
    ("什么是比特币?", "zh", "NO"),
    ("Échanger 100 USDC contre ETH", "fr", "YES"),

    # === EDGE CASES ===
    ("What is UNKNOWNTOKEN123?", "en", "NO"),
    ("what is BITCOIN?", "en", "NO"),
    ("Waht is Etherem?", "en", "NO"),
]


async def run_guest_queries(app, container) -> List[Dict[str, Any]]:
    """Run guest queries and capture results."""
    results = []

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for i, (query, language, is_multi_step) in enumerate(GUEST_TEST_QUERIES, 1):
            print(f"[{i}/{len(GUEST_TEST_QUERIES)}] Guest: {query[:50]}... ({language})")
            try:
                # Add delay between requests to avoid rate limiting
                # Guest users: 20 msg/hour = 0.33/min = 180sec per msg
                # We use 1 second which is safe for 47 tests
                if i > 1:
                    await asyncio.sleep(1.0)

                response = await client.post(
                    "/api/v1/guest/chat",
                    json={"content": query, "language": language}
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    content = data.get('agent_message', {}).get('content', '')
                    # Truncate for CSV
                    if len(content) > 300:
                        content = content[:297] + "..."

                    results.append({
                        'Type': 'query',
                        'device': 'pytest',
                        'is_multi_step': is_multi_step,
                        'input_1': query,
                        'output_1': content,
                        'input_2': '',
                        'output_2': '',
                        'input_3': '',
                        'output_3': '',
                        'input_4': '',
                        'output_4': '',
                        'test_pass': 'PASS'
                    })
                else:
                    results.append({
                        'Type': 'query',
                        'device': 'pytest',
                        'is_multi_step': is_multi_step,
                        'input_1': query,
                        'output_1': f'Error: HTTP {response.status_code}',
                        'input_2': '',
                        'output_2': '',
                        'input_3': '',
                        'output_3': '',
                        'input_4': '',
                        'output_4': '',
                        'test_pass': 'FAIL'
                    })
            except Exception as e:
                print(f"Error: {e}")
                results.append({
                    'Type': 'query',
                    'device': 'pytest',
                    'is_multi_step': is_multi_step,
                    'input_1': query,
                    'output_1': f'Error: {str(e)}',
                    'input_2': '',
                    'output_2': '',
                    'input_3': '',
                    'output_3': '',
                    'input_4': '',
                    'output_4': '',
                    'test_pass': 'FAIL'
                })

    return results


async def run_auth_queries(app, container) -> List[Dict[str, Any]]:
    """Run authenticated user queries and capture results with rate limit handling."""
    results = []

    # Create authenticated user in database to get proper rate limits (200/hour vs 20/hour for guest)
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    from uuid import uuid4

    async_engine = create_async_engine(
        "postgresql+asyncpg://postgres:changethis@localhost:5432/anvil_test",
        pool_pre_ping=True,
        echo=False
    )
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create authenticated user in chat_users table
    auth_user_id = None
    async with async_session_maker() as session:
        try:
            result = await session.execute(
                text("""
                    INSERT INTO chat_users (user_type, identifier, email, preferred_language)
                    VALUES (:user_type, :identifier, :email, :language)
                    ON CONFLICT (user_type, identifier) DO UPDATE SET email = EXCLUDED.email
                    RETURNING id
                """),
                {
                    "user_type": "premium",  # Use premium to avoid rate limits
                    "identifier": "1",  # Test user ID
                    "email": "test@example.com",
                    "language": "en"
                }
            )
            auth_user_id = result.scalar_one()
            await session.commit()
            print(f"✓ Created premium user in database: {auth_user_id} (unlimited rate limits)")
        except Exception as e:
            print(f"  ⚠ Failed to create authenticated user: {e}")
            await session.rollback()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Auth headers
        auth_headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJ0ZXN0LXNlc3Npb24iLCJleHAiOjk5OTk5OTk5OTl9.test",
            "Content-Type": "application/json"
        }

        # Create initial conversation
        conversation_id = None
        try:
            resp = await client.post(
                "/api/v1/conversations",
                headers=auth_headers,
                json={"title": "Comprehensive Test Conversation"}
            )
            conversation_id = resp.json()["id"]
            print(f"✓ Created conversation: {conversation_id}")
        except Exception as e:
            print(f"Failed to create conversation: {e}")
            return results

        for i, (query, language, is_multi_step) in enumerate(AUTH_TEST_QUERIES, 1):
            print(f"[{i}/{len(AUTH_TEST_QUERIES)}] Auth: {query[:50]}... ({language})")

            # Create new conversation every 15 queries to reset rate limits
            if i > 1 and (i - 1) % 15 == 0:
                try:
                    resp = await client.post(
                        "/api/v1/conversations",
                        headers=auth_headers,
                        json={"title": f"Test Conversation {i}"}
                    )
                    conversation_id = resp.json()["id"]
                    print(f"  ✓ Created new conversation: {conversation_id}")
                    # Add extra delay after creating new conversation
                    await asyncio.sleep(1.0)
                except Exception as e:
                    print(f"  ⚠ Failed to create new conversation: {e}")

            try:
                # Add delay between requests to avoid rate limiting
                # Authenticated users: 200 msg/hour = 3.33/min = 18sec per msg
                # We use 3 seconds as a safer interval
                if i > 1:
                    await asyncio.sleep(3.0)

                response = await client.post(
                    f"/api/v1/conversations/{conversation_id}/messages",
                    headers=auth_headers,
                    json={"content": query, "language": language}
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    content = data.get('agent_message', {}).get('content', '')
                    # Truncate for CSV
                    if len(content) > 300:
                        content = content[:297] + "..."

                    results.append({
                        'Type': 'query',
                        'device': 'pytest',
                        'is_multi_step': is_multi_step,
                        'input_1': query,
                        'output_1': content,
                        'input_2': '',
                        'output_2': '',
                        'input_3': '',
                        'output_3': '',
                        'input_4': '',
                        'output_4': '',
                        'test_pass': 'PASS'
                    })
                else:
                    results.append({
                        'Type': 'query',
                        'device': 'pytest',
                        'is_multi_step': is_multi_step,
                        'input_1': query,
                        'output_1': f'Error: HTTP {response.status_code}',
                        'input_2': '',
                        'output_2': '',
                        'input_3': '',
                        'output_3': '',
                        'input_4': '',
                        'output_4': '',
                        'test_pass': 'FAIL'
                    })
            except Exception as e:
                print(f"Error: {e}")
                results.append({
                    'Type': 'query',
                    'device': 'pytest',
                    'is_multi_step': is_multi_step,
                    'input_1': query,
                    'output_1': f'Error: {str(e)}',
                    'input_2': '',
                    'output_2': '',
                    'input_3': '',
                    'output_3': '',
                    'input_4': '',
                    'output_4': '',
                    'test_pass': 'FAIL'
                })

    return results


def write_csv(filename: str, results: List[Dict[str, Any]]):
    """Write results to CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            'Type', 'device', 'is multi step',
            'input 1', 'output 1',
            'input 2', 'output 2',
            'input 3', 'output 3',
            'input 4', 'output 4',
            'test pass'
        ])
        # Data rows
        for result in results:
            writer.writerow([
                result['Type'],
                result['device'],
                result['is_multi_step'],
                result['input_1'],
                result['output_1'],
                result['input_2'],
                result['output_2'],
                result['input_3'],
                result['output_3'],
                result['input_4'],
                result['output_4'],
                result['test_pass']
            ])

    # Count pass/fail
    pass_count = sum(1 for r in results if r['test_pass'] == 'PASS')
    fail_count = sum(1 for r in results if r['test_pass'] == 'FAIL')

    print(f"✓ Written {len(results)} results to {filename}")
    print(f"  PASS: {pass_count}, FAIL: {fail_count}")


async def main():
    """Main execution."""
    print("=" * 70)
    print("GENERATING COMPREHENSIVE TEST CSV FILES")
    print("=" * 70)

    # Create test app once for both guest and auth queries
    print("\nInitializing test application...")
    app, container = await create_test_app()

    print(f"\n[1/2] Running Guest Queries ({len(GUEST_TEST_QUERIES)} tests)...")
    guest_results = await run_guest_queries(app, container)
    write_csv('docs/output/guest.csv', guest_results)

    print(f"\n[2/2] Running Authenticated User Queries ({len(AUTH_TEST_QUERIES)} tests)...")
    auth_results = await run_auth_queries(app, container)
    write_csv('docs/output/log-user.csv', auth_results)

    # Close container
    await container.close()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Guest queries: {len(guest_results)}")
    print(f"Auth queries: {len(auth_results)}")
    print(f"Total: {len(guest_results) + len(auth_results)}")
    print(f"\nFiles created:")
    print(f"  - docs/output/guest.csv")
    print(f"  - docs/output/log-user.csv")

    # Cleanup: Drop all tables after execution
    from app.infrastructure.persistence_sqla.registry import mapping_registry
    from sqlalchemy import create_engine

    engine = create_engine(
        "postgresql+psycopg://postgres:changethis@localhost:5432/anvil_test",
        pool_pre_ping=True,
        echo=False
    )
    mapping_registry.metadata.drop_all(engine)
    engine.dispose()
    print("\n✓ Database cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())
