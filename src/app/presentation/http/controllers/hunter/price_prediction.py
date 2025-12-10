"""Price prediction API endpoints.

REST API for LSTM price predictions.
"""

from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict

from app.application.hunter.lstm_price_predictor import (
    LSTMPricePredictor,
    LSTMConfig,
)
from app.application.hunter.price_data_service import PriceDataService


class PricePredictionResponse(BaseModel):
    """Response model for price prediction."""

    token_symbol: str = Field(..., description="Token symbol (e.g., ETH, BTC)")
    current_price: float = Field(..., description="Current token price in USD")
    predicted_price: float = Field(..., description="Predicted future price in USD")
    confidence: float = Field(..., description="Prediction confidence (0-1)", ge=0, le=1)
    prediction_time: str = Field(..., description="Time prediction was made")
    forecast_time: str = Field(..., description="Time of forecasted price")
    horizon_hours: int = Field(..., description="Forecast horizon in hours")
    change_percent: float = Field(..., description="Predicted price change percentage")
    direction: str = Field(..., description="Price direction: up, down, or neutral")

    class Config:
        json_schema_extra = {
            "example": {
                "token_symbol": "ETH",
                "current_price": 2450.50,
                "predicted_price": 2580.75,
                "confidence": 0.82,
                "prediction_time": "2025-12-03T16:00:00Z",
                "forecast_time": "2025-12-04T16:00:00Z",
                "horizon_hours": 24,
                "change_percent": 5.32,
                "direction": "up",
            }
        }


class MultiHorizonPredictionResponse(BaseModel):
    """Response model for multi-horizon predictions."""

    token_symbol: str = Field(..., description="Token symbol")
    predictions: Dict[str, PricePredictionResponse] = Field(
        ..., description="Predictions at different time horizons"
    )


class ModelInfoResponse(BaseModel):
    """Response model for model information."""

    architecture: str = Field(..., description="Model architecture (LSTM)")
    layers: int = Field(..., description="Number of LSTM layers")
    hidden_size: int = Field(..., description="Hidden layer size")
    total_parameters: int = Field(..., description="Total model parameters")
    is_trained: bool = Field(..., description="Whether model is trained")
    device: str = Field(..., description="Computation device (cpu/cuda)")


def create_price_prediction_router() -> APIRouter:
    """Create price prediction router.

    Returns:
        Configured FastAPI router
    """
    router = APIRouter(prefix="/hunter/predictions", tags=["hunter-predictions"])

    @router.post(
        "/train/{token_symbol}",
        response_model=dict,
        summary="Train LSTM model",
        description="Train LSTM price prediction model on historical data for a token",
    )
    async def train_model(
        token_symbol: str,
        days: int = Query(90, ge=30, le=365, description="Days of historical data for training"),
    ) -> dict:
        """Train LSTM model on historical data.

        Args:
            token_symbol: Token to train on
            days: Days of historical training data

        Returns:
            Training metrics

        Example:
            POST /api/v1/hunter/predictions/train/ETH?days=90

            Response:
            {
                "token_symbol": "ETH",
                "epochs": 50,
                "final_train_loss": 0.0023,
                "final_val_loss": 0.0031,
                "training_samples": 1728,
                "validation_samples": 432
            }
        """
        try:
            predictor = LSTMPricePredictor()
            metrics = await predictor.train(token_symbol, days=days)
            return metrics

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Training failed: {str(e)}",
            )

    @router.get(
        "/predict/{token_symbol}",
        response_model=PricePredictionResponse,
        summary="Predict token price",
        description="Predict future price for a cryptocurrency token using LSTM",
    )
    async def predict_price(
        token_symbol: str,
        horizon: int = Query(
            24, ge=1, le=168, description="Prediction horizon in hours (24h or 168h/7d)"
        ),
    ) -> PricePredictionResponse:
        """Predict future token price.

        Automatically trains model if not already trained.

        Args:
            token_symbol: Token to predict
            horizon: Hours ahead to predict (24 or 168)

        Returns:
            Price prediction with confidence

        Example:
            GET /api/v1/hunter/predictions/predict/ETH?horizon=24

            Response:
            {
                "token_symbol": "ETH",
                "current_price": 2450.50,
                "predicted_price": 2580.75,
                "confidence": 0.82,
                "prediction_time": "2025-12-03T16:00:00Z",
                "forecast_time": "2025-12-04T16:00:00Z",
                "horizon_hours": 24,
                "change_percent": 5.32,
                "direction": "up"
            }
        """
        try:
            predictor = LSTMPricePredictor()
            prediction = await predictor.predict(token_symbol, horizon_hours=horizon)

            return PricePredictionResponse(**prediction.to_dict())

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Prediction failed: {str(e)}",
            )

    @router.get(
        "/predict/{token_symbol}/multi-horizon",
        response_model=MultiHorizonPredictionResponse,
        summary="Multi-horizon price prediction",
        description="Predict token prices at multiple time horizons (24h and 7d)",
    )
    async def predict_multi_horizon(
        token_symbol: str,
    ) -> MultiHorizonPredictionResponse:
        """Predict token prices at multiple time horizons.

        Args:
            token_symbol: Token to predict

        Returns:
            Predictions for 24h and 7d horizons

        Example:
            GET /api/v1/hunter/predictions/predict/ETH/multi-horizon

            Response:
            {
                "token_symbol": "ETH",
                "predictions": {
                    "24h": {
                        "predicted_price": 2580.75,
                        "confidence": 0.82,
                        "change_percent": 5.32,
                        "direction": "up"
                    },
                    "7d": {
                        "predicted_price": 2720.30,
                        "confidence": 0.68,
                        "change_percent": 11.02,
                        "direction": "up"
                    }
                }
            }
        """
        try:
            predictor = LSTMPricePredictor()
            predictions = await predictor.predict_multi_horizon(token_symbol)

            # Convert to response format
            predictions_dict = {
                horizon: PricePredictionResponse(**pred.to_dict())
                for horizon, pred in predictions.items()
            }

            return MultiHorizonPredictionResponse(
                token_symbol=token_symbol, predictions=predictions_dict
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Multi-horizon prediction failed: {str(e)}",
            )

    @router.get(
        "/model-info",
        response_model=ModelInfoResponse,
        summary="Get model information",
        description="Get LSTM model architecture and training information",
    )
    async def get_model_info() -> ModelInfoResponse:
        """Get LSTM model information.

        Returns:
            Model architecture details

        Example:
            GET /api/v1/hunter/predictions/model-info

            Response:
            {
                "architecture": "LSTM",
                "layers": 3,
                "hidden_size": 128,
                "total_parameters": 167297,
                "is_trained": true,
                "device": "cpu"
            }
        """
        try:
            predictor = LSTMPricePredictor()
            info = predictor.get_model_info()

            return ModelInfoResponse(**info)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get model info: {str(e)}",
            )

    return router
