"""Chat GraphRAG search integration handler.

Supports multi-language queries and responses (EN, ES, PT, ZH, FR).
"""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from app.application.graph.hybrid_retrieval import (
    HybridRetrievalInteractor,
    HybridRetrievalResult,
)
from app.domain.graph.ports.graph_repository import GraphRepository


# Multi-language translations for GraphRAG responses
GRAPHRAG_TRANSLATIONS = {
    "en": {
        "no_results": "I couldn't find any protocols matching your criteria. Try broadening your search or adjusting your preferences.",
        "found_protocols": "Found {count} protocol{plural}",
        "that_are": "that are",
        "on_chain": "on {chain}",
        "risk": "{level}-risk",
        "risk_warning": "Consider reviewing the risk factors before proceeding",
        "low_tvl_warning": "Low TVL protocols may have higher liquidity risk",
        "audit_warning": "Some protocols have limited audit history - proceed with caution",
        "diversify": "Consider diversifying across multiple protocol types",
        "all_good": "All protocols meet your criteria - review details before selecting",
        "broaden_search": "Try broadening your search criteria",
        "explore_categories": "Consider exploring different protocol categories",
        "check_risk": "Check your risk tolerance settings",
        "high_match": "High semantic match to your search",
        "category_match": "{category} protocol as requested",
        "deployed_on": "Deployed on {chain}",
        "high_tvl": "High TVL (${tvl}B)",
        "well_audited": "Well audited ({count} audits)",
        "matches_criteria": "Matches your search criteria",
    },
    "es": {
        "no_results": "No pude encontrar protocolos que coincidan con tus criterios. Intenta ampliar tu búsqueda o ajustar tus preferencias.",
        "found_protocols": "Encontré {count} protocolo{plural}",
        "that_are": "que son",
        "on_chain": "en {chain}",
        "risk": "riesgo {level}",
        "risk_warning": "Considera revisar los factores de riesgo antes de continuar",
        "low_tvl_warning": "Los protocolos con bajo TVL pueden tener mayor riesgo de liquidez",
        "audit_warning": "Algunos protocolos tienen historial de auditorías limitado - procede con precaución",
        "diversify": "Considera diversificar entre múltiples tipos de protocolos",
        "all_good": "Todos los protocolos cumplen tus criterios - revisa los detalles antes de seleccionar",
        "broaden_search": "Intenta ampliar tus criterios de búsqueda",
        "explore_categories": "Considera explorar diferentes categorías de protocolos",
        "check_risk": "Revisa tu configuración de tolerancia al riesgo",
        "high_match": "Alta coincidencia semántica con tu búsqueda",
        "category_match": "Protocolo {category} como solicitaste",
        "deployed_on": "Desplegado en {chain}",
        "high_tvl": "Alto TVL (${tvl}B)",
        "well_audited": "Bien auditado ({count} auditorías)",
        "matches_criteria": "Coincide con tus criterios de búsqueda",
    },
    "pt": {
        "no_results": "Não encontrei protocolos que correspondam aos seus critérios. Tente ampliar sua busca ou ajustar suas preferências.",
        "found_protocols": "Encontrei {count} protocolo{plural}",
        "that_are": "que são",
        "on_chain": "na {chain}",
        "risk": "risco {level}",
        "risk_warning": "Considere revisar os fatores de risco antes de prosseguir",
        "low_tvl_warning": "Protocolos com baixo TVL podem ter maior risco de liquidez",
        "audit_warning": "Alguns protocolos têm histórico de auditorias limitado - prossiga com cautela",
        "diversify": "Considere diversificar entre múltiplos tipos de protocolos",
        "all_good": "Todos os protocolos atendem seus critérios - revise os detalhes antes de selecionar",
        "broaden_search": "Tente ampliar seus critérios de busca",
        "explore_categories": "Considere explorar diferentes categorias de protocolos",
        "check_risk": "Verifique suas configurações de tolerância ao risco",
        "high_match": "Alta correspondência semântica com sua busca",
        "category_match": "Protocolo {category} conforme solicitado",
        "deployed_on": "Implantado na {chain}",
        "high_tvl": "Alto TVL (${tvl}B)",
        "well_audited": "Bem auditado ({count} auditorias)",
        "matches_criteria": "Corresponde aos seus critérios de busca",
    },
    "zh": {
        "no_results": "未能找到符合您条件的协议。请尝试扩大搜索范围或调整您的偏好。",
        "found_protocols": "找到 {count} 个协议",
        "that_are": "属于",
        "on_chain": "在 {chain} 上",
        "risk": "{level}风险",
        "risk_warning": "请在继续之前查看风险因素",
        "low_tvl_warning": "低TVL协议可能有更高的流动性风险",
        "audit_warning": "部分协议审计历史有限 - 请谨慎操作",
        "diversify": "考虑在多种协议类型之间进行多元化",
        "all_good": "所有协议都符合您的条件 - 选择前请查看详情",
        "broaden_search": "尝试扩大您的搜索条件",
        "explore_categories": "考虑探索不同的协议类别",
        "check_risk": "检查您的风险承受能力设置",
        "high_match": "与您的搜索高度语义匹配",
        "category_match": "您请求的{category}协议",
        "deployed_on": "部署在{chain}",
        "high_tvl": "高TVL (${tvl}B)",
        "well_audited": "审计良好 ({count}次审计)",
        "matches_criteria": "符合您的搜索条件",
    },
    "fr": {
        "no_results": "Je n'ai trouvé aucun protocole correspondant à vos critères. Essayez d'élargir votre recherche ou d'ajuster vos préférences.",
        "found_protocols": "{count} protocole{plural} trouvé{plural}",
        "that_are": "qui sont",
        "on_chain": "sur {chain}",
        "risk": "risque {level}",
        "risk_warning": "Envisagez de revoir les facteurs de risque avant de continuer",
        "low_tvl_warning": "Les protocoles à faible TVL peuvent présenter un risque de liquidité plus élevé",
        "audit_warning": "Certains protocoles ont un historique d'audit limité - procédez avec prudence",
        "diversify": "Envisagez de diversifier entre plusieurs types de protocoles",
        "all_good": "Tous les protocoles répondent à vos critères - examinez les détails avant de sélectionner",
        "broaden_search": "Essayez d'élargir vos critères de recherche",
        "explore_categories": "Envisagez d'explorer différentes catégories de protocoles",
        "check_risk": "Vérifiez vos paramètres de tolérance au risque",
        "high_match": "Correspondance sémantique élevée avec votre recherche",
        "category_match": "Protocole {category} comme demandé",
        "deployed_on": "Déployé sur {chain}",
        "high_tvl": "TVL élevé (${tvl}B)",
        "well_audited": "Bien audité ({count} audits)",
        "matches_criteria": "Correspond à vos critères de recherche",
    },
}


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

    Supports multi-language queries and responses (EN, ES, PT, ZH, FR).
    Uses multilingual embeddings (BAAI/bge-m3) for cross-language search.
    """

    def __init__(
        self,
        hybrid_retrieval: HybridRetrievalInteractor,
        graph_repository: GraphRepository,
    ):
        self._hybrid_retrieval = hybrid_retrieval
        self._graph_repo = graph_repository

    def _get_translations(self, language: str) -> dict:
        """Get translations for the specified language."""
        return GRAPHRAG_TRANSLATIONS.get(language, GRAPHRAG_TRANSLATIONS["en"])

    async def search_protocols_from_chat(
        self,
        message: str,
        user_preferences: Optional[dict] = None,
        conversation_id: Optional[UUID] = None,
        language: str = "en",
    ) -> ChatSearchContext:
        """
        Extract search intent and perform hybrid search.

        Args:
            message: User's natural language message
            user_preferences: Optional user preferences for filtering
            conversation_id: Optional conversation ID for context
            language: Response language (en, es, pt, zh, fr)

        Returns:
            Chat-formatted search results with explanations
        """
        # Extract search parameters from natural language
        search_params = self._extract_search_intent(message, user_preferences)

        # Perform hybrid retrieval (uses multilingual embeddings)
        retrieval_results = await self._hybrid_retrieval.search_protocols(
            query=search_params["query"],
            limit=search_params.get("limit", 5),
            similarity_threshold=search_params.get("similarity_threshold", 0.7),
            include_risks=True,
        )

        # Convert to chat-friendly format
        chat_results = [
            self._convert_to_chat_result(result, search_params, language)
            for result in retrieval_results
        ]

        # Filter by user preferences if provided
        if user_preferences:
            chat_results = self._apply_user_filters(chat_results, user_preferences)

        # Generate natural language explanation (localized)
        explanation = self._generate_search_explanation(
            message, len(chat_results), search_params, language
        )

        # Generate recommendations (localized)
        recommendations = self._generate_recommendations(
            chat_results, search_params, user_preferences, language
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
            params["query"] = (
                message_lower.replace("low-risk", "").replace("safe", "").strip()
            )
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
        self, result: HybridRetrievalResult, search_params: dict, language: str = "en"
    ) -> ChatProtocolSearchResult:
        """Convert hybrid retrieval result to chat-friendly format."""
        # Classify risk level
        risk_level = self._classify_risk_level(result.risk_score)

        # Generate relevance explanation (localized)
        why_relevant = self._explain_relevance(result, search_params, language)

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
        self, result: HybridRetrievalResult, search_params: dict, language: str = "en"
    ) -> str:
        """Generate explanation for why protocol is relevant (localized)."""
        t = self._get_translations(language)
        reasons = []

        # High similarity
        if result.combined_score > 0.8:
            reasons.append(t["high_match"])

        # Category match
        if "category" in search_params and result.category == search_params["category"]:
            reasons.append(t["category_match"].format(category=result.category))

        # Chain match
        if "chain" in search_params and result.chain == search_params["chain"]:
            reasons.append(t["deployed_on"].format(chain=result.chain))

        # Risk match
        risk_level = self._classify_risk_level(result.risk_score)
        if "risk_level" in search_params and risk_level == search_params["risk_level"]:
            reasons.append(t["risk"].format(level=risk_level.lower()))

        # High TVL
        if result.tvl > 1_000_000_000:
            reasons.append(t["high_tvl"].format(tvl=f"{result.tvl / 1e9:.1f}"))

        # Well audited
        if result.audit_count >= 5:
            reasons.append(t["well_audited"].format(count=result.audit_count))

        # Default
        if not reasons:
            reasons.append(t["matches_criteria"])

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
        self, message: str, result_count: int, search_params: dict, language: str = "en"
    ) -> str:
        """Generate natural language explanation of search results (localized)."""
        t = self._get_translations(language)

        if result_count == 0:
            return t["no_results"]

        plural = "s" if result_count != 1 else ""
        explanation_parts = [
            t["found_protocols"].format(count=result_count, plural=plural)
        ]

        # Add filters explanation
        filters = []
        if "risk_level" in search_params:
            filters.append(t["risk"].format(level=search_params["risk_level"].lower()))
        if "category" in search_params:
            filters.append(search_params["category"].lower())
        if "chain" in search_params:
            filters.append(t["on_chain"].format(chain=search_params["chain"]))

        if filters:
            explanation_parts.append(t["that_are"] + " " + ", ".join(filters))

        return " ".join(explanation_parts) + "."

    def _generate_recommendations(
        self,
        results: List[ChatProtocolSearchResult],
        search_params: dict,
        user_preferences: Optional[dict],
        language: str = "en",
    ) -> List[str]:
        """Generate contextual recommendations based on results (localized)."""
        t = self._get_translations(language)

        if not results:
            return [
                t["broaden_search"],
                t["explore_categories"],
                t["check_risk"],
            ]

        recommendations = []

        # Risk-based recommendations
        avg_risk = sum(r.risk_score for r in results) / len(results)
        if avg_risk > 5.0:
            recommendations.append(t["risk_warning"])

        # TVL-based recommendations
        if results[0].tvl < 10_000_000:  # Less than $10M
            recommendations.append(t["low_tvl_warning"])

        # Audit-based recommendations
        if any(r.audit_count < 3 for r in results):
            recommendations.append(t["audit_warning"])

        # Diversification
        unique_categories = len({r.category for r in results})
        if unique_categories > 1:
            recommendations.append(t["diversify"])

        # Default recommendation
        if not recommendations:
            recommendations.append(t["all_good"])

        return recommendations
