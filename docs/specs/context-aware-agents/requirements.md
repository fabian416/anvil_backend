# Context-Aware Agent Responses Specification

> **Spec Version:** 2.0  
> **Status:** Draft  
> **Created:** 2026-01-23  
> **Updated:** 2026-01-23  
> **Authors:** @prompt-engineer @backend-engineer @business-analyst @database-architect @tech-lead-orchestrator

---

## Executive Summary

This specification defines a comprehensive **Context-Aware Agent System** that:
1. **Classifies users** based on portfolio state, chat interactions, and activity patterns
2. **Stores user context** in a dedicated `user_context_aware` table
3. **Routes responses** based on user type and behavior
4. **Automates context updates** via Celery background tasks
5. **Integrates with privy-login** for new user initialization

---

## 1. Problem Analysis (First Principles)

### 1.1 Current State

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Request ─────► Authenticated Supervisor                    │
│                              │                                   │
│                              ▼                                   │
│                      ┌──────────────────┐                        │
│                      │  UserDataService │                        │
│                      │  - Wallet        │                        │
│                      │  - Portfolio     │ ◄── Data fetched but   │
│                      │  - Transactions  │     NOT used for       │
│                      └────────┬─────────┘     routing decisions  │
│                               │                                  │
│                               ▼                                  │
│                      ┌──────────────────┐                        │
│                      │  Agent Routing   │ ◄── Generic routing    │
│                      │  (LLM-based)     │     ignores balance    │
│                      └────────┬─────────┘                        │
│                               │                                  │
│                               ▼                                  │
│                      ┌──────────────────┐                        │
│                      │  Agent Response  │ ◄── Same response      │
│                      │  (Generic)       │     regardless of      │
│                      └──────────────────┘     user state         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Identified Issues

| Issue | Impact | Example |
|-------|--------|---------|
| **Generic empty state responses** | Users get irrelevant suggestions | Empty portfolio: "Try swap" (can't swap without tokens) |
| **No balance validation in workflows** | Failed transactions | Swap 1 ETH when user has 0 ETH |
| **Missing onboarding flow** | Poor UX for new users | No guided first-purchase flow |
| **No user behavior tracking** | Can't personalize | Active traders get same response as casual users |
| **No activity classification** | Missed re-engagement | Inactive users not prompted differently |

---

## 2. User Context Model

### 2.1 User Classification Dimensions

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER CONTEXT DIMENSIONS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PORTFOLIO STATE          ACTIVITY LEVEL         USER TYPE       │
│  ┌────────────────┐      ┌────────────────┐    ┌────────────────┐│
│  │ EMPTY    ($0)  │      │ VERY_ACTIVE    │    │ NEW_USER       ││
│  │ STARTER (<$100)│      │ ACTIVE         │    │ CASUAL         ││
│  │ ACTIVE  (<$10k)│      │ WEEKLY_ACTIVE  │    │ TRADER         ││
│  │ WHALE   (>$10k)│      │ MONTHLY_ACTIVE │    │ YIELD_FARMER   ││
│  └────────────────┘      │ INACTIVE       │    │ POWER_USER     ││
│                          │ REACTIVATED    │    └────────────────┘│
│                          └────────────────┘                      │
│                                                                  │
│  EXECUTION HISTORY        INTERACTION STYLE                      │
│  ┌────────────────┐      ┌────────────────┐                     │
│  │ swap_count     │      │ questions_asked│                     │
│  │ buy_count      │      │ shortcuts_used │                     │
│  │ cashout_count  │      │ multi_step_    │                     │
│  │ lending_count  │      │   completed    │                     │
│  │ money_market   │      │ avg_session_   │                     │
│  │   _count       │      │   duration     │                     │
│  └────────────────┘      └────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Database Schema

```sql
-- User Context Aware Table
CREATE TABLE user_context_aware (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Key to chat_users (UUID-based)
    chat_user_id UUID NOT NULL REFERENCES chat_users(id) ON DELETE CASCADE,
    
    -- Also link to legacy users table if exists
    legacy_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- ═══════════════════════════════════════════════════════════════
    -- PORTFOLIO STATE
    -- ═══════════════════════════════════════════════════════════════
    portfolio_state VARCHAR(20) DEFAULT 'empty',  -- empty | starter | active | whale
    total_balance_usd DECIMAL(18, 2) DEFAULT 0.00,
    token_count INTEGER DEFAULT 0,
    primary_chain VARCHAR(50),  -- ethereum | polygon | arbitrum | etc.
    
    -- ═══════════════════════════════════════════════════════════════
    -- ACTIVITY LEVEL
    -- ═══════════════════════════════════════════════════════════════
    activity_level VARCHAR(20) DEFAULT 'new',  -- very_active | active | weekly_active | monthly_active | inactive | reactivated | new
    last_active_at TIMESTAMP WITH TIME ZONE,
    first_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Activity metrics (rolling 30-day)
    chat_sessions_30d INTEGER DEFAULT 0,
    messages_sent_30d INTEGER DEFAULT 0,
    
    -- ═══════════════════════════════════════════════════════════════
    -- USER TYPE (Inferred from behavior)
    -- ═══════════════════════════════════════════════════════════════
    user_type VARCHAR(30) DEFAULT 'new_user',  -- new_user | casual | trader | yield_farmer | power_user
    
    -- ═══════════════════════════════════════════════════════════════
    -- EXECUTION HISTORY (Lifetime counts)
    -- ═══════════════════════════════════════════════════════════════
    swap_count INTEGER DEFAULT 0,
    buy_count INTEGER DEFAULT 0,
    cashout_count INTEGER DEFAULT 0,
    lending_count INTEGER DEFAULT 0,
    money_market_count INTEGER DEFAULT 0,
    transfer_count INTEGER DEFAULT 0,
    
    -- Execution success rate
    execution_success_rate DECIMAL(5, 2) DEFAULT 0.00,
    total_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    
    -- ═══════════════════════════════════════════════════════════════
    -- CHAT INTERACTION PATTERNS
    -- ═══════════════════════════════════════════════════════════════
    total_conversations INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    shortcuts_used_count INTEGER DEFAULT 0,
    multi_step_completed_count INTEGER DEFAULT 0,
    avg_messages_per_session DECIMAL(5, 2) DEFAULT 0.00,
    
    -- Language preference (detected from interactions)
    detected_language VARCHAR(5) DEFAULT 'en',
    language_history JSONB DEFAULT '[]',  -- ["en", "es", "pt"] - for multilingual users
    
    -- ═══════════════════════════════════════════════════════════════
    -- WALLET DATA
    -- ═══════════════════════════════════════════════════════════════
    wallet_count INTEGER DEFAULT 0,
    has_connected_wallet BOOLEAN DEFAULT FALSE,
    primary_wallet_address VARCHAR(255),
    wallet_provider VARCHAR(50),  -- privy | metamask | walletconnect | etc.
    
    -- ═══════════════════════════════════════════════════════════════
    -- AGENT INTERACTION STATS
    -- ═══════════════════════════════════════════════════════════════
    most_used_agents JSONB DEFAULT '[]',  -- ["swap_workflow", "portfolio", "hunter_ai"]
    agent_usage_counts JSONB DEFAULT '{}',  -- {"swap_workflow": 15, "portfolio": 10}
    
    -- ═══════════════════════════════════════════════════════════════
    -- PROCESSING METADATA
    -- ═══════════════════════════════════════════════════════════════
    context_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    next_update_eligible_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    update_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- ═══════════════════════════════════════════════════════════════
    -- CONSTRAINTS & INDEXES
    -- ═══════════════════════════════════════════════════════════════
    CONSTRAINT valid_portfolio_state CHECK (portfolio_state IN ('empty', 'starter', 'active', 'whale')),
    CONSTRAINT valid_activity_level CHECK (activity_level IN ('very_active', 'active', 'weekly_active', 'monthly_active', 'inactive', 'reactivated', 'new')),
    CONSTRAINT valid_user_type CHECK (user_type IN ('new_user', 'casual', 'trader', 'yield_farmer', 'power_user'))
);

-- Indexes for efficient querying
CREATE INDEX idx_user_context_chat_user ON user_context_aware(chat_user_id);
CREATE INDEX idx_user_context_legacy_user ON user_context_aware(legacy_user_id) WHERE legacy_user_id IS NOT NULL;
CREATE INDEX idx_user_context_portfolio_state ON user_context_aware(portfolio_state);
CREATE INDEX idx_user_context_activity_level ON user_context_aware(activity_level);
CREATE INDEX idx_user_context_user_type ON user_context_aware(user_type);
CREATE INDEX idx_user_context_next_update ON user_context_aware(next_update_eligible_at) WHERE next_update_eligible_at <= CURRENT_TIMESTAMP;
CREATE INDEX idx_user_context_updated_at ON user_context_aware(context_updated_at);

-- Unique constraint: one context per chat user
CREATE UNIQUE INDEX idx_user_context_unique_chat_user ON user_context_aware(chat_user_id);
```

### 2.3 Classification Rules

#### Portfolio State Classification

```python
class PortfolioState(Enum):
    EMPTY = "empty"       # $0 total value
    STARTER = "starter"   # $0.01 - $99.99
    ACTIVE = "active"     # $100 - $9,999.99
    WHALE = "whale"       # $10,000+
    
    @classmethod
    def from_balance(cls, balance_usd: Decimal) -> "PortfolioState":
        if balance_usd <= 0:
            return cls.EMPTY
        if balance_usd < 100:
            return cls.STARTER
        if balance_usd < 10000:
            return cls.ACTIVE
        return cls.WHALE
```

#### Activity Level Classification

```python
class ActivityLevel(Enum):
    VERY_ACTIVE = "very_active"      # 5+ sessions in last 7 days
    ACTIVE = "active"                # 2+ sessions in last 7 days
    WEEKLY_ACTIVE = "weekly_active"  # 1+ session in last 7 days
    MONTHLY_ACTIVE = "monthly_active"# 1+ session in last 30 days (not weekly)
    INACTIVE = "inactive"            # No activity in 30+ days
    REACTIVATED = "reactivated"      # Was inactive, now active again
    NEW = "new"                      # < 7 days since registration
    
    @classmethod
    def calculate(
        cls,
        days_since_registration: int,
        sessions_7d: int,
        sessions_30d: int,
        was_inactive: bool,
    ) -> "ActivityLevel":
        if days_since_registration < 7:
            return cls.NEW
        
        if was_inactive and sessions_7d > 0:
            return cls.REACTIVATED
        
        if sessions_7d >= 5:
            return cls.VERY_ACTIVE
        if sessions_7d >= 2:
            return cls.ACTIVE
        if sessions_7d >= 1:
            return cls.WEEKLY_ACTIVE
        if sessions_30d >= 1:
            return cls.MONTHLY_ACTIVE
        return cls.INACTIVE
```

#### User Type Classification

```python
class UserType(Enum):
    NEW_USER = "new_user"         # < 5 total interactions
    CASUAL = "casual"             # Uses chat for questions, rarely executes
    TRADER = "trader"             # Primarily swaps and buys
    YIELD_FARMER = "yield_farmer" # Focuses on lending/money market
    POWER_USER = "power_user"     # High activity across all categories
    
    @classmethod
    def calculate(cls, context: "UserContextAware") -> "UserType":
        total_interactions = context.total_messages
        total_executions = context.total_executions
        
        # New users
        if total_interactions < 5:
            return cls.NEW_USER
        
        # Power users: high activity across multiple categories
        execution_types = sum([
            1 if context.swap_count > 0 else 0,
            1 if context.buy_count > 0 else 0,
            1 if context.lending_count > 0 else 0,
            1 if context.money_market_count > 0 else 0,
        ])
        
        if execution_types >= 3 and total_executions >= 10:
            return cls.POWER_USER
        
        # Yield farmers: primarily lending/money market
        defi_executions = context.lending_count + context.money_market_count
        trading_executions = context.swap_count + context.buy_count
        
        if defi_executions > trading_executions and defi_executions >= 3:
            return cls.YIELD_FARMER
        
        # Traders: primarily swaps/buys
        if trading_executions >= 3:
            return cls.TRADER
        
        # Default: casual user
        return cls.CASUAL
```

---

## 3. Proposed Architecture

### 3.1 Enhanced Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROPOSED ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Request ─────► Authenticated Supervisor                    │
│                              │                                   │
│                              ▼                                   │
│                      ┌──────────────────┐                        │
│                      │ UserContextAware │ ◄── NEW: Pre-computed  │
│                      │ (from table)     │     user context       │
│                      └────────┬─────────┘                        │
│                               │                                  │
│              ┌────────────────┼────────────────┐                 │
│              ▼                ▼                ▼                 │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│    │ Portfolio    │  │ Activity     │  │ User Type    │         │
│    │ State        │  │ Level        │  │              │         │
│    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│           │                 │                 │                  │
│           └─────────────────┼─────────────────┘                  │
│                             ▼                                    │
│                      ┌──────────────────┐                        │
│                      │ Context-Aware    │ ◄── State-based        │
│                      │ Routing & Prompts│     prompt selection   │
│                      └────────┬─────────┘                        │
│                               │                                  │
│              ┌────────────────┼────────────────┐                 │
│              ▼                ▼                ▼                 │
│       ┌───────────┐    ┌───────────┐    ┌───────────┐           │
│       │ Onboarding│    │ Standard  │    │ Power User│           │
│       │ Response  │    │ Response  │    │ Response  │           │
│       │ (EMPTY)   │    │ (ACTIVE)  │    │ (WHALE)   │           │
│       └───────────┘    └───────────┘    └───────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                       DATA FLOW                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PRIVY LOGIN (New User)                                       │
│     ┌──────────────┐                                             │
│     │ privy-login  │ ──────► INSERT user_context_aware           │
│     │ endpoint     │         (default values, user_type='new')   │
│     └──────────────┘                                             │
│                                                                  │
│  2. CELERY TASK (Every 10 min, max 100 users)                    │
│     ┌──────────────┐                                             │
│     │ update_user_ │ ──────► SELECT users WHERE                  │
│     │ context_task │         next_update_eligible_at <= NOW()    │
│     └──────┬───────┘         LIMIT 100                           │
│            │                                                     │
│            ▼                                                     │
│     ┌──────────────┐                                             │
│     │ For each user│ ──────► Aggregate from:                     │
│     │              │         - chat_messages (counts)            │
│     │              │         - chat_conversations (sessions)     │
│     │              │         - wallets (balances)                │
│     │              │         - transactions (executions)         │
│     └──────┬───────┘                                             │
│            │                                                     │
│            ▼                                                     │
│     ┌──────────────┐                                             │
│     │ Calculate    │ ──────► portfolio_state                     │
│     │ classifications       activity_level                       │
│     │              │         user_type                           │
│     └──────┬───────┘                                             │
│            │                                                     │
│            ▼                                                     │
│     ┌──────────────┐                                             │
│     │ UPDATE       │ ──────► SET next_update_eligible_at =       │
│     │ user_context │         NOW() + INTERVAL '1 hour'           │
│     └──────────────┘                                             │
│                                                                  │
│  3. CHAT REQUEST (Read context)                                  │
│     ┌──────────────┐                                             │
│     │ Supervisor   │ ──────► SELECT * FROM user_context_aware    │
│     │              │         WHERE chat_user_id = ?              │
│     └──────────────┘                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Response Templates by Context

### 4.1 Portfolio State Templates

#### EMPTY State (No Holdings)

```python
EMPTY_STATE_RESPONSES = {
    "portfolio": {
        "message": """**Welcome to Anvil! 🚀**

Your portfolio is ready to grow.

**Start here:**
→ "buy 100 USD of ETH" - Purchase your first crypto
→ "what is ETH" - Learn about Ethereum first

Once you have crypto, you can swap, earn yield, and more!""",
        "suggested_actions": ["buy", "learn"],
    },
    "swap": {
        "message": """**You need crypto to swap!**

Get started:
→ "buy 100 USD of ETH" - Then you can swap to other tokens""",
        "block_workflow": True,
    },
    "lending": {
        "message": """**You need crypto to earn yield!**

Get started:
→ "buy 100 USD of USDC" - Then earn 5-10% APY on stablecoins""",
        "block_workflow": True,
    },
}
```

#### STARTER State (< $100)

```python
STARTER_STATE_RESPONSES = {
    "portfolio": {
        "enhance_prompt": """
⚠️ USER IS NEW (< $100 portfolio):
- Suggest small, safe operations
- Warn about gas costs relative to balance
- Prioritize education
- Suggest building up balance first for most operations
""",
    },
    "swap": {
        "pre_check": "warn_gas_costs",  # Gas might be significant % of trade
        "suggestion": "Consider amounts that make gas costs worthwhile",
    },
}
```

#### ACTIVE State ($100 - $10k)

```python
ACTIVE_STATE_RESPONSES = {
    "portfolio": {
        "enhance_prompt": """
✅ USER HAS ACTIVE PORTFOLIO:
- Full feature access
- Provide optimization suggestions
- Consider diversification recommendations
- Suggest yield opportunities based on holdings
""",
    },
}
```

#### WHALE State (> $10k)

```python
WHALE_STATE_RESPONSES = {
    "portfolio": {
        "enhance_prompt": """
✅ HIGH-VALUE USER (> $10k):
- Emphasize slippage protection for large trades
- Suggest gas optimization strategies
- Recommend advanced DeFi strategies
- Consider cross-chain opportunities
- Mention tax implications for large trades
""",
    },
}
```

### 4.2 Activity Level Templates

```python
ACTIVITY_LEVEL_PROMPTS = {
    ActivityLevel.INACTIVE: """
👋 RETURNING USER (Inactive > 30 days):
- Welcome them back warmly
- Highlight what's new since they left
- Offer to catch them up on their portfolio
- Don't overwhelm with options
""",
    ActivityLevel.REACTIVATED: """
🎉 REACTIVATED USER:
- Acknowledge their return
- Show any portfolio changes while away
- Ease them back in gently
""",
    ActivityLevel.VERY_ACTIVE: """
⚡ POWER USER (Very Active):
- Skip basic explanations
- Get straight to the point
- Offer advanced options
- Assume familiarity with DeFi concepts
""",
}
```

### 4.3 User Type Templates

```python
USER_TYPE_PROMPTS = {
    UserType.TRADER: """
📈 TRADER USER:
- Emphasize swap efficiency and gas
- Show price impacts
- Highlight arbitrage opportunities
- Quick execution is priority
""",
    UserType.YIELD_FARMER: """
🌾 YIELD FARMER:
- Prioritize APY comparisons
- Highlight new yield opportunities
- Warn about impermanent loss
- Track lending positions
""",
    UserType.POWER_USER: """
🚀 POWER USER:
- Full feature access, minimal hand-holding
- Show advanced analytics
- Suggest cross-protocol strategies
- Multi-step workflow optimization
""",
}
```

---

## 5. Celery Task Implementation

### 5.1 Task Configuration

```python
# src/app/infrastructure/celery/tasks/user_context_tasks.py

from celery import shared_task
from celery.schedules import crontab
from datetime import datetime, timedelta, UTC

# Schedule: Every 10 minutes
SCHEDULE = {
    "update-user-context": {
        "task": "update_user_context",
        "schedule": crontab(minute="*/10"),
    },
}

# Task configuration
MAX_USERS_PER_RUN = 100
UPDATE_COOLDOWN_HOURS = 1
```

### 5.2 Task Implementation

```python
@celery_app.task(name="update_user_context")
def update_user_context():
    """
    Update user context for users eligible for processing.
    
    Runs every 10 minutes, processes max 100 users per run.
    Skips users updated within the last hour.
    """
    async def runner(container):
        from app.application.chat.services.user_context_service import UserContextService
        
        service = await container.get(UserContextService)
        
        # Get eligible users (not updated in last hour)
        users = await service.get_users_for_update(
            limit=MAX_USERS_PER_RUN,
            cooldown_hours=UPDATE_COOLDOWN_HOURS,
        )
        
        logger.info(f"🔄 Processing {len(users)} users for context update")
        
        updated_count = 0
        for user in users:
            try:
                await service.update_user_context(user.chat_user_id)
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update context for user {user.chat_user_id}: {e}")
        
        logger.info(f"✅ Updated context for {updated_count}/{len(users)} users")
    
    asyncio.run(_run_task(runner))
```

### 5.3 Context Update Service

```python
# src/app/application/chat/services/user_context_service.py

class UserContextService:
    """Service for managing user context awareness."""
    
    def __init__(
        self,
        context_repo: UserContextRepository,
        chat_repo: ChatRepository,
        wallet_repo: WalletRepository,
        tx_repo: TransactionRepository,
    ):
        self._context_repo = context_repo
        self._chat_repo = chat_repo
        self._wallet_repo = wallet_repo
        self._tx_repo = tx_repo
    
    async def get_users_for_update(
        self,
        limit: int = 100,
        cooldown_hours: int = 1,
    ) -> list[UserContextAware]:
        """Get users eligible for context update."""
        cutoff = datetime.now(UTC) - timedelta(hours=cooldown_hours)
        return await self._context_repo.get_eligible_for_update(
            before=cutoff,
            limit=limit,
        )
    
    async def update_user_context(self, chat_user_id: UUID) -> UserContextAware:
        """
        Update context for a single user.
        
        Aggregates data from:
        - chat_messages (interaction counts)
        - chat_conversations (session counts)
        - wallets (balance, chain)
        - transactions (execution counts)
        """
        # Get existing context or create new
        context = await self._context_repo.get_by_chat_user_id(chat_user_id)
        if not context:
            context = UserContextAware(chat_user_id=chat_user_id)
        
        # Aggregate chat interactions
        chat_stats = await self._chat_repo.get_user_stats(chat_user_id)
        context.total_conversations = chat_stats.conversation_count
        context.total_messages = chat_stats.message_count
        context.messages_sent_30d = chat_stats.messages_30d
        context.chat_sessions_30d = chat_stats.sessions_30d
        context.shortcuts_used_count = chat_stats.shortcuts_used
        context.multi_step_completed_count = chat_stats.multi_step_completed
        context.avg_messages_per_session = chat_stats.avg_messages_per_session
        context.most_used_agents = chat_stats.agent_usage_top_5
        context.agent_usage_counts = chat_stats.agent_usage_counts
        context.detected_language = chat_stats.most_common_language
        
        # Aggregate wallet data
        wallets = await self._wallet_repo.get_by_user_id(chat_user_id)
        context.wallet_count = len(wallets)
        context.has_connected_wallet = len(wallets) > 0
        
        if wallets:
            primary = wallets[0]
            context.primary_wallet_address = primary.address
            context.wallet_provider = primary.provider
            context.primary_chain = primary.chain_type
            
            # Get total balance across wallets
            total_balance = await self._wallet_repo.get_total_balance_usd(chat_user_id)
            context.total_balance_usd = total_balance
            context.token_count = await self._wallet_repo.get_token_count(chat_user_id)
        
        # Aggregate execution data
        exec_stats = await self._tx_repo.get_execution_stats(chat_user_id)
        context.swap_count = exec_stats.swap_count
        context.buy_count = exec_stats.buy_count
        context.cashout_count = exec_stats.cashout_count
        context.lending_count = exec_stats.lending_count
        context.money_market_count = exec_stats.money_market_count
        context.transfer_count = exec_stats.transfer_count
        context.total_executions = exec_stats.total
        context.failed_executions = exec_stats.failed
        context.execution_success_rate = exec_stats.success_rate
        
        # Calculate classifications
        context.portfolio_state = PortfolioState.from_balance(context.total_balance_usd).value
        
        days_since_registration = (datetime.now(UTC) - context.first_active_at).days
        was_inactive = context.activity_level == ActivityLevel.INACTIVE.value
        context.activity_level = ActivityLevel.calculate(
            days_since_registration=days_since_registration,
            sessions_7d=chat_stats.sessions_7d,
            sessions_30d=context.chat_sessions_30d,
            was_inactive=was_inactive,
        ).value
        
        context.user_type = UserType.calculate(context).value
        
        # Update timestamps
        context.last_active_at = chat_stats.last_message_at
        context.context_updated_at = datetime.now(UTC)
        context.next_update_eligible_at = datetime.now(UTC) + timedelta(hours=1)
        context.update_count += 1
        
        # Save
        await self._context_repo.save(context)
        
        return context
    
    async def create_for_new_user(
        self,
        chat_user_id: UUID,
        legacy_user_id: int | None = None,
        wallet_address: str | None = None,
        wallet_provider: str | None = None,
    ) -> UserContextAware:
        """
        Create context entry for a new user (called from privy-login).
        """
        context = UserContextAware(
            chat_user_id=chat_user_id,
            legacy_user_id=legacy_user_id,
            portfolio_state=PortfolioState.EMPTY.value,
            activity_level=ActivityLevel.NEW.value,
            user_type=UserType.NEW_USER.value,
            has_connected_wallet=wallet_address is not None,
            primary_wallet_address=wallet_address,
            wallet_provider=wallet_provider,
            wallet_count=1 if wallet_address else 0,
            first_active_at=datetime.now(UTC),
            last_active_at=datetime.now(UTC),
            context_updated_at=datetime.now(UTC),
            next_update_eligible_at=datetime.now(UTC) + timedelta(hours=1),
        )
        
        await self._context_repo.save(context)
        return context
```

---

## 6. Privy Login Integration

### 6.1 Updated Privy Login Flow

```python
# src/app/application/commands/auth/privy_login.py

class PrivyLogin:
    """Enhanced privy login with context creation."""
    
    def __init__(
        self,
        user_repo: UserRepository,
        session_service: SessionService,
        chat_user_repo: ChatUserRepository,
        context_service: UserContextService,  # NEW
    ):
        self._user_repo = user_repo
        self._session_service = session_service
        self._chat_user_repo = chat_user_repo
        self._context_service = context_service  # NEW
    
    async def execute(self, request: PrivyLoginRequest) -> PrivyLoginResponse:
        # Existing logic: create/get user...
        user = await self._get_or_create_user(request)
        
        # Get or create chat_user (UUID-based)
        chat_user = await self._chat_user_repo.get_or_create(
            privy_id=request.privy_user_id,
            email=request.email,
        )
        
        # NEW: Create context entry if it doesn't exist
        existing_context = await self._context_service.get_by_chat_user_id(chat_user.id)
        if not existing_context:
            await self._context_service.create_for_new_user(
                chat_user_id=chat_user.id,
                legacy_user_id=user.id,
                wallet_address=request.wallet_address,
                wallet_provider=request.auth_provider,
            )
            logger.info(f"✅ Created user_context_aware entry for new user {chat_user.id}")
        
        # Existing logic: create session, return tokens...
        return PrivyLoginResponse(...)
```

---

## 7. Implementation Plan

### Phase 1: Database & Domain (2-3 days)

| Task | File | Priority |
|------|------|----------|
| Create migration for `user_context_aware` table | `alembic/versions/xxx_add_user_context_aware.py` | P0 |
| Create domain entity `UserContextAware` | `src/app/domain/chat/entities/user_context_aware.py` | P0 |
| Create enums: `PortfolioState`, `ActivityLevel`, `UserType` | `src/app/domain/chat/enums/` | P0 |
| Create repository port | `src/app/domain/chat/ports/user_context_repository.py` | P0 |
| Create SQLAlchemy mapping | `src/app/infrastructure/persistence_sqla/mappings/user_context.py` | P0 |
| Create repository adapter | `src/app/infrastructure/adapters/user_context_repository_sqla.py` | P0 |

### Phase 2: Context Service (2-3 days)

| Task | File | Priority |
|------|------|----------|
| Create `UserContextService` | `src/app/application/chat/services/user_context_service.py` | P0 |
| Add chat stats aggregation to repository | `src/app/infrastructure/adapters/chat_repository_sqla.py` | P0 |
| Add execution stats aggregation | `src/app/infrastructure/adapters/transaction_repository_sqla.py` | P1 |
| Register in IoC container | `src/app/setup/ioc/chat.py` | P0 |

### Phase 3: Celery Task (1-2 days)

| Task | File | Priority |
|------|------|----------|
| Create Celery task `update_user_context` | `src/app/infrastructure/celery/tasks/user_context_tasks.py` | P0 |
| Add to beat schedule | `src/app/infrastructure/celery/tasks.py` | P0 |
| Add monitoring/logging | Task implementation | P1 |

### Phase 4: Privy Login Integration (1 day)

| Task | File | Priority |
|------|------|----------|
| Update `PrivyLogin` to create context | `src/app/application/commands/auth/privy_login.py` | P0 |
| Update IoC to inject `UserContextService` | `src/app/setup/ioc/application.py` | P0 |

### Phase 5: Supervisor Integration (2-3 days)

| Task | File | Priority |
|------|------|----------|
| Load context in supervisor | `src/app/domain/services/agent_squad/authenticated_supervisor.py` | P0 |
| Add context-aware prompt building | `authenticated_supervisor.py` | P1 |
| Add workflow pre-validation | `authenticated_supervisor.py` | P1 |
| Update agent response templates | `src/app/infrastructure/adapters/agent_squad/agents/` | P2 |

---

## 8. Trade-off Analysis

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Real-time calculation** | Always fresh | Slow, expensive on every request | ❌ Rejected |
| **Cached table (selected)** | Fast reads, batch updates | Slightly stale (1 hour max) | ✅ Selected |
| **Redis cache** | Very fast | Adds complexity, sync issues | ❌ Rejected |

---

## 9. Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Empty user → first purchase rate | Unknown | > 30% |
| Failed workflow starts (insufficient balance) | ~5% | < 1% |
| Inactive user reactivation rate | Unknown | > 15% |
| Average session duration (new users) | Unknown | +20% |

---

## 10. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Celery task overload | Slow updates | Limit to 100 users/run |
| Classification errors | Wrong UX | Fallback to generic |
| Stale data | Outdated context | Max 1-hour staleness |
| Table bloat | Slow queries | Proper indexing, cleanup |

---

## Appendix A: SQL Query Examples

### Get Users for Update

```sql
SELECT * FROM user_context_aware
WHERE next_update_eligible_at <= CURRENT_TIMESTAMP
ORDER BY context_updated_at ASC
LIMIT 100;
```

### Aggregate Chat Stats

```sql
SELECT
    user_id,
    COUNT(DISTINCT conversation_id) as conversation_count,
    COUNT(*) as message_count,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as messages_30d,
    COUNT(DISTINCT conversation_id) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as sessions_7d,
    MAX(created_at) as last_message_at,
    (metadata->>'shortcut')::boolean as shortcuts_used
FROM chat_messages
WHERE user_id = $1
GROUP BY user_id;
```

### Get Execution Stats

```sql
SELECT
    user_id,
    COUNT(*) FILTER (WHERE action_type = 'swap') as swap_count,
    COUNT(*) FILTER (WHERE action_type = 'buy') as buy_count,
    COUNT(*) FILTER (WHERE action_type = 'cashout') as cashout_count,
    COUNT(*) FILTER (WHERE action_type = 'lending') as lending_count,
    COUNT(*) FILTER (WHERE action_type = 'money_market') as money_market_count,
    COUNT(*) FILTER (WHERE action_type = 'transfer') as transfer_count,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'failed') as failed
FROM transactions
WHERE user_id = $1
GROUP BY user_id;
```

---

## Appendix B: Implementation Status

**Last Updated:** 2026-01-24 (Login handlers updated)

### ✅ Phase 1: Database & Domain (COMPLETE)

| Component | Status | File |
|-----------|--------|------|
| PortfolioState Enum | ✅ Done | `src/app/domain/chat/enums/portfolio_state.py` |
| ActivityLevel Enum | ✅ Done | `src/app/domain/chat/enums/activity_level.py` |
| UserType Enum | ✅ Done | `src/app/domain/chat/enums/user_type.py` |
| UserContextAware Entity | ✅ Done | `src/app/domain/chat/entities/user_context_aware.py` |
| UserContextRepository Port | ✅ Done | `src/app/domain/chat/ports/user_context_repository.py` |
| UserContextRepositorySqla | ✅ Done | `src/app/infrastructure/adapters/user_context_repository_sqla.py` |
| SQLAlchemy Mapping | ✅ Done | `src/app/infrastructure/persistence_sqla/mappings/user_context.py` |
| Alembic Migration | ✅ Done | `alembic/versions/2026_01_23_0001-add_user_context_aware_table.py` |
| IoC Registration | ✅ Done | `src/app/setup/ioc/chat.py` |

### ✅ Phase 2: Context Service (COMPLETE)

| Component | Status | File |
|-----------|--------|------|
| UserContextService | ✅ Done | `src/app/application/chat/services/user_context_service.py` |
| ChatStats aggregation | ✅ Done | `src/app/infrastructure/adapters/chat_repository_sqla.py` |
| ExecutionStats aggregation | ✅ Done | `src/app/infrastructure/adapters/chat_repository_sqla.py` |

### ✅ Phase 3: Celery Task (COMPLETE)

| Component | Status | File |
|-----------|--------|------|
| update_user_context task | ✅ Done | `src/app/infrastructure/celery/tasks/user_context_tasks.py` |
| create_missing_user_contexts task | ✅ Done | `src/app/infrastructure/celery/tasks/user_context_tasks.py` |
| user_context_analytics task | ✅ Done | `src/app/infrastructure/celery/tasks/user_context_tasks.py` |
| Beat schedule (10 min) | ✅ Done | `src/app/infrastructure/celery/tasks.py` |

### ✅ Phase 4: Login Integration (COMPLETE)

| Component | Status | File |
|-----------|--------|------|
| PrivyLogin integration | ✅ Done | `src/app/application/commands/auth/privy_login.py` |
| _ensure_user_context method | ✅ Done | `src/app/application/commands/auth/privy_login.py` |
| LogInHandler integration | ✅ Done | `src/app/infrastructure/auth/handlers/log_in.py` |
| _ensure_user_context method | ✅ Done | `src/app/infrastructure/auth/handlers/log_in.py` |

### ✅ Phase 5: Supervisor Integration (COMPLETE)

| Component | Status | File |
|-----------|--------|------|
| set_context_aware method | ✅ Done | `src/app/domain/services/agent_squad/authenticated_supervisor.py` |
| Enhanced system prompt | ✅ Done | `src/app/domain/services/agent_squad/authenticated_supervisor.py` |
| can_execute_workflow method | ✅ Done | `src/app/domain/services/agent_squad/authenticated_supervisor.py` |
| get_onboarding_suggestion method | ✅ Done | `src/app/domain/services/agent_squad/authenticated_supervisor.py` |

### 🔄 Future Enhancements

| Enhancement | Priority | Status |
|------------|----------|--------|
| Wire up context in conversations_router | High | ✅ Done (Phase 5) |
| Create missing contexts in Celery | High | ✅ Done |
| Add wallet balance aggregation | Medium | Pending |
| Add response template system | Medium | Pending |
| Analytics dashboard | Low | Pending |

---

## Appendix C: Future Enhancements Implementation Plan

### Enhancement 1: Wallet Balance Aggregation (Medium Priority)

**Goal**: Query real wallet balances to update `portfolio_state` with actual USD values instead of defaults.

#### 1.1 Technical Design

```
┌─────────────────────────────────────────────────────────────────┐
│                  WALLET BALANCE AGGREGATION                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Data Sources:                                                   │
│  ┌────────────────┐     ┌────────────────┐                       │
│  │ wallets table  │     │ External APIs  │                       │
│  │ (DB)           │     │ (DeBank/Zerion)│                       │
│  └───────┬────────┘     └───────┬────────┘                       │
│          │                      │                                │
│          ▼                      ▼                                │
│  ┌─────────────────────────────────────────┐                     │
│  │         WalletBalanceService            │                     │
│  │  - get_total_balance(user_id) -> USD    │                     │
│  │  - get_chain_breakdown(user_id)         │                     │
│  │  - get_token_holdings(user_id)          │                     │
│  └───────────────────┬─────────────────────┘                     │
│                      │                                           │
│                      ▼                                           │
│  ┌─────────────────────────────────────────┐                     │
│  │         UserContextService              │                     │
│  │  - _aggregate_wallet_stats()            │                     │
│  │  - portfolio_state = from_balance(usd)  │                     │
│  └─────────────────────────────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 1.2 Implementation Steps

| Step | Task | File | Effort |
|------|------|------|--------|
| 1.1 | Create `WalletBalancePort` interface | `src/app/domain/chat/ports/wallet_balance.py` | S |
| 1.2 | Implement DB-based adapter | `src/app/infrastructure/adapters/wallet_balance_db.py` | M |
| 1.3 | (Optional) Implement DeBank/Zerion adapter | `src/app/infrastructure/adapters/wallet_balance_external.py` | L |
| 1.4 | Update `UserContextService._aggregate_wallet_stats()` | `src/app/application/chat/services/user_context_service.py` | S |
| 1.5 | Add `wallet_total_usd` column to `user_context_aware` | Migration | S |
| 1.6 | Update Celery task to call wallet aggregation | `src/app/infrastructure/celery/tasks/user_context_tasks.py` | S |

#### 1.3 Database Schema Changes

```sql
-- Add to user_context_aware table
ALTER TABLE user_context_aware 
ADD COLUMN wallet_total_usd NUMERIC(20,2) DEFAULT 0,
ADD COLUMN wallet_chain_breakdown JSONB DEFAULT '{}',
ADD COLUMN wallet_last_sync_at TIMESTAMP WITH TIME ZONE;
```

#### 1.4 Port Interface

```python
# src/app/domain/chat/ports/wallet_balance.py
from typing import Protocol
from uuid import UUID
from decimal import Decimal

class WalletBalancePort(Protocol):
    async def get_total_balance_usd(self, wallet_address: str) -> Decimal:
        """Get total USD value across all chains."""
        ...
    
    async def get_chain_breakdown(self, wallet_address: str) -> dict[str, Decimal]:
        """Get balance breakdown by chain."""
        ...
```

---

### Enhancement 2: Response Template System (Medium Priority)

**Goal**: Pre-defined response templates for different user states to ensure consistent, optimized messaging.

#### 2.1 Technical Design

```
┌─────────────────────────────────────────────────────────────────┐
│                   RESPONSE TEMPLATE SYSTEM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Templates by Context:                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │   EMPTY     │  │   STARTER   │  │   WHALE     │               │
│  │  Templates  │  │  Templates  │  │  Templates  │               │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘               │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────────────────────────────────────┐                 │
│  │         ResponseTemplateService             │                 │
│  │  - get_template(state, action, lang)        │                 │
│  │  - render_template(template, context)       │                 │
│  │  - get_suggested_actions(state)             │                 │
│  └─────────────────────────────────────────────┘                 │
│                      │                                           │
│                      ▼                                           │
│  ┌─────────────────────────────────────────────┐                 │
│  │         Agent Response Generation           │                 │
│  │  - Uses templates instead of LLM for        │                 │
│  │    common scenarios (empty portfolio, etc.) │                 │
│  └─────────────────────────────────────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.2 Implementation Steps

| Step | Task | File | Effort |
|------|------|------|--------|
| 2.1 | Define `ResponseTemplate` entity | `src/app/domain/chat/entities/response_template.py` | S |
| 2.2 | Create template YAML/JSON files | `src/app/infrastructure/templates/` | M |
| 2.3 | Implement `ResponseTemplateService` | `src/app/application/chat/services/response_template_service.py` | M |
| 2.4 | Update agents to use templates | `src/app/infrastructure/adapters/agent_squad/agents/*.py` | M |
| 2.5 | Add multi-language support | Template files + service | M |

#### 2.3 Template Structure

```yaml
# src/app/infrastructure/templates/portfolio_responses.yaml
portfolio:
  empty:
    en:
      message: |
        **Welcome to Anvil! 🚀**
        
        Your portfolio is ready to grow.
        
        **Start here:**
        → "buy 100 USD of ETH" - Purchase your first crypto
        → "what is ETH" - Learn about Ethereum first
      suggested_actions: ["buy", "learn"]
      block_swap: true
    
    es:
      message: |
        **¡Bienvenido a Anvil! 🚀**
        
        Tu portafolio está listo para crecer.
        
        **Empieza aquí:**
        → "comprar 100 USD de ETH" - Compra tu primera crypto
      suggested_actions: ["buy", "learn"]
      block_swap: true
  
  starter:
    en:
      message: |
        **Your Portfolio: ${total_usd}**
        
        You're off to a great start! Here's what you can do:
        → Swap tokens to diversify
        → Earn yield on stablecoins (5-10% APY)
      suggested_actions: ["swap", "earn", "buy_more"]
```

#### 2.4 Service Interface

```python
# src/app/application/chat/services/response_template_service.py
class ResponseTemplateService:
    def __init__(self, templates_path: str):
        self._templates = self._load_templates(templates_path)
    
    def get_response(
        self,
        portfolio_state: PortfolioState,
        action: str,  # "portfolio", "swap", "lending", etc.
        language: str = "en",
        context: dict | None = None,  # For variable substitution
    ) -> TemplateResponse:
        """Get pre-defined response for user state + action."""
        ...
    
    def should_use_template(
        self,
        portfolio_state: PortfolioState,
        action: str,
    ) -> bool:
        """Check if template exists for this combination."""
        ...
```

---

### Enhancement 3: Analytics Dashboard (Low Priority)

**Goal**: Visualize user distribution across classifications for business insights.

#### 3.1 Technical Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYTICS DASHBOARD                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Data Flow:                                                      │
│  ┌────────────────┐     ┌────────────────┐                       │
│  │ user_context_  │────▶│  Analytics     │                       │
│  │ aware table    │     │  Aggregation   │                       │
│  └────────────────┘     │  (Celery)      │                       │
│                         └───────┬────────┘                       │
│                                 │                                │
│                                 ▼                                │
│                         ┌────────────────┐                       │
│                         │ analytics_     │                       │
│                         │ snapshots      │                       │
│                         │ table          │                       │
│                         └───────┬────────┘                       │
│                                 │                                │
│                                 ▼                                │
│  ┌─────────────────────────────────────────────┐                 │
│  │           REST API Endpoints                │                 │
│  │  GET /api/v1/admin/analytics/users          │                 │
│  │  GET /api/v1/admin/analytics/trends         │                 │
│  │  GET /api/v1/admin/analytics/cohorts        │                 │
│  └─────────────────────────────────────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.2 Implementation Steps

| Step | Task | File | Effort |
|------|------|------|--------|
| 3.1 | Create `analytics_snapshots` table | Migration | S |
| 3.2 | Update `user_context_analytics` Celery task to persist | `src/app/infrastructure/celery/tasks/user_context_tasks.py` | S |
| 3.3 | Create `AnalyticsQueryGateway` port | `src/app/domain/chat/ports/analytics_gateway.py` | S |
| 3.4 | Implement SQLAlchemy adapter | `src/app/infrastructure/adapters/analytics_gateway_sqla.py` | M |
| 3.5 | Create admin API endpoints | `src/app/presentation/http/controllers/admin/analytics.py` | M |
| 3.6 | (Optional) Build frontend dashboard | Frontend repo | L |

#### 3.3 Database Schema

```sql
-- Analytics snapshots table
CREATE TABLE analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date DATE NOT NULL,
    snapshot_type VARCHAR(50) NOT NULL,  -- 'daily', 'weekly', 'monthly'
    
    -- User counts by portfolio state
    portfolio_empty_count INTEGER DEFAULT 0,
    portfolio_starter_count INTEGER DEFAULT 0,
    portfolio_active_count INTEGER DEFAULT 0,
    portfolio_whale_count INTEGER DEFAULT 0,
    
    -- User counts by activity level
    activity_new_count INTEGER DEFAULT 0,
    activity_very_active_count INTEGER DEFAULT 0,
    activity_active_count INTEGER DEFAULT 0,
    activity_weekly_active_count INTEGER DEFAULT 0,
    activity_monthly_active_count INTEGER DEFAULT 0,
    activity_inactive_count INTEGER DEFAULT 0,
    activity_reactivated_count INTEGER DEFAULT 0,
    
    -- User counts by type
    type_new_user_count INTEGER DEFAULT 0,
    type_casual_count INTEGER DEFAULT 0,
    type_trader_count INTEGER DEFAULT 0,
    type_yield_farmer_count INTEGER DEFAULT 0,
    type_power_user_count INTEGER DEFAULT 0,
    
    -- Totals
    total_users INTEGER DEFAULT 0,
    total_executions INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(snapshot_date, snapshot_type)
);

CREATE INDEX idx_analytics_date ON analytics_snapshots(snapshot_date);
```

#### 3.4 API Endpoints

```python
# src/app/presentation/http/controllers/admin/analytics.py
@router.get("/analytics/users")
async def get_user_analytics(
    authorization: Annotated[str, Security(bearer_scheme)],
    start_date: date | None = None,
    end_date: date | None = None,
) -> UserAnalyticsResponse:
    """Get user distribution analytics."""
    ...

@router.get("/analytics/trends")
async def get_trend_analytics(
    authorization: Annotated[str, Security(bearer_scheme)],
    period: str = "30d",  # 7d, 30d, 90d
) -> TrendAnalyticsResponse:
    """Get user classification trends over time."""
    ...

@router.get("/analytics/cohorts")
async def get_cohort_analytics(
    authorization: Annotated[str, Security(bearer_scheme)],
) -> CohortAnalyticsResponse:
    """Get cohort analysis (retention, conversion)."""
    ...
```

---

### Implementation Priority Matrix

```
                    IMPACT
                    High    Medium    Low
              ┌─────────┬─────────┬─────────┐
         High │ ✅ Core │ Wallet  │         │
              │ (Done)  │ Balance │         │
EFFORT        ├─────────┼─────────┼─────────┤
       Medium │Response │         │Analytics│
              │Templates│         │Dashboard│
              ├─────────┼─────────┼─────────┤
         Low  │         │         │         │
              └─────────┴─────────┴─────────┘
```

### Recommended Implementation Order

1. **Wallet Balance Aggregation** (Next)
   - Direct impact on classification accuracy
   - Enables accurate portfolio_state values
   - Required for meaningful EMPTY/STARTER/ACTIVE/WHALE distinctions

2. **Response Template System**
   - Improves consistency and reduces LLM costs
   - Enables multi-language support
   - Better UX for common scenarios

3. **Analytics Dashboard**
   - Nice-to-have for business insights
   - Can be deferred until user base grows
   - Low urgency but valuable long-term
