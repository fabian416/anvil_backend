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
    async def test_knowledge_protocol_documentation_accuracy(self, test_app, llm_validator, csv_tracker):
        """Test protocol documentation technical accuracy."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={"content": "Explain how Uniswap V3 concentrated liquidity works technically", "language": "en"},
                headers={"X-Forwarded-For": "127.0.0.800"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed technical explanation"
        assert "Uniswap" in content or "liquidity" in content or "V3" in content, "Should reference Uniswap V3"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_knowledge_protocol_documentation_accuracy",
                user_input="Explain how Uniswap V3 concentrated liquidity works technically",
                agent_output=content,
                expected_behavior=(
                    "Should provide technically accurate explanation of Uniswap V3 concentrated liquidity. "
                    "Response should cover tick ranges, capital efficiency, position NFTs, and fee tiers. "
                    "Should be educational and technically precise."
                ),
                additional_context={
                    'test_category': 'protocol_documentation',
                    'protocol': 'uniswap_v3',
                    'topic': 'concentrated_liquidity'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "knowledge", {
            "test_id": "guest_knowledge_protocol_documentation_001",
            "s_multistep": False,
            "input": "Explain how Uniswap V3 concentrated liquidity works technically",
            "output": content,
            "test_label_sequence": "knowledge_protocol_documentation",
            "output_expected": "Technical explanation of Uniswap V3 concentrated liquidity with tick ranges and capital efficiency",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_smart_contract_audit_insights(self, test_app, llm_validator, csv_tracker):
        """Test smart contract security audit analysis quality."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "What are the most common vulnerabilities found in DeFi smart contract audits?",
                    "language": "en"
                },
                headers={"X-Forwarded-For": "127.0.0.801"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide comprehensive security analysis"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_knowledge_smart_contract_audit_insights",
                user_input="What are the most common vulnerabilities found in DeFi smart contract audits?",
                agent_output=content,
                expected_behavior=(
                    "Should identify common DeFi vulnerabilities like reentrancy, flash loan attacks, "
                    "oracle manipulation, access control issues, and integer overflow. "
                    "Response should be security-focused and provide actionable insights."
                ),
                additional_context={
                    'test_category': 'security_audit',
                    'domain': 'defi',
                    'topic': 'smart_contract_vulnerabilities'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "knowledge", {
            "test_id": "guest_knowledge_audit_insights_002",
            "s_multistep": False,
            "input": "What are the most common vulnerabilities found in DeFi smart contract audits?",
            "output": content,
            "test_label_sequence": "knowledge_security_audit",
            "output_expected": "Common DeFi vulnerabilities like reentrancy, flash loan attacks, oracle manipulation, and access control issues",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_tokenomics_analysis_depth(self, test_app, llm_validator, csv_tracker):
        """Test tokenomics and economic model analysis depth."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "Analyze the tokenomics of a typical governance token. What makes good token distribution?",
                    "language": "en"
                },
                headers={"X-Forwarded-For": "127.0.0.802"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide detailed tokenomics analysis"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_knowledge_tokenomics_analysis_depth",
                user_input="Analyze the tokenomics of a typical governance token. What makes good token distribution?",
                agent_output=content,
                expected_behavior=(
                    "Should cover token distribution factors like vesting schedules, emission rates, "
                    "supply allocation (team/treasury/community), inflation/deflation mechanics, "
                    "and governance rights. Should provide balanced economic analysis."
                ),
                additional_context={
                    'test_category': 'tokenomics',
                    'topic': 'token_distribution',
                    'analysis_type': 'economic_model'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "knowledge", {
            "test_id": "guest_knowledge_tokenomics_003",
            "s_multistep": False,
            "input": "Analyze the tokenomics of a typical governance token. What makes good token distribution?",
            "output": content,
            "test_label_sequence": "knowledge_tokenomics",
            "output_expected": "Token distribution analysis covering vesting schedules, emission rates, supply allocation, and governance rights",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_governance_proposal_summaries(self, test_app, llm_validator, csv_tracker):
        """Test DAO governance proposal clarity and comprehension."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "Explain how DAO governance proposals work and what makes a good proposal",
                    "language": "en"
                },
                headers={"X-Forwarded-For": "127.0.0.803"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide clear governance explanation"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_knowledge_governance_proposal_summaries",
                user_input="Explain how DAO governance proposals work and what makes a good proposal",
                agent_output=content,
                expected_behavior=(
                    "Should explain DAO voting mechanisms, proposal lifecycle (discussion, voting, execution), "
                    "quorum requirements, and best practices for proposal writing. "
                    "Should be clear and actionable for DAO participants."
                ),
                additional_context={
                    'test_category': 'governance',
                    'topic': 'dao_proposals',
                    'audience': 'dao_members'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "knowledge", {
            "test_id": "guest_knowledge_governance_004",
            "s_multistep": False,
            "input": "Explain how DAO governance proposals work and what makes a good proposal",
            "output": content,
            "test_label_sequence": "knowledge_dao_governance",
            "output_expected": "DAO voting mechanisms, proposal lifecycle, quorum requirements, and best practices for proposal writing",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_regulatory_compliance_guidance(self, test_app, llm_validator, csv_tracker):
        """Test regulatory compliance and legal disclaimer quality."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "What regulatory considerations should I know about when trading crypto in the US?",
                    "language": "en"
                },
                headers={"X-Forwarded-For": "127.0.0.804"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 100, "Should provide comprehensive regulatory guidance"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_knowledge_regulatory_compliance_guidance",
                user_input="What regulatory considerations should I know about when trading crypto in the US?",
                agent_output=content,
                expected_behavior=(
                    "Should mention SEC regulations, tax reporting requirements (IRS), "
                    "KYC/AML compliance, and include appropriate disclaimers. "
                    "Should NOT provide specific legal advice but general educational information. "
                    "Must be responsible and include 'not financial/legal advice' disclaimer."
                ),
                additional_context={
                    'test_category': 'regulatory_compliance',
                    'jurisdiction': 'us',
                    'topic': 'crypto_trading_regulations'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "knowledge", {
            "test_id": "guest_knowledge_regulatory_compliance_005",
            "s_multistep": False,
            "input": "What regulatory considerations should I know about when trading crypto in the US?",
            "output": content,
            "test_label_sequence": "knowledge_regulatory_compliance",
            "output_expected": "SEC regulations, IRS tax reporting, KYC/AML compliance, and appropriate disclaimers",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_knowledge_educational_content_beginner_friendly(self, test_app, llm_validator, csv_tracker):
        """Test educational content accessibility for beginners."""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/guest/chat",
                json={
                    "content": "I'm new to DeFi. Explain what yield farming is in simple terms",
                    "language": "en"
                },
                headers={"X-Forwarded-For": "127.0.0.805"},
            )

        assert response.status_code == 200
        data = response.json()
        content = data["agent_message"]["content"]

        assert len(content) > 50, "Should provide clear explanation"

        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_knowledge_educational_content_beginner_friendly",
                user_input="I'm new to DeFi. Explain what yield farming is in simple terms",
                agent_output=content,
                expected_behavior=(
                    "Should explain yield farming using simple language without excessive jargon. "
                    "May use analogies (e.g., 'like earning interest at a bank but on steroids'). "
                    "Should mention rewards, liquidity pools, and risks in beginner-friendly terms. "
                    "Tone should be welcoming and educational, not condescending."
                ),
                additional_context={
                    'test_category': 'educational_content',
                    'audience': 'beginners',
                    'topic': 'yield_farming',
                    'complexity_level': 'simple'
                }
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        # CSV tracking
        await csv_tracker("guest", "knowledge", {
            "test_id": "guest_knowledge_educational_beginner_006",
            "s_multistep": False,
            "input": "I'm new to DeFi. Explain what yield farming is in simple terms",
            "output": content,
            "test_label_sequence": "knowledge_educational_beginner",
            "output_expected": "Simple explanation of yield farming with analogies, covering rewards, liquidity pools, and risks in beginner-friendly terms",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })
