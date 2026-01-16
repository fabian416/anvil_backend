"""
Integration Test: Verify All Shortcut Examples Work Correctly

Tests all examples from the shortcuts endpoint to ensure:
1. Intent detection works correctly
2. Responses are not generic fallback messages
3. All shortcuts provide meaningful responses

Follows CTO Engineering Framework methodology.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.run import make_app

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
async def shortcuts_data(client: AsyncClient):
    """Fetch shortcuts data from API."""
    response = await client.get("/api/v1/chat/shortcuts?lang=en")
    assert response.status_code == 200
    data = response.json()
    return data["shortcuts"]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_all_shortcut_examples_detect_correct_intent(
    client: AsyncClient, shortcuts_data: list
):
    """
    Test that all shortcut examples detect the correct intent.
    
    CTO Framework: Verification Phase
    - Verify intent detection accuracy
    - Ensure no false positives/negatives
    """
    failures = []
    
    for shortcut in shortcuts_data:
        intent = shortcut["intent"]
        command = shortcut["command"]
        
        for example in shortcut["examples"]:
            # Use unique IP for each test to avoid context interference
            ip_address = f"127.0.0.{hash(f'{intent}_{example}') % 100000}"
            
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"},
                headers={"X-Forwarded-For": ip_address},
            )
            
            assert response.status_code == 200, f"Failed for {intent}: {example}"
            data = response.json()
            
            detected_intent = data["routing"]["intent"]
            
            if detected_intent != intent:
                failures.append(
                    {
                        "shortcut": command,
                        "intent": intent,
                        "example": example,
                        "detected": detected_intent,
                    }
                )
    
    if failures:
        error_msg = "\n".join(
            [
                f"❌ {f['shortcut']} ({f['intent']}): '{f['example']}' → detected as '{f['detected']}'"
                for f in failures
            ]
        )
        pytest.fail(f"Intent detection failures:\n{error_msg}")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_all_shortcut_examples_not_generic_fallback(
    client: AsyncClient, shortcuts_data: list
):
    """
    Test that all shortcut examples return meaningful responses, not generic fallback.
    
    CTO Framework: Validation Phase
    - Verify responses are contextually relevant
    - Ensure no generic "I'm your AI assistant" messages
    """
    failures = []
    
    for shortcut in shortcuts_data:
        intent = shortcut["intent"]
        command = shortcut["command"]
        
        for example in shortcut["examples"]:
            # Use unique IP for each test to avoid context interference
            ip_address = f"127.0.0.{hash(f'{intent}_{example}') % 100000 + 200000}"
            
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"},
                headers={"X-Forwarded-For": ip_address},
            )
            
            assert response.status_code == 200, f"Failed for {intent}: {example}"
            data = response.json()
            
            content = data["agent_message"]["content"]
            
            # Check if response is generic fallback
            if GENERIC_FALLBACK_MESSAGE in content:
                failures.append(
                    {
                        "shortcut": command,
                        "intent": intent,
                        "example": example,
                        "content_preview": content[:100],
                    }
                )
    
    if failures:
        error_msg = "\n".join(
            [
                f"❌ {f['shortcut']} ({f['intent']}): '{f['example']}' → Generic fallback detected"
                for f in failures
            ]
        )
        pytest.fail(f"Generic fallback detected for:\n{error_msg}")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_shortcut_examples_have_meaningful_content(
    client: AsyncClient, shortcuts_data: list
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
    intent_keywords = {
        "lending": ["lending", "vault", "yield", "morpho", "deposit"],
        "money_market": ["aave", "compound", "rate", "supply", "lending"],
        "swap": ["swap", "quote", "rate", "bridge", "exchange"],
        "portfolio": ["portfolio", "dashboard", "holdings", "assets", "tokens"],
        "balance": ["balance", "wallet", "account", "required"],
        "activity": ["transaction", "history", "activity", "account", "required"],
        "receive": ["address", "wallet", "receive", "deposit", "required"],
        "buy": ["buy", "crypto", "card", "account", "required"],
        "send": ["send", "transfer", "wallet", "account", "required"],
    }
    
    for shortcut in shortcuts_data:
        intent = shortcut["intent"]
        command = shortcut["command"]
        
        for example in shortcut["examples"]:
            # Use unique IP for each test to avoid context interference
            ip_address = f"127.0.0.{hash(f'{intent}_{example}') % 100000 + 300000}"
            
            response = await client.post(
                "/api/v1/guest/chat",
                json={"content": example, "language": "en"},
                headers={"X-Forwarded-For": ip_address},
            )
            
            assert response.status_code == 200, f"Failed for {intent}: {example}"
            data = response.json()
            
            content = data["agent_message"]["content"].lower()
            
            # Check minimum content length (should be more than generic message)
            if len(content) < 50:
                failures.append(
                    {
                        "shortcut": command,
                        "intent": intent,
                        "example": example,
                        "issue": "Content too short",
                        "length": len(content),
                    }
                )
                continue
            
            # Check for intent-specific keywords
            if intent in intent_keywords:
                keywords = intent_keywords[intent]
                found_keyword = any(keyword in content for keyword in keywords)
                
                if not found_keyword:
                    failures.append(
                        {
                            "shortcut": command,
                            "intent": intent,
                            "example": example,
                            "issue": "No intent-specific keywords found",
                            "expected_keywords": keywords,
                            "content_preview": content[:150],
                        }
                    )
    
    if failures:
        error_msg = "\n".join(
            [
                f"❌ {f['shortcut']} ({f['intent']}): '{f['example']}' → {f['issue']}"
                for f in failures
            ]
        )
        pytest.fail(f"Content quality issues:\n{error_msg}")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_shortcuts_endpoint_structure(client: AsyncClient, llm_validator):
    """
    Test that shortcuts endpoint returns correct structure.
    
    CTO Framework: Structure Validation
    - Verify API contract compliance
    - Ensure all required fields are present
    """
    response = await client.get("/api/v1/chat/shortcuts?lang=en")
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify structure
    assert "language" in data
    assert "language_name" in data
    assert "shortcuts" in data
    assert isinstance(data["shortcuts"], list)
    assert len(data["shortcuts"]) > 0
    
    # Verify each shortcut has required fields
    for shortcut in data["shortcuts"]:
        assert "intent" in shortcut
        assert "command" in shortcut
        assert "description" in shortcut
        assert "examples" in shortcut
        assert "icon" in shortcut
        assert isinstance(shortcut["examples"], list)
        assert len(shortcut["examples"]) > 0
        
        # Verify examples are non-empty strings
        for example in shortcut["examples"]:
            assert isinstance(example, str)
            assert len(example.strip()) > 0

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_shortcuts_endpoint_structure",
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
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_all_languages_have_same_shortcuts(client: AsyncClient, llm_validator):
    """
    Test that all languages have the same shortcuts structure.
    
    CTO Framework: Consistency Validation
    - Verify i18n completeness
    - Ensure no missing translations
    """
    languages = ["en", "es", "fr", "zh", "pt"]
    shortcuts_by_lang = {}
    
    for lang in languages:
        response = await client.get(f"/api/v1/chat/shortcuts?lang={lang}")
        assert response.status_code == 200
        data = response.json()
        shortcuts_by_lang[lang] = {s["intent"]: s for s in data["shortcuts"]}
    
    # Get English intents as reference
    en_intents = set(shortcuts_by_lang["en"].keys())
    
    # Verify all languages have the same intents
    for lang in languages:
        lang_intents = set(shortcuts_by_lang[lang].keys())
        missing = en_intents - lang_intents
        extra = lang_intents - en_intents
        
        if missing or extra:
            pytest.fail(
                f"Language {lang} has mismatched shortcuts:\n"
                f"Missing: {missing}\n"
                f"Extra: {extra}"
            )
        
        # Verify each shortcut has examples
        for intent in en_intents:
            examples = shortcuts_by_lang[lang][intent]["examples"]

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_all_languages_have_same_shortcuts",
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

            assert len(examples) > 0, f"Language {lang}, intent {intent} has no examples"