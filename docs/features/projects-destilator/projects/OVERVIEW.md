# Admin-Configured Projects System

## Overview

The Projects System allows administrators to create pre-configured contexts for specific DeFi use cases, providing users with specialized assistance tailored to their needs.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ADMIN PROJECTS SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      ADMIN DASHBOARD                                   │  │
│  │                                                                        │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │  │
│  │  │   CREATE    │ │  CONFIGURE  │ │   ASSIGN    │ │   MONITOR   │     │  │
│  │  │   PROJECT   │ │   PROJECT   │ │   USERS     │ │  ANALYTICS  │     │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘     │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                        │                                     │
│                                        ▼                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                       PROJECT COMPONENTS                               │  │
│  │                                                                        │  │
│  │  ┌────────────────────────────────────────────────────────────────┐   │  │
│  │  │                    PROJECT DEFINITION                           │   │  │
│  │  │                                                                 │   │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐│   │  │
│  │  │  │ KNOWLEDGE   │  │   TOOLS     │  │    SYSTEM PROMPT        ││   │  │
│  │  │  │    BASE     │  │             │  │                         ││   │  │
│  │  │  │             │  │ • Swap      │  │ "You are an expert in   ││   │  │
│  │  │  │ • Docs      │  │ • Stake     │  │  {protocol}. Help users ││   │  │
│  │  │  │ • FAQs      │  │ • Lend      │  │  with {use_case}..."    ││   │  │
│  │  │  │ • Guides    │  │ • Bridge    │  │                         ││   │  │
│  │  │  │ • Data      │  │ • Custom    │  │                         ││   │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘│   │  │
│  │  │                                                                 │   │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐│   │  │
│  │  │  │  PROTOCOLS  │  │   CHAINS    │  │      RISK CONFIG        ││   │  │
│  │  │  │             │  │             │  │                         ││   │  │
│  │  │  │ • Aave      │  │ • Ethereum  │  │ • Max Slippage: 1%      ││   │  │
│  │  │  │ • Uniswap   │  │ • Arbitrum  │  │ • Max Position: $10K    ││   │  │
│  │  │  │ • Compound  │  │ • Polygon   │  │ • Require 2FA: Yes      ││   │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘│   │  │
│  │  │                                                                 │   │  │
│  │  └────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                        │                                     │
│                                        ▼                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      USER EXPERIENCE                                   │  │
│  │                                                                        │  │
│  │    User selects project → Context loaded → Specialized assistance     │  │
│  │                                                                        │  │
│  │    "I want to stake ETH"                                              │  │
│  │         │                                                              │  │
│  │         ▼                                                              │  │
│  │    [Staking Project Context]                                          │  │
│  │    • Lido knowledge loaded                                            │  │
│  │    • Staking tools enabled                                            │  │
│  │    • Risk parameters applied                                          │  │
│  │         │                                                              │  │
│  │         ▼                                                              │  │
│  │    "I recommend Lido for liquid staking. Current APY is 3.8%..."     │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Project Definition

```python
@dataclass
class Project:
    """Admin-configured project definition."""
    
    # Identity
    id: UUID
    slug: str                    # "savings", "earning", "aave"
    name: str                    # "Savings Project"
    description: str
    icon: str                    # Emoji or icon URL
    color: str                   # Brand color hex
    
    # Configuration
    status: ProjectStatus        # ACTIVE, DRAFT, ARCHIVED
    visibility: Visibility       # PUBLIC, PRIVATE, INVITE_ONLY
    
    # Components
    knowledge_base_id: UUID
    system_prompt: str
    welcome_message: str
    
    # DeFi Configuration
    enabled_protocols: List[str]
    enabled_chains: List[str]
    enabled_tools: List[str]
    
    # Risk Configuration
    risk_config: ProjectRiskConfig
    
    # User Management
    auto_assign_rules: List[AutoAssignRule]
    max_users: Optional[int]
    
    # Analytics
    created_at: datetime
    updated_at: datetime
    created_by: UUID            # Admin user ID
    usage_stats: ProjectStats


@dataclass
class ProjectRiskConfig:
    """Risk parameters for project."""
    max_slippage_bps: int = 100          # 1%
    max_position_usd: Decimal = 10000
    max_daily_volume_usd: Decimal = 50000
    require_2fa_for_transactions: bool = True
    allowed_tokens: Optional[List[str]] = None
    blocked_tokens: List[str] = field(default_factory=list)
    require_simulation: bool = True


class ProjectStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Visibility(Enum):
    PUBLIC = "public"           # All users can see and join
    PRIVATE = "private"         # Only assigned users
    INVITE_ONLY = "invite_only" # Requires invitation
```

### 2. Knowledge Base

```python
@dataclass
class KnowledgeBase:
    """Project-specific knowledge repository."""
    
    id: UUID
    project_id: UUID
    
    # Documents
    documents: List[KnowledgeDocument]
    
    # Vector embeddings for retrieval
    embedding_model: str
    vector_store_id: str
    
    # Statistics
    total_documents: int
    total_chunks: int
    last_updated: datetime


@dataclass
class KnowledgeDocument:
    """Individual knowledge document."""
    
    id: UUID
    knowledge_base_id: UUID
    
    # Content
    title: str
    content: str
    doc_type: DocumentType       # GUIDE, FAQ, REFERENCE, DATA
    
    # Source
    source_url: Optional[str]
    source_type: str             # MANUAL, CRAWLED, API
    
    # Metadata
    tags: List[str]
    priority: int                # Higher = more important in retrieval
    
    # Processing
    is_processed: bool
    chunk_count: int
    embedding_status: str


class DocumentType(Enum):
    GUIDE = "guide"              # How-to guides
    FAQ = "faq"                  # Frequently asked questions
    REFERENCE = "reference"      # Technical documentation
    DATA = "data"                # Dynamic data (APYs, prices)
    ANNOUNCEMENT = "announcement" # Updates, news
```

### 3. Tool Configuration

```python
@dataclass
class ProjectToolConfig:
    """Tool configuration for project."""
    
    project_id: UUID
    tool_id: str
    
    # Enablement
    is_enabled: bool
    
    # Restrictions
    max_calls_per_session: Optional[int]
    max_amount_per_call: Optional[Decimal]
    requires_confirmation: bool
    
    # Custom parameters
    default_params: Dict[str, Any]
    locked_params: Dict[str, Any]  # Cannot be overridden


# Available tools for projects
PROJECT_TOOLS = {
    "swap": {
        "name": "Token Swap",
        "description": "Swap tokens on DEXs",
        "applicable_projects": ["trading", "portfolio", "earning"]
    },
    "stake": {
        "name": "Staking",
        "description": "Stake tokens for rewards",
        "applicable_projects": ["staking", "earning", "savings"]
    },
    "lend": {
        "name": "Lending",
        "description": "Lend assets to protocols",
        "applicable_projects": ["aave", "savings", "earning"]
    },
    "borrow": {
        "name": "Borrowing",
        "description": "Borrow against collateral",
        "applicable_projects": ["aave", "trading"]
    },
    "bridge": {
        "name": "Bridge",
        "description": "Cross-chain transfers",
        "applicable_projects": ["bridge", "portfolio"]
    },
    "governance": {
        "name": "Governance",
        "description": "Vote on proposals",
        "applicable_projects": ["governance"]
    },
    "analyze_portfolio": {
        "name": "Portfolio Analysis",
        "description": "Analyze holdings and performance",
        "applicable_projects": ["portfolio", "risk"]
    },
    "check_health": {
        "name": "Health Factor Check",
        "description": "Check lending position health",
        "applicable_projects": ["aave", "risk"]
    }
}
```

---

## 10 Pre-Configured Project Templates

### 1. 💰 Savings Project

```python
SAVINGS_PROJECT = {
    "slug": "savings",
    "name": "Smart Savings",
    "description": "Low-risk yield optimization for stablecoin holdings",
    "icon": "💰",
    "color": "#10B981",  # Green
    
    "system_prompt": """You are Anvil's Savings Specialist, focused on helping users 
maximize returns on their stablecoin holdings with minimal risk.

Your expertise includes:
- Stablecoin yield opportunities across protocols
- Risk assessment for different yield strategies
- USDC, USDT, DAI optimization
- Understanding of depeg risks and mitigation

Guidelines:
- Always prioritize capital preservation over yield
- Recommend only audited, battle-tested protocols
- Explain risks clearly before any action
- Focus on APY consistency over maximum returns
- Consider gas costs in recommendations""",
    
    "welcome_message": """Welcome to Smart Savings! 💰

I help you find the best low-risk yields for your stablecoins. 

I can help you with:
• Finding the best APY for USDC, USDT, or DAI
• Comparing lending protocols safely
• Setting up automated yield strategies
• Understanding the risks of each option

What would you like to optimize today?""",
    
    "enabled_protocols": ["aave", "compound", "morpho", "yearn"],
    "enabled_chains": ["ethereum", "arbitrum", "base"],
    "enabled_tools": ["lend", "analyze_portfolio", "check_health"],
    
    "risk_config": {
        "max_slippage_bps": 50,
        "max_position_usd": 100000,
        "allowed_tokens": ["USDC", "USDT", "DAI", "FRAX"],
        "require_simulation": True
    },
    
    "knowledge_base_topics": [
        "Stablecoin yield strategies",
        "Protocol risk comparison",
        "Depeg risk assessment",
        "Gas optimization for deposits",
        "Auto-compounding explained"
    ]
}
```

### 2. 🌾 Earning Project

```python
EARNING_PROJECT = {
    "slug": "earning",
    "name": "Yield Farming",
    "description": "Active yield farming and liquidity provision strategies",
    "icon": "🌾",
    "color": "#F59E0B",  # Amber
    
    "system_prompt": """You are Anvil's Yield Farming Expert, helping users maximize 
returns through active DeFi strategies.

Your expertise includes:
- Liquidity provision on Uniswap, Curve, Balancer
- Yield farming opportunities across chains
- Impermanent loss calculations and mitigation
- Reward token strategies (compound vs sell)
- Multi-protocol strategies

Guidelines:
- Explain impermanent loss risk for every LP position
- Calculate realistic APY after fees
- Consider reward token sustainability
- Warn about rug pull indicators
- Factor in gas costs for harvest strategies""",
    
    "welcome_message": """Welcome to Yield Farming! 🌾

I'm here to help you find and manage high-yield DeFi opportunities.

I can help you with:
• Finding the best LP opportunities
• Calculating real APY vs advertised APY
• Managing impermanent loss risk
• Optimizing harvest and compound strategies
• Multi-chain yield opportunities

What yields are you looking to capture?""",
    
    "enabled_protocols": ["uniswap", "curve", "balancer", "convex", "yearn", "beefy"],
    "enabled_chains": ["ethereum", "arbitrum", "polygon", "optimism"],
    "enabled_tools": ["swap", "stake", "lend", "analyze_portfolio"],
    
    "risk_config": {
        "max_slippage_bps": 100,
        "max_position_usd": 50000,
        "require_simulation": True
    },
    
    "knowledge_base_topics": [
        "Impermanent loss explained",
        "LP strategy guide",
        "Reward token analysis",
        "Yield aggregator comparison",
        "Farm risk assessment"
    ]
}
```

### 3. 🏦 Aave Project

```python
AAVE_PROJECT = {
    "slug": "aave",
    "name": "Aave Lending",
    "description": "Complete Aave lending and borrowing assistance",
    "icon": "🏦",
    "color": "#B6509E",  # Aave purple
    
    "system_prompt": """You are Anvil's Aave Specialist, an expert in the Aave 
lending protocol across all supported chains.

Your expertise includes:
- Supply and borrow optimization on Aave V3
- Health factor management and liquidation prevention
- E-mode strategies for correlated assets
- GHO stablecoin mechanics
- Cross-chain Aave positions

Guidelines:
- Always check health factor before borrowing
- Warn about liquidation risks clearly
- Explain interest rate models
- Consider gas costs for small positions
- Recommend appropriate LTV ratios
- Monitor health factor alerts""",
    
    "welcome_message": """Welcome to Aave Lending! 🏦

I'm your dedicated Aave assistant, here to help you lend, borrow, and manage positions.

I can help you with:
• Depositing assets to earn yield
• Borrowing against your collateral safely
• Managing your health factor
• Understanding E-mode opportunities
• Optimizing your Aave strategy

What would you like to do with Aave today?""",
    
    "enabled_protocols": ["aave"],
    "enabled_chains": ["ethereum", "arbitrum", "polygon", "optimism", "base"],
    "enabled_tools": ["lend", "borrow", "check_health", "swap"],
    
    "risk_config": {
        "max_slippage_bps": 50,
        "max_position_usd": 100000,
        "min_health_factor": 1.5,
        "require_simulation": True,
        "require_2fa_for_transactions": True
    },
    
    "knowledge_base_topics": [
        "Aave V3 documentation",
        "Health factor explained",
        "Liquidation mechanics",
        "E-mode strategies",
        "GHO stablecoin guide",
        "Interest rate models"
    ]
}
```

### 4. 📈 Trading Project

```python
TRADING_PROJECT = {
    "slug": "trading",
    "name": "DeFi Trading",
    "description": "Spot and perpetual futures trading assistance",
    "icon": "📈",
    "color": "#3B82F6",  # Blue
    
    "system_prompt": """You are Anvil's Trading Assistant, helping users execute 
trades and manage positions in DeFi markets.

Your expertise includes:
- DEX aggregation for best execution
- Perpetual futures on Hyperliquid, GMX
- Leverage management and risk
- Technical analysis basics
- MEV protection strategies

Guidelines:
- Always quote slippage and price impact
- Warn about leverage risks
- Explain funding rates for perps
- Consider liquidity depth
- Never provide financial advice on direction
- Focus on execution quality""",
    
    "welcome_message": """Welcome to DeFi Trading! 📈

I help you execute trades efficiently and manage your trading positions.

I can help you with:
• Finding the best swap routes
• Opening and managing perpetual positions
• Understanding leverage and margin
• Calculating slippage and price impact
• Setting up stop losses and take profits

What trade are you looking to execute?""",
    
    "enabled_protocols": ["uniswap", "1inch", "hyperliquid", "gmx", "dydx"],
    "enabled_chains": ["ethereum", "arbitrum", "optimism"],
    "enabled_tools": ["swap", "trade_perps", "analyze_portfolio"],
    
    "risk_config": {
        "max_slippage_bps": 100,
        "max_leverage": 10,
        "max_position_usd": 25000,
        "require_simulation": True
    },
    
    "knowledge_base_topics": [
        "DEX aggregation guide",
        "Perpetual futures basics",
        "Leverage risk management",
        "Funding rate mechanics",
        "MEV protection"
    ]
}
```

### 5. 🥩 Staking Project

```python
STAKING_PROJECT = {
    "slug": "staking",
    "name": "Staking Hub",
    "description": "ETH staking and liquid staking token management",
    "icon": "🥩",
    "color": "#8B5CF6",  # Purple
    
    "system_prompt": """You are Anvil's Staking Expert, specializing in Ethereum 
staking and liquid staking derivatives.

Your expertise includes:
- Native ETH staking requirements
- Liquid staking with Lido, Rocket Pool, Coinbase
- LST yield optimization strategies
- Validator economics and rewards
- Restaking with EigenLayer

Guidelines:
- Explain staking vs liquid staking tradeoffs
- Discuss slashing risks honestly
- Compare LST options fairly
- Consider withdrawal times
- Explain reward mechanics""",
    
    "welcome_message": """Welcome to Staking Hub! 🥩

I'm here to help you stake your ETH and maximize staking rewards.

I can help you with:
• Choosing between native and liquid staking
• Comparing Lido, Rocket Pool, Coinbase cbETH
• Understanding staking rewards
• Managing your staked positions
• Exploring restaking opportunities

How would you like to put your ETH to work?""",
    
    "enabled_protocols": ["lido", "rocket_pool", "coinbase", "eigenlayer"],
    "enabled_chains": ["ethereum"],
    "enabled_tools": ["stake", "swap", "analyze_portfolio"],
    
    "risk_config": {
        "max_slippage_bps": 50,
        "max_position_usd": 500000,
        "allowed_tokens": ["ETH", "stETH", "rETH", "cbETH"],
        "require_simulation": True
    },
    
    "knowledge_base_topics": [
        "ETH staking guide",
        "Liquid staking comparison",
        "Slashing risk explained",
        "Withdrawal mechanics",
        "Restaking with EigenLayer"
    ]
}
```

### 6. 🌉 Bridge Project

```python
BRIDGE_PROJECT = {
    "slug": "bridge",
    "name": "Cross-Chain Bridge",
    "description": "Safe and efficient cross-chain asset transfers",
    "icon": "🌉",
    "color": "#EC4899",  # Pink
    
    "system_prompt": """You are Anvil's Bridge Expert, helping users safely move 
assets across different blockchain networks.

Your expertise includes:
- Native bridges vs third-party bridges
- Bridge security and risk assessment
- Gas optimization for bridging
- Multi-hop bridging strategies
- Canonical vs non-canonical assets

Guidelines:
- Always verify bridge contract addresses
- Warn about bridge security history
- Explain expected wait times
- Compare fees across options
- Verify asset canonicality on destination""",
    
    "welcome_message": """Welcome to Cross-Chain Bridge! 🌉

I help you move assets safely between different blockchains.

I can help you with:
• Bridging ETH and tokens to L2s
• Comparing bridge options and fees
• Understanding bridge security
• Tracking pending bridge transactions
• Multi-chain portfolio management

Where would you like to move your assets?""",
    
    "enabled_protocols": ["arbitrum_bridge", "optimism_bridge", "polygon_bridge", "stargate", "across"],
    "enabled_chains": ["ethereum", "arbitrum", "optimism", "polygon", "base"],
    "enabled_tools": ["bridge", "swap", "analyze_portfolio"],
    
    "risk_config": {
        "max_slippage_bps": 100,
        "max_position_usd": 100000,
        "require_simulation": True
    },
    
    "knowledge_base_topics": [
        "Bridge security guide",
        "L2 bridging comparison",
        "Canonical vs wrapped assets",
        "Bridge fee optimization",
        "Multi-hop strategies"
    ]
}
```

### 7. 📊 Portfolio Project

```python
PORTFOLIO_PROJECT = {
    "slug": "portfolio",
    "name": "Portfolio Manager",
    "description": "Comprehensive portfolio tracking and optimization",
    "icon": "📊",
    "color": "#06B6D4",  # Cyan
    
    "system_prompt": """You are Anvil's Portfolio Manager, helping users track, 
analyze, and optimize their DeFi holdings.

Your expertise includes:
- Multi-chain portfolio aggregation
- Performance attribution analysis
- Risk assessment and diversification
- Rebalancing strategies
- Tax-efficient management

Guidelines:
- Provide comprehensive portfolio views
- Calculate true cost basis
- Identify concentration risks
- Suggest diversification improvements
- Consider tax implications
- Track historical performance""",
    
    "welcome_message": """Welcome to Portfolio Manager! 📊

I help you understand and optimize your complete DeFi portfolio.

I can help you with:
• Viewing all your holdings across chains
• Analyzing your portfolio performance
• Identifying risk concentrations
• Suggesting rebalancing strategies
• Tracking gains and losses

Want me to analyze your current portfolio?""",
    
    "enabled_protocols": ["all"],
    "enabled_chains": ["ethereum", "arbitrum", "polygon", "optimism", "base"],
    "enabled_tools": ["analyze_portfolio", "swap", "rebalance"],
    
    "risk_config": {
        "max_slippage_bps": 100,
        "max_position_usd": 500000,
        "require_simulation": True
    },
    
    "knowledge_base_topics": [
        "Portfolio theory basics",
        "Risk metrics explained",
        "Rebalancing strategies",
        "Tax-loss harvesting",
        "DeFi portfolio best practices"
    ]
}
```

### 8. 🗳️ Governance Project

```python
GOVERNANCE_PROJECT = {
    "slug": "governance",
    "name": "DAO Governance",
    "description": "DAO participation, voting, and delegation",
    "icon": "🗳️",
    "color": "#F97316",  # Orange
    
    "system_prompt": """You are Anvil's Governance Expert, helping users participate 
effectively in DeFi governance.

Your expertise includes:
- Understanding DAO proposals
- Voting strategies and delegation
- Governance token economics
- Proposal impact analysis
- Delegation to active participants

Guidelines:
- Summarize proposals objectively
- Explain voting power mechanics
- Discuss potential impacts
- Never recommend how to vote
- Highlight contentious issues""",
    
    "welcome_message": """Welcome to DAO Governance! 🗳️

I help you participate effectively in DeFi governance decisions.

I can help you with:
• Understanding active proposals
• Calculating your voting power
• Setting up delegation
• Tracking governance across protocols
• Analyzing proposal impacts

Which DAO would you like to engage with?""",
    
    "enabled_protocols": ["aave_governance", "uniswap_governance", "compound_governance", "curve_governance"],
    "enabled_chains": ["ethereum"],
    "enabled_tools": ["governance", "delegate", "analyze_proposal"],
    
    "risk_config": {
        "require_simulation": False,
        "require_2fa_for_transactions": True
    },
    
    "knowledge_base_topics": [
        "DAO governance basics",
        "Delegation strategies",
        "Voting power mechanics",
        "Historical proposal analysis",
        "Governance token economics"
    ]
}
```

### 9. 🛡️ Risk Management Project

```python
RISK_PROJECT = {
    "slug": "risk",
    "name": "Risk Management",
    "description": "Position protection, hedging, and risk mitigation",
    "icon": "🛡️",
    "color": "#EF4444",  # Red
    
    "system_prompt": """You are Anvil's Risk Manager, helping users protect their 
positions and manage DeFi risks effectively.

Your expertise includes:
- Position risk assessment
- Hedging strategies with options/perps
- Liquidation prevention
- Insurance protocols (Nexus, InsurAce)
- Smart contract risk evaluation

Guidelines:
- Prioritize capital preservation
- Quantify risks clearly
- Suggest appropriate hedges
- Monitor health factors proactively
- Explain worst-case scenarios
- Recommend insurance when appropriate""",
    
    "welcome_message": """Welcome to Risk Management! 🛡️

I help you protect your DeFi positions and manage risk effectively.

I can help you with:
• Assessing your current risk exposure
• Setting up hedges for your positions
• Preventing liquidations
• Understanding insurance options
• Evaluating smart contract risks

Would you like me to analyze your risk profile?""",
    
    "enabled_protocols": ["aave", "compound", "nexus_mutual", "insurace", "gmx"],
    "enabled_chains": ["ethereum", "arbitrum"],
    "enabled_tools": ["check_health", "analyze_portfolio", "hedge", "insure"],
    
    "risk_config": {
        "max_slippage_bps": 50,
        "conservative_mode": True,
        "require_simulation": True,
        "require_2fa_for_transactions": True
    },
    
    "knowledge_base_topics": [
        "DeFi risk framework",
        "Hedging strategies",
        "Insurance protocol guide",
        "Liquidation prevention",
        "Smart contract audit reading"
    ]
}
```

### 10. 🎨 NFT Finance Project

```python
NFT_FINANCE_PROJECT = {
    "slug": "nft-finance",
    "name": "NFT Finance",
    "description": "NFT collateral, lending, and financial strategies",
    "icon": "🎨",
    "color": "#A855F7",  # Purple
    
    "system_prompt": """You are Anvil's NFT Finance Expert, helping users leverage 
their NFTs for financial opportunities.

Your expertise includes:
- NFT-backed lending (Blur, NFTfi, BendDAO)
- Floor price tracking and analysis
- NFT fractionalization strategies
- NFT market dynamics
- Collection risk assessment

Guidelines:
- Verify collection authenticity
- Explain liquidation risks for NFT loans
- Track floor prices accurately
- Warn about illiquidity risks
- Consider gas costs for NFT transactions""",
    
    "welcome_message": """Welcome to NFT Finance! 🎨

I help you unlock the financial potential of your NFT holdings.

I can help you with:
• Borrowing against your NFTs
• Understanding NFT floor prices
• Evaluating NFT-backed loans
• Fractionalization opportunities
• Managing NFT loan positions

What would you like to do with your NFTs?""",
    
    "enabled_protocols": ["blur_lending", "nftfi", "bendao", "sudoswap"],
    "enabled_chains": ["ethereum"],
    "enabled_tools": ["nft_lend", "nft_borrow", "check_floor", "analyze_portfolio"],
    
    "risk_config": {
        "max_slippage_bps": 200,
        "max_position_usd": 50000,
        "require_simulation": True,
        "require_2fa_for_transactions": True
    },
    
    "knowledge_base_topics": [
        "NFT lending basics",
        "Floor price mechanics",
        "NFT liquidation risks",
        "Collection analysis",
        "Fractionalization guide"
    ]
}
```

---

## User Assignment

### Auto-Assignment Rules

```python
@dataclass
class AutoAssignRule:
    """Rule for automatic project assignment."""
    
    id: UUID
    project_id: UUID
    
    # Conditions
    condition_type: str          # PORTFOLIO, ACTIVITY, PREFERENCE, ONBOARDING
    condition_params: Dict
    
    # Actions
    priority: int                # Higher = evaluated first
    auto_switch: bool            # Automatically switch user's active project
    
    is_active: bool


# Example rules
AUTO_ASSIGN_RULES = [
    # Assign to Aave if user has Aave positions
    {
        "project": "aave",
        "condition_type": "PORTFOLIO",
        "condition_params": {
            "has_protocol_positions": ["aave"],
            "min_value_usd": 100
        },
        "auto_switch": False
    },
    
    # Assign to Savings if mostly stablecoins
    {
        "project": "savings",
        "condition_type": "PORTFOLIO",
        "condition_params": {
            "token_category": "stablecoin",
            "min_percentage": 70
        },
        "auto_switch": True
    },
    
    # Assign based on onboarding preference
    {
        "project": "earning",
        "condition_type": "ONBOARDING",
        "condition_params": {
            "selected_goal": "maximize_yield"
        },
        "auto_switch": True
    }
]
```

### Manual Assignment

```python
class ProjectAssignmentManager:
    """Manage user-project assignments."""
    
    async def assign_user(
        self,
        user_id: UUID,
        project_id: UUID,
        assigned_by: UUID,        # Admin ID
        reason: str
    ) -> ProjectAssignment:
        """Manually assign user to project."""
        pass
    
    async def auto_assign(self, user_id: UUID) -> List[ProjectAssignment]:
        """Run auto-assignment rules for user."""
        pass
    
    async def set_active_project(
        self,
        user_id: UUID,
        project_id: UUID
    ):
        """Set user's currently active project."""
        pass
```

---

## Project Context Injection

```python
class ProjectContextBuilder:
    """Build context for LLM from project configuration."""
    
    async def build_context(
        self,
        project: Project,
        user_message: str,
        user_context: UserContext
    ) -> ProjectContext:
        """
        Build full context for LLM request.
        
        Components:
        1. System prompt from project
        2. Relevant knowledge chunks (RAG)
        3. User's portfolio context
        4. Available tools
        5. Risk parameters
        """
        
        # Get relevant knowledge
        knowledge_chunks = await self.knowledge_retriever.retrieve(
            knowledge_base_id=project.knowledge_base_id,
            query=user_message,
            top_k=5
        )
        
        # Build system message
        system_message = self._build_system_message(
            project=project,
            knowledge=knowledge_chunks,
            user_context=user_context
        )
        
        # Get available tools
        tools = self._get_project_tools(project)
        
        return ProjectContext(
            system_message=system_message,
            available_tools=tools,
            risk_config=project.risk_config,
            enabled_chains=project.enabled_chains,
            enabled_protocols=project.enabled_protocols
        )
```

---

## Analytics

```python
@dataclass
class ProjectAnalytics:
    """Analytics for a project."""
    
    project_id: UUID
    period: str                  # 24h, 7d, 30d
    
    # Usage
    total_users: int
    active_users: int
    total_sessions: int
    total_messages: int
    
    # Engagement
    avg_session_duration_minutes: float
    avg_messages_per_session: float
    return_rate: float           # Users returning within period
    
    # Satisfaction
    avg_satisfaction_score: float
    helpful_responses_rate: float
    
    # Transactions
    total_transactions: int
    total_volume_usd: Decimal
    success_rate: float
    
    # Knowledge
    knowledge_queries: int
    knowledge_hit_rate: float
    top_queries: List[str]
```
