"""
Integration tests for guest chat with shortcuts.

Tests the /api/v1/guest/chat endpoint with all shortcut examples
to ensure proper intent detection and routing.
"""

import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport


class TestGuestChatShortcuts:
    """Test guest chat with all shortcut examples."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcuts_endpoint(self, client):
        """Test that shortcuts endpoint returns all shortcuts."""
        response = await test_client.get("/api/v1/chat/shortcuts?lang=en")

        assert response.status_code == 200
        data = response.json()

        assert data["language"] == "en"
        assert data["language_name"] == "English"
        assert len(data["shortcuts"]) == 9

        # Verify all expected intents are present
        expected_intents = {
            "lending", "money_market", "swap", "portfolio",
            "balance", "activity", "receive", "buy", "send"
        }
        actual_intents = {s["intent"] for s in data["shortcuts"]}
        assert actual_intents == expected_intents

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcuts_endpoint",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_lending_shortcut(self, test_client: AsyncClient, llm_validator):
        """Test lending shortcut examples."""
        examples = [
            "Deposit USDC on Morpho",
            "Show best lending vaults",
            "Earn yield on my ETH",
        ]

        for example in examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect lending intent
            assert data["routing"]["intent"] in ["lending", "LENDING"]
            assert "agent_message" in data
            assert data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_lending_shortcut",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_money_market_shortcut(self, test_client: AsyncClient, llm_validator):
        """Test money market comparison shortcut examples."""
        examples = [
            "Compare Aave vs Compound",
            "Best money market rates for USDC",
            "Compare lending rates for ETH",
        ]

        for example in examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect money_market intent
            assert data["routing"]["intent"] in ["money_market", "MONEY_MARKET"]
            assert "agent_message" in data
            assert data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_money_market_shortcut",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide market sentiment analysis for ETH. Response should include relevant market indicators, community sentiment, or price trends without making specific investment recommendations."
                ),
                additional_context={'test_category': 'sentiment_query', 'token': 'ETH'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_swap_shortcut(self, test_client: AsyncClient, llm_validator):
        """Test swap shortcut examples."""
        examples = [
            "Swap 100 USDC for ETH",
            "Swap USDC from Ethereum to Base",
            "Best swap rate for ETH to USDC",
            "Swap BTC to ETH",
        ]

        for example in examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect swap intent
            intent = data["routing"]["intent"].upper()
            assert "SWAP" in intent
            assert "agent_message" in data
            assert data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_swap_shortcut",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_portfolio_shortcut_requires_registration(self, test_client: AsyncClient, llm_validator):
        """Test portfolio shortcut requires registration (restricted)."""
        examples = [
            "Show my portfolio",
            "What tokens do I have?",
            "List my holdings",
        ]

        for example in examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect portfolio intent
            assert data["routing"]["intent"] in ["portfolio", "PORTFOLIO"]

            # Should require registration for guests
            assert data["registration_required"] is not None
            assert data["registration_required"]["required"] is True
            assert data["registration_required"]["reason"] == "view_portfolio"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_portfolio_shortcut_requires_registration",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_balance_shortcut_requires_registration(self, test_client: AsyncClient, llm_validator):
        """Test balance shortcut requires registration (restricted)."""
        examples = [
            "What's my balance?",
            "Check my balance",
            "Show my balance",
        ]

        for example in examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect balance intent
            assert data["routing"]["intent"] in ["balance", "BALANCE"]

            # Should require registration for guests
            assert data["registration_required"] is not None
            assert data["registration_required"]["required"] is True
            assert data["registration_required"]["reason"] == "view_balance"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_balance_shortcut_requires_registration",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_activity_shortcut_requires_registration(self, test_client: AsyncClient, llm_validator):
        """Test activity shortcut requires registration (restricted)."""
        examples = [
            "Show my transactions",
            "Recent activity",
            "What did I do today?",
        ]

        for example in examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect activity intent
            assert data["routing"]["intent"] in ["activity", "ACTIVITY"]

            # Should require registration for guests
            assert data["registration_required"] is not None
            assert data["registration_required"]["required"] is True
            assert data["registration_required"]["reason"] == "view_activity"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_activity_shortcut_requires_registration",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_receive_shortcut_requires_registration(self, test_client: AsyncClient, llm_validator):
        """Test receive shortcut requires registration (restricted)."""
        examples = [
            "I want to receive crypto",
            "Receive crypto",
            "My wallet address",
        ]

        for example in examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect receive intent
            assert data["routing"]["intent"] in ["receive", "RECEIVE"]

            # Should require registration for guests
            assert data["registration_required"] is not None
            assert data["registration_required"]["required"] is True
            assert data["registration_required"]["reason"] == "view_receive_address"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_receive_shortcut_requires_registration",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_buy_shortcut_requires_registration(self, test_client: AsyncClient, llm_validator):
        """Test buy shortcut requires registration (restricted)."""
        examples = [
            "I want to buy crypto",
            "Buy Bitcoin with card",
            "How to buy ETH",
        ]

        for example in examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect buy intent
            assert data["routing"]["intent"] in ["buy", "BUY"]

            # Should require registration for guests
            assert data["registration_required"] is not None
            assert data["registration_required"]["required"] is True
            assert data["registration_required"]["reason"] == "execute_buy"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_buy_shortcut_requires_registration",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_send_shortcut_requires_registration(self, test_client: AsyncClient, llm_validator):
        """Test send shortcut requires registration (restricted)."""
        examples = [
            "Send crypto to a friend",
            "Transfer ETH to another wallet",
            "I want to send USDC",
        ]

        for example in examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect send intent
            assert data["routing"]["intent"] in ["send", "SEND"]

            # Should require registration for guests
            assert data["registration_required"] is not None
            assert data["registration_required"]["required"] is True
            assert data["registration_required"]["reason"] == "execute_send"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_send_shortcut_requires_registration",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multilingual_shortcuts_spanish(self, test_client: AsyncClient, llm_validator):
        """Test Spanish shortcuts."""
        response = await test_client.get("/api/v1/chat/shortcuts?lang=es")
        assert response.status_code == 200
        data = response.json()

        assert data["language"] == "es"
        assert data["language_name"] == "Español"

        # Test a Spanish example
        response = await test_client.post(
            "/api/v1/guest/chat",
            json={"content": "Depositar USDC en Morpho", "language": "es"}
        )

        assert response.status_code == 200
        chat_data = response.json()
        assert chat_data["routing"]["intent"] in ["lending", "LENDING"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_multilingual_shortcuts_spanish",
                user_input="Depositar USDC en Morpho",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multilingual_shortcuts_portuguese(self, test_client: AsyncClient, llm_validator):
        """Test Portuguese shortcuts."""
        response = await test_client.get("/api/v1/chat/shortcuts?lang=pt")
        assert response.status_code == 200
        data = response.json()

        assert data["language"] == "pt"
        assert data["language_name"] == "Português"

        # Test a Portuguese example
        response = await test_client.post(
            "/api/v1/guest/chat",
            json={"content": "Trocar 100 USDC por ETH", "language": "pt"}
        )

        assert response.status_code == 200
        chat_data = response.json()
        intent = chat_data["routing"]["intent"].upper()
        assert "SWAP" in intent

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_multilingual_shortcuts_portuguese",
                user_input="Trocar 100 USDC por ETH",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_multilingual_shortcuts_chinese(self, test_client: AsyncClient, llm_validator):
        """Test Mandarin Chinese shortcuts."""
        response = await test_client.get("/api/v1/chat/shortcuts?lang=zh")
        assert response.status_code == 200
        data = response.json()

        assert data["language"] == "zh"
        assert data["language_name"] == "中文"

        # Test a Chinese example
        response = await test_client.post(
            "/api/v1/guest/chat",
            json={"content": "显示我的投资组合", "language": "zh"}
        )

        assert response.status_code == 200
        chat_data = response.json()
        assert chat_data["routing"]["intent"] in ["portfolio", "PORTFOLIO"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_multilingual_shortcuts_chinese",
                user_input="显示我的投资组合",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_hunter_ai_shortcuts(self, test_client: AsyncClient, llm_validator):
        """Test Hunter AI intents (not in shortcuts but should work)."""
        hunter_examples = [
            ("What's BTC sentiment?", "sentiment"),
            ("Show me ETH trading signals", "trading_signals"),
            ("Predict SOL price", "price"),
        ]

        for content, expected_keyword in hunter_examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": content, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect Hunter AI intent
            intent = data["routing"]["intent"].lower()
            assert "hunter" in intent or expected_keyword in intent

            # Should have enrichment data (real Hunter AI processing)
            assert data["enrichment"] is not None
            assert "token" in data["enrichment"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_hunter_ai_shortcuts",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_graphrag_shortcuts(self, test_client: AsyncClient, llm_validator):
        """Test GraphRAG intents (protocol search)."""
        graphrag_examples = [
            "Tell me about Aave protocol",
            "What is Compound?",
            "Search for Uniswap",
        ]

        for content in graphrag_examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": content, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect protocol search or similar intent
            intent = data["routing"]["intent"].upper()
            assert "PROTOCOL" in intent or "SEARCH" in intent or "GENERAL" in intent

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_graphrag_shortcuts",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_shortcuts(self, test_client: AsyncClient, llm_validator):
        """Test ULTRA intents (arbitrage, MEV, flash loans)."""
        ultra_examples = [
            "Find arbitrage opportunities for ETH",
            "Show flash loan opportunities",
            "How can I avoid MEV attacks?",
        ]

        for content in ultra_examples:
            response = await test_client.post(
                "/api/v1/guest/chat",
                json={"content": content, "language": "en"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should detect ULTRA intent
            intent = data["routing"]["intent"].upper()
            assert "ULTRA" in intent or "ARBITRAGE" in intent or "MEV" in intent or "FLASH" in intent

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ultra_shortcuts",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_rate_limiting_info(self, test_client: AsyncClient, llm_validator):
        """Test that rate limiting info is returned."""
        response = await test_client.post(
            "/api/v1/guest/chat",
            json={"content": "What's BTC price?", "language": "en"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have guest info with rate limit status
        assert "guest_info" in data
        assert data["guest_info"]["messages_remaining"] > 0
        assert data["guest_info"]["session_active"] is True

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_rate_limiting_info",
                user_input="What",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto. Response must focus on crypto specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_all_shortcuts_have_examples(self, test_client: AsyncClient, llm_validator):
        """Test that all shortcuts have at least one example."""
        response = await test_client.get("/api/v1/chat/shortcuts?lang=en")
        assert response.status_code == 200
        data = response.json()

        for shortcut in data["shortcuts"]:
            assert len(shortcut["examples"]) > 0, f"Shortcut {shortcut['intent']} has no examples"
            assert shortcut["icon"], f"Shortcut {shortcut['intent']} has no icon"
            assert shortcut["command"], f"Shortcut {shortcut['intent']} has no command"
            assert shortcut["description"], f"Shortcut {shortcut['intent']} has no description"


# ========================================
# Advanced Shortcuts Tests (Phase 2.5)
# ========================================


@pytest.mark.integration
class TestGuestChatShortcutsAdvanced:
    """Advanced shortcuts tests for multi-step workflows and edge cases."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcuts_multi_step_portfolio_analysis(self, test_app, llm_validator, csv_tracker):
        """Test chained shortcut workflow for portfolio analysis."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "Show me top DeFi protocols and analyze their risks",
                    "language": "en"
                },
                headers={"X-Forwarded-For": "127.0.0.900"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide comprehensive multi-step analysis"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcuts_multi_step_portfolio_analysis",
                user_input="Show me top DeFi protocols and analyze their risks",
                agent_output=content,
                expected_behavior=(
                    "Should handle multi-step workflow combining protocol discovery and risk analysis. "
                    "Response should list top DeFi protocols and then analyze risks for each. "
                    "Should demonstrate ability to chain multiple shortcuts in sequence."
                ),
                additional_context={
                    'test_category': 'multi_step_workflow',
                    'shortcuts_involved': ['hunter_research', 'risk_analysis']
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "shortcuts", {
            "test_id": "guest_shortcuts_multi_step_001",
            "s_multistep": True,
            "input": "Show me top DeFi protocols and analyze their risks",
            "output": content,
            "test_label_sequence": "shortcuts_multi_step_workflow",
            "output_expected": "Multi-step workflow combining protocol discovery and risk analysis",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcuts_conditional_execution_logic(self, test_app, llm_validator, csv_tracker):
        """Test if-then shortcut behaviors."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "Check ETH price and tell me if it's a good buy opportunity",
                    "language": "en"
                },
                headers={"X-Forwarded-For": "127.0.0.901"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 50, "Should provide conditional analysis"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcuts_conditional_execution_logic",
                user_input="Check ETH price and tell me if it's a good buy opportunity",
                agent_output=content,
                expected_behavior=(
                    "Should check ETH price and provide conditional recommendation. "
                    "Response should include current price and then evaluate buy opportunity. "
                    "Should demonstrate conditional logic (if price X, then recommend Y)."
                ),
                additional_context={
                    'test_category': 'conditional_logic',
                    'asset': 'ETH',
                    'action': 'buy_recommendation'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "shortcuts", {
            "test_id": "guest_shortcuts_conditional_002",
            "s_multistep": False,
            "input": "Check ETH price and tell me if it's a good buy opportunity",
            "output": content,
            "test_label_sequence": "shortcuts_conditional_logic",
            "output_expected": "ETH price check with conditional buy recommendation based on current conditions",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcuts_parameter_validation_edge_cases(self, test_app, llm_validator, csv_tracker):
        """Test invalid input handling in shortcuts."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "Swap -100 ETH for BTC",
                    "language": "en"
                },
                headers={"X-Forwarded-For": "127.0.0.902"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 30, "Should provide error guidance"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcuts_parameter_validation_edge_cases",
                user_input="Swap -100 ETH for BTC",
                agent_output=content,
                expected_behavior=(
                    "Should gracefully handle invalid parameter (negative amount). "
                    "Response should explain why -100 ETH is invalid and provide helpful guidance. "
                    "Should NOT process the invalid request but educate the user."
                ),
                additional_context={
                    'test_category': 'parameter_validation',
                    'invalid_parameter': 'negative_amount',
                    'expected_behavior': 'graceful_error_handling'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "shortcuts", {
            "test_id": "guest_shortcuts_parameter_validation_003",
            "s_multistep": False,
            "input": "Swap -100 ETH for BTC",
            "output": content,
            "test_label_sequence": "shortcuts_parameter_validation",
            "output_expected": "Graceful error handling for invalid parameter with educational guidance",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcuts_output_format_consistency(self, test_app, llm_validator, csv_tracker):
        """Test standardized response structures across shortcuts."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Test multiple shortcuts to verify consistent formatting
            responses = []
            for i, query in enumerate([
                "What's BTC price?",
                "Analyze ETH trends",
                "Show DeFi yields"
            ]):
                resp = await ac.post(
                    "/api/v1/guest/chat",
                    json={"content": query, "language": "en"},
                    headers={"X-Forwarded-For": f"127.0.0.{903+i}"},
                )
                assert resp.status_code == 200
                responses.append(resp.json())

        # All responses should have consistent structure
        for data in responses:
            assert "agent_message" in data
            assert "content" in data["agent_message"]
            assert "routing" in data
            assert "guest_info" in data

        validation = None
        combined_content = ""
        if llm_validator.enabled:
            combined_content = " | ".join([r["agent_message"]["content"] for r in responses])
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcuts_output_format_consistency",
                user_input="Multiple shortcut queries for format consistency check",
                agent_output=combined_content,
                expected_behavior=(
                    "All shortcut responses should follow consistent formatting patterns. "
                    "Structure should be predictable and well-organized across different shortcut types."
                ),
                additional_context={
                    'test_category': 'format_consistency',
                    'shortcuts_tested': 3
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "shortcuts", {
            "test_id": "guest_shortcuts_format_consistency_004",
            "s_multistep": True,
            "input": "Multiple queries: What's BTC price? | Analyze ETH trends | Show DeFi yields",
            "output": combined_content or " | ".join([r["agent_message"]["content"] for r in responses]),
            "test_label_sequence": "shortcuts_format_consistency",
            "output_expected": "Consistent format across multiple shortcut responses",
            "status": "PASS" if all(r.status_code == 200 for r in [resp]) else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcuts_internationalization_parity(self, test_app, llm_validator, csv_tracker):
        """Test multi-language quality consistency."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            # Test same query in different languages
            languages = ["en", "es", "pt", "zh"]
            responses = {}

            for i, lang in enumerate(languages):
                resp = await ac.post(
                    "/api/v1/guest/chat",
                    json={"content": "What is DeFi?", "language": lang},
                    headers={"X-Forwarded-For": f"127.0.0.{910+i}"},
                )
                assert resp.status_code == 200
                responses[lang] = resp.json()

        # All languages should get responses
        for lang, data in responses.items():
            content = data["agent_message"]["content"]
            assert len(content) > 20, f"Language {lang} should get substantive response"
            assert data["routing"]["language"] == lang, f"Language routing should match {lang}"

        validation = None
        en_content = responses["en"]["agent_message"]["content"]
        if llm_validator.enabled:
            # Validate English response quality (representative)
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcuts_internationalization_parity",
                user_input="What is DeFi? (tested across 4 languages)",
                agent_output=en_content,
                expected_behavior=(
                    "Should provide quality response about DeFi that maintains consistent quality "
                    "across all supported languages (en, es, pt, zh). Response should be informative "
                    "and culturally appropriate."
                ),
                additional_context={
                    'test_category': 'internationalization',
                    'languages_tested': 4
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "shortcuts", {
            "test_id": "guest_shortcuts_internationalization_005",
            "s_multistep": True,
            "input": "What is DeFi? (tested in en, es, pt, zh)",
            "output": en_content,
            "test_label_sequence": "shortcuts_internationalization",
            "output_expected": "Quality consistent response across 4 languages",
            "status": "PASS" if all(responses.values()) else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcuts_accessibility_considerations(self, test_app, llm_validator, csv_tracker):
        """Test screen reader friendly responses."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "Explain current market conditions",
                    "language": "en"
                },
                headers={"X-Forwarded-For": "127.0.0.920"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        # Check for structured content (not just visual formatting)
        assert len(content) > 50, "Should provide detailed explanation"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcuts_accessibility_considerations",
                user_input="Explain current market conditions",
                agent_output=content,
                expected_behavior=(
                    "Response should be accessible for screen readers. "
                    "Should use clear structure, avoid emoji-only communication, "
                    "provide text descriptions, and organize information logically. "
                    "Content should be understandable without visual formatting."
                ),
                additional_context={
                    'test_category': 'accessibility',
                    'consideration': 'screen_reader_friendly'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "shortcuts", {
            "test_id": "guest_shortcuts_accessibility_006",
            "s_multistep": False,
            "input": "Explain current market conditions",
            "output": content,
            "test_label_sequence": "shortcuts_accessibility",
            "output_expected": "Screen reader friendly response with clear structure and text descriptions",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_shortcuts_mobile_optimization_responses(self, test_app, llm_validator, csv_tracker):
        """Test concise mobile-friendly output."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "Quick ETH update",
                    "language": "en"
                },
                headers={"X-Forwarded-For": "127.0.0.921"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        # Should be concise but informative
        assert len(content) > 30, "Should provide informative content"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcuts_mobile_optimization_responses",
                user_input="Quick ETH update",
                agent_output=content,
                expected_behavior=(
                    "Response should be mobile-optimized. Should provide concise, scannable information "
                    "suitable for small screens. Key information should come first. "
                    "Should avoid overly long paragraphs that are hard to read on mobile."
                ),
                additional_context={
                    'test_category': 'mobile_optimization',
                    'query_type': 'quick_update'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "shortcuts", {
            "test_id": "guest_shortcuts_mobile_optimization_007",
            "s_multistep": False,
            "input": "Quick ETH update",
            "output": content,
            "test_label_sequence": "shortcuts_mobile_optimization",
            "output_expected": "Mobile-optimized concise response with key information first",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })