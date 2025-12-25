#!/usr/bin/env python3
"""
Test script for DeepInfra API integration.

Tests:
1. Direct API call with httpx
2. List available models
3. Distillation integration test
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


async def test_deepinfra_direct():
    """Test DeepInfra API directly with httpx."""
    print("\n" + "="*60)
    print("TEST 1: Direct DeepInfra API Call")
    print("="*60)

    try:
        import httpx
        import tomli

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
        client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        print("✅ Client initialized")

        # List models
        print("\n📋 Listing available models...")
        try:
            response = await client.get("/models")
            if response.status_code == 200:
                models = response.json()
                if isinstance(models, dict) and "data" in models:
                    model_list = models["data"]
                    print(f"✅ Found {len(model_list)} models")

                    # Show some Llama models
                    llama_models = [m.get("id", m) for m in model_list if isinstance(m, dict) and "llama" in str(m.get("id", "")).lower()][:5]
                    if llama_models:
                        print(f"   Llama models: {', '.join(llama_models)}")
                else:
                    print(f"⚠️  Unexpected response format: {type(models)}")
            else:
                print(f"⚠️  Could not list models: {response.status_code}")
        except Exception as e:
            print(f"⚠️  Could not list models: {e}")

        # Test generation
        print("\n🧪 Testing generation with meta-llama/Llama-3.2-3B-Instruct...")
        response = await client.post(
            "/chat/completions",
            json={
                "model": "meta-llama/Llama-3.2-3B-Instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": 'Say "Hello from DeepInfra!" in exactly 5 words.'
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 50,
            },
        )

        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            await client.aclose()
            return False

        data = response.json()

        if "choices" not in data or len(data["choices"]) == 0:
            print(f"❌ No choices in response: {data}")
            await client.aclose()
            return False

        message = data["choices"][0]["message"]["content"]
        print(f"✅ Generation successful")
        print(f"Response: {message}")

        # Show usage stats
        if "usage" in data:
            usage = data["usage"]
            print(f"\n📊 Token usage:")
            print(f"   Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"   Completion tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"   Total tokens: {usage.get('total_tokens', 'N/A')}")

        await client.aclose()
        return True

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install httpx tomli")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_distillation_integration():
    """Test distillation system with DeepInfra."""
    print("\n" + "="*60)
    print("TEST 2: Distillation System Integration")
    print("="*60)

    try:
        from app.setup.config.settings import load_settings
        from app.infrastructure.distillation.providers.deepinfra_distillator import DeepInfraDistillator
        from app.domain.entities.distillation import DistillationRequest

        # Load settings
        settings = load_settings()

        # Override API key from secrets if not already set
        if not settings.distillation.deepinfra.api_key:
            try:
                import tomli
                secrets_path = project_root / "config" / "local" / ".secrets.toml"
                with open(secrets_path, "rb") as f:
                    secrets = tomli.load(f)
                    api_key = secrets.get("deepinfra", {}).get("API_KEY", "")
                    if api_key:
                        settings.distillation.deepinfra.api_key = api_key
                        print(f"✅ Loaded API key from secrets")
            except Exception as e:
                print(f"⚠️  Could not load API key from secrets: {e}")

        print(f"Distillation enabled: {settings.distillation.enabled}")
        print(f"Provider: {settings.distillation.provider}")
        print(f"DeepInfra Model: {settings.distillation.deepinfra.model}")
        print(f"DeepInfra Base URL: {settings.distillation.deepinfra.base_url}")

        # Create distillator
        distillator = DeepInfraDistillator(settings.distillation)
        print("✅ Distillator created")

        # Test health check
        print("\n🏥 Running health check...")
        health = await distillator.check_health()
        print(f"Health check: {health}")

        if not health["healthy"]:
            print(f"❌ Health check failed: {health.get('error')}")
            await distillator.close()
            return False

        print(f"✅ Health check passed ({health['latency_ms']:.0f}ms)")

        # Test validation
        request = DistillationRequest(
            user_id="test-user-123",
            conversation_id="test-conv-456",
            user_message="What is the price of ETH?",
            conversation_history=[],
            detected_language="en",
        )

        print(f"\n🧪 Testing validation with message: '{request.user_message}'")
        result = await distillator.validate(request)

        print(f"✅ Validation complete:")
        print(f"  Success: {result.success}")
        print(f"  Message: {result.message}")
        print(f"  Reason: {result.reason}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Provider: {result.provider}")
        print(f"  Model: {result.model}")
        print(f"  Latency: {result.latency_ms:.0f}ms")
        print(f"  Tokens: {result.tokens_used}")
        print(f"  Cost: ${result.cost_usd:.6f}")

        await distillator.close()

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "🧪 "*30)
    print("DEEPINFRA API TEST SUITE")
    print("🧪 "*30)

    results = []

    # Test 1: Direct API
    try:
        result1 = await test_deepinfra_direct()
        results.append(("Direct DeepInfra API", result1))
    except Exception as e:
        print(f"Test 1 crashed: {e}")
        results.append(("Direct DeepInfra API", False))

    # Test 2: Distillation Integration
    try:
        result2 = await test_distillation_integration()
        results.append(("Distillation Integration", result2))
    except Exception as e:
        print(f"Test 2 crashed: {e}")
        results.append(("Distillation Integration", False))

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
        print("\n🎉 All tests passed! DeepInfra is configured correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
