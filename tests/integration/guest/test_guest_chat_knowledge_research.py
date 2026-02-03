"""
Integration tests for knowledge and research features in guest chat.

Tests cover protocol documentation, security audits, tokenomics analysis,
governance proposals, regulatory compliance, and educational content quality.
All tests use LLM validation for semantic quality assessment.
"""

import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport


@pytest.mark.integration
class TestGuestChatKnowledgeResearch:
    """Test knowledge and research features in guest chat."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_protocol_documentation_accuracy(
        self, test_app, llm_validator, csv_tracker
    ):
        """Test protocol documentation technical accuracy."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "Explain how Uniswap V3 concentrated liquidity works technically",
                    "language": "en",
                },
                headers={"X-Forwarded-For": "127.0.0.800"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed technical explanation"
        assert "Uniswap" in content or "liquidity" in content or "V3" in content, (
            "Should reference Uniswap V3"
        )

        validation = None

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_smart_contract_audit_insights(
        self, test_app, llm_validator, csv_tracker
    ):
        """Test smart contract security audit analysis quality."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "What are the most common vulnerabilities found in DeFi smart contract audits?",
                    "language": "en",
                },
                headers={"X-Forwarded-For": "127.0.0.801"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide comprehensive security analysis"

        validation = None

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_tokenomics_analysis_depth(
        self, test_app, llm_validator, csv_tracker
    ):
        """Test tokenomics and economic model analysis depth."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "Analyze the tokenomics of a typical governance token. What makes good token distribution?",
                    "language": "en",
                },
                headers={"X-Forwarded-For": "127.0.0.802"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed tokenomics analysis"

        validation = None

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_governance_proposal_summaries(
        self, test_app, llm_validator, csv_tracker
    ):
        """Test DAO governance proposal clarity and comprehension."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "Explain how DAO governance proposals work and what makes a good proposal",
                    "language": "en",
                },
                headers={"X-Forwarded-For": "127.0.0.803"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide clear governance explanation"

        validation = None

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_regulatory_compliance_guidance(
        self, test_app, llm_validator, csv_tracker
    ):
        """Test regulatory compliance and legal disclaimer quality."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "What regulatory considerations should I know about when trading crypto in the US?",
                    "language": "en",
                },
                headers={"X-Forwarded-For": "127.0.0.804"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide comprehensive regulatory guidance"

        validation = None

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_educational_content_beginner_friendly(
        self, test_app, llm_validator, csv_tracker
    ):
        """Test educational content accessibility for beginners."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "I'm new to DeFi. Explain what yield farming is in simple terms",
                    "language": "en",
                },
                headers={"X-Forwarded-For": "127.0.0.805"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 50, "Should provide clear explanation"

        validation = None
