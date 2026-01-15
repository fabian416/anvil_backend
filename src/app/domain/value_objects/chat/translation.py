"""
Chat translation value objects.

Enterprise-grade multi-language support with technical term preservation.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime, UTC
from enum import Enum


class SupportedLanguage(Enum):
    """Supported languages for translation."""

    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    JAPANESE = "ja"
    KOREAN = "ko"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    RUSSIAN = "ru"
    ARABIC = "ar"


class TranslationMode(Enum):
    """Translation display modes."""

    REPLACE = "replace"  # Replace original with translation
    SIDE_BY_SIDE = "side_by_side"  # Show both original and translation
    INLINE = "inline"  # Show translation inline with original
    POPUP = "popup"  # Show translation on hover/click


@dataclass(frozen=True)
class TranslationResult:
    """Result of a translation operation."""

    original_text: str
    translated_text: str
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    confidence_score: float  # 0.0 to 1.0
    detected_language: Optional[SupportedLanguage] = None
    preserved_terms: List[str] = None  # Technical terms not translated
    translation_time_ms: int = 0

    def __post_init__(self):
        """Initialize mutable fields with defaults."""
        if self.preserved_terms is None:
            object.__setattr__(self, "preserved_terms", [])

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "source_language": self.source_language.value,
            "target_language": self.target_language.value,
            "confidence_score": self.confidence_score,
            "detected_language": self.detected_language.value if self.detected_language else None,
            "preserved_terms": self.preserved_terms,
            "translation_time_ms": self.translation_time_ms,
        }


@dataclass(frozen=True)
class PreservedTermsConfig:
    """Configuration for preserving technical terms during translation."""

    # DeFi protocol names (never translate)
    protocols: List[str] = None

    # Token symbols (never translate)
    tokens: List[str] = None

    # Technical terms (preserve in original language)
    technical_terms: List[str] = None

    # Wallet addresses (never translate)
    preserve_addresses: bool = True

    # Transaction hashes (never translate)
    preserve_tx_hashes: bool = True

    # Code snippets (never translate)
    preserve_code: bool = True

    def __post_init__(self):
        """Initialize with default DeFi terms."""
        if self.protocols is None:
            object.__setattr__(self, "protocols", [
                "Aave", "Compound", "Curve", "Uniswap", "MakerDAO",
                "Lido", "Morpho", "Balancer", "Convex", "Yearn",
                "SushiSwap", "PancakeSwap", "QuickSwap",
            ])

        if self.tokens is None:
            object.__setattr__(self, "tokens", [
                "ETH", "WETH", "BTC", "WBTC", "USDC", "USDT", "DAI",
                "stETH", "wstETH", "CRV", "AAVE", "UNI", "COMP",
                "LINK", "SNX", "MKR", "YFI", "BAL", "CVX",
            ])

        if self.technical_terms is None:
            object.__setattr__(self, "technical_terms", [
                "APY", "APR", "TVL", "DeFi", "liquidity pool",
                "smart contract", "gas fee", "slippage", "impermanent loss",
                "yield farming", "staking", "governance", "oracle",
                "flash loan", "DEX", "CEX", "collateral",
            ])

    def should_preserve(self, term: str) -> bool:
        """Check if a term should be preserved."""
        term_lower = term.lower()

        # Check protocols
        if any(p.lower() == term_lower for p in self.protocols):
            return True

        # Check tokens
        if any(t.lower() == term_lower for t in self.tokens):
            return True

        # Check technical terms
        if any(tt.lower() in term_lower for tt in self.technical_terms):
            return True

        return False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "protocols": self.protocols,
            "tokens": self.tokens,
            "technical_terms": self.technical_terms,
            "preserve_addresses": self.preserve_addresses,
            "preserve_tx_hashes": self.preserve_tx_hashes,
            "preserve_code": self.preserve_code,
        }


@dataclass(frozen=True)
class TranslationQuality:
    """Translation quality metrics."""

    fluency_score: float  # 0.0 to 1.0
    adequacy_score: float  # 0.0 to 1.0
    terminology_accuracy: float  # 0.0 to 1.0
    context_preservation: float  # 0.0 to 1.0
    overall_quality: float  # 0.0 to 1.0

    @classmethod
    def from_scores(
        cls,
        fluency: float,
        adequacy: float,
        terminology: float,
        context: float,
    ) -> "TranslationQuality":
        """Create quality metrics with calculated overall score."""
        overall = (fluency + adequacy + terminology + context) / 4
        return cls(
            fluency_score=fluency,
            adequacy_score=adequacy,
            terminology_accuracy=terminology,
            context_preservation=context,
            overall_quality=overall,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "fluency_score": self.fluency_score,
            "adequacy_score": self.adequacy_score,
            "terminology_accuracy": self.terminology_accuracy,
            "context_preservation": self.context_preservation,
            "overall_quality": self.overall_quality,
        }


@dataclass
class UserLanguagePreference:
    """User's language preferences."""

    user_id: str
    primary_language: SupportedLanguage
    auto_translate_enabled: bool = False
    translation_mode: TranslationMode = TranslationMode.SIDE_BY_SIDE
    preserve_technical_terms: bool = True
    show_original_on_hover: bool = True
    preferred_terms_config: Optional[PreservedTermsConfig] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        """Initialize timestamps."""
        if self.created_at is None:
            self.created_at = datetime.now(UTC)
        if self.updated_at is None:
            self.updated_at = datetime.now(UTC)
        if self.preferred_terms_config is None:
            self.preferred_terms_config = PreservedTermsConfig()

    def enable_auto_translate(self) -> None:
        """Enable automatic translation."""
        self.auto_translate_enabled = True
        self.updated_at = datetime.now(UTC)

    def disable_auto_translate(self) -> None:
        """Disable automatic translation."""
        self.auto_translate_enabled = False
        self.updated_at = datetime.now(UTC)

    def set_translation_mode(self, mode: TranslationMode) -> None:
        """Set translation display mode."""
        self.translation_mode = mode
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "primary_language": self.primary_language.value,
            "auto_translate_enabled": self.auto_translate_enabled,
            "translation_mode": self.translation_mode.value,
            "preserve_technical_terms": self.preserve_technical_terms,
            "show_original_on_hover": self.show_original_on_hover,
            "preferred_terms_config": self.preferred_terms_config.to_dict() if self.preferred_terms_config else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
