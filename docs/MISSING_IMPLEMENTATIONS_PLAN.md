# Missing Backend Implementations Plan

**Date**: December 1, 2025  
**Status**: PLAN READY  
**Estimated Effort**: 4-6 weeks  
**Priority**: MEDIUM-HIGH

---

## 🎯 Plan Overview

While we've implemented the core GraphRAG, ML, and WebSocket systems, some frontend use cases require additional backend endpoints and features. This plan identifies and prioritizes missing implementations.

**Goal**: Complete all backend endpoints needed for full frontend feature coverage.

---

## 📊 Current Implementation Status

```
╔═══════════════════════════════════════════════════════════╗
║           BACKEND IMPLEMENTATION STATUS                   ║
╠═══════════════════════════════════════════════════════════╣
║  Core API (Account, Auth, Admin):    ████████████  100%  ║
║  Subscription & Payment:              ████████████  100%  ║
║  LLM Orchestration:                   ████████████  100%  ║
║  Distillation:                        ████████████  100%  ║
║  Projects:                            ████████████  100%  ║
║  GraphRAG Core:                       ████████████  100%  ║
║  ML Prediction:                       ████████████  100%  ║
║  Network Analysis:                    ████████████  100%  ║
║  WebSocket:                           ████████████  100%  ║
║  Data Sources (Basic):                ████████████  100%  ║
║                                                            ║
║  Chat Integration:                    ██████░░░░░░  60%   ║
║  Portfolio Endpoints:                 ████░░░░░░░░  40%   ║
║  User Preferences:                    ░░░░░░░░░░░░   0%   ║
║  Notification System:                 ████░░░░░░░░  40%   ║
║  Search History:                      ░░░░░░░░░░░░   0%   ║
║  Dashboard Aggregation:               ████░░░░░░░░  40%   ║
║  Real-Time Event Broadcasting:        ██████░░░░░░  60%   ║
║  Admin Graph Management:              ████░░░░░░░░  40%   ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 📋 Phase 1: Chat & Conversation Features (Week 1)

### **1.1 Chat-GraphRAG Integration**
**Priority**: HIGH  
**Status**: ❌ Missing

**What's Needed**:
```python
# src/app/application/chat/graph_search_handler.py
class ChatGraphSearchHandler:
    """Handle GraphRAG searches from chat messages"""
    
    async def search_protocols_from_chat(
        self,
        message: str,
        user_context: UserContext,
    ) -> GraphSearchResult:
        """
        Extract search intent and perform hybrid search
        
        Returns search results formatted for chat
        """
        pass

# src/app/application/chat/risk_insights_handler.py
class ChatRiskInsightsHandler:
    """Handle risk analysis requests from chat"""
    
    async def get_protocol_risk_from_chat(
        self,
        protocol_name: str,
        conversation_id: str,
    ) -> RiskInsightResponse:
        """Get risk insights for chat response"""
        pass
```

**New Endpoints**:
```
POST /api/v1/chat/search-protocols
POST /api/v1/chat/analyze-risk
POST /api/v1/chat/similar-protocols
```

**Estimated Lines**: ~400

---

### **1.2 Conversation History with GraphRAG Context**
**Priority**: MEDIUM  
**Status**: ⚠️ Partial (basic conversation exists)

**What's Needed**:
```python
# Enhance existing conversation repository
class ConversationRepository:
    async def save_graph_context(
        self,
        conversation_id: UUID,
        protocol_ids: List[UUID],
        search_queries: List[str],
    ) -> None:
        """Save GraphRAG context for conversation"""
        pass
    
    async def get_conversation_protocols(
        self,
        conversation_id: UUID,
    ) -> List[ProtocolContext]:
        """Get protocols discussed in conversation"""
        pass
```

**Database Changes**:
```sql
-- Add to existing conversations table
ALTER TABLE conversations ADD COLUMN graph_context JSONB;

-- Index for querying
CREATE INDEX idx_conversations_graph_context 
ON conversations USING gin(graph_context);
```

**Estimated Lines**: ~200

---

## 📋 Phase 2: Portfolio & User Data (Week 2)

### **2.1 Portfolio Risk Aggregation**
**Priority**: HIGH  
**Status**: ❌ Missing

**What's Needed**:
```python
# src/app/application/portfolio/portfolio_risk.py
class PortfolioRiskAnalysis:
    """Aggregate risk analysis for user's portfolio"""
    
    async def get_portfolio_risk(
        self,
        user_id: UUID,
    ) -> PortfolioRiskSummary:
        """
        Calculate aggregate risk for user's protocols
        
        Includes:
        - Overall risk score
        - Risk distribution
        - Dependency risks
        - Recommendations
        """
        pass
    
    async def simulate_portfolio_cascade(
        self,
        user_id: UUID,
        origin_protocol_id: UUID,
    ) -> PortfolioCascadeResult:
        """Simulate cascade impact on user's portfolio"""
        pass

@dataclass
class PortfolioRiskSummary:
    user_id: UUID
    overall_risk_score: float
    risk_distribution: Dict[str, float]  # LOW/MEDIUM/HIGH/CRITICAL
    protocols_at_risk: List[ProtocolRisk]
    dependency_risks: List[DependencyRisk]
    systemic_risk_score: float
    recommendations: List[str]
    last_updated: datetime
```

**New Endpoints**:
```
GET /api/v1/portfolio/risk
POST /api/v1/portfolio/risk/simulate-cascade
GET /api/v1/portfolio/protocols/:id/dependencies
```

**Estimated Lines**: ~500

---

### **2.2 User Portfolio Tracking**
**Priority**: HIGH  
**Status**: ⚠️ Partial (wallet exists, not protocol tracking)

**What's Needed**:
```python
# src/app/domain/entities/user_portfolio.py
class UserPortfolio(BaseEntity):
    """Track user's protocol exposures"""
    
    user_id: UUID
    protocols: List[ProtocolExposure]
    chains: List[str]
    total_value_usd: Decimal
    risk_profile: str  # conservative/moderate/aggressive
    preferences: PortfolioPreferences
    created_at: datetime
    updated_at: datetime

@dataclass
class ProtocolExposure:
    protocol_id: UUID
    protocol_name: str
    value_usd: Decimal
    percentage: float
    chain: str
    position_type: str  # supply/borrow/stake/lp
```

**New Endpoints**:
```
GET /api/v1/users/me/portfolio
POST /api/v1/users/me/portfolio/track-protocol
DELETE /api/v1/users/me/portfolio/protocols/:id
GET /api/v1/users/me/portfolio/summary
```

**Database Changes**:
```sql
CREATE TABLE user_portfolios (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    protocol_id UUID,
    protocol_name VARCHAR(255),
    value_usd DECIMAL(20, 2),
    percentage FLOAT,
    chain VARCHAR(50),
    position_type VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_user_portfolios_user_id ON user_portfolios(user_id);
```

**Estimated Lines**: ~600

---

### **2.3 User Preferences & Filters**
**Priority**: MEDIUM  
**Status**: ❌ Missing

**What's Needed**:
```python
# src/app/domain/entities/user_preferences.py
class UserPreferences(BaseEntity):
    """User's GraphRAG search and notification preferences"""
    
    user_id: UUID
    risk_tolerance: str  # conservative/moderate/aggressive
    preferred_chains: List[str]
    preferred_categories: List[str]
    excluded_protocols: List[UUID]
    notification_settings: NotificationPreferences
    search_settings: SearchPreferences

@dataclass
class SearchPreferences:
    default_similarity_threshold: float
    default_risk_filter: Optional[str]
    saved_searches: List[SavedSearch]
    search_history_enabled: bool
```

**New Endpoints**:
```
GET /api/v1/users/me/preferences
PUT /api/v1/users/me/preferences
GET /api/v1/users/me/preferences/search
PUT /api/v1/users/me/preferences/search
```

**Database Changes**:
```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) UNIQUE,
    risk_tolerance VARCHAR(50),
    preferred_chains JSONB,
    preferred_categories JSONB,
    excluded_protocols JSONB,
    notification_settings JSONB,
    search_settings JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Estimated Lines**: ~400

---

## 📋 Phase 3: Search & Discovery (Week 3)

### **3.1 Search History & Saved Searches**
**Priority**: MEDIUM  
**Status**: ❌ Missing

**What's Needed**:
```python
# src/app/application/search/search_history.py
class SearchHistoryService:
    """Manage user's search history"""
    
    async def save_search(
        self,
        user_id: UUID,
        query: str,
        results: List[ProtocolSearchResult],
        filters: Optional[Dict],
    ) -> SearchHistoryEntry:
        """Save search to history"""
        pass
    
    async def get_search_history(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> List[SearchHistoryEntry]:
        """Get user's search history"""
        pass
    
    async def save_search_preset(
        self,
        user_id: UUID,
        name: str,
        query: str,
        filters: Dict,
    ) -> SavedSearch:
        """Save search as preset"""
        pass
```

**New Endpoints**:
```
GET /api/v1/search/history
POST /api/v1/search/history
DELETE /api/v1/search/history/:id
POST /api/v1/search/saved
GET /api/v1/search/saved
DELETE /api/v1/search/saved/:id
```

**Database Changes**:
```sql
CREATE TABLE search_history (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    query TEXT,
    results_count INTEGER,
    filters JSONB,
    created_at TIMESTAMP
);

CREATE TABLE saved_searches (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255),
    query TEXT,
    filters JSONB,
    created_at TIMESTAMP
);

CREATE INDEX idx_search_history_user_id ON search_history(user_id, created_at DESC);
```

**Estimated Lines**: ~400

---

### **3.2 Protocol Comparison**
**Priority**: MEDIUM  
**Status**: ❌ Missing

**What's Needed**:
```python
# src/app/application/graph/protocol_comparison.py
class ProtocolComparisonService:
    """Compare multiple protocols side-by-side"""
    
    async def compare_protocols(
        self,
        protocol_ids: List[UUID],
    ) -> ProtocolComparison:
        """
        Compare protocols across dimensions:
        - Risk scores
        - TVL
        - Dependencies
        - Audits
        - Centrality metrics
        """
        pass

@dataclass
class ProtocolComparison:
    protocols: List[ProtocolDetail]
    comparison_matrix: Dict[str, List[Any]]
    winner_by_metric: Dict[str, UUID]
    recommendations: str
```

**New Endpoints**:
```
POST /api/v1/protocols/compare
{
  "protocol_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Estimated Lines**: ~300

---

## 📋 Phase 4: Notifications & Alerts (Week 4)

### **4.1 Risk Alert System**
**Priority**: HIGH  
**Status**: ⚠️ Partial (basic notifications exist)

**What's Needed**:
```python
# src/app/application/notifications/risk_alerts.py
class RiskAlertService:
    """Generate and send risk alerts"""
    
    async def check_user_protocols_risk(
        self,
        user_id: UUID,
    ) -> List[RiskAlert]:
        """
        Check all user's protocols for risk changes
        
        Triggers:
        - Risk score increase >20%
        - Anomaly detected
        - Critical risk level reached
        - Dependency risk change
        """
        pass
    
    async def send_risk_alert(
        self,
        user_id: UUID,
        alert: RiskAlert,
    ) -> None:
        """Send risk alert via notification system"""
        pass

@dataclass
class RiskAlert:
    alert_id: UUID
    user_id: UUID
    protocol_id: UUID
    protocol_name: str
    alert_type: str  # risk_increase/anomaly/critical/dependency
    severity: str  # LOW/MEDIUM/HIGH/CRITICAL
    message: str
    details: Dict
    recommendations: List[str]
    created_at: datetime
```

**New Endpoints**:
```
GET /api/v1/alerts/risk
POST /api/v1/alerts/risk/subscribe
DELETE /api/v1/alerts/risk/:id
PUT /api/v1/alerts/risk/:id/acknowledge
```

**Background Task**:
```python
@celery_app.task(name="check_user_risk_alerts")
def check_user_risk_alerts():
    """
    Scheduled task (every 15 minutes)
    Check all users' protocols for risk changes
    """
    pass
```

**Database Changes**:
```sql
CREATE TABLE risk_alerts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    protocol_id UUID,
    protocol_name VARCHAR(255),
    alert_type VARCHAR(50),
    severity VARCHAR(20),
    message TEXT,
    details JSONB,
    recommendations JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);

CREATE INDEX idx_risk_alerts_user_id ON risk_alerts(user_id, created_at DESC);
```

**Estimated Lines**: ~500

---

### **4.2 WebSocket Event Broadcasting Enhancement**
**Priority**: HIGH  
**Status**: ⚠️ Partial (structure exists, needs event generation)

**What's Needed**:
```python
# src/app/infrastructure/websocket/event_broadcaster.py
class GraphEventBroadcaster:
    """Broadcast graph events to WebSocket subscribers"""
    
    async def broadcast_protocol_update(
        self,
        protocol_id: UUID,
        protocol_name: str,
        changes: Dict[str, Any],
    ) -> None:
        """Broadcast protocol update event"""
        await publish_graph_event('graph:protocol_update', {
            'protocol_id': str(protocol_id),
            'protocol_name': protocol_name,
            'changes': changes,
            'timestamp': datetime.utcnow().timestamp(),
        })
    
    async def broadcast_risk_alert(
        self,
        alert: RiskAlert,
    ) -> None:
        """Broadcast risk alert to subscribed users"""
        await publish_graph_event('graph:risk_alert', {
            'alert_id': str(alert.alert_id),
            'protocol_id': str(alert.protocol_id),
            'severity': alert.severity,
            'message': alert.message,
            'timestamp': datetime.utcnow().timestamp(),
        })
```

**Integration Points**:
- Call from data sync tasks
- Call from risk alert service
- Call from graph update operations

**Estimated Lines**: ~200

---

## 📋 Phase 5: Dashboard Aggregations (Week 5)

### **5.1 User Dashboard Data Aggregation**
**Priority**: HIGH  
**Status**: ⚠️ Partial (basic endpoint exists, needs GraphRAG/ML)

**What's Needed**:
```python
# src/app/application/dashboard/user_dashboard.py
class UserDashboardService:
    """Aggregate data for user dashboard"""
    
    async def get_dashboard_data(
        self,
        user_id: UUID,
    ) -> DashboardData:
        """
        Aggregate all dashboard data:
        - Portfolio summary
        - GraphRAG insights
        - ML risk alerts
        - Recent activity
        - Recommendations
        - Real-time updates
        """
        pass

@dataclass
class DashboardData:
    portfolio: PortfolioSummary
    graphrag_insights: List[GraphInsight]
    risk_alerts: List[RiskAlert]
    recent_activity: List[Transaction]
    recommendations: List[Recommendation]
    market_highlights: List[MarketHighlight]
```

**Enhanced Endpoint**:
```
GET /api/v1/users/me/dashboard
// Already exists, enhance with GraphRAG/ML data
```

**Estimated Lines**: ~400

---

### **5.2 AI Insights Generation**
**Priority**: MEDIUM  
**Status**: ❌ Missing

**What's Needed**:
```python
# src/app/application/insights/ai_insights.py
class AIInsightsGenerator:
    """Generate AI-powered insights for users"""
    
    async def generate_portfolio_insights(
        self,
        user_id: UUID,
    ) -> List[Insight]:
        """
        Generate insights based on:
        - Portfolio composition
        - Risk profile
        - Market conditions
        - GraphRAG analysis
        - ML predictions
        """
        pass
    
    async def generate_protocol_recommendations(
        self,
        user_id: UUID,
        preferences: UserPreferences,
    ) -> List[ProtocolRecommendation]:
        """Recommend protocols based on user preferences"""
        pass

@dataclass
class Insight:
    insight_id: UUID
    insight_type: str  # opportunity/warning/optimization
    title: str
    message: str
    affected_protocols: List[UUID]
    potential_impact: str
    action_url: Optional[str]
    priority: str
    expires_at: datetime
```

**New Endpoints**:
```
GET /api/v1/insights
POST /api/v1/insights/:id/dismiss
GET /api/v1/insights/recommendations
```

**Estimated Lines**: ~500

---

## 📋 Phase 6: Admin Features (Week 6)

### **6.1 Graph Node Management UI Endpoints**
**Priority**: MEDIUM  
**Status**: ⚠️ Partial (validation exists, not full CRUD)

**What's Needed**:
```python
# src/app/application/admin/graph_management.py
class GraphManagementService:
    """Admin tools for graph management"""
    
    async def list_nodes(
        self,
        node_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[GraphNode]:
        """List graph nodes with pagination"""
        pass
    
    async def update_node_properties(
        self,
        node_id: UUID,
        properties: Dict[str, Any],
    ) -> GraphNode:
        """Update node properties"""
        pass
    
    async def create_relationship(
        self,
        source_id: UUID,
        target_id: UUID,
        relationship_type: str,
        properties: Optional[Dict] = None,
    ) -> GraphEdge:
        """Create new graph relationship"""
        pass
    
    async def delete_relationship(
        self,
        source_id: UUID,
        target_id: UUID,
        relationship_type: str,
    ) -> None:
        """Delete graph relationship"""
        pass
```

**New Endpoints**:
```
GET /api/v1/admin/graph/nodes
GET /api/v1/admin/graph/nodes/:id
PUT /api/v1/admin/graph/nodes/:id
POST /api/v1/admin/graph/relationships
DELETE /api/v1/admin/graph/relationships/:id
GET /api/v1/admin/graph/orphaned-nodes
```

**Estimated Lines**: ~600

---

### **6.2 Data Source Sync Management**
**Priority**: LOW  
**Status**: ⚠️ Partial (background tasks exist, no admin UI)

**What's Needed**:
```python
# src/app/application/admin/data_sync.py
class DataSyncManagementService:
    """Admin tools for data source management"""
    
    async def get_sync_status(self) -> Dict[str, SyncStatus]:
        """Get status of all data sources"""
        pass
    
    async def trigger_manual_sync(
        self,
        source: str,  # defillama/thegraph/oneinch
    ) -> SyncJob:
        """Trigger manual data sync"""
        pass
    
    async def get_sync_history(
        self,
        source: Optional[str] = None,
        limit: int = 50,
    ) -> List[SyncHistoryEntry]:
        """Get sync history"""
        pass
```

**New Endpoints**:
```
GET /api/v1/admin/datasources/status
POST /api/v1/admin/datasources/:source/sync
GET /api/v1/admin/datasources/history
GET /api/v1/admin/datasources/:source/config
PUT /api/v1/admin/datasources/:source/config
```

**Estimated Lines**: ~400

---

## 📊 Total Implementation Effort

```
╔═══════════════════════════════════════════════════════════╗
║         MISSING IMPLEMENTATIONS EFFORT ESTIMATE           ║
╠═══════════════════════════════════════════════════════════╣
║  Phase 1: Chat Integration (2 features)     Week 1       ║
║  Phase 2: Portfolio & User Data (3)         Week 2       ║
║  Phase 3: Search & Discovery (2)            Week 3       ║
║  Phase 4: Notifications & Alerts (2)        Week 4       ║
║  Phase 5: Dashboard Aggregations (2)        Week 5       ║
║  Phase 6: Admin Features (2)                Week 6       ║
║                                                           ║
║  Total New Services:                 13                  ║
║  Total New Endpoints:                ~40                 ║
║  Total New Database Tables:          7                   ║
║  Total New Background Tasks:         2                   ║
║  Total Estimated Lines:              ~4,900              ║
║                                                           ║
║  Estimated Duration:                 4-6 weeks           ║
║  Required Role:                      Backend Engineer    ║
╚═══════════════════════════════════════════════════════════╝
```

---

## 🎯 Implementation Priority

### **CRITICAL (Must Have for MVP)**:
1. Portfolio Risk Aggregation
2. User Portfolio Tracking
3. Risk Alert System
4. WebSocket Event Broadcasting
5. Chat-GraphRAG Integration

### **IMPORTANT (Should Have)**:
6. User Preferences & Filters
7. Dashboard Data Aggregation
8. Search History
9. AI Insights Generation

### **NICE TO HAVE**:
10. Protocol Comparison
11. Graph Node Management UI
12. Data Source Sync Management
13. Conversation History Enhancement

---

## 📝 Database Migration Strategy

**Total New Tables**: 7

1. `user_portfolios`
2. `user_preferences`
3. `search_history`
4. `saved_searches`
5. `risk_alerts`
6. `ai_insights`
7. `sync_history`

**Migration Files Needed**:
- `20251202_005_add_portfolio_tracking.py`
- `20251202_006_add_user_preferences.py`
- `20251202_007_add_search_features.py`
- `20251202_008_add_risk_alerts.py`
- `20251202_009_add_ai_insights.py`

---

## 🎯 Success Criteria

✅ **All critical user flows** supported by backend  
✅ **Real-time updates** working for all features  
✅ **Portfolio tracking** fully functional  
✅ **Risk alerts** generated and delivered  
✅ **Chat integration** with GraphRAG working  
✅ **Admin tools** for graph management  
✅ **Performance** maintained (<500ms response time)  

---

**Next Step**: Prioritize and begin Phase 1 implementation.
