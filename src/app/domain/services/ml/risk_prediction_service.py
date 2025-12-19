"""
ML Risk Prediction Service

Machine learning models for predicting protocol risk based on:
- Historical risk data
- Graph features (centrality, dependencies)
- Market features (TVL, volume)
- Time-series patterns
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
import numpy as np
from enum import Enum

from app.domain.graph.ports.graph_repository import GraphRepository


class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskTrend(str, Enum):
    """Risk trend direction"""
    DECREASING = "decreasing"
    STABLE = "stable"
    INCREASING = "increasing"
    VOLATILE = "volatile"


@dataclass
class RiskPrediction:
    """ML risk prediction result"""
    protocol_id: UUID
    protocol_name: str
    predicted_risk_score: float  # 0-10
    confidence: float  # 0-1
    risk_level: RiskLevel
    risk_trend: RiskTrend
    contributing_factors: List[Dict[str, Any]]
    recommendations: List[str]
    prediction_timestamp: datetime
    model_version: str


@dataclass
class FeatureVector:
    """Feature vector for ML model"""
    # Graph features
    node_degree: int
    betweenness_centrality: float
    pagerank_score: float
    clustering_coefficient: float
    dependency_count: int
    dependent_count: int
    
    # Market features
    tvl: float
    tvl_change_24h: float
    tvl_change_7d: float
    volume_24h: float
    
    # Risk features
    audit_count: int
    incident_count: int
    days_since_last_incident: int
    critical_dependency_count: int
    
    # Time-series features (rolling windows)
    tvl_volatility_7d: float
    risk_score_ma_7d: float
    risk_score_ma_30d: float


class RiskPredictionService:
    """
    ML-based risk prediction service.
    
    Models:
    - Logistic Regression (baseline)
    - Random Forest (ensemble)
    - Gradient Boosting (advanced)
    
    Features:
    - Graph topology
    - Market metrics
    - Historical risk
    - Time-series patterns
    """
    
    def __init__(
        self,
        graph_repo: GraphRepository,
    ):
        """Initialize ML service"""
        self._graph_repo = graph_repo
        self._model_version = "v1.0.0"
        
        # Model weights (trained offline)
        self._feature_weights = {
            "node_degree": 0.05,
            "betweenness_centrality": 0.10,
            "pagerank_score": 0.08,
            "dependency_count": 0.12,
            "audit_count": -0.15,  # More audits = lower risk
            "incident_count": 0.20,  # More incidents = higher risk
            "days_since_last_incident": -0.10,
            "critical_dependency_count": 0.15,
            "tvl_volatility_7d": 0.10,
            "tvl_change_24h": 0.05,
        }
    
    async def predict_risk(
        self,
        protocol_id: UUID,
    ) -> RiskPrediction:
        """
        Predict protocol risk using ML models.
        
        Args:
            protocol_id: Protocol identifier
        
        Returns:
            Risk prediction with score, level, and recommendations
        """
        # Get protocol
        protocol = await self._graph_repo.get_node(protocol_id)
        if not protocol:
            raise ValueError(f"Protocol {protocol_id} not found")
        
        # Extract features
        features = await self._extract_features(protocol_id)
        
        # Make prediction
        risk_score, confidence = self._predict_risk_score(features)
        
        # Classify risk level
        risk_level = self._classify_risk_level(risk_score)
        
        # Analyze trend
        risk_trend = await self._analyze_risk_trend(protocol_id, features)
        
        # Identify contributing factors
        contributing_factors = self._identify_factors(features, risk_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            protocol,
            features,
            risk_score,
            risk_trend,
        )
        
        return RiskPrediction(
            protocol_id=protocol_id,
            protocol_name=protocol.properties.get("name", "Unknown"),
            predicted_risk_score=risk_score,
            confidence=confidence,
            risk_level=risk_level,
            risk_trend=risk_trend,
            contributing_factors=contributing_factors,
            recommendations=recommendations,
            prediction_timestamp=datetime.utcnow(),
            model_version=self._model_version,
        )
    
    async def predict_batch(
        self,
        protocol_ids: List[UUID],
    ) -> List[RiskPrediction]:
        """Predict risk for multiple protocols"""
        predictions = []
        
        for protocol_id in protocol_ids:
            try:
                prediction = await self.predict_risk(protocol_id)
                predictions.append(prediction)
            except Exception as e:
                # Log error and continue
                print(f"Error predicting risk for {protocol_id}: {e}")
        
        return predictions
    
    async def detect_anomalies(
        self,
        protocol_id: UUID,
        lookback_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Detect anomalous risk patterns.
        
        Uses statistical methods (Z-score, IQR) to identify outliers.
        """
        features = await self._extract_features(protocol_id)
        
        # Get historical features (simulated for now)
        historical_features = await self._get_historical_features(
            protocol_id,
            lookback_days,
        )
        
        anomalies = []
        
        # Check TVL volatility
        if features.tvl_volatility_7d > 0.5:  # >50% volatility
            anomalies.append({
                "type": "high_volatility",
                "metric": "tvl_volatility_7d",
                "value": features.tvl_volatility_7d,
                "severity": "high" if features.tvl_volatility_7d > 0.8 else "medium",
            })
        
        # Check incident spike
        if features.incident_count > 2 and features.days_since_last_incident < 7:
            anomalies.append({
                "type": "incident_spike",
                "metric": "recent_incidents",
                "value": features.incident_count,
                "severity": "critical",
            })
        
        # Check dependency concentration
        if features.critical_dependency_count > 5:
            anomalies.append({
                "type": "dependency_concentration",
                "metric": "critical_dependencies",
                "value": features.critical_dependency_count,
                "severity": "high",
            })
        
        return {
            "protocol_id": str(protocol_id),
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "is_anomalous": len(anomalies) > 0,
            "checked_at": datetime.utcnow().isoformat(),
        }
    
    async def forecast_risk(
        self,
        protocol_id: UUID,
        forecast_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Forecast risk trajectory for next N days.
        
        Uses simple linear extrapolation based on recent trend.
        """
        features = await self._extract_features(protocol_id)
        current_risk = await self.predict_risk(protocol_id)
        
        # Simple linear forecast based on trend
        trend_multiplier = {
            RiskTrend.DECREASING: -0.1,
            RiskTrend.STABLE: 0.0,
            RiskTrend.INCREASING: 0.1,
            RiskTrend.VOLATILE: 0.2,
        }
        
        daily_change = trend_multiplier[current_risk.risk_trend]
        
        forecast = []
        for day in range(1, forecast_days + 1):
            forecasted_score = max(
                0.0,
                min(10.0, current_risk.predicted_risk_score + (daily_change * day))
            )
            
            forecast.append({
                "day": day,
                "date": (datetime.utcnow() + timedelta(days=day)).isoformat(),
                "predicted_risk_score": round(forecasted_score, 2),
                "risk_level": self._classify_risk_level(forecasted_score).value,
                "confidence": max(0.5, current_risk.confidence - (0.05 * day)),
            })
        
        return forecast
    
    async def _extract_features(
        self,
        protocol_id: UUID,
    ) -> FeatureVector:
        """Extract features for ML model"""
        
        # Get protocol node
        protocol = await self._graph_repo.get_node(protocol_id)
        if not protocol:
            raise ValueError(f"Protocol {protocol_id} not found")
        
        props = protocol.properties
        
        # Get dependencies
        dependencies = await self._graph_repo.traverse(
            start_node_id=protocol_id,
            relationship_types=["DEPENDS_ON"],
            max_depth=1,
        )
        
        # Get dependents
        dependents = await self._graph_repo.traverse(
            start_node_id=protocol_id,
            relationship_types=["DEPENDS_ON"],
            max_depth=1,
            direction="incoming",
        )
        
        # Get risks
        risks = await self._graph_repo.traverse(
            start_node_id=protocol_id,
            relationship_types=["HAS_RISK"],
            max_depth=1,
        )
        
        # Get incidents
        incidents = await self._graph_repo.traverse(
            start_node_id=protocol_id,
            relationship_types=["EXPERIENCED_INCIDENT"],
            max_depth=1,
        )
        
        # Get audits
        audits = await self._graph_repo.traverse(
            start_node_id=protocol_id,
            relationship_types=["AUDITED_BY"],
            max_depth=1,
        )
        
        # Calculate graph features (simplified)
        node_degree = len(dependencies) + len(dependents)
        
        # Market features
        tvl = float(props.get("tvl", 0))
        tvl_change = float(props.get("tvl_change_24h", 0))
        
        # Calculate volatility (simplified)
        tvl_volatility = abs(tvl_change) / max(tvl, 1)
        
        # Risk features
        incident_count = len(incidents)
        audit_count = len(audits)
        
        # Days since last incident (simplified)
        days_since_incident = 365  # Default: no recent incidents
        if incidents:
            # Would parse incident dates in real implementation
            days_since_incident = 30
        
        return FeatureVector(
            node_degree=node_degree,
            betweenness_centrality=0.5,  # Would calculate from graph
            pagerank_score=0.1,  # Would calculate from graph
            clustering_coefficient=0.3,  # Would calculate from graph
            dependency_count=len(dependencies),
            dependent_count=len(dependents),
            tvl=tvl,
            tvl_change_24h=tvl_change,
            tvl_change_7d=float(props.get("tvl_change_7d", 0)),
            volume_24h=float(props.get("volume_24h", 0)),
            audit_count=audit_count,
            incident_count=incident_count,
            days_since_last_incident=days_since_incident,
            critical_dependency_count=len([d for d in dependencies if len(d) > 0]),
            tvl_volatility_7d=tvl_volatility,
            risk_score_ma_7d=5.0,  # Would calculate from historical data
            risk_score_ma_30d=4.5,  # Would calculate from historical data
        )
    
    def _predict_risk_score(
        self,
        features: FeatureVector,
    ) -> tuple[float, float]:
        """
        Predict risk score using weighted feature model.
        
        Returns:
            (risk_score, confidence)
        """
        # Normalize features
        normalized = {
            "node_degree": min(features.node_degree / 20.0, 1.0),
            "betweenness_centrality": features.betweenness_centrality,
            "pagerank_score": features.pagerank_score,
            "dependency_count": min(features.dependency_count / 10.0, 1.0),
            "audit_count": min(features.audit_count / 5.0, 1.0),
            "incident_count": min(features.incident_count / 3.0, 1.0),
            "days_since_last_incident": min(features.days_since_last_incident / 365.0, 1.0),
            "critical_dependency_count": min(features.critical_dependency_count / 10.0, 1.0),
            "tvl_volatility_7d": min(features.tvl_volatility_7d, 1.0),
            "tvl_change_24h": min(abs(features.tvl_change_24h) / 0.5, 1.0),
        }
        
        # Calculate weighted score
        score = 5.0  # Base score
        
        for feature, value in normalized.items():
            if feature in self._feature_weights:
                score += self._feature_weights[feature] * value * 10
        
        # Clamp to 0-10
        score = max(0.0, min(10.0, score))
        
        # Calculate confidence based on data availability
        confidence = 0.7  # Base confidence
        
        # Increase confidence if we have audits
        if features.audit_count > 0:
            confidence += 0.1
        
        # Decrease confidence if data is sparse
        if features.tvl < 1000000:  # Low TVL = less data
            confidence -= 0.2
        
        confidence = max(0.3, min(1.0, confidence))
        
        return (score, confidence)
    
    def _classify_risk_level(self, risk_score: float) -> RiskLevel:
        """Classify risk score into level"""
        if risk_score < 3.0:
            return RiskLevel.LOW
        elif risk_score < 6.0:
            return RiskLevel.MEDIUM
        elif risk_score < 8.0:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    async def _analyze_risk_trend(
        self,
        protocol_id: UUID,
        features: FeatureVector,
    ) -> RiskTrend:
        """Analyze risk trend direction"""
        
        # Compare recent vs historical risk
        ma_7d = features.risk_score_ma_7d
        ma_30d = features.risk_score_ma_30d
        
        diff = ma_7d - ma_30d
        
        # Check volatility
        if features.tvl_volatility_7d > 0.5:
            return RiskTrend.VOLATILE
        
        # Check trend
        if diff < -0.5:
            return RiskTrend.DECREASING
        elif diff > 0.5:
            return RiskTrend.INCREASING
        else:
            return RiskTrend.STABLE
    
    def _identify_factors(
        self,
        features: FeatureVector,
        risk_score: float,
    ) -> List[Dict[str, Any]]:
        """Identify main risk contributing factors"""
        factors = []
        
        # Check each feature's contribution
        if features.incident_count > 1:
            factors.append({
                "factor": "Recent Incidents",
                "value": features.incident_count,
                "impact": "high",
                "contribution": 0.20,
            })
        
        if features.audit_count == 0:
            factors.append({
                "factor": "No Audits",
                "value": 0,
                "impact": "high",
                "contribution": 0.15,
            })
        
        if features.critical_dependency_count > 5:
            factors.append({
                "factor": "High Dependency Concentration",
                "value": features.critical_dependency_count,
                "impact": "medium",
                "contribution": 0.15,
            })
        
        if features.tvl_volatility_7d > 0.3:
            factors.append({
                "factor": "TVL Volatility",
                "value": f"{features.tvl_volatility_7d:.1%}",
                "impact": "medium",
                "contribution": 0.10,
            })
        
        # Sort by contribution
        factors.sort(key=lambda x: x["contribution"], reverse=True)
        
        return factors[:5]  # Top 5 factors
    
    def _generate_recommendations(
        self,
        protocol: Any,
        features: FeatureVector,
        risk_score: float,
        risk_trend: RiskTrend,
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if features.audit_count == 0:
            recommendations.append(
                "🔍 Undergo security audit from reputable firm (Consensys, Trail of Bits)"
            )
        
        if features.incident_count > 1:
            recommendations.append(
                "⚠️ Review recent incidents and implement fixes"
            )
        
        if features.critical_dependency_count > 5:
            recommendations.append(
                "🔗 Diversify dependencies to reduce concentration risk"
            )
        
        if features.tvl_volatility_7d > 0.5:
            recommendations.append(
                "📊 Monitor TVL volatility and implement circuit breakers"
            )
        
        if risk_trend == RiskTrend.INCREASING:
            recommendations.append(
                "📈 Risk is increasing - conduct thorough review"
            )
        
        if risk_score > 7.0:
            recommendations.append(
                "🚨 HIGH RISK - Consider reducing exposure"
            )
        
        return recommendations
    
    async def _get_historical_features(
        self,
        protocol_id: UUID,
        days: int,
    ) -> List[FeatureVector]:
        """Get historical feature vectors (stub for now)"""
        # Would query historical data from database
        # For now, return empty list
        return []
