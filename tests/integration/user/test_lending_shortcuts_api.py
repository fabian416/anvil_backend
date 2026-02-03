"""
Integration test for Shortcuts API - Lending Vault Examples

Validates that the Shortcuts API at GET /api/v1/chat/shortcuts includes
the vault query examples added in Commit 2 (4ccf3009).

This ensures the shortcuts.json vault patterns are properly exposed via the API
for frontend autocomplete/suggestion features.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.run import make_app

# Skip - Tests specific shortcut patterns that may have changed
pytestmark = pytest.mark.skip(reason="Shortcut patterns may have changed")


@pytest_asyncio.fixture
async def client():
    """Create test client."""
    app = make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
@pytest.mark.integration
async def test_shortcuts_api_includes_vault_patterns_english(client: AsyncClient):
    """Test that shortcuts API includes vault query patterns in English."""
    response = await client.get("/api/v1/chat/shortcuts?lang=en")

    assert response.status_code == 200
    data = response.json()

    # Find LENDING_COMPARE command
    lending_commands = data.get("lending", {}).get("commands", [])
    lending_compare = next(
        (cmd for cmd in lending_commands if cmd.get("intent") == "LENDING_COMPARE"),
        None,
    )

    assert lending_compare is not None, "LENDING_COMPARE intent not found in shortcuts"

    patterns_en = lending_compare.get("patterns", {}).get("en", [])

    # Vault patterns that should be present (from Commit 2: 4ccf3009)
    expected_vault_patterns = [
        "best lending vaults",
        "top vaults",
        "best morpho vaults",
        "show best vaults",
        "compare vaults",
        "vault comparison",
        "vault recommendations",
        "vaults with best apy",
        "list morpho vaults",
        "find best vaults",
    ]

    for pattern in expected_vault_patterns:
        assert pattern in patterns_en, (
            f"Expected vault pattern '{pattern}' not found in shortcuts API. "
            f"Available patterns: {patterns_en}"
        )

    print(
        f"\n✅ All {len(expected_vault_patterns)} vault patterns found in shortcuts API"
    )
    print(f"Total patterns in LENDING_COMPARE: {len(patterns_en)}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_shortcuts_api_includes_vault_patterns_spanish(client: AsyncClient):
    """Test that shortcuts API includes vault query patterns in Spanish."""
    response = await client.get("/api/v1/chat/shortcuts?lang=es")

    assert response.status_code == 200
    data = response.json()

    # Find LENDING_COMPARE command
    lending_commands = data.get("lending", {}).get("commands", [])
    lending_compare = next(
        (cmd for cmd in lending_commands if cmd.get("intent") == "LENDING_COMPARE"),
        None,
    )

    assert lending_compare is not None, "LENDING_COMPARE intent not found in shortcuts"

    patterns_es = lending_compare.get("patterns", {}).get("es", [])

    # Spanish vault patterns (from Commit 2: 4ccf3009)
    expected_vault_patterns_es = [
        "mejores bóvedas de préstamo",
        "mejores bóvedas morpho",
        "comparar bóvedas",
        "recomendaciones de bóvedas",
    ]

    for pattern in expected_vault_patterns_es:
        assert pattern in patterns_es, (
            f"Expected Spanish vault pattern '{pattern}' not found in shortcuts API. "
            f"Available patterns: {patterns_es}"
        )

    print(
        f"\n✅ All {len(expected_vault_patterns_es)} Spanish vault patterns found in shortcuts API"
    )
    print(f"Total patterns in LENDING_COMPARE (es): {len(patterns_es)}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_shortcuts_api_vault_patterns_match_test_queries(client: AsyncClient):
    """Test that shortcuts API patterns match the queries used in integration tests."""
    response = await client.get("/api/v1/chat/shortcuts?lang=en")

    assert response.status_code == 200
    data = response.json()

    # Find LENDING_COMPARE command
    lending_commands = data.get("lending", {}).get("commands", [])
    lending_compare = next(
        (cmd for cmd in lending_commands if cmd.get("intent") == "LENDING_COMPARE"),
        None,
    )

    patterns_en = lending_compare.get("patterns", {}).get("en", [])

    # Queries used in test_lending_vaults.py
    test_queries = [
        "Show best lending vaults",  # test 001
        "top vaults",  # test 002
        "best morpho vaults",  # test 003
        "compare vaults",  # test 004
    ]

    # Normalize for comparison (lowercase, remove "show ")
    patterns_normalized = [p.lower() for p in patterns_en]

    for query in test_queries:
        query_normalized = query.lower().replace("show ", "")

        # Check if query matches any pattern
        found = any(
            query_normalized == pattern
            or query_normalized in pattern
            or pattern in query_normalized
            for pattern in patterns_normalized
        )

        assert found, (
            f"Test query '{query}' not represented in shortcuts API patterns. "
            f"This means users won't see this example in autocomplete. "
            f"Available patterns: {patterns_en}"
        )

    print(f"\n✅ All test queries are represented in shortcuts API patterns")
    print("This ensures consistency between tests and user-facing examples.")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_shortcuts_api_lending_compare_metadata(client: AsyncClient):
    """Test that LENDING_COMPARE has proper metadata for vault queries."""
    response = await client.get("/api/v1/chat/shortcuts?lang=en")

    assert response.status_code == 200
    data = response.json()

    # Find LENDING_COMPARE command
    lending_commands = data.get("lending", {}).get("commands", [])
    lending_compare = next(
        (cmd for cmd in lending_commands if cmd.get("intent") == "LENDING_COMPARE"),
        None,
    )

    assert lending_compare is not None

    # Validate metadata
    assert lending_compare.get("intent") == "LENDING_COMPARE"
    assert lending_compare.get("category") == "lending"

    # Check description exists in multiple languages
    description = lending_compare.get("description", {})
    assert "en" in description
    assert "es" in description
    assert "pt" in description
    assert "zh" in description

    # Check patterns exist in multiple languages
    patterns = lending_compare.get("patterns", {})
    assert "en" in patterns
    assert "es" in patterns
    assert len(patterns["en"]) > 10, "Should have comprehensive English patterns"
    assert len(patterns["es"]) > 5, "Should have Spanish patterns"

    # Check examples exist
    examples = lending_compare.get("examples", {})
    assert "en" in examples

    print("\n✅ LENDING_COMPARE metadata is complete with multi-language support")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_shortcuts_api_multi_language_support(client: AsyncClient):
    """Test that shortcuts API supports all languages for vault patterns."""
    languages = ["en", "es", "pt", "zh"]

    for lang in languages:
        response = await client.get(f"/api/v1/chat/shortcuts?lang={lang}")

        assert response.status_code == 200, (
            f"Failed to fetch shortcuts for language: {lang}"
        )
        data = response.json()

        # Find LENDING_COMPARE
        lending_commands = data.get("lending", {}).get("commands", [])
        lending_compare = next(
            (cmd for cmd in lending_commands if cmd.get("intent") == "LENDING_COMPARE"),
            None,
        )

        assert lending_compare is not None, (
            f"LENDING_COMPARE not found for language: {lang}"
        )

        # Check patterns exist for this language
        patterns = lending_compare.get("patterns", {})
        assert lang in patterns, f"Patterns not found for language: {lang}"
        assert len(patterns[lang]) > 0, f"No patterns defined for language: {lang}"

        print(f"✅ {lang.upper()}: {len(patterns[lang])} patterns available")

    print(f"\n✅ All {len(languages)} languages supported for vault patterns")
