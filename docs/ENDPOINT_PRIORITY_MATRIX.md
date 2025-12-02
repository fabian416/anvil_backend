# Endpoint Priority Matrix

**Generated:** December 1, 2025  
**Total Endpoints:** 147  
**Status:** Phase 2 Complete  

---

## 🎯 Priority Classification

### 🔴 CRITICAL Priority (70 endpoints)
**Business Impact:** Revenue-critical, core user experience  
**Documentation Required:** Complete standard format with examples  
**Timeline:** Days 3-5

#### Account & Auth (15 endpoints)
- **`account/router.py`** (~10 endpoints): Signup, Login, Email verification, Password management, Profile
- **`auth/router.py`** (~5 endpoints): Token refresh, Role management, Logout

#### Payment & Subscriptions (8 endpoints)
- **`payment/router.py`** (2 endpoints): Payment processing, Payment status
- **`subscription/router.py`** (6 endpoints): List, Create, Cancel, Success callback, Init, Get

#### Core User Features (42 endpoints) ✅
- ✅ **`preferences/router.py`** (7) - **DONE**
- ✅ **`alerts/router.py`** (7) - **DONE**
- ✅ **`search/router.py`** (6) - **DONE**
- ✅ **`dashboard/router.py`** (2) - **DONE**
- ✅ **`markets/router.py`** (4) - **DONE**
- ✅ **`portfolio/router.py`** (2) - **DONE**
- ✅ **`comparison/router.py`** (1) - **DONE**
- ✅ **`chat/router.py`** (8) - **DONE**
- ✅ **`user/projects_router.py`** (5) - **DONE**

#### WebSocket Real-Time (5 endpoints)
- **`chat/websocket_router.py`** (5 endpoints): Chat streaming, Protocol updates, Risk alerts

---

### 🟠 HIGH Priority (40 endpoints)
**Business Impact:** Admin features, advanced capabilities  
**Documentation Required:** Standard format, basic examples  
**Timeline:** Days 5-6

#### Admin Features (25 endpoints)
- **`admin/projects_router.py`** (13): Project CRUD, Knowledge management, User assignments
- **`admin/distillation_router.py`** (10): Knowledge distillation, Document management
- **`admin/stats/router.py`** (1): System statistics
- **`admin/agent/router.py`** (1): Agent management

#### Notifications (2 endpoints)
- **`notification/router.py`** (2): Get notifications, Mark as read

#### DeFi Operations (10 endpoints)
- Supply, Swap, Borrow, Stake, Bridge operations

#### Metrics (3 endpoints)
- **`metrics/router.py`** (3): System metrics, Performance stats

---

### 🟡 MEDIUM Priority (30 endpoints)
**Business Impact:** Support features, nice-to-haves  
**Documentation Required:** Basic format, minimal examples  
**Timeline:** Days 6-7

#### General Endpoints (5 endpoints)
- **`general/router.py`** (5): General utilities, Health checks

#### Atlas/Location (5 endpoints)
- **`atlas/router.py`** (5): Country/city data, Location services

#### Additional Features (20 endpoints)
- User profile management
- Transaction history
- Settings variations
- Support endpoints

---

### 🟢 LOW Priority (7 endpoints)
**Business Impact:** Internal, dev-only, deprecated  
**Documentation Required:** Minimal, reference only  
**Timeline:** Day 7

#### Internal/Dev (7 endpoints)
- Root redirect (1)
- Health checks (2)
- Dev utilities (4)

---

## 📊 Documentation Effort Estimates

### By Priority Level

| Priority | Endpoints | Est. Hours | Timeline |
|----------|-----------|------------|----------|
| 🔴 CRITICAL | 70 | 20-24 hours | Days 3-5 |
| 🟠 HIGH | 40 | 12-16 hours | Days 5-6 |
| 🟡 MEDIUM | 30 | 8-12 hours | Days 6-7 |
| 🟢 LOW | 7 | 2-4 hours | Day 7 |
| **TOTAL** | **147** | **42-56 hours** | **5 days** |

### Completed vs Remaining

| Status | Endpoints | Percentage |
|--------|-----------|------------|
| ✅ Completed | 42 | 28.6% |
| ⏳ In Progress | 0 | 0% |
| 📋 Remaining | 105 | 71.4% |
| **TOTAL** | **147** | **100%** |

---

## 🎯 Execution Order

### Phase 4: Critical Documentation (Days 3-5)

**Day 3 Morning** (4 hours):
1. Account Management (10 endpoints)
   - Signup, Login, Logout
   - Email verification
   - Password management

**Day 3 Afternoon** (4 hours):
2. Payment & Subscription (8 endpoints)
   - Payment processing
   - Subscription lifecycle

**Day 4 Morning** (3 hours):
3. Authentication (5 endpoints)
   - Token management
   - Role management

**Day 4 Afternoon** (4 hours):
4. WebSocket Endpoints (5 endpoints)
   - Real-time chat
   - Protocol updates
   - Risk alerts push

**Day 5** (6 hours):
5. Enhancement Pass
   - Add example responses to all CRITICAL endpoints
   - Validate format compliance
   - Cross-reference documentation

---

### Phase 5: High Priority (Days 5-6)

**Day 5 Afternoon** (4 hours):
1. Admin Projects (13 endpoints)

**Day 6 Morning** (4 hours):
2. Admin Distillation (10 endpoints)

**Day 6 Afternoon** (4 hours):
3. DeFi Operations (10 endpoints)
4. Notifications (2 endpoints)
5. Metrics (3 endpoints)

---

### Phase 6: Complete Coverage (Day 6-7)

**Day 6 Evening** (3 hours):
1. General endpoints (5)
2. Atlas endpoints (5)

**Day 7** (8 hours):
1. Remaining MEDIUM priority (20)
2. LOW priority (7)
3. Final polish

---

## 🚨 Critical Path Dependencies

### Must Complete First (Blockers)
1. ✅ API Documentation Standard - **DONE**
2. ✅ Backend endpoint inventory - **DONE**
3. ✅ Coverage report - **DONE**
4. ⏳ Priority matrix - **IN PROGRESS**

### Can Be Parallelized
- Account docs + Payment docs (different developers)
- Admin Projects + DeFi Operations (different developers)
- Enhancement pass while new docs being written

---

## 📋 Quality Gates

### Per Endpoint Checklist
- [ ] Complete path (`/api/v1/...`)
- [ ] HTTP method documented
- [ ] Path parameters with types
- [ ] Query parameters with types
- [ ] Request body interface
- [ ] Response interface
- [ ] TypeScript implementation
- [ ] Example request (if POST/PUT/PATCH)
- [ ] Example success response (200/201)
- [ ] Example error response (400/401/404)
- [ ] Authentication requirements
- [ ] Rate limits (if applicable)
- [ ] Cross-references to related endpoints

### Per Module Checklist
- [ ] All endpoints documented
- [ ] User stories present
- [ ] Wireframes included
- [ ] React components specified
- [ ] React hooks provided
- [ ] User flows documented
- [ ] Error handling patterns
- [ ] Testing examples
- [ ] Accessibility guidelines

---

## 💰 ROI by Priority

### CRITICAL Endpoints (20-24 hours investment)
**Return:**
- Core user features functional
- Payment system integrated
- User onboarding smooth
- **Estimated Value:** $50K-$80K in prevented delays

### HIGH Priority Endpoints (12-16 hours investment)
**Return:**
- Admin tools fully functional
- Advanced features accessible
- Platform management enabled
- **Estimated Value:** $30K-$50K in productivity

### MEDIUM/LOW Priority (10-16 hours investment)
**Return:**
- Complete feature parity
- Zero documentation gaps
- Future-proof documentation
- **Estimated Value:** $20K-$30K in reduced tech debt

**Total ROI:** $100K-$160K in value from 42-56 hours investment

---

## 🔄 Risk Mitigation

### Risk: Documentation Drift
**Mitigation:** Weekly automated validation  
**Owner:** Engineering team

### Risk: Incomplete Example Data
**Mitigation:** QA review of all examples  
**Owner:** QA team

### Risk: Backend Changes Not Reflected
**Mitigation:** Pre-commit hooks, CI/CD validation  
**Owner:** DevOps

---

**Matrix Status**: ✅ **COMPLETE**  
**Next**: Phase 4 - Critical Endpoint Documentation  
**Owner**: CTO Office + Engineering Team  

---

*This matrix ensures systematic, priority-driven documentation coverage.*
