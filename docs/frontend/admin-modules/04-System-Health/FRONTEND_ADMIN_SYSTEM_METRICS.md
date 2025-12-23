# Module: System Metrics

**Route**: `/admin/system-health/metrics`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/system-health/metrics`

## 1. Overview
Provides low-level infrastructure monitoring for SRE teams. Focuses on the "machine" itself - resource usage, API latency, database health, transaction metrics, wallet metrics, and user activity metrics. While dashboards provide business value, this view provides technical operational data.

## 2. API Contract

### Get Metrics Overview
**Endpoint**: `GET /api/admin/metrics/overview`  
**Query Params**: None

#### Response Body (`AdminMetricsOverview`)
| Field | Type | Description |
|---|---|---|
| `wallets` | `WalletOverviewMetrics` | Wallet metrics |
| `transactions` | `TransactionOverviewMetrics` | Transaction metrics |
| `users` | `UserOverviewMetrics` | User metrics |
| `generated_at` | `string` | ISO 8601 timestamp of generation |

**WalletOverviewMetrics Object**:
| Field | Type | Description |
|---|---|---|
| `total_wallets` | `number` | Total wallets |
| `active_wallets` | `number` | Active wallets |
| `privy_wallets` | `number` | Privy-managed wallets |
| `imported_wallets` | `number` | Imported wallets |
| `external_wallets` | `number` | External wallets |

**TransactionOverviewMetrics Object**:
| Field | Type | Description |
|---|---|---|
| `total_transactions` | `number` | Total transactions |
| `pending_transactions` | `number` | Pending transactions |
| `successful_transactions` | `number` | Successful transactions |
| `failed_transactions` | `number` | Failed transactions |

**UserOverviewMetrics Object**:
| Field | Type | Description |
|---|---|---|
| `total_users` | `number` | Total users |
| `total_users_with_transactions` | `number` | Users with transactions |
| `active_users_today` | `number` | Active users today |
| `active_users_7d` | `number` | Active users in last 7 days |
| `active_users_30d` | `number` | Active users in last 30 days |

**JSON Example**:
```json
{
  "wallets": {
    "total_wallets": 1500,
    "active_wallets": 1200,
    "privy_wallets": 800,
    "imported_wallets": 500,
    "external_wallets": 200
  },
  "transactions": {
    "total_transactions": 5000,
    "pending_transactions": 50,
    "successful_transactions": 4800,
    "failed_transactions": 150
  },
  "users": {
    "total_users": 1000,
    "total_users_with_transactions": 500,
    "active_users_today": 50,
    "active_users_7d": 200,
    "active_users_30d": 400
  },
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### Get Transaction Time Series
**Endpoint**: `GET /api/admin/metrics/transactions/timeseries`  
**Query Params**:
- `from_date` (datetime, optional): Start date (ISO 8601, Default: 30 days ago).
- `to_date` (datetime, optional): End date (ISO 8601, Default: Now).
- `chain` (string, optional): Filter by chain.
- `tx_type` (string, optional): Filter by transaction type.
- `group_by` (string, optional): Grouping - `day`, `hour`, `chain`, `type` (Default: `day`).

#### Response Body (`TransactionTimeSeriesResponse`)
| Field | Type | Description |
|---|---|---|
| `data` | `TimeSeriesDataPoint[]` | Time series data points |
| `from_date` | `string` | ISO 8601 start date |
| `to_date` | `string` | ISO 8601 end date |
| `group_by` | `string` | Grouping used |
| `chain` | `string \| null` | Chain filter or null |
| `tx_type` | `string \| null` | Transaction type filter or null |
| `total_count` | `number` | Total transaction count |

**TimeSeriesDataPoint Object**:
| Field | Type | Description |
|---|---|---|
| `date` | `string` | ISO 8601 date |
| `value` | `number` | Metric value |

### Get Wallet Time Series
**Endpoint**: `GET /api/admin/metrics/wallets/timeseries`  
**Query Params**:
- `from_date` (datetime, optional): Start date (ISO 8601, Default: 30 days ago).
- `to_date` (datetime, optional): End date (ISO 8601, Default: Now).
- `group_by` (string, optional): Grouping - `day`, `hour` (Default: `day`).

#### Response Body (`WalletTimeSeriesResponse`)
| Field | Type | Description |
|---|---|---|
| `data` | `TimeSeriesDataPoint[]` | Time series data points |
| `from_date` | `string` | ISO 8601 start date |
| `to_date` | `string` | ISO 8601 end date |
| `group_by` | `string` | Grouping used |
| `total_wallets` | `number` | Total wallet count |

### Get User Activity Time Series
**Endpoint**: `GET /api/admin/metrics/users/activity`  
**Query Params**:
- `from_date` (datetime, optional): Start date (ISO 8601, Default: 30 days ago).
- `to_date` (datetime, optional): End date (ISO 8601, Default: Now).

#### Response Body (`UserActivityTimeSeriesResponse`)
| Field | Type | Description |
|---|---|---|
| `data` | `TimeSeriesDataPoint[]` | Time series data points |
| `from_date` | `string` | ISO 8601 start date |
| `to_date` | `string` | ISO 8601 end date |
| `total_active_users` | `number` | Total active users |

### Get Wallet Distribution
**Endpoint**: `GET /api/admin/metrics/wallets/distribution`  
**Query Params**: None

#### Response Body (`WalletDistributionResponse`)
| Field | Type | Description |
|---|---|---|
| `by_provider` | `DistributionItem[]` | Distribution by provider |
| `total` | `number` | Total wallets |

**DistributionItem Object**:
| Field | Type | Description |
|---|---|---|
| `name` | `string` | Distribution category name |
| `count` | `number` | Count |
| `percentage` | `number` | Percentage (0-100) |

### Get Transaction Distribution
**Endpoint**: `GET /api/admin/metrics/transactions/distribution`  
**Query Params**: None

#### Response Body (`TransactionDistributionResponse`)
| Field | Type | Description |
|---|---|---|
| `by_chain` | `DistributionItem[]` | Distribution by chain |
| `by_status` | `DistributionItem[]` | Distribution by status |
| `by_type` | `DistributionItem[]` | Distribution by type |
| `total` | `number` | Total transactions |

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `400` | `DomainFieldError` | Invalid date format or parameter | Show error: "Invalid date format" + Reset to defaults |
| `500` | `Exception` | Internal server error | Show error: "Failed to load metrics" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useMetricsOverview()` hook which fetches `/api/admin/metrics/overview`.
2. **Display**:
   - Overview cards: Display `wallets`, `transactions`, `users` metrics in summary cards.
   - Time series charts: Call time series endpoints to display trends:
     - Transaction time series: Line chart showing transaction volume over time.
     - Wallet time series: Line chart showing wallet growth over time.
     - User activity time series: Line chart showing active users over time.
   - Distribution charts: Call distribution endpoints to display:
     - Wallet distribution: Pie/bar chart showing wallet distribution by provider.
     - Transaction distribution: Stacked bar chart showing distribution by chain, status, type.
3. **Date Range Selection**: On date range change, update `from_date` and `to_date` query params, refetch time series data.
4. **Filtering**: On chain or transaction type filter change, update query params and refetch.
5. **Real-time Updates**: Poll metrics every 30 seconds or use WebSocket for live updates (optional).
