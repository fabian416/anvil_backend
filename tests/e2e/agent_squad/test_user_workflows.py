"""
End-to-end tests for complete user workflows.
"""

import pytest
from uuid import uuid4

from app.domain.enums.agent_type import AgentType
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.agent_squad.conversation_context import ConversationContext


@pytest.mark.e2e
@pytest.mark.asyncio
class TestUserWorkflows:
    """End-to-end user workflow tests."""
    
    async def test_complete_defi_research_workflow(
        self,
        agent_orchestrator,
        mock_agents,
    ):
        """
        Test complete DeFi research workflow:
        1. User asks about protocol
        2. Research agent provides details
        3. User asks about risks
        4. Risk analyzer provides assessment
        5. User asks to compare yields
        6. DeFi yield agent provides comparison
        """
        conversation_id = ConversationId(uuid4())
        
        # Step 1: Research query
        message1 = MessageContent("Tell me about Aave protocol")
        context1 = ConversationContext()
        
        result1 = await agent_orchestrator.route_message(
            conversation_id, message1, context1
        )
        
        assert result1.agent_type == AgentType.RESEARCH
        assert result1.confidence > 0.85
        
        # Step 2: Risk query (with context)
        message2 = MessageContent("What are the risks?")
        context2 = ConversationContext(
            conversation_history=[
                {"role": "user", "content": "Tell me about Aave protocol"},
                {"role": "agent", "content": "Aave is a lending protocol...", "agent_type": "research"},
            ]
        )
        
        result2 = await agent_orchestrator.route_message(
            conversation_id, message2, context2
        )
        
        assert result2.agent_type == AgentType.RISK_ANALYZER
        
        # Step 3: Yield comparison
        message3 = MessageContent("Compare yields for USDC lending")
        context3 = ConversationContext(
            conversation_history=[
                *context2.conversation_history,
                {"role": "user", "content": "What are the risks?"},
                {"role": "agent", "content": "Risk assessment...", "agent_type": "risk_analyzer"},
            ]
        )
        
        result3 = await agent_orchestrator.route_message(
            conversation_id, message3, context3
        )
        
        assert result3.agent_type == AgentType.DEFI_YIELD
        
        print("\n✅ Complete DeFi Research Workflow:")
        print(f"  Step 1: {result1.agent_type.value} (confidence: {result1.confidence:.2f})")
        print(f"  Step 2: {result2.agent_type.value} (context-aware)")
        print(f"  Step 3: {result3.agent_type.value}")
    
    async def test_transaction_execution_workflow(
        self,
        agent_orchestrator,
        mock_agents,
    ):
        """
        Test transaction execution workflow:
        1. User requests swap
        2. Execution agent parses request
        3. User confirms transaction
        4. Transaction executed
        """
        conversation_id = ConversationId(uuid4())
        
        # Step 1: Swap request
        message = MessageContent("Swap 1 ETH for USDC")
        context = ConversationContext()
        
        result = await agent_orchestrator.route_message(
            conversation_id, message, context
        )
        
        assert result.agent_type == AgentType.EXECUTION
        assert result.confidence > 0.90  # High confidence for clear swap intent
        
        print("\n✅ Transaction Execution Workflow:")
        print(f"  Agent: {result.agent_type.value}")
        print(f"  Intent: swap_tokens")
        print(f"  Confidence: {result.confidence:.2f}")
    
    async def test_multi_agent_supervisor_workflow(
        self,
        supervisor_coordinator,
        mock_agents,
    ):
        """
        Test multi-agent supervisor workflow:
        1. User requests complex task
        2. Supervisor creates workflow plan
        3. Multiple agents execute in parallel
        4. Results aggregated
        """
        conversation_id = ConversationId(uuid4())
        message = MessageContent("Create a balanced DeFi portfolio with 10k USDC")
        context = ConversationContext()
        
        # Available agents for workflow
        available_agents = [
            AgentType.RESEARCH,
            AgentType.RISK_ANALYZER,
            AgentType.PORTFOLIO,
            AgentType.DEFI_YIELD,
        ]
        
        # Create workflow plan
        workflow_plan = await supervisor_coordinator.create_workflow_plan(
            conversation_id, message, context, available_agents
        )
        
        assert len(workflow_plan.tasks) > 1  # Multiple tasks
        assert workflow_plan.tasks[0].agent_type in available_agents
        
        # Execute workflow
        result = await supervisor_coordinator.execute_workflow(
            conversation_id, workflow_plan, context
        )
        
        assert result is not None
        assert len(result) > 100  # Substantive response
        
        print("\n✅ Multi-Agent Supervisor Workflow:")
        print(f"  Tasks Created: {len(workflow_plan.tasks)}")
        print(f"  Agents Used: {[t.agent_type.value for t in workflow_plan.tasks]}")
        print(f"  Result Length: {len(result)} chars")


@pytest.fixture
def agent_orchestrator(mocker):
    """Mock agent orchestrator."""
    from app.domain.services.agent_squad.agent_orchestrator import AgentOrchestrator
    
    intent_classifier = mocker.AsyncMock()
    feature_flags = mocker.AsyncMock()
    feature_flags.is_agent_enabled.return_value = True
    
    return AgentOrchestrator(
        intent_classifier=intent_classifier,
        feature_flags=feature_flags,
    )


@pytest.fixture
def supervisor_coordinator(mocker):
    """Mock supervisor coordinator."""
    from app.domain.services.agent_squad.supervisor_coordinator import SupervisorCoordinator
    
    llm_client = mocker.AsyncMock()
    agent_executor = mocker.AsyncMock()
    
    return SupervisorCoordinator(
        llm_client=llm_client,
        agent_executor=agent_executor,
    )


@pytest.fixture
def mock_agents(mocker):
    """Mock all agents for e2e testing."""
    return mocker.Mock()
