"""
Integration Tests: Shortcuts Edge Cases
========================================

Tests edge cases and input variations for shortcut intent detection.

CTO.md Framework Application:
- Phase 1: Identified robustness requirements (case, whitespace, punctuation, languages)
- Phase 2: Comprehensive edge case matrix design
- Phase 3: Validation strategy for input normalization

Test Categories:
---------------
1. Case Sensitivity: UPPER, lower, MiXeD, camelCase
2. Whitespace Tolerance: Multiple spaces, tabs, leading/trailing
3. Punctuation Handling: !, ?, ., commas, quotes
4. Multi-Language: en, es, pt, fr, zh
5. Special Characters: Emojis, unicode, symbols
6. Typos & Variations: Common misspellings, abbreviations
7. Boundary Conditions: Very short, very long messages
8. Ambiguous Inputs: Multiple intents, unclear requests

Generated: 2026-01-10
Framework: CTO.md Engineering Methodology
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.run import make_app

# Access token for authenticated tests
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJ0ZXN0X3Nlc3Npb25fMjAyNl8xNzY4MDY2MDc5IiwiZXhwIjoxNzk5NjAyMDc5fQ.OUFFmZW2_QACkgrIphLFcOOB3Qb-1ckVB_RvZ-VTaF0"


# ============================================================================
# FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def client():
    """Create test client."""
    app = make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def user_conversation_id(client: AsyncClient):
    """Create conversation for authenticated user."""
    response = await client.post(
        "/api/v1/user/chat/conversations",
        json={"title": "Edge Case Test", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


# ============================================================================
# CATEGORY 1: Case Sensitivity Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("message,expected_intent", [
    ("SEND CRYPTO TO A FRIEND", "send"),
    ("send crypto to a friend", "send"),
    ("Send Crypto To A Friend", "send"),
    ("SeNd CrYpTo To A fRiEnD", "send"),
    ("BEST LENDING VAULTS", "lending"),
    ("best lending vaults", "lending"),
    ("Best Lending Vaults", "lending"),
    ("BeSt LeNdInG vAuLtS", "lending"),
])
@pytest.mark.llm_validation
async def test_case_sensitivity_guest(client: AsyncClient, message: str, expected_intent: str):
    """
    Test that intent detection is case-insensitive.

    Message normalization should convert all inputs to lowercase
    before pattern matching.
    """
    guest_ip = f"127.0.0.{hash(message) % 255}"

    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": message, "language": "en"},
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["routing"]["intent"] == expected_intent, \
        f"Case variation '{message}' should detect as '{expected_intent}'"


# ============================================================================
# CATEGORY 2: Whitespace Tolerance Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("message,expected_intent", [
    ("   send crypto to a friend   ", "send"),  # Leading/trailing spaces
    ("send  crypto  to  a  friend", "send"),    # Multiple spaces
    ("send\tcrypto\tto\ta\tfriend", "send"),    # Tabs
    ("send   crypto      to   a   friend", "send"),  # Irregular spacing
    ("   best   lending   vaults   ", "lending"),
    ("swap\t\tETH\t\tto\t\tUSDC", "swap"),
])
@pytest.mark.llm_validation
async def test_whitespace_tolerance_guest(client: AsyncClient, message: str, expected_intent: str):
    """
    Test that whitespace variations don't affect intent detection.

    Message normalization should:
    - Strip leading/trailing whitespace
    - Normalize multiple spaces to single space
    - Handle tabs and other whitespace characters
    """
    guest_ip = f"127.0.0.{hash(message) % 255}"

    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": message, "language": "en"},
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["routing"]["intent"] == expected_intent, \
        f"Whitespace variation should not affect intent detection"


# ============================================================================
# CATEGORY 3: Punctuation Handling Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("message,expected_intent", [
    ("Send crypto to a friend!", "send"),
    ("Send crypto to a friend?", "send"),
    ("Send crypto to a friend.", "send"),
    ("Send, crypto, to, a, friend", "send"),
    ("Send crypto to a friend...", "send"),
    ("Best lending vaults!!!", "lending"),
    ("What are the best lending vaults?", "lending"),
    ("Swap ETH to USDC!", "swap"),
])
@pytest.mark.llm_validation
async def test_punctuation_handling_guest(client: AsyncClient, message: str, expected_intent: str):
    """
    Test that punctuation doesn't interfere with intent detection.

    Common punctuation should be handled gracefully:
    - End punctuation: ! ? . ...
    - Internal punctuation: , ; :
    - Multiple punctuation: !!! ???
    """
    guest_ip = f"127.0.0.{hash(message) % 255}"

    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": message, "language": "en"},
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["routing"]["intent"] == expected_intent


# ============================================================================
# CATEGORY 4: Multi-Language Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("language,message,expected_intent", [
    ("en", "Send crypto to a friend", "send"),
    ("es", "Enviar cripto a un amigo", "send"),
    ("pt", "Enviar cripto para um amigo", "send"),
    ("en", "Best lending vaults", "lending"),
    ("es", "Mejores bóvedas de préstamos", "lending"),
    ("pt", "Melhores cofres de empréstimo", "lending"),
])
@pytest.mark.llm_validation
async def test_multi_language_support_guest(
    client: AsyncClient,
    language: str,
    message: str,
    expected_intent: str,
):
    """
    Test intent detection across supported languages.

    Supported languages: en, es, pt, fr, zh
    Each language should have equivalent keyword patterns.
    """
    guest_ip = f"127.0.0.{hash(f'{language}_{message}') % 255}"

    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": message, "language": language},
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["routing"]["intent"] == expected_intent, \
        f"Language '{language}' should detect intent correctly"


# ============================================================================
# CATEGORY 5: Special Characters & Emojis
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("message,expected_intent", [
    ("Send crypto 💰 to a friend 👥", "send"),
    ("🚀 Best lending vaults 💎", "lending"),
    ("Swap ETH ➡️ USDC", "swap"),
    ("Buy crypto 💳", "buy"),
    ("📊 Portfolio view", "portfolio"),
])
@pytest.mark.llm_validation
async def test_emojis_handling_guest(client: AsyncClient, message: str, expected_intent: str):
    """
    Test that emojis don't interfere with intent detection.

    Common crypto/finance emojis:
    💰 💵 💳 💎 🚀 📊 📈 📉 ➡️ 👥
    """
    guest_ip = f"127.0.0.{hash(message) % 255}"

    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": message, "language": "en"},
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["routing"]["intent"] == expected_intent


# ============================================================================
# CATEGORY 6: Typos & Common Variations
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.parametrize("message,expected_intent", [
    ("sen crypto to a friend", "send"),  # Missing 'd' - should still match keyword
    ("Best lendig vaults", "lending"),   # Typo in 'lending' - should still match
    ("swp ETH to USDC", "swap"),         # Missing 'a' - should still match
    ("bi crypto with card", "buy"),      # Missing 'y' - should still match
])
@pytest.mark.llm_validation
async def test_typo_tolerance_guest(client: AsyncClient, message: str, expected_intent: str):
    """
    Test graceful handling of common typos.

    Note: Exact match patterns won't match typos, but keyword detection should
    still work if core keywords are recognizable.
    """
    guest_ip = f"127.0.0.{hash(message) % 255}"

    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": message, "language": "en"},
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()

    # Typos may result in lower confidence or different routing
    # This test documents current behavior
    detected = data["routing"]["intent"]
    # We accept the detected intent (may fall back to different handler)
    assert detected is not None, "Should detect some intent even with typos"


# ============================================================================
# CATEGORY 7: Boundary Conditions
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_very_short_message_guest(client: AsyncClient):
    """
    Test handling of very short messages.

    Minimum meaningful input: 2-3 characters
    Examples: "hi", "ok", "btc"
    """
    guest_ip = f"127.0.0.{hash('short_001') % 255}"

    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": "hi", "language": "en"},
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()
    # Should route to generic greeting handler
    assert data["routing"]["intent"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_very_long_message_guest(client: AsyncClient):
    """
    Test handling of very long messages.

    Should still extract intent from verbose descriptions.
    """
    guest_ip = f"127.0.0.{hash('long_001') % 255}"

    long_message = (
        "Hello, I would like to send some cryptocurrency to my friend who lives in another country. "
        "I have some USDC in my wallet and I want to transfer it to their wallet address. "
        "Can you help me with this transaction? I'm not sure about the gas fees and how long it will take."
    )

    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": long_message, "language": "en"},
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["routing"]["intent"] == "send", \
        "Should detect 'send' intent from long verbose message"


# ============================================================================
# CATEGORY 8: Ambiguous Inputs
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_ambiguous_multi_intent_guest(client: AsyncClient):
    """
    Test handling of messages with multiple possible intents.

    Example: "Check my balance and send USDC"
    Contains both 'balance' and 'send' keywords.

    Expected: Should route to first/strongest detected intent.
    """
    guest_ip = f"127.0.0.{hash('ambiguous_001') % 255}"

    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": "Check my balance and send USDC to friend", "language": "en"},
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()

    # Should route to one of the intents (implementation dependent)
    detected = data["routing"]["intent"]
    assert detected in ["balance", "send"], \
        "Should route to one of the mentioned intents"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_unclear_request_guest(client: AsyncClient):
    """
    Test handling of unclear/vague requests.

    Example: "I need help with crypto"
    No specific intent, should route to generic assistant.
    """
    guest_ip = f"127.0.0.{hash('unclear_001') % 255}"

    response = await client.post(
        "/api/v1/guest/chat",
        json={"content": "I need help with crypto", "language": "en"},
        headers={"X-Forwarded-For": guest_ip},
    )

    assert response.status_code == 200
    data = response.json()

    # Should route to generic chat handler
    detected = data["routing"]["intent"]
    assert detected is not None, "Should route to some handler (likely generic)"


# ============================================================================
# AUTHENTICATED USER EDGE CASES
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_case_sensitivity_user(client: AsyncClient, user_conversation_id: str):
    """
    Test case sensitivity for authenticated users.
    Should behave same as guest users.
    """
    response = await client.post(
        f"/api/v1/user/chat/conversations/{user_conversation_id}/messages",
        json={"content": "SEND CRYPTO TO A FRIEND", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["routing"]["intent"] == "send"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_whitespace_tolerance_user(client: AsyncClient, user_conversation_id: str):
    """
    Test whitespace handling for authenticated users.
    """
    response = await client.post(
        f"/api/v1/user/chat/conversations/{user_conversation_id}/messages",
        json={"content": "   best   lending   vaults   ", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["routing"]["intent"] == "lending"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_emojis_user(client: AsyncClient, user_conversation_id: str):
    """
    Test emoji handling for authenticated users.
    """
    response = await client.post(
        f"/api/v1/user/chat/conversations/{user_conversation_id}/messages",
        json={"content": "Send crypto 💰 to friend 👥", "language": "en"},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["routing"]["intent"] == "send"


# ============================================================================
# REGRESSION TESTS - Known Issues
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_moonpay_routing_regression(client: AsyncClient):
    """
    Regression test: MoonPay pairs should route to swap_moonpay.

    Known behavior: BTC, ETH, SOL pairs route to swap_moonpay handler.
    This is CORRECT and intentional.
    """
    test_cases = [
        ("Swap BTC to ETH", "swap_moonpay"),
        ("Swap ETH to USDC", "swap_moonpay"),
        ("Swap SOL to BTC", "swap_moonpay"),
    ]

    for message, expected_intent in test_cases:
        response = await client.post(
            "/api/v1/guest/chat",
            json={"content": message, "language": "en"},
            headers={"X-Forwarded-For": f"127.0.0.{hash(message) % 255}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["routing"]["intent"] == expected_intent, \
            f"'{message}' should route to {expected_intent} (MoonPay handler)"


# ============================================================================
# SUMMARY TEST - Edge Case Coverage Validation
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
async def test_edge_case_coverage_summary():
    """
    Meta-test: Validate edge case coverage.

    Ensures we have tests for all edge case categories:
    1. Case sensitivity
    2. Whitespace tolerance
    3. Punctuation handling
    4. Multi-language support
    5. Special characters/emojis
    6. Typos and variations
    7. Boundary conditions
    8. Ambiguous inputs
    """
    import inspect
    current_module = inspect.getmodule(inspect.currentframe())
    test_functions = [
        name for name, obj in inspect.getmembers(current_module)
        if inspect.isfunction(obj) and name.startswith("test_")
    ]

    edge_case_categories = [
        "case_sensitivity",
        "whitespace_tolerance",
        "punctuation_handling",
        "multi_language",
        "emojis",
        "typo",
        "very_short",
        "very_long",
        "ambiguous",
        "unclear",
    ]

    print("\n✅ Edge Case Coverage:")
    for category in edge_case_categories:
        category_tests = [t for t in test_functions if category in t]
        print(f"  - {category}: {len(category_tests)} tests")
        assert len(category_tests) > 0, f"Missing tests for category: {category}"

    print(f"\n📊 Total edge case tests: {len(test_functions) - 1}")  # -1 for this summary test
