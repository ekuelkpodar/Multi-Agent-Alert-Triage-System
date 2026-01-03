"""Risk assessment models."""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk level categorization."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class ComponentScores(BaseModel):
    """Individual risk component scores."""

    customer_risk: int = Field(ge=0, le=100)
    geographic_risk: int = Field(ge=0, le=100)
    transaction_risk: int = Field(ge=0, le=100)
    adverse_media_risk: int = Field(ge=0, le=100)
    network_risk: int = Field(ge=0, le=100)


class RiskFactors(BaseModel):
    """Risk factors identified."""

    mitigating: List[str] = Field(default_factory=list)
    aggravating: List[str] = Field(default_factory=list)


class MLInsights(BaseModel):
    """Machine learning model insights."""

    anomaly_score: float = Field(ge=0.0, le=1.0)
    pattern_detection: str
    model_confidence: float = Field(ge=0.0, le=1.0)
    similar_cases: List[str] = Field(default_factory=list)
    feature_importance: Dict[str, float] = Field(default_factory=dict)


class RegulatoryCompliance(BaseModel):
    """Regulatory compliance assessment."""

    applicable_frameworks: List[str] = Field(default_factory=list)
    compliance_concerns: List[str] = Field(default_factory=list)
    regulatory_citations: List[str] = Field(default_factory=list)
    red_flags_identified: List[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Comprehensive risk assessment output."""

    overall_risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    component_breakdown: ComponentScores
    risk_narrative: str

    # Regulatory context
    regulatory_context: RegulatoryCompliance

    # ML insights
    ml_insights: Optional[MLInsights] = None

    # Risk factors
    risk_factors: RiskFactors

    # Scoring metadata
    scoring_methodology: str = "Weighted Multi-Factor"
    confidence: float = Field(ge=0.0, le=1.0)
    calculation_timestamp: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "overall_risk_score": 75,
                "risk_level": "HIGH",
                "component_breakdown": {
                    "customer_risk": 65,
                    "geographic_risk": 80,
                    "transaction_risk": 70,
                    "adverse_media_risk": 85,
                    "network_risk": 55
                },
                "risk_narrative": "High risk due to sanctions match and high-risk jurisdiction. Customer has adverse media related to financial fraud.",
                "regulatory_context": {
                    "applicable_frameworks": ["BSA/AML", "OFAC"],
                    "compliance_concerns": ["Potential sanctions violation"],
                    "regulatory_citations": ["31 CFR 1020.220"]
                },
                "risk_factors": {
                    "mitigating": ["Long-standing customer relationship", "No previous violations"],
                    "aggravating": ["High-risk jurisdiction", "Adverse media", "PEP status"]
                },
                "confidence": 0.87
            }
        }
