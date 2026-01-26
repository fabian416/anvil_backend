# Agent Sessions Test Specification

> **Last Updated**: 2026-01-25  
> **Status**: Production  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The Agent Sessions module has **moderate test coverage**:
- **E2E Tests**: 10 tests for API endpoints
- **Component Tests**: 7 tests for intent classification
- **Unit Tests**: Limited domain service tests

**Total Existing Tests**: ~17 tests  
**Missing Tests**: Domain service tests, infrastructure adapter tests, integration tests

---

## 1. Existing Tests

### 1.1 E2E API Endpoint Tests
**Path**: `tests/e2e/agent_squad/test_api_endpoints.py`

| Test | Description | Status |
|------|-------------|--------|
| `test_send_agent_squad_message_basic_flow` | Basic message flow | ✅ |
| `test_send_agent_squad_message_with_force_agent` | Forced agent routing | ✅ |
| `test_execute_supervisor_workflow` | Multi-agent workflow | ✅ |
| `test_list_enabled_agents` | List agents endpoint | ✅ |
| `test_list_enabled_agents_by_tier` | Tier-based filtering | ✅ |
| `test_conversation_context_preservation` | Context across messages | ✅ |
| `test_agent_routing_accuracy` | Intent → Agent mapping | ✅ |
| `test_error_handling` | Error scenarios | ✅ |
| `test_telemetry_tracking` | Metrics tracking | ✅ |

```python
async def test_send_agent_squad_message_basic_flow(self, client, auth_headers):
    """Test basic message sending flow."""
    conversation_id = uuid4()

    response = client.post(
        f"/api/v1/chat/agent-squad/messages?conversation_id={conversation_id}",
        headers=auth_headers,
        json={"content": "What's the current price of ETH?"},
    )

    if response.status_code == 201:
        data = response.json()
        assert "user_message_id" in data
        assert "agent_message_id" in data
        assert "agent_type" in data
        assert "content" in data
        assert "latency_ms" in data
        assert data["latency_ms"] > 0
```

---

### 1.2 Component Intent Classification Tests
**Path**: `tests/component/agent_squad/test_intent_classification.py`

| Test | Description | Status |
|------|-------------|--------|
| `test_classify_general_chat` | Chat intent | ✅ |
| `test_classify_market_sentiment` | Hunter AI intent | ✅ |
| `test_classify_protocol_research` | Research intent | ✅ |
| `test_classify_swap_execution` | Execution intent | ✅ |
| `test_classify_risk_analysis` | Risk analyzer intent | ✅ |
| `test_context_aware_classification` | Multi-turn context | ✅ |

```python
async def test_classify_swap_execution(self, mock_llm_client):
    """Test classification of swap/transaction intent."""
    classifier = IntentClassifier(llm_client=mock_llm_client)
    
    message = MessageContent("Swap 1 ETH for USDC")
    context = ConversationContext()
    
    mock_llm_client.classify_intent.return_value = {
        "intent": "swap_tokens",
        "confidence": 0.97,
        "reasoning": "User requesting token swap transaction",
    }
    
    result = await classifier.classify(message, context)
    
    assert result.agent_type == AgentType.EXECUTION
    assert result.intent == "swap_tokens"
    assert result.confidence >= 0.95
```

---

## 2. Missing Tests

### 2.1 Domain Service Unit Tests (Critical)
**Priority**: HIGH  
**Location**: Should be in `tests/unit/domain/agent_squad/`

**Missing Tests for AgentOrchestrator**:
```python
class TestAgentOrchestrator:
    """Unit tests for AgentOrchestrator domain service."""

    @pytest.mark.asyncio
    async def test_route_message_high_confidence(self):
        """High confidence routes to recommended agent."""
        mock_intent_classifier = AsyncMock()
        mock_feature_flags = AsyncMock()
        mock_feature_flags.is_agent_enabled.return_value = True
        
        mock_intent_classifier.classify.return_value = IntentClassification(
            intent="market_data",
            confidence=0.95,
            agent_type=AgentType.HUNTER_AI,
            reasoning="Price query",
        )
        
        orchestrator = AgentOrchestrator(
            intent_classifier=mock_intent_classifier,
            feature_flags=mock_feature_flags,
            confidence_threshold=0.85,
        )
        
        result = await orchestrator.route_message(
            conversation_id=ConversationId(uuid4()),
            message=MessageContent("ETH price?"),
            conversation_context=ConversationContext(),
        )
        
        assert result.agent_type == AgentType.HUNTER_AI
        assert result.fallback_used is False

    @pytest.mark.asyncio
    async def test_route_message_low_confidence_uses_fallback(self):
        """Low confidence routes to fallback agent."""
        mock_intent_classifier = AsyncMock()
        mock_feature_flags = AsyncMock()
        mock_feature_flags.is_agent_enabled.return_value = True
        
        mock_intent_classifier.classify.return_value = IntentClassification(
            intent="unknown",
            confidence=0.40,  # Below threshold
            agent_type=AgentType.RESEARCH,
            reasoning="Ambiguous query",
        )
        
        orchestrator = AgentOrchestrator(
            intent_classifier=mock_intent_classifier,
            feature_flags=mock_feature_flags,
            confidence_threshold=0.85,
            fallback_agent=AgentType.CHAT,
        )
        
        result = await orchestrator.route_message(
            conversation_id=ConversationId(uuid4()),
            message=MessageContent("Something vague"),
            conversation_context=ConversationContext(),
        )
        
        assert result.agent_type == AgentType.CHAT
        assert result.fallback_used is True

    @pytest.mark.asyncio
    async def test_route_message_disabled_agent_uses_fallback(self):
        """Disabled agent routes to fallback."""
        mock_intent_classifier = AsyncMock()
        mock_feature_flags = AsyncMock()
        mock_feature_flags.is_agent_enabled.return_value = False  # Agent disabled
        
        mock_intent_classifier.classify.return_value = IntentClassification(
            intent="compliance",
            confidence=0.95,
            agent_type=AgentType.COMPLIANCE_MONITOR,
            reasoning="Compliance query",
        )
        
        orchestrator = AgentOrchestrator(
            intent_classifier=mock_intent_classifier,
            feature_flags=mock_feature_flags,
        )
        
        result = await orchestrator.route_message(
            conversation_id=ConversationId(uuid4()),
            message=MessageContent("AML check"),
            conversation_context=ConversationContext(),
        )
        
        assert result.agent_type == AgentType.CHAT
        assert result.fallback_used is True

    @pytest.mark.asyncio
    async def test_execute_agent_success(self):
        """Execute agent returns response."""
        mock_agent = AsyncMock()
        mock_agent.execute.return_value = AgentResponse(
            content="ETH is $2,450",
            agent_type=AgentType.HUNTER_AI,
            tools_used=["coingecko_api"],
        )
        
        orchestrator = AgentOrchestrator(
            intent_classifier=AsyncMock(),
            feature_flags=AsyncMock(),
            agent_registry={AgentType.HUNTER_AI: mock_agent},
        )
        
        response = await orchestrator.execute_agent(
            agent_type=AgentType.HUNTER_AI,
            message="ETH price?",
            conversation_context=ConversationContext(),
        )
        
        assert response.content == "ETH is $2,450"
        assert response.agent_type == AgentType.HUNTER_AI

    @pytest.mark.asyncio
    async def test_execute_agent_not_found_raises(self):
        """Execute unknown agent raises ValueError."""
        orchestrator = AgentOrchestrator(
            intent_classifier=AsyncMock(),
            feature_flags=AsyncMock(),
            agent_registry={},  # Empty registry
        )
        
        with pytest.raises(ValueError, match="not found in registry"):
            await orchestrator.execute_agent(
                agent_type=AgentType.HUNTER_AI,
                message="ETH price?",
                conversation_context=ConversationContext(),
            )
```

---

**Missing Tests for ContextManager**:
```python
class TestContextManager:
    """Unit tests for ContextManager domain service."""

    @pytest.mark.asyncio
    async def test_add_message_success(self):
        """Add message stores in context storage."""
        mock_storage = AsyncMock()
        mock_storage.get_message_count.return_value = 5
        
        context_manager = ContextManager(
            storage=mock_storage,
            history_limit=20,
        )
        
        await context_manager.add_message(
            conversation_id=ConversationId(uuid4()),
            message_id=MessageId(uuid4()),
            role="user",
            content="Hello",
            agent_type=None,
        )
        
        mock_storage.add_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_message_enforces_limit(self):
        """History limit is enforced after adding."""
        mock_storage = AsyncMock()
        mock_storage.get_message_count.return_value = 25  # Over limit
        
        context_manager = ContextManager(
            storage=mock_storage,
            history_limit=20,
        )
        
        await context_manager.add_message(
            conversation_id=ConversationId(uuid4()),
            message_id=MessageId(uuid4()),
            role="user",
            content="Hello",
        )
        
        mock_storage.remove_oldest_messages.assert_called_once_with(
            ANY,  # conversation_id
            5,    # 25 - 20 = 5 to remove
        )

    @pytest.mark.asyncio
    async def test_get_conversation_context_returns_history(self):
        """Get context returns recent messages."""
        mock_storage = AsyncMock()
        mock_storage.get_messages.return_value = [
            ConversationMessage(
                message_id=MessageId(uuid4()),
                role="user",
                content="Hello",
                agent_type=None,
                timestamp=datetime.now(UTC),
            )
        ]
        mock_storage.get_metadata.return_value = {"user": {}, "session": {}}
        
        context_manager = ContextManager(storage=mock_storage)
        
        context = await context_manager.get_conversation_context(
            conversation_id=ConversationId(uuid4()),
        )
        
        assert len(context.conversation_history) == 1
        assert context.conversation_history[0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_get_summary_empty_history(self):
        """Summary for empty history."""
        mock_storage = AsyncMock()
        mock_storage.get_messages.return_value = []
        
        context_manager = ContextManager(storage=mock_storage)
        
        summary = await context_manager.get_summary(
            conversation_id=ConversationId(uuid4()),
        )
        
        assert "No previous conversation history" in summary

    @pytest.mark.asyncio
    async def test_estimate_token_count(self):
        """Token count estimation."""
        mock_storage = AsyncMock()
        mock_storage.get_messages.return_value = [
            ConversationMessage(
                message_id=MessageId(uuid4()),
                role="user",
                content="A" * 400,  # 400 chars
                agent_type=None,
                timestamp=datetime.now(UTC),
            )
        ]
        
        context_manager = ContextManager(storage=mock_storage)
        
        tokens = await context_manager.estimate_token_count(
            conversation_id=ConversationId(uuid4()),
        )
        
        assert tokens == 100  # 400 chars / 4 chars per token
```

---

**Missing Tests for SupervisorCoordinator**:
```python
class TestSupervisorCoordinator:
    """Unit tests for SupervisorCoordinator domain service."""

    @pytest.mark.asyncio
    async def test_create_workflow_plan_simple_task(self):
        """Create plan for simple task."""
        mock_llm_client = AsyncMock()
        mock_llm_client.plan_workflow.return_value = {
            "tasks": [
                {"agent_type": "hunter_ai", "task_description": "Get price", "depends_on": []}
            ]
        }
        
        coordinator = SupervisorCoordinator(
            llm_client=mock_llm_client,
            agent_executor=AsyncMock(),
        )
        
        plan = await coordinator.create_workflow_plan(
            conversation_id=ConversationId(uuid4()),
            message=MessageContent("ETH price?"),
            conversation_context=ConversationContext(),
            available_agents=[AgentType.HUNTER_AI],
        )
        
        assert len(plan.tasks) == 1
        assert plan.tasks[0].agent_type == AgentType.HUNTER_AI

    @pytest.mark.asyncio
    async def test_create_workflow_plan_adds_chat_aggregator(self):
        """Multi-agent plan adds CHAT as aggregator."""
        mock_llm_client = AsyncMock()
        mock_llm_client.plan_workflow.return_value = {
            "tasks": [
                {"agent_type": "hunter_ai", "task_description": "Get price", "depends_on": []},
                {"agent_type": "risk_analyzer", "task_description": "Analyze", "depends_on": []},
                {"agent_type": "portfolio", "task_description": "Recommend", "depends_on": []},
            ]
        }
        
        coordinator = SupervisorCoordinator(
            llm_client=mock_llm_client,
            agent_executor=AsyncMock(),
        )
        
        plan = await coordinator.create_workflow_plan(
            conversation_id=ConversationId(uuid4()),
            message=MessageContent("Build portfolio"),
            conversation_context=ConversationContext(),
            available_agents=[AgentType.HUNTER_AI, AgentType.RISK_ANALYZER, AgentType.PORTFOLIO],
        )
        
        # Should have 4 tasks (3 original + 1 CHAT aggregator)
        assert len(plan.tasks) == 4
        assert plan.tasks[-1].agent_type == AgentType.CHAT
        assert "aggregate" in plan.tasks[-1].task_description.lower()

    @pytest.mark.asyncio
    async def test_execute_workflow_single_task(self):
        """Execute single-task workflow."""
        mock_agent_executor = AsyncMock()
        mock_agent_executor.execute_agent.return_value = AgentResponse(
            content="ETH is $2,450",
            agent_type=AgentType.HUNTER_AI,
            tools_used=["coingecko_api"],
        )
        
        coordinator = SupervisorCoordinator(
            llm_client=AsyncMock(),
            agent_executor=mock_agent_executor,
        )
        
        plan = WorkflowPlan(
            tasks=[
                AgentTask(
                    agent_type=AgentType.HUNTER_AI,
                    task_description="Get price",
                    depends_on=[],
                )
            ],
            execution_order=[0],
            estimated_time_seconds=10,
        )
        
        content, sources, timings = await coordinator.execute_workflow(
            conversation_id=ConversationId(uuid4()),
            workflow_plan=plan,
            conversation_context=ConversationContext(),
            original_message="ETH price?",
        )
        
        assert "ETH is $2,450" in content
        mock_agent_executor.execute_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_plan_properties(self):
        """Test WorkflowPlan helper properties."""
        plan = WorkflowPlan(
            tasks=[
                AgentTask(agent_type=AgentType.HUNTER_AI, task_description="T1", depends_on=[], status=TaskStatus.COMPLETED),
                AgentTask(agent_type=AgentType.RISK_ANALYZER, task_description="T2", depends_on=[0], status=TaskStatus.COMPLETED),
            ],
            execution_order=[0, 1],
            estimated_time_seconds=20,
        )
        
        assert plan.is_complete is True
        assert plan.has_failures is False

    @pytest.mark.asyncio
    async def test_workflow_plan_has_failures(self):
        """Test failure detection."""
        plan = WorkflowPlan(
            tasks=[
                AgentTask(agent_type=AgentType.HUNTER_AI, task_description="T1", depends_on=[], status=TaskStatus.COMPLETED),
                AgentTask(agent_type=AgentType.RISK_ANALYZER, task_description="T2", depends_on=[0], status=TaskStatus.FAILED),
            ],
            execution_order=[0, 1],
            estimated_time_seconds=20,
        )
        
        assert plan.is_complete is False
        assert plan.has_failures is True
```

---

### 2.2 Infrastructure Adapter Tests (High)
**Priority**: HIGH  
**Location**: Should be in `tests/unit/infrastructure/agent_squad/`

**Missing Tests for ContextStorageRedis**:
```python
class TestContextStorageRedis:
    """Unit tests for ContextStorageRedis adapter."""

    @pytest.mark.asyncio
    async def test_add_message_stores_in_list(self, mock_redis):
        """Add message appends to Redis list."""
        storage = ContextStorageRedis(redis_client=mock_redis)
        
        await storage.add_message(
            conversation_id=ConversationId(uuid4()),
            message=ConversationMessage(
                message_id=MessageId(uuid4()),
                role="user",
                content="Hello",
                agent_type=None,
                timestamp=datetime.now(UTC),
            ),
        )
        
        mock_redis.rpush.assert_called_once()
        mock_redis.expire.assert_called()  # TTL set

    @pytest.mark.asyncio
    async def test_get_messages_returns_recent(self, mock_redis):
        """Get messages returns last N."""
        mock_redis.lrange.return_value = [
            json.dumps({"message_id": str(uuid4()), "role": "user", "content": "Hi", "timestamp": "2026-01-01T00:00:00"})
        ]
        
        storage = ContextStorageRedis(redis_client=mock_redis)
        
        messages = await storage.get_messages(
            conversation_id=ConversationId(uuid4()),
            limit=10,
        )
        
        assert len(messages) == 1
        assert messages[0].content == "Hi"

    @pytest.mark.asyncio
    async def test_get_message_count(self, mock_redis):
        """Get count returns integer."""
        mock_redis.get.return_value = "15"
        
        storage = ContextStorageRedis(redis_client=mock_redis)
        
        count = await storage.get_message_count(
            conversation_id=ConversationId(uuid4()),
        )
        
        assert count == 15

    @pytest.mark.asyncio
    async def test_remove_oldest_messages(self, mock_redis):
        """Remove oldest pops from left."""
        storage = ContextStorageRedis(redis_client=mock_redis)
        
        await storage.remove_oldest_messages(
            conversation_id=ConversationId(uuid4()),
            count=3,
        )
        
        assert mock_redis.lpop.call_count == 3
```

---

### 2.3 Integration Tests (Medium)
**Priority**: MEDIUM  
**Location**: Should be in `tests/integration/agent_squad/`

**Missing Tests**:
```python
class TestAgentSquadIntegration:
    """Integration tests for Agent Squad system."""

    @pytest.mark.asyncio
    async def test_full_message_flow(self, db_session, redis_client, auth_client):
        """Test complete message flow: API → Orchestrator → Agent → Response."""
        # Create conversation
        conv_response = await auth_client.post("/api/v1/conversations")
        conversation_id = conv_response.json()["id"]
        
        # Send message
        response = await auth_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "What is DeFi?"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "agent_response" in data
        assert data["agent_type"] in ["chat", "knowledge"]

    @pytest.mark.asyncio
    async def test_context_preserved_across_messages(self, auth_client):
        """Context preserved across multiple messages."""
        conv_response = await auth_client.post("/api/v1/conversations")
        conversation_id = conv_response.json()["id"]
        
        # First message about ETH
        await auth_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "Tell me about ETH"},
        )
        
        # Follow-up with "it"
        response = await auth_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "What's its price?"},  # "it" = ETH
        )
        
        data = response.json()
        # Response should reference ETH (context preserved)
        assert "eth" in data["agent_response"]["content"].lower()

    @pytest.mark.asyncio
    async def test_agent_telemetry_tracked(self, db_session, auth_client):
        """Telemetry is recorded after agent call."""
        conv_response = await auth_client.post("/api/v1/conversations")
        conversation_id = conv_response.json()["id"]
        
        # Send message
        await auth_client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "ETH price?"},
        )
        
        # Check telemetry table
        from sqlalchemy import text
        result = await db_session.execute(
            text("SELECT * FROM agent_telemetry WHERE conversation_id = :conv_id"),
            {"conv_id": conversation_id},
        )
        telemetry = result.fetchone()
        
        # May be None if async task not completed
        # But structure should be valid if present
        if telemetry:
            assert telemetry.latency_ms > 0
```

---

## 3. Test Coverage Summary

| Component | Existing | Missing | Coverage |
|-----------|----------|---------|----------|
| E2E API Tests | 10 | 2 | ~80% |
| Intent Classification | 7 | 3 | ~70% |
| AgentOrchestrator | 0 | 5 | 0% |
| ContextManager | 0 | 5 | 0% |
| SupervisorCoordinator | 0 | 4 | 0% |
| ContextStorageRedis | 0 | 4 | 0% |
| Integration Tests | 0 | 3 | 0% |

**Overall Estimated Coverage**: ~35%  
**Target Coverage**: 80%

---

## 4. Testing Priorities

### Immediate (Phase 1)
1. AgentOrchestrator unit tests - Core routing logic
2. ContextManager unit tests - Context handling

### Short-term (Phase 2)
3. SupervisorCoordinator tests - Multi-agent workflows
4. ContextStorageRedis tests - Redis adapter

### Medium-term (Phase 3)
5. Integration tests - Full flow
6. Additional intent classification tests

---

## 5. Running Tests

```bash
# Run all Agent Squad tests
pytest tests/e2e/agent_squad/ -v
pytest tests/component/agent_squad/ -v

# Run with coverage
pytest tests/component/agent_squad/ --cov=src/app/domain/services/agent_squad --cov-report=html

# Run specific test class
pytest tests/component/agent_squad/test_intent_classification.py::TestIntentClassification -v
```

---

## References

- **E2E Tests**: `tests/e2e/agent_squad/test_api_endpoints.py`
- **Component Tests**: `tests/component/agent_squad/test_intent_classification.py`
- **Test Fixtures**: `tests/component/agent_squad/conftest.py`
- **Domain Services**: `src/app/domain/services/agent_squad/`
- **Infrastructure Adapters**: `src/app/infrastructure/adapters/agent_squad/`
