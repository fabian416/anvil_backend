#!/usr/bin/env python3
"""
Script to get user token and generate test file for authenticated user shortcuts.

This script:
1. Gets access token for ops@anvilcrypto.com from database
2. Generates tests/integration/user/test_user_shortcuts_examples.py
   based on test_all_shortcuts_examples.py but for authenticated users

Usage:
    python scripts/generate_user_tests.py
"""

import asyncio
import sys
import os
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.infrastructure.persistence_sqla.mappings.all import map_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry
from app.setup.config.settings import load_settings
from app.infrastructure.auth.session.service import AuthSessionService
from app.infrastructure.auth.session.id_generator_str import StrAuthSessionIdGenerator
from app.infrastructure.auth.session.timer_utc import UtcAuthSessionTimer
from app.infrastructure.auth.refresh_token.generator import RefreshTokenGenerator
from app.infrastructure.auth.adapters.data_mapper_sqla import SqlaAuthSessionDataMapper
from app.infrastructure.auth.adapters.transaction_manager_sqla import (
    SqlaAuthSessionTransactionManager,
)
from app.presentation.http.auth.access_token_processor_jwt import (
    JwtAccessTokenProcessor,
)
from app.infrastructure.auth.session.model import AuthSession
from app.domain.value_objects.user_id import UserId
from app.setup.config.security import SecuritySettings


async def get_or_create_token(email: str) -> str | None:
    """Get or create access token for user."""
    settings = load_settings()
    database_url = settings.postgres.dsn

    map_tables()

    engine = create_async_engine(database_url, echo=False)
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        users_table = mapping_registry.metadata.tables.get("users")
        sessions_table = mapping_registry.metadata.tables.get("sessions")

        if users_table is None or sessions_table is None:
            await engine.dispose()
            return None

        # Find user
        stmt = select(users_table.c.id).where(users_table.c.email == email)
        result = await session.execute(stmt)
        user_row = result.first()

        if not user_row:
            print(f"❌ User {email} not found")
            await engine.dispose()
            return None

        user_id = user_row.id
        print(f"✓ Found user: {email} (ID: {user_id})")

        # Try to get existing token
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
            token = token_row.access_token
            print(f"✓ Found existing token")
            await engine.dispose()
            return token

        # Create new session
        print("⚠️  Creating new session...")

        # Get security settings from loaded config
        settings = load_settings()
        security_settings = settings.security

        jwt_processor = JwtAccessTokenProcessor(
            secret=security_settings.auth.jwt_secret,
            algorithm=security_settings.auth.jwt_algorithm,
        )

        session_id_gen = StrAuthSessionIdGenerator()
        session_timer = UtcAuthSessionTimer(
            auth_session_ttl_min=security_settings.auth.session_ttl_min,
            auth_session_refresh_threshold=security_settings.auth.session_refresh_threshold,
        )
        refresh_gen = RefreshTokenGenerator()

        session_id = session_id_gen()
        expiration = session_timer.auth_session_expiration  # Property, not method
        refresh_token = refresh_gen()

        auth_session = AuthSession(
            id_=session_id,
            user_id=UserId(value=user_id),
            expiration=expiration,
            refresh_token=refresh_token,
        )

        access_token = jwt_processor.encode(auth_session)

        # Save to auth_sessions
        auth_mapper = SqlaAuthSessionDataMapper(session)
        auth_mapper.add(auth_session)

        # Save to sessions table
        from datetime import datetime

        insert_stmt = sessions_table.insert().values(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_at=expiration,
            is_active=True,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
        )
        await session.execute(insert_stmt)
        await session.commit()

        print(f"✓ Created new token")
        await engine.dispose()
        return access_token


def generate_test_file(token: str) -> str:
    """Generate test file content with embedded token."""
    # Template with placeholders that will be replaced
    template = '''"""
Integration Test: Verify All Shortcut Examples Work for Authenticated Users

Tests all examples from the shortcuts endpoint for authenticated users to ensure:
1. Intent detection works correctly
2. Responses are not generic fallback messages
3. All shortcuts provide meaningful responses
4. Uses real access token from database (ops@anvilcrypto.com)

Follows CTO Engineering Framework methodology.
Based on test_all_shortcuts_examples.py but for authenticated users.

Generated by scripts/generate_user_tests.py
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from uuid import uuid4

from app.run import make_app

# Access token for ops@anvilcrypto.com (embedded from database)
ACCESS_TOKEN = "{ACCESS_TOKEN}"

# Generic fallback message that should NOT appear
GENERIC_FALLBACK_MESSAGE = (
    "I'm your AI assistant for DeFi! I can help with market analysis (Hunter AI), "
    "automated trading (ULTRA), lending rates, swaps, and more. "
    "Ask me about protocols, yields, risks, or how to get started. "
    "Sign up for full access to all features."
)


@pytest_asyncio.fixture
async def client():
    """Create test client."""
    app = make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def conversation_id(client: AsyncClient):
    """Create or get conversation for authenticated user."""
    # Try to get existing conversation first
    response = await client.get(
        "/api/v1/user/chat/conversations",
        headers={{"Authorization": f"Bearer {{ACCESS_TOKEN}}"},
    )
    
    if response.status_code == 200:
        conversations = response.json()
        if conversations and len(conversations) > 0:
            return conversations[0]["id"]
    
    # Create new conversation
    response = await client.post(
        "/api/v1/user/chat/conversations",
        json={"title": "Test Conversation", "language": "en"},
        headers={{"Authorization": f"Bearer {{ACCESS_TOKEN}}"},
    )
    
    if response.status_code == 201:
        return response.json()["id"]
    
    # Fallback: generate UUID (will be auto-created by endpoint)
    return str(uuid4())


@pytest_asyncio.fixture
async def shortcuts_data(client: AsyncClient):
    """Fetch shortcuts data from API."""
    response = await client.get("/api/v1/chat/shortcuts?lang=en")
    assert response.status_code == 200
    data = response.json()
    return data["shortcuts"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_user_shortcut_examples_detect_correct_intent(
    client: AsyncClient,
    shortcuts_data: list,
    conversation_id: str,
):
    """
    Test that all shortcut examples detect the correct intent for authenticated users.
    
    CTO Framework: Verification Phase
    - Verify intent detection accuracy for authenticated users
    - Ensure no false positives/negatives
    """
    failures = []
    
    for shortcut in shortcuts_data:
        intent = shortcut["intent"]
        command = shortcut["command"]
        
        for example in shortcut["examples"]:
            response = await client.post(
                f"/api/v1/user/chat/conversations/{{conversation_id}}/messages",
                json={'content': example, 'language': 'en'},
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'},
            )
            
            assert response.status_code == 200, f"Failed for {{intent}}: {{example}}"
            data = response.json()
            
            detected_intent = data["routing"]["intent"]
            
            if detected_intent != intent:
                failures.append(
                    {{
                        "shortcut": command,
                        "intent": intent,
                        "example": example,
                        "detected": detected_intent,
                    }}
                )
    
    if failures:
        error_msg = "\\n".join(
            [
                f"❌ {{f['shortcut']}} ({{f['intent']}}): '{{f['example']}}' → detected as '{{f['detected']}}'"
                for f in failures
            ]
        )
        pytest.fail(f"Intent detection failures:\\n{{error_msg}}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_user_shortcut_examples_not_generic_fallback(
    client: AsyncClient,
    shortcuts_data: list,
    conversation_id: str,
):
    """
    Test that all shortcut examples return meaningful responses, not generic fallback.
    
    CTO Framework: Validation Phase
    - Verify responses are contextually relevant for authenticated users
    - Ensure no generic "I'm your AI assistant" messages
    """
    failures = []
    
    for shortcut in shortcuts_data:
        intent = shortcut["intent"]
        command = shortcut["command"]
        
        for example in shortcut["examples"]:
            response = await client.post(
                f"/api/v1/user/chat/conversations/{{conversation_id}}/messages",
                json={'content': example, 'language': 'en'},
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'},
            )
            
            assert response.status_code == 200, f"Failed for {{intent}}: {{example}}"
            data = response.json()
            
            content = data["agent_message"]["content"]
            
            # Check if response is generic fallback
            if GENERIC_FALLBACK_MESSAGE in content:
                failures.append(
                    {{
                        "shortcut": command,
                        "intent": intent,
                        "example": example,
                        "content_preview": content[:100],
                    }}
                )
    
    if failures:
        error_msg = "\\n".join(
            [
                f"❌ {{f['shortcut']}} ({{f['intent']}}): '{{f['example']}}' → Generic fallback detected"
                for f in failures
            ]
        )
        pytest.fail(f"Generic fallback detected for:\\n{{error_msg}}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_user_shortcut_examples_have_meaningful_content(
    client: AsyncClient,
    shortcuts_data: list,
    conversation_id: str,
):
    """
    Test that all shortcut examples return responses with meaningful content.
    
    CTO Framework: Quality Assurance Phase
    - Verify responses contain relevant information
    - Ensure minimum content length
    - Check for intent-specific keywords
    """
    failures = []
    
    # Intent-specific keywords that should appear in responses
    intent_keywords = {{
        "lending": ["lending", "vault", "yield", "morpho", "deposit"],
        "money_market": ["aave", "compound", "rate", "supply", "lending"],
        "swap": ["swap", "quote", "rate", "bridge", "exchange"],
        "portfolio": ["portfolio", "dashboard", "holdings", "assets", "tokens"],
        "balance": ["balance", "wallet", "account"],
        "activity": ["transaction", "history", "activity"],
        "receive": ["address", "wallet", "receive", "deposit"],
        "buy": ["buy", "crypto", "card"],
        "send": ["send", "transfer", "wallet"],
    }}
    
    for shortcut in shortcuts_data:
        intent = shortcut["intent"]
        command = shortcut["command"]
        
        for example in shortcut["examples"]:
            response = await client.post(
                f"/api/v1/user/chat/conversations/{{conversation_id}}/messages",
                json={'content': example, 'language': 'en'},
                headers={'Authorization': f'Bearer {ACCESS_TOKEN}'},
            )
            
            assert response.status_code == 200, f"Failed for {{intent}}: {{example}}"
            data = response.json()
            
            content = data["agent_message"]["content"].lower()
            
            # Check minimum content length
            if len(content) < 50:
                failures.append(
                    {{
                        "shortcut": command,
                        "intent": intent,
                        "example": example,
                        "issue": "Content too short",
                        "length": len(content),
                    }}
                )
                continue
            
            # Check for intent-specific keywords
            if intent in intent_keywords:
                keywords = intent_keywords[intent]
                found_keyword = any(keyword in content for keyword in keywords)
                
                if not found_keyword:
                    failures.append(
                        {{
                            "shortcut": command,
                            "intent": intent,
                            "example": example,
                            "issue": "No intent-specific keywords found",
                            "expected_keywords": keywords,
                            "content_preview": content[:150],
                        }}
                    )
    
    if failures:
        error_msg = "\\n".join(
            [
                f"❌ {{f['shortcut']}} ({{f['intent']}}): '{{f['example']}}' → {{f['issue']}}"
                for f in failures
            ]
        )
        pytest.fail(f"Content quality issues:\\n{{error_msg}}")
'''

    # Replace placeholder with actual token
    return template.replace("{ACCESS_TOKEN}", token)


async def main():
    """Main entry point."""
    email = "ops@anvilcrypto.com"
    print(f"Getting token for: {email}")

    token = await get_or_create_token(email)

    if not token:
        print("❌ Could not get or create token")
        sys.exit(1)

    print(f"✓ Token obtained: {token[:30]}...")

    # Generate test file
    test_content = generate_test_file(token)
    test_file_path = "tests/integration/user/test_user_shortcuts_examples.py"

    with open(test_file_path, "w") as f:
        f.write(test_content)

    print(f"\n✅ Generated test file: {test_file_path}")
    print(f"   Token embedded in file")
    print(f"\nRun tests with:")
    print(f"   pytest {test_file_path} -v")


if __name__ == "__main__":
    asyncio.run(main())
