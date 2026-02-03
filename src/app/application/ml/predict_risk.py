"""
ML Risk Prediction Interactor

Application service for ML-based risk prediction.
"""

from typing import List
from uuid import UUID

from app.domain.ml.services.risk_prediction_service import (
    RiskPredictionService,
    RiskPrediction,
)


class PredictRiskInteractor:
    """Predict protocol risk using ML models"""

    def __init__(
        self,
        prediction_service: RiskPredictionService,
    ):
        """Initialize interactor"""
        self._prediction_service = prediction_service

    async def execute(
        self,
        protocol_id: UUID,
    ) -> RiskPrediction:
        """
        Predict protocol risk.

        Args:
            protocol_id: Protocol identifier

        Returns:
            ML risk prediction
        """
        return await self._prediction_service.predict_risk(protocol_id)


class PredictBatchRiskInteractor:
    """Predict risk for multiple protocols"""

    def __init__(
        self,
        prediction_service: RiskPredictionService,
    ):
        """Initialize interactor"""
        self._prediction_service = prediction_service

    async def execute(
        self,
        protocol_ids: List[UUID],
    ) -> List[RiskPrediction]:
        """
        Predict risk for multiple protocols.

        Args:
            protocol_ids: List of protocol identifiers

        Returns:
            List of ML risk predictions
        """
        return await self._prediction_service.predict_batch(protocol_ids)


class DetectAnomaliesInteractor:
    """Detect anomalous risk patterns"""

    def __init__(
        self,
        prediction_service: RiskPredictionService,
    ):
        """Initialize interactor"""
        self._prediction_service = prediction_service

    async def execute(
        self,
        protocol_id: UUID,
        lookback_days: int = 7,
    ) -> dict:
        """
        Detect anomalies in protocol risk.

        Args:
            protocol_id: Protocol identifier
            lookback_days: Days to look back

        Returns:
            Anomaly detection result
        """
        return await self._prediction_service.detect_anomalies(
            protocol_id,
            lookback_days,
        )


class ForecastRiskInteractor:
    """Forecast future risk trajectory"""

    def __init__(
        self,
        prediction_service: RiskPredictionService,
    ):
        """Initialize interactor"""
        self._prediction_service = prediction_service

    async def execute(
        self,
        protocol_id: UUID,
        forecast_days: int = 7,
    ) -> List[dict]:
        """
        Forecast protocol risk for next N days.

        Args:
            protocol_id: Protocol identifier
            forecast_days: Days to forecast

        Returns:
            Risk forecast
        """
        return await self._prediction_service.forecast_risk(
            protocol_id,
            forecast_days,
        )
