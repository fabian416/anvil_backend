"""Risk alert service for monitoring and generating alerts."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import logging

from app.domain.alerts.entities.risk_alert import RiskAlert, AlertSubscription
from app.domain.portfolio.entities.user_portfolio import UserPortfolio
from app.domain.ml.services.risk_prediction_service import (
    RiskPredictionService,
    RiskLevel,
)
from app.infrastructure.websocket.event_broadcaster import GraphEventBroadcaster

logger = logging.getLogger(__name__)


class RiskAlertService:
    """
    Generate and manage risk alerts for users.

    Monitors user portfolios for risk changes and generates alerts
    based on ML predictions, anomaly detection, and user preferences.
    """

    def __init__(
        self,
        risk_prediction_service: RiskPredictionService,
        event_broadcaster: GraphEventBroadcaster,
    ):
        self._risk_service = risk_prediction_service
        self._broadcaster = event_broadcaster

    async def check_user_protocols_risk(
        self,
        user_id: UUID,
        portfolio: UserPortfolio,
        subscription: Optional[AlertSubscription] = None,
    ) -> List[RiskAlert]:
        """
        Check all user's protocols for risk changes.

        Generates alerts for:
        - Risk score increase >20%
        - Anomaly detected
        - Critical risk level reached
        - Dependency risk change

        Args:
            user_id: User UUID
            portfolio: User's portfolio
            subscription: Alert subscription preferences

        Returns:
            List of generated risk alerts
        """
        if not portfolio.protocols:
            return []

        alerts = []

        # Check each protocol
        for exposure in portfolio.protocols:
            # Skip if excluded by subscription
            if subscription and not subscription.should_alert_for_protocol(
                exposure.protocol_id
            ):
                continue

            # Get current risk prediction
            try:
                current_risk = await self._risk_service.predict_risk(
                    exposure.protocol_id
                )

                # Check for risk increase
                if exposure.risk_score and current_risk.risk_score > exposure.risk_score:
                    risk_change = current_risk.risk_score - exposure.risk_score

                    # Alert if >20% increase or >1 point
                    if risk_change >= 1.0 or risk_change / exposure.risk_score >= 0.2:
                        alert = self._create_risk_increase_alert(
                            user_id,
                            exposure,
                            current_risk.risk_score,
                            exposure.risk_score,
                            current_risk,
                        )

                        if self._should_send_alert(alert, subscription):
                            alerts.append(alert)

                # Check for critical risk level
                if current_risk.risk_level == RiskLevel.CRITICAL:
                    alert = self._create_critical_risk_alert(
                        user_id, exposure, current_risk
                    )

                    if self._should_send_alert(alert, subscription):
                        alerts.append(alert)

                # Check for anomalies
                anomalies = await self._risk_service.detect_anomalies(
                    exposure.protocol_id
                )
                if anomalies.is_anomalous:
                    alert = self._create_anomaly_alert(user_id, exposure, anomalies)

                    if self._should_send_alert(alert, subscription):
                        alerts.append(alert)

            except Exception as e:
                logger.error(
                    f"Error checking risk for protocol {exposure.protocol_name}: {e}",
                    exc_info=True,
                )
                continue

        return alerts

    async def send_risk_alert(
        self,
        alert: RiskAlert,
        send_push: bool = True,
        send_websocket: bool = True,
    ) -> None:
        """
        Send risk alert to user via configured channels.

        Args:
            alert: Risk alert to send
            send_push: Send push notification
            send_websocket: Send via WebSocket
        """
        # Broadcast via WebSocket
        if send_websocket:
            await self._broadcaster.broadcast_risk_alert(
                protocol_id=alert.protocol_id,
                protocol_name=alert.protocol_name,
                severity=alert.severity,
                message=alert.message,
                risk_score=alert.current_risk_score,
                risk_change=alert.risk_change,
                affected_users=[str(alert.user_id)],
            )

        # TODO: Send push notification
        # if send_push:
        #     await self._push_service.send(alert)

        logger.info(
            f"Sent risk alert to user {alert.user_id}: {alert.protocol_name}",
            extra={
                "user_id": str(alert.user_id),
                "protocol_id": str(alert.protocol_id),
                "severity": alert.severity,
            },
        )

    def _create_risk_increase_alert(
        self,
        user_id: UUID,
        exposure: any,
        current_score: float,
        previous_score: float,
        prediction: any,
    ) -> RiskAlert:
        """Create risk increase alert."""
        risk_change = current_score - previous_score
        percentage_change = (risk_change / previous_score) * 100

        severity = self._determine_severity(current_score, risk_change)

        # Generate message
        message = (
            f"Risk increased for {exposure.protocol_name}: "
            f"{previous_score:.1f} → {current_score:.1f} "
            f"(+{percentage_change:.1f}%)"
        )

        # Extract top contributing factors
        factors = [f.feature for f in prediction.contributing_factors[:3]]

        return RiskAlert(
            user_id=user_id,
            protocol_id=exposure.protocol_id,
            protocol_name=exposure.protocol_name,
            alert_type="risk_increase",
            severity=severity,
            message=message,
            details={
                "current_score": current_score,
                "previous_score": previous_score,
                "change": risk_change,
                "percentage_change": percentage_change,
                "contributing_factors": factors,
                "exposure_usd": float(exposure.value_usd),
            },
            recommendations=prediction.recommendations,
            current_risk_score=current_score,
            previous_risk_score=previous_score,
            risk_change=risk_change,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

    def _create_critical_risk_alert(
        self, user_id: UUID, exposure: any, prediction: any
    ) -> RiskAlert:
        """Create critical risk level alert."""
        message = (
            f"⚠️ CRITICAL RISK: {exposure.protocol_name} has reached "
            f"critical risk level ({prediction.risk_score:.1f}/10)"
        )

        recommendations = [
            "Consider exiting this position immediately",
            "Review alternative protocols",
            "Monitor closely for further developments",
        ] + prediction.recommendations[:2]

        return RiskAlert(
            user_id=user_id,
            protocol_id=exposure.protocol_id,
            protocol_name=exposure.protocol_name,
            alert_type="critical",
            severity="CRITICAL",
            message=message,
            details={
                "risk_score": prediction.risk_score,
                "risk_level": prediction.risk_level.value,
                "exposure_usd": float(exposure.value_usd),
                "exposure_percentage": exposure.percentage,
            },
            recommendations=recommendations,
            current_risk_score=prediction.risk_score,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

    def _create_anomaly_alert(
        self, user_id: UUID, exposure: any, anomalies: any
    ) -> RiskAlert:
        """Create anomaly detection alert."""
        # Get detected anomalies
        anomaly_details = []
        for anomaly in anomalies.anomalies:
            if anomaly.is_anomalous:
                anomaly_details.append(
                    f"{anomaly.feature}: {anomaly.z_score:.2f}σ deviation"
                )

        message = (
            f"Anomaly detected in {exposure.protocol_name}: "
            f"{len(anomaly_details)} unusual metric(s)"
        )

        severity = "HIGH" if len(anomaly_details) >= 3 else "MEDIUM"

        return RiskAlert(
            user_id=user_id,
            protocol_id=exposure.protocol_id,
            protocol_name=exposure.protocol_name,
            alert_type="anomaly",
            severity=severity,
            message=message,
            details={
                "anomalies": anomaly_details,
                "confidence": anomalies.confidence,
                "exposure_usd": float(exposure.value_usd),
            },
            recommendations=[
                "Review protocol for unusual activity",
                "Check official channels for announcements",
                "Consider reducing exposure until anomaly is understood",
            ],
            current_risk_score=0.0,  # Anomaly doesn't have direct score
            expires_at=datetime.utcnow() + timedelta(days=14),
        )

    def _determine_severity(self, current_score: float, change: float) -> str:
        """Determine alert severity based on risk score and change."""
        # Critical: Score >7 or change >3
        if current_score >= 7.0 or change >= 3.0:
            return "CRITICAL"

        # High: Score >5 or change >2
        if current_score >= 5.0 or change >= 2.0:
            return "HIGH"

        # Medium: Score >3 or change >1
        if current_score >= 3.0 or change >= 1.0:
            return "MEDIUM"

        return "LOW"

    def _should_send_alert(
        self, alert: RiskAlert, subscription: Optional[AlertSubscription]
    ) -> bool:
        """Determine if alert should be sent based on preferences."""
        if subscription is None:
            return True  # Send all alerts if no preferences

        # Check if alert type is enabled
        if alert.alert_type == "risk_increase" and not subscription.risk_alerts_enabled:
            return False
        if alert.alert_type == "anomaly" and not subscription.anomaly_alerts_enabled:
            return False

        # Check severity threshold
        if not subscription.should_alert_for_severity(alert.severity):
            return False

        return True


class RiskAlertMonitor:
    """
    Background monitor for checking user portfolios.

    This class is designed to be called from Celery tasks to
    periodically check all users for risk changes.
    """

    def __init__(
        self,
        alert_service: RiskAlertService,
    ):
        self._alert_service = alert_service

    async def check_all_users(
        self,
        # TODO: Add portfolio repository to fetch all user portfolios
    ) -> int:
        """
        Check all users for risk alerts.

        Returns:
            Number of alerts generated
        """
        # TODO: Implement once portfolio repository exists
        # This would:
        # 1. Fetch all user portfolios
        # 2. For each user:
        #    - Check protocols for risk changes
        #    - Generate alerts
        #    - Send alerts via appropriate channels
        # 3. Return total alert count

        logger.info("Risk alert check completed (no-op - portfolio repo needed)")
        return 0

    async def check_specific_protocol(
        self,
        protocol_id: UUID,
        protocol_name: str,
        new_risk_score: float,
        # TODO: Add portfolio repository
    ) -> List[RiskAlert]:
        """
        Check all users who hold a specific protocol.

        Called when a protocol's risk score changes significantly.

        Args:
            protocol_id: Protocol UUID
            protocol_name: Protocol name
            new_risk_score: New risk score

        Returns:
            List of alerts generated
        """
        # TODO: Implement once portfolio repository exists
        # This would:
        # 1. Find all users holding this protocol
        # 2. For each user:
        #    - Check if risk change is significant
        #    - Generate alert
        #    - Send alert
        # 3. Return alerts

        logger.info(
            f"Protocol risk check: {protocol_name} = {new_risk_score}",
            extra={"protocol_id": str(protocol_id), "risk_score": new_risk_score},
        )
        return []
