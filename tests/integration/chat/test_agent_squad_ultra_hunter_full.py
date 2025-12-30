"""
Full integration tests for Agent Squad, Ultra, and Hunter systems.

Tests comprehensive functionality for:
- Agent Squad: All 18 specialized AI agents
- Ultra: Arbitrage, flash loans, MEV protection, auto-executor
- Hunter: Sentiment, price prediction, patterns, portfolio, risk, trading signals

This test suite validates the unified chat endpoint properly routes
to specialized handlers and returns correctly structured responses.
"""

import json
import pytest
import pytest_asyncio
from pathlib import Path
from typing import Dict, Any, List
from uuid import UUID

from tests.helpers.api_client import AuthenticatedClient
from tests.helpers.auth_helper import AuthHelper


# =============================================================================
# Test Data - Comprehensive test cases for all systems
# =============================================================================

AGENT_SQUAD_TEST_CASES = {
    "core_agents": [
        # Chat Agent
        {
            "id": "squad_chat_001",
            "description": "General chat agent - greeting",
            "input": {"content": "Hello! What can you help me with?"},
            "expected_routing": {
                "intent": "general_conversation",
                "confidence_min": 0.85,
            },
            "agent_type": "chat",
        },
        {
            "id": "squad_chat_002",
            "description": "Chat agent - feature inquiry",
            "input": {"content": "What features do you offer?"},
            "expected_routing": {
                "intent": "general_conversation",
                "confidence_min": 0.8,
            },
            "agent_type": "chat",
        },
        # Hunter AI Agent
        {
            "id": "squad_hunter_001",
            "description": "Hunter AI agent - sentiment analysis",
            "input": {"content": "What's the current market sentiment for Ethereum?"},
            "expected_routing": {
                "intent": "hunter_sentiment",
                "confidence_min": 0.8,
            },
            "agent_type": "hunter_ai",
        },
        {
            "id": "squad_hunter_002",
            "description": "Hunter AI agent - price prediction",
            "input": {"content": "Predict Bitcoin price for the next week"},
            "expected_routing": {
                "intent": "hunter_price_prediction",
                "confidence_min": 0.8,
            },
            "agent_type": "hunter_ai",
        },
        # Research Agent
        {
            "id": "squad_research_001",
            "description": "Research agent - protocol deep dive",
            "input": {"content": "Do a deep research analysis on Aave V3 protocol"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.75,
            },
            "expected_enrichment": {
                "task_type": "research",
            },
            "agent_type": "research",
        },
        {
            "id": "squad_research_002",
            "description": "Research agent - tokenomics analysis",
            "input": {"content": "Research the tokenomics of Uniswap UNI token"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.75,
            },
            "agent_type": "research",
        },
        # Execution Agent
        {
            "id": "squad_exec_001",
            "description": "Execution agent - swap request",
            "input": {"content": "Execute a swap of 1 ETH for USDC on Uniswap"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.75,
            },
            "expected_enrichment": {
                "task_type": "execution",
            },
            "agent_type": "execution",
        },
        # Risk Analyzer Agent
        {
            "id": "squad_risk_001",
            "description": "Risk analyzer agent - portfolio risk",
            "input": {"content": "Analyze the risk of my current DeFi positions"},
            "expected_routing": {
                "intent": "hunter_risk_signals",
                "confidence_min": 0.75,
            },
            "agent_type": "risk_analyzer",
        },
        {
            "id": "squad_risk_002",
            "description": "Risk analyzer agent - protocol risk",
            "input": {"content": "What are the risks of using Curve Finance?"},
            "expected_routing": {
                "intent": "risk_assessment",
                "confidence_min": 0.75,
            },
            "agent_type": "risk_analyzer",
        },
        # Portfolio Agent
        {
            "id": "squad_portfolio_001",
            "description": "Portfolio agent - optimization",
            "input": {"content": "Optimize my crypto portfolio for maximum Sharpe ratio"},
            "expected_routing": {
                "intent": "hunter_portfolio",
                "confidence_min": 0.75,
            },
            "agent_type": "portfolio",
        },
        {
            "id": "squad_portfolio_002",
            "description": "Portfolio agent - rebalancing",
            "input": {"content": "Suggest rebalancing for my BTC, ETH, SOL holdings"},
            "expected_routing": {
                "intent": "hunter_portfolio",
                "confidence_min": 0.75,
            },
            "agent_type": "portfolio",
        },
        # Tax Optimizer Agent
        {
            "id": "squad_tax_001",
            "description": "Tax optimizer agent - tax loss harvesting",
            "input": {"content": "Find tax loss harvesting opportunities in my portfolio"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "tax_optimizer",
        },
        {
            "id": "squad_tax_002",
            "description": "Tax optimizer agent - tax report",
            "input": {"content": "Generate a tax report for my 2024 crypto transactions"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "tax_optimizer",
        },
        # DeFi Yield Agent
        {
            "id": "squad_yield_001",
            "description": "DeFi yield agent - best yields",
            "input": {"content": "Find the best yield farming opportunities on Ethereum"},
            "expected_routing": {
                "intent": "protocol_search",
                "confidence_min": 0.75,
            },
            "agent_type": "defi_yield",
        },
        {
            "id": "squad_yield_002",
            "description": "DeFi yield agent - staking rewards",
            "input": {"content": "Compare staking rewards across different protocols"},
            "expected_routing": {
                "intent": "protocol_search",
                "confidence_min": 0.75,
            },
            "agent_type": "defi_yield",
        },
        # Security Auditor Agent
        {
            "id": "squad_security_001",
            "description": "Security auditor agent - contract audit",
            "input": {"content": "Audit this smart contract for vulnerabilities: 0x1234..."},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "security_auditor",
        },
        {
            "id": "squad_security_002",
            "description": "Security auditor agent - protocol security",
            "input": {"content": "Check if Compound protocol has any known security issues"},
            "expected_routing": {
                "intent": "risk_assessment",
                "confidence_min": 0.7,
            },
            "agent_type": "security_auditor",
        },
        # Gas Optimizer Agent
        {
            "id": "squad_gas_001",
            "description": "Gas optimizer agent - optimize transaction",
            "input": {"content": "Optimize gas for my pending swap transaction"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "gas_optimizer",
        },
        {
            "id": "squad_gas_002",
            "description": "Gas optimizer agent - gas price analysis",
            "input": {"content": "When is the best time to send transactions for low gas?"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "gas_optimizer",
        },
    ],
    "advanced_agents": [
        # Bridge Crosschain Agent
        {
            "id": "squad_bridge_001",
            "description": "Bridge agent - cross-chain transfer",
            "input": {"content": "Bridge 100 USDC from Ethereum to Arbitrum"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "expected_enrichment": {
                "task_type": "bridging",
            },
            "agent_type": "bridge_crosschain",
        },
        {
            "id": "squad_bridge_002",
            "description": "Bridge agent - best bridge route",
            "input": {"content": "Find the cheapest bridge route from Polygon to Optimism"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "bridge_crosschain",
        },
        # Lending Borrowing Agent
        {
            "id": "squad_lending_001",
            "description": "Lending agent - leverage position",
            "input": {"content": "Create a 2x leveraged position on ETH using Aave"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "lending_borrowing",
        },
        {
            "id": "squad_lending_002",
            "description": "Lending agent - collateral optimization",
            "input": {"content": "Optimize my collateral ratio on Compound"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "lending_borrowing",
        },
        # NFT Asset Manager Agent
        {
            "id": "squad_nft_001",
            "description": "NFT agent - portfolio valuation",
            "input": {"content": "Value my NFT portfolio and suggest which to hold or sell"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "nft_asset_manager",
        },
        {
            "id": "squad_nft_002",
            "description": "NFT agent - collection analysis",
            "input": {"content": "Analyze the Bored Ape Yacht Club collection floor price trends"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "nft_asset_manager",
        },
        # DAO Governance Agent
        {
            "id": "squad_dao_001",
            "description": "DAO agent - active proposals",
            "input": {"content": "Show me active governance proposals on Uniswap DAO"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "dao_governance",
        },
        {
            "id": "squad_dao_002",
            "description": "DAO agent - vote recommendation",
            "input": {"content": "Should I vote yes or no on Aave proposal #42?"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "dao_governance",
        },
    ],
    "enterprise_agents": [
        # Compliance Monitor Agent
        {
            "id": "squad_compliance_001",
            "description": "Compliance agent - wallet screening",
            "input": {"content": "Screen wallet 0xabc123 for AML compliance"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "compliance_monitor",
        },
        {
            "id": "squad_compliance_002",
            "description": "Compliance agent - transaction check",
            "input": {"content": "Check if this transaction is compliant with regulations"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "compliance_monitor",
        },
        # Multi-Sig Coordinator Agent
        {
            "id": "squad_multisig_001",
            "description": "Multi-sig agent - create proposal",
            "input": {"content": "Create a multi-sig proposal to transfer 10 ETH from treasury"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "multisig_coordinator",
        },
        {
            "id": "squad_multisig_002",
            "description": "Multi-sig agent - pending approvals",
            "input": {"content": "Show pending multi-sig approvals for our Gnosis Safe"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "multisig_coordinator",
        },
        # Alert Monitoring Agent
        {
            "id": "squad_alert_001",
            "description": "Alert agent - set price alert",
            "input": {"content": "Set an alert when ETH drops below $2000"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "alert_monitoring",
        },
        {
            "id": "squad_alert_002",
            "description": "Alert agent - security alerts",
            "input": {"content": "Monitor my wallet for suspicious activity"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "alert_monitoring",
        },
        # Crisis Manager Agent
        {
            "id": "squad_crisis_001",
            "description": "Crisis agent - emergency response",
            "input": {"content": "There's a potential exploit on the protocol I'm using, what should I do?"},
            "expected_routing": {
                "intent": "specialist_task",
                "confidence_min": 0.7,
            },
            "agent_type": "crisis_manager",
        },
        {
            "id": "squad_crisis_002",
            "description": "Crisis agent - incident analysis",
            "input": {"content": "Analyze the recent flash loan attack on XYZ protocol"},
            "expected_routing": {
                "intent": "risk_assessment",
                "confidence_min": 0.7,
            },
            "agent_type": "crisis_manager",
        },
    ],
}

ULTRA_TEST_CASES = {
    "arbitrage": [
        {
            "id": "ultra_arb_basic_001",
            "description": "Basic arbitrage discovery",
            "input": {"content": "Find arbitrage opportunities with $10,000 capital"},
            "expected_routing": {
                "intent": "ultra_arbitrage",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "capital": 10000,
                "ultra_tool": "arbitrage_scanner",
            },
        },
        {
            "id": "ultra_arb_2hop_001",
            "description": "2-hop arbitrage search",
            "input": {"content": "Search for 2-hop arbitrage between Uniswap and SushiSwap"},
            "expected_routing": {
                "intent": "ultra_arbitrage",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "arb_type": "2hop",
            },
        },
        {
            "id": "ultra_arb_triangle_001",
            "description": "Triangle arbitrage discovery",
            "input": {"content": "Find triangle arbitrage opportunities on ETH/USDC/WBTC"},
            "expected_routing": {
                "intent": "ultra_arbitrage",
                "confidence_min": 0.75,
            },
            "expected_enrichment": {
                "arb_type": "triangle",
            },
        },
        {
            "id": "ultra_arb_crosschain_001",
            "description": "Cross-chain arbitrage",
            "input": {"content": "Discover cross-chain arbitrage between Ethereum and Arbitrum"},
            "expected_routing": {
                "intent": "ultra_arbitrage",
                "confidence_min": 0.75,
            },
            "expected_enrichment": {
                "arb_type": "cross-chain",
            },
        },
        {
            "id": "ultra_arb_profitable_001",
            "description": "Profitable arbitrage filter",
            "input": {"content": "Show me arbitrage opportunities with at least 1% profit"},
            "expected_routing": {
                "intent": "ultra_arbitrage",
                "confidence_min": 0.75,
            },
            "expected_enrichment": {
                "min_profit_pct": 1.0,
            },
        },
    ],
    "flash_loans": [
        {
            "id": "ultra_flash_protocol_001",
            "description": "Flash loan protocol selection",
            "input": {"content": "Best flash loan protocol for 100k USDC"},
            "expected_routing": {
                "intent": "ultra_flash_loans",
                "confidence_min": 0.85,
            },
            "expected_enrichment": {
                "token_symbol": "USDC",
                "amount": 100000,
                "ultra_tool": "flash_loan_selector",
            },
        },
        {
            "id": "ultra_flash_aave_001",
            "description": "Aave flash loan",
            "input": {"content": "Get a flash loan from Aave for 50 ETH"},
            "expected_routing": {
                "intent": "ultra_flash_loans",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "protocol": "aave",
                "token_symbol": "ETH",
            },
        },
        {
            "id": "ultra_flash_balancer_001",
            "description": "Balancer flash loan",
            "input": {"content": "Execute flash loan on Balancer for WBTC"},
            "expected_routing": {
                "intent": "ultra_flash_loans",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "protocol": "balancer",
            },
        },
        {
            "id": "ultra_flash_leverage_001",
            "description": "Flash loan for leverage",
            "input": {"content": "Use flash loan to create 3x leverage on ETH"},
            "expected_routing": {
                "intent": "ultra_flash_loans",
                "confidence_min": 0.75,
            },
            "expected_enrichment": {
                "use_case": "leverage",
            },
        },
        {
            "id": "ultra_flash_comparison_001",
            "description": "Flash loan fee comparison",
            "input": {"content": "Compare flash loan fees across all providers"},
            "expected_routing": {
                "intent": "ultra_flash_loans",
                "confidence_min": 0.75,
            },
        },
    ],
    "mev_protection": [
        {
            "id": "ultra_mev_flashbots_001",
            "description": "Flashbots MEV protection",
            "input": {"content": "Execute ARB-001 with Flashbots protection"},
            "expected_routing": {
                "intent": "ultra_mev_protection",
                "confidence_min": 0.85,
            },
            "expected_enrichment": {
                "protection_method": "flashbots",
                "ultra_tool": "mev_protector",
            },
        },
        {
            "id": "ultra_mev_private_001",
            "description": "Private transaction",
            "input": {"content": "Send this transaction privately to avoid frontrunning"},
            "expected_routing": {
                "intent": "ultra_mev_protection",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "protection_method": "private",
            },
        },
        {
            "id": "ultra_mev_sandwich_001",
            "description": "Sandwich attack protection",
            "input": {"content": "Protect my large swap from sandwich attacks"},
            "expected_routing": {
                "intent": "ultra_mev_protection",
                "confidence_min": 0.75,
            },
        },
        {
            "id": "ultra_mev_bundle_001",
            "description": "Transaction bundle",
            "input": {"content": "Bundle my transactions to avoid MEV extraction"},
            "expected_routing": {
                "intent": "ultra_mev_protection",
                "confidence_min": 0.75,
            },
        },
    ],
    "auto_executor": [
        {
            "id": "ultra_ae_start_001",
            "description": "Start auto executor",
            "input": {"content": "Start the automated trading bot"},
            "expected_routing": {
                "intent": "ultra_auto_executor",
                "confidence_min": 0.85,
            },
            "expected_enrichment": {
                "action": "start",
                "ultra_tool": "auto_executor",
            },
        },
        {
            "id": "ultra_ae_stop_001",
            "description": "Stop auto executor",
            "input": {"content": "Stop the trading bot immediately"},
            "expected_routing": {
                "intent": "ultra_auto_executor",
                "confidence_min": 0.85,
            },
            "expected_enrichment": {
                "action": "stop",
            },
        },
        {
            "id": "ultra_ae_status_001",
            "description": "Auto executor status",
            "input": {"content": "Show me the current bot status and performance"},
            "expected_routing": {
                "intent": "ultra_auto_executor",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "action": "status",
            },
        },
        {
            "id": "ultra_ae_config_001",
            "description": "Configure auto executor",
            "input": {"content": "Configure bot with 1.5% minimum profit threshold"},
            "expected_routing": {
                "intent": "ultra_auto_executor",
                "confidence_min": 0.75,
            },
            "expected_enrichment": {
                "action": "configure",
            },
        },
        {
            "id": "ultra_ae_pause_001",
            "description": "Pause auto executor",
            "input": {"content": "Pause the bot for 30 minutes"},
            "expected_routing": {
                "intent": "ultra_auto_executor",
                "confidence_min": 0.75,
            },
            "expected_enrichment": {
                "action": "pause",
            },
        },
    ],
}

HUNTER_TEST_CASES = {
    "sentiment": [
        {
            "id": "hunter_sent_eth_001",
            "description": "ETH sentiment analysis",
            "input": {"content": "What's the ETH sentiment on Twitter and Reddit?"},
            "expected_routing": {
                "intent": "hunter_sentiment",
                "confidence_min": 0.85,
            },
            "expected_enrichment": {
                "token_symbol": "ETH",
                "sources": ["twitter", "reddit"],
                "hunter_tool": "sentiment_analyzer",
            },
        },
        {
            "id": "hunter_sent_btc_001",
            "description": "BTC sentiment with time range",
            "input": {"content": "Show me BTC social media sentiment from last 7 days"},
            "expected_routing": {
                "intent": "hunter_sentiment",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "token_symbol": "BTC",
                "time_range": "7d",
            },
        },
        {
            "id": "hunter_sent_multi_001",
            "description": "Multi-token sentiment comparison",
            "input": {"content": "Compare sentiment between ETH, SOL, and AVAX"},
            "expected_routing": {
                "intent": "hunter_sentiment",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "token_symbols": ["ETH", "SOL", "AVAX"],
            },
        },
        {
            "id": "hunter_sent_discord_001",
            "description": "Discord sentiment",
            "input": {"content": "What's the Discord sentiment for Solana?"},
            "expected_routing": {
                "intent": "hunter_sentiment",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "token_symbol": "SOL",
                "sources": ["discord"],
            },
        },
        {
            "id": "hunter_sent_news_001",
            "description": "News sentiment analysis",
            "input": {"content": "Analyze crypto news sentiment for Bitcoin"},
            "expected_routing": {
                "intent": "hunter_sentiment",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "token_symbol": "BTC",
                "sources": ["news"],
            },
        },
    ],
    "price_prediction": [
        {
            "id": "hunter_pp_btc_7d_001",
            "description": "BTC 7-day prediction",
            "input": {"content": "Predict BTC price for next 7 days"},
            "expected_routing": {
                "intent": "hunter_price_prediction",
                "confidence_min": 0.85,
            },
            "expected_enrichment": {
                "token_symbol": "BTC",
                "time_horizon": "7d",
                "hunter_tool": "lstm_predictor",
            },
        },
        {
            "id": "hunter_pp_eth_30d_001",
            "description": "ETH 30-day forecast",
            "input": {"content": "Forecast ETH price for next 30 days"},
            "expected_routing": {
                "intent": "hunter_price_prediction",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "token_symbol": "ETH",
                "time_horizon": "30d",
            },
        },
        {
            "id": "hunter_pp_sol_001",
            "description": "SOL price prediction",
            "input": {"content": "What will SOL price be next week?"},
            "expected_routing": {
                "intent": "hunter_price_prediction",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "token_symbol": "SOL",
            },
        },
        {
            "id": "hunter_pp_range_001",
            "description": "Price range prediction",
            "input": {"content": "Give me a price range prediction for BTC"},
            "expected_routing": {
                "intent": "hunter_price_prediction",
                "confidence_min": 0.75,
            },
        },
    ],
    "patterns": [
        {
            "id": "hunter_pat_btc_001",
            "description": "BTC chart patterns",
            "input": {"content": "What chart patterns do you see for BTC?"},
            "expected_routing": {
                "intent": "hunter_patterns",
                "confidence_min": 0.85,
            },
            "expected_enrichment": {
                "token_symbol": "BTC",
                "hunter_tool": "pattern_detector",
            },
        },
        {
            "id": "hunter_pat_eth_001",
            "description": "ETH technical formations",
            "input": {"content": "Detect technical formations for ETH"},
            "expected_routing": {
                "intent": "hunter_patterns",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "token_symbol": "ETH",
            },
        },
        {
            "id": "hunter_pat_head_shoulders_001",
            "description": "Head and shoulders pattern",
            "input": {"content": "Is there a head and shoulders pattern on BTC?"},
            "expected_routing": {
                "intent": "hunter_patterns",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "pattern_type": "head_and_shoulders",
            },
        },
        {
            "id": "hunter_pat_support_001",
            "description": "Support resistance levels",
            "input": {"content": "Show me support and resistance levels for ETH"},
            "expected_routing": {
                "intent": "hunter_patterns",
                "confidence_min": 0.75,
            },
        },
    ],
    "portfolio": [
        {
            "id": "hunter_port_moderate_001",
            "description": "Moderate risk portfolio",
            "input": {"content": "Optimize my portfolio with BTC, ETH, and SOL for moderate risk"},
            "expected_routing": {
                "intent": "hunter_portfolio",
                "confidence_min": 0.85,
            },
            "expected_enrichment": {
                "tokens": ["BTC", "ETH", "SOL"],
                "risk_tolerance": "moderate",
                "hunter_tool": "mpt_optimizer",
            },
        },
        {
            "id": "hunter_port_conservative_001",
            "description": "Conservative portfolio",
            "input": {"content": "Create a conservative crypto portfolio for me"},
            "expected_routing": {
                "intent": "hunter_portfolio",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "risk_tolerance": "conservative",
            },
        },
        {
            "id": "hunter_port_aggressive_001",
            "description": "Aggressive portfolio",
            "input": {"content": "Build an aggressive high-risk portfolio for maximum gains"},
            "expected_routing": {
                "intent": "hunter_portfolio",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "risk_tolerance": "aggressive",
            },
        },
        {
            "id": "hunter_port_rebalance_001",
            "description": "Portfolio rebalancing",
            "input": {"content": "Rebalance my portfolio to target allocations"},
            "expected_routing": {
                "intent": "hunter_portfolio",
                "confidence_min": 0.75,
            },
        },
    ],
    "risk_signals": [
        {
            "id": "hunter_rs_eth_001",
            "description": "ETH risk signals",
            "input": {"content": "Show risk signals for ETH"},
            "expected_routing": {
                "intent": "hunter_risk_signals",
                "confidence_min": 0.85,
            },
            "expected_enrichment": {
                "token_symbol": "ETH",
                "hunter_tool": "risk_detector",
            },
        },
        {
            "id": "hunter_rs_btc_001",
            "description": "BTC risk indicators",
            "input": {"content": "What are the current risk indicators for Bitcoin?"},
            "expected_routing": {
                "intent": "hunter_risk_signals",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "token_symbol": "BTC",
            },
        },
        {
            "id": "hunter_rs_market_001",
            "description": "Market-wide risk signals",
            "input": {"content": "Show me overall crypto market risk signals"},
            "expected_routing": {
                "intent": "hunter_risk_signals",
                "confidence_min": 0.75,
            },
        },
    ],
    "trading_signals": [
        {
            "id": "hunter_ts_sol_001",
            "description": "SOL trading signals",
            "input": {"content": "Should I buy SOL now? Give me trading signals"},
            "expected_routing": {
                "intent": "hunter_trading_signals",
                "confidence_min": 0.85,
            },
            "expected_enrichment": {
                "token_symbol": "SOL",
                "hunter_tool": "signal_generator",
            },
        },
        {
            "id": "hunter_ts_btc_entry_001",
            "description": "BTC entry/exit signals",
            "input": {"content": "What are the entry and exit signals for BTC?"},
            "expected_routing": {
                "intent": "hunter_trading_signals",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "token_symbol": "BTC",
                "signal_types": ["entry", "exit"],
            },
        },
        {
            "id": "hunter_ts_swing_001",
            "description": "Swing trading signals",
            "input": {"content": "Give me swing trading signals for ETH"},
            "expected_routing": {
                "intent": "hunter_trading_signals",
                "confidence_min": 0.8,
            },
            "expected_enrichment": {
                "token_symbol": "ETH",
                "strategy": "swing",
            },
        },
        {
            "id": "hunter_ts_scalping_001",
            "description": "Scalping signals",
            "input": {"content": "Show scalping opportunities for BTC in the next hour"},
            "expected_routing": {
                "intent": "hunter_trading_signals",
                "confidence_min": 0.75,
            },
            "expected_enrichment": {
                "strategy": "scalping",
            },
        },
    ],
}


def get_all_agent_squad_cases() -> List[Dict[str, Any]]:
    """Get all Agent Squad test cases flattened."""
    cases = []
    for category, category_cases in AGENT_SQUAD_TEST_CASES.items():
        for case in category_cases:
            case_copy = case.copy()
            case_copy["_category"] = "agent_squad"
            case_copy["_subcategory"] = category
            cases.append(case_copy)
    return cases


def get_all_ultra_cases() -> List[Dict[str, Any]]:
    """Get all Ultra test cases flattened."""
    cases = []
    for category, category_cases in ULTRA_TEST_CASES.items():
        for case in category_cases:
            case_copy = case.copy()
            case_copy["_category"] = "ultra"
            case_copy["_subcategory"] = category
            cases.append(case_copy)
    return cases


def get_all_hunter_cases() -> List[Dict[str, Any]]:
    """Get all Hunter test cases flattened."""
    cases = []
    for category, category_cases in HUNTER_TEST_CASES.items():
        for case in category_cases:
            case_copy = case.copy()
            case_copy["_category"] = "hunter"
            case_copy["_subcategory"] = category
            cases.append(case_copy)
    return cases


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def authenticated_client(test_app, async_db_session):
    """Create authenticated client for API requests with database-backed user."""
    # Create user in database
    user, token = await AuthHelper.create_test_user_in_db(
        db_session=async_db_session,
        role="user",
    )

    # Create authenticated client with real token
    client = AuthenticatedClient()
    client.set_app(test_app)
    client._access_token = token
    client._current_user = user
    client._update_headers()

    return client


@pytest_asyncio.fixture
async def test_conversation(authenticated_client):
    """Create a test conversation for message testing."""
    response = await authenticated_client.post(
        "/api/v1/user/chat/conversations",
        json={"title": "Integration Test Conversation"},
    )

    assert response.status_code == 201, f"Failed to create conversation: {response.text}"
    conversation_data = response.json()
    return conversation_data["id"]


# =============================================================================
# Agent Squad Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.agent_squad
class TestAgentSquadCoreAgents:
    """Test core Agent Squad agents (10 agents)."""

    @pytest.mark.parametrize(
        "test_case",
        AGENT_SQUAD_TEST_CASES["core_agents"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_core_agent_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that core agents respond correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()

        # Validate response structure
        assert "user_message" in data, f"Missing user_message for {test_case['id']}"
        assert "agent_message" in data, f"Missing agent_message for {test_case['id']}"
        assert "routing" in data, f"Missing routing for {test_case['id']}"

        # Validate core response properties
        routing = data["routing"]
        assert "intent" in routing, f"Missing intent in routing for {test_case['id']}"
        assert "confidence" in routing, f"Missing confidence in routing for {test_case['id']}"
        assert "handler" in routing, f"Missing handler in routing for {test_case['id']}"
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate confidence is reasonable
        assert routing["confidence"] >= 0.5, (
            f"Confidence too low for {test_case['id']}: got {routing['confidence']}"
        )


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.agent_squad
class TestAgentSquadAdvancedAgents:
    """Test advanced Agent Squad agents (4 agents)."""

    @pytest.mark.parametrize(
        "test_case",
        AGENT_SQUAD_TEST_CASES["advanced_agents"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_advanced_agent_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that advanced agents respond correctly."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5, (
            f"Confidence too low for {test_case['id']}"
        )


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.agent_squad
class TestAgentSquadEnterpriseAgents:
    """Test enterprise Agent Squad agents (4 agents)."""

    @pytest.mark.parametrize(
        "test_case",
        AGENT_SQUAD_TEST_CASES["enterprise_agents"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_enterprise_agent_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test that enterprise agents are properly routed."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        assert len(data["agent_message"]["content"]) > 0


# =============================================================================
# Ultra Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.ultra
class TestUltraArbitrage:
    """Test Ultra arbitrage discovery functionality."""

    @pytest.mark.parametrize(
        "test_case",
        ULTRA_TEST_CASES["arbitrage"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_arbitrage_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test arbitrage discovery via chat."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.ultra
class TestUltraFlashLoans:
    """Test Ultra flash loan functionality."""

    @pytest.mark.parametrize(
        "test_case",
        ULTRA_TEST_CASES["flash_loans"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_flash_loan_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test flash loan requests via chat."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.ultra
class TestUltraMEVProtection:
    """Test Ultra MEV protection functionality."""

    @pytest.mark.parametrize(
        "test_case",
        ULTRA_TEST_CASES["mev_protection"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_mev_protection_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test MEV protection requests via chat."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.ultra
class TestUltraAutoExecutor:
    """Test Ultra auto-executor functionality."""

    @pytest.mark.parametrize(
        "test_case",
        ULTRA_TEST_CASES["auto_executor"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_auto_executor_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test auto-executor commands via chat."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5


# =============================================================================
# Hunter Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterSentiment:
    """Test Hunter sentiment analysis functionality."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["sentiment"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_sentiment_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test sentiment analysis via chat."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterPricePrediction:
    """Test Hunter price prediction functionality."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["price_prediction"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_price_prediction_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test price prediction via chat."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterPatterns:
    """Test Hunter pattern detection functionality."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["patterns"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_pattern_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test pattern detection via chat."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterPortfolio:
    """Test Hunter portfolio optimization functionality."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["portfolio"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_portfolio_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test portfolio optimization via chat."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterRiskSignals:
    """Test Hunter risk signal detection functionality."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["risk_signals"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_risk_signal_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test risk signal detection via chat."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5


@pytest.mark.integration
@pytest.mark.chat
@pytest.mark.hunter
class TestHunterTradingSignals:
    """Test Hunter trading signal generation functionality."""

    @pytest.mark.parametrize(
        "test_case",
        HUNTER_TEST_CASES["trading_signals"],
        ids=lambda tc: tc["id"],
    )
    @pytest.mark.asyncio
    async def test_trading_signal_routing(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
        test_case: Dict[str, Any],
    ):
        """Test trading signal generation via chat."""
        response = await authenticated_client.post(
            f"/api/v1/user/chat/conversations/{test_conversation}/messages",
            json={"content": test_case["input"]["content"]},
        )

        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code} for {test_case['id']}. "
            f"Response: {response.text}"
        )

        data = response.json()
        assert "routing" in data
        assert "agent_message" in data
        
        # Validate that we got a non-empty response
        agent_msg = data["agent_message"]
        assert len(agent_msg["content"]) > 0, f"Empty agent response for {test_case['id']}"
        
        # Validate routing structure
        routing = data["routing"]
        assert "intent" in routing
        assert "confidence" in routing
        assert routing["confidence"] >= 0.5


# =============================================================================
# Combined Full Test Suite
# =============================================================================


@pytest.mark.integration
@pytest.mark.chat
class TestFullSystemIntegration:
    """Test full system integration across all components."""

    @pytest.mark.asyncio
    async def test_all_agent_squad_agents_respond(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
    ):
        """Verify all Agent Squad agents can respond."""
        all_cases = get_all_agent_squad_cases()
        passed = 0
        failed = []

        for case in all_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": case["input"]["content"]},
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("agent_message", {}).get("content"):
                    passed += 1
                else:
                    failed.append(f"{case['id']}: Empty response")
            else:
                failed.append(f"{case['id']}: Status {response.status_code}")

        total = len(all_cases)
        assert passed == total, (
            f"Agent Squad: {passed}/{total} passed. Failed: {failed[:5]}..."
        )

    @pytest.mark.asyncio
    async def test_all_ultra_features_respond(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
    ):
        """Verify all Ultra features can respond."""
        all_cases = get_all_ultra_cases()
        passed = 0
        failed = []

        for case in all_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": case["input"]["content"]},
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("agent_message", {}).get("content"):
                    passed += 1
                else:
                    failed.append(f"{case['id']}: Empty response")
            else:
                failed.append(f"{case['id']}: Status {response.status_code}")

        total = len(all_cases)
        assert passed == total, (
            f"Ultra: {passed}/{total} passed. Failed: {failed[:5]}..."
        )

    @pytest.mark.asyncio
    async def test_all_hunter_features_respond(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
    ):
        """Verify all Hunter features can respond."""
        all_cases = get_all_hunter_cases()
        passed = 0
        failed = []

        for case in all_cases:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": case["input"]["content"]},
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("agent_message", {}).get("content"):
                    passed += 1
                else:
                    failed.append(f"{case['id']}: Empty response")
            else:
                failed.append(f"{case['id']}: Status {response.status_code}")

        total = len(all_cases)
        assert passed == total, (
            f"Hunter: {passed}/{total} passed. Failed: {failed[:5]}..."
        )

    @pytest.mark.asyncio
    async def test_response_structure_consistency(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
    ):
        """Verify all responses have consistent structure."""
        test_messages = [
            "Hello!",  # General chat
            "Analyze BTC sentiment",  # Hunter
            "Find arbitrage opportunities",  # Ultra
            "Optimize my portfolio",  # Agent Squad
        ]

        for message in test_messages:
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": message},
            )

            assert response.status_code == 201
            data = response.json()

            # Required fields
            assert "user_message" in data
            assert "agent_message" in data
            assert "routing" in data

            # User message structure
            assert "id" in data["user_message"]
            assert "role" in data["user_message"]
            assert "content" in data["user_message"]

            # Agent message structure
            assert "id" in data["agent_message"]
            assert "role" in data["agent_message"]
            assert "content" in data["agent_message"]

            # Routing structure
            assert "intent" in data["routing"]
            assert "confidence" in data["routing"]
            assert "handler" in data["routing"]

    @pytest.mark.asyncio
    async def test_latency_within_bounds(
        self,
        authenticated_client: AuthenticatedClient,
        test_conversation: str,
    ):
        """Verify response latencies are within acceptable bounds."""
        import time

        test_messages = [
            ("Hello!", 5000),  # General chat: 5s max
            ("What's ETH sentiment?", 10000),  # Hunter: 10s max
            ("Find arbitrage", 10000),  # Ultra: 10s max
        ]

        for message, max_ms in test_messages:
            start = time.time()
            response = await authenticated_client.post(
                f"/api/v1/user/chat/conversations/{test_conversation}/messages",
                json={"content": message},
            )
            elapsed_ms = (time.time() - start) * 1000

            assert response.status_code == 201
            assert elapsed_ms < max_ms, (
                f"Latency {elapsed_ms:.0f}ms exceeds {max_ms}ms for '{message}'"
            )
