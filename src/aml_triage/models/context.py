"""Context building models."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """Event in the timeline."""

    date: datetime
    event: str
    significance: str
    source: Optional[str] = None


class Timeline(BaseModel):
    """Chronological timeline of events."""

    events: List[TimelineEvent] = Field(default_factory=list)
    summary: Optional[str] = None


class Node(BaseModel):
    """Node in relationship graph."""

    node_id: str
    node_type: str
    name: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    """Edge in relationship graph."""

    from_node: str
    to_node: str
    relationship_type: str
    strength: float = Field(ge=0.0, le=1.0)


class RelationshipMap(BaseModel):
    """Map of entity relationships."""

    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    key_connections: List[str] = Field(default_factory=list)
    network_summary: Optional[str] = None


class Pattern(BaseModel):
    """Identified pattern."""

    pattern_type: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    instances: List[str] = Field(default_factory=list)


class PatternAnalysis(BaseModel):
    """Pattern analysis results."""

    identified_patterns: List[Pattern] = Field(default_factory=list)
    similarity_to_past_cases: Optional[str] = None
    trend_analysis: Optional[str] = None


class InvestigationGuidance(BaseModel):
    """Guidance for investigation."""

    key_questions: List[str] = Field(default_factory=list)
    recommended_data_points: List[str] = Field(default_factory=list)
    regulatory_considerations: List[str] = Field(default_factory=list)
    suggested_next_steps: List[str] = Field(default_factory=list)


class DetailedNarrative(BaseModel):
    """Detailed narrative sections."""

    entity_overview: str
    alert_trigger_details: str
    risk_context: str
    historical_context: Optional[str] = None
    regulatory_context: str


class ContextNarrative(BaseModel):
    """Complete context narrative for the alert."""

    executive_summary: str
    detailed_narrative: DetailedNarrative
    timeline: Timeline
    relationship_map: Optional[RelationshipMap] = None
    pattern_analysis: PatternAnalysis
    investigation_guidance: InvestigationGuidance

    # Metadata
    narrative_generated_at: datetime = Field(default_factory=datetime.now)
    confidence_score: float = Field(ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "executive_summary": "John Smith matched OFAC SDN list with 92% confidence. Entity is based in high-risk jurisdiction with adverse media related to sanctions evasion. Recommend L2 escalation for detailed investigation.",
                "detailed_narrative": {
                    "entity_overview": "John Smith is an individual customer...",
                    "alert_trigger_details": "Alert triggered by name match to OFAC SDN list...",
                    "risk_context": "Entity exhibits multiple high-risk indicators...",
                    "regulatory_context": "Under BSA/AML and OFAC regulations..."
                },
                "timeline": {
                    "events": [
                        {
                            "date": "2024-01-15T10:00:00Z",
                            "event": "Account opened",
                            "significance": "Customer onboarding"
                        }
                    ]
                },
                "pattern_analysis": {
                    "identified_patterns": []
                },
                "investigation_guidance": {
                    "key_questions": ["Is this the same person as the SDN match?"],
                    "recommended_data_points": ["Date of birth verification"],
                    "regulatory_considerations": ["OFAC compliance required"]
                },
                "confidence_score": 0.85
            }
        }
