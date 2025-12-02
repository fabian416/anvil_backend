"""
Risk Analysis Service

Domain service for analyzing systemic risks in DeFi protocols using the knowledge graph.
"""

from typing import List, Dict, Any
from uuid import UUID
from dataclasses import dataclass

from app.domain.ports.graph import (
    GraphRepository,
    GraphNode,
    TraversalDirection,
)


@dataclass
class RiskAnalysisResult:
    """Complete risk analysis for a protocol"""
    protocol: GraphNode
    direct_risks: List[GraphNode]
    systemic_risks: List[GraphNode]
    risk_score: float  # 0.0-10.0
    risk_breakdown: Dict[str, float]
    recommendations: List[str]


class RiskAnalysisService:
    """
    Analyze systemic risks for DeFi protocols.
    
    Uses the knowledge graph to identify:
    - Direct risks (attached to protocol)
    - Systemic risks (from dependencies)
    - Cascade risk (failures that propagate)
    - Concentration risk (over-reliance on single protocol)
    """
    
    def __init__(self, graph_repo: GraphRepository):
        """
        Initialize risk analysis service.
        
        Args:
            graph_repo: Graph repository implementation
        """
        self._graph_repo = graph_repo
        
        # Risk severity weights
        self._severity_weights = {
            "low": 1.0,
            "medium": 3.0,
            "high": 7.0,
            "critical": 10.0,
        }
    
    async def analyze_systemic_risk(
        self,
        protocol_id: UUID,
    ) -> RiskAnalysisResult:
        """
        Perform comprehensive systemic risk analysis.
        
        Args:
            protocol_id: UUID of the protocol to analyze
            
        Returns:
            RiskAnalysisResult with complete analysis
            
        Example:
            >>> analysis = await risk_service.analyze_systemic_risk(aave_id)
            >>> print(f"Risk score: {analysis.risk_score}/10")
            >>> print(f"Direct risks: {len(analysis.direct_risks)}")
            >>> print(f"Systemic risks: {len(analysis.systemic_risks)}")
        """
        
        # Get protocol node
        protocol = await self._graph_repo.get_node(protocol_id)
        if not protocol:
            raise ValueError(f"Protocol {protocol_id} not found")
        
        # Get direct risks
        direct_risks = await self._get_direct_risks(protocol_id)
        
        # Get systemic risks (from dependencies)
        systemic_risks = await self._get_systemic_risks(protocol_id)
        
        # Calculate risk score
        risk_score, risk_breakdown = self._calculate_risk_score(
            direct_risks,
            systemic_risks,
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            protocol,
            direct_risks,
            systemic_risks,
            risk_score,
        )
        
        return RiskAnalysisResult(
            protocol=protocol,
            direct_risks=direct_risks,
            systemic_risks=systemic_risks,
            risk_score=risk_score,
            risk_breakdown=risk_breakdown,
            recommendations=recommendations,
        )
    
    async def _get_direct_risks(
        self,
        protocol_id: UUID,
    ) -> List[GraphNode]:
        """Get risks directly attached to protocol"""
        
        return await self._graph_repo.get_neighbors(
            node_id=protocol_id,
            relationship_type="HAS_RISK",
            direction=TraversalDirection.OUTGOING,
        )
    
    async def _get_systemic_risks(
        self,
        protocol_id: UUID,
    ) -> List[GraphNode]:
        """Get risks from dependencies (systemic)"""
        
        # Get all dependencies (up to 2 hops)
        dep_paths = await self._graph_repo.traverse(
            start_node_id=protocol_id,
            relationship_types=["DEPENDS_ON"],
            max_depth=2,
            direction=TraversalDirection.OUTGOING,
        )
        
        systemic_risks = []
        seen_risk_ids = set()
        
        # For each dependency, get its risks
        for path in dep_paths:
            if len(path.nodes) > 1:
                # Last node is the dependency
                dep = path.nodes[-1]
                
                # Get risks of this dependency
                dep_risks = await self._graph_repo.get_neighbors(
                    node_id=dep.id,
                    relationship_type="HAS_RISK",
                    direction=TraversalDirection.OUTGOING,
                )
                
                # Add to systemic risks (avoid duplicates)
                for risk in dep_risks:
                    risk_id = str(risk.id)
                    if risk_id not in seen_risk_ids:
                        systemic_risks.append(risk)
                        seen_risk_ids.add(risk_id)
        
        return systemic_risks
    
    def _calculate_risk_score(
        self,
        direct_risks: List[GraphNode],
        systemic_risks: List[GraphNode],
    ) -> tuple[float, Dict[str, float]]:
        """Calculate overall risk score and breakdown"""
        
        # Calculate direct risk score
        direct_score = sum(
            self._severity_weights.get(
                risk.properties.get("severity", "low"),
                1.0
            )
            for risk in direct_risks
        )
        
        # Calculate systemic risk score (weighted at 50%)
        systemic_score = sum(
            self._severity_weights.get(
                risk.properties.get("severity", "low"),
                1.0
            ) * 0.5
            for risk in systemic_risks
        )
        
        # Breakdown by risk type
        risk_breakdown = {}
        for risk in direct_risks + systemic_risks:
            risk_type = risk.properties.get("type", "other")
            severity = risk.properties.get("severity", "low")
            weight = self._severity_weights.get(severity, 1.0)
            
            if risk_type not in risk_breakdown:
                risk_breakdown[risk_type] = 0.0
            risk_breakdown[risk_type] += weight
        
        # Normalize to 0-10 scale
        total_score = direct_score + systemic_score
        normalized_score = min(total_score / 10.0, 10.0)
        
        return round(normalized_score, 2), risk_breakdown
    
    def _generate_recommendations(
        self,
        protocol: GraphNode,
        direct_risks: List[GraphNode],
        systemic_risks: List[GraphNode],
        risk_score: float,
    ) -> List[str]:
        """Generate risk mitigation recommendations"""
        
        recommendations = []
        
        # Overall risk level
        if risk_score >= 7.0:
            recommendations.append(
                "⚠️ HIGH RISK: Exercise extreme caution when interacting with this protocol"
            )
        elif risk_score >= 4.0:
            recommendations.append(
                "⚠️ MODERATE RISK: Use with caution and consider risk management strategies"
            )
        else:
            recommendations.append(
                "✅ LOW RISK: Protocol has relatively low risk profile"
            )
        
        # Check for unaudited protocol
        if any(r.properties.get("type") == "smart_contract" for r in direct_risks):
            has_audit_risk = any(
                "no audit" in r.properties.get("description", "").lower()
                for r in direct_risks
            )
            if has_audit_risk:
                recommendations.append(
                    "• Protocol lacks security audits - consider using audited alternatives"
                )
        
        # Check for oracle risks
        oracle_risks = [
            r for r in direct_risks + systemic_risks
            if r.properties.get("type") == "oracle"
        ]
        if oracle_risks:
            recommendations.append(
                f"• Oracle dependency risk detected ({len(oracle_risks)} risks) - "
                "ensure price feeds are reliable"
            )
        
        # Check for admin key risks
        admin_risks = [
            r for r in direct_risks
            if r.properties.get("type") == "admin_key"
        ]
        if admin_risks:
            recommendations.append(
                "• Admin key risk present - protocol owners have significant control"
            )
        
        # Check for economic/depeg risks
        depeg_risks = [
            r for r in direct_risks + systemic_risks
            if r.properties.get("type") in ["depeg", "economic"]
        ]
        if depeg_risks:
            recommendations.append(
                "• Stablecoin depeg risk detected - monitor collateral ratios"
            )
        
        # Systemic risks
        if len(systemic_risks) > 5:
            recommendations.append(
                f"• High systemic risk exposure ({len(systemic_risks)} risks from dependencies) - "
                "diversify across protocols"
            )
        
        # Active risks
        active_risks = [
            r for r in direct_risks + systemic_risks
            if r.properties.get("is_active", True)
        ]
        if len(active_risks) > 0:
            recommendations.append(
                f"• {len(active_risks)} active risks identified - review risk details"
            )
        
        return recommendations
    
    async def compare_protocol_risks(
        self,
        protocol_ids: List[UUID],
    ) -> Dict[str, Any]:
        """
        Compare risk profiles of multiple protocols.
        
        Args:
            protocol_ids: List of protocol UUIDs to compare
            
        Returns:
            Dictionary with comparative risk analysis
            
        Example:
            >>> comparison = await risk_service.compare_protocol_risks([aave_id, compound_id])
            >>> print(f"Safest: {comparison['safest']['name']}")
        """
        
        analyses = []
        for protocol_id in protocol_ids:
            analysis = await self.analyze_systemic_risk(protocol_id)
            analyses.append(analysis)
        
        # Sort by risk score (lowest = safest)
        analyses.sort(key=lambda a: a.risk_score)
        
        return {
            "analyses": [
                {
                    "protocol": a.protocol.properties.get("name", "Unknown"),
                    "risk_score": a.risk_score,
                    "direct_risks": len(a.direct_risks),
                    "systemic_risks": len(a.systemic_risks),
                }
                for a in analyses
            ],
            "safest": {
                "name": analyses[0].protocol.properties.get("name", "Unknown"),
                "score": analyses[0].risk_score,
            },
            "riskiest": {
                "name": analyses[-1].protocol.properties.get("name", "Unknown"),
                "score": analyses[-1].risk_score,
            },
        }
    
    async def identify_cascade_risks(
        self,
        protocol_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Identify potential cascade failure risks.
        
        A cascade risk occurs when a protocol failure could propagate
        to dependent protocols.
        
        Args:
            protocol_id: UUID of the protocol
            
        Returns:
            List of cascade risk scenarios
            
        Example:
            >>> cascades = await risk_service.identify_cascade_risks(chainlink_id)
            >>> print(f"Identified {len(cascades)} cascade scenarios")
        """
        
        # Get all protocols that depend on this one
        dependents = await self._graph_repo.get_neighbors(
            node_id=protocol_id,
            relationship_type="DEPENDS_ON",
            direction=TraversalDirection.INCOMING,
        )
        
        cascade_scenarios = []
        
        for dependent in dependents:
            # Check if dependency is marked critical
            edges = await self._graph_repo.find_edges(
                from_id=dependent.id,
                to_id=protocol_id,
                relationship_type="DEPENDS_ON",
            )
            
            for edge in edges:
                criticality = edge.properties.get("criticality", "low")
                can_function_without = edge.properties.get("can_function_without", True)
                
                if criticality in ["high", "critical"] or not can_function_without:
                    cascade_scenarios.append({
                        "dependent_protocol": dependent.properties.get("name", "Unknown"),
                        "dependent_id": str(dependent.id),
                        "dependency_type": edge.properties.get("dependency_type", "unknown"),
                        "criticality": criticality,
                        "can_function_without": can_function_without,
                        "impact": "Protocol would fail if dependency fails" if not can_function_without else "Protocol would be severely impacted",
                    })
        
        return cascade_scenarios
