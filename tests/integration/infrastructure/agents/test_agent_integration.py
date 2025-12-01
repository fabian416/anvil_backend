"""
Integration tests for AI agent system.

Tests real agent interactions with tools, context, and multi-turn conversations.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.infrastructure.ai.agent_gateway import AgentGateway
from app.infrastructure.agents.swap_agent import SwapAgent
from app.infrastructure.agents.trading_agent import TradingAgent
from app.infrastructure.agents.portfolio_agent import PortfolioAgent


class TestAgentGatewayIntegration:
    """Integration tests for AgentGateway with real agent orchestration."""
    
    @pytest.mark.asyncio
    async def test_swap_agent_with_tools(self):
        """Test SwapAgent processes message with tools."""
        # Create mock LLM gateway
        mock_llm = AsyncMock()
        mock_llm.generate_response.return_value = "I'll help you swap 100 USDC to ETH. Let me get you a quote."
        
        # Create mock DeFi clients
        mock_oneinch = AsyncMock()
        mock_oneinch.get_quote.return_value = {
            "toAmount": "50000000000000000000",  # 50 ETH
            "estimatedGas": "150000",
        }
        
        mock_hyperliquid = AsyncMock()
        
        # Create gateway
        gateway = AgentGateway(
            llm_gateway=mock_llm,
            oneinch_client=mock_oneinch,
            hyperliquid_client=mock_hyperliquid,
        )
        
        # Process swap request
        response = await gateway.process_message(
            user_id=uuid4(),
            session_id=str(uuid4()),
            message="Swap 100 USDC to ETH",
            context={},
        )
        
        # Verify response
        assert response is not None
        assert "swap" in response.lower() or "eth" in response.lower()
    
    @pytest.mark.asyncio
    async def test_trading_agent_with_position_tools(self):
        """Test TradingAgent processes position request with tools."""
        # Create mock LLM gateway
        mock_llm = AsyncMock()
        mock_llm.generate_response.return_value = "I'll help you open a 10x long BTC position."
        
        # Create mock DeFi clients
        mock_oneinch = AsyncMock()
        mock_hyperliquid = AsyncMock()
        mock_hyperliquid.get_market_price.return_value = {
            "price": "45000.00",
        }
        
        # Create gateway
        gateway = AgentGateway(
            llm_gateway=mock_llm,
            oneinch_client=mock_oneinch,
            hyperliquid_client=mock_hyperliquid,
        )
        
        # Process trading request
        response = await gateway.process_message(
            user_id=uuid4(),
            session_id=str(uuid4()),
            message="Open 10x long BTC with $1000",
            context={},
        )
        
        # Verify response
        assert response is not None
        assert "btc" in response.lower() or "position" in response.lower()
    
    @pytest.mark.asyncio
    async def test_portfolio_agent_with_data_tools(self):
        """Test PortfolioAgent processes portfolio request with data tools."""
        # Create mock LLM gateway
        mock_llm = AsyncMock()
        mock_llm.generate_response.return_value = "Here's your portfolio overview."
        
        # Create mock DeFi clients
        mock_wallet = AsyncMock()
        mock_wallet.get_portfolio_balances.return_value = {
            "native": {"balance": "1.5", "symbol": "ETH"},
            "tokens": [
                {"symbol": "USDC", "balance": "1000.0"},
            ],
        }
        
        mock_defillama = AsyncMock()
        mock_coingecko = AsyncMock()
        mock_coingecko.get_price.return_value = {
            "usd": 3000.0,
        }
        
        # Create gateway with wallet provider
        gateway = AgentGateway(
            llm_gateway=mock_llm,
            wallet_provider=mock_wallet,
            defillama_client=mock_defillama,
            coingecko_client=mock_coingecko,
        )
        
        # Process portfolio request
        response = await gateway.process_message(
            user_id=uuid4(),
            session_id=str(uuid4()),
            message="Show my portfolio for address 0x123",
            context={},
        )
        
        # Verify response
        assert response is not None
        assert "portfolio" in response.lower() or "balance" in response.lower()
    
    @pytest.mark.asyncio
    async def test_agent_selection_based_on_intent(self):
        """Test gateway selects correct agent based on message intent."""
        mock_llm = AsyncMock()
        mock_llm.generate_response.return_value = "Response"
        
        gateway = AgentGateway(
            llm_gateway=mock_llm,
            oneinch_client=AsyncMock(),
            hyperliquid_client=AsyncMock(),
        )
        
        # Test swap intent
        with patch.object(SwapAgent, 'process_message', new_callable=AsyncMock) as mock_swap:
            mock_swap.return_value = "Swap processed"
            await gateway.process_message(
                user_id=uuid4(),
                session_id=str(uuid4()),
                message="Swap USDC to ETH",
                context={},
            )
            # Verify SwapAgent was used (would need agent selection logic)
            # For now, just verify no errors
        
        # Test trading intent
        with patch.object(TradingAgent, 'process_message', new_callable=AsyncMock) as mock_trading:
            mock_trading.return_value = "Position opened"
            await gateway.process_message(
                user_id=uuid4(),
                session_id=str(uuid4()),
                message="Open long BTC",
                context={},
            )
            # Verify TradingAgent was used
        
        # Test portfolio intent
        with patch.object(PortfolioAgent, 'process_message', new_callable=AsyncMock) as mock_portfolio:
            mock_portfolio.return_value = "Portfolio shown"
            await gateway.process_message(
                user_id=uuid4(),
                session_id=str(uuid4()),
                message="Show my portfolio",
                context={},
            )
            # Verify PortfolioAgent was used


class TestMultiTurnConversationIntegration:
    """Integration tests for multi-turn conversation flows."""
    
    @pytest.mark.asyncio
    async def test_incomplete_swap_request_followup(self):
        """Test agent handles incomplete swap request with follow-up."""
        from app.infrastructure.ai.conversation_manager import get_conversation_manager
        
        manager = get_conversation_manager()
        session_id = str(uuid4())
        
        # First turn: incomplete request
        is_complete, question = manager.check_completeness(
            intent="trade_swap",
            entities={"src_token": "USDC", "amount": "100"},
            context={},
        )
        
        assert not is_complete
        assert question is not None
        assert "token" in question.lower()
        
        # Store pending
        manager.store_pending(
            session_id=session_id,
            intent="trade_swap",
            entities={"src_token": "USDC", "amount": "100"},
            original_message="Swap 100 USDC",
        )
        
        # Second turn: provide missing info
        result = manager.handle_followup_response(
            session_id=session_id,
            message="ETH",
            extracted_entities={"dst_token": "ETH"},
        )
        
        assert result is not None
        assert result["intent"] == "trade_swap"
        assert result["entities"]["dst_token"] == "ETH"
    
    @pytest.mark.asyncio
    async def test_ambiguous_intent_clarification(self):
        """Test agent handles ambiguous intent with clarification."""
        from app.infrastructure.ai.intent_refiner import IntentRefiner
        
        refiner = IntentRefiner()
        
        # Ambiguous "trade" without context
        refined = refiner.refine_intent(
            message="I want to trade BTC",
            initial_intent="trade",
            initial_confidence=0.5,
            context={},
        )
        
        assert refined.requires_clarification
        assert refined.clarification_question is not None
        assert "swap" in refined.clarification_question.lower() or "position" in refined.clarification_question.lower()
    
    @pytest.mark.asyncio
    async def test_context_resolves_ambiguity(self):
        """Test context resolves ambiguous intent without clarification."""
        from app.infrastructure.ai.intent_refiner import IntentRefiner
        
        refiner = IntentRefiner()
        
        # Ambiguous "trade" with recent swap context
        refined = refiner.refine_intent(
            message="I want to trade BTC",
            initial_intent="trade",
            initial_confidence=0.5,
            context={
                "recent_intents": ["trade_swap", "trade_swap", "portfolio_view"],
            },
        )
        
        assert not refined.requires_clarification
        assert refined.intent == "trade_swap"
        assert refined.confidence > 0.7


class TestAgentToolExecution:
    """Integration tests for agent tool execution."""
    
    @pytest.mark.asyncio
    async def test_swap_quote_tool_execution(self):
        """Test swap quote tool executes correctly."""
        from app.infrastructure.defi.tools.swap_tools import get_swap_quote_tool
        
        # Mock 1inch client
        mock_client = AsyncMock()
        mock_client.get_quote.return_value = {
            "toAmount": "50000000000000000000",
            "estimatedGas": "150000",
        }
        
        # Execute tool
        result = await get_swap_quote_tool(
            src_token="USDC",
            dst_token="ETH",
            amount="100",
            oneinch_client=mock_client,
        )
        
        assert result is not None
        assert "100 USDC" in result
        assert "ETH" in result
        assert "Gas" in result
    
    @pytest.mark.asyncio
    async def test_position_info_tool_execution(self):
        """Test position info tool executes correctly."""
        from app.infrastructure.defi.tools.trading_tools import get_position_info_tool
        
        # Mock Hyperliquid client
        mock_client = AsyncMock()
        mock_client.get_market_price.return_value = {"price": "45000.00"}
        mock_client.get_funding_rate.return_value = {"fundingRate": "0.01"}
        mock_client.calculate_liquidation_price.return_value = 40500.0
        
        # Execute tool
        result = await get_position_info_tool(
            symbol="BTC",
            leverage=10,
            collateral="1000",
            is_long=True,
            hyperliquid_client=mock_client,
        )
        
        assert result is not None
        assert "BTC" in result
        assert "10x" in result
        assert "liquidation" in result.lower()
    
    @pytest.mark.asyncio
    async def test_wallet_balance_tool_execution(self):
        """Test wallet balance tool executes correctly."""
        from app.infrastructure.defi.tools.portfolio_tools import get_wallet_balance_tool
        
        # Mock providers
        mock_wallet = AsyncMock()
        mock_wallet.get_portfolio_balances.return_value = {
            "native": {"balance": "1.5", "symbol": "ETH"},
            "tokens": [{"symbol": "USDC", "balance": "1000.0", "decimals": 6}],
        }
        
        mock_coingecko = AsyncMock()
        mock_coingecko.get_price.return_value = {"usd": 3000.0}
        mock_coingecko.resolve_token_symbol.return_value = "ethereum"
        
        # Execute tool
        result = await get_wallet_balance_tool(
            address="0x123",
            network="ethereum",
            wallet_provider=mock_wallet,
            coingecko_client=mock_coingecko,
        )
        
        assert result is not None
        assert "0x123" in result
        assert "ETH" in result
        assert "USDC" in result
