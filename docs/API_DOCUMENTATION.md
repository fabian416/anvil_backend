# Anvil Backend API Documentation

**Version**: 2.0  
**Base URL**: `http://localhost:8000/api/v1`  
**WebSocket URL**: `ws://localhost:8000/api/v1`  

---

## Table of Contents

1. [Authentication](#authentication)
2. [WebSocket Chat](#websocket-chat)
3. [MCP Servers](#mcp-servers)
4. [Admin Endpoints](#admin-endpoints)
5. [Performance](#performance)
6. [Error Handling](#error-handling)

---

## Authentication

All authenticated endpoints require a JWT token in the `Authorization` header or as a query parameter for WebSocket connections.

### Format
```
Authorization: Bearer <your_jwt_token>
```

### Obtaining a Token
```bash
POST /api/v1/account/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## WebSocket Chat

Real-time chat with AI agents using WebSocket streaming.

### Connection

**Endpoint**: `ws://localhost:8000/api/v1/ws/chat`

**Query Parameters**:
- `token` (required): JWT authentication token
- `session_id` (optional): Chat session ID for conversation continuity

**Example**:
```javascript
const ws = new WebSocket(
  'ws://localhost:8000/api/v1/ws/chat?token=YOUR_JWT_TOKEN'
);
```

### Client → Server Messages

#### Send Chat Message
```json
{
  "type": "message",
  "content": "Swap 1 ETH for USDC on Ethereum",
  "conversation_id": "optional-uuid"
}
```

#### Heartbeat
```json
{
  "type": "ping"
}
```

### Server → Client Messages

#### Streaming Token
```json
{
  "type": "stream",
  "content": "token",
  "message_id": "uuid"
}
```

#### Progress Event
```json
{
  "type": "progress",
  "status": "thinking|routing|tool_call|tool_completed",
  "message": "Checking swap prices...",
  "tool": "get_swap_quote",
  "agent": "trading"
}
```

#### Complete Message
```json
{
  "type": "message_complete",
  "message_id": "uuid",
  "content": "Complete response text",
  "metadata": {
    "agent": "trading",
    "confidence": 0.95
  }
}
```

#### Error
```json
{
  "type": "error",
  "error": "Error message",
  "code": "error_code"
}
```

#### System Message
```json
{
  "type": "system",
  "message": "Connected to Anvil AI Chat",
  "user_id": "user_123",
  "session_id": "session_456",
  "timestamp": "2024-12-02T00:00:00Z"
}
```

---

## MCP Servers

Model Context Protocol servers expose tools for DeFi operations.

### MCP Manager

**Base URL**: `http://localhost:8080`

#### List All Tools
```bash
GET /tools
```

**Response:**
```json
{
  "tools": [
    {
      "name": "portfolio__get_user_balance",
      "server": "portfolio",
      "description": "Get user token balances",
      "parameters": {...}
    }
  ],
  "total_tools": 27,
  "servers": ["portfolio", "1inch", "aave", "defillama"]
}
```

#### Call Tool
```bash
POST /tools/{tool_name}
Content-Type: application/json

{
  "parameters": {
    "chain_id": 1,
    "from_token": "0xEeee...",
    "to_token": "0xA0b8...",
    "amount": "1000000000000000000"
  }
}
```

**Response:**
```json
{
  "result": {
    "to_amount": "2500000000",
    "price_impact": 0.15,
    "gas_estimate": "150000"
  }
}
```

### Portfolio MCP (`http://localhost:8081`)

#### get_user_balance
Get token balances for a user.

**Parameters**:
- `user_id` (string, required)
- `chain_id` (integer, optional)

**Example**:
```bash
POST /tools/get_user_balance
{
  "parameters": {
    "user_id": "user_123",
    "chain_id": 1
  }
}
```

#### get_user_positions
Get DeFi positions (lending, LP, staking).

**Parameters**:
- `user_id` (string, required)

#### get_portfolio_summary
Get complete portfolio summary.

**Parameters**:
- `user_id` (string, required)

### 1inch MCP (`http://localhost:8082`)

#### get_swap_quote
Get swap quote from 1inch.

**Parameters**:
- `chain_id` (integer, required): 1=Ethereum, 137=Polygon, etc.
- `from_token` (string, required): Token address (0xEeee... for ETH)
- `to_token` (string, required): Token address
- `amount` (string, required): Amount in wei
- `slippage` (float, optional): Max slippage % (default: 1.0)

#### get_token_price
Get token price in USD.

**Parameters**:
- `chain_id` (integer, required)
- `token` (string, required): Token symbol or address

#### execute_swap
Execute swap transaction.

**Parameters**:
- `chain_id` (integer, required)
- `from_token` (string, required)
- `to_token` (string, required)
- `amount` (string, required)
- `user_address` (string, required)
- `slippage` (float, optional)

#### get_liquidity_sources
Get available liquidity sources.

**Parameters**:
- `chain_id` (integer, required)

### Aave MCP (`http://localhost:8083`)

#### get_market_data
Get lending/borrowing rates for Aave markets.

**Parameters**:
- `chain_id` (integer, required)
- `assets` (array[string], optional): Filter by assets

#### get_user_positions
Get user's Aave positions.

**Parameters**:
- `chain_id` (integer, required)
- `user_address` (string, required)

#### supply_asset
Supply asset to Aave.

**Parameters**:
- `chain_id` (integer, required)
- `asset` (string, required)
- `amount` (string, required)
- `user_address` (string, required)

#### borrow_asset
Borrow asset from Aave.

**Parameters**:
- `chain_id` (integer, required)
- `asset` (string, required)
- `amount` (string, required)
- `user_address` (string, required)
- `rate_mode` (integer, required): 1=stable, 2=variable

#### calculate_health_factor
Calculate user's health factor.

**Parameters**:
- `chain_id` (integer, required)
- `user_address` (string, required)

### DeFiLlama MCP (`http://localhost:8084`)

#### get_protocol_tvl
Get protocol TVL.

**Parameters**:
- `protocol` (string, required): Protocol slug (e.g., "aave", "uniswap")

#### get_yields
Get yield farming opportunities.

**Parameters**:
- `chain` (string, optional)
- `stablecoin` (boolean, optional)
- `min_tvl` (float, optional)

#### get_protocol_fees
Get protocol fees and revenue.

**Parameters**:
- `protocol` (string, required)

#### compare_protocols
Compare multiple protocols.

**Parameters**:
- `protocols` (array[string], required)

---

## Admin Endpoints

### Distillation Management

#### Get Configuration
```bash
GET /admin/distillation/config
Authorization: Bearer <admin_token>
```

#### Update Configuration
```bash
PUT /admin/distillation/config
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "cache_ttl_hours": 24,
  "semantic_threshold": 0.85,
  "static_response_enabled": true
}
```

#### Get Telemetry
```bash
GET /admin/distillation/telemetry?start_date=2024-01-01&end_date=2024-12-31
Authorization: Bearer <admin_token>
```

### Projects Management

#### Create Project
```bash
POST /admin/projects
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "DeFi Trading Bot",
  "description": "Automated trading strategies",
  "owner_id": "user_123"
}
```

#### List Projects
```bash
GET /admin/projects?skip=0&limit=20
Authorization: Bearer <admin_token>
```

#### Update Project
```bash
PUT /admin/projects/{project_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Updated Name",
  "is_active": true
}
```

---

## Performance

### Agent Performance Statistics

#### Get Overall Statistics
```bash
GET /api/v1/agno/stats
```

**Response:**
```json
{
  "total_requests": 1000,
  "successful_requests": 950,
  "failed_requests": 50,
  "success_rate": 95.0,
  "cache_hit_rate": 75.2,
  "duration_ms": {
    "avg": 1250.5,
    "min": 50.2,
    "max": 5000.0,
    "p50": 1000.0,
    "p95": 3000.0,
    "p99": 4500.0
  },
  "tool_usage": {
    "get_swap_quote": 150,
    "get_market_data": 200
  }
}
```

#### Get Real-time Statistics (Last 5 minutes)
```bash
GET /api/v1/agno/stats/realtime
```

#### Get Agent-Specific Statistics
```bash
GET /api/v1/agno/stats/agent/trading
```

#### Get Slow Queries
```bash
GET /api/v1/agno/slow-queries?threshold_ms=5000&limit=10
```

**Response:**
```json
{
  "slow_queries": [
    {
      "agent_type": "trading",
      "query": "Swap 1000 ETH for USDC...",
      "duration_ms": 7500.0,
      "tools_used": ["get_swap_quote", "execute_swap"],
      "success": true,
      "timestamp": "2024-12-02T00:00:00Z"
    }
  ]
}
```

### WebSocket Statistics

#### Get Connection Statistics
```bash
GET /api/v1/ws/stats
```

**Response:**
```json
{
  "active_connections": 42,
  "active_users": 35,
  "total_connections": 1523,
  "total_messages_sent": 45678,
  "connections_per_user": {
    "user_123": 2,
    "user_456": 1
  }
}
```

---

## Error Handling

### Standard Error Response
```json
{
  "type": "error",
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### Common Error Codes

#### Authentication Errors
- `invalid_token`: JWT token is invalid or expired
- `missing_token`: No authentication token provided
- `insufficient_permissions`: User lacks required permissions

#### Validation Errors
- `empty_message`: Message content is empty
- `invalid_parameters`: Tool parameters are invalid
- `unknown_type`: Unknown message type

#### Processing Errors
- `processing_error`: Error during agent processing
- `tool_error`: Error executing tool
- `timeout`: Operation timed out

#### WebSocket Errors
- `connection_limit`: Too many concurrent connections
- `rate_limit`: Rate limit exceeded

### HTTP Status Codes
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Rate Limits

### WebSocket
- Max connections per user: 5
- Max messages per minute: 60

### HTTP API
- Max requests per minute: 1000
- Max requests per hour: 50000

---

## Best Practices

### WebSocket Chat
1. Always implement reconnection logic
2. Use heartbeat (ping/pong) to keep connection alive
3. Handle all message types (stream, progress, error, etc.)
4. Display progress events to improve UX
5. Accumulate streaming tokens for smooth display

### MCP Tools
1. Always validate parameters before calling
2. Handle errors gracefully
3. Use batching for multiple tool calls
4. Implement timeout handling
5. Cache responses when appropriate

### Performance
1. Enable response caching for repeated queries
2. Use tool call batching for parallel execution
3. Monitor slow queries and optimize
4. Implement proper error handling
5. Use WebSocket for real-time features

---

## Support

For issues or questions:
- GitHub: [github.com/Anvil-com/anvil_backend](https://github.com/Anvil-com/anvil_backend)
- Email: support@anvil.com
- Docs: [docs.anvil.com](https://docs.anvil.com)

---

**Last Updated**: December 2, 2024  
**API Version**: 2.0  
**Status**: Production Ready
