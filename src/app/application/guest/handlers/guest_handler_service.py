"""
Guest Handler Service.

Provides real data responses for guest users using existing handlers.
All responses are read-only (no wallet execution).
"""

import logging
from decimal import Decimal
from typing import Any

# Caching
from app.infrastructure.caching.guest_cache import GuestCache

# DeFi Handler imports
from app.application.chat.handlers.lending_handler import LendingHandler
from app.application.chat.handlers.money_market_handler import MoneyMarketHandler
from app.application.chat.handlers.swap_handler import SwapHandler
from app.application.chat.handlers.buy_handler import BuyHandler
from app.application.chat.handlers.moonpay_swap_handler import MoonPaySwapHandler
from app.application.guest.handlers.moonpay_swap_multistep import (
    MoonPaySwapMultiStepHandler,
)
from app.application.guest.handlers.send_multistep import SendMultiStepHandler
from app.application.guest.handlers.buy_multistep import BuyMultiStepHandler
from app.application.guest.handlers.lending_multistep import LendingMultiStepHandler
from app.application.guest.handlers.portfolio_multistep import PortfolioMultiStepHandler
from app.application.guest.handlers.activity_multistep import ActivityMultiStepHandler
from app.application.chat.services.intent_detector import ChatIntent
from app.application.hunter.discord_sentiment import (
    DiscordConfig,
    DiscordSentimentAnalyzer,
)
from app.application.hunter.lstm_price_predictor import LSTMPricePredictor
from app.application.hunter.news_sentiment import NewsConfig, NewsSentimentAnalyzer
from app.application.hunter.pattern_recognition import PatternRecognizer
from app.application.hunter.portfolio_optimizer import PortfolioOptimizer
from app.application.hunter.reddit_sentiment import (
    RedditConfig,
    RedditSentimentAnalyzer,
)
from app.application.hunter.risk_analyzer import RiskAnalyzer

# Hunter AI imports
from app.application.hunter.sentiment_aggregator import SentimentAggregator
from app.application.hunter.trading_signal_generator import (
    Timeframe,
    TradingSignalGenerator,
)
from app.application.hunter.twitter_sentiment import (
    TwitterConfig,
    TwitterSentimentAnalyzer,
)

# ULTRA imports
from app.application.ultra.arbitrage_discovery import ArbitrageDiscovery
from app.application.ultra.flash_loan_engine import FlashLoanEngine
from app.application.ultra.mev_protection import MEVProtection

logger = logging.getLogger(__name__)


class GuestHandlerService:
    """
    Service to handle guest chat intents with real data.

    All handlers are read-only - no wallet execution.
    Users see real market data but must register to execute actions.
    """

    def __init__(
        self,
        lending_handler: LendingHandler | None = None,
        swap_handler: SwapHandler | None = None,
        money_market_handler: MoneyMarketHandler | None = None,
        buy_handler: BuyHandler | None = None,
        moonpay_swap_handler: MoonPaySwapHandler | None = None,
        morpho_gateway: "MorphoGateway | None" = None,
        aave_gateway: "AaveGateway | None" = None,
        guest_cache: GuestCache | None = None,
        portfolio_service: "PortfolioService | None" = None,
    ):
        from app.domain.ports.morpho_gateway import MorphoGateway as MorphoGatewayType

        self._lending_handler = lending_handler
        self._swap_handler = swap_handler
        self._money_market_handler = money_market_handler
        self._buy_handler = buy_handler
        self._moonpay_swap_handler = moonpay_swap_handler
        self._portfolio_service = portfolio_service
        # Multi-step swap flow handler
        self._moonpay_multistep = (
            MoonPaySwapMultiStepHandler(moonpay_swap_handler)
            if moonpay_swap_handler
            else None
        )
        # Multi-step send flow handler
        self._send_multistep = SendMultiStepHandler()
        # Multi-step buy flow handler
        self._buy_multistep = BuyMultiStepHandler()
        # Multi-step lending flow handler
        self._lending_multistep = LendingMultiStepHandler(
            morpho_gateway=morpho_gateway,
            aave_gateway=aave_gateway,
        )
        # Portfolio and activity handlers (demo for guests)
        self._portfolio_multistep = PortfolioMultiStepHandler()
        self._activity_multistep = ActivityMultiStepHandler()
        # Cache layer for Hunter AI responses
        self._cache = guest_cache or GuestCache()

    async def handle_intent(
        self,
        intent: ChatIntent,
        content: str,
        language: str = "en",
        context: str = "",
        is_authenticated: bool = False,
        continuation_step: str | None = None,
        previous_lending_info: dict | None = None,
        previous_swap_info: dict | None = None,
        previous_send_info: dict | None = None,
        previous_buy_info: dict | None = None,
        user_id: int | None = None,
        wallet_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Handle intent with real data.

        Args:
            intent: The detected chat intent
            content: The user's message content
            language: Language code (en, es, pt, zh)
            context: Conversation context from previous messages (for multi-turn)
            is_authenticated: Whether the user is authenticated (no signup prompts if True)
            user_id: User's database ID (required for BUY intent with authenticated users)

        Returns:
            dict with 'content', 'enrichment', and 'requires_registration' fields
        """
        handler_map = {
            # GraphRAG - Protocol Search
            ChatIntent.PROTOCOL_SEARCH: self._handle_protocol_search,
            ChatIntent.RISK_ASSESSMENT: self._handle_risk_assessment,
            ChatIntent.SIMILAR_PROTOCOLS: self._handle_similar_protocols,
            # Hunter AI
            ChatIntent.HUNTER_SENTIMENT: self._handle_sentiment,
            ChatIntent.HUNTER_PRICE_PREDICTION: self._handle_price_prediction,
            ChatIntent.HUNTER_RISK_SIGNALS: self._handle_risk_signals,
            ChatIntent.HUNTER_TRADING_SIGNALS: self._handle_trading_signals,
            ChatIntent.HUNTER_PATTERNS: self._handle_patterns,
            ChatIntent.HUNTER_PORTFOLIO: self._handle_portfolio_optimization,
            # ULTRA
            ChatIntent.ULTRA_ARBITRAGE: self._handle_arbitrage,
            ChatIntent.ULTRA_FLASH_LOANS: self._handle_flash_loans,
            ChatIntent.ULTRA_MEV_PROTECTION: self._handle_mev_protection,
            ChatIntent.ULTRA_AUTO_EXECUTOR: self._handle_auto_executor,
            # DeFi
            ChatIntent.LENDING: self._handle_lending,
            ChatIntent.MONEY_MARKET: self._handle_money_market,
            ChatIntent.SWAP: self._handle_swap,
            ChatIntent.SWAP_MOONPAY: self._handle_moonpay_swap,
            ChatIntent.BUY: self._handle_buy,
            ChatIntent.SEND: self._handle_send,
            ChatIntent.BALANCE: self._handle_balance,
            ChatIntent.RECEIVE: self._handle_receive,
            ChatIntent.PORTFOLIO: self._handle_portfolio,
            ChatIntent.ACTIVITY: self._handle_activity,
            # Agent Squad (Specialist Tasks & Complex Workflows)
            ChatIntent.SPECIALIST_TASK: self._handle_specialist_task,
            ChatIntent.COMPLEX_WORKFLOW: self._handle_complex_workflow,
            # Out of scope (reject non-crypto topics)
            ChatIntent.OUT_OF_SCOPE: self._handle_out_of_scope,
        }

        handler = handler_map.get(intent)
        if handler:
            try:
                # Pass context and is_authenticated to handlers that support it
                if intent == ChatIntent.SWAP:
                    return await self._handle_swap(
                        content,
                        language,
                        context,
                        is_authenticated,
                        continuation_step,
                        previous_swap_info,
                    )
                # Hunter AI handlers can use context for follow-up questions
                elif intent in [
                    ChatIntent.HUNTER_SENTIMENT,
                    ChatIntent.HUNTER_PRICE_PREDICTION,
                    ChatIntent.HUNTER_RISK_SIGNALS,
                    ChatIntent.HUNTER_TRADING_SIGNALS,
                    ChatIntent.HUNTER_PATTERNS,
                ]:
                    return await handler(content, language, context, is_authenticated)
                # Other handlers
                elif intent in [
                    ChatIntent.PROTOCOL_SEARCH,
                    ChatIntent.RISK_ASSESSMENT,
                    ChatIntent.SIMILAR_PROTOCOLS,
                    ChatIntent.HUNTER_PORTFOLIO,
                    ChatIntent.ULTRA_ARBITRAGE,
                    ChatIntent.ULTRA_FLASH_LOANS,
                    ChatIntent.ULTRA_MEV_PROTECTION,
                    ChatIntent.ULTRA_AUTO_EXECUTOR,
                    ChatIntent.MONEY_MARKET,
                    ChatIntent.SPECIALIST_TASK,
                    ChatIntent.COMPLEX_WORKFLOW,
                ]:
                    return await handler(content, language, is_authenticated)
                # Lending handler with continuation support
                elif intent == ChatIntent.LENDING:
                    return await handler(
                        content,
                        language,
                        context,
                        is_authenticated,
                        continuation_step,
                        previous_lending_info,
                        wallet_address,
                    )
                # Buy handler (supports multi-step flow)
                elif intent == ChatIntent.BUY:
                    return await self._handle_buy(
                        content,
                        language,
                        is_authenticated,
                        user_id,
                        continuation_step,
                        previous_buy_info,
                    )
                # MoonPay swap handler (supports multi-step flow)
                elif intent == ChatIntent.SWAP_MOONPAY:
                    return await self._handle_moonpay_swap(
                        content,
                        language,
                        is_authenticated,
                        continuation_step,
                        previous_swap_info,
                    )
                # Send handler (supports multi-step flow)
                elif intent == ChatIntent.SEND:
                    return await self._handle_send(
                        content,
                        language,
                        is_authenticated,
                        continuation_step,
                        previous_send_info,
                    )
                # Balance handler (needs wallet address for authenticated users)
                elif intent == ChatIntent.BALANCE:
                    return await self._handle_balance(
                        content,
                        language,
                        is_authenticated,
                        wallet_address,
                    )
                # Portfolio handler (needs wallet address for authenticated users)
                elif intent == ChatIntent.PORTFOLIO:
                    return await self._handle_portfolio(
                        content,
                        language,
                        is_authenticated,
                        wallet_address,
                    )
                # Activity handler (needs wallet address and user_id for authenticated users)
                elif intent == ChatIntent.ACTIVITY:
                    return await self._handle_activity(
                        content,
                        language,
                        is_authenticated,
                        wallet_address,
                        str(user_id) if user_id else None,
                    )
                # Receive handler (needs wallet address for authenticated users)
                elif intent == ChatIntent.RECEIVE:
                    return await self._handle_receive(
                        content,
                        language,
                        is_authenticated,
                        wallet_address,
                    )
                return await handler(content, language, is_authenticated)
            except Exception as e:
                logger.warning(f"Handler error for {intent}: {e}")
                return self._fallback_response(intent, language, is_authenticated)

        return self._fallback_response(intent, language, is_authenticated)

    # ========================================
    # ========================================
    # GraphRAG Protocol Search Handlers (Demo Mode)
    # ========================================

    async def _handle_protocol_search(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle protocol search intent (demo mode with example protocols)."""
        # Demo protocols data - in production, this would query the graph
        demo_protocols = [
            {
                "name": "Aave",
                "category": "Lending",
                "tvl": 12.5,
                "risk": "LOW",
                "chain": "Ethereum",
            },
            {
                "name": "Compound",
                "category": "Lending",
                "tvl": 3.2,
                "risk": "LOW",
                "chain": "Ethereum",
            },
            {
                "name": "Uniswap",
                "category": "DEX",
                "tvl": 5.8,
                "risk": "LOW",
                "chain": "Ethereum",
            },
            {
                "name": "Curve",
                "category": "DEX",
                "tvl": 4.1,
                "risk": "LOW",
                "chain": "Ethereum",
            },
            {
                "name": "Lido",
                "category": "Staking",
                "tvl": 25.0,
                "risk": "LOW",
                "chain": "Ethereum",
            },
            {
                "name": "Morpho",
                "category": "Lending",
                "tvl": 1.8,
                "risk": "MEDIUM",
                "chain": "Ethereum",
            },
        ]

        translations = {
            "en": {
                "title": "🔍 **Protocol Search Results (Demo)**",
                "desc": "Here are some top DeFi protocols matching your criteria:",
                "tvl": "TVL",
                "risk": "Risk",
                "chain": "Chain",
                "note": "Register for full access to:",
                "features": [
                    "Search 500+ protocols",
                    "Custom filters",
                    "Real-time data",
                    "Risk analysis",
                ],
            },
            "es": {
                "title": "🔍 **Resultados de Búsqueda de Protocolos (Demo)**",
                "desc": "Aquí hay algunos protocolos DeFi principales que coinciden con tus criterios:",
                "tvl": "TVL",
                "risk": "Riesgo",
                "chain": "Red",
                "note": "Regístrate para acceso completo a:",
                "features": [
                    "Buscar 500+ protocolos",
                    "Filtros personalizados",
                    "Datos en tiempo real",
                    "Análisis de riesgo",
                ],
            },
            "pt": {
                "title": "🔍 **Resultados da Pesquisa de Protocolos (Demo)**",
                "desc": "Aqui estão alguns dos principais protocolos DeFi que correspondem aos seus critérios:",
                "tvl": "TVL",
                "risk": "Risco",
                "chain": "Rede",
                "note": "Registre-se para acesso completo a:",
                "features": [
                    "Pesquisar 500+ protocolos",
                    "Filtros personalizados",
                    "Dados em tempo real",
                    "Análise de risco",
                ],
            },
            "zh": {
                "title": "🔍 **协议搜索结果 (演示)**",
                "desc": "以下是符合您条件的一些顶级DeFi协议:",
                "tvl": "总锁仓量",
                "risk": "风险",
                "chain": "链",
                "note": "注册后可访问:",
                "features": ["搜索500+协议", "自定义筛选", "实时数据", "风险分析"],
            },
        }
        t = translations.get(language, translations["en"])

        response = f"{t['title']}\n\n{t['desc']}\n\n"
        for p in demo_protocols[:5]:
            response += f"• **{p['name']}** ({p['category']})\n"
            response += f"  {t['tvl']}: ${p['tvl']}B | {t['risk']}: {p['risk']} | {t['chain']}: {p['chain']}\n"
        response += f"\n{t['note']}\n"
        for feature in t["features"]:
            response += f"  ✓ {feature}\n"
        response += "\n" + self._get_auth_cta_message(
            language, for_action=False, is_authenticated=is_authenticated
        )

        return {
            "content": response,
            "enrichment": {
                "graphrag": True,
                "demo_protocols": len(demo_protocols),
                "full_search_requires_registration": True,
            },
            "requires_registration": not is_authenticated,
        }

    async def _handle_risk_assessment(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle risk assessment intent (demo mode with example analysis)."""
        # Extract protocol name from content
        protocol = "Aave"  # Default
        for p in ["aave", "uniswap", "compound", "curve", "morpho", "lido"]:
            if p in content.lower():
                protocol = p.capitalize()
                break

        # Demo risk data
        risk_data = {
            "Aave": {"score": 2.5, "level": "LOW", "audits": 12, "tvl": 12.5},
            "Uniswap": {"score": 2.8, "level": "LOW", "audits": 10, "tvl": 5.8},
            "Compound": {"score": 2.3, "level": "LOW", "audits": 8, "tvl": 3.2},
            "Curve": {"score": 3.0, "level": "LOW", "audits": 7, "tvl": 4.1},
            "Morpho": {"score": 4.5, "level": "MEDIUM", "audits": 4, "tvl": 1.8},
            "Lido": {"score": 2.2, "level": "LOW", "audits": 9, "tvl": 25.0},
        }
        data = risk_data.get(protocol, risk_data["Aave"])

        translations = {
            "en": {
                "title": f"🛡️ **Risk Assessment: {protocol} (Demo)**",
                "score": "Risk Score",
                "level": "Risk Level",
                "audits": "Security Audits",
                "tvl": "Total Value Locked",
                "factors": "Key Risk Factors",
                "smart_contract": "Smart Contract Risk",
                "liquidity": "Liquidity Risk",
                "oracle": "Oracle Risk",
                "note": "Register for full risk analysis including:",
                "features": [
                    "Real-time monitoring",
                    "Historical data",
                    "ML predictions",
                    "Alerts",
                ],
            },
            "es": {
                "title": f"🛡️ **Evaluación de Riesgo: {protocol} (Demo)**",
                "score": "Puntuación de Riesgo",
                "level": "Nivel de Riesgo",
                "audits": "Auditorías de Seguridad",
                "tvl": "Valor Total Bloqueado",
                "factors": "Factores Clave de Riesgo",
                "smart_contract": "Riesgo de Contrato Inteligente",
                "liquidity": "Riesgo de Liquidez",
                "oracle": "Riesgo de Oráculo",
                "note": "Regístrate para análisis de riesgo completo incluyendo:",
                "features": [
                    "Monitoreo en tiempo real",
                    "Datos históricos",
                    "Predicciones ML",
                    "Alertas",
                ],
            },
            "pt": {
                "title": f"🛡️ **Avaliação de Risco: {protocol} (Demo)**",
                "score": "Pontuação de Risco",
                "level": "Nível de Risco",
                "audits": "Auditorias de Segurança",
                "tvl": "Valor Total Bloqueado",
                "factors": "Fatores Chave de Risco",
                "smart_contract": "Risco de Contrato Inteligente",
                "liquidity": "Risco de Liquidez",
                "oracle": "Risco de Oráculo",
                "note": "Registre-se para análise de risco completa incluindo:",
                "features": [
                    "Monitoramento em tempo real",
                    "Dados históricos",
                    "Previsões ML",
                    "Alertas",
                ],
            },
            "zh": {
                "title": f"🛡️ **风险评估: {protocol} (演示)**",
                "score": "风险评分",
                "level": "风险等级",
                "audits": "安全审计",
                "tvl": "总锁仓量",
                "factors": "主要风险因素",
                "smart_contract": "智能合约风险",
                "liquidity": "流动性风险",
                "oracle": "预言机风险",
                "note": "注册后可获得完整风险分析:",
                "features": ["实时监控", "历史数据", "ML预测", "警报"],
            },
        }
        t = translations.get(language, translations["en"])

        response = f"{t['title']}\n\n"
        response += f"📊 **{t['score']}:** {data['score']}/10\n"
        response += f"⚡ **{t['level']}:** {data['level']}\n"
        response += f"🔒 **{t['audits']}:** {data['audits']}\n"
        response += f"💰 **{t['tvl']}:** ${data['tvl']}B\n\n"
        response += f"**{t['factors']}:**\n"
        response += f"  • {t['smart_contract']}: {'✅ Low' if data['score'] < 4 else '⚠️ Medium'}\n"
        response += f"  • {t['liquidity']}: ✅ Low\n"
        response += f"  • {t['oracle']}: ✅ Low\n\n"
        response += f"{t['note']}\n"
        for feature in t["features"]:
            response += f"  ✓ {feature}\n"
        response += "\n" + self._get_auth_cta_message(
            language, for_action=False, is_authenticated=is_authenticated
        )

        return {
            "content": response,
            "enrichment": {
                "graphrag": True,
                "protocol": protocol,
                "risk_score": data["score"],
                "risk_level": data["level"],
                "full_analysis_requires_registration": True,
            },
            "requires_registration": False,
        }

    async def _handle_similar_protocols(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle similar protocols search intent (demo mode)."""
        # Extract protocol name from content
        protocol = "Aave"  # Default
        for p in ["aave", "uniswap", "compound", "curve", "morpho", "lido"]:
            if p in content.lower():
                protocol = p.capitalize()
                break

        # Demo similar protocols
        similar_map = {
            "Aave": [("Compound", 0.92), ("Morpho", 0.85), ("Spark", 0.82)],
            "Uniswap": [("Curve", 0.88), ("SushiSwap", 0.85), ("Balancer", 0.80)],
            "Compound": [("Aave", 0.92), ("Morpho", 0.80), ("Spark", 0.78)],
            "Curve": [("Uniswap", 0.88), ("Balancer", 0.82), ("Velodrome", 0.75)],
            "Morpho": [("Aave", 0.85), ("Compound", 0.80), ("Spark", 0.78)],
            "Lido": [("Rocket Pool", 0.90), ("Frax ETH", 0.85), ("Swell", 0.80)],
        }
        similar = similar_map.get(protocol, similar_map["Aave"])

        translations = {
            "en": {
                "title": f"🔗 **Protocols Similar to {protocol} (Demo)**",
                "desc": f"Based on category, features, and risk profile, here are protocols similar to {protocol}:",
                "similarity": "Similarity",
                "note": "Register for full comparison including:",
                "features": [
                    "Detailed feature comparison",
                    "APY comparison",
                    "Risk analysis",
                    "User reviews",
                ],
            },
            "es": {
                "title": f"🔗 **Protocolos Similares a {protocol} (Demo)**",
                "desc": f"Basándose en categoría, características y perfil de riesgo, aquí hay protocolos similares a {protocol}:",
                "similarity": "Similitud",
                "note": "Regístrate para comparación completa incluyendo:",
                "features": [
                    "Comparación detallada de características",
                    "Comparación de APY",
                    "Análisis de riesgo",
                    "Opiniones de usuarios",
                ],
            },
            "pt": {
                "title": f"🔗 **Protocolos Similares a {protocol} (Demo)**",
                "desc": f"Com base em categoria, recursos e perfil de risco, aqui estão protocolos semelhantes a {protocol}:",
                "similarity": "Similaridade",
                "note": "Registre-se para comparação completa incluindo:",
                "features": [
                    "Comparação detalhada de recursos",
                    "Comparação de APY",
                    "Análise de risco",
                    "Avaliações de usuários",
                ],
            },
            "zh": {
                "title": f"🔗 **与{protocol}类似的协议 (演示)**",
                "desc": f"根据类别、功能和风险配置,以下是与{protocol}类似的协议:",
                "similarity": "相似度",
                "note": "注册后可获得完整比较:",
                "features": ["详细功能比较", "APY比较", "风险分析", "用户评价"],
            },
        }
        t = translations.get(language, translations["en"])

        response = f"{t['title']}\n\n{t['desc']}\n\n"
        for name, score in similar:
            bar = "█" * int(score * 10)
            response += f"• **{name}** - {t['similarity']}: {score:.0%} {bar}\n"
        response += f"\n{t['note']}\n"
        for feature in t["features"]:
            response += f"  ✓ {feature}\n"
        response += "\n" + self._get_auth_cta_message(
            language, for_action=False, is_authenticated=is_authenticated
        )

        return {
            "content": response,
            "enrichment": {
                "graphrag": True,
                "base_protocol": protocol,
                "similar_protocols": [s[0] for s in similar],
                "full_comparison_requires_registration": True,
            },
            "requires_registration": not is_authenticated,
        }

    # ========================================
    # Hunter AI Handlers
    # ========================================

    async def _handle_sentiment(
        self,
        content: str,
        language: str,
        context: str = "",
        is_authenticated: bool = False,
    ) -> dict[str, Any]:
        """Handle sentiment analysis with real data."""
        # Extract token from content, using context if token not found in current message
        token = (
            self._extract_token(content)
            or self._extract_token_from_context(context)
            or "ETH"
        )

        # Check cache first
        cached = await self._cache.get_hunter_response("sentiment", token, language)
        if cached:
            logger.debug(f"Cache HIT for sentiment: {token}/{language}")
            return cached

        try:
            # Initialize analyzers
            twitter = TwitterSentimentAnalyzer(TwitterConfig(enabled=True))
            reddit = RedditSentimentAnalyzer(RedditConfig(enabled=True))
            discord = DiscordSentimentAnalyzer(DiscordConfig(enabled=True))
            news = NewsSentimentAnalyzer(NewsConfig(enabled=True))
            aggregator = SentimentAggregator()

            # Collect readings
            readings = []
            readings.append(await twitter.analyze_token_sentiment(token, 24))
            readings.append(await reddit.analyze_token_sentiment(token, 24))
            readings.append(await discord.analyze_token_sentiment(token, 24))
            readings.append(await news.analyze_token_sentiment(token, 24))

            # Aggregate
            aggregated = aggregator.aggregate(readings, token)
            breakdown = aggregator.get_source_breakdown(aggregated)

            # Format response
            # Translations for sentiment analysis
            translations = {
                "en": {
                    "title": f"📊 **Sentiment Analysis for {token}**",
                    "overall": "**Overall:**",
                    "confidence": "**Confidence:**",
                    "sources": "**Sources:**",
                },
                "es": {
                    "title": f"📊 **Análisis de Sentimiento para {token}**",
                    "overall": "**General:**",
                    "confidence": "**Confianza:**",
                    "sources": "**Fuentes:**",
                },
                "pt": {
                    "title": f"📊 **Análise de Sentimento para {token}**",
                    "overall": "**Geral:**",
                    "confidence": "**Confiança:**",
                    "sources": "**Fontes:**",
                },
                "zh": {
                    "title": f"📊 **{token} 情绪分析**",
                    "overall": "**总体:**",
                    "confidence": "**置信度:**",
                    "sources": "**来源:**",
                },
            }
            t = translations.get(language, translations["en"])

            response = f"{t['title']}\n\n"
            response += f"{t['overall']} {aggregated.classification.value.title()} "
            response += f"({aggregated.overall_score:.1f}/100)\n"
            response += (
                f"{t['confidence']} {aggregated.overall_confidence * 100:.0f}%\n\n"
            )

            response += "**By Source:**\n"
            for source, data in breakdown.items():
                emoji = (
                    "🟢" if data["score"] > 60 else "🔴" if data["score"] < 40 else "🟡"
                )
                response += f"- {source.title()}: {emoji} {data['score']:.0f}/100\n"

            response += self._get_auth_cta_message(
                language, for_action=False, is_authenticated=is_authenticated
            )

            # Build sources list
            from datetime import datetime, UTC
            from app.domain.value_objects.chat.source_info import SourceInfo, SourceType

            sources = []
            fetched_at = datetime.now(UTC)

            # Add social media sources
            for source_name, data in breakdown.items():
                sources.append(
                    SourceInfo(
                        source_type=SourceType.SOCIAL_MEDIA
                        if source_name.lower() in ["twitter", "reddit", "discord"]
                        else SourceType.RSS_FEED,
                        source_name=source_name.title(),
                        citation_text=f"{source_name.title()} sentiment analysis for {token}",
                        fetched_at=fetched_at,
                        data_points_used=data.get("sample_size", 0),
                        relevance_score=data.get("weight", 0.25),
                        metadata={
                            "score": data["score"],
                            "classification": data["classification"],
                        },
                    )
                )

            # Normalize score from 0-100 to -1 to 1 range for API consistency
            # 0 → -1 (bearish), 50 → 0 (neutral), 100 → 1 (bullish)
            normalized_score = (aggregated.overall_score - 50) / 50

            result = {
                "content": response,
                "enrichment": {
                    "token": token,
                    "overall_score": normalized_score,
                    "overall_score_percentage": aggregated.overall_score,  # Keep original for display
                    "classification": aggregated.classification.value,
                    "sources": breakdown,
                    "hunter_tool": "sentiment_aggregator",
                },
                "sources": [s.to_dict() for s in sources],  # NEW
                "requires_registration": False,
            }

            # Cache the successful response
            await self._cache.set_hunter_response("sentiment", token, language, result)

            return result
        except Exception as e:
            logger.warning(f"Sentiment analysis error: {e}")
            return self._fallback_response(
                ChatIntent.HUNTER_SENTIMENT, language, is_authenticated
            )

    async def _handle_price_prediction(
        self,
        content: str,
        language: str,
        context: str = "",
        is_authenticated: bool = False,
    ) -> dict[str, Any]:
        """Handle price prediction with real ML model."""
        # Extract token from content, using context if token not found in current message
        token = (
            self._extract_token(content)
            or self._extract_token_from_context(context)
            or "ETH"
        )

        # Check cache first
        cached = await self._cache.get_hunter_response(
            "price_prediction", token, language
        )
        if cached:
            logger.debug(f"Cache HIT for price_prediction: {token}/{language}")
            return cached

        try:
            predictor = LSTMPricePredictor()
            prediction = await predictor.predict(token, horizon_hours=168)  # 7 days

            # Determine emoji based on direction
            direction_emoji = (
                "🟢"
                if prediction.direction == "up"
                else "🔴"
                if prediction.direction == "down"
                else "🟡"
            )

            # Translations for price prediction response
            translations = {
                "en": {
                    "title": f"📈 **Price Prediction for {token}**",
                    "current_price": "**Current Price:**",
                    "forecast": "**7-Day Forecast:**",
                    "expected_change": "**Expected Change:**",
                    "direction": "**Direction:**",
                    "confidence": "**Confidence:**",
                    "model": "**Model:** LSTM Neural Network",
                    "horizon": "**Horizon:**",
                    "hours": "hours",
                    "up": "UP",
                    "down": "DOWN",
                    "neutral": "NEUTRAL",
                },
                "es": {
                    "title": f"📈 **Predicción de Precio para {token}**",
                    "current_price": "**Precio Actual:**",
                    "forecast": "**Pronóstico 7 Días:**",
                    "expected_change": "**Cambio Esperado:**",
                    "direction": "**Dirección:**",
                    "confidence": "**Confianza:**",
                    "model": "**Modelo:** Red Neuronal LSTM",
                    "horizon": "**Horizonte:**",
                    "hours": "horas",
                    "up": "ALZA",
                    "down": "BAJA",
                    "neutral": "NEUTRAL",
                },
                "pt": {
                    "title": f"📈 **Previsão de Preço para {token}**",
                    "current_price": "**Preço Atual:**",
                    "forecast": "**Previsão 7 Dias:**",
                    "expected_change": "**Mudança Esperada:**",
                    "direction": "**Direção:**",
                    "confidence": "**Confiança:**",
                    "model": "**Modelo:** Rede Neural LSTM",
                    "horizon": "**Horizonte:**",
                    "hours": "horas",
                    "up": "ALTA",
                    "down": "BAIXA",
                    "neutral": "NEUTRO",
                },
                "zh": {
                    "title": f"📈 **{token} 价格预测**",
                    "current_price": "**当前价格:**",
                    "forecast": "**7天预测:**",
                    "expected_change": "**预期变化:**",
                    "direction": "**方向:**",
                    "confidence": "**置信度:**",
                    "model": "**模型:** LSTM 神经网络",
                    "horizon": "**时间范围:**",
                    "hours": "小时",
                    "up": "上涨",
                    "down": "下跌",
                    "neutral": "中性",
                },
            }

            t = translations.get(language, translations["en"])

            # Map direction to translated text
            direction_text = {
                "up": t["up"],
                "down": t["down"],
                "neutral": t["neutral"],
            }.get(prediction.direction, prediction.direction.upper())

            response = f"{t['title']}\n\n"
            response += f"{t['current_price']} ${prediction.current_price:,.2f}\n"
            response += f"{t['forecast']} ${prediction.predicted_price:,.2f}\n"
            response += f"{t['expected_change']} {direction_emoji} {prediction.change_percent:+.1f}%\n"
            response += f"{t['direction']} {direction_text}\n"
            response += f"{t['confidence']} {prediction.confidence * 100:.0f}%\n\n"

            response += f"{t['model']}\n"
            response += f"{t['horizon']} {prediction.horizon_hours} {t['hours']}\n"

            # Use conditional CTA helper
            response += self._get_auth_cta_message(
                language, for_action=False, is_authenticated=is_authenticated
            )

            result = {
                "content": response,
                "enrichment": {
                    "token": token,
                    "current_price": prediction.current_price,
                    "predicted_price": prediction.predicted_price,
                    "change_percent": prediction.change_percent,
                    "direction": prediction.direction,
                    "confidence": prediction.confidence,
                    "hunter_tool": "lstm_predictor",
                },
                "requires_registration": not is_authenticated,
            }

            # Cache the successful response
            await self._cache.set_hunter_response(
                "price_prediction", token, language, result
            )

            return result
        except Exception as e:
            logger.error(
                f"Price prediction error for token {token}: {e}", exc_info=True
            )
            # Try to provide a helpful response even on error
            # Get current price at least
            try:
                from app.infrastructure.adapters.external.coingecko_client import (
                    CoinGeckoClient,
                )

                client = CoinGeckoClient()
                try:
                    symbol_to_id = {
                        "BTC": "bitcoin",
                        "ETH": "ethereum",
                        "SOL": "solana",
                    }
                    coin_id = symbol_to_id.get(token.upper(), token.lower())
                    price_data = await client.get_simple_price(
                        coin_ids=[coin_id], vs_currencies=["usd"]
                    )
                    if price_data and coin_id in price_data:
                        current_price = price_data[coin_id]["usd"]
                        # Provide basic response with current price
                        translations = {
                            "en": f"📈 **Current Price for {token}:** ${current_price:,.2f}\n\nPrice prediction model is temporarily unavailable. Please try again in a moment.",
                            "es": f"📈 **Precio Actual para {token}:** ${current_price:,.2f}\n\nEl modelo de predicción de precios no está disponible temporalmente. Intenta de nuevo en un momento.",
                            "pt": f"📈 **Preço Atual para {token}:** ${current_price:,.2f}\n\nO modelo de previsão de preços não está disponível temporariamente. Tente novamente em um momento.",
                            "zh": f"📈 **{token} 当前价格:** ${current_price:,.2f}\n\n价格预测模型暂时不可用。请稍后再试。",
                        }
                        return {
                            "content": translations.get(language, translations["en"]),
                            "enrichment": {
                                "token": token,
                                "current_price": current_price,
                                "error": True,
                            },
                            "requires_registration": False,
                        }
                finally:
                    await client.close()
            except Exception as e2:
                logger.warning(f"Failed to get fallback price: {e2}")

            return self._fallback_response(
                ChatIntent.HUNTER_PRICE_PREDICTION, language, is_authenticated
            )

    async def _handle_risk_signals(
        self,
        content: str,
        language: str,
        context: str = "",
        is_authenticated: bool = False,
    ) -> dict[str, Any]:
        """Handle market risk signals."""
        # Extract token from content, using context if token not found in current message
        token = (
            self._extract_token(content)
            or self._extract_token_from_context(context)
            or "ETH"
        )

        # Check cache first
        cached = await self._cache.get_hunter_response("risk_signals", token, language)
        if cached:
            logger.debug(f"Cache HIT for risk_signals: {token}/{language}")
            return cached

        try:
            analyzer = RiskAnalyzer()
            assessment = await analyzer.analyze_comprehensive_risk(token)

            # Translations for risk signals
            translations = {
                "en": {
                    "title": f"⚠️ **Risk Signals for {token}**",
                    "overall_risk": "**Overall Risk Level:**",
                    "risk_score": "**Risk Score:**",
                    "risk_factors": "**Risk Factors:**",
                    "whale_activity": "**🐋 Whale Activity:**",
                    "large_transfers": "Large transfers:",
                    "net_flow": "Net flow:",
                },
                "es": {
                    "title": f"⚠️ **Señales de Riesgo para {token}**",
                    "overall_risk": "**Nivel de Riesgo General:**",
                    "risk_score": "**Puntuación de Riesgo:**",
                    "risk_factors": "**Factores de Riesgo:**",
                    "whale_activity": "**🐋 Actividad de Ballenas:**",
                    "large_transfers": "Transferencias grandes:",
                    "net_flow": "Flujo neto:",
                },
                "pt": {
                    "title": f"⚠️ **Sinais de Risco para {token}**",
                    "overall_risk": "**Nível de Risco Geral:**",
                    "risk_score": "**Pontuação de Risco:**",
                    "risk_factors": "**Fatores de Risco:**",
                    "whale_activity": "**🐋 Atividade de Baleias:**",
                    "large_transfers": "Transferências grandes:",
                    "net_flow": "Fluxo líquido:",
                },
                "zh": {
                    "title": f"⚠️ **{token} 风险信号**",
                    "overall_risk": "**总体风险级别:**",
                    "risk_score": "**风险评分:**",
                    "risk_factors": "**风险因素:**",
                    "whale_activity": "**🐋 鲸鱼活动:**",
                    "large_transfers": "大额转账:",
                    "net_flow": "净流量:",
                },
            }
            t = translations.get(language, translations["en"])

            response = f"{t['title']}\n\n"
            response += f"{t['overall_risk']} {assessment.overall_risk_level.upper()}\n"
            response += f"{t['risk_score']} {assessment.overall_risk_score:.1f}/100\n\n"

            response += f"{t['risk_factors']}\n"
            # Display risk factors from assessment
            for factor_name, risk_score in assessment.risk_factors.items():
                emoji = (
                    "🔴"
                    if risk_score.level in ["high", "extreme"]
                    else "🟡"
                    if risk_score.level == "medium"
                    else "🟢"
                )
                factor_display = factor_name.replace("_", " ").title()
                response += f"- {emoji} {factor_display}: {risk_score.level.upper()} risk (score: {risk_score.score:.1f}/100)\n"

            # Add recommendation
            if assessment.recommendation:
                response += f"\n**Recommendation:** {assessment.recommendation}\n"

            response += self._get_auth_cta_message(
                language, for_action=False, is_authenticated=is_authenticated
            )

            result = {
                "content": response,
                "enrichment": {
                    "token": token,
                    "overall_risk_score": assessment.overall_risk_score,
                    "risk_level": assessment.overall_risk_level,
                    "risk_factors": {
                        k: v.to_dict() for k, v in assessment.risk_factors.items()
                    },
                    "recommendation": assessment.recommendation,
                    "hunter_tool": "risk_analyzer",
                },
                "requires_registration": not is_authenticated,
            }

            # Cache the successful response
            await self._cache.set_hunter_response(
                "risk_signals", token, language, result
            )

            return result
        except Exception as e:
            logger.error(f"Risk signals error for token {token}: {e}", exc_info=True)
            return self._fallback_response(
                ChatIntent.HUNTER_RISK_SIGNALS, language, is_authenticated
            )

    async def _handle_trading_signals(
        self,
        content: str,
        language: str,
        context: str = "",
        is_authenticated: bool = False,
    ) -> dict[str, Any]:
        """Handle trading signal generation."""
        # Extract token from content, using context if token not found in current message
        token = (
            self._extract_token(content)
            or self._extract_token_from_context(context)
            or "ETH"
        )

        # Check cache first
        cached = await self._cache.get_hunter_response(
            "trading_signals", token, language
        )
        if cached:
            logger.debug(f"Cache HIT for trading_signals: {token}/{language}")
            return cached

        try:
            generator = TradingSignalGenerator()
            signal = await generator.generate_signal(token, Timeframe.HOUR_4)

            # Determine emoji based on signal type
            signal_emoji = (
                "🟢"
                if signal.signal_type.value == "buy"
                else "🔴"
                if signal.signal_type.value == "sell"
                else "🟡"
            )

            # Translations for trading signals
            translations = {
                "en": {
                    "title": f"💹 **Trading Signal for {token}**",
                    "signal": "**Signal:**",
                    "strength": "**Strength:**",
                    "confidence": "**Confidence:**",
                    "timeframe": "**Timeframe:**",
                    "entry_price": "**Entry Price:**",
                    "stop_loss": "**Stop Loss:**",
                    "take_profit": "**Take Profit:**",
                    "factor_scores": "**Factor Scores:**",
                    "sentiment": "Sentiment:",
                    "prediction": "Prediction:",
                    "risk": "Risk:",
                },
                "es": {
                    "title": f"💹 **Señal de Trading para {token}**",
                    "signal": "**Señal:**",
                    "strength": "**Fuerza:**",
                    "confidence": "**Confianza:**",
                    "timeframe": "**Marco Temporal:**",
                    "entry_price": "**Precio de Entrada:**",
                    "stop_loss": "**Stop Loss:**",
                    "take_profit": "**Take Profit:**",
                    "factor_scores": "**Puntuaciones de Factores:**",
                    "sentiment": "Sentimiento:",
                    "prediction": "Predicción:",
                    "risk": "Riesgo:",
                },
                "pt": {
                    "title": f"💹 **Sinal de Trading para {token}**",
                    "signal": "**Sinal:**",
                    "strength": "**Força:**",
                    "confidence": "**Confiança:**",
                    "timeframe": "**Período:**",
                    "entry_price": "**Preço de Entrada:**",
                    "stop_loss": "**Stop Loss:**",
                    "take_profit": "**Take Profit:**",
                    "factor_scores": "**Pontuações de Fatores:**",
                    "sentiment": "Sentimento:",
                    "prediction": "Previsão:",
                    "risk": "Risco:",
                },
                "zh": {
                    "title": f"💹 **{token} 交易信号**",
                    "signal": "**信号:**",
                    "strength": "**强度:**",
                    "confidence": "**置信度:**",
                    "timeframe": "**时间框架:**",
                    "entry_price": "**入场价:**",
                    "stop_loss": "**止损:**",
                    "take_profit": "**止盈:**",
                    "factor_scores": "**因子评分:**",
                    "sentiment": "情绪:",
                    "prediction": "预测:",
                    "risk": "风险:",
                },
            }
            t = translations.get(language, translations["en"])

            response = f"{t['title']}\n\n"
            response += (
                f"{t['signal']} {signal_emoji} {signal.signal_type.value.upper()}\n"
            )
            response += f"{t['strength']} {signal.signal_strength:.0f}/100\n"
            response += f"{t['confidence']} {signal.confidence * 100:.0f}%\n"
            response += f"{t['timeframe']} {signal.timeframe.value}\n\n"

            if signal.entry_price:
                response += f"{t['entry_price']} ${signal.entry_price:,.2f}\n"
            if signal.stop_loss_price:
                response += f"{t['stop_loss']} ${signal.stop_loss_price:,.2f}\n"
            if signal.take_profit_price:
                response += f"{t['take_profit']} ${signal.take_profit_price:,.2f}\n"

            response += f"\n{t['factor_scores']}\n"
            response += f"- {t['sentiment']} {signal.sentiment_score:.0f}/100\n"
            response += f"- {t['prediction']} {signal.prediction_score:.0f}/100\n"
            response += f"- {t['risk']} {signal.risk_score:.0f}/100\n"

            response += self._get_auth_cta_message(
                language, for_action=False, is_authenticated=is_authenticated
            )

            result = {
                "content": response,
                "enrichment": {
                    "token": token,
                    "signal_type": signal.signal_type.value,
                    "signal_strength": signal.signal_strength,
                    "confidence": signal.confidence,
                    "entry_price": signal.entry_price,
                    "stop_loss_price": signal.stop_loss_price,
                    "take_profit_price": signal.take_profit_price,
                    "hunter_tool": "signal_generator",
                },
                "requires_registration": False,
            }

            # Cache the successful response
            await self._cache.set_hunter_response(
                "trading_signals", token, language, result
            )

            return result
        except Exception as e:
            logger.warning(f"Trading signals error: {e}")
            return self._fallback_response(
                ChatIntent.HUNTER_TRADING_SIGNALS, language, is_authenticated
            )

    async def _handle_patterns(
        self,
        content: str,
        language: str,
        context: str = "",
        is_authenticated: bool = False,
    ) -> dict[str, Any]:
        """Handle chart pattern recognition."""
        # Extract token from content, using context if token not found in current message
        token = (
            self._extract_token(content)
            or self._extract_token_from_context(context)
            or "ETH"
        )

        # Check cache first
        cached = await self._cache.get_hunter_response("patterns", token, language)
        if cached:
            logger.debug(f"Cache HIT for patterns: {token}/{language}")
            return cached

        try:
            recognizer = PatternRecognizer()
            # Detect both chart patterns and candlestick patterns
            chart_patterns = await recognizer.detect_chart_patterns(token)
            candlestick_patterns = await recognizer.detect_candlestick_patterns(token)

            # Translations for chart patterns
            translations = {
                "en": {
                    "title": f"📊 **Chart Patterns for {token}**",
                    "no_patterns": "No significant patterns detected currently.",
                    "confidence": "Confidence:",
                    "signal": "Signal:",
                    "pattern_type": "Pattern:",
                    "chart_patterns": "**Chart Patterns:**",
                    "candlestick_patterns": "**Candlestick Patterns:**",
                },
                "es": {
                    "title": f"📊 **Patrones de Gráfico para {token}**",
                    "no_patterns": "No se detectaron patrones significativos actualmente.",
                    "confidence": "Confianza:",
                    "signal": "Señal:",
                    "pattern_type": "Patrón:",
                    "chart_patterns": "**Patrones de Gráfico:**",
                    "candlestick_patterns": "**Patrones de Velas:**",
                },
                "pt": {
                    "title": f"📊 **Padrões de Gráfico para {token}**",
                    "no_patterns": "Nenhum padrão significativo detectado no momento.",
                    "confidence": "Confiança:",
                    "signal": "Sinal:",
                    "pattern_type": "Padrão:",
                    "chart_patterns": "**Padrões de Gráfico:**",
                    "candlestick_patterns": "**Padrões de Velas:**",
                },
                "zh": {
                    "title": f"📊 **{token} 图表模式**",
                    "no_patterns": "当前未检测到显著模式。",
                    "confidence": "置信度:",
                    "signal": "信号:",
                    "pattern_type": "模式:",
                    "chart_patterns": "**图表模式:**",
                    "candlestick_patterns": "**蜡烛图模式:**",
                },
            }
            t = translations.get(language, translations["en"])

            response = f"{t['title']}\n\n"

            if not chart_patterns and not candlestick_patterns:
                response += f"{t['no_patterns']}\n"
            else:
                # Chart patterns
                if chart_patterns:
                    response += f"{t['chart_patterns']}\n"
                    for pattern in chart_patterns[:3]:
                        emoji = (
                            "🟢"
                            if pattern.signal.value == "bullish"
                            else "🔴"
                            if pattern.signal.value == "bearish"
                            else "🟡"
                        )
                        pattern_name = pattern.pattern_type.value.replace(
                            "_", " "
                        ).title()
                        response += f"**{emoji} {pattern_name}**\n"
                        response += f"- {t['signal']} {pattern.signal.value.upper()}\n"
                        response += (
                            f"- {t['confidence']} {pattern.confidence * 100:.0f}%\n"
                        )
                        if pattern.key_levels:
                            target = pattern.key_levels.get(
                                "target", pattern.key_levels.get("neckline", 0)
                            )
                            if target:
                                response += f"- Target: ${target:,.2f}\n"
                        response += f"- {pattern.description}\n\n"

                # Candlestick patterns
                if candlestick_patterns:
                    response += f"{t['candlestick_patterns']}\n"
                    for signal in candlestick_patterns[:2]:
                        emoji = (
                            "🟢"
                            if signal.signal.value == "bullish"
                            else "🔴"
                            if signal.signal.value == "bearish"
                            else "🟡"
                        )
                        pattern_name = signal.pattern.value.replace("_", " ").title()
                        response += f"**{emoji} {pattern_name}**\n"
                        response += f"- {t['signal']} {signal.signal.value.upper()}\n"
                        response += (
                            f"- {t['confidence']} {signal.confidence * 100:.0f}%\n"
                        )
                        response += f"- Price: ${signal.price:,.2f}\n\n"

            response += self._get_auth_cta_message(
                language, for_action=False, is_authenticated=is_authenticated
            )

            result = {
                "content": response,
                "enrichment": {
                    "token": token,
                    "chart_patterns": [p.pattern_type.value for p in chart_patterns],
                    "candlestick_patterns": [
                        s.pattern.value for s in candlestick_patterns
                    ],
                    "hunter_tool": "pattern_recognizer",
                },
                "requires_registration": False,
            }

            # Cache the successful response
            await self._cache.set_hunter_response("patterns", token, language, result)

            return result
        except Exception as e:
            logger.error(
                f"Pattern recognition error for token {token}: {e}", exc_info=True
            )
            return self._fallback_response(
                ChatIntent.HUNTER_PATTERNS, language, is_authenticated
            )

    async def _handle_portfolio_optimization(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle portfolio optimization suggestions."""
        # Check cache first (using demo portfolio as cache key)
        cached = await self._cache.get_hunter_response("portfolio", "demo", language)
        if cached:
            logger.debug(f"Cache HIT for portfolio: demo/{language}")
            return cached

        try:
            optimizer = PortfolioOptimizer()

            # Use default portfolio for demo
            demo_portfolio = ["ETH", "BTC", "USDC"]
            result = await optimizer.optimize(demo_portfolio, risk_tolerance="moderate")

            # Translations for portfolio optimization
            translations = {
                "en": {
                    "title": "💼 **Portfolio Optimization (Demo)**",
                    "strategy": "**Strategy:**",
                    "risk_level": "**Risk Level:**",
                    "suggested_allocation": "**Suggested Allocation:**",
                    "expected_return": "**Expected Return:**",
                    "annual": "(annual)",
                    "sharpe_ratio": "**Sharpe Ratio:**",
                },
                "es": {
                    "title": "💼 **Optimización de Portafolio (Demo)**",
                    "strategy": "**Estrategia:**",
                    "risk_level": "**Nivel de Riesgo:**",
                    "suggested_allocation": "**Asignación Sugerida:**",
                    "expected_return": "**Retorno Esperado:**",
                    "annual": "(anual)",
                    "sharpe_ratio": "**Ratio de Sharpe:**",
                },
                "pt": {
                    "title": "💼 **Otimização de Portfólio (Demo)**",
                    "strategy": "**Estratégia:**",
                    "risk_level": "**Nível de Risco:**",
                    "suggested_allocation": "**Alocação Sugerida:**",
                    "expected_return": "**Retorno Esperado:**",
                    "annual": "(anual)",
                    "sharpe_ratio": "**Índice de Sharpe:**",
                },
                "zh": {
                    "title": "💼 **投资组合优化 (演示)**",
                    "strategy": "**策略:**",
                    "risk_level": "**风险级别:**",
                    "suggested_allocation": "**建议配置:**",
                    "expected_return": "**预期回报:**",
                    "annual": "(年化)",
                    "sharpe_ratio": "**夏普比率:**",
                },
            }
            t = translations.get(language, translations["en"])

            response = f"{t['title']}\n\n"
            response += f"{t['strategy']} {result.strategy}\n"
            response += f"{t['risk_level']} {result.risk_level}\n\n"

            response += f"{t['suggested_allocation']}\n"
            for token, weight in result.allocation.items():
                response += f"- {token}: {weight * 100:.0f}%\n"

            response += f"\n{t['expected_return']} {result.expected_return * 100:.1f}% {t['annual']}\n"
            response += f"{t['sharpe_ratio']} {result.sharpe_ratio:.2f}\n"

            response += self._get_auth_cta_message(
                language, for_action=True, is_authenticated=is_authenticated
            )

            result_dict = {
                "content": response,
                "enrichment": {
                    "allocation": result.allocation,
                    "expected_return": result.expected_return,
                    "sharpe_ratio": result.sharpe_ratio,
                    "hunter_tool": "portfolio_optimizer",
                },
                "requires_registration": not is_authenticated,  # Need wallet to apply
            }

            # Cache the successful response
            await self._cache.set_hunter_response(
                "portfolio", "demo", language, result_dict
            )

            return result_dict
        except Exception as e:
            logger.warning(f"Portfolio optimization error: {e}")
            return self._fallback_response(
                ChatIntent.HUNTER_PORTFOLIO, language, is_authenticated
            )

    # ========================================
    # ULTRA Handlers
    # ========================================

    async def _handle_arbitrage(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle arbitrage opportunity discovery with REAL data."""
        try:
            # Try to get real data from 1inch API
            import os

            # Try multiple sources for API key
            oneinch_api_key = None

            # 1. Try environment variable
            oneinch_api_key = os.getenv("ONEINCH_API_KEY", "").strip()

            # 2. Try from TOML config if not in env
            if not oneinch_api_key:
                try:
                    from app.setup.config.defi import load_defi_config

                    defi_config = load_defi_config()
                    oneinch_api_key = (
                        defi_config.oneinch_api_key.strip()
                        if defi_config.oneinch_api_key
                        else ""
                    )
                except (ValueError, Exception) as e:
                    logger.debug(f"Could not load 1inch API key from config: {e}")

            # 3. Try from TOML config (external_apis section in .secrets.toml)
            if not oneinch_api_key:
                try:
                    from app.setup.config.loader import (
                        load_full_config,
                        get_current_env,
                    )

                    raw_config = load_full_config(env=get_current_env())
                    if "external_apis" in raw_config and isinstance(
                        raw_config["external_apis"], dict
                    ):
                        oneinch_key = raw_config["external_apis"].get(
                            "ONEINCH_API_KEY", ""
                        )
                        if oneinch_key:
                            oneinch_api_key = str(oneinch_key).strip()
                except Exception as e:
                    logger.debug(f"Could not load 1inch API key from TOML config: {e}")

            if not oneinch_api_key:
                logger.info("1inch API key not available - using simulated data")

            discovery = ArbitrageDiscovery()
            capital = Decimal("10000")  # Demo with $10k

            # Use real data if API key is available
            if oneinch_api_key and oneinch_api_key.strip():
                try:
                    logger.info("Using 1inch API for real arbitrage data")
                    opportunities = await discovery.discover_with_real_data(
                        capital=capital,
                        oneinch_api_key=oneinch_api_key,
                        chain="ethereum",
                    )
                    logger.info(
                        f"Found {len(opportunities)} real arbitrage opportunities"
                    )
                except Exception as e:
                    logger.error(
                        f"Real arbitrage data fetch failed: {e}", exc_info=True
                    )
                    # Fallback to regular discovery if real data fails
                    opportunities = await discovery.discover_all_opportunities(capital)
            else:
                # No API key - use regular discovery (may find opportunities with increased variations)
                logger.info("No 1inch API key available, using simulated data")
                opportunities = await discovery.discover_all_opportunities(capital)

            # Translations for arbitrage
            translations = {
                "en": {
                    "title": "🔄 **Arbitrage Opportunities**",
                    "demo_note": "**Demo Mode:** Using $10,000 capital for simulation",
                    "no_opportunities": "❌ No profitable opportunities found currently.",
                    "markets_efficient": "Markets are efficient or gas > profit.",
                    "found": "**Found",
                    "opportunities": "opportunities:**",
                    "route": "Route:",
                    "net_profit": "Net Profit:",
                    "roi": "ROI:",
                },
                "es": {
                    "title": "🔄 **Oportunidades de Arbitraje**",
                    "demo_note": "**Modo Demo:** Usando $10,000 de capital para simulación",
                    "no_opportunities": "❌ No se encontraron oportunidades rentables actualmente.",
                    "markets_efficient": "Los mercados son eficientes o el gas > ganancia.",
                    "found": "**Se encontraron",
                    "opportunities": "oportunidades:**",
                    "route": "Ruta:",
                    "net_profit": "Ganancia Neta:",
                    "roi": "ROI:",
                },
                "pt": {
                    "title": "🔄 **Oportunidades de Arbitragem**",
                    "demo_note": "**Modo Demo:** Usando $10,000 de capital para simulação",
                    "no_opportunities": "❌ Nenhuma oportunidade lucrativa encontrada no momento.",
                    "markets_efficient": "Mercados são eficientes ou gas > lucro.",
                    "found": "**Encontradas",
                    "opportunities": "oportunidades:**",
                    "route": "Rota:",
                    "net_profit": "Lucro Líquido:",
                    "roi": "ROI:",
                },
                "zh": {
                    "title": "🔄 **套利机会**",
                    "demo_note": "**演示模式:** 使用 $10,000 资金进行模拟",
                    "no_opportunities": "❌ 当前未找到有利可图的机会。",
                    "markets_efficient": "市场高效或 gas > 利润。",
                    "found": "**找到",
                    "opportunities": "个机会:**",
                    "route": "路线:",
                    "net_profit": "净利润:",
                    "roi": "投资回报率:",
                },
            }
            t = translations.get(language, translations["en"])

            # Determine if using real data
            using_real_data = (
                oneinch_api_key
                and oneinch_api_key.strip()
                and any(
                    opp.metadata.get("is_real_data", False) for opp in opportunities
                )
            )

            if using_real_data:
                response = f"{t['title']}\n\n"
                response += "**Using real-time DEX data from 1inch API**\n\n"
            else:
                response = f"{t['title']}\n\n"
                response += f"{t['demo_note']}\n\n"
                if not oneinch_api_key:
                    no_key_msgs = {
                        "en": "⚠️ **Note:** Real-time data requires 1inch API key. Currently using simulated prices.",
                        "es": "⚠️ **Nota:** Los datos en tiempo real requieren una clave API de 1inch. Actualmente usando precios simulados.",
                        "pt": "⚠️ **Nota:** Dados em tempo real requerem chave API do 1inch. Atualmente usando preços simulados.",
                        "zh": "⚠️ **注意:** 实时数据需要 1inch API 密钥。当前使用模拟价格。",
                    }
                    response += f"{no_key_msgs.get(language, no_key_msgs['en'])}\n\n"

            if not opportunities:
                response += f"{t['no_opportunities']}\n\n"
                response += f"{t['markets_efficient']}\n\n"
                # Add helpful context about arbitrage
                context_msgs = {
                    "en": "**Why no opportunities?**\n"
                    "- Markets are highly efficient (prices align quickly)\n"
                    "- Gas costs exceed potential profit margins\n"
                    "- Slippage reduces profitability\n"
                    "- High competition from MEV bots\n\n"
                    "**When opportunities appear:**\n"
                    "- Market volatility creates temporary price gaps\n"
                    "- New token listings with initial price discovery\n"
                    "- Low liquidity pools with price inefficiencies\n"
                    "- Cross-chain arbitrage during bridge delays",
                    "es": "**¿Por qué no hay oportunidades?**\n"
                    "- Los mercados son muy eficientes (precios se alinean rápidamente)\n"
                    "- Los costos de gas superan los márgenes de ganancia potenciales\n"
                    "- El slippage reduce la rentabilidad\n"
                    "- Alta competencia de bots MEV\n\n"
                    "**Cuándo aparecen oportunidades:**\n"
                    "- La volatilidad del mercado crea brechas de precio temporales\n"
                    "- Nuevos listados de tokens con descubrimiento de precio inicial\n"
                    "- Pools de baja liquidez con ineficiencias de precio\n"
                    "- Arbitraje cross-chain durante retrasos de puentes",
                    "pt": "**Por que não há oportunidades?**\n"
                    "- Os mercados são altamente eficientes (preços se alinham rapidamente)\n"
                    "- Custos de gas excedem margens de lucro potenciais\n"
                    "- Slippage reduz a rentabilidade\n"
                    "- Alta competição de bots MEV\n\n"
                    "**Quando oportunidades aparecem:**\n"
                    "- Volatilidade do mercado cria lacunas de preço temporárias\n"
                    "- Novos listagens de tokens com descoberta de preço inicial\n"
                    "- Pools de baixa liquidez com ineficiências de preço\n"
                    "- Arbitragem cross-chain durante atrasos de pontes",
                    "zh": "**为什么没有机会？**\n"
                    "- 市场高度高效（价格快速对齐）\n"
                    "- Gas 成本超过潜在利润空间\n"
                    "- 滑点降低盈利能力\n"
                    "- MEV 机器人竞争激烈\n\n"
                    "**机会何时出现：**\n"
                    "- 市场波动产生临时价格差距\n"
                    "- 新代币上市时的初始价格发现\n"
                    "- 低流动性池的价格低效\n"
                    "- 跨链套利在桥接延迟期间",
                }
                response += context_msgs.get(language, context_msgs["en"])
            else:
                response += (
                    f"{t['found']} {len(opportunities)} {t['opportunities']}\n\n"
                )
                for i, opp in enumerate(opportunities[:3], 1):
                    response += f"**{i}. {opp.type.value.upper()}**\n"
                    # Build path string from trading pairs
                    path_tokens = [opp.path[0].token_in]
                    for pair in opp.path:
                        path_tokens.append(pair.token_out)
                    path_str = " → ".join(path_tokens)
                    response += f"- {t['route']} {path_str}\n"
                    response += (
                        f"- {t['net_profit']} ${float(opp.expected_profit_usd):,.2f}\n"
                    )
                    response += (
                        f"- {t['roi']} {float(opp.profit_percentage * 100):.2f}%\n\n"
                    )

            response += self._get_auth_cta_message(
                language, for_action=True, is_authenticated=is_authenticated
            )

            return {
                "content": response,
                "enrichment": {
                    "capital": 10000,
                    "opportunities_found": len(opportunities),
                    "ultra_tool": "arbitrage_discovery",
                },
                "requires_registration": not is_authenticated,  # Need wallet to execute
            }
        except Exception as e:
            logger.warning(f"Arbitrage discovery error: {e}")
            return self._fallback_response(
                ChatIntent.ULTRA_ARBITRAGE, language, is_authenticated
            )

    async def _handle_flash_loans(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle flash loan information."""
        try:
            engine = FlashLoanEngine()
            protocols = await engine.get_protocols()

            # Translations for flash loans
            translations = {
                "en": {
                    "title": "⚡ **Flash Loan Protocols**",
                    "max_loan": "Max Loan:",
                    "fee": "Fee:",
                    "tokens": "Tokens:",
                    "use_cases": "**Use Cases:**",
                    "arbitrage": "Arbitrage execution",
                    "collateral": "Collateral swaps",
                    "liquidation": "Liquidation protection",
                },
                "es": {
                    "title": "⚡ **Protocolos de Flash Loan**",
                    "max_loan": "Préstamo Máximo:",
                    "fee": "Comisión:",
                    "tokens": "Tokens:",
                    "use_cases": "**Casos de Uso:**",
                    "arbitrage": "Ejecución de arbitraje",
                    "collateral": "Intercambio de colateral",
                    "liquidation": "Protección contra liquidación",
                },
                "pt": {
                    "title": "⚡ **Protocolos de Flash Loan**",
                    "max_loan": "Empréstimo Máximo:",
                    "fee": "Taxa:",
                    "tokens": "Tokens:",
                    "use_cases": "**Casos de Uso:**",
                    "arbitrage": "Execução de arbitragem",
                    "collateral": "Trocas de garantia",
                    "liquidation": "Proteção contra liquidação",
                },
                "zh": {
                    "title": "⚡ **闪电贷协议**",
                    "max_loan": "最大贷款:",
                    "fee": "费用:",
                    "tokens": "代币:",
                    "use_cases": "**用例:**",
                    "arbitrage": "套利执行",
                    "collateral": "抵押品交换",
                    "liquidation": "清算保护",
                },
            }
            t = translations.get(language, translations["en"])

            response = f"{t['title']}\n\n"

            for protocol in protocols:
                response += f"**{protocol.name}**\n"
                response += f"- {t['max_loan']} ${float(protocol.max_loan_usd):,.0f}\n"
                response += (
                    f"- {t['fee']} {float(protocol.fee_percentage * 100):.2f}%\n"
                )
                response += (
                    f"- {t['tokens']} {', '.join(protocol.supported_tokens[:3])}\n\n"
                )

            response += f"{t['use_cases']}\n"
            response += f"- {t['arbitrage']}\n"
            response += f"- {t['collateral']}\n"
            response += f"- {t['liquidation']}\n"

            response += self._get_auth_cta_message(
                language, for_action=True, is_authenticated=is_authenticated
            )

            return {
                "content": response,
                "enrichment": {
                    "protocols": [p.name for p in protocols],
                    "ultra_tool": "flash_loan_engine",
                },
                "requires_registration": True,
            }
        except Exception as e:
            logger.warning(f"Flash loans error: {e}")
            return self._fallback_response(
                ChatIntent.ULTRA_FLASH_LOANS, language, is_authenticated
            )

    async def _handle_mev_protection(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle MEV protection information."""
        try:
            protection = MEVProtection()
            info = protection.get_protection_info()

            # Translations for MEV protection
            translations = {
                "en": {
                    "title": "🛡️ **MEV Protection Status**",
                    "flashbots": "**Flashbots:**",
                    "private_relay": "**Private Relay:**",
                    "mev_share": "**MEV-Share:**",
                    "protection_level": "**Protection Level:**",
                    "max_gas_price": "**Max Gas Price:**",
                    "protection_features": "**Protection Features:**",
                    "sandwich": "Sandwich attack prevention",
                    "front_running": "Front-running protection",
                    "private_routing": "Private transaction routing",
                    "backrun": "Backrun capture",
                    "enabled": "✅ Enabled",
                    "disabled": "❌ Disabled",
                },
                "es": {
                    "title": "🛡️ **Estado de Protección MEV**",
                    "flashbots": "**Flashbots:**",
                    "private_relay": "**Relé Privado:**",
                    "mev_share": "**MEV-Share:**",
                    "protection_level": "**Nivel de Protección:**",
                    "max_gas_price": "**Precio Máximo de Gas:**",
                    "protection_features": "**Características de Protección:**",
                    "sandwich": "Prevención de ataques sandwich",
                    "front_running": "Protección contra front-running",
                    "private_routing": "Enrutamiento de transacciones privadas",
                    "backrun": "Captura de backrun",
                    "enabled": "✅ Habilitado",
                    "disabled": "❌ Deshabilitado",
                },
                "pt": {
                    "title": "🛡️ **Status de Proteção MEV**",
                    "flashbots": "**Flashbots:**",
                    "private_relay": "**Relé Privado:**",
                    "mev_share": "**MEV-Share:**",
                    "protection_level": "**Nível de Proteção:**",
                    "max_gas_price": "**Preço Máximo de Gas:**",
                    "protection_features": "**Recursos de Proteção:**",
                    "sandwich": "Prevenção de ataques sandwich",
                    "front_running": "Proteção contra front-running",
                    "private_routing": "Roteamento de transações privadas",
                    "backrun": "Captura de backrun",
                    "enabled": "✅ Habilitado",
                    "disabled": "❌ Desabilitado",
                },
                "zh": {
                    "title": "🛡️ **MEV 保护状态**",
                    "flashbots": "**Flashbots:**",
                    "private_relay": "**私有中继:**",
                    "mev_share": "**MEV-Share:**",
                    "protection_level": "**保护级别:**",
                    "max_gas_price": "**最大 Gas 价格:**",
                    "protection_features": "**保护功能:**",
                    "sandwich": "三明治攻击防护",
                    "front_running": "抢跑保护",
                    "private_routing": "私有交易路由",
                    "backrun": "后跑捕获",
                    "enabled": "✅ 已启用",
                    "disabled": "❌ 已禁用",
                },
            }
            t = translations.get(language, translations["en"])

            enabled_text = t["enabled"]
            disabled_text = t["disabled"]

            response = f"{t['title']}\n\n"
            response += f"{t['flashbots']} {enabled_text if info['use_flashbots'] else disabled_text}\n"
            response += f"{t['private_relay']} {enabled_text if info['use_private_relay'] else disabled_text}\n"
            response += f"{t['mev_share']} {enabled_text if info['use_mev_share'] else disabled_text}\n"
            response += f"{t['protection_level']} {info['protection_level'].upper()}\n"
            response += f"{t['max_gas_price']} {info['max_gas_price_gwei']} gwei\n\n"

            response += f"{t['protection_features']}\n"
            response += f"- ✅ {t['sandwich']}\n"
            response += f"- ✅ {t['front_running']}\n"
            response += f"- ✅ {t['private_routing']}\n"
            response += f"- ✅ {t['backrun']}\n"

            response += self._get_auth_cta_message(
                language, for_action=True, is_authenticated=is_authenticated
            )

            return {
                "content": response,
                "enrichment": {
                    "protection_level": info["protection_level"],
                    "use_flashbots": info["use_flashbots"],
                    "use_private_relay": info["use_private_relay"],
                    "ultra_tool": "mev_protection",
                },
                "requires_registration": True,
            }
        except Exception as e:
            logger.warning(f"MEV protection error: {e}")
            return self._fallback_response(
                ChatIntent.ULTRA_MEV_PROTECTION, language, is_authenticated
            )

    async def _handle_auto_executor(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle auto-executor information with multi-language support."""
        translations = {
            "en": {
                "title": "🤖 **Auto-Executor Features**",
                "strategies": "**Available Strategies:**",
                "dca": "📊 DCA (Dollar Cost Averaging)",
                "limit": "🎯 Limit Orders",
                "stop_loss": "🛑 Stop-Loss Orders",
                "take_profit": "📈 Take-Profit Orders",
                "trailing": "🔄 Trailing Stops",
                "conditional": "⚡ Conditional Trades",
                "execution": "**Execution:**",
                "monitoring": "24/7 automated monitoring",
                "mev": "MEV-protected execution",
                "multichain": "Multi-chain support (ETH, ARB, OP, BASE)",
            },
            "es": {
                "title": "🤖 **Funciones del Auto-Executor**",
                "strategies": "**Estrategias Disponibles:**",
                "dca": "📊 DCA (Promedio de Costo en Dólares)",
                "limit": "🎯 Órdenes Límite",
                "stop_loss": "🛑 Órdenes Stop-Loss",
                "take_profit": "📈 Órdenes Take-Profit",
                "trailing": "🔄 Trailing Stops",
                "conditional": "⚡ Trades Condicionales",
                "execution": "**Ejecución:**",
                "monitoring": "Monitoreo automatizado 24/7",
                "mev": "Ejecución protegida contra MEV",
                "multichain": "Soporte multi-cadena (ETH, ARB, OP, BASE)",
            },
            "pt": {
                "title": "🤖 **Recursos do Auto-Executor**",
                "strategies": "**Estratégias Disponíveis:**",
                "dca": "📊 DCA (Média de Custo em Dólares)",
                "limit": "🎯 Ordens Limitadas",
                "stop_loss": "🛑 Ordens Stop-Loss",
                "take_profit": "📈 Ordens Take-Profit",
                "trailing": "🔄 Trailing Stops",
                "conditional": "⚡ Trades Condicionais",
                "execution": "**Execução:**",
                "monitoring": "Monitoramento automatizado 24/7",
                "mev": "Execução protegida contra MEV",
                "multichain": "Suporte multi-chain (ETH, ARB, OP, BASE)",
            },
            "zh": {
                "title": "🤖 **自动执行器功能**",
                "strategies": "**可用策略：**",
                "dca": "📊 DCA（平均成本法）",
                "limit": "🎯 限价单",
                "stop_loss": "🛑 止损单",
                "take_profit": "📈 止盈单",
                "trailing": "🔄 追踪止损",
                "conditional": "⚡ 条件交易",
                "execution": "**执行：**",
                "monitoring": "24/7 自动监控",
                "mev": "MEV 保护执行",
                "multichain": "多链支持 (ETH, ARB, OP, BASE)",
            },
        }

        t = translations.get(language, translations["en"])

        response = f"{t['title']}\n\n"
        response += f"{t['strategies']}\n"
        response += f"- {t['dca']}\n"
        response += f"- {t['limit']}\n"
        response += f"- {t['stop_loss']}\n"
        response += f"- {t['take_profit']}\n"
        response += f"- {t['trailing']}\n"
        response += f"- {t['conditional']}\n\n"

        response += f"{t['execution']}\n"
        response += f"- {t['monitoring']}\n"
        response += f"- {t['mev']}\n"
        response += f"- {t['multichain']}\n\n"

        response += self._get_auth_cta_message(
            language, for_action=True, is_authenticated=is_authenticated
        )

        return {
            "content": response,
            "enrichment": {
                "ultra_tool": "auto_executor",
                "supported_chains": ["ethereum", "arbitrum", "optimism", "base"],
                "strategies": ["dca", "limit", "stop_loss", "take_profit", "trailing"],
            },
            "requires_registration": True,
        }

    # ========================================
    # DeFi Handlers
    # ========================================

    async def _handle_lending(
        self,
        content: str,
        language: str,
        context: str = "",
        is_authenticated: bool = False,
        continuation_step: str | None = None,
        previous_lending_info: dict | None = None,
        wallet_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Handle lending/deposit intent with multi-step flow.

        Flow states:
        - lending_awaiting_asset: Need asset to deposit
        - lending_awaiting_amount: Need deposit amount
        - lending_awaiting_confirmation: Show vault quote, await confirmation
        """
        logger.info(
            f"[Lending] Handler called - language: {language}, authenticated: {is_authenticated}"
        )
        logger.info(f"[Lending] Continuation step: {continuation_step}")
        logger.info(f"[Lending] Previous lending info: {previous_lending_info}")

        # Use multi-step flow for both guests and authenticated users
        if self._lending_multistep:
            try:
                result = await self._lending_multistep.handle_flow(
                    content=content,
                    language=language,
                    is_authenticated=is_authenticated,
                    continuation_step=continuation_step,
                    previous_lending_info=previous_lending_info,
                    wallet_address=wallet_address,
                )
                logger.info(f"[Lending] Multi-step handler returned: {result.keys()}")
                return result
            except Exception as e:
                logger.error(f"[Lending] Multi-step handler error: {e}", exc_info=True)
                # Fall through to fallback

        # Fallback: For authenticated users, use real LendingHandler (Morpho API)
        if self._lending_handler and is_authenticated:
            try:
                # Handle continuation from previous lending query
                if continuation_step and previous_lending_info:
                    result = await self._lending_handler.execute(
                        message=content,
                        chain=previous_lending_info.get("chain", "base"),
                        asset=previous_lending_info.get("asset", "USDC"),
                        whitelisted_only=True,
                        language=language,
                        continuation_step=continuation_step,
                        previous_lending_info=previous_lending_info,
                    )
                else:
                    # Extract chain and asset from message
                    chain, asset = self._lending_handler._extract_params_from_message(
                        content
                    )

                    # Call execute method with correct parameters
                    result = await self._lending_handler.execute(
                        message=content,
                        chain=chain,
                        asset=asset,
                        whitelisted_only=True,
                        language=language,
                    )

                # Convert LendingHandlerResult to dict format
                response_content = result.content
                # Only add CTA if not in a continuation flow
                if not continuation_step:
                    response_content += self._get_auth_cta_message(
                        language, for_action=True, is_authenticated=is_authenticated
                    )

                response = {
                    "content": response_content,
                    "enrichment": {
                        "vaults": result.vaults,
                        "chain": result.chain,
                        "asset": result.asset,
                        "best_apy": result.best_apy,
                        "latency_ms": result.latency_ms,
                        "hunter_tool": "lending_handler",
                    },
                    "requires_registration": not is_authenticated,
                }

                # Include pending_action and lending_info if set (for multi-turn flows)
                if result.pending_action:
                    response["pending_action"] = result.pending_action
                    # Use lending_info from result if available, otherwise create from result
                    if hasattr(result, "lending_info") and result.lending_info:
                        response["lending_info"] = result.lending_info
                    else:
                        response["lending_info"] = {
                            "chain": result.chain,
                            "asset": result.asset,
                        }

                # Include execute_data if available (for transaction execution)
                if hasattr(result, "execute_data") and result.execute_data:
                    response["execute_data"] = result.execute_data

                return response
            except Exception as e:
                logger.error(
                    f"Lending handler error for '{content}': {e}", exc_info=True
                )

        return self._fallback_response(ChatIntent.LENDING, language, is_authenticated)

    async def _handle_money_market(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle money market rates with real Aave/Compound/Morpho data."""
        # NOTE:
        # MoneyMarketHandler exposes `compare_rates()` (not `.handle()`).
        # Calling `.handle()` forces an exception and makes the guest endpoint
        # always fall back to the generic "🏦 ¡Puedo comparar tasas..." message.
        asset = (self._extract_token(content) or "USDC").upper()
        chain = (self._extract_chain(content) or "ethereum").lower()

        try:
            handler = self._money_market_handler or MoneyMarketHandler()
            result = await handler.compare_rates(
                asset=asset,
                chain=chain,
                language=language,
            )

            return {
                "content": result.content
                + self._get_auth_cta_message(
                    language, for_action=True, is_authenticated=is_authenticated
                ),
                "enrichment": {
                    "asset": result.asset,
                    "chain": chain,
                    "rates": result.rates,
                    "best_supply_protocol": result.best_supply_protocol,
                    "best_supply_apy": result.best_supply_apy,
                    "best_borrow_protocol": result.best_borrow_protocol,
                    "best_borrow_apy": result.best_borrow_apy,
                    "latency_ms": result.latency_ms,
                },
                "requires_registration": not is_authenticated,
            }
        except Exception as e:
            logger.warning(f"Money market handler error: {e}")
            return self._fallback_response(
                ChatIntent.MONEY_MARKET, language, is_authenticated
            )

    async def _handle_swap(
        self,
        content: str,
        language: str,
        context: str = "",
        is_authenticated: bool = False,
        continuation_step: str | None = None,
        previous_swap_info: dict | None = None,
    ) -> dict[str, Any]:
        """
        Handle swap quotes with real 1inch/LiFi data or demo response.

        Supports multi-turn conversations:
        - "quiero swap" → "de USDC" → "a ETH" → "100 tokens"
        - "Swap 100 USDC for ETH"
        - "Bridge USDC from Ethereum to Base"
        - "Best swap rate for ETH to USDC"

        Args:
            content: User message
            language: Language code
            context: Previous conversation context for multi-turn support
            continuation_step: Pending action from previous message
            previous_swap_info: Accumulated swap parameters from multi-step flow
        """
        # For guest users without specific tokens, use multi-step MoonPay flow
        # This provides a guided experience: swap → from token → to token → amount → confirm
        if self._moonpay_multistep:
            # Parse to see if we have tokens from the message
            swap_info = self._parse_swap_from_context(content, context)

            # If no tokens specified OR we're in a continuation flow, use multi-step handler
            if not swap_info.get("from_token") or continuation_step:
                logger.info(
                    f"[SWAP] Delegating to multi-step MoonPay flow (continuation={continuation_step})"
                )
                return await self._moonpay_multistep.handle_flow(
                    content=content,
                    language=language,
                    is_authenticated=is_authenticated,
                    continuation_step=continuation_step,
                    previous_swap_info=previous_swap_info,
                )

        # Parse swap parameters from content and context for non-multistep flow
        swap_info = self._parse_swap_from_context(content, context)
        logger.info(f"[SWAP] Parsed swap_info: {swap_info}")

        # Try to use real swap handler if available
        if self._swap_handler:
            logger.info(f"Using real SwapHandler for swap request: {content[:50]}")
            try:
                # Extract swap parameters
                from_token = swap_info.get("from_token")
                to_token = swap_info.get("to_token")
                amount = swap_info.get("amount", "1")
                is_bridge = swap_info.get("is_bridge", False)
                from_chain = swap_info.get("from_chain", "ethereum")
                to_chain = swap_info.get("to_chain")

                # For bridge swaps
                if is_bridge and from_token and to_chain:
                    # Use default amount if not specified
                    bridge_amount = (
                        amount or "100"
                    )  # Default to 100 tokens for bridge quotes

                    result = await self._swap_handler.get_swap_quote(
                        from_token=from_token,
                        to_token=from_token,  # Same token, different chain
                        amount=bridge_amount,
                        from_chain=from_chain,
                        to_chain=to_chain,
                        slippage=1.0,
                    )
                    content_response = result.content
                    if language != "en":
                        # Translate key phrases (simplified)
                        content_response = self._translate_swap_response(
                            content_response, language
                        )

                    # Add registration message - clear that execution requires registration
                    registration_msg = self._get_registration_message_for_execution(
                        language
                    )
                    content_response += f"\n\n{registration_msg}"

                    return {
                        "content": content_response,
                        "enrichment": {
                            "from_token": result.from_token,
                            "to_token": result.to_token,
                            "from_amount": result.from_amount,
                            "to_amount": result.to_amount,
                            "chain": result.chain,
                            "aggregator": result.aggregator,
                            "is_bridge": True,
                            "from_chain": from_chain,
                            "to_chain": to_chain,
                            "latency_ms": result.latency_ms,
                            "quote": result.quote,  # Include full quote data
                        },
                        "requires_registration": True,
                    }

                # For regular swaps or best rate queries
                elif from_token and to_token:
                    result = await self._swap_handler.get_swap_quote(
                        from_token=from_token,
                        to_token=to_token,
                        amount=amount or "1",
                        from_chain=from_chain,
                        to_chain=to_chain or from_chain,
                        slippage=1.0,
                    )
                    content_response = result.content
                    if language != "en":
                        content_response = self._translate_swap_response(
                            content_response, language
                        )

                    # Add registration message - clear that execution requires registration
                    registration_msg = self._get_registration_message_for_execution(
                        language
                    )
                    content_response += f"\n\n{registration_msg}"

                    return {
                        "content": content_response,
                        "enrichment": {
                            "from_token": result.from_token,
                            "to_token": result.to_token,
                            "from_amount": result.from_amount,
                            "to_amount": result.to_amount,
                            "chain": result.chain,
                            "aggregator": result.aggregator,
                            "price_impact": result.price_impact,
                            "latency_ms": result.latency_ms,
                        },
                        "requires_registration": True,
                    }
            except Exception as e:
                logger.warning(f"Swap handler error: {e}", exc_info=True)
        else:
            logger.info("SwapHandler not available, using demo response")

        # Demo response with parsed swap info
        demo_response = self._get_swap_demo_response(
            swap_info, language, is_authenticated
        )
        # Ensure registration message is present in demo response too
        # Check if registration message is already in content (for bridge/best rate responses)
        content_lower = demo_response["content"].lower()
        has_registration_msg = (
            "to execute" in content_lower
            or "para ejecutar" in content_lower
            or "para executar" in content_lower
            or "要执行" in content_lower
        )
        if not has_registration_msg:
            registration_msg = self._get_registration_message_for_execution(language)
            demo_response["content"] += f"\n\n{registration_msg}"
        # Add registration CTA if not already present
        if (
            "👉" not in demo_response["content"]
            and "Sign up" not in demo_response["content"]
        ):
            demo_response["content"] += (
                f"\n\n{self._get_auth_cta_message(language, for_action=True, is_authenticated=is_authenticated)}"
            )
        demo_response["requires_registration"] = True
        return demo_response

    def _parse_swap_from_context(
        self, content: str, context: str
    ) -> dict[str, str | None]:
        """
        Parse swap parameters from message and conversation context.

        Supports multi-turn conversations like:
        - "quiero swap" → "de USDC" → "a ETH" → "100"
        - "Swap 100 USDC for ETH"
        - "Bridge USDC from Ethereum to Base"
        - "Best swap rate for ETH to USDC"
        """
        import re

        combined = f"{context}\n{content}".lower()

        result = {
            "from_token": None,
            "to_token": None,
            "amount": None,
            "is_complete": False,
            "is_bridge": False,
            "from_chain": None,
            "to_chain": None,
        }

        # Extract tokens mentioned
        tokens = [
            "eth",
            "usdc",
            "usdt",
            "dai",
            "wbtc",
            "weth",
            "btc",
            "sol",
            "matic",
            "arb",
            "op",
        ]
        chains = [
            "ethereum",
            "base",
            "arbitrum",
            "optimism",
            "polygon",
            "avalanche",
            "mainnet",
        ]
        found_tokens = []
        for token in tokens:
            if token in combined:
                found_tokens.append(token.upper())

        # Pattern 1: Bridge - "bridge USDC from Ethereum to Base"
        bridge_pattern = re.compile(
            r"bridge\s+(\w+)\s+(?:from\s+)?(\w+)?\s*(?:to|on)\s+(\w+)",
            re.IGNORECASE,
        )
        bridge_match = bridge_pattern.search(combined)
        if bridge_match:
            result["from_token"] = bridge_match.group(1).upper()
            if bridge_match.group(2) and bridge_match.group(2) in chains:
                result["from_chain"] = bridge_match.group(2).lower()
            if bridge_match.group(3) in chains:
                result["to_chain"] = bridge_match.group(3).lower()
            result["is_bridge"] = True
            result["is_complete"] = True
            return result

        # Pattern 2: Best swap rate - "best swap rate for ETH to USDC"
        best_rate_pattern = re.compile(
            r"(?:best\s+)?(?:swap\s+)?rate\s+(?:for|from)?\s*(\w+)\s+(?:to|for)\s+(\w+)",
            re.IGNORECASE,
        )
        best_rate_match = best_rate_pattern.search(combined)
        if best_rate_match:
            result["from_token"] = best_rate_match.group(1).upper()
            result["to_token"] = best_rate_match.group(2).upper()
            result["is_complete"] = True
            return result

        # Pattern 3: Swap with amount - "swap 100 USDC for ETH" or "swap 100 USDC to ETH"
        swap_pattern = re.compile(
            r"swap\s+(\d*\.?\d*)\s*(\w+)\s+(?:for|to)\s+(\w+)",
            re.IGNORECASE,
        )
        swap_match = swap_pattern.search(combined)
        if swap_match:
            if swap_match.group(1):
                result["amount"] = swap_match.group(1)
            result["from_token"] = swap_match.group(2).upper()
            result["to_token"] = swap_match.group(3).upper()
            result["is_complete"] = True
            return result

        # Pattern 4: Token to token - "ETH to USDC" or "USDC for ETH"
        token_to_token = re.compile(
            r"(\w+)\s+(?:to|for)\s+(\w+)",
            re.IGNORECASE,
        )
        token_match = token_to_token.search(combined)
        if token_match:
            token1 = token_match.group(1).upper()
            token2 = token_match.group(2).upper()
            if token1 in [t.upper() for t in tokens] and token2 in [
                t.upper() for t in tokens
            ]:
                result["from_token"] = token1
                result["to_token"] = token2
                result["is_complete"] = True
                return result

        # Try to extract source/target from patterns
        from_patterns = [
            r"(?:de|from|del)\s+(\w+)",
            r"swap\s+(\d*\.?\d*)\s*(\w+)",
            r"cambiar\s+(\d*\.?\d*)\s*(\w+)",
        ]
        to_patterns = [
            r"(?:a|to|hacia|por|for)\s+(\w+)",
        ]
        amount_patterns = [
            r"(\d+\.?\d*)\s*(?:tokens?)?",
            r"swap\s+(\d+\.?\d*)",
        ]

        for pattern in from_patterns:
            match = re.search(pattern, combined)
            if match:
                groups = match.groups()
                if len(groups) >= 2 and groups[0]:  # Amount + token
                    result["amount"] = groups[0]
                    token = groups[1].upper()
                    if token in [t.upper() for t in tokens]:
                        result["from_token"] = token
                elif groups[0].upper() in [t.upper() for t in tokens]:
                    result["from_token"] = groups[0].upper()

        for pattern in to_patterns:
            match = re.search(pattern, combined)
            if match and match.group(1).upper() in [t.upper() for t in tokens]:
                result["to_token"] = match.group(1).upper()

        for pattern in amount_patterns:
            match = re.search(pattern, combined)
            if match and match.group(1):
                result["amount"] = match.group(1)

        # If we found tokens but couldn't determine source/target, use order
        if found_tokens and not result["from_token"] and not result["to_token"]:
            if len(found_tokens) >= 1:
                result["from_token"] = found_tokens[0]
            if len(found_tokens) >= 2:
                result["to_token"] = found_tokens[1]

        # Check if we have enough info
        result["is_complete"] = bool(
            result["from_token"]
            and result["to_token"]
            and (result["amount"] or result["is_bridge"])
        )

        return result

    def _get_swap_demo_response(
        self,
        swap_info: dict[str, str | None],
        language: str,
        is_authenticated: bool = False,
    ) -> dict[str, Any]:
        """Generate demo swap response based on parsed info."""
        from_token = swap_info.get("from_token")
        to_token = swap_info.get("to_token")
        amount = swap_info.get("amount")
        is_complete = swap_info.get("is_complete", False)
        is_bridge = swap_info.get("is_bridge", False)
        from_chain = swap_info.get("from_chain")
        to_chain = swap_info.get("to_chain")

        logger.info(
            f"[SWAP DEMO] from_token={from_token}, to_token={to_token}, amount={amount}, is_complete={is_complete}"
        )

        # Bridge swap - show bridge quote with detailed information
        if is_bridge and from_token and to_chain:
            # Use default amount for demo if not specified
            bridge_amount = amount or "100"

            # Estimate bridge details (demo data)
            # In production, this would come from LiFi/LayerZero API
            estimated_time_minutes = 5  # Typical bridge time
            estimated_fee_usd = 2.5  # Typical bridge fee
            bridge_protocol = "LiFi"  # Default bridge aggregator

            # For same token bridge, amount received is same (minus fees)
            try:
                amount_float = float(bridge_amount)
                received_amount = amount_float * 0.9975  # ~0.25% bridge fee
            except ValueError:
                amount_float = 100.0
                received_amount = 99.75

            translations = {
                "en": {
                    "title": "🌉 **Bridge Quote**",
                    "from": f"**From:** {bridge_amount} {from_token}",
                    "from_chain": f"**Source Chain:** {from_chain or 'Ethereum'}",
                    "to_chain": f"**Destination Chain:** {to_chain}",
                    "to": f"**You'll Receive:** ~{received_amount:.2f} {from_token}",
                    "protocol": f"**Bridge Protocol:** {bridge_protocol}",
                    "time": f"**Estimated Time:** ~{estimated_time_minutes} minutes",
                    "fee": f"**Bridge Fee:** ~${estimated_fee_usd:.2f}",
                    "gas": "**Estimated Gas:** ~$5-10 (source chain)",
                    "note": "⚠️ **To execute this bridge, you need to register.** Sign up to proceed with the transaction.",
                },
                "es": {
                    "title": "🌉 **Cotización de Bridge**",
                    "from": f"**Desde:** {bridge_amount} {from_token}",
                    "from_chain": f"**Cadena Origen:** {from_chain or 'Ethereum'}",
                    "to_chain": f"**Cadena Destino:** {to_chain}",
                    "to": f"**Recibirás:** ~{received_amount:.2f} {from_token}",
                    "protocol": f"**Protocolo de Bridge:** {bridge_protocol}",
                    "time": f"**Tiempo Estimado:** ~{estimated_time_minutes} minutos",
                    "fee": f"**Tarifa de Bridge:** ~${estimated_fee_usd:.2f}",
                    "gas": "**Gas Estimado:** ~$5-10 (cadena origen)",
                    "note": "⚠️ **Para ejecutar este bridge, necesitas registrarte.** Regístrate para proceder con la transacción.",
                },
                "pt": {
                    "title": "🌉 **Cotação de Bridge**",
                    "from": f"**De:** {bridge_amount} {from_token}",
                    "from_chain": f"**Cadeia Origem:** {from_chain or 'Ethereum'}",
                    "to_chain": f"**Cadeia Destino:** {to_chain}",
                    "to": f"**Você Receberá:** ~{received_amount:.2f} {from_token}",
                    "protocol": f"**Protocolo de Bridge:** {bridge_protocol}",
                    "time": f"**Tempo Estimado:** ~{estimated_time_minutes} minutos",
                    "fee": f"**Taxa de Bridge:** ~${estimated_fee_usd:.2f}",
                    "gas": "**Gas Estimado:** ~$5-10 (cadeia origem)",
                    "note": "⚠️ **Para executar este bridge, você precisa se cadastrar.** Cadastre-se para prosseguir com a transação.",
                },
                "zh": {
                    "title": "🌉 **桥接报价**",
                    "from": f"**从:** {bridge_amount} {from_token}",
                    "from_chain": f"**源链:** {from_chain or 'Ethereum'}",
                    "to_chain": f"**目标链:** {to_chain}",
                    "to": f"**您将收到:** ~{received_amount:.2f} {from_token}",
                    "protocol": f"**桥接协议:** {bridge_protocol}",
                    "time": f"**预计时间:** ~{estimated_time_minutes} 分钟",
                    "fee": f"**桥接费用:** ~${estimated_fee_usd:.2f}",
                    "gas": "**预估Gas:** ~$5-10 (源链)",
                    "note": "⚠️ **要执行此桥接，您需要注册。** 注册以继续交易。",
                },
            }
            t = translations.get(language, translations["en"])

            response = f"{t['title']}\n\n"
            response += f"{t['from']}\n"
            response += f"{t['from_chain']}\n"
            response += f"{t['to_chain']}\n\n"
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"**DETAILS**\n"
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"{t['to']}\n"
            response += f"{t['protocol']}\n"
            response += f"{t['time']}\n"
            response += f"{t['fee']}\n"
            response += f"{t['gas']}\n\n"
            response += f"{t['note']}\n\n"
            # Note: registration_cta is added by the caller, don't duplicate here

            return {
                "content": response,
                "enrichment": {
                    "swap_demo": True,
                    "is_bridge": True,
                    "from_token": from_token,
                    "from_chain": from_chain or "ethereum",
                    "to_chain": to_chain,
                    "from_amount": bridge_amount,
                    "to_amount": str(received_amount),
                    "bridge_protocol": bridge_protocol,
                    "estimated_time_minutes": estimated_time_minutes,
                    "estimated_fee_usd": estimated_fee_usd,
                },
                "requires_registration": True,
            }

        # Best rate query - show comprehensive rate comparison
        if is_complete and from_token and to_token and not amount:
            # Demo rates for common pairs
            demo_rates = {
                ("ETH", "USDC"): 2200.0,
                ("USDC", "ETH"): 0.0004545,
                ("ETH", "USDT"): 2200.0,
                ("USDT", "ETH"): 0.0004545,
                ("BTC", "USDC"): 45000.0,
                ("USDC", "BTC"): 0.0000222,
            }

            rate = demo_rates.get((from_token.upper(), to_token.upper()))
            if not rate:
                # Default rate estimation
                rate = 1.0 if from_token.upper() == to_token.upper() else 0.5

            # Simulate multiple protocol rates for comparison
            base_rate = rate
            protocols = [
                {
                    "name": "1inch",
                    "rate": base_rate,
                    "price_impact": 0.12,
                    "gas_usd": 8.50,
                    "slippage": 0.1,
                },
                {
                    "name": "Uniswap V3",
                    "rate": base_rate * 0.9995,
                    "price_impact": 0.15,
                    "gas_usd": 12.00,
                    "slippage": 0.3,
                },
                {
                    "name": "Curve",
                    "rate": base_rate * 0.9998,
                    "price_impact": 0.08,
                    "gas_usd": 15.00,
                    "slippage": 0.1,
                },
                {
                    "name": "Balancer",
                    "rate": base_rate * 0.9992,
                    "price_impact": 0.18,
                    "gas_usd": 10.00,
                    "slippage": 0.2,
                },
            ]

            # Sort by best rate
            protocols.sort(key=lambda x: x["rate"], reverse=True)
            best_protocol = protocols[0]

            translations = {
                "en": {
                    "title": "🔄 **Best Swap Rate Comparison**",
                    "best_rate": f"**Best Rate:** 1 {from_token.upper()} = {best_protocol['rate']:.6f} {to_token.upper()}",
                    "best_protocol": f"**Best Protocol:** {best_protocol['name']}",
                    "comparison": "**Protocol Comparison:**",
                    "protocol_row": "• **{name}**: {rate:.6f} {to_token} | Impact: {impact}% | Gas: ${gas:.2f}",
                    "price_impact": f"**Price Impact:** {best_protocol['price_impact']:.2f}%",
                    "gas_estimate": f"**Estimated Gas:** ${best_protocol['gas_usd']:.2f}",
                    "slippage": f"**Slippage:** {best_protocol['slippage']:.1f}%",
                    "note": f"👉 **To execute swap {from_token.upper()} to {to_token.upper()}, you need to register**",
                },
                "es": {
                    "title": "🔄 **Comparación de Mejores Tasas**",
                    "best_rate": f"**Mejor Tasa:** 1 {from_token.upper()} = {best_protocol['rate']:.6f} {to_token.upper()}",
                    "best_protocol": f"**Mejor Protocolo:** {best_protocol['name']}",
                    "comparison": "**Comparación de Protocolos:**",
                    "protocol_row": "• **{name}**: {rate:.6f} {to_token} | Impacto: {impact}% | Gas: ${gas:.2f}",
                    "price_impact": f"**Impacto de Precio:** {best_protocol['price_impact']:.2f}%",
                    "gas_estimate": f"**Gas Estimado:** ${best_protocol['gas_usd']:.2f}",
                    "slippage": f"**Deslizamiento:** {best_protocol['slippage']:.1f}%",
                    "note": f"👉 **Para ejecutar swap de {from_token.upper()} a {to_token.upper()}, necesitas registrarte**",
                },
                "pt": {
                    "title": "🔄 **Comparação de Melhores Taxas**",
                    "best_rate": f"**Melhor Taxa:** 1 {from_token.upper()} = {best_protocol['rate']:.6f} {to_token.upper()}",
                    "best_protocol": f"**Melhor Protocolo:** {best_protocol['name']}",
                    "comparison": "**Comparação de Protocolos:**",
                    "protocol_row": "• **{name}**: {rate:.6f} {to_token} | Impacto: {impact}% | Gas: ${gas:.2f}",
                    "price_impact": f"**Impacto de Preço:** {best_protocol['price_impact']:.2f}%",
                    "gas_estimate": f"**Gas Estimado:** ${best_protocol['gas_usd']:.2f}",
                    "slippage": f"**Deslizamento:** {best_protocol['slippage']:.1f}%",
                    "note": f"👉 **Para executar swap de {from_token.upper()} para {to_token.upper()}, você precisa se cadastrar**",
                },
                "zh": {
                    "title": "🔄 **最佳交换率比较**",
                    "best_rate": f"**最佳汇率:** 1 {from_token.upper()} = {best_protocol['rate']:.6f} {to_token.upper()}",
                    "best_protocol": f"**最佳协议:** {best_protocol['name']}",
                    "comparison": "**协议比较:**",
                    "protocol_row": "• **{name}**: {rate:.6f} {to_token} | 影响: {impact}% | Gas: ${gas:.2f}",
                    "price_impact": f"**价格影响:** {best_protocol['price_impact']:.2f}%",
                    "gas_estimate": f"**预估Gas:** ${best_protocol['gas_usd']:.2f}",
                    "slippage": f"**滑点:** {best_protocol['slippage']:.1f}%",
                    "note": "⚠️ **要执行此交换，您需要注册。** 注册以继续交易。",
                },
            }
            t = translations.get(language, translations["en"])

            response = f"{t['title']}\n\n"
            response += f"{t['best_rate']}\n"
            response += f"{t['best_protocol']}\n\n"
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"{t['comparison']}\n"
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for proto in protocols:
                response += f"{t['protocol_row'].format(name=proto['name'], rate=proto['rate'], to_token=to_token.upper(), impact=proto['price_impact'], gas=proto['gas_usd'])}\n"
            response += f"\n"
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"**DETAILS**\n"
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"{t['price_impact']}\n"
            response += f"{t['gas_estimate']}\n"
            response += f"{t['slippage']}\n\n"
            response += f"{t['note']}\n\n"
            # Note: registration_cta is added by the caller if needed

            return {
                "content": response,
                "enrichment": {
                    "swap_demo": True,
                    "is_best_rate": True,
                    "from_token": from_token,
                    "to_token": to_token,
                    "rate": best_protocol["rate"],
                    "protocol": best_protocol["name"],
                    "protocols": protocols,
                    "price_impact": best_protocol["price_impact"],
                    "gas_estimate": best_protocol["gas_usd"],
                    "slippage": best_protocol["slippage"],
                },
                "requires_registration": True,
            }

        if is_complete and from_token and to_token and amount:
            logger.info(
                f"[SWAP DEMO] Entering complete swap block with amount={amount}"
            )
            # Generate realistic demo quote
            demo_rates = {
                ("USDC", "ETH"): 0.00045,
                ("ETH", "USDC"): 2200.0,
                ("USDC", "WBTC"): 0.000024,
                ("WBTC", "USDC"): 42000.0,
                ("ETH", "WBTC"): 0.053,
                ("WBTC", "ETH"): 18.9,
            }

            rate = demo_rates.get((from_token, to_token), 1.0)
            try:
                from_amount = float(amount)
                to_amount = from_amount * rate
            except ValueError:
                from_amount = 100.0
                to_amount = from_amount * rate

            translations = {
                "en": {
                    "title": "🔄 **Swap Quote**",
                    "from": "From",
                    "to": "To",
                    "rate": "Rate",
                    "impact": "Price Impact",
                    "gas": "Est. Gas",
                    "note": f"👉 **To execute swap {amount} {from_token} to {to_token}, you need to register**",
                },
                "es": {
                    "title": "🔄 **Cotización de Swap**",
                    "from": "De",
                    "to": "A",
                    "rate": "Tasa",
                    "impact": "Impacto en Precio",
                    "gas": "Gas Est.",
                    "note": f"👉 **Para ejecutar swap de {amount} {from_token} a {to_token}, necesitas registrarte**",
                },
                "pt": {
                    "title": "🔄 **Cotação de Swap**",
                    "from": "De",
                    "to": "Para",
                    "rate": "Taxa",
                    "impact": "Impacto no Preço",
                    "gas": "Gas Est.",
                    "note": f"👉 **Para executar swap de {amount} {from_token} para {to_token}, você precisa se cadastrar**",
                },
                "zh": {
                    "title": "🔄 **交换报价**",
                    "from": "从",
                    "to": "到",
                    "rate": "汇率",
                    "impact": "价格影响",
                    "gas": "预估Gas",
                    "note": f"👉 **执行 {amount} {from_token} 到 {to_token} 的交换需要注册**",
                },
            }
            t = translations.get(language, translations["en"])

            response = f"{t['title']}\n\n"
            response += f"**{t['from']}:** {from_amount:.4f} {from_token}\n"
            response += f"**{t['to']}:** {to_amount:.6f} {to_token}\n\n"
            response += f"**{t['rate']}:** 1 {from_token} = {rate:.6f} {to_token}\n"
            response += f"**{t['impact']}:** ~0.12%\n"
            response += f"**{t['gas']}:** ~$0.50\n\n"
            response += f"{t['note']}\n\n"
            response += self._get_auth_cta_message(
                language, for_action=True, is_authenticated=is_authenticated
            )

            return {
                "content": response,
                "enrichment": {
                    "swap_demo": True,
                    "from_token": from_token,
                    "to_token": to_token,
                    "from_amount": str(from_amount),
                    "to_amount": str(to_amount),
                    "rate": rate,
                },
                "requires_registration": True,
            }

        # Incomplete swap - ask for more info WITH persuasive registration CTA
        if from_token and not to_token:
            prompts = {
                "en": f"🔄 Got it! You want to swap **{from_token}**. What token would you like to receive?\n\n👉 **To execute the swap, you need to register**",
                "es": f"🔄 ¡Entendido! Quieres cambiar **{from_token}**. ¿A qué token quieres cambiar?\n\n👉 **Para ejecutar el swap, necesitas registrarte**",
                "pt": f"🔄 Entendi! Você quer trocar **{from_token}**. Para qual token você quer trocar?\n\n👉 **Para executar o swap, você precisa se cadastrar**",
                "zh": f"🔄 好的！您想交换 **{from_token}**。您想要接收什么代币？\n\n👉 **执行交换需要注册**",
            }
        elif from_token and to_token and not amount:
            prompts = {
                "en": f"🔄 Perfect! Swapping **{from_token}** to **{to_token}**. How much {from_token} would you like to swap?\n\n👉 **To execute swap {from_token} to {to_token}, you need to register**",
                "es": f"🔄 ¡Perfecto! Cambiando **{from_token}** a **{to_token}**. ¿Cuánto {from_token} quieres cambiar?\n\n👉 **Para ejecutar swap de {from_token} a {to_token}, necesitas registrarte**",
                "pt": f"🔄 Perfeito! Trocando **{from_token}** para **{to_token}**. Quanto {from_token} você quer trocar?\n\n👉 **Para executar swap de {from_token} para {to_token}, você precisa se cadastrar**",
                "zh": f"🔄 好的！将 **{from_token}** 交换为 **{to_token}**。您想交换多少 {from_token}？\n\n👉 **执行 {from_token} 到 {to_token} 的交换需要注册**",
            }
        else:
            prompts = {
                "en": "🔄 I can help you swap tokens! Please tell me:\n\n• **From:** Which token to swap\n• **To:** Which token to receive\n• **Amount:** How much to swap\n\nExample: *swap 100 USDC to ETH*\n\n👉 **To execute any swap, you need to register**",
                "es": "🔄 ¡Puedo ayudarte a cambiar tokens! Por favor dime:\n\n• **De:** Qué token cambiar\n• **A:** Qué token recibir\n• **Cantidad:** Cuánto cambiar\n\nEjemplo: *cambiar 100 USDC a ETH*\n\n👉 **Para ejecutar cualquier swap, necesitas registrarte**",
                "pt": "🔄 Posso ajudá-lo a trocar tokens! Por favor me diga:\n\n• **De:** Qual token trocar\n• **Para:** Qual token receber\n• **Quantidade:** Quanto trocar\n\nExemplo: *trocar 100 USDC para ETH*\n\n👉 **Para executar qualquer swap, você precisa se cadastrar**",
                "zh": "🔄 我可以帮您交换代币！请告诉我：\n\n• **从：** 要交换的代币\n• **到：** 要接收的代币\n• **数量：** 交换多少\n\n示例：*交换 100 USDC 到 ETH*\n\n👉 **执行任何交换都需要注册**",
            }

        return {
            "content": prompts.get(language, prompts["en"]),
            "enrichment": {
                "swap_demo": True,
                "awaiting_info": True,
                "from_token": from_token,
                "to_token": to_token,
                "amount": amount,
            },
            "requires_registration": True,
        }

    # ========================================
    # Agent Squad Handlers
    # ========================================

    async def _handle_specialist_task(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle specialist task requests (Agent Squad)."""
        translations = {
            "en": {
                "title": "🤖 **Agent Squad - Specialist Agents**",
                "desc": "Our AI agents can help with specialized DeFi tasks:",
                "agents": [
                    (
                        "🔬 Research Agent",
                        "Deep protocol analysis and yield strategies",
                    ),
                    (
                        "🛡️ Security Auditor",
                        "Smart contract security analysis via Slither",
                    ),
                    (
                        "⛽ Gas Optimizer",
                        "Reduce transaction costs with optimal timing",
                    ),
                    ("📊 Tax Optimizer", "Capital gains strategies and tax reporting"),
                    (
                        "📈 Risk Analyzer",
                        "Portfolio risk assessment and exposure analysis",
                    ),
                    (
                        "💼 Portfolio Agent",
                        "Asset allocation and rebalancing recommendations",
                    ),
                    ("🌉 Bridge Agent", "Cross-chain transfers via Axelar/LayerZero"),
                    ("🏛️ Compliance", "AML/KYC checks via Chainalysis"),
                    ("🔐 Multi-Sig", "Gnosis Safe treasury management"),
                    ("🗳️ DAO Governance", "Snapshot voting and proposals"),
                    ("🖼️ NFT Manager", "NFT portfolio via OpenSea"),
                    ("💰 Lending Agent", "Aave/Morpho borrow optimization"),
                ],
            },
            "es": {
                "title": "🤖 **Agent Squad - Agentes Especialistas**",
                "desc": "Nuestros agentes IA pueden ayudarte con tareas DeFi especializadas:",
                "agents": [
                    ("🔬 Agente de Investigación", "Análisis profundo de protocolos"),
                    ("🛡️ Auditor de Seguridad", "Análisis de contratos inteligentes"),
                    ("⛽ Optimizador de Gas", "Reduce costos de transacción"),
                    ("📊 Optimizador de Impuestos", "Estrategias fiscales"),
                    ("📈 Analizador de Riesgo", "Evaluación de riesgo del portafolio"),
                    ("💼 Agente de Portafolio", "Recomendaciones de asignación"),
                    ("🌉 Agente de Bridge", "Transferencias cross-chain"),
                    ("🏛️ Compliance", "Verificaciones AML/KYC"),
                    ("🔐 Multi-Sig", "Gestión de tesorería Gnosis Safe"),
                    ("🗳️ Gobernanza DAO", "Votaciones y propuestas Snapshot"),
                    ("🖼️ Gestor NFT", "Portafolio NFT via OpenSea"),
                    ("💰 Agente de Préstamos", "Optimización Aave/Morpho"),
                ],
            },
            "pt": {
                "title": "🤖 **Agent Squad - Agentes Especialistas**",
                "desc": "Nossos agentes IA podem ajudar com tarefas DeFi especializadas:",
                "agents": [
                    ("🔬 Agente de Pesquisa", "Análise profunda de protocolos"),
                    ("🛡️ Auditor de Segurança", "Análise de contratos inteligentes"),
                    ("⛽ Otimizador de Gas", "Reduz custos de transação"),
                    ("📊 Otimizador de Impostos", "Estratégias fiscais"),
                    ("📈 Analisador de Risco", "Avaliação de risco do portfólio"),
                    ("💼 Agente de Portfólio", "Recomendações de alocação"),
                    ("🌉 Agente de Bridge", "Transferências cross-chain"),
                    ("🏛️ Compliance", "Verificações AML/KYC"),
                    ("🔐 Multi-Sig", "Gestão de tesouraria Gnosis Safe"),
                    ("🗳️ Governança DAO", "Votações e propostas Snapshot"),
                    ("🖼️ Gestor NFT", "Portfólio NFT via OpenSea"),
                    ("💰 Agente de Empréstimos", "Otimização Aave/Morpho"),
                ],
            },
            "zh": {
                "title": "🤖 **Agent Squad - 专家代理**",
                "desc": "我们的AI代理可以帮助处理专业的DeFi任务：",
                "agents": [
                    ("🔬 研究代理", "深度协议分析和收益策略"),
                    ("🛡️ 安全审计师", "通过Slither进行智能合约安全分析"),
                    ("⛽ Gas优化器", "通过最佳时机减少交易成本"),
                    ("📊 税务优化器", "资本利得策略和税务报告"),
                    ("📈 风险分析师", "投资组合风险评估"),
                    ("💼 投资组合代理", "资产配置和再平衡建议"),
                    ("🌉 跨链代理", "通过Axelar/LayerZero跨链转账"),
                    ("🏛️ 合规", "通过Chainalysis进行AML/KYC检查"),
                    ("🔐 多签", "Gnosis Safe资金管理"),
                    ("🗳️ DAO治理", "Snapshot投票和提案"),
                    ("🖼️ NFT管理器", "通过OpenSea管理NFT投资组合"),
                    ("💰 借贷代理", "Aave/Morpho借贷优化"),
                ],
            },
        }

        t = translations.get(language, translations["en"])

        response = f"{t['title']}\n\n{t['desc']}\n\n"
        for agent_name, agent_desc in t["agents"]:
            response += f"- {agent_name}: {agent_desc}\n"

        response += "\n" + self._get_auth_cta_message(
            language, for_action=True, is_authenticated=is_authenticated
        )

        return {
            "content": response,
            "enrichment": {
                "agent_squad": True,
                "available_agents": [
                    "research",
                    "security_auditor",
                    "gas_optimizer",
                    "tax_optimizer",
                    "risk_analyzer",
                    "portfolio",
                    "bridge_crosschain",
                    "compliance_monitor",
                    "multisig_coordinator",
                    "dao_governance",
                    "nft_asset_manager",
                    "lending_borrowing",
                ],
            },
            "requires_registration": True,
        }

    async def _handle_complex_workflow(
        self, content: str, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Handle complex workflow requests (Supervisor)."""
        translations = {
            "en": {
                "title": "🧠 **Agent Squad - Multi-Agent Workflows**",
                "desc": "Our Supervisor can coordinate multiple agents for complex tasks:",
                "examples": [
                    "📊 Portfolio rebalancing with tax optimization",
                    "🔍 Comprehensive DeFi protocol analysis",
                    "⚖️ Risk assessment + execution planning",
                    "💰 Yield optimization with security audit",
                    "🌉 Cross-chain migration strategy",
                ],
                "how": "**How it works:**",
                "steps": [
                    "1️⃣ Supervisor analyzes your request",
                    "2️⃣ Selects relevant specialist agents",
                    "3️⃣ Coordinates their outputs",
                    "4️⃣ Delivers comprehensive results",
                ],
            },
            "es": {
                "title": "🧠 **Agent Squad - Flujos Multi-Agente**",
                "desc": "Nuestro Supervisor puede coordinar múltiples agentes:",
                "examples": [
                    "📊 Rebalanceo de portafolio con optimización fiscal",
                    "🔍 Análisis comprensivo de protocolos DeFi",
                    "⚖️ Evaluación de riesgo + planificación de ejecución",
                    "💰 Optimización de rendimiento con auditoría de seguridad",
                    "🌉 Estrategia de migración cross-chain",
                ],
                "how": "**Cómo funciona:**",
                "steps": [
                    "1️⃣ El Supervisor analiza tu solicitud",
                    "2️⃣ Selecciona agentes especialistas relevantes",
                    "3️⃣ Coordina sus resultados",
                    "4️⃣ Entrega resultados comprensivos",
                ],
            },
            "pt": {
                "title": "🧠 **Agent Squad - Fluxos Multi-Agente**",
                "desc": "Nosso Supervisor pode coordenar múltiplos agentes:",
                "examples": [
                    "📊 Rebalanceamento de portfólio com otimização fiscal",
                    "🔍 Análise abrangente de protocolos DeFi",
                    "⚖️ Avaliação de risco + planejamento de execução",
                    "💰 Otimização de rendimento com auditoria de segurança",
                    "🌉 Estratégia de migração cross-chain",
                ],
                "how": "**Como funciona:**",
                "steps": [
                    "1️⃣ O Supervisor analisa sua solicitação",
                    "2️⃣ Seleciona agentes especialistas relevantes",
                    "3️⃣ Coordena seus resultados",
                    "4️⃣ Entrega resultados abrangentes",
                ],
            },
            "zh": {
                "title": "🧠 **Agent Squad - 多代理工作流**",
                "desc": "我们的Supervisor可以协调多个代理处理复杂任务：",
                "examples": [
                    "📊 投资组合再平衡与税务优化",
                    "🔍 全面的DeFi协议分析",
                    "⚖️ 风险评估 + 执行规划",
                    "💰 收益优化与安全审计",
                    "🌉 跨链迁移策略",
                ],
                "how": "**工作原理：**",
                "steps": [
                    "1️⃣ Supervisor分析您的请求",
                    "2️⃣ 选择相关专家代理",
                    "3️⃣ 协调他们的输出",
                    "4️⃣ 交付全面结果",
                ],
            },
        }

        t = translations.get(language, translations["en"])

        response = f"{t['title']}\n\n{t['desc']}\n\n**Examples:**\n"
        for example in t["examples"]:
            response += f"- {example}\n"

        response += f"\n{t['how']}\n"
        for step in t["steps"]:
            response += f"{step}\n"

        response += "\n" + self._get_auth_cta_message(
            language, for_action=True, is_authenticated=is_authenticated
        )

        return {
            "content": response,
            "enrichment": {
                "agent_squad": True,
                "workflow_type": "supervisor",
                "max_agents": 5,
            },
            "requires_registration": True,
        }

    # ========================================
    # Helpers
    # ========================================

    def _extract_token(self, content: str) -> str | None:
        """Extract token symbol from content."""
        content_lower = content.lower()

        # Token aliases map common names to their symbols
        token_aliases = {
            "bitcoin": "BTC",
            "btc": "BTC",
            "ethereum": "ETH",
            "eth": "ETH",
            "ether": "ETH",
            "solana": "SOL",
            "sol": "SOL",
            "usdc": "USDC",
            "usdt": "USDT",
            "tether": "USDT",
            "dai": "DAI",
            "weth": "WETH",
            "wrapped eth": "WETH",
            "wrapped ether": "WETH",
            "wbtc": "WBTC",
            "wrapped bitcoin": "WBTC",
            "matic": "MATIC",
            "polygon": "MATIC",
            "arbitrum": "ARB",
            "arb": "ARB",
            "optimism": "OP",
            "op": "OP",
        }

        # Check aliases (longer names first to avoid partial matches)
        for alias, symbol in sorted(token_aliases.items(), key=lambda x: -len(x[0])):
            if alias in content_lower:
                return symbol
        return None

    def _extract_token_from_context(self, context: str) -> str | None:
        """Extract token from conversation context (for follow-up questions)."""
        if not context:
            return None

        # Look for token mentions in context
        # Context format: "User: message\nAssistant: response\n..."
        context_lower = context.lower()

        # Extract token from context using same logic as _extract_token
        token_aliases = {
            "bitcoin": "BTC",
            "btc": "BTC",
            "ethereum": "ETH",
            "eth": "ETH",
            "ether": "ETH",
            "solana": "SOL",
            "sol": "SOL",
            "usdc": "USDC",
            "usdt": "USDT",
            "tether": "USDT",
            "dai": "DAI",
            "weth": "WETH",
            "wrapped eth": "WETH",
            "wrapped ether": "WETH",
            "wbtc": "WBTC",
            "wrapped bitcoin": "WBTC",
            "matic": "MATIC",
            "polygon": "MATIC",
            "arbitrum": "ARB",
            "arb": "ARB",
            "optimism": "OP",
            "op": "OP",
        }

        # Check aliases (longer names first to avoid partial matches)
        for alias, symbol in sorted(token_aliases.items(), key=lambda x: -len(x[0])):
            if alias in context_lower:
                return symbol
        return None

    def _extract_chain(self, content: str) -> str | None:
        """Extract chain name from content (best-effort)."""
        content_lower = content.lower()

        chain_aliases = {
            # Canonical: ethereum
            "ethereum": "ethereum",
            "mainnet": "ethereum",
            # L2s
            "base": "base",
            "arbitrum": "arbitrum",
            "optimism": "optimism",
            # Other EVM
            "polygon": "polygon",
            "avalanche": "avalanche",
        }

        for alias, chain in sorted(chain_aliases.items(), key=lambda x: -len(x[0])):
            if alias in content_lower:
                return chain

        # Short aliases (avoid false positives like "eth" in "tether")
        if " op " in f" {content_lower} ":
            return "optimism"
        if " arb " in f" {content_lower} ":
            return "arbitrum"
        if " eth " in f" {content_lower} ":
            return "ethereum"

        return None

    def _translate_swap_response(self, content: str, language: str) -> str:
        """Translate swap response content to target language."""
        # Simple translation mapping for key phrases
        translations = {
            "es": {
                "Swap Quote": "Cotización de Swap",
                "From": "Desde",
                "To": "A",
                "Rate": "Tasa",
                "Price Impact": "Impacto en Precio",
                "Est. Gas": "Gas Est.",
                "Chain": "Cadena",
                "Cross-Chain Swap": "Swap Cross-Chain",
                "Route": "Ruta",
                "Estimated Time": "Tiempo Estimado",
                "Aggregator": "Agregador",
                "Ready to swap?": "¿Listo para intercambiar?",
            },
            "pt": {
                "Swap Quote": "Cotação de Swap",
                "From": "De",
                "To": "Para",
                "Rate": "Taxa",
                "Price Impact": "Impacto no Preço",
                "Est. Gas": "Gas Est.",
                "Chain": "Cadeia",
                "Cross-Chain Swap": "Swap Cross-Chain",
                "Route": "Rota",
                "Estimated Time": "Tempo Estimado",
                "Aggregator": "Agregador",
                "Ready to swap?": "Pronto para trocar?",
            },
            "zh": {
                "Swap Quote": "交换报价",
                "From": "从",
                "To": "到",
                "Rate": "汇率",
                "Price Impact": "价格影响",
                "Est. Gas": "预估Gas",
                "Chain": "链",
                "Cross-Chain Swap": "跨链交换",
                "Route": "路线",
                "Estimated Time": "预计时间",
                "Aggregator": "聚合器",
                "Ready to swap?": "准备交换？",
            },
        }

        if language not in translations:
            return content

        translated = content
        for en_phrase, translated_phrase in translations[language].items():
            translated = translated.replace(en_phrase, translated_phrase)

        return translated

    def _get_registration_message_for_execution(self, language: str) -> str:
        """Get registration message specifically for swap execution."""
        messages = {
            "en": "⚠️ **To execute this swap, you need to register.** Sign up to proceed with the transaction.",
            "es": "⚠️ **Para ejecutar este swap, necesitas registrarte.** Regístrate para proceder con la transacción.",
            "pt": "⚠️ **Para executar este swap, você precisa se cadastrar.** Cadastre-se para prosseguir com a transação.",
            "zh": "⚠️ **要执行此交换，您需要注册。** 注册以继续交易。",
        }
        return messages.get(language, messages["en"])

    def _get_registration_cta(self, language: str, for_action: bool = False) -> str:
        """Get registration call-to-action based on language."""
        if for_action:
            ctas = {
                "en": "\n\n👉 **Sign up to execute this action**",
                "es": "\n\n👉 **Regístrate para ejecutar esta acción**",
                "pt": "\n\n👉 **Cadastre-se para executar esta ação**",
                "zh": "\n\n👉 **注册以执行此操作**",
            }
        else:
            ctas = {
                "en": "\n\n👉 **Sign up for real-time alerts**",
                "es": "\n\n👉 **Regístrate para alertas en tiempo real**",
                "pt": "\n\n👉 **Cadastre-se para alertas em tempo real**",
                "zh": "\n\n👉 **注册以获取实时警报**",
            }
        return ctas.get(language, ctas["en"])

    def _get_auth_cta_message(
        self, language: str, for_action: bool = False, is_authenticated: bool = False
    ) -> str:
        """
        Get registration CTA message based on authentication status.

        Returns empty string if user is authenticated (no signup prompts needed).
        """
        if is_authenticated:
            return ""
        return self._get_registration_cta(language, for_action)

    def _fallback_response(
        self, intent: ChatIntent, language: str, is_authenticated: bool = False
    ) -> dict[str, Any]:
        """Generate fallback response when handler fails."""
        fallbacks = {
            ChatIntent.HUNTER_SENTIMENT: {
                "en": "🎯 Sentiment analysis is temporarily unavailable. Please try again.",
                "es": "🎯 El análisis de sentimiento no está disponible. Intenta de nuevo.",
                "pt": "🎯 Análise de sentimento indisponível. Tente novamente.",
                "zh": "🎯 情绪分析暂时不可用。请重试。",
            },
            ChatIntent.HUNTER_PRICE_PREDICTION: {
                "en": "📈 Price prediction service is loading. Please try again.",
                "es": "📈 El servicio de predicción de precios está cargando. Intenta de nuevo.",
                "pt": "📈 Serviço de previsão de preços carregando. Tente novamente.",
                "zh": "📈 价格预测服务正在加载。请重试。",
            },
            ChatIntent.SWAP: {
                "en": "🔄 I can help you swap tokens! Please tell me:\n\n• **From:** Which token to swap\n• **To:** Which token to receive\n• **Amount:** How much to swap\n\nExample: *swap 100 USDC to ETH*\n\n👉 **To execute any swap, you need to register**",
                "es": "🔄 ¡Puedo ayudarte a cambiar tokens! Por favor dime:\n\n• **De:** Qué token cambiar\n• **A:** Qué token recibir\n• **Cantidad:** Cuánto cambiar\n\nEjemplo: *cambiar 100 USDC a ETH*\n\n👉 **Para ejecutar cualquier swap, necesitas registrarte**",
                "pt": "🔄 Posso ajudá-lo a trocar tokens! Por favor me diga:\n\n• **De:** Qual token trocar\n• **Para:** Qual token receber\n• **Quantidade:** Quanto trocar\n\nExemplo: *trocar 100 USDC para ETH*\n\n👉 **Para executar qualquer swap, você precisa se cadastrar**",
                "zh": "🔄 我可以帮您交换代币！请告诉我：\n\n• **从：** 要交换的代币\n• **到：** 要接收的代币\n• **数量：** 交换多少\n\n示例：*交换 100 USDC 到 ETH*\n\n👉 **执行任何交换都需要注册**",
            },
            ChatIntent.LENDING: {
                "en": "💰 I can show you lending rates! Try asking:\n• 'show Morpho rates'\n• 'deposit USDC to earn yield'\n• 'best lending rates on Ethereum'",
                "es": "💰 ¡Puedo mostrarte tasas de préstamo! Intenta preguntar:\n• 'mostrar tasas de Morpho'\n• 'depositar USDC para ganar rendimiento'\n• 'mejores tasas en Ethereum'",
                "pt": "💰 Posso mostrar taxas de empréstimo! Tente perguntar:\n• 'mostrar taxas do Morpho'\n• 'depositar USDC para ganhar rendimento'\n• 'melhores taxas em Ethereum'",
                "zh": "💰 我可以为您显示借贷利率！尝试询问：\n• '显示 Morpho 利率'\n• '存入 USDC 赚取收益'\n• '以太坊最佳借贷利率'",
            },
            ChatIntent.MONEY_MARKET: {
                "en": "🏦 I can compare money market rates! Try asking:\n• 'compare Aave vs Compound'\n• 'money market rates for USDC'\n• 'best borrow rates'",
                "es": "🏦 ¡Puedo comparar tasas del mercado monetario! Intenta preguntar:\n• 'comparar Aave vs Compound'\n• 'tasas de mercado para USDC'\n• 'mejores tasas de préstamo'",
                "pt": "🏦 Posso comparar taxas do mercado monetário! Tente perguntar:\n• 'comparar Aave vs Compound'\n• 'taxas de mercado para USDC'\n• 'melhores taxas de empréstimo'",
                "zh": "🏦 我可以比较货币市场利率！尝试询问：\n• '比较 Aave 和 Compound'\n• 'USDC 货币市场利率'\n• '最佳借贷利率'",
            },
            ChatIntent.SWAP_MOONPAY: {
                "en": "🌙 **MoonPay Swap**\n\nQuick crypto-to-crypto swap with competitive rates.\n\n⚠️ Service temporarily unavailable. Please try again later.\n\n**Supported Pairs:**\n• BTC ↔ ETH, SOL, USDC\n• ETH ↔ BTC, SOL, USDC\n• SOL ↔ BTC, ETH, USDC\n• USDC ↔ BTC, ETH, SOL",
                "es": "🌙 **Swap MoonPay**\n\nIntercambio rápido cripto-a-cripto con tasas competitivas.\n\n⚠️ Servicio temporalmente no disponible. Por favor intente más tarde.\n\n**Pares Soportados:**\n• BTC ↔ ETH, SOL, USDC\n• ETH ↔ BTC, SOL, USDC\n• SOL ↔ BTC, ETH, USDC\n• USDC ↔ BTC, ETH, SOL",
                "pt": "🌙 **Swap MoonPay**\n\nTroca rápida cripto-a-cripto com taxas competitivas.\n\n⚠️ Serviço temporariamente indisponível. Por favor tente novamente mais tarde.\n\n**Pares Suportados:**\n• BTC ↔ ETH, SOL, USDC\n• ETH ↔ BTC, SOL, USDC\n• SOL ↔ BTC, ETH, USDC\n• USDC ↔ BTC, ETH, SOL",
                "zh": "🌙 **MoonPay交换**\n\n快速加密货币互换，汇率优惠。\n\n⚠️ 服务暂时不可用。请稍后再试。\n\n**支持的交易对:**\n• BTC ↔ ETH, SOL, USDC\n• ETH ↔ BTC, SOL, USDC\n• SOL ↔ BTC, ETH, USDC\n• USDC ↔ BTC, ETH, SOL",
            },
        }

        default = {
            "en": "Service temporarily unavailable. Please try again or sign up for full access.",
            "es": "Servicio no disponible. Intenta de nuevo o regístrate para acceso completo.",
            "pt": "Serviço indisponível. Tente novamente ou cadastre-se para acesso completo.",
            "zh": "服务暂时不可用。请重试或注册以获得完整访问。",
        }

        messages = fallbacks.get(intent, default)
        content = messages.get(language, messages.get("en", ""))

        # Add CTA only for guests
        if not is_authenticated and intent in [
            ChatIntent.SWAP,
            ChatIntent.SWAP_MOONPAY,
            ChatIntent.LENDING,
            ChatIntent.MONEY_MARKET,
        ]:
            content += self._get_auth_cta_message(
                language, for_action=True, is_authenticated=is_authenticated
            )

        return {
            "content": content,
            "enrichment": None,
            "requires_registration": not is_authenticated,
        }

    async def _handle_buy(
        self,
        content: str,
        language: str,
        is_authenticated: bool = False,
        user_id: int | None = None,
        continuation_step: str | None = None,
        previous_buy_info: dict | None = None,
    ) -> dict[str, Any]:
        """
        Handle buy crypto intent with multi-step flow.

        Flow states:
        - buy_awaiting_crypto: Need crypto to buy
        - buy_awaiting_amount: Need USD amount
        - buy_awaiting_confirmation: Show quote, await confirmation
        """
        logger.info(
            f"[Buy] Handler called - language: {language}, authenticated: {is_authenticated}"
        )
        logger.info(f"[Buy] Continuation step: {continuation_step}")
        logger.info(f"[Buy] Previous buy info: {previous_buy_info}")

        # For guests, use multi-step flow
        if not is_authenticated or not user_id:
            if self._buy_multistep:
                try:
                    result = await self._buy_multistep.handle_flow(
                        content=content,
                        language=language,
                        is_authenticated=is_authenticated,
                        continuation_step=continuation_step,
                        previous_buy_info=previous_buy_info,
                    )
                    logger.info(f"[Buy] Multi-step handler returned: {result.keys()}")
                    return result
                except Exception as e:
                    logger.error(f"[Buy] Multi-step handler error: {e}", exc_info=True)
                    # Fall through to fallback

        # For authenticated users with user_id, use BuyHandler
        if self._buy_handler and user_id:
            try:
                result = await self._buy_handler.get_buy_info(
                    user_id=user_id,
                    language=language,
                )
                return {
                    "content": result.content,
                    "enrichment": {
                        "wallet_address": result.wallet_address,
                        "supported_assets": result.supported_assets,
                        "supported_networks": result.supported_networks,
                        "requires_privy_modal": result.requires_privy_modal,
                        "latency_ms": result.latency_ms,
                        "action": "open_fund_wallet",
                    },
                    "requires_registration": False,
                }
            except Exception as e:
                logger.warning(f"BuyHandler error: {e}")
                # Fall through to fallback response

        # Fallback for guests or if BuyHandler not available
        return self._fallback_buy_response(language, is_authenticated)

    def _fallback_buy_response(
        self, language: str, is_authenticated: bool
    ) -> dict[str, Any]:
        """Fallback response when BuyHandler is not available."""
        translations = {
            "en": {
                "title": "💳 **Buy Crypto**",
                "description": "Purchase crypto with card, Apple Pay, or Google Pay via MoonPay/Coinbase.",
                "no_wallet": "⚠️ **No Wallet Found**\n\nPlease connect or create a wallet first to buy crypto.",
            },
            "es": {
                "title": "💳 **Comprar Cripto**",
                "description": "Compra cripto con tarjeta, Apple Pay o Google Pay vía MoonPay/Coinbase.",
                "no_wallet": "⚠️ **No se encontró Wallet**\n\nPor favor conecta o crea una wallet primero para comprar cripto.",
            },
            "pt": {
                "title": "💳 **Comprar Cripto**",
                "description": "Compre cripto com cartão, Apple Pay ou Google Pay via MoonPay/Coinbase.",
                "no_wallet": "⚠️ **Wallet não encontrada**\n\nPor favor conecte ou crie uma wallet primeiro para comprar cripto.",
            },
            "zh": {
                "title": "💳 **购买加密货币**",
                "description": "通过MoonPay/Coinbase使用银行卡、Apple Pay或Google Pay购买加密货币。",
                "no_wallet": "⚠️ **未找到钱包**\n\n请先连接或创建钱包才能购买加密货币。",
            },
        }
        t = translations.get(language, translations["en"])

        content = f"{t['title']}\n\n{t['description']}\n\n"
        if not is_authenticated:
            content += t["no_wallet"] + "\n\n"
            content += self._get_auth_cta_message(
                language, for_action=True, is_authenticated=False
            )

        return {
            "content": content,
            "enrichment": {
                "action": "open_fund_wallet" if is_authenticated else None,
            },
            "requires_registration": not is_authenticated,
        }

    async def _handle_moonpay_swap(
        self,
        content: str,
        language: str,
        is_authenticated: bool = False,
        continuation_step: str | None = None,
        previous_swap_info: dict | None = None,
    ) -> dict[str, Any]:
        """
        Handle MoonPay crypto-to-crypto swap intent with multi-step flow.

        Flow states:
        - swap_awaiting_from_token: Need FROM token
        - swap_awaiting_to_token: Need TO token
        - swap_awaiting_amount: Need amount
        - swap_awaiting_confirmation: Show quote, await confirmation
        - swap_edit: User editing parameters
        """
        logger.info(
            f"[MoonPay Swap] Handler called - language: {language}, authenticated: {is_authenticated}"
        )
        logger.info(f"[MoonPay Swap] Continuation step: {continuation_step}")
        logger.info(f"[MoonPay Swap] Previous swap info: {previous_swap_info}")
        logger.info(
            f"[MoonPay Swap] Multi-step handler available: {self._moonpay_multistep is not None}"
        )
        logger.info(f"[MoonPay Swap] Message content: {content}")

        # Use multi-step flow handler if available
        if self._moonpay_multistep:
            try:
                result = await self._moonpay_multistep.handle_flow(
                    content=content,
                    language=language,
                    is_authenticated=is_authenticated,
                    continuation_step=continuation_step,
                    previous_swap_info=previous_swap_info,
                )
                logger.info(
                    f"[MoonPay Swap] Multi-step handler returned: {result.keys()}"
                )
                return result
            except Exception as e:
                logger.error(
                    f"[MoonPay Swap] Multi-step handler error: {e}", exc_info=True
                )
                # Fall through to fallback

        # Fallback: original single-step handler
        if self._moonpay_swap_handler:
            try:
                # Parse tokens from content
                content_lower = content.lower()

                # MoonPay supported tokens
                moonpay_tokens = {
                    "btc": "btc",
                    "bitcoin": "btc",
                    "eth": "eth",
                    "ethereum": "eth",
                    "ether": "eth",
                    "sol": "sol",
                    "solana": "sol",
                    "usdc": "usdc",
                }

                # Extract from_token and to_token
                from_token = None
                to_token = None
                amount = "1"  # Default amount

                # Pattern 1: swap/exchange/convert [AMOUNT] TOKEN1 to/for TOKEN2
                # Pattern 2: TOKEN1 to/for TOKEN2 AMOUNT  (implicit swap)
                # Pattern 3: AMOUNT TOKEN1 to/for TOKEN2  (implicit swap)
                import re

                # Try explicit swap pattern first: "swap 100 BTC to ETH"
                swap_pattern = re.compile(
                    r"(?:swap|exchange|convert|trade)\s+(?:(\d+\.?\d*)\s+)?(\w+)\s+(?:to|for|into)\s+(\w+)",
                    re.IGNORECASE,
                )
                match = swap_pattern.search(content)

                if match:
                    if match.group(1):  # Amount specified
                        amount = match.group(1)
                    token1 = match.group(2).lower()
                    token2 = match.group(3).lower()

                    # Map to MoonPay tokens
                    from_token = moonpay_tokens.get(token1)
                    to_token = moonpay_tokens.get(token2)

                # Try implicit patterns: "USDC to eth 1" or "1 BTC to SOL"
                if not from_token or not to_token:
                    # Pattern: TOKEN1 to TOKEN2 AMOUNT or AMOUNT TOKEN1 to TOKEN2
                    implicit_pattern = re.compile(
                        r"(?:(\d+\.?\d*)\s+)?(\w+)\s+(?:to|for|into)\s+(\w+)(?:\s+(\d+\.?\d*))?",
                        re.IGNORECASE,
                    )
                    match = implicit_pattern.search(content)

                    if match:
                        # Check if amount is at beginning or end
                        amount_start = match.group(1)
                        token1 = match.group(2).lower()
                        token2 = match.group(3).lower()
                        amount_end = match.group(4)

                        # Use whichever amount is present
                        if amount_start:
                            amount = amount_start
                        elif amount_end:
                            amount = amount_end

                        # Map to MoonPay tokens
                        from_token = moonpay_tokens.get(token1)
                        to_token = moonpay_tokens.get(token2)

                if from_token and to_token:
                    logger.info(
                        f"[MoonPay Swap] Parsed: from={from_token}, to={to_token}, amount={amount}"
                    )

                # If both tokens are specified, get quote
                if from_token and to_token:
                    logger.info(
                        f"[MoonPay Swap] Getting quote for {from_token} → {to_token}, amount={amount}"
                    )
                    result = await self._moonpay_swap_handler.get_swap_quote(
                        from_currency=from_token,
                        to_currency=to_token,
                        amount=amount,
                        language=language,
                    )
                    logger.info(f"[MoonPay Swap] Quote returned successfully")
                else:
                    # Show available pairs if tokens not specified
                    logger.info(
                        f"[MoonPay Swap] Tokens not fully specified, showing available pairs"
                    )
                    result = await self._moonpay_swap_handler.get_available_pairs(
                        language=language
                    )

                logger.info(
                    f"[MoonPay Swap] Handler returned successfully - action: {result.action}"
                )
                return {
                    "content": result.content,
                    "enrichment": {
                        "pairs": result.pairs,
                        "quote": result.quote,
                        "latency_ms": result.latency_ms,
                        "action": result.action,
                        "handler": result.handler,
                    },
                    "requires_registration": not is_authenticated,
                }
            except Exception as e:
                logger.error(f"[MoonPay Swap] Handler error: {e}", exc_info=True)
                # Fall through to fallback response
        else:
            logger.warning(
                "[MoonPay Swap] Handler not available - using fallback response"
            )

        # Fallback for guests or if MoonPaySwapHandler not available
        return self._fallback_moonpay_swap_response(language, is_authenticated)

    async def _handle_send(
        self,
        content: str,
        language: str,
        is_authenticated: bool = False,
        continuation_step: str | None = None,
        previous_send_info: dict | None = None,
    ) -> dict[str, Any]:
        """
        Handle send tokens intent with multi-step flow.

        Flow states:
        - send_awaiting_token: Need token to send
        - send_awaiting_amount: Need amount to send
        - send_awaiting_address: Need destination address
        - send_awaiting_confirmation: Show review, await confirmation
        - send_edit: User editing parameters
        """
        logger.info(
            f"[Send] Handler called - language: {language}, authenticated: {is_authenticated}"
        )
        logger.info(f"[Send] Continuation step: {continuation_step}")
        logger.info(f"[Send] Previous send info: {previous_send_info}")
        logger.info(f"[Send] Message content: {content}")

        # Use multi-step flow handler if available
        if self._send_multistep:
            try:
                result = await self._send_multistep.handle_flow(
                    content=content,
                    language=language,
                    is_authenticated=is_authenticated,
                    continuation_step=continuation_step,
                    previous_send_info=previous_send_info,
                )
                logger.info(f"[Send] Multi-step handler returned: {result.keys()}")
                return result
            except Exception as e:
                logger.error(f"[Send] Multi-step handler error: {e}", exc_info=True)
                # Fall through to fallback

        # Fallback response
        return self._fallback_send_response(language, is_authenticated)

    def _fallback_send_response(
        self, language: str, is_authenticated: bool
    ) -> dict[str, Any]:
        """Fallback response when send handler is not available."""
        translations = {
            "en": {
                "title": "📤 **Send Crypto**",
                "description": "Send crypto to any wallet address",
                "unavailable": "⚠️ **Send Feature**\n\nSend feature requires you to be signed in with a wallet.",
                "cta": "Sign up to send crypto securely.",
            },
            "es": {
                "title": "📤 **Enviar Cripto**",
                "description": "Envía cripto a cualquier dirección de wallet",
                "unavailable": "⚠️ **Función de Envío**\n\nLa función de envío requiere que inicies sesión con una wallet.",
                "cta": "Regístrate para enviar cripto de forma segura.",
            },
            "pt": {
                "title": "📤 **Enviar Cripto**",
                "description": "Envie cripto para qualquer endereço de carteira",
                "unavailable": "⚠️ **Recurso de Envio**\n\nO recurso de envio requer que você faça login com uma carteira.",
                "cta": "Cadastre-se para enviar cripto com segurança.",
            },
            "zh": {
                "title": "📤 **发送加密货币**",
                "description": "向任何钱包地址发送加密货币",
                "unavailable": "⚠️ **发送功能**\n\n发送功能需要您使用钱包登录。",
                "cta": "注册以安全发送加密货币。",
            },
            "fr": {
                "title": "📤 **Envoyer Crypto**",
                "description": "Envoyez de la crypto vers n'importe quelle adresse de portefeuille",
                "unavailable": "⚠️ **Fonction d'Envoi**\n\nLa fonction d'envoi nécessite que vous soyez connecté avec un portefeuille.",
                "cta": "Inscrivez-vous pour envoyer de la crypto en toute sécurité.",
            },
        }
        t = translations.get(language, translations["en"])

        content = f"{t['title']}\n\n{t['description']}\n\n{t['unavailable']}\n\n"
        if not is_authenticated:
            content += f"👉 **{t['cta']}**\n"

        return {
            "content": content,
            "enrichment": {},
            "requires_registration": not is_authenticated,
        }

    async def _handle_balance(
        self,
        content: str,
        language: str,
        is_authenticated: bool = False,
        wallet_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Handle balance inquiry with enhanced storytelling.

        For guests: Show sample balances with signup CTA
        For authenticated: Show real wallet balances
        """
        logger.info(
            f"[Balance] Handler called - language: {language}, authenticated: {is_authenticated}, wallet: {wallet_address[:10] if wallet_address else 'None'}..."
        )

        translations = {
            "en": {
                "title": "💰 **Your Crypto Balance**",
                "greeting": "Let me show you your crypto holdings!\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "guest_note": "🎮 **Demo Mode** - Example balances shown below\n\n",
                "total_label": "📊 **Total Portfolio Value:**",
                "balances_label": "**Token Balances:**",
                "zero_balance": "💭 Your wallet is empty. Time to start your crypto journey!\n\n",
                "cta_title": "**Get Started**",
                "cta_body": "Sign up to connect your wallet and see your real balances.",
                "learn_more": "💡 *With Anvil, you can track balances across multiple chains and protocols.*",
                "loading_error": "⚠️ Unable to fetch your balance at this time. Please try again.",
            },
            "es": {
                "title": "💰 **Tu Saldo de Cripto**",
                "greeting": "¡Déjame mostrarte tus tenencias de cripto!\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "guest_note": "🎮 **Modo Demo** - Saldos de ejemplo mostrados abajo\n\n",
                "total_label": "📊 **Valor Total del Portafolio:**",
                "balances_label": "**Saldos de Tokens:**",
                "zero_balance": "💭 Tu wallet está vacía. ¡Hora de comenzar tu viaje cripto!\n\n",
                "cta_title": "**Comienza**",
                "cta_body": "Regístrate para conectar tu wallet y ver tus saldos reales.",
                "learn_more": "💡 *Con Anvil, puedes seguir saldos a través de múltiples cadenas y protocolos.*",
            },
            "pt": {
                "title": "💰 **Seu Saldo de Cripto**",
                "greeting": "Deixe-me mostrar suas posses de cripto!\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "guest_note": "🎮 **Modo Demo** - Saldos de exemplo mostrados abaixo\n\n",
                "total_label": "📊 **Valor Total do Portfólio:**",
                "balances_label": "**Saldos de Tokens:**",
                "zero_balance": "💭 Sua carteira está vazia. Hora de começar sua jornada cripto!\n\n",
                "cta_title": "**Comece**",
                "cta_body": "Cadastre-se para conectar sua carteira e ver seus saldos reais.",
                "learn_more": "💡 *Com Anvil, você pode rastrear saldos em várias chains e protocolos.*",
            },
            "zh": {
                "title": "💰 **您的加密货币余额**",
                "greeting": "让我向您展示您的加密货币持仓!\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "guest_note": "🎮 **演示模式** - 以下显示示例余额\n\n",
                "total_label": "📊 **投资组合总价值:**",
                "balances_label": "**代币余额:**",
                "zero_balance": "💭 您的钱包是空的。是时候开始您的加密货币之旅了!\n\n",
                "cta_title": "**开始**",
                "cta_body": "注册以连接您的钱包并查看您的真实余额。",
                "learn_more": "💡 *使用Anvil，您可以跨多个链和协议跟踪余额。*",
            },
            "fr": {
                "title": "💰 **Votre Solde Crypto**",
                "greeting": "Laissez-moi vous montrer vos avoirs en crypto!\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "guest_note": "🎮 **Mode Démo** - Soldes d'exemple affichés ci-dessous\n\n",
                "total_label": "📊 **Valeur Totale du Portefeuille:**",
                "balances_label": "**Soldes de Tokens:**",
                "zero_balance": "💭 Votre portefeuille est vide. Il est temps de commencer votre voyage crypto!\n\n",
                "cta_title": "**Commencer**",
                "cta_body": "Inscrivez-vous pour connecter votre portefeuille et voir vos soldes réels.",
                "learn_more": "💡 *Avec Anvil, vous pouvez suivre les soldes sur plusieurs chaînes et protocoles.*",
            },
        }
        t = translations.get(language, translations["en"])

        # Try to fetch real balances for authenticated users with wallet
        if is_authenticated and wallet_address and self._portfolio_service:
            try:
                from app.domain.enums.chain_type import ChainType

                logger.info(
                    f"[Balance] Fetching real portfolio for wallet: {wallet_address[:10]}..."
                )
                portfolio = await self._portfolio_service.get_portfolio_by_address(
                    address=wallet_address,
                    chain=ChainType.BASE,  # Default to Base chain
                )

                logger.info(
                    f"[Balance] Portfolio result: {portfolio is not None}, has_value: {portfolio.has_value if portfolio else 'N/A'}, total_usd: {portfolio.total_usd if portfolio else 'N/A'}"
                )

                if portfolio:
                    # Build real balances list (even if empty for authenticated users)
                    real_balances = []

                    # Add native token (ETH) if has balance
                    if portfolio.native_balance > 0:
                        token_emoji = {"ETH": "Ξ", "WETH": "Ξ"}.get(
                            portfolio.native_symbol, "🪙"
                        )
                        real_balances.append({
                            "token": portfolio.native_symbol,
                            "amount": f"{portfolio.native_balance:.4f}",
                            "value_usd": f"${portfolio.native_usd_value:.2f}"
                            if portfolio.native_usd_value
                            else "N/A",
                            "emoji": token_emoji,
                        })

                    # Add ERC-20 tokens
                    for token in portfolio.tokens:
                        token_emoji = {
                            "USDC": "💵",
                            "USDT": "💵",
                            "DAI": "💵",
                            "WETH": "Ξ",
                            "WBTC": "₿",
                            "ETH": "Ξ",
                            "BTC": "₿",
                        }.get(token.get("symbol", ""), "🪙")

                        real_balances.append({
                            "token": token.get("symbol", "Unknown"),
                            "amount": f"{token.get('amount', 0):.4f}",
                            "value_usd": f"${token.get('usd_value', 0):.2f}"
                            if token.get("usd_value")
                            else "N/A",
                            "emoji": token_emoji,
                        })

                    # Build response with real data
                    content = f"{t['title']}\n\n{t['greeting']}{t['divider']}"
                    content += f"{t['total_label']} **${portfolio.total_usd:.2f}**\n\n"
                    content += f"{t['balances_label']}\n"

                    if real_balances:
                        for balance in real_balances:
                            content += f"• {balance['emoji']} **{balance['token']}**: {balance['amount']} (~{balance['value_usd']})\n"
                    else:
                        content += f"{t['zero_balance']}"

                    content += f"\n{t['divider']}"
                    content += t["learn_more"]

                    logger.info(
                        f"[Balance] Successfully fetched real portfolio - Total: ${portfolio.total_usd:.2f}"
                    )
                    return {
                        "content": content,
                        "enrichment": {
                            "balances": real_balances,
                            "total_value": f"${portfolio.total_usd:.2f}",
                            "chain": portfolio.chain,
                            "wallet_address": portfolio.wallet_address,
                        },
                        "requires_registration": False,
                    }

            except Exception as e:
                logger.error(
                    f"[Balance] Error fetching real portfolio: {e}", exc_info=True
                )
                # Fall through to demo data for guests, but show wallet not connected for authenticated users

        # For authenticated users without wallet data, show wallet connection message
        if is_authenticated:
            content = f"{t['title']}\n\n{t['greeting']}{t['divider']}"
            content += "💼 **No Wallet Connected**\n\n"
            content += "To view your crypto balance, please connect your wallet through your account settings.\n\n"
            content += f"{t['divider']}"
            content += "💡 *Once connected, you'll see your real-time balances across all supported chains.*"

            return {
                "content": content,
                "enrichment": {
                    "balances": [],
                    "total_value": "$0.00",
                },
                "requires_registration": False,
            }

        # Demo balances for guests only
        demo_balances = [
            {
                "token": "USDC",
                "amount": "1,250.00",
                "value_usd": "$1,250.00",
                "emoji": "💵",
            },
            {"token": "ETH", "amount": "0.5", "value_usd": "$975.00", "emoji": "Ξ"},
            {"token": "BTC", "amount": "0.01", "value_usd": "$450.00", "emoji": "₿"},
            {"token": "SOL", "amount": "10.0", "value_usd": "$325.00", "emoji": "◎"},
        ]
        total_value = "$3,000.00"

        # Build response for guests
        content = f"{t['title']}\n\n{t['greeting']}{t['divider']}"
        content += f"{t['guest_note']}"
        content += f"{t['total_label']} **{total_value}**\n\n"
        content += f"{t['balances_label']}\n"

        for balance in demo_balances:
            content += f"• {balance['emoji']} **{balance['token']}**: {balance['amount']} (~{balance['value_usd']})\n"

        content += f"\n{t['divider']}"
        content += f"{t['cta_title']}\n\n{t['cta_body']}\n\n👉 **Sign Up Now**\n\n"
        content += t["learn_more"]

        return {
            "content": content,
            "enrichment": {
                "balances": demo_balances,
                "total_value": total_value,
            },
            "requires_registration": True,
        }

    async def _handle_receive(
        self,
        content: str,
        language: str,
        is_authenticated: bool = False,
        wallet_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Handle receive/deposit inquiry with enhanced storytelling.

        For guests: Show sample addresses with signup CTA
        For authenticated: Show real wallet addresses
        """
        logger.info(
            f"[Receive] Handler called - language: {language}, authenticated: {is_authenticated}, wallet: {wallet_address[:10] if wallet_address else 'None'}..."
        )

        translations = {
            "en": {
                "title": "📥 **Receive Crypto**",
                "greeting": "Ready to receive crypto? Here's how!\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "guest_note": "🎮 **Demo Mode** - Sample addresses shown below\n\n",
                "instructions": "**How to Receive:**\n\n1️⃣ Share your wallet address with the sender\n2️⃣ Wait for the transaction to confirm\n3️⃣ Funds will appear in your balance\n\n",
                "addresses_label": "**Your Wallet Addresses:**",
                "ethereum": "🔷 **Ethereum (ETH, USDC, DAI):**",
                "bitcoin": "₿ **Bitcoin (BTC):**",
                "solana": "◎ **Solana (SOL, USDC):**",
                "demo_eth": "`0x1234...5678` (example)",
                "demo_btc": "`bc1q1234...5678` (example)",
                "demo_sol": "`A1B2C3...XYZ` (example)",
                "warning": "⚠️ **Important:** Always verify the network before sending crypto!",
                "cta_title": "**Get Your Real Addresses**",
                "cta_body": "Sign up to get your actual wallet addresses and receive crypto securely.",
            },
            "es": {
                "title": "📥 **Recibir Cripto**",
                "greeting": "¿Listo para recibir cripto? ¡Así es como!\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "guest_note": "🎮 **Modo Demo** - Direcciones de ejemplo mostradas abajo\n\n",
                "instructions": "**Cómo Recibir:**\n\n1️⃣ Comparte tu dirección de wallet con el remitente\n2️⃣ Espera a que la transacción se confirme\n3️⃣ Los fondos aparecerán en tu saldo\n\n",
                "addresses_label": "**Tus Direcciones de Wallet:**",
                "ethereum": "🔷 **Ethereum (ETH, USDC, DAI):**",
                "bitcoin": "₿ **Bitcoin (BTC):**",
                "solana": "◎ **Solana (SOL, USDC):**",
                "demo_eth": "`0x1234...5678` (ejemplo)",
                "demo_btc": "`bc1q1234...5678` (ejemplo)",
                "demo_sol": "`A1B2C3...XYZ` (ejemplo)",
                "warning": "⚠️ **Importante:** ¡Siempre verifica la red antes de enviar cripto!",
                "cta_title": "**Obtén Tus Direcciones Reales**",
                "cta_body": "Regístrate para obtener tus direcciones de wallet reales y recibir cripto de forma segura.",
            },
            "pt": {
                "title": "📥 **Receber Cripto**",
                "greeting": "Pronto para receber cripto? Veja como!\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "guest_note": "🎮 **Modo Demo** - Endereços de exemplo mostrados abaixo\n\n",
                "instructions": "**Como Receber:**\n\n1️⃣ Compartilhe seu endereço de carteira com o remetente\n2️⃣ Aguarde a confirmação da transação\n3️⃣ Os fundos aparecerão no seu saldo\n\n",
                "addresses_label": "**Seus Endereços de Carteira:**",
                "ethereum": "🔷 **Ethereum (ETH, USDC, DAI):**",
                "bitcoin": "₿ **Bitcoin (BTC):**",
                "solana": "◎ **Solana (SOL, USDC):**",
                "demo_eth": "`0x1234...5678` (exemplo)",
                "demo_btc": "`bc1q1234...5678` (exemplo)",
                "demo_sol": "`A1B2C3...XYZ` (exemplo)",
                "warning": "⚠️ **Importante:** Sempre verifique a rede antes de enviar cripto!",
                "cta_title": "**Obtenha Seus Endereços Reais**",
                "cta_body": "Cadastre-se para obter seus endereços de carteira reais e receber cripto com segurança.",
            },
            "zh": {
                "title": "📥 **接收加密货币**",
                "greeting": "准备接收加密货币？方法如下！\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "guest_note": "🎮 **演示模式** - 以下显示示例地址\n\n",
                "instructions": "**如何接收:**\n\n1️⃣ 与发送方分享您的钱包地址\n2️⃣ 等待交易确认\n3️⃣ 资金将显示在您的余额中\n\n",
                "addresses_label": "**您的钱包地址:**",
                "ethereum": "🔷 **以太坊 (ETH, USDC, DAI):**",
                "bitcoin": "₿ **比特币 (BTC):**",
                "solana": "◎ **Solana (SOL, USDC):**",
                "demo_eth": "`0x1234...5678` (示例)",
                "demo_btc": "`bc1q1234...5678` (示例)",
                "demo_sol": "`A1B2C3...XYZ` (示例)",
                "warning": "⚠️ **重要提示:** 发送加密货币前务必验证网络！",
                "cta_title": "**获取您的真实地址**",
                "cta_body": "注册以获取您的实际钱包地址并安全接收加密货币。",
            },
            "fr": {
                "title": "📥 **Recevoir Crypto**",
                "greeting": "Prêt à recevoir de la crypto? Voici comment!\n\n",
                "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n",
                "guest_note": "🎮 **Mode Démo** - Adresses d'exemple affichées ci-dessous\n\n",
                "instructions": "**Comment Recevoir:**\n\n1️⃣ Partagez votre adresse de portefeuille avec l'expéditeur\n2️⃣ Attendez la confirmation de la transaction\n3️⃣ Les fonds apparaîtront dans votre solde\n\n",
                "addresses_label": "**Vos Adresses de Portefeuille:**",
                "ethereum": "🔷 **Ethereum (ETH, USDC, DAI):**",
                "bitcoin": "₿ **Bitcoin (BTC):**",
                "solana": "◎ **Solana (SOL, USDC):**",
                "demo_eth": "`0x1234...5678` (exemple)",
                "demo_btc": "`bc1q1234...5678` (exemple)",
                "demo_sol": "`A1B2C3...XYZ` (exemple)",
                "warning": "⚠️ **Important:** Vérifiez toujours le réseau avant d'envoyer de la crypto!",
                "cta_title": "**Obtenez Vos Adresses Réelles**",
                "cta_body": "Inscrivez-vous pour obtenir vos adresses de portefeuille réelles et recevoir de la crypto en toute sécurité.",
            },
        }
        t = translations.get(language, translations["en"])

        # Build response
        content = f"{t['title']}\n\n{t['greeting']}{t['divider']}"

        if not is_authenticated:
            content += f"{t['guest_note']}"

        content += f"{t['instructions']}{t['addresses_label']}\n\n"

        # Show real or demo addresses based on authentication
        if is_authenticated and wallet_address:
            # Show real wallet address for authenticated users
            content += f"{t['ethereum']}\n`{wallet_address}`\n\n"
            content += f"💡 **Note:** This is your EVM-compatible address (works for Ethereum, Base, Polygon, etc.)\n\n"
            logger.info(
                f"[Receive] Showing real wallet address: {wallet_address[:10]}..."
            )
        else:
            # Show demo addresses for guests
            content += f"{t['ethereum']}\n{t['demo_eth']}\n\n"
            content += f"{t['bitcoin']}\n{t['demo_btc']}\n\n"
            content += f"{t['solana']}\n{t['demo_sol']}\n\n"

        content += f"{t['divider']}{t['warning']}\n\n"

        if not is_authenticated:
            content += f"{t['cta_title']}\n\n{t['cta_body']}\n\n👉 **Sign Up Now**\n"

        return {
            "content": content,
            "enrichment": {
                "addresses": {
                    "ethereum": wallet_address
                    if is_authenticated and wallet_address
                    else ("0x1234...5678" if not is_authenticated else None),
                    "bitcoin": "bc1q1234...5678" if not is_authenticated else None,
                    "solana": "A1B2C3...XYZ" if not is_authenticated else None,
                }
            },
            "requires_registration": not is_authenticated,
        }

    def _fallback_moonpay_swap_response(
        self, language: str, is_authenticated: bool
    ) -> dict[str, Any]:
        """Fallback response when MoonPaySwapHandler is not available."""
        translations = {
            "en": {
                "title": "🌙 **MoonPay Swap**",
                "description": "Quick crypto-to-crypto swap with competitive rates",
                "unavailable": "⚠️ **Service Temporarily Unavailable**\n\nMoonPay swap service is currently unavailable. Please try again later.",
            },
            "es": {
                "title": "🌙 **Swap MoonPay**",
                "description": "Intercambio rápido cripto-a-cripto con tasas competitivas",
                "unavailable": "⚠️ **Servicio Temporalmente No Disponible**\n\nEl servicio de swap MoonPay no está disponible actualmente. Por favor intente más tarde.",
            },
            "pt": {
                "title": "🌙 **Swap MoonPay**",
                "description": "Troca rápida cripto-a-cripto com taxas competitivas",
                "unavailable": "⚠️ **Serviço Temporariamente Indisponível**\n\nO serviço de swap MoonPay está temporariamente indisponível. Por favor tente novamente mais tarde.",
            },
            "zh": {
                "title": "🌙 **MoonPay交换**",
                "description": "快速加密货币互换，汇率优惠",
                "unavailable": "⚠️ **服务暂时不可用**\n\nMoonPay交换服务当前不可用。请稍后再试。",
            },
            "fr": {
                "title": "🌙 **Swap MoonPay**",
                "description": "Échange rapide crypto-à-crypto avec taux compétitifs",
                "unavailable": "⚠️ **Service Temporairement Indisponible**\n\nLe service de swap MoonPay est temporairement indisponible. Veuillez réessayer plus tard.",
            },
        }
        t = translations.get(language, translations["en"])

        content = f"{t['title']}\n\n{t['description']}\n\n{t['unavailable']}\n\n"
        if not is_authenticated:
            content += self._get_auth_cta_message(
                language, for_action=True, is_authenticated=False
            )

        return {
            "content": content,
            "enrichment": {
                "action": "open_swap_modal" if is_authenticated else None,
            },
            "requires_registration": not is_authenticated,
        }

    async def _build_real_portfolio_response(
        self, portfolio, language: str
    ) -> dict[str, Any]:
        """Build real portfolio response from on-chain data."""
        messages = {
            "en": {
                "title": "💼 Your Portfolio",
                "total_value": "Total Portfolio Value",
                "holdings_title": "Holdings",
                "empty_portfolio": "Your portfolio is empty. Time to start investing!",
                "learn_more": "💡 *Track your portfolio in real-time across multiple chains and protocols.*",
                "assets": "assets",
            },
            "es": {
                "title": "💼 Tu Portafolio",
                "total_value": "Valor Total del Portafolio",
                "holdings_title": "Holdings",
                "empty_portfolio": "Tu portafolio está vacío. ¡Es hora de comenzar a invertir!",
                "learn_more": "💡 *Rastrea tu portafolio en tiempo real en múltiples cadenas y protocolos.*",
                "assets": "activos",
            },
            "pt": {
                "title": "💼 Seu Portfólio",
                "total_value": "Valor Total do Portfólio",
                "holdings_title": "Holdings",
                "empty_portfolio": "Seu portfólio está vazio. Hora de começar a investir!",
                "learn_more": "💡 *Rastreie seu portfólio em tempo real em várias chains e protocolos.*",
                "assets": "ativos",
            },
            "zh": {
                "title": "💼 您的投资组合",
                "total_value": "投资组合总价值",
                "holdings_title": "持仓",
                "empty_portfolio": "您的投资组合是空的。是时候开始投资了！",
                "learn_more": "💡 *跨多个链和协议实时追踪您的投资组合。*",
                "assets": "资产",
            },
            "fr": {
                "title": "💼 Votre Portefeuille",
                "total_value": "Valeur Totale du Portefeuille",
                "holdings_title": "Holdings",
                "empty_portfolio": "Votre portefeuille est vide. Il est temps de commencer à investir!",
                "learn_more": "💡 *Suivez votre portefeuille en temps réel sur plusieurs chaînes et protocoles.*",
                "assets": "actifs",
            },
        }
        msg = messages.get(language, messages["en"])

        # Build real holdings list
        real_holdings = []

        # Add native token (ETH) if has balance
        if portfolio.native_balance > 0:
            token_emoji = {"ETH": "Ξ", "WETH": "Ξ"}.get(portfolio.native_symbol, "🪙")
            allocation_pct = (
                (portfolio.native_usd_value / portfolio.total_usd * 100)
                if portfolio.total_usd > 0
                else 0
            )
            real_holdings.append({
                "token": portfolio.native_symbol,
                "symbol": portfolio.native_symbol,
                "amount": portfolio.native_balance,
                "value_usd": portfolio.native_usd_value,
                "emoji": token_emoji,
                "allocation_pct": allocation_pct,
            })

        # Add ERC-20 tokens
        for token in portfolio.tokens:
            token_symbol = token.get("symbol", "Unknown")
            token_emoji = {
                "USDC": "💵",
                "USDT": "💵",
                "DAI": "💵",
                "WETH": "Ξ",
                "WBTC": "₿",
                "ETH": "Ξ",
                "BTC": "₿",
            }.get(token_symbol, "🪙")

            token_value = token.get("usd_value", 0)
            allocation_pct = (
                (token_value / portfolio.total_usd * 100)
                if portfolio.total_usd > 0
                else 0
            )

            real_holdings.append({
                "token": token.get("name", token_symbol),
                "symbol": token_symbol,
                "amount": token.get("amount", 0),
                "value_usd": token_value,
                "emoji": token_emoji,
                "allocation_pct": allocation_pct,
            })

        # Build holdings text
        holdings_text = ""
        if real_holdings:
            for holding in real_holdings:
                holdings_text += f"""
{holding["emoji"]} **{holding["token"]} ({holding["symbol"]})**
   • Amount: {holding["amount"]:,.4f} {holding["symbol"]}
   • Value: ${holding["value_usd"]:,.2f}
   • Allocation: {holding["allocation_pct"]:.1f}%
"""

        # Build content
        divider = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        content = f"""{divider}{msg["title"]}
{divider}
**📊 {msg["total_value"]}**
{divider}

💰 **${portfolio.total_usd:,.2f}**

{divider}**💎 {msg["holdings_title"]}** ({len(real_holdings)} {msg["assets"]})
{divider}"""

        if real_holdings:
            content += holdings_text
        else:
            content += f"\n{msg['empty_portfolio']}\n"

        content += f"\n{divider}\n{msg['learn_more']}"

        logger.info(
            f"[Portfolio] Successfully fetched real portfolio - Total: ${portfolio.total_usd:.2f}, Holdings: {len(real_holdings)}"
        )

        return {
            "content": content,
            "enrichment": {
                "portfolio": {
                    "total_value_usd": portfolio.total_usd,
                    "holdings_count": len(real_holdings),
                    "chain": portfolio.chain,
                    "wallet_address": portfolio.wallet_address,
                },
                "balances": [
                    {
                        "token": h["symbol"],
                        "amount": h["amount"],
                        "value_usd": h["value_usd"],
                    }
                    for h in real_holdings
                ],
                "total_value": portfolio.total_usd,
            },
            "requires_registration": False,
        }

    async def _handle_portfolio(
        self,
        content: str,
        language: str,
        is_authenticated: bool = False,
        wallet_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Handle portfolio inquiry.

        For guests: Show demo portfolio with sample holdings
        For authenticated: Show real on-chain portfolio with actual holdings
        """
        logger.info(
            f"[Portfolio] Handler called - language: {language}, authenticated: {is_authenticated}, wallet: {wallet_address[:10] if wallet_address else 'None'}..."
        )

        # Try to fetch real portfolio for authenticated users with wallet
        if is_authenticated and wallet_address and self._portfolio_service:
            try:
                from app.domain.enums.chain_type import ChainType

                logger.info(
                    f"[Portfolio] Fetching real portfolio for wallet: {wallet_address[:10]}..."
                )
                portfolio = await self._portfolio_service.get_portfolio_by_address(
                    address=wallet_address,
                    chain=ChainType.BASE,  # Default to Base chain
                )

                logger.info(
                    f"[Portfolio] Portfolio result: {portfolio is not None}, has_value: {portfolio.has_value if portfolio else 'N/A'}, total_usd: {portfolio.total_usd if portfolio else 'N/A'}"
                )

                if portfolio:
                    # Build real portfolio response
                    return await self._build_real_portfolio_response(
                        portfolio, language
                    )

            except Exception as e:
                logger.error(
                    f"[Portfolio] Error fetching real portfolio: {e}", exc_info=True
                )
                # Fall through to demo data for guests, but show wallet not connected for authenticated users

        # For authenticated users without wallet data, show wallet connection message
        if is_authenticated:
            messages = {
                "en": {
                    "title": "📊 Portfolio Overview",
                    "greeting": "**Your Crypto Portfolio**\n\n",
                    "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
                    "no_wallet": "💼 **No Wallet Connected**\n\n"
                    "To view your crypto portfolio, please connect your wallet through your account settings.\n\n",
                    "hint": "💡 *Once connected, you'll see your complete portfolio with real-time values across all supported chains.*",
                },
                "es": {
                    "title": "📊 Resumen de Cartera",
                    "greeting": "**Tu Cartera de Criptomonedas**\n\n",
                    "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
                    "no_wallet": "💼 **Sin Cartera Conectada**\n\n"
                    "Para ver tu cartera de criptomonedas, conecta tu cartera en la configuración de tu cuenta.\n\n",
                    "hint": "💡 *Una vez conectada, verás tu cartera completa con valores en tiempo real en todas las cadenas compatibles.*",
                },
                "pt": {
                    "title": "📊 Visão Geral da Carteira",
                    "greeting": "**Sua Carteira de Criptomoedas**\n\n",
                    "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
                    "no_wallet": "💼 **Nenhuma Carteira Conectada**\n\n"
                    "Para visualizar sua carteira de criptomoedas, conecte sua carteira nas configurações da sua conta.\n\n",
                    "hint": "💡 *Uma vez conectada, você verá sua carteira completa com valores em tempo real em todas as cadeias suportadas.*",
                },
                "zh": {
                    "title": "📊 投资组合概览",
                    "greeting": "**您的加密货币投资组合**\n\n",
                    "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
                    "no_wallet": "💼 **未连接钱包**\n\n"
                    "要查看您的加密货币投资组合，请通过帐户设置连接您的钱包。\n\n",
                    "hint": "💡 *连接后，您将看到所有支持链上的完整投资组合及实时价值。*",
                },
                "fr": {
                    "title": "📊 Aperçu du Portefeuille",
                    "greeting": "**Votre Portefeuille Crypto**\n\n",
                    "divider": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
                    "no_wallet": "💼 **Aucun Portefeuille Connecté**\n\n"
                    "Pour voir votre portefeuille crypto, connectez votre portefeuille dans les paramètres de votre compte.\n\n",
                    "hint": "💡 *Une fois connecté, vous verrez votre portefeuille complet avec des valeurs en temps réel sur toutes les chaînes prises en charge.*",
                },
            }
            t = messages.get(language, messages["en"])

            content = f"{t['title']}\n\n{t['greeting']}{t['divider']}"
            content += t["no_wallet"]
            content += f"{t['divider']}"
            content += t["hint"]

            return {
                "content": content,
                "enrichment": {
                    "portfolio": [],
                    "total_value": "$0.00",
                },
                "requires_registration": False,
            }

        # For guests, show demo portfolio
        return await self._portfolio_multistep.handle_flow(
            content=content,
            language=language,
            is_authenticated=is_authenticated,
        )

    async def _build_real_activity_response(
        self, language: str, wallet_address: str | None
    ) -> dict[str, Any]:
        """Build real activity response (empty or from blockchain scan)."""
        messages = {
            "en": {
                "title": "📜 Transaction History",
                "empty_title": "No Transactions Found",
                "empty_message": "Your wallet doesn't have any recorded transactions yet.",
                "explanation": "Transaction history shows:\n• Transfers (send/receive)\n• Token swaps\n• Smart contract interactions\n• DeFi protocol activity",
                "coming_soon": "💡 **Enhanced Transaction History Coming Soon**\n\nWe're adding blockchain scanning to show your complete on-chain activity across all protocols and DEXs.",
                "wallet_label": "Wallet",
            },
            "es": {
                "title": "📜 Historial de Transacciones",
                "empty_title": "No se Encontraron Transacciones",
                "empty_message": "Tu billetera aún no tiene transacciones registradas.",
                "explanation": "El historial de transacciones muestra:\n• Transferencias (enviar/recibir)\n• Intercambios de tokens\n• Interacciones con contratos inteligentes\n• Actividad de protocolos DeFi",
                "coming_soon": "💡 **Historial de Transacciones Mejorado Próximamente**\n\nEstamos agregando escaneo de blockchain para mostrar tu actividad completa en cadena en todos los protocolos y DEXs.",
                "wallet_label": "Billetera",
            },
            "pt": {
                "title": "📜 Histórico de Transações",
                "empty_title": "Nenhuma Transação Encontrada",
                "empty_message": "Sua carteira ainda não possui transações registradas.",
                "explanation": "O histórico de transações mostra:\n• Transferências (enviar/receber)\n• Trocas de tokens\n• Interações com contratos inteligentes\n• Atividade de protocolos DeFi",
                "coming_soon": "💡 **Histórico de Transações Aprimorado em Breve**\n\nEstamos adicionando varredura de blockchain para mostrar sua atividade completa na cadeia em todos os protocolos e DEXs.",
                "wallet_label": "Carteira",
            },
            "zh": {
                "title": "📜 交易历史",
                "empty_title": "未找到交易",
                "empty_message": "您的钱包还没有任何记录的交易。",
                "explanation": "交易历史显示：\n• 转账（发送/接收）\n• 代币交换\n• 智能合约交互\n• DeFi协议活动",
                "coming_soon": "💡 **增强交易历史即将推出**\n\n我们正在添加区块链扫描，以显示您在所有协议和DEX上的完整链上活动。",
                "wallet_label": "钱包",
            },
            "fr": {
                "title": "📜 Historique des Transactions",
                "empty_title": "Aucune Transaction Trouvée",
                "empty_message": "Votre portefeuille n'a pas encore de transactions enregistrées.",
                "explanation": "L'historique des transactions affiche:\n• Transferts (envoi/réception)\n• Échanges de tokens\n• Interactions avec contrats intelligents\n• Activité des protocoles DeFi",
                "coming_soon": "💡 **Historique des Transactions Amélioré Bientôt Disponible**\n\nNous ajoutons la numérisation de la blockchain pour afficher votre activité complète en chaîne sur tous les protocoles et DEXs.",
                "wallet_label": "Portefeuille",
            },
        }
        msg = messages.get(language, messages["en"])

        divider = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        # Build content for empty transaction history
        content = f"""{divider}{msg["title"]}
{divider}

**{msg["empty_title"]}**

{msg["empty_message"]}

{msg["explanation"]}

{divider}
{msg["coming_soon"]}
"""

        if wallet_address:
            content += f"\n**{msg['wallet_label']}:** `{wallet_address[:6]}...{wallet_address[-4:]}`"

        logger.info(
            f"[Activity] Showing empty transaction history for authenticated user"
        )

        return {
            "content": content,
            "enrichment": {
                "transactions": [],
                "count": 0,
                "wallet_address": wallet_address,
            },
            "requires_registration": False,
        }

    async def _handle_activity(
        self,
        content: str,
        language: str,
        is_authenticated: bool = False,
        wallet_address: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Handle activity/transaction history inquiry.

        For guests: Show demo transaction history
        For authenticated: Show real on-chain transaction history
        """
        logger.info(
            f"[Activity] Handler called - language: {language}, authenticated: {is_authenticated}, wallet: {wallet_address[:10] if wallet_address else 'None'}..."
        )

        # Try to fetch real activity for authenticated users
        if is_authenticated and user_id:
            try:
                from app.domain.value_objects.user_id import UserId

                logger.info(
                    f"[Activity] Fetching real transactions for user: {user_id[:10]}..."
                )

                # Fetch user's transactions from database (limited to recent 20)
                # Note: This requires transaction_repository to be injected
                # For now, we'll show a message that real data requires blockchain scanning
                # In a full implementation, we would:
                # 1. Fetch from transaction_repository for app-initiated transactions
                # 2. Scan blockchain using Etherscan API or similar for all wallet activity

                # Build response indicating real transaction history is coming soon
                return await self._build_real_activity_response(
                    language, wallet_address
                )

            except Exception as e:
                logger.error(
                    f"[Activity] Error fetching real activity: {e}", exc_info=True
                )
                # Fall through to demo data

        # For guests or fallback, show demo activity
        return await self._activity_multistep.handle_flow(
            content=content,
            language=language,
            is_authenticated=is_authenticated,
        )

    async def _handle_out_of_scope(
        self,
        content: str,
        language: str,
        is_authenticated: bool = False,
    ) -> dict[str, Any]:
        """
        Handle out-of-scope queries (non-crypto, non-DeFi topics).

        Politely decline and redirect user to Anvil's DeFi capabilities.
        """
        logger.info(
            f"[OutOfScope] Declining off-topic query - language: {language}, content: {content[:50]}..."
        )

        translations = {
            "en": {
                "title": "⚠️ **Outside My Expertise**",
                "message": "I'm Anvil, a specialized DeFi assistant focused on:\n\n"
                "💰 **Portfolio Management** - Check balances, view holdings\n"
                "📊 **Market Intelligence** - Hunter AI sentiment, price predictions\n"
                "🔄 **DeFi Operations** - Swap, lend, stake, bridge\n"
                "⚡ **ULTRA Tools** - Arbitrage, flash loans, MEV protection\n"
                "🤖 **Agent Squad** - Specialist agents for yield, risk, security\n\n"
                "I can't help with questions outside crypto and DeFi.\n\n"
                "**Try asking:**\n"
                '• "What\'s my portfolio worth?"\n'
                '• "Show me USDC lending rates"\n'
                '• "Find arbitrage opportunities"\n'
                '• "Analyze ETH sentiment"',
            },
            "es": {
                "title": "⚠️ **Fuera de Mi Experiencia**",
                "message": "Soy Anvil, un asistente DeFi especializado en:\n\n"
                "💰 **Gestión de Portafolio** - Verificar saldos, ver tenencias\n"
                "📊 **Inteligencia de Mercado** - Sentimiento Hunter AI, predicciones\n"
                "🔄 **Operaciones DeFi** - Intercambiar, prestar, stakear, puentear\n"
                "⚡ **Herramientas ULTRA** - Arbitraje, préstamos flash, protección MEV\n"
                "🤖 **Escuadrón de Agentes** - Agentes especialistas\n\n"
                "No puedo ayudar con preguntas fuera de cripto y DeFi.\n\n"
                "**Intenta preguntar:**\n"
                '• "¿Cuánto vale mi portafolio?"\n'
                '• "Muéstrame tasas de préstamo USDC"\n'
                '• "Encuentra oportunidades de arbitraje"',
            },
            "pt": {
                "title": "⚠️ **Fora da Minha Expertise**",
                "message": "Sou Anvil, um assistente DeFi especializado em:\n\n"
                "💰 **Gestão de Portfólio** - Verificar saldos, ver holdings\n"
                "📊 **Inteligência de Mercado** - Sentimento Hunter AI, previsões\n"
                "🔄 **Operações DeFi** - Trocar, emprestar, stake, bridge\n"
                "⚡ **Ferramentas ULTRA** - Arbitragem, flash loans, proteção MEV\n"
                "🤖 **Equipe de Agentes** - Agentes especialistas\n\n"
                "Não posso ajudar com perguntas fora de cripto e DeFi.\n\n"
                "**Tente perguntar:**\n"
                '• "Quanto vale meu portfólio?"\n'
                '• "Mostre taxas de empréstimo USDC"\n'
                '• "Encontre oportunidades de arbitragem"',
            },
            "zh": {
                "title": "⚠️ **超出我的专业范围**",
                "message": "我是Anvil，专注于DeFi的助手：\n\n"
                "💰 **投资组合管理** - 检查余额，查看持仓\n"
                "📊 **市场情报** - Hunter AI情绪，价格预测\n"
                "🔄 **DeFi操作** - 交换，借贷，质押，跨链\n"
                "⚡ **ULTRA工具** - 套利，闪电贷，MEV保护\n"
                "🤖 **代理小队** - 专业代理\n\n"
                "我无法帮助加密和DeFi之外的问题。\n\n"
                "**尝试问：**\n"
                '• "我的投资组合值多少？"\n'
                '• "显示USDC借贷利率"\n'
                '• "寻找套利机会"',
            },
            "fr": {
                "title": "⚠️ **Hors de Mon Expertise**",
                "message": "Je suis Anvil, un assistant DeFi spécialisé dans:\n\n"
                "💰 **Gestion de Portefeuille** - Vérifier soldes, voir holdings\n"
                "📊 **Intelligence du Marché** - Sentiment Hunter AI, prédictions\n"
                "🔄 **Opérations DeFi** - Échanger, prêter, staker, bridge\n"
                "⚡ **Outils ULTRA** - Arbitrage, flash loans, protection MEV\n"
                "🤖 **Équipe d'Agents** - Agents spécialistes\n\n"
                "Je ne peux pas aider avec des questions hors crypto et DeFi.\n\n"
                "**Essayez de demander:**\n"
                '• "Quelle est la valeur de mon portefeuille?"\n'
                '• "Montrez les taux de prêt USDC"\n'
                '• "Trouvez des opportunités d\'arbitrage"',
            },
        }
        t = translations.get(language, translations["en"])

        content = f"{t['title']}\n\n{t['message']}"

        return {
            "content": content,
            "enrichment": {
                "intent": "out_of_scope",
                "suggested_topics": [
                    "portfolio",
                    "swap",
                    "lending",
                    "arbitrage",
                    "sentiment",
                ],
            },
            "requires_registration": False,
        }
