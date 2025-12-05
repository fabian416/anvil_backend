"""
Chat router for conversation and message endpoints.
"""

from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status, Security
from fastapi.exceptions import HTTPException

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.common.services.current_user import CurrentUserService
from app.application.agent_squad.commands.send_agent_squad_message import SendAgentSquadMessage
from app.application.agent_squad.commands.execute_supervisor_workflow import ExecuteSupervisorWorkflow
from app.application.agent_squad.queries.get_enabled_agents import GetEnabledAgents
from app.presentation.http.schemas.chat import (
    CreateConversationRequest,
    ConversationResponse,
    SendMessageRequest,
    SendMessageResponse,
    ConversationListResponse,
    MessageListResponse,
    # NEW: GraphRAG and ML schemas
    ChatProtocolSearchRequest,
    ChatProtocolSearchResponse,
    ChatRiskAnalysisRequest,
    ChatRiskAnalysisResponse,
    ChatSimilarProtocolsRequest,
    ChatSimilarProtocolsResponse,
    # NEW: Agent Squad schemas
    AgentSquadMessageRequest,
    AgentSquadMessageResponse,
    SupervisorWorkflowRequest,
    SupervisorWorkflowResponse,
    ListEnabledAgentsResponse,
)
from app.application.chat.commands.create_conversation import CreateConversation
from app.application.chat.commands.send_message import SendMessage
from app.application.chat.queries.get_conversation import GetConversation
from app.application.chat.queries.list_conversations import ListConversations
from app.application.chat.queries.get_messages import GetMessages
# NEW: GraphRAG and ML handlers
from app.application.chat import (
    ChatGraphSearchHandler,
    ChatRiskInsightsHandler,
)


def create_chat_router() -> APIRouter:
    router = APIRouter(
        prefix="/chat",
        tags=["chat"],
    )
    
    @router.post(
        "/conversations",
        status_code=status.HTTP_201_CREATED,
        response_model=ConversationResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def create_conversation(
        request: CreateConversationRequest,
        current_user: FromDishka[CurrentUserService],
        interactor: FromDishka[CreateConversation],
    ) -> ConversationResponse:
        """
        Create a new conversation.
        
        Requires authentication.
        """
        user = await current_user.get_current_user()
        conversation = await interactor.execute(
            user_id=user.id,
            title=request.title,
        )
        
        return ConversationResponse.model_validate(conversation)
    
    @router.get(
        "/conversations",
        status_code=status.HTTP_200_OK,
        response_model=ConversationListResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def list_conversations(
        current_user: FromDishka[CurrentUserService],
        limit: int = 20,
        offset: int = 0,
        interactor: FromDishka[ListConversations] = None,
    ) -> ConversationListResponse:
        """
        List conversations for the authenticated user.
        
        Supports pagination via limit and offset.
        """
        user = await current_user.get_current_user()
        conversations = await interactor.execute(
            user_id=user.id,
            limit=limit,
            offset=offset,
        )
        
        return ConversationListResponse(
            conversations=[
                ConversationResponse.model_validate(c) for c in conversations
            ],
            total=len(conversations),
        )
    
    @router.get(
        "/conversations/{conversation_id}",
        status_code=status.HTTP_200_OK,
        response_model=ConversationResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_conversation(
        conversation_id: UUID,
        current_user: FromDishka[CurrentUserService],
        interactor: FromDishka[GetConversation],
    ) -> ConversationResponse:
        """
        Get a specific conversation.
        
        Returns 404 if not found or not owned by user.
        """
        user = await current_user.get_current_user()
        conversation = await interactor.execute(
            user_id=user.id,
            conversation_id=conversation_id,
        )
        
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        return ConversationResponse.model_validate(conversation)
    
    @router.post(
        "/conversations/{conversation_id}/messages",
        status_code=status.HTTP_201_CREATED,
        response_model=SendMessageResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def send_message(
        conversation_id: UUID,
        request: SendMessageRequest,
        current_user: FromDishka[CurrentUserService],
        interactor: FromDishka[SendMessage],
    ) -> SendMessageResponse:
        """
        Send a message in a conversation.
        
        Returns both the user message and the agent response.
        """
        user = await current_user.get_current_user()
        user_message, agent_message = await interactor.execute(
            user_id=user.id,
            conversation_id=conversation_id,
            content=request.content,
        )
        
        return SendMessageResponse(
            user_message=user_message,
            agent_message=agent_message,
        )
    
    @router.get(
        "/conversations/{conversation_id}/messages",
        status_code=status.HTTP_200_OK,
        response_model=MessageListResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_messages(
        conversation_id: UUID,
        current_user: FromDishka[CurrentUserService],
        limit: int = 50,
        interactor: FromDishka[GetMessages] = None,
    ) -> MessageListResponse:
        """
        Get messages for a conversation.
        
        Messages are returned in chronological order (oldest first).
        """
        user = await current_user.get_current_user()
        messages = await interactor.execute(
            user_id=user.id,
            conversation_id=conversation_id,
            limit=limit,
        )
        
        return MessageListResponse(
            messages=messages,
            total=len(messages),
        )
    
    # NEW: GraphRAG protocol search from chat
    @router.post(
        "/search-protocols",
        status_code=status.HTTP_200_OK,
        response_model=ChatProtocolSearchResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def search_protocols_from_chat(
        request: ChatProtocolSearchRequest,
        current_user: FromDishka[CurrentUserService],
        search_handler: FromDishka[ChatGraphSearchHandler],
    ) -> ChatProtocolSearchResponse:
        """
        Search protocols using GraphRAG hybrid search from chat context.
        
        Returns protocol results with risk scores, relevance explanations,
        and contextual recommendations.
        """
        user = await current_user.get_current_user()
        
        # Get user preferences (would come from user profile in production)
        user_preferences = request.user_preferences or {}
        
        # Perform search
        search_context = await search_handler.search_protocols_from_chat(
            message=request.query,
            user_preferences=user_preferences,
            conversation_id=request.conversation_id,
        )
        
        return ChatProtocolSearchResponse(
            results=[
                {
                    "protocol_id": str(r.protocol_id),
                    "protocol_name": r.protocol_name,
                    "similarity_score": r.similarity_score,
                    "risk_score": r.risk_score,
                    "risk_level": r.risk_level,
                    "tvl": r.tvl,
                    "apy": r.apy,
                    "audit_count": r.audit_count,
                    "description": r.description,
                    "category": r.category,
                    "chain": r.chain,
                    "why_relevant": r.why_relevant,
                }
                for r in search_context.results
            ],
            search_context=search_context.search_explanation,
            recommendations=search_context.recommendations,
        )
    
    # NEW: Get risk analysis for protocol mentioned in chat
    @router.post(
        "/analyze-risk",
        status_code=status.HTTP_200_OK,
        response_model=ChatRiskAnalysisResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def analyze_protocol_risk_from_chat(
        request: ChatRiskAnalysisRequest,
        current_user: FromDishka[CurrentUserService],
        risk_handler: FromDishka[ChatRiskInsightsHandler],
    ) -> ChatRiskAnalysisResponse:
        """
        Get ML-powered risk analysis for a protocol mentioned in chat.
        
        Returns risk scores, contributing factors, recommendations,
        and safer alternatives if risk is high.
        """
        user = await current_user.get_current_user()
        
        # Get risk insights
        insights = await risk_handler.get_protocol_risk_from_chat(
            protocol_name=request.protocol_name,
            conversation_id=request.conversation_id,
            operation_type=request.operation_type,
            amount_usd=request.amount_usd,
        )
        
        return ChatRiskAnalysisResponse(
            risk_analysis={
                "protocol_id": str(insights.risk_analysis.protocol_id),
                "protocol_name": insights.risk_analysis.protocol_name,
                "risk_score": insights.risk_analysis.risk_score,
                "risk_level": insights.risk_analysis.risk_level,
                "confidence": insights.risk_analysis.confidence,
                "contributing_factors": [
                    {
                        "factor": f.factor,
                        "impact": f.impact,
                        "description": f.description,
                        "is_critical": f.is_critical,
                    }
                    for f in insights.risk_analysis.contributing_factors
                ],
                "recommendations": insights.risk_analysis.recommendations,
                "should_warn": insights.risk_analysis.should_warn,
                "warning_message": insights.risk_analysis.warning_message,
            },
            alternatives=[
                {
                    "protocol_id": str(a.protocol_id),
                    "protocol_name": a.protocol_name,
                    "similarity_score": a.similarity_score,
                    "risk_score": a.risk_score,
                    "risk_level": a.risk_level,
                    "tvl": a.tvl,
                    "apy": a.apy,
                    "why_better": a.why_better,
                }
                for a in insights.alternatives
            ],
            contextual_message=insights.contextual_message,
        )
    
    # NEW: Get similar protocols from chat
    @router.post(
        "/similar-protocols",
        status_code=status.HTTP_200_OK,
        response_model=ChatSimilarProtocolsResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_similar_protocols_from_chat(
        request: ChatSimilarProtocolsRequest,
        current_user: FromDishka[CurrentUserService],
        search_handler: FromDishka[ChatGraphSearchHandler],
    ) -> ChatSimilarProtocolsResponse:
        """
        Find similar protocols using GraphRAG hybrid search.
        
        Returns protocols with high semantic and graph similarity,
        useful for discovering alternatives and related protocols.
        """
        user = await current_user.get_current_user()
        
        # Search for the base protocol first
        base_search = await search_handler.search_protocols_from_chat(
            message=request.protocol_name,
            conversation_id=request.conversation_id,
        )
        
        if not base_search.results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Protocol '{request.protocol_name}' not found",
            )
        
        base_protocol = base_search.results[0]
        
        # Find similar protocols
        similar_query = f"protocols similar to {request.protocol_name}"
        similar_search = await search_handler.search_protocols_from_chat(
            message=similar_query,
            conversation_id=request.conversation_id,
        )
        
        # Filter out the base protocol itself
        similar_protocols = [
            r for r in similar_search.results 
            if r.protocol_id != base_protocol.protocol_id
        ][:request.limit or 5]
        
        return ChatSimilarProtocolsResponse(
            base_protocol={
                "protocol_id": str(base_protocol.protocol_id),
                "protocol_name": base_protocol.protocol_name,
                "risk_score": base_protocol.risk_score,
                "risk_level": base_protocol.risk_level,
                "tvl": base_protocol.tvl,
                "category": base_protocol.category,
            },
            similar_protocols=[
                {
                    "protocol_id": str(p.protocol_id),
                    "protocol_name": p.protocol_name,
                    "similarity_score": p.similarity_score,
                    "risk_score": p.risk_score,
                    "risk_level": p.risk_level,
                    "tvl": p.tvl,
                    "why_similar": p.why_relevant,
                }
                for p in similar_protocols
            ],
        )
    
    # ========================================
    # Agent Squad Endpoints
    # ========================================
    
    @router.post(
        "/agent-squad/messages",
        status_code=status.HTTP_201_CREATED,
        response_model=AgentSquadMessageResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def send_agent_squad_message(
        conversation_id: UUID,
        request: AgentSquadMessageRequest,
        current_user: FromDishka[CurrentUserService],
        interactor: FromDishka["SendAgentSquadMessage"],
    ) -> AgentSquadMessageResponse:
        """
        Send message with Agent Squad intelligent routing.
        
        Features:
        - Automatic intent classification
        - Route to best specialist agent (18 agents)
        - Context preservation across turns
        - Telemetry tracking
        
        Optional: Force specific agent via force_agent parameter
        """
        user = await current_user.get_current_user()
        
        # Execute command
        result = await interactor.execute(
            conversation_id=conversation_id,
            user_id=user.id,
            content=request.content,
            force_agent=request.force_agent,
        )
        
        return AgentSquadMessageResponse(**result)
    
    @router.post(
        "/agent-squad/supervisor",
        status_code=status.HTTP_201_CREATED,
        response_model=SupervisorWorkflowResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def execute_supervisor_workflow(
        conversation_id: UUID,
        request: SupervisorWorkflowRequest,
        current_user: FromDishka[CurrentUserService],
        interactor: FromDishka["ExecuteSupervisorWorkflow"],
    ) -> SupervisorWorkflowResponse:
        """
        Execute complex multi-agent workflow.
        
        Features:
        - Supervisor coordinates multiple agents
        - Break complex task into subtasks
        - Parallel agent execution
        - Result aggregation
        - Dependency management
        
        Example: "Create balanced DeFi portfolio"
        -> Research agent: Find protocols
        -> Risk agent: Assess risks
        -> Portfolio agent: Create allocation
        -> Chat agent: Summarize
        """
        user = await current_user.get_current_user()
        
        # Execute command
        result = await interactor.execute(
            conversation_id=conversation_id,
            user_id=user.id,
            complex_task=request.complex_task,
            max_agents=request.max_agents or 5,
        )
        
        return SupervisorWorkflowResponse(**result)
    
    @router.get(
        "/agent-squad/agents",
        status_code=status.HTTP_200_OK,
        response_model=ListEnabledAgentsResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def list_enabled_agents(
        current_user: FromDishka[CurrentUserService],
        interactor: FromDishka["GetEnabledAgents"],
        user_subscription_tier: str | None = None,
    ) -> ListEnabledAgentsResponse:
        """
        List all enabled agents for current user.
        
        Returns:
        - All enabled agents (based on subscription tier)
        - Agent capabilities (model, temperature, etc.)
        - Core vs enterprise classification
        
        Tiers:
        - Free: 5 agents (chat, hunter_ai, research, portfolio, gas_optimizer)
        - Pro: 10 agents (all core user-facing)
        - Enterprise: 18 agents (all agents including enterprise/advanced)
        """
        # Get user for subscription tier check (if needed)
        # user = await current_user.get_current_user()
        # user_subscription_tier = user.subscription_tier  # TODO: Add to user model
        
        # Execute query
        result = await interactor.execute(
            user_subscription_tier=user_subscription_tier,
        )
        
        return ListEnabledAgentsResponse(**result)
    
    return router
