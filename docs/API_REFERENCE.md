# Anvil Backend API Reference

Complete API documentation for all endpoints including Hunter AI Bot features.

**Version:** 1.1.0  
**Last Updated:** December 1, 2025

## 🆕 What's New in v1.1.0

### Hunter AI Chat Integration ✅
All 6 Hunter AI modules now accessible via **chat interface**!

**Natural Language Queries:**
- "Analyze ETH" → Sentiment + Prediction + Risk + Signals (all tools)
- "What's BTC sentiment?" → Sentiment analysis
- "Should I buy UNI?" → Trading signal
- "How risky is SOL?" → Risk assessment

See [Phase 1 Integration Docs](./PHASE1_HUNTER_CHAT_INTEGRATION.md) for details.

---

## Table of Contents

1. [General Endpoints](#general-endpoints)
2. [Account Management](#account-management)
3. [User Management](#user-management)
4. [Subscription Management](#subscription-management)
5. [Hunter AI Bot](#hunter-ai-bot)
   - [Sentiment Analysis](#sentiment-analysis)
   - [Price Prediction](#price-prediction)
   - [Risk Analysis](#risk-analysis)
   - [Trading Signals](#trading-signals)
   - [Portfolio Optimization](#portfolio-optimization)
   - [Pattern Recognition](#pattern-recognition)
6. [MCP Servers](#mcp-servers)
7. [GraphRAG](#graphrag)

---

## General Endpoints

### Health Check
- **GET** `/` - Redirects to Swagger documentation
- **GET** `/api/v1/` - Returns `200 OK` if API is alive

---

## Account Management

**Base Path:** `/api/v1/account`

### Public Endpoints (No Authentication Required)

#### Sign Up
- **POST** `/signup`
- **Description:** Register a new user
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response:** `201 Created`

#### Login
- **POST** `/login`
- **Description:** Authenticate and create session
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response:** JWT token in cookies

#### Password Reset Request
- **POST** `/password-reset/request`
- **Description:** Request password reset token
- **Request Body:**
  ```json
  {
    "email": "user@example.com"
  }
  ```

#### Password Reset Confirm
- **POST** `/password-reset/confirm`
- **Description:** Reset password with token
- **Request Body:**
  ```json
  {
    "token": "reset_token",
    "new_password": "NewPassword123!"
  }
  ```

### Authenticated Endpoints

#### Get Current User
- **GET** `/me`
- **Description:** Get current user profile
- **Headers:** `Authorization: Bearer <token>`
- **Response:**
  ```json
  {
    "id": "uuid",
    "email": "user@example.com",
    "is_active": true,
    "is_admin": false
  }
  ```

#### Update Profile
- **PUT** `/me`
- **Description:** Update current user profile

#### Change Password
- **PUT** `/password`
- **Description:** Change user password

#### Logout
- **DELETE** `/logout`
- **Description:** End current session

#### Refresh Token
- **POST** `/refresh-token`
- **Description:** Refresh access token

---

## User Management

**Base Path:** `/api/v1/users`
**Authentication:** Admin required for most endpoints

#### List Users
- **GET** `/`
- **Description:** Get paginated list of users
- **Query Parameters:**
  - `page`: Page number (default: 1)
  - `size`: Items per page (default: 20)

#### Create User
- **POST** `/`
- **Description:** Create new user (admin only)

#### Grant Admin
- **PATCH** `/{email}/grant-admin`
- **Description:** Grant admin privileges (super admin only)

#### Revoke Admin
- **PATCH** `/{email}/revoke-admin`
- **Description:** Revoke admin privileges (super admin only)

#### Activate User
- **PATCH** `/{email}/activate`
- **Description:** Activate deactivated user

#### Deactivate User
- **PATCH** `/{email}/deactivate`
- **Description:** Deactivate user account

---

## Subscription Management

**Base Path:** `/api/v1/subscription`
**Authentication:** Required

#### Get Subscriptions
- **GET** `/`
- **Description:** Get all available subscription plans
- **Response:**
  ```json
  [
    {
      "id": "uuid",
      "name": "Premium",
      "price": 29.99,
      "interval": "month"
    }
  ]
  ```

#### Create Subscription
- **POST** `/`
- **Description:** Subscribe to a plan
- **Request Body:**
  ```json
  {
    "plan_id": "uuid"
  }
  ```

#### Cancel Subscription
- **POST** `/cancel`
- **Description:** Cancel active subscription

---

## Hunter AI Bot

### Sentiment Analysis

**Base Path:** `/api/v1/hunter/sentiment`
**Authentication:** Required

#### Multi-Source Sentiment Analysis
- **POST** `/analyze/{token_symbol}`
- **Description:** Analyze sentiment from 4 sources (Twitter, Reddit, Discord, News)
- **Path Parameters:**
  - `token_symbol`: Token symbol (e.g., BTC, ETH)
- **Response:**
  ```json
  {
    "sentiment": {
      "overall_score": 72.5,
      "overall_confidence": 0.85,
      "trend": "rising",
      "sources": {
        "twitter": 75.0,
        "reddit": 68.0,
        "discord": 74.0,
        "news": 73.0
      }
    },
    "timestamp": "2025-12-03T20:00:00Z"
  }
  ```

#### Trending Tokens
- **GET** `/trending`
- **Description:** Get tokens with highest sentiment momentum
- **Query Parameters:**
  - `limit`: Number of results (default: 10)
- **Response:**
  ```json
  [
    {
      "token": "BTC",
      "sentiment_score": 78.5,
      "change_24h": 5.2
    }
  ]
  ```

#### Compare Tokens
- **POST** `/compare`
- **Description:** Compare sentiment across multiple tokens
- **Request Body:**
  ```json
  {
    "tokens": ["BTC", "ETH", "SOL"]
  }
  ```

#### News Headlines
- **GET** `/news/headlines`
- **Description:** Get latest crypto news sentiment
- **Query Parameters:**
  - `limit`: Number of headlines (default: 20)

---

### Price Prediction

**Base Path:** `/api/v1/hunter/prediction`
**Authentication:** Required

#### Train LSTM Model
- **POST** `/train/{token_symbol}`
- **Description:** Train price prediction model for token
- **Path Parameters:**
  - `token_symbol`: Token symbol
- **Response:**
  ```json
  {
    "status": "training_started",
    "estimated_time": "5 minutes"
  }
  ```

#### Predict Price
- **GET** `/predict/{token_symbol}`
- **Description:** Get price prediction
- **Path Parameters:**
  - `token_symbol`: Token symbol
- **Query Parameters:**
  - `horizon`: Forecast horizon in hours (default: 24)
- **Response:**
  ```json
  {
    "current_price": 2000.0,
    "predicted_price": 2060.0,
    "change_percent": 3.0,
    "confidence": 0.75,
    "direction": "up",
    "forecast_time": "2025-12-04T20:00:00Z"
  }
  ```

#### Multi-Horizon Prediction
- **GET** `/predict/{token_symbol}/multi-horizon`
- **Description:** Get predictions for multiple time horizons
- **Response:**
  ```json
  {
    "predictions": {
      "24h": {"predicted_price": 2060.0, "confidence": 0.75},
      "7d": {"predicted_price": 2200.0, "confidence": 0.65}
    }
  }
  ```

---

### Risk Analysis

**Base Path:** `/api/v1/hunter/risk`
**Authentication:** Required

#### Comprehensive Risk Analysis
- **GET** `/analyze/{token_symbol}`
- **Description:** Get 4-factor risk assessment
- **Response:**
  ```json
  {
    "overall_score": 45.2,
    "risk_level": "Medium",
    "factors": {
      "volatility": 52.3,
      "liquidity": 35.8,
      "smart_contract": 42.1,
      "correlation": 50.5
    },
    "recommendation": "Moderate position sizing recommended"
  }
  ```

#### Individual Risk Factors
- **GET** `/volatility/{token_symbol}` - Volatility risk
- **GET** `/liquidity/{token_symbol}` - Liquidity risk
- **GET** `/smart-contract/{token_symbol}` - Smart contract risk
- **GET** `/correlation/{token_symbol}` - Market correlation risk

---

### Trading Signals

**Base Path:** `/api/v1/hunter/signals`
**Authentication:** Required

#### Generate Trading Signal
- **GET** `/generate/{token_symbol}`
- **Description:** Generate AI trading signal
- **Query Parameters:**
  - `timeframe`: Timeframe (1h, 4h, 1d, 1w, 1M)
- **Response:**
  ```json
  {
    "signal_type": "BUY",
    "confidence": 0.82,
    "entry_price": 2000.0,
    "stop_loss": 1920.0,
    "take_profit": 2160.0,
    "position_size": 0.15,
    "recommendation": "Strong buy signal based on positive sentiment and bullish price prediction"
  }
  ```

#### Multi-Timeframe Analysis
- **GET** `/multi-timeframe/{token_symbol}`
- **Description:** Get signals across all timeframes
- **Response:**
  ```json
  {
    "signals": {
      "1h": {"signal": "BUY", "confidence": 0.75},
      "4h": {"signal": "BUY", "confidence": 0.80},
      "1d": {"signal": "BUY", "confidence": 0.82}
    },
    "consensus": "STRONG_BUY",
    "alignment_score": 0.85
  }
  ```

#### Batch Generate Signals
- **GET** `/batch`
- **Description:** Generate signals for multiple tokens
- **Query Parameters:**
  - `tokens`: Comma-separated token list

#### Top Signals
- **GET** `/top-signals`
- **Description:** Get highest conviction signals
- **Query Parameters:**
  - `signal_type`: Filter by BUY/SELL (optional)
  - `limit`: Number of results (default: 10)

---

### Portfolio Optimization

**Base Path:** `/api/v1/hunter/portfolio`
**Authentication:** Required

#### Optimize Portfolio
- **POST** `/optimize`
- **Description:** Optimize portfolio allocation using MPT
- **Query Parameters:**
  - `tokens`: Comma-separated token symbols (e.g., BTC,ETH,SOL)
  - `risk_tolerance`: Risk tolerance 0-1 (default: 0.5)
- **Response:**
  ```json
  {
    "weights": {
      "BTC": 45.0,
      "ETH": 35.0,
      "SOL": 20.0
    },
    "metrics": {
      "expected_return": 45.2,
      "volatility": 32.8,
      "sharpe_ratio": 1.28,
      "sortino_ratio": 1.45,
      "max_drawdown": -28.5
    }
  }
  ```

#### Calculate Efficient Frontier
- **GET** `/efficient-frontier`
- **Description:** Get efficient frontier curve
- **Query Parameters:**
  - `tokens`: Comma-separated token symbols
- **Response:**
  ```json
  {
    "returns": [25.0, 30.0, 35.0, 40.0],
    "risks": [20.0, 25.0, 30.0, 35.0],
    "sharpe_ratios": [1.1, 1.15, 1.08, 0.95],
    "max_sharpe_portfolio": {
      "return": 30.0,
      "risk": 25.0,
      "weights": {"BTC": 40.0, "ETH": 35.0, "SOL": 25.0}
    }
  }
  ```

#### Analyze Portfolio
- **POST** `/analyze`
- **Description:** Analyze existing portfolio
- **Request Body:**
  ```json
  {
    "BTC": 0.6,
    "ETH": 0.4
  }
  ```
- **Response:** Portfolio metrics (return, volatility, Sharpe, etc.)

#### Generate Rebalancing Plan
- **POST** `/rebalance`
- **Description:** Get rebalancing recommendations
- **Request Body:**
  ```json
  {
    "current_portfolio": {"BTC": 0.7, "ETH": 0.3},
    "risk_tolerance": 0.5
  }
  ```
- **Response:**
  ```json
  {
    "target_weights": {"BTC": 0.55, "ETH": 0.45},
    "changes": {"BTC": -0.15, "ETH": +0.15},
    "trades": [
      {"token": "BTC", "action": "SELL", "change_pct": -15.0},
      {"token": "ETH", "action": "BUY", "change_pct": +15.0}
    ],
    "estimated_cost": 0.30
  }
  ```

---

### Pattern Recognition

**Base Path:** `/api/v1/hunter/patterns`
**Authentication:** Required

#### Detect Chart Patterns
- **GET** `/chart/{token_symbol}`
- **Description:** Detect technical chart patterns
- **Query Parameters:**
  - `min_confidence`: Minimum confidence (0-1, default: 0.6)
- **Response:**
  ```json
  [
    {
      "pattern_type": "ascending_triangle",
      "signal": "bullish",
      "confidence": 0.75,
      "key_levels": {
        "resistance": 2100.0,
        "support_start": 1950.0,
        "support_end": 2050.0
      },
      "description": "Ascending triangle indicates bullish breakout potential"
    }
  ]
  ```

#### Detect Candlestick Patterns
- **GET** `/candlestick/{token_symbol}`
- **Description:** Detect candlestick patterns
- **Query Parameters:**
  - `min_confidence`: Minimum confidence (default: 0.6)
- **Response:**
  ```json
  [
    {
      "pattern": "bullish_engulfing",
      "signal": "bullish",
      "confidence": 0.8,
      "price": 2000.0,
      "date": "2025-12-03T20:00:00Z",
      "description": "Bullish engulfing indicates strong buying pressure"
    }
  ]
  ```

#### Find Support/Resistance
- **GET** `/support-resistance/{token_symbol}`
- **Description:** Identify key price levels
- **Response:**
  ```json
  {
    "support": [
      {
        "level": 1950.0,
        "strength": 0.85,
        "touches": 4,
        "first_touch": "2025-11-15T00:00:00Z",
        "last_touch": "2025-12-01T00:00:00Z"
      }
    ],
    "resistance": [
      {
        "level": 2100.0,
        "strength": 0.90,
        "touches": 5
      }
    ]
  }
  ```

#### Comprehensive Pattern Analysis
- **GET** `/analysis/{token_symbol}`
- **Description:** Get all pattern types in one request
- **Response:**
  ```json
  {
    "chart_patterns": [...],
    "candlestick_patterns": [...],
    "support_resistance": {
      "support": [...],
      "resistance": [...]
    }
  }
  ```

---

## Pattern Types Reference

### Chart Patterns (14 types)

**Reversal Patterns:**
- `head_and_shoulders` - Bearish reversal
- `inverse_head_and_shoulders` - Bullish reversal
- `double_top` - Bearish reversal
- `double_bottom` - Bullish reversal
- `triple_top` - Bearish reversal
- `triple_bottom` - Bullish reversal

**Continuation Patterns:**
- `ascending_triangle` - Bullish continuation
- `descending_triangle` - Bearish continuation
- `symmetrical_triangle` - Neutral (breakout direction)
- `bull_flag` - Bullish continuation
- `bear_flag` - Bearish continuation
- `pennant` - Continuation (direction depends on prior trend)
- `rising_wedge` - Bearish reversal
- `falling_wedge` - Bullish reversal

### Candlestick Patterns (16 types)

**Single Candle:**
- `doji` - Indecision
- `dragonfly_doji` - Bullish reversal
- `gravestone_doji` - Bearish reversal
- `hammer` - Bullish reversal
- `hanging_man` - Bearish reversal
- `shooting_star` - Bearish reversal
- `inverted_hammer` - Bullish reversal

**Two Candle:**
- `bullish_engulfing` - Bullish reversal
- `bearish_engulfing` - Bearish reversal
- `bullish_harami` - Bullish reversal
- `bearish_harami` - Bearish reversal
- `piercing_line` - Bullish reversal
- `dark_cloud_cover` - Bearish reversal

**Three Candle:**
- `morning_star` - Bullish reversal
- `evening_star` - Bearish reversal
- `three_white_soldiers` - Strong bullish
- `three_black_crows` - Strong bearish

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message description"
}
```

**Status Codes:**
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Rate Limiting

API rate limits (per authenticated user):
- General endpoints: 100 requests/minute
- Hunter AI endpoints: 20 requests/minute
- ML-intensive endpoints (train, predict): 5 requests/minute

---

## Authentication

All protected endpoints require JWT authentication:

```
Authorization: Bearer <access_token>
```

Tokens are obtained via `/api/v1/account/login` and automatically refreshed before expiration.

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page`: Page number (1-indexed)
- `size`: Items per page (max: 100)

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

---

## API Documentation

**Interactive API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Support

For API support and questions:
- Documentation: `/docs` directory
- Issues: GitHub Issues
- API Status: `/api/v1/` health check

---

**Last Updated:** December 3, 2025  
**API Version:** v1  
**Phase 7 Complete:** Hunter AI Bot fully integrated
