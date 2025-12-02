"""
ML API Schemas

Pydantic models for ML prediction and network analysis endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# Risk Prediction Schemas

class RiskPredictionResponse(BaseModel):
    """ML risk prediction result"""
    protocol_id: str
    protocol_name: str
    predicted_risk_score: float = Field(..., ge=0.0, le=10.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_level: str
    risk_trend: str
    contributing_factors: List[Dict[str, Any]]
    recommendations: List[str]
    prediction_timestamp: datetime
    model_version: str


class BatchRiskPredictionRequest(BaseModel):
    """Batch risk prediction request"""
    protocol_ids: List[str] = Field(..., min_items=1, max_items=50)


class BatchRiskPredictionResponse(BaseModel):
    """Batch risk prediction response"""
    predictions: List[RiskPredictionResponse]
    total: int


class AnomalyDetectionResponse(BaseModel):
    """Anomaly detection result"""
    protocol_id: str
    anomalies_detected: int
    anomalies: List[Dict[str, Any]]
    is_anomalous: bool
    checked_at: str


class RiskForecastResponse(BaseModel):
    """Risk forecast result"""
    protocol_id: str
    forecast: List[Dict[str, Any]]
    forecast_days: int


# Network Analysis Schemas

class PageRankResponse(BaseModel):
    """PageRank result"""
    protocol_id: str
    protocol_name: str
    pagerank_score: float
    rank: int
    in_degree: int
    out_degree: int


class PageRankListResponse(BaseModel):
    """List of PageRank results"""
    results: List[PageRankResponse]
    total: int


class CommunityResponse(BaseModel):
    """Community detection result"""
    community_id: int
    protocols: List[Dict[str, Any]]
    size: int
    density: float
    description: str


class CommunityListResponse(BaseModel):
    """List of detected communities"""
    communities: List[CommunityResponse]
    total_communities: int


class CentralityResponse(BaseModel):
    """Centrality metrics"""
    protocol_id: str
    protocol_name: str
    degree_centrality: float
    betweenness_centrality: float
    closeness_centrality: float
    eigenvector_centrality: float
    importance_score: float


class CentralityListResponse(BaseModel):
    """List of centrality results"""
    results: List[CentralityResponse]
    total: int


class ContagionSimulationResponse(BaseModel):
    """Contagion simulation result"""
    origin_protocol_id: str
    origin_protocol_name: str
    affected_protocols: List[Dict[str, Any]]
    cascade_depth: int
    total_affected: int
    total_tvl_at_risk: float
    risk_score: float
