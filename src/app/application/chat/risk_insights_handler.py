"""Chat ML risk analysis integration handler."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.application.graph.hybrid_retrieval import HybridRetrievalInteractor
from app.domain.ports.graph.graph_repository import GraphRepository
from app.domain.services.ml.risk_prediction_service import (
    RiskLevel,
    RiskPrediction,
    RiskPredictionService,
)


@dataclass
class ChatRiskFactor:
    """Risk factor formatted for chat."""

    factor: str
    impact: float  # -10 to +10
    description: str
    is_critical: bool


@dataclass
class ChatAlternativeProtocol:
    """Alternative protocol suggestion for chat."""

    protocol_id: UUID
    protocol_name: str
    similarity_score: float
    risk_score: float
    risk_level: str
    tvl: float
    apy: Optional[float]
    why_better: str


@dataclass
class ChatRiskAnalysis:
    """Risk analysis formatted for chat."""

    protocol_id: UUID
    protocol_name: str
    risk_score: float  # 0-10
    risk_level: str  # LOW/MEDIUM/HIGH/CRITICAL
    confidence: float  # 0-1
    contributing_factors: List[ChatRiskFactor]
    recommendations: List[str]
    should_warn: bool
    warning_message: Optional[str]


@dataclass
class RiskInsightResponse:
    """Complete risk insight response for chat."""

    risk_analysis: ChatRiskAnalysis
    alternatives: List[ChatAlternativeProtocol]
    contextual_message: str


class ChatRiskInsightsHandler:
    """Handle ML risk analysis requests from chat.

    This service integrates ML risk prediction with natural language
    generation to provide chat-friendly risk insights and warnings.
    """

    def __init__(
        self,
        risk_prediction_service: RiskPredictionService,
        hybrid_retrieval: HybridRetrievalInteractor,
        graph_repository: GraphRepository,
    ):
        self._risk_service = risk_prediction_service
        self._hybrid_retrieval = hybrid_retrieval
        self._graph_repo = graph_repository

    async def get_protocol_risk_from_chat(
        self,
        protocol_name: str,
        conversation_id: UUID,
        operation_type: Optional[str] = None,
        amount_usd: Optional[float] = None,
    ) -> RiskInsightResponse:
        """
        Get risk insights for a protocol mentioned in chat.

        Args:
            protocol_name: Name of the protocol
            conversation_id: Conversation ID for context
            operation_type: Optional operation type (supply, borrow, etc.)
            amount_usd: Optional amount in USD

        Returns:
            Complete risk insight response with alternatives
        """
        # Find protocol by name
        protocol = await self._find_protocol_by_name(protocol_name)
        if not protocol:
            raise ValueError(f"Protocol '{protocol_name}' not found")

        # Get ML risk prediction
        risk_prediction = await self._risk_service.predict_risk(protocol.id)

        # Convert to chat-friendly format
        risk_analysis = self._convert_to_chat_risk(risk_prediction, operation_type)

        # Find alternatives if risk is high
        alternatives = []
        if risk_analysis.should_warn:
            alternatives = await self._find_safer_alternatives(
                protocol_name, protocol.id, risk_analysis.risk_score
            )

        # Generate contextual message
        contextual_message = self._generate_risk_message(
            risk_analysis, alternatives, operation_type, amount_usd
        )

        return RiskInsightResponse(
            risk_analysis=risk_analysis,
            alternatives=alternatives,
            contextual_message=contextual_message,
        )

    async def _find_protocol_by_name(self, protocol_name: str):
        """Find protocol by name using hybrid search."""
        # Use exact name search via graph repository
        results = await self._graph_repo.find_nodes_by_property(
            node_type="Protocol", property_name="name", property_value=protocol_name
        )

        if not results:
            # Try fuzzy search
            search_results = await self._hybrid_retrieval.search_protocols(
                query=protocol_name, limit=1, similarity_threshold=0.8
            )
            if search_results:
                # Get node for first result
                results = await self._graph_repo.get_node(
                    search_results[0].protocol_id
                )
                if results:
                    return results

        return results[0] if results else None

    def _convert_to_chat_risk(
        self, prediction: RiskPrediction, operation_type: Optional[str]
    ) -> ChatRiskAnalysis:
        """Convert ML risk prediction to chat-friendly format."""
        # Convert factors
        chat_factors = []
        for factor in prediction.contributing_factors:
            chat_factors.append(
                ChatRiskFactor(
                    factor=factor.feature,
                    impact=factor.impact * 10,  # Scale to -10 to +10
                    description=factor.explanation,
                    is_critical=abs(factor.impact) > 0.7,
                )
            )

        # Determine if warning should be shown
        should_warn = (
            prediction.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            or prediction.risk_score >= 7.0
        )

        # Generate warning message if needed
        warning_message = None
        if should_warn:
            warning_message = self._generate_warning_message(
                prediction, operation_type
            )

        # Enhance recommendations with operation-specific advice
        recommendations = self._enhance_recommendations(
            prediction.recommendations, operation_type
        )

        return ChatRiskAnalysis(
            protocol_id=prediction.protocol_id,
            protocol_name=prediction.protocol_name,
            risk_score=prediction.risk_score,
            risk_level=prediction.risk_level.value,
            confidence=prediction.confidence,
            contributing_factors=chat_factors[:5],  # Top 5 factors
            recommendations=recommendations,
            should_warn=should_warn,
            warning_message=warning_message,
        )

    def _generate_warning_message(
        self, prediction: RiskPrediction, operation_type: Optional[str]
    ) -> str:
        """Generate contextual warning message."""
        operation_text = ""
        if operation_type:
            operation_text = f" for {operation_type} operations"

        if prediction.risk_level == RiskLevel.CRITICAL:
            return f"⚠️ **CRITICAL RISK DETECTED**: {prediction.protocol_name} has a very high risk score ({prediction.risk_score:.1f}/10){operation_text}. I strongly recommend considering safer alternatives."
        elif prediction.risk_level == RiskLevel.HIGH:
            return f"⚠️ **HIGH RISK**: {prediction.protocol_name} has elevated risk ({prediction.risk_score:.1f}/10){operation_text}. Please review risk factors carefully before proceeding."
        elif prediction.risk_score >= 7.0:
            return f"⚠️ **Risk Warning**: {prediction.protocol_name} has a risk score of {prediction.risk_score:.1f}/10{operation_text}. Consider reviewing alternatives."

        return ""

    def _enhance_recommendations(
        self, recommendations: List[str], operation_type: Optional[str]
    ) -> List[str]:
        """Enhance recommendations with operation-specific advice."""
        enhanced = list(recommendations)

        # Add operation-specific recommendations
        if operation_type == "supply" or operation_type == "lend":
            enhanced.append(
                "For lending, ensure you understand liquidation risks and collateral requirements"
            )
        elif operation_type == "borrow":
            enhanced.append(
                "Monitor your health factor closely to avoid liquidation"
            )
            enhanced.append("Consider using stablecoins as collateral to reduce volatility risk")
        elif operation_type == "stake":
            enhanced.append("Verify the unbonding period and withdrawal restrictions")
            enhanced.append("Consider the smart contract risk of the staking protocol")
        elif operation_type == "swap":
            enhanced.append("Check slippage tolerance and price impact before swapping")
            enhanced.append("Use limit orders for large swaps to get better prices")

        return enhanced

    async def _find_safer_alternatives(
        self, protocol_name: str, protocol_id: UUID, current_risk_score: float
    ) -> List[ChatAlternativeProtocol]:
        """Find safer alternative protocols using hybrid search and ML."""
        # Find similar protocols
        similar_results = await self._hybrid_retrieval.find_similar_protocols(
            protocol_id=protocol_id, limit=10, similarity_threshold=0.6
        )

        alternatives = []
        for result in similar_results:
            # Get risk prediction for alternative
            alt_risk = await self._risk_service.predict_risk(result.protocol_id)

            # Only suggest if risk is lower
            if alt_risk.risk_score < current_risk_score:
                why_better = self._explain_why_better(
                    current_risk_score, alt_risk.risk_score, alt_risk
                )

                alternatives.append(
                    ChatAlternativeProtocol(
                        protocol_id=result.protocol_id,
                        protocol_name=result.protocol_name,
                        similarity_score=result.combined_score,
                        risk_score=alt_risk.risk_score,
                        risk_level=alt_risk.risk_level.value,
                        tvl=result.tvl,
                        apy=None,  # Would come from external data
                        why_better=why_better,
                    )
                )

        # Sort by risk score (lowest first)
        alternatives.sort(key=lambda x: x.risk_score)

        # Return top 3
        return alternatives[:3]

    def _explain_why_better(
        self, current_risk: float, alt_risk: float, alt_prediction: RiskPrediction
    ) -> str:
        """Explain why alternative is better."""
        risk_reduction = current_risk - alt_risk
        reasons = [f"{risk_reduction:.1f} points lower risk"]

        # Add specific positive factors
        positive_factors = [
            f for f in alt_prediction.contributing_factors if f.impact < -0.3
        ]
        if positive_factors:
            # Get top positive factor
            top_factor = min(positive_factors, key=lambda f: f.impact)
            reasons.append(top_factor.explanation.split(":")[0])  # First part

        return "; ".join(reasons)

    def _generate_risk_message(
        self,
        risk_analysis: ChatRiskAnalysis,
        alternatives: List[ChatAlternativeProtocol],
        operation_type: Optional[str],
        amount_usd: Optional[float],
    ) -> str:
        """Generate contextual message about risk."""
        messages = []

        # Risk summary
        if risk_analysis.should_warn:
            messages.append(risk_analysis.warning_message or "Risk warning detected.")

            if alternatives:
                messages.append(
                    f"\nI found {len(alternatives)} safer alternative{'s' if len(alternatives) > 1 else ''} with similar functionality:"
                )
        else:
            confidence_pct = int(risk_analysis.confidence * 100)
            messages.append(
                f"{risk_analysis.protocol_name} has a {risk_analysis.risk_level.lower()} risk level "
                f"(score: {risk_analysis.risk_score:.1f}/10, {confidence_pct}% confidence)."
            )

        # Amount context
        if amount_usd and risk_analysis.should_warn:
            messages.append(
                f"\nWith ${amount_usd:,.0f} at stake, I recommend extra caution."
            )

        # Operation context
        if operation_type:
            operation_risks = self._get_operation_specific_risks(operation_type)
            if operation_risks:
                messages.append(f"\n{operation_risks}")

        return " ".join(messages)

    def _get_operation_specific_risks(self, operation_type: str) -> str:
        """Get operation-specific risk information."""
        risks = {
            "supply": "Supplying funds exposes you to smart contract risk and potential liquidity issues.",
            "borrow": "Borrowing carries liquidation risk if collateral value drops.",
            "stake": "Staking typically has unbonding periods where funds are locked.",
            "swap": "Large swaps can have significant price impact and slippage.",
            "bridge": "Cross-chain bridges carry additional smart contract and bridge security risks.",
        }
        return risks.get(operation_type, "")


async def should_show_risk_warning(
    protocol_name: str,
    risk_handler: ChatRiskInsightsHandler,
    conversation_id: UUID,
    operation_type: Optional[str] = None,
) -> bool:
    """
    Helper function to determine if risk warning should be shown.

    Args:
        protocol_name: Name of the protocol
        risk_handler: Risk insights handler instance
        conversation_id: Conversation ID
        operation_type: Optional operation type

    Returns:
        True if risk warning should be shown
    """
    try:
        insights = await risk_handler.get_protocol_risk_from_chat(
            protocol_name=protocol_name,
            conversation_id=conversation_id,
            operation_type=operation_type,
        )
        return insights.risk_analysis.should_warn
    except Exception:
        # If unable to get risk, show warning to be safe
        return True
