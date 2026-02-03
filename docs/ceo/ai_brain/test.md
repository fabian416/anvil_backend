# AI Brain Module - Comprehensive Test Coverage Analysis

**Version:** 1.0.0
**Date:** 2026-01-26
**Status:** Test Specification
**Author:** Senior Code Reviewer (Claude Sonnet 4.5)

---

## Executive Summary

This document provides a comprehensive test coverage analysis for the AI Brain module, a centralized knowledge and configuration management system for AI agents. The AI Brain is a NEW module being designed from scratch, requiring thorough test coverage to ensure reliability, security, and performance.

**Testing Scope:**
- **8 Core Components**: Repositories, Cache, Services, Health Checks
- **300+ Total Tests**: Unit, Integration, E2E, Security, Performance
- **95%+ Coverage Target**: Critical paths fully tested
- **5-Week Implementation**: Parallel with development phases

**Key Testing Priorities:**
1. **Configuration changes correctly impact agent knowledge** (P0 - Critical)
2. **Cache invalidation works reliably** (P0 - Critical)
3. **Integration health checks are accurate** (P0 - Critical)
4. **Only admins can modify configurations** (P0 - Critical)
5. **Context-aware knowledge delivery functions** (P1 - High)

---

## Table of Contents

1. [Test Strategy Overview](#test-strategy-overview)
2. [Unit Tests (170 tests)](#unit-tests)
3. [Integration Tests (72 tests)](#integration-tests)
4. [End-to-End Tests (37 tests)](#end-to-end-tests)
5. [Security Tests (57 tests)](#security-tests)
6. [Performance Tests (15 tests)](#performance-tests)
7. [Test Implementation Plan](#test-implementation-plan)
8. [Test Templates & Code Examples](#test-templates--code-examples)
9. [Success Metrics](#success-metrics)
10. [Appendix: Test Data](#appendix-test-data)

---

## Test Strategy Overview

### Testing Pyramid

```
                    ┌─────────────────┐
                    │  E2E Tests      │  37 tests (10%)
                    │  (Workflows)    │
                    └─────────────────┘
                  ┌───────────────────────┐
                  │  Integration Tests    │  72 tests (20%)
                  │  (Component Interaction)│
                  └───────────────────────┘
              ┌─────────────────────────────────┐
              │      Unit Tests                  │  170 tests (48%)
              │  (Individual Components)         │
              └─────────────────────────────────┘
          ┌───────────────────────────────────────────┐
          │     Security Tests                         │  57 tests (16%)
          │  (Authorization, Access Control)           │
          └───────────────────────────────────────────┘
      ┌───────────────────────────────────────────────────┐
      │         Performance Tests                          │  15 tests (4%)
      │  (Load Testing, Benchmarks)                        │
      └───────────────────────────────────────────────────┘

Total: 351 tests
```

### Test Coverage Targets

| Component | Unit Tests | Integration Tests | E2E Tests | Security Tests | Total Tests | Coverage Target |
|-----------|------------|-------------------|-----------|----------------|-------------|-----------------|
| **AgentConfigRepository** | 15 | 8 | 3 | 6 | 32 | 95% |
| **KnowledgeRepository** | 20 | 10 | 5 | 8 | 43 | 95% |
| **PromptRepository** | 12 | 6 | 2 | 5 | 25 | 90% |
| **IntegrationRepository** | 10 | 6 | 3 | 4 | 23 | 90% |
| **RedisKnowledgeCache** | 15 | 8 | 4 | 6 | 33 | 95% |
| **KnowledgeInjector** | 18 | 10 | 5 | 8 | 41 | 95% |
| **ConfigurationService** | 20 | 8 | 6 | 10 | 44 | 95% |
| **IntegrationHealthService** | 12 | 6 | 4 | 5 | 27 | 90% |
| **Admin API Endpoints** | 25 | 5 | 3 | 5 | 38 | 95% |
| **Cache Invalidation** | 15 | 5 | 2 | - | 22 | 95% |
| **Performance Benchmarks** | - | - | - | - | 15 | N/A |
| **TOTAL** | **170** | **72** | **37** | **57** | **351** | **95%** |

### Test Environment Requirements

**Database:**
- PostgreSQL 14+ with test database
- Test data seeding scripts
- Alembic migrations applied

**Cache:**
- Redis 7+ test instance
- Isolated from production cache
- Automatic cleanup between tests

**Dependencies:**
- Mock external integrations (Hyperliquid, 1inch, Morpho)
- Test user accounts (guest, authenticated, premium, admin)
- Sample knowledge data

---

## Unit Tests

### 1. AgentConfigRepository (15 tests)

**Purpose:** Test CRUD operations for agent configurations

#### Test Suite: `test_agent_config_repository.py`

```python
"""
Unit tests for AgentConfigRepository
Location: tests/unit/infrastructure/adapters/test_agent_config_repository.py
"""

class TestAgentConfigRepository:
    """Test suite for agent configuration repository"""

    # CREATE Tests (3 tests)

    async def test_create_agent_config_success(self, db_session):
        """Test creating a new agent configuration"""
        # Arrange
        config_data = {
            "agent_type": "test_agent",
            "agent_name": "Test Agent",
            "agent_category": "core",
            "is_enabled": True,
            "model_name": "gemini-2.0-flash",
            "temperature": 0.7,
            "max_tokens": 1500,
            "depends_on_integrations": ["hyperliquid"]
        }

        # Act
        result = await repository.create_agent_config(config_data)

        # Assert
        assert result.agent_type == "test_agent"
        assert result.is_enabled is True
        assert result.version == 1
        assert result.configuration_hash is not None

    async def test_create_agent_config_duplicate_fails(self, db_session):
        """Test creating duplicate agent config raises error"""
        # Arrange
        await repository.create_agent_config({"agent_type": "chat", ...})

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.create_agent_config({"agent_type": "chat", ...})

    async def test_create_agent_config_invalid_category_fails(self, db_session):
        """Test creating config with invalid category fails"""
        # Arrange
        config_data = {"agent_category": "invalid", ...}

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid agent_category"):
            await repository.create_agent_config(config_data)

    # READ Tests (5 tests)

    async def test_get_agent_config_by_type_success(self, db_session):
        """Test retrieving agent config by agent_type"""
        # Arrange
        await seed_agent_config("knowledge")

        # Act
        result = await repository.get_agent_config("knowledge")

        # Assert
        assert result.agent_type == "knowledge"
        assert result.agent_name == "Knowledge Agent"

    async def test_get_agent_config_not_found_returns_none(self, db_session):
        """Test retrieving non-existent config returns None"""
        # Act
        result = await repository.get_agent_config("non_existent")

        # Assert
        assert result is None

    async def test_get_all_enabled_configs(self, db_session):
        """Test retrieving all enabled agent configurations"""
        # Arrange
        await seed_agent_config("knowledge", is_enabled=True)
        await seed_agent_config("chat", is_enabled=True)
        await seed_agent_config("disabled_agent", is_enabled=False)

        # Act
        results = await repository.get_all_enabled_configs()

        # Assert
        assert len(results) == 2
        assert all(r.is_enabled for r in results)

    async def test_get_configs_by_category(self, db_session):
        """Test filtering configs by category"""
        # Arrange
        await seed_agent_config("agent1", category="core")
        await seed_agent_config("agent2", category="core")
        await seed_agent_config("agent3", category="enterprise")

        # Act
        results = await repository.get_configs_by_category("core")

        # Assert
        assert len(results) == 2

    async def test_get_configs_depending_on_integration(self, db_session):
        """Test finding configs that depend on specific integration"""
        # Arrange
        await seed_agent_config("swap", depends_on=["hyperliquid", "1inch"])
        await seed_agent_config("lending", depends_on=["morpho"])

        # Act
        results = await repository.get_configs_depending_on("hyperliquid")

        # Assert
        assert len(results) == 1
        assert results[0].agent_type == "swap"

    # UPDATE Tests (4 tests)

    async def test_update_agent_config_success(self, db_session):
        """Test updating existing agent configuration"""
        # Arrange
        await seed_agent_config("knowledge")

        # Act
        result = await repository.update_agent_config(
            "knowledge",
            {"is_enabled": False, "temperature": 0.9}
        )

        # Assert
        assert result.is_enabled is False
        assert result.temperature == 0.9
        assert result.version == 2  # Version incremented
        assert result.updated_at > result.created_at

    async def test_update_agent_config_increments_version(self, db_session):
        """Test that updates increment version number"""
        # Arrange
        await seed_agent_config("knowledge")

        # Act
        await repository.update_agent_config("knowledge", {"temperature": 0.8})
        await repository.update_agent_config("knowledge", {"temperature": 0.9})
        result = await repository.get_agent_config("knowledge")

        # Assert
        assert result.version == 3

    async def test_update_agent_config_updates_configuration_hash(self, db_session):
        """Test that configuration hash changes on update"""
        # Arrange
        config = await seed_agent_config("knowledge")
        original_hash = config.configuration_hash

        # Act
        updated = await repository.update_agent_config(
            "knowledge",
            {"temperature": 0.9}
        )

        # Assert
        assert updated.configuration_hash != original_hash

    async def test_update_non_existent_config_raises_error(self, db_session):
        """Test updating non-existent config raises NotFoundError"""
        # Act & Assert
        with pytest.raises(NotFoundError):
            await repository.update_agent_config("non_existent", {"is_enabled": False})

    # DELETE Tests (1 test)

    async def test_delete_agent_config_success(self, db_session):
        """Test deleting agent configuration"""
        # Arrange
        await seed_agent_config("test_agent")

        # Act
        await repository.delete_agent_config("test_agent")
        result = await repository.get_agent_config("test_agent")

        # Assert
        assert result is None

    # AUDIT Tests (2 tests)

    async def test_get_config_version_history(self, db_session):
        """Test retrieving version history for agent config"""
        # Arrange
        await seed_agent_config("knowledge")
        await repository.update_agent_config("knowledge", {"temperature": 0.8})
        await repository.update_agent_config("knowledge", {"temperature": 0.9})

        # Act
        history = await repository.get_config_version_history("knowledge")

        # Assert
        assert len(history) == 3  # Original + 2 updates
        assert history[0].version == 3  # Latest first
        assert history[-1].version == 1  # Oldest last

    async def test_rollback_to_previous_version(self, db_session):
        """Test rolling back to previous configuration version"""
        # Arrange
        original = await seed_agent_config("knowledge", temperature=0.7)
        await repository.update_agent_config("knowledge", {"temperature": 0.9})

        # Act
        result = await repository.rollback_to_version("knowledge", version=1)

        # Assert
        assert result.temperature == 0.7
        assert result.version == 3  # New version, old config
```

**Test Coverage:**
- CREATE: 3 tests (success, duplicate, validation)
- READ: 5 tests (by type, not found, all enabled, by category, by integration)
- UPDATE: 4 tests (success, versioning, hash update, not found)
- DELETE: 1 test
- AUDIT: 2 tests (history, rollback)
- **Total: 15 tests**

---

### 2. KnowledgeRepository (20 tests)

**Purpose:** Test knowledge retrieval with context-aware queries

#### Test Suite: `test_knowledge_repository.py`

```python
"""
Unit tests for KnowledgeRepository
Location: tests/unit/infrastructure/adapters/test_knowledge_repository.py
"""

class TestKnowledgeRepository:
    """Test suite for knowledge repository"""

    # CREATE Tests (3 tests)

    async def test_create_knowledge_entry_success(self, db_session):
        """Test creating a new knowledge entry"""
        # Arrange
        knowledge_data = {
            "knowledge_key": "swap_overview",
            "knowledge_category": "feature",
            "agent_types": ["knowledge", "chat", "swap_workflow"],
            "intent_patterns": ["SWAP", "EXCHANGE"],
            "title": "Token Swap Overview",
            "content": {"feature_name": "Token Swap", ...},
            "depends_on_integrations": ["hyperliquid"],
            "user_type": None,  # Available for all
            "language": "en"
        }

        # Act
        result = await repository.create_knowledge(knowledge_data)

        # Assert
        assert result.knowledge_key == "swap_overview"
        assert "SWAP" in result.intent_patterns
        assert result.is_enabled is True

    async def test_create_knowledge_with_fallback(self, db_session):
        """Test creating knowledge entry with fallback reference"""
        # Arrange
        fallback = await seed_knowledge("swap_fallback")
        knowledge_data = {
            "knowledge_key": "swap_hyperliquid",
            "fallback_knowledge_id": fallback.id,
            ...
        }

        # Act
        result = await repository.create_knowledge(knowledge_data)

        # Assert
        assert result.fallback_knowledge_id == fallback.id

    async def test_create_knowledge_duplicate_key_fails(self, db_session):
        """Test creating duplicate knowledge key fails"""
        # Arrange
        await seed_knowledge("swap_overview", user_type="guest", language="en")

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.create_knowledge({
                "knowledge_key": "swap_overview",
                "user_type": "guest",
                "language": "en",
                ...
            })

    # READ - Basic Queries (5 tests)

    async def test_get_knowledge_by_key_success(self, db_session):
        """Test retrieving knowledge by key"""
        # Arrange
        await seed_knowledge("swap_overview")

        # Act
        result = await repository.get_knowledge_by_key("swap_overview")

        # Assert
        assert result.knowledge_key == "swap_overview"

    async def test_get_knowledge_by_intent(self, db_session):
        """Test retrieving knowledge by intent pattern"""
        # Arrange
        await seed_knowledge("swap_overview", intent_patterns=["SWAP", "EXCHANGE"])
        await seed_knowledge("hunter_ai", intent_patterns=["HUNTER", "SENTIMENT"])

        # Act
        results = await repository.get_knowledge_by_intent("SWAP")

        # Assert
        assert len(results) == 1
        assert results[0].knowledge_key == "swap_overview"

    async def test_get_knowledge_for_agent_type(self, db_session):
        """Test retrieving knowledge for specific agent"""
        # Arrange
        await seed_knowledge("swap", agent_types=["knowledge", "swap_workflow"])
        await seed_knowledge("hunter", agent_types=["knowledge", "hunter_ai"])

        # Act
        results = await repository.get_knowledge_for_agent("swap_workflow")

        # Assert
        assert len(results) == 1
        assert results[0].knowledge_key == "swap"

    async def test_get_enabled_knowledge_only(self, db_session):
        """Test that only enabled knowledge is returned"""
        # Arrange
        await seed_knowledge("enabled", is_enabled=True)
        await seed_knowledge("disabled", is_enabled=False)

        # Act
        results = await repository.get_all_knowledge(enabled_only=True)

        # Assert
        assert len(results) == 1
        assert results[0].knowledge_key == "enabled"

    async def test_get_knowledge_by_category(self, db_session):
        """Test filtering knowledge by category"""
        # Arrange
        await seed_knowledge("swap", category="feature")
        await seed_knowledge("hyperliquid_info", category="integration")

        # Act
        results = await repository.get_knowledge_by_category("feature")

        # Assert
        assert len(results) == 1
        assert results[0].knowledge_key == "swap"

    # READ - Context-Aware Queries (6 tests)

    async def test_get_knowledge_for_guest_user(self, db_session):
        """Test retrieving knowledge filtered for guest users"""
        # Arrange
        await seed_knowledge("guest_only", user_type="guest")
        await seed_knowledge("auth_only", user_type="authenticated")
        await seed_knowledge("all_users", user_type=None)

        # Act
        results = await repository.get_knowledge_for_user_type("guest")

        # Assert
        assert len(results) == 2  # guest_only + all_users
        keys = [r.knowledge_key for r in results]
        assert "guest_only" in keys
        assert "all_users" in keys
        assert "auth_only" not in keys

    async def test_get_knowledge_for_authenticated_user(self, db_session):
        """Test retrieving knowledge for authenticated users"""
        # Arrange
        await seed_knowledge("guest_only", user_type="guest")
        await seed_knowledge("auth_only", user_type="authenticated")
        await seed_knowledge("premium_only", user_type="premium")
        await seed_knowledge("all_users", user_type=None)

        # Act
        results = await repository.get_knowledge_for_user_type("authenticated")

        # Assert
        assert len(results) == 3  # guest + auth + all
        keys = [r.knowledge_key for r in results]
        assert "premium_only" not in keys

    async def test_get_knowledge_by_language(self, db_session):
        """Test retrieving knowledge by language"""
        # Arrange
        await seed_knowledge("swap_en", language="en")
        await seed_knowledge("swap_es", language="es")

        # Act
        results = await repository.get_knowledge_by_language("es")

        # Assert
        assert len(results) == 1
        assert results[0].knowledge_key == "swap_es"

    async def test_get_knowledge_with_integration_dependencies(self, db_session):
        """Test retrieving knowledge filtered by available integrations"""
        # Arrange
        await seed_knowledge("swap_hyperliquid", depends_on=["hyperliquid"])
        await seed_knowledge("swap_1inch", depends_on=["1inch"])
        await seed_knowledge("swap_any", depends_on=[])

        # Act
        available_integrations = ["hyperliquid"]
        results = await repository.get_knowledge_with_available_integrations(
            available_integrations
        )

        # Assert
        keys = [r.knowledge_key for r in results]
        assert "swap_hyperliquid" in keys
        assert "swap_any" in keys
        assert "swap_1inch" not in keys

    async def test_get_knowledge_for_intent_with_context(self, db_session):
        """Test complete context-aware knowledge retrieval"""
        # Arrange
        await seed_knowledge(
            "swap_guest_en",
            intent_patterns=["SWAP"],
            user_type="guest",
            language="en",
            depends_on=["hyperliquid"]
        )

        # Act
        result = await repository.get_knowledge_for_intent(
            detected_intent="SWAP",
            user_type="guest",
            language="en",
            available_integrations=["hyperliquid"]
        )

        # Assert
        assert result.knowledge_key == "swap_guest_en"

    async def test_get_knowledge_fallback_when_dependencies_unavailable(self, db_session):
        """Test fallback knowledge when integration dependencies unavailable"""
        # Arrange
        fallback = await seed_knowledge("swap_fallback", depends_on=[])
        await seed_knowledge(
            "swap_hyperliquid",
            depends_on=["hyperliquid"],
            fallback_knowledge_id=fallback.id
        )

        # Act (Hyperliquid not available)
        result = await repository.get_knowledge_for_intent(
            detected_intent="SWAP",
            user_type="authenticated",
            available_integrations=[]  # No integrations available
        )

        # Assert
        assert result.knowledge_key == "swap_fallback"

    # UPDATE Tests (3 tests)

    async def test_update_knowledge_content(self, db_session):
        """Test updating knowledge content"""
        # Arrange
        knowledge = await seed_knowledge("swap_overview")
        original_hash = knowledge.content_hash

        # Act
        updated = await repository.update_knowledge(
            "swap_overview",
            {"content": {"feature_name": "Updated Swap", ...}}
        )

        # Assert
        assert updated.content["feature_name"] == "Updated Swap"
        assert updated.content_hash != original_hash
        assert updated.version == 2

    async def test_update_knowledge_access_count(self, db_session):
        """Test incrementing knowledge access count"""
        # Arrange
        knowledge = await seed_knowledge("swap_overview")

        # Act
        await repository.increment_access_count("swap_overview")
        await repository.increment_access_count("swap_overview")
        result = await repository.get_knowledge_by_key("swap_overview")

        # Assert
        assert result.access_count == 2
        assert result.last_accessed_at is not None

    async def test_update_knowledge_retrieval_metrics(self, db_session):
        """Test updating average retrieval time"""
        # Arrange
        knowledge = await seed_knowledge("swap_overview")

        # Act
        await repository.update_retrieval_metrics("swap_overview", retrieval_time_ms=25)
        await repository.update_retrieval_metrics("swap_overview", retrieval_time_ms=35)
        result = await repository.get_knowledge_by_key("swap_overview")

        # Assert
        assert result.avg_retrieval_time_ms == 30  # Average of 25 and 35

    # HIERARCHICAL Tests (2 tests)

    async def test_get_child_knowledge_entries(self, db_session):
        """Test retrieving child knowledge entries"""
        # Arrange
        parent = await seed_knowledge("swap_parent")
        await seed_knowledge("swap_child1", parent_knowledge_id=parent.id)
        await seed_knowledge("swap_child2", parent_knowledge_id=parent.id)

        # Act
        children = await repository.get_child_knowledge(parent.id)

        # Assert
        assert len(children) == 2

    async def test_get_knowledge_tree(self, db_session):
        """Test retrieving full knowledge tree"""
        # Arrange
        parent = await seed_knowledge("swap_parent")
        child1 = await seed_knowledge("swap_child1", parent_knowledge_id=parent.id)
        grandchild = await seed_knowledge("swap_grandchild", parent_knowledge_id=child1.id)

        # Act
        tree = await repository.get_knowledge_tree(parent.id)

        # Assert
        assert len(tree) == 3  # parent + child + grandchild

    # DELETE Test (1 test)

    async def test_delete_knowledge_cascades_to_children(self, db_session):
        """Test deleting parent knowledge cascades to children"""
        # Arrange
        parent = await seed_knowledge("swap_parent")
        await seed_knowledge("swap_child", parent_knowledge_id=parent.id)

        # Act
        await repository.delete_knowledge(parent.id)

        # Assert
        result = await repository.get_knowledge_by_key("swap_child")
        assert result is None  # Cascade delete
```

**Test Coverage:**
- CREATE: 3 tests
- READ (Basic): 5 tests
- READ (Context-Aware): 6 tests
- UPDATE: 3 tests
- HIERARCHICAL: 2 tests
- DELETE: 1 test
- **Total: 20 tests**

---

### 3. PromptRepository (12 tests)

**Purpose:** Test prompt management with versioning and A/B testing

#### Test Suite: `test_prompt_repository.py`

```python
"""
Unit tests for PromptRepository
Location: tests/unit/infrastructure/adapters/test_prompt_repository.py
"""

class TestPromptRepository:
    """Test suite for agent prompt repository"""

    # CREATE Tests (3 tests)

    async def test_create_prompt_success(self, db_session):
        """Test creating a new agent prompt"""
        # Arrange
        prompt_data = {
            "agent_type": "knowledge",
            "prompt_type": "system",
            "prompt_content": "You are a knowledge assistant...",
            "variant_name": "default",
            "traffic_percentage": 100.0,
            "is_active": True
        }

        # Act
        result = await repository.create_prompt(prompt_data)

        # Assert
        assert result.agent_type == "knowledge"
        assert result.version == 1
        assert result.is_active is True

    async def test_create_prompt_ab_variant(self, db_session):
        """Test creating A/B test variant prompt"""
        # Arrange
        await seed_prompt("knowledge", "system", variant="default", traffic=70.0)
        variant_data = {
            "agent_type": "knowledge",
            "prompt_type": "system",
            "prompt_content": "You are an advanced knowledge assistant...",
            "variant_name": "variant_a",
            "traffic_percentage": 30.0,
            "is_active": True
        }

        # Act
        result = await repository.create_prompt(variant_data)

        # Assert
        assert result.variant_name == "variant_a"
        assert result.traffic_percentage == 30.0

    async def test_create_prompt_traffic_exceeds_100_fails(self, db_session):
        """Test that total traffic percentage cannot exceed 100%"""
        # Arrange
        await seed_prompt("knowledge", "system", variant="default", traffic=80.0)

        # Act & Assert
        with pytest.raises(ValidationError, match="Total traffic exceeds 100%"):
            await repository.create_prompt({
                "agent_type": "knowledge",
                "prompt_type": "system",
                "variant_name": "variant_a",
                "traffic_percentage": 30.0,  # 80 + 30 = 110%
                "is_active": True
            })

    # READ Tests (4 tests)

    async def test_get_active_prompt_for_agent(self, db_session):
        """Test retrieving active prompt for agent"""
        # Arrange
        await seed_prompt("knowledge", "system", is_active=True)
        await seed_prompt("knowledge", "user", is_active=False)

        # Act
        result = await repository.get_active_prompt("knowledge", "system")

        # Assert
        assert result.prompt_type == "system"
        assert result.is_active is True

    async def test_get_prompt_variant_based_on_traffic(self, db_session):
        """Test selecting prompt variant based on traffic percentage"""
        # Arrange
        await seed_prompt("knowledge", "system", variant="default", traffic=70.0)
        await seed_prompt("knowledge", "system", variant="variant_a", traffic=30.0)

        # Act - Simulate 100 requests
        variants_selected = []
        for i in range(100):
            result = await repository.get_prompt_for_request(
                "knowledge", "system", random_value=i/100
            )
            variants_selected.append(result.variant_name)

        # Assert - Approximately 70/30 split
        default_count = variants_selected.count("default")
        variant_a_count = variants_selected.count("variant_a")
        assert 65 <= default_count <= 75
        assert 25 <= variant_a_count <= 35

    async def test_get_all_prompts_for_agent(self, db_session):
        """Test retrieving all prompts for specific agent"""
        # Arrange
        await seed_prompt("knowledge", "system")
        await seed_prompt("knowledge", "user")
        await seed_prompt("chat", "system")

        # Act
        results = await repository.get_all_prompts_for_agent("knowledge")

        # Assert
        assert len(results) == 2
        prompt_types = [r.prompt_type for r in results]
        assert "system" in prompt_types
        assert "user" in prompt_types

    async def test_get_prompt_version_history(self, db_session):
        """Test retrieving prompt version history"""
        # Arrange
        original = await seed_prompt("knowledge", "system")
        await repository.update_prompt(original.id, {"prompt_content": "Updated v2"})
        await repository.update_prompt(original.id, {"prompt_content": "Updated v3"})

        # Act
        history = await repository.get_prompt_version_history(original.id)

        # Assert
        assert len(history) == 3
        assert history[0].version == 3  # Latest first

    # UPDATE Tests (3 tests)

    async def test_update_prompt_content_increments_version(self, db_session):
        """Test updating prompt increments version"""
        # Arrange
        prompt = await seed_prompt("knowledge", "system")

        # Act
        updated = await repository.update_prompt(
            prompt.id,
            {"prompt_content": "Updated prompt content"}
        )

        # Assert
        assert updated.version == 2
        assert updated.prompt_content == "Updated prompt content"

    async def test_deactivate_prompt(self, db_session):
        """Test deactivating a prompt"""
        # Arrange
        prompt = await seed_prompt("knowledge", "system", is_active=True)

        # Act
        updated = await repository.deactivate_prompt(prompt.id)

        # Assert
        assert updated.is_active is False
        assert updated.deactivated_at is not None

    async def test_update_prompt_performance_metrics(self, db_session):
        """Test updating prompt performance metrics"""
        # Arrange
        prompt = await seed_prompt("knowledge", "system")

        # Act
        await repository.update_performance_metrics(
            prompt.id,
            avg_response_time_ms=150,
            success_rate=95.5,
            user_satisfaction_score=4.2
        )
        result = await repository.get_prompt_by_id(prompt.id)

        # Assert
        assert result.avg_response_time_ms == 150
        assert result.success_rate == 95.5
        assert result.user_satisfaction_score == 4.2

    # A/B TESTING Tests (2 tests)

    async def test_adjust_traffic_percentage(self, db_session):
        """Test adjusting traffic percentage for A/B testing"""
        # Arrange
        default = await seed_prompt("knowledge", "system", variant="default", traffic=70.0)
        variant_a = await seed_prompt("knowledge", "system", variant="variant_a", traffic=30.0)

        # Act - Shift traffic to better performer
        await repository.adjust_traffic("knowledge", "system", {
            "default": 50.0,
            "variant_a": 50.0
        })

        # Assert
        updated_default = await repository.get_prompt_by_id(default.id)
        updated_variant = await repository.get_prompt_by_id(variant_a.id)
        assert updated_default.traffic_percentage == 50.0
        assert updated_variant.traffic_percentage == 50.0

    async def test_promote_variant_to_default(self, db_session):
        """Test promoting successful variant to default"""
        # Arrange
        default = await seed_prompt("knowledge", "system", variant="default", traffic=70.0)
        variant_a = await seed_prompt("knowledge", "system", variant="variant_a", traffic=30.0)

        # Act - variant_a performs better, promote it
        await repository.promote_variant_to_default("knowledge", "system", "variant_a")

        # Assert
        updated_default = await repository.get_active_prompt("knowledge", "system")
        assert updated_default.variant_name == "variant_a"
        assert updated_default.traffic_percentage == 100.0
```

**Test Coverage:**
- CREATE: 3 tests (basic, A/B variant, validation)
- READ: 4 tests (active prompt, variant selection, all prompts, version history)
- UPDATE: 3 tests (version increment, deactivate, performance metrics)
- A/B TESTING: 2 tests (traffic adjustment, variant promotion)
- **Total: 12 tests**

---

### 4. IntegrationRepository (10 tests)

**Purpose:** Test integration health tracking and status management

#### Test Suite: `test_integration_repository.py`

```python
"""
Unit tests for IntegrationRepository
Location: tests/unit/infrastructure/adapters/test_integration_repository.py
"""

class TestIntegrationRepository:
    """Test suite for integration configuration repository"""

    # CREATE Tests (2 tests)

    async def test_create_integration_config_success(self, db_session):
        """Test creating integration configuration"""
        # Arrange
        integration_data = {
            "integration_key": "hyperliquid",
            "integration_name": "Hyperliquid Spot",
            "integration_type": "exchange",
            "is_enabled": True,
            "health_status": "healthy",
            "api_endpoint": "https://api.hyperliquid.xyz",
            "rate_limit_per_minute": 60,
            "impacts_features": ["swap", "trading"],
            "impacts_agents": ["swap_workflow"]
        }

        # Act
        result = await repository.create_integration_config(integration_data)

        # Assert
        assert result.integration_key == "hyperliquid"
        assert result.health_status == "healthy"
        assert "swap" in result.impacts_features

    async def test_create_integration_with_fallback(self, db_session):
        """Test creating integration with fallback reference"""
        # Arrange
        await seed_integration("1inch")

        # Act
        result = await repository.create_integration_config({
            "integration_key": "hyperliquid",
            "fallback_integration_key": "1inch",
            ...
        })

        # Assert
        assert result.fallback_integration_key == "1inch"

    # READ Tests (3 tests)

    async def test_get_integration_by_key(self, db_session):
        """Test retrieving integration by key"""
        # Arrange
        await seed_integration("hyperliquid")

        # Act
        result = await repository.get_integration("hyperliquid")

        # Assert
        assert result.integration_key == "hyperliquid"

    async def test_get_all_enabled_integrations(self, db_session):
        """Test retrieving all enabled integrations"""
        # Arrange
        await seed_integration("hyperliquid", is_enabled=True)
        await seed_integration("1inch", is_enabled=True)
        await seed_integration("disabled", is_enabled=False)

        # Act
        results = await repository.get_all_enabled_integrations()

        # Assert
        assert len(results) == 2
        keys = [r.integration_key for r in results]
        assert "disabled" not in keys

    async def test_get_healthy_integrations(self, db_session):
        """Test retrieving only healthy integrations"""
        # Arrange
        await seed_integration("hyperliquid", health_status="healthy")
        await seed_integration("1inch", health_status="degraded")
        await seed_integration("morpho", health_status="down")

        # Act
        results = await repository.get_healthy_integrations()

        # Assert
        assert len(results) == 1
        assert results[0].integration_key == "hyperliquid"

    # UPDATE - Health Status Tests (3 tests)

    async def test_update_health_status_to_down(self, db_session):
        """Test updating integration health status to down"""
        # Arrange
        integration = await seed_integration("hyperliquid", health_status="healthy")

        # Act
        updated = await repository.update_health_status(
            "hyperliquid",
            health_status="down",
            error_message="API timeout after 30s"
        )

        # Assert
        assert updated.health_status == "down"
        assert updated.health_check_error == "API timeout after 30s"
        assert updated.last_health_check_at is not None

    async def test_update_health_status_to_healthy_clears_error(self, db_session):
        """Test that healthy status clears error message"""
        # Arrange
        integration = await seed_integration(
            "hyperliquid",
            health_status="down",
            error_message="Previous error"
        )

        # Act
        updated = await repository.update_health_status(
            "hyperliquid",
            health_status="healthy"
        )

        # Assert
        assert updated.health_status == "healthy"
        assert updated.health_check_error is None

    async def test_update_performance_metrics(self, db_session):
        """Test updating integration performance metrics"""
        # Arrange
        integration = await seed_integration("hyperliquid")

        # Act
        await repository.update_performance_metrics(
            "hyperliquid",
            avg_response_time_ms=45,
            error_rate=0.01,
            uptime_percentage=99.95
        )
        result = await repository.get_integration("hyperliquid")

        # Assert
        assert result.avg_response_time_ms == 45
        assert result.error_rate == 0.01
        assert result.uptime_percentage == 99.95

    # IMPACT ANALYSIS Tests (2 tests)

    async def test_get_impacted_features_when_integration_down(self, db_session):
        """Test finding features impacted by integration failure"""
        # Arrange
        await seed_integration(
            "hyperliquid",
            impacts_features=["swap", "trading"],
            health_status="down"
        )

        # Act
        impacted = await repository.get_impacted_features("hyperliquid")

        # Assert
        assert "swap" in impacted
        assert "trading" in impacted

    async def test_get_impacted_agents_when_integration_down(self, db_session):
        """Test finding agents impacted by integration failure"""
        # Arrange
        await seed_integration(
            "morpho",
            impacts_agents=["lending_workflow"],
            health_status="down"
        )

        # Act
        impacted = await repository.get_impacted_agents("morpho")

        # Assert
        assert "lending_workflow" in impacted
```

**Test Coverage:**
- CREATE: 2 tests
- READ: 3 tests
- UPDATE (Health Status): 3 tests
- IMPACT ANALYSIS: 2 tests
- **Total: 10 tests**

---

### 5. RedisKnowledgeCache (15 tests)

**Purpose:** Test Redis caching operations and invalidation

#### Test Suite: `test_redis_knowledge_cache.py`

```python
"""
Unit tests for RedisKnowledgeCache
Location: tests/unit/infrastructure/adapters/test_redis_knowledge_cache.py
"""

class TestRedisKnowledgeCache:
    """Test suite for Redis knowledge cache"""

    @pytest.fixture(autouse=True)
    async def setup_teardown(self, redis_client):
        """Clear Redis cache before and after each test"""
        await redis_client.flushdb()
        yield
        await redis_client.flushdb()

    # SET Tests (4 tests)

    async def test_cache_knowledge_entry(self, redis_client):
        """Test caching knowledge entry in Redis"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client)
        knowledge_data = {
            "id": "uuid-123",
            "knowledge_key": "swap_overview",
            "content": {"feature_name": "Token Swap"},
            "version": 1
        }

        # Act
        await cache.set_knowledge(
            key="swap_overview",
            user_type="guest",
            language="en",
            data=knowledge_data,
            ttl=3600
        )

        # Assert
        cached = await redis_client.hgetall("ai_brain:knowledge:swap_overview:guest:en")
        assert cached["knowledge_key"] == "swap_overview"
        assert json.loads(cached["content"])["feature_name"] == "Token Swap"

    async def test_cache_with_compression(self, redis_client):
        """Test caching with compression enabled"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client, compression_enabled=True)
        large_content = {"data": "x" * 10000}  # 10KB content

        # Act
        await cache.set_knowledge(
            key="large_knowledge",
            user_type="authenticated",
            language="en",
            data={"content": large_content},
            ttl=3600
        )

        # Assert
        cached = await redis_client.hget("ai_brain:knowledge:large_knowledge:authenticated:en", "content")
        # Should be compressed (smaller than original)
        assert len(cached) < len(json.dumps(large_content))

    async def test_cache_ttl_is_set(self, redis_client):
        """Test that cache entries have correct TTL"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client)

        # Act
        await cache.set_knowledge(
            key="swap_overview",
            user_type="guest",
            language="en",
            data={"id": "123"},
            ttl=3600
        )

        # Assert
        ttl = await redis_client.ttl("ai_brain:knowledge:swap_overview:guest:en")
        assert 3500 <= ttl <= 3600  # Allow small timing variance

    async def test_cache_agent_config(self, redis_client):
        """Test caching agent configuration"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client)
        config_data = {
            "agent_type": "knowledge",
            "is_enabled": True,
            "model_name": "gemini-2.0-flash"
        }

        # Act
        await cache.set_agent_config(
            agent_type="knowledge",
            data=config_data,
            ttl=7200
        )

        # Assert
        cached = await redis_client.hgetall("ai_brain:config:agent:knowledge")
        assert cached["agent_type"] == "knowledge"
        assert cached["is_enabled"] == "True"

    # GET Tests (4 tests)

    async def test_get_cached_knowledge_hit(self, redis_client):
        """Test retrieving cached knowledge (cache hit)"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client)
        knowledge_data = {"knowledge_key": "swap_overview"}
        await cache.set_knowledge("swap_overview", "guest", "en", knowledge_data, 3600)

        # Act
        result = await cache.get_knowledge("swap_overview", "guest", "en")

        # Assert
        assert result is not None
        assert result["knowledge_key"] == "swap_overview"

    async def test_get_cached_knowledge_miss(self, redis_client):
        """Test retrieving non-existent knowledge (cache miss)"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client)

        # Act
        result = await cache.get_knowledge("non_existent", "guest", "en")

        # Assert
        assert result is None

    async def test_get_with_decompression(self, redis_client):
        """Test retrieving compressed knowledge"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client, compression_enabled=True)
        large_content = {"data": "x" * 10000}
        await cache.set_knowledge("large", "guest", "en", {"content": large_content}, 3600)

        # Act
        result = await cache.get_knowledge("large", "guest", "en")

        # Assert
        assert result["content"] == large_content  # Decompressed correctly

    async def test_get_expired_cache_returns_none(self, redis_client):
        """Test that expired cache entries return None"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client)
        await cache.set_knowledge("swap", "guest", "en", {"id": "123"}, ttl=1)  # 1 second TTL

        # Act
        await asyncio.sleep(2)  # Wait for expiration
        result = await cache.get_knowledge("swap", "guest", "en")

        # Assert
        assert result is None

    # INVALIDATE Tests (4 tests)

    async def test_invalidate_specific_knowledge(self, redis_client):
        """Test invalidating specific knowledge entry"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client)
        await cache.set_knowledge("swap", "guest", "en", {"id": "123"}, 3600)
        await cache.set_knowledge("hunter", "guest", "en", {"id": "456"}, 3600)

        # Act
        await cache.invalidate_knowledge("swap", "guest", "en")

        # Assert
        swap_cached = await cache.get_knowledge("swap", "guest", "en")
        hunter_cached = await cache.get_knowledge("hunter", "guest", "en")
        assert swap_cached is None
        assert hunter_cached is not None  # Not affected

    async def test_invalidate_knowledge_pattern(self, redis_client):
        """Test invalidating knowledge entries by pattern"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client)
        await cache.set_knowledge("swap", "guest", "en", {"id": "1"}, 3600)
        await cache.set_knowledge("swap", "guest", "es", {"id": "2"}, 3600)
        await cache.set_knowledge("swap", "authenticated", "en", {"id": "3"}, 3600)

        # Act - Invalidate all swap knowledge
        await cache.invalidate_pattern("ai_brain:knowledge:swap:*")

        # Assert
        assert await cache.get_knowledge("swap", "guest", "en") is None
        assert await cache.get_knowledge("swap", "guest", "es") is None
        assert await cache.get_knowledge("swap", "authenticated", "en") is None

    async def test_invalidate_agent_config_cache(self, redis_client):
        """Test invalidating agent configuration cache"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client)
        await cache.set_agent_config("knowledge", {"is_enabled": True}, 7200)

        # Act
        await cache.invalidate_agent_config("knowledge")

        # Assert
        result = await cache.get_agent_config("knowledge")
        assert result is None

    async def test_flush_all_ai_brain_cache(self, redis_client):
        """Test flushing all AI Brain cache entries"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client)
        await cache.set_knowledge("swap", "guest", "en", {"id": "1"}, 3600)
        await cache.set_agent_config("knowledge", {"is_enabled": True}, 7200)
        await redis_client.set("other:key", "value")  # Non-AI-Brain key

        # Act
        await cache.flush_ai_brain_cache()

        # Assert
        assert await cache.get_knowledge("swap", "guest", "en") is None
        assert await cache.get_agent_config("knowledge") is None
        assert await redis_client.get("other:key") == "value"  # Not affected

    # METRICS Tests (3 tests)

    async def test_track_cache_hit(self, redis_client, db_session):
        """Test tracking cache hit metrics"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client, db_session)
        cache_key = "ai_brain:knowledge:swap:guest:en"
        await cache.set_knowledge("swap", "guest", "en", {"id": "1"}, 3600)

        # Act
        await cache.get_knowledge("swap", "guest", "en")  # Cache hit

        # Assert - Check database metrics
        metadata = await db_session.fetch_one("""
            SELECT hit_count, miss_count
            FROM knowledge_cache_metadata
            WHERE cache_key = :key
        """, {"key": cache_key})
        assert metadata["hit_count"] == 1
        assert metadata["miss_count"] == 0

    async def test_track_cache_miss(self, redis_client, db_session):
        """Test tracking cache miss metrics"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client, db_session)
        cache_key = "ai_brain:knowledge:swap:guest:en"

        # Act
        await cache.get_knowledge("swap", "guest", "en")  # Cache miss

        # Assert
        metadata = await db_session.fetch_one("""
            SELECT hit_count, miss_count
            FROM knowledge_cache_metadata
            WHERE cache_key = :key
        """, {"key": cache_key})
        assert metadata["hit_count"] == 0
        assert metadata["miss_count"] == 1

    async def test_calculate_hit_rate(self, redis_client, db_session):
        """Test calculating cache hit rate"""
        # Arrange
        cache = RedisKnowledgeCache(redis_client, db_session)
        await cache.set_knowledge("swap", "guest", "en", {"id": "1"}, 3600)

        # Act - 7 hits, 3 misses
        for _ in range(7):
            await cache.get_knowledge("swap", "guest", "en")  # Hit
        for i in range(3):
            await cache.get_knowledge(f"non_existent_{i}", "guest", "en")  # Miss

        # Assert - 70% hit rate
        cache_key = "ai_brain:knowledge:swap:guest:en"
        metadata = await db_session.fetch_one("""
            SELECT hit_rate
            FROM knowledge_cache_metadata
            WHERE cache_key = :key
        """, {"key": cache_key})
        assert metadata["hit_rate"] == 70.0
```

**Test Coverage:**
- SET: 4 tests (basic, compression, TTL, agent config)
- GET: 4 tests (hit, miss, decompression, expiration)
- INVALIDATE: 4 tests (specific, pattern, agent config, flush all)
- METRICS: 3 tests (hit tracking, miss tracking, hit rate calculation)
- **Total: 15 tests**

---

## Integration Tests

### 6. Database + Redis Cache Coherence (25 tests)

**Purpose:** Test that database and cache stay synchronized

#### Test Suite: `test_cache_coherence.py`

```python
"""
Integration tests for database and Redis cache coherence
Location: tests/integration/test_cache_coherence.py
"""

class TestCacheCoherence:
    """Test suite for cache coherence with database"""

    # KNOWLEDGE CACHE COHERENCE (10 tests)

    async def test_knowledge_update_invalidates_cache(self, db_session, redis_client):
        """Test that updating knowledge in database invalidates cache"""
        # Arrange
        knowledge_repo = KnowledgeRepositorySQLA(db_session, redis_client)
        cache = RedisKnowledgeCache(redis_client, db_session)

        # Create and cache knowledge
        knowledge = await knowledge_repo.create_knowledge({
            "knowledge_key": "swap_overview",
            "content": {"version": 1},
            ...
        })
        cached = await cache.get_knowledge("swap_overview", None, "en")
        assert cached is not None

        # Act - Update knowledge
        await knowledge_repo.update_knowledge("swap_overview", {
            "content": {"version": 2}
        })

        # Assert - Cache should be invalidated
        cached_after = await cache.get_knowledge("swap_overview", None, "en")
        assert cached_after is None  # Cache invalidated

        # Verify database has new version
        db_knowledge = await knowledge_repo.get_knowledge_by_key("swap_overview")
        assert db_knowledge.content["version"] == 2

    async def test_knowledge_delete_invalidates_cache(self, db_session, redis_client):
        """Test that deleting knowledge invalidates cache"""
        # Arrange
        knowledge_repo = KnowledgeRepositorySQLA(db_session, redis_client)
        cache = RedisKnowledgeCache(redis_client, db_session)

        knowledge = await knowledge_repo.create_knowledge({"knowledge_key": "test", ...})
        await cache.set_knowledge("test", None, "en", {"id": knowledge.id}, 3600)

        # Act
        await knowledge_repo.delete_knowledge(knowledge.id)

        # Assert
        assert await cache.get_knowledge("test", None, "en") is None
        assert await knowledge_repo.get_knowledge_by_key("test") is None

    async def test_cache_miss_loads_from_database(self, db_session, redis_client):
        """Test that cache miss loads data from database and caches it"""
        # Arrange
        knowledge_repo = KnowledgeRepositorySQLA(db_session, redis_client)
        cache = RedisKnowledgeCache(redis_client, db_session)

        # Create knowledge without caching
        await db_session.execute("""
            INSERT INTO agent_knowledge (knowledge_key, content, ...)
            VALUES ('swap', '{"version": 1}', ...)
        """)

        # Act - Get knowledge (should load from DB and cache)
        result = await knowledge_repo.get_knowledge_with_cache("swap", None, "en")

        # Assert
        assert result.content["version"] == 1

        # Verify it's now cached
        cached = await cache.get_knowledge("swap", None, "en")
        assert cached is not None
        assert cached["content"]["version"] == 1

    async def test_concurrent_updates_maintain_coherence(self, db_session, redis_client):
        """Test that concurrent updates don't cause cache/DB inconsistency"""
        # Arrange
        knowledge_repo = KnowledgeRepositorySQLA(db_session, redis_client)

        # Act - Simulate concurrent updates
        async def update_knowledge(version):
            await knowledge_repo.update_knowledge("swap", {
                "content": {"version": version}
            })

        await asyncio.gather(
            update_knowledge(1),
            update_knowledge(2),
            update_knowledge(3)
        )

        # Assert - Final state should be consistent
        db_knowledge = await knowledge_repo.get_knowledge_by_key("swap")
        cached_knowledge = await redis_client.hget(
            "ai_brain:knowledge:swap:null:en", "content"
        )

        # Cache should either be None (invalidated) or match DB
        if cached_knowledge:
            assert json.loads(cached_knowledge) == db_knowledge.content

    async def test_stale_cache_detection(self, db_session, redis_client):
        """Test detecting stale cache entries"""
        # Arrange
        knowledge_repo = KnowledgeRepositorySQLA(db_session, redis_client)
        cache = RedisKnowledgeCache(redis_client, db_session)

        # Create and cache knowledge
        knowledge = await knowledge_repo.create_knowledge({
            "knowledge_key": "swap",
            "content": {"version": 1},
            "version": 1,
            ...
        })

        # Manually update DB without invalidating cache (simulate stale cache)
        await db_session.execute("""
            UPDATE agent_knowledge
            SET content = '{"version": 2}', version = 2
            WHERE knowledge_key = 'swap'
        """)

        # Act - Get knowledge with staleness check
        result = await knowledge_repo.get_knowledge_with_staleness_check("swap", None, "en")

        # Assert - Should detect staleness and reload from DB
        assert result.content["version"] == 2
        assert result.version == 2

    # Additional cache coherence tests omitted for brevity...
    # (15 more tests covering agent config cache, integration status cache, etc.)
```

**Test Coverage:**
- Knowledge cache coherence: 10 tests
- Agent config cache coherence: 8 tests
- Integration status cache coherence: 7 tests
- **Total: 25 tests**

---

### 7. Configuration Change → Cache Invalidation Flow (15 tests)

**Purpose:** Test end-to-end configuration change propagation

#### Test Suite: `test_config_change_propagation.py`

```python
"""
Integration tests for configuration change propagation
Location: tests/integration/test_config_change_propagation.py
"""

class TestConfigChangePropagation:
    """Test suite for configuration change → cache invalidation flow"""

    async def test_disable_agent_invalidates_related_caches(self, app_context):
        """Test that disabling an agent invalidates all related caches"""
        # Arrange
        config_service = app_context.config_service
        cache = app_context.cache

        # Cache agent config and related knowledge
        await cache.set_agent_config("swap_workflow", {"is_enabled": True}, 7200)
        await cache.set_knowledge("swap_overview", None, "en", {...}, 3600)

        # Act - Disable agent
        await config_service.disable_agent("swap_workflow")

        # Assert - All related caches invalidated
        assert await cache.get_agent_config("swap_workflow") is None
        assert await cache.get_knowledge("swap_overview", None, "en") is None

    async def test_integration_goes_down_invalidates_dependent_knowledge(self, app_context):
        """Test that integration failure invalidates dependent knowledge"""
        # Arrange
        integration_service = app_context.integration_health_service
        cache = app_context.cache

        # Cache knowledge that depends on Hyperliquid
        await cache.set_knowledge("swap_hyperliquid", None, "en", {
            "depends_on": ["hyperliquid"],
            ...
        }, 3600)

        # Act - Mark Hyperliquid as down
        await integration_service.update_health_status("hyperliquid", "down")

        # Assert - Dependent knowledge invalidated
        assert await cache.get_knowledge("swap_hyperliquid", None, "en") is None

    async def test_configuration_change_propagates_within_100ms(self, app_context):
        """Test that config changes propagate to cache within 100ms"""
        # Arrange
        config_service = app_context.config_service
        cache = app_context.cache

        await cache.set_agent_config("knowledge", {"is_enabled": True}, 7200)

        # Act
        start_time = time.time()
        await config_service.update_agent_config("knowledge", {"is_enabled": False})

        # Check cache invalidation
        cached = await cache.get_agent_config("knowledge")
        end_time = time.time()

        # Assert
        assert cached is None
        assert (end_time - start_time) < 0.1  # < 100ms

    # Additional propagation tests omitted for brevity...
    # (12 more tests covering various propagation scenarios)
```

**Test Coverage: 15 tests**

---

## Security Tests

### 8. Admin Authorization Tests (30 tests)

**Purpose:** Ensure only admins can modify configurations

#### Test Suite: `test_admin_authorization.py`

```python
"""
Security tests for admin authorization on all endpoints
Location: tests/security/test_admin_authorization.py
"""

class TestAdminAuthorization:
    """Test suite for admin-only endpoint access control"""

    # AGENT CONFIGURATION ENDPOINTS (8 tests)

    async def test_create_agent_config_requires_admin(self, client, guest_token):
        """Test that guest users cannot create agent config"""
        # Arrange
        headers = {"Authorization": f"Bearer {guest_token}"}

        # Act
        response = await client.post(
            "/api/v1/admin/agents/configurations",
            json={"agent_type": "test", ...},
            headers=headers
        )

        # Assert
        assert response.status_code == 403
        assert "Forbidden" in response.json()["detail"]

    async def test_update_agent_config_requires_admin(self, client, authenticated_token):
        """Test that authenticated users cannot update agent config"""
        # Arrange
        headers = {"Authorization": f"Bearer {authenticated_token}"}

        # Act
        response = await client.patch(
            "/api/v1/admin/agents/configurations/knowledge",
            json={"is_enabled": False},
            headers=headers
        )

        # Assert
        assert response.status_code == 403

    async def test_delete_agent_config_requires_admin(self, client, premium_token):
        """Test that premium users cannot delete agent config"""
        # Arrange
        headers = {"Authorization": f"Bearer {premium_token}"}

        # Act
        response = await client.delete(
            "/api/v1/admin/agents/configurations/test_agent",
            headers=headers
        )

        # Assert
        assert response.status_code == 403

    async def test_admin_can_create_agent_config(self, client, admin_token):
        """Test that admin users can create agent config"""
        # Arrange
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Act
        response = await client.post(
            "/api/v1/admin/agents/configurations",
            json={
                "agent_type": "test_agent",
                "agent_name": "Test Agent",
                "agent_category": "core",
                ...
            },
            headers=headers
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["agent_type"] == "test_agent"

    # Similar tests for other agent config endpoints...

    # KNOWLEDGE ENDPOINTS (10 tests)

    async def test_create_knowledge_requires_admin(self, client, guest_token):
        """Test that guest users cannot create knowledge"""
        # Implementation similar to above
        pass

    async def test_update_knowledge_requires_admin(self, client, authenticated_token):
        """Test that authenticated users cannot update knowledge"""
        pass

    # PROMPT ENDPOINTS (6 tests)

    async def test_create_prompt_requires_admin(self, client, guest_token):
        """Test that guest users cannot create prompts"""
        pass

    # INTEGRATION CONFIG ENDPOINTS (6 tests)

    async def test_update_integration_config_requires_admin(self, client, authenticated_token):
        """Test that non-admins cannot update integration config"""
        pass
```

**Test Coverage:**
- Agent configuration endpoints: 8 tests
- Knowledge endpoints: 10 tests
- Prompt endpoints: 6 tests
- Integration config endpoints: 6 tests
- **Total: 30 tests**

---

## End-to-End Tests

### 9. Complete Knowledge Injection Workflow (10 tests)

**Purpose:** Test the full knowledge injection workflow from user query to agent response

#### Test Suite: `test_knowledge_injection_e2e.py`

```python
"""
E2E tests for complete knowledge injection workflow
Location: tests/e2e/test_knowledge_injection_e2e.py
"""

class TestKnowledgeInjectionE2E:
    """E2E test suite for knowledge injection workflow"""

    async def test_guest_swap_query_full_workflow(self, app_context):
        """Test complete workflow: Guest user asks about swap"""
        # Arrange
        user_query = "Can I swap 100 USDC to PURR?"
        user_type = "guest"

        # Act - Complete workflow
        # 1. Intent detection
        intent = await app_context.intent_detector.detect(user_query)
        assert intent.detected_intent == "SWAP"

        # 2. Get knowledge
        knowledge = await app_context.knowledge_injector.get_knowledge_for_intent(
            user_query=user_query,
            detected_intent="SWAP",
            user_type=user_type
        )

        # 3. Verify knowledge is guest-appropriate
        assert knowledge is not None
        assert "sign in" in knowledge.get("description", "").lower()

        # 4. Agent response
        response = await app_context.chat_agent.generate_response(
            user_query=user_query,
            knowledge=knowledge,
            user_type=user_type
        )

        # Assert - Response should guide guest to sign in
        assert "sign in" in response.lower() or "login" in response.lower()
        assert "swap" in response.lower()

    async def test_authenticated_user_swap_with_hyperliquid_healthy(self, app_context):
        """Test workflow: Authenticated user with Hyperliquid available"""
        # Similar structure to above, but with authenticated user
        # and verifying Hyperliquid is mentioned
        pass

    async def test_swap_workflow_when_hyperliquid_down(self, app_context):
        """Test workflow: Swap query when Hyperliquid is down"""
        # Arrange
        user_query = "Swap 100 USDC to PURR"
        user_type = "authenticated"

        # Mark Hyperliquid as down
        await app_context.integration_health_service.update_health_status(
            "hyperliquid", "down"
        )

        # Act
        knowledge = await app_context.knowledge_injector.get_knowledge_for_intent(
            user_query=user_query,
            detected_intent="SWAP",
            user_type=user_type
        )

        # Assert - Should use fallback knowledge (1inch)
        assert "1inch" in str(knowledge).lower()
        assert "hyperliquid" not in str(knowledge).lower()

    # Additional E2E workflow tests...
    # (7 more tests covering different scenarios)
```

**Test Coverage: 10 tests**

---

## Test Implementation Plan

### Week 1-2: P0 Critical Tests (110 tests)

**Priority:** Repository unit tests + Security authorization tests

| Component | Tests | Priority | Owner |
|-----------|-------|----------|-------|
| AgentConfigRepository | 15 | P0 | Backend Team |
| KnowledgeRepository | 20 | P0 | Backend Team |
| PromptRepository | 12 | P0 | Backend Team |
| IntegrationRepository | 10 | P0 | Backend Team |
| RedisKnowledgeCache | 15 | P0 | Backend Team |
| Admin Authorization | 30 | P0 | Security Team |
| Configuration Impact | 8 | P0 | Integration Team |

**Deliverables:**
- 110 passing unit + security tests
- Test coverage reports (>90% for P0 components)
- Security audit sign-off

---

### Week 3-4: P1 High Priority Tests (90 tests)

**Priority:** Integration tests + Cache coherence tests

| Component | Tests | Priority | Owner |
|-----------|-------|----------|-------|
| KnowledgeInjector | 18 | P1 | Backend Team |
| ConfigurationService | 20 | P1 | Backend Team |
| IntegrationHealthService | 12 | P1 | Integration Team |
| Cache Coherence | 25 | P1 | Backend Team |
| Config Change Propagation | 15 | P1 | Integration Team |

**Deliverables:**
- 90 passing integration tests
- Cache coherence validation
- Performance benchmarks for cache hit rates

---

### Week 5: P2 Medium Priority Tests (151 tests)

**Priority:** E2E tests + Performance tests

| Component | Tests | Priority | Owner |
|-----------|-------|----------|-------|
| E2E Knowledge Injection | 10 | P2 | QA Team |
| E2E Admin Actions | 15 | P2 | QA Team |
| E2E Context-Aware Delivery | 12 | P2 | QA Team |
| Row-Level Security | 15 | P2 | Security Team |
| SQL Injection Prevention | 12 | P2 | Security Team |
| Performance Benchmarks | 15 | P2 | Performance Team |
| Admin API Endpoints | 25 | P2 | Backend Team |
| Cache Invalidation | 22 | P2 | Backend Team |
| Additional Integration Tests | 25 | P2 | Integration Team |

**Deliverables:**
- 151 passing E2E + performance tests
- Load test results (1M requests/hour)
- Security penetration test report

---

## Success Metrics

### Test Coverage Goals

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Overall Test Coverage** | 95% | 0% (new module) | 🔵 Design Phase |
| **Unit Test Coverage** | 95% | 0% | 🔵 Design Phase |
| **Integration Test Coverage** | 90% | 0% | 🔵 Design Phase |
| **E2E Test Coverage** | 100% critical workflows | 0% | 🔵 Design Phase |
| **Security Test Coverage** | 100% endpoints | 0% | 🔵 Design Phase |

### Test Execution Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Test Execution Time** | <5 minutes | All tests should run in <5 min |
| **Flaky Test Rate** | <1% | Tests should be deterministic |
| **Test Failure Rate** | <5% | High test stability |
| **Code Review Coverage** | 100% | All tests reviewed |

### Quality Gates

**Before Production Deployment:**
- [ ] 95%+ overall test coverage
- [ ] All P0 tests passing (110 tests)
- [ ] All P1 tests passing (90 tests)
- [ ] Security audit approved (all 57 security tests passing)
- [ ] Performance benchmarks met (>90% cache hit rate, <50ms p95 latency)
- [ ] Load test passed (1M requests/hour)
- [ ] Zero critical bugs
- [ ] Test execution time <5 minutes

---

## Appendix: Test Data

### Sample Test Data Factories

```python
"""
Test data factories for AI Brain module
Location: tests/factories.py
"""

async def seed_agent_config(
    agent_type: str,
    **overrides
) -> AgentConfiguration:
    """Factory for creating test agent configurations"""
    defaults = {
        "agent_name": f"{agent_type.replace('_', ' ').title()} Agent",
        "agent_category": "core",
        "is_enabled": True,
        "model_name": "gemini-2.0-flash",
        "temperature": 0.7,
        "max_tokens": 1500,
        "depends_on_integrations": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    data = {**defaults, **overrides}

    return await db.execute("""
        INSERT INTO agent_configurations (agent_type, ...)
        VALUES (:agent_type, ...)
        RETURNING *
    """, {"agent_type": agent_type, **data})

async def seed_knowledge(
    knowledge_key: str,
    **overrides
) -> AgentKnowledge:
    """Factory for creating test knowledge entries"""
    defaults = {
        "knowledge_category": "feature",
        "agent_types": ["knowledge", "chat"],
        "intent_patterns": [knowledge_key.upper()],
        "title": f"{knowledge_key.replace('_', ' ').title()}",
        "description": f"Test knowledge for {knowledge_key}",
        "content": {"test": True},
        "user_type": None,
        "language": "en",
        "depends_on_integrations": [],
        "is_enabled": True,
        "created_at": datetime.utcnow()
    }
    data = {**defaults, **overrides}

    return await db.execute("""
        INSERT INTO agent_knowledge (knowledge_key, ...)
        VALUES (:knowledge_key, ...)
        RETURNING *
    """, {"knowledge_key": knowledge_key, **data})

async def seed_integration(
    integration_key: str,
    **overrides
) -> IntegrationConfiguration:
    """Factory for creating test integration configurations"""
    defaults = {
        "integration_name": f"{integration_key.title()} Integration",
        "integration_type": "exchange",
        "is_enabled": True,
        "health_status": "healthy",
        "api_endpoint": f"https://api.{integration_key}.xyz",
        "rate_limit_per_minute": 60,
        "impacts_features": ["swap"],
        "impacts_agents": ["swap_workflow"],
        "created_at": datetime.utcnow()
    }
    data = {**defaults, **overrides}

    return await db.execute("""
        INSERT INTO integration_configurations (integration_key, ...)
        VALUES (:integration_key, ...)
        RETURNING *
    """, {"integration_key": integration_key, **data})
```

---

**END OF DOCUMENT**

**Total Test Count:** 351 tests
**Estimated Implementation Time:** 5 weeks
**Test Coverage Target:** 95%+
**Status:** Test Specification Complete

**Next Steps:**
1. Review and approve test specification
2. Set up test infrastructure (databases, Redis)
3. Begin Week 1-2 implementation (P0 tests)
4. Establish CI/CD pipeline for automated testing
5. Weekly test coverage reviews

**Questions? Contact:**
- Senior Code Reviewer: Claude Sonnet 4.5
- QA Lead: [QA Team Lead]
- Security Team: [Security Lead]
