"""
Hunter AI tool definitions for chat integration.

These tool definitions allow the AI agent to invoke Hunter AI capabilities
(sentiment analysis, price predictions, risk scoring, etc.) during chat conversations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class HunterToolType(Enum):
    """Hunter AI tool types."""

    SENTIMENT_ANALYSIS = "hunter_sentiment_analysis"
    PRICE_PREDICTION = "hunter_price_prediction"
    RISK_ANALYSIS = "hunter_risk_analysis"
    TRADING_SIGNALS = "hunter_trading_signals"
    PORTFOLIO_OPTIMIZATION = "hunter_portfolio_optimization"
    PATTERN_RECOGNITION = "hunter_pattern_recognition"


@dataclass(frozen=True)
class HunterToolDefinition:
    """
    Hunter AI tool definition for agent use.

    Attributes:
        name: Tool function name
        type: Hunter AI tool type
        description: Human-readable description of what the tool does
        parameters: Parameter schema (JSON Schema format)
    """

    name: str
    type: HunterToolType
    description: str
    parameters: Dict[str, Any]

    def to_agent_format(self) -> Dict[str, Any]:
        """
        Convert to Agent Squad tool format.

        Returns:
            Dictionary in Agent Squad tool format
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


# Predefined Hunter AI tools available in chat
HUNTER_TOOLS: List[HunterToolDefinition] = [
    HunterToolDefinition(
        name="analyze_sentiment",
        type=HunterToolType.SENTIMENT_ANALYSIS,
        description=(
            "Analyze multi-source sentiment for a cryptocurrency token. "
            "Sources include Twitter, Reddit, Discord, and news articles. "
            "Returns overall sentiment score (0-100), confidence level, trend direction, "
            "and breakdown by source. Use this to gauge market sentiment and social buzz."
        ),
        parameters={
            "type": "object",
            "properties": {
                "token_symbol": {
                    "type": "string",
                    "description": "Token symbol (e.g., ETH, BTC, UNI, AAVE)",
                },
            },
            "required": ["token_symbol"],
        },
    ),
    HunterToolDefinition(
        name="predict_price",
        type=HunterToolType.PRICE_PREDICTION,
        description=(
            "Predict future token price using LSTM neural network. "
            "Analyzes historical price data, volume, and technical indicators. "
            "Returns predicted price, confidence level, percentage change, and forecast direction. "
            "Supports multiple timeframes (1h, 6h, 24h, 7d)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "token_symbol": {
                    "type": "string",
                    "description": "Token symbol (e.g., ETH, BTC, UNI)",
                },
                "horizon_hours": {
                    "type": "integer",
                    "description": "Forecast horizon in hours (1, 6, 24, 168). Default: 24",
                    "default": 24,
                    "enum": [1, 6, 24, 168],
                },
            },
            "required": ["token_symbol"],
        },
    ),
    HunterToolDefinition(
        name="analyze_risk",
        type=HunterToolType.RISK_ANALYSIS,
        description=(
            "Perform comprehensive 4-factor risk analysis for a token. "
            "Evaluates: (1) Volatility risk - historical price volatility, "
            "(2) Liquidity risk - trading volume and DEX liquidity, "
            "(3) Smart contract risk - code complexity and audit status, "
            "(4) Market correlation risk - beta to major assets. "
            "Returns overall risk score (0-100) and risk level classification."
        ),
        parameters={
            "type": "object",
            "properties": {
                "token_symbol": {
                    "type": "string",
                    "description": "Token symbol (e.g., ETH, BTC, SOL)",
                },
            },
            "required": ["token_symbol"],
        },
    ),
    HunterToolDefinition(
        name="generate_trading_signal",
        type=HunterToolType.TRADING_SIGNALS,
        description=(
            "Generate AI trading signal (BUY/SELL/HOLD) based on multi-factor analysis. "
            "Combines sentiment score, price prediction, and risk assessment. "
            "Returns signal type, confidence level, entry/exit prices, stop-loss, "
            "take-profit targets, position sizing recommendation, and reasoning. "
            "Supports multiple timeframes."
        ),
        parameters={
            "type": "object",
            "properties": {
                "token_symbol": {
                    "type": "string",
                    "description": "Token symbol (e.g., ETH, BTC, UNI)",
                },
                "timeframe": {
                    "type": "string",
                    "description": "Analysis timeframe (1h, 4h, 1d, 1w, 1M). Default: 1d",
                    "default": "1d",
                    "enum": ["1h", "4h", "1d", "1w", "1M"],
                },
            },
            "required": ["token_symbol"],
        },
    ),
    HunterToolDefinition(
        name="optimize_portfolio",
        type=HunterToolType.PORTFOLIO_OPTIMIZATION,
        description=(
            "Optimize portfolio allocation using Modern Portfolio Theory (MPT). "
            "Calculates optimal asset weights to maximize Sharpe ratio or minimize variance. "
            "Returns optimized allocation, expected return, volatility, Sharpe ratio, "
            "diversification score, and rebalancing recommendations. "
            "Supports conservative, balanced, and aggressive risk profiles."
        ),
        parameters={
            "type": "object",
            "properties": {
                "tokens": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of token symbols to include in portfolio (e.g., ['ETH', 'BTC', 'UNI'])",
                },
                "risk_tolerance": {
                    "type": "number",
                    "description": "Risk tolerance level: 0-0.33 (conservative), 0.33-0.67 (balanced), 0.67-1.0 (aggressive). Default: 0.5",
                    "default": 0.5,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
            },
            "required": ["tokens"],
        },
    ),
    HunterToolDefinition(
        name="detect_patterns",
        type=HunterToolType.PATTERN_RECOGNITION,
        description=(
            "Detect technical chart patterns and support/resistance levels. "
            "Identifies chart patterns (head & shoulders, triangles, flags, etc.) "
            "and candlestick patterns (doji, hammer, engulfing, etc.). "
            "Returns detected patterns with confidence scores, signal direction (bullish/bearish), "
            "and key price levels. Use for technical analysis and entry/exit timing."
        ),
        parameters={
            "type": "object",
            "properties": {
                "token_symbol": {
                    "type": "string",
                    "description": "Token symbol (e.g., ETH, BTC, SOL)",
                },
                "min_confidence": {
                    "type": "number",
                    "description": "Minimum confidence threshold for pattern detection (0-1). Default: 0.6",
                    "default": 0.6,
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
            },
            "required": ["token_symbol"],
        },
    ),
]


def get_hunter_tool_by_name(name: str) -> HunterToolDefinition | None:
    """
    Get Hunter AI tool definition by name.

    Args:
        name: Tool name

    Returns:
        Tool definition if found, None otherwise
    """
    for tool in HUNTER_TOOLS:
        if tool.name == name:
            return tool
    return None


def get_hunter_tool_by_type(tool_type: HunterToolType) -> HunterToolDefinition | None:
    """
    Get Hunter AI tool definition by type.

    Args:
        tool_type: Tool type enum

    Returns:
        Tool definition if found, None otherwise
    """
    for tool in HUNTER_TOOLS:
        if tool.type == tool_type:
            return tool
    return None
