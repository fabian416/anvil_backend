"""
Integration Test: Verify All Shortcut Examples Work for Authenticated Users

Tests all examples from the shortcuts endpoint for authenticated users to ensure:
1. Intent detection works correctly
2. Responses are not generic fallback messages
3. All shortcuts provide meaningful responses
4. Uses dynamic token authentication

Follows CTO Engineering Framework methodology.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from httpx import AsyncClient
import warnings
import os

from .conftest import (
    TestResult,
    CSVReporter,
    create_test_result,
    validate_with_llm,
)

# Generic fallback message that should NOT appear
GENERIC_FALLBACK_MESSAGE = (
    "I'm your AI assistant for DeFi! I can help with market analysis (Hunter AI), "
    "automated trading (ULTRA), lending rates, swaps, and more. "
    "Ask me about protocols, yields, risks, or how to get started. "
    "Sign up for full access to all features."
)


@pytest_asyncio.fixture
async def shortcuts_data(client: AsyncClient):
    """Fetch shortcuts data from API."""
    response = await client.get("/api/v1/public/chat/shortcuts?lang=en")
    if response.status_code != 200:
        # Fallback to old endpoint
        response = await client.get("/api/v1/chat/shortcuts?lang=en")
    assert response.status_code == 200, f"Failed to get shortcuts: {response.text}"
    data = response.json()
    return data["shortcuts"]


@pytest_asyncio.fixture
async def conversation_id(client: AsyncClient, auth_token: str):
    """Create conversation for authenticated user."""
    response = await client.post(
        "/api/v1/conversations",
        json={"title": "Shortcuts Test", "language": "en"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    if response.status_code != 201:
        # Fallback to legacy endpoint
        response = await client.post(
            "/api/v1/user/chat/conversations",
            json={"title": "Shortcuts Test", "language": "en"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
    
    assert response.status_code == 201, f"Failed to create conversation: {response.status_code} {response.text}"
    return response.json()["id"]


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.llm_validation
class TestUserShortcuts:
    """Test all shortcut examples for authenticated users."""
    
    results: list[TestResult] = []
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, client, auth_token, llm_validator):
        """Setup for each test."""
        self.client = client
        self.auth_token = auth_token
        self.llm_validator = llm_validator
        yield
    
    @classmethod
    def teardown_class(cls):
        """Save results after all tests."""
        if cls.results:
            reporter = CSVReporter("shortcuts")
            for result in cls.results:
                reporter.add_result(result)
            csv_path = reporter.write_csv()
            summary_path = reporter.write_summary()
            print(f"\n{'='*60}")
            print(f"Test Results: shortcuts")
            print(f"{'='*60}")
            print(f"Total:   {len(cls.results)}")
            pass_count = sum(1 for r in cls.results if r.status == "PASS")
            fail_count = sum(1 for r in cls.results if r.status == "FAIL")
            partial_count = sum(1 for r in cls.results if r.status == "PARTIAL")
            print(f"PASS:    {pass_count} ({100*pass_count/len(cls.results):.1f}%)")
            print(f"PARTIAL: {partial_count} ({100*partial_count/len(cls.results):.1f}%)")
            print(f"FAIL:    {fail_count} ({100*fail_count/len(cls.results):.1f}%)")
            print(f"{'='*60}")
            print(f"CSV output: {csv_path}")
            print(f"Summary: {summary_path}")
    
    @pytest.mark.asyncio
    async def test_shortcut_intent_detection(
        self,
        shortcuts_data: list,
        conversation_id: str,  # Keep for compatibility but create fresh ones per shortcut
    ):
        """
        Test that all shortcut examples detect the correct intent.
        Creates a fresh conversation per shortcut category to avoid context pollution.
        """
        failures = []
        passes = []
        
        for shortcut in shortcuts_data:
            intent = shortcut["intent"]
            command = shortcut["command"]
            
            # Create fresh conversation for each shortcut category to avoid context pollution
            create_resp = await self.client.post(
                "/api/v1/conversations",
                json={"title": f"Test {command}", "language": "en"},
                headers={"Authorization": f"Bearer {self.auth_token}"},
            )
            if create_resp.status_code == 201:
                fresh_conv_id = create_resp.json()["id"]
            else:
                # Fallback to provided conversation_id if creation fails
                fresh_conv_id = conversation_id
            
            for example in shortcut["examples"]:
                start_time = datetime.now(timezone.utc)
                
                # Try new endpoint first
                response = await self.client.post(
                    f"/api/v1/conversations/{fresh_conv_id}/messages",
                    json={"content": example, "language": "en"},
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                )
                
                if response.status_code == 404:
                    # Fallback to legacy
                    response = await self.client.post(
                        f"/api/v1/user/chat/conversations/{fresh_conv_id}/messages",
                        json={"content": example, "language": "en"},
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                    )
                
                elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                
                if response.status_code not in (200, 201):
                    failures.append({
                        "shortcut": command,
                        "intent": intent,
                        "example": example,
                        "error": f"HTTP {response.status_code}",
                    })
                    continue
                
                data = response.json()
                detected_intent = data.get("routing", {}).get("intent", "unknown")
                content = data.get("agent_message", {}).get("content", "")
                
                # Acceptable intent mappings (shortcut intent -> valid detected intents)
                # Some shortcuts may route through different handlers that achieve the same result
                acceptable_intents = {
                    "swap": ["swap", "moonpay_swap", "swap_continue", "supervisor_workflow"],
                    "money_market": ["money_market", "supervisor_workflow", "lending"],
                    "lending": ["lending", "lending_continue", "supervisor_workflow"],
                    "buy": ["buy", "buy_continue", "moonpay_swap"],
                    "send": ["send", "transfer", "supervisor_workflow"],
                    "portfolio": ["portfolio", "supervisor_workflow", "balance"],
                    "balance": ["balance", "supervisor_workflow", "portfolio"],
                    "activity": ["activity", "supervisor_workflow"],
                    "receive": ["receive", "supervisor_workflow"],
                }
                
                # Check if detected intent is acceptable for this shortcut
                valid_intents = acceptable_intents.get(intent.lower(), [intent.lower()])
                status = "PASS" if detected_intent.lower() in valid_intents else "FAIL"
                
                if status == "FAIL":
                    failures.append({
                        "shortcut": command,
                        "intent": intent,
                        "example": example,
                        "detected": detected_intent.lower(),
                    })
                else:
                    passes.append(example)
                
                # LLM validation
                llm_validation = await validate_with_llm(
                    self.llm_validator,
                    f"shortcut_{intent}",
                    example,
                    content,
                    f"System should detect intent as '{intent}' and provide relevant response",
                    {"expected_intent": intent, "detected_intent": detected_intent}
                )
                
                # Record result using correct signature
                test_case = {
                    "category": "shortcuts",
                    "subcategory": intent,
                    "input": example,
                    "expected_agent": intent,
                    "requires_execute": False,  # Intent detection doesn't need execute data
                }
                response_data = {
                    "agent_message": {"content": content[:500]},
                    "routing": {
                        "intent": detected_intent,
                        "agents_used": [detected_intent.lower()],  # Must be a list
                        "handler": data.get("routing", {}).get("handler", ""),
                        "user_type": data.get("routing", {}).get("user_type", "authenticated"),
                    },
                }
                result = create_test_result(
                    test_id=f"shortcut_{intent}_{command.replace(' ', '_')}",
                    test_case=test_case,
                    response_data=response_data,
                    response_time_ms=int(elapsed_ms),
                    llm_validation=llm_validation,
                )
                TestUserShortcuts.results.append(result)
        
        # Summary
        total = len(passes) + len(failures)
        print(f"\n✅ Intent Detection: {len(passes)}/{total} passed")
        
        if failures:
            error_msg = "\n".join([
                f"❌ {f['shortcut']} ({f['intent']}): '{f['example']}' → detected as '{f.get('detected', f.get('error'))}'"
                for f in failures[:10]  # Show first 10
            ])
            if len(failures) > 10:
                error_msg += f"\n... and {len(failures) - 10} more failures"
            pytest.fail(f"Intent detection failures ({len(failures)}/{total}):\n{error_msg}")


    @pytest.mark.asyncio
    async def test_shortcut_no_generic_fallback(
        self,
        shortcuts_data: list,
        conversation_id: str,
    ):
        """
        Test that all shortcut examples return meaningful responses, not generic fallback.
        """
        failures = []
        passes = []
        
        for shortcut in shortcuts_data:
            intent = shortcut["intent"]
            command = shortcut["command"]
            
            for example in shortcut["examples"]:
                start_time = datetime.now(timezone.utc)
                
                # Try new endpoint first
                response = await self.client.post(
                    f"/api/v1/conversations/{conversation_id}/messages",
                    json={"content": example, "language": "en"},
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                )
                
                if response.status_code == 404:
                    response = await self.client.post(
                        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
                        json={"content": example, "language": "en"},
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                    )
                
                elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                
                if response.status_code not in (200, 201):
                    continue
                
                data = response.json()
                content = data.get("agent_message", {}).get("content", "")
                
                # Check if response is generic fallback
                is_generic = GENERIC_FALLBACK_MESSAGE in content
                status = "FAIL" if is_generic else "PASS"
                
                if is_generic:
                    failures.append({
                        "shortcut": command,
                        "intent": intent,
                        "example": example,
                    })
                else:
                    passes.append(example)
                
                # Record result using correct signature
                detected = data.get("routing", {}).get("intent", "unknown")
                test_case = {
                    "category": "shortcuts",
                    "subcategory": f"{intent}_fallback",
                    "input": example,
                    "expected_agent": intent,
                }
                response_data = {
                    "agent_message": {"content": content[:500]},
                    "routing": {
                        "intent": detected,
                        "agents_used": [detected.lower()],
                        "handler": data.get("routing", {}).get("handler", ""),
                        "user_type": "authenticated",
                    },
                }
                result = create_test_result(
                    test_id=f"shortcut_fallback_{intent}_{command.replace(' ', '_')}",
                    test_case=test_case,
                    response_data=response_data,
                    response_time_ms=int(elapsed_ms),
                )
                TestUserShortcuts.results.append(result)
        
        total = len(passes) + len(failures)
        print(f"\n✅ No Generic Fallback: {len(passes)}/{total} passed")
        
        if failures:
            error_msg = "\n".join([
                f"❌ {f['shortcut']} ({f['intent']}): '{f['example']}' → Generic fallback"
                for f in failures[:10]
            ])
            pytest.fail(f"Generic fallback detected ({len(failures)}/{total}):\n{error_msg}")
    
    @pytest.mark.asyncio
    async def test_shortcut_meaningful_content(
        self,
        shortcuts_data: list,
        conversation_id: str,
    ):
        """
        Test that all shortcut examples return responses with meaningful content.
        """
        failures = []
        passes = []
        
        # Intent-specific keywords
        intent_keywords = {
            "lending": ["lending", "vault", "yield", "morpho", "deposit", "apy", "rate"],
            "money_market": ["aave", "compound", "rate", "supply", "lending", "borrow"],
            "swap": ["swap", "quote", "rate", "bridge", "exchange", "price", "usdc", "eth"],
            "portfolio": ["portfolio", "dashboard", "holdings", "assets", "tokens", "balance"],
            "balance": ["balance", "wallet", "account", "holdings"],
            "activity": ["transaction", "history", "activity", "recent"],
            "receive": ["address", "wallet", "receive", "deposit", "0x"],
            "buy": ["buy", "crypto", "card", "purchase"],
            "send": ["send", "transfer", "wallet", "recipient"],
        }
        
        for shortcut in shortcuts_data:
            intent = shortcut["intent"]
            command = shortcut["command"]
            
            for example in shortcut["examples"]:
                start_time = datetime.now(timezone.utc)
                
                response = await self.client.post(
                    f"/api/v1/conversations/{conversation_id}/messages",
                    json={"content": example, "language": "en"},
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                )
                
                if response.status_code == 404:
                    response = await self.client.post(
                        f"/api/v1/user/chat/conversations/{conversation_id}/messages",
                        json={"content": example, "language": "en"},
                        headers={"Authorization": f"Bearer {self.auth_token}"},
                    )
                
                elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                
                if response.status_code not in (200, 201):
                    continue
                
                data = response.json()
                content = data.get("agent_message", {}).get("content", "").lower()
                
                # Check minimum length
                if len(content) < 50:
                    failures.append({
                        "shortcut": command,
                        "intent": intent,
                        "example": example,
                        "issue": f"Too short ({len(content)} chars)",
                    })
                    status = "FAIL"
                elif intent in intent_keywords:
                    keywords = intent_keywords[intent]
                    found = any(kw in content for kw in keywords)
                    if not found:
                        failures.append({
                            "shortcut": command,
                            "intent": intent,
                            "example": example,
                            "issue": "No intent keywords",
                        })
                        status = "FAIL"
                    else:
                        passes.append(example)
                        status = "PASS"
                else:
                    passes.append(example)
                    status = "PASS"
                
                # Record result using correct signature
                detected = data.get("routing", {}).get("intent", "unknown")
                test_case = {
                    "category": "shortcuts",
                    "subcategory": f"{intent}_content",
                    "input": example,
                    "expected_agent": intent,
                }
                response_data = {
                    "agent_message": {"content": content[:500]},
                    "routing": {
                        "intent": detected,
                        "agents_used": [detected.lower()],
                        "handler": data.get("routing", {}).get("handler", ""),
                        "user_type": "authenticated",
                    },
                }
                result = create_test_result(
                    test_id=f"shortcut_content_{intent}_{command.replace(' ', '_')}",
                    test_case=test_case,
                    response_data=response_data,
                    response_time_ms=int(elapsed_ms),
                )
                TestUserShortcuts.results.append(result)
        
        total = len(passes) + len(failures)
        print(f"\n✅ Meaningful Content: {len(passes)}/{total} passed")
        
        if failures:
            error_msg = "\n".join([
                f"❌ {f['shortcut']} ({f['intent']}): '{f['example']}' → {f['issue']}"
                for f in failures[:10]
            ])
            pytest.fail(f"Content quality issues ({len(failures)}/{total}):\n{error_msg}")
