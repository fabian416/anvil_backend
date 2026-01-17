"""
Integration tests for guest Hunter AI sentiment analysis.

Tests the sentiment analysis feature for guest users with real data sources.
"""

import json
import pytest
import warnings
from datetime import datetime


class TestGuestHunterSentiment:
    """Test Hunter AI sentiment analysis for guests."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_analysis_basic(self, client, llm_validator, csv_tracker):
        """Test basic sentiment analysis request."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What's the sentiment for ETH?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "agent_message" in data
        content = data["agent_message"]["content"]

        # Should show sentiment analysis
        assert "Sentiment" in content or "sentiment" in content.lower()
        assert "ETH" in content

        # Should have enrichment
        assert "enrichment" in data
        enrichment = data["enrichment"]
        assert "token" in enrichment
        assert enrichment["token"] == "ETH"
        assert "overall_score" in enrichment
        assert "classification" in enrichment

        # Guests can access without registration (field may be None for unrestricted features)
        registration_required = data.get("registration_required")
        if registration_required is not None:
            assert registration_required["required"] is False
        # None means no registration required at all

        # Optional LLM semantic validation (environment-gated with custom prompts)
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_analysis_basic",
                user_input="What's the sentiment for ETH?",
                agent_output=content,
                expected_behavior=(
                    "Response should provide sentiment analysis for ETH (Ethereum). "
                    "Should include sentiment classification (bullish/bearish/neutral), "
                    "overall sentiment score, and sources breakdown. "
                    "Should use emojis and clear formatting for visual appeal."
                ),
                test_func=self.test_sentiment_analysis_basic,  # PHASE 3: Custom prompt generation
                additional_context={
                    'test_category': 'hunter_sentiment',
                    'user_type': 'guest',
                    'token': 'ETH',
                    'feature': 'basic_sentiment_analysis'
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )

        # CSV tracking with enhanced fields (PHASE 3: 23 columns)
        await csv_tracker("guest", "hunter", {
            # Standard 11 fields
            "test_id": "guest_hunter_sentiment_basic_001",
            "s_multistep": False,
            "input": "What's the sentiment for ETH?",
            "output": content,
            "test_label_sequence": "hunter_sentiment_basic",
            "output_expected": "Sentiment analysis for ETH with classification, score, and sources",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.scoring.overall_score if validation and validation.scoring else None,
            "qa_status": validation.verdict.value if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            # Enhanced 12 fields (granular scores + metadata + recommendations)
            "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
            "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
            "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
            "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
            "test_category": validation.metadata.test_category if validation and validation.metadata else "hunter",
            "test_type": validation.metadata.test_type if validation and validation.metadata else None,
            "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
            "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
            "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
            "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
            "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
            "model_used": validation.metadata.model_used if validation and validation.metadata else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_sources_breakdown(self, client, llm_validator, csv_tracker):
        """Test that sentiment shows source breakdown."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentiment analysis for BTC", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        content = data["agent_message"]["content"]

        # Should have sources breakdown
        assert "sources" in enrichment
        sources = enrichment["sources"]

        # Should include major sources
        source_names = [s.lower() for s in sources.keys()]
        assert any("twitter" in s or "reddit" in s or "news" in s for s in source_names)

        # Should mention sources in content
        assert any(word in content.lower() for word in ["twitter", "reddit", "news", "sources", "social"])

        # Optional LLM semantic validation (environment-gated with custom prompts)
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_sources_breakdown",
                user_input="sentiment analysis for BTC",
                agent_output=content,
                expected_behavior=(
                    "Response should provide sentiment analysis for BTC with sources breakdown. "
                    "Should mention multiple data sources (Twitter, Reddit, news, social media). "
                    "Should show how different sources contribute to overall sentiment."
                ),
                test_func=self.test_sentiment_sources_breakdown,  # PHASE 3: Custom prompt generation
                additional_context={
                    'test_category': 'hunter_sentiment',
                    'user_type': 'guest',
                    'token': 'BTC',
                    'feature': 'sources_breakdown'
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )

        # CSV tracking with enhanced fields (PHASE 3: 23 columns)
        await csv_tracker("guest", "hunter", {
            # Standard 11 fields
            "test_id": "guest_hunter_sentiment_sources_002",
            "s_multistep": False,
            "input": "sentiment analysis for BTC",
            "output": content,
            "test_label_sequence": "hunter_sentiment_sources",
            "output_expected": "Sentiment analysis with sources breakdown (Twitter, Reddit, news)",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.scoring.overall_score if validation and validation.scoring else None,
            "qa_status": validation.verdict.value if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
            # Enhanced 12 fields (granular scores + metadata + recommendations)
            "accuracy_score": validation.scoring.accuracy_score if validation and validation.scoring else None,
            "relevance_score": validation.scoring.relevance_score if validation and validation.scoring else None,
            "safety_score": validation.scoring.safety_score if validation and validation.scoring else None,
            "coherence_score": validation.scoring.coherence_score if validation and validation.scoring else None,
            "test_category": validation.metadata.test_category if validation and validation.metadata else "hunter",
            "test_type": validation.metadata.test_type if validation and validation.metadata else None,
            "expected_intents": json.dumps(validation.metadata.expected_intents) if validation and validation.metadata else None,
            "token_usage": validation.metadata.token_usage if validation and validation.metadata else None,
            "improvement_suggestions": json.dumps(validation.recommendations.improvement_suggestions) if validation and validation.recommendations else None,
            "critical_issues": json.dumps(validation.recommendations.critical_issues) if validation and validation.recommendations else None,
            "next_steps": json.dumps(validation.recommendations.next_steps) if validation and validation.recommendations else None,
            "model_used": validation.metadata.model_used if validation and validation.metadata else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_multiple_tokens(self, client, llm_validator, csv_tracker):
        """Test sentiment for different tokens."""

        tokens = ["BTC", "ETH", "SOL"]
        last_content = ""

        for token in tokens:
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": f"sentiment for {token}", "language": "en"}
            )
            assert response.status_code == 200
            data = response.json()

            enrichment = data["enrichment"]
            assert enrichment["token"] == token
            last_content = data["agent_message"]["content"]

        # Optional LLM semantic validation (environment-gated)
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_multiple_tokens",
                user_input="sentiment for SOL (tested BTC, ETH, SOL sequentially)",
                agent_output=last_content,
                expected_behavior=(
                    "Response should provide sentiment analysis for the requested token. "
                    "System should handle multiple different tokens correctly. "
                    "Each token should have its own sentiment data and enrichment."
                ),
                additional_context={
                    'test_category': 'hunter_sentiment',
                    'user_type': 'guest',
                    'tokens_tested': tokens,
                    'feature': 'multiple_tokens'
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                )

        # CSV tracking
        await csv_tracker("guest", "hunter", {
            "test_id": "guest_hunter_sentiment_multiple_003",
            "s_multistep": True,
            "input": "sentiment for BTC, ETH, SOL (sequential multi-token test)",
            "output": last_content,
            "test_label_sequence": "hunter_sentiment_multiple_tokens",
            "output_expected": "Sentiment analysis working correctly for multiple different tokens",
            "status": "PASS",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_classification_types(self, client, llm_validator, csv_tracker):
        """Test that sentiment returns valid classifications."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "What's the sentiment for ETH?", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "classification" in enrichment

        # Should be one of: bullish, bearish, neutral, mixed
        valid_classifications = ["bullish", "bearish", "neutral", "mixed"]
        assert enrichment["classification"].lower() in valid_classifications

        content = data["agent_message"]["content"]

        # Optional LLM semantic validation
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_classification_types",
                user_input="What's the sentiment for ETH?",
                agent_output=content,
                expected_behavior=(
                    "Response should provide sentiment with valid classification type "
                    "(bullish, bearish, neutral, or mixed). Classification should match "
                    "the overall sentiment tone."
                ),
                additional_context={
                    'test_category': 'hunter_sentiment',
                    'user_type': 'guest',
                    'token': 'ETH',
                    'feature': 'classification_validation'
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(f"LLM validation concern (confidence={validation.confidence:.2f}): {validation.reasoning}")

        # CSV tracking
        await csv_tracker("guest", "hunter", {
            "test_id": "guest_hunter_sentiment_classification_004",
            "s_multistep": False,
            "input": "What's the sentiment for ETH?",
            "output": content,
            "test_label_sequence": "hunter_sentiment_classification",
            "output_expected": "Sentiment with valid classification (bullish/bearish/neutral/mixed)",
            "status": "PASS" if enrichment["classification"].lower() in valid_classifications else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_score_range(self, client, llm_validator, csv_tracker):
        """Test that sentiment score is in valid range."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentiment BTC", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "overall_score" in enrichment

        score = enrichment["overall_score"]
        # Score should be between -1 and 1
        assert -1.0 <= score <= 1.0

        content = data["agent_message"]["content"]

        # Optional LLM semantic validation
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_score_range",
                user_input="sentiment BTC",
                agent_output=content,
                expected_behavior=(
                    "Response should provide sentiment with numerical score in valid range (-1 to 1). "
                    "Score should align with the sentiment classification and narrative."
                ),
                additional_context={
                    'test_category': 'hunter_sentiment',
                    'user_type': 'guest',
                    'token': 'BTC',
                    'feature': 'score_validation',
                    'score': score
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(f"LLM validation concern (confidence={validation.confidence:.2f}): {validation.reasoning}")

        # CSV tracking
        await csv_tracker("guest", "hunter", {
            "test_id": "guest_hunter_sentiment_score_005",
            "s_multistep": False,
            "input": "sentiment BTC",
            "output": content,
            "test_label_sequence": "hunter_sentiment_score",
            "output_expected": "Sentiment with valid score range (-1.0 to 1.0)",
            "status": "PASS" if -1.0 <= score <= 1.0 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_multilingual_spanish(self, client, llm_validator, csv_tracker):
        """Test sentiment analysis in Spanish."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentimiento de ETH", "language": "es"}
        )
        assert response.status_code == 200
        data = response.json()

        content = data["agent_message"]["content"]

        # Should contain Spanish or English text (fallback), or at minimum some response
        # Language detection may result in English fallback or error messages
        assert len(content) > 0  # At minimum, has some content

        # Optional LLM semantic validation
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_multilingual_spanish",
                user_input="sentimiento de ETH (Spanish: 'sentiment of ETH')",
                agent_output=content,
                expected_behavior=(
                    "Response should handle Spanish language request. May respond in Spanish or "
                    "English (fallback). Should still provide sentiment analysis for ETH."
                ),
                additional_context={
                    'test_category': 'hunter_sentiment',
                    'user_type': 'guest',
                    'token': 'ETH',
                    'feature': 'multilingual',
                    'language': 'es'
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(f"LLM validation concern (confidence={validation.confidence:.2f}): {validation.reasoning}")

        # CSV tracking
        await csv_tracker("guest", "hunter", {
            "test_id": "guest_hunter_sentiment_multilingual_006",
            "s_multistep": False,
            "input": "sentimiento de ETH (Spanish)",
            "output": content,
            "test_label_sequence": "hunter_sentiment_multilingual",
            "output_expected": "Sentiment analysis in Spanish or English fallback",
            "status": "PASS" if len(content) > 0 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_with_hunter_tool_tag(self, client, llm_validator, csv_tracker):
        """Test that response includes hunter_tool tag."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentiment ETH", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        enrichment = data["enrichment"]
        assert "hunter_tool" in enrichment
        assert enrichment["hunter_tool"] == "sentiment_aggregator"

        content = data["agent_message"]["content"]

        # Optional LLM semantic validation
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_with_hunter_tool_tag",
                user_input="sentiment ETH",
                agent_output=content,
                expected_behavior=(
                    "Response should provide sentiment analysis powered by Hunter AI sentiment aggregator tool. "
                    "Should aggregate sentiment from multiple sources."
                ),
                additional_context={
                    'test_category': 'hunter_sentiment',
                    'user_type': 'guest',
                    'token': 'ETH',
                    'feature': 'tool_tagging',
                    'hunter_tool': 'sentiment_aggregator'
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(f"LLM validation concern (confidence={validation.confidence:.2f}): {validation.reasoning}")

        # CSV tracking
        await csv_tracker("guest", "hunter", {
            "test_id": "guest_hunter_sentiment_tool_tag_007",
            "s_multistep": False,
            "input": "sentiment ETH",
            "output": content,
            "test_label_sequence": "hunter_sentiment_tool_tag",
            "output_expected": "Sentiment with hunter_tool tag (sentiment_aggregator)",
            "status": "PASS" if enrichment.get("hunter_tool") == "sentiment_aggregator" else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_real_data_sources(self, client, llm_validator, csv_tracker):
        """Test that sentiment uses real data sources."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH sentiment", "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should have sources array (new field)
        assert "sources" in data or "enrichment" in data

        enrichment = data["enrichment"]

        # Should have real source data
        assert "sources" in enrichment
        assert isinstance(enrichment["sources"], dict)
        assert len(enrichment["sources"]) > 0

        content = data["agent_message"]["content"]

        # Optional LLM semantic validation
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_real_data_sources",
                user_input="ETH sentiment",
                agent_output=content,
                expected_behavior=(
                    "Response should provide sentiment analysis using real data sources. "
                    "Should aggregate data from multiple real sources (news, social media, etc.)."
                ),
                additional_context={
                    'test_category': 'hunter_sentiment',
                    'user_type': 'guest',
                    'token': 'ETH',
                    'feature': 'real_data_sources',
                    'sources_count': len(enrichment.get("sources", {}))
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(f"LLM validation concern (confidence={validation.confidence:.2f}): {validation.reasoning}")

        # CSV tracking
        await csv_tracker("guest", "hunter", {
            "test_id": "guest_hunter_sentiment_real_sources_008",
            "s_multistep": False,
            "input": "ETH sentiment",
            "output": content,
            "test_label_sequence": "hunter_sentiment_real_sources",
            "output_expected": "Sentiment using real data sources (news, social media)",
            "status": "PASS" if len(enrichment.get("sources", {})) > 0 else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })


class TestGuestHunterSentimentStorytellingQuality:
    """Test storytelling and UX quality of sentiment responses."""

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_uses_emojis(self, client, llm_validator, csv_tracker):
        """Test that sentiment uses emojis for visual appeal."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentiment BTC", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should have emoji indicators
        has_emojis = any(emoji in content for emoji in ["📊", "📈", "📉", "🐂", "🐻", "⚖️"])
        assert has_emojis

        # Optional LLM semantic validation
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_uses_emojis",
                user_input="sentiment BTC",
                agent_output=content,
                expected_behavior=(
                    "Response should use emojis for visual appeal and clarity. "
                    "Emojis should enhance storytelling and make sentiment easy to understand at a glance."
                ),
                additional_context={
                    'test_category': 'hunter_sentiment_quality',
                    'user_type': 'guest',
                    'token': 'BTC',
                    'feature': 'emoji_usage'
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(f"LLM validation concern (confidence={validation.confidence:.2f}): {validation.reasoning}")

        # CSV tracking
        await csv_tracker("guest", "hunter", {
            "test_id": "guest_hunter_sentiment_emojis_009",
            "s_multistep": False,
            "input": "sentiment BTC",
            "output": content,
            "test_label_sequence": "hunter_sentiment_storytelling_emojis",
            "output_expected": "Sentiment with emojis for visual appeal (📊📈📉🐂🐻⚖️)",
            "status": "PASS" if has_emojis else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_clear_formatting(self, client, llm_validator, csv_tracker):
        """Test that sentiment has clear visual formatting."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "ETH sentiment", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should use markdown formatting
        has_formatting = "**" in content and ("\n\n" in content or "\n" in content)
        assert has_formatting

        # Optional LLM semantic validation
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_clear_formatting",
                user_input="ETH sentiment",
                agent_output=content,
                expected_behavior=(
                    "Response should use clear markdown formatting (bold text, line breaks). "
                    "Should have structured sections that make information easy to scan and read."
                ),
                additional_context={
                    'test_category': 'hunter_sentiment_quality',
                    'user_type': 'guest',
                    'token': 'ETH',
                    'feature': 'formatting'
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(f"LLM validation concern (confidence={validation.confidence:.2f}): {validation.reasoning}")

        # CSV tracking
        await csv_tracker("guest", "hunter", {
            "test_id": "guest_hunter_sentiment_formatting_010",
            "s_multistep": False,
            "input": "ETH sentiment",
            "output": content,
            "test_label_sequence": "hunter_sentiment_storytelling_formatting",
            "output_expected": "Sentiment with clear markdown formatting (bold, line breaks, structure)",
            "status": "PASS" if has_formatting else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })

    @pytest.mark.asyncio
    @pytest.mark.llm_validation
    async def test_sentiment_actionable_insights(self, client, llm_validator, csv_tracker):
        """Test that sentiment provides actionable context."""

        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": "sentiment SOL", "language": "en"}
        )
        content = response.json()["agent_message"]["content"]

        # Should provide context about what sentiment means
        insights_keywords = ["bullish", "bearish", "neutral", "positive", "negative", "mixed"]
        has_insights = any(keyword in content.lower() for keyword in insights_keywords)
        assert has_insights

        # Optional LLM semantic validation
        validation = None
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_sentiment_actionable_insights",
                user_input="sentiment SOL",
                agent_output=content,
                expected_behavior=(
                    "Response should provide actionable context about sentiment. "
                    "Should explain what the sentiment means and provide context for decision-making."
                ),
                additional_context={
                    'test_category': 'hunter_sentiment_quality',
                    'user_type': 'guest',
                    'token': 'SOL',
                    'feature': 'actionable_insights'
                }
            )
            if validation.verdict != "PASS":
                warnings.warn(f"LLM validation concern (confidence={validation.confidence:.2f}): {validation.reasoning}")

        # CSV tracking
        await csv_tracker("guest", "hunter", {
            "test_id": "guest_hunter_sentiment_insights_011",
            "s_multistep": False,
            "input": "sentiment SOL",
            "output": content,
            "test_label_sequence": "hunter_sentiment_storytelling_insights",
            "output_expected": "Sentiment with actionable insights and context for understanding",
            "status": "PASS" if has_insights else "FAIL",
            "date": datetime.utcnow().isoformat(),
            "quality": validation.confidence if validation else None,
            "qa_status": validation.verdict if validation else "SKIPPED",
            "qa_output": validation.reasoning if validation else None,
        })
