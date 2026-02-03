"""Complexity assessment service."""

import re
from typing import Dict

from app.domain.value_objects.distillation import ComplexityLevel, Intent


class ComplexityAssessor:
    """Assess request complexity to determine processing needs."""

    # Intents that are always trivial
    TRIVIAL_INTENTS = {
        Intent.GREETING,
        Intent.SMALL_TALK,
        Intent.PRICE_CHECK,
        Intent.GAS_CHECK,
        Intent.BALANCE_CHECK,
    }

    # Intents that are complex by default
    COMPLEX_INTENTS = {
        Intent.RISK_ASSESSMENT,
        Intent.STRATEGY_ADVICE,
        Intent.PORTFOLIO_ANALYSIS,
    }

    def assess(self, text: str, intent: Intent) -> ComplexityLevel:
        """
        Determine complexity level of request.

        Args:
            text: User query text
            intent: Classified intent

        Returns:
            ComplexityLevel
        """
        # Check intent-based rules first
        if intent in self.TRIVIAL_INTENTS:
            return ComplexityLevel.TRIVIAL

        if intent in self.COMPLEX_INTENTS:
            return ComplexityLevel.COMPLEX

        # Analyze text factors
        factors = {
            "token_count": len(text.split()),
            "question_count": text.count("?"),
            "requires_calculation": self._needs_calculation(text),
            "requires_comparison": self._needs_comparison(text),
            "multi_step": self._is_multi_step(text),
            "requires_tools": self._needs_tools(intent),
            "requires_context": self._needs_context(text),
        }

        # Calculate complexity score
        score = self._calculate_complexity_score(factors)

        if score < 0.2:
            return ComplexityLevel.TRIVIAL
        elif score < 0.4:
            return ComplexityLevel.SIMPLE
        elif score < 0.6:
            return ComplexityLevel.MODERATE
        elif score < 0.8:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.EXPERT

    def _needs_calculation(self, text: str) -> bool:
        """Check if query requires calculations."""
        calc_keywords = [
            r"\bcalculate\b",
            r"\bcompute\b",
            r"\bhow much (would|will)",
            r"\bimpermanent loss\b",
            r"\breturn\b",
            r"\bprofit\b",
        ]
        return any(re.search(pattern, text.lower()) for pattern in calc_keywords)

    def _needs_comparison(self, text: str) -> bool:
        """Check if query requires comparisons."""
        comp_keywords = [
            r"\bcompare\b",
            r"\bvs\b",
            r"\bbetter\b",
            r"\bbest\b",
            r"\bwhich\b",
            r"\bdifference\b",
        ]
        return any(re.search(pattern, text.lower()) for pattern in comp_keywords)

    def _is_multi_step(self, text: str) -> bool:
        """Check if query has multiple steps."""
        multi_step_indicators = [
            r"\b(then|after|next|first|second|finally)\b",
            r"\band (then|also)\b",
            text.count(".") > 1,
            text.count(";") > 0,
        ]
        return (
            sum(
                1
                for indicator in multi_step_indicators
                if (isinstance(indicator, bool) and indicator)
                or (
                    isinstance(indicator, re.Pattern)
                    and re.search(indicator, text.lower())
                )
            )
            >= 2
        )

    def _needs_tools(self, intent: Intent) -> bool:
        """Check if intent requires tool usage."""
        tool_intents = {
            Intent.SWAP_REQUEST,
            Intent.STAKE_REQUEST,
            Intent.LEND_REQUEST,
            Intent.BORROW_REQUEST,
            Intent.BRIDGE_REQUEST,
            Intent.PORTFOLIO_ANALYSIS,
        }
        return intent in tool_intents

    def _needs_context(self, text: str) -> bool:
        """Check if query needs additional context."""
        context_keywords = [
            r"\bmy\b",
            r"\bcurrent\b",
            r"\brecent\b",
            r"\blast (week|month|year)\b",
            r"\bhistorical\b",
        ]
        return any(re.search(pattern, text.lower()) for pattern in context_keywords)

    def _calculate_complexity_score(self, factors: Dict) -> float:
        """
        Calculate overall complexity score from factors.

        Weights:
        - token_count: 0.1
        - question_count: 0.1
        - requires_calculation: 0.15
        - requires_comparison: 0.15
        - multi_step: 0.2
        - requires_tools: 0.15
        - requires_context: 0.15
        """
        score = 0.0

        # Token count (normalized, max 100 tokens = 1.0)
        score += min(factors["token_count"] / 100, 1.0) * 0.1

        # Question count (normalized, max 3 questions = 1.0)
        score += min(factors["question_count"] / 3, 1.0) * 0.1

        # Boolean factors
        score += float(factors["requires_calculation"]) * 0.15
        score += float(factors["requires_comparison"]) * 0.15
        score += float(factors["multi_step"]) * 0.2
        score += float(factors["requires_tools"]) * 0.15
        score += float(factors["requires_context"]) * 0.15

        return score
