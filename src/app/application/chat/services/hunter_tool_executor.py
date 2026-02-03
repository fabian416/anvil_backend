"""
Hunter AI tool executor for chat integration.

This service executes Hunter AI tools and formats responses for chat display.
"""

import httpx
from typing import Any, Dict
from datetime import datetime

from app.domain.value_objects.agent_tools.hunter_tools import HunterToolType


class HunterToolExecutor:
    """
    Executes Hunter AI tools and formats responses for chat.

    This service acts as a bridge between the chat system and Hunter AI APIs.
    It calls the appropriate Hunter AI endpoints and formats the responses
    into human-readable text suitable for chat display.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize Hunter AI tool executor.

        Args:
            base_url: Base URL for Hunter AI APIs (default: localhost)
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def execute_tool(
        self,
        tool_type: HunterToolType,
        parameters: Dict[str, Any],
    ) -> str:
        """
        Execute Hunter AI tool and format response for chat.

        Args:
            tool_type: Type of Hunter AI tool to execute
            parameters: Tool parameters (validated against schema)

        Returns:
            Formatted string response suitable for chat display

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If tool type is unknown
        """
        if tool_type == HunterToolType.SENTIMENT_ANALYSIS:
            return await self._execute_sentiment(parameters)
        elif tool_type == HunterToolType.PRICE_PREDICTION:
            return await self._execute_prediction(parameters)
        elif tool_type == HunterToolType.RISK_ANALYSIS:
            return await self._execute_risk(parameters)
        elif tool_type == HunterToolType.TRADING_SIGNALS:
            return await self._execute_signal(parameters)
        elif tool_type == HunterToolType.PORTFOLIO_OPTIMIZATION:
            return await self._execute_portfolio(parameters)
        elif tool_type == HunterToolType.PATTERN_RECOGNITION:
            return await self._execute_patterns(parameters)
        else:
            raise ValueError(f"Unknown Hunter AI tool type: {tool_type}")

    async def _execute_sentiment(self, params: Dict[str, Any]) -> str:
        """Execute sentiment analysis and format response."""
        token = params["token_symbol"]

        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/hunter/sentiment/analyze/{token}"
            )
            response.raise_for_status()
            data = response.json()

            return self._format_sentiment_response(token, data)
        except httpx.HTTPError as e:
            return f"❌ Error analyzing sentiment for {token}: {str(e)}"

    async def _execute_prediction(self, params: Dict[str, Any]) -> str:
        """Execute price prediction and format response."""
        token = params["token_symbol"]
        horizon = params.get("horizon_hours", 24)

        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/hunter/prediction/predict/{token}",
                params={"horizon_hours": horizon},
            )
            response.raise_for_status()
            data = response.json()

            return self._format_prediction_response(token, data)
        except httpx.HTTPError as e:
            return f"❌ Error predicting price for {token}: {str(e)}"

    async def _execute_risk(self, params: Dict[str, Any]) -> str:
        """Execute risk analysis and format response."""
        token = params["token_symbol"]

        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/hunter/risk/analyze/{token}"
            )
            response.raise_for_status()
            data = response.json()

            return self._format_risk_response(token, data)
        except httpx.HTTPError as e:
            return f"❌ Error analyzing risk for {token}: {str(e)}"

    async def _execute_signal(self, params: Dict[str, Any]) -> str:
        """Execute trading signal generation and format response."""
        token = params["token_symbol"]
        timeframe = params.get("timeframe", "1d")

        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/hunter/signals/generate/{token}",
                params={"timeframe": timeframe},
            )
            response.raise_for_status()
            data = response.json()

            return self._format_signal_response(token, data)
        except httpx.HTTPError as e:
            return f"❌ Error generating signal for {token}: {str(e)}"

    async def _execute_portfolio(self, params: Dict[str, Any]) -> str:
        """Execute portfolio optimization and format response."""
        tokens = params["tokens"]
        risk_tolerance = params.get("risk_tolerance", 0.5)

        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/hunter/portfolio/optimize",
                json={
                    "tokens": tokens,
                    "risk_tolerance": risk_tolerance,
                },
            )
            response.raise_for_status()
            data = response.json()

            return self._format_portfolio_response(tokens, data)
        except httpx.HTTPError as e:
            return f"❌ Error optimizing portfolio: {str(e)}"

    async def _execute_patterns(self, params: Dict[str, Any]) -> str:
        """Execute pattern recognition and format response."""
        token = params["token_symbol"]
        min_confidence = params.get("min_confidence", 0.6)

        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/hunter/patterns/analysis/{token}",
                params={"min_confidence": min_confidence},
            )
            response.raise_for_status()
            data = response.json()

            return self._format_patterns_response(token, data)
        except httpx.HTTPError as e:
            return f"❌ Error detecting patterns for {token}: {str(e)}"

    # Response formatting methods

    def _format_sentiment_response(self, token: str, data: Dict) -> str:
        """Format sentiment response for chat display."""
        sentiment = data.get("sentiment", {})
        score = sentiment.get("overall_score", 0)
        confidence = sentiment.get("overall_confidence", 0) * 100
        trend = sentiment.get("trend", "stable")

        # Emoji and label based on score
        if score >= 70:
            emoji = "🟢"
            label = "Bullish"
        elif score >= 50:
            emoji = "🔵"
            label = "Neutral-Bullish"
        elif score >= 30:
            emoji = "🟡"
            label = "Neutral"
        elif score >= 10:
            emoji = "🟠"
            label = "Bearish"
        else:
            emoji = "🔴"
            label = "Very Bearish"

        result = f"💭 **{token} Sentiment Analysis:**\n\n"
        result += f"**Overall:** {score:.1f}/100 ({label}) {emoji}\n"
        result += f"**Confidence:** {confidence:.0f}%\n\n"

        # Source breakdown
        sources = sentiment.get("sources", {})
        if sources:
            result += "**Sources:**\n"
            for source, info in sources.items():
                src_score = info.get("score", 0) if isinstance(info, dict) else info
                result += f"• {source.capitalize()}: {src_score:.1f}/100\n"

        # Trend
        trend_emoji = "↑" if trend == "rising" else "↓" if trend == "declining" else "→"
        result += f"\n**Trend:** {trend_emoji} {trend.capitalize()}"

        return result

    def _format_prediction_response(self, token: str, data: Dict) -> str:
        """Format price prediction response for chat display."""
        current = data.get("current_price", 0)
        predicted = data.get("predicted_price", 0)
        change = data.get("change_percent", 0)
        confidence = data.get("confidence", 0) * 100
        horizon = data.get("horizon_hours", 24)
        direction = data.get("direction", "neutral")

        # Direction emoji
        direction_emoji = (
            "🚀" if direction == "up" else "📉" if direction == "down" else "→"
        )
        change_sign = "+" if change > 0 else ""

        result = f"🔮 **{token} Price Prediction ({horizon}h):**\n\n"
        result += f"**Current Price:** ${current:.2f}\n"
        result += f"**Predicted Price:** ${predicted:.2f} ({change_sign}{change:.2f}%) {direction_emoji}\n"
        result += f"**Confidence:** {confidence:.0f}%\n"
        result += f"**Direction:** {direction.upper()}"

        return result

    def _format_risk_response(self, token: str, data: Dict) -> str:
        """Format risk analysis response for chat display."""
        overall = data.get("overall_risk_score", 0)
        level = data.get("risk_level", "unknown")

        # Risk level emoji
        if level in ["very_high", "high"]:
            emoji = "🔴"
        elif level == "medium":
            emoji = "⚠️"
        else:
            emoji = "🟢"

        result = f"⚠️ **{token} Risk Analysis:**\n\n"
        result += f"**Overall Risk:** {overall:.1f}/100 ({level.replace('_', ' ').title()}) {emoji}\n\n"

        # Risk factors
        factors = data.get("factors", {})
        if factors:
            result += "**Risk Factors:**\n"
            for factor, info in factors.items():
                factor_score = info.get("score", 0) if isinstance(info, dict) else info
                result += (
                    f"• {factor.replace('_', ' ').title()}: {factor_score:.1f}/100\n"
                )

        return result

    def _format_signal_response(self, token: str, data: Dict) -> str:
        """Format trading signal response for chat display."""
        signal_type = data.get("signal_type", "hold").upper()
        confidence = data.get("confidence", 0) * 100
        entry = data.get("entry_price", 0)
        exit_price = data.get("exit_price", 0)
        stop_loss = data.get("stop_loss", 0)
        take_profit = data.get("take_profit", 0)
        timeframe = data.get("timeframe", "1d")

        # Signal emoji
        if "buy" in signal_type.lower():
            emoji = "🟢"
        elif "sell" in signal_type.lower():
            emoji = "🔴"
        else:
            emoji = "🟡"

        result = f"🔔 **{token} Trading Signal ({timeframe}):**\n\n"
        result += f"**Signal:** {signal_type} {emoji}\n"
        result += f"**Confidence:** {confidence:.0f}%\n\n"

        if entry > 0:
            result += f"**Entry Price:** ${entry:.2f}\n"
        if exit_price > 0:
            result += f"**Exit Target:** ${exit_price:.2f}\n"
        if stop_loss > 0:
            result += f"**Stop Loss:** ${stop_loss:.2f}\n"
        if take_profit > 0:
            result += f"**Take Profit:** ${take_profit:.2f}\n"

        # Reasoning
        reasoning = data.get("reasoning", "")
        if reasoning:
            result += f"\n**Reasoning:** {reasoning}"

        return result

    def _format_portfolio_response(self, tokens: list, data: Dict) -> str:
        """Format portfolio optimization response for chat display."""
        result = "💼 **Portfolio Optimization:**\n\n"

        # Allocations
        allocations = data.get("allocations", [])
        if allocations:
            result += "**Optimal Allocation:**\n"
            for alloc in allocations:
                token = alloc.get("token", "")
                weight = alloc.get("weight", 0) * 100
                result += f"• {token}: {weight:.1f}%\n"

        # Metrics
        metrics = data.get("metrics", {})
        if metrics:
            result += "\n**Expected Performance:**\n"
            exp_return = metrics.get("expected_return", 0) * 100
            volatility = metrics.get("expected_volatility", 0) * 100
            sharpe = metrics.get("sharpe_ratio", 0)

            result += f"• Expected Return: {exp_return:.1f}% annually\n"
            result += f"• Volatility: {volatility:.1f}%\n"
            result += f"• Sharpe Ratio: {sharpe:.2f}"

        return result

    def _format_patterns_response(self, token: str, data: Dict) -> str:
        """Format pattern recognition response for chat display."""
        result = f"📈 **{token} Pattern Analysis:**\n\n"

        # Chart patterns
        chart_patterns = data.get("chart_patterns", [])
        if chart_patterns:
            result += "**Chart Patterns:**\n"
            for pattern in chart_patterns[:3]:  # Top 3
                ptype = pattern.get("pattern_type", "").replace("_", " ").title()
                signal = pattern.get("signal", "neutral")
                confidence = pattern.get("confidence", 0) * 100

                signal_emoji = (
                    "🟢"
                    if signal == "bullish"
                    else "🔴"
                    if signal == "bearish"
                    else "🟡"
                )
                result += f"• {ptype} ({signal_emoji} {signal}, {confidence:.0f}% confidence)\n"

        # Candlestick patterns
        candle_patterns = data.get("candlestick_patterns", [])
        if candle_patterns:
            result += "\n**Candlestick Patterns:**\n"
            for pattern in candle_patterns[:3]:  # Top 3
                ptype = pattern.get("pattern_type", "").replace("_", " ").title()
                signal = pattern.get("signal", "neutral")
                confidence = pattern.get("confidence", 0) * 100

                signal_emoji = (
                    "🟢"
                    if signal == "bullish"
                    else "🔴"
                    if signal == "bearish"
                    else "🟡"
                )
                result += f"• {ptype} ({signal_emoji} {signal}, {confidence:.0f}% confidence)\n"

        # Support/Resistance
        sr_levels = data.get("support_resistance", {})
        if sr_levels:
            support = sr_levels.get("support_levels", [])
            resistance = sr_levels.get("resistance_levels", [])

            if support:
                result += "\n**Support Levels:**\n"
                for level in support[:2]:  # Top 2
                    price = level.get("price", 0)
                    strength = level.get("strength", 0)
                    result += f"• ${price:.2f} (strength: {strength})\n"

            if resistance:
                result += "\n**Resistance Levels:**\n"
                for level in resistance[:2]:  # Top 2
                    price = level.get("price", 0)
                    strength = level.get("strength", 0)
                    result += f"• ${price:.2f} (strength: {strength})\n"

        return result

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
