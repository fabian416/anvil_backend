#!/usr/bin/env python3
"""
Test script for Vertex AI / Gemini API integration.

Tests:
1. Configuration loading
2. API authentication
3. Simple generation test
4. Distillation integration test
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


async def test_google_generative_ai():
    """Test direct Google Generative AI SDK (new google.genai package)."""
    print("\n" + "=" * 60)
    print("TEST 1: Google Genai SDK (Gemini API)")
    print("=" * 60)

    try:
        import google.genai as genai
        from google.genai import types

        # Load API key from secrets
        import tomli

        secrets_path = project_root / "config" / "local" / ".secrets.toml"
        with open(secrets_path, "rb") as f:
            secrets = tomli.load(f)
            api_key = secrets.get("vertex_ai", {}).get("API_KEY", "")

        if not api_key:
            print("❌ No API key found in .secrets.toml")
            return False

        print(f"✅ API Key loaded: {api_key[:20]}...")

        # Initialize client
        client = genai.Client(api_key=api_key)
        print("✅ Client initialized")

        # List available models
        print("\n📋 Listing available models...")
        try:
            models = client.models.list()
            print(f"✅ Found {len(list(models))} models")

            # Re-list to use (iterator consumed)
            models = client.models.list()
            gemini_models = [m.name for m in models if "gemini" in m.name.lower()]
            if gemini_models:
                print(f"   Gemini models: {', '.join(gemini_models[:5])}")
        except Exception as e:
            print(f"⚠️  Could not list models: {e}")

        # Test with gemini-2.0-flash-exp (latest)
        print("\n🧪 Testing generation with gemini-2.0-flash-exp...")
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents='Say "Hello from Gemini!" in exactly 5 words.',
            )
            print(f"✅ Generation successful")
            print(f"Response: {response.text}")
            return True
        except Exception as e:
            # Try fallback model
            print(f"⚠️  gemini-2.0-flash-exp failed: {e}")
            print("\n🧪 Trying fallback model: gemini-1.5-flash-latest...")

            response = client.models.generate_content(
                model="gemini-1.5-flash-latest",
                contents='Say "Hello from Gemini!" in exactly 5 words.',
            )
            print(f"✅ Generation successful")
            print(f"Response: {response.text}")
            return True

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install google-genai")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_vertex_ai_direct():
    """Test Vertex AI SDK directly."""
    print("\n" + "=" * 60)
    print("TEST 2: Vertex AI SDK (with credentials)")
    print("=" * 60)

    try:
        from google.cloud import aiplatform
        from vertexai.generative_models import GenerativeModel

        # Load settings
        from app.setup.config.settings import load_settings

        settings = load_settings()

        vertex_settings = settings.distillation.vertex_ai

        print(f"Project ID: {vertex_settings.project_id}")
        print(f"Project Number: {vertex_settings.project_number}")
        print(f"Location: {vertex_settings.location}")
        print(f"Model: {vertex_settings.model}")

        # Initialize (with API key if available)
        if vertex_settings.api_key:
            os.environ["GOOGLE_API_KEY"] = vertex_settings.api_key
            print("✅ Using API Key authentication")
        else:
            print("⚠️  No API key - using default credentials")

        aiplatform.init(
            project=vertex_settings.project_id,
            location=vertex_settings.location,
        )
        print("✅ Vertex AI initialized")

        # Test generation
        model = GenerativeModel(vertex_settings.model)
        response = model.generate_content(
            "Say 'Hello from Vertex AI!' in one sentence."
        )
        print(f"✅ Generation successful")
        print(f"Response: {response.text}")

        return True

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install google-cloud-aiplatform")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_distillation_integration():
    """Test distillation system with Vertex AI."""
    print("\n" + "=" * 60)
    print("TEST 3: Distillation System Integration")
    print("=" * 60)

    try:
        from app.setup.config.settings import load_settings
        from app.infrastructure.distillation.providers.vertex_ai_distillator import (
            VertexAIDistillator,
        )
        from app.domain.entities.distillation import DistillationRequest

        # Load settings
        settings = load_settings()

        # Override API key from secrets if not already set
        if not settings.distillation.vertex_ai.api_key:
            try:
                import tomli

                secrets_path = project_root / "config" / "local" / ".secrets.toml"
                with open(secrets_path, "rb") as f:
                    secrets = tomli.load(f)
                    api_key = secrets.get("vertex_ai", {}).get("API_KEY", "")
                    if api_key:
                        settings.distillation.vertex_ai.api_key = api_key
                        print(f"✅ Loaded API key from secrets")
            except Exception as e:
                print(f"⚠️  Could not load API key from secrets: {e}")

        print(f"Distillation enabled: {settings.distillation.enabled}")
        print(f"Provider: {settings.distillation.provider}")
        print(f"Vertex AI Project: {settings.distillation.vertex_ai.project_id}")
        print(f"Vertex AI Model: {settings.distillation.vertex_ai.model}")

        # Create distillator
        distillator = VertexAIDistillator(settings.distillation)
        print("✅ Distillator created")

        # Test health check
        health = await distillator.check_health()
        print(f"Health check: {health}")

        if not health["healthy"]:
            print(f"❌ Health check failed: {health.get('error')}")
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

        print(f"Testing validation with message: '{request.user_message}'")
        result = await distillator.validate(request)

        print(f"✅ Validation complete:")
        print(f"  Success: {result.success}")
        print(f"  Message: {result.message}")
        print(f"  Reason: {result.reason}")
        print(f"  Confidence: {result.confidence:.2f}")
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
    print("\n" + "🧪 " * 30)
    print("VERTEX AI / GEMINI API TEST SUITE")
    print("🧪 " * 30)

    results = []

    # Test 1: Google Generative AI SDK
    try:
        result1 = await test_google_generative_ai()
        results.append(("Google Generative AI SDK", result1))
    except Exception as e:
        print(f"Test 1 crashed: {e}")
        results.append(("Google Generative AI SDK", False))

    # Test 2: Vertex AI SDK
    try:
        result2 = await test_vertex_ai_direct()
        results.append(("Vertex AI SDK", result2))
    except Exception as e:
        print(f"Test 2 crashed: {e}")
        results.append(("Vertex AI SDK", False))

    # Test 3: Distillation Integration
    try:
        result3 = await test_distillation_integration()
        results.append(("Distillation Integration", result3))
    except Exception as e:
        print(f"Test 3 crashed: {e}")
        results.append(("Distillation Integration", False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Vertex AI is configured correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
