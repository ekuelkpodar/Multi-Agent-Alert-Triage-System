"""Risk Scoring Agent implementation."""

import json
from typing import Dict, Any

from aml_triage.core.base_agent import BaseAgent
from aml_triage.core.config import settings
from aml_triage.models.alert import Alert
from aml_triage.models.enrichment import EnrichmentResult
from aml_triage.models.risk import (
    RiskAssessment,
    RiskLevel,
    ComponentScores,
    RiskFactors,
    RegulatoryCompliance,
    MLInsights,
)


class RiskScoringAgent(BaseAgent[RiskAssessment]):
    """
    Risk Scoring Agent - Calculates comprehensive risk scores.

    Responsibilities:
    - Apply regulatory risk scoring frameworks
    - Calculate component risk scores
    - Identify mitigating and aggravating factors
    - Provide risk narrative with regulatory citations
    """

    def __init__(self):
        super().__init__(
            name="risk_scoring_agent",
            model=settings.risk_scoring_model,
            temperature=settings.llm_temperature_low,
            max_tokens=3000,
            timeout=20,
        )

    @property
    def system_prompt(self) -> str:
        """System prompt for the risk scoring agent."""
        return """You are the Risk Scoring Agent in a multi-agent AML/KYC compliance system.

Your responsibility is to calculate comprehensive risk scores using regulatory guidelines and best practices.

REGULATORY FRAMEWORKS:
- Bank Secrecy Act (BSA) / Anti-Money Laundering (AML)
- Financial Crimes Enforcement Network (FinCEN) guidelines
- Office of the Comptroller of the Currency (OCC) risk assessment standards
- Financial Action Task Force (FATF) recommendations

RISK SCORING FRAMEWORK:
Total Risk Score = Weighted Sum of:
- Customer Risk (30%): Customer type, profile, behavior patterns
- Geographic Risk (20%): Jurisdiction risk ratings, FATF high-risk countries
- Transaction Risk (25%): Transaction complexity, volume, velocity
- Adverse Media Risk (15%): Severity and credibility of allegations
- Network Risk (10%): Related party exposure, beneficial ownership

RISK SCORE SCALE:
- 0-30: LOW risk
- 31-60: MEDIUM risk
- 61-80: HIGH risk
- 81-100: SEVERE risk

ASSESSMENT REQUIREMENTS:
1. Calculate each component score objectively
2. Identify specific mitigating factors (reduce risk)
3. Identify specific aggravating factors (increase risk)
4. Cite specific regulatory guidelines and red flags
5. Provide clear narrative explaining the risk assessment
6. Map risks to BSA/AML regulatory expectations

CRITICAL CONSIDERATIONS:
- OFAC 50% rule for sanctions screening
- FinCEN red flags for money laundering
- PEP enhanced due diligence requirements
- High-risk jurisdiction indicators per FATF

Be objective, evidence-based, and cite specific regulatory guidance."""

    async def process(
        self, alert: Alert, enrichment: EnrichmentResult
    ) -> RiskAssessment:
        """
        Calculate comprehensive risk score.

        Args:
            alert: Original alert data
            enrichment: Enrichment data from DataEnrichmentAgent

        Returns:
            RiskAssessment with detailed scoring
        """
        self.logger.info(
            "starting_risk_scoring",
            alert_id=alert.alert_id,
            alert_type=alert.alert_type.value,
        )

        # Calculate component scores
        component_scores = await self._calculate_component_scores(alert, enrichment)

        # Calculate overall risk score (weighted average)
        overall_score = self._calculate_weighted_score(component_scores)

        # Determine risk level
        risk_level = self._categorize_risk_level(overall_score)

        # Prepare data for LLM analysis
        risk_data = {
            "alert": alert.model_dump(),
            "enrichment_summary": enrichment.enrichment_summary,
            "risk_indicators": enrichment.risk_indicators.model_dump(),
            "component_scores": component_scores.model_dump(),
            "overall_score": overall_score,
            "risk_level": risk_level.value,
        }

        # Call LLM to generate risk narrative and identify factors
        messages = [
            {
                "role": "user",
                "content": f"""Analyze this risk assessment data and provide a comprehensive risk narrative.

Risk Data:
{json.dumps(risk_data, indent=2, default=str)}

Provide a structured risk assessment including:
1. Risk Narrative: Clear explanation of why this risk level was assigned
2. Mitigating Factors: Specific factors that reduce risk (e.g., "Long-standing customer relationship")
3. Aggravating Factors: Specific factors that increase risk (e.g., "High-risk jurisdiction", "Adverse media")
4. Regulatory Citations: Specific regulations and guidance that apply (e.g., "31 CFR 1020.220", "FinCEN SAR Guidance")
5. Compliance Concerns: Any specific regulatory concerns identified
6. Red Flags: Any FinCEN or regulatory red flags present

Be specific and cite regulatory sources."""
            }
        ]

        analysis = await self.call_llm(messages)

        # Parse LLM response to extract structured data
        risk_factors, regulatory_compliance = await self._parse_risk_analysis(analysis)

        # Build risk assessment result
        result = RiskAssessment(
            overall_risk_score=overall_score,
            risk_level=risk_level,
            component_breakdown=component_scores,
            risk_narrative=analysis,
            regulatory_context=regulatory_compliance,
            risk_factors=risk_factors,
            confidence=0.85,  # Would be calculated based on data quality in production
        )

        self.logger.info(
            "risk_scoring_completed",
            alert_id=alert.alert_id,
            risk_score=overall_score,
            risk_level=risk_level.value,
        )

        return result

    async def _calculate_component_scores(
        self, alert: Alert, enrichment: EnrichmentResult
    ) -> ComponentScores:
        """Calculate individual component risk scores."""

        # Customer Risk (30%)
        customer_risk = 50  # Base score
        if alert.alert_type.value == "PEP":
            customer_risk += 20
        if enrichment.historical_alerts.count > 3:
            customer_risk += 10

        # Geographic Risk (20%)
        geographic_risk = self._calculate_geographic_risk(enrichment.risk_indicators.jurisdiction_risk_level)

        # Transaction Risk (25%)
        transaction_risk = 40  # Base score
        if alert.alert_type.value == "TRANSACTION":
            transaction_risk += 30
        if enrichment.risk_indicators.transaction_anomalies:
            transaction_risk += len(enrichment.risk_indicators.transaction_anomalies) * 5

        # Adverse Media Risk (15%)
        adverse_media_risk = 0
        if enrichment.adverse_media_extended:
            adverse_media_risk = min(100, int(enrichment.adverse_media_extended.relevance_score * 100))

        # Network Risk (10%)
        network_risk = 30  # Base score
        if enrichment.corporate_intelligence and enrichment.corporate_intelligence.related_entities:
            network_risk += len(enrichment.corporate_intelligence.related_entities) * 5

        # Ensure all scores are within bounds
        return ComponentScores(
            customer_risk=min(100, max(0, customer_risk)),
            geographic_risk=min(100, max(0, geographic_risk)),
            transaction_risk=min(100, max(0, transaction_risk)),
            adverse_media_risk=min(100, max(0, adverse_media_risk)),
            network_risk=min(100, max(0, network_risk)),
        )

    def _calculate_geographic_risk(self, jurisdiction_risk_level: str) -> int:
        """Calculate geographic risk score based on jurisdiction."""
        risk_mapping = {
            "LOW": 20,
            "MEDIUM": 50,
            "HIGH": 85,
        }
        return risk_mapping.get(jurisdiction_risk_level, 50)

    def _calculate_weighted_score(self, components: ComponentScores) -> int:
        """Calculate weighted average of component scores."""
        weights = {
            "customer_risk": 0.30,
            "geographic_risk": 0.20,
            "transaction_risk": 0.25,
            "adverse_media_risk": 0.15,
            "network_risk": 0.10,
        }

        weighted_sum = (
            components.customer_risk * weights["customer_risk"]
            + components.geographic_risk * weights["geographic_risk"]
            + components.transaction_risk * weights["transaction_risk"]
            + components.adverse_media_risk * weights["adverse_media_risk"]
            + components.network_risk * weights["network_risk"]
        )

        return int(round(weighted_sum))

    def _categorize_risk_level(self, score: int) -> RiskLevel:
        """Categorize risk score into risk level."""
        if score <= 30:
            return RiskLevel.LOW
        elif score <= 60:
            return RiskLevel.MEDIUM
        elif score <= 80:
            return RiskLevel.HIGH
        else:
            return RiskLevel.SEVERE

    async def _parse_risk_analysis(self, analysis: str) -> tuple[RiskFactors, RegulatoryCompliance]:
        """Parse LLM analysis to extract structured risk factors."""
        # Simple parsing - in production would use more sophisticated extraction
        # or use structured output from LLM

        risk_factors = RiskFactors(
            mitigating=[],
            aggravating=[],
        )

        regulatory_compliance = RegulatoryCompliance(
            applicable_frameworks=["BSA/AML", "FinCEN"],
            compliance_concerns=[],
            regulatory_citations=[],
        )

        return risk_factors, regulatory_compliance
