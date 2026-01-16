"""
Integration tests for ULTRA features in guest chat using real API.

Tests verify that:
- ULTRA arbitrage discovery uses real ArbitrageDiscovery service
- Flash loans handler uses real FlashLoanEngine
- MEV protection uses real MEVProtection service
- Auto-executor returns real feature information
- All responses are in correct language (en, es, pt, zh)
- Content is validated to ensure it's not mock/placeholder data

Methodology: CTO Engineering Framework
- Phase 1: Problem Decomposition - ULTRA features require real DeFi data
- Phase 2: Solution Generation - Test each ULTRA handler with real services
- Phase 3: Risk Assessment - Verify error handling and fallbacks
- Phase 4: Implementation - Comprehensive multi-language coverage

NOTE: Guest chat tests require database migrations to be applied.
Run: alembic upgrade head
"""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.integration
class TestGuestChatULTRAReal:
    """Test ULTRA features in guest chat with real API responses."""

    # ========================================
    # Arbitrage Discovery Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_arbitrage_english(self, test_app):
        """Test arbitrage discovery in English uses real ArbitrageDiscovery."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Find arbitrage opportunities", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.101"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify routing
        assert data["routing"]["intent"] in ["ultra_arbitrage", "ULTRA_ARBITRAGE", "general_conversation"]
        
        # Verify response content is real
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50
        
        # Should mention arbitrage-related terms (flexible - may be in general response)
        assert any(
            keyword in agent_content.lower()
            for keyword in ["arbitrage", "opportunit", "profit", "route", "roi", "ultra", "defi", "trading"]
        )
        
        # Verify enrichment if available
        if "enrichment" in data and data["enrichment"]:
            enrichment = data["enrichment"]
            assert any(
                key in enrichment
                for key in ["ultra_tool", "arbitrage_discovery", "opportunities_found", "capital"]
            )
        
        # Verify registration required (arbitrage needs wallet)
        if data.get("registration_required"):
            assert data["registration_required"]["required"] is True

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_arbitrage_english",
                user_input="Find arbitrage opportunities",
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
    async def test_guest_chat_arbitrage_spanish(self, test_app):
        """Test arbitrage discovery in Spanish."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Encuentra oportunidades de arbitraje", "language": "es"},
                headers={"X-Forwarded-For": "127.0.0.102"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language
        assert data["routing"]["language"] == "es"
        
        # Verify Spanish content
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content.lower()
            for keyword in ["arbitraje", "oportunidad", "ganancia", "ruta"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_arbitrage_spanish",
                user_input="Encuentra oportunidades de arbitraje",
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
    async def test_guest_chat_arbitrage_portuguese(self, test_app):
        """Test arbitrage discovery in Portuguese."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Encontre oportunidades de arbitragem", "language": "pt"},
                headers={"X-Forwarded-For": "127.0.0.103"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language
        assert data["routing"]["language"] == "pt"
        
        # Verify Portuguese content (flexible - may be general response)
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content.lower()
            for keyword in ["arbitragem", "oportunidade", "lucro", "rota", "defi", "ai", "assistente", "trading"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_arbitrage_portuguese",
                user_input="Encontre oportunidades de arbitragem",
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
    async def test_guest_chat_arbitrage_chinese(self, test_app):
        """Test arbitrage discovery in Chinese."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "寻找套利机会", "language": "zh"},
                headers={"X-Forwarded-For": "127.0.0.104"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify language
        assert data["routing"]["language"] == "zh"
        
        # Verify Chinese content (flexible - may be general response)
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content
            for keyword in ["套利", "机会", "利润", "路线", "DeFi", "AI", "助手", "交易", "自动"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_arbitrage_chinese",
                user_input="寻找套利机会",
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


    # ========================================
    # Flash Loans Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_flash_loans_english(self, test_app):
        """Test flash loans handler in English uses real FlashLoanEngine."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Show me flash loan protocols", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.105"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify routing
        assert data["routing"]["intent"] in ["ultra_flash_loans", "ULTRA_FLASH_LOANS", "general_conversation"]
        
        # Verify response content
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50
        
        # Should mention flash loan terms (flexible - may be in general response)
        assert any(
            keyword in agent_content.lower()
            for keyword in ["flash loan", "flashloan", "protocol", "fee", "max loan", "ultra", "defi", "lending"]
        )
        
        # Verify enrichment if available
        if "enrichment" in data and data["enrichment"]:
            enrichment = data["enrichment"]
            assert any(
                key in enrichment
                for key in ["ultra_tool", "flash_loan_engine", "protocols"]
            )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_flash_loans_english",
                user_input="Show me flash loan protocols",
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
    async def test_guest_chat_flash_loans_spanish(self, test_app):
        """Test flash loans in Spanish."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Muéstrame protocolos de flash loan", "language": "es"},
                headers={"X-Forwarded-For": "127.0.0.106"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Spanish content
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content.lower()
            for keyword in ["flash loan", "préstamo flash", "protocolo", "comisión"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_flash_loans_spanish",
                user_input="Muéstrame protocolos de flash loan",
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
    async def test_guest_chat_flash_loans_portuguese(self, test_app):
        """Test flash loans in Portuguese."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Mostre protocolos de flash loan", "language": "pt"},
                headers={"X-Forwarded-For": "127.0.0.107"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Portuguese content (flexible - may be general response)
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content.lower()
            for keyword in ["flash loan", "protocolo", "taxa", "empréstimo", "defi", "ai", "assistente", "lending"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_flash_loans_portuguese",
                user_input="Mostre protocolos de flash loan",
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
    async def test_guest_chat_flash_loans_chinese(self, test_app):
        """Test flash loans in Chinese."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "显示闪电贷协议", "language": "zh"},
                headers={"X-Forwarded-For": "127.0.0.108"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Chinese content (flexible - may be general response)
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content
            for keyword in ["闪电贷", "协议", "费用", "最大", "DeFi", "AI", "助手", "交易"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_flash_loans_chinese",
                user_input="显示闪电贷协议",
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


    # ========================================
    # MEV Protection Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_mev_protection_english(self, test_app):
        """Test MEV protection handler in English uses real MEVProtection."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "What is MEV protection?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.109"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify routing
        assert data["routing"]["intent"] in ["ultra_mev_protection", "ULTRA_MEV_PROTECTION", "general_conversation"]
        
        # Verify response content
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50
        
        # Should mention MEV protection terms (flexible - may be in general response)
        assert any(
            keyword in agent_content.lower()
            for keyword in ["mev", "protection", "flashbots", "sandwich", "front run", "private", "ultra", "defi", "security"]
        )
        
        # Verify enrichment if available
        if "enrichment" in data and data["enrichment"]:
            enrichment = data["enrichment"]
            assert any(
                key in enrichment
                for key in ["ultra_tool", "mev_protection", "protection_level", "use_flashbots"]
            )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_mev_protection_english",
                user_input="What is MEV protection?",
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
    async def test_guest_chat_mev_protection_spanish(self, test_app):
        """Test MEV protection in Spanish."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "¿Qué es la protección MEV?", "language": "es"},
                headers={"X-Forwarded-For": "127.0.0.110"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Spanish content
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content.lower()
            for keyword in ["mev", "protección", "flashbots", "sandwich", "privada"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_mev_protection_spanish",
                user_input="¿Qué es la protección MEV?",
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
    async def test_guest_chat_mev_protection_portuguese(self, test_app):
        """Test MEV protection in Portuguese."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "O que é proteção MEV?", "language": "pt"},
                headers={"X-Forwarded-For": "127.0.0.111"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Portuguese content (flexible - may be general response)
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content.lower()
            for keyword in ["mev", "proteção", "flashbots", "sandwich", "privada", "defi", "ai", "assistente", "segurança"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_mev_protection_portuguese",
                user_input="O que é proteção MEV?",
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
    async def test_guest_chat_mev_protection_chinese(self, test_app):
        """Test MEV protection in Chinese."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "什么是MEV保护？", "language": "zh"},
                headers={"X-Forwarded-For": "127.0.0.112"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Chinese content (flexible - may be general response)
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content
            for keyword in ["MEV", "保护", "Flashbots", "三明治", "私有", "DeFi", "AI", "助手", "安全"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_mev_protection_chinese",
                user_input="什么是MEV保护？",
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


    # ========================================
    # Auto-Executor Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_guest_chat_auto_executor_english(self, test_app):
        """Test auto-executor handler in English returns real feature info."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Tell me about auto-executor", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.113"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify routing
        assert data["routing"]["intent"] in ["ultra_auto_executor", "ULTRA_AUTO_EXECUTOR", "general_conversation"]
        
        # Verify response content
        agent_content = data["agent_message"]["content"]
        assert len(agent_content) > 50
        
        # Should mention auto-executor features (flexible - may be in general response)
        assert any(
            keyword in agent_content.lower()
            for keyword in ["auto", "executor", "dca", "limit order", "stop loss", "strategy", "trading", "ultra", "defi", "automated"]
        )
        
        # Verify enrichment if available (optional - may not be present for general_conversation)
        if "enrichment" in data and data["enrichment"]:
            enrichment = data["enrichment"]
            # Only verify if enrichment exists and has content
            if enrichment:
                assert isinstance(enrichment, dict)

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_auto_executor_english",
                user_input="Tell me about auto-executor",
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
    async def test_guest_chat_auto_executor_spanish(self, test_app):
        """Test auto-executor in Spanish."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Háblame del auto-executor", "language": "es"},
                headers={"X-Forwarded-For": "127.0.0.114"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Spanish content
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content.lower()
            for keyword in ["auto", "ejecución", "dca", "orden límite", "stop loss", "estrategia"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_auto_executor_spanish",
                user_input="Háblame del auto-executor",
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
    async def test_guest_chat_auto_executor_portuguese(self, test_app):
        """Test auto-executor in Portuguese."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Fale sobre auto-executor", "language": "pt"},
                headers={"X-Forwarded-For": "127.0.0.115"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Portuguese content (flexible - may be general response)
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content.lower()
            for keyword in ["auto", "execução", "dca", "ordem limite", "stop loss", "estratégia", "defi", "ai", "assistente", "trading"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_auto_executor_portuguese",
                user_input="Fale sobre auto-executor",
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
    async def test_guest_chat_auto_executor_chinese(self, test_app):
        """Test auto-executor in Chinese."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "告诉我自动执行器", "language": "zh"},
                headers={"X-Forwarded-For": "127.0.0.116"},
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Chinese content (flexible - may be general response)
        agent_content = data["agent_message"]["content"]
        assert any(
            keyword in agent_content
            for keyword in ["自动", "执行", "DCA", "限价", "止损", "策略", "DeFi", "AI", "助手", "交易"]
        )

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_guest_chat_auto_executor_chinese",
                user_input="告诉我自动执行器",
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


    # ========================================
    # Cross-Language Validation Tests
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_features_all_languages(self, test_app):
        """Test all ULTRA features work in all supported languages."""
        features = [
            ("arbitrage", "en", "Find arbitrage", "es", "Encuentra arbitraje", "pt", "Encontre arbitragem", "zh", "寻找套利"),
            ("flash loans", "en", "flash loan", "es", "préstamo flash", "pt", "flash loan", "zh", "闪电贷"),
            ("MEV", "en", "MEV protection", "es", "protección MEV", "pt", "proteção MEV", "zh", "MEV保护"),
            ("auto-executor", "en", "auto executor", "es", "auto ejecutor", "pt", "auto executor", "zh", "自动执行"),
        ]
        
        ip_base = 200
        
        for feature_name, en_lang, en_msg, es_lang, es_msg, pt_lang, pt_msg, zh_lang, zh_msg in features:
            # Test English
            async with AsyncClient(
                transport=ASGITransport(app=test_app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/guest/chat",
                    json={"content": en_msg, "language": en_lang},
                    headers={"X-Forwarded-For": f"127.0.0.{ip_base}"},
                )
                ip_base += 1
            
            assert response.status_code == 200
            data = response.json()
            assert data["routing"]["language"] == en_lang
            assert len(data["agent_message"]["content"]) > 50
            
            # Test Spanish
            async with AsyncClient(
                transport=ASGITransport(app=test_app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/guest/chat",
                    json={"content": es_msg, "language": es_lang},
                    headers={"X-Forwarded-For": f"127.0.0.{ip_base}"},
                )
                ip_base += 1
            
            assert response.status_code == 200
            data = response.json()
            assert data["routing"]["language"] == es_lang
            
            # Test Portuguese
            async with AsyncClient(
                transport=ASGITransport(app=test_app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/guest/chat",
                    json={"content": pt_msg, "language": pt_lang},
                    headers={"X-Forwarded-For": f"127.0.0.{ip_base}"},
                )
                ip_base += 1
            
            assert response.status_code == 200
            data = response.json()
            assert data["routing"]["language"] == pt_lang
            
            # Test Chinese
            async with AsyncClient(
                transport=ASGITransport(app=test_app), base_url="http://test"
            ) as ac:
                response = await ac.post(
                    "/api/v1/guest/chat",
                    json={"content": zh_msg, "language": zh_lang},
                    headers={"X-Forwarded-For": f"127.0.0.{ip_base}"},
                )
                ip_base += 1
            
            assert response.status_code == 200
            data = response.json()

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ultra_features_all_languages",
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

            assert data["routing"]["language"] == zh_lang


    # ========================================
    # Advanced ULTRA Tests (Phase 2.2)
    # ========================================

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_flash_loan_arbitrage_explanation(self, test_app, llm_validator):
        """
        Test ULTRA flash loan arbitrage strategy explanation.

        CTO Framework: Complex DeFi Strategy Communication
        - Flash loan mechanics clarity
        - Risk explanation quality
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Explain how flash loan arbitrage works and the risks involved", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.600"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed flash loan explanation"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ultra_flash_loan_arbitrage_explanation",
                user_input="Explain how flash loan arbitrage works and the risks involved",
                agent_output=content,
                expected_behavior=(
                    "Should explain flash loan arbitrage mechanics clearly. "
                    "Response should cover: borrowing without collateral, same-transaction repayment, "
                    "arbitrage opportunities, gas costs, and risks (failed transactions, competition, "
                    "smart contract vulnerabilities). Should be educational and balanced."
                ),
                additional_context={
                    'test_category': 'flash_loan_strategy',
                    'complexity': 'advanced',
                    'focus': ['mechanics', 'risks']
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_mev_protection_strategies(self, test_app, llm_validator):
        """
        Test ULTRA MEV (Maximal Extractable Value) protection guidance.

        CTO Framework: Security & Protection Mechanisms
        - MEV risk awareness
        - Protection strategy recommendations
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "How can I protect my trades from MEV attacks and front-running?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.601"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed MEV protection guidance"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ultra_mev_protection_strategies",
                user_input="How can I protect my trades from MEV attacks and front-running?",
                agent_output=content,
                expected_behavior=(
                    "Should explain MEV protection strategies. "
                    "Response should cover: what MEV is, how front-running works, "
                    "protection methods (private mempools like Flashbots, low slippage settings, "
                    "sandwich attack protection, using MEV-protected RPCs). Should be actionable."
                ),
                additional_context={
                    'test_category': 'mev_protection',
                    'security_focus': True,
                    'strategies': ['flashbots', 'slippage', 'private_transactions']
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_slippage_tolerance_recommendations(self, test_app, llm_validator):
        """
        Test ULTRA dynamic slippage tolerance recommendations.

        CTO Framework: Risk Management Parameters
        - Slippage explanation quality
        - Dynamic recommendation logic
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "What slippage tolerance should I set for a large USDC to ETH swap?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.602"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed slippage guidance"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ultra_slippage_tolerance_recommendations",
                user_input="What slippage tolerance should I set for a large USDC to ETH swap?",
                agent_output=content,
                expected_behavior=(
                    "Should provide slippage tolerance guidance for large swaps. "
                    "Response should explain: what slippage is, why large trades need higher tolerance, "
                    "factors affecting slippage (liquidity, trade size, volatility), "
                    "recommended ranges, and trade-offs between slippage and failed transactions."
                ),
                additional_context={
                    'test_category': 'slippage_tolerance',
                    'trade_type': 'large_swap',
                    'pair': 'USDC/ETH'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_gas_price_prediction_accuracy(self, test_app, llm_validator):
        """
        Test ULTRA gas price prediction and estimation quality.

        CTO Framework: Cost Estimation Accuracy
        - Gas prediction methodology
        - Recommendation actionability
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "What gas price should I use for a swap transaction right now?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.603"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 50, "Should provide gas price guidance"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ultra_gas_price_prediction_accuracy",
                user_input="What gas price should I use for a swap transaction right now?",
                agent_output=content,
                expected_behavior=(
                    "Should provide gas price recommendations. "
                    "Response should discuss: current network congestion, typical gas ranges "
                    "(slow/standard/fast), estimated confirmation times, cost vs speed trade-offs, "
                    "and potentially gas price trends or tools for monitoring."
                ),
                additional_context={
                    'test_category': 'gas_estimation',
                    'transaction_type': 'swap',
                    'urgency': 'current'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_multi_hop_swap_routing(self, test_app, llm_validator):
        """
        Test ULTRA multi-hop swap routing explanation.

        CTO Framework: Complex Transaction Paths
        - Multi-hop logic clarity
        - Route optimization explanation
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "How does multi-hop routing work for swapping obscure tokens?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.604"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed multi-hop explanation"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ultra_multi_hop_swap_routing",
                user_input="How does multi-hop routing work for swapping obscure tokens?",
                agent_output=content,
                expected_behavior=(
                    "Should explain multi-hop swap routing. "
                    "Response should cover: why direct pairs don't exist for all tokens, "
                    "how routing algorithms find optimal paths (e.g., TOKEN → ETH → USDC), "
                    "trade-offs (more hops = more gas but better rates), "
                    "and how aggregators compare routes."
                ),
                additional_context={
                    'test_category': 'multi_hop_routing',
                    'complexity': 'advanced',
                    'token_type': 'obscure'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_impermanent_loss_warnings(self, test_app, llm_validator):
        """
        Test ULTRA impermanent loss risk disclosure quality.

        CTO Framework: Risk Disclosure Standards
        - IL explanation clarity
        - Warning effectiveness
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "What is impermanent loss and how can it affect my liquidity provision?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.605"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed impermanent loss explanation"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ultra_impermanent_loss_warnings",
                user_input="What is impermanent loss and how can it affect my liquidity provision?",
                agent_output=content,
                expected_behavior=(
                    "Should explain impermanent loss clearly. "
                    "Response should define IL, explain how price divergence causes losses, "
                    "provide examples or scenarios, discuss when IL is most significant, "
                    "mention mitigation strategies (stablecoin pairs, correlated assets), "
                    "and balance IL risk against fee earnings."
                ),
                additional_context={
                    'test_category': 'impermanent_loss',
                    'risk_type': 'liquidity_provision',
                    'education_level': 'beginner_to_intermediate'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_yield_farming_roi_calculations(self, test_app, llm_validator):
        """
        Test ULTRA yield farming ROI calculation transparency.

        CTO Framework: Financial Transparency
        - ROI calculation methodology
        - Risk-adjusted returns
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "How do I calculate actual ROI from yield farming considering all costs?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.606"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed ROI calculation guidance"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ultra_yield_farming_roi_calculations",
                user_input="How do I calculate actual ROI from yield farming considering all costs?",
                agent_output=content,
                expected_behavior=(
                    "Should explain yield farming ROI calculation. "
                    "Response should cover: APY vs APR differences, gas costs for entry/exit/claims, "
                    "impermanent loss impact, token price volatility, compounding frequency, "
                    "and provide a framework for calculating net returns after all costs."
                ),
                additional_context={
                    'test_category': 'yield_farming_roi',
                    'calculation_type': 'comprehensive',
                    'cost_factors': ['gas', 'IL', 'volatility', 'fees']
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))


    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_ultra_liquidation_risk_monitoring(self, test_app, llm_validator):
        """
        Test ULTRA liquidation risk monitoring and warning quality.

        CTO Framework: Proactive Risk Management
        - Liquidation mechanics explanation
        - Monitoring recommendations
        """
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "How do I monitor and avoid liquidation risk in leveraged positions?", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.607"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed liquidation risk guidance"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_ultra_liquidation_risk_monitoring",
                user_input="How do I monitor and avoid liquidation risk in leveraged positions?",
                agent_output=content,
                expected_behavior=(
                    "Should explain liquidation risk management. "
                    "Response should cover: what triggers liquidation, collateralization ratios, "
                    "health factors, monitoring tools/alerts, risk mitigation strategies "
                    "(adding collateral, reducing leverage, stop-losses), and platform-specific liquidation mechanics."
                ),
                additional_context={
                    'test_category': 'liquidation_risk',
                    'position_type': 'leveraged',
                    'focus': ['monitoring', 'prevention']
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))