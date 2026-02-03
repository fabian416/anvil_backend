# Money Market Implementation Roadmap

**Version**: 1.0
**Date**: 2026-01-28
**Author**: Claude Code (CTO Methodology)
**Status**: Ready for Implementation

---

## Executive Summary

This roadmap provides a detailed, task-by-task plan to close the gaps identified in the Money Market workflow implementation. The plan is divided into 3 weeks with clear milestones, success criteria, and risk mitigation strategies.

**Total Effort**: 96 hours (12 days)
**Priority**: High (performance optimization + analytics)
**Risk Level**: Medium (database work is straightforward)

---

## Week 1: Critical Database Infrastructure (P0 Items)

**Goal**: Implement caching layer to reduce RPC calls by 90% and improve performance 5-8x

**Effort**: 40 hours
**Team Size**: 1 backend engineer + 1 reviewer

---

### Task 1.1: Create Money Market Database Tables

**Priority**: P0 - CRITICAL
**Effort**: 8 hours
**Owner**: Backend Engineer
**Dependencies**: None

#### Subtasks

1. **Create Migration File** (2 hours)
   - File: `src/app/infrastructure/persistence_sqla/alembic/versions/2026_01_28_0100-money_market_core_001_create_tables.py`
   - Use lending migration as template
   - Add revision ID and down_revision

2. **Define PostgreSQL ENUMs** (1 hour)
   ```python
   # Idempotent enum creation
   op.execute("""
       DO $$ BEGIN
           IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mm_protocol_enum') THEN
               CREATE TYPE mm_protocol_enum AS ENUM ('aave_v3', 'compound_v3');
           END IF;
       END $$;
   """)

   op.execute("""
       DO $$ BEGIN
           IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mm_data_source_enum') THEN
               CREATE TYPE mm_data_source_enum AS ENUM ('rpc', 'subgraph', 'api', 'estimated');
           END IF;
       END $$;
   """)
   ```

3. **Create Table: money_market_protocols** (1 hour)
   - UUID primary key
   - Fields: name, protocol_type, supported_chains (JSONB), supported_assets (JSONB)
   - Add indexes on is_active, supported_chains (GIN)
   - Add seed data for Aave V3 and Compound V3

4. **Create Table: money_market_rates** (2 hours)
   - UUID primary key
   - Foreign key to money_market_protocols
   - Fields: asset, chain, supply_apy, borrow_apy_variable, valid_until (60s TTL)
   - Add indexes:
     - `idx_mm_rates_asset_chain` (asset, chain, protocol_id) WHERE valid_until > NOW()
     - `idx_mm_rates_valid_until` (valid_until) WHERE valid_until > NOW()
     - `idx_mm_rates_comparison` (asset, chain, supply_apy DESC) covering index

5. **Create Table: money_market_comparisons** (1 hour)
   - UUID primary key
   - Foreign key to users (nullable for guests)
   - Fields: asset, chain, protocols_compared (JSONB), best_supply_protocol, latency_ms
   - Add indexes on user_id, asset/chain, created_at

6. **Create Table: money_market_user_preferences** (30 min)
   - UUID primary key
   - Foreign key to users (unique)
   - Fields: enable_rate_alerts, alert_threshold_apy_change, watched_assets (JSONB)

7. **Create Table: money_market_rate_alerts** (30 min)
   - UUID primary key
   - Foreign key to users
   - Fields: alert_type, protocol, asset, previous_apy, new_apy, notification_sent

8. **Test Migration** (1 hour)
   - Run on dev database: `alembic upgrade head`
   - Verify tables created: `\dt money_market*`
   - Check indexes: `\di money_market*`
   - Verify foreign keys: `\d money_market_rates`

#### Success Criteria
- [ ] Migration runs without errors
- [ ] All 5 tables created with correct schemas
- [ ] All indexes created and functional
- [ ] Seed data inserted (2 protocols)
- [ ] Foreign key constraints working

#### Testing Checklist
```sql
-- Verify tables
\dt money_market*

-- Check row counts
SELECT COUNT(*) FROM money_market_protocols;  -- Should be 2 (Aave + Compound)

-- Test foreign key
INSERT INTO money_market_rates (protocol_id, asset, chain, supply_apy, valid_until)
VALUES ('invalid-uuid', 'USDC', 'base', 4.5, NOW() + INTERVAL '60 seconds');
-- Should fail with foreign key violation

-- Test valid_until index
EXPLAIN ANALYZE
SELECT * FROM money_market_rates
WHERE asset = 'USDC' AND chain = 'base' AND valid_until > NOW();
-- Should use idx_mm_rates_asset_chain
```

---

### Task 1.2: Create Optimized Views and Indexes

**Priority**: P0 - CRITICAL
**Effort**: 4 hours
**Owner**: Backend Engineer
**Dependencies**: Task 1.1

#### Subtasks

1. **Create Migration File** (30 min)
   - File: `src/app/infrastructure/persistence_sqla/alembic/versions/2026_01_28_0200-money_market_core_002_views_indexes.py`

2. **Create View: v_latest_money_market_rates** (1 hour)
   ```sql
   CREATE VIEW v_latest_money_market_rates AS
   SELECT DISTINCT ON (protocol_id, asset, chain)
       r.id,
       p.name as protocol_name,
       r.asset,
       r.chain,
       r.supply_apy,
       r.borrow_apy_variable,
       r.total_supplied_usd,
       r.utilization_rate,
       r.data_source,
       r.created_at,
       r.valid_until
   FROM money_market_rates r
   JOIN money_market_protocols p ON r.protocol_id = p.id
   WHERE r.valid_until > NOW()
     AND r.is_active = TRUE
   ORDER BY protocol_id, asset, chain, created_at DESC;
   ```

3. **Create View: v_best_supply_rates** (30 min)
   ```sql
   CREATE VIEW v_best_supply_rates AS
   SELECT DISTINCT ON (asset, chain)
       r.asset,
       r.chain,
       p.name as protocol_name,
       r.supply_apy as best_supply_apy,
       r.data_source,
       r.created_at
   FROM money_market_rates r
   JOIN money_market_protocols p ON r.protocol_id = p.id
   WHERE r.valid_until > NOW()
     AND r.is_active = TRUE
   ORDER BY asset, chain, supply_apy DESC;
   ```

4. **Create View: v_protocol_comparison_summary** (1 hour)
   ```sql
   CREATE VIEW v_protocol_comparison_summary AS
   SELECT
       r.asset,
       r.chain,
       jsonb_object_agg(
           p.name,
           jsonb_build_object(
               'supply_apy', r.supply_apy,
               'borrow_apy_variable', r.borrow_apy_variable,
               'utilization', r.utilization_rate,
               'data_source', r.data_source
           )
       ) as protocols
   FROM money_market_rates r
   JOIN money_market_protocols p ON r.protocol_id = p.id
   WHERE r.valid_until > NOW()
     AND r.is_active = TRUE
   GROUP BY r.asset, r.chain;
   ```

5. **Add Performance Indexes** (1 hour)
   ```python
   # Covering index for hot comparison path
   op.create_index(
       "idx_mm_rates_hot_path",
       "money_market_rates",
       ["asset", "chain", sa.text("supply_apy DESC")],
       postgresql_include=["protocol_id", "borrow_apy_variable", "data_source", "created_at"],
       postgresql_where=sa.text("valid_until > NOW() AND is_active = TRUE"),
   )

   # Composite index for user analytics
   op.create_index(
       "idx_mm_comparisons_analytics",
       "money_market_comparisons",
       ["asset", "chain", sa.text("created_at DESC")],
   )
   ```

#### Success Criteria
- [ ] All 3 views created and queryable
- [ ] Views return correct data
- [ ] Covering indexes improve query performance
- [ ] EXPLAIN ANALYZE shows index usage

---

### Task 1.3: Implement Caching Layer (Domain + Infrastructure)

**Priority**: P0 - CRITICAL
**Effort**: 12 hours
**Owner**: Backend Engineer
**Dependencies**: Task 1.1, Task 1.2

#### Subtasks

1. **Create Domain Port** (1 hour)
   - File: `src/app/domain/ports/money_market_cache_gateway.py`
   ```python
   from abc import ABC, abstractmethod
   from typing import Optional
   from dataclasses import dataclass
   from datetime import datetime

   @dataclass
   class CachedRate:
       protocol_name: str
       asset: str
       chain: str
       supply_apy: float
       borrow_apy_variable: float
       total_supplied_usd: float
       utilization_rate: float
       data_source: str
       valid_until: datetime

   class MoneyMarketCacheGateway(ABC):
       @abstractmethod
       async def get_cached_rates(
           self,
           asset: str,
           chain: str,
       ) -> list[CachedRate]:
           """Get cached rates for asset/chain if still valid."""
           pass

       @abstractmethod
       async def cache_rate(
           self,
           protocol_name: str,
           asset: str,
           chain: str,
           supply_apy: float,
           borrow_apy_variable: float,
           total_supplied_usd: float,
           utilization_rate: float,
           data_source: str,
           ttl_seconds: int = 60,
       ) -> None:
           """Cache rate data with TTL."""
           pass

       @abstractmethod
       async def invalidate_cache(
           self,
           asset: str,
           chain: str,
       ) -> None:
           """Invalidate cached rates for asset/chain."""
           pass
   ```

2. **Create SQLAlchemy Adapter** (4 hours)
   - File: `src/app/infrastructure/adapters/money_market_cache_sqla_adapter.py`
   ```python
   import logging
   from datetime import datetime, timedelta, UTC
   from typing import Optional
   from uuid import uuid4

   from sqlalchemy import select, and_, delete
   from sqlalchemy.ext.asyncio import AsyncSession

   from app.domain.ports.money_market_cache_gateway import (
       MoneyMarketCacheGateway,
       CachedRate,
   )
   from app.infrastructure.persistence_sqla.tables import (
       money_market_rates,
       money_market_protocols,
   )

   logger = logging.getLogger(__name__)

   class MoneyMarketCacheSqlaAdapter(MoneyMarketCacheGateway):
       def __init__(self, session: AsyncSession):
           self._session = session

       async def get_cached_rates(
           self,
           asset: str,
           chain: str,
       ) -> list[CachedRate]:
           """Get cached rates that are still valid."""
           now = datetime.now(UTC)

           query = (
               select(
                   money_market_protocols.c.name.label("protocol_name"),
                   money_market_rates.c.asset,
                   money_market_rates.c.chain,
                   money_market_rates.c.supply_apy,
                   money_market_rates.c.borrow_apy_variable,
                   money_market_rates.c.total_supplied_usd,
                   money_market_rates.c.utilization_rate,
                   money_market_rates.c.data_source,
                   money_market_rates.c.valid_until,
               )
               .select_from(
                   money_market_rates.join(
                       money_market_protocols,
                       money_market_rates.c.protocol_id == money_market_protocols.c.id,
                   )
               )
               .where(
                   and_(
                       money_market_rates.c.asset == asset.upper(),
                       money_market_rates.c.chain == chain.lower(),
                       money_market_rates.c.valid_until > now,
                       money_market_rates.c.is_active == True,
                   )
               )
               .order_by(money_market_rates.c.created_at.desc())
           )

           result = await self._session.execute(query)
           rows = result.fetchall()

           return [
               CachedRate(
                   protocol_name=row.protocol_name,
                   asset=row.asset,
                   chain=row.chain,
                   supply_apy=float(row.supply_apy),
                   borrow_apy_variable=float(row.borrow_apy_variable or 0),
                   total_supplied_usd=float(row.total_supplied_usd or 0),
                   utilization_rate=float(row.utilization_rate or 0),
                   data_source=row.data_source,
                   valid_until=row.valid_until,
               )
               for row in rows
           ]

       async def cache_rate(
           self,
           protocol_name: str,
           asset: str,
           chain: str,
           supply_apy: float,
           borrow_apy_variable: float,
           total_supplied_usd: float,
           utilization_rate: float,
           data_source: str,
           ttl_seconds: int = 60,
       ) -> None:
           """Cache rate data with TTL."""
           # Get protocol_id
           protocol_query = select(money_market_protocols.c.id).where(
               money_market_protocols.c.name == protocol_name
           )
           protocol_result = await self._session.execute(protocol_query)
           protocol_id = protocol_result.scalar_one_or_none()

           if not protocol_id:
               logger.error(f"Protocol not found: {protocol_name}")
               return

           now = datetime.now(UTC)
           valid_until = now + timedelta(seconds=ttl_seconds)

           insert_stmt = money_market_rates.insert().values(
               id=uuid4(),
               protocol_id=protocol_id,
               asset=asset.upper(),
               chain=chain.lower(),
               supply_apy=supply_apy,
               borrow_apy_variable=borrow_apy_variable,
               total_supplied_usd=total_supplied_usd,
               utilization_rate=utilization_rate,
               data_source=data_source,
               valid_until=valid_until,
               is_active=True,
           )

           await self._session.execute(insert_stmt)
           await self._session.commit()

           logger.info(
               f"Cached {protocol_name} rate for {asset} on {chain}: "
               f"{supply_apy:.2f}% APY (valid until {valid_until})"
           )

       async def invalidate_cache(
           self,
           asset: str,
           chain: str,
       ) -> None:
           """Invalidate cached rates by setting valid_until to past."""
           now = datetime.now(UTC)

           update_stmt = (
               money_market_rates.update()
               .where(
                   and_(
                       money_market_rates.c.asset == asset.upper(),
                       money_market_rates.c.chain == chain.lower(),
                       money_market_rates.c.valid_until > now,
                   )
               )
               .values(valid_until=now)
           )

           await self._session.execute(update_stmt)
           await self._session.commit()

           logger.info(f"Invalidated cache for {asset} on {chain}")
   ```

3. **Create SQLAlchemy Table Definitions** (2 hours)
   - File: `src/app/infrastructure/persistence_sqla/tables.py` (add to existing)
   ```python
   from sqlalchemy import (
       Table, Column, String, Integer, Numeric, Boolean,
       TIMESTAMP, ForeignKey, Enum, text,
   )
   from sqlalchemy.dialects.postgresql import UUID, JSONB
   from sqlalchemy import MetaData

   metadata = MetaData()

   money_market_protocols = Table(
       "money_market_protocols",
       metadata,
       Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
       Column("name", String(50), nullable=False, unique=True),
       Column("protocol_type", String(20), nullable=False),
       Column("supported_chains", JSONB, nullable=False),
       Column("supported_assets", JSONB, nullable=False),
       Column("is_active", Boolean, default=True),
       Column("created_at", TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")),
   )

   money_market_rates = Table(
       "money_market_rates",
       metadata,
       Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
       Column("protocol_id", UUID(as_uuid=True), ForeignKey("money_market_protocols.id"), nullable=False),
       Column("asset", String(20), nullable=False),
       Column("chain", String(20), nullable=False),
       Column("supply_apy", Numeric(10, 4), nullable=False),
       Column("borrow_apy_variable", Numeric(10, 4)),
       Column("total_supplied_usd", Numeric(20, 2)),
       Column("utilization_rate", Numeric(5, 4)),
       Column("data_source", String(20), nullable=False),
       Column("valid_until", TIMESTAMP(timezone=True), nullable=False),
       Column("is_active", Boolean, default=True),
       Column("created_at", TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")),
   )

   # ... other tables
   ```

4. **Update MoneyMarketHandler to Use Cache** (3 hours)
   - File: `src/app/application/chat/handlers/money_market_handler.py`
   - Add cache_gateway parameter to __init__
   - Check cache before making RPC calls
   - Store rates in cache after RPC calls
   ```python
   async def compare_rates(
       self,
       asset: str = "USDC",
       chain: str = "base",
       language: str = "en",
   ) -> MoneyMarketHandlerResult:
       start_time = time.time()

       # Check cache first
       if self._cache:
           try:
               cached_rates = await self._cache.get_cached_rates(asset, chain)
               if cached_rates:
                   logger.info(f"Cache HIT for {asset} on {chain}")
                   rates = [self._cached_rate_to_dict(cr) for cr in cached_rates]
                   # ... format and return
           except Exception as e:
               logger.warning(f"Cache check failed: {e}")

       # Cache miss - fetch from gateways
       rates = []

       # Get Aave rates
       if self._aave:
           aave_market = await self._aave.get_market_details(asset, chain)
           if aave_market:
               # Add to rates list
               # Cache the result
               if self._cache:
                   await self._cache.cache_rate(
                       protocol_name="Aave V3",
                       asset=asset,
                       chain=chain,
                       supply_apy=float(aave_market.supply_apy) * 100,
                       borrow_apy_variable=float(aave_market.borrow_apy_variable) * 100,
                       total_supplied_usd=float(aave_market.total_supplied_usd),
                       utilization_rate=float(aave_market.utilization_rate),
                       data_source="rpc",
                       ttl_seconds=60,
                   )

       # ... similar for Compound
   ```

5. **Add Dishka DI Configuration** (1 hour)
   - File: `src/app/setup/ioc/chat_phase2.py` (update existing)
   ```python
   from app.domain.ports.money_market_cache_gateway import MoneyMarketCacheGateway
   from app.infrastructure.adapters.money_market_cache_sqla_adapter import MoneyMarketCacheSqlaAdapter

   class ChatPhase2Provider(Provider):
       scope = Scope.REQUEST

       # ... existing providers

       @provide
       async def provide_money_market_cache_gateway(
           self,
           session: AsyncSession,
       ) -> MoneyMarketCacheGateway:
           return MoneyMarketCacheSqlaAdapter(session)

       @provide
       async def provide_money_market_handler(
           self,
           aave_gateway: AaveGateway | None,
           compound_gateway: CompoundGateway | None,
           cache_gateway: MoneyMarketCacheGateway,
       ) -> MoneyMarketHandler:
           return MoneyMarketHandler(
               aave_gateway=aave_gateway,
               compound_gateway=compound_gateway,
               cache_gateway=cache_gateway,
           )
   ```

6. **Write Unit Tests** (1 hour)
   - File: `tests/unit/infrastructure/adapters/test_money_market_cache_sqla_adapter.py`
   - Test cache hit with valid data
   - Test cache miss when TTL expired
   - Test cache invalidation
   - Test concurrent cache writes

#### Success Criteria
- [ ] Domain port defined with clear interface
- [ ] SQLAlchemy adapter implements all methods
- [ ] MoneyMarketHandler uses cache before RPC calls
- [ ] Cache hit rate > 90% in tests
- [ ] Unit tests pass with 100% coverage
- [ ] Performance improvement: 5-8x faster with cache

---

### Task 1.4: Add Comparison Logging

**Priority**: P1 - HIGH
**Effort**: 4 hours
**Owner**: Backend Engineer
**Dependencies**: Task 1.1

#### Subtasks

1. **Update MoneyMarketHandler** (2 hours)
   - Add logging after successful comparison
   ```python
   async def compare_rates(...) -> MoneyMarketHandlerResult:
       # ... existing logic

       # Log comparison
       if self._logger:
           try:
               await self._logger.log_comparison(
                   user_id=user_id,
                   guest_session_id=guest_session_id,
                   asset=asset,
                   chain=chain,
                   protocols_compared=rates,
                   best_supply_protocol=best_supply["protocol"],
                   best_supply_apy=best_supply["supply_apy"],
                   latency_ms=latency_ms,
                   language=language,
               )
           except Exception as e:
               logger.warning(f"Failed to log comparison: {e}")
   ```

2. **Create Comparison Logger** (1 hour)
   - File: `src/app/infrastructure/adapters/money_market_comparison_logger_sqla.py`
   ```python
   class MoneyMarketComparisonLoggerSqla:
       def __init__(self, session: AsyncSession):
           self._session = session

       async def log_comparison(
           self,
           user_id: UUID | None,
           guest_session_id: str | None,
           asset: str,
           chain: str,
           protocols_compared: list[dict],
           best_supply_protocol: str,
           best_supply_apy: float,
           latency_ms: int,
           language: str,
       ) -> None:
           insert_stmt = money_market_comparisons.insert().values(
               id=uuid4(),
               user_id=user_id,
               guest_session_id=guest_session_id,
               asset=asset,
               chain=chain,
               protocols_compared=protocols_compared,
               best_supply_protocol=best_supply_protocol,
               best_supply_apy=best_supply_apy,
               latency_ms=latency_ms,
               language=language,
           )
           await self._session.execute(insert_stmt)
           await self._session.commit()
   ```

3. **Add Analytics Queries** (1 hour)
   - File: `src/app/application/chat/queries/money_market_analytics.py`
   ```sql
   -- Most compared assets
   SELECT asset, COUNT(*) as comparison_count
   FROM money_market_comparisons
   WHERE created_at > NOW() - INTERVAL '7 days'
   GROUP BY asset
   ORDER BY comparison_count DESC;

   -- Average latency per chain
   SELECT chain, AVG(latency_ms) as avg_latency_ms
   FROM money_market_comparisons
   WHERE created_at > NOW() - INTERVAL '7 days'
   GROUP BY chain;

   -- Most selected protocols
   SELECT best_supply_protocol, COUNT(*) as selection_count
   FROM money_market_comparisons
   WHERE created_at > NOW() - INTERVAL '7 days'
   GROUP BY best_supply_protocol
   ORDER BY selection_count DESC;
   ```

#### Success Criteria
- [ ] All comparisons logged to database
- [ ] Analytics queries return useful insights
- [ ] Logging doesn't impact latency (async)
- [ ] Guest comparisons tracked separately

---

### Week 1 Milestone

**Deliverables**:
- ✅ 5 database tables created
- ✅ 3 optimized views created
- ✅ 20+ indexes created
- ✅ Caching layer implemented with 60s TTL
- ✅ Comparison logging functional
- ✅ Unit tests passing (> 90% coverage)

**Performance Improvement**:
- Before: 500-800ms per comparison (3 RPC calls)
- After: 50-100ms per comparison (90% cache hit rate)
- **8x faster** ⚡

**Success Metrics**:
- Cache hit rate: > 90%
- Database query time: < 100ms
- RPC call reduction: > 90%
- Migration runs without errors

---

## Week 2: Integration and Testing (P1 Items)

**Goal**: Ensure money market workflow integrates with frontend execute pattern

**Effort**: 24 hours
**Team Size**: 1 backend engineer + 1 frontend engineer

---

### Task 2.1: Execute Pattern Integration Testing

**Priority**: P1 - HIGH
**Effort**: 8 hours
**Owner**: Backend Engineer + Frontend Engineer
**Dependencies**: None (can start immediately)

#### Subtasks

1. **Create Integration Test** (4 hours)
   - File: `tests/integration/user/workflows/test_money_market_execute_flow.py`
   ```python
   import pytest
   from uuid import uuid4

   @pytest.mark.asyncio
   async def test_money_market_compare_returns_execute_data(
       authenticated_client,
       money_market_handler,
   ):
       """Test that money market comparison returns valid execute_data."""

       # Send message: "compare USDC rates"
       response = await authenticated_client.post(
           f"/api/v1/conversations/{conversation_id}/messages",
           json={
               "content": "compare USDC rates on base",
               "language": "en",
           },
       )

       assert response.status_code == 200
       data = response.json()

       # Check execute_data present
       assert data["execute"] is not None
       execute_data = data["execute"]

       # Validate schema
       assert execute_data["action_type"] == "deposit"
       assert execute_data["protocol"] in ["aave", "compound", "morpho"]
       assert execute_data["asset_symbol"] == "USDC"
       assert execute_data["chain"] == "base"
       assert execute_data["supply_apy"] > 0
       assert execute_data["amount"] is not None  # User specified or None

   @pytest.mark.asyncio
   async def test_money_market_workflow_full_flow(
       authenticated_client,
       money_market_workflow_agent,
   ):
       """Test full money market workflow with protocol selection."""

       # Step 1: Compare rates
       response1 = await send_message("compare USDC rates")
       assert "Aave" in response1["agent_message"]["content"]
       assert "Compound" in response1["agent_message"]["content"]

       # Step 2: Select protocol
       response2 = await send_message("aave")
       assert "Aave V3 Selected" in response2["agent_message"]["content"]

       # Step 3: Enter amount
       response3 = await send_message("deposit 1000")
       assert response3["execute"] is not None
       assert response3["execute"]["amount"] == "1000"
       assert response3["execute"]["protocol"] == "aave"
   ```

2. **Create Frontend Mock Test** (2 hours)
   - File: `tests/e2e/test_money_market_frontend_integration.py`
   - Test that frontend can parse execute_data
   - Test that Privy wallet API receives correct transaction params

3. **Performance Benchmarking** (2 hours)
   - File: `tests/performance/test_money_market_performance.py`
   - Test with cache hit: should be < 200ms
   - Test with cache miss: should be < 1s
   - Test concurrent comparisons: 100 req/s

#### Success Criteria
- [ ] Integration tests pass
- [ ] Frontend can parse execute_data correctly
- [ ] Performance benchmarks meet targets
- [ ] Execute flow matches lending pattern exactly

---

### Task 2.2: Benchmark Cache Performance

**Priority**: P1 - HIGH
**Effort**: 4 hours
**Owner**: Backend Engineer
**Dependencies**: Task 1.3

#### Subtasks

1. **Measure Cache Hit Rate** (2 hours)
   - Run 1000 comparison requests
   - Measure cache hit/miss ratio
   - Target: > 90% hit rate

2. **Benchmark Latency** (2 hours)
   - Compare latency with vs without cache
   - Measure p50, p95, p99 percentiles
   - Verify 5-8x improvement

#### Success Criteria
- [ ] Cache hit rate > 90%
- [ ] p50 latency < 200ms (with cache)
- [ ] p99 latency < 1s (with cache miss)
- [ ] 5-8x performance improvement confirmed

---

### Week 2 Milestone

**Deliverables**:
- ✅ Execute pattern integration tests passing
- ✅ Frontend integration verified
- ✅ Performance benchmarks meet targets
- ✅ Cache hit rate > 90%

**Success Metrics**:
- Integration test coverage: > 90%
- Frontend compatibility: 100%
- Performance improvement: 5-8x confirmed
- Zero breaking changes

---

## Week 3: User Features (P2 Items)

**Goal**: Enable user personalization and rate alerts

**Effort**: 32 hours
**Team Size**: 1 backend engineer + 1 frontend engineer

---

### Task 3.1: User Preferences

**Priority**: P2 - MEDIUM
**Effort**: 12 hours
**Owner**: Backend + Frontend Engineers
**Dependencies**: Task 1.1

#### Subtasks

1. **Create CQRS Commands** (3 hours)
   - File: `src/app/application/chat/commands/update_money_market_preferences.py`
   - File: `src/app/application/chat/commands/create_money_market_preferences.py`

2. **Create CQRS Queries** (2 hours)
   - File: `src/app/application/chat/queries/get_money_market_preferences.py`

3. **Create HTTP Endpoints** (3 hours)
   - `GET /api/v1/money-market/preferences`
   - `PUT /api/v1/money-market/preferences`

4. **Create Frontend UI** (4 hours)
   - Settings page for money market preferences
   - Toggle for rate alerts
   - Select watched assets and chains
   - Set alert threshold APY change

#### Success Criteria
- [ ] Users can save preferences
- [ ] Preferences persist across sessions
- [ ] Frontend UI functional
- [ ] Integration tests passing

---

### Task 3.2: Rate Change Alerts

**Priority**: P2 - MEDIUM
**Effort**: 20 hours
**Owner**: Backend Engineer
**Dependencies**: Task 3.1

#### Subtasks

1. **Create Alert Service** (6 hours)
   - File: `src/app/application/chat/services/money_market_alert_service.py`
   - Check for rate changes exceeding threshold
   - Send alerts via email/push/telegram

2. **Create Celery Background Task** (4 hours)
   - File: `src/app/infrastructure/tasks/money_market_rate_monitor.py`
   - Run every 5 minutes
   - Query users with rate alerts enabled
   - Compare current rates to last known rates
   - Send alerts if threshold exceeded

3. **Add Email/Push Notifications** (6 hours)
   - Email template for rate alerts
   - Push notification integration
   - Telegram bot integration

4. **Create Alert History UI** (4 hours)
   - Show alert history in frontend
   - Mark alerts as read
   - Unsubscribe from alerts

#### Success Criteria
- [ ] Alerts sent when rates change > threshold
- [ ] Celery task runs reliably
- [ ] Users receive notifications
- [ ] Alert history visible in UI

---

### Week 3 Milestone

**Deliverables**:
- ✅ User preferences functional
- ✅ Rate alert system operational
- ✅ Email/push notifications working
- ✅ Alert history UI complete

**Success Metrics**:
- Alert latency: < 5 minutes after rate change
- Notification delivery rate: > 95%
- User adoption: > 20% enable alerts
- Zero false alerts

---

## Risk Mitigation Strategies

### Technical Risks

1. **Database Migration Conflicts**
   - **Mitigation**: Use idempotent DO $$ blocks
   - **Fallback**: Manual enum creation if needed
   - **Testing**: Test migration on dev database first

2. **Cache Inconsistency**
   - **Mitigation**: 60s TTL keeps data fresh
   - **Fallback**: Manual cache invalidation API
   - **Monitoring**: Track cache hit/miss ratio

3. **RPC Rate Limiting**
   - **Mitigation**: Cache reduces RPC calls by 90%
   - **Fallback**: Use estimated rates from handler
   - **Monitoring**: Alert if cache hit rate drops < 80%

4. **Frontend Integration Breaking**
   - **Mitigation**: Follow exact ExecuteActionData schema
   - **Fallback**: Gradual rollout with feature flag
   - **Testing**: Integration tests before deploy

---

## Success Metrics Summary

### Performance Metrics
- **Cache Hit Rate**: > 90%
- **Comparison Latency**: < 200ms (with cache), < 1s (cache miss)
- **RPC Call Reduction**: > 90%
- **Database Query Time**: < 100ms

### Business Metrics
- **Comparison Volume**: Track daily/weekly growth
- **Protocol Selection**: Aave vs Compound vs Morpho distribution
- **Alert Adoption**: % of users enabling rate alerts
- **Conversion Rate**: Comparisons → actual deposits

### Quality Metrics
- **Test Coverage**: > 90%
- **Zero Breaking Changes**: Frontend compatibility maintained
- **Zero Data Loss**: All comparisons logged
- **High Availability**: > 99.9% uptime

---

## Deployment Plan

### Phase 1: Database Migration (Week 1 Day 1-2)
1. Create migration on dev environment
2. Run migration: `alembic upgrade head`
3. Verify tables created
4. Deploy to staging
5. Deploy to production (off-peak hours)

### Phase 2: Caching Layer (Week 1 Day 3-5)
1. Deploy caching adapter to staging
2. Monitor cache hit rate
3. Benchmark performance improvement
4. Deploy to production with feature flag
5. Gradually roll out to 100% traffic

### Phase 3: Integration Testing (Week 2)
1. Run integration tests on staging
2. Frontend team tests execute_data parsing
3. Performance benchmarking
4. Production rollout

### Phase 4: User Features (Week 3)
1. Deploy preferences API to staging
2. Deploy alert service with Celery task
3. Frontend team deploys UI
4. Production rollout

---

## Conclusion

This roadmap provides a clear, step-by-step plan to close all identified gaps in the Money Market implementation. By following this plan, the team will achieve:

- ✅ 5-8x performance improvement through caching
- ✅ Analytics and tracking for all comparisons
- ✅ User personalization with preferences and alerts
- ✅ Full integration with frontend execute pattern
- ✅ Production-ready, scalable implementation

**Total Effort**: 96 hours (12 days)
**Risk Level**: Medium (straightforward database work)
**Recommendation**: Start with Week 1 (P0 items) immediately

---

**Status**: ✅ Roadmap Complete | 🚀 Ready for Implementation
