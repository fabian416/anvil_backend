"""
ML Prediction API Endpoints

Risk prediction using machine learning models.
"""

from typing import Annotated
from fastapi import APIRouter, status, Security, Query
from dishka.integrations.fastapi import FromDishka, inject
from uuid import UUID

from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.controllers.ml.schemas import (
    RiskPredictionResponse,
    BatchRiskPredictionRequest,
    BatchRiskPredictionResponse,
    AnomalyDetectionResponse,
    RiskForecastResponse,
)
from app.application.ml import (
    PredictRiskInteractor,
    PredictBatchRiskInteractor,
    DetectAnomaliesInteractor,
    ForecastRiskInteractor,
)

router = APIRouter(prefix="/ml/prediction", tags=["ML Prediction"])


@router.get(
    "/{protocol_id}",
    response_model=RiskPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict protocol risk",
    description="Predict protocol risk using ML models based on graph features, market data, and historical risks",
)
@inject
async def predict_risk(
    protocol_id: UUID,
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[PredictRiskInteractor],
) -> RiskPredictionResponse:
    """Predict protocol risk using ML"""
    
    prediction = await interactor.execute(protocol_id)
    
    return RiskPredictionResponse(
        protocol_id=str(prediction.protocol_id),
        protocol_name=prediction.protocol_name,
        predicted_risk_score=prediction.predicted_risk_score,
        confidence=prediction.confidence,
        risk_level=prediction.risk_level.value,
        risk_trend=prediction.risk_trend.value,
        contributing_factors=prediction.contributing_factors,
        recommendations=prediction.recommendations,
        prediction_timestamp=prediction.prediction_timestamp,
        model_version=prediction.model_version,
    )


@router.post(
    "/batch",
    response_model=BatchRiskPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch predict protocol risks",
    description="Predict risk for multiple protocols in a single request",
)
@inject
async def predict_batch_risk(
    request: BatchRiskPredictionRequest,
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[PredictBatchRiskInteractor],
) -> BatchRiskPredictionResponse:
    """Batch predict protocol risks"""
    
    protocol_ids = [UUID(pid) for pid in request.protocol_ids]
    predictions = await interactor.execute(protocol_ids)
    
    return BatchRiskPredictionResponse(
        predictions=[
            RiskPredictionResponse(
                protocol_id=str(p.protocol_id),
                protocol_name=p.protocol_name,
                predicted_risk_score=p.predicted_risk_score,
                confidence=p.confidence,
                risk_level=p.risk_level.value,
                risk_trend=p.risk_trend.value,
                contributing_factors=p.contributing_factors,
                recommendations=p.recommendations,
                prediction_timestamp=p.prediction_timestamp,
                model_version=p.model_version,
            )
            for p in predictions
        ],
        total=len(predictions),
    )


@router.get(
    "/{protocol_id}/anomalies",
    response_model=AnomalyDetectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect anomalies",
    description="Detect anomalous risk patterns using statistical methods",
)
@inject
async def detect_anomalies(
    protocol_id: UUID,
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[DetectAnomaliesInteractor],
    lookback_days: int = Query(7, ge=1, le=90, description="Days to look back"),
) -> AnomalyDetectionResponse:
    """Detect anomalous risk patterns"""
    
    result = await interactor.execute(protocol_id, lookback_days)
    
    return AnomalyDetectionResponse(**result)


@router.get(
    "/{protocol_id}/forecast",
    response_model=RiskForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Forecast risk",
    description="Forecast protocol risk trajectory for next N days",
)
@inject
async def forecast_risk(
    protocol_id: UUID,
    authorization: Annotated[str, Security(bearer_scheme)],
    interactor: FromDishka[ForecastRiskInteractor],
    forecast_days: int = Query(7, ge=1, le=30, description="Days to forecast"),
) -> RiskForecastResponse:
    """Forecast protocol risk"""
    
    forecast = await interactor.execute(protocol_id, forecast_days)
    
    return RiskForecastResponse(
        protocol_id=str(protocol_id),
        forecast=forecast,
        forecast_days=forecast_days,
    )
