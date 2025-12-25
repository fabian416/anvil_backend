#!/usr/bin/env python3
"""
Test script for Agent LLM providers (Vertex AI + DeepInfra fallback).

Tests:
1. Vertex AI LLM client direct
2. DeepInfra LLM client direct
3. LLM client with fallback (Vertex AI -> DeepInfra)
4. Intent classification with agents
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment
os.environ["APP_ENV"] = "local"


async def test_vertex_ai_client():
    """Test Vertex AI LLM client directly."""
    print("\n" + "="*60)
    print("TEST 1: Vertex AI LLM Client")
    print("="*60)

    try:
        import tomli
        from app.infrastructure.adapters.agent_squad.llm_client_vertex_ai import LLMClientVertexAI

        # Load API key from secrets
        secrets_path = project_root / "config" / "local" / ".secrets.toml"
        with open(secrets_path, "rb") as f:
            secrets = tomli.load(f)
            api_key = secrets.get("vertex_ai", {}).get("API_KEY", "")

        if not api_key:
            print("❌ No API key found in .secrets.toml")
            return False

        print(f"✅ API Key loaded: {api_key[:20]}...")

        # Create client
        client = LLMClientVertexAI(api_key=api_key)
        print("✅ Client created")

        # Test chat
        print("\n🧪 Testing chat completion...")
        result = await client.chat(
            messages=[
                {"role": "user", "content": "Say 'Hello from Vertex AI!' in 5 words exactly"}
            ],
            model="gpt-4o-mini",  # Will be mapped to gemini-2.0-flash-exp
            temperature=0.7,
            max_tokens=50,
        )

        print(f"✅ Chat successful")
        print(f"Response: {result['content']}")
        print(f"Model used: {result['model']}")
        print(f"Tokens: {result['tokens_used']}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_deepinfra_client():
    """Test DeepInfra LLM client directly."""
    print("\n" + "="*60)
    print("TEST 2: DeepInfra LLM Client")
    print("="*60)

    try:
        import tomli
        from app.infrastructure.adapters.agent_squad.llm_client_deepinfra import LLMClientDeepInfra

        # Load API key from secrets
        secrets_path = project_root / "config" / "local" / ".secrets.toml"
        with open(secrets_path, "rb") as f:
            secrets = tomli.load(f)
            api_key = secrets.get("deepinfra", {}).get("API_KEY", "")
            base_url = secrets.get("deepinfra", {}).get("BASE_URL", "https://api.deepinfra.com/v1/openai")

        if not api_key:
            print("❌ No API key found in .secrets.toml")
            return False

        print(f"✅ API Key loaded: {api_key[:20]}...")
        print(f"✅ Base URL: {base_url}")

        # Create client
        client = LLMClientDeepInfra(api_key=api_key, base_url=base_url)
        print("✅ Client created")

        # Test chat
        print("\n🧪 Testing chat completion...")
        result = await client.chat(
            messages=[
                {"role": "user", "content": "Say 'Hello from DeepInfra!' in 5 words exactly"}
            ],
            model="gpt-4o-mini",  # Will be mapped to meta-llama/Llama-3.2-3B-Instruct
            temperature=0.7,
            max_tokens=50,
        )

        print(f"✅ Chat successful")
        print(f"Response: {result['content']}")
        print(f"Model used: {result['model']}")
        print(f"Tokens: {result['tokens_used']}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fallback_client():
    """Test LLM client with fallback."""
    print("\n" + "="*60)
    print("TEST 3: LLM Client with Fallback")
    print("="*60)

    try:
        import tomli
        from app.infrastructure.adapters.agent_squad.llm_client_vertex_ai import LLMClientVertexAI
        from app.infrastructure.adapters.agent_squad.llm_client_deepinfra import LLMClientDeepInfra
        from app.infrastructure.adapters.agent_squad.llm_client_with_fallback import LLMClientWithFallback

        # Load credentials from secrets
        secrets_path = project_root / "config" / "local" / ".secrets.toml"
        with open(secrets_path, "rb") as f:
            secrets = tomli.load(f)
            vertex_api_key = secrets.get("vertex_ai", {}).get("API_KEY", "")
            deepinfra_api_key = secrets.get("deepinfra", {}).get("API_KEY", "")
            deepinfra_base_url = secrets.get("deepinfra", {}).get("BASE_URL", "https://api.deepinfra.com/v1/openai")

        if not vertex_api_key or not deepinfra_api_key:
            print("❌ Missing API keys in .secrets.toml")
            return False

        print("✅ API Keys loaded")

        # Create clients
        primary_client = LLMClientVertexAI(api_key=vertex_api_key)
        fallback_client = LLMClientDeepInfra(api_key=deepinfra_api_key, base_url=deepinfra_base_url)

        # Wrap with fallback
        client = LLMClientWithFallback(
            primary_client=primary_client,
            fallback_client=fallback_client,
            enable_fallback=True,
        )
        print("✅ Fallback client created")

        # Test chat (should use Vertex AI)
        print("\n🧪 Testing chat completion (should use Vertex AI)...")
        result = await client.chat(
            messages=[
                {"role": "user", "content": "Say 'Fallback test passed!' in 4 words"}
            ],
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=50,
        )

        print(f"✅ Chat successful")
        print(f"Response: {result['content']}")
        print(f"Model used: {result['model']}")

        # Test intent classification
        print("\n🧪 Testing intent classification...")
        intent_result = await client.classify_intent(
            prompt="What is the price of ETH right now?",
            model="gpt-4o-mini",
        )

        print(f"✅ Intent classification successful")
        print(f"Intent: {intent_result.get('intent', 'N/A')}")
        print(f"Confidence: {intent_result.get('confidence', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_system_integration():
    """Test full agent system integration."""
    print("\n" + "="*60)
    print("TEST 4: Agent System Integration")
    print("="*60)

    try:
        import tomli
        from app.setup.config.settings import load_settings
        from app.setup.config.loader import load_full_config

        # Load raw config
        raw_config = load_full_config(env="local")
        print(f"✅ Raw config loaded")

        # Load settings
        settings = load_settings()
        print(f"✅ Settings loaded")

        # Check LLM provider config
        llm_config = raw_config.get("llm_provider", {})
        primary_provider = llm_config.get("primary_provider", "N/A")
        fallback_provider = llm_config.get("fallback_provider", "N/A")

        print(f"\n📋 Configuration:")
        print(f"  Primary provider: {primary_provider}")
        print(f"  Fallback provider: {fallback_provider}")

        # Check credentials
        vertex_api_key = raw_config.get("vertex_ai", {}).get("API_KEY")
        deepinfra_api_key = raw_config.get("deepinfra", {}).get("API_KEY")

        if vertex_api_key:
            print(f"  ✅ Vertex AI API key found")
        else:
            print(f"  ❌ Vertex AI API key missing")

        if deepinfra_api_key:
            print(f"  ✅ DeepInfra API key found")
        else:
            print(f"  ❌ DeepInfra API key missing")

        # Test that we can create the LLM client through DI
        print("\n🧪 Testing LLM client creation through DI...")
        from app.infrastructure.adapters.agent_squad.llm_client_vertex_ai import LLMClientVertexAI
        from app.infrastructure.adapters.agent_squad.llm_client_deepinfra import LLMClientDeepInfra
        from app.infrastructure.adapters.agent_squad.llm_client_with_fallback import LLMClientWithFallback

        # Simulate what the DI container does
        primary_client = LLMClientVertexAI(api_key=vertex_api_key)
        fallback_client = LLMClientDeepInfra(
            api_key=deepinfra_api_key,
            base_url=raw_config.get("deepinfra", {}).get("BASE_URL", "https://api.deepinfra.com/v1/openai")
        )
        client = LLMClientWithFallback(
            primary_client=primary_client,
            fallback_client=fallback_client,
            enable_fallback=True,
        )

        print(f"✅ LLM client created successfully")

        # Test a simple chat
        print("\n🧪 Testing agent chat...")
        result = await client.chat(
            messages=[
                {"role": "system", "content": "You are a helpful DeFi assistant."},
                {"role": "user", "content": "What is DeFi in one sentence?"}
            ],
            model="gpt-4o",
            temperature=0.7,
            max_tokens=100,
        )

        print(f"✅ Chat successful")
        print(f"Response: {result['content'][:100]}...")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "🧪 "*30)
    print("AGENT LLM PROVIDERS TEST SUITE")
    print("🧪 "*30)

    results = []

    # Test 1: Vertex AI Client
    try:
        result1 = await test_vertex_ai_client()
        results.append(("Vertex AI Client", result1))
    except Exception as e:
        print(f"Test 1 crashed: {e}")
        results.append(("Vertex AI Client", False))

    # Test 2: DeepInfra Client
    try:
        result2 = await test_deepinfra_client()
        results.append(("DeepInfra Client", result2))
    except Exception as e:
        print(f"Test 2 crashed: {e}")
        results.append(("DeepInfra Client", False))

    # Test 3: Fallback Client
    try:
        result3 = await test_fallback_client()
        results.append(("LLM Client with Fallback", result3))
    except Exception as e:
        print(f"Test 3 crashed: {e}")
        results.append(("LLM Client with Fallback", False))

    # Test 4: Agent System Integration
    try:
        result4 = await test_agent_system_integration()
        results.append(("Agent System Integration", result4))
    except Exception as e:
        print(f"Test 4 crashed: {e}")
        results.append(("Agent System Integration", False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Agent system is configured correctly with Vertex AI + DeepInfra fallback.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
