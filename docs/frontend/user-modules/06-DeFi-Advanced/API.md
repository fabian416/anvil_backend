# DeFi Advanced API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URL**: `/api/v1/user/ultra`

---

## 📋 Table of Contents

1. [Auto-Executor Endpoints](#auto-executor-endpoints)
2. [Arbitrage Endpoints](#arbitrage-endpoints)
3. [Flash Loans Endpoints](#flash-loans-endpoints)
4. [MEV Protection Endpoints](#mev-protection-endpoints)
5. [Request/Response Schemas](#requestresponse-schemas)
6. [Error Handling](#error-handling)

---

## 🔌 Auto-Executor Endpoints

### 1. Start Auto-Executor

**Method**: `POST`  
**Endpoint**: `/api/v1/user/ultra/auto-executor/start`  
**Auth Required**: Yes (Bearer Token)

#### Request

No request body required

#### Response

##### Success Response (200 OK)
```typescript
interface AutoExecutorResponse {
  status: string;                 // "started" | "stopped" | "paused" | "running"
  message: string;
}
```

**JSON Example**:
```json
{
  "status": "started",
  "message": "Auto-executor started successfully"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `400` | `BadRequestError` | Already running | Show error: "Auto-executor is already running" |
| `500` | `InternalServerError` | Failed to start | Show error: "Failed to start auto-executor" + Retry |

---

### 2. Stop Auto-Executor

**Method**: `POST`  
**Endpoint**: `/api/v1/user/ultra/auto-executor/stop`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface AutoExecutorResponse {
  status: "stopped";
  message: string;
}
```

---

### 3. Pause Auto-Executor

**Method**: `POST`  
**Endpoint**: `/api/v1/user/ultra/auto-executor/pause`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface AutoExecutorResponse {
  status: "paused";
  message: string;
}
```

---

### 4. Resume Auto-Executor

**Method**: `POST`  
**Endpoint**: `/api/v1/user/ultra/auto-executor/resume`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface AutoExecutorResponse {
  status: "running";
  message: string;
}
```

---

### 5. Get Auto-Executor Status

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/auto-executor/status`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface AutoExecutorStatusResponse {
  status: string;                 // "started" | "stopped" | "paused" | "running"
  is_running: boolean;
  last_scan_at: string | null;    // ISO 8601
  opportunities_found: number;
  executions_successful: number;
  executions_failed: number;
  config: AutoExecutorConfig;
}

interface AutoExecutorConfig {
  min_profit_usd: number;
  scan_interval_seconds: number;
  max_gas_price_gwei: number;
}
```

**JSON Example**:
```json
{
  "status": "running",
  "is_running": true,
  "last_scan_at": "2024-01-15T10:30:00Z",
  "opportunities_found": 5,
  "executions_successful": 3,
  "executions_failed": 0,
  "config": {
    "min_profit_usd": 75.0,
    "scan_interval_seconds": 10,
    "max_gas_price_gwei": 120
  }
}
```

---

### 6. Update Auto-Executor Config

**Method**: `PUT`  
**Endpoint**: `/api/v1/user/ultra/auto-executor/config`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ConfigUpdateRequest {
  min_profit_usd?: number;        // Optional: Minimum profit USD
  scan_interval_seconds?: number; // Optional: Scan interval seconds
  max_gas_price_gwei?: number;   // Optional: Max gas price gwei
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `min_profit_usd` | `number` | No | Minimum profit USD | > 0 |
| `scan_interval_seconds` | `number` | No | Scan interval | >= 5 |
| `max_gas_price_gwei` | `number` | No | Max gas price | > 0 |

**JSON Example**:
```json
{
  "min_profit_usd": 75.0,
  "scan_interval_seconds": 10,
  "max_gas_price_gwei": 120
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ConfigUpdateResponse {
  message: string;
  config: AutoExecutorConfig;
}
```

---

### 7. Manual Scan

**Method**: `POST`  
**Endpoint**: `/api/v1/user/ultra/auto-executor/scan`  
**Auth Required**: Yes (Bearer Token)

#### Request

No request body required

#### Response

##### Success Response (200 OK)
```typescript
interface ManualScanResponse {
  opportunities_found: number;
  opportunities: ArbitrageOpportunity[];
  executed: boolean;
  execution_result?: ExecutionResult;
}

interface ArbitrageOpportunity {
  id: string;
  profit_usd: number;
  route: string[];
  gas_estimate: number;
  risk_score: number;
}

interface ExecutionResult {
  success: boolean;
  tx_hash?: string;
  profit_realized?: number;
  error?: string;
}
```

---

## 🔌 Arbitrage Endpoints

### 8. Discover Arbitrage Opportunities

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/arbitrage/discover`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `capital` | `number` | No | Starting capital USD | `10000` |
| `type` | `string` | No | Filter by type | All types |
| `min_profit` | `number` | No | Minimum profit USD | None |

**Valid Type Values**: `2hop`, `3hop`, `triangle`

#### Response

##### Success Response (200 OK)
```typescript
interface ArbitrageOpportunityResponse {
  opportunity_id: string;
  type: string;                   // "2hop" | "3hop" | "triangle"
  path: TradingPath[];
  expected_profit_usd: string;
  profit_percentage: number;
  required_capital: string;
  estimated_gas_cost: string;
  confidence_score: number;       // 0-1
}

interface TradingPath {
  dex: string;                    // "uniswap_v2" | "sushiswap" | etc.
  token_in: string;
  token_out: string;
  amount_in: string;
  amount_out: string;
  price: string;
}
```

**JSON Example**:
```json
{
  "opportunity_id": "ARB-1638360000-0001",
  "type": "2hop",
  "path": [
    {
      "dex": "uniswap_v2",
      "token_in": "WETH",
      "token_out": "USDC",
      "amount_in": "10000",
      "amount_out": "20000000",
      "price": "2000.0"
    },
    {
      "dex": "sushiswap",
      "token_in": "USDC",
      "token_out": "WETH",
      "amount_in": "20000000",
      "amount_out": "10050",
      "price": "0.0004975"
    }
  ],
  "expected_profit_usd": "95.50",
  "profit_percentage": 0.955,
  "required_capital": "10000",
  "estimated_gas_cost": "15.00",
  "confidence_score": 0.85
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `BadRequestError` | Invalid type parameter | Show error: "Invalid arbitrage type" |
| `500` | `InternalServerError` | Discovery failed | Show error: "Failed to discover opportunities" + Retry |

---

### 9. List Arbitrage Opportunities

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/arbitrage/opportunities`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max results | `10` |
| `sort_by` | `string` | No | Sort field | `profit` |

**Valid Sort Values**: `profit`, `confidence`, `timestamp`

#### Response

##### Success Response (200 OK)
Returns `ArbitrageOpportunityResponse[]` (array of opportunities)

---

### 10. Simulate Arbitrage Opportunity

**Method**: `POST`  
**Endpoint**: `/api/v1/user/ultra/arbitrage/simulate`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface SimulationRequest {
  opportunity_id: string;         // Required: Opportunity ID
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface SimulationResponse {
  opportunity_id: string;
  type: string;
  expected_profit: string;
  simulated_profit: string;       // With slippage
  slippage_impact: string;
  success_probability: number;    // 0-1
  recommendation: string;         // "Execute" | "Skip"
}
```

**JSON Example**:
```json
{
  "opportunity_id": "ARB-1638360000-0001",
  "type": "2hop",
  "expected_profit": "95.50",
  "simulated_profit": "94.55",
  "slippage_impact": "0.95",
  "success_probability": 0.85,
  "recommendation": "Execute"
}
```

---

### 11. Execute Arbitrage (MEV-Protected)

**Method**: `POST`  
**Endpoint**: `/api/v1/user/ultra/mev/execute`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ExecuteArbitrageRequest {
  opportunity_id: string;         // Required: Opportunity ID
  use_mev_protection: boolean;     // Optional: Use MEV protection (default: true)
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ExecutionResponse {
  execution_id: string;
  opportunity_id: string;
  status: string;                 // "success" | "failed" | "pending"
  expected_profit: string;
  realized_profit?: string;
  gas_cost: string;
}
```

---

### 12. Get Bundle Status

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/mev/bundles/{bundle_id}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `bundle_id` | `string` | Yes | Bundle ID |

#### Response

##### Success Response (200 OK)
```typescript
interface BundleStatusResponse {
  bundle_id: string;
  status: string;                 // "included" | "failed" | "pending"
  block_number?: number;
  profit_realized?: string;
}
```

---

### 13. Get MEV Statistics

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/mev/statistics`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface MEVStatisticsResponse {
  total_bundles: number;
  by_status: {
    included: number;
    failed: number;
    pending: number;
  };
  success_rate: number;           // Percentage
  total_profit: string;
}
```

---

### 14. Get MEV Protection Info

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/mev/protection-info`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface MEVProtectionInfoResponse {
  protection_level: string;       // "basic" | "advanced"
  use_flashbots: boolean;
  use_private_relay: boolean;
  use_mev_share: boolean;
  max_gas_price_gwei: number;
  simulation_enabled: boolean;
}
```

---

## 🔌 Flash Loans Endpoints

### 15. Get Flash Loan Protocols

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/flash-loans/protocols`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface FlashLoanProtocolsResponse {
  protocols: FlashLoanProtocol[];
}

interface FlashLoanProtocol {
  protocol: string;               // "aave_v3" | "balancer" | "uniswap_v3"
  name: string;
  fee_percentage: number;         // Protocol fee (e.g., 0.09 = 0.09%)
  max_loan_usd: string;
  supported_tokens: string[];
  requires_collateral: boolean;
}
```

**JSON Example**:
```json
{
  "protocols": [
    {
      "protocol": "aave_v3",
      "name": "Aave V3",
      "fee_percentage": 0.09,
      "max_loan_usd": "10000000",
      "supported_tokens": ["USDC", "USDT", "DAI", "WETH", "WBTC"],
      "requires_collateral": false
    },
    {
      "protocol": "balancer",
      "name": "Balancer",
      "fee_percentage": 0.0,
      "max_loan_usd": "5000000",
      "supported_tokens": ["USDC", "USDT", "DAI", "WETH"],
      "requires_collateral": false
    }
  ]
}
```

---

### 16. Get Best Flash Loan Protocol

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/flash-loans/best-protocol`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `token` | `string` | **Yes** | Token symbol (e.g., "USDC", "USDT") |
| `amount_usd` | `number` | **Yes** | Loan amount in USD |

#### Response

##### Success Response (200 OK)
```typescript
interface BestProtocolResponse {
  recommended_protocol: string;
  protocol_name: string;
  fee_percentage: number;
  estimated_fees_usd: string;
  reason: string;
}
```

**JSON Example**:
```json
{
  "recommended_protocol": "balancer",
  "protocol_name": "Balancer",
  "fee_percentage": 0.0,
  "estimated_fees_usd": "5.00",
  "reason": "No protocol fee, only gas cost"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `BadRequestError` | No protocol supports token/amount | Show error: "No protocol available for this token/amount" |
| `500` | `InternalServerError` | Failed to get protocol | Show error + Retry |

---

### 17. Simulate Flash Loan

**Method**: `POST`  
**Endpoint**: `/api/v1/user/ultra/flash-loans/simulate`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface FlashLoanSimulateRequest {
  protocol: string;               // Required: "aave_v3" | "balancer" | "uniswap_v3"
  token_address: string;           // Required: Token contract address
  amount: string;                 // Required: Loan amount (in token units)
  receiver_address: string;        // Required: Receiver contract address
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `protocol` | `string` | **Yes** | Flash loan protocol | Valid protocol identifier |
| `token_address` | `string` | **Yes** | Token contract address | Valid 0x address |
| `amount` | `string` | **Yes** | Loan amount | Valid number string |
| `receiver_address` | `string` | **Yes** | Receiver contract address | Valid 0x address |

#### Response

##### Success Response (200 OK)
```typescript
interface FlashLoanResultResponse {
  status: string;                 // "success" | "failed"
  tx_hash?: string;
  gas_used?: number;
  gas_price_gwei?: number;
  profit_usd?: string;
  fees_paid: string;
  error_message?: string;
}
```

**Note**: This is a simulation - no actual transaction is executed.

---

### 18. Get Protocol Liquidity

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/flash-loans/liquidity`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `protocol` | `string` | **Yes** | Protocol identifier |
| `token` | `string` | **Yes** | Token symbol |

#### Response

##### Success Response (200 OK)
```typescript
interface ProtocolLiquidityResponse {
  protocol: string;
  token: string;
  available_liquidity_usd: string;
  max_loan_usd: string;
}
```

---

### 19. Estimate Flash Loan Fees

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/flash-loans/estimate-fees`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `protocol` | `string` | **Yes** | Protocol identifier |
| `amount_usd` | `number` | **Yes** | Amount in USD |

#### Response

##### Success Response (200 OK)
```typescript
interface FlashLoanFeeEstimate {
  protocol: string;
  amount_usd: number;
  fee_usd: number;
  fee_percentage: string;
  total_cost_usd: number;
}
```

---

## 🔌 MEV Protection Endpoints

### 12. Get MEV Protection Status

**Method**: `GET`  
**Endpoint**: `/api/v1/user/ultra/mev/status`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface MEVProtectionStatus {
  enabled: boolean;
  protected_transactions: number;
  mev_attempts_blocked: number;
  last_scan_at: string | null;
}
```

---

### 13. Enable MEV Protection

**Method**: `POST`  
**Endpoint**: `/api/v1/user/ultra/mev/enable`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface MEVProtectionResponse {
  enabled: boolean;
  message: string;
}
```

---

## 📊 Error Handling Summary

### Common Error Patterns

1. **Authentication Errors (401)**
   - Invalid or expired token
   - **Action**: Refresh token, if fails → redirect to login

2. **Validation Errors (400)**
   - Invalid request data
   - **Action**: Show inline field errors

3. **Service Unavailable (503)**
   - Backend service down
   - **Action**: Show error message + Retry button

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

---

## 🔗 Related Documentation

- **Backend Controller**: `src/app/presentation/http/controllers/ultra/auto_executor.py`
- **Backend Controller**: `src/app/presentation/http/controllers/ultra/arbitrage.py`
- **Backend Controller**: `src/app/presentation/http/controllers/ultra/flash_loans.py`
- **Backend Controller**: `src/app/presentation/http/controllers/ultra/mev.py`
- **Application Service**: `src/app/application/ultra/auto_executor.py`
- **Frontend Implementation**: `06-DeFi-Advanced/IMPLEMENTATION.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready
