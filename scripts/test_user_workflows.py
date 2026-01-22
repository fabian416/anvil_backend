#!/usr/bin/env python3
"""
Test script for AGNO User Workflow Agents.

Tests all workflow agents and generates CSV output:
- swap_workflow
- lending_workflow
- transfer_workflow
- buy_workflow
- money_market_workflow
"""

import asyncio
import csv
import json
import time
from datetime import datetime
from typing import Any

import httpx

# Configuration
BASE_URL = "http://localhost:8080"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdXRoX3Nlc3Npb25faWQiOiJQYVJLMEhZdWZrdmp1OHlsMWlZTkU5Q2NJcWp2dnRiaF9WTG4xVWQtRl9FIiwiZXhwIjoxNzY5MDYzNTQ4fQ.MBmBbB7Uwt_Rg47q8DSwJUxlrvLpaHeeLljaL2Y2Iv0"
OUTPUT_FILE = "docs/output/user_workflows.csv"

# Test cases for each workflow
TEST_CASES = [
    # Swap Workflow Tests
    {
        "test_id": 1,
        "input": "swap 1 ETH to USDC",
        "language": "en",
        "expected_workflow": "swap_workflow",
        "category": "swap",
    },
    {
        "test_id": 2,
        "input": "exchange 100 USDC for ETH",
        "language": "en",
        "expected_workflow": "swap_workflow",
        "category": "swap",
    },
    {
        "test_id": 3,
        "input": "convert 0.5 ETH to DAI",
        "language": "en",
        "expected_workflow": "swap_workflow",
        "category": "swap",
    },
    {
        "test_id": 4,
        "input": "quiero cambiar 50 USDC por ETH",
        "language": "es",
        "expected_workflow": "swap_workflow",
        "category": "swap",
    },
    
    # Lending Workflow Tests
    {
        "test_id": 5,
        "input": "deposit 1000 USDC",
        "language": "en",
        "expected_workflow": "lending_workflow",
        "category": "lending",
    },
    {
        "test_id": 6,
        "input": "lend 0.5 ETH",
        "language": "en",
        "expected_workflow": "lending_workflow",
        "category": "lending",
    },
    {
        "test_id": 7,
        "input": "earn yield on 500 DAI",
        "language": "en",
        "expected_workflow": "lending_workflow",
        "category": "lending",
    },
    {
        "test_id": 8,
        "input": "depositar 1000 USDC en morpho",
        "language": "es",
        "expected_workflow": "lending_workflow",
        "category": "lending",
    },
    
    # Transfer Workflow Tests
    {
        "test_id": 9,
        "input": "send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "language": "en",
        "expected_workflow": "transfer_workflow",
        "category": "transfer",
    },
    {
        "test_id": 10,
        "input": "transfer 0.5 ETH to my friend",
        "language": "en",
        "expected_workflow": "transfer_workflow",
        "category": "transfer",
    },
    {
        "test_id": 11,
        "input": "send ETH",
        "language": "en",
        "expected_workflow": "transfer_workflow",
        "category": "transfer",
    },
    {
        "test_id": 12,
        "input": "enviar 50 USDC a 0x123456789abcdef0123456789abcdef012345678",
        "language": "es",
        "expected_workflow": "transfer_workflow",
        "category": "transfer",
    },
    
    # Buy Workflow Tests
    {
        "test_id": 13,
        "input": "buy $100 of ETH",
        "language": "en",
        "expected_workflow": "buy_workflow",
        "category": "buy",
    },
    {
        "test_id": 14,
        "input": "purchase 50 dollars of USDC",
        "language": "en",
        "expected_workflow": "buy_workflow",
        "category": "buy",
    },
    {
        "test_id": 15,
        "input": "buy crypto",
        "language": "en",
        "expected_workflow": "buy_workflow",
        "category": "buy",
    },
    {
        "test_id": 16,
        "input": "comprar $200 de BTC",
        "language": "es",
        "expected_workflow": "buy_workflow",
        "category": "buy",
    },
    
    # Money Market Workflow Tests
    {
        "test_id": 17,
        "input": "compare USDC rates",
        "language": "en",
        "expected_workflow": "money_market_workflow",
        "category": "money_market",
    },
    {
        "test_id": 18,
        "input": "best lending rates for ETH",
        "language": "en",
        "expected_workflow": "money_market_workflow",
        "category": "money_market",
    },
    {
        "test_id": 19,
        "input": "where should I deposit DAI",
        "language": "en",
        "expected_workflow": "money_market_workflow",
        "category": "money_market",
    },
    {
        "test_id": 20,
        "input": "comparar tasas de USDC",
        "language": "es",
        "expected_workflow": "money_market_workflow",
        "category": "money_market",
    },
    
    # Edge Cases - Should NOT trigger workflow agents
    {
        "test_id": 21,
        "input": "what is the price of ETH",
        "language": "en",
        "expected_workflow": "hunter_ai",
        "category": "price_query",
    },
    {
        "test_id": 22,
        "input": "best yield for USDC",
        "language": "en",
        "expected_workflow": "defi_yield",
        "category": "yield_info",
    },
    {
        "test_id": 23,
        "input": "my portfolio",
        "language": "en",
        "expected_workflow": "portfolio",
        "category": "portfolio",
    },
    {
        "test_id": 24,
        "input": "my wallets",
        "language": "en",
        "expected_workflow": "wallet",
        "category": "wallet",
    },
    {
        "test_id": 25,
        "input": "transaction history",
        "language": "en",
        "expected_workflow": "transaction_history",
        "category": "transactions",
    },
    
    # Multi-language tests
    {
        "test_id": 26,
        "input": "我想交换 1 ETH 到 USDC",
        "language": "zh",
        "expected_workflow": "swap_workflow",
        "category": "swap_multilang",
    },
    {
        "test_id": 27,
        "input": "depositar 500 USDC",
        "language": "pt",
        "expected_workflow": "lending_workflow",
        "category": "lending_multilang",
    },
    {
        "test_id": 28,
        "input": "comprar $100 de ETH",
        "language": "pt",
        "expected_workflow": "buy_workflow",
        "category": "buy_multilang",
    },
]


async def get_or_create_conversation(client: httpx.AsyncClient) -> str:
    """Get existing conversation or create a new one."""
    # Try to list conversations first
    response = await client.get(
        f"{BASE_URL}/api/v1/conversations",
        headers={"Authorization": f"Bearer {JWT_TOKEN}"},
    )
    
    if response.status_code == 200:
        data = response.json()
        # Response is a list directly
        conversations = data if isinstance(data, list) else data.get("conversations", [])
        if conversations:
            return conversations[0]["id"]
    
    # Create new conversation
    response = await client.post(
        f"{BASE_URL}/api/v1/conversations",
        headers={"Authorization": f"Bearer {JWT_TOKEN}"},
        json={"title": "Workflow Test Session"},
    )
    
    if response.status_code in (200, 201):
        data = response.json()
        return data.get("id") or data.get("conversation_id")
    
    raise Exception(f"Failed to create conversation: {response.text}")


async def send_message(
    client: httpx.AsyncClient,
    conversation_id: str,
    content: str,
    language: str = "en",
) -> dict[str, Any]:
    """Send message to conversation and get response."""
    
    start_time = time.time()
    
    response = await client.post(
        f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages",
        headers={
            "Authorization": f"Bearer {JWT_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "content": content,
            "language": language,
        },
        timeout=60.0,
    )
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    if response.status_code not in (200, 201):
        return {
            "content": f"ERROR: {response.status_code} - {response.text[:200]}",
            "agents_used": "",
            "sources": "",
            "handler": "error",
            "workflow_type": "error",
            "response_time_ms": elapsed_ms,
            "execute_data": None,
            "error": True,
        }
    
    data = response.json()
    
    # Extract from nested response structure
    routing = data.get("routing", {})
    enrichment = data.get("enrichment", {})
    agent_message = data.get("agent_message", {})
    
    # Check for error in enrichment metadata
    error_msg = enrichment.get("metadata", {}).get("error", "")
    
    return {
        "content": agent_message.get("content", "")[:500],
        "agents_used": ",".join(routing.get("agents_used", []) or enrichment.get("agents_used", [])),
        "sources": json.dumps(agent_message.get("sources", []))[:200] if agent_message.get("sources") else "",
        "handler": routing.get("handler", ""),
        "workflow_type": enrichment.get("workflow_type", ""),
        "response_time_ms": elapsed_ms,
        "execute_data": data.get("execute"),
        "user_type": routing.get("user_type", ""),
        "error": bool(error_msg),
        "error_message": error_msg,
    }


def analyze_result(test_case: dict, result: dict) -> tuple[str, str]:
    """Analyze test result and determine status."""
    
    expected = test_case["expected_workflow"]
    agents_used = result.get("agents_used", "")
    content = result.get("content", "")
    execute_data = result.get("execute_data")
    
    # Check for errors
    if result.get("error"):
        return "FAIL", f"FAIL: Error response - {content[:100]}"
    
    # For workflow agents, check if execute_data is present
    workflow_agents = ["swap_workflow", "lending_workflow", "transfer_workflow", "buy_workflow", "money_market_workflow"]
    
    if expected in workflow_agents:
        if expected in agents_used:
            if execute_data:
                return "PASS", f"PASS: {expected} executed with execute_data"
            else:
                return "PARTIAL", f"PARTIAL: {expected} routed but no execute_data"
        else:
            # Check if response indicates workflow behavior
            workflow_keywords = {
                "swap_workflow": ["swap", "exchange", "convert", "quote"],
                "lending_workflow": ["deposit", "vault", "apy", "yield"],
                "transfer_workflow": ["send", "transfer", "recipient", "address"],
                "buy_workflow": ["buy", "purchase", "payment", "moonpay"],
                "money_market_workflow": ["compare", "rates", "aave", "compound", "morpho"],
            }
            
            keywords = workflow_keywords.get(expected, [])
            content_lower = content.lower()
            
            if any(kw in content_lower for kw in keywords):
                return "PARTIAL", f"PARTIAL: Content suggests {expected} but agents_used={agents_used}"
            else:
                return "FAIL", f"FAIL: Expected {expected}, got agents_used={agents_used}"
    else:
        # For non-workflow agents
        if expected in agents_used:
            return "PASS", f"PASS: {expected} correctly routed"
        else:
            return "PARTIAL", f"PARTIAL: Expected {expected}, got {agents_used}"


async def run_tests():
    """Run all workflow tests and generate CSV output."""
    
    results = []
    
    async with httpx.AsyncClient() as client:
        # Get or create conversation
        try:
            conversation_id = await get_or_create_conversation(client)
            print(f"Using conversation: {conversation_id}")
        except Exception as e:
            print(f"Failed to get conversation: {e}")
            return
        
        # Run each test
        for test_case in TEST_CASES:
            test_id = test_case["test_id"]
            input_text = test_case["input"]
            language = test_case["language"]
            category = test_case["category"]
            
            print(f"\n[{test_id}] Testing: {input_text[:50]}...")
            
            try:
                result = await send_message(client, conversation_id, input_text, language)
                status, analysis = analyze_result(test_case, result)
                
                print(f"    Status: {status}")
                print(f"    Agents: {result.get('agents_used', 'N/A')}")
                print(f"    Execute Data: {'Yes' if result.get('execute_data') else 'No'}")
                print(f"    Time: {result.get('response_time_ms', 0)}ms")
                
                results.append({
                    "test_id": test_id,
                    "timestamp": datetime.now().isoformat(),
                    "input": input_text,
                    "language": language,
                    "category": category,
                    "expected_workflow": test_case["expected_workflow"],
                    "output": result.get("content", "")[:400],
                    "agents_used": result.get("agents_used", ""),
                    "sources": result.get("sources", ""),
                    "handler": result.get("handler", ""),
                    "workflow_type": result.get("workflow_type", ""),
                    "response_time_ms": result.get("response_time_ms", 0),
                    "has_execute_data": "Yes" if result.get("execute_data") else "No",
                    "execute_data_type": result.get("execute_data", {}).get("action_type", "") if result.get("execute_data") else "",
                    "user_type": result.get("user_type", ""),
                    "status": status,
                    "analysis": analysis,
                })
                
            except Exception as e:
                print(f"    Error: {e}")
                results.append({
                    "test_id": test_id,
                    "timestamp": datetime.now().isoformat(),
                    "input": input_text,
                    "language": language,
                    "category": category,
                    "expected_workflow": test_case["expected_workflow"],
                    "output": f"EXCEPTION: {str(e)[:200]}",
                    "agents_used": "",
                    "sources": "",
                    "handler": "exception",
                    "workflow_type": "",
                    "response_time_ms": 0,
                    "has_execute_data": "No",
                    "execute_data_type": "",
                    "user_type": "",
                    "status": "ERROR",
                    "analysis": f"ERROR: {str(e)[:100]}",
                })
            
            # Small delay between requests
            await asyncio.sleep(1)
    
    # Write CSV output
    fieldnames = [
        "test_id", "timestamp", "input", "language", "category", "expected_workflow",
        "output", "agents_used", "sources", "handler", "workflow_type",
        "response_time_ms", "has_execute_data", "execute_data_type", "user_type",
        "status", "analysis"
    ]
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n{'='*60}")
    print(f"Results written to: {OUTPUT_FILE}")
    print(f"{'='*60}")
    
    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    failed = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
    
    print(f"\nSummary:")
    print(f"  Total: {total}")
    print(f"  PASS: {passed} ({passed/total*100:.1f}%)")
    print(f"  PARTIAL: {partial} ({partial/total*100:.1f}%)")
    print(f"  FAIL/ERROR: {failed} ({failed/total*100:.1f}%)")
    
    # Category breakdown
    print(f"\nBy Category:")
    categories = set(r["category"] for r in results)
    for cat in sorted(categories):
        cat_results = [r for r in results if r["category"] == cat]
        cat_passed = sum(1 for r in cat_results if r["status"] == "PASS")
        print(f"  {cat}: {cat_passed}/{len(cat_results)} PASS")


if __name__ == "__main__":
    asyncio.run(run_tests())
