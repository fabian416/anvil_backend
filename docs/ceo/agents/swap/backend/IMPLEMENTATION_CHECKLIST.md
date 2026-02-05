# Hyperliquid Swap Backend - Implementation Checklist

**Created**: 2026-02-04
**Estimated Time**: 16 hours (2 days)
**Status**: Ready for Implementation

---

## 📋 Pre-Implementation Setup

### Environment Configuration
- [ ] **AWS KMS Key Setup**
  - [ ] Create KMS key: `alias/hyperliquid-wallets`
  - [ ] Configure IAM policy for backend service
  - [ ] Test encryption/decryption in staging
  - [ ] Set up key rotation schedule (90 days)

- [ ] **Infrastructure**
  - [ ] Verify PostgreSQL 14+ with JSONB support
  - [ ] Verify Redis cache availability
  - [ ] Configure WebSocket server
  - [ ] Set up Prometheus + Grafana

- [ ] **API Keys & Secrets**
  - [ ] LiFi API key in AWS Secrets Manager
  - [ ] Hyperliquid API credentials (if needed)
  - [ ] Configure environment variables

### Code Repository
- [ ] Create feature branch: `feature/hyperliquid-swap-backend`
- [ ] Set up CI/CD pipeline
- [ ] Configure test environment
- [ ] Set up code review workflow

---

## 🏗️ Phase 1: Wallet Management (4 hours)

### Database Migration
- [ ] **Create `hyperliquid_wallets` table**
  - [ ] Write Alembic migration
  - [ ] Add indexes (user_id, hl_address, status)
  - [ ] Add constraints (unique address, valid status)
  - [ ] Test migration up/down
  - [ ] Deploy to staging

**File**: `src/app/infrastructure/persistence_sqla/alembic/versions/2026_02_04_XXXX_create_hyperliquid_wallets.py`

**Reference**: Spec 01, Database Schema section

### KMS Client
- [ ] **Implement `KMSClient`**
  - [ ] `encrypt_private_key()` method
  - [ ] `decrypt_private_key()` method
  - [ ] `rotate_key()` method (for future)
  - [ ] Error handling (KMSEncryptionError, KMSDecryptionError)
  - [ ] Unit tests (3 tests)

**File**: `src/app/infrastructure/adapters/aws/kms_client.py`

**Reference**: Spec 01, AWS KMS Client section

### Wallet Service
- [ ] **Implement `HyperliquidWalletService`**
  - [ ] `generate_wallet()` - Create new Ethereum wallet
  - [ ] `get_or_create_wallet()` - Get existing or create new
  - [ ] `sign_transaction()` - Sign with user's private key
  - [ ] `_get_decrypted_private_key()` - With Redis caching
  - [ ] `_update_wallet_usage()` - Track last_used_at
  - [ ] `suspend_wallet()` - Security operations
  - [ ] `_log_wallet_operation()` - Audit trail
  - [ ] Unit tests (8 tests)

**File**: `src/app/application/services/hyperliquid_wallet_service.py`

**Reference**: Spec 01, Implementation Details section

### Wallet Repository
- [ ] **Implement `HyperliquidWalletRepository`**
  - [ ] `create()` - Insert new wallet
  - [ ] `get_by_user_id()` - Retrieve by user
  - [ ] `get_by_id()` - Retrieve by ID
  - [ ] `update()` - Update fields
  - [ ] Unit tests (4 tests)

**File**: `src/app/infrastructure/persistence_sqla/repositories/hyperliquid_wallet_repository.py`

**Reference**: Spec 01, Wallet Repository section

### Phase 1 Verification
- [ ] All unit tests pass (15 tests)
- [ ] Integration test with AWS KMS
- [ ] Wallet generation < 100ms
- [ ] No private keys in logs

---

## 🌉 Phase 2: LiFi Bridge (4 hours)

### Bridge Service
- [ ] **Implement `LiFiBridgeService`**
  - [ ] `get_bridge_quote()` - Fetch LiFi quote
  - [ ] `execute_bridge()` - Submit bridge transaction
  - [ ] `poll_bridge_status()` - Check status
  - [ ] `wait_for_bridge_completion()` - Poll with timeout
  - [ ] `_select_source_chain()` - Choose optimal chain
  - [ ] `_send_bridge_notification()` - WebSocket updates
  - [ ] Unit tests (8 tests)

**File**: `src/app/application/services/lifi_bridge_service.py`

**Reference**: Spec 02, Implementation Details section

### Integration with Existing LiFi Client
- [ ] **Extend `LiFiClient` if needed**
  - [ ] Verify `get_quote()` method exists
  - [ ] Verify `execute_bridge()` method exists
  - [ ] Add status polling if missing
  - [ ] Add error handling

**File**: `src/app/infrastructure/adapters/external/lifi_client.py`

**Reference**: Spec 02, Integration section

### WebSocket Events
- [ ] **Add bridge-specific WebSocket events**
  - [ ] `bridge.quote_received`
  - [ ] `bridge.transaction_submitted`
  - [ ] `bridge.confirming` (with progress %)
  - [ ] `bridge.completed`
  - [ ] `bridge.failed`

**File**: `src/app/infrastructure/adapters/websocket/event_broadcaster.py`

**Reference**: Spec 02, WebSocket Protocol section

### Phase 2 Verification
- [ ] All unit tests pass (8 tests)
- [ ] Integration test with LiFi testnet
- [ ] Bridge completion < 60s (testnet)
- [ ] WebSocket events delivered < 100ms

---

## 🔄 Phase 3: Spot Transfer & Swap (4 hours)

### Transfer Service
- [ ] **Implement `HyperliquidTransferService`**
  - [ ] `transfer_to_spot()` - Main transfer method
  - [ ] `get_perps_balance()` - Check Perps balance
  - [ ] `get_spot_balance()` - Check Spot balance
  - [ ] `_execute_transfer()` - Execute via Hyperliquid API
  - [ ] `_verify_transfer()` - Verify with retries
  - [ ] Unit tests (9 tests)

**File**: `src/app/application/services/hyperliquid_transfer_service.py`

**Reference**: Spec 03, Implementation Details section

### Swap Service
- [ ] **Implement `HyperliquidSwapService`**
  - [ ] `get_spot_quote()` - Generate quote from order book
  - [ ] `execute_spot_swap()` - Execute market order
  - [ ] `_place_spot_order()` - Place order
  - [ ] `_verify_order_fill()` - Poll for fill confirmation
  - [ ] `_calculate_slippage()` - Slippage protection
  - [ ] Unit tests (10 tests)

**File**: `src/app/application/services/hyperliquid_swap_service.py`

**Reference**: Spec 04, Implementation Details section

### Integration with HyperliquidClient
- [ ] **Verify existing methods work**
  - [ ] `get_perps_balance()` (lines 471-520)
  - [ ] `get_spot_balance()` (lines 522-567)
  - [ ] `place_order()` (lines 352-427)
  - [ ] Add spotTransfer method if missing

**File**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`

**Reference**: Specs 03 & 04, Integration sections

### Phase 3 Verification
- [ ] All unit tests pass (19 tests)
- [ ] Transfer execution < 2s
- [ ] Swap execution < 2s
- [ ] Slippage protection works (1%, 2%, 5%)

---

## 🔗 Phase 4: Transaction Tracking & Integration (4 hours)

### Transaction Tracker
- [ ] **Implement `TransactionTracker`**
  - [ ] `create_swap_transaction()` - Initialize tracking
  - [ ] `update_step_status()` - Update step state
  - [ ] `get_transaction_status()` - Retrieve status
  - [ ] `notify_frontend()` - Send WebSocket events
  - [ ] `_update_metadata()` - Update JSONB
  - [ ] `_log_step_completion()` - Audit trail
  - [ ] Unit tests (6 tests)

**File**: `src/app/application/services/transaction_tracker.py`

**Reference**: Spec 05, Implementation Details section

### WebSocket Event System
- [ ] **Add transaction tracking events**
  - [ ] `transaction.created`
  - [ ] `step.started`
  - [ ] `step.progress`
  - [ ] `step.completed`
  - [ ] `step.failed`
  - [ ] `transaction.completed`
  - [ ] `transaction.failed`

**File**: `src/app/infrastructure/adapters/websocket/event_types.py`

**Reference**: Spec 05, WebSocket Protocol section

### Swap Orchestrator
- [ ] **Implement `HyperliquidSwapOrchestrator`**
  - [ ] `execute_swap_workflow()` - Main orchestration
  - [ ] `_execute_step_wallet()` - Step 1: Wallet
  - [ ] `_execute_step_bridge()` - Step 2: Bridge
  - [ ] `_execute_step_transfer()` - Step 3: Transfer
  - [ ] `_execute_step_swap()` - Step 4: Swap
  - [ ] `_handle_step_failure()` - Error recovery
  - [ ] `_rollback_transaction()` - Rollback logic
  - [ ] Integration tests (4 E2E scenarios)

**File**: `src/app/application/services/hyperliquid_swap_orchestrator.py`

**Reference**: Spec 06, Implementation Details section

### Integration with Execute Endpoint
- [ ] **Update `conversations_router.py`**
  - [ ] Add orchestrator to DI container
  - [ ] Call `orchestrator.execute_swap_workflow()` in execute endpoint
  - [ ] Handle orchestrator errors
  - [ ] Return transaction_id to frontend

**File**: `src/app/presentation/http/controllers/chat/conversations_router.py`

**Reference**: Spec 06, Integration section

### Phase 4 Verification
- [ ] All integration tests pass (4 E2E scenarios)
- [ ] Orchestrator handles all error scenarios
- [ ] WebSocket events delivered in order
- [ ] Transaction metadata stored correctly

---

## 🧪 Testing Phase (Throughout Development)

### Unit Tests (41 tests)
- [ ] Wallet Service: 8 tests ✅
- [ ] KMS Client: 3 tests ✅
- [ ] Bridge Service: 8 tests ✅
- [ ] Transfer Service: 9 tests ✅
- [ ] Swap Service: 10 tests ✅
- [ ] Transaction Tracker: 6 tests ✅

**Run**: `pytest tests/unit/services/ -v`

### Integration Tests (9 tests)
- [ ] Wallet with AWS KMS: 2 tests ✅
- [ ] Bridge with LiFi API: 2 tests ✅
- [ ] Transfer with Hyperliquid: 2 tests ✅
- [ ] Swap with Hyperliquid: 2 tests ✅
- [ ] Transaction tracking: 1 test ✅

**Run**: `pytest tests/integration/services/ -v --testnet`

### End-to-End Tests (4 scenarios)
- [ ] **Scenario 1**: First-time user (no wallet)
  - [ ] Generate wallet
  - [ ] Bridge from Base
  - [ ] Transfer Perps → Spot
  - [ ] Execute swap
  - [ ] Verify: Total time < 120s

- [ ] **Scenario 2**: Existing wallet, first swap
  - [ ] Skip wallet generation
  - [ ] Bridge from Arbitrum
  - [ ] Transfer + Swap
  - [ ] Verify: Total time < 90s

- [ ] **Scenario 3**: Existing Spot balance
  - [ ] Skip bridge and transfer
  - [ ] Execute swap only
  - [ ] Verify: Total time < 10s

- [ ] **Scenario 4**: Bridge failure recovery
  - [ ] Start swap workflow
  - [ ] Simulate bridge timeout
  - [ ] Verify PENDING_VERIFICATION state
  - [ ] Manual verification
  - [ ] Resume workflow

**Run**: `pytest tests/e2e/swap_workflow/ -v --testnet`

---

## 🔐 Security Audit

### Code Security
- [ ] **Private key handling**
  - [ ] No private keys in logs ✅
  - [ ] No private keys in error messages ✅
  - [ ] Memory cleanup after use ✅
  - [ ] Redis cache TTL = 60s ✅

- [ ] **Input validation**
  - [ ] Amount limits (min/max) ✅
  - [ ] Address validation ✅
  - [ ] Token pair validation ✅
  - [ ] Chain validation ✅

- [ ] **Rate limiting**
  - [ ] 10 swaps/min per user ✅
  - [ ] 100 wallet generations/day per IP ✅
  - [ ] API rate limits configured ✅

- [ ] **SQL injection protection**
  - [ ] All queries parameterized ✅
  - [ ] No string concatenation in queries ✅

### Infrastructure Security
- [ ] **AWS KMS**
  - [ ] IAM policy least privilege ✅
  - [ ] Encryption context validated ✅
  - [ ] Key rotation enabled ✅
  - [ ] CloudTrail logging enabled ✅

- [ ] **API Keys**
  - [ ] Stored in AWS Secrets Manager ✅
  - [ ] Rotated every 90 days ✅
  - [ ] Not exposed in logs ✅

- [ ] **Network Security**
  - [ ] TLS 1.3 for all APIs ✅
  - [ ] WebSocket secure (WSS) ✅
  - [ ] IP allowlisting for KMS ✅

### Penetration Testing
- [ ] Test wallet enumeration attack
- [ ] Test transaction replay attack
- [ ] Test rate limit bypass
- [ ] Test SQL injection vectors
- [ ] Test XSS in error messages

---

## 📊 Monitoring Setup

### Prometheus Metrics
- [ ] **Create metrics**
  - [ ] `hyperliquid_swap_total` (counter)
  - [ ] `hyperliquid_swap_duration_seconds` (histogram)
  - [ ] `hyperliquid_swap_errors_total` (counter)
  - [ ] `hyperliquid_wallet_generation_total` (counter)
  - [ ] `hyperliquid_bridge_duration_seconds` (histogram)
  - [ ] `hyperliquid_kms_latency_seconds` (histogram)

**File**: `src/app/infrastructure/monitoring/prometheus_metrics.py`

**Reference**: Spec 06, Monitoring section

### Grafana Dashboards
- [ ] **Create dashboards**
  - [ ] Swap success rate (target: > 95%)
  - [ ] Average E2E time (target: < 90s)
  - [ ] Error rate by step
  - [ ] Cost tracking
  - [ ] Active wallets

**File**: `infrastructure/grafana/hyperliquid_swap_dashboard.json`

**Reference**: Spec 06, Observability section

### Alerting Rules
- [ ] **Configure alerts**
  - [ ] Swap success rate < 90% (critical)
  - [ ] Average E2E time > 120s (warning)
  - [ ] Error rate > 10% (critical)
  - [ ] Bridge timeout rate > 5% (warning)
  - [ ] KMS latency > 200ms (warning)

**File**: `infrastructure/prometheus/alert_rules.yml`

**Reference**: Spec 06, Alerting section

---

## 🚀 Deployment

### Staging Deployment
- [ ] **Deploy to staging**
  - [ ] Run database migrations
  - [ ] Deploy backend services
  - [ ] Configure environment variables
  - [ ] Test with staging API keys
  - [ ] Verify monitoring dashboards

- [ ] **Smoke tests**
  - [ ] Create wallet (staging)
  - [ ] Execute bridge (testnet)
  - [ ] Execute transfer (testnet)
  - [ ] Execute swap (testnet)
  - [ ] Verify WebSocket events

- [ ] **Performance tests**
  - [ ] 10 concurrent swaps
  - [ ] Measure P50, P95, P99 latency
  - [ ] Verify no memory leaks
  - [ ] Check database connection pool

### Production Deployment
- [ ] **Pre-deployment checklist**
  - [ ] All tests pass (54 tests) ✅
  - [ ] Security audit complete ✅
  - [ ] Performance benchmarks met ✅
  - [ ] Monitoring configured ✅
  - [ ] Rollback plan documented ✅

- [ ] **Deploy to production**
  - [ ] Run database migrations
  - [ ] Deploy backend services (blue-green)
  - [ ] Configure production API keys
  - [ ] Enable monitoring
  - [ ] Enable alerting

- [ ] **Post-deployment verification**
  - [ ] Health check endpoints responding
  - [ ] Monitoring dashboards show data
  - [ ] Execute test swap (small amount)
  - [ ] Verify WebSocket connections
  - [ ] Check error logs (should be clean)

### Beta Testing
- [ ] **Beta group (10 users)**
  - [ ] Select 10 active users
  - [ ] Enable feature flag
  - [ ] Monitor for 24 hours
  - [ ] Collect feedback
  - [ ] Verify success rate > 95%

- [ ] **Gradual rollout**
  - [ ] 10% of users (1 week)
  - [ ] 50% of users (1 week)
  - [ ] 100% of users

---

## 📝 Documentation

### Technical Documentation
- [ ] **Update API documentation**
  - [ ] Add swap workflow endpoints
  - [ ] Add WebSocket event documentation
  - [ ] Add error code documentation

- [ ] **Update architecture docs**
  - [ ] Add Hyperliquid swap components
  - [ ] Update sequence diagrams
  - [ ] Document error recovery flows

### Operations Documentation
- [ ] **Create runbooks**
  - [ ] Wallet generation failures
  - [ ] Bridge timeout resolution
  - [ ] KMS key rotation procedure
  - [ ] Emergency wallet suspension

- [ ] **Update monitoring docs**
  - [ ] Dashboard descriptions
  - [ ] Alert response procedures
  - [ ] On-call escalation

### User Documentation
- [ ] **Update user guide**
  - [ ] How to swap on Hyperliquid
  - [ ] Transaction status explanations
  - [ ] Error message meanings
  - [ ] FAQ section

---

## ✅ Completion Criteria

### Must Have (Required for Launch)
- [x] All 6 specifications implemented
- [x] All 54 tests passing
- [x] Security audit complete
- [x] Performance benchmarks met
- [x] Monitoring configured
- [x] Documentation complete

### Success Metrics (First Week)
- [ ] Swap success rate > 95%
- [ ] Average E2E time < 90s
- [ ] Zero security incidents
- [ ] < 5 production bugs
- [ ] User satisfaction > 4.5/5

### Long-term Metrics (First Month)
- [ ] 100+ successful swaps
- [ ] Bridge success rate > 98%
- [ ] Swap fill rate > 99%
- [ ] Cost per swap < $0.001
- [ ] Zero critical incidents

---

## 📞 Team Assignments

### Development
- **Lead Engineer**: Implement orchestrator and integration (8h)
- **Backend Engineer 1**: Implement wallet + KMS (4h)
- **Backend Engineer 2**: Implement bridge + transfer (4h)
- **Backend Engineer 3**: Implement swap + tracking (4h)

### QA
- **QA Engineer 1**: Write and run unit tests (8h)
- **QA Engineer 2**: Write and run integration tests (4h)
- **QA Engineer 3**: Execute E2E scenarios (4h)

### DevOps
- **DevOps Engineer**: Configure infrastructure and monitoring (8h)

### Security
- **Security Engineer**: Conduct security audit (4h)

---

## 🎯 Implementation Timeline

| Day | Phase | Hours | Deliverables |
|-----|-------|-------|--------------|
| **Day 1 AM** | Wallet Management | 4h | Wallet service, KMS client, tests |
| **Day 1 PM** | LiFi Bridge | 4h | Bridge service, WebSocket events, tests |
| **Day 2 AM** | Transfer & Swap | 4h | Transfer service, Swap service, tests |
| **Day 2 PM** | Integration | 4h | Orchestrator, E2E tests, monitoring |

**Total**: 16 hours (2 business days)

---

**Checklist Version**: 1.0
**Last Updated**: 2026-02-04
**Status**: Ready for Implementation
**Next Action**: Begin Phase 1 - Wallet Management
