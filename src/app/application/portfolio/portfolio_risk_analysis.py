"""Portfolio risk analysis application service."""

from dataclasses import dataclass
from datetime import datetime, UTC
from decimal import Decimal
from typing import List, Dict, Optional
from uuid import UUID

from app.domain.portfolio.entities.user_portfolio import UserPortfolio, ProtocolExposure
from app.domain.graph.ports.graph_repository import GraphRepository
from app.domain.ml.services.risk_prediction_service import (
    RiskPredictionService,
    RiskLevel,
)
from app.domain.ml.services.network_analysis_service import NetworkAnalysisService


@dataclass
class ProtocolRiskDetail:
    """Risk details for a protocol in portfolio."""

    protocol_id: UUID
    protocol_name: str
    exposure_usd: Decimal
    exposure_percentage: float
    risk_score: float  # 0-10
    risk_level: str
    risk_trend: str
    contributing_factors: List[str]
    value_at_risk_usd: Decimal  # Estimated max loss


@dataclass
class DependencyRisk:
    """Risk from protocol dependencies."""

    dependency_protocol_id: UUID
    dependency_protocol_name: str
    dependent_protocols: List[str]  # Portfolio protocols that depend on this
    impact_if_failure: str  # LOW/MEDIUM/HIGH/CRITICAL
    total_exposure_usd: Decimal
    risk_score: float


@dataclass
class PortfolioRiskSummary:
    """Comprehensive portfolio risk analysis."""

    user_id: UUID
    overall_risk_score: float  # Weighted average
    risk_distribution: Dict[str, float]  # Percentage by risk level
    protocols_at_risk: List[ProtocolRiskDetail]
    dependency_risks: List[DependencyRisk]
    systemic_risk_score: float  # Based on interconnections
    concentration_risk: float  # Based on allocation
    chain_risk_distribution: Dict[str, float]
    recommendations: List[str]
    total_value_at_risk_usd: Decimal
    last_updated: datetime


@dataclass
class CascadeImpact:
    """Impact of cascade failure on portfolio."""

    origin_protocol_id: UUID
    origin_protocol_name: str
    directly_affected: List[str]  # Protocol names
    indirectly_affected: List[str]
    total_exposure_at_risk_usd: Decimal
    cascade_probability: float  # 0-1
    time_to_impact: str  # immediate/hours/days


@dataclass
class PortfolioCascadeResult:
    """Result of cascade simulation on portfolio."""

    user_id: UUID
    cascade_impacts: List[CascadeImpact]
    worst_case_loss_usd: Decimal
    worst_case_loss_percentage: float
    protocols_to_exit: List[str]
    protocols_to_reduce: List[str]
    safe_protocols: List[str]


class PortfolioRiskAnalysis:
    """Aggregate risk analysis for user's portfolio.

    Combines ML risk predictions, network analysis, and portfolio
    composition to provide comprehensive risk assessment.
    """

    def __init__(
        self,
        risk_prediction_service: RiskPredictionService,
        network_analysis_service: NetworkAnalysisService,
        graph_repository: GraphRepository,
    ):
        self._risk_service = risk_prediction_service
        self._network_service = network_analysis_service
        self._graph_repo = graph_repository

    async def get_portfolio_risk(
        self, portfolio: UserPortfolio
    ) -> PortfolioRiskSummary:
        """
        Calculate comprehensive risk for user's portfolio.

        Args:
            portfolio: User's portfolio

        Returns:
            Comprehensive risk summary
        """
        if not portfolio.protocols:
            return self._empty_risk_summary(portfolio.user_id)

        # Get risk predictions for all protocols
        protocol_risks = await self._analyze_protocol_risks(portfolio.protocols)

        # Calculate overall risk score (weighted by exposure)
        overall_risk = self._calculate_weighted_risk(portfolio.protocols, protocol_risks)

        # Get risk distribution
        risk_distribution = self._calculate_risk_distribution(protocol_risks)

        # Identify high-risk protocols
        protocols_at_risk = self._identify_at_risk_protocols(
            portfolio.protocols, protocol_risks
        )

        # Analyze dependency risks
        dependency_risks = await self._analyze_dependency_risks(
            portfolio.protocols, protocol_risks
        )

        # Calculate systemic risk
        systemic_risk = await self._calculate_systemic_risk(portfolio.protocols)

        # Calculate concentration risk
        concentration_risk = self._calculate_concentration_risk(portfolio.protocols)

        # Get chain risk distribution
        chain_risk = self._calculate_chain_risk(portfolio.protocols, protocol_risks)

        # Calculate value at risk
        total_var = self._calculate_total_value_at_risk(
            portfolio.protocols, protocol_risks
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_risk,
            concentration_risk,
            protocols_at_risk,
            dependency_risks,
        )

        return PortfolioRiskSummary(
            user_id=portfolio.user_id,
            overall_risk_score=overall_risk,
            risk_distribution=risk_distribution,
            protocols_at_risk=protocols_at_risk,
            dependency_risks=dependency_risks,
            systemic_risk_score=systemic_risk,
            concentration_risk=concentration_risk,
            chain_risk_distribution=chain_risk,
            recommendations=recommendations,
            total_value_at_risk_usd=total_var,
            last_updated=datetime.now(UTC),
        )

    async def simulate_portfolio_cascade(
        self,
        portfolio: UserPortfolio,
        origin_protocol_id: UUID,
    ) -> PortfolioCascadeResult:
        """
        Simulate cascade impact on user's portfolio.

        Args:
            portfolio: User's portfolio
            origin_protocol_id: Protocol that fails

        Returns:
            Cascade simulation result
        """
        # Get origin protocol exposure
        origin_exposure = portfolio.get_exposure(origin_protocol_id)
        if not origin_exposure:
            raise ValueError("Protocol not in portfolio")

        # Run network contagion simulation
        contagion = await self._network_service.simulate_contagion(
            origin_protocol_id=origin_protocol_id,
            failure_probability=0.8,
            transmission_rate=0.6,
            max_hops=3,
        )

        # Map to portfolio
        cascade_impacts = await self._map_contagion_to_portfolio(
            portfolio, contagion, origin_exposure.protocol_name
        )

        # Calculate worst case
        worst_case_loss = sum(c.total_exposure_at_risk_usd for c in cascade_impacts)
        worst_case_pct = float(
            (worst_case_loss / portfolio.total_value_usd) * 100
            if portfolio.total_value_usd > 0
            else 0
        )

        # Generate action recommendations
        protocols_to_exit, protocols_to_reduce, safe_protocols = (
            self._generate_cascade_actions(portfolio, cascade_impacts)
        )

        return PortfolioCascadeResult(
            user_id=portfolio.user_id,
            cascade_impacts=cascade_impacts,
            worst_case_loss_usd=worst_case_loss,
            worst_case_loss_percentage=worst_case_pct,
            protocols_to_exit=protocols_to_exit,
            protocols_to_reduce=protocols_to_reduce,
            safe_protocols=safe_protocols,
        )

    async def _analyze_protocol_risks(
        self, exposures: List[ProtocolExposure]
    ) -> Dict[UUID, any]:
        """Get risk predictions for all protocols."""
        protocol_ids = [e.protocol_id for e in exposures]

        # Batch predict risks
        predictions = await self._risk_service.predict_batch(protocol_ids)

        return {pred.protocol_id: pred for pred in predictions}

    def _calculate_weighted_risk(
        self, exposures: List[ProtocolExposure], risks: Dict[UUID, any]
    ) -> float:
        """Calculate weighted average risk score."""
        total_value = sum(e.value_usd for e in exposures)
        if total_value == 0:
            return 0.0

        weighted_sum = sum(
            float(e.value_usd) * risks[e.protocol_id].risk_score
            for e in exposures
            if e.protocol_id in risks
        )

        return weighted_sum / float(total_value)

    def _calculate_risk_distribution(self, risks: Dict[UUID, any]) -> Dict[str, float]:
        """Calculate percentage of portfolio in each risk level."""
        if not risks:
            return {"LOW": 0.0, "MEDIUM": 0.0, "HIGH": 0.0, "CRITICAL": 0.0}

        total = len(risks)
        distribution = {}

        for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            count = sum(1 for r in risks.values() if r.risk_level.value == level)
            distribution[level] = (count / total) * 100

        return distribution

    def _identify_at_risk_protocols(
        self, exposures: List[ProtocolExposure], risks: Dict[UUID, any]
    ) -> List[ProtocolRiskDetail]:
        """Identify protocols with elevated risk."""
        at_risk = []

        for exposure in exposures:
            if exposure.protocol_id not in risks:
                continue

            risk_pred = risks[exposure.protocol_id]

            # Consider HIGH or CRITICAL as "at risk"
            if risk_pred.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                # Estimate value at risk (simple: risk_score/10 * exposure)
                var = float(exposure.value_usd) * (risk_pred.risk_score / 10)

                at_risk.append(
                    ProtocolRiskDetail(
                        protocol_id=exposure.protocol_id,
                        protocol_name=exposure.protocol_name,
                        exposure_usd=exposure.value_usd,
                        exposure_percentage=exposure.percentage,
                        risk_score=risk_pred.risk_score,
                        risk_level=risk_pred.risk_level.value,
                        risk_trend=risk_pred.risk_trend.value,
                        contributing_factors=[
                            f.feature for f in risk_pred.contributing_factors[:3]
                        ],
                        value_at_risk_usd=Decimal(str(var)),
                    )
                )

        # Sort by exposure (descending)
        at_risk.sort(key=lambda x: x.exposure_usd, reverse=True)

        return at_risk

    async def _analyze_dependency_risks(
        self, exposures: List[ProtocolExposure], risks: Dict[UUID, any]
    ) -> List[DependencyRisk]:
        """Analyze risks from protocol dependencies."""
        dependency_map = {}  # dependency_id -> list of dependent protocols

        # Build dependency map for portfolio protocols
        for exposure in exposures:
            # Get dependencies for this protocol
            try:
                node = await self._graph_repo.get_node(exposure.protocol_id)
                if not node:
                    continue

                # Get outgoing DEPENDS_ON relationships
                edges = await self._graph_repo.get_edges(
                    source_id=exposure.protocol_id, relationship_type="DEPENDS_ON"
                )

                for edge in edges:
                    dep_id = edge.target_id
                    if dep_id not in dependency_map:
                        dependency_map[dep_id] = []
                    dependency_map[dep_id].append(exposure.protocol_name)

            except Exception:
                continue

        # Calculate risk for each dependency
        dependency_risks = []

        for dep_id, dependent_names in dependency_map.items():
            # Get dependency node
            try:
                dep_node = await self._graph_repo.get_node(dep_id)
                if not dep_node:
                    continue

                # Get risk score for dependency
                dep_risk = await self._risk_service.predict_risk(dep_id)

                # Calculate total exposure (sum of dependent protocols)
                total_exposure = sum(
                    e.value_usd
                    for e in exposures
                    if e.protocol_name in dependent_names
                )

                # Determine impact level
                impact = self._determine_dependency_impact(
                    len(dependent_names), float(total_exposure), dep_risk.risk_score
                )

                dependency_risks.append(
                    DependencyRisk(
                        dependency_protocol_id=dep_id,
                        dependency_protocol_name=dep_node.properties.get(
                            "name", "Unknown"
                        ),
                        dependent_protocols=dependent_names,
                        impact_if_failure=impact,
                        total_exposure_usd=total_exposure,
                        risk_score=dep_risk.risk_score,
                    )
                )

            except Exception:
                continue

        # Sort by impact and exposure
        dependency_risks.sort(
            key=lambda x: (x.impact_if_failure, x.total_exposure_usd), reverse=True
        )

        return dependency_risks

    def _determine_dependency_impact(
        self, num_dependents: int, exposure: float, risk_score: float
    ) -> str:
        """Determine impact level of dependency failure."""
        # Combine factors
        score = (num_dependents * 2) + (exposure / 1000) + risk_score

        if score >= 15:
            return "CRITICAL"
        elif score >= 10:
            return "HIGH"
        elif score >= 5:
            return "MEDIUM"
        else:
            return "LOW"

    async def _calculate_systemic_risk(
        self, exposures: List[ProtocolExposure]
    ) -> float:
        """Calculate systemic risk based on interconnections."""
        if len(exposures) <= 1:
            return 0.0

        # Get network centrality for portfolio protocols
        protocol_ids = [e.protocol_id for e in exposures]

        try:
            # Calculate centrality for all protocols
            centrality = await self._network_service.calculate_centrality(
                metric="betweenness"
            )

            # Get average centrality for portfolio
            portfolio_centrality = [
                c.centrality_value
                for c in centrality.protocols
                if c.protocol_id in protocol_ids
            ]

            if not portfolio_centrality:
                return 0.0

            avg_centrality = sum(portfolio_centrality) / len(portfolio_centrality)

            # Normalize to 0-10 scale
            # High centrality = high systemic risk
            return min(avg_centrality * 10, 10.0)

        except Exception:
            return 5.0  # Default moderate risk

    def _calculate_concentration_risk(
        self, exposures: List[ProtocolExposure]
    ) -> float:
        """Calculate concentration risk (Herfindahl index)."""
        if not exposures:
            return 0.0

        # Calculate Herfindahl index
        herfindahl = sum((e.percentage / 100) ** 2 for e in exposures)

        # Normalize to 0-10 scale
        # Higher concentration = higher risk
        return herfindahl * 10

    def _calculate_chain_risk(
        self, exposures: List[ProtocolExposure], risks: Dict[UUID, any]
    ) -> Dict[str, float]:
        """Calculate risk distribution by chain."""
        chain_risks = {}

        for exposure in exposures:
            if exposure.protocol_id not in risks:
                continue

            risk_score = risks[exposure.protocol_id].risk_score

            if exposure.chain not in chain_risks:
                chain_risks[exposure.chain] = []

            chain_risks[exposure.chain].append(
                (float(exposure.value_usd), risk_score)
            )

        # Calculate weighted average for each chain
        result = {}
        for chain, values in chain_risks.items():
            total_value = sum(v[0] for v in values)
            if total_value > 0:
                weighted_risk = sum(v[0] * v[1] for v in values) / total_value
                result[chain] = weighted_risk

        return result

    def _calculate_total_value_at_risk(
        self, exposures: List[ProtocolExposure], risks: Dict[UUID, any]
    ) -> Decimal:
        """Calculate total value at risk across portfolio."""
        total_var = Decimal("0")

        for exposure in exposures:
            if exposure.protocol_id not in risks:
                continue

            risk_score = risks[exposure.protocol_id].risk_score

            # Simple VaR: risk_score/10 * exposure
            var = float(exposure.value_usd) * (risk_score / 10)
            total_var += Decimal(str(var))

        return total_var

    def _generate_recommendations(
        self,
        overall_risk: float,
        concentration_risk: float,
        at_risk_protocols: List[ProtocolRiskDetail],
        dependency_risks: List[DependencyRisk],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Overall risk
        if overall_risk > 7.0:
            recommendations.append(
                "Portfolio has HIGH overall risk - consider reducing exposure to risky protocols"
            )
        elif overall_risk > 5.0:
            recommendations.append(
                "Portfolio has MODERATE risk - review individual protocol risks"
            )

        # Concentration
        if concentration_risk > 7.0:
            recommendations.append(
                "High concentration risk - diversify across more protocols"
            )

        # Specific protocols
        if at_risk_protocols:
            top_risk = at_risk_protocols[0]
            recommendations.append(
                f"Consider reducing exposure to {top_risk.protocol_name} "
                f"(risk: {top_risk.risk_level}, {top_risk.exposure_percentage:.1f}% of portfolio)"
            )

        # Dependencies
        critical_deps = [d for d in dependency_risks if d.impact_if_failure == "CRITICAL"]
        if critical_deps:
            recommendations.append(
                f"Critical dependency risk: {critical_deps[0].dependency_protocol_name} "
                f"affects {len(critical_deps[0].dependent_protocols)} of your protocols"
            )

        # Default
        if not recommendations:
            recommendations.append("Portfolio risk is within acceptable limits")

        return recommendations

    async def _map_contagion_to_portfolio(
        self, portfolio: UserPortfolio, contagion: any, origin_name: str
    ) -> List[CascadeImpact]:
        """Map network contagion to portfolio impact."""
        impacts = []

        # Get affected protocols in portfolio
        portfolio_ids = {e.protocol_id for e in portfolio.protocols}

        # Direct impacts
        directly_affected = []
        for wave in contagion.cascade_waves:
            if wave.wave_number == 1:  # Direct connections
                directly_affected.extend(
                    [p for p in wave.affected_protocols if p in portfolio_ids]
                )

        # Indirect impacts
        indirectly_affected = []
        for wave in contagion.cascade_waves:
            if wave.wave_number > 1:
                indirectly_affected.extend(
                    [p for p in wave.affected_protocols if p in portfolio_ids]
                )

        # Calculate exposure at risk
        exposure_at_risk = sum(
            e.value_usd
            for e in portfolio.protocols
            if e.protocol_id in directly_affected + indirectly_affected
        )

        # Create impact
        impacts.append(
            CascadeImpact(
                origin_protocol_id=contagion.origin_protocol_id,
                origin_protocol_name=origin_name,
                directly_affected=[
                    portfolio.get_exposure(pid).protocol_name
                    for pid in directly_affected
                ],
                indirectly_affected=[
                    portfolio.get_exposure(pid).protocol_name
                    for pid in indirectly_affected
                ],
                total_exposure_at_risk_usd=exposure_at_risk,
                cascade_probability=contagion.total_protocols_affected
                / max(len(portfolio.protocols), 1),
                time_to_impact="immediate" if directly_affected else "hours",
            )
        )

        return impacts

    def _generate_cascade_actions(
        self, portfolio: UserPortfolio, impacts: List[CascadeImpact]
    ) -> tuple[List[str], List[str], List[str]]:
        """Generate action recommendations from cascade simulation."""
        to_exit = []
        to_reduce = []
        safe = []

        affected = set()
        for impact in impacts:
            affected.update(impact.directly_affected)
            affected.update(impact.indirectly_affected)

        for protocol in portfolio.protocols:
            if protocol.protocol_name in affected:
                if protocol.protocol_name in [
                    i.directly_affected[0] if i.directly_affected else ""
                    for i in impacts
                ]:
                    to_exit.append(protocol.protocol_name)
                else:
                    to_reduce.append(protocol.protocol_name)
            else:
                safe.append(protocol.protocol_name)

        return to_exit, to_reduce, safe

    def _empty_risk_summary(self, user_id: UUID) -> PortfolioRiskSummary:
        """Return empty risk summary."""
        return PortfolioRiskSummary(
            user_id=user_id,
            overall_risk_score=0.0,
            risk_distribution={"LOW": 0.0, "MEDIUM": 0.0, "HIGH": 0.0, "CRITICAL": 0.0},
            protocols_at_risk=[],
            dependency_risks=[],
            systemic_risk_score=0.0,
            concentration_risk=0.0,
            chain_risk_distribution={},
            recommendations=["No protocols in portfolio"],
            total_value_at_risk_usd=Decimal("0"),
            last_updated=datetime.now(UTC),
        )
