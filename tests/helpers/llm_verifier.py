"""
LLM response verifier for validating AI-generated content.

Provides utilities for:
- Validating response structure
- Checking content relevance to queries
- Verifying risk disclaimers for financial advice
- Validating DeFi data formatting

Usage:
    from tests.helpers.llm_verifier import verify_response_structure, LLMVerifier

    # Verify response structure
    assert verify_response_structure(response)

    # Check content relevance
    score = verify_content_relevance(query, response_content)
    assert score > 0.5

    # Verify risk disclaimers present
    assert verify_risk_disclaimers(response_content)
"""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMVerificationResult:
    """Result of LLM response verification."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    metrics: dict[str, Any]

    @property
    def passed(self) -> bool:
        """Check if verification passed with no errors."""
        return self.is_valid and len(self.errors) == 0


class LLMVerifier:
    """
    Verifier for LLM response quality and structure.

    Validates that AI-generated responses meet quality standards
    for structure, relevance, safety, and formatting.
    """

    # Required fields in LLM response
    REQUIRED_RESPONSE_FIELDS = {"content", "agent_type"}
    OPTIONAL_RESPONSE_FIELDS = {"confidence", "sources", "metadata"}

    # Valid agent types
    VALID_AGENT_TYPES = {
        "trading",
        "research",
        "portfolio",
        "risk",
        "general",
        "hunter",
        "yield",
    }

    # Financial risk disclaimer patterns
    RISK_DISCLAIMER_PATTERNS = [
        r"not\s+financial\s+advice",
        r"do\s+your\s+own\s+research",
        r"dyor",
        r"risk\s+of\s+loss",
        r"past\s+performance",
        r"consult\s+.*professional",
        r"at\s+your\s+own\s+risk",
        r"disclaimer",
        r"this\s+is\s+not\s+.*recommendation",
    ]

    # DeFi data field patterns
    DEFI_DATA_FIELDS = {
        "tvl": (int, float),
        "apy": (int, float),
        "apr": (int, float),
        "risk_score": (int, float),
        "price": (int, float),
        "volume": (int, float),
        "liquidity": (int, float),
        "market_cap": (int, float),
    }

    # Minimum content length (characters)
    MIN_CONTENT_LENGTH = 10

    # Maximum content length (characters)
    MAX_CONTENT_LENGTH = 50000

    def verify_response_structure(self, response: dict) -> LLMVerificationResult:
        """
        Verify LLM response has required structure.

        Args:
            response: LLM response dictionary

        Returns:
            LLMVerificationResult with validation details
        """
        errors = []
        warnings = []
        metrics = {}

        # Handle empty/None response
        if not response:
            return LLMVerificationResult(
                is_valid=False,
                errors=["Response is empty or None"],
                warnings=[],
                metrics={},
            )

        if not isinstance(response, dict):
            return LLMVerificationResult(
                is_valid=False,
                errors=[f"Response must be a dict, got {type(response)}"],
                warnings=[],
                metrics={},
            )

        # Check for content in various locations
        content = response.get("content", "")
        if not content and "message" in response:
            content = response.get("message", "")
        if not content and "text" in response:
            content = response.get("text", "")

        if not content:
            errors.append("Content is empty")
        elif len(content) < self.MIN_CONTENT_LENGTH:
            errors.append(
                f"Content too short: {len(content)} < {self.MIN_CONTENT_LENGTH}"
            )
        elif len(content) > self.MAX_CONTENT_LENGTH:
            warnings.append(
                f"Content very long: {len(content)} > {self.MAX_CONTENT_LENGTH}"
            )

        metrics["content_length"] = len(content) if content else 0

        # Check agent type (optional)
        agent_type = response.get("agent_type", "")
        if agent_type:
            agent_type_lower = agent_type.lower()
            if agent_type_lower not in self.VALID_AGENT_TYPES:
                warnings.append(f"Unknown agent type: {agent_type}")
            metrics["agent_type"] = agent_type

        # Check confidence if present
        confidence = response.get("confidence")
        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                warnings.append(f"Confidence must be numeric, got {type(confidence)}")
            elif not 0 <= confidence <= 1:
                warnings.append(f"Confidence out of range [0,1]: {confidence}")
            metrics["confidence"] = confidence

        is_valid = len(errors) == 0
        return LLMVerificationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )

    def verify_content_relevance(
        self,
        query: str,
        response_content: str,
        threshold: float = 0.3,
    ) -> float:
        """
        Measure relevance of response content to query.

        Uses simple keyword overlap scoring.
        For production, consider using embeddings or LLM evaluation.

        Args:
            query: User query
            response_content: LLM response content
            threshold: Minimum relevance score (0-1)

        Returns:
            Relevance score between 0 and 1
        """
        if not query or not response_content:
            return 0.0

        # Normalize text
        query_lower = query.lower()
        content_lower = response_content.lower()

        # Extract keywords (simple tokenization)
        query_words = set(re.findall(r"\b\w{3,}\b", query_lower))
        content_words = set(re.findall(r"\b\w{3,}\b", content_lower))

        if not query_words:
            return 0.5  # No meaningful query words

        # Calculate overlap
        overlap = len(query_words & content_words)
        relevance = overlap / len(query_words)

        # Boost for longer matching phrases
        for word in query_words:
            if word in content_lower:
                relevance = min(1.0, relevance + 0.1)

        return min(1.0, relevance)

    def verify_risk_disclaimers(self, content: str) -> bool:
        """
        Check if content contains appropriate risk disclaimers.

        Args:
            content: Response content to check

        Returns:
            True if risk disclaimers are present
        """
        if not content:
            return False

        content_lower = content.lower()

        for pattern in self.RISK_DISCLAIMER_PATTERNS:
            if re.search(pattern, content_lower):
                return True

        return False

    def verify_defi_data_format(self, data: dict) -> LLMVerificationResult:
        """
        Validate DeFi data has proper formatting.

        Args:
            data: DeFi data dictionary

        Returns:
            LLMVerificationResult with validation details
        """
        errors = []
        warnings = []
        metrics = {}

        if not isinstance(data, dict):
            return LLMVerificationResult(
                is_valid=False,
                errors=[f"Data must be a dict, got {type(data)}"],
                warnings=[],
                metrics={},
            )

        # Check known DeFi fields
        for field, expected_types in self.DEFI_DATA_FIELDS.items():
            if field in data:
                value = data[field]
                if value is not None and not isinstance(value, expected_types):
                    errors.append(
                        f"Field '{field}' should be {expected_types}, got {type(value)}"
                    )
                elif isinstance(value, (int, float)):
                    # Validate ranges for known fields
                    if field in ("apy", "apr") and not -100 <= value <= 10000:
                        warnings.append(f"Unusual {field} value: {value}%")
                    elif field == "risk_score" and not 0 <= value <= 10:
                        warnings.append(f"Risk score out of range [0,10]: {value}")
                    elif field in ("tvl", "volume", "liquidity") and value < 0:
                        errors.append(f"Negative value for {field}: {value}")

                    metrics[field] = value

        # Check for required identifiers
        if "protocol_name" not in data and "token_symbol" not in data:
            warnings.append("Missing protocol_name or token_symbol identifier")

        is_valid = len(errors) == 0
        return LLMVerificationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )

    def verify_financial_advice_safety(self, content: str) -> LLMVerificationResult:
        """
        Verify that financial-related content is appropriately cautious.

        Args:
            content: Response content

        Returns:
            LLMVerificationResult with safety assessment
        """
        errors = []
        warnings = []
        metrics = {}

        if not content:
            return LLMVerificationResult(
                is_valid=False,
                errors=["Empty content"],
                warnings=[],
                metrics={},
            )

        content_lower = content.lower()

        # Check for overly confident language
        confident_phrases = [
            r"guaranteed\s+return",
            r"risk\s*-?\s*free",
            r"100%\s+safe",
            r"can't\s+lose",
            r"will\s+definitely",
            r"absolutely\s+certain",
        ]

        for phrase in confident_phrases:
            if re.search(phrase, content_lower):
                errors.append(f"Overconfident language detected: '{phrase}'")

        # Check for disclaimers on financial content
        financial_indicators = [
            "invest",
            "buy",
            "sell",
            "trade",
            "yield",
            "apy",
            "return",
        ]

        has_financial_content = any(
            ind in content_lower for ind in financial_indicators
        )

        if has_financial_content:
            metrics["has_financial_content"] = True
            if not self.verify_risk_disclaimers(content):
                warnings.append("Financial content without risk disclaimers")
        else:
            metrics["has_financial_content"] = False

        is_valid = len(errors) == 0
        return LLMVerificationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metrics=metrics,
        )


# Module-level verifier instance
_verifier = LLMVerifier()


def verify_response_structure(response: dict) -> bool:
    """
    Verify LLM response has required structure.

    Args:
        response: LLM response dictionary

    Returns:
        True if structure is valid (has content)
    """
    if not response:
        return False
    if not isinstance(response, dict):
        return False
    # Check for content in common locations
    content = response.get("content") or response.get("message") or response.get("text")
    return bool(content)


def verify_content_relevance(
    query: str,
    response_content: str,
    threshold: float = 0.3,
) -> float:
    """
    Measure relevance of response content to query.

    Args:
        query: User query
        response_content: LLM response content
        threshold: Minimum relevance score

    Returns:
        Relevance score between 0 and 1
    """
    return _verifier.verify_content_relevance(query, response_content, threshold)


def verify_risk_disclaimers(content: str) -> bool:
    """
    Check if content contains appropriate risk disclaimers.

    Args:
        content: Response content to check

    Returns:
        True if risk disclaimers are present
    """
    return _verifier.verify_risk_disclaimers(content)


def verify_defi_data_format(data: dict) -> bool:
    """
    Validate DeFi data has proper formatting.

    Args:
        data: DeFi data dictionary

    Returns:
        True if data format is valid
    """
    if not isinstance(data, dict):
        return False

    # Check TVL type if present
    if "tvl" in data:
        tvl = data["tvl"]
        if tvl is not None and not isinstance(tvl, (int, float)):
            return False
        if isinstance(tvl, (int, float)) and tvl < 0:
            return False

    # Check APY range if present
    if "apy" in data:
        apy = data["apy"]
        if apy is not None and not isinstance(apy, (int, float)):
            return False
        if isinstance(apy, (int, float)) and apy < -100:
            return False

    return True


def get_full_verification(response: dict, query: str | None = None) -> LLMVerificationResult:
    """
    Perform full verification of LLM response.

    Args:
        response: LLM response dictionary
        query: Original user query (optional)

    Returns:
        Comprehensive LLMVerificationResult
    """
    errors = []
    warnings = []
    metrics = {}

    # Structure verification
    structure_result = _verifier.verify_response_structure(response)
    errors.extend(structure_result.errors)
    warnings.extend(structure_result.warnings)
    metrics.update(structure_result.metrics)

    # Content relevance if query provided
    if query and response.get("content"):
        relevance = _verifier.verify_content_relevance(query, response["content"])
        metrics["relevance_score"] = relevance
        if relevance < 0.3:
            warnings.append(f"Low relevance score: {relevance:.2f}")

    # Safety verification for content
    if response.get("content"):
        safety_result = _verifier.verify_financial_advice_safety(response["content"])
        errors.extend(safety_result.errors)
        warnings.extend(safety_result.warnings)
        metrics.update(safety_result.metrics)

    is_valid = len(errors) == 0
    return LLMVerificationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        metrics=metrics,
    )
