# FRONTEND_ADMIN_PROJECTS_RULES

## Admin Project Auto-Assignment Rules Module

**User Type:** Admin  
**Module:** Auto-Assignment Rules  
**Route:** `/admin/projects/:id/rules`  
**Access Level:** Full CRUD (Admin)

---

## 📋 Module Overview

### Title
**Auto-Assignment Rules** - Intelligent User Routing

### Description
Configuration interface for automatic project assignment rules. When users interact with Anvil without selecting a project, these rules automatically route them to the most appropriate project based on their query intent, wallet holdings, past behavior, and other signals.

### Key Capabilities
- Create intent-based assignment rules
- Configure wallet-based routing (token holdings)
- Set user attribute conditions
- Priority ordering of rules
- Test rules against sample users
- View assignment analytics

---

## 👤 User Stories

### US-ADMIN-RULES-001: View Assignment Rules
**As a** platform administrator  
**I want to** see all auto-assignment rules  
**So that** I understand how users are routed

### US-ADMIN-RULES-002: Create Intent-Based Rules
**As a** platform administrator  
**I want to** create rules based on query intent  
**So that** users asking about Aave go to Aave project

### US-ADMIN-RULES-003: Create Wallet-Based Rules
**As a** platform administrator  
**I want to** route users based on token holdings  
**So that** users with AAVE tokens see the Aave project

### US-ADMIN-RULES-004: Set Rule Priority
**As a** platform administrator  
**I want to** order rules by priority  
**So that** important rules are evaluated first

### US-ADMIN-RULES-005: Test Rules
**As a** platform administrator  
**I want to** test rules against sample inputs  
**So that** I verify they work correctly

---

## 🖼️ Views & Wireframes

### View 1: Rules Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🎯 Auto-Assignment Rules: Aave                                      [+ Add Rule]   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─ Summary ───────────────────────────────────────────────────────────────────────┐│
│  │  📋 5 Active Rules    🎯 1,245 Assignments (24h)    📈 89% Match Rate           ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ⚡ Rules are evaluated in priority order. First matching rule wins.               │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │ PRI │ RULE NAME                    │ CONDITIONS              │ MATCHES │ STATUS ││
│  ├─────┼──────────────────────────────┼─────────────────────────┼─────────┼────────┤│
│  │ ≡ 1 │ Aave Intent Mentions         │ intent contains "aave"  │ 456     │ 🟢 On  ││
│  │     │                              │ OR query contains "aave"│         │        ││
│  ├─────┼──────────────────────────────┼─────────────────────────┼─────────┼────────┤│
│  │ ≡ 2 │ AAVE Token Holders           │ wallet holds AAVE       │ 312     │ 🟢 On  ││
│  │     │                              │ balance > $100          │         │        ││
│  ├─────┼──────────────────────────────┼─────────────────────────┼─────────┼────────┤│
│  │ ≡ 3 │ Lending Intent               │ intent = "lend" OR      │ 234     │ 🟢 On  ││
│  │     │                              │ intent = "borrow"       │         │        ││
│  ├─────┼──────────────────────────────┼─────────────────────────┼─────────┼────────┤│
│  │ ≡ 4 │ Health Factor Questions      │ query contains "health" │ 156     │ 🟢 On  ││
│  │     │                              │ AND "factor"            │         │        ││
│  ├─────┼──────────────────────────────┼─────────────────────────┼─────────┼────────┤│
│  │ ≡ 5 │ Previous Aave Users          │ user.last_project =     │ 87      │ 🟢 On  ││
│  │     │                              │ "aave"                  │         │        ││
│  └─────┴──────────────────────────────┴─────────────────────────┴─────────┴────────┘│
│                                                                                      │
│  💡 Drag rules to reorder priority                                                  │
│                                                                                      │
│  ┌─ Test Assignment ───────────────────────────────────────────────────────────────┐│
│  │  Query: [I want to borrow USDC using my ETH as collateral    ] [🧪 Test]       ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 2: Rule Editor

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📝 Edit Rule: Aave Intent Mentions                                         [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  BASIC INFO                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Rule Name *                                                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Aave Intent Mentions                                                    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  Description                                                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Route users who mention Aave or related terms                           │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  CONDITIONS (Match ANY / Match ALL: [ANY ▼])                                        │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [Intent ▼]      [contains ▼]     [aave                    ]     [🗑️]  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  OR                                                                          │  │
│  │                                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [Query ▼]       [contains ▼]     [aave                    ]     [🗑️]  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  OR                                                                          │  │
│  │                                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ [Query ▼]       [contains ▼]     [health factor           ]     [🗑️]  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                               │  │
│  │  [+ Add Condition]                                                           │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  AVAILABLE CONDITION TYPES                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  📝 Query-Based           👤 User-Based            💰 Wallet-Based           │  │
│  │  • query.text             • user.tier              • wallet.holds_token      │  │
│  │  • query.intent           • user.last_project      • wallet.token_balance    │  │
│  │  • query.entities         • user.signup_date       • wallet.total_value      │  │
│  │  • query.language         • user.country           • wallet.chain_activity   │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  STATUS                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  [●] Enabled    [ ] Disabled                                                 │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [Delete Rule]                                       [Cancel]        [Save Rule]    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### View 3: Test Results

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🧪 Rule Test Results                                                       [✕]     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  INPUT                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Query: "I want to borrow USDC using my ETH as collateral"                   │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  CLASSIFICATION                                                                     │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  Intent: borrow_request (0.92)                                               │  │
│  │  Entities: [USDC, ETH, collateral]                                           │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RULE EVALUATION                                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                               │  │
│  │  Rule 1: "Aave Intent Mentions"                                              │  │
│  │  └─ ❌ No match: intent does not contain "aave"                              │  │
│  │                                                                               │  │
│  │  Rule 2: "AAVE Token Holders"                                                │  │
│  │  └─ ⚠️ Skipped: requires wallet context                                      │  │
│  │                                                                               │  │
│  │  Rule 3: "Lending Intent" ✅ MATCHED                                         │  │
│  │  └─ ✅ Match: intent = "borrow_request" matches "borrow"                     │  │
│  │                                                                               │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
│  RESULT                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────┐  │
│  │  ✅ Assigned to: Aave                                                        │  │
│  │  Matched Rule: #3 "Lending Intent"                                           │  │
│  │  Evaluation Time: 12ms                                                        │  │
│  └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Project Rules

```typescript
// GET /admin/projects/{id}/rules
interface GetProjectRulesResponse {
  success: true;
  data: {
    rules: AssignmentRule[];
    summary: {
      total_rules: number;
      active_rules: number;
      assignments_24h: number;
      match_rate: number;
    };
  };
}

interface AssignmentRule {
  id: string;
  name: string;
  description?: string;
  priority: number;
  conditions: RuleCondition[];
  condition_logic: 'any' | 'all';
  is_enabled: boolean;
  stats: {
    matches_24h: number;
    matches_7d: number;
    last_matched?: string;
  };
  created_at: string;
  updated_at: string;
}

interface RuleCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'not_in';
  value: any;
}
```

### Create Rule

```typescript
// POST /admin/projects/{id}/rules
interface CreateRuleRequest {
  name: string;
  description?: string;
  conditions: RuleCondition[];
  condition_logic?: 'any' | 'all';
  is_enabled?: boolean;
}
```

### Reorder Rules

```typescript
// PUT /admin/projects/{id}/rules/reorder
interface ReorderRulesRequest {
  rule_ids: string[];  // In priority order
}
```

### Test Rules

```typescript
// POST /admin/projects/{id}/rules/test
interface TestRulesRequest {
  query: string;
  user_context?: {
    user_id?: string;
    wallet_address?: string;
  };
}

interface TestRulesResponse {
  success: true;
  data: {
    query: string;
    classification: {
      intent: string;
      confidence: number;
      entities: string[];
    };
    evaluations: Array<{
      rule_id: string;
      rule_name: string;
      matched: boolean;
      reason: string;
    }>;
    result: {
      assigned: boolean;
      matched_rule_id?: string;
      matched_rule_name?: string;
      evaluation_time_ms: number;
    };
  };
}
```

---

## 🎬 Motion Design

```typescript
const rulesAnimations = {
  ruleDrag: {
    scale: 1.02,
    boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
    transition: { duration: 0.15 }
  },
  
  ruleReorder: {
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 25 }
  },
  
  matchHighlight: {
    backgroundColor: ['transparent', 'rgba(16, 185, 129, 0.2)', 'transparent'],
    transition: { duration: 0.5 }
  },
  
  conditionAdd: {
    opacity: [0, 1],
    height: ['0px', 'auto'],
    transition: { duration: 0.2 }
  }
};
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Auto-Assignment Rules*
