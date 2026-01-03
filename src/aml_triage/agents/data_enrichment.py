"""Data Enrichment Agent implementation."""

import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

from aml_triage.core.base_agent import BaseAgent
from aml_triage.core.config import settings
from aml_triage.models.alert import Alert
from aml_triage.models.enrichment import (
    EnrichmentResult,
    HistoricalAlerts,
    AdverseMediaExtended,
    CorporateIntelligence,
    RiskIndicators,
    DataQualityMetrics,
    PreviousResolution,
    MediaSource,
)


class DataEnrichmentAgent(BaseAgent[EnrichmentResult]):
    """
    Data Enrichment Agent - Augments alert data with additional context.

    Responsibilities:
    - Query internal and external data sources
    - Retrieve historical customer interactions
    - Gather adverse media and corporate intelligence
    - Assess data quality and completeness
    """

    def __init__(self):
        super().__init__(
            name="data_enrichment_agent",
            model=settings.data_enrichment_model,
            temperature=settings.llm_temperature_medium,
            max_tokens=2000,
            timeout=30,
        )

    @property
    def system_prompt(self) -> str:
        """System prompt for the data enrichment agent."""
        return """You are the Data Enrichment Agent in a multi-agent AML/KYC compliance system.

Your responsibility is to augment alert data with additional context from multiple data sources.

CORE TASKS:
1. Analyze the alert and identify what additional data is needed
2. Evaluate the completeness and quality of available data
3. Summarize enrichment findings in a clear, concise manner
4. Highlight any data gaps or quality issues

DATA SOURCES TO CONSIDER:
- Historical alert database
- Customer relationship management (CRM) systems
- Transaction history
- Adverse media feeds
- Corporate registries and beneficial ownership databases
- Sanctions lists (OFAC, UN, EU)
- PEP databases
- Court records and legal filings

ENRICHMENT ASSESSMENT:
When assessing enrichment results, evaluate:
- Data completeness: Are all critical fields populated?
- Data freshness: How recent is the data?
- Data reliability: How trustworthy are the sources?
- Pattern identification: Any concerning patterns in historical data?

OUTPUT REQUIREMENTS:
- Provide a clear executive summary of enrichment findings
- Identify critical missing data points
- Flag any concerning patterns or anomalies
- Assess data quality with specific metrics

You must be objective, thorough, and focused on regulatory compliance."""

    async def process(self, alert: Alert) -> EnrichmentResult:
        """
        Process alert and enrich with additional data.

        Args:
            alert: Alert to enrich

        Returns:
            EnrichmentResult with additional context
        """
        self.logger.info(
            "starting_enrichment",
            alert_id=alert.alert_id,
            alert_type=alert.alert_type.value,
        )

        # Gather enrichment data from multiple sources
        historical_data = await self._fetch_historical_alerts(alert.customer_data.customer_id)
        adverse_media = await self._fetch_adverse_media(alert.customer_data.name, alert.customer_data.aliases)
        corporate_intel = await self._fetch_corporate_intelligence(alert.customer_data)
        risk_indicators = await self._assess_risk_indicators(alert)

        # Prepare data for LLM analysis
        enrichment_data = {
            "alert": alert.model_dump(),
            "historical_alerts": historical_data,
            "adverse_media": adverse_media,
            "corporate_intelligence": corporate_intel,
            "risk_indicators": risk_indicators,
        }

        # Call LLM to analyze and summarize enrichment
        messages = [
            {
                "role": "user",
                "content": f"""Analyze this enrichment data and provide a comprehensive summary.

Alert Data:
{json.dumps(enrichment_data, indent=2, default=str)}

Provide:
1. Executive summary of key findings
2. Assessment of data completeness and quality
3. Identification of any concerning patterns
4. List of critical missing data points (if any)

Be objective and focus on facts relevant to AML/KYC compliance."""
            }
        ]

        analysis = await self.call_llm(messages)

        # Calculate data quality metrics
        data_quality = self._calculate_data_quality(enrichment_data)

        # Build enrichment result
        result = EnrichmentResult(
            enrichment_summary=analysis,
            historical_alerts=historical_data,
            adverse_media_extended=adverse_media,
            corporate_intelligence=corporate_intel,
            risk_indicators=risk_indicators,
            sources_used=self._get_sources_used(),
            data_quality=data_quality,
            api_calls_made=len(self._get_sources_used()),
        )

        self.logger.info(
            "enrichment_completed",
            alert_id=alert.alert_id,
            data_completeness=data_quality.completeness_score,
            sources_used=len(result.sources_used),
        )

        return result

    async def _fetch_historical_alerts(self, customer_id: str) -> HistoricalAlerts:
        """Fetch historical alerts for the customer."""
        # In production, this would query the database
        # For now, return mock data
        return HistoricalAlerts(
            count=0,
            previous_resolutions=[],
            pattern_analysis=None,
        )

    async def _fetch_adverse_media(
        self, name: str, aliases: List[str]
    ) -> AdverseMediaExtended:
        """Fetch adverse media for the entity."""
        # In production, this would call Castellum.AI API or other media sources
        # For now, return mock data
        return AdverseMediaExtended(
            new_sources_found=0,
            media_sources=[],
            severity_assessment="No adverse media found",
            relevance_score=0.0,
            topics=[],
        )

    async def _fetch_corporate_intelligence(self, customer_data: Any) -> CorporateIntelligence:
        """Fetch corporate intelligence data."""
        # In production, this would query corporate registries
        # For now, return mock data
        return CorporateIntelligence(
            ultimate_beneficial_owners=[],
            corporate_structure={},
            related_entities=[],
        )

    async def _assess_risk_indicators(self, alert: Alert) -> RiskIndicators:
        """Assess risk indicators based on alert data."""
        # Determine jurisdiction risk
        jurisdiction = alert.customer_data.addresses[0].country if alert.customer_data.addresses else "UNKNOWN"

        # High-risk jurisdictions (example list)
        high_risk_jurisdictions = ["IRN", "PRK", "SYR", "AFG", "YEM"]

        jurisdiction_risk = "HIGH" if jurisdiction in high_risk_jurisdictions else "MEDIUM" if jurisdiction not in ["USA", "CAN", "GBR", "DEU", "FRA"] else "LOW"

        return RiskIndicators(
            jurisdiction_risk_level=jurisdiction_risk,
            jurisdiction_details={"country_code": jurisdiction},
            transaction_anomalies=[],
            sanctions_exposure=alert.alert_type.value == "SANCTIONS",
        )

    def _calculate_data_quality(self, enrichment_data: Dict[str, Any]) -> DataQualityMetrics:
        """Calculate data quality metrics."""
        # Simple heuristic-based quality calculation
        # In production, this would be more sophisticated

        critical_fields = ["name", "addresses", "entity_type"]
        missing_fields = []

        customer_data = enrichment_data["alert"]["customer_data"]
        for field in critical_fields:
            if not customer_data.get(field):
                missing_fields.append(field)

        completeness_score = max(0.0, 1.0 - (len(missing_fields) / len(critical_fields)))
        freshness_score = 0.95  # Would be based on data timestamps in production
        reliability_score = 0.90  # Would be based on source credibility in production

        return DataQualityMetrics(
            completeness_score=completeness_score,
            freshness_score=freshness_score,
            reliability_score=reliability_score,
            missing_critical_fields=missing_fields,
        )

    def _get_sources_used(self) -> List[str]:
        """Get list of data sources consulted."""
        return [
            "Internal CRM",
            "Historical Alert Database",
            "Transaction Monitoring System",
        ]
