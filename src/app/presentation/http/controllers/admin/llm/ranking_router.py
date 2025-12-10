"""
Admin API Router for LLM Ranking Management.

Endpoints for viewing, recalculating, and overriding model rankings.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Security
from dishka.integrations.fastapi import FromDishka, inject

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.controllers.admin.llm.schemas import (
    # Responses
    AgentRankingsResponse,
    AllRankingsOverviewResponse,
    RecalculateResponse,
    OverrideResponse,
    RegisterModelResponse,
    ModelRankingResponse,
    AgentTypeOverview,
    # Requests
    SetOverrideRequest,
    RegisterVertexAIModelRequest,
    RegisterDeepInfraModelRequest,
)
from app.application.llm.ranking.get_rankings import (
    GetRankingsForAgent,
    GetAllRankingsOverview,
)
from app.application.llm.ranking.recalculate_agent_rankings import (
    RecalculateAgentRankings,
)
from app.application.llm.ranking.manage_overrides import (
    SetRankingOverride,
    RemoveRankingOverride,
)
from app.application.llm.ranking.register_model import (
    RegisterVertexAIModel,
    RegisterDeepInfraModel,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/llm",
    tags=["Admin - LLM Ranking"],
)


# ============================================================================
# Endpoint 1: GET /rankings/{agent_type} - View rankings
# ============================================================================


@router.get(
    "/rankings/{agent_type}",
    response_model=AgentRankingsResponse,
    summary="Get Rankings for Agent Type",
    description=(
        "View current model rankings for a specific agent type. "
        "Returns models sorted by ranking score with position numbers."
    ),
)
@inject
async def get_rankings(
    agent_type: str,
    authorization: str = Security(bearer_scheme),
    interactor: FromDishka[GetRankingsForAgent] = None,
):
    """Get rankings for specific agent type."""
    try:
        result = await interactor.execute(agent_type)

        return AgentRankingsResponse(
            agent_type=result.agent_type,
            total_models=len(result.models),
            models=[
                ModelRankingResponse(
                    model_id=m.ranking.model_id,
                    model_name=m.ranking.model_name,
                    provider_name=m.ranking.provider_name,
                    display_name=m.ranking.display_name,
                    ranking_score=m.ranking.ranking_score,
                    position=m.position,
                    success_rate=m.ranking.success_rate,
                    avg_latency_ms=m.ranking.avg_latency_ms,
                    avg_cost_per_request=m.ranking.avg_cost_per_request,
                    total_requests=m.ranking.total_requests,
                    successful_requests=m.ranking.successful_requests,
                    failed_requests=m.ranking.failed_requests,
                    last_used_at=m.ranking.last_used_at,
                    has_override=m.has_override,
                    override_reason=m.override_reason,
                )
                for m in result.models
            ],
            last_recalculated_at=result.last_recalculated_at,
        )

    except Exception as e:
        logger.error(f"Failed to get rankings for {agent_type}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rankings: {str(e)}",
        )


# ============================================================================
# Endpoint 2: GET /rankings - All processes overview
# ============================================================================


@router.get(
    "/rankings",
    response_model=AllRankingsOverviewResponse,
    summary="Get All Agent Types Overview",
    description=(
        "View overview of all agent types with their top models. "
        "Useful for dashboard display."
    ),
)
@inject
async def get_all_rankings_overview(
    authorization: str = Security(bearer_scheme),
    interactor: FromDishka[GetAllRankingsOverview] = None,
):
    """Get overview of all agent types."""
    try:
        overviews = await interactor.execute()

        return AllRankingsOverviewResponse(
            total_agent_types=len(overviews),
            agent_types=[
                AgentTypeOverview(
                    agent_type=o.agent_type,
                    total_models=o.total_models,
                    top_model=o.top_model,
                    top_model_score=o.top_model_score,
                    last_recalculated_at=o.last_recalculated_at,
                )
                for o in overviews
            ],
        )

    except Exception as e:
        logger.error(f"Failed to get rankings overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve overview: {str(e)}",
        )


# ============================================================================
# Endpoint 3: POST /rankings/{agent_type}/recalculate - Manual trigger
# ============================================================================


@router.post(
    "/rankings/{agent_type}/recalculate",
    response_model=RecalculateResponse,
    summary="Manually Recalculate Rankings",
    description=(
        "Trigger manual recalculation of rankings for a specific agent type. "
        "Analyzes last 24h of telemetry and updates scores."
    ),
)
@inject
async def recalculate_rankings(
    agent_type: str,
    authorization: str = Security(bearer_scheme),
    interactor: FromDishka[RecalculateAgentRankings] = None,
):
    """Manually trigger ranking recalculation."""
    try:
        result = await interactor.execute(agent_type, hours_to_analyze=24)

        return RecalculateResponse(
            agent_type=result.agent_type,
            models_evaluated=result.models_evaluated,
            models_updated=result.models_updated,
            changes_made=len(result.changes),
            recalculated_at=result.recalculated_at,
            success=True,
            message=f"Recalculated {result.models_updated} models",
        )

    except Exception as e:
        logger.error(
            f"Failed to recalculate rankings for {agent_type}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recalculation failed: {str(e)}",
        )


# ============================================================================
# Endpoint 4: PUT /rankings/{agent_type}/{model_id}/override - Force position
# ============================================================================


@router.put(
    "/rankings/{agent_type}/{model_id}/override",
    response_model=OverrideResponse,
    summary="Set Manual Ranking Override",
    description=(
        "Force a specific ranking score for a model in an agent type. "
        "Override expires after specified hours or is permanent if not set."
    ),
)
@inject
async def set_ranking_override(
    agent_type: str,
    model_id: UUID,
    request: SetOverrideRequest,
    authorization: str = Security(bearer_scheme),
    interactor: FromDishka[SetRankingOverride] = None,
):
    """Set manual ranking override."""
    try:
        result = await interactor.execute(
            agent_type=agent_type,
            model_id=model_id,
            override_score=float(request.override_score),
            reason=request.reason,
            expires_in_hours=request.expires_in_hours,
            created_by=None,  # TODO: Get from auth context
        )

        return OverrideResponse(
            agent_type=result.agent_type,
            model_id=result.model_id,
            model_name=result.model_name,
            action=result.action,
            override_score=request.override_score,
            expires_at=result.expires_at,
            success=True,
            message=f"Override {result.action} for {result.model_name}",
        )

    except Exception as e:
        logger.error(
            f"Failed to set override for {agent_type}/{model_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set override: {str(e)}",
        )


# ============================================================================
# Endpoint 5: DELETE /rankings/{agent_type}/{model_id}/override - Remove override
# ============================================================================


@router.delete(
    "/rankings/{agent_type}/{model_id}/override",
    response_model=OverrideResponse,
    summary="Remove Manual Ranking Override",
    description="Remove a manual ranking override and return to calculated scores.",
)
@inject
async def remove_ranking_override(
    agent_type: str,
    model_id: UUID,
    authorization: str = Security(bearer_scheme),
    interactor: FromDishka[RemoveRankingOverride] = None,
):
    """Remove manual ranking override."""
    try:
        result = await interactor.execute(
            agent_type=agent_type,
            model_id=model_id,
        )

        return OverrideResponse(
            agent_type=result.agent_type,
            model_id=result.model_id,
            model_name=result.model_name,
            action=result.action,
            success=True,
            message=f"Override removed for {result.model_name}",
        )

    except Exception as e:
        logger.error(
            f"Failed to remove override for {agent_type}/{model_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove override: {str(e)}",
        )


# ============================================================================
# Endpoint 6: POST /models/register/vertex-ai - Register Vertex AI model
# ============================================================================


@router.post(
    "/models/register/vertex-ai",
    response_model=RegisterModelResponse,
    summary="Register New Vertex AI Model",
    description=(
        "Register a new Vertex AI model. Automatically places at rank 1 "
        "with 24h override for initial metric collection."
    ),
)
@inject
async def register_vertex_ai_model(
    request: RegisterVertexAIModelRequest,
    authorization: str = Security(bearer_scheme),
    interactor: FromDishka[RegisterVertexAIModel] = None,
):
    """Register new Vertex AI model."""
    try:
        result = await interactor.execute(
            model_id=request.model_id,
            display_name=request.display_name,
            description=request.description,
            context_window=request.context_window,
            input_cost_per_1k=request.input_cost_per_1k,
            output_cost_per_1k=request.output_cost_per_1k,
            max_output_tokens=request.max_output_tokens,
            supports_streaming=request.supports_streaming,
            agent_types=request.agent_types,
            created_by=None,  # TODO: Get from auth context
        )

        return RegisterModelResponse(
            model_id=result.model_id,
            model_name=result.model_name,
            provider_name=result.provider_name,
            display_name=result.display_name,
            initial_ranking_score=result.initial_ranking_score,
            override_expires_at=result.override_expires_at,
            agent_types_registered=result.agent_types_registered,
            success=True,
            message=(
                f"Model {result.display_name} registered successfully. "
                f"Ranked #1 for 24h to collect metrics."
            ),
        )

    except Exception as e:
        logger.error(f"Failed to register Vertex AI model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


# ============================================================================
# Endpoint 7: POST /models/register/deepinfra - Register DeepInfra model
# ============================================================================


@router.post(
    "/models/register/deepinfra",
    response_model=RegisterModelResponse,
    summary="Register New DeepInfra Model",
    description=(
        "Register a new DeepInfra model. Automatically places at rank 1 "
        "with 24h override for initial metric collection."
    ),
)
@inject
async def register_deepinfra_model(
    request: RegisterDeepInfraModelRequest,
    authorization: str = Security(bearer_scheme),
    interactor: FromDishka[RegisterDeepInfraModel] = None,
):
    """Register new DeepInfra model."""
    try:
        result = await interactor.execute(
            model_id=request.model_id,
            display_name=request.display_name,
            description=request.description,
            context_window=request.context_window,
            input_cost_per_1k=request.input_cost_per_1k,
            output_cost_per_1k=request.output_cost_per_1k,
            max_output_tokens=request.max_output_tokens,
            supports_streaming=request.supports_streaming,
            agent_types=request.agent_types,
            created_by=None,  # TODO: Get from auth context
        )

        return RegisterModelResponse(
            model_id=result.model_id,
            model_name=result.model_name,
            provider_name=result.provider_name,
            display_name=result.display_name,
            initial_ranking_score=result.initial_ranking_score,
            override_expires_at=result.override_expires_at,
            agent_types_registered=result.agent_types_registered,
            success=True,
            message=(
                f"Model {result.display_name} registered successfully. "
                f"Ranked #1 for 24h to collect metrics."
            ),
        )

    except Exception as e:
        logger.error(f"Failed to register DeepInfra model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )
