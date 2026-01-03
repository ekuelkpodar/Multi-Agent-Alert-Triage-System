"""Decision data models."""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DecisionDisposition(str, Enum):
    """Final disposition decisions."""

    AUTO_CLEAR = "AUTO_CLEAR"
    ESCALATE_L2 = "ESCALATE_L2"
    ESCALATE_L3 = "ESCALATE_L3"
    ESCALATE_SAR = "ESCALATE_SAR"
    BLOCK_TRANSACTION = "BLOCK_TRANSACTION"


class EscalationPriority(str, Enum):
    """Priority for escalated alerts."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class DecisionFactors(BaseModel):
    """Factors contributing to the decision."""

    primary_factors: List[str] = Field(default_factory=list)
    supporting_factors: List[str] = Field(default_factory=list)
    contrary_evidence: List[str] = Field(default_factory=list)
    uncertainty_factors: List[str] = Field(default_factory=list)


class EscalationDetails(BaseModel):
    """Details for escalated alerts."""

    requires_human_review: bool
    escalation_reason: str
    priority: EscalationPriority
    suggested_reviewer: Optional[str] = None
    estimated_complexity: Optional[str] = None


class RecommendedAction(BaseModel):
    """Recommended action item."""

    action: str
    priority: int
    rationale: str
    deadline: Optional[datetime] = None


class Documentation(BaseModel):
    """Documentation requirements for the decision."""

    sar_filing_considerations: List[str] = Field(default_factory=list)
    customer_communication_needed: bool = False
    account_restrictions: List[str] = Field(default_factory=list)
    follow_up_monitoring: Optional[str] = None


class AgentContribution(BaseModel):
    """Contribution from a specific agent."""

    agent_name: str
    processing_time_ms: int
    confidence: float = Field(ge=0.0, le=1.0)
    output_summary: str
    warnings: List[str] = Field(default_factory=list)


class Decision(BaseModel):
    """Final decision output from the system."""

    alert_id: str
    disposition: DecisionDisposition
    confidence_score: float = Field(ge=0.0, le=1.0)
    rationale: str
    risk_score: int = Field(ge=0, le=100)

    # Supporting evidence
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    regulatory_citations: List[str] = Field(default_factory=list)

    # Agent contributions
    agent_contributions: Dict[str, AgentContribution] = Field(default_factory=dict)

    # Decision factors
    decision_factors: DecisionFactors

    # Escalation details
    escalation_details: Optional[EscalationDetails] = None

    # Recommended actions
    recommended_actions: List[RecommendedAction] = Field(default_factory=list)

    # Documentation
    documentation: Documentation = Field(default_factory=Documentation)

    # Audit trail
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    processing_time_ms: int
    requires_human_review: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    system_version: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "550e8400-e29b-41d4-a716-446655440000",
                "disposition": "ESCALATE_L2",
                "confidence_score": 0.78,
                "rationale": "Entity matched OFAC SDN list with 92% confidence. Further investigation needed to confirm identity match.",
                "risk_score": 75,
                "decision_factors": {
                    "primary_factors": ["High OFAC match score", "Jurisdiction risk"],
                    "supporting_factors": ["Transaction pattern anomaly"],
                    "contrary_evidence": ["Different date of birth"],
                    "uncertainty_factors": ["Limited beneficial ownership data"]
                },
                "requires_human_review": True,
                "processing_time_ms": 2847
            }
        }
