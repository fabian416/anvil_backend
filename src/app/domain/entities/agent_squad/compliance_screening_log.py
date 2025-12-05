"""
Compliance Screening Log entity - AML/KYC screening results.
"""

from dataclasses import dataclass
from typing import Any
from decimal import Decimal
import uuid

from app.domain.entities.base import Entity
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.wallet_address import WalletAddress
from app.domain.value_objects.created_at import CreatedAt


@dataclass(eq=False, kw_only=True)
class ComplianceScreeningLogId:
    """Compliance Screening Log identifier."""
    value: uuid.UUID
    
    def __init__(self, value: uuid.UUID | str):
        if isinstance(value, str):
            value = uuid.UUID(value)
        object.__setattr__(self, 'value', value)
    
    def __hash__(self) -> int:
        return hash(self.value)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ComplianceScreeningLogId):
            return False
        return self.value == other.value
    
    def __str__(self) -> str:
        return str(self.value)


class ScreeningResult:
    """Screening result enum."""
    APPROVED = "approved"
    BLOCKED = "blocked"
    REVIEW = "review"


class OFACStatus:
    """OFAC sanction status."""
    CLEAR = "clear"
    SANCTIONED = "sanctioned"


class PEPStatus:
    """Politically Exposed Person status."""
    CLEAR = "clear"
    DETECTED = "detected"


@dataclass(eq=False, kw_only=True)
class ComplianceScreeningLog(Entity[ComplianceScreeningLogId]):
    """
    Compliance screening log: AML/KYC screening results.
    
    Enterprise feature for regulatory compliance:
    - OFAC sanction checks
    - PEP (Politically Exposed Person) detection
    - Mixer exposure analysis (Tornado Cash, etc.)
    - High-risk source detection
    - Risk scoring (0-100)
    """
    user_id: UserId
    wallet_address: WalletAddress
    risk_score: int  # 0-100 (higher = riskier)
    ofac_status: str  # "clear" or "sanctioned"
    pep_status: str  # "clear" or "detected"
    mixer_exposure_pct: float  # 0.0-100.0 (% of funds from mixers)
    high_risk_sources_pct: float  # 0.0-100.0 (% from high-risk sources)
    screening_result: str  # "approved", "blocked", "review"
    screening_data: dict[str, Any]  # Full Chainalysis/TRM Labs response
    created_at: CreatedAt
    
    @classmethod
    def create(
        cls,
        user_id: UserId,
        wallet_address: WalletAddress,
        risk_score: int,
        ofac_status: str,
        pep_status: str,
        mixer_exposure_pct: float,
        high_risk_sources_pct: float,
        screening_result: str,
        screening_data: dict[str, Any],
    ) -> "ComplianceScreeningLog":
        """Create new compliance screening log."""
        return cls(
            id_=ComplianceScreeningLogId(uuid.uuid4()),
            user_id=user_id,
            wallet_address=wallet_address,
            risk_score=risk_score,
            ofac_status=ofac_status,
            pep_status=pep_status,
            mixer_exposure_pct=mixer_exposure_pct,
            high_risk_sources_pct=high_risk_sources_pct,
            screening_result=screening_result,
            screening_data=screening_data,
            created_at=CreatedAt.now(),
        )
    
    @property
    def is_high_risk(self) -> bool:
        """Check if wallet is high-risk (score >= 70)."""
        return self.risk_score >= 70
    
    @property
    def is_sanctioned(self) -> bool:
        """Check if wallet is on OFAC sanction list."""
        return self.ofac_status == OFACStatus.SANCTIONED
    
    @property
    def is_pep(self) -> bool:
        """Check if wallet owner is a Politically Exposed Person."""
        return self.pep_status == PEPStatus.DETECTED
    
    @property
    def has_mixer_exposure(self) -> bool:
        """Check if wallet has significant mixer exposure (>10%)."""
        return self.mixer_exposure_pct > 10.0
    
    @property
    def is_approved(self) -> bool:
        """Check if screening result is approved."""
        return self.screening_result == ScreeningResult.APPROVED
    
    @property
    def is_blocked(self) -> bool:
        """Check if screening result is blocked."""
        return self.screening_result == ScreeningResult.BLOCKED
    
    @property
    def requires_manual_review(self) -> bool:
        """Check if screening requires manual compliance review."""
        return self.screening_result == ScreeningResult.REVIEW
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "id": str(self.id_),
            "user_id": str(self.user_id.value),
            "wallet_address": str(self.wallet_address.value),
            "risk_score": self.risk_score,
            "ofac_status": self.ofac_status,
            "pep_status": self.pep_status,
            "mixer_exposure_pct": self.mixer_exposure_pct,
            "high_risk_sources_pct": self.high_risk_sources_pct,
            "screening_result": self.screening_result,
            "screening_data": self.screening_data,
            "created_at": self.created_at.value.isoformat(),
        }
