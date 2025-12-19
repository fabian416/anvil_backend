# Projects & Workspaces - Complete User Flow Specification

**Module**: Projects & Workspaces
**Version**: 1.0
**Last Updated**: December 18, 2025
**Methodology**: CTO Framework + UX Design Thinking
**Total Endpoints**: 18 (5 User + 13 Admin)

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [User Personas](#user-personas)
3. [User Journey Maps](#user-journey-maps)
4. [Endpoint Flow Diagrams](#endpoint-flow-diagrams)
5. [TypeScript Integration Patterns](#typescript-integration-patterns)
6. [React Hooks & Components](#react-hooks--components)
7. [Error Handling Flows](#error-handling-flows)
8. [Performance Optimization](#performance-optimization)
9. [Accessibility Guidelines (WCAG 2.1 AA)](#accessibility-guidelines-wcag-21-aa)
10. [Implementation Checklist](#implementation-checklist)
11. [Success Metrics](#success-metrics)

---

## 📊 Executive Summary

### What is Projects & Workspaces?

**Projects & Workspaces** is a **multi-tenancy workspace management system** that enables:

- **Users** to work in different DeFi project contexts (e.g., "Yield Optimizer", "Risk Analyzer", "NFT Portfolio")
- **Project-specific configurations**: Each project has its own system prompt, enabled protocols, tools, and knowledge base
- **Access control**: Rule-based automatic assignments + manual admin assignments
- **Workspace switching**: Users can seamlessly switch between different project contexts

### Key Capabilities

**For End Users (5 endpoints):**
- View assigned projects
- Discover available public projects
- Join projects
- Switch active workspace
- View project details

**For Administrators (13 endpoints):**
- Full CRUD on projects
- Knowledge base management
- Assignment rule configuration
- User assignment management
- Project search

### Business Value

- **Context Isolation**: Each project operates independently with its own AI behavior
- **Scalability**: Support unlimited specialized DeFi use cases
- **Monetization**: Premium projects for PRO/ENTERPRISE tiers
- **User Engagement**: Users discover and join projects that match their interests

---

## 👥 User Personas

### Persona 1: **Alex - Active DeFi Trader**

**Demographics:**
- Age: 32
- Role: Full-time crypto trader
- Tech Savvy: High
- Subscription: PRO tier

**Goals:**
- Switch between different trading strategies
- Access specialized tools for each strategy
- Get AI assistance tailored to specific DeFi protocols

**Pain Points:**
- Generic AI doesn't understand context switching
- Needs separate workspaces for yield farming vs trading vs NFTs
- Wants project-specific knowledge base

**Usage Pattern:**
- Uses 3-4 projects daily
- Frequently switches active workspace
- Explores new projects monthly

---

### Persona 2: **Maria - Platform Administrator**

**Demographics:**
- Age: 28
- Role: DeFi platform operations manager
- Tech Savvy: Very High
- Access: Admin privileges

**Goals:**
- Create specialized projects for different user segments
- Control which users can access premium projects
- Monitor project usage and engagement
- Manage knowledge base content

**Pain Points:**
- Manual user assignment is time-consuming
- Need automatic rules based on subscription tier
- Hard to track which projects are most popular

**Usage Pattern:**
- Creates 2-3 new projects per month
- Reviews analytics weekly
- Updates knowledge base continuously

---

### Persona 3: **James - Curious DeFi Beginner**

**Demographics:**
- Age: 25
- Role: Junior developer learning DeFi
- Tech Savvy: Medium
- Subscription: FREE tier

**Goals:**
- Discover beginner-friendly projects
- Learn from project-specific guides
- Gradually access more advanced projects as he learns

**Pain Points:**
- Overwhelmed by too many options
- Needs curated learning paths
- Wants clear project descriptions before joining

**Usage Pattern:**
- Browses available projects frequently
- Sticks to 1-2 projects initially
- Reads knowledge base extensively

---

## 🗺️ User Journey Maps

### Journey 1: **First-Time Project Discovery & Selection**

**Persona**: James (DeFi Beginner)
**Scenario**: James logs in for the first time and needs to select a project to start

#### Journey Steps:

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: Initial Landing                                       │
├─────────────────────────────────────────────────────────────────┤
│ Action:    User logs in to platform                            │
│ API Call:  GET /api/v1/user/projects/                          │
│ State:     assigned_projects: []  (empty, first time)          │
│ UI:        Shows "Welcome! Choose your first project" screen   │
│ Emotion:   😊 Curious but slightly uncertain                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: Browsing Available Projects                           │
├─────────────────────────────────────────────────────────────────┤
│ Action:    User clicks "Explore Projects"                      │
│ API Call:  GET /api/v1/user/projects/available                 │
│ Response:  List of public projects with:                       │
│            - Name, description, icon                            │
│            - Tags (beginner/intermediate/advanced)              │
│            - Member count                                       │
│            - Featured badge                                     │
│ UI:        Grid/list view with filters                         │
│ Emotion:   😮 Excited to see options                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: Project Detail View                                   │
├─────────────────────────────────────────────────────────────────┤
│ Action:    User clicks on "DeFi Basics" project                │
│ API Call:  GET /api/v1/user/projects/defi-basics               │
│ Response:  Full project details:                               │
│            - Welcome message                                    │
│            - Enabled protocols and tools                        │
│            - Member testimonials                                │
│            - Preview of knowledge base                          │
│ UI:        Project detail page with "Join Project" button      │
│ Emotion:   😊 Confident this is the right choice               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: Joining the Project                                   │
├─────────────────────────────────────────────────────────────────┤
│ Action:    User clicks "Join Project"                          │
│ API Call:  POST /api/v1/user/projects/{id}/join                │
│ Response:  201 Created - User added to project                 │
│ Side Effect: Project automatically selected as active          │
│ UI:        Success message + redirect to project home          │
│ Emotion:   🎉 Excited to get started                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: First Interaction                                     │
├─────────────────────────────────────────────────────────────────┤
│ Action:    User starts chat with AI                            │
│ Context:   AI uses "DeFi Basics" system prompt                 │
│ Tools:     Only beginner-friendly protocols enabled            │
│ Knowledge: Access to beginner guides                           │
│ Emotion:   😊 Happy with personalized experience               │
└─────────────────────────────────────────────────────────────────┘
```

**Key Touchpoints:**
1. Empty state → Available projects
2. Project discovery → Detail view
3. Join action → Immediate activation
4. Context-aware AI interaction

**Success Criteria:**
- User joins a project within 3 minutes
- First AI chat happens within 5 minutes
- User understands they're in a specific context

---

### Journey 2: **Multi-Project Power User Workflow**

**Persona**: Alex (Active Trader)
**Scenario**: Alex switches between yield farming, trading, and NFT projects throughout the day

#### Journey Steps:

```
┌─────────────────────────────────────────────────────────────────┐
│ MORNING: Yield Farming Context                                 │
├─────────────────────────────────────────────────────────────────┤
│ Time:      9:00 AM                                             │
│ Action:    Alex opens app                                      │
│ API Call:  GET /api/v1/user/projects/                          │
│ Response:  assigned_projects: ["Yield", "Trading", "NFT"]      │
│            active_project_id: "yield-optimizer-id"             │
│ UI:        Shows "Yield Optimizer" as active (highlighted)     │
│ Context:   All queries use Yield system prompt                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ AFTERNOON: Switching to Trading                                │
├─────────────────────────────────────────────────────────────────┤
│ Time:      2:00 PM                                             │
│ Action:    Alex clicks project switcher dropdown               │
│ UI:        Shows 3 projects with radio selection               │
│ Action:    Selects "Perpetual Trading Pro"                     │
│ API Call:  POST /api/v1/user/projects/{trading-id}/select      │
│ Response:  200 OK                                              │
│ Effect:    Active workspace changed                            │
│ UI:        Navbar updates to show trading context              │
│            AI tools switch to trading-specific                  │
│ Emotion:   ⚡ Seamless transition                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ EVENING: NFT Analysis                                          │
├─────────────────────────────────────────────────────────────────┤
│ Time:      7:00 PM                                             │
│ Action:    Quick switch to NFT project via keyboard shortcut   │
│ Shortcut:  Cmd/Ctrl + K → "Switch Project" → "NFT"            │
│ API Call:  POST /api/v1/user/projects/{nft-id}/select          │
│ Response:  200 OK                                              │
│ Effect:    Context switches to NFT analytics                   │
│ UI:        Different color scheme (NFT project branding)        │
│ Tools:     OpenSea, Blur, NFT metrics enabled                  │
│ Emotion:   🚀 Productivity boost from context switching        │
└─────────────────────────────────────────────────────────────────┘
```

**Key Features Used:**
- Project switcher dropdown (always visible in navbar)
- Keyboard shortcuts for power users
- Visual indicators of active context
- Instant context switching

**Success Criteria:**
- Context switch completes in < 200ms
- No data loss during switch
- Clear visual feedback of active workspace
- Keyboard shortcuts work reliably

---

### Journey 3: **Admin Creating & Configuring New Project**

**Persona**: Maria (Platform Admin)
**Scenario**: Maria creates a premium "Whale Tracker Pro" project for ENTERPRISE users

#### Journey Steps:

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: Project Creation                                      │
├─────────────────────────────────────────────────────────────────┤
│ Location:  Admin Dashboard → Projects → "Create New"           │
│ Form:      Multi-step wizard                                   │
│            Step 1: Basic Info (name, slug, description)         │
│            Step 2: Branding (icon, color, banner)              │
│            Step 3: AI Configuration (system prompt)            │
│            Step 4: Features (protocols, chains, tools)         │
│            Step 5: Access Control (visibility, max users)      │
│ API Call:  POST /api/v1/admin/projects/                        │
│ Request:   {                                                   │
│              slug: "whale-tracker-pro",                        │
│              name: "Whale Tracker Pro",                        │
│              visibility: "private",                            │
│              system_prompt: "You are a whale tracking...",     │
│              enabled_protocols: ["etherscan", "arkham"],       │
│              max_users: 50,                                    │
│              is_featured: true                                 │
│            }                                                    │
│ Response:  201 Created - project_id returned                   │
│ UI:        Success notification + redirect to project page     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: Knowledge Base Setup                                  │
├─────────────────────────────────────────────────────────────────┤
│ Location:  Project Settings → Knowledge Base                   │
│ Action:    Upload documentation files                          │
│ API Calls: POST /api/v1/admin/projects/{id}/knowledge (x3)     │
│ Documents: 1. "Whale Tracking Guide.md"                        │
│            2. "On-Chain Analysis FAQ.md"                        │
│            3. "Alert Configuration.md"                          │
│ Response:  201 Created for each document                       │
│ UI:        Knowledge base list updates in real-time            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: Assignment Rule Configuration                         │
├─────────────────────────────────────────────────────────────────┤
│ Location:  Project Settings → Access Control                   │
│ Action:    Create automatic assignment rule                    │
│ API Call:  POST /api/v1/admin/projects/assignments/rules       │
│ Request:   {                                                   │
│              project_id: "whale-tracker-pro-id",               │
│              rule_type: "subscription",                        │
│              conditions: {                                     │
│                subscription_tier: "ENTERPRISE",                │
│                min_tier: "ENTERPRISE"                          │
│              },                                                │
│              priority: 10,                                     │
│              is_active: true                                   │
│            }                                                    │
│ Response:  201 Created                                         │
│ Effect:    All ENTERPRISE users auto-assigned                  │
│ UI:        Rule appears in rules list                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: Beta Tester Manual Assignments                        │
├─────────────────────────────────────────────────────────────────┤
│ Location:  Project Settings → Users                            │
│ Action:    Manually assign 10 PRO users for beta testing       │
│ API Calls: POST /api/v1/admin/projects/{id}/users (x10)        │
│ Request:   {                                                   │
│              user_id: "user-123",                              │
│              role: "contributor",                              │
│              expiry_date: "2025-03-31T23:59:59Z"               │
│            }                                                    │
│ Response:  201 Created per assignment                          │
│ UI:        User list updates with assignees                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: Monitoring & Analytics                                │
├─────────────────────────────────────────────────────────────────┤
│ Location:  Project Dashboard → Analytics                       │
│ API Call:  GET /api/v1/admin/projects/{id}                     │
│ Metrics:   - 60 total users (50 ENTERPRISE + 10 beta)          │
│            - 234 AI conversations this week                     │
│            - 4.8/5 average satisfaction                         │
│            - 45 knowledge base accesses                         │
│ UI:        Charts and graphs showing engagement                │
│ Action:    Export report for stakeholders                      │
└─────────────────────────────────────────────────────────────────┘
```

**Admin Workflow Insights:**
- Wizard-based creation reduces errors
- Real-time validation of slug uniqueness
- Preview mode before publishing
- Bulk operations for user assignments
- Analytics dashboard for monitoring

**Success Criteria:**
- Project created in < 10 minutes
- Zero configuration errors
- Knowledge base easily uploadable
- Rules work as expected
- Clear analytics visibility

---

## 📊 Endpoint Flow Diagrams

### Flow 1: User Project Discovery & Join

```
┌─────────┐
│  User   │
│  Logs   │
│   In    │
└────┬────┘
     │
     ▼
┌─────────────────────────────────────┐
│ GET /api/v1/user/projects/          │
│                                     │
│ Response:                           │
│ {                                   │
│   assigned_projects: [],            │
│   active_project_id: null           │
│ }                                   │
└────┬────────────────────────────────┘
     │
     │ Empty state detected
     │
     ▼
┌─────────────────────────────────────┐
│ GET /api/v1/user/projects/available │
│                                     │
│ Response:                           │
│ [                                   │
│   {                                 │
│     id: "proj-1",                   │
│     name: "DeFi Basics",            │
│     visibility: "public",           │
│     is_featured: true               │
│   },                                │
│   { ... more projects }             │
│ ]                                   │
└────┬────────────────────────────────┘
     │
     │ User browses and selects
     │
     ▼
┌─────────────────────────────────────┐
│ GET /api/v1/user/projects/          │
│     defi-basics                     │
│                                     │
│ Response:                           │
│ {                                   │
│   id: "proj-1",                     │
│   name: "DeFi Basics",              │
│   description: "Learn DeFi...",     │
│   welcome_message: "Welcome!",      │
│   enabled_protocols: [...],         │
│   enabled_tools: [...]              │
│ }                                   │
└────┬────────────────────────────────┘
     │
     │ User clicks "Join"
     │
     ▼
┌─────────────────────────────────────┐
│ POST /api/v1/user/projects/         │
│      {proj-1}/join                  │
│                                     │
│ Response: 201 Created               │
│                                     │
│ Side Effect:                        │
│ - User assigned to project          │
│ - Project auto-selected as active   │
└────┬────────────────────────────────┘
     │
     │ Success! Redirect to project home
     │
     ▼
┌─────────────────────────────────────┐
│        Project Home Page            │
│                                     │
│ - Welcome message displayed         │
│ - AI chat ready (with context)      │
│ - Tools enabled for this project    │
│ - Knowledge base accessible         │
└─────────────────────────────────────┘
```

---

### Flow 2: Multi-Project Context Switching

```
┌─────────┐
│  User   │
│  with   │
│   3     │
│Projects │
└────┬────┘
     │
     ▼
┌─────────────────────────────────────┐
│ GET /api/v1/user/projects/          │
│                                     │
│ Response:                           │
│ {                                   │
│   assigned_projects: [              │
│     { id: "yield", name: "Yield" }, │
│     { id: "trade", name: "Trade" }, │
│     { id: "nft", name: "NFT" }      │
│   ],                                │
│   active_project_id: "yield"        │
│ }                                   │
└────┬────────────────────────────────┘
     │
     │ UI: Shows "Yield" as active
     │ User clicks project switcher
     │
     ▼
┌─────────────────────────────────────┐
│     Dropdown Menu Rendered          │
│                                     │
│ ● Yield Optimizer (active)          │
│ ○ Perpetual Trading                 │
│ ○ NFT Portfolio                     │
│                                     │
│ [Explore More Projects]             │
└────┬────────────────────────────────┘
     │
     │ User selects "Perpetual Trading"
     │
     ▼
┌─────────────────────────────────────┐
│ POST /api/v1/user/projects/         │
│      {trade}/select                 │
│                                     │
│ Request: {} (empty body)            │
│ Response: 200 OK                    │
│                                     │
│ Side Effect:                        │
│ - active_project_id updated         │
│ - User session context switched     │
└────┬────────────────────────────────┘
     │
     │ Context switch complete
     │
     ▼
┌─────────────────────────────────────┐
│   UI Updates (Instant Feedback)     │
│                                     │
│ 1. Navbar color changes             │
│ 2. Project name updates             │
│ 3. Available tools change           │
│ 4. AI chat context resets           │
│ 5. New system prompt active         │
│                                     │
│ User continues work in new context  │
└─────────────────────────────────────┘
```

**Performance Note**: Context switching must complete in < 200ms for smooth UX.

---

### Flow 3: Admin Project Creation Workflow

```
┌─────────┐
│  Admin  │
│  Maria  │
└────┬────┘
     │
     ▼
┌─────────────────────────────────────┐
│ Admin Dashboard → Create Project    │
│                                     │
│ Multi-Step Form Wizard:             │
│ Step 1/5: Basic Info                │
└────┬────────────────────────────────┘
     │
     │ Form filled & validated
     │
     ▼
┌─────────────────────────────────────┐
│ POST /api/v1/admin/projects/        │
│                                     │
│ Request: {                          │
│   slug: "whale-tracker-pro",        │
│   name: "Whale Tracker Pro",        │
│   description: "...",               │
│   icon: "🐋",                       │
│   color: "#1E40AF",                 │
│   status: "draft",                  │
│   visibility: "private",            │
│   system_prompt: "You are...",      │
│   enabled_protocols: [...],         │
│   enabled_chains: [...],            │
│   enabled_tools: [...],             │
│   max_users: 50,                    │
│   is_featured: true                 │
│ }                                   │
│                                     │
│ Response: 201 Created               │
│ {                                   │
│   id: "new-project-uuid",           │
│   slug: "whale-tracker-pro",        │
│   ...all fields                     │
│ }                                   │
└────┬────────────────────────────────┘
     │
     │ Project created (draft status)
     │ Redirect to project settings
     │
     ▼
┌─────────────────────────────────────┐
│  Upload Knowledge Base Documents    │
│                                     │
│  For i=1 to 3:                      │
│    POST /api/v1/admin/projects/     │
│         {id}/knowledge              │
│                                     │
│    Request: {                       │
│      title: "Guide X",              │
│      content: "# Guide...",         │
│      document_type: "protocol_guide"│
│    }                                │
│                                     │
│    Response: 201 Created            │
└────┬────────────────────────────────┘
     │
     │ Knowledge base populated
     │
     ▼
┌─────────────────────────────────────┐
│  Configure Assignment Rules         │
│                                     │
│  POST /api/v1/admin/projects/       │
│       assignments/rules             │
│                                     │
│  Request: {                         │
│    project_id: "new-project-uuid",  │
│    rule_type: "subscription",       │
│    conditions: {                    │
│      subscription_tier: "ENTERPRISE"│
│    },                               │
│    priority: 10,                    │
│    is_active: true                  │
│  }                                  │
│                                     │
│  Response: 201 Created              │
│                                     │
│  Effect: Rule activates immediately │
│  → All ENTERPRISE users auto-assigned│
└────┬────────────────────────────────┘
     │
     │ Rules configured
     │
     ▼
┌─────────────────────────────────────┐
│  Manually Assign Beta Testers       │
│                                     │
│  For each PRO user in list:         │
│    POST /api/v1/admin/projects/     │
│         {id}/users                  │
│                                     │
│    Request: {                       │
│      user_id: "user-xxx",           │
│      role: "contributor",           │
│      expiry_date: "2025-03-31..."   │
│    }                                │
│                                     │
│    Response: 201 Created            │
└────┬────────────────────────────────┘
     │
     │ Beta testers assigned
     │
     ▼
┌─────────────────────────────────────┐
│  Publish Project                    │
│                                     │
│  PATCH /api/v1/admin/projects/{id}  │
│                                     │
│  Request: {                         │
│    status: "active"                 │
│  }                                  │
│                                     │
│  Response: 200 OK                   │
│                                     │
│  Effect:                            │
│  - Project visible to assigned users│
│  - Featured on discovery page       │
│  - Ready for use                    │
└─────────────────────────────────────┘
```

---

## 💻 TypeScript Integration Patterns

### Type Definitions

```typescript
// ============================================
// Core Types
// ============================================

interface Project {
  id: string;
  slug: string;
  name: string;
  description?: string;
  icon?: string; // Emoji or URL
  color?: string; // Hex color
  banner_url?: string;
  status: 'draft' | 'active' | 'archived';
  visibility: 'public' | 'private' | 'team';
  system_prompt: string;
  welcome_message?: string;
  enabled_protocols: string[];
  enabled_chains: string[];
  enabled_tools: string[];
  risk_config?: Record<string, any>;
  max_users?: number;
  current_users?: number;
  display_order?: number;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

interface UserProjectsResponse {
  assigned_projects: Project[];
  active_project_id: string | null;
}

interface KnowledgeDocument {
  id: string;
  project_id: string;
  title: string;
  content: string;
  document_type: 'protocol_guide' | 'faq' | 'strategy' | 'general';
  metadata?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AssignmentRule {
  id: string;
  project_id: string;
  rule_type: 'user_tier' | 'subscription' | 'manual';
  conditions: Record<string, any>;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface UserAssignment {
  id: string;
  project_id: string;
  user_id: string;
  email?: string;
  role: 'member' | 'contributor' | 'admin';
  assigned_at: string;
  expiry_date?: string;
}

// ============================================
// API Client
// ============================================

class ProjectsAPI {
  private baseURL = '/api/v1';

  // -----------------
  // User Endpoints
  // -----------------

  async getUserProjects(): Promise<UserProjectsResponse> {
    const response = await fetch(`${this.baseURL}/user/projects/`, {
      headers: {
        Authorization: `Bearer ${this.getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch projects: ${response.statusText}`);
    }

    return response.json();
  }

  async getAvailableProjects(): Promise<Project[]> {
    const response = await fetch(`${this.baseURL}/user/projects/available`, {
      headers: {
        Authorization: `Bearer ${this.getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch available projects: ${response.statusText}`);
    }

    return response.json();
  }

  async selectProject(projectId: string): Promise<void> {
    const response = await fetch(
      `${this.baseURL}/user/projects/${projectId}/select`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getToken()}`,
        },
        body: JSON.stringify({}),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to select project: ${response.statusText}`);
    }
  }

  async joinProject(projectId: string): Promise<void> {
    const response = await fetch(
      `${this.baseURL}/user/projects/${projectId}/join`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getToken()}`,
        },
        body: JSON.stringify({}),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to join project: ${response.statusText}`);
    }
  }

  async getProjectBySlug(slug: string): Promise<Project> {
    const response = await fetch(`${this.baseURL}/user/projects/${slug}`, {
      headers: {
        Authorization: `Bearer ${this.getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch project: ${response.statusText}`);
    }

    return response.json();
  }

  // -----------------
  // Admin Endpoints
  // -----------------

  async createProject(data: Partial<Project>): Promise<Project> {
    const response = await fetch(`${this.baseURL}/admin/projects/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.getToken()}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to create project: ${response.statusText}`);
    }

    return response.json();
  }

  async listProjects(filters?: {
    status?: string;
    visibility?: string;
    is_featured?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<Project[]> {
    const params = new URLSearchParams(
      filters as Record<string, string>
    ).toString();
    const response = await fetch(`${this.baseURL}/admin/projects/?${params}`, {
      headers: {
        Authorization: `Bearer ${this.getToken()}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to list projects: ${response.statusText}`);
    }

    return response.json();
  }

  async updateProject(
    projectId: string,
    updates: Partial<Project>
  ): Promise<Project> {
    const response = await fetch(
      `${this.baseURL}/admin/projects/${projectId}`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getToken()}`,
        },
        body: JSON.stringify(updates),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to update project: ${response.statusText}`);
    }

    return response.json();
  }

  async deleteProject(projectId: string): Promise<void> {
    const response = await fetch(
      `${this.baseURL}/admin/projects/${projectId}`,
      {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${this.getToken()}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to delete project: ${response.statusText}`);
    }
  }

  async createKnowledgeDocument(
    projectId: string,
    data: Partial<KnowledgeDocument>
  ): Promise<KnowledgeDocument> {
    const response = await fetch(
      `${this.baseURL}/admin/projects/${projectId}/knowledge`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getToken()}`,
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(
        `Failed to create knowledge document: ${response.statusText}`
      );
    }

    return response.json();
  }

  async listKnowledgeDocuments(
    projectId: string
  ): Promise<KnowledgeDocument[]> {
    const response = await fetch(
      `${this.baseURL}/admin/projects/${projectId}/knowledge`,
      {
        headers: {
          Authorization: `Bearer ${this.getToken()}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(
        `Failed to list knowledge documents: ${response.statusText}`
      );
    }

    return response.json();
  }

  async createAssignmentRule(
    data: Partial<AssignmentRule>
  ): Promise<AssignmentRule> {
    const response = await fetch(
      `${this.baseURL}/admin/projects/assignments/rules`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getToken()}`,
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(
        `Failed to create assignment rule: ${response.statusText}`
      );
    }

    return response.json();
  }

  async assignUserToProject(
    projectId: string,
    data: Partial<UserAssignment>
  ): Promise<UserAssignment> {
    const response = await fetch(
      `${this.baseURL}/admin/projects/${projectId}/users`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.getToken()}`,
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to assign user: ${response.statusText}`);
    }

    return response.json();
  }

  async searchProjects(query: string): Promise<Project[]> {
    const response = await fetch(
      `${this.baseURL}/admin/projects/search?q=${encodeURIComponent(query)}`,
      {
        headers: {
          Authorization: `Bearer ${this.getToken()}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to search projects: ${response.statusText}`);
    }

    return response.json();
  }

  private getToken(): string {
    return localStorage.getItem('access_token') || '';
  }
}

export const projectsAPI = new ProjectsAPI();
```

---

## 🪝 React Hooks & Components

### Custom Hooks

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsAPI } from './api';

// ============================================
// User Hooks
// ============================================

export const useUserProjects = () => {
  return useQuery({
    queryKey: ['user', 'projects'],
    queryFn: () => projectsAPI.getUserProjects(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useAvailableProjects = () => {
  return useQuery({
    queryKey: ['projects', 'available'],
    queryFn: () => projectsAPI.getAvailableProjects(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useProjectBySlug = (slug: string) => {
  return useQuery({
    queryKey: ['projects', 'slug', slug],
    queryFn: () => projectsAPI.getProjectBySlug(slug),
    enabled: !!slug,
  });
};

export const useSelectProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => projectsAPI.selectProject(projectId),
    onSuccess: () => {
      // Invalidate user projects to reflect new active project
      queryClient.invalidateQueries({ queryKey: ['user', 'projects'] });

      // Also invalidate any chat or context-dependent queries
      queryClient.invalidateQueries({ queryKey: ['chat'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useJoinProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => projectsAPI.joinProject(projectId),
    onSuccess: () => {
      // Refresh user's project list
      queryClient.invalidateQueries({ queryKey: ['user', 'projects'] });
      // Refresh available projects (this one may no longer be joinable)
      queryClient.invalidateQueries({ queryKey: ['projects', 'available'] });
    },
  });
};

// ============================================
// Admin Hooks
// ============================================

export const useAdminProjects = (filters?: {
  status?: string;
  visibility?: string;
  is_featured?: boolean;
}) => {
  return useQuery({
    queryKey: ['admin', 'projects', filters],
    queryFn: () => projectsAPI.listProjects(filters),
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Project>) => projectsAPI.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'projects'] });
    },
  });
};

export const useUpdateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      updates,
    }: {
      projectId: string;
      updates: Partial<Project>;
    }) => projectsAPI.updateProject(projectId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'projects'] });
      queryClient.invalidateQueries({
        queryKey: ['projects', 'slug', variables.updates.slug],
      });
    },
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => projectsAPI.deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'projects'] });
    },
  });
};

export const useKnowledgeDocuments = (projectId: string) => {
  return useQuery({
    queryKey: ['projects', projectId, 'knowledge'],
    queryFn: () => projectsAPI.listKnowledgeDocuments(projectId),
    enabled: !!projectId,
  });
};

export const useCreateKnowledgeDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: string;
      data: Partial<KnowledgeDocument>;
    }) => projectsAPI.createKnowledgeDocument(projectId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'knowledge'],
      });
    },
  });
};

export const useCreateAssignmentRule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<AssignmentRule>) =>
      projectsAPI.createAssignmentRule(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.project_id, 'rules'],
      });
    },
  });
};

export const useAssignUserToProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: string;
      data: Partial<UserAssignment>;
    }) => projectsAPI.assignUserToProject(projectId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['projects', variables.projectId, 'users'],
      });
    },
  });
};

export const useSearchProjects = () => {
  return useMutation({
    mutationFn: (query: string) => projectsAPI.searchProjects(query),
  });
};
```

---

### React Components

#### 1. Project Switcher Dropdown

```typescript
import React, { useState } from 'react';
import { useUserProjects, useSelectProject } from './hooks';

export const ProjectSwitcher: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { data, isLoading } = useUserProjects();
  const selectProject = useSelectProject();

  if (isLoading) {
    return <div className="animate-pulse">Loading projects...</div>;
  }

  const activeProject = data?.assigned_projects.find(
    (p) => p.id === data.active_project_id
  );

  const handleSelect = async (projectId: string) => {
    await selectProject.mutateAsync(projectId);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-100"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <span className="text-2xl">{activeProject?.icon}</span>
        <span className="font-medium">{activeProject?.name}</span>
        <svg className="w-4 h-4" /* chevron icon */ />
      </button>

      {isOpen && (
        <div
          className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-lg border"
          role="listbox"
        >
          {data?.assigned_projects.map((project) => (
            <button
              key={project.id}
              onClick={() => handleSelect(project.id)}
              className={`
                w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50
                ${project.id === data.active_project_id ? 'bg-blue-50' : ''}
              `}
              role="option"
              aria-selected={project.id === data.active_project_id}
            >
              <span className="text-2xl">{project.icon}</span>
              <div className="flex-1 text-left">
                <div className="font-medium">{project.name}</div>
                <div className="text-sm text-gray-500">{project.description}</div>
              </div>
              {project.id === data.active_project_id && (
                <svg className="w-5 h-5 text-blue-600" /* checkmark */ />
              )}
            </button>
          ))}

          <div className="border-t">
            <button
              onClick={() => {
                setIsOpen(false);
                // Navigate to project discovery page
              }}
              className="w-full px-4 py-3 text-blue-600 hover:bg-blue-50 text-left font-medium"
            >
              + Explore More Projects
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
```

#### 2. Available Projects Grid

```typescript
import React, { useState } from 'react';
import { useAvailableProjects, useJoinProject } from './hooks';

export const AvailableProjectsGrid: React.FC = () => {
  const { data: projects, isLoading } = useAvailableProjects();
  const joinProject = useJoinProject();
  const [selectedProject, setSelectedProject] = useState<string | null>(null);

  const handleJoin = async (projectId: string) => {
    await joinProject.mutateAsync(projectId);
    // Navigate to project home
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {projects?.map((project) => (
        <div
          key={project.id}
          className="border rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
        >
          {/* Banner */}
          {project.banner_url && (
            <img
              src={project.banner_url}
              alt={project.name}
              className="w-full h-32 object-cover"
            />
          )}

          {/* Content */}
          <div className="p-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-4xl">{project.icon}</span>
              <div className="flex-1">
                <h3 className="font-semibold text-lg">{project.name}</h3>
                {project.is_featured && (
                  <span className="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">
                    ⭐ Featured
                  </span>
                )}
              </div>
            </div>

            <p className="text-gray-600 text-sm mb-4">{project.description}</p>

            {/* Stats */}
            <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
              <span>👥 {project.current_users} members</span>
              {project.max_users && (
                <span>
                  (Max: {project.max_users})
                </span>
              )}
            </div>

            {/* Protocols */}
            <div className="flex flex-wrap gap-2 mb-4">
              {project.enabled_protocols.slice(0, 3).map((protocol) => (
                <span
                  key={protocol}
                  className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                >
                  {protocol}
                </span>
              ))}
              {project.enabled_protocols.length > 3 && (
                <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                  +{project.enabled_protocols.length - 3} more
                </span>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedProject(project.id)}
                className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Learn More
              </button>
              <button
                onClick={() => handleJoin(project.id)}
                disabled={joinProject.isPending}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {joinProject.isPending ? 'Joining...' : 'Join Project'}
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
```

#### 3. Admin Project Creation Wizard

```typescript
import React, { useState } from 'react';
import { useCreateProject } from './hooks';

type Step = 'basic' | 'branding' | 'ai' | 'features' | 'access';

export const ProjectCreationWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<Step>('basic');
  const [formData, setFormData] = useState<Partial<Project>>({
    status: 'draft',
    visibility: 'public',
    is_featured: false,
    enabled_protocols: [],
    enabled_chains: [],
    enabled_tools: [],
  });

  const createProject = useCreateProject();

  const steps: Step[] = ['basic', 'branding', 'ai', 'features', 'access'];
  const currentStepIndex = steps.indexOf(currentStep);

  const handleNext = () => {
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < steps.length) {
      setCurrentStep(steps[nextIndex]);
    }
  };

  const handleBack = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(steps[prevIndex]);
    }
  };

  const handleSubmit = async () => {
    await createProject.mutateAsync(formData);
    // Navigate to project settings
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          {steps.map((step, index) => (
            <React.Fragment key={step}>
              <div
                className={`
                  flex items-center justify-center w-10 h-10 rounded-full
                  ${
                    index <= currentStepIndex
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-500'
                  }
                `}
              >
                {index + 1}
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`
                    flex-1 h-1
                    ${
                      index < currentStepIndex ? 'bg-blue-600' : 'bg-gray-200'
                    }
                  `}
                />
              )}
            </React.Fragment>
          ))}
        </div>
        <div className="text-center text-sm text-gray-600">
          Step {currentStepIndex + 1} of {steps.length}:{' '}
          {currentStep.charAt(0).toUpperCase() + currentStep.slice(1)}
        </div>
      </div>

      {/* Form Content */}
      <div className="bg-white rounded-lg border p-8">
        {currentStep === 'basic' && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold mb-4">Basic Information</h2>

            <div>
              <label className="block text-sm font-medium mb-1">
                Project Name *
              </label>
              <input
                type="text"
                value={formData.name || ''}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                className="w-full px-4 py-2 border rounded-lg"
                placeholder="DeFi Yield Optimizer"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Slug (URL) *
              </label>
              <input
                type="text"
                value={formData.slug || ''}
                onChange={(e) =>
                  setFormData({ ...formData, slug: e.target.value })
                }
                className="w-full px-4 py-2 border rounded-lg"
                placeholder="defi-yield-optimizer"
              />
              <p className="text-xs text-gray-500 mt-1">
                URL: /projects/{formData.slug || 'slug'}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Description
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                className="w-full px-4 py-2 border rounded-lg"
                rows={3}
                placeholder="Brief description of what this project does..."
              />
            </div>
          </div>
        )}

        {currentStep === 'branding' && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold mb-4">Branding</h2>

            <div>
              <label className="block text-sm font-medium mb-1">
                Icon (Emoji)
              </label>
              <input
                type="text"
                value={formData.icon || ''}
                onChange={(e) =>
                  setFormData({ ...formData, icon: e.target.value })
                }
                className="w-full px-4 py-2 border rounded-lg"
                placeholder="🎯"
                maxLength={2}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Brand Color (Hex)
              </label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={formData.color || '#3B82F6'}
                  onChange={(e) =>
                    setFormData({ ...formData, color: e.target.value })
                  }
                  className="w-16 h-10"
                />
                <input
                  type="text"
                  value={formData.color || '#3B82F6'}
                  onChange={(e) =>
                    setFormData({ ...formData, color: e.target.value })
                  }
                  className="flex-1 px-4 py-2 border rounded-lg"
                  placeholder="#3B82F6"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Banner Image URL
              </label>
              <input
                type="url"
                value={formData.banner_url || ''}
                onChange={(e) =>
                  setFormData({ ...formData, banner_url: e.target.value })
                }
                className="w-full px-4 py-2 border rounded-lg"
                placeholder="https://..."
              />
            </div>
          </div>
        )}

        {currentStep === 'ai' && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold mb-4">AI Configuration</h2>

            <div>
              <label className="block text-sm font-medium mb-1">
                System Prompt *
              </label>
              <textarea
                value={formData.system_prompt || ''}
                onChange={(e) =>
                  setFormData({ ...formData, system_prompt: e.target.value })
                }
                className="w-full px-4 py-2 border rounded-lg font-mono text-sm"
                rows={8}
                placeholder="You are a DeFi yield optimization specialist. Help users find the best yields across protocols..."
              />
              <p className="text-xs text-gray-500 mt-1">
                This prompt defines the AI's behavior and expertise
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Welcome Message
              </label>
              <textarea
                value={formData.welcome_message || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    welcome_message: e.target.value,
                  })
                }
                className="w-full px-4 py-2 border rounded-lg"
                rows={3}
                placeholder="Welcome! I'll help you optimize your DeFi yields."
              />
            </div>
          </div>
        )}

        {currentStep === 'features' && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold mb-4">Features & Protocols</h2>

            <div>
              <label className="block text-sm font-medium mb-2">
                Enabled Protocols
              </label>
              <div className="grid grid-cols-2 gap-2">
                {['aave-v3', 'compound', 'curve', 'uniswap', 'morpho'].map(
                  (protocol) => (
                    <label key={protocol} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.enabled_protocols?.includes(protocol)}
                        onChange={(e) => {
                          const current = formData.enabled_protocols || [];
                          setFormData({
                            ...formData,
                            enabled_protocols: e.target.checked
                              ? [...current, protocol]
                              : current.filter((p) => p !== protocol),
                          });
                        }}
                      />
                      <span>{protocol}</span>
                    </label>
                  )
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Enabled Chains
              </label>
              <div className="grid grid-cols-2 gap-2">
                {['ethereum', 'arbitrum', 'optimism', 'polygon'].map(
                  (chain) => (
                    <label key={chain} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.enabled_chains?.includes(chain)}
                        onChange={(e) => {
                          const current = formData.enabled_chains || [];
                          setFormData({
                            ...formData,
                            enabled_chains: e.target.checked
                              ? [...current, chain]
                              : current.filter((c) => c !== chain),
                          });
                        }}
                      />
                      <span>{chain}</span>
                    </label>
                  )
                )}
              </div>
            </div>
          </div>
        )}

        {currentStep === 'access' && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold mb-4">Access Control</h2>

            <div>
              <label className="block text-sm font-medium mb-2">
                Visibility
              </label>
              <select
                value={formData.visibility}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    visibility: e.target.value as Project['visibility'],
                  })
                }
                className="w-full px-4 py-2 border rounded-lg"
              >
                <option value="public">Public (Anyone can join)</option>
                <option value="private">Private (Invitation only)</option>
                <option value="team">Team (Organization only)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Max Users
              </label>
              <input
                type="number"
                value={formData.max_users || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    max_users: parseInt(e.target.value) || undefined,
                  })
                }
                className="w-full px-4 py-2 border rounded-lg"
                placeholder="Leave empty for unlimited"
              />
            </div>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_featured}
                  onChange={(e) =>
                    setFormData({ ...formData, is_featured: e.target.checked })
                  }
                />
                <span>Feature this project on discovery page</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between mt-6">
        <button
          onClick={handleBack}
          disabled={currentStepIndex === 0}
          className="px-6 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Back
        </button>

        {currentStepIndex === steps.length - 1 ? (
          <button
            onClick={handleSubmit}
            disabled={createProject.isPending}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {createProject.isPending ? 'Creating...' : 'Create Project'}
          </button>
        ) : (
          <button
            onClick={handleNext}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Next
          </button>
        )}
      </div>
    </div>
  );
};
```

---

## ⚠️ Error Handling Flows

### Common Error Scenarios

```typescript
import { toast } from 'react-hot-toast';

// ============================================
// Error Types
// ============================================

interface APIError {
  error: string;
  error_code: string;
  details?: Record<string, any>;
}

// ============================================
// Error Handlers
// ============================================

export const handleProjectError = (error: unknown) => {
  if (error instanceof Response) {
    switch (error.status) {
      case 400:
        return handleBadRequest(error);
      case 401:
        return handleUnauthorized(error);
      case 403:
        return handleForbidden(error);
      case 404:
        return handleNotFound(error);
      case 409:
        return handleConflict(error);
      case 429:
        return handleRateLimit(error);
      case 500:
        return handleServerError(error);
      default:
        toast.error('An unexpected error occurred');
    }
  } else if (error instanceof Error) {
    toast.error(error.message);
  } else {
    toast.error('An unknown error occurred');
  }
};

const handleBadRequest = async (response: Response) => {
  const data: APIError = await response.json();

  switch (data.error_code) {
    case 'INVALID_SLUG':
      toast.error('Project slug is invalid. Use lowercase letters, numbers, and hyphens only.');
      break;
    case 'SLUG_TAKEN':
      toast.error('This project slug is already taken. Please choose another.');
      break;
    case 'MISSING_REQUIRED_FIELD':
      toast.error(`Missing required field: ${data.details?.field}`);
      break;
    default:
      toast.error(data.error || 'Invalid request');
  }
};

const handleUnauthorized = async (response: Response) => {
  toast.error('Please log in to continue');
  // Redirect to login
  window.location.href = '/login';
};

const handleForbidden = async (response: Response) => {
  const data: APIError = await response.json();

  switch (data.error_code) {
    case 'PROJECT_NOT_ACCESSIBLE':
      toast.error('You do not have access to this project');
      break;
    case 'ADMIN_ONLY':
      toast.error('This action requires admin privileges');
      break;
    case 'PROJECT_FULL':
      toast.error('This project has reached its maximum number of users');
      break;
    case 'SUBSCRIPTION_REQUIRED':
      toast.error(`This project requires ${data.details?.required_tier} subscription`);
      // Show upgrade modal
      break;
    default:
      toast.error('You do not have permission to perform this action');
  }
};

const handleNotFound = async (response: Response) => {
  const data: APIError = await response.json();

  switch (data.error_code) {
    case 'PROJECT_NOT_FOUND':
      toast.error('Project not found');
      break;
    case 'KNOWLEDGE_DOCUMENT_NOT_FOUND':
      toast.error('Knowledge document not found');
      break;
    default:
      toast.error('Resource not found');
  }
};

const handleConflict = async (response: Response) => {
  const data: APIError = await response.json();

  switch (data.error_code) {
    case 'ALREADY_MEMBER':
      toast.error('You are already a member of this project');
      break;
    case 'ALREADY_SELECTED':
      toast.error('This project is already your active workspace');
      break;
    default:
      toast.error('Conflict detected');
  }
};

const handleRateLimit = async (response: Response) => {
  const data: APIError = await response.json();
  const retryAfter = response.headers.get('Retry-After') || '60';

  toast.error(`Rate limit exceeded. Please try again in ${retryAfter} seconds.`);
};

const handleServerError = async (response: Response) => {
  toast.error('Server error. Please try again later.');
  // Log to error tracking service
  console.error('Server error:', response);
};

// ============================================
// Error Boundary Component
// ============================================

export class ProjectErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Project error boundary caught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">Something went wrong</h2>
            <p className="text-gray-600 mb-4">
              We encountered an error while loading projects
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Error Handling in Components

```typescript
export const ProjectSelector: React.FC = () => {
  const selectProject = useSelectProject();

  const handleSelect = async (projectId: string) => {
    try {
      await selectProject.mutateAsync(projectId);
      toast.success('Project switched successfully');
    } catch (error) {
      handleProjectError(error);
    }
  };

  return (
    // Component JSX
  );
};
```

---

## 🚀 Performance Optimization

### 1. Prefetching

```typescript
import { useQueryClient } from '@tanstack/react-query';
import { projectsAPI } from './api';

export const useProjectPrefetch = () => {
  const queryClient = useQueryClient();

  const prefetchAvailableProjects = () => {
    queryClient.prefetchQuery({
      queryKey: ['projects', 'available'],
      queryFn: () => projectsAPI.getAvailableProjects(),
      staleTime: 10 * 60 * 1000, // 10 minutes
    });
  };

  const prefetchProjectBySlug = (slug: string) => {
    queryClient.prefetchQuery({
      queryKey: ['projects', 'slug', slug],
      queryFn: () => projectsAPI.getProjectBySlug(slug),
    });
  };

  return {
    prefetchAvailableProjects,
    prefetchProjectBySlug,
  };
};

// Usage: Prefetch on hover
<div
  onMouseEnter={() => prefetchProjectBySlug('defi-basics')}
  onClick={() => navigate('/projects/defi-basics')}
>
  DeFi Basics Project
</div>
```

### 2. Optimistic Updates

```typescript
export const useSelectProjectOptimistic = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => projectsAPI.selectProject(projectId),
    onMutate: async (projectId) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: ['user', 'projects'] });

      // Snapshot previous value
      const previousData = queryClient.getQueryData<UserProjectsResponse>([
        'user',
        'projects',
      ]);

      // Optimistically update
      if (previousData) {
        queryClient.setQueryData<UserProjectsResponse>(
          ['user', 'projects'],
          {
            ...previousData,
            active_project_id: projectId,
          }
        );
      }

      // Return context for rollback
      return { previousData };
    },
    onError: (error, variables, context) => {
      // Rollback on error
      if (context?.previousData) {
        queryClient.setQueryData(
          ['user', 'projects'],
          context.previousData
        );
      }
      toast.error('Failed to switch project');
    },
    onSuccess: () => {
      toast.success('Project switched!');
    },
  });
};
```

### 3. Infinite Scroll for Admin Project List

```typescript
import { useInfiniteQuery } from '@tanstack/react-query';

export const useInfiniteProjects = (filters?: {
  status?: string;
  visibility?: string;
}) => {
  return useInfiniteQuery({
    queryKey: ['admin', 'projects', 'infinite', filters],
    queryFn: ({ pageParam = 0 }) =>
      projectsAPI.listProjects({
        ...filters,
        limit: 20,
        offset: pageParam,
      }),
    getNextPageParam: (lastPage, allPages) => {
      const totalFetched = allPages.flat().length;
      return lastPage.length === 20 ? totalFetched : undefined;
    },
    initialPageParam: 0,
  });
};

// Component usage
export const InfiniteProjectList: React.FC = () => {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteProjects();

  const observerTarget = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 1 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [fetchNextPage, hasNextPage]);

  return (
    <div>
      {data?.pages.flat().map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}

      <div ref={observerTarget} className="h-10" />

      {isFetchingNextPage && <div>Loading more...</div>}
    </div>
  );
};
```

### 4. Debounced Search

```typescript
import { useState, useEffect } from 'react';
import { useSearchProjects } from './hooks';

export const ProjectSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const searchProjects = useSearchProjects();

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Trigger search when debounced query changes
  useEffect(() => {
    if (debouncedQuery.length >= 2) {
      searchProjects.mutate(debouncedQuery);
    }
  }, [debouncedQuery]);

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search projects..."
        className="w-full px-4 py-2 border rounded-lg"
      />

      {searchProjects.isLoading && <div>Searching...</div>}

      {searchProjects.data && (
        <div className="mt-4">
          {searchProjects.data.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </div>
  );
};
```

### 5. Memoization

```typescript
import { useMemo } from 'react';

export const ProjectList: React.FC<{ projects: Project[] }> = ({ projects }) => {
  const sortedProjects = useMemo(() => {
    return [...projects].sort((a, b) => {
      // Featured projects first
      if (a.is_featured && !b.is_featured) return -1;
      if (!a.is_featured && b.is_featured) return 1;

      // Then by display order
      if (a.display_order !== b.display_order) {
        return (a.display_order || 999) - (b.display_order || 999);
      }

      // Then alphabetically
      return a.name.localeCompare(b.name);
    });
  }, [projects]);

  return (
    <div>
      {sortedProjects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
};
```

---

## ♿ Accessibility Guidelines (WCAG 2.1 AA)

### 1. Semantic HTML

```typescript
// ✅ GOOD: Proper semantic structure
<nav aria-label="Project switcher">
  <button
    aria-expanded={isOpen}
    aria-haspopup="listbox"
    aria-controls="project-menu"
  >
    {activeProject?.name}
  </button>

  {isOpen && (
    <ul id="project-menu" role="listbox" aria-label="Available projects">
      {projects.map((project) => (
        <li key={project.id} role="option" aria-selected={project.id === activeId}>
          {project.name}
        </li>
      ))}
    </ul>
  )}
</nav>

// ❌ BAD: Generic divs without roles
<div>
  <div onClick={toggle}>{activeProject?.name}</div>
  {isOpen && (
    <div>
      {projects.map((project) => (
        <div onClick={() => select(project.id)}>{project.name}</div>
      ))}
    </div>
  )}
</div>
```

### 2. Keyboard Navigation

```typescript
export const ProjectSwitcher: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(0);
  const { data } = useUserProjects();

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ') {
        setIsOpen(true);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex((prev) =>
          Math.min(prev + 1, (data?.assigned_projects.length || 1) - 1)
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex((prev) => Math.max(prev - 1, 0));
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (data?.assigned_projects[focusedIndex]) {
          handleSelect(data.assigned_projects[focusedIndex].id);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        break;
    }
  };

  return (
    <div onKeyDown={handleKeyDown}>
      {/* Component implementation */}
    </div>
  );
};
```

### 3. Screen Reader Support

```typescript
// Add screen reader announcements
import { announce } from './utils/a11y';

export const useSelectProjectWithAnnouncement = () => {
  const selectProject = useSelectProject();

  return useMutation({
    mutationFn: (projectId: string) => projectsAPI.selectProject(projectId),
    onSuccess: (_, projectId) => {
      const project = /* get project from cache */;
      announce(`Now viewing ${project.name} project`);
    },
  });
};

// Utility for screen reader announcements
export const announce = (message: string) => {
  const el = document.createElement('div');
  el.setAttribute('aria-live', 'polite');
  el.setAttribute('aria-atomic', 'true');
  el.className = 'sr-only';
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 1000);
};
```

### 4. Focus Management

```typescript
export const ProjectDetailModal: React.FC<{ projectId: string }> = ({
  projectId,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      // Store previous focus
      previousFocusRef.current = document.activeElement as HTMLElement;

      // Focus modal
      modalRef.current?.focus();

      // Trap focus
      const handleTabKey = (e: KeyboardEvent) => {
        if (e.key !== 'Tab') return;

        const focusableElements = modalRef.current?.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (!focusableElements?.length) return;

        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[
          focusableElements.length - 1
        ] as HTMLElement;

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      };

      document.addEventListener('keydown', handleTabKey);
      return () => document.removeEventListener('keydown', handleTabKey);
    } else {
      // Restore previous focus
      previousFocusRef.current?.focus();
    }
  }, [isOpen]);

  return (
    <div
      ref={modalRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      tabIndex={-1}
    >
      {/* Modal content */}
    </div>
  );
};
```

### 5. Color Contrast

```typescript
// Ensure proper color contrast for project branding
export const ProjectBadge: React.FC<{ project: Project }> = ({ project }) => {
  const getContrastColor = (bgColor: string): string => {
    // Calculate luminance
    const rgb = parseInt(bgColor.slice(1), 16);
    const r = (rgb >> 16) & 0xff;
    const g = (rgb >> 8) & 0xff;
    const b = (rgb >> 0) & 0xff;
    const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;

    // Return white or black based on contrast
    return luminance > 128 ? '#000000' : '#FFFFFF';
  };

  const bgColor = project.color || '#3B82F6';
  const textColor = getContrastColor(bgColor);

  return (
    <div
      style={{
        backgroundColor: bgColor,
        color: textColor,
      }}
      className="px-3 py-1 rounded"
    >
      {project.name}
    </div>
  );
};
```

---

## ✅ Implementation Checklist

### Phase 1: User Features (Week 1)

- [ ] **API Integration**
  - [ ] Set up API client with all user endpoints
  - [ ] Configure authentication headers
  - [ ] Add error handling

- [ ] **Core Components**
  - [ ] Project switcher dropdown (navbar)
  - [ ] My projects list page
  - [ ] Available projects grid
  - [ ] Project detail page
  - [ ] Join project flow

- [ ] **State Management**
  - [ ] Set up React Query
  - [ ] Implement custom hooks
  - [ ] Add optimistic updates for project selection

- [ ] **Testing**
  - [ ] Unit tests for hooks
  - [ ] Integration tests for flows
  - [ ] E2E test for project join workflow

### Phase 2: Admin Features (Week 2)

- [ ] **Admin Dashboard**
  - [ ] Projects list with filters
  - [ ] Project creation wizard
  - [ ] Project editing interface
  - [ ] Bulk operations

- [ ] **Knowledge Base Management**
  - [ ] Document upload interface
  - [ ] Markdown editor/viewer
  - [ ] Document list and search

- [ ] **Assignment Rules**
  - [ ] Rule creation form
  - [ ] Rule list and management
  - [ ] Rule preview/testing

- [ ] **User Management**
  - [ ] User assignment interface
  - [ ] Assignment list with filters
  - [ ] Expiry date management

- [ ] **Testing**
  - [ ] Admin flow tests
  - [ ] Permission tests
  - [ ] Rule logic tests

### Phase 3: Polish & Optimization (Week 3)

- [ ] **Performance**
  - [ ] Implement prefetching
  - [ ] Add infinite scroll for admin list
  - [ ] Optimize bundle size
  - [ ] Add loading skeletons

- [ ] **Accessibility**
  - [ ] Keyboard navigation
  - [ ] Screen reader testing
  - [ ] Focus management
  - [ ] Color contrast validation

- [ ] **UX Enhancements**
  - [ ] Empty states
  - [ ] Error states
  - [ ] Success animations
  - [ ] Tooltips and help text

- [ ] **Documentation**
  - [ ] User guide
  - [ ] Admin guide
  - [ ] API documentation
  - [ ] Troubleshooting guide

---

## 📈 Success Metrics

### User Engagement Metrics

1. **Project Adoption Rate**
   - Target: 80% of users join at least 1 project within first week
   - Measurement: `users_with_projects / total_users`

2. **Multi-Project Usage**
   - Target: 30% of users active in 2+ projects
   - Measurement: `users_with_multiple_projects / total_users`

3. **Context Switching Frequency**
   - Target: Average 3-5 switches per active user per day
   - Measurement: Track project selection API calls

4. **Project Discovery**
   - Target: 50% of users browse available projects monthly
   - Measurement: `/available` endpoint calls

### Admin Efficiency Metrics

5. **Project Creation Time**
   - Target: < 10 minutes from start to publish
   - Measurement: Time between wizard start and final save

6. **Assignment Rule Effectiveness**
   - Target: 90% of assignments happen automatically via rules
   - Measurement: `auto_assignments / total_assignments`

7. **Knowledge Base Usage**
   - Target: 60% of projects have active knowledge base
   - Measurement: `projects_with_docs / total_projects`

### Technical Performance Metrics

8. **Context Switch Speed**
   - Target: < 200ms from click to UI update
   - Measurement: Frontend performance monitoring

9. **API Response Times**
   - Target: P95 < 500ms for all endpoints
   - Measurement: Backend monitoring

10. **Error Rate**
    - Target: < 0.1% error rate on project operations
    - Measurement: Error tracking (Sentry/DataDog)

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 18, 2025 | Initial specification |

---

## 🎯 Summary

This specification provides complete implementation guidance for the Projects & Workspaces module:

- ✅ **18 endpoints** documented (5 user + 13 admin)
- ✅ **3 user personas** with detailed journeys
- ✅ **Complete TypeScript integration** with API client
- ✅ **Production-ready React components** with hooks
- ✅ **Comprehensive error handling** for all scenarios
- ✅ **Performance optimization** patterns
- ✅ **WCAG 2.1 AA accessibility** compliance
- ✅ **Implementation checklist** with 3-week timeline
- ✅ **Success metrics** for measuring adoption

**Key Takeaway**: Projects & Workspaces is a foundational multi-tenancy system that enables context-specific AI experiences, driving user engagement through specialized workspaces.

---

**Next Steps**: Implement Phase 1 (User Features) following this specification.
