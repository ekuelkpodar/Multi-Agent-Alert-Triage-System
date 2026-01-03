"""Data enrichment result models."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PreviousResolution(BaseModel):
    """Previous alert resolution information."""

    alert_id: str
    resolution_date: datetime
    disposition: str
    risk_score: int
    analyst_notes: Optional[str] = None


class HistoricalAlerts(BaseModel):
    """Historical alert information."""

    count: int
    previous_resolutions: List[PreviousResolution] = Field(default_factory=list)
    pattern_analysis: Optional[str] = None
    first_alert_date: Optional[datetime] = None
    most_recent_alert_date: Optional[datetime] = None


class MediaSource(BaseModel):
    """Adverse media source information."""

    source_name: str
    article_title: str
    publication_date: datetime
    url: Optional[str] = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    severity: str
    summary: str


class AdverseMediaExtended(BaseModel):
    """Extended adverse media findings."""

    new_sources_found: int
    media_sources: List[MediaSource] = Field(default_factory=list)
    severity_assessment: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    topics: List[str] = Field(default_factory=list)


class BeneficialOwner(BaseModel):
    """Beneficial ownership information."""

    name: str
    ownership_percentage: Optional[float] = None
    relationship: str
    is_pep: bool = False
    risk_indicators: List[str] = Field(default_factory=list)


class RelatedEntity(BaseModel):
    """Related entity information."""

    entity_id: str
    entity_name: str
    relationship_type: str
    relationship_strength: float = Field(ge=0.0, le=1.0)
    risk_level: Optional[str] = None


class CorporateIntelligence(BaseModel):
    """Corporate structure and intelligence."""

    ultimate_beneficial_owners: List[BeneficialOwner] = Field(default_factory=list)
    corporate_structure: Dict[str, Any] = Field(default_factory=dict)
    related_entities: List[RelatedEntity] = Field(default_factory=list)
    industry_classification: Optional[str] = None
    business_description: Optional[str] = None
    incorporation_date: Optional[datetime] = None
    incorporation_jurisdiction: Optional[str] = None


class RiskIndicators(BaseModel):
    """Risk indicator findings."""

    jurisdiction_risk_level: str
    jurisdiction_details: Dict[str, Any] = Field(default_factory=dict)
    industry_risk: Optional[str] = None
    transaction_anomalies: List[str] = Field(default_factory=list)
    pep_exposure: bool = False
    sanctions_exposure: bool = False
    adverse_media_exposure: bool = False


class DataQualityMetrics(BaseModel):
    """Data quality and completeness metrics."""

    completeness_score: float = Field(ge=0.0, le=1.0)
    freshness_score: float = Field(ge=0.0, le=1.0)
    reliability_score: float = Field(ge=0.0, le=1.0)
    missing_critical_fields: List[str] = Field(default_factory=list)


class EnrichmentResult(BaseModel):
    """Result from data enrichment process."""

    enrichment_summary: str
    historical_alerts: HistoricalAlerts
    adverse_media_extended: Optional[AdverseMediaExtended] = None
    corporate_intelligence: Optional[CorporateIntelligence] = None
    risk_indicators: RiskIndicators

    # Enrichment metadata
    sources_used: List[str] = Field(default_factory=list)
    enrichment_timestamp: datetime = Field(default_factory=datetime.now)
    data_quality: DataQualityMetrics
    api_calls_made: int = 0
    errors_encountered: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "enrichment_summary": "Customer has 2 previous alerts, both cleared. No adverse media found. Low jurisdiction risk.",
                "historical_alerts": {
                    "count": 2,
                    "pattern_analysis": "Previous alerts were false positives with different entities"
                },
                "risk_indicators": {
                    "jurisdiction_risk_level": "LOW",
                    "transaction_anomalies": []
                },
                "sources_used": ["Internal CRM", "OFAC", "WorldCheck"],
                "data_quality": {
                    "completeness_score": 0.85,
                    "freshness_score": 0.95,
                    "reliability_score": 0.90,
                    "missing_critical_fields": []
                }
            }
        }
