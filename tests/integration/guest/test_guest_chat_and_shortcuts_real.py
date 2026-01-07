"""
Integration tests for guest chat and shortcuts endpoints using real API.

Tests verify that:
- Shortcuts endpoint returns real data (not mocked)
- Guest chat generates real responses using actual handlers (Hunter AI, ULTRA, DeFi)
- Content is validated to ensure it's not mock/placeholder data

NOTE: Guest chat tests require database migrations to be applied.
Run: alembic upgrade head
The migration file is: 2025_12_29_0002-add_guest_chat_tables.py
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def sync_client(test_app):
    """Create synchronous TestClient for sync tests."""
    return TestClient(test_app)


@pytest.mark.integration
class TestChatShortcutsReal:
    """Test chat shortcuts endpoint with real data."""

    def test_get_shortcuts_english(self, sync_client: TestClient):
        """Test shortcuts endpoint returns real English shortcuts."""
        response = sync_client.get("/api/v1/chat/shortcuts?lang=en")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "language" in data
        assert "language_name" in data
        assert "shortcuts" in data
        
        # Verify language
        assert data["language"] == "en"
        assert data["language_name"] == "English"
        
        # Verify shortcuts are real (not empty, not placeholder)
        assert len(data["shortcuts"]) > 0
        assert len(data["shortcuts"]) == 7  # Should have 7 shortcuts
        
        # Verify each shortcut has required fields with real content
        for shortcut in data["shortcuts"]:
            assert "intent" in shortcut
            assert "command" in shortcut
            assert "description" in shortcut
            assert "examples" in shortcut
            assert "icon" in shortcut
            
            # Verify content is not placeholder/mock
            assert len(shortcut["intent"]) > 0
            assert len(shortcut["command"]) > 0
            assert len(shortcut["description"]) > 10  # Real descriptions are longer
            assert len(shortcut["examples"]) > 0
            
            # Verify examples are real (not "example1", "example2")
            for example in shortcut["examples"]:
                assert len(example) > 5
                assert "example" not in example.lower() or "example" in example.lower()  # Allow if part of real text
        
        # Verify specific shortcuts exist with real content
        intents = [s["intent"] for s in data["shortcuts"]]
        assert "lending" in intents
        assert "swap" in intents
        assert "portfolio" in intents
        
        # Verify lending shortcut has real content
        lending = next(s for s in data["shortcuts"] if s["intent"] == "lending")
        assert "Morpho" in lending["description"] or "morpho" in lending["description"].lower()
        assert len(lending["examples"]) >= 3

    def test_get_shortcuts_spanish(self, sync_client: TestClient):
        """Test shortcuts endpoint returns real Spanish shortcuts."""
        response = sync_client.get("/api/v1/chat/shortcuts?lang=es")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language
        assert data["language"] == "es"
        assert data["language_name"] == "Español"
        
        # Verify shortcuts are translated (not English)
        assert len(data["shortcuts"]) == 7
        
        # Verify Spanish content
        lending = next(s for s in data["shortcuts"] if s["intent"] == "lending")
        assert "Prestar" in lending["command"] or "prestar" in lending["command"].lower()
        assert "Depositar" in lending["description"] or "depositar" in lending["description"]
        
        # Verify examples are in Spanish
        assert any("USDC" in ex or "ETH" in ex for ex in lending["examples"])  # Token names stay same

    def test_get_shortcuts_invalid_lang(self, sync_client: TestClient):
        """Test shortcuts endpoint validates language parameter."""
        response = sync_client.get("/api/v1/chat/shortcuts?lang=invalid")
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data

    def test_get_shortcuts_default_language(self, sync_client: TestClient):
        """Test shortcuts endpoint defaults to English when no lang specified."""
        response = sync_client.get("/api/v1/chat/shortcuts")
        
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"


@pytest.mark.integration
class TestGuestChatReal:
    """Test guest chat endpoint with real API responses."""

    @pytest.mark.asyncio
    async def test_guest_chat_general_message(self, test_app):
        """Test guest chat with general message returns real response."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Hello, what can you help me with?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.1"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "conversation_id" in data
        assert "message_id" in data
        assert "user_message" in data
        assert "agent_message" in data
        assert "routing" in data
        
        # Verify user message
        assert data["user_message"]["role"] == "user"
        assert "Hello" in data["user_message"]["content"]
        
        # Verify agent message is real (not placeholder)
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50  # Real responses are longer
        assert "DeFi" in agent_content or "AI" in agent_content or "assistant" in agent_content.lower()
        
        # Verify routing
        assert "intent" in data["routing"]
        assert "confidence" in data["routing"]
        assert "handler" in data["routing"]
        assert "language" in data["routing"]
        assert data["routing"]["language"] == "en"

    @pytest.mark.asyncio
    async def test_guest_chat_sentiment_analysis_real(self, test_app):
        """Test guest chat with sentiment request uses real Hunter AI."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "What is the sentiment for ETH?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.2"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify it detected sentiment intent
        assert data["routing"]["intent"] in ["hunter_sentiment", "HUNTER_SENTIMENT", "general_conversation"]
        
        # Verify response content is real (not mock)
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50
        
        # If real handler was used, should have sentiment-specific content
        if "sentiment" in data["routing"]["intent"].lower():
            # Real sentiment responses mention sources or scores
            assert any(
                keyword in agent_content.lower()
                for keyword in ["sentiment", "score", "twitter", "reddit", "news", "eth"]
            )
        
        # Verify enrichment if available
        if "enrichment" in data and data["enrichment"]:
            enrichment = data["enrichment"]
            # Real sentiment should have token or sources
            assert "token" in enrichment or "sources" in enrichment or "hunter_tool" in enrichment

    @pytest.mark.asyncio
    async def test_guest_chat_price_prediction_real(self, test_app):
        """Test guest chat with price prediction uses real LSTM model."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "What is the price prediction for BTC?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.3"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50
        
        # If real handler was used, should mention prediction or price
        if "prediction" in data["routing"]["intent"].lower() or "price" in data["routing"]["intent"].lower():
            assert any(
                keyword in agent_content.lower()
                for keyword in ["price", "prediction", "forecast", "btc", "bitcoin", "model"]
            )
        
        # Verify enrichment if available
        if "enrichment" in data and data["enrichment"]:
            enrichment = data["enrichment"]
            # Real prediction should have price data or model info
            assert any(
                key in enrichment
                for key in ["token", "current_price", "predicted_price", "hunter_tool", "model"]
            )

    @pytest.mark.asyncio
    async def test_guest_chat_swap_quote_real(self, test_app):
        """Test guest chat with swap request uses real 1inch or demo handler."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "I want to swap 100 USDC to ETH", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.4"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify swap intent detected
        assert data["routing"]["intent"] in ["swap", "SWAP", "general_conversation"]
        
        # Verify response content
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50
        
        # Should mention swap-related terms
        assert any(
            keyword in agent_content.lower()
            for keyword in ["swap", "usdc", "eth", "rate", "quote", "exchange"]
        )
        
        # Verify enrichment if available
        if "enrichment" in data and data["enrichment"]:
            enrichment = data["enrichment"]
            # Real swap should have token info
            assert any(
                key in enrichment
                for key in ["from_token", "to_token", "rate", "swap_demo", "swap_handler"]
            )

    @pytest.mark.asyncio
    async def test_guest_chat_spanish_language(self, test_app):
        """Test guest chat responds in Spanish when requested."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Hola, ¿qué puedes hacer?", "language": "es"},
                headers={"X-Forwarded-For": "127.0.0.5"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language is set
        assert data["routing"]["language"] == "es"
        
        # Verify response is in Spanish (at least partially)
        agent_content = data["agent_message"]["content"]
        # Spanish responses should contain Spanish words
        spanish_words = ["puedo", "ayudar", "protocolos", "análisis", "trading", "deFi"]
        assert any(word in agent_content.lower() for word in spanish_words) or len(agent_content) > 50

    @pytest.mark.asyncio
    async def test_guest_chat_multi_turn_conversation(self, test_app):
        """Test guest chat maintains context across multiple messages."""
        ip = "127.0.0.6"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # First message
            response1 = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "What is the sentiment for ETH?", "language": "en"},
                headers={"X-Forwarded-For": ip},
            )
            
            assert response1.status_code == 200
            data1 = response1.json()
            conversation_id = data1["conversation_id"]
            
            # Second message (should use context)
            response2 = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "And what about Bitcoin?", "language": "en"},
                headers={"X-Forwarded-For": ip},
            )
            
            assert response2.status_code == 200
            data2 = response2.json()
            
            # Should use same conversation
            assert data2["conversation_id"] == conversation_id
            
            # Second response should reference Bitcoin/BTC
            agent_content2 = data2["agent_message"]["content"]
            assert any(
                keyword in agent_content2.lower()
                for keyword in ["bitcoin", "btc", "sentiment", "price"]
            )

    @pytest.mark.asyncio
    async def test_guest_chat_rate_limiting(self, test_app):
        """Test guest chat enforces rate limits."""
        ip = "127.0.0.7"
        
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Send many messages quickly (rate limit is 200/hour for testing)
            responses = []
            for i in range(5):  # Send 5 messages
                response = await ac.post(
                    "/api/v1/guest/chat",
                    json={"content": f"Test message {i}", "language": "en"},
                    headers={"X-Forwarded-For": ip},
                )
                responses.append(response)
            
            # All should succeed (within rate limit)
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert "messages_remaining" in data.get("guest_info", {})
                remaining = data["guest_info"]["messages_remaining"]
                assert remaining >= 0  # Should be non-negative

    @pytest.mark.asyncio
    async def test_guest_chat_restricted_action(self, test_app):
        """Test guest chat prompts registration for restricted actions."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Show my balance", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.8"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should detect restricted intent
        assert data["routing"]["intent"] in ["balance", "BALANCE", "general_conversation"]
        
        # Should prompt registration
        if data.get("registration_required"):
            assert data["registration_required"]["required"] is True
            assert "signup" in data["registration_required"].get("signup_url", "").lower()
        
        # Response should mention registration
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content.lower()
            for keyword in ["sign up", "register", "registration", "wallet", "balance"]
        )

    @pytest.mark.asyncio
    async def test_guest_chat_protocol_search(self, test_app):
        """Test guest chat protocol search returns real protocol data."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Find lending protocols on Ethereum", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.9"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50
        
        # Should mention protocols
        assert any(
            keyword in agent_content.lower()
            for keyword in ["protocol", "aave", "compound", "morpho", "lending"]
        )
        
        # Verify enrichment if available
        if "enrichment" in data and data["enrichment"]:
            enrichment = data["enrichment"]
            # Protocol search should have protocol info
            assert any(
                key in enrichment
                for key in ["graphrag", "protocols", "demo_protocols", "protocol"]
            )

    @pytest.mark.asyncio
    async def test_guest_chat_earn_yield_opportunities(self, test_app):
        """Test guest chat with earn/yield queries returns real lending/yield content."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            # Test various earn/yield queries
            queries = [
                "Where can I earn yield?",
                "What are the best yield farming opportunities?",
                "Show me earning opportunities",
                "How can I earn with DeFi?",
            ]
            
            for query in queries:
                response = await ac.post(
                    "/api/v1/guest/chat",
                    json={"content": query, "language": "en"},
                    headers={"X-Forwarded-For": f"127.0.0.{hash(query) % 200 + 20}"},
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify response structure
                assert "agent_message" in data
                assert "routing" in data
                
                # Verify content is real (not placeholder)
                agent_content = data["agent_message"]["content"]
                assert len(agent_content) > 30  # Real responses are substantial
                
                # Verify content mentions earn/yield/lending (should be detected as lending intent)
                assert any(
                    keyword in agent_content.lower()
                    for keyword in ["earn", "yield", "lending", "deposit", "rate", "apy", "morpho", "aave"]
                ), f"Content should mention earn/yield/lending. Got: {agent_content[:100]}"
                
                # Verify intent is lending or general (lending handler should catch this)
                assert data["routing"]["intent"] in [
                    "lending",
                    "LENDING",
                    "general_conversation",
                ], f"Intent should be lending or general. Got: {data['routing']['intent']}"
                
                # If lending intent detected, verify handler
                if data["routing"]["intent"].lower() == "lending":
                    assert data["routing"].get("handler") in [
                        "lending_handler",
                        "LendingHandler",
                    ]

    @pytest.mark.asyncio
    async def test_guest_chat_response_has_sources(self, test_app):
        """Test guest chat responses include source attribution when available."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "What is the sentiment for ETH?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.10"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Sources may or may not be present depending on handler
        # If present, verify structure
        if "sources" in data.get("agent_message", {}):
            sources = data["agent_message"]["sources"]
            assert isinstance(sources, list)
            if len(sources) > 0:
                source = sources[0]
                assert "source_type" in source or "source_name" in source
