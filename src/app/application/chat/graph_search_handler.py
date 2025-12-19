"""Chat GraphRAG search integration handler."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.application.graph.hybrid_retrieval import (
    HybridRetrievalInteractor,
    HybridRetrievalResult,
)
from app.domain.graph.ports.graph_repository import GraphRepository


@dataclass
class ChatProtocolSearchResult:
    """Protocol search result formatted for chat."""

    protocol_id: UUID
    protocol_name: str
    similarity_score: float  # 0-1
    risk_score: float  # 0-10
    risk_level: str  # LOW/MEDIUM/HIGH/CRITICAL
    tvl: float
    apy: Optional[float]
    audit_count: int
    description: str
    category: str
    chain: str
    why_relevant: str  # Why this was suggested


@dataclass
class ChatSearchContext:
    """Context for chat search results."""

    results: List[ChatProtocolSearchResult]
    search_explanation: str
    recommendations: List[str]


class ChatGraphSearchHandler:
    """Handle GraphRAG searches from chat messages.

    This service integrates hybrid retrieval with natural language
    understanding to provide chat-friendly protocol search results.
    """

    def __init__(
        self,
        hybrid_retrieval: HybridRetrievalInteractor,
        graph_repository: GraphRepository,
    ):
        self._hybrid_retrieval = hybrid_retrieval
        self._graph_repo = graph_repository

    async def search_protocols_from_chat(
        self,
        message: str,
        user_preferences: Optional[dict] = None,
        conversation_id: Optional[UUID] = None,
    ) -> ChatSearchContext:
        """
        Extract search intent and perform hybrid search.

        Args:
            message: User's natural language message
            user_preferences: Optional user preferences for filtering
            conversation_id: Optional conversation ID for context

        Returns:
            Chat-formatted search results with explanations
        """
        # Extract search parameters from natural language
        search_params = self._extract_search_intent(message, user_preferences)

        # Perform hybrid retrieval
        retrieval_results = await self._hybrid_retrieval.search_protocols(
            query=search_params["query"],
            limit=search_params.get("limit", 5),
            similarity_threshold=search_params.get("similarity_threshold", 0.7),
            include_risks=True,
        )

        # Convert to chat-friendly format
        chat_results = [
            self._convert_to_chat_result(result, search_params)
            for result in retrieval_results
        ]

        # Filter by user preferences if provided
        if user_preferences:
            chat_results = self._apply_user_filters(chat_results, user_preferences)

        # Generate natural language explanation
        explanation = self._generate_search_explanation(
            message, len(chat_results), search_params
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            chat_results, search_params, user_preferences
        )

        return ChatSearchContext(
            results=chat_results,
            search_explanation=explanation,
            recommendations=recommendations,
        )

    def _extract_search_intent(
        self, message: str, user_preferences: Optional[dict]
    ) -> dict:
        """Extract search parameters from natural language message.

        Uses keyword detection and pattern matching to understand user intent.
        In production, this could use an LLM for better understanding.
        """
        message_lower = message.lower()
        params = {
            "query": message,  # Full message as base query
            "limit": 5,
            "similarity_threshold": 0.7,
        }

        # Detect risk preferences
        if any(
            word in message_lower
            for word in ["safe", "low-risk", "secure", "conservative"]
        ):
            params["risk_level"] = "LOW"
            params["query"] = message_lower.replace("low-risk", "").replace(
                "safe", ""
            ).strip()
        elif any(
            word in message_lower
            for word in ["risky", "high-risk", "aggressive", "volatile"]
        ):
            params["risk_level"] = "HIGH"

        # Detect TVL requirements
        if "high tvl" in message_lower or "large" in message_lower:
            params["min_tvl"] = 1_000_000_000  # $1B+

        # Detect operation type
        if any(word in message_lower for word in ["staking", "stake", "earn rewards"]):
            params["category"] = "Staking"
        elif any(word in message_lower for word in ["lending", "supply", "borrow"]):
            params["category"] = "Lending"
        elif any(word in message_lower for word in ["swap", "dex", "exchange"]):
            params["category"] = "DEX"
        elif any(word in message_lower for word in ["bridge", "cross-chain"]):
            params["category"] = "Bridge"

        # Detect chain preference
        if "ethereum" in message_lower or " eth " in message_lower:
            params["chain"] = "Ethereum"
        elif "arbitrum" in message_lower or " arb " in message_lower:
            params["chain"] = "Arbitrum"
        elif "polygon" in message_lower:
            params["chain"] = "Polygon"
        elif "base" in message_lower:
            params["chain"] = "Base"

        # Detect result count
        if "top" in message_lower:
            # Extract number after "top"
            import re

            match = re.search(r"top\s+(\d+)", message_lower)
            if match:
                params["limit"] = int(match.group(1))

        return params

    def _convert_to_chat_result(
        self, result: HybridRetrievalResult, search_params: dict
    ) -> ChatProtocolSearchResult:
        """Convert hybrid retrieval result to chat-friendly format."""
        # Classify risk level
        risk_level = self._classify_risk_level(result.risk_score)

        # Generate relevance explanation
        why_relevant = self._explain_relevance(result, search_params)

        return ChatProtocolSearchResult(
            protocol_id=result.protocol_id,
            protocol_name=result.protocol_name,
            similarity_score=result.combined_score,  # Using combined score
            risk_score=result.risk_score,
            risk_level=risk_level,
            tvl=result.tvl,
            apy=None,  # Would come from external data sources
            audit_count=result.audit_count,
            description=result.description or "No description available",
            category=result.category or "Unknown",
            chain=result.chain or "Multi-chain",
            why_relevant=why_relevant,
        )

    def _classify_risk_level(self, risk_score: float) -> str:
        """Classify risk score into level."""
        if risk_score < 3.0:
            return "LOW"
        elif risk_score < 5.0:
            return "MEDIUM"
        elif risk_score < 7.0:
            return "HIGH"
        else:
            return "CRITICAL"

    def _explain_relevance(
        self, result: HybridRetrievalResult, search_params: dict
    ) -> str:
        """Generate explanation for why protocol is relevant."""
        reasons = []

        # High similarity
        if result.combined_score > 0.8:
            reasons.append("High semantic match to your search")

        # Category match
        if "category" in search_params and result.category == search_params["category"]:
            reasons.append(f"{result.category} protocol as requested")

        # Chain match
        if "chain" in search_params and result.chain == search_params["chain"]:
            reasons.append(f"Deployed on {result.chain}")

        # Risk match
        risk_level = self._classify_risk_level(result.risk_score)
        if "risk_level" in search_params and risk_level == search_params["risk_level"]:
            reasons.append(f"{risk_level.lower()}-risk as preferred")

        # High TVL
        if result.tvl > 1_000_000_000:
            reasons.append(f"High TVL (${result.tvl/1e9:.1f}B)")

        # Well audited
        if result.audit_count >= 5:
            reasons.append(f"Well audited ({result.audit_count} audits)")

        # Default
        if not reasons:
            reasons.append("Matches your search criteria")

        return "; ".join(reasons)

    def _apply_user_filters(
        self, results: List[ChatProtocolSearchResult], preferences: dict
    ) -> List[ChatProtocolSearchResult]:
        """Filter results based on user preferences."""
        filtered = results

        # Filter by risk tolerance
        if "risk_tolerance" in preferences:
            tolerance = preferences["risk_tolerance"]
            if tolerance == "conservative":
                filtered = [r for r in filtered if r.risk_level == "LOW"]
            elif tolerance == "moderate":
                filtered = [r for r in filtered if r.risk_level in ["LOW", "MEDIUM"]]
            # Aggressive allows all

        # Filter by preferred chains
        if "preferred_chains" in preferences:
            chains = preferences["preferred_chains"]
            filtered = [r for r in filtered if r.chain in chains]

        # Filter by preferred categories
        if "preferred_categories" in preferences:
            categories = preferences["preferred_categories"]
            filtered = [r for r in filtered if r.category in categories]

        # Exclude protocols
        if "excluded_protocols" in preferences:
            excluded = {UUID(pid) for pid in preferences["excluded_protocols"]}
            filtered = [r for r in filtered if r.protocol_id not in excluded]

        return filtered

    def _generate_search_explanation(
        self, message: str, result_count: int, search_params: dict
    ) -> str:
        """Generate natural language explanation of search results."""
        if result_count == 0:
            return "I couldn't find any protocols matching your criteria. Try broadening your search or adjusting your preferences."

        explanation_parts = [f"Found {result_count} protocol{'s' if result_count != 1 else ''}"]

        # Add filters explanation
        filters = []
        if "risk_level" in search_params:
            filters.append(f"{search_params['risk_level'].lower()}-risk")
        if "category" in search_params:
            filters.append(search_params["category"].lower())
        if "chain" in search_params:
            filters.append(f"on {search_params['chain']}")

        if filters:
            explanation_parts.append("that are " + ", ".join(filters))

        return " ".join(explanation_parts) + "."

    def _generate_recommendations(
        self,
        results: List[ChatProtocolSearchResult],
        search_params: dict,
        user_preferences: Optional[dict],
    ) -> List[str]:
        """Generate contextual recommendations based on results."""
        if not results:
            return [
                "Try broadening your search criteria",
                "Consider exploring different protocol categories",
                "Check your risk tolerance settings",
            ]

        recommendations = []

        # Risk-based recommendations
        avg_risk = sum(r.risk_score for r in results) / len(results)
        if avg_risk > 5.0:
            recommendations.append(
                "Consider reviewing the risk factors before proceeding"
            )

        # TVL-based recommendations
        if results[0].tvl < 10_000_000:  # Less than $10M
            recommendations.append(
                "Low TVL protocols may have higher liquidity risk"
            )

        # Audit-based recommendations
        if any(r.audit_count < 3 for r in results):
            recommendations.append(
                "Some protocols have limited audit history - proceed with caution"
            )

        # Diversification
        unique_categories = len({r.category for r in results})
        if unique_categories > 1:
            recommendations.append(
                "Consider diversifying across multiple protocol types"
            )

        # Default recommendation
        if not recommendations:
            recommendations.append(
                "All protocols meet your criteria - review details before selecting"
            )

        return recommendations
