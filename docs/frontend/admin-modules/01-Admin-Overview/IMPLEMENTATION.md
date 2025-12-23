# Admin Overview Module Implementation

> **Complete TypeScript/React Implementation for Admin Overview Module**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)

## 📖 Module Overview

The **Admin Overview** module is the landing page for the Admin Console. It provides high-level visibility into system performance and security, answering the question: **"Is the system healthy and performing?"**

### Key Capabilities
1. **Chat Analytics Dashboard**: Usage volume, agent performance, and cost tracking
2. **Security Dashboard**: Vulnerability scan results and security health status
3. **Real-time Updates**: WebSocket connections for live metrics and alerts
4. **Export Capabilities**: Export dashboard data in JSON/CSV formats

### Business Value
- **Visibility**: At-a-glance system health and security status
- **Alerting**: Critical security alerts take precedence
- **Performance Monitoring**: Real-time metrics for system performance
- **Cost Awareness**: Track spending and usage trends
- **Decision Support**: Data-driven insights for operational decisions

---

## 🎨 UX/UI Specifications

### Design Principles (First Principles Analysis)

**Essential Problem**: Admins need immediate visibility into system health and security without information overload.

**Root Cause Analysis**:
- **Information Overload**: Too much data causes decision paralysis
- **Solution**: Dashboard layout with "Sparkline" cards, prioritized alerts, drill-down capabilities

**Design Decisions**:
1. **Dashboard Layout**: Grid-based layout with summary cards at the top
2. **Priority System**: Security "Critical" alerts must take precedence over everything else
3. **Progressive Disclosure**: Summary cards → Detailed views → Full reports
4. **Visual Hierarchy**: Color coding (red for critical, yellow for warnings, green for healthy)
5. **Real-time Updates**: WebSocket for live metrics without page refresh

### Trade-off Analysis (Design Thinking)

**Key Design Decisions with Trade-offs**:

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Grid Layout** | List Layout | Visual vs. Scannable | Grid provides better visual overview, but list is more scannable |
| **Sparkline Cards** | Full Charts | Overview vs. Detail | Sparklines provide quick trends without taking space |
| **Security Priority** | Equal Priority | Security vs. Performance | Security issues can cause data breaches; must be prioritized |
| **Real-time Updates** | Manual Refresh | Current vs. Performance | Real-time provides current data, but requires WebSocket connections |
| **Export Functionality** | View Only | Usability vs. Complexity | Export enables offline analysis, but adds UI complexity |

### Visual Design

#### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│              Admin Overview Dashboard                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Security     │  │ Chat Metrics │  │ System Health│  │
│  │ Status Card  │  │ Summary Card │  │ Summary Card │  │
│  │ [Critical]   │  │ [Active: 50] │  │ [CPU: 45%]   │  │
│  │ 🔴           │  │ 📈          │  │ ✅           │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │   Security Dashboard (if critical alerts)        │  │
│  │   - Latest scan results                           │  │
│  │   - Critical vulnerabilities                     │  │
│  │   - Attack statistics                            │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │   Chat Analytics Dashboard                        │  │
│  │   - Active conversations                          │  │
│  │   - Agent performance                             │  │
│  │   - Cost tracking                                 │  │
│  │   - Cache efficiency                              │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### Color Palette
- **Critical**: `#EF4444` (Red) - Security alerts, critical errors
- **Warning**: `#F59E0B` (Amber) - Warnings, degraded performance
- **Success**: `#10B981` (Green) - Healthy status, positive trends
- **Info**: `#3B82F6` (Blue) - Informational, neutral status
- **Background**: `#FFFFFF` (White) / `#F9FAFB` (Gray-50)
- **Card Background**: `#FFFFFF` with subtle shadow
- **Text Primary**: `#111827` (Gray-900)
- **Text Secondary**: `#6B7280` (Gray-500)

#### Typography
- **Dashboard Title**: Inter, 700 weight, 32px
- **Card Titles**: Inter, 600 weight, 18px
- **Metric Values**: Inter, 700 weight, 36px (large numbers)
- **Section Headings**: Inter, 600 weight, 20px
- **Body Text**: Inter, 400 weight, 16px
- **Labels**: Inter, 500 weight, 14px
- **Helper Text**: Inter, 400 weight, 12px

#### Component Specifications

##### Summary Card Component
```typescript
interface SummaryCardProps {
  title: string;
  value: string | number;
  trend?: 'up' | 'down' | 'stable';
  sparkline?: number[];
  status?: 'critical' | 'warning' | 'healthy' | 'info';
  onClick?: () => void;
  loading?: boolean;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  value,
  trend,
  sparkline,
  status = 'info',
  onClick,
  loading = false,
}) => {
  const statusColors = {
    critical: 'bg-red-50 border-red-200',
    warning: 'bg-amber-50 border-amber-200',
    healthy: 'bg-emerald-50 border-emerald-200',
    info: 'bg-gray-50 border-gray-200',
  };

  const statusIndicators = {
    critical: 'bg-red-500',
    warning: 'bg-amber-500',
    healthy: 'bg-emerald-500',
    info: 'bg-blue-500',
  };

  return (
    <div
      className={`
        relative p-6 rounded-lg border-2 transition-all
        ${statusColors[status]}
        ${onClick ? 'cursor-pointer hover:shadow-md' : ''}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-label={onClick ? `View ${title} details` : undefined}
    >
      {/* Status Indicator */}
      <div className={`absolute top-4 right-4 w-3 h-3 rounded-full ${statusIndicators[status]}`} />

      {/* Title */}
      <h3 className="text-sm font-medium text-gray-600 mb-2">{title}</h3>

      {/* Value */}
      <div className="text-3xl font-bold text-gray-900 mb-4">
        {loading ? <Skeleton className="h-9 w-24" /> : value}
      </div>

      {/* Sparkline */}
      {sparkline && (
        <div className="h-12 mb-2">
          <Sparkline data={sparkline} trend={trend} />
        </div>
      )}

      {/* Trend Indicator */}
      {trend && (
        <div className="flex items-center text-sm">
          <TrendIcon direction={trend} />
          <span className="ml-1 text-gray-600">vs last period</span>
        </div>
      )}
    </div>
  );
};
```

##### Security Alert Banner
```typescript
interface SecurityAlertBannerProps {
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  dismissible?: boolean;
  onDismiss?: () => void;
}

export const SecurityAlertBanner: React.FC<SecurityAlertBannerProps> = ({
  severity,
  title,
  description,
  actionLabel,
  onAction,
  dismissible = false,
  onDismiss,
}) => {
  const severityStyles = {
    critical: 'bg-red-600 text-white',
    high: 'bg-amber-500 text-white',
    medium: 'bg-yellow-400 text-gray-900',
    low: 'bg-blue-100 text-blue-900',
  };

  return (
    <div className={`${severityStyles[severity]} p-4 rounded-lg mb-4`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-semibold mb-1">{title}</h4>
          <p className="text-sm opacity-90">{description}</p>
          {actionLabel && onAction && (
            <button
              onClick={onAction}
              className="mt-2 px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded transition"
            >
              {actionLabel}
            </button>
          )}
        </div>
        {dismissible && onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 text-white opacity-75 hover:opacity-100"
            aria-label="Dismiss alert"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};
```

##### Sparkline Component
```typescript
interface SparklineProps {
  data: number[];
  trend?: 'up' | 'down' | 'stable';
  height?: number;
  color?: string;
}

export const Sparkline: React.FC<SparklineProps> = ({
  data,
  trend = 'stable',
  height = 40,
  color,
}) => {
  const colors = {
    up: '#10B981',
    down: '#EF4444',
    stable: '#6B7280',
  };

  const lineColor = color || colors[trend];
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 100 - ((value - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width="100%" height={height} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={lineColor}
        strokeWidth="2"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
};
```

### Responsive Breakpoints

**Mobile** (< 640px):
- Single column layout
- Stacked summary cards
- Collapsible dashboard sections
- Bottom navigation

**Tablet** (640px - 1024px):
- Two-column summary cards
- Side-by-side charts
- Expanded dashboard sections

**Desktop** (> 1024px):
- Three-column summary cards
- Full-width charts
- Detailed metric tables
- Sidebar for quick actions

### Accessibility Requirements

1. **Screen Readers**:
   - Announce security alerts immediately
   - Describe metric values and trends
   - Label all interactive elements
   - Announce status changes

2. **Keyboard Navigation**:
   - Tab through all cards
   - Enter to drill down into details
   - Escape to close modals
   - Arrow keys for chart navigation

3. **Color Contrast**:
   - All text: 4.5:1 minimum
   - Status indicators: 3:1 minimum
   - Charts: 3:1 minimum

### Loading States

**Initial Load**:
- Skeleton loaders for summary cards
- Shimmer effect for chart areas
- Progressive loading (security → chat → system)

**Data Refresh**:
- Subtle loading indicator in card header
- No full page reload
- Optimistic updates where possible

### Empty States

**No Data Available**:
- Illustration: Empty dashboard
- Message: "No data available for selected period"
- CTA: "Adjust date range" or "Refresh data"

**No Security Scans**:
- Message: "No security scans found"
- CTA: "Run Security Scan"

### Error States

**API Error**:
- Error card replacing data
- Message: "Unable to load dashboard data"
- Retry button
- Last known data (if available)

**WebSocket Connection Error**:
- Connection status indicator
- Fallback to polling
- "Reconnecting..." message

---

## 🔌 API Endpoints

### 1. Get Chat Dashboard

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date for analytics | 30 days ago |
| `date_to` | `datetime` | No | End date for analytics | Now |

#### Response

##### Success Response (200 OK)
```typescript
interface AdminChatDashboardSummaryResponse {
  date_from: string;                    // ISO 8601
  date_to: string;                       // ISO 8601
  total_conversations: number;
  total_messages: number;
  total_active_users: number;
  total_cost_usd: number;
  total_agent_invocations: number;
  most_used_agent: string;
  avg_success_rate: number;              // 0-1
  avg_response_time_ms: number;
  error_rate: number;                    // 0-1
  cache_hit_rate: number;                // 0-1
  top_agents: AgentLeaderboardEntry[];   // Top 5
  conversation_trend: TimeSeriesDataPoint[];
  cost_trend: TimeSeriesDataPoint[];
}
```

**JSON Example**:
```json
{
  "date_from": "2024-01-01T00:00:00Z",
  "date_to": "2024-01-15T10:30:00Z",
  "total_conversations": 1250,
  "total_messages": 8900,
  "total_active_users": 450,
  "total_cost_usd": 125.50,
  "total_agent_invocations": 5000,
  "most_used_agent": "swap_agent",
  "avg_success_rate": 0.987,
  "avg_response_time_ms": 1200,
  "error_rate": 0.005,
  "cache_hit_rate": 0.45,
  "top_agents": [...],
  "conversation_trend": [...],
  "cost_trend": [...]
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `500` | `Exception` | Internal server error | Show error: "Failed to load dashboard" + Retry |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service temporarily unavailable" + Retry |

---

### 2. Get Security Dashboard

**Method**: `GET`  
**Endpoint**: `/api/admin/security/dashboard`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface SecurityDashboardResponse {
  timestamp: string;                    // ISO 8601
  security_posture: {
    overall_score: number;             // 0-100
    level: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'CRITICAL';
  };
  latest_scan: {
    scan_id: string;
    scan_date: string;                   // ISO 8601
    status: 'completed' | 'running' | 'failed';
    vulnerabilities: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
  attack_statistics: {
    xss_attempts: {
      total: number;
      blocked: number;
    };
    prompt_injections: {
      total: number;
      blocked: number;
    };
  };
  total_scans: number;
  active_tools: string[];
  overall_status: 'healthy' | 'warning' | 'critical' | 'unknown';
}
```

---

### 3. Get Agent Performance

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard/agents/performance`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date | 30 days ago |
| `date_to` | `datetime` | No | End date | Now |
| `agent_type` | `string` | No | Filter by agent type | All agents |
| `sort_by` | `string` | No | Sort metric | `invocations` |
| `limit` | `number` | No | Max results | `10` |

**Valid `sort_by` Values**: `invocations`, `success_rate`, `avg_response_time`, `total_cost`

#### Response

##### Success Response (200 OK)
```typescript
interface AgentPerformanceResponse {
  date_from: string;
  date_to: string;
  total_agents: number;
  leaderboard: AgentLeaderboardEntry[];
  total_invocations: number;
  overall_success_rate: number;         // 0-1
  avg_response_time_ms: number;
  total_cost_usd: number;
  invocation_trend: TimeSeriesDataPoint[];
  response_time_trend: TimeSeriesDataPoint[];
}
```

---

### 4. Export Dashboard Data

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard/export`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date | 30 days ago |
| `date_to` | `datetime` | No | End date | Now |
| `format` | `string` | **Yes** | Export format | - |
| `include_sections` | `string[]` | No | Sections to include | All sections |

**Valid `format` Values**: `json`, `csv`

**Valid `include_sections` Values**: `agents`, `costs`, `errors`, `users`, `conversations`

#### Response

##### Success Response (200 OK)
Returns export data in requested format (JSON or CSV)

---

## 🔄 User Flows & Use Cases

### Use Case 1: View Admin Overview Dashboard

**Actor**: Admin User  
**Goal**: View system health and security status at a glance  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to `/admin` or `/admin/overview` after login
2. **Initial State**: 
   - Dashboard loads
   - Show loading skeleton for all cards
   - Call `GET /api/admin/chat/dashboard` and `GET /api/admin/security/dashboard` in parallel
3. **System Response**:
   - Display security status card (critical/warning/healthy)
   - Display chat metrics summary cards
   - Display system health summary
   - If critical security alerts: Show security alert banner at top
4. **User Action**: User clicks on a summary card
5. **System Response**:
   - Navigate to detailed view (e.g., `/admin/chat/analytics` or `/admin/security`)
   - Load detailed metrics
6. **Success Path**:
   - Dashboard displays correctly
   - Real-time updates via WebSocket (if connected)
   - User can drill down into details
7. **Error Path**:
   - If API error: Show error message + Retry button
   - If WebSocket fails: Fallback to polling
   - If one dashboard fails: Show error for that section, keep others visible

#### Flow Diagram
```
[Admin] → [Admin Overview Dashboard]
         ↓
    [Load Dashboards in Parallel]
         ↓
    ┌─────────────────┐
    │ Security Status? │ → Critical → [Show Alert Banner]
    └─────────────────┘
         ↓
    [Display Summary Cards]
         ↓
    [Connect WebSocket]
         ↓
    [Real-time Updates]
         ↓
    [User Clicks Card]
         ↓
    [Navigate to Details]
```

#### Success Criteria
- [ ] Dashboard loads in < 2 seconds
- [ ] All summary cards display correctly
- [ ] Critical security alerts are immediately visible
- [ ] Real-time updates work via WebSocket
- [ ] Error states are clear and actionable

---

### Use Case 2: Monitor Security Status

**Actor**: Admin User  
**Goal**: Check security posture and recent scan results  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User views security status card on overview dashboard
2. **Initial State**: 
   - Security dashboard loads
   - Call `GET /api/admin/security/dashboard`
3. **System Response**:
   - Display security posture score and level
   - Show latest scan results
   - Display attack statistics
   - Show active security tools
4. **User Action**: User clicks "View Latest Scan"
5. **System Response**:
   - Navigate to scan details
   - Load `GET /api/admin/security/scans/{scan_id}`
   - Display detailed vulnerability report
6. **User Action**: User clicks "View Security Trends"
7. **System Response**:
   - Load `GET /api/admin/security/trends?days=30`
   - Display trend chart
   - Show vulnerability trends over time

#### Success Criteria
- [ ] Security status is clearly visible
- [ ] Scan results are accessible
- [ ] Trends are easy to understand
- [ ] Critical vulnerabilities are highlighted

---

### Use Case 3: Export Dashboard Data

**Actor**: Admin User  
**Goal**: Export dashboard data for offline analysis  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User clicks "Export" button on dashboard
2. **Initial State**: 
   - Export modal opens
   - Show export options (format, sections, date range)
3. **User Action**: User selects format (JSON/CSV) and sections
4. **System Response**:
   - Call `GET /api/admin/chat/dashboard/export` with parameters
   - Show loading state
5. **System Response**:
   - Download file starts
   - Show success message
   - Close modal

#### Success Criteria
- [ ] Export options are clear
- [ ] Export completes successfully
- [ ] File format is correct
- [ ] All selected sections are included

---

## 📁 File Structure

```
src/modules/admin/overview/
├── AdminOverview.tsx
├── AdminOverview.types.ts
├── AdminOverview.hooks.ts
├── AdminOverview.service.ts
├── components/
│   ├── SummaryCard.tsx
│   ├── SecurityAlertBanner.tsx
│   ├── Sparkline.tsx
│   ├── ChatDashboard.tsx
│   ├── SecurityDashboard.tsx
│   ├── SystemHealthCard.tsx
│   └── ExportModal.tsx
├── hooks/
│   ├── useChatDashboard.ts
│   ├── useSecurityDashboard.ts
│   ├── useDashboardWebSocket.ts
│   └── useExportData.ts
├── services/
│   ├── chatDashboard.service.ts
│   ├── securityDashboard.service.ts
│   └── export.service.ts
└── __tests__/
    ├── AdminOverview.test.tsx
    ├── SummaryCard.test.tsx
    └── services.test.ts
```

## 🔑 Key Implementation Files

### 1. Admin Overview Module

#### `AdminOverview.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type {
  AdminChatDashboardSummaryResponse,
  SecurityDashboardResponse,
} from './AdminOverview.types';

export const adminOverviewService = {
  async getChatDashboard(
    dateFrom?: string,
    dateTo?: string
  ): Promise<AdminChatDashboardSummaryResponse> {
    const params: Record<string, string> = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;

    const response = await apiClient.get<AdminChatDashboardSummaryResponse>(
      '/api/admin/chat/dashboard',
      { params }
    );
    return response.data;
  },

  async getSecurityDashboard(): Promise<SecurityDashboardResponse> {
    const response = await apiClient.get<SecurityDashboardResponse>(
      '/api/admin/security/dashboard'
    );
    return response.data;
  },

  async exportDashboard(
    format: 'json' | 'csv',
    dateFrom?: string,
    dateTo?: string,
    includeSections?: string[]
  ): Promise<Blob> {
    const params: Record<string, string | string[]> = {
      format,
    };
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    if (includeSections) params.include_sections = includeSections;

    const response = await apiClient.get('/api/admin/chat/dashboard/export', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
};
```

#### `AdminOverview.types.ts`
```typescript
export interface AdminChatDashboardSummaryResponse {
  date_from: string;
  date_to: string;
  total_conversations: number;
  total_messages: number;
  total_active_users: number;
  total_cost_usd: number;
  total_agent_invocations: number;
  most_used_agent: string;
  avg_success_rate: number;
  avg_response_time_ms: number;
  error_rate: number;
  cache_hit_rate: number;
  top_agents: AgentLeaderboardEntry[];
  conversation_trend: TimeSeriesDataPoint[];
  cost_trend: TimeSeriesDataPoint[];
}

export interface SecurityDashboardResponse {
  timestamp: string;
  security_posture: {
    overall_score: number;
    level: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'CRITICAL';
  };
  latest_scan: {
    scan_id: string;
    scan_date: string;
    status: 'completed' | 'running' | 'failed';
    vulnerabilities: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
  attack_statistics: {
    xss_attempts: { total: number; blocked: number };
    prompt_injections: { total: number; blocked: number };
  };
  overall_status: 'healthy' | 'warning' | 'critical' | 'unknown';
}

export interface AgentLeaderboardEntry {
  agent_type: string;
  agent_name: string;
  rank: number;
  total_invocations: number;
  success_rate: number;
  avg_response_time_ms: number;
  total_cost_usd: number;
  error_count: number;
  last_used: string | null;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  label: string | null;
}
```

#### `AdminOverview.hooks.ts`
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { adminOverviewService } from './AdminOverview.service';
import { useDashboardWebSocket } from './hooks/useDashboardWebSocket';
import type {
  AdminChatDashboardSummaryResponse,
  SecurityDashboardResponse,
} from './AdminOverview.types';

export function useChatDashboard(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: ['admin', 'chat', 'dashboard', dateFrom, dateTo],
    queryFn: () => adminOverviewService.getChatDashboard(dateFrom, dateTo),
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: true,
  });
}

export function useSecurityDashboard() {
  return useQuery({
    queryKey: ['admin', 'security', 'dashboard'],
    queryFn: () => adminOverviewService.getSecurityDashboard(),
    staleTime: 60000, // 1 minute
    refetchOnWindowFocus: true,
  });
}

export function useExportDashboard() {
  return useMutation({
    mutationFn: async (params: {
      format: 'json' | 'csv';
      dateFrom?: string;
      dateTo?: string;
      includeSections?: string[];
    }) => {
      const blob = await adminOverviewService.exportDashboard(
        params.format,
        params.dateFrom,
        params.dateTo,
        params.includeSections
      );
      
      // Trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dashboard-export-${Date.now()}.${params.format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}

// WebSocket hook for real-time updates
export function useDashboardRealTimeUpdates() {
  return useDashboardWebSocket({
    onChatMetricsUpdate: (data) => {
      // Update React Query cache
    },
    onSecurityAlert: (alert) => {
      // Show alert banner
    },
  });
}
```

#### `AdminOverview.tsx`
```typescript
'use client';

import React, { useState } from 'react';
import { useChatDashboard, useSecurityDashboard } from './AdminOverview.hooks';
import { SummaryCard } from './components/SummaryCard';
import { SecurityAlertBanner } from './components/SecurityAlertBanner';
import { ChatDashboard } from './components/ChatDashboard';
import { SecurityDashboard } from './components/SecurityDashboard';
import { LoadingSpinner } from '@/design-system/components/LoadingSpinner';
import { ErrorMessage } from '@/design-system/components/ErrorMessage';

export const AdminOverview: React.FC = () => {
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    to: new Date().toISOString(),
  });

  const {
    data: chatData,
    isLoading: chatLoading,
    error: chatError,
    refetch: refetchChat,
  } = useChatDashboard(dateRange.from, dateRange.to);

  const {
    data: securityData,
    isLoading: securityLoading,
    error: securityError,
    refetch: refetchSecurity,
  } = useSecurityDashboard();

  // Determine security status
  const securityStatus =
    securityData?.overall_status === 'critical'
      ? 'critical'
      : securityData?.overall_status === 'warning'
      ? 'warning'
      : 'healthy';

  if (chatLoading && securityLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="admin-overview-container p-6">
      <h1 className="text-3xl font-bold mb-6">Admin Overview</h1>

      {/* Security Alert Banner (if critical) */}
      {securityData?.overall_status === 'critical' && (
        <SecurityAlertBanner
          severity="critical"
          title="Critical Security Alert"
          description={`Security score: ${securityData.security_posture.overall_score}/100. ${securityData.latest_scan.vulnerabilities.critical} critical vulnerabilities detected.`}
          actionLabel="View Security Dashboard"
          onAction={() => window.location.href = '/admin/security'}
          dismissible={false}
        />
      )}

      {/* Summary Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <SummaryCard
          title="Security Status"
          value={securityData?.security_posture.level || 'Unknown'}
          status={securityStatus}
          onClick={() => window.location.href = '/admin/security'}
          loading={securityLoading}
        />
        
        <SummaryCard
          title="Active Conversations"
          value={chatData?.total_conversations || 0}
          trend="up"
          sparkline={chatData?.conversation_trend.map(p => p.value)}
          status="info"
          onClick={() => window.location.href = '/admin/chat/analytics'}
          loading={chatLoading}
        />
        
        <SummaryCard
          title="Total Cost (USD)"
          value={`$${chatData?.total_cost_usd.toFixed(2) || '0.00'}`}
          trend="up"
          sparkline={chatData?.cost_trend.map(p => p.value)}
          status="info"
          loading={chatLoading}
        />
      </div>

      {/* Security Dashboard Section */}
      {securityError ? (
        <ErrorMessage error={securityError} onRetry={refetchSecurity} />
      ) : (
        <SecurityDashboard data={securityData} loading={securityLoading} />
      )}

      {/* Chat Analytics Dashboard Section */}
      {chatError ? (
        <ErrorMessage error={chatError} onRetry={refetchChat} />
      ) : (
        <ChatDashboard data={chatData} loading={chatLoading} />
      )}
    </div>
  );
};
```

### 2. WebSocket Hook

#### `hooks/useDashboardWebSocket.ts`
```typescript
import { useEffect, useRef } from 'react';
import { useAuth } from '@/hooks/useAuth';

interface DashboardWebSocketOptions {
  onChatMetricsUpdate?: (data: any) => void;
  onSecurityAlert?: (alert: any) => void;
}

export function useDashboardWebSocket(options: DashboardWebSocketOptions) {
  const { token } = useAuth();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) return;

    const ws = new WebSocket(
      `ws://localhost:8000/api/admin/llm/dashboard/ws?token=${token}`
    );

    ws.onopen = () => {
      console.log('Dashboard WebSocket connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'metrics_update':
          options.onChatMetricsUpdate?.(message.data);
          break;
        case 'security_alert':
          options.onSecurityAlert?.(message);
          break;
        case 'pong':
          // Heartbeat response
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('Dashboard WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Dashboard WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(() => {
        if (token) {
          // Reconnect logic
        }
      }, 5000);
    };

    wsRef.current = ws;

    // Send ping every 30 seconds
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [token]);

  return wsRef.current;
}
```

## 📝 Complete File List

### Admin Overview Module
- [ ] `AdminOverview.tsx` - Main component
- [ ] `AdminOverview.types.ts` - TypeScript interfaces
- [ ] `AdminOverview.hooks.ts` - React hooks
- [ ] `AdminOverview.service.ts` - API service
- [ ] `components/SummaryCard.tsx` - Summary card component
- [ ] `components/SecurityAlertBanner.tsx` - Security alert banner
- [ ] `components/Sparkline.tsx` - Sparkline chart component
- [ ] `components/ChatDashboard.tsx` - Chat analytics dashboard
- [ ] `components/SecurityDashboard.tsx` - Security dashboard
- [ ] `components/SystemHealthCard.tsx` - System health card
- [ ] `components/ExportModal.tsx` - Export modal
- [ ] `hooks/useChatDashboard.ts` - Chat dashboard hook
- [ ] `hooks/useSecurityDashboard.ts` - Security dashboard hook
- [ ] `hooks/useDashboardWebSocket.ts` - WebSocket hook
- [ ] `hooks/useExportData.ts` - Export data hook
- [ ] `services/chatDashboard.service.ts` - Chat dashboard service
- [ ] `services/securityDashboard.service.ts` - Security dashboard service
- [ ] `services/export.service.ts` - Export service
- [ ] `__tests__/AdminOverview.test.tsx` - Component tests
- [ ] `__tests__/SummaryCard.test.tsx` - Component tests
- [ ] `__tests__/services.test.ts` - Service tests

---

## 🧪 Testing Requirements

### Unit Tests

**Admin Overview Component**:
- [ ] Renders summary cards correctly
- [ ] Displays security alert banner when critical
- [ ] Handles loading states
- [ ] Displays error states
- [ ] Navigates to detail views on card click

**Summary Card Component**:
- [ ] Renders title and value
- [ ] Displays sparkline when provided
- [ ] Shows trend indicator
- [ ] Applies correct status colors
- [ ] Handles click events

**Security Alert Banner**:
- [ ] Renders with correct severity styling
- [ ] Shows action button when provided
- [ ] Handles dismiss when dismissible
- [ ] Announces to screen readers

**Services**:
- [ ] Calls correct API endpoints
- [ ] Handles query parameters
- [ ] Parses response correctly
- [ ] Handles errors (401, 403, 500, 503)

### Integration Tests

**Dashboard Flow**:
- [ ] Load chat and security dashboards in parallel
- [ ] Display summary cards with data
- [ ] Show security alert when critical
- [ ] Navigate to detail views
- [ ] Export dashboard data

**WebSocket Integration**:
- [ ] Connect to WebSocket
- [ ] Receive real-time updates
- [ ] Handle connection errors
- [ ] Reconnect on disconnect

### E2E Tests

**Admin Overview Journey**:
- [ ] Login as admin → View overview dashboard
- [ ] See security status
- [ ] View chat metrics
- [ ] Click card to drill down
- [ ] Export dashboard data
- [ ] Handle errors gracefully

### Performance Tests

- [ ] Dashboard loads in < 2 seconds
- [ ] Summary cards render in < 500ms
- [ ] WebSocket connection in < 1 second
- [ ] Real-time updates < 500ms latency
- [ ] Export generation < 5 seconds

### Accessibility Tests

- [ ] Screen reader announces security alerts
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG 2.1 AA
- [ ] All interactive elements are focusable
- [ ] Status changes are announced

---

## 🔍 Risk Assessment (CTO Methodology)

### Cognitive Limitation Analysis

**Areas Where Analysis May Overlook Factors**:

1. **Information Overload**
   - **Risk**: Too many metrics cause decision paralysis
   - **Mitigation**: Progressive disclosure, summary cards, drill-down
   - **Validation**: User testing with admins

2. **Security Alert Fatigue**
   - **Risk**: Too many alerts cause admins to ignore them
   - **Mitigation**: Prioritize critical alerts, allow filtering
   - **Validation**: Monitor alert response rates

3. **Real-time Update Complexity**
   - **Risk**: WebSocket connection management is complex
   - **Mitigation**: Robust reconnection logic, fallback to polling
   - **Validation**: Test connection failures and recovery

### Technical Debt Assessment

**Rapid Implementation Compromises to Avoid**:

1. **No Data Caching**
   - **Debt**: Repeated API calls
   - **Cost**: Poor performance, high API costs
   - **Prevention**: Implement React Query caching with appropriate stale times

2. **Hardcoded Date Ranges**
   - **Debt**: Cannot customize analysis periods
   - **Cost**: Limited flexibility
   - **Prevention**: Date range picker with presets

3. **No Error Recovery**
   - **Debt**: Single failure breaks entire dashboard
   - **Cost**: Poor user experience
   - **Prevention**: Error boundaries, graceful degradation

### Validation & Testing Strategy

**Module-Specific Success Criteria**:
- ✅ Dashboard loads in < 2 seconds (p95)
- ✅ Security alerts visible within 1 second
- ✅ Real-time updates latency < 500ms (WebSocket)
- ✅ Error recovery rate > 95% (users can recover from errors)
- ✅ Export generation < 5 seconds for 30-day period
- ✅ WebSocket connection uptime > 99%
- ✅ Accessibility score: 100/100 (WCAG 2.1 AA)

**Module-Specific Test Requirements**:
- **Unit Tests**: Component rendering, state management, service functions
- **Integration Tests**: API integration, WebSocket connection, export functionality
- **E2E Tests**: Complete dashboard flow, security alert handling, export flow
- **Performance Tests**: Load with multiple dashboards, WebSocket stress testing
- **Accessibility Tests**: Screen reader navigation, keyboard shortcuts, color contrast

**Failure Detection & Monitoring**:
- Monitor API response times (alert if p95 > 2s)
- Track error rates (alert if > 1%)
- Alert on WebSocket connection failures (alert if uptime < 99%)
- Monitor security alert response times
- Track dashboard load times
- Log all export operations for audit trail

---

## 📚 References

- **Backend Controller**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/security_router.py`
- **Response Schemas**: `src/app/presentation/http/schemas/admin_chat_dashboard.py`
- **API Documentation**: `01-Admin-Overview/API.md`
- **UI/UX Design**: `01-Admin-Overview/UI_UX.md`
- **Related Modules**: 
  - Chat Analytics (detailed chat metrics)
  - Security Dashboard (detailed security metrics)

---

**Note**: These are implementation file structures. Actual files should be created in the frontend codebase repository.
