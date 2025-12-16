"""Trend Analysis Template

Comprehensive trend identification and analysis using multiple timeframes,
indicators, and market structure to determine trend strength and direction.
"""

from uuid import UUID

from app.domain.entities.chat.conversation_template import (
    AgentStep,
    ConversationTemplate,
    InputSpec,
)


def create_trend_analysis_template(created_by: UUID) -> ConversationTemplate:
    """Create trend analysis template.

    Multi-timeframe trend analysis including:
    - Trend identification across timeframes
    - Trend strength measurement
    - Market structure analysis (HH/HL or LH/LL)
    - Key support/resistance levels
    - Trend continuation vs reversal signals
    - Trading recommendations aligned with trend

    Args:
        created_by: User ID creating the template

    Returns:
        Configured ConversationTemplate instance
    """

    agent_sequence = [
        AgentStep(
            agent_name="@technical-analyst",
            prompt_template=(
                "Analyze price action structure for {{asset_symbol}}: "
                "On primary timeframe {{timeframe}}: "
                "1. Swing Point Analysis: "
                "   - Identify last 10 swing highs and lows "
                "   - Determine sequence: "
                "     * Higher Highs + Higher Lows = Uptrend "
                "     * Lower Highs + Lower Lows = Downtrend "
                "     * Mixed = Ranging/Choppy "
                "2. Market Structure: "
                "   - Break of structure points "
                "   - Change of character (CHoCH) "
                "   - Order blocks and fair value gaps "
                "3. Current Phase: "
                "   - Accumulation (basing after downtrend) "
                "   - Markup (sustained uptrend) "
                "   - Distribution (topping after uptrend) "
                "   - Markdown (sustained downtrend) "
                "Classify current trend and phase"
            ),
            depends_on=[],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "swing_structure",
                "market_structure",
                "trend_classification",
                "market_phase",
            ],
        ),
        AgentStep(
            agent_name="@technical-analyst",
            prompt_template=(
                "Perform multi-timeframe trend alignment: "
                "For {{asset_symbol}}, analyze: "
                "1. Higher Timeframe ({{higher_timeframe}}): "
                "   - Trend direction "
                "   - Trend strength "
                "   - Key S/R levels "
                "2. Primary Timeframe ({{timeframe}}): "
                "   - Trend direction "
                "   - Current from {{trend_classification}} "
                "3. Lower Timeframe ({{lower_timeframe}}): "
                "   - Trend direction "
                "   - Entry timing signals "
                "Alignment Analysis: "
                "- All aligned (same direction): Strong trend, high confidence "
                "- Primary + Higher aligned: Moderate confidence "
                "- Conflicting: Low confidence, wait for alignment "
                "Create timeframe alignment matrix"
            ),
            depends_on=[0],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "htf_trend",
                "primary_trend",
                "ltf_trend",
                "alignment_score",
                "timeframe_matrix",
            ],
        ),
        AgentStep(
            agent_name="@technical-analyst",
            prompt_template=(
                "Calculate trend strength indicators: "
                "For {{asset_symbol}} on {{timeframe}}: "
                "1. ADX (Average Directional Index): "
                "   - ADX value: <20 = weak/ranging, 20-40 = trending, >40 = strong trend "
                "   - +DI vs -DI: Which is stronger "
                "2. Moving Average Analysis: "
                "   - 20/50/200 EMA alignment "
                "   - Price position relative to EMAs "
                "   - MA spacing (wider = stronger trend) "
                "3. Slope Analysis: "
                "   - Linear regression slope "
                "   - R-squared (how linear the trend) "
                "4. Momentum Oscillators: "
                "   - MACD: Above/below zero, histogram expansion "
                "   - RSI: Sustained >50 (up) or <50 (down) "
                "   - Rate of Change (ROC) "
                "Combine into trend strength score (0-100)"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=[
                "adx_reading",
                "ma_alignment",
                "momentum_indicators",
                "trend_strength_score",
            ],
        ),
        AgentStep(
            agent_name="@market-analyst",
            prompt_template=(
                "Identify key support and resistance levels: "
                "For {{asset_symbol}}: "
                "1. Horizontal Levels: "
                "   - Major support zones (historical bounces) "
                "   - Major resistance zones (historical rejections) "
                "   - Round numbers and psychological levels "
                "2. Dynamic Levels: "
                "   - Key moving averages (50/200 MA) "
                "   - Trendlines (connecting swing points) "
                "   - Channels (parallel to trendlines) "
                "3. Volume-Based Levels: "
                "   - High volume nodes (VPOC) "
                "   - Low volume areas (LVN - potential fast moves) "
                "4. Fibonacci Levels: "
                "   - Retracement levels from recent swing "
                "   - Extension levels for targets "
                "Rank levels by significance and proximity to price"
            ),
            depends_on=[0],
            parallel_execution=True,
            timeout_seconds=45,
            outputs=[
                "support_levels",
                "resistance_levels",
                "dynamic_levels",
                "level_significance",
            ],
        ),
        AgentStep(
            agent_name="@risk-analyst",
            prompt_template=(
                "Identify trend continuation vs reversal signals: "
                "Current trend: {{trend_classification}} "
                "Continuation Signals (trend likely to continue): "
                "1. Pullbacks to support in uptrend (buy dip) "
                "   - Pullback to {{support_levels}} "
                "   - Holds above key MA "
                "   - RSI reset to 40-50 zone "
                "2. Rallies to resistance in downtrend (sell rally) "
                "   - Rally to {{resistance_levels}} "
                "   - Rejects at key MA "
                "   - RSI resets to 50-60 zone "
                "Reversal Signals (trend may reverse): "
                "1. Divergences: RSI/MACD diverging from price "
                "2. Failed breakouts/breakdowns "
                "3. Change in market structure (break of trendline) "
                "4. Exhaustion: Climactic volume, extended RSI "
                "5. Higher timeframe resistance/support "
                "Current signals present: List all active signals"
            ),
            depends_on=[1, 2, 3],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "continuation_signals",
                "reversal_signals",
                "active_signals",
                "signal_strength",
            ],
        ),
        AgentStep(
            agent_name="@portfolio-analyst",
            prompt_template=(
                "Develop trend-aligned trading recommendations: "
                "Based on: "
                "- Trend: {{trend_classification}} "
                "- Strength: {{trend_strength_score}}/100 "
                "- Alignment: {{alignment_score}} "
                "- Active signals: {{active_signals}} "
                "Recommendations: "
                "STRONG UPTREND (strength >70, aligned timeframes): "
                "- Bias: Long only "
                "- Strategy: Buy pullbacks to {{support_levels}} "
                "- Targets: {{resistance_levels}} "
                "- Stop: Below recent swing low "
                "MODERATE UPTREND (strength 40-70): "
                "- Bias: Long preferred "
                "- Wait for confirmation on pullbacks "
                "- Tighter stops "
                "RANGING (strength <40): "
                "- Bias: Neutral "
                "- Trade range: Buy support, sell resistance "
                "- Breakout watch "
                "DOWNTREND: "
                "- Bias: Short or stay out "
                "- Sell rallies to {{resistance_levels}} "
                "- Targets: {{support_levels}} "
                "POTENTIAL REVERSAL (reversal signals present): "
                "- Wait for confirmation "
                "- Look for: {{reversal_signals}} "
                "- Early entry at reversal or wait for new trend established "
                "Provide specific entry zones and invalidation levels"
            ),
            depends_on=[4],
            parallel_execution=False,
            timeout_seconds=45,
            outputs=[
                "trading_bias",
                "entry_strategy",
                "target_levels",
                "risk_management",
            ],
        ),
        AgentStep(
            agent_name="@product-manager",
            prompt_template=(
                "Create comprehensive trend analysis report: "
                "1. Trend Summary: "
                "   - Asset: {{asset_symbol}} "
                "   - Primary timeframe: {{timeframe}} "
                "   - Trend direction: {{trend_classification}} "
                "   - Trend strength: {{trend_strength_score}}/100 "
                "   - Market phase: {{market_phase}} "
                "2. Market Structure: "
                "   - Swing structure: {{swing_structure}} "
                "   - Recent highs/lows: [list] "
                "   - Break of structure: [if any] "
                "3. Timeframe Alignment: "
                "   - Higher TF ({{higher_timeframe}}): {{htf_trend}} "
                "   - Primary TF ({{timeframe}}): {{primary_trend}} "
                "   - Lower TF ({{lower_timeframe}}): {{ltf_trend}} "
                "   - Alignment: {{alignment_score}}/100 "
                "   - Matrix: {{timeframe_matrix}} "
                "4. Trend Strength Indicators: "
                "   - ADX: {{adx_reading}} "
                "   - MA alignment: {{ma_alignment}} "
                "   - Momentum: {{momentum_indicators}} "
                "   - Overall score: {{trend_strength_score}}/100 "
                "5. Key Levels: "
                "   - Support: {{support_levels}} "
                "   - Resistance: {{resistance_levels}} "
                "   - Dynamic: {{dynamic_levels}} "
                "   - Significance: {{level_significance}} "
                "6. Signals: "
                "   - Continuation: {{continuation_signals}} "
                "   - Reversal: {{reversal_signals}} "
                "   - Active now: {{active_signals}} "
                "7. Trading Plan: "
                "   - Bias: {{trading_bias}} "
                "   - Entry strategy: {{entry_strategy}} "
                "   - Entry zones: [specific prices] "
                "   - Targets: {{target_levels}} "
                "   - Stop loss: [specific price] "
                "   - Risk/reward: 1:X "
                "8. Trend Outlook: "
                "   - Short-term (days): [forecast] "
                "   - Medium-term (weeks): [forecast] "
                "   - Key events to watch: [upcoming catalysts] "
                "   - Invalidation: Trend invalid if [condition]"
            ),
            depends_on=[5],
            parallel_execution=False,
            timeout_seconds=60,
            outputs=[
                "trend_analysis_report",
                "trend_summary",
                "trading_plan",
                "trend_forecast",
            ],
        ),
    ]

    required_inputs = {
        "asset_symbol": InputSpec(
            type="string",
            required=True,
            description="Asset symbol to analyze (e.g., BTC, ETH, LINK)",
        ),
        "timeframe": InputSpec(
            type="string",
            required=False,
            description="Primary analysis timeframe: '1h', '4h', '1d', '1w'",
            default="1d",
        ),
        "higher_timeframe": InputSpec(
            type="string",
            required=False,
            description="Higher timeframe for context (auto: 1 level up from primary)",
            default="auto",
        ),
        "lower_timeframe": InputSpec(
            type="string",
            required=False,
            description="Lower timeframe for entries (auto: 1 level down from primary)",
            default="auto",
        ),
    }

    return ConversationTemplate.create(
        name="Trend Analysis",
        description=(
            "Comprehensive multi-timeframe trend analysis using market structure, "
            "technical indicators, and price action. Identifies trend direction and strength, "
            "analyzes timeframe alignment, locates key support/resistance levels, and provides "
            "trend-aligned trading recommendations with specific entry/exit strategies."
        ),
        category="trading_strategy",
        agent_sequence=agent_sequence,
        required_inputs=required_inputs,
        estimated_duration_seconds=300,  # 5 minutes
        created_by=created_by,
        is_public=True,
        tags=["trading", "trend-analysis", "technical-analysis", "market-structure"],
    )
