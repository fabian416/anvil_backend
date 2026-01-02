"""
Guest Handler Service.

Provides real data responses for guest users using existing handlers.
All responses are read-only (no wallet execution).
"""

import logging
from decimal import Decimal
from typing import Any

# DeFi Handler imports
from app.application.chat.handlers.lending_handler import LendingHandler
from app.application.chat.handlers.money_market_handler import MoneyMarketHandler
from app.application.chat.handlers.swap_handler import SwapHandler
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
    ):
        self._lending_handler = lending_handler
        self._swap_handler = swap_handler
        self._money_market_handler = money_market_handler

    async def handle_intent(
        self,
        intent: ChatIntent,
        content: str,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Handle intent with real data.

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
            # Agent Squad (Specialist Tasks & Complex Workflows)
            ChatIntent.SPECIALIST_TASK: self._handle_specialist_task,
            ChatIntent.COMPLEX_WORKFLOW: self._handle_complex_workflow,
        }

        handler = handler_map.get(intent)
        if handler:
            try:
                return await handler(content, language)
            except Exception as e:
                logger.warning(f"Handler error for {intent}: {e}")
                return self._fallback_response(intent, language)

        return self._fallback_response(intent, language)

    # ========================================
    # ========================================
    # GraphRAG Protocol Search Handlers (Demo Mode)
    # ========================================

    async def _handle_protocol_search(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle protocol search intent (demo mode with example protocols)."""
        # Demo protocols data - in production, this would query the graph
        demo_protocols = [
            {"name": "Aave", "category": "Lending", "tvl": 12.5, "risk": "LOW", "chain": "Ethereum"},
            {"name": "Compound", "category": "Lending", "tvl": 3.2, "risk": "LOW", "chain": "Ethereum"},
            {"name": "Uniswap", "category": "DEX", "tvl": 5.8, "risk": "LOW", "chain": "Ethereum"},
            {"name": "Curve", "category": "DEX", "tvl": 4.1, "risk": "LOW", "chain": "Ethereum"},
            {"name": "Lido", "category": "Staking", "tvl": 25.0, "risk": "LOW", "chain": "Ethereum"},
            {"name": "Morpho", "category": "Lending", "tvl": 1.8, "risk": "MEDIUM", "chain": "Ethereum"},
        ]

        translations = {
            "en": {
                "title": "🔍 **Protocol Search Results (Demo)**",
                "desc": "Here are some top DeFi protocols matching your criteria:",
                "tvl": "TVL",
                "risk": "Risk",
                "chain": "Chain",
                "note": "Register for full access to:",
                "features": ["Search 500+ protocols", "Custom filters", "Real-time data", "Risk analysis"],
            },
            "es": {
                "title": "🔍 **Resultados de Búsqueda de Protocolos (Demo)**",
                "desc": "Aquí hay algunos protocolos DeFi principales que coinciden con tus criterios:",
                "tvl": "TVL",
                "risk": "Riesgo",
                "chain": "Red",
                "note": "Regístrate para acceso completo a:",
                "features": ["Buscar 500+ protocolos", "Filtros personalizados", "Datos en tiempo real", "Análisis de riesgo"],
            },
            "pt": {
                "title": "🔍 **Resultados da Pesquisa de Protocolos (Demo)**",
                "desc": "Aqui estão alguns dos principais protocolos DeFi que correspondem aos seus critérios:",
                "tvl": "TVL",
                "risk": "Risco",
                "chain": "Rede",
                "note": "Registre-se para acesso completo a:",
                "features": ["Pesquisar 500+ protocolos", "Filtros personalizados", "Dados em tempo real", "Análise de risco"],
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
        response += "\n" + self._get_registration_cta(language, for_action=False)

        return {
            "content": response,
            "enrichment": {
                "graphrag": True,
                "demo_protocols": len(demo_protocols),
                "full_search_requires_registration": True,
            },
            "requires_registration": False,
        }

    async def _handle_risk_assessment(
        self, content: str, language: str
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
                "features": ["Real-time monitoring", "Historical data", "ML predictions", "Alerts"],
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
                "features": ["Monitoreo en tiempo real", "Datos históricos", "Predicciones ML", "Alertas"],
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
                "features": ["Monitoramento em tempo real", "Dados históricos", "Previsões ML", "Alertas"],
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
        response += "\n" + self._get_registration_cta(language, for_action=False)

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
        self, content: str, language: str
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
                "features": ["Detailed feature comparison", "APY comparison", "Risk analysis", "User reviews"],
            },
            "es": {
                "title": f"🔗 **Protocolos Similares a {protocol} (Demo)**",
                "desc": f"Basándose en categoría, características y perfil de riesgo, aquí hay protocolos similares a {protocol}:",
                "similarity": "Similitud",
                "note": "Regístrate para comparación completa incluyendo:",
                "features": ["Comparación detallada de características", "Comparación de APY", "Análisis de riesgo", "Opiniones de usuarios"],
            },
            "pt": {
                "title": f"🔗 **Protocolos Similares a {protocol} (Demo)**",
                "desc": f"Com base em categoria, recursos e perfil de risco, aqui estão protocolos semelhantes a {protocol}:",
                "similarity": "Similaridade",
                "note": "Registre-se para comparação completa incluindo:",
                "features": ["Comparação detalhada de recursos", "Comparação de APY", "Análise de risco", "Avaliações de usuários"],
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
        response += "\n" + self._get_registration_cta(language, for_action=False)

        return {
            "content": response,
            "enrichment": {
                "graphrag": True,
                "base_protocol": protocol,
                "similar_protocols": [s[0] for s in similar],
                "full_comparison_requires_registration": True,
            },
            "requires_registration": False,
        }

    # ========================================
    # Hunter AI Handlers
    # ========================================

    async def _handle_sentiment(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle sentiment analysis with real data."""
        # Extract token from content (simple parsing)
        token = self._extract_token(content) or "ETH"

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
            response = f"📊 **Sentiment Analysis for {token}**\n\n"
            response += f"**Overall:** {aggregated.classification.value.title()} "
            response += f"({aggregated.overall_score:.1f}/100)\n"
            response += f"**Confidence:** {aggregated.overall_confidence * 100:.0f}%\n\n"

            response += "**By Source:**\n"
            for source, data in breakdown.items():
                emoji = "🟢" if data["score"] > 60 else "🔴" if data["score"] < 40 else "🟡"
                response += f"- {source.title()}: {emoji} {data['score']:.0f}/100\n"

            response += self._get_registration_cta(language)

            return {
                "content": response,
                "enrichment": {
                    "token": token,
                    "overall_score": aggregated.overall_score,
                    "classification": aggregated.classification.value,
                    "sources": breakdown,
                    "hunter_tool": "sentiment_aggregator",
                },
                "requires_registration": False,
            }
        except Exception as e:
            logger.warning(f"Sentiment analysis error: {e}")
            return self._fallback_response(ChatIntent.HUNTER_SENTIMENT, language)

    async def _handle_price_prediction(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle price prediction with real ML model."""
        token = self._extract_token(content) or "ETH"

        try:
            predictor = LSTMPricePredictor()
            prediction = await predictor.predict(token, horizon_hours=168)  # 7 days

            # Determine emoji based on direction
            direction_emoji = "🟢" if prediction.direction == "up" else "🔴" if prediction.direction == "down" else "🟡"

            response = f"📈 **Price Prediction for {token}**\n\n"
            response += f"**Current Price:** ${prediction.current_price:,.2f}\n"
            response += f"**7-Day Forecast:** ${prediction.predicted_price:,.2f}\n"
            response += f"**Expected Change:** {direction_emoji} {prediction.change_percent:+.1f}%\n"
            response += f"**Direction:** {prediction.direction.upper()}\n"
            response += f"**Confidence:** {prediction.confidence * 100:.0f}%\n\n"

            response += "**Model:** LSTM Neural Network\n"
            response += f"**Horizon:** {prediction.horizon_hours} hours\n"

            response += self._get_registration_cta(language)

            return {
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
                "requires_registration": False,
            }
        except Exception as e:
            logger.warning(f"Price prediction error: {e}")
            return self._fallback_response(ChatIntent.HUNTER_PRICE_PREDICTION, language)

    async def _handle_risk_signals(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle market risk signals."""
        token = self._extract_token(content) or "ETH"

        try:
            analyzer = RiskAnalyzer()
            signals = await analyzer.analyze_market_risk(token)

            response = f"⚠️ **Risk Signals for {token}**\n\n"
            response += f"**Overall Risk Level:** {signals.risk_level.upper()}\n"
            response += f"**Risk Score:** {signals.risk_score}/100\n\n"

            response += "**Risk Factors:**\n"
            for factor in signals.factors[:5]:
                emoji = "🔴" if factor.severity == "high" else "🟡" if factor.severity == "medium" else "🟢"
                response += f"- {emoji} {factor.name}: {factor.description}\n"

            if signals.whale_activity:
                response += "\n**🐋 Whale Activity:**\n"
                response += f"- Large transfers: {signals.whale_activity.transfer_count}\n"
                response += f"- Net flow: ${signals.whale_activity.net_flow:,.0f}\n"

            response += self._get_registration_cta(language)

            return {
                "content": response,
                "enrichment": {
                    "token": token,
                    "risk_level": signals.risk_level,
                    "risk_score": signals.risk_score,
                    "factors": [f.name for f in signals.factors],
                    "hunter_tool": "risk_analyzer",
                },
                "requires_registration": False,
            }
        except Exception as e:
            logger.warning(f"Risk signals error: {e}")
            return self._fallback_response(ChatIntent.HUNTER_RISK_SIGNALS, language)

    async def _handle_trading_signals(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle trading signal generation."""
        token = self._extract_token(content) or "ETH"

        try:
            generator = TradingSignalGenerator()
            signal = await generator.generate_signal(token, Timeframe.HOUR_4)

            # Determine emoji based on signal type
            signal_emoji = "🟢" if signal.signal_type.value == "buy" else "🔴" if signal.signal_type.value == "sell" else "🟡"

            response = f"💹 **Trading Signal for {token}**\n\n"
            response += f"**Signal:** {signal_emoji} {signal.signal_type.value.upper()}\n"
            response += f"**Strength:** {signal.signal_strength:.0f}/100\n"
            response += f"**Confidence:** {signal.confidence * 100:.0f}%\n"
            response += f"**Timeframe:** {signal.timeframe.value}\n\n"

            if signal.entry_price:
                response += f"**Entry Price:** ${signal.entry_price:,.2f}\n"
            if signal.stop_loss_price:
                response += f"**Stop Loss:** ${signal.stop_loss_price:,.2f}\n"
            if signal.take_profit_price:
                response += f"**Take Profit:** ${signal.take_profit_price:,.2f}\n"

            response += "\n**Factor Scores:**\n"
            response += f"- Sentiment: {signal.sentiment_score:.0f}/100\n"
            response += f"- Prediction: {signal.prediction_score:.0f}/100\n"
            response += f"- Risk: {signal.risk_score:.0f}/100\n"

            response += self._get_registration_cta(language)

            return {
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
        except Exception as e:
            logger.warning(f"Trading signals error: {e}")
            return self._fallback_response(ChatIntent.HUNTER_TRADING_SIGNALS, language)

    async def _handle_patterns(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle chart pattern recognition."""
        token = self._extract_token(content) or "ETH"

        try:
            recognizer = PatternRecognizer()
            patterns = await recognizer.detect_patterns(token, timeframe="4h")

            response = f"📊 **Chart Patterns for {token}**\n\n"

            if not patterns:
                response += "No significant patterns detected currently.\n"
            else:
                for pattern in patterns[:3]:
                    emoji = "🟢" if pattern.bias == "bullish" else "🔴" if pattern.bias == "bearish" else "🟡"
                    response += f"**{emoji} {pattern.name}**\n"
                    response += f"- Confidence: {pattern.confidence * 100:.0f}%\n"
                    response += f"- Target: ${pattern.target_price:,.2f}\n"
                    response += f"- Status: {pattern.status}\n\n"

            response += self._get_registration_cta(language)

            return {
                "content": response,
                "enrichment": {
                    "token": token,
                    "patterns": [p.name for p in patterns],
                    "hunter_tool": "pattern_recognizer",
                },
                "requires_registration": False,
            }
        except Exception as e:
            logger.warning(f"Pattern recognition error: {e}")
            return self._fallback_response(ChatIntent.HUNTER_PATTERNS, language)

    async def _handle_portfolio_optimization(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle portfolio optimization suggestions."""
        try:
            optimizer = PortfolioOptimizer()

            # Use default portfolio for demo
            demo_portfolio = ["ETH", "BTC", "USDC"]
            result = await optimizer.optimize(demo_portfolio, risk_tolerance="moderate")

            response = "💼 **Portfolio Optimization (Demo)**\n\n"
            response += f"**Strategy:** {result.strategy}\n"
            response += f"**Risk Level:** {result.risk_level}\n\n"

            response += "**Suggested Allocation:**\n"
            for token, weight in result.allocation.items():
                response += f"- {token}: {weight * 100:.0f}%\n"

            response += f"\n**Expected Return:** {result.expected_return * 100:.1f}% (annual)\n"
            response += f"**Sharpe Ratio:** {result.sharpe_ratio:.2f}\n"

            response += self._get_registration_cta(language, for_action=True)

            return {
                "content": response,
                "enrichment": {
                    "allocation": result.allocation,
                    "expected_return": result.expected_return,
                    "sharpe_ratio": result.sharpe_ratio,
                    "hunter_tool": "portfolio_optimizer",
                },
                "requires_registration": True,  # Need wallet to apply
            }
        except Exception as e:
            logger.warning(f"Portfolio optimization error: {e}")
            return self._fallback_response(ChatIntent.HUNTER_PORTFOLIO, language)

    # ========================================
    # ULTRA Handlers
    # ========================================

    async def _handle_arbitrage(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle arbitrage opportunity discovery."""
        try:
            discovery = ArbitrageDiscovery()
            capital = Decimal("10000")  # Demo with $10k
            opportunities = await discovery.discover_all_opportunities(capital)

            response = "🔄 **Arbitrage Opportunities** (Demo: $10,000)\n\n"

            if not opportunities:
                response += "❌ No profitable opportunities found currently.\n\n"
                response += "Markets are efficient or gas > profit.\n"
            else:
                response += f"**Found {len(opportunities)} opportunities:**\n\n"
                for i, opp in enumerate(opportunities[:3], 1):
                    response += f"**{i}. {opp.type.value.upper()}**\n"
                    # Build path string from trading pairs
                    path_tokens = [opp.path[0].token_in]
                    for pair in opp.path:
                        path_tokens.append(pair.token_out)
                    path_str = " → ".join(path_tokens)
                    response += f"- Route: {path_str}\n"
                    response += f"- Net Profit: ${float(opp.expected_profit_usd):,.2f}\n"
                    response += f"- ROI: {float(opp.profit_percentage * 100):.2f}%\n\n"

            response += self._get_registration_cta(language, for_action=True)

            return {
                "content": response,
                "enrichment": {
                    "capital": 10000,
                    "opportunities_found": len(opportunities),
                    "ultra_tool": "arbitrage_discovery",
                },
                "requires_registration": True,  # Need wallet to execute
            }
        except Exception as e:
            logger.warning(f"Arbitrage discovery error: {e}")
            return self._fallback_response(ChatIntent.ULTRA_ARBITRAGE, language)

    async def _handle_flash_loans(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle flash loan information."""
        try:
            engine = FlashLoanEngine()
            protocols = await engine.get_protocols()

            response = "⚡ **Flash Loan Protocols**\n\n"

            for protocol in protocols:
                response += f"**{protocol.name}**\n"
                response += f"- Max Loan: ${float(protocol.max_loan_usd):,.0f}\n"
                response += f"- Fee: {float(protocol.fee_percentage * 100):.2f}%\n"
                response += f"- Tokens: {', '.join(protocol.supported_tokens[:3])}\n\n"

            response += "**Use Cases:**\n"
            response += "- Arbitrage execution\n"
            response += "- Collateral swaps\n"
            response += "- Liquidation protection\n"

            response += self._get_registration_cta(language, for_action=True)

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
            return self._fallback_response(ChatIntent.ULTRA_FLASH_LOANS, language)

    async def _handle_mev_protection(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle MEV protection information."""
        try:
            protection = MEVProtection()
            info = protection.get_protection_info()

            response = "🛡️ **MEV Protection Status**\n\n"
            response += f"**Flashbots:** {'✅ Enabled' if info['use_flashbots'] else '❌ Disabled'}\n"
            response += f"**Private Relay:** {'✅ Enabled' if info['use_private_relay'] else '❌ Disabled'}\n"
            response += f"**MEV-Share:** {'✅ Enabled' if info['use_mev_share'] else '❌ Disabled'}\n"
            response += f"**Protection Level:** {info['protection_level'].upper()}\n"
            response += f"**Max Gas Price:** {info['max_gas_price_gwei']} gwei\n\n"

            response += "**Protection Features:**\n"
            response += "- ✅ Sandwich attack prevention\n"
            response += "- ✅ Front-running protection\n"
            response += "- ✅ Private transaction routing\n"
            response += "- ✅ Backrun capture\n"

            response += self._get_registration_cta(language, for_action=True)

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
            return self._fallback_response(ChatIntent.ULTRA_MEV_PROTECTION, language)

    async def _handle_auto_executor(
        self, content: str, language: str
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

        response += self._get_registration_cta(language, for_action=True)

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
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle lending rates with real Morpho data."""
        if self._lending_handler:
            try:
                result = await self._lending_handler.handle(
                    content=content,
                    user_id=None,  # Guest mode
                    wallet_address=None,
                    language=language,
                )
                # Add registration CTA
                result["content"] += self._get_registration_cta(language, for_action=True)
                result["requires_registration"] = True
                return result
            except Exception as e:
                logger.warning(f"Lending handler error: {e}")

        return self._fallback_response(ChatIntent.LENDING, language)

    async def _handle_money_market(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle money market rates with real Aave/Compound data."""
        if self._money_market_handler:
            try:
                result = await self._money_market_handler.handle(
                    content=content,
                    user_id=None,
                    wallet_address=None,
                    language=language,
                )
                result["content"] += self._get_registration_cta(language, for_action=True)
                result["requires_registration"] = True
                return result
            except Exception as e:
                logger.warning(f"Money market handler error: {e}")

        return self._fallback_response(ChatIntent.MONEY_MARKET, language)

    async def _handle_swap(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle swap quotes with real 1inch data."""
        if self._swap_handler:
            try:
                result = await self._swap_handler.handle(
                    content=content,
                    user_id=None,
                    wallet_address=None,
                    language=language,
                )
                result["content"] += self._get_registration_cta(language, for_action=True)
                result["requires_registration"] = True
                return result
            except Exception as e:
                logger.warning(f"Swap handler error: {e}")

        return self._fallback_response(ChatIntent.SWAP, language)

    # ========================================
    # Agent Squad Handlers
    # ========================================

    async def _handle_specialist_task(
        self, content: str, language: str
    ) -> dict[str, Any]:
        """Handle specialist task requests (Agent Squad)."""
        translations = {
            "en": {
                "title": "🤖 **Agent Squad - Specialist Agents**",
                "desc": "Our AI agents can help with specialized DeFi tasks:",
                "agents": [
                    ("🔬 Research Agent", "Deep protocol analysis and yield strategies"),
                    ("🛡️ Security Auditor", "Smart contract security analysis via Slither"),
                    ("⛽ Gas Optimizer", "Reduce transaction costs with optimal timing"),
                    ("📊 Tax Optimizer", "Capital gains strategies and tax reporting"),
                    ("📈 Risk Analyzer", "Portfolio risk assessment and exposure analysis"),
                    ("💼 Portfolio Agent", "Asset allocation and rebalancing recommendations"),
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

        response += "\n" + self._get_registration_cta(language, for_action=True)

        return {
            "content": response,
            "enrichment": {
                "agent_squad": True,
                "available_agents": [
                    "research", "security_auditor", "gas_optimizer", "tax_optimizer",
                    "risk_analyzer", "portfolio", "bridge_crosschain", "compliance_monitor",
                    "multisig_coordinator", "dao_governance", "nft_asset_manager", "lending_borrowing",
                ],
            },
            "requires_registration": True,
        }

    async def _handle_complex_workflow(
        self, content: str, language: str
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

        response += "\n" + self._get_registration_cta(language, for_action=True)

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
        content_upper = content.upper()
        tokens = ["ETH", "BTC", "USDC", "USDT", "DAI", "WETH", "WBTC", "SOL", "MATIC", "ARB", "OP"]
        for token in tokens:
            if token in content_upper:
                return token
        return None

    def _get_registration_cta(
        self, language: str, for_action: bool = False
    ) -> str:
        """Get registration call-to-action based on language."""
        if for_action:
            ctas = {
                "en": "\n\n👉 **Sign up to execute this action** → /signup",
                "es": "\n\n👉 **Regístrate para ejecutar esta acción** → /signup",
                "pt": "\n\n👉 **Cadastre-se para executar esta ação** → /signup",
                "zh": "\n\n👉 **注册以执行此操作** → /signup",
            }
        else:
            ctas = {
                "en": "\n\n👉 **Sign up for real-time alerts** → /signup",
                "es": "\n\n👉 **Regístrate para alertas en tiempo real** → /signup",
                "pt": "\n\n👉 **Cadastre-se para alertas em tempo real** → /signup",
                "zh": "\n\n👉 **注册以获取实时警报** → /signup",
            }
        return ctas.get(language, ctas["en"])

    def _fallback_response(
        self, intent: ChatIntent, language: str
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
        }

        default = {
            "en": "Service temporarily unavailable. Please try again or sign up for full access.",
            "es": "Servicio no disponible. Intenta de nuevo o regístrate para acceso completo.",
            "pt": "Serviço indisponível. Tente novamente ou cadastre-se para acesso completo.",
            "zh": "服务暂时不可用。请重试或注册以获得完整访问。",
        }

        messages = fallbacks.get(intent, default)
        content = messages.get(language, messages.get("en", ""))

        return {
            "content": content,
            "enrichment": None,
            "requires_registration": False,
        }
