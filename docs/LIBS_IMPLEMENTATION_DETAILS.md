# 🔧 Libraries Implementation Details - Technical Deep Dive

**Date:** December 2, 2025  
**Audience:** Senior Developers  
**Purpose:** Detailed technical implementation guide

---

## 📋 **EXECUTIVE SUMMARY FOR DEVELOPERS**

This document provides **step-by-step implementation details** for integrating the 3 critical libraries into Anvil Backend. Each section includes:
- ✅ Current state analysis
- ❌ Gap identification  
- 📝 Exact code changes needed
- 🧪 Testing strategy
- ⚡ Performance considerations

---

## 1️⃣ **AGENT SQUAD INTEGRATION - DETAILED IMPLEMENTATION**

### **🎯 Current State Analysis**

```python
# WHAT EXISTS TODAY:
src/app/infrastructure/adapters/ai/agent_gateway_impl.py
└── AgentGatewayImpl class
    ├── ✅ Intent classification (keyword + LLM-based)
    ├── ✅ Agent registry system
    ├── ✅ Context management
    ├── ✅ Fallback response generation
    └── ❌ NO actual Agent Squad library integration

src/app/setup/config/agent_squad.py
└── AgentSquadConfig
    ├── ✅ Configuration dataclass
    ├── ✅ Feature flags
    └── ✅ Performance settings

src/app/domain/ports/ai/agent_gateway.py
└── AgentGateway Protocol
    └── ✅ Well-defined interface
```

### **❌ The Critical Gap**

Your `AgentGatewayImpl` is a **hand-rolled orchestrator** - it works, but lacks:
- ❌ Advanced intent classification (it's doing keyword matching + basic LLM)
- ❌ Context preservation across agent switches
- ❌ Supervisor agent patterns
- ❌ Multi-agent collaboration

**Agent Squad library location:** `libs/agent-squad/python/src/agent_squad/`

### **📝 Step-by-Step Integration**

#### **Step 1: Install Agent Squad (5 minutes)**

```bash
# Method 1: Install from local submodule
cd /home/ubuntu/anvil_backend
pip install -e libs/agent-squad/python/

# Method 2: Install from PyPI
pip install agent-squad

# Verify installation
python3 -c "from agent_squad import MultiAgentOrchestrator; print('✅ Agent Squad installed')"
```

#### **Step 2: Create AgentSquadGateway Adapter (2 hours)**

**File:** `src/app/infrastructure/adapters/ai/agent_squad_gateway.py`

```python
"""
Agent Squad Gateway - Production-grade multi-agent orchestration.

Replaces AgentGatewayImpl with Agent Squad library for:
- Advanced intent classification
- Context preservation
- Supervisor agent patterns
- Multi-agent collaboration
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import asyncio

# Agent Squad imports
from agent_squad import MultiAgentOrchestrator
from agent_squad.agents import BedrockLLMAgent, OpenAIAgent
from agent_squad.types import ConversationMessage, ParticipantRole
from agent_squad.classifiers import BedrockClassifier, AnthropicClassifier

# Your existing imports
from app.domain.ports.ai.agent_gateway import AgentGateway
from app.domain.enums.agent_type import AgentType
from app.infrastructure.adapters.ai.squad_storage import AnvilSquadStorage
from app.setup.config.agent_squad import AgentSquadConfig


class AgentSquadGateway(AgentGateway):
    """
    Production Agent Squad integration.
    
    Features:
    - Intelligent intent classification via Agent Squad
    - Multi-agent orchestration
    - Context preservation
    - Supervisor patterns
    """
    
    def __init__(
        self,
        storage: AnvilSquadStorage,
        config: AgentSquadConfig,
    ):
        """
        Initialize Agent Squad Gateway.
        
        Args:
            storage: Anvil storage adapter for Agent Squad
            config: Agent Squad configuration
        """
        self.storage = storage
        self.config = config
        
        # Create orchestrator
        self.orchestrator = MultiAgentOrchestrator(
            storage=storage,
            config={
                "LOG_AGENT_CHAT": config.log_agent_selection,
                "LOG_CLASSIFIER_CHAT": config.log_intent_classification,
                "LOG_CLASSIFIER_RAW_OUTPUT": config.debug_mode,
                "LOG_CLASSIFIER_OUTPUT": config.debug_mode,
                "LOG_EXECUTION_TIMES": config.debug_mode,
                "MAX_RETRIES": config.max_retries,
                "USE_DEFAULT_AGENT_IF_NONE_IDENTIFIED": True,
            }
        )
        
        # Initialize classifier based on config
        self._setup_classifier()
        
        # Register specialized agents
        self._register_agents()
    
    def _setup_classifier(self):
        """Set up the intent classifier."""
        # Use Anthropic Claude for classification (best performance)
        # You can also use BedrockClassifier or custom classifier
        self.orchestrator.classifier = AnthropicClassifier()
    
    def _register_agents(self):
        """Register all specialized DeFi agents."""
        
        # 1. Trading Agent (Swaps, Perps)
        trading_agent = OpenAIAgent(
            name="Trading Agent",
            description="""Specialized in DeFi trading operations including:
            - Token swaps on DEXes (Uniswap, Curve, 1inch)
            - Opening perpetual positions
            - Closing positions
            - Executing market orders
            Always explain risks and ask for confirmation before trades.""",
            model=self.config.default_model,
        )
        self.orchestrator.add_agent(trading_agent)
        
        # 2. Lending Agent (Supply, Borrow)
        lending_agent = OpenAIAgent(
            name="Lending Agent",
            description="""Specialized in DeFi lending and borrowing:
            - Supply/lend tokens (Aave, Compound)
            - Borrow against collateral
            - Manage health factors
            - Calculate optimal collateral ratios
            Always explain liquidation risks.""",
            model=self.config.default_model,
        )
        self.orchestrator.add_agent(lending_agent)
        
        # 3. Portfolio Agent (View, Analyze)
        portfolio_agent = OpenAIAgent(
            name="Portfolio Agent",
            description="""Specialized in portfolio management:
            - View token balances and positions
            - Analyze portfolio composition
            - Track profit/loss
            - Provide diversification insights
            Display information clearly and concisely.""",
            model=self.config.default_model,
        )
        self.orchestrator.add_agent(portfolio_agent)
        
        # 4. Market Data Agent (Prices, Rates, Info)
        market_agent = OpenAIAgent(
            name="Market Agent",
            description="""Specialized in DeFi market data:
            - Real-time token prices
            - APY/APR rates
            - TVL and liquidity data
            - Funding rates for perps
            Provide accurate, up-to-date information.""",
            model=self.config.default_model,
        )
        self.orchestrator.add_agent(market_agent)
        
        # 5. Risk Agent (Analysis, Warnings)
        risk_agent = OpenAIAgent(
            name="Risk Agent",
            description="""Specialized in risk analysis:
            - Assess position risks
            - Calculate liquidation prices
            - Evaluate protocol risks
            - Warn about high-risk operations
            Always be thorough and cautious.""",
            model=self.config.default_model,
        )
        self.orchestrator.add_agent(risk_agent)
        
        # 6. Research Agent (General Questions, Education)
        research_agent = OpenAIAgent(
            name="Research Agent",
            description="""Specialized in DeFi education and research:
            - Explain DeFi concepts
            - Protocol analysis
            - Answer general questions
            - Provide educational content
            Make complex topics simple and clear.""",
            model=self.config.fallback_model,  # Use cheaper model for education
        )
        self.orchestrator.add_agent(research_agent)
        
        # Set research agent as default fallback
        self.orchestrator.set_default_agent(research_agent)
    
    async def process_message(
        self,
        user_id: UUID,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        suggested_model: Optional[str] = None,
        suggested_agent: Optional[str] = None,
    ) -> str:
        """
        Process message through Agent Squad orchestrator.
        
        Args:
            user_id: User identifier
            session_id: Session/conversation identifier  
            message: User message content
            context: Optional context dictionary
            suggested_model: Optional model hint (ignored - Agent Squad handles)
            suggested_agent: Optional agent hint for routing
        
        Returns:
            Agent response text
        """
        try:
            # Convert our user_id to string for Agent Squad
            user_id_str = str(user_id)
            
            # Route through Agent Squad
            response = await self.orchestrator.route_request(
                user_input=message,
                user_id=user_id_str,
                session_id=session_id,
            )
            
            # Extract text response
            # Agent Squad returns AgentResponse object
            if hasattr(response, 'output'):
                return response.output
            elif isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception as e:
            # Log error
            print(f"Agent Squad error: {str(e)}")
            
            # Fallback to friendly error
            return (
                "I apologize, but I encountered an error processing your request. "
                "Please try rephrasing your message or contact support if the issue persists."
            )
```

#### **Step 3: Update Dependency Injection (30 minutes)**

**File:** `src/app/setup/ioc/infrastructure.py`

```python
# Add to imports
from app.infrastructure.adapters.ai.agent_squad_gateway import AgentSquadGateway

# Update provider method
class InfrastructureProvider(Provider):
    
    @provide(scope=Scope.REQUEST)
    async def get_agent_gateway(
        self,
        storage: AnvilSquadStorage,
        config: AgentSquadConfig,
    ) -> AgentGateway:
        """
        Provide Agent Squad Gateway.
        
        NEW: Uses Agent Squad library for production-grade orchestration.
        """
        return AgentSquadGateway(
            storage=storage,
            config=config,
        )
```

#### **Step 4: Update Storage Adapter (1 hour)**

Agent Squad needs a storage adapter. Update your existing `AnvilSquadStorage`:

**File:** `src/app/infrastructure/adapters/ai/squad_storage.py`

```python
"""
Anvil Storage Adapter for Agent Squad.

Bridges Agent Squad's storage interface with our PostgreSQL database.
"""

from typing import List, Dict, Any, Optional
from agent_squad.storage import ChatStorage
from agent_squad.types import ConversationMessage, ParticipantRole

from app.domain.ports.conversation_repository import ConversationRepository


class AnvilSquadStorage(ChatStorage):
    """
    Storage adapter that connects Agent Squad to Anvil's database.
    
    Agent Squad expects:
    - save_chat_message(user_id, session_id, agent_id, new_message, max_history_size)
    - fetch_chat(user_id, session_id, max_history_size)
    - fetch_all_chats(user_id)
    """
    
    def __init__(self, conversation_repo: ConversationRepository):
        """
        Initialize storage adapter.
        
        Args:
            conversation_repo: Anvil conversation repository
        """
        self.conversation_repo = conversation_repo
    
    async def save_chat_message(
        self,
        user_id: str,
        session_id: str,
        agent_id: str,
        new_message: ConversationMessage,
        max_history_size: int = 100
    ) -> List[ConversationMessage]:
        """
        Save message to Anvil database.
        
        Args:
            user_id: User identifier
            session_id: Session/conversation identifier
            agent_id: Agent that generated the message
            new_message: Message to save
            max_history_size: Maximum messages to keep
        
        Returns:
            Updated conversation history
        """
        # Convert Agent Squad message to Anvil format
        await self.conversation_repo.save_message(
            session_id=session_id,
            role=new_message.role,  # USER, ASSISTANT, or SYSTEM
            content=new_message.content[0]['text'] if new_message.content else '',
            agent_type=agent_id,
        )
        
        # Return updated history
        return await self.fetch_chat(user_id, session_id, max_history_size)
    
    async def fetch_chat(
        self,
        user_id: str,
        session_id: str,
        max_history_size: int = 100
    ) -> List[ConversationMessage]:
        """
        Fetch conversation history from Anvil database.
        
        Args:
            user_id: User identifier
            session_id: Session/conversation identifier
            max_history_size: Maximum messages to return
        
        Returns:
            List of conversation messages
        """
        # Get messages from database
        messages = await self.conversation_repo.get_messages(
            session_id=session_id,
            limit=max_history_size
        )
        
        # Convert to Agent Squad format
        squad_messages = []
        for msg in messages:
            squad_msg = ConversationMessage(
                role=self._convert_role(msg.role),
                content=[{"text": msg.content}]
            )
            squad_messages.append(squad_msg)
        
        return squad_messages
    
    async def fetch_all_chats(
        self,
        user_id: str
    ) -> Dict[str, List[ConversationMessage]]:
        """
        Fetch all conversations for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary mapping session_id to messages
        """
        # Get all user conversations
        conversations = await self.conversation_repo.get_user_conversations(
            user_id=user_id
        )
        
        # Build response dictionary
        all_chats = {}
        for conv in conversations:
            messages = await self.fetch_chat(user_id, conv.id, max_history_size=100)
            all_chats[conv.id] = messages
        
        return all_chats
    
    def _convert_role(self, anvil_role: str) -> ParticipantRole:
        """Convert Anvil role to Agent Squad role."""
        role_map = {
            "user": ParticipantRole.USER,
            "agent": ParticipantRole.ASSISTANT,
            "system": ParticipantRole.SYSTEM,
        }
        return role_map.get(anvil_role.lower(), ParticipantRole.USER)
```

#### **Step 5: Testing Strategy (2 hours)**

Create comprehensive tests:

**File:** `tests/integration/agent_squad/test_agent_squad_gateway.py`

```python
"""
Integration tests for Agent Squad Gateway.

Tests the complete Agent Squad integration including:
- Intent classification
- Agent routing
- Context preservation
- Multi-agent collaboration
"""

import pytest
from uuid import uuid4

from app.infrastructure.adapters.ai.agent_squad_gateway import AgentSquadGateway
from app.infrastructure.adapters.ai.squad_storage import AnvilSquadStorage
from app.setup.config.agent_squad import AgentSquadConfig


@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentSquadGateway:
    """Integration tests for Agent Squad integration."""
    
    async def test_trading_intent_classification(
        self,
        agent_squad_gateway: AgentSquadGateway,
    ):
        """Test message is routed to Trading Agent."""
        # Arrange
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        message = "I want to swap 100 USDC for ETH on Uniswap"
        
        # Act
        response = await agent_squad_gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message=message,
        )
        
        # Assert
        assert response is not None
        assert len(response) > 0
        # Response should mention swap/trade concepts
        assert any(word in response.lower() for word in ['swap', 'trade', 'uniswap'])
    
    async def test_context_preservation(
        self,
        agent_squad_gateway: AgentSquadGateway,
    ):
        """Test context is preserved across messages."""
        # Arrange
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        
        # Act - First message
        response1 = await agent_squad_gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message="What is Aave?",
        )
        
        # Act - Follow-up message (should understand "it" refers to Aave)
        response2 = await agent_squad_gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message="What are the risks of using it?",
        )
        
        # Assert
        assert "aave" in response2.lower()
    
    async def test_agent_switching(
        self,
        agent_squad_gateway: AgentSquadGateway,
    ):
        """Test orchestrator switches agents based on intent."""
        # Arrange
        user_id = uuid4()
        session_id = f"test_{uuid4()}"
        
        # Act - Portfolio question
        response1 = await agent_squad_gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message="Show me my portfolio",
        )
        
        # Act - Switch to risk question
        response2 = await agent_squad_gateway.process_message(
            user_id=user_id,
            session_id=session_id,
            message="What are my liquidation risks?",
        )
        
        # Assert - Both should have valid responses
        assert len(response1) > 0
        assert len(response2) > 0
```

#### **Step 6: Performance Benchmarking (1 hour)**

Create performance tests to ensure Agent Squad meets your requirements:

**File:** `tests/performance/test_agent_squad_performance.py`

```python
"""
Performance benchmarks for Agent Squad.

Target metrics:
- Intent classification: < 100ms
- Agent routing: < 50ms  
- Total response time: < 2s
"""

import pytest
import time
from uuid import uuid4


@pytest.mark.performance
@pytest.mark.asyncio
class TestAgentSquadPerformance:
    """Performance tests for Agent Squad."""
    
    async def test_intent_classification_speed(
        self,
        agent_squad_gateway,
    ):
        """Test intent classification completes in < 100ms."""
        # Arrange
        user_id = uuid4()
        session_id = f"perf_{uuid4()}"
        messages = [
            "Swap 100 USDC for ETH",
            "Show my portfolio",
            "What is DeFi?",
            "Calculate my risk",
        ]
        
        # Act & Assert
        for message in messages:
            start = time.time()
            await agent_squad_gateway.process_message(
                user_id=user_id,
                session_id=session_id,
                message=message,
            )
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            # Assert: Total time should be < 2000ms (including LLM call)
            assert elapsed < 2000, f"Message took {elapsed}ms (target: <2000ms)"
    
    async def test_concurrent_users(
        self,
        agent_squad_gateway,
    ):
        """Test system handles 100 concurrent users."""
        import asyncio
        
        # Arrange
        async def user_session(user_num):
            user_id = uuid4()
            session_id = f"concurrent_{user_num}"
            return await agent_squad_gateway.process_message(
                user_id=user_id,
                session_id=session_id,
                message="What is the price of ETH?",
            )
        
        # Act
        start = time.time()
        results = await asyncio.gather(*[user_session(i) for i in range(100)])
        elapsed = time.time() - start
        
        # Assert
        assert len(results) == 100
        assert all(len(r) > 0 for r in results)
        assert elapsed < 30  # 100 requests in < 30 seconds
```

---

## 2️⃣ **AGNO MCP SERVERS - DETAILED IMPLEMENTATION**

### **🎯 Current State Analysis**

```python
# WHAT EXISTS TODAY:
src/app/infrastructure/agno/base_agent.py (406 lines)
└── DeFiAgentBase class
    ├── ✅ Agno Agent integration
    ├── ✅ MCP tool loading framework
    ├── ✅ Session management
    ├── ✅ Streaming support
    └── ⚠️  Expects MCP servers to exist (but they don't yet)

# YOUR INFRASTRUCTURE IS READY!
# Just need to create the MCP servers for external APIs
```

### **📝 Step-by-Step: Create MCP Servers**

#### **Step 1: MCP Server Base Infrastructure (2 hours)**

**File:** `src/app/infrastructure/mcp/base_server.py`

```python
"""
Base MCP Server for Anvil.

Provides foundation for all MCP tool servers.
Implements Model Context Protocol for tool discovery and execution.
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


@dataclass
class MCPTool:
    """MCP Tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable


class MCPServer:
    """
    Base MCP Server implementation.
    
    Provides:
    - Tool registration
    - Discovery endpoint
    - Execution endpoint
    - Error handling
    """
    
    def __init__(self, server_name: str, description: str):
        """
        Initialize MCP server.
        
        Args:
            server_name: Unique server identifier (e.g., "1inch", "defillama")
            description: Server description
        """
        self.server_name = server_name
        self.description = description
        self.tools: Dict[str, MCPTool] = {}
        self.app = FastAPI(title=f"{server_name} MCP Server")
        
        # Register MCP endpoints
        self._setup_routes()
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
    ):
        """
        Register a tool with this MCP server.
        
        Args:
            name: Tool name
            description: Tool description
            parameters: JSON Schema for parameters
            handler: Async function that executes the tool
        """
        tool = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )
        self.tools[name] = tool
    
    def _setup_routes(self):
        """Set up FastAPI routes for MCP protocol."""
        
        @self.app.get("/tools")
        async def list_tools():
            """List all available tools (MCP discovery)."""
            return {
                "server": self.server_name,
                "description": self.description,
                "tools": [
                    {
                        "name": tool.name,
                        "qualified_name": f"{self.server_name}_{tool.name}",
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                    for tool in self.tools.values()
                ]
            }
        
        @self.app.post("/execute/{tool_name}")
        async def execute_tool(tool_name: str, params: Dict[str, Any]):
            """Execute a specific tool (MCP execution)."""
            if tool_name not in self.tools:
                raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
            
            tool = self.tools[tool_name]
            
            try:
                result = await tool.handler(**params)
                return {
                    "success": True,
                    "result": result,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                }
```

#### **Step 2: 1inch DEX MCP Server (3 hours)**

**File:** `src/app/infrastructure/mcp/servers/oneinch_mcp.py`

```python
"""
1inch DEX MCP Server.

Provides MCP tools for:
- Getting swap quotes
- Finding best swap routes
- Checking liquidity
"""

from typing import Dict, Any
import httpx

from app.infrastructure.mcp.base_server import MCPServer
from app.infrastructure.external_data.oneinch.client import OneInchClient


class OneInchMCPServer(MCPServer):
    """MCP Server for 1inch DEX aggregator."""
    
    def __init__(self, oneinch_client: OneInchClient):
        """
        Initialize 1inch MCP server.
        
        Args:
            oneinch_client: 1inch API client
        """
        super().__init__(
            server_name="1inch",
            description="1inch DEX aggregator for best swap routes and prices"
        )
        self.client = oneinch_client
        
        # Register tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all 1inch tools."""
        
        # Tool 1: Get swap quote
        self.register_tool(
            name="get_swap_quote",
            description="Get best swap quote from 1inch aggregator",
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID (1=Ethereum, 137=Polygon, etc.)",
                    },
                    "from_token": {
                        "type": "string",
                        "description": "Source token contract address",
                    },
                    "to_token": {
                        "type": "string",
                        "description": "Destination token contract address",
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount to swap (in wei)",
                    },
                },
                "required": ["chain_id", "from_token", "to_token", "amount"],
            },
            handler=self._get_swap_quote,
        )
        
        # Tool 2: Get liquidity sources
        self.register_tool(
            name="get_liquidity_sources",
            description="Get available liquidity sources (Uniswap, Curve, etc.)",
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID",
                    },
                },
                "required": ["chain_id"],
            },
            handler=self._get_liquidity_sources,
        )
    
    async def _get_swap_quote(
        self,
        chain_id: int,
        from_token: str,
        to_token: str,
        amount: str,
    ) -> Dict[str, Any]:
        """Get swap quote from 1inch."""
        try:
            quote = await self.client.get_quote(
                chain_id=chain_id,
                src=from_token,
                dst=to_token,
                amount=amount,
            )
            return {
                "estimated_output": quote["toAmount"],
                "estimated_gas": quote["estimatedGas"],
                "protocols": quote["protocols"],
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_liquidity_sources(
        self,
        chain_id: int,
    ) -> Dict[str, Any]:
        """Get available liquidity sources."""
        try:
            sources = await self.client.get_liquidity_sources(chain_id)
            return {"sources": sources}
        except Exception as e:
            return {"error": str(e)}
```

**Run the server:**

```python
# src/app/infrastructure/mcp/servers/__main__.py
import uvicorn
from app.infrastructure.mcp.servers.oneinch_mcp import OneInchMCPServer
from app.infrastructure.external_data.oneinch.client import OneInchClient

# Create server
client = OneInchClient()
server = OneInchMCPServer(client)

# Run
if __name__ == "__main__":
    uvicorn.run(server.app, host="0.0.0.0", port=8081)
```

#### **Step 3: DeFiLlama, The Graph, CoinGecko MCP Servers (6 hours)**

Create similar MCP servers for:
- `src/app/infrastructure/mcp/servers/defillama_mcp.py`
- `src/app/infrastructure/mcp/servers/thegraph_mcp.py`
- `src/app/infrastructure/mcp/servers/coingecko_mcp.py`

Follow the same pattern as 1inch server.

---

## 3️⃣ **GRAPHRAG POLISH - MINOR ENHANCEMENTS**

### **🎯 Current State: 90% Complete (EXCELLENT!)**

Your GraphRAG implementation is **world-class**. Here are optional enhancements:

#### **Enhancement 1: LLM-based Entity Extraction (4 hours)**

**File:** `src/app/application/graph/entity_extraction.py`

```python
"""
LLM-based entity extraction for GraphRAG.

Extracts entities and relationships from protocol documents
using GPT-4 for automatic knowledge graph population.
"""

from typing import List, Tuple
from app.domain.ports.ai.llm_gateway import LLMGateway
from app.domain.ports.graph.graph_repository import GraphRepository


class EntityExtractor:
    """Extract entities from text using LLM."""
    
    def __init__(
        self,
        llm_gateway: LLMGateway,
        graph_repo: GraphRepository,
    ):
        self.llm = llm_gateway
        self.graph = graph_repo
    
    async def extract_from_document(
        self,
        document_text: str,
        document_source: str,
    ) -> List[Tuple[str, str, str]]:
        """
        Extract (subject, predicate, object) triples from document.
        
        Args:
            document_text: Document content
            document_source: Source URL/reference
        
        Returns:
            List of (subject, predicate, object) triples
        """
        prompt = f"""Extract entities and relationships from this DeFi protocol document.

Document:
{document_text[:2000]}  # Truncate for token limits

Return JSON with format:
{{
  "entities": [
    {{"type": "Protocol", "name": "Aave", "properties": {{"tvl": "5B"}}}},
    {{"type": "Token", "name": "USDT", "properties": {{}}}}
  ],
  "relationships": [
    {{"subject": "Aave", "predicate": "USES_COLLATERAL", "object": "USDT"}},
    {{"subject": "Aave", "predicate": "DEPLOYED_ON", "object": "Ethereum"}}
  ]
}}

Focus on:
- Protocols and their dependencies
- Tokens used as collateral
- Governance structures
- Risk factors"""
        
        response = await self.llm.generate(
            prompt=prompt,
            system_message="You are a DeFi knowledge graph expert. Extract entities and relationships.",
            max_tokens=1000,
            temperature=0.0,
        )
        
        # Parse response and create graph nodes/edges
        # ... (implementation details)
        
        return triples
```

---

## ⚡ **PERFORMANCE TARGETS**

```
AGENT SQUAD:
├── Intent classification: < 100ms
├── Agent routing: < 50ms
├── Context loading: < 50ms
└── Total overhead: < 200ms

AGNO + MCP:
├── Tool discovery: < 50ms (cached)
├── Tool execution: < 500ms (external API)
├── Agent runtime: < 50ms
└── Total: < 600ms

GRAPHRAG:
├── Node query: < 50ms
├── Path finding: < 100ms
├── Complex traversal: < 200ms
└── Cached queries: < 10ms
```

---

## 🧪 **TESTING CHECKLIST**

```
AGENT SQUAD:
[ ] Intent classification accuracy > 90%
[ ] Context preserved across 20+ messages
[ ] Agent switching works smoothly
[ ] Fallback agent handles unknown intents
[ ] 100 concurrent users supported

AGNO MCP:
[ ] All 4 MCP servers running
[ ] Tools discoverable via /tools endpoint
[ ] Tool execution < 500ms
[ ] Error handling works
[ ] Retry logic functional

GRAPHRAG:
[ ] All CRUD operations work
[ ] Path finding algorithms accurate
[ ] Cypher queries optimized
[ ] Caching reduces latency
[ ] Real-time updates via WebSocket
```

---

## 🎯 **SUCCESS CRITERIA**

```
PHASE 1 (Agent Squad) - Week 2:
✅ 6 specialized agents registered
✅ Intent classification > 90% accurate
✅ Context preserved across conversations
✅ Response time < 2s
✅ Test coverage > 90%

PHASE 2 (MCP Servers) - Week 4:
✅ 4 MCP servers operational
✅ Tools accessible via Agno agents
✅ External API calls < 500ms
✅ Error rate < 0.1%
✅ Integration tests passing

PHASE 3 (Polish) - Week 6:
✅ Entity extraction working
✅ Graph visualization endpoints
✅ Overall system latency < 1s
✅ Ready for production
```

---

## 📚 **REFERENCES**

**Agent Squad:**
- Library: `libs/agent-squad/python/src/agent_squad/`
- Docs: `libs/agent-squad/README.md`
- Examples: `libs/agent-squad/examples/`

**Agno:**
- Base class: `src/app/infrastructure/agno/base_agent.py`
- Config: `src/app/setup/config/agno.py`

**GraphRAG:**
- Repository: `src/app/infrastructure/persistence_age/graph_repository_age.py`
- Service: `src/app/domain/services/graph/graph_service.py`

---

**Ready to start coding?** Let me know which section you'd like to dive deeper into! 🚀💪
