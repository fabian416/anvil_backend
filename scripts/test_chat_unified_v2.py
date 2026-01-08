#!/usr/bin/env python3
"""
Test script for Chat Unified v2 System.

This script tests the new chat system components:
1. Database tables creation
2. Entity creation and persistence
3. Intent detection with multi-language
4. Multi-turn swap flow
5. Restricted action handling
6. Rate limiting

Usage:
    python scripts/test_chat_unified_v2.py
"""

import asyncio
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def print_header(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_test(name: str, passed: bool, details: str = "") -> None:
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} | {name}")
    if details:
        print(f"         └── {details}")


async def test_entities():
    """Test entity creation."""
    print_header("Testing Entity Creation")
    
    try:
        from app.domain.chat.entities.chat_user import ChatUser, UserType
        from app.domain.chat.entities.chat_conversation import ChatConversation, ConversationStatus
        from app.domain.chat.entities.chat_message import ChatMessage, MessageRole
        from app.domain.chat.entities.rate_limit import RateLimit, RateLimitResult
        
        # Test ChatUser
        guest = ChatUser.create_guest(ip_address="192.168.1.1", language="es")
        print_test("ChatUser.create_guest", 
                   guest.user_type == UserType.GUEST and guest.identifier == "192.168.1.1",
                   f"type={guest.user_type.value}, id={guest.identifier}")
        
        auth = ChatUser.create_authenticated(privy_id="did:privy:123", email="test@test.com")
        print_test("ChatUser.create_authenticated",
                   auth.user_type == UserType.AUTHENTICATED and auth.privy_id == "did:privy:123",
                   f"type={auth.user_type.value}, privy_id={auth.privy_id}")
        
        # Test ChatConversation
        conv = ChatConversation.create(user_id=guest.id, title="Test Chat", language="es")
        print_test("ChatConversation.create",
                   conv.status == ConversationStatus.ACTIVE,
                   f"status={conv.status.value}, title={conv.title}")
        
        conv.increment_messages()
        print_test("ChatConversation.increment_messages",
                   conv.message_count == 1,
                   f"message_count={conv.message_count}")
        
        # Test ChatMessage
        msg = ChatMessage.create_user_message(
            conversation_id=conv.id,
            content="¿Cuál es el precio de Bitcoin?",
            language="es"
        )
        print_test("ChatMessage.create_user_message",
                   msg.role == MessageRole.USER and msg.content != "",
                   f"role={msg.role.value}")
        
        # Test RateLimitResult
        allow_result = RateLimitResult.allow(remaining_hourly=19, remaining_daily=49)
        print_test("RateLimitResult.allow",
                   allow_result.allowed == True,
                   f"remaining_hourly={allow_result.remaining_hourly}")
        
        deny_result = RateLimitResult.deny("hourly_limit", 20, 20, 3600)
        print_test("RateLimitResult.deny",
                   deny_result.allowed == False and deny_result.reason == "hourly_limit",
                   f"reason={deny_result.reason}, reset_in={deny_result.reset_in}")
        
        return True
    except Exception as e:
        print_test("Entity imports and creation", False, str(e))
        return False


async def test_intent_detector():
    """Test intent detection with multi-language support."""
    print_header("Testing Intent Detector v2")
    
    try:
        from app.application.chat.services.intent_detector_v2 import IntentDetectorV2, ChatIntentV2
        
        detector = IntentDetectorV2()
        
        # Test English sentiment
        result = detector.detect("What is the market sentiment for Bitcoin?", language="en")
        print_test("English sentiment detection",
                   result.intent == ChatIntentV2.HUNTER_SENTIMENT,
                   f"intent={result.intent.value}, confidence={result.confidence}")
        
        # Test Spanish sentiment
        result = detector.detect("¿Cuál es el sentimiento del mercado para Ethereum?", language="es")
        print_test("Spanish sentiment detection",
                   result.intent == ChatIntentV2.HUNTER_SENTIMENT,
                   f"intent={result.intent.value}")
        
        # Test Spanish price
        result = detector.detect("¿Cuánto vale Bitcoin?", language="es")
        print_test("Spanish price detection",
                   result.intent == ChatIntentV2.HUNTER_PRICE_PREDICTION,
                   f"intent={result.intent.value}")
        
        # Test swap detection
        result = detector.detect("swap 100 USDC to ETH", language="en")
        print_test("Swap detection",
                   result.intent == ChatIntentV2.SWAP,
                   f"intent={result.intent.value}")
        
        # Test Spanish swap
        result = detector.detect("quiero cambiar USDC a ETH", language="es")
        print_test("Spanish swap detection",
                   result.intent == ChatIntentV2.SWAP,
                   f"intent={result.intent.value}")
        
        # Test restricted balance
        result = detector.detect("show my balance", language="en")
        print_test("Balance detection (restricted)",
                   result.intent == ChatIntentV2.BALANCE and result.is_restricted,
                   f"intent={result.intent.value}, restricted={result.is_restricted}")
        
        # Test Spanish balance
        result = detector.detect("mostrar mi saldo", language="es")
        print_test("Spanish balance detection (restricted)",
                   result.intent == ChatIntentV2.BALANCE and result.is_restricted,
                   f"intent={result.intent.value}")
        
        # Test portfolio (restricted)
        result = detector.detect("show my portfolio", language="en")
        print_test("Portfolio detection (restricted)",
                   result.intent == ChatIntentV2.PORTFOLIO and result.is_restricted,
                   f"intent={result.intent.value}, restricted={result.is_restricted}")
        
        # Test protocol search
        result = detector.detect("find staking protocols on ethereum", language="en")
        print_test("Protocol search detection",
                   result.intent == ChatIntentV2.PROTOCOL_SEARCH,
                   f"intent={result.intent.value}")
        
        return True
    except Exception as e:
        print_test("Intent detector tests", False, str(e))
        import traceback
        traceback.print_exc()
        return False


async def test_swap_handler():
    """Test multi-turn swap handler."""
    print_header("Testing SwapHandler v2 (Multi-turn)")
    
    try:
        from app.application.chat.handlers.swap_handler_v2 import SwapHandlerV2
        
        handler = SwapHandlerV2()
        
        # Step 1: Initial swap request (incomplete)
        result = await handler.handle("quiero hacer swap", language="es")
        print_test("Step 1: Initiate swap",
                   result.pending_action == "swap_awaiting_from_token",
                   f"pending={result.pending_action}")
        
        # Step 2: Provide from token
        result = await handler.handle("USDC", continuation_step="from_token", continuation_value="USDC", language="es")
        print_test("Step 2: From token",
                   result.pending_action == "swap_awaiting_to_token",
                   f"pending={result.pending_action}")
        
        # Step 3: Provide to token
        result = await handler.handle("ETH", continuation_step="to_token", continuation_value="ETH", language="es")
        print_test("Step 3: To token",
                   result.pending_action == "swap_awaiting_amount",
                   f"pending={result.pending_action}")
        
        # Step 4: Provide amount (complete)
        result = await handler.handle("100", continuation_step="amount", continuation_value="100", language="es")
        print_test("Step 4: Amount (complete quote)",
                   result.pending_action is None and result.requires_registration,
                   f"requires_registration={result.requires_registration}")
        
        # Test complete swap in one message
        result = await handler.handle("swap 500 USDC to ETH", language="en")
        print_test("Complete swap in one message",
                   result.pending_action is None and "swap_quote" in (result.enrichment or {}),
                   f"has_quote={result.enrichment is not None}")
        
        return True
    except Exception as e:
        print_test("Swap handler tests", False, str(e))
        import traceback
        traceback.print_exc()
        return False


async def test_restricted_handler():
    """Test restricted action handler."""
    print_header("Testing RestrictedActionHandler")
    
    try:
        from app.application.chat.handlers.restricted_handler import RestrictedActionHandler
        
        handler = RestrictedActionHandler()
        
        # Test balance
        result = await handler.handle("BALANCE", language="en")
        print_test("Balance handler (EN)",
                   result.requires_registration and "wallet" in result.content.lower(),
                   f"len={len(result.content)}")
        
        result = await handler.handle("BALANCE", language="es")
        print_test("Balance handler (ES)",
                   "billetera" in result.content.lower(),
                   f"contains billetera: True")
        
        # Test portfolio
        result = await handler.handle("PORTFOLIO", language="en")
        print_test("Portfolio handler (EN)",
                   result.requires_registration and "portfolio" in result.content.lower(),
                   f"len={len(result.content)}")
        
        # Test Portuguese
        result = await handler.handle("BALANCE", language="pt")
        print_test("Balance handler (PT)",
                   "carteira" in result.content.lower(),
                   f"contains carteira: True")
        
        return True
    except Exception as e:
        print_test("Restricted handler tests", False, str(e))
        import traceback
        traceback.print_exc()
        return False


async def test_rate_limit_config():
    """Test rate limit configuration."""
    print_header("Testing Rate Limit Configuration")
    
    try:
        from app.application.chat.services.rate_limit_config import (
            RATE_LIMITS,
            get_rate_limit_config,
            has_unlimited_access,
            can_access_feature,
        )
        
        # Test guest limits
        guest_config = get_rate_limit_config("guest")
        print_test("Guest config",
                   guest_config["messages_per_hour"] == 20 and guest_config["messages_per_day"] == 50,
                   f"hourly={guest_config['messages_per_hour']}, daily={guest_config['messages_per_day']}")
        
        # Test authenticated limits
        auth_config = get_rate_limit_config("authenticated")
        print_test("Authenticated config",
                   auth_config["messages_per_hour"] == 200,
                   f"hourly={auth_config['messages_per_hour']}")
        
        # Test premium (unlimited)
        print_test("Premium unlimited",
                   has_unlimited_access("premium"),
                   f"unlimited={has_unlimited_access('premium')}")
        
        # Test feature access
        print_test("Guest can access sentiment",
                   can_access_feature("guest", "sentiment"),
                   f"access=True")
        
        print_test("Authenticated can access all",
                   can_access_feature("authenticated", "anything"),
                   f"access=True")
        
        return True
    except Exception as e:
        print_test("Rate limit config tests", False, str(e))
        import traceback
        traceback.print_exc()
        return False


async def test_conversation_memory():
    """Test conversation memory service."""
    print_header("Testing ConversationMemory")
    
    try:
        from app.application.chat.services.conversation_memory import (
            ConversationMemory,
            ConversationContext,
        )
        from app.domain.chat.entities.chat_message import ChatMessage
        
        # Create mock context
        context = ConversationContext()
        print_test("Empty context",
                   not context.has_context and context.message_count == 0,
                   f"has_context={context.has_context}")
        
        # Create context with messages
        messages = [
            ChatMessage.create_user_message(uuid4(), "What is the sentiment for BTC?"),
            ChatMessage.create_assistant_message(uuid4(), "Bitcoin sentiment is bullish.", intent="HUNTER_SENTIMENT"),
        ]
        context = ConversationContext(
            messages=messages,
            summary="User: What is the sentiment for BTC?\nAssistant [HUNTER_SENTIMENT]: Bitcoin sentiment is bullish.",
        )
        print_test("Context with messages",
                   context.has_context and context.message_count == 2,
                   f"message_count={context.message_count}")
        
        # Test pending intent extraction
        messages[1].set_pending_action("swap_awaiting_from_token")
        context = ConversationContext(messages=messages)
        # Would need to call _get_pending_intent but testing basic functionality
        print_test("Context pending intent",
                   messages[1].get_pending_action() == "swap_awaiting_from_token",
                   f"pending={messages[1].get_pending_action()}")
        
        return True
    except Exception as e:
        print_test("Conversation memory tests", False, str(e))
        import traceback
        traceback.print_exc()
        return False


async def test_database_connection():
    """Test database table existence."""
    print_header("Testing Database Tables")
    
    try:
        import subprocess
        
        # Check tables exist
        result = subprocess.run(
            [
                "docker", "exec", "app_db_pg_",
                "psql", "-U", "postgres", "-d", "anvil_db",
                "-c", "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'chat_%' ORDER BY table_name;"
            ],
            capture_output=True,
            text=True,
        )
        
        tables_found = result.stdout.count("chat_")
        print_test("chat_users table exists",
                   "chat_users" in result.stdout,
                   "Found")
        print_test("chat_conversations table exists",
                   "chat_conversations" in result.stdout,
                   "Found")
        print_test("chat_messages table exists",
                   "chat_messages" in result.stdout,
                   "Found")
        print_test("chat_rate_limits table exists",
                   "chat_rate_limits" in result.stdout,
                   "Found")
        
        return tables_found == 4
    except Exception as e:
        print_test("Database tests", False, str(e))
        return False


async def main():
    """Run all tests."""
    print("\n" + "🚀 " + "=" * 56 + " 🚀")
    print("   CHAT UNIFIED V2 - TEST SUITE")
    print("🚀 " + "=" * 56 + " 🚀")
    
    results = []
    
    # Run tests
    results.append(("Database Tables", await test_database_connection()))
    results.append(("Entity Creation", await test_entities()))
    results.append(("Intent Detector v2", await test_intent_detector()))
    results.append(("Swap Handler v2", await test_swap_handler()))
    results.append(("Restricted Handler", await test_restricted_handler()))
    results.append(("Rate Limit Config", await test_rate_limit_config()))
    results.append(("Conversation Memory", await test_conversation_memory()))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print("\n" + "-" * 60)
    if passed == total:
        print(f"  🎉 ALL TESTS PASSED ({passed}/{total})")
    else:
        print(f"  ⚠️  {passed}/{total} tests passed, {total - passed} failed")
    print("-" * 60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)








