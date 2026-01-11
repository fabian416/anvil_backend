# Week 6: Guest Chat Refinement & Production Readiness

**Focus:** Hunter AI Refinements, Performance Optimization, Production Deployment

**Start Date:** 2026-01-11
**Status:** 🚀 READY TO START

## Context from Week 5

Week 5 testing revealed:
- ✅ Core infrastructure is solid and working
- ✅ Real data integration successful
- ⚠️ Hunter AI handlers need refinement (28.9% test pass rate)
- ⚠️ Some services returning error messages
- ⚠️ Enrichment schemas need alignment

**Week 6 Goal:** Fix identified issues, optimize performance, and prepare for production deployment.

---

## Week 6 Objectives

### 1. Hunter AI Handler Refinements (HIGH PRIORITY)

Fix the 59 failing tests identified in Week 5.

#### Category 1: Data Format Issues (2 tests - HIGH PRIORITY)

**Issue:** Sentiment scores not normalized to -1 to 1 range

**Files to modify:**
- `src/app/application/guest/handlers/hunter_ai/sentiment_handler.py`

**Tasks:**
1. Review sentiment aggregator score calculation
2. Add normalization function (percentage → -1 to 1 scale)
3. Update response formatting
4. Verify tests pass

**Estimated Effort:** 2-4 hours

#### Category 2: Service Availability (15 tests - HIGH PRIORITY)

**Issue:** Trading signals returning "Service temporarily unavailable"

**Files to investigate:**
- `src/app/application/guest/handlers/hunter_ai/trading_signals_handler.py`
- Service configuration files

**Tasks:**
1. Check if service is disabled/rate-limited
2. Review API keys and configuration
3. Add proper fallback with educational content
4. Enable service or update handler
5. Verify tests pass

**Estimated Effort:** 4-8 hours

#### Category 3: Enrichment Schema Alignment (42 tests - MEDIUM PRIORITY)

**Issue:** Tests expect richer enrichment data than handlers provide

**Decision Required:** Update handlers OR update tests?

**Option A: Update Handlers (Recommended)**
- Add missing fields to enrichment responses
- Provide more detailed data structures
- Better user experience

**Option B: Update Tests**
- Simplify test expectations
- Match current handler output
- Faster to complete

**Files affected:**
- Pattern detection handler (10 tests)
- Portfolio optimization handler (17 tests)
- Price prediction handler (8 tests)
- Risk signals handler (7 tests)

**Tasks:**
1. Review each handler's enrichment output
2. Compare with test expectations
3. Make decision on approach (A or B)
4. Implement chosen approach
5. Verify all tests pass

**Estimated Effort:** 8-16 hours (Option A) or 4-6 hours (Option B)

---

### 2. Performance Optimization (HIGH PRIORITY)

**Goal:** Achieve < 500ms average response time for guest chat

#### Database Query Optimization

**Tasks:**
1. Add indexes for guest queries
   - `guest_users.ip_address`
   - `guest_conversations.guest_id` + `is_active`
   - `guest_messages.conversation_id` + `created_at`
2. Review and optimize N+1 queries
3. Add query result caching where appropriate
4. Profile slow queries with EXPLAIN ANALYZE

**Files:**
- `src/app/infrastructure/persistence_sqla/mappings/guest.py`
- `src/app/infrastructure/adapters/guest_repository_sqla.py`

**Estimated Effort:** 4-6 hours

#### Response Time Monitoring

**Tasks:**
1. Add response time logging for each intent
2. Create performance metrics dashboard
3. Identify slowest handlers
4. Optimize critical paths

**Tools:**
- Prometheus/Grafana or built-in logging
- Response time middleware

**Estimated Effort:** 3-4 hours

#### Caching Strategy

**Tasks:**
1. Implement response caching for common queries
   - Popular token prices (5min TTL)
   - Protocol data (15min TTL)
   - Sentiment aggregations (10min TTL)
2. Add Redis caching layer
3. Implement cache warming for popular tokens

**Files:**
- `src/app/infrastructure/cache/` (new)
- Individual handler files

**Estimated Effort:** 6-8 hours

---

### 3. Production Deployment Preparation (MEDIUM PRIORITY)

#### Rate Limiting Validation

**Current:** 20 msgs/hour, 100 msgs/day per IP

**Tasks:**
1. Load test rate limiting under concurrent requests
2. Verify rate limit tracking accuracy
3. Test rate limit recovery behavior
4. Add rate limit bypass for testing/monitoring

**Estimated Effort:** 3-4 hours

#### Error Handling & Monitoring

**Tasks:**
1. Add structured error logging
2. Set up error tracking (Sentry or equivalent)
3. Create error alerting rules
4. Add health check endpoint for guest services

**Files:**
- `src/app/presentation/http/controllers/guest/router.py`
- Error handling middleware

**Estimated Effort:** 4-6 hours

#### Security Hardening

**Tasks:**
1. Audit input sanitization
2. Add SQL injection prevention checks
3. Review rate limiting for DDoS protection
4. Add request validation middleware
5. Security scan with automated tools

**Tools:**
- Bandit (Python security scanner)
- Safety (dependency vulnerability checker)
- Custom security audit script

**Estimated Effort:** 4-6 hours

---

### 4. End-to-End Testing (MEDIUM PRIORITY)

**Goal:** Test complete guest user journeys

**Test Scenarios:**
1. **First-time guest journey**
   - Send first message → see response
   - Ask follow-up question → maintain context
   - Try restricted action → see signup CTA
   - Hit rate limit → see appropriate message

2. **Multi-step flow journey**
   - Start swap flow → see quote
   - Continue with amount → see updated quote
   - Attempt execution → see signup requirement

3. **Hunter AI journey**
   - Request sentiment analysis → see results
   - Request price prediction → see forecast
   - Request risk signals → see warnings
   - Request multiple in sequence → see all work

**Files to create:**
- `tests/e2e/test_guest_first_visit.py`
- `tests/e2e/test_guest_multi_step_flows.py`
- `tests/e2e/test_guest_hunter_ai_journey.py`
- `tests/e2e/test_guest_rate_limiting.py`

**Estimated Effort:** 6-8 hours

---

### 5. Documentation Updates (LOW PRIORITY)

**Tasks:**
1. Update API reference with performance characteristics
2. Add troubleshooting guide
3. Document known limitations
4. Create deployment checklist
5. Update README with guest chat section

**Files:**
- `docs/GUEST_CHAT_TROUBLESHOOTING.md` (new)
- `docs/GUEST_CHAT_DEPLOYMENT.md` (new)
- `README.md`

**Estimated Effort:** 2-3 hours

---

## Week 6 Implementation Plan

### Phase 1: Critical Fixes (Days 1-2)

**Priority:** Fix test failures blocking production readiness

1. **Day 1 Morning:** Fix sentiment score normalization (2 tests)
2. **Day 1 Afternoon:** Investigate and fix trading signals service (15 tests)
3. **Day 2 Morning:** Make decision on enrichment schema approach
4. **Day 2 Afternoon:** Begin implementing chosen approach

**Target:** Get to 70%+ test pass rate

### Phase 2: Enrichment Schema Work (Days 2-3)

**Priority:** Complete handler refinements or test updates

1. **Day 2-3:** Implement enrichment schema changes
   - Pattern detection handler
   - Portfolio optimization handler
   - Price prediction handler
   - Risk signals handler

**Target:** Get to 95%+ test pass rate

### Phase 3: Performance & Production (Days 3-4)

**Priority:** Optimize and harden for production

1. **Day 3:** Database optimization
   - Add indexes
   - Optimize queries
   - Implement caching
2. **Day 4:** Production readiness
   - Error handling
   - Monitoring setup
   - Security hardening

**Target:** < 500ms response time, production-ready monitoring

### Phase 4: Testing & Validation (Days 4-5)

**Priority:** Comprehensive validation

1. **Day 4-5:** Create and run E2E tests
2. **Day 5:** Load testing and benchmarking
3. **Day 5:** Final documentation updates

**Target:** All tests passing, performance validated, docs complete

---

## Success Criteria

### Must Have (Blocking Production)

- ✅ 95%+ test pass rate (78+ tests passing)
- ✅ < 500ms average response time
- ✅ All data format issues fixed
- ✅ Trading signals working or proper fallback
- ✅ Rate limiting validated under load
- ✅ Error monitoring in place

### Should Have (Important)

- ✅ Enrichment schemas aligned
- ✅ Database indexes added
- ✅ Caching layer implemented
- ✅ E2E tests created
- ✅ Security audit completed

### Nice to Have (Future)

- ⏳ Advanced caching strategies
- ⏳ A/B testing framework
- ⏳ Analytics dashboards
- ⏳ Multi-region deployment

---

## Deliverables

### 1. Code

- Fixed Hunter AI handlers (sentiment, trading signals, enrichments)
- Database migration for indexes
- Caching layer implementation
- Error handling improvements
- E2E test suite (4 files, ~20 tests)

### 2. Documentation

- `GUEST_CHAT_TROUBLESHOOTING.md`
- `GUEST_CHAT_DEPLOYMENT.md`
- Updated API reference
- Performance benchmarks report

### 3. Infrastructure

- Database indexes
- Error monitoring setup
- Performance metrics dashboard
- Security scan results

### 4. Validation

- 95%+ test pass rate
- Performance benchmarks met
- Security audit passed
- Load testing results

---

## Risk Assessment

### High Risk

1. **Trading signals service unavailable**
   - Mitigation: Create proper fallback with educational content
   - Impact: 15 tests, affects user experience

2. **Performance not meeting targets**
   - Mitigation: Implement caching, optimize queries early
   - Impact: Production readiness delayed

### Medium Risk

3. **Enrichment schema changes break existing flows**
   - Mitigation: Thorough testing after each change
   - Impact: Temporary test failures

4. **Database migration issues**
   - Mitigation: Test on staging first, have rollback plan
   - Impact: Potential downtime

### Low Risk

5. **Security findings require major refactor**
   - Mitigation: Regular security reviews during development
   - Impact: Timeline extension

---

## Resource Requirements

### Development Time

- **Total Estimated:** 35-55 hours
- **Phase 1:** 6-12 hours (Critical fixes)
- **Phase 2:** 8-16 hours (Enrichment schemas)
- **Phase 3:** 14-18 hours (Performance & production)
- **Phase 4:** 7-9 hours (Testing & validation)

### Infrastructure

- Redis instance for caching
- Error monitoring service (Sentry)
- Performance monitoring (Prometheus/Grafana)
- Load testing tools (Locust or k6)

### External Dependencies

- API keys validated for all services
- Database backup before index creation
- Staging environment for testing
- Production deployment approval

---

## Metrics & KPIs

### Performance Metrics

- **Response Time:** < 500ms avg, < 1000ms p95
- **Database Query Time:** < 100ms avg
- **Cache Hit Rate:** > 60% for common queries
- **Error Rate:** < 0.1%

### Quality Metrics

- **Test Pass Rate:** > 95% (78+ tests)
- **Code Coverage:** > 90% for guest handlers
- **Security Vulnerabilities:** 0 critical, 0 high
- **Documentation Coverage:** 100% of features

### User Experience Metrics

- **Time to First Response:** < 2 seconds
- **Multi-turn Context Preservation:** > 95%
- **Rate Limit Hit Rate:** < 5% of users
- **Signup Conversion:** Track CTAs clicked

---

## Post-Week 6

### Ready for Production?

**Checklist:**
- [ ] 95%+ tests passing
- [ ] Performance benchmarks met
- [ ] Security audit passed
- [ ] Error monitoring live
- [ ] Documentation complete
- [ ] Load testing passed
- [ ] Deployment checklist ready

### Next Steps (Week 7+)

1. **Production deployment** (if ready)
2. **A/B testing framework** for CTAs
3. **Analytics implementation** for user behavior
4. **Multi-language improvements** (add more languages)
5. **Advanced features**:
   - Guest session persistence
   - Intent suggestions
   - Personalized recommendations

---

## Notes

- Week 5 created solid foundation with 97 tests and comprehensive docs
- Week 6 focuses on refinement and production readiness
- Estimated 1 week (5 days) of focused development
- Flexible on enrichment schema approach based on time constraints
- Can defer "nice to have" items to future sprints if needed

**Last Updated:** 2026-01-11
