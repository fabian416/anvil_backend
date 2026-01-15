"""
Integration tests for guest chat with shortcuts.

Tests the /api/v1/guest/chat endpoint with all shortcut examples
to ensure proper intent detection and routing.
"""

import pytest


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

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_all_shortcuts_have_examples",
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

            assert shortcut["description"], f"Shortcut {shortcut['intent']} has no description"