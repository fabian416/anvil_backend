"""Protocol comparison service for side-by-side analysis."""

from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass


@dataclass
class ProtocolMetrics:
    """Comprehensive protocol metrics for comparison."""

    protocol_id: UUID
    protocol_name: str
    
    # Basic Info
    chain: str
    category: str
    logo_url: Optional[str]
    
    # Risk Metrics (ML-powered)
    risk_score: float  # 0-10
    risk_level: str  # LOW/MEDIUM/HIGH/CRITICAL
    confidence: float  # 0-1
    risk_trend: str  # INCREASING/DECREASING/STABLE
    
    # Financial Metrics
    tvl_usd: float
    tvl_change_24h_percent: float
    tvl_change_7d_percent: float
    volume_24h_usd: Optional[float]
    
    # Yield Metrics
    apy_supply: Optional[float]
    apy_borrow: Optional[float]
    apy_stake: Optional[float]
    
    # Security Metrics
    audit_count: int
    auditor_names: List[str]
    last_audit_date: Optional[str]
    vulnerability_count: int
    
    # Network Metrics
    user_count_24h: Optional[int]
    transaction_count_24h: Optional[int]
    network_centrality: Optional[float]
    
    # Historical
    age_days: int
    incident_count: int
    
    # Governance
    has_governance: bool
    token_symbol: Optional[str]


class ProtocolComparisonService:
    """
    Service for comparing multiple protocols side-by-side.

    Enables users to:
    - Compare metrics across protocols
    - Identify best options for their needs
    - Understand tradeoffs between protocols
    - Get AI-powered recommendations
    """

    def __init__(self):
        # TODO: Inject dependencies (repositories, ML service, GraphRAG)
        pass

    async def compare_protocols(
        self,
        protocol_ids: List[UUID],
        dimensions: Optional[List[str]] = None,
    ) -> dict:
        """
        Compare multiple protocols across key dimensions.

        Args:
            protocol_ids: List of protocol UUIDs to compare (2-5 protocols)
            dimensions: Optional list of dimensions to compare
                       (risk, yield, security, network, all)

        Returns:
            Comprehensive comparison data
        """
        if len(protocol_ids) < 2:
            raise ValueError("Must compare at least 2 protocols")
        if len(protocol_ids) > 5:
            raise ValueError("Cannot compare more than 5 protocols at once")

        # Default dimensions
        if dimensions is None:
            dimensions = ["risk", "yield", "security", "network"]

        # TODO: Fetch protocol metrics from repositories
        # For now, return structured comparison format
        protocols = await self._fetch_protocol_metrics(protocol_ids)

        comparison = {
            "protocols": [self._serialize_metrics(p) for p in protocols],
            "comparison_matrix": self._build_comparison_matrix(
                protocols, dimensions
            ),
            "winner_by_dimension": self._determine_winners(protocols, dimensions),
            "trade_offs": self._identify_tradeoffs(protocols),
            "recommendation": await self._generate_recommendation(protocols),
        }

        return comparison

    async def _fetch_protocol_metrics(
        self, protocol_ids: List[UUID]
    ) -> List[ProtocolMetrics]:
        """Fetch metrics for all protocols (TODO: implement)."""
        # TODO: Fetch from repositories
        # Placeholder for structure
        return []

    def _serialize_metrics(self, protocol: ProtocolMetrics) -> dict:
        """Serialize protocol metrics to dict."""
        return {
            "protocol_id": str(protocol.protocol_id),
            "name": protocol.protocol_name,
            "chain": protocol.chain,
            "category": protocol.category,
            "logo_url": protocol.logo_url,
            "risk": {
                "score": protocol.risk_score,
                "level": protocol.risk_level,
                "confidence": protocol.confidence,
                "trend": protocol.risk_trend,
            },
            "tvl": {
                "current_usd": protocol.tvl_usd,
                "change_24h_percent": protocol.tvl_change_24h_percent,
                "change_7d_percent": protocol.tvl_change_7d_percent,
            },
            "yield": {
                "supply_apy": protocol.apy_supply,
                "borrow_apy": protocol.apy_borrow,
                "stake_apy": protocol.apy_stake,
            },
            "security": {
                "audit_count": protocol.audit_count,
                "auditors": protocol.auditor_names,
                "last_audit": protocol.last_audit_date,
                "vulnerabilities": protocol.vulnerability_count,
            },
            "network": {
                "users_24h": protocol.user_count_24h,
                "transactions_24h": protocol.transaction_count_24h,
                "centrality": protocol.network_centrality,
            },
            "historical": {
                "age_days": protocol.age_days,
                "incidents": protocol.incident_count,
            },
        }

    def _build_comparison_matrix(
        self, protocols: List[ProtocolMetrics], dimensions: List[str]
    ) -> dict:
        """
        Build comparison matrix showing relative performance.

        Returns dict mapping dimensions to protocol comparisons.
        """
        matrix = {}

        if "risk" in dimensions:
            matrix["risk"] = self._compare_risk(protocols)

        if "yield" in dimensions:
            matrix["yield"] = self._compare_yield(protocols)

        if "security" in dimensions:
            matrix["security"] = self._compare_security(protocols)

        if "network" in dimensions:
            matrix["network"] = self._compare_network(protocols)

        return matrix

    def _compare_risk(self, protocols: List[ProtocolMetrics]) -> dict:
        """Compare protocols by risk metrics."""
        return {
            "metric": "Risk Score",
            "lower_is_better": True,
            "values": [
                {
                    "protocol": p.protocol_name,
                    "value": p.risk_score,
                    "label": p.risk_level,
                    "trend": p.risk_trend,
                }
                for p in protocols
            ],
            "best": min(protocols, key=lambda p: p.risk_score).protocol_name,
            "worst": max(protocols, key=lambda p: p.risk_score).protocol_name,
        }

    def _compare_yield(self, protocols: List[ProtocolMetrics]) -> dict:
        """Compare protocols by yield metrics."""
        # Get max supply APY for each protocol
        max_apys = [
            max(
                filter(None, [p.apy_supply, p.apy_borrow, p.apy_stake]),
                default=0
            )
            for p in protocols
        ]

        return {
            "metric": "Max APY",
            "lower_is_better": False,
            "values": [
                {
                    "protocol": p.protocol_name,
                    "value": apy,
                    "supply_apy": p.apy_supply,
                    "borrow_apy": p.apy_borrow,
                    "stake_apy": p.apy_stake,
                }
                for p, apy in zip(protocols, max_apys)
            ],
            "best": protocols[max_apys.index(max(max_apys))].protocol_name
            if max_apys else None,
        }

    def _compare_security(self, protocols: List[ProtocolMetrics]) -> dict:
        """Compare protocols by security metrics."""
        # Security score: more audits + fewer vulnerabilities = better
        security_scores = [
            (p.audit_count * 10) - (p.vulnerability_count * 5)
            for p in protocols
        ]

        return {
            "metric": "Security Score",
            "lower_is_better": False,
            "values": [
                {
                    "protocol": p.protocol_name,
                    "score": score,
                    "audits": p.audit_count,
                    "vulnerabilities": p.vulnerability_count,
                    "auditors": p.auditor_names,
                }
                for p, score in zip(protocols, security_scores)
            ],
            "best": protocols[security_scores.index(max(security_scores))].protocol_name
            if security_scores else None,
        }

    def _compare_network(self, protocols: List[ProtocolMetrics]) -> dict:
        """Compare protocols by network activity."""
        return {
            "metric": "Network Activity",
            "lower_is_better": False,
            "values": [
                {
                    "protocol": p.protocol_name,
                    "users_24h": p.user_count_24h,
                    "transactions_24h": p.transaction_count_24h,
                    "centrality": p.network_centrality,
                }
                for p in protocols
            ],
        }

    def _determine_winners(
        self, protocols: List[ProtocolMetrics], dimensions: List[str]
    ) -> dict:
        """Determine which protocol wins in each dimension."""
        winners = {}

        if "risk" in dimensions:
            winners["safest"] = min(
                protocols, key=lambda p: p.risk_score
            ).protocol_name

        if "yield" in dimensions:
            max_apys = [
                max(
                    filter(None, [p.apy_supply, p.apy_borrow, p.apy_stake]),
                    default=0
                )
                for p in protocols
            ]
            if max_apys:
                winners["highest_yield"] = protocols[
                    max_apys.index(max(max_apys))
                ].protocol_name

        if "security" in dimensions:
            winners["most_secure"] = max(
                protocols, key=lambda p: p.audit_count
            ).protocol_name

        if "network" in dimensions:
            winners["most_active"] = max(
                protocols,
                key=lambda p: p.transaction_count_24h or 0
            ).protocol_name

        # Overall winner (balanced across all dimensions)
        winners["balanced"] = self._calculate_balanced_winner(protocols)

        return winners

    def _calculate_balanced_winner(
        self, protocols: List[ProtocolMetrics]
    ) -> str:
        """Calculate overall best protocol considering all factors."""
        # Scoring: low risk + high yield + high security + high activity
        scores = []

        for p in protocols:
            # Normalize scores to 0-100 scale
            risk_score = (10 - p.risk_score) * 10  # Lower is better
            yield_score = max(
                filter(None, [p.apy_supply, p.apy_borrow, p.apy_stake]),
                default=0
            )
            security_score = (p.audit_count * 10) - (p.vulnerability_count * 5)
            activity_score = (p.transaction_count_24h or 0) / 1000  # Normalized

            total_score = (
                risk_score * 0.4
                + yield_score * 0.3
                + security_score * 0.2
                + activity_score * 0.1
            )
            scores.append(total_score)

        return protocols[scores.index(max(scores))].protocol_name

    def _identify_tradeoffs(self, protocols: List[ProtocolMetrics]) -> List[dict]:
        """Identify key tradeoffs between protocols."""
        tradeoffs = []

        # Risk vs Yield tradeoff
        risk_scores = [p.risk_score for p in protocols]
        yields = [
            max(
                filter(None, [p.apy_supply, p.apy_borrow, p.apy_stake]),
                default=0
            )
            for p in protocols
        ]

        if len(set(risk_scores)) > 1 and len(set(yields)) > 1:
            safest = min(protocols, key=lambda p: p.risk_score)
            highest_yield = protocols[yields.index(max(yields))]

            if safest.protocol_id != highest_yield.protocol_id:
                tradeoffs.append({
                    "dimension": "Risk vs Yield",
                    "description": f"{safest.protocol_name} is safest (risk: {safest.risk_score:.1f}) "
                                   f"but {highest_yield.protocol_name} offers higher yield ({max(yields):.1f}% APY)",
                })

        # TVL vs Risk tradeoff
        largest_tvl = max(protocols, key=lambda p: p.tvl_usd)
        safest = min(protocols, key=lambda p: p.risk_score)

        if largest_tvl.protocol_id != safest.protocol_id:
            tradeoffs.append({
                "dimension": "Size vs Safety",
                "description": f"{largest_tvl.protocol_name} has largest TVL "
                               f"(${largest_tvl.tvl_usd/1e9:.1f}B) but "
                               f"{safest.protocol_name} is safer (risk: {safest.risk_score:.1f})",
            })

        return tradeoffs

    async def _generate_recommendation(
        self, protocols: List[ProtocolMetrics]
    ) -> dict:
        """Generate AI-powered recommendation."""
        # Calculate balanced winner
        balanced_winner = self._calculate_balanced_winner(protocols)
        winner = next(p for p in protocols if p.protocol_name == balanced_winner)

        return {
            "recommended_protocol": balanced_winner,
            "reason": f"Best balance of safety (risk: {winner.risk_score:.1f}), "
                      f"yield, and security across all compared protocols",
            "confidence": 0.85,  # TODO: Calculate based on data quality
            "alternatives": [
                p.protocol_name for p in protocols
                if p.protocol_name != balanced_winner
            ],
        }
