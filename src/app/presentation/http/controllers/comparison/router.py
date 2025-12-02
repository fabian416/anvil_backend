"""
Protocol comparison router.
"""

from typing import List, Optional
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status, Security, Body
from pydantic import BaseModel, Field

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.comparison import ProtocolComparisonService


class CompareProtocolsRequest(BaseModel):
    """Request to compare protocols."""

    protocol_ids: List[str] = Field(
        ..., min_items=2, max_items=5, description="2-5 protocol IDs to compare"
    )
    dimensions: Optional[List[str]] = Field(
        None, description="Dimensions to compare: risk, yield, security, network"
    )


def create_comparison_router() -> APIRouter:
    router = APIRouter(
        prefix="/comparison",
        tags=["comparison"],
    )

    @router.post(
        "/protocols",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def compare_protocols(
        request: CompareProtocolsRequest,
        comparison_service: FromDishka[ProtocolComparisonService],
    ) -> dict:
        """
        Compare multiple protocols side-by-side.

        Request Body:
        - protocol_ids: List of 2-5 protocol UUIDs
        - dimensions: Optional list of comparison dimensions
          (risk, yield, security, network, all)

        Returns comprehensive comparison including:
        - Detailed metrics for each protocol
        - Comparison matrix across dimensions
        - Winners by dimension
        - Identified tradeoffs
        - AI-powered recommendation
        """
        # Convert string IDs to UUIDs
        protocol_uuids = [UUID(pid) for pid in request.protocol_ids]

        comparison = await comparison_service.compare_protocols(
            protocol_ids=protocol_uuids,
            dimensions=request.dimensions,
        )

        return comparison

    return router
