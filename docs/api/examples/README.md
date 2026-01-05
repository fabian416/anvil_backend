# API Examples

**Purpose**: API examples and testing resources  
**Audience**: Developers, QA Engineers, API Consumers

---

## 📚 Documentation

See [Main Documentation Index](../README.md) for complete documentation.

---

## 🚀 Postman Collections

### Complete API Collection

**File**: [`anvil-backend-complete-postman-collection.json`](./anvil-backend-complete-postman-collection.json)

**Description**: Complete Postman collection for Anvil Backend API following CTO methodology.

**Features**:
- ✅ 200+ endpoints organized in 30+ modules
- ✅ Automatic authentication flow
- ✅ Pre-request scripts for dynamic data
- ✅ Test scripts for validation
- ✅ Environment variables support
- ✅ Multi-language support (en, es, pt, zh)
- ✅ Rate limiting awareness
- ✅ Error handling examples

**Organization**:
1. **Setup & Authentication** - Login, signup, token management
2. **Public Endpoints** - Guest chat, health check, shortcuts
3. **User Endpoints - Chat** - Conversations, messages, unified routing
4. **User Endpoints - Wallet** - Wallet management, sync, export
5. **User Endpoints - Portfolio** - Snapshots, positions, balances
6. **User Endpoints - DeFi Protocols** - Aave, Morpho, Hyperliquid
7. **User Endpoints - Hunter AI** - Sentiment, predictions, signals
8. **User Endpoints - ULTRA Arbitrage** - Arbitrage, flash loans, MEV
9. **User Endpoints - Other** - Alerts, projects, transactions
10. **Admin Endpoints** - User management, LLM, security, analytics
11. **Subscription & Payment** - Stripe integration

**Usage**:
1. Import collection into Postman
2. Set `base_url` variable (default: `http://localhost:8000/api/v1`)
3. Run "Login" request to auto-populate `auth_token`
4. All authenticated requests will use the token automatically

**Methodology Applied**:
- **Problem Decomposition**: Organized by functional domains
- **Solution Generation**: Modular structure with reusable variables
- **Risk Assessment**: Comprehensive test coverage and error handling

### Unified Chat Collection

**File**: [`unified-chat-postman-collection.json`](./unified-chat-postman-collection.json)

**Description**: Focused collection for testing unified chat routing and intent detection.

---

## 📝 Other Examples

- **cURL Scripts**: [`curl_test_scripts.sh`](./curl_test_scripts.sh)
- **Python SDK**: [`python_sdk_examples.py`](./python_sdk_examples.py)
- **TypeScript SDK**: [`typescript_sdk_examples.ts`](./typescript_sdk_examples.ts)
- **OpenAPI Examples**: [`openapi_examples.yaml`](./openapi_examples.yaml)
- **Quick Reference**: [`quick_reference.md`](./quick_reference.md)

---

**Last Updated**: January 2, 2026
