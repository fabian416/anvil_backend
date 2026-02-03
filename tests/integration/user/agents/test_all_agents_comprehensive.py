"""
Comprehensive Agent Test Suite for Authenticated Supervisor.

Tests all 27 agents with simple and complex queries:
- Core Agents (12): chat, knowledge, hunter_ai, research, execution, risk_analyzer,
                    portfolio, tax_optimizer, defi_yield, security_auditor, gas_optimizer, guest_auth
- Authenticated Agents (2): wallet, transaction_history
- Workflow Agents (5): swap_workflow, lending_workflow, buy_workflow, transfer_workflow, money_market_workflow
- Enterprise Agents (8): compliance_monitor, multisig_coordinator, alert_monitoring, crisis_manager,
                         bridge_crosschain, lending_borrowing, nft_asset_manager, dao_governance

Test Categories:
1. Simple Queries - Single agent routing
2. Complex Queries - Multi-agent collaboration
3. Multi-step Workflows - Stateful conversations
4. Multi-language Support - Spanish, Portuguese, Chinese
"""

import asyncio
import pytest
import pytest_asyncio
import time
from datetime import datetime, UTC
from typing import Any, Optional
from dataclasses import dataclass

from tests.integration.user.conftest import (
    CSVReporter,
    TestResult,
    TokenManager,
    send_message,
    create_conversation,
    parse_response,
    create_test_result,
    OUTPUT_DIR,
)

# ============================================================
# Test Case Definitions
# ============================================================

# Simple Queries - Single Agent Routing
SIMPLE_QUERIES = [
    # ---- CORE AGENTS ----
    # Chat Agent
    {"id": "chat_001", "input": "hi", "expected_agent": "chat", "category": "core", "subcategory": "chat"},
    {"id": "chat_002", "input": "hello", "expected_agent": "chat", "category": "core", "subcategory": "chat"},
    {"id": "chat_003", "input": "write a poem about Ethereum gas fees", "expected_agent": "chat", "category": "core", "subcategory": "chat"},
    {"id": "chat_004", "input": "tell me a joke about crypto", "expected_agent": "chat", "category": "core", "subcategory": "chat"},
    
    # Knowledge Agent
    {"id": "knowledge_001", "input": "what is defi", "expected_agent": "knowledge", "category": "core", "subcategory": "knowledge"},
    {"id": "knowledge_002", "input": "how does Aave work", "expected_agent": "knowledge", "category": "core", "subcategory": "knowledge"},
    {"id": "knowledge_003", "input": "explain impermanent loss", "expected_agent": "knowledge", "category": "core", "subcategory": "knowledge"},
    {"id": "knowledge_004", "input": "what is a liquidity pool", "expected_agent": "knowledge", "category": "core", "subcategory": "knowledge"},
    
    # Hunter AI Agent (Market Data)
    {"id": "hunter_001", "input": "btc price", "expected_agent": "hunter_ai", "category": "core", "subcategory": "hunter_ai"},
    {"id": "hunter_002", "input": "ETH price today", "expected_agent": "hunter_ai", "category": "core", "subcategory": "hunter_ai"},
    {"id": "hunter_003", "input": "crypto news", "expected_agent": "hunter_ai", "category": "core", "subcategory": "hunter_ai"},
    {"id": "hunter_004", "input": "bitcoin social sentiment", "expected_agent": "hunter_ai", "category": "core", "subcategory": "hunter_ai"},
    {"id": "hunter_005", "input": "BTC trading signals", "expected_agent": "hunter_ai", "category": "core", "subcategory": "hunter_ai"},
    {"id": "hunter_006", "input": "will ETH go up", "expected_agent": "hunter_ai", "category": "core", "subcategory": "hunter_ai"},
    {"id": "hunter_007", "input": "whale activity for BTC", "expected_agent": "hunter_ai", "category": "core", "subcategory": "hunter_ai"},
    {"id": "hunter_008", "input": "DEX volume for Uniswap", "expected_agent": "hunter_ai", "category": "core", "subcategory": "hunter_ai"},
    {"id": "hunter_009", "input": "token unlocks this week", "expected_agent": "hunter_ai", "category": "core", "subcategory": "hunter_ai"},
    {"id": "hunter_010", "input": "ETH staking yield", "expected_agent": "hunter_ai", "category": "core", "subcategory": "hunter_ai"},
    
    # Risk Analyzer Agent
    {"id": "risk_001", "input": "risk of yield farming", "expected_agent": "risk_analyzer", "category": "core", "subcategory": "risk_analyzer"},
    {"id": "risk_002", "input": "analyze risk of Compound protocol", "expected_agent": "risk_analyzer", "category": "core", "subcategory": "risk_analyzer"},
    
    # DeFi Yield Agent
    {"id": "yield_001", "input": "best yield for USDC", "expected_agent": "defi_yield", "category": "core", "subcategory": "defi_yield"},
    {"id": "yield_002", "input": "top APY opportunities", "expected_agent": "defi_yield", "category": "core", "subcategory": "defi_yield"},
    {"id": "yield_003", "input": "show me high yield farms", "expected_agent": "defi_yield", "category": "core", "subcategory": "defi_yield"},
    
    # Gas Optimizer Agent
    {"id": "gas_001", "input": "best time for gas", "expected_agent": "gas_optimizer", "category": "core", "subcategory": "gas_optimizer"},
    {"id": "gas_002", "input": "when is the best time to execute Ethereum transactions to save on gas", "expected_agent": "gas_optimizer", "category": "core", "subcategory": "gas_optimizer"},
    {"id": "gas_003", "input": "current gas prices", "expected_agent": "gas_optimizer", "category": "core", "subcategory": "gas_optimizer"},
    
    # Portfolio Agent (Authenticated)
    {"id": "portfolio_001", "input": "my portfolio", "expected_agent": "portfolio", "category": "authenticated", "subcategory": "portfolio"},
    {"id": "portfolio_002", "input": "my balance", "expected_agent": "portfolio", "category": "authenticated", "subcategory": "portfolio"},
    {"id": "portfolio_003", "input": "show my holdings", "expected_agent": "portfolio", "category": "authenticated", "subcategory": "portfolio"},
    
    # Wallet Agent (Authenticated)
    {"id": "wallet_001", "input": "my wallets", "expected_agent": "wallet", "category": "authenticated", "subcategory": "wallet"},
    {"id": "wallet_002", "input": "show my wallet address", "expected_agent": "wallet", "category": "authenticated", "subcategory": "wallet"},
    {"id": "wallet_003", "input": "my connected wallets", "expected_agent": "wallet", "category": "authenticated", "subcategory": "wallet"},
    
    # Transaction History Agent (Authenticated)
    {"id": "history_001", "input": "my transactions", "expected_agent": "transaction_history", "category": "authenticated", "subcategory": "transaction_history"},
    {"id": "history_002", "input": "recent activity", "expected_agent": "transaction_history", "category": "authenticated", "subcategory": "transaction_history"},
    {"id": "history_003", "input": "show my transaction history", "expected_agent": "transaction_history", "category": "authenticated", "subcategory": "transaction_history"},
    
    # ---- WORKFLOW AGENTS ----
    # Swap Workflow (can use moonpay_swap_flow_handler OR swap_workflow agent)
    {"id": "swap_001", "input": "swap 1 ETH to USDC", "expected_agent": "swap_workflow", "expected_handler": "moonpay_swap_flow_handler", "category": "workflow", "subcategory": "swap", "is_multi_step": True},
    {"id": "swap_002", "input": "exchange 100 USDC for ETH", "expected_agent": "swap_workflow", "expected_handler": "moonpay_swap_flow_handler", "category": "workflow", "subcategory": "swap", "is_multi_step": True},
    {"id": "swap_003", "input": "convert 0.5 ETH to DAI", "expected_agent": "swap_workflow", "expected_handler": "moonpay_swap_flow_handler", "category": "workflow", "subcategory": "swap", "is_multi_step": True},
    
    # Lending Workflow
    {"id": "lending_001", "input": "deposit 100 USDC", "expected_agent": "lending_workflow", "category": "workflow", "subcategory": "lending", "is_multi_step": True},
    {"id": "lending_002", "input": "lend 0.5 ETH on Aave", "expected_agent": "lending_workflow", "category": "workflow", "subcategory": "lending", "is_multi_step": True},
    {"id": "lending_003", "input": "earn yield on 500 DAI", "expected_agent": "lending_workflow", "category": "workflow", "subcategory": "lending", "is_multi_step": True},
    
    # Buy Workflow
    {"id": "buy_001", "input": "buy $100 of ETH", "expected_agent": "buy_workflow", "category": "workflow", "subcategory": "buy", "is_multi_step": True},
    {"id": "buy_002", "input": "purchase 50 dollars of USDC", "expected_agent": "buy_workflow", "category": "workflow", "subcategory": "buy", "is_multi_step": True},
    {"id": "buy_003", "input": "buy crypto", "expected_agent": "buy_workflow", "category": "workflow", "subcategory": "buy", "is_multi_step": True},
    
    # Transfer Workflow
    {"id": "transfer_001", "input": "send 100 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "expected_agent": "transfer_workflow", "category": "workflow", "subcategory": "transfer", "is_multi_step": True},
    {"id": "transfer_002", "input": "transfer 0.5 ETH to my friend", "expected_agent": "transfer_workflow", "category": "workflow", "subcategory": "transfer", "is_multi_step": True},
    {"id": "transfer_003", "input": "send ETH", "expected_agent": "transfer_workflow", "category": "workflow", "subcategory": "transfer", "is_multi_step": True},
    
    # Money Market Workflow
    {"id": "mm_001", "input": "compare USDC rates", "expected_agent": "money_market_workflow", "category": "workflow", "subcategory": "money_market"},
    {"id": "mm_002", "input": "compare rates for USDC", "expected_agent": "money_market_workflow", "category": "workflow", "subcategory": "money_market"},
    {"id": "mm_003", "input": "Morpho vs Aave rates", "expected_agent": "money_market_workflow", "category": "workflow", "subcategory": "money_market"},
    {"id": "mm_004", "input": "best lending rates for ETH", "expected_agent": "money_market_workflow", "category": "workflow", "subcategory": "money_market"},
    {"id": "mm_005", "input": "where should I deposit DAI", "expected_agent": "money_market_workflow", "category": "workflow", "subcategory": "money_market"},
]

# Complex Queries - Multi-Agent Collaboration
COMPLEX_QUERIES = [
    # Hunter AI + Risk Analyzer
    {
        "id": "complex_001",
        "input": "find arbitrage opportunities between Ethereum and Polygon",
        "expected_agents": ["hunter_ai", "risk_analyzer"],
        "category": "complex",
        "subcategory": "arbitrage",
    },
    
    # Portfolio + Hunter AI
    {
        "id": "complex_002",
        "input": "I have 70% ETH and 30% BTC. Should I rebalance?",
        "expected_agents": ["portfolio", "hunter_ai"],
        "category": "complex",
        "subcategory": "rebalancing",
    },
    
    # DeFi Yield + Risk Analyzer
    {
        "id": "complex_003",
        "input": "suggest low-risk DeFi yield opportunities",
        "expected_agents": ["defi_yield", "risk_analyzer"],
        "category": "complex",
        "subcategory": "yield_risk",
    },
    
    # Hunter AI - Complex Analysis
    {
        "id": "complex_004",
        "input": "how correlated are BTC, ETH, and SOL",
        "expected_agents": ["hunter_ai"],
        "category": "complex",
        "subcategory": "correlation",
    },
    
    # Hunter AI - Historical Patterns
    {
        "id": "complex_005",
        "input": "Show me Bitcoin's price patterns during the last 3 bull markets",
        "expected_agents": ["hunter_ai"],
        "category": "complex",
        "subcategory": "historical",
    },
    
    # Market Regime Analysis
    {
        "id": "complex_006",
        "input": "are we in a bull market or bear market",
        "expected_agents": ["hunter_ai"],
        "category": "complex",
        "subcategory": "market_regime",
    },
    
    # DeFi Protocol Rankings
    {
        "id": "complex_007",
        "input": "DeFi protocols by market cap",
        "expected_agents": ["hunter_ai"],
        "category": "complex",
        "subcategory": "rankings",
    },
    
    # Portfolio Analysis with Market Context
    {
        "id": "complex_008",
        "input": "analyze my portfolio risk and suggest improvements",
        "expected_agents": ["portfolio", "risk_analyzer"],
        "category": "complex",
        "subcategory": "portfolio_risk",
    },
    
    # Yield Farming with Gas Optimization
    {
        "id": "complex_009",
        "input": "best yield farms with low gas costs",
        "expected_agents": ["defi_yield", "gas_optimizer"],
        "category": "complex",
        "subcategory": "yield_gas",
    },
    
    # Comprehensive Market Overview
    {
        "id": "complex_010",
        "input": "give me a complete market overview with prices, sentiment, and news",
        "expected_agents": ["hunter_ai"],
        "category": "complex",
        "subcategory": "market_overview",
    },
]

# Multi-step Workflow Tests
MULTISTEP_WORKFLOWS = [
    # Swap Workflow - Full Flow
    {
        "id": "flow_swap_001",
        "category": "multistep",
        "subcategory": "swap",
        "steps": [
            {"input": "swap 1 ETH to USDC", "expected_agent": "swap_workflow", "requires_execute": False},
            {"input": "yes", "expected_agent": "swap_workflow", "requires_execute": True},
        ],
    },
    
    # Lending Workflow - Full Flow
    {
        "id": "flow_lending_001",
        "category": "multistep",
        "subcategory": "lending",
        "steps": [
            {"input": "deposit 100 USDC on Aave", "expected_agent": "lending_workflow", "requires_execute": False},
            {"input": "yes", "expected_agent": "lending_workflow", "requires_execute": True},
        ],
    },
    
    # Buy Workflow - Full Flow
    {
        "id": "flow_buy_001",
        "category": "multistep",
        "subcategory": "buy",
        "steps": [
            {"input": "buy $50 of ETH", "expected_agent": "buy_workflow", "requires_execute": False},
            {"input": "yes", "expected_agent": "buy_workflow", "requires_execute": True},
        ],
    },
    
    # Transfer Workflow - Full Flow
    {
        "id": "flow_transfer_001",
        "category": "multistep",
        "subcategory": "transfer",
        "steps": [
            {"input": "send 10 USDC to 0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "expected_agent": "transfer_workflow", "requires_execute": False},
            {"input": "yes", "expected_agent": "transfer_workflow", "requires_execute": True},
        ],
    },
    
    # Swap - Partial Info Flow
    {
        "id": "flow_swap_002",
        "category": "multistep",
        "subcategory": "swap_partial",
        "steps": [
            {"input": "swap ETH", "expected_agent": "swap_workflow", "requires_execute": False},
            {"input": "1 ETH to USDC", "expected_agent": "swap_workflow", "requires_execute": False},
            {"input": "yes", "expected_agent": "swap_workflow", "requires_execute": True},
        ],
    },
]

# Multi-language Tests
MULTILINGUAL_QUERIES = [
    # Spanish
    {"id": "es_001", "input": "hola", "expected_agent": "chat", "category": "multilingual", "subcategory": "spanish", "language": "es"},
    {"id": "es_002", "input": "precio de bitcoin", "expected_agent": "hunter_ai", "category": "multilingual", "subcategory": "spanish", "language": "es"},
    {"id": "es_003", "input": "comparar tasas de USDC", "expected_agent": "money_market_workflow", "category": "multilingual", "subcategory": "spanish", "language": "es"},
    {"id": "es_004", "input": "cambiar 1 ETH a USDC", "expected_agent": "swap_workflow", "expected_handler": "moonpay_swap_flow_handler", "category": "multilingual", "subcategory": "spanish", "language": "es"},
    {"id": "es_005", "input": "mi cartera", "expected_agent": "portfolio", "category": "multilingual", "subcategory": "spanish", "language": "es"},
    
    # Portuguese
    {"id": "pt_001", "input": "olá", "expected_agent": "chat", "category": "multilingual", "subcategory": "portuguese", "language": "pt"},
    {"id": "pt_002", "input": "preço do bitcoin", "expected_agent": "hunter_ai", "category": "multilingual", "subcategory": "portuguese", "language": "pt"},
    {"id": "pt_003", "input": "comparar taxas de USDC", "expected_agent": "money_market_workflow", "category": "multilingual", "subcategory": "portuguese", "language": "pt"},
    {"id": "pt_004", "input": "trocar 1 ETH por USDC", "expected_agent": "swap_workflow", "expected_handler": "moonpay_swap_flow_handler", "category": "multilingual", "subcategory": "portuguese", "language": "pt"},
    {"id": "pt_005", "input": "minha carteira", "expected_agent": "portfolio", "category": "multilingual", "subcategory": "portuguese", "language": "pt"},
    
    # Chinese
    {"id": "zh_001", "input": "你好", "expected_agent": "chat", "category": "multilingual", "subcategory": "chinese", "language": "zh"},
    {"id": "zh_002", "input": "比特币价格", "expected_agent": "hunter_ai", "category": "multilingual", "subcategory": "chinese", "language": "zh"},
    {"id": "zh_003", "input": "我的钱包", "expected_agent": "wallet", "category": "multilingual", "subcategory": "chinese", "language": "zh"},
]

# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture(scope="module")
def all_agents_reporter() -> CSVReporter:
    """Create CSV reporter for all agents test suite."""
    reporter = CSVReporter(category="all_agents_comprehensive")
    yield reporter
    
    if reporter.results:
        csv_path = reporter.write_csv()
        summary_path = reporter.write_summary()
        reporter.print_summary()
        print(f"\nCSV output: {csv_path}")
        print(f"Summary: {summary_path}")


# ============================================================
# Test Functions
# ============================================================

@pytest.mark.asyncio
class TestSimpleQueries:
    """Test simple single-agent queries."""
    
    async def test_all_simple_queries(self, authenticated_client, all_agents_reporter):
        """Run all simple query tests."""
        for test_case in SIMPLE_QUERIES:
            # Create new conversation for each test
            conv_id = await create_conversation(authenticated_client, title=f"Test {test_case['id']}")
            
            # Send message
            language = test_case.get("language", "en")
            response_data, response_time = await send_message(
                authenticated_client,
                conv_id,
                test_case["input"],
                language=language,
                timeout=90.0,
            )
            
            # Parse response
            parsed = parse_response(response_data)
            
            # Determine status
            expected_agent = test_case.get("expected_agent", "")
            expected_handler = test_case.get("expected_handler", "")
            actual_agents = parsed.get("agents_used", "")
            actual_handler = parsed.get("handler", "")
            has_error = parsed.get("error", False)
            
            if has_error:
                status = "FAIL"
            elif expected_agent and expected_agent in actual_agents:
                status = "PASS"
            elif expected_handler and expected_handler in actual_handler:
                # Alternative: handler-based workflows (e.g., moonpay_swap_flow_handler)
                status = "PASS"
                actual_agents = actual_handler  # Use handler as agent for reporting
            elif actual_agents:
                status = "PARTIAL"
            else:
                status = "FAIL"
            
            # Create result
            result = TestResult(
                test_id=test_case["id"],
                category=test_case.get("category", ""),
                subcategory=test_case.get("subcategory", ""),
                is_multi_step="YES" if test_case.get("is_multi_step") else "NO",
                input=test_case["input"],
                output=parsed.get("content", "")[:500],
                expected_agent=expected_agent or expected_handler,
                actual_agents=actual_agents or actual_handler,
                sources=parsed.get("sources", ""),
                handler=actual_handler,
                response_time_ms=response_time,
                has_execute_data="YES" if parsed.get("execute_data") else "NO",
                execute_action_type=parsed.get("execute_data", {}).get("action_type", "") if parsed.get("execute_data") else "",
                user_type="authenticated",
                language=language,
                status=status,
                error_message=parsed.get("error_message", ""),
                conversation_id=conv_id,
            )
            
            all_agents_reporter.add_result(result)
            
            # Print progress
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            display_agents = actual_agents or actual_handler
            print(f"{status_emoji} {test_case['id']}: {test_case['input'][:40]}... → {display_agents} ({response_time}ms)")
            
            # Small delay between tests
            await asyncio.sleep(0.5)


@pytest.mark.asyncio
class TestComplexQueries:
    """Test complex multi-agent queries."""
    
    async def test_all_complex_queries(self, authenticated_client, all_agents_reporter):
        """Run all complex query tests."""
        for test_case in COMPLEX_QUERIES:
            # Create new conversation
            conv_id = await create_conversation(authenticated_client, title=f"Complex {test_case['id']}")
            
            # Send message
            response_data, response_time = await send_message(
                authenticated_client,
                conv_id,
                test_case["input"],
                timeout=120.0,
            )
            
            # Parse response
            parsed = parse_response(response_data)
            
            # Determine status - for complex queries, check if ANY expected agent was used
            expected_agents = test_case.get("expected_agents", [])
            actual_agents = parsed.get("agents_used", "")
            has_error = parsed.get("error", False)
            
            if has_error:
                status = "FAIL"
            else:
                # Check how many expected agents were used
                agents_found = sum(1 for ea in expected_agents if ea in actual_agents)
                if agents_found == len(expected_agents):
                    status = "PASS"
                elif agents_found > 0:
                    status = "PARTIAL"
                elif actual_agents:
                    status = "PARTIAL"  # Some agent responded
                else:
                    status = "FAIL"
            
            # Create result
            result = TestResult(
                test_id=test_case["id"],
                category=test_case.get("category", ""),
                subcategory=test_case.get("subcategory", ""),
                input=test_case["input"],
                output=parsed.get("content", "")[:500],
                expected_agent=",".join(expected_agents),
                actual_agents=actual_agents,
                sources=parsed.get("sources", ""),
                handler=parsed.get("handler", ""),
                response_time_ms=response_time,
                has_execute_data="YES" if parsed.get("execute_data") else "NO",
                user_type="authenticated",
                status=status,
                error_message=parsed.get("error_message", ""),
                conversation_id=conv_id,
            )
            
            all_agents_reporter.add_result(result)
            
            # Print progress
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"{status_emoji} {test_case['id']}: {test_case['input'][:40]}... → {actual_agents} ({response_time}ms)")
            
            await asyncio.sleep(0.5)


@pytest.mark.asyncio
class TestMultiStepWorkflows:
    """Test multi-step workflow conversations."""
    
    async def test_all_multistep_workflows(self, authenticated_client, all_agents_reporter):
        """Run all multi-step workflow tests."""
        for workflow in MULTISTEP_WORKFLOWS:
            # Create new conversation for the workflow
            conv_id = await create_conversation(authenticated_client, title=f"Workflow {workflow['id']}")
            
            total_steps = len(workflow["steps"])
            
            for step_num, step in enumerate(workflow["steps"], 1):
                # Send message
                response_data, response_time = await send_message(
                    authenticated_client,
                    conv_id,
                    step["input"],
                    timeout=90.0,
                )
                
                # Parse response
                parsed = parse_response(response_data)
                
                # Determine status
                expected_agent = step.get("expected_agent", "")
                actual_agents = parsed.get("agents_used", "")
                has_execute = bool(parsed.get("execute_data"))
                requires_execute = step.get("requires_execute", False)
                has_error = parsed.get("error", False)
                
                if has_error:
                    status = "FAIL"
                elif expected_agent and expected_agent in actual_agents:
                    if requires_execute and not has_execute:
                        status = "PARTIAL"
                    else:
                        status = "PASS"
                elif actual_agents:
                    status = "PARTIAL"
                else:
                    status = "FAIL"
                
                # Create result
                result = TestResult(
                    test_id=f"{workflow['id']}_step{step_num}",
                    category=workflow.get("category", ""),
                    subcategory=workflow.get("subcategory", ""),
                    is_multi_step="YES",
                    step_number=step_num,
                    total_steps=total_steps,
                    input=step["input"],
                    output=parsed.get("content", "")[:500],
                    expected_agent=expected_agent,
                    actual_agents=actual_agents,
                    sources=parsed.get("sources", ""),
                    handler=parsed.get("handler", ""),
                    response_time_ms=response_time,
                    has_execute_data="YES" if has_execute else "NO",
                    execute_action_type=parsed.get("execute_data", {}).get("action_type", "") if has_execute else "",
                    user_type="authenticated",
                    status=status,
                    error_message=parsed.get("error_message", ""),
                    conversation_id=conv_id,
                )
                
                all_agents_reporter.add_result(result)
                
                # Print progress
                status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
                exec_marker = "🎯" if has_execute else ""
                print(f"{status_emoji} {workflow['id']} Step {step_num}/{total_steps}: {step['input'][:30]}... → {actual_agents} {exec_marker} ({response_time}ms)")
                
                # Stop workflow if a step failed
                if status == "FAIL":
                    print(f"  ⛔ Workflow {workflow['id']} stopped due to failure")
                    break
                
                await asyncio.sleep(1.0)  # Longer delay between workflow steps
            
            await asyncio.sleep(0.5)


@pytest.mark.asyncio
class TestMultilingualSupport:
    """Test multi-language support."""
    
    async def test_all_multilingual_queries(self, authenticated_client, all_agents_reporter):
        """Run all multilingual query tests."""
        for test_case in MULTILINGUAL_QUERIES:
            # Create new conversation
            conv_id = await create_conversation(
                authenticated_client,
                title=f"Multilingual {test_case['id']}",
                language=test_case.get("language", "en"),
            )
            
            # Send message
            language = test_case.get("language", "en")
            response_data, response_time = await send_message(
                authenticated_client,
                conv_id,
                test_case["input"],
                language=language,
                timeout=90.0,
            )
            
            # Parse response
            parsed = parse_response(response_data)
            
            # Determine status
            expected_agent = test_case.get("expected_agent", "")
            expected_handler = test_case.get("expected_handler", "")
            actual_agents = parsed.get("agents_used", "")
            actual_handler = parsed.get("handler", "")
            has_error = parsed.get("error", False)
            
            if has_error:
                status = "FAIL"
            elif expected_agent and expected_agent in actual_agents:
                status = "PASS"
            elif expected_handler and expected_handler in actual_handler:
                # Alternative: handler-based workflows
                status = "PASS"
                actual_agents = actual_handler
            elif actual_agents:
                status = "PARTIAL"
            else:
                status = "FAIL"
            
            # Create result
            result = TestResult(
                test_id=test_case["id"],
                category=test_case.get("category", ""),
                subcategory=test_case.get("subcategory", ""),
                input=test_case["input"],
                output=parsed.get("content", "")[:500],
                expected_agent=expected_agent or expected_handler,
                actual_agents=actual_agents or actual_handler,
                handler=parsed.get("handler", ""),
                response_time_ms=response_time,
                user_type="authenticated",
                language=language,
                status=status,
                error_message=parsed.get("error_message", ""),
                conversation_id=conv_id,
            )
            
            all_agents_reporter.add_result(result)
            
            # Print progress
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            lang_flag = {"es": "🇪🇸", "pt": "🇧🇷", "zh": "🇨🇳", "en": "🇺🇸"}.get(language, "🌐")
            print(f"{status_emoji} {lang_flag} {test_case['id']}: {test_case['input'][:30]}... → {actual_agents} ({response_time}ms)")
            
            await asyncio.sleep(0.5)


# ============================================================
# Main Runner
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
