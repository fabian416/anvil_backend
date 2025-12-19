# Endpoint Path Mapping

**Date:** December 19, 2025  
**Status:** ✅ All user endpoints updated to `/api/v1/user/*` prefix

## Overview

All authenticated user endpoints have been reorganized to use the `/api/v1/user/` prefix for better API organization and clarity. Admin endpoints remain under `/api/v1/admin/` and public/guest endpoints remain at `/api/v1/`.

## Updated Endpoints

### Graph Endpoints (USER)
- ✅ `/api/v1/user/graph/analytics/overview` - Get graph analytics
- ✅ `/api/v1/user/graph/analytics/validate` - Validate graph integrity
- ✅ `/api/v1/user/graph/analytics/embeddings/generate` - Generate embeddings (admin)
- ✅ `/api/v1/user/graph/search/hybrid` - Hybrid search protocols
- ✅ `/api/v1/user/graph/search/similar` - Find similar protocols
- ✅ `/api/v1/user/graph/search/contextual` - Contextual search with preferences
- ✅ `/api/v1/user/graph/monitoring/cache-stats` - Get cache statistics
- ✅ `/api/v1/user/graph/monitoring/cache` - Clear cache (admin)

### ML Endpoints (USER)
- ✅ `/api/v1/user/ml/prediction/{protocol_id}` - Predict protocol risk
- ✅ `/api/v1/user/ml/prediction/batch` - Batch predict risks
- ✅ `/api/v1/user/ml/prediction/{protocol_id}/anomalies` - Detect anomalies
- ✅ `/api/v1/user/ml/prediction/{protocol_id}/forecast` - Forecast risk
- ✅ `/api/v1/user/ml/network/pagerank` - Calculate PageRank
- ✅ `/api/v1/user/ml/network/communities` - Detect communities
- ✅ `/api/v1/user/ml/network/centrality` - Calculate centrality
- ✅ `/api/v1/user/ml/network/contagion/{protocol_id}` - Simulate contagion

### Alerts Endpoints (USER)
- ✅ `/api/v1/user/alerts/risk` - Get risk alerts
- ✅ `/api/v1/user/alerts/risk/{alert_id}` - Get specific alert
- ✅ `/api/v1/user/alerts/risk/{alert_id}/acknowledge` - Acknowledge alert
- ✅ `/api/v1/user/alerts/subscription` - Manage alert subscriptions
- ✅ `/api/v1/user/alerts/subscription/protocols/{protocol_id}` - Protocol subscriptions

### Dashboard Endpoints (USER)
- ✅ `/api/v1/user/dashboard/insights` - Get dashboard insights
- ✅ `/api/v1/user/dashboard/portfolio` - Get portfolio dashboard

### Comparison Endpoints (USER)
- ✅ `/api/v1/user/comparison/protocols` - Compare protocols

### Markets Endpoints (USER)
- ✅ `/api/v1/user/markets/overview` - Get market overview
- ✅ `/api/v1/user/markets/tokens/{token_symbol}` - Get token data
- ✅ `/api/v1/user/markets/tokens/{token_symbol}/history` - Get token history
- ✅ `/api/v1/user/markets/yields` - Get yield data

### Transaction Endpoints (USER)
- ✅ `/api/v1/user/transactions` - Log transaction / Get transaction history

### Bitcoin Endpoints (USER)
- ✅ `/api/v1/user/bitcoin/transactions` - Log/get Bitcoin transactions
- ✅ `/api/v1/user/bitcoin/wallets/create` - Create Bitcoin wallet
- ✅ `/api/v1/user/bitcoin/wallets/me` - Get my Bitcoin wallet

### Portfolio Endpoints (USER)
- ✅ `/api/v1/user/portfolio/me` - Get my portfolio
- ✅ `/api/v1/user/portfolio/{address}` - Get portfolio by address
- ✅ `/api/v1/user/portfolio/risk` - Get portfolio risk analysis
- ✅ `/api/v1/user/portfolio/risk/simulate-cascade` - Simulate cascade failure

### Hunter AI Endpoints (USER)
- ✅ `/api/v1/user/hunter/patterns/chart/{token}` - Chart pattern recognition
- ✅ `/api/v1/user/hunter/patterns/candlestick/{token}` - Candlestick patterns
- ✅ `/api/v1/user/hunter/patterns/support-resistance/{token}` - Support/resistance
- ✅ `/api/v1/user/hunter/patterns/analysis/{token}` - Pattern analysis
- ✅ `/api/v1/user/hunter/signals/generate/{token}` - Generate trading signals
- ✅ `/api/v1/user/hunter/signals/multi-timeframe/{token}` - Multi-timeframe signals
- ✅ `/api/v1/user/hunter/signals/batch` - Batch signal generation
- ✅ `/api/v1/user/hunter/signals/top-signals` - Top signals
- ✅ `/api/v1/user/hunter/sentiment/analyze/{token}` - Sentiment analysis
- ✅ `/api/v1/user/hunter/sentiment/trending` - Trending sentiment
- ✅ `/api/v1/user/hunter/sentiment/compare` - Compare sentiment
- ✅ `/api/v1/user/hunter/sentiment/news/headlines` - News headlines
- ✅ `/api/v1/user/hunter/risk/analyze/{token}` - Risk analysis
- ✅ `/api/v1/user/hunter/risk/volatility/{token}` - Volatility analysis
- ✅ `/api/v1/user/hunter/risk/liquidity/{token}` - Liquidity analysis
- ✅ `/api/v1/user/hunter/risk/smart-contract/{token}` - Smart contract risk
- ✅ `/api/v1/user/hunter/risk/correlation/{token}` - Correlation analysis
- ✅ `/api/v1/user/hunter/predictions/train/{token}` - Train prediction model
- ✅ `/api/v1/user/hunter/predictions/predict/{token}` - Predict price
- ✅ `/api/v1/user/hunter/predictions/predict/{token}/multi-horizon` - Multi-horizon prediction
- ✅ `/api/v1/user/hunter/predictions/model-info` - Model information
- ✅ `/api/v1/user/hunter/portfolio/optimize` - Optimize portfolio
- ✅ `/api/v1/user/hunter/portfolio/efficient-frontier` - Efficient frontier
- ✅ `/api/v1/user/hunter/portfolio/analyze` - Analyze portfolio
- ✅ `/api/v1/user/hunter/portfolio/rebalance` - Rebalance portfolio

### ULTRA Endpoints (USER)
- ✅ `/api/v1/user/ultra/flash-loans/protocols` - Get flash loan protocols
- ✅ `/api/v1/user/ultra/flash-loans/best-protocol` - Get best protocol
- ✅ `/api/v1/user/ultra/flash-loans/simulate` - Simulate flash loan
- ✅ `/api/v1/user/ultra/flash-loans/liquidity/{protocol}` - Get liquidity
- ✅ `/api/v1/user/ultra/flash-loans/estimate-fees` - Estimate fees
- ✅ `/api/v1/user/ultra/arbitrage/discover` - Discover arbitrage
- ✅ `/api/v1/user/ultra/arbitrage/opportunities` - Get opportunities
- ✅ `/api/v1/user/ultra/arbitrage/simulate` - Simulate arbitrage
- ✅ `/api/v1/user/ultra/arbitrage/statistics` - Get statistics
- ✅ `/api/v1/user/ultra/mev/execute` - Execute MEV protection
- ✅ `/api/v1/user/ultra/mev/bundles/{bundle_id}` - Get bundle
- ✅ `/api/v1/user/ultra/mev/statistics` - Get MEV statistics
- ✅ `/api/v1/user/ultra/mev/protection-info` - Get protection info
- ✅ `/api/v1/user/ultra/auto-executor/*` - Auto-executor endpoints

### Projects Endpoints (USER)
- ✅ `/api/v1/user/projects/*` - User project management

### Search Endpoints (USER)
- ✅ `/api/v1/user/search/history` - Get search history
- ✅ `/api/v1/user/search/*` - Other search endpoints

### Preferences Endpoints (USER)
- ✅ `/api/v1/user/preferences` - Get/update user preferences
- ✅ `/api/v1/user/preferences/*` - Preference management

### Chat Endpoints (USER)
- ✅ `/api/v1/user/chat/conversations` - Conversation management
- ✅ `/api/v1/user/chat/conversations/{id}/messages` - Message management
- ✅ `/api/v1/user/chat/intent/detect` - Intent detection
- ✅ `/api/v1/user/chat/intent/autocomplete` - Autocomplete suggestions
- ✅ `/api/v1/user/chat/intent/similar-conversations` - Find similar conversations
- ✅ `/api/v1/user/chat/search-protocols` - Search protocols from chat
- ✅ `/api/v1/user/chat/my-analytics/*` - Chat analytics dashboard
- ✅ `/api/v1/user/chat/ws/{conversation_id}` - Chat WebSocket

### Atlas Endpoints (USER)
- ✅ `/api/v1/user/atlas/countries/search` - Search countries
- ✅ `/api/v1/user/atlas/cities/search` - Search cities

### WebSocket Endpoints (USER)
- ✅ `/api/v1/user/ws/stats` - Get WebSocket statistics

## Admin Endpoints (Unchanged)

Admin endpoints remain under `/api/v1/admin/`:
- `/api/v1/admin/*` - All admin operations

## Public/Guest Endpoints (Unchanged)

Public endpoints remain at `/api/v1/`:
- `/api/v1/account/signup` - User registration
- `/api/v1/account/login` - User login
- `/api/v1/account/password-reset/*` - Password reset
- `/api/v1/general/health` - Health check

## Summary

- **Total Routes:** 226
- **User Routes:** 135+ (all authenticated endpoints)
- **Admin Routes:** 45 (under `/api/v1/admin/`)
- **Public Routes:** 46 (under `/api/v1/` - account, general, health)

## Migration Notes

All endpoints that previously required authentication (`bearer_scheme`) have been moved to `/api/v1/user/` prefix. This provides:

1. **Clear API organization** - Easy to identify user vs admin vs public endpoints
2. **Better security** - Clear separation of concerns
3. **Easier documentation** - Grouped by user type
4. **Future scalability** - Easy to add role-based prefixes (e.g., `/api/v1/premium/`)

## Testing

All endpoints have been tested and verified to work with the new paths. The application starts successfully with 226 total routes.

