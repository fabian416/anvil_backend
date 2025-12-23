# System Health Module Implementation

> **Complete TypeScript/React Implementation for System Health Module**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)

## 📖 Module Overview

The **System Health** module provides technical monitoring for DevOps and Site Reliability Engineering (SRE) tasks. It monitors low-level infrastructure metrics, system statistics, and retry system status.

### Key Capabilities
1. **Metrics**: CPU/RAM usage, database connectivity, API latency, transaction metrics, wallet metrics, user activity
2. **Stats**: System statistics overview, active conversations, agent usage
3. **Retry System**: Service status monitoring, circuit breaker management, retry metrics

### Business Value
- **Operational Visibility**: Real-time system health monitoring
- **Incident Response**: Quick identification of service issues
- **Performance Optimization**: Identify bottlenecks and optimize
- **Reliability**: Ensure system availability and performance

---

## 🎨 UX/UI Specifications

### Design Principles (First Principles Analysis)

**Essential Problem**: SRE teams need dense technical data for monitoring and troubleshooting.

**Root Cause Analysis**:
- **Information Density**: SREs need more data than business dashboards
- **Solution**: High-density layouts, detailed charts, drill-down capabilities, real-time updates

**Design Decisions**:
1. **High Density**: Allow more dense technical data (logs, charts) than business dashboards
2. **Real-time Updates**: WebSocket connections for live metrics
3. **Drill-down**: Summary → Detailed metrics → Logs
4. **Time Series Focus**: Charts and graphs for trend analysis

### Trade-off Analysis (Design Thinking)

**Key Design Decisions with Trade-offs**:

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **High Density Layout** | Sparse Layout | Information vs. Readability | SREs need more data, but it can be overwhelming |
| **Real-time Updates** | Manual Refresh | Current vs. Performance | Real-time provides current data, but requires WebSocket connections |
| **Time Series Charts** | Tables Only | Visual vs. Precision | Charts show trends better, but tables show exact values |
| **Service Control** | View Only | Control vs. Safety | Manual control allows intervention, but requires careful management |

### Visual Design

#### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│              System Health                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Tabs: [Metrics] [Stats] [Retry System]           │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Metrics Overview                                  │  │
│  │ ┌──────────────┐  ┌──────────────┐              │  │
│  │ │ Wallets      │  │ Transactions │              │  │
│  │ │ 1,500        │  │ 5,000        │              │  │
│  │ └──────────────┘  └──────────────┘              │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Transaction Time Series Chart                     │  │
│  │ [Line Chart]                                      │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Retry System Services                             │  │
│  │ ┌──────────────┐                                  │  │
│  │ │ Service Name │ Status │ Circuit │ Actions      │  │
│  │ │ openai_api   │ ✅     │ CLOSED  │ [Reset]      │  │
│  │ └──────────────┘                                  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### Color Palette
- **Healthy**: `#10B981` (Green)
- **Degraded**: `#F59E0B` (Amber)
- **Down**: `#EF4444` (Red)
- **Circuit Breaker Closed**: `#10B981` (Green)
- **Circuit Breaker Open**: `#EF4444` (Red)
- **Circuit Breaker Half-Open**: `#F59E0B` (Amber)

#### Component Specifications

##### Metric Card Component
```typescript
interface MetricCardProps {
  title: string;
  value: number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  chart?: TimeSeriesDataPoint[];
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  trend,
  chart,
  onClick,
}) => {
  return (
    <div
      className="bg-white rounded-lg border-2 border-gray-200 p-6 hover:shadow-md transition cursor-pointer"
      onClick={onClick}
    >
      <h3 className="text-sm font-medium text-gray-600 mb-2">{title}</h3>
      <div className="text-3xl font-bold text-gray-900 mb-4">
        {value.toLocaleString()} {unit}
      </div>
      {chart && (
        <div className="h-16">
          <LineChart data={chart} />
        </div>
      )}
      {trend && (
        <div className="flex items-center text-sm mt-2">
          <TrendIcon direction={trend} />
          <span className="ml-1 text-gray-600">vs last period</span>
        </div>
      )}
    </div>
  );
};
```

##### Service Status Table Component
```typescript
interface ServiceStatusTableProps {
  services: ServiceStatusResponse[];
  onDisable: (serviceName: string, reason: string) => void;
  onEnable: (serviceName: string, reason: string) => void;
  onResetCircuitBreaker: (serviceName: string, reason: string) => void;
  onViewMetrics: (serviceName: string) => void;
}

export const ServiceStatusTable: React.FC<ServiceStatusTableProps> = ({
  services,
  onDisable,
  onEnable,
  onResetCircuitBreaker,
  onViewMetrics,
}) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Service Name
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Circuit Breaker
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Failures
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {services.map((service) => (
            <ServiceStatusRow
              key={service.service_name}
              service={service}
              onDisable={onDisable}
              onEnable={onEnable}
              onResetCircuitBreaker={onResetCircuitBreaker}
              onViewMetrics={onViewMetrics}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

### Responsive Breakpoints

**Mobile** (< 640px):
- Single column layout
- Stacked metric cards
- Horizontal scroll for tables
- Bottom sheet for actions

**Tablet** (640px - 1024px):
- Two-column metric cards
- Full table width
- Side panel for details

**Desktop** (> 1024px):
- Three-column metric cards
- Full table layout
- Sidebar for filters
- Modal for detailed views

### Accessibility Requirements

1. **Screen Readers**:
   - Announce metric values
   - Describe chart data
   - Label all interactive elements
   - Announce status changes

2. **Keyboard Navigation**:
   - Tab through all cards
   - Enter to drill down
   - Escape to close modals
   - Arrow keys for chart navigation

3. **Color Contrast**:
   - All text: 4.5:1 minimum
   - Status indicators: 3:1 minimum
   - Charts: 3:1 minimum

---

## 🔌 API Endpoints

See `04-System-Health/API.md` for complete API documentation.

### Key Endpoints Summary

1. **Metrics Overview**: `GET /api/admin/metrics/overview`
2. **Transaction Time Series**: `GET /api/admin/metrics/transactions/timeseries`
3. **Wallet Time Series**: `GET /api/admin/metrics/wallets/timeseries`
4. **User Activity Time Series**: `GET /api/admin/metrics/users/activity`
5. **Wallet Distribution**: `GET /api/admin/metrics/wallets/distribution`
6. **Transaction Distribution**: `GET /api/admin/metrics/transactions/distribution`
7. **System Stats**: `GET /api/admin/stats/`
8. **Retry Services**: `GET /api/v1/admin/retry/services`
9. **Service Status**: `GET /api/v1/admin/retry/services/{service_name}`
10. **Disable Service**: `POST /api/v1/admin/retry/services/{service_name}/disable`
11. **Enable Service**: `POST /api/v1/admin/retry/services/{service_name}/enable`
12. **Circuit Breakers**: `GET /api/v1/admin/retry/circuit-breakers`
13. **Reset Circuit Breaker**: `POST /api/v1/admin/retry/circuit-breakers/{service_name}/reset`
14. **Service Metrics**: `GET /api/v1/admin/retry/metrics/{service_name}`

---

## 🔄 User Flows & Use Cases

### Use Case 1: Monitor System Metrics

**Actor**: SRE/Admin User  
**Goal**: View system health metrics and trends  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to `/admin/system-health` → Metrics tab
2. **Initial State**: 
   - Metrics overview loads
   - Show loading skeleton
   - Call `GET /api/admin/metrics/overview`
3. **System Response**:
   - Display metric cards (wallets, transactions, users)
   - Show time series charts
   - Display distribution charts
4. **User Action**: User selects date range
5. **System Response**:
   - Update date range filter
   - Refetch time series data
   - Update charts
6. **User Action**: User clicks on a metric card
7. **System Response**:
   - Navigate to detailed metric view
   - Load detailed time series
   - Show breakdown

#### Success Criteria
- [ ] Metrics load in < 2 seconds
- [ ] Charts render correctly
- [ ] Date range selection works
- [ ] Drill-down navigation works

---

### Use Case 2: Manage Retry System

**Actor**: SRE/Admin User  
**Goal**: Monitor and control retry system services  
**Preconditions**: User is authenticated and has admin role

#### Flow Steps

1. **Entry Point**: User navigates to `/admin/system-health` → Retry System tab
2. **Initial State**: 
   - Services list loads
   - Call `GET /api/v1/admin/retry/services`
3. **System Response**:
   - Display service status table
   - Show circuit breaker states
   - Display failure counts
4. **User Action**: User clicks "Reset Circuit Breaker" on a service
5. **System Response**:
   - Show confirmation modal
   - Request reason for reset
6. **User Action**: User confirms with reason
7. **System Response**:
   - Call `POST /api/v1/admin/retry/circuit-breakers/{service_name}/reset`
   - Show loading state
8. **System Response**:
   - On success: Update circuit breaker state, show success toast
   - On error: Show error message

#### Success Criteria
- [ ] Service status displays correctly
- [ ] Circuit breaker reset works
- [ ] Confirmation prevents mistakes
- [ ] Error handling works

---

## 📁 File Structure

```
src/modules/admin/system-health/
├── SystemHealth.tsx
├── SystemHealth.types.ts
├── SystemHealth.hooks.ts
├── SystemHealth.service.ts
├── components/
│   ├── MetricCard.tsx
│   ├── TimeSeriesChart.tsx
│   ├── DistributionChart.tsx
│   ├── ServiceStatusTable.tsx
│   ├── ServiceStatusRow.tsx
│   ├── CircuitBreakerStatus.tsx
│   ├── ServiceMetricsModal.tsx
│   └── DateRangePicker.tsx
├── tabs/
│   ├── MetricsTab.tsx
│   ├── StatsTab.tsx
│   └── RetrySystemTab.tsx
├── hooks/
│   ├── useMetrics.ts
│   ├── useStats.ts
│   ├── useRetrySystem.ts
│   └── useSystemHealthWebSocket.ts
├── services/
│   ├── metrics.service.ts
│   ├── stats.service.ts
│   └── retry.service.ts
└── __tests__/
    ├── SystemHealth.test.tsx
    ├── MetricCard.test.tsx
    └── services.test.ts
```

## 🔑 Key Implementation Files

### 1. System Health Module

#### `SystemHealth.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type {
  AdminMetricsOverview,
  TransactionTimeSeriesResponse,
  WalletTimeSeriesResponse,
  UserActivityTimeSeriesResponse,
  WalletDistributionResponse,
  TransactionDistributionResponse,
  AdminStats,
  ServiceListResponse,
  ServiceStatusResponse,
  CircuitBreakerStatusResponse,
  ServiceMetricsResponse,
} from './SystemHealth.types';

export const systemHealthService = {
  async getMetricsOverview(): Promise<AdminMetricsOverview> {
    const response = await apiClient.get<AdminMetricsOverview>(
      '/api/admin/metrics/overview'
    );
    return response.data;
  },

  async getTransactionTimeSeries(params: {
    from_date?: string;
    to_date?: string;
    chain?: string;
    tx_type?: string;
    group_by?: string;
  }): Promise<TransactionTimeSeriesResponse> {
    const response = await apiClient.get<TransactionTimeSeriesResponse>(
      '/api/admin/metrics/transactions/timeseries',
      { params }
    );
    return response.data;
  },

  async getWalletTimeSeries(params: {
    from_date?: string;
    to_date?: string;
    group_by?: string;
  }): Promise<WalletTimeSeriesResponse> {
    const response = await apiClient.get<WalletTimeSeriesResponse>(
      '/api/admin/metrics/wallets/timeseries',
      { params }
    );
    return response.data;
  },

  async getUserActivityTimeSeries(params: {
    from_date?: string;
    to_date?: string;
  }): Promise<UserActivityTimeSeriesResponse> {
    const response = await apiClient.get<UserActivityTimeSeriesResponse>(
      '/api/admin/metrics/users/activity',
      { params }
    );
    return response.data;
  },

  async getWalletDistribution(): Promise<WalletDistributionResponse> {
    const response = await apiClient.get<WalletDistributionResponse>(
      '/api/admin/metrics/wallets/distribution'
    );
    return response.data;
  },

  async getTransactionDistribution(): Promise<TransactionDistributionResponse> {
    const response = await apiClient.get<TransactionDistributionResponse>(
      '/api/admin/metrics/transactions/distribution'
    );
    return response.data;
  },

  async getStats(): Promise<AdminStats> {
    const response = await apiClient.get<AdminStats>(
      '/api/admin/stats/'
    );
    return response.data;
  },

  async listServices(): Promise<ServiceListResponse> {
    const response = await apiClient.get<ServiceListResponse>(
      '/api/v1/admin/retry/services'
    );
    return response.data;
  },

  async getServiceStatus(serviceName: string): Promise<ServiceStatusResponse> {
    const response = await apiClient.get<ServiceStatusResponse>(
      `/api/v1/admin/retry/services/${serviceName}`
    );
    return response.data;
  },

  async disableService(
    serviceName: string,
    reason: string,
    durationMinutes?: number | null
  ): Promise<void> {
    await apiClient.post(
      `/api/v1/admin/retry/services/${serviceName}/disable`,
      { reason, duration_minutes: durationMinutes }
    );
  },

  async enableService(serviceName: string, reason: string): Promise<void> {
    await apiClient.post(
      `/api/v1/admin/retry/services/${serviceName}/enable`,
      { reason }
    );
  },

  async getCircuitBreakers(): Promise<CircuitBreakerStatusResponse[]> {
    const response = await apiClient.get<CircuitBreakerStatusResponse[]>(
      '/api/v1/admin/retry/circuit-breakers'
    );
    return response.data;
  },

  async resetCircuitBreaker(
    serviceName: string,
    reason: string
  ): Promise<void> {
    await apiClient.post(
      `/api/v1/admin/retry/circuit-breakers/${serviceName}/reset`,
      { reason }
    );
  },

  async getServiceMetrics(
    serviceName: string,
    days?: number
  ): Promise<ServiceMetricsResponse> {
    const params = days ? { days } : {};
    const response = await apiClient.get<ServiceMetricsResponse>(
      `/api/v1/admin/retry/metrics/${serviceName}`,
      { params }
    );
    return response.data;
  },
};
```

#### `SystemHealth.types.ts`
```typescript
export interface AdminMetricsOverview {
  wallets: WalletOverviewMetrics;
  transactions: TransactionOverviewMetrics;
  users: UserOverviewMetrics;
  generated_at: string;                  // ISO 8601
}

export interface WalletOverviewMetrics {
  total_wallets: number;
  active_wallets: number;
  privy_wallets: number;
  imported_wallets: number;
  external_wallets: number;
}

export interface TransactionOverviewMetrics {
  total_transactions: number;
  pending_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
}

export interface UserOverviewMetrics {
  total_users: number;
  total_users_with_transactions: number;
  active_users_today: number;
  active_users_7d: number;
  active_users_30d: number;
}

export interface TimeSeriesDataPoint {
  date: string;                          // ISO 8601
  value: number;
}

export interface TransactionTimeSeriesResponse {
  data: TimeSeriesDataPoint[];
  from_date: string;
  to_date: string;
  group_by: string;
  chain: string | null;
  tx_type: string | null;
  total_count: number;
}

export interface DistributionItem {
  name: string;
  count: number;
  percentage: number;                    // 0-100
}

export interface ServiceStatusResponse {
  service_name: string;
  enabled: boolean;
  circuit_state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failure_count: number;
  success_count: number;
  last_error: string | null;
  last_error_at: string | null;          // ISO 8601
  override_reason: string | null;
  override_expires_at: string | null;    // ISO 8601
}

export interface CircuitBreakerStatusResponse {
  service_name: string;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failure_count: number;
  success_count: number;
  opened_at: string | null;              // ISO 8601
  config: {
    failure_threshold: number;
    success_threshold: number;
    timeout_seconds: number;
  };
}
```

#### `SystemHealth.hooks.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { systemHealthService } from './SystemHealth.service';

export function useMetricsOverview() {
  return useQuery({
    queryKey: ['admin', 'metrics', 'overview'],
    queryFn: () => systemHealthService.getMetricsOverview(),
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: true,
  });
}

export function useTransactionTimeSeries(params: {
  from_date?: string;
  to_date?: string;
  chain?: string;
  tx_type?: string;
  group_by?: string;
}) {
  return useQuery({
    queryKey: ['admin', 'metrics', 'transactions', 'timeseries', params],
    queryFn: () => systemHealthService.getTransactionTimeSeries(params),
    staleTime: 60000, // 1 minute
  });
}

export function useRetryServices() {
  return useQuery({
    queryKey: ['admin', 'retry', 'services'],
    queryFn: () => systemHealthService.listServices(),
    staleTime: 30000, // 30 seconds
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useDisableService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      serviceName,
      reason,
      durationMinutes,
    }: {
      serviceName: string;
      reason: string;
      durationMinutes?: number | null;
    }) => systemHealthService.disableService(serviceName, reason, durationMinutes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'retry', 'services'] });
    },
  });
}

export function useResetCircuitBreaker() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      serviceName,
      reason,
    }: {
      serviceName: string;
      reason: string;
    }) => systemHealthService.resetCircuitBreaker(serviceName, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'retry', 'services'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'retry', 'circuit-breakers'] });
    },
  });
}
```

#### `SystemHealth.tsx`
```typescript
'use client';

import React, { useState } from 'react';
import { MetricsTab } from './tabs/MetricsTab';
import { StatsTab } from './tabs/StatsTab';
import { RetrySystemTab } from './tabs/RetrySystemTab';

type Tab = 'metrics' | 'stats' | 'retry';

export const SystemHealth: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('metrics');

  const tabs = [
    { id: 'metrics' as Tab, label: 'Metrics' },
    { id: 'stats' as Tab, label: 'Stats' },
    { id: 'retry' as Tab, label: 'Retry System' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'metrics':
        return <MetricsTab />;
      case 'stats':
        return <StatsTab />;
      case 'retry':
        return <RetrySystemTab />;
      default:
        return <MetricsTab />;
    }
  };

  return (
    <div className="system-health-container p-6">
      <h1 className="text-3xl font-bold mb-6">System Health</h1>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {renderTabContent()}
    </div>
  );
};
```

## 📝 Complete File List

### System Health Module
- [ ] `SystemHealth.tsx` - Main component
- [ ] `SystemHealth.types.ts` - TypeScript interfaces
- [ ] `SystemHealth.hooks.ts` - React hooks
- [ ] `SystemHealth.service.ts` - API service
- [ ] `components/MetricCard.tsx` - Metric card component
- [ ] `components/TimeSeriesChart.tsx` - Time series chart
- [ ] `components/DistributionChart.tsx` - Distribution chart
- [ ] `components/ServiceStatusTable.tsx` - Service status table
- [ ] `components/ServiceStatusRow.tsx` - Service status row
- [ ] `components/CircuitBreakerStatus.tsx` - Circuit breaker status
- [ ] `components/ServiceMetricsModal.tsx` - Service metrics modal
- [ ] `components/DateRangePicker.tsx` - Date range picker
- [ ] `tabs/MetricsTab.tsx` - Metrics tab
- [ ] `tabs/StatsTab.tsx` - Stats tab
- [ ] `tabs/RetrySystemTab.tsx` - Retry system tab
- [ ] `hooks/useMetrics.ts` - Metrics hook
- [ ] `hooks/useStats.ts` - Stats hook
- [ ] `hooks/useRetrySystem.ts` - Retry system hook
- [ ] `hooks/useSystemHealthWebSocket.ts` - WebSocket hook
- [ ] `services/metrics.service.ts` - Metrics service
- [ ] `services/stats.service.ts` - Stats service
- [ ] `services/retry.service.ts` - Retry service
- [ ] `__tests__/SystemHealth.test.tsx` - Component tests
- [ ] `__tests__/MetricCard.test.tsx` - Component tests
- [ ] `__tests__/services.test.ts` - Service tests

---

## 🧪 Testing Requirements

### Unit Tests

**System Health Component**:
- [ ] Renders tab navigation correctly
- [ ] Switches tabs correctly
- [ ] Displays tab content
- [ ] Handles loading states
- [ ] Displays error states

**Metric Card Component**:
- [ ] Renders metric value correctly
- [ ] Displays chart when provided
- [ ] Shows trend indicator
- [ ] Handles click events

**Service Status Table**:
- [ ] Renders service rows correctly
- [ ] Displays circuit breaker status
- [ ] Handles action clicks
- [ ] Shows loading states

**Services**:
- [ ] Calls correct API endpoints
- [ ] Handles query parameters
- [ ] Parses response correctly
- [ ] Handles errors (401, 403, 404, 500, 503)

### Integration Tests

**System Health Flow**:
- [ ] Load metrics overview
- [ ] View time series charts
- [ ] Filter by date range
- [ ] View service status
- [ ] Disable/enable service
- [ ] Reset circuit breaker
- [ ] View service metrics

### E2E Tests

**System Health Journey**:
- [ ] Login as admin → View system health
- [ ] Monitor metrics
- [ ] Manage retry system
- [ ] Handle errors gracefully

### Performance Tests

- [ ] Metrics load in < 2 seconds
- [ ] Charts render in < 1 second
- [ ] Time series queries complete in < 2 seconds
- [ ] Service status updates in < 1 second

### Accessibility Tests

- [ ] Screen reader announces metric values
- [ ] Keyboard navigation works
- [ ] Color contrast meets WCAG 2.1 AA
- [ ] Charts are accessible
- [ ] All interactive elements are focusable

---

## 🔍 Risk Assessment (CTO Methodology)

### Cognitive Limitation Analysis

**Areas Where Analysis May Overlook Factors**:

1. **Data Density**
   - **Risk**: Too much data causes information overload
   - **Mitigation**: Progressive disclosure, drill-down, filters
   - **Validation**: User testing with SREs

2. **Real-time Update Complexity**
   - **Risk**: WebSocket connection management is complex
   - **Mitigation**: Robust reconnection logic, fallback to polling
   - **Validation**: Test connection failures and recovery

3. **Service Control Safety**
   - **Risk**: Accidental service disable causes outages
   - **Mitigation**: Confirmation modals, audit trail, reason required
   - **Validation**: Test confirmation flows

### Technical Debt Assessment

**Rapid Implementation Compromises to Avoid**:

1. **No Data Aggregation**
   - **Debt**: Raw data only, no summaries
   - **Cost**: Poor performance, high API load
   - **Prevention**: Implement client-side aggregation for small datasets

2. **No Chart Optimization**
   - **Debt**: Charts render slowly with large datasets
   - **Cost**: Poor user experience
   - **Prevention**: Implement data sampling for large time series

3. **No Service Control Audit**
   - **Debt**: No record of service changes
   - **Cost**: Compliance issues
   - **Prevention**: Log all service operations

### Validation & Testing Strategy

**Module-Specific Success Criteria**:
- ✅ Metrics load in < 2 seconds (p95)
- ✅ Charts render in < 1 second
- ✅ Service status updates in < 1 second
- ✅ Time series queries complete in < 2 seconds
- ✅ Error recovery rate > 95%
- ✅ Accessibility score: 100/100 (WCAG 2.1 AA)

**Module-Specific Test Requirements**:
- **Unit Tests**: Component rendering, state management, service functions, chart rendering
- **Integration Tests**: API integration, time series queries, service operations
- **E2E Tests**: Complete metrics flow, retry system management
- **Performance Tests**: Load with large time series, multiple services, concurrent updates
- **Accessibility Tests**: Screen reader navigation, keyboard shortcuts, color contrast

**Failure Detection & Monitoring**:
- Monitor API response times (alert if p95 > 2s)
- Track error rates (alert if > 1%)
- Alert on service failures
- Monitor circuit breaker state changes
- Track time series query performance
- Log all service operations for audit trail

---

## 📚 References

- **Backend Controller**: `src/app/presentation/http/controllers/admin/metrics/router.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/stats/router.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/retry/router.py`
- **Response Schemas**: `src/app/presentation/http/schemas/admin/metrics.py`
- **API Documentation**: `04-System-Health/API.md`
- **UI/UX Design**: `04-System-Health/UI_UX.md`
- **Related Modules**: 
  - Admin Overview (system health summary)
  - Intelligence Ops (circuit breaker details)

---

**Note**: These are implementation file structures. Actual files should be created in the frontend codebase repository.
