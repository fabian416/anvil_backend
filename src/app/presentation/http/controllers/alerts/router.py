"""
Alerts router for risk alert endpoints.
"""

from uuid import UUID
from typing import Optional

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status, Security, Query
from fastapi.exceptions import HTTPException

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.application.common.services.current_user import CurrentUserService
from app.presentation.http.schemas.alerts import (
    RiskAlertResponse,
    RiskAlertListResponse,
    AcknowledgeAlertRequest,
    UpdateSubscriptionRequest,
    AlertSubscriptionResponse,
)
from app.application.alerts import RiskAlertService


def create_alerts_router() -> APIRouter:
    router = APIRouter(
        prefix="/alerts",
        tags=["alerts"],
    )

    @router.get(
        "/risk",
        status_code=status.HTTP_200_OK,
        response_model=RiskAlertListResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_risk_alerts(
        current_user: FromDishka[CurrentUserService],
        unacknowledged_only: bool = Query(False),
        severity: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=100),
    ) -> RiskAlertListResponse:
        """
        Get risk alerts for the authenticated user.

        Query Parameters:
        - unacknowledged_only: Only return unacknowledged alerts
        - severity: Filter by severity (LOW/MEDIUM/HIGH/CRITICAL)
        - limit: Maximum number of alerts to return

        Returns:
        - List of risk alerts
        - Total count
        - Unacknowledged count
        """
        user = await current_user.get_current_user()

        # TODO: Fetch from alert repository
        # For now, return empty list
        alerts = []

        return RiskAlertListResponse(
            alerts=alerts,
            total=len(alerts),
            unacknowledged=0,
        )

    @router.put(
        "/risk/{alert_id}/acknowledge",
        status_code=status.HTTP_200_OK,
        response_model=RiskAlertResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def acknowledge_alert(
        alert_id: UUID,
        request: AcknowledgeAlertRequest,
        current_user: FromDishka[CurrentUserService],
    ) -> RiskAlertResponse:
        """
        Acknowledge a risk alert.

        Marks the alert as acknowledged and optionally as acted upon.

        Args:
            alert_id: Alert UUID
            request: Acknowledgement details

        Returns:
            Updated alert
        """
        user = await current_user.get_current_user()

        # TODO: Update in repository
        # alert = await alert_repo.get(alert_id)
        # if alert.user_id != user.id:
        #     raise HTTPException(403, "Not your alert")
        # alert.acknowledge()
        # if request.acted_upon:
        #     alert.mark_acted_upon()
        # await alert_repo.save(alert)

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Alert repository not yet implemented",
        )

    @router.delete(
        "/risk/{alert_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def dismiss_alert(
        alert_id: UUID,
        current_user: FromDishka[CurrentUserService],
    ) -> None:
        """
        Dismiss a risk alert.

        Marks the alert as dismissed (not relevant).

        Args:
            alert_id: Alert UUID
        """
        user = await current_user.get_current_user()

        # TODO: Update in repository
        # alert = await alert_repo.get(alert_id)
        # if alert.user_id != user.id:
        #     raise HTTPException(403, "Not your alert")
        # alert.dismiss()
        # await alert_repo.save(alert)

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Alert repository not yet implemented",
        )

    @router.get(
        "/subscription",
        status_code=status.HTTP_200_OK,
        response_model=AlertSubscriptionResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_alert_subscription(
        current_user: FromDishka[CurrentUserService],
    ) -> AlertSubscriptionResponse:
        """
        Get user's alert subscription preferences.

        Returns:
        - Alert type preferences
        - Severity threshold
        - Notification channels
        - Subscribed protocols
        """
        user = await current_user.get_current_user()

        # TODO: Fetch from repository
        # For now, return default preferences
        return AlertSubscriptionResponse(
            risk_alerts_enabled=True,
            anomaly_alerts_enabled=True,
            protocol_update_alerts_enabled=True,
            price_alerts_enabled=True,
            min_severity="MEDIUM",
            subscribed_protocols=[],
            excluded_protocols=[],
            push_notifications=True,
            email_notifications=False,
            websocket_notifications=True,
            max_alerts_per_hour=10,
        )

    @router.put(
        "/subscription",
        status_code=status.HTTP_200_OK,
        response_model=AlertSubscriptionResponse,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def update_alert_subscription(
        request: UpdateSubscriptionRequest,
        current_user: FromDishka[CurrentUserService],
    ) -> AlertSubscriptionResponse:
        """
        Update user's alert subscription preferences.

        Args:
            request: Updated preferences

        Returns:
            Updated subscription
        """
        user = await current_user.get_current_user()

        # TODO: Update in repository
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Alert repository not yet implemented",
        )

    @router.post(
        "/subscription/protocols/{protocol_id}",
        status_code=status.HTTP_200_OK,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def subscribe_to_protocol(
        protocol_id: UUID,
        current_user: FromDishka[CurrentUserService],
    ) -> dict:
        """
        Subscribe to alerts for a specific protocol.

        Args:
            protocol_id: Protocol UUID

        Returns:
            Success message
        """
        user = await current_user.get_current_user()

        # TODO: Add to subscription
        return {"success": True, "message": f"Subscribed to protocol {protocol_id}"}

    @router.delete(
        "/subscription/protocols/{protocol_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def unsubscribe_from_protocol(
        protocol_id: UUID,
        current_user: FromDishka[CurrentUserService],
    ) -> None:
        """
        Unsubscribe from alerts for a specific protocol.

        Args:
            protocol_id: Protocol UUID
        """
        user = await current_user.get_current_user()

        # TODO: Remove from subscription
        pass

    return router
