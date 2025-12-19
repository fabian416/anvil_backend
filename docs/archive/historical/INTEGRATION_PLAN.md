# Anvil Backend - Integration Plan (Excluding Privy)

**Date:** December 1, 2025  
**Owner:** Development Team  
**Status:** Active Planning  
**Duration:** 9-10 Weeks  

---

## Executive Summary

This plan covers all critical integrations needed to complete the Anvil MVP, **excluding Privy integration** (handled by separate developer). The focus is on agent orchestration, DeFi operations, blockchain interactions, and real-time communication.

### Scope: 7 Major Integration Areas
1. Agent Orchestration (Agent Squad)
2. Agent Runtime (Agno)
3. DeFi Data Providers (1inch, DefiLlama, The Graph)
4. Blockchain Infrastructure (Web3.py, RPC Providers)
5. DeFi Protocol SDKs (Hyperliquid, Aave)
6. Real-time Communication (WebSocket/SSE)
7. Chat Feature Complete Implementation

### Timeline: 9-10 Weeks
- **Phase 1 (Weeks 1-3):** Core Agent Infrastructure
- **Phase 2 (Weeks 4-6):** DeFi Operations & Blockchain
- **Phase 3 (Weeks 7-9):** Integration & Testing
- **Week 10:** Buffer & Polish

---

## Phase 1: Core Agent Infrastructure (Weeks 1-3)

### 🎯 Goal: Get agents working end-to-end with real data

---

### **Integration 1: Agent Squad (Manager/Router)**

**Duration:** Week 1 (5 days)  
**Priority:** CRITICAL  
**Dependencies:** None  
**Owner:** Backend Team

#### 1.1 Current State
```python
# File: src/app/infrastructure/adapters/ai/agent_gateway_impl.py
# Status: Imports commented out, mock implementation

# from agent_squad.orchestrator import AgentSquad
# from agent_squad.core import AgentSquadOptions
```

#### 1.2 Implementation Steps

**Day 1: Setup & Configuration**
- [ ] Create Agent Squad configuration file
  ```python
  # File: src/app/setup/config/agent_squad.py
  
  from dataclasses import dataclass
  from typing import List
  
  @dataclass
  class AgentSquadConfig:
      default_model: str = "gpt-4-turbo"
      fallback_model: str = "gpt-3.5-turbo"
      intent_threshold: float = 0.75
      session_timeout: int = 3600  # 1 hour
      max_context_messages: int = 20
  ```

- [ ] Add Agent Squad settings to TOML config
  ```toml
  # File: config/local/config.toml
  
  [agent_squad]
  default_model = "gpt-4-turbo"
  fallback_model = "gpt-3.5-turbo"
  intent_threshold = 0.75
  session_timeout = 3600
  max_context_messages = 20
  ```

**Day 2: Storage Adapter**
- [ ] Implement SQLAlchemy storage adapter for Agent Squad
  ```python
  # File: src/app/infrastructure/adapters/ai/squad_storage.py
  # Status: EXISTS but needs enhancement
  
  from agent_squad.storage import ChatStorage
  from app.domain.ports.ai.llm_conversation_repository import LLMConversationRepository
  
  class AnvilSquadStorage(ChatStorage):
      """Maps Agent Squad storage to our ConversationRepository"""
      
      def __init__(self, conversation_repo: LLMConversationRepository):
          self._repo = conversation_repo
      
      async def save_message(self, session_id: str, role: str, content: str):
          # Implement using our repository
          pass
      
      async def get_history(self, session_id: str, limit: int = 20):
          # Implement using our repository
          pass
  ```

- [ ] Add storage adapter to dependency injection
  ```python
  # File: src/app/setup/ioc/infrastructure.py
  
  @provide
  def get_squad_storage(
      self, 
      repo: LLMConversationRepository
  ) -> AnvilSquadStorage:
      return AnvilSquadStorage(repo)
  ```

**Day 3: Intent Classification**
- [ ] Define DeFi intent classifiers
  ```python
  # File: src/app/infrastructure/agents/classifiers.py
  
  from agent_squad.classifiers import IntentClassifier
  
  class DeFiIntentClassifier:
      """Classifies user intents for DeFi operations"""
      
      INTENTS = [
          "trade_swap",           # "swap 100 USDC to ETH"
          "trade_perp_open",      # "open 10x long on BTC"
          "trade_perp_close",     # "close my ETH position"
          "lend_supply",          # "lend 1000 USDC on Aave"
          "lend_borrow",          # "borrow ETH against my USDC"
          "earn_stake",           # "stake ETH for yield"
          "portfolio_view",       # "show my portfolio"
          "market_info",          # "what's the funding rate on BTC?"
          "risk_analysis",        # "analyze my position risk"
          "save_schedule",        # "save $100 weekly to USDC"
          "general_question",     # "how does Aave work?"
      ]
      
      def __init__(self, model: str = "gpt-4-turbo"):
          self.classifier = IntentClassifier(
              intents=self.INTENTS,
              model=model,
              examples=self._get_examples()
          )
      
      def _get_examples(self):
          return {
              "trade_swap": [
                  "swap 100 USDC to ETH",
                  "exchange my DAI for USDC",
                  "convert 0.5 ETH to USDC"
              ],
              "trade_perp_open": [
                  "open 10x long on BTC",
                  "long ETH with 5x leverage",
                  "short SOL 20x"
              ],
              # ... more examples
          }
  ```

**Day 4: AgentGateway Implementation**
- [ ] Uncomment and implement AgentGatewayImpl
  ```python
  # File: src/app/infrastructure/adapters/ai/agent_gateway_impl.py
  
  from typing import Dict, Any, Optional
  from uuid import UUID
  from agent_squad.orchestrator import AgentSquad
  from agent_squad.core import AgentSquadOptions
  from app.domain.ports.ai.agent_gateway import AgentGateway
  from app.infrastructure.adapters.ai.squad_storage import AnvilSquadStorage
  from app.infrastructure.agents.classifiers import DeFiIntentClassifier
  
  class AgentGatewayImpl(AgentGateway):
      def __init__(
          self, 
          storage: AnvilSquadStorage,
          config: AgentSquadConfig
      ):
          self.storage = storage
          self.config = config
          
          # Initialize Agent Squad
          self.orchestrator = AgentSquad(
              options=AgentSquadOptions(
                  storage=storage,
                  classifiers=[DeFiIntentClassifier(config.default_model)],
                  default_model=config.default_model,
                  fallback_model=config.fallback_model
              )
          )
          
          # Register agents (we'll implement these in next integration)
          self._register_agents()
      
      def _register_agents(self):
          """Register all specialized agents"""
          # To be implemented with Agno integration
          pass
      
      async def process_message(
          self, 
          user_id: UUID, 
          session_id: str, 
          message: str,
          context: Optional[Dict[str, Any]] = None
      ) -> str:
          """Route message to appropriate agent and return response"""
          
          # Agent Squad handles:
          # 1. Intent classification
          # 2. Agent selection
          # 3. Context management
          # 4. Response generation
          
          response = await self.orchestrator.route_request(
              message=message,
              user_id=str(user_id),
              session_id=session_id,
              context=context or {}
          )
          
          return response.text
  ```

**Day 5: Testing & Documentation**
- [ ] Write unit tests for AgentGatewayImpl
  ```python
  # File: tests/unit/infrastructure/adapters/ai/test_agent_gateway_impl.py
  
  import pytest
  from uuid import uuid4
  from app.infrastructure.adapters.ai.agent_gateway_impl import AgentGatewayImpl
  
  @pytest.mark.asyncio
  async def test_agent_gateway_routes_message():
      # Test basic message routing
      pass
  
  @pytest.mark.asyncio
  async def test_intent_classification():
      # Test intent classifier
      pass
  ```

- [ ] Integration test with database
  ```python
  # File: tests/integration/ai/test_agent_gateway_integration.py
  
  @pytest.mark.asyncio
  async def test_agent_gateway_with_real_storage():
      # Test with real database
      pass
  ```

- [ ] Update documentation
  ```markdown
  # File: docs/integrations/agent_squad.md
  
  # Agent Squad Integration
  
  ## Overview
  Agent Squad provides the "Manager" layer for our multi-agent system.
  
  ## Configuration
  ...
  
  ## Usage
  ...
  ```

#### 1.3 Success Criteria
- [ ] Agent Squad initialized without errors
- [ ] Intent classification working for 11 intent types
- [ ] Session context persisted to database
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing

#### 1.4 Rollback Plan
If Agent Squad integration fails:
- Revert to direct LLM calls (already implemented in LLMGatewayImpl)
- Implement simple rule-based intent classification
- Manual agent selection based on keywords

---

### **Integration 2: Agno Runtime (Workers)**

**Duration:** Week 2 (5 days)  
**Priority:** CRITICAL  
**Dependencies:** Agent Squad (Week 1)  
**Owner:** Backend Team

#### 2.1 Current State
```python
# Files: src/app/infrastructure/agents/
# - base.py (AnvilAgent wrapper exists, Agno imports commented)
# - trading_agent.py (skeleton)
# - risk_agent.py (skeleton)
```

#### 2.2 Implementation Steps

**Day 1: Base Agent Setup**
- [ ] Uncomment and configure Agno imports
  ```python
  # File: src/app/infrastructure/agents/base.py
  
  from typing import List, Any, Optional
  from agno.agent import Agent
  from agno.models.openai import OpenAIChat
  from agno.tools import Tool
  
  class AnvilAgent:
      """Base wrapper for Agno Agents"""
      
      def __init__(
          self, 
          name: str, 
          model_id: str = "gpt-4-turbo",
          tools: Optional[List[Tool]] = None,
          instructions: Optional[str] = None,
          markdown: bool = True
      ):
          self.name = name
          self.model_id = model_id
          
          self.agent = Agent(
              name=name,
              model=OpenAIChat(id=model_id),
              tools=tools or [],
              instructions=instructions or self._default_instructions(),
              markdown=markdown,
              show_tool_calls=True,
              debug_mode=False
          )
      
      def _default_instructions(self) -> str:
          return f"""You are {self.name}, a specialized DeFi assistant.
          Provide clear, accurate, and actionable advice.
          Always explain risks and never guarantee returns."""
      
      async def run(self, prompt: str, context: Optional[dict] = None) -> str:
          """Execute agent with prompt and context"""
          response = await self.agent.run(prompt, context=context)
          return response.content
  ```

**Day 2: Trading Agent (Hyperliquid)**
- [ ] Implement Hyperliquid tools
  ```python
  # File: src/app/infrastructure/agents/tools/hyperliquid.py
  
  from typing import List, Dict, Any
  from agno.tools import Tool
  import httpx
  
  class HyperliquidTools:
      """Tools for Hyperliquid perpetual futures"""
      
      BASE_URL = "https://api.hyperliquid.xyz"
      
      def __init__(self):
          self.client = httpx.AsyncClient(base_url=self.BASE_URL)
      
      @Tool
      async def get_funding_rate(self, coin: str) -> Dict[str, Any]:
          """Get current funding rate for a coin
          
          Args:
              coin: Trading pair symbol (e.g., "BTC", "ETH")
          
          Returns:
              Funding rate information
          """
          response = await self.client.get(f"/info/funding/{coin}")
          return response.json()
      
      @Tool
      async def get_positions(self, wallet_address: str) -> List[Dict[str, Any]]:
          """Get open positions for a wallet
          
          Args:
              wallet_address: Ethereum wallet address
          
          Returns:
              List of open positions
          """
          response = await self.client.post(
              "/info/positions",
              json={"user": wallet_address}
          )
          return response.json()
      
      @Tool
      async def get_market_info(self, coin: str) -> Dict[str, Any]:
          """Get market information (mark price, volume, etc.)
          
          Args:
              coin: Trading pair symbol
          
          Returns:
              Market information
          """
          response = await self.client.get(f"/info/market/{coin}")
          return response.json()
      
      @Tool
      async def create_order_preview(
          self,
          coin: str,
          is_buy: bool,
          size: float,
          leverage: int,
          limit_price: Optional[float] = None
      ) -> Dict[str, Any]:
          """Create an UNSIGNED order preview (for user approval)
          
          SECURITY: This does NOT execute trades, only prepares the payload
          
          Args:
              coin: Trading pair
              is_buy: True for long, False for short
              size: Position size in USD
              leverage: Leverage multiplier (1-50x)
              limit_price: Limit price (None for market order)
          
          Returns:
              Unsigned transaction payload for frontend wallet signing
          """
          order = {
              "coin": coin,
              "is_buy": is_buy,
              "sz": size,
              "leverage": leverage,
              "limit_px": limit_price,
              "order_type": "market" if limit_price is None else "limit",
              "reduce_only": False
          }
          
          # Return unsigned payload
          return {
              "action": "open_position",
              "chain": "arbitrum",
              "contract": "hyperliquid_perp",
              "order": order,
              "requires_signature": True,
              "estimated_gas": "0.001 ETH",
              "warnings": [
                  f"Opening {leverage}x leveraged position",
                  "Liquidation risk exists",
                  "Funding rates apply"
              ]
          }
  ```

- [ ] Implement Trading Agent
  ```python
  # File: src/app/infrastructure/agents/trading_agent.py
  
  from app.infrastructure.agents.base import AnvilAgent
  from app.infrastructure.agents.tools.hyperliquid import HyperliquidTools
  
  class TradingAgent(AnvilAgent):
      """Specialized agent for perpetual futures trading"""
      
      INSTRUCTIONS = """
      You are a Perpetual Futures Trading Specialist for Hyperliquid.
      
      CAPABILITIES:
      - Check funding rates for any trading pair
      - View open positions and their PnL
      - Get real-time market data
      - Create UNSIGNED order previews for user approval
      
      IMPORTANT RULES:
      1. NEVER execute trades directly - only create unsigned transaction previews
      2. Always explain leverage risks clearly
      3. Show funding rates before suggesting positions
      4. Calculate liquidation prices
      5. Warn about market volatility
      6. Never guarantee profits
      
      WORKFLOW:
      1. User asks to trade
      2. You fetch current market data and funding rates
      3. You explain the trade parameters and risks
      4. You create an UNSIGNED transaction preview
      5. You return the preview for user wallet approval
      
      Be concise but thorough. Use markdown formatting.
      """
      
      def __init__(self):
          tools = HyperliquidTools()
          super().__init__(
              name="TradingAgent",
              model_id="gpt-4-turbo",
              tools=[tools],
              instructions=self.INSTRUCTIONS
          )
  ```

**Day 3: Risk Agent**
- [ ] Implement risk analysis tools
  ```python
  # File: src/app/infrastructure/agents/tools/risk_analysis.py
  
  from typing import Dict, Any, List
  from agno.tools import Tool
  
  class RiskAnalysisTools:
      """Tools for analyzing DeFi position risks"""
      
      @Tool
      async def calculate_liquidation_price(
          self,
          entry_price: float,
          leverage: int,
          is_long: bool,
          maintenance_margin: float = 0.03  # 3%
      ) -> Dict[str, Any]:
          """Calculate liquidation price for leveraged position
          
          Args:
              entry_price: Position entry price
              leverage: Leverage multiplier
              is_long: True for long position, False for short
              maintenance_margin: Maintenance margin requirement (default 3%)
          
          Returns:
              Liquidation price and distance
          """
          if is_long:
              liq_price = entry_price * (1 - (1/leverage) + maintenance_margin)
          else:
              liq_price = entry_price * (1 + (1/leverage) - maintenance_margin)
          
          distance_pct = abs((liq_price - entry_price) / entry_price * 100)
          
          return {
              "liquidation_price": round(liq_price, 2),
              "current_price": entry_price,
              "distance_percent": round(distance_pct, 2),
              "direction": "long" if is_long else "short",
              "leverage": leverage,
              "risk_level": self._assess_risk(distance_pct)
          }
      
      @Tool
      async def analyze_portfolio_risk(
          self,
          positions: List[Dict[str, Any]]
      ) -> Dict[str, Any]:
          """Analyze overall portfolio risk
          
          Args:
              positions: List of open positions
          
          Returns:
              Risk assessment with recommendations
          """
          total_exposure = sum(p.get("size", 0) for p in positions)
          weighted_leverage = sum(
              p.get("size", 0) * p.get("leverage", 1) 
              for p in positions
          ) / total_exposure if total_exposure > 0 else 0
          
          return {
              "total_positions": len(positions),
              "total_exposure_usd": total_exposure,
              "average_leverage": round(weighted_leverage, 2),
              "risk_level": self._assess_portfolio_risk(weighted_leverage),
              "recommendations": self._get_recommendations(positions)
          }
      
      def _assess_risk(self, distance_pct: float) -> str:
          """Assess risk based on liquidation distance"""
          if distance_pct < 5:
              return "CRITICAL"
          elif distance_pct < 10:
              return "HIGH"
          elif distance_pct < 20:
              return "MEDIUM"
          else:
              return "LOW"
      
      def _assess_portfolio_risk(self, avg_leverage: float) -> str:
          """Assess portfolio risk based on average leverage"""
          if avg_leverage > 20:
              return "VERY_HIGH"
          elif avg_leverage > 10:
              return "HIGH"
          elif avg_leverage > 5:
              return "MEDIUM"
          else:
              return "LOW"
      
      def _get_recommendations(self, positions: List[Dict]) -> List[str]:
          """Generate risk recommendations"""
          recommendations = []
          
          high_leverage_count = sum(1 for p in positions if p.get("leverage", 1) > 10)
          if high_leverage_count > 0:
              recommendations.append(
                  f"Consider reducing leverage on {high_leverage_count} position(s)"
              )
          
          # More recommendations...
          
          return recommendations
  ```

- [ ] Implement Risk Agent
  ```python
  # File: src/app/infrastructure/agents/risk_agent.py
  
  from app.infrastructure.agents.base import AnvilAgent
  from app.infrastructure.agents.tools.risk_analysis import RiskAnalysisTools
  
  class RiskAgent(AnvilAgent):
      """Specialized agent for risk analysis"""
      
      INSTRUCTIONS = """
      You are a DeFi Risk Analysis Specialist.
      
      CAPABILITIES:
      - Calculate liquidation prices for leveraged positions
      - Analyze overall portfolio risk
      - Provide risk mitigation recommendations
      - Assess position sizing
      
      YOUR ROLE:
      - Always provide honest risk assessments
      - Never downplay risks to encourage trading
      - Use clear risk levels (LOW, MEDIUM, HIGH, CRITICAL)
      - Provide actionable recommendations
      - Explain risk concepts in simple terms
      
      Be direct and honest about risks. User safety is priority #1.
      """
      
      def __init__(self):
          tools = RiskAnalysisTools()
          super().__init__(
              name="RiskAgent",
              model_id="gpt-4-turbo",
              tools=[tools],
              instructions=self.INSTRUCTIONS
          )
  ```

**Day 4: Lending Agent (Aave)**
- [ ] Implement Aave tools (similar structure to Hyperliquid)
- [ ] Create LendingAgent class

**Day 5: Agent Registration & Testing**
- [ ] Register agents with Agent Squad
  ```python
  # File: src/app/infrastructure/adapters/ai/agent_gateway_impl.py
  
  def _register_agents(self):
      """Register all specialized agents with Agent Squad"""
      from app.infrastructure.agents.trading_agent import TradingAgent
      from app.infrastructure.agents.risk_agent import RiskAgent
      from app.infrastructure.agents.lending_agent import LendingAgent
      
      # Register with intent mappings
      self.orchestrator.register_agent(
          agent=TradingAgent(),
          intents=["trade_swap", "trade_perp_open", "trade_perp_close"]
      )
      
      self.orchestrator.register_agent(
          agent=RiskAgent(),
          intents=["risk_analysis", "portfolio_view"]
      )
      
      self.orchestrator.register_agent(
          agent=LendingAgent(),
          intents=["lend_supply", "lend_borrow"]
      )
  ```

- [ ] Write comprehensive tests
- [ ] Test end-to-end agent flow

#### 2.3 Success Criteria
- [ ] All 3 agents (Trading, Risk, Lending) operational
- [ ] Tools correctly integrated with Agno
- [ ] Agents registered with Agent Squad
- [ ] End-to-end test: User message → Intent → Agent → Response
- [ ] No actual transaction execution (only unsigned previews)

---

### **Integration 3: Chat Feature Real Implementation**

**Duration:** Week 3 (5 days)  
**Priority:** CRITICAL  
**Dependencies:** Agent Squad + Agno (Weeks 1-2)  
**Owner:** Backend Team

#### 3.1 Current State
```python
# File: src/app/presentation/http/controllers/chat/router.py
# Status: Returns hardcoded mock data

@router.post("/conversations/{conversation_id}/messages", response_model=MessageRead)
async def send_message(conversation_id: UUID, data: MessageCreate):
    return MessageRead(
        id=uuid4(),
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=data.content,
        agent_type=data.agent_type,
        created_at=datetime.now()
    )
```

#### 3.2 Implementation Steps

**Day 1: Complete Command Interactors**
- [ ] Finish CreateConversation interactor
  ```python
  # File: src/app/application/commands/chat/create_conversation.py
  
  from uuid import UUID
  from app.domain.entities.conversation import Conversation
  from app.domain.value_objects.conversation_id import ConversationId
  from app.domain.value_objects.user_id import UserId
  from app.domain.ports.ai.llm_conversation_repository import LLMConversationRepository
  from app.application.common.ports.transaction_manager import TransactionManager
  
  class CreateConversation:
      def __init__(
          self, 
          repo: LLMConversationRepository,
          tx: TransactionManager
      ):
          self._repo = repo
          self._tx = tx
  
      async def execute(self, user_id: int, title: str = None) -> Conversation:
          """Create a new conversation for a user"""
          
          # Create entity using factory method
          conversation = Conversation.create(
              user_id=UserId(user_id),
              title=ConversationTitle(title) if title else None
          )
          
          # Persist within transaction
          async with self._tx:
              await self._repo.add(conversation)
          
          return conversation
  ```

- [ ] Finish SendMessage interactor
  ```python
  # File: src/app/application/commands/chat/send_message.py
  
  from uuid import UUID
  from app.domain.entities.message import Message
  from app.domain.enums.message_role import MessageRole
  from app.domain.value_objects.message_id import MessageId
  from app.domain.value_objects.conversation_id import ConversationId
  from app.domain.value_objects.message_content import MessageContent
  from app.domain.ports.ai.llm_conversation_repository import LLMConversationRepository
  from app.application.common.ports.transaction_manager import TransactionManager
  from app.infrastructure.celery.tasks import process_agent_response
  
  class SendMessage:
      def __init__(
          self,
          repo: LLMConversationRepository,
          tx: TransactionManager
      ):
          self._repo = repo
          self._tx = tx
  
      async def execute(
          self, 
          conversation_id: UUID, 
          content: str,
          user_id: int
      ) -> Message:
          """Send a user message and trigger agent processing"""
          
          # Validate conversation exists and belongs to user
          conversation = await self._repo.get_conversation(conversation_id)
          if not conversation:
              raise ConversationNotFoundError(conversation_id)
          if conversation.user_id.value != user_id:
              raise UnauthorizedError("Not your conversation")
          
          # Create message entity
          message = Message.create(
              conversation_id=ConversationId(conversation_id),
              role=MessageRole.USER,
              content=MessageContent(content),
              agent_type=None
          )
          
          # Persist message
          async with self._tx:
              await self._repo.add_message(message)
          
          # Trigger async agent processing (Celery task)
          process_agent_response.delay(
              conversation_id=str(conversation_id),
              message_id=str(message.id_.value),
              user_id=user_id
          )
          
          return message
  ```

**Day 2: Implement Query Interactors**
- [ ] GetConversation query
  ```python
  # File: src/app/application/queries/chat/get_conversation.py
  
  from uuid import UUID
  from typing import List
  from app.domain.entities.conversation import Conversation
  from app.domain.entities.message import Message
  from app.domain.ports.ai.llm_conversation_repository import LLMConversationRepository
  
  class GetConversation:
      def __init__(self, repo: LLMConversationRepository):
          self._repo = repo
      
      async def execute(
          self, 
          conversation_id: UUID, 
          user_id: int,
          limit: int = 50
      ) -> tuple[Conversation, List[Message]]:
          """Get conversation with message history"""
          
          conversation = await self._repo.get_conversation(conversation_id)
          if not conversation:
              raise ConversationNotFoundError(conversation_id)
          
          # Verify ownership
          if conversation.user_id.value != user_id:
              raise UnauthorizedError("Not your conversation")
          
          # Get messages
          messages = await self._repo.get_messages(
              conversation_id=conversation_id,
              limit=limit
          )
          
          return conversation, messages
  ```

- [ ] ListConversations query
  ```python
  # File: src/app/application/queries/chat/list_conversations.py
  
  from typing import List
  from app.domain.entities.conversation import Conversation
  from app.domain.ports.ai.llm_conversation_repository import LLMConversationRepository
  
  class ListConversations:
      def __init__(self, repo: LLMConversationRepository):
          self._repo = repo
      
      async def execute(
          self, 
          user_id: int,
          limit: int = 20,
          offset: int = 0
      ) -> List[Conversation]:
          """List user's conversations"""
          
          conversations = await self._repo.list_conversations(
              user_id=user_id,
              limit=limit,
              offset=offset
          )
          
          return conversations
  ```

**Day 3: Update Chat Controller**
- [ ] Replace mock implementation with real interactors
  ```python
  # File: src/app/presentation/http/controllers/chat/router.py
  
  from typing import List
  from uuid import UUID
  from fastapi import APIRouter, Security, Depends, status
  from dishka.integrations.fastapi import FromDishka, inject
  
  from app.presentation.http.schemas.chat.conversation import (
      ConversationCreate, ConversationRead
  )
  from app.presentation.http.schemas.chat.message import (
      MessageCreate, MessageRead
  )
  from app.application.commands.chat.create_conversation import CreateConversation
  from app.application.commands.chat.send_message import SendMessage
  from app.application.queries.chat.get_conversation import GetConversation
  from app.application.queries.chat.list_conversations import ListConversations
  from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
  from app.infrastructure.auth.handlers.get_current_user import get_current_user_id
  
  def create_chat_router() -> APIRouter:
      router = APIRouter(
          prefix="/chat", 
          tags=["chat"],
          dependencies=[Security(bearer_scheme)]
      )
  
      @router.post(
          "/conversations", 
          response_model=ConversationRead,
          status_code=status.HTTP_201_CREATED
      )
      @inject
      async def create_conversation(
          data: ConversationCreate,
          user_id: int = Depends(get_current_user_id),
          interactor: FromDishka[CreateConversation] = None
      ):
          """Create a new conversation"""
          conversation = await interactor.execute(
              user_id=user_id,
              title=data.title
          )
          return ConversationRead.from_entity(conversation)
  
      @router.get(
          "/conversations", 
          response_model=List[ConversationRead]
      )
      @inject
      async def list_conversations(
          user_id: int = Depends(get_current_user_id),
          limit: int = 20,
          offset: int = 0,
          interactor: FromDishka[ListConversations] = None
      ):
          """List user's conversations"""
          conversations = await interactor.execute(
              user_id=user_id,
              limit=limit,
              offset=offset
          )
          return [ConversationRead.from_entity(c) for c in conversations]
  
      @router.get(
          "/conversations/{conversation_id}", 
          response_model=ConversationRead
      )
      @inject
      async def get_conversation(
          conversation_id: UUID,
          user_id: int = Depends(get_current_user_id),
          interactor: FromDishka[GetConversation] = None
      ):
          """Get conversation details with messages"""
          conversation, messages = await interactor.execute(
              conversation_id=conversation_id,
              user_id=user_id
          )
          
          response = ConversationRead.from_entity(conversation)
          response.messages = [MessageRead.from_entity(m) for m in messages]
          return response
  
      @router.post(
          "/conversations/{conversation_id}/messages", 
          response_model=MessageRead,
          status_code=status.HTTP_202_ACCEPTED
      )
      @inject
      async def send_message(
          conversation_id: UUID,
          data: MessageCreate,
          user_id: int = Depends(get_current_user_id),
          interactor: FromDishka[SendMessage] = None
      ):
          """Send a message (triggers async agent processing)"""
          message = await interactor.execute(
              conversation_id=conversation_id,
              content=data.content,
              user_id=user_id
          )
          return MessageRead.from_entity(message)
  
      return router
  ```

**Day 4: Update Celery Task**
- [ ] Complete agent processing task
  ```python
  # File: src/app/infrastructure/celery/tasks.py
  
  @celery_app.task(
      name="process_agent_response",
      bind=True,
      max_retries=3,
      default_retry_delay=60
  )
  def process_agent_response(
      self,
      conversation_id: str, 
      message_id: str,
      user_id: int
  ):
      """Background task to process user message and generate agent response"""
      
      async def runner(container):
          from app.domain.ports.ai.agent_gateway import AgentGateway
          from app.domain.ports.ai.llm_conversation_repository import LLMConversationRepository
          from app.domain.entities.message import Message
          from app.domain.enums.message_role import MessageRole
          from app.domain.value_objects.message_content import MessageContent
          from uuid import UUID
          
          # Get dependencies
          gateway = await container.get(AgentGateway)
          repo = await container.get(LLMConversationRepository)
          tx = await container.get(TransactionManager)
          
          try:
              # Get user message
              user_message = await repo.get_message(UUID(message_id))
              if not user_message:
                  raise ValueError(f"Message {message_id} not found")
              
              # Get conversation history for context
              messages = await repo.get_messages(
                  conversation_id=UUID(conversation_id),
                  limit=20
              )
              
              # Build context
              context = {
                  "user_id": user_id,
                  "conversation_id": conversation_id,
                  "history": [
                      {"role": m.role.value, "content": m.content.value}
                      for m in messages
                  ]
              }
              
              # Process through agent gateway
              response_text = await gateway.process_message(
                  user_id=UUID(int=user_id),
                  session_id=conversation_id,
                  message=user_message.content.value,
                  context=context
              )
              
              # Create agent response message
              agent_message = Message.create(
                  conversation_id=ConversationId(UUID(conversation_id)),
                  role=MessageRole.AGENT,
                  content=MessageContent(response_text),
                  agent_type=None  # Will be set by gateway based on intent
              )
              
              # Save agent response
              async with tx:
                  await repo.add_message(agent_message)
              
              # TODO: Send notification (WebSocket, Push, etc.)
              
          except Exception as e:
              # Log error
              print(f"Error processing agent response: {e}")
              
              # Retry task
              raise self.retry(exc=e)
      
      asyncio.run(_run_task(runner))
  ```

**Day 5: Testing & Documentation**
- [ ] Integration tests for full flow
- [ ] API documentation update
- [ ] Test with real user scenarios

#### 3.3 Success Criteria
- [ ] POST /chat/conversations creates real conversation in DB
- [ ] POST /conversations/{id}/messages triggers agent processing
- [ ] GET endpoints return real data from DB
- [ ] Celery task processes messages and generates responses
- [ ] End-to-end test: Create conversation → Send message → Agent responds

---

## Phase 2: DeFi Operations & Blockchain (Weeks 4-6)

### 🎯 Goal: Enable real DeFi data and blockchain interactions

---

### **Integration 4: DeFi Data Providers**

**Duration:** Week 4 (5 days)  
**Priority:** HIGH  
**Dependencies:** None (can parallel with Phase 1)  
**Owner:** Backend Team

#### 4.1 Providers to Integrate
1. **1inch** - DEX aggregator for swap quotes
2. **DefiLlama** - Protocol analytics and TVL data
3. **The Graph** - On-chain data queries

#### 4.2 Implementation Steps

**Day 1: Define Ports**
- [ ] Create port interfaces
  ```python
  # File: src/app/domain/ports/defi/dex_aggregator.py
  
  from typing import Protocol, List, Dict, Any
  from decimal import Decimal
  
  class DexAggregatorPort(Protocol):
      """Port for DEX aggregator (1inch, 0x, etc.)"""
      
      async def get_quote(
          self,
          chain: str,
          from_token: str,
          to_token: str,
          amount: Decimal
      ) -> Dict[str, Any]:
          """Get swap quote"""
          ...
      
      async def get_swap_path(
          self,
          chain: str,
          from_token: str,
          to_token: str,
          amount: Decimal
      ) -> List[Dict[str, Any]]:
          """Get optimal swap path"""
          ...
  ```

  ```python
  # File: src/app/domain/ports/defi/protocol_analytics.py
  
  from typing import Protocol, Dict, Any, List
  
  class ProtocolAnalyticsPort(Protocol):
      """Port for protocol analytics (DefiLlama)"""
      
      async def get_protocol_tvl(self, protocol: str) -> Dict[str, Any]:
          """Get protocol total value locked"""
          ...
      
      async def get_yields(
          self,
          chain: str = None,
          protocol: str = None
      ) -> List[Dict[str, Any]]:
          """Get yield opportunities"""
          ...
  ```

**Day 2-3: Implement 1inch Adapter**
- [ ] 1inch API integration
  ```python
  # File: src/app/infrastructure/adapters/defi/oneinch_adapter.py
  
  from typing import Dict, Any, List
  from decimal import Decimal
  import httpx
  from app.domain.ports.defi.dex_aggregator import DexAggregatorPort
  
  class OneInchAdapter(DexAggregatorPort):
      """1inch DEX aggregator adapter"""
      
      BASE_URL = "https://api.1inch.dev/swap/v6.0"
      
      CHAIN_IDS = {
          "ethereum": 1,
          "arbitrum": 42161,
          "polygon": 137,
          "optimism": 10,
          "base": 8453
      }
      
      def __init__(self, api_key: str):
          self.api_key = api_key
          self.client = httpx.AsyncClient(
              base_url=self.BASE_URL,
              headers={"Authorization": f"Bearer {api_key}"}
          )
      
      async def get_quote(
          self,
          chain: str,
          from_token: str,
          to_token: str,
          amount: Decimal
      ) -> Dict[str, Any]:
          """Get swap quote from 1inch"""
          
          chain_id = self.CHAIN_IDS.get(chain.lower())
          if not chain_id:
              raise ValueError(f"Unsupported chain: {chain}")
          
          # Convert amount to smallest unit (wei for ETH)
          amount_wei = int(amount * Decimal(10**18))
          
          response = await self.client.get(
              f"/{chain_id}/quote",
              params={
                  "src": from_token,
                  "dst": to_token,
                  "amount": str(amount_wei)
              }
          )
          
          if response.status_code != 200:
              raise Exception(f"1inch API error: {response.text}")
          
          data = response.json()
          
          # Parse response
          return {
              "from_token": from_token,
              "to_token": to_token,
              "from_amount": str(amount),
              "to_amount": str(Decimal(data["dstAmount"]) / Decimal(10**18)),
              "estimated_gas": data.get("estimatedGas"),
              "price_impact": self._calculate_price_impact(data),
              "protocol_fees": data.get("protocols", []),
              "provider": "1inch"
          }
      
      async def get_swap_path(
          self,
          chain: str,
          from_token: str,
          to_token: str,
          amount: Decimal
      ) -> List[Dict[str, Any]]:
          """Get swap path with intermediate tokens"""
          
          quote = await self.get_quote(chain, from_token, to_token, amount)
          
          # Parse protocols from quote
          protocols = quote.get("protocol_fees", [])
          
          # Build swap path
          path = []
          for protocol in protocols:
              path.append({
                  "protocol": protocol.get("name"),
                  "part": protocol.get("part"),
                  "from_token": protocol.get("fromTokenAddress"),
                  "to_token": protocol.get("toTokenAddress")
              })
          
          return path
      
      def _calculate_price_impact(self, quote_data: Dict) -> str:
          """Calculate price impact percentage"""
          # Implementation based on 1inch response
          return "0.5%"  # Placeholder
  ```

**Day 4: Implement DefiLlama Adapter**
- [ ] Similar to 1inch adapter structure

**Day 5: Implement The Graph Adapter**
- [ ] GraphQL client for subgraph queries

#### 4.3 Success Criteria
- [ ] Get real swap quotes from 1inch
- [ ] Get yield data from DefiLlama
- [ ] Query on-chain data from The Graph
- [ ] Unit tests for each adapter
- [ ] Error handling for rate limits and API failures

---

### **Integration 5: Blockchain Infrastructure (Web3)**

**Duration:** Week 5 (5 days)  
**Priority:** HIGH  
**Dependencies:** DeFi Data Providers (Week 4)  
**Owner:** Backend Team

#### 5.1 Implementation Steps

**Day 1: RPC Provider Setup**
- [ ] Configure Infura/Alchemy
  ```python
  # File: src/app/setup/config/blockchain.py
  
  from dataclasses import dataclass
  from typing import Dict
  
  @dataclass
  class BlockchainConfig:
      """Blockchain RPC configuration"""
      
      infura_api_key: str
      alchemy_api_key: str
      
      rpc_endpoints: Dict[str, Dict[str, str]] = None
      
      def __post_init__(self):
          self.rpc_endpoints = {
              "ethereum": {
                  "infura": f"https://mainnet.infura.io/v3/{self.infura_api_key}",
                  "alchemy": f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
              },
              "arbitrum": {
                  "infura": f"https://arbitrum-mainnet.infura.io/v3/{self.infura_api_key}",
                  "alchemy": f"https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
              },
              "polygon": {
                  "infura": f"https://polygon-mainnet.infura.io/v3/{self.infura_api_key}",
                  "alchemy": f"https://polygon-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
              },
              "base": {
                  "infura": f"https://base-mainnet.infura.io/v3/{self.infura_api_key}",
                  "alchemy": f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
              }
          }
  ```

**Day 2-3: Web3 Port & Adapter**
- [ ] Create blockchain port
  ```python
  # File: src/app/domain/ports/blockchain/web3_provider.py
  
  from typing import Protocol, Dict, Any, List
  from decimal import Decimal
  
  class Web3ProviderPort(Protocol):
      """Port for Web3 blockchain interactions"""
      
      async def get_balance(
          self, 
          chain: str, 
          address: str,
          token: str = None
      ) -> Decimal:
          """Get wallet balance (native or ERC20)"""
          ...
      
      async def get_transaction(
          self, 
          chain: str, 
          tx_hash: str
      ) -> Dict[str, Any]:
          """Get transaction details"""
          ...
      
      async def estimate_gas(
          self,
          chain: str,
          transaction: Dict[str, Any]
      ) -> int:
          """Estimate gas for transaction"""
          ...
  ```

- [ ] Implement adapter
  ```python
  # File: src/app/infrastructure/adapters/blockchain/web3_adapter.py
  
  from web3 import Web3, AsyncWeb3
  from web3.providers import AsyncHTTPProvider
  from typing import Dict, Any
  from decimal import Decimal
  from app.domain.ports.blockchain.web3_provider import Web3ProviderPort
  from app.setup.config.blockchain import BlockchainConfig
  
  class Web3Adapter(Web3ProviderPort):
      """Web3.py adapter for blockchain interactions"""
      
      # ERC20 ABI (minimal)
      ERC20_ABI = [
          {
              "constant": True,
              "inputs": [{"name": "_owner", "type": "address"}],
              "name": "balanceOf",
              "outputs": [{"name": "balance", "type": "uint256"}],
              "type": "function"
          },
          {
              "constant": True,
              "inputs": [],
              "name": "decimals",
              "outputs": [{"name": "", "type": "uint8"}],
              "type": "function"
          }
      ]
      
      def __init__(self, config: BlockchainConfig):
          self.config = config
          self._w3_instances: Dict[str, AsyncWeb3] = {}
          self._initialize_connections()
      
      def _initialize_connections(self):
          """Initialize Web3 connections for each chain"""
          for chain, endpoints in self.config.rpc_endpoints.items():
              # Use Alchemy as primary, Infura as fallback
              rpc_url = endpoints.get("alchemy") or endpoints.get("infura")
              
              self._w3_instances[chain] = AsyncWeb3(
                  AsyncHTTPProvider(rpc_url)
              )
      
      def _get_w3(self, chain: str) -> AsyncWeb3:
          """Get Web3 instance for chain"""
          w3 = self._w3_instances.get(chain.lower())
          if not w3:
              raise ValueError(f"Unsupported chain: {chain}")
          return w3
      
      async def get_balance(
          self, 
          chain: str, 
          address: str,
          token: str = None
      ) -> Decimal:
          """Get wallet balance"""
          w3 = self._get_w3(chain)
          
          # Validate address
          if not w3.is_address(address):
              raise ValueError(f"Invalid address: {address}")
          
          checksum_addr = w3.to_checksum_address(address)
          
          if token is None:
              # Get native token balance (ETH, MATIC, etc.)
              balance_wei = await w3.eth.get_balance(checksum_addr)
              return Decimal(balance_wei) / Decimal(10**18)
          else:
              # Get ERC20 token balance
              token_addr = w3.to_checksum_address(token)
              contract = w3.eth.contract(
                  address=token_addr,
                  abi=self.ERC20_ABI
              )
              
              balance = await contract.functions.balanceOf(checksum_addr).call()
              decimals = await contract.functions.decimals().call()
              
              return Decimal(balance) / Decimal(10**decimals)
      
      async def get_transaction(
          self, 
          chain: str, 
          tx_hash: str
      ) -> Dict[str, Any]:
          """Get transaction details"""
          w3 = self._get_w3(chain)
          
          # Get transaction
          tx = await w3.eth.get_transaction(tx_hash)
          receipt = await w3.eth.get_transaction_receipt(tx_hash)
          
          return {
              "hash": tx_hash,
              "from": tx["from"],
              "to": tx["to"],
              "value": str(Decimal(tx["value"]) / Decimal(10**18)),
              "gas_price": str(tx["gasPrice"]),
              "gas_used": receipt["gasUsed"],
              "status": "success" if receipt["status"] == 1 else "failed",
              "block_number": tx["blockNumber"],
              "timestamp": (await w3.eth.get_block(tx["blockNumber"]))["timestamp"]
          }
      
      async def estimate_gas(
          self,
          chain: str,
          transaction: Dict[str, Any]
      ) -> int:
          """Estimate gas for transaction"""
          w3 = self._get_w3(chain)
          
          # Build transaction dict
          tx_dict = {
              "from": w3.to_checksum_address(transaction["from"]),
              "to": w3.to_checksum_address(transaction["to"]),
              "value": int(Decimal(transaction.get("value", "0")) * Decimal(10**18)),
              "data": transaction.get("data", "0x")
          }
          
          # Estimate gas
          gas_estimate = await w3.eth.estimate_gas(tx_dict)
          
          return int(gas_estimate * 1.2)  # Add 20% buffer
  ```

**Day 4: Integration with Agents**
- [ ] Add blockchain tools to agents
- [ ] Test wallet balance queries
- [ ] Test transaction lookups

**Day 5: Testing**
- [ ] Test all chains (Ethereum, Arbitrum, Polygon, Base)
- [ ] Test failover between providers
- [ ] Integration tests

#### 5.2 Success Criteria
- [ ] Get balances for native and ERC20 tokens
- [ ] Query transactions across all chains
- [ ] Estimate gas for unsigned transactions
- [ ] Automatic failover between RPC providers

---

### **Integration 6: DeFi Protocol SDKs**

**Duration:** Week 6 (5 days)  
**Priority:** HIGH  
**Dependencies:** Blockchain Infrastructure (Week 5)  
**Owner:** Backend Team

#### 6.1 Protocols to Integrate
1. **Hyperliquid** - Perpetual futures (already started)
2. **Aave V3** - Lending and borrowing

#### 6.2 Implementation Steps

**Day 1-2: Complete Hyperliquid Integration**
- [ ] Expand HyperliquidTools
- [ ] Add position monitoring
- [ ] Add liquidation price calculations

**Day 3-4: Aave V3 Integration**
- [ ] Implement Aave tools (similar to Hyperliquid)
- [ ] Health factor monitoring
- [ ] Supply/borrow APY queries

**Day 5: Integration & Testing**
- [ ] Complete end-to-end testing
- [ ] Test with real testnet data

#### 6.3 Success Criteria
- [ ] Query real Hyperliquid positions
- [ ] Get Aave user data (health factor, collateral)
- [ ] Generate unsigned transactions for both protocols

---

## Phase 3: Real-time & Polish (Weeks 7-9)

### 🎯 Goal: Real-time updates and production readiness

---

### **Integration 7: Real-time Communication**

**Duration:** Week 7 (5 days)  
**Priority:** MEDIUM  
**Dependencies:** Chat Feature (Week 3)  
**Owner:** Backend Team

#### 7.1 Implementation Options
1. **WebSocket** - Primary (bi-directional)
2. **Server-Sent Events (SSE)** - Fallback (uni-directional)

#### 7.2 Implementation Steps

**Day 1-2: WebSocket Implementation**
- [ ] Create WebSocket endpoint
  ```python
  # File: src/app/presentation/http/controllers/websocket/router.py
  
  from fastapi import APIRouter, WebSocket, WebSocketDisconnect
  from typing import Dict
  from uuid import UUID
  import json
  
  router = APIRouter()
  
  # Active connections: {user_id: {conversation_id: WebSocket}}
  active_connections: Dict[int, Dict[UUID, WebSocket]] = {}
  
  @router.websocket("/ws/chat/{conversation_id}")
  async def websocket_endpoint(
      websocket: WebSocket,
      conversation_id: UUID,
      token: str  # JWT token for auth
  ):
      """WebSocket endpoint for real-time chat updates"""
      
      # Authenticate user from token
      user_id = await authenticate_websocket(token)
      if not user_id:
          await websocket.close(code=4001, reason="Unauthorized")
          return
      
      # Accept connection
      await websocket.accept()
      
      # Register connection
      if user_id not in active_connections:
          active_connections[user_id] = {}
      active_connections[user_id][conversation_id] = websocket
      
      try:
          while True:
              # Receive messages (for typing indicators, etc.)
              data = await websocket.receive_text()
              
              # Handle client messages (ping/pong, typing, etc.)
              await handle_client_message(data, user_id, conversation_id)
              
      except WebSocketDisconnect:
          # Clean up connection
          if user_id in active_connections:
              active_connections[user_id].pop(conversation_id, None)
              if not active_connections[user_id]:
                  del active_connections[user_id]
  
  async def broadcast_message(
      user_id: int,
      conversation_id: UUID,
      message: Dict
  ):
      """Broadcast message to user's WebSocket connection"""
      
      if user_id in active_connections:
          if conversation_id in active_connections[user_id]:
              websocket = active_connections[user_id][conversation_id]
              await websocket.send_json(message)
  ```

**Day 3: Update Celery Task to Broadcast**
- [ ] Send WebSocket notification when agent responds
  ```python
  # In process_agent_response task:
  
  from app.presentation.http.controllers.websocket.router import broadcast_message
  
  # After saving agent response:
  await broadcast_message(
      user_id=user_id,
      conversation_id=UUID(conversation_id),
      message={
          "type": "agent_response",
          "message_id": str(agent_message.id_.value),
          "content": response_text,
          "timestamp": agent_message.created_at.value.isoformat()
      }
  )
  ```

**Day 4: SSE Fallback**
- [ ] Implement SSE endpoint for browsers that don't support WebSocket

**Day 5: Testing**
- [ ] Test WebSocket connections
- [ ] Test reconnection logic
- [ ] Test with multiple concurrent users

#### 7.3 Success Criteria
- [ ] Real-time message delivery via WebSocket
- [ ] Typing indicators working
- [ ] Automatic reconnection on disconnect
- [ ] SSE fallback functional

---

### **Weeks 8-9: Testing, Documentation, Polish**

**Duration:** 2 weeks  
**Priority:** CRITICAL  
**Owner:** Full Team

#### 8.1 Week 8: Comprehensive Testing

**Day 1-2: Unit Tests**
- [ ] Domain layer tests (>90% coverage)
- [ ] Application layer tests (>85% coverage)
- [ ] Infrastructure adapter tests (>80% coverage)

**Day 3-4: Integration Tests**
- [ ] End-to-end chat flow tests
- [ ] DeFi operation tests (with testnet)
- [ ] Agent processing tests
- [ ] WebSocket tests

**Day 5: Performance Tests**
- [ ] Load testing (1000+ concurrent users)
- [ ] Agent processing under load
- [ ] Database query optimization
- [ ] API response time benchmarks

#### 8.2 Week 9: Polish & Documentation

**Day 1-2: Error Handling**
- [ ] Comprehensive error handling
- [ ] User-friendly error messages
- [ ] Retry logic for all external calls
- [ ] Circuit breakers for external services

**Day 3-4: Documentation**
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Integration guide for each provider
- [ ] Deployment guide
- [ ] Troubleshooting guide

**Day 5: Security Review**
- [ ] Input validation audit
- [ ] API authentication audit
- [ ] Rate limiting configuration
- [ ] Secret management review

---

## Integration Checklist Summary

### Phase 1: Core Agent Infrastructure (Weeks 1-3)
- [ ] Agent Squad integration complete
- [ ] Agno runtime integrated with 3+ agents
- [ ] Chat controllers using real interactors
- [ ] Celery processing agent messages
- [ ] End-to-end test: User message → Agent response

### Phase 2: DeFi Operations (Weeks 4-6)
- [ ] 1inch adapter providing swap quotes
- [ ] DefiLlama providing yield data
- [ ] The Graph querying on-chain data
- [ ] Web3.py connected to all chains
- [ ] Hyperliquid SDK operational
- [ ] Aave SDK operational

### Phase 3: Real-time & Polish (Weeks 7-9)
- [ ] WebSocket real-time updates working
- [ ] Comprehensive test suite (>80% coverage)
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Security audit passed

---

## Risk Management

### High Risk Items

**Risk 1: Agent Squad/Agno Integration Complexity**
- **Probability:** MEDIUM
- **Impact:** HIGH
- **Mitigation:** 
  - Start with simple test cases
  - Have fallback to direct LLM calls
  - Allocate buffer time in Week 10

**Risk 2: Blockchain RPC Rate Limits**
- **Probability:** MEDIUM
- **Impact:** MEDIUM
- **Mitigation:**
  - Use multiple providers (Infura + Alchemy)
  - Implement aggressive caching
  - Circuit breakers for failover

**Risk 3: DeFi Provider API Changes**
- **Probability:** LOW
- **Impact:** HIGH
- **Mitigation:**
  - Version lock APIs where possible
  - Monitor provider changelog
  - Adapter pattern allows easy replacement

**Risk 4: WebSocket Scalability**
- **Probability:** MEDIUM
- **Impact:** MEDIUM
- **Mitigation:**
  - Use Redis pub/sub for distributed WS
  - SSE fallback
  - Load test early

### Medium Risk Items

**Risk 5: Test Coverage Time**
- **Probability:** HIGH
- **Impact:** MEDIUM
- **Mitigation:**
  - Integrate testing into development (not separate phase)
  - Use TDD for critical paths
  - Prioritize integration tests over unit tests

---

## Week 10: Buffer & Contingency

**Purpose:** Handle unexpected issues, technical debt, or missed items

**Allocation:**
- 3 days: Address highest priority gaps from Weeks 1-9
- 2 days: Final polish and launch preparation

---

## Success Metrics

### By End of Week 3 (Phase 1 Complete)
- [ ] Agent processes 10 test messages successfully
- [ ] Chat API returns real data (not mocks)
- [ ] Average agent response time < 5 seconds

### By End of Week 6 (Phase 2 Complete)
- [ ] Get real swap quotes from 1inch
- [ ] Query real Hyperliquid positions
- [ ] Check Aave health factors
- [ ] All blockchain interactions working

### By End of Week 9 (Phase 3 Complete)
- [ ] Real-time messages delivered < 500ms
- [ ] Test coverage > 80%
- [ ] API response times < 200ms (p95)
- [ ] Load test: 1000 concurrent users
- [ ] Zero critical security issues

### MVP Launch Ready (Week 10)
- [ ] All integration tests passing
- [ ] Documentation complete
- [ ] Security audit passed
- [ ] Performance benchmarks met
- [ ] Monitoring and alerts configured

---

## Daily Standup Template

**What was completed yesterday?**
- Integration milestones
- Blockers resolved

**What will be completed today?**
- Specific tasks from plan
- Expected outcomes

**Any blockers?**
- Technical issues
- Missing dependencies
- Need help from other developers

---

## Coordination with Privy Developer

**Critical Handoff Points:**

1. **Week 1-2:** Share user authentication contract
   - Your team: Implement `get_current_user_id()` helper
   - Privy developer: Provide JWT validation middleware

2. **Week 3:** Integration point for mobile users
   - Chat endpoints must support both admin JWT (your existing) and Privy JWT
   - User table should distinguish user types

3. **Week 5:** Wallet address integration
   - Privy provides MPC wallet addresses
   - Your blockchain adapter queries these addresses
   - Coordinate on address format and retrieval

4. **Week 7:** Test end-to-end mobile flow
   - Privy auth → Chat → DeFi operations
   - Joint testing session

---

## Document Metadata

- **Created:** December 1, 2025
- **Last Updated:** December 1, 2025
- **Version:** 1.0
- **Status:** Active
- **Next Review:** End of Week 3 (adjust timeline if needed)
