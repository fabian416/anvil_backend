# Chat Message Sources Attribution - Implementation Specification

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Specification Ready for Implementation  
**Methodology**: CTO Engineering Framework

---

## Executive Summary

This specification defines the implementation of **source attribution** for chat messages, enabling the frontend to display knowledge sources, citations, and data provenance for each agent response.

**Key Requirements**:
- Track all data sources used by each agent
- Provide structured source information (URLs, timestamps, citations)
- Support multiple source types (APIs, databases, external services)
- Enable frontend to display source attribution UI
- Maintain backward compatibility with existing messages

**Benefits**:
- **Transparency**: Users see where information comes from
- **Trust**: Citations and data sources build user confidence
- **Compliance**: Source tracking for regulatory requirements
- **Debugging**: Easier to trace data issues
- **Analytics**: Understand which sources are most valuable

---

## Problem Decomposition (CTO Methodology)

### Phase 1: Problem Analysis

#### Assumption Questioning

**Q1**: What is the actual requirement?
- **A**: Frontend needs to display sources/citations for agent responses
- **A**: Users want to know where data comes from (transparency)
- **A**: Compliance may require source tracking

**Q2**: What unverified assumptions exist?
- ❓ Do we need to track sources for ALL messages or just agent responses?
- ❓ Should sources be stored in database or computed on-the-fly?
- ❓ Do we need full citation details or just source names?

**Q3**: What are the constraints?
- **Hard**: Must not break existing API contracts
- **Hard**: Must support all 18 agents + handlers
- **Soft**: Should be performant (no significant latency increase)
- **Soft**: Should be storage-efficient

#### Root Cause Identification

**Current State**:
- `AgentResponse` has `tools_used: list[str]` (e.g., `["openai_api", "coingecko_api"]`)
- `Message.metadata` is a generic dict (can store anything)
- No structured source information
- No citation URLs or timestamps
- Frontend cannot display source attribution

**Root Cause**:
- Source tracking was not part of initial design
- `tools_used` is too generic (just names, no details)
- No standardized format for source information

#### Solution Space Mapping

**System Invariants**:
- Message entity structure (id, conversation_id, role, content, agent_type, metadata)
- AgentResponse structure (content, agent_type, tools_used, metadata)
- API response schemas (MessageResponse, UnifiedChatResponse)

**Design Degrees of Freedom**:
- Where to store sources (metadata field vs separate table)
- Source data structure (simple list vs rich objects)
- When to collect sources (during execution vs post-processing)

**Hard Constraints**:
- Must not break existing API contracts
- Must support all agents and handlers
- Must be queryable by frontend

**Soft Constraints**:
- Performance (minimal latency impact)
- Storage (efficient data structure)
- Maintainability (easy to extend)

---

## Solution Generation (CTO Methodology)

### Phase 2: Solution Options

#### Solution X: Rich Source Objects in Metadata ⚖️

**Technical Benefits**:
- Structured data with full details (URLs, timestamps, citations)
- Easy to extend with new source types
- Can be stored in existing `metadata` field (JSONB)

**Implementation Cost**: Medium
- Update `AgentResponse` to include `sources: list[SourceInfo]`
- Update all agents to collect source information
- Update response schemas

**Risk Assessment**: Low
- Backward compatible (metadata is optional)
- No database schema changes needed
- Can be implemented incrementally

#### Solution Y: Separate Sources Table ⚖️

**Technical Benefits**:
- Normalized data structure
- Queryable sources independently
- Better for analytics

**Implementation Cost**: High
- Database migration (new table)
- Foreign key relationships
- More complex queries

**Risk Assessment**: Medium
- Requires database changes
- More complex to implement
- May impact performance

#### Solution Z: Hybrid Approach (Metadata + Optional Table) ⚖️ ✅ **SELECTED**

**Technical Benefits**:
- Rich source objects in metadata (immediate)
- Optional separate table for analytics (future)
- Best of both worlds

**Implementation Cost**: Medium-High
- Start with metadata approach
- Add table later if needed for analytics

**Risk Assessment**: Low
- Incremental implementation
- Can start simple, add complexity later

---

## Detailed Specification

### 1. Data Model

#### SourceInfo Value Object

**Location**: `src/app/domain/value_objects/chat/source_info.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class SourceType(str, Enum):
    """Type of data source."""
    API = "api"                    # External API (CoinGecko, 1inch, etc.)
    DATABASE = "database"          # Internal database query
    MCP_SERVER = "mcp_server"     # MCP server tool
    RSS_FEED = "rss_feed"          # RSS news feed
    SOCIAL_MEDIA = "social_media"  # Twitter, Reddit, Discord
    BLOCKCHAIN = "blockchain"      # On-chain data (RPC calls)
    LLM = "llm"                    # LLM-generated content
    AGGREGATED = "aggregated"      # Aggregated from multiple sources

@dataclass
class SourceInfo:
    """
    Information about a data source used in agent response.
    
    Provides structured source attribution for frontend display.
    """
    # Source identification
    source_type: SourceType
    source_name: str              # e.g., "CoinGecko", "1inch", "Aave V3"
    source_id: Optional[str] = None  # API endpoint, contract address, etc.
    
    # Citation information
    url: Optional[str] = None      # Direct link to source (if available)
    citation_text: Optional[str] = None  # Human-readable citation
    
    # Data freshness
    fetched_at: Optional[datetime] = None  # When data was fetched
    data_age_seconds: Optional[int] = None  # Age of data in seconds
    
    # Source metadata
    provider: Optional[str] = None  # Provider name (e.g., "CoinGecko API")
    endpoint: Optional[str] = None  # API endpoint used
    query_params: Optional[dict] = None  # Query parameters (sanitized)
    
    # Relevance
    relevance_score: Optional[float] = None  # 0.0-1.0, how relevant to response
    data_points_used: Optional[int] = None  # Number of data points from this source
    
    # Additional context
    metadata: Optional[dict] = None  # Additional source-specific data
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "source_type": self.source_type.value,
            "source_name": self.source_name,
            "source_id": self.source_id,
            "url": self.url,
            "citation_text": self.citation_text,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "data_age_seconds": self.data_age_seconds,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "query_params": self.query_params,
            "relevance_score": self.relevance_score,
            "data_points_used": self.data_points_used,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SourceInfo":
        """Deserialize from dictionary."""
        fetched_at = None
        if data.get("fetched_at"):
            if isinstance(data["fetched_at"], str):
                fetched_at = datetime.fromisoformat(data["fetched_at"])
            else:
                fetched_at = data["fetched_at"]
        
        return cls(
            source_type=SourceType(data.get("source_type", "api")),
            source_name=data["source_name"],
            source_id=data.get("source_id"),
            url=data.get("url"),
            citation_text=data.get("citation_text"),
            fetched_at=fetched_at,
            data_age_seconds=data.get("data_age_seconds"),
            provider=data.get("provider"),
            endpoint=data.get("endpoint"),
            query_params=data.get("query_params"),
            relevance_score=data.get("relevance_score"),
            data_points_used=data.get("data_points_used"),
            metadata=data.get("metadata"),
        )
```

#### Updated AgentResponse

**Location**: `src/app/domain/ports/agent_squad/agent_gateway.py`

```python
@dataclass
class AgentResponse:
    """
    Response from agent execution.
    
    Contains:
    - content: Agent response text
    - agent_type: Which agent generated the response
    - tools_used: List of tools/APIs used (legacy, for backward compatibility)
    - sources: List of detailed source information (NEW)
    - metadata: Additional metadata (tokens, latency, etc.)
    """
    content: str
    agent_type: AgentType
    tools_used: list[str]  # Legacy field, kept for backward compatibility
    sources: list[SourceInfo] = field(default_factory=list)  # NEW: Detailed sources
    metadata: dict = field(default_factory=dict)
    
    @property
    def tokens_used(self) -> int | None:
        """Get tokens used (if available)."""
        return self.metadata.get("tokens_used")
    
    @property
    def latency_ms(self) -> int | None:
        """Get latency in milliseconds (if available)."""
        return self.metadata.get("latency_ms")
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "content": self.content,
            "agent_type": self.agent_type.value,
            "tools_used": self.tools_used,
            "sources": [s.to_dict() for s in self.sources],  # NEW
            "metadata": self.metadata,
        }
```

---

### 2. Source Mapping by Agent

#### Hunter AI Agent

**Data Sources**:
1. **CoinGecko API**
   - Type: `SourceType.API`
   - Name: "CoinGecko"
   - Endpoints: `/simple/price`, `/coins/{id}/market_chart`
   - Data: Real-time prices, market charts, market cap, volume
   - URL: `https://www.coingecko.com/en/coins/{id}`

2. **Twitter Sentiment** (if enabled)
   - Type: `SourceType.SOCIAL_MEDIA`
   - Name: "Twitter"
   - Data: Sentiment scores, tweet counts
   - Note: Currently simulated (OAuth2 required for real data)

3. **Reddit Sentiment** (if enabled)
   - Type: `SourceType.SOCIAL_MEDIA`
   - Name: "Reddit"
   - Data: Sentiment scores, post counts
   - Note: Currently fallback mode (OAuth2 required)

4. **Discord Sentiment** (if enabled)
   - Type: `SourceType.SOCIAL_MEDIA`
   - Name: "Discord"
   - Data: Sentiment scores, message counts
   - Note: Currently simulated

5. **RSS News Feeds**
   - Type: `SourceType.RSS_FEED`
   - Name: "Crypto News" (CoinDesk, CoinTelegraph, etc.)
   - URLs: Feed URLs for each news source
   - Data: News articles, sentiment scores

**Implementation**:
```python
# In HunterAIAgentOpenAI.execute()
sources = []

# CoinGecko source
if self._coingecko_client:
    price = await self._coingecko_client.get_price(token)
    sources.append(SourceInfo(
        source_type=SourceType.API,
        source_name="CoinGecko",
        source_id=f"coin:{token}",
        url=f"https://www.coingecko.com/en/coins/{token}",
        citation_text=f"CoinGecko price data for {token.upper()}",
        fetched_at=datetime.utcnow(),
        provider="CoinGecko API",
        endpoint="/simple/price",
        query_params={"ids": token, "vs_currencies": "usd"},
        relevance_score=1.0,
        data_points_used=1,
    ))

# Social media sources (if used)
if twitter_reading:
    sources.append(SourceInfo(
        source_type=SourceType.SOCIAL_MEDIA,
        source_name="Twitter",
        citation_text=f"Twitter sentiment analysis for {token.upper()}",
        fetched_at=datetime.utcnow(),
        data_points_used=twitter_reading.sample_size,
        metadata={"sentiment_score": twitter_reading.score},
    ))

# ... (similar for Reddit, Discord, News)

return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=tools_used,
    sources=sources,  # NEW
    metadata={...},
)
```

#### Research Agent (Perplexity)

**Data Sources**:
1. **Perplexity API**
   - Type: `SourceType.API`
   - Name: "Perplexity AI"
   - Data: Research results with citations
   - Citations: Already provided by Perplexity API

**Implementation**:
```python
# In ResearchAgentPerplexity.execute()
result = await self._perplexity_client.search(query)

sources = []
# Perplexity provides citations
if result.get("citations"):
    for citation in result["citations"]:
        sources.append(SourceInfo(
            source_type=SourceType.API,
            source_name="Perplexity AI",
            url=citation.get("url"),
            citation_text=citation.get("title", citation.get("url")),
            fetched_at=datetime.utcnow(),
            provider="Perplexity API",
            metadata={"citation": citation},
        ))

return AgentResponse(
    content=result["answer"],
    agent_type=self.agent_type,
    tools_used=["perplexity_api"],
    sources=sources,
    metadata={...},
)
```

#### DeFi Yield Agent

**Data Sources**:
1. **DeFiLlama API**
   - Type: `SourceType.API`
   - Name: "DeFiLlama"
   - Endpoints: `/protocols`, `/yields`
   - Data: APY data, TVL, protocol information
   - URL: `https://defillama.com/protocol/{protocol}`

2. **Aave V3** (via MCP or direct)
   - Type: `SourceType.MCP_SERVER` or `SourceType.API`
   - Name: "Aave V3"
   - Data: Supply/borrow rates, market data
   - URL: `https://app.aave.com/` (or contract address)

3. **Morpho Protocol** (via MCP)
   - Type: `SourceType.MCP_SERVER`
   - Name: "Morpho"
   - Data: Vault APY, market allocations
   - URL: `https://app.morpho.org/`

4. **Compound V3** (via direct RPC)
   - Type: `SourceType.BLOCKCHAIN`
   - Name: "Compound V3"
   - Data: Supply/borrow rates
   - URL: Contract address on Etherscan

**Implementation**:
```python
# In DefiYieldAgentOpenAI.execute()
sources = []

# DeFiLlama source
if defillama_data:
    sources.append(SourceInfo(
        source_type=SourceType.API,
        source_name="DeFiLlama",
        url=f"https://defillama.com/protocol/{protocol}",
        citation_text=f"DeFiLlama APY data for {protocol}",
        fetched_at=datetime.utcnow(),
        provider="DeFiLlama API",
        endpoint="/yields",
        relevance_score=1.0,
    ))

# Aave source (if used)
if aave_data:
    sources.append(SourceInfo(
        source_type=SourceType.MCP_SERVER,
        source_name="Aave V3",
        source_id=aave_pool_address,
        url=f"https://app.aave.com/",
        citation_text=f"Aave V3 market data",
        fetched_at=datetime.utcnow(),
        provider="Aave MCP Server",
        metadata={"chain": chain, "pool_address": aave_pool_address},
    ))

# ... (similar for Morpho, Compound)

return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=["defillama_api", "aave_api"],
    sources=sources,
    metadata={...},
)
```

#### Execution Agent

**Data Sources**:
1. **1inch API**
   - Type: `SourceType.API`
   - Name: "1inch"
   - Endpoints: `/swap/v5.2/{chain}/quote`
   - Data: Swap quotes, routes, prices
   - URL: `https://1inch.io/` or swap interface

2. **Privy Wallet SDK**
   - Type: `SourceType.API`
   - Name: "Privy"
   - Data: Wallet balances, transaction signing
   - URL: `https://privy.io/`

3. **Blockchain RPC**
   - Type: `SourceType.BLOCKCHAIN`
   - Name: "Ethereum" / "Base" / etc.
   - Data: Transaction status, gas prices
   - URL: Etherscan/BaseScan transaction link

**Implementation**:
```python
# In ExecutionAgentPrivy.execute()
sources = []

# 1inch quote source
if quote:
    sources.append(SourceInfo(
        source_type=SourceType.API,
        source_name="1inch",
        url=f"https://app.1inch.io/#/{chain}/swap/{from_token}/{to_token}",
        citation_text=f"1inch swap quote: {from_token} → {to_token}",
        fetched_at=datetime.utcnow(),
        provider="1inch Aggregator API",
        endpoint=f"/swap/v5.2/{chain}/quote",
        query_params={"fromTokenAddress": from_token, "toTokenAddress": to_token},
        relevance_score=1.0,
    ))

# Blockchain source (for transaction)
if tx_hash:
    sources.append(SourceInfo(
        source_type=SourceType.BLOCKCHAIN,
        source_name=chain.title(),
        source_id=tx_hash,
        url=f"https://{explorer}/tx/{tx_hash}",
        citation_text=f"Transaction on {chain}",
        fetched_at=datetime.utcnow(),
        provider=f"{chain} RPC",
        metadata={"tx_hash": tx_hash, "chain": chain},
    ))

return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=["1inch_api", "privy_wallet"],
    sources=sources,
    metadata={...},
)
```

#### Portfolio Agent

**Data Sources**:
1. **Portfolio Repository** (Database)
   - Type: `SourceType.DATABASE`
   - Name: "Anvil Portfolio"
   - Data: User's portfolio snapshots, token holdings
   - Note: Internal data, no external URL

2. **Price APIs** (CoinGecko, 1inch)
   - Type: `SourceType.API`
   - Name: "CoinGecko" or "1inch"
   - Data: Token prices for USD conversion

3. **DeFi Protocol APIs** (Aave, Morpho, Compound)
   - Type: `SourceType.API` or `SourceType.MCP_SERVER`
   - Data: Lending positions, yield positions

**Implementation**:
```python
# In PortfolioAgentOpenAI.execute()
sources = []

# Portfolio database source
sources.append(SourceInfo(
    source_type=SourceType.DATABASE,
    source_name="Anvil Portfolio",
    citation_text="Your portfolio data from Anvil",
    fetched_at=datetime.utcnow(),
    data_points_used=len(holdings),
    metadata={"snapshot_id": snapshot_id},
))

# Price source
if price_data:
    sources.append(SourceInfo(
        source_type=SourceType.API,
        source_name="CoinGecko",
        url="https://www.coingecko.com/",
        citation_text="Token prices from CoinGecko",
        fetched_at=datetime.utcnow(),
        provider="CoinGecko API",
    ))

return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=["portfolio_repository", "coingecko_api"],
    sources=sources,
    metadata={...},
)
```

#### Risk Analyzer Agent

**Data Sources**:
1. **DeFiLlama API**
   - Type: `SourceType.API`
   - Name: "DeFiLlama"
   - Data: Protocol risk scores, TVL, audits
   - URL: `https://defillama.com/protocol/{protocol}`

2. **Protocol APIs** (Aave, Morpho, Compound)
   - Type: `SourceType.API` or `SourceType.MCP_SERVER`
   - Data: Health factors, liquidation thresholds

3. **Security Audit Databases**
   - Type: `SourceType.API`
   - Name: "Audit Reports"
   - Data: Security audit information

**Implementation**:
```python
# In RiskAnalyzerAgentOpenAI.execute()
sources = []

# DeFiLlama risk data
if defillama_risk:
    sources.append(SourceInfo(
        source_type=SourceType.API,
        source_name="DeFiLlama",
        url=f"https://defillama.com/protocol/{protocol}",
        citation_text=f"DeFiLlama risk analysis for {protocol}",
        fetched_at=datetime.utcnow(),
        provider="DeFiLlama API",
        relevance_score=1.0,
    ))

# Protocol-specific risk data
if aave_health_factor:
    sources.append(SourceInfo(
        source_type=SourceType.MCP_SERVER,
        source_name="Aave V3",
        citation_text="Aave V3 health factor calculation",
        fetched_at=datetime.utcnow(),
        provider="Aave MCP Server",
        metadata={"health_factor": aave_health_factor},
    ))

return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=["defillama_api", "aave_api"],
    sources=sources,
    metadata={...},
)
```

#### Chat Agent (General)

**Data Sources**:
1. **LLM Only** (no external sources)
   - Type: `SourceType.LLM`
   - Name: "Vertex AI" or "DeepInfra"
   - Data: LLM-generated content
   - Note: No external data sources, just LLM knowledge

**Implementation**:
```python
# In ChatAgentOpenAI.execute()
sources = []

# LLM source (if we want to track which LLM was used)
sources.append(SourceInfo(
    source_type=SourceType.LLM,
    source_name=response.get("model", "Unknown"),
    citation_text=f"Generated by {response.get('model', 'AI model')}",
    fetched_at=datetime.utcnow(),
    provider="Vertex AI" or "DeepInfra",
    metadata={"model": response.get("model")},
))

return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=[],
    sources=sources,
    metadata={...},
)
```

#### Other Agents

**Similar pattern** for:
- **Tax Optimizer**: Tax calculation APIs, tax databases
- **Security Auditor**: Slither, Mythril, audit databases
- **Gas Optimizer**: Gas price oracles, EIP-1559 data
- **Compliance Monitor**: Chainalysis, OFAC APIs
- **MultiSig Coordinator**: Gnosis Safe API
- **Alert Monitoring**: Forta API
- **Crisis Manager**: Forta API, blockchain data
- **Bridge Crosschain**: Axelar, LayerZero APIs
- **Lending Borrowing**: Aave, Compound, Morpho APIs
- **NFT Asset Manager**: OpenSea, Blur APIs
- **DAO Governance**: Snapshot, Tally APIs

---

### 3. Updated Response Schemas

#### MessageResponse Schema

**Location**: `src/app/presentation/http/schemas/chat.py`

```python
class SourceInfoResponse(BaseModel):
    """Source information response for frontend."""
    
    source_type: str  # api, database, mcp_server, rss_feed, social_media, blockchain, llm, aggregated
    source_name: str
    source_id: Optional[str] = None
    url: Optional[str] = None
    citation_text: Optional[str] = None
    fetched_at: Optional[str] = None  # ISO format
    data_age_seconds: Optional[int] = None
    provider: Optional[str] = None
    endpoint: Optional[str] = None
    query_params: Optional[dict] = None
    relevance_score: Optional[float] = None
    data_points_used: Optional[int] = None
    metadata: Optional[dict] = None


class MessageResponse(BaseModel):
    """Message response with source attribution."""
    
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    agent_type: Optional[str]
    sources: List[SourceInfoResponse] = Field(default_factory=list)  # NEW
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_domain(cls, message: Message) -> "MessageResponse":
        """Create response from domain entity."""
        # Extract sources from metadata
        sources = []
        if message.metadata and "sources" in message.metadata:
            sources_data = message.metadata["sources"]
            if isinstance(sources_data, list):
                sources = [
                    SourceInfoResponse(**s) if isinstance(s, dict) else SourceInfoResponse(**s.to_dict())
                    for s in sources_data
                ]
        
        return cls(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role.value if hasattr(message.role, "value") else str(message.role),
            content=message.content,
            agent_type=message.agent_type,
            sources=sources,  # NEW
            created_at=message.created_at,
        )
```

#### UnifiedChatResponse Schema

**Location**: `src/app/presentation/http/schemas/chat.py`

```python
class UnifiedChatResponse(BaseModel):
    """Unified response for all chat routing handlers with source attribution."""

    user_message: dict  # User message data
    agent_message: dict  # Agent response data with sources
    routing: RoutingMetadata  # Routing information
    enrichment: Optional[EnrichmentData] = None  # Handler-specific data
    sources: List[SourceInfoResponse] = Field(default_factory=list)  # NEW: Aggregated sources
```

---

### 4. Database Schema (Optional - Future Enhancement)

#### Sources Table (For Analytics)

**Migration**: `alembic/versions/xxxx_add_message_sources_table.py`

```python
def upgrade():
    op.create_table(
        "message_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_name", sa.String(200), nullable=False),
        sa.Column("source_id", sa.String(200), nullable=True),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("citation_text", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_age_seconds", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(200), nullable=True),
        sa.Column("endpoint", sa.String(500), nullable=True),
        sa.Column("query_params", postgresql.JSONB(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("data_points_used", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
    )
    
    op.create_index("ix_message_sources_message_id", "message_sources", ["message_id"])
    op.create_index("ix_message_sources_source_type", "message_sources", ["source_type"])
    op.create_index("ix_message_sources_source_name", "message_sources", ["source_name"])
```

**Note**: This table is optional. Start with metadata-only approach, add table later if needed for analytics.

---

### 5. Implementation Plan

#### Phase 1: Core Infrastructure (Week 1)

**Tasks**:
1. ✅ Create `SourceInfo` value object
2. ✅ Update `AgentResponse` to include `sources` field
3. ✅ Create `SourceInfoResponse` schema
4. ✅ Update `MessageResponse` to include sources
5. ✅ Update `UnifiedChatResponse` to include sources

**Files to Create/Modify**:
- `src/app/domain/value_objects/chat/source_info.py` (NEW)
- `src/app/domain/ports/agent_squad/agent_gateway.py` (MODIFY)
- `src/app/presentation/http/schemas/chat.py` (MODIFY)

#### Phase 2: Agent Implementation (Week 2)

**Tasks**:
1. ✅ Update Hunter AI Agent (CoinGecko, social media, news)
2. ✅ Update Research Agent (Perplexity citations)
3. ✅ Update DeFi Yield Agent (DeFiLlama, Aave, Morpho, Compound)
4. ✅ Update Execution Agent (1inch, Privy, blockchain)
5. ✅ Update Portfolio Agent (database, price APIs)
6. ✅ Update Risk Analyzer Agent (DeFiLlama, protocol APIs)
7. ✅ Update Chat Agent (LLM source)
8. ✅ Update remaining 12 agents

**Priority Order**:
1. **High Priority**: Hunter AI, Research, DeFi Yield, Execution, Portfolio
2. **Medium Priority**: Risk Analyzer, Tax Optimizer, Security Auditor
3. **Low Priority**: Chat, Gas Optimizer, Enterprise agents

#### Phase 3: Handler Updates (Week 2-3)

**Tasks**:
1. ✅ Update `UnifiedChatOrchestrator` to extract sources from agent responses
2. ✅ Update `SendMessageUnified` to include sources in response
3. ✅ Update GraphRAG handlers to include source information
4. ✅ Update Hunter AI handlers to include source breakdown
5. ✅ Update ULTRA handlers (if applicable)

**Files to Modify**:
- `src/app/application/chat/commands/send_message_unified.py`
- `src/app/application/chat/graph_search_handler.py`
- `src/app/application/chat/risk_insights_handler.py`
- `src/app/application/chat/handlers/*.py` (various handlers)

#### Phase 4: Message Persistence (Week 3)

**Tasks**:
1. ✅ Update `Message` entity to store sources in metadata
2. ✅ Update message repository to persist sources
3. ✅ Update message mappers to handle sources
4. ✅ Ensure backward compatibility (messages without sources)

**Files to Modify**:
- `src/app/domain/entities/message.py` (already has metadata field)
- `src/app/infrastructure/persistence_sqla/mappings/chat.py` (if exists)

#### Phase 5: Frontend Integration (Week 4)

**Tasks**:
1. ✅ Update API response schemas (already done in Phase 1)
2. ✅ Document source display format for frontend
3. ✅ Provide example responses with sources
4. ✅ Create frontend component guidelines

**Deliverables**:
- Updated API documentation
- Example responses with sources
- Frontend component spec

---

### 6. Source Collection Patterns

#### Pattern 1: API Calls

```python
# Before API call
start_time = datetime.utcnow()

# Make API call
result = await api_client.get_data(params)

# After API call
fetched_at = datetime.utcnow()
data_age = (fetched_at - start_time).total_seconds()

# Create source info
source = SourceInfo(
    source_type=SourceType.API,
    source_name="API Name",
    url=api_url,
    citation_text=f"Data from {api_name}",
    fetched_at=fetched_at,
    data_age_seconds=int(data_age),
    provider=f"{api_name} API",
    endpoint=endpoint,
    query_params=sanitize_params(params),  # Remove sensitive data
    relevance_score=1.0,
    data_points_used=len(result) if isinstance(result, list) else 1,
)

sources.append(source)
```

#### Pattern 2: MCP Server Tools

```python
# MCP tool call
result = await mcp_client.call_tool("tool_name", params)

# Create source info
source = SourceInfo(
    source_type=SourceType.MCP_SERVER,
    source_name="MCP Server Name",
    source_id=result.get("id"),
    url=result.get("url"),
    citation_text=f"Data from {mcp_server_name}",
    fetched_at=datetime.utcnow(),
    provider=f"{mcp_server_name} MCP Server",
    endpoint=f"tool:{tool_name}",
    metadata={"mcp_server": mcp_server_name, "tool": tool_name},
)

sources.append(source)
```

#### Pattern 3: Database Queries

```python
# Database query
results = await repository.get_data(query_params)

# Create source info
source = SourceInfo(
    source_type=SourceType.DATABASE,
    source_name="Anvil Database",
    citation_text="Your data from Anvil",
    fetched_at=datetime.utcnow(),
    provider="Anvil Backend",
    data_points_used=len(results),
    metadata={"query_type": "portfolio_snapshot"},
)

sources.append(source)
```

#### Pattern 4: Aggregated Sources

```python
# Multiple sources aggregated
sources = []

# Source 1
sources.append(SourceInfo(...))

# Source 2
sources.append(SourceInfo(...))

# Aggregated source (if needed)
aggregated_source = SourceInfo(
    source_type=SourceType.AGGREGATED,
    source_name="Aggregated Analysis",
    citation_text="Combined analysis from multiple sources",
    fetched_at=datetime.utcnow(),
    metadata={"source_count": len(sources)},
)

# Or just return individual sources
return AgentResponse(..., sources=sources)
```

---

### 7. Source Sanitization

#### Security Considerations

**Rule**: Never expose sensitive data in source information

**Sanitization**:
```python
def sanitize_query_params(params: dict) -> dict:
    """Remove sensitive data from query params."""
    sanitized = {}
    sensitive_keys = ["api_key", "secret", "password", "token", "private_key"]
    
    for key, value in params.items():
        if key.lower() in sensitive_keys:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str) and len(value) > 100:
            sanitized[key] = value[:50] + "..."
        else:
            sanitized[key] = value
    
    return sanitized
```

**Example**:
```python
# Before sanitization
params = {
    "api_key": "sk-1234567890",
    "token": "ETH",
    "amount": "1000",
}

# After sanitization
sanitized = {
    "api_key": "[REDACTED]",
    "token": "ETH",
    "amount": "1000",
}
```

---

### 8. Frontend Display Guidelines

#### Source Attribution UI

**Component Structure**:
```typescript
interface SourceInfo {
  source_type: string;
  source_name: string;
  url?: string;
  citation_text?: string;
  fetched_at?: string;
  data_age_seconds?: number;
  provider?: string;
}

// Display format
<div className="sources">
  <h4>Sources</h4>
  {sources.map((source, idx) => (
    <div key={idx} className="source-item">
      <span className="source-type">{source.source_type}</span>
      <span className="source-name">{source.source_name}</span>
      {source.url && (
        <a href={source.url} target="_blank" rel="noopener noreferrer">
          View Source
        </a>
      )}
      {source.citation_text && (
        <p className="citation">{source.citation_text}</p>
      )}
      {source.data_age_seconds && (
        <span className="data-age">
          {formatAge(source.data_age_seconds)} ago
        </span>
      )}
    </div>
  ))}
</div>
```

#### Display Examples

**Example 1: Hunter AI Sentiment**
```
Sources:
- Twitter: Sentiment analysis for BTC (1,234 tweets analyzed)
- Reddit: Sentiment analysis for BTC (567 posts analyzed)
- CoinGecko: Real-time price data for BTC
  → View Source: https://www.coingecko.com/en/coins/bitcoin
- News: Sentiment from CoinDesk, CoinTelegraph (23 articles)
```

**Example 2: DeFi Yield Agent**
```
Sources:
- DeFiLlama: APY data for Aave V3
  → View Source: https://defillama.com/protocol/aave-v3
- Aave V3: Market data (Ethereum)
  → View Source: https://app.aave.com/
- Morpho: Vault APY data (Base)
  → View Source: https://app.morpho.org/
Data fetched: 2 minutes ago
```

**Example 3: Research Agent**
```
Sources:
- Perplexity AI: Research with citations
  → Citation 1: "Aave V3 Documentation" (https://docs.aave.com/)
  → Citation 2: "DeFiLlama Protocol Data" (https://defillama.com/...)
  → Citation 3: "Compound V3 Whitepaper" (https://compound.finance/...)
```

---

### 9. Testing Strategy

#### Unit Tests

**SourceInfo Value Object**:
```python
def test_source_info_creation():
    source = SourceInfo(
        source_type=SourceType.API,
        source_name="CoinGecko",
        url="https://coingecko.com/",
        citation_text="Price data",
        fetched_at=datetime.utcnow(),
    )
    assert source.source_type == SourceType.API
    assert source.source_name == "CoinGecko"
    
def test_source_info_serialization():
    source = SourceInfo(...)
    data = source.to_dict()
    restored = SourceInfo.from_dict(data)
    assert restored.source_name == source.source_name
```

**Agent Source Collection**:
```python
async def test_hunter_ai_collects_sources():
    agent = HunterAIAgentOpenAI(...)
    response = await agent.execute(...)
    
    assert len(response.sources) > 0
    assert any(s.source_name == "CoinGecko" for s in response.sources)
    assert all(isinstance(s, SourceInfo) for s in response.sources)
```

#### Integration Tests

**End-to-End Source Flow**:
```python
async def test_sources_in_api_response():
    # Send message
    response = await client.post(
        "/api/v1/user/chat/conversations/{id}/messages",
        json={"content": "What's the price of BTC?"},
    )
    
    # Check response includes sources
    agent_message = response.json()["agent_message"]
    assert "sources" in agent_message
    assert len(agent_message["sources"]) > 0
    assert agent_message["sources"][0]["source_name"] == "CoinGecko"
```

---

### 10. Migration Strategy

#### Backward Compatibility

**Existing Messages**:
- Messages without sources: `sources` field will be empty list `[]`
- Frontend should handle empty sources gracefully
- No breaking changes to API

**Gradual Rollout**:
1. **Phase 1**: Add sources to new messages only
2. **Phase 2**: All agents collect sources
3. **Phase 3**: Frontend displays sources
4. **Phase 4**: Optional: Backfill sources for old messages (if needed)

#### Database Migration

**If using separate sources table** (optional):
```python
# Migration: Add sources to existing messages (optional backfill)
def upgrade():
    # Create table (already done)
    # Backfill sources from metadata (if metadata contains sources)
    op.execute("""
        INSERT INTO message_sources (message_id, ...)
        SELECT id, ...
        FROM messages
        WHERE metadata->'sources' IS NOT NULL
    """)
```

---

### 11. Performance Considerations

#### Latency Impact

**Source Collection Overhead**:
- **Minimal**: Creating SourceInfo objects is fast (<1ms)
- **Acceptable**: Additional metadata in response (~100-500 bytes)
- **Mitigation**: Sources collected during agent execution (no extra API calls)

#### Storage Impact

**Per Message**:
- **Metadata approach**: ~500 bytes per source (JSON)
- **Typical message**: 2-5 sources = 1-2.5 KB additional storage
- **Acceptable**: Negligible compared to message content

**If using separate table**:
- **Per source row**: ~1 KB
- **Typical message**: 2-5 rows = 2-5 KB
- **Indexes**: Additional ~500 bytes per source

---

### 12. Analytics & Monitoring

#### Source Usage Analytics

**Metrics to Track**:
- Most used sources (by agent, by user)
- Source reliability (success rate, latency)
- Source freshness (average data age)
- Source relevance (relevance scores)

**Admin Dashboard**:
```python
# Endpoint: GET /api/v1/admin/chat/sources/analytics
{
    "total_sources_used": 1250,
    "sources_by_type": {
        "api": 800,
        "mcp_server": 300,
        "database": 100,
        "social_media": 50,
    },
    "top_sources": [
        {"name": "CoinGecko", "usage_count": 450},
        {"name": "1inch", "usage_count": 200},
        {"name": "Aave V3", "usage_count": 150},
    ],
    "source_reliability": {
        "CoinGecko": {"success_rate": 0.99, "avg_latency_ms": 150},
        "1inch": {"success_rate": 0.95, "avg_latency_ms": 200},
    },
}
```

---

### 13. Error Handling

#### Missing Sources

**Graceful Degradation**:
```python
# If source collection fails, still return response
try:
    sources = collect_sources(...)
except Exception as e:
    logger.warning(f"Failed to collect sources: {e}")
    sources = []  # Empty list, response still works

return AgentResponse(
    content=response["content"],
    sources=sources,  # May be empty
    ...
)
```

#### Invalid Source Data

**Validation**:
```python
def validate_source(source: SourceInfo) -> bool:
    """Validate source information."""
    if not source.source_name:
        return False
    if source.relevance_score and not (0.0 <= source.relevance_score <= 1.0):
        return False
    return True

# Filter invalid sources
valid_sources = [s for s in sources if validate_source(s)]
```

---

### 14. Configuration

#### Source Collection Toggle

**Feature Flag**:
```toml
# config/local/config.toml
[chat]
enable_source_attribution = true
include_source_urls = true
include_query_params = false  # Privacy: don't include query params by default
max_sources_per_message = 10
```

#### Per-Agent Configuration

```toml
[agent_squad.agents.hunter_ai]
collect_sources = true
include_social_media_sources = true

[agent_squad.agents.chat]
collect_sources = false  # LLM-only, no external sources
```

---

### 15. Implementation Checklist

#### Phase 1: Core Infrastructure
- [ ] Create `SourceInfo` value object
- [ ] Create `SourceType` enum
- [ ] Update `AgentResponse` dataclass
- [ ] Create `SourceInfoResponse` schema
- [ ] Update `MessageResponse` schema
- [ ] Update `UnifiedChatResponse` schema
- [ ] Add source sanitization utilities

#### Phase 2: Agent Implementation
- [ ] Hunter AI Agent (CoinGecko, social media, news)
- [ ] Research Agent (Perplexity citations)
- [ ] DeFi Yield Agent (DeFiLlama, Aave, Morpho, Compound)
- [ ] Execution Agent (1inch, Privy, blockchain)
- [ ] Portfolio Agent (database, price APIs)
- [ ] Risk Analyzer Agent (DeFiLlama, protocol APIs)
- [ ] Chat Agent (LLM source)
- [ ] Remaining 11 agents

#### Phase 3: Handler Updates
- [ ] Update `UnifiedChatOrchestrator`
- [ ] Update `SendMessageUnified`
- [ ] Update GraphRAG handlers
- [ ] Update Hunter AI handlers
- [ ] Update ULTRA handlers (if applicable)

#### Phase 4: Testing
- [ ] Unit tests for `SourceInfo`
- [ ] Unit tests for agent source collection
- [ ] Integration tests for API responses
- [ ] Backward compatibility tests

#### Phase 5: Documentation
- [ ] API documentation update
- [ ] Frontend integration guide
- [ ] Source display examples
- [ ] Migration guide

---

## Risk Assessment (CTO Methodology)

### Phase 3: Risk Analysis

#### Cognitive Limitations

**Potential Issues**:
- May miss some sources (agents use many APIs)
- Source relevance scoring is subjective
- Data freshness calculation may be inaccurate

**Mitigation**:
- Comprehensive agent audit
- Default relevance_score = 1.0 (assume all sources relevant)
- Use actual fetch timestamps

#### Technical Debt

**Rapid Implementation Compromises**:
- Starting with metadata-only (no separate table)
- Simple source collection (no complex relevance scoring)
- Basic sanitization (can enhance later)

**Long-term Maintenance**:
- May need separate sources table for analytics
- May need source caching to reduce API calls
- May need source validation rules

#### Validation Strategy

**Success Criteria**:
- ✅ All agents collect at least one source
- ✅ Frontend can display sources
- ✅ No breaking API changes
- ✅ Performance impact < 5% latency increase

**Failure Modes**:
- Source collection fails silently (mitigated by try/except)
- Invalid source data (mitigated by validation)
- Storage bloat (mitigated by metadata size limits)

---

## Example Implementations

### Example 1: Hunter AI with Multiple Sources

```python
# In HunterAIAgentOpenAI.execute()
sources = []
fetched_at = datetime.utcnow()

# CoinGecko source
if self._coingecko_client:
    price = await self._coingecko_client.get_price(token)
    sources.append(SourceInfo(
        source_type=SourceType.API,
        source_name="CoinGecko",
        source_id=f"coin:{token}",
        url=f"https://www.coingecko.com/en/coins/{token}",
        citation_text=f"Real-time price data for {token.upper()} from CoinGecko",
        fetched_at=fetched_at,
        provider="CoinGecko API",
        endpoint="/simple/price",
        query_params={"ids": token, "vs_currencies": "usd"},
        relevance_score=1.0,
        data_points_used=1,
        metadata={"price_usd": float(price.usd)},
    ))

# Twitter sentiment source
if twitter_reading:
    sources.append(SourceInfo(
        source_type=SourceType.SOCIAL_MEDIA,
        source_name="Twitter",
        citation_text=f"Twitter sentiment analysis for {token.upper()}",
        fetched_at=fetched_at,
        data_points_used=twitter_reading.sample_size,
        relevance_score=0.8,
        metadata={
            "sentiment_score": twitter_reading.score,
            "classification": twitter_reading.classification.value,
        },
    ))

# News sentiment source
if news_reading:
    sources.append(SourceInfo(
        source_type=SourceType.RSS_FEED,
        source_name="Crypto News",
        citation_text=f"News sentiment from CoinDesk, CoinTelegraph, and other sources",
        fetched_at=fetched_at,
        data_points_used=news_reading.sample_size,
        relevance_score=0.7,
        metadata={
            "news_sources": ["coindesk.com", "cointelegraph.com"],
            "article_count": news_reading.sample_size,
        },
    ))

return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=tools_used,
    sources=sources,  # NEW
    metadata={
        "tokens_used": response.get("tokens_used"),
        "latency_ms": latency_ms,
        "model": response.get("model"),
    },
)
```

### Example 2: Research Agent with Citations

```python
# In ResearchAgentPerplexity.execute()
result = await self._perplexity_client.search(query)

sources = []
fetched_at = datetime.utcnow()

# Perplexity provides citations
if result.get("citations"):
    for idx, citation in enumerate(result["citations"], 1):
        sources.append(SourceInfo(
            source_type=SourceType.API,
            source_name="Perplexity AI",
            url=citation.get("url"),
            citation_text=citation.get("title") or citation.get("url"),
            fetched_at=fetched_at,
            provider="Perplexity API",
            endpoint="/chat/completions",
            relevance_score=1.0 / len(result["citations"]),  # Distribute relevance
            metadata={
                "citation_index": idx,
                "citation": citation,
            },
        ))

# If no citations, still include Perplexity as source
if not sources:
    sources.append(SourceInfo(
        source_type=SourceType.API,
        source_name="Perplexity AI",
        citation_text="AI-powered research from Perplexity",
        fetched_at=fetched_at,
        provider="Perplexity API",
    ))

return AgentResponse(
    content=result["answer"],
    agent_type=self.agent_type,
    tools_used=["perplexity_api"],
    sources=sources,
    metadata={...},
)
```

### Example 3: DeFi Yield Agent with Protocol Sources

```python
# In DefiYieldAgentOpenAI.execute()
sources = []
fetched_at = datetime.utcnow()

# DeFiLlama source
if defillama_data:
    for protocol_data in defillama_data:
        sources.append(SourceInfo(
            source_type=SourceType.API,
            source_name="DeFiLlama",
            url=f"https://defillama.com/protocol/{protocol_data['protocol']}",
            citation_text=f"DeFiLlama APY and TVL data for {protocol_data['protocol']}",
            fetched_at=fetched_at,
            provider="DeFiLlama API",
            endpoint="/yields",
            relevance_score=1.0,
            metadata={"protocol": protocol_data["protocol"]},
        ))

# Aave source (via MCP)
if aave_data:
    sources.append(SourceInfo(
        source_type=SourceType.MCP_SERVER,
        source_name="Aave V3",
        source_id=aave_pool_address,
        url=f"https://app.aave.com/",
        citation_text=f"Aave V3 market data on {chain}",
        fetched_at=fetched_at,
        provider="Aave MCP Server",
        endpoint="mcp://aave/get_markets",
        metadata={
            "chain": chain,
            "pool_address": aave_pool_address,
            "markets_count": len(aave_data.get("markets", [])),
        },
    ))

# Morpho source (via MCP)
if morpho_data:
    sources.append(SourceInfo(
        source_type=SourceType.MCP_SERVER,
        source_name="Morpho",
        url="https://app.morpho.org/",
        citation_text=f"Morpho vault APY data on {chain}",
        fetched_at=fetched_at,
        provider="Morpho MCP Server",
        endpoint="mcp://morpho/get_vaults",
        metadata={"chain": chain, "vaults_count": len(morpho_data)},
    ))

return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=["defillama_api", "aave_api", "morpho_api"],
    sources=sources,
    metadata={...},
)
```

---

## API Response Examples

### Example 1: Hunter AI Response with Sources

```json
{
  "user_message": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "content": "What's the sentiment for BTC?",
    "role": "user",
    "created_at": "2026-01-02T10:00:00Z"
  },
  "agent_message": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "content": "📊 **Sentiment Analysis for BTC**\n\n**Overall Sentiment:** Bullish (72.5/100)...",
    "role": "agent",
    "agent_type": "hunter_ai",
    "sources": [
      {
        "source_type": "api",
        "source_name": "CoinGecko",
        "source_id": "coin:bitcoin",
        "url": "https://www.coingecko.com/en/coins/bitcoin",
        "citation_text": "Real-time price data for BTC from CoinGecko",
        "fetched_at": "2026-01-02T10:00:15Z",
        "data_age_seconds": 2,
        "provider": "CoinGecko API",
        "endpoint": "/simple/price",
        "query_params": {"ids": "bitcoin", "vs_currencies": "usd"},
        "relevance_score": 1.0,
        "data_points_used": 1
      },
      {
        "source_type": "social_media",
        "source_name": "Twitter",
        "citation_text": "Twitter sentiment analysis for BTC",
        "fetched_at": "2026-01-02T10:00:15Z",
        "data_points_used": 1234,
        "relevance_score": 0.8,
        "metadata": {
          "sentiment_score": 75.0,
          "classification": "bullish"
        }
      },
      {
        "source_type": "rss_feed",
        "source_name": "Crypto News",
        "citation_text": "News sentiment from CoinDesk, CoinTelegraph, and other sources",
        "fetched_at": "2026-01-02T10:00:15Z",
        "data_points_used": 23,
        "relevance_score": 0.7,
        "metadata": {
          "news_sources": ["coindesk.com", "cointelegraph.com"],
          "article_count": 23
        }
      }
    ],
    "created_at": "2026-01-02T10:00:16Z"
  },
  "routing": {
    "intent": "HUNTER_SENTIMENT",
    "confidence": 0.95,
    "handler": "hunter_ai",
    "agent_used": "hunter_ai"
  }
}
```

### Example 2: Research Agent Response with Citations

```json
{
  "agent_message": {
    "content": "Aave V3 is a decentralized lending protocol...",
    "agent_type": "research",
    "sources": [
      {
        "source_type": "api",
        "source_name": "Perplexity AI",
        "url": "https://docs.aave.com/developers/",
        "citation_text": "Aave V3 Developer Documentation",
        "fetched_at": "2026-01-02T10:05:00Z",
        "provider": "Perplexity API",
        "relevance_score": 0.33
      },
      {
        "source_type": "api",
        "source_name": "Perplexity AI",
        "url": "https://defillama.com/protocol/aave-v3",
        "citation_text": "DeFiLlama Protocol Data",
        "fetched_at": "2026-01-02T10:05:00Z",
        "provider": "Perplexity API",
        "relevance_score": 0.33
      },
      {
        "source_type": "api",
        "source_name": "Perplexity AI",
        "url": "https://github.com/aave/aave-v3-core",
        "citation_text": "Aave V3 Core Smart Contracts",
        "fetched_at": "2026-01-02T10:05:00Z",
        "provider": "Perplexity API",
        "relevance_score": 0.34
      }
    ]
  }
}
```

### Example 3: DeFi Yield Agent Response

```json
{
  "agent_message": {
    "content": "🌾 **Best USDC Yields**\n\n1. **Morpho Base USDC Vault**: 5.2% APY...",
    "agent_type": "defi_yield",
    "sources": [
      {
        "source_type": "api",
        "source_name": "DeFiLlama",
        "url": "https://defillama.com/yields",
        "citation_text": "DeFiLlama yield farming data",
        "fetched_at": "2026-01-02T10:10:00Z",
        "provider": "DeFiLlama API",
        "endpoint": "/yields",
        "relevance_score": 1.0
      },
      {
        "source_type": "mcp_server",
        "source_name": "Morpho",
        "url": "https://app.morpho.org/",
        "citation_text": "Morpho vault APY data on Base",
        "fetched_at": "2026-01-02T10:10:01Z",
        "provider": "Morpho MCP Server",
        "endpoint": "mcp://morpho/get_vaults",
        "metadata": {
          "chain": "base",
          "vaults_count": 5
        }
      },
      {
        "source_type": "mcp_server",
        "source_name": "Aave V3",
        "url": "https://app.aave.com/",
        "citation_text": "Aave V3 market data on Ethereum",
        "fetched_at": "2026-01-02T10:10:02Z",
        "provider": "Aave MCP Server",
        "endpoint": "mcp://aave/get_markets",
        "metadata": {
          "chain": "ethereum",
          "markets_count": 35
        }
      }
    ]
  }
}
```

---

## Summary

### Implementation Approach

**Selected Solution**: **Hybrid Approach (Metadata + Optional Table)**
- **Phase 1**: Rich source objects in `Message.metadata` (immediate)
- **Phase 2**: Optional separate table for analytics (future, if needed)

### Key Components

1. **SourceInfo Value Object**: Structured source information
2. **Updated AgentResponse**: Includes `sources: list[SourceInfo]`
3. **Updated Schemas**: `MessageResponse` and `UnifiedChatResponse` include sources
4. **Agent Implementation**: All 18 agents collect sources
5. **Handler Updates**: Extract and include sources in responses

### Benefits

- **Transparency**: Users see data sources
- **Trust**: Citations build confidence
- **Compliance**: Source tracking for regulations
- **Debugging**: Easier to trace issues
- **Analytics**: Understand source value

### Implementation Timeline

- **Week 1**: Core infrastructure (SourceInfo, schemas)
- **Week 2**: Agent implementation (priority agents)
- **Week 3**: Handler updates, remaining agents
- **Week 4**: Testing, documentation, frontend integration

### Risk Mitigation

- **Backward Compatible**: Empty sources list for old messages
- **Graceful Degradation**: Source collection failures don't break responses
- **Performance**: Minimal latency impact (<5%)
- **Storage**: Efficient JSONB storage (~1-2 KB per message)

---

**Last Updated**: January 2, 2026
