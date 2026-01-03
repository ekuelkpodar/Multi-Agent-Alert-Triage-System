"""Alert data models and schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class AlertType(str, Enum):
    """Types of AML/KYC alerts."""

    SANCTIONS = "SANCTIONS"
    PEP = "PEP"
    ADVERSE_MEDIA = "ADVERSE_MEDIA"
    TRANSACTION = "TRANSACTION"
    KYC_ONGOING = "KYC_ONGOING"


class AlertPriority(str, Enum):
    """Priority levels for alerts."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EntityType(str, Enum):
    """Type of customer entity."""

    INDIVIDUAL = "INDIVIDUAL"
    BUSINESS = "BUSINESS"


class Address(BaseModel):
    """Address information."""

    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    postal_code: Optional[str] = None


class CustomerData(BaseModel):
    """Customer/entity data."""

    customer_id: str
    name: str
    aliases: List[str] = Field(default_factory=list)
    dob: Optional[datetime] = None
    addresses: List[Address] = Field(default_factory=list)
    entity_type: EntityType
    nationality: Optional[str] = None
    industry: Optional[str] = None


class MatchDetail(BaseModel):
    """Details of a screening match."""

    source: str
    match_type: str
    matched_name: str
    match_score: float = Field(ge=0.0, le=1.0)
    list_name: str
    additional_info: Dict[str, Any] = Field(default_factory=dict)


class ScreeningResults(BaseModel):
    """Results from screening engine."""

    match_details: List[MatchDetail] = Field(default_factory=list)
    match_scores: List[float] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    screening_timestamp: datetime = Field(default_factory=datetime.now)


class RegulatoryContext(BaseModel):
    """Regulatory context for the alert."""

    jurisdiction: str
    applicable_regulations: List[str] = Field(default_factory=list)
    institution_type: Optional[str] = None
    risk_appetite: Optional[str] = None


class Alert(BaseModel):
    """Main alert data structure."""

    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    alert_type: AlertType
    priority: AlertPriority
    customer_data: CustomerData
    screening_results: ScreeningResults
    timestamp: datetime = Field(default_factory=datetime.now)
    regulatory_context: RegulatoryContext

    # Optional fields for additional context
    transaction_data: Optional[Dict[str, Any]] = None
    account_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "550e8400-e29b-41d4-a716-446655440000",
                "alert_type": "SANCTIONS",
                "priority": "HIGH",
                "customer_data": {
                    "customer_id": "CUST-12345",
                    "name": "John Smith",
                    "aliases": ["Jon Smith"],
                    "entity_type": "INDIVIDUAL",
                    "addresses": [
                        {
                            "country": "USA",
                            "city": "New York",
                            "state": "NY"
                        }
                    ]
                },
                "screening_results": {
                    "match_details": [
                        {
                            "source": "OFAC",
                            "match_type": "NAME",
                            "matched_name": "John Smith",
                            "match_score": 0.92,
                            "list_name": "SDN"
                        }
                    ],
                    "match_scores": [0.92],
                    "data_sources": ["OFAC", "UN", "EU"]
                },
                "regulatory_context": {
                    "jurisdiction": "USA",
                    "applicable_regulations": ["BSA", "OFAC"],
                    "institution_type": "BANK"
                }
            }
        }
