"""Context Builder Agent implementation."""

import json
from datetime import datetime

from aml_triage.core.base_agent import BaseAgent
from aml_triage.core.config import settings
from aml_triage.models.alert import Alert
from aml_triage.models.enrichment import EnrichmentResult
from aml_triage.models.risk import RiskAssessment
from aml_triage.models.context import (
    ContextNarrative,
    DetailedNarrative,
    Timeline,
    TimelineEvent,
    PatternAnalysis,
    InvestigationGuidance,
)


class ContextBuilderAgent(BaseAgent[ContextNarrative]):
    """
    Context Builder Agent - Synthesizes data into coherent narratives.

    Responsibilities:
    - Create human-readable alert summaries
    - Build chronological timelines
    - Generate regulatory-compliant documentation
    - Provide investigation guidance
    """

    def __init__(self):
        super().__init__(
            name="context_builder_agent",
            model=settings.context_builder_model,
            temperature=settings.llm_temperature_high,
            max_tokens=4000,
            timeout=25,
        )

    @property
    def system_prompt(self) -> str:
        """System prompt for the context builder agent."""
        return """You are the Context Builder Agent in a multi-agent AML/KYC compliance system.

Your responsibility is to synthesize technical data into clear, coherent narratives for compliance analysts and regulators.

NARRATIVE REQUIREMENTS:
1. Executive Summary (3-5 sentences):
   - Who is the subject entity?
   - What triggered the alert?
   - What is the key risk concern?
   - What action is recommended?

2. Detailed Narrative Sections:
   - Entity Overview: Identity, business activities, relationship to institution
   - Alert Trigger Details: Specific reasons for the alert
   - Risk Context: Key risk factors and concerns
   - Historical Context: Relevant historical patterns
   - Regulatory Context: Applicable regulations and requirements

3. Investigation Guidance:
   - Key questions that need answering
   - Recommended data points to collect
   - Regulatory considerations
   - Suggested next steps

WRITING STYLE:
- Clear and professional language
- Avoid jargon where possible, explain technical terms
- Use active voice
- Be concise but comprehensive
- Focus on facts and evidence
- Cite specific data points and sources

COMPLIANCE STANDARDS:
- Documentation must be audit-ready
- All claims must be evidence-based
- Maintain objective tone
- Include regulatory citations where applicable
- Structure for easy regulatory review

You are creating documentation that compliance analysts and potentially regulators will read."""

    async def process(
        self,
        alert: Alert,
        enrichment: EnrichmentResult,
        risk_assessment: RiskAssessment,
    ) -> ContextNarrative:
        """
        Build comprehensive context narrative.

        Args:
            alert: Original alert data
            enrichment: Enrichment data
            risk_assessment: Risk assessment results

        Returns:
            ContextNarrative with complete documentation
        """
        self.logger.info(
            "starting_context_building",
            alert_id=alert.alert_id,
        )

        # Prepare consolidated data for LLM
        context_data = {
            "alert": {
                "id": alert.alert_id,
                "type": alert.alert_type.value,
                "priority": alert.priority.value,
                "customer_name": alert.customer_data.name,
                "entity_type": alert.customer_data.entity_type.value,
                "screening_matches": len(alert.screening_results.match_details),
            },
            "enrichment_summary": enrichment.enrichment_summary,
            "risk_score": risk_assessment.overall_risk_score,
            "risk_level": risk_assessment.risk_level.value,
            "risk_narrative": risk_assessment.risk_narrative,
            "data_quality": enrichment.data_quality.completeness_score,
        }

        # Call LLM to generate narrative
        messages = [
            {
                "role": "user",
                "content": f"""Create a comprehensive context narrative for this AML alert.

Alert and Risk Data:
{json.dumps(context_data, indent=2, default=str)}

Generate:
1. Executive Summary (3-5 sentences) - Clear overview for quick understanding
2. Entity Overview - Who is this entity and their relationship to the institution
3. Alert Trigger Details - Specific details about what triggered the alert
4. Risk Context - Key risk factors and why they matter
5. Regulatory Context - Applicable regulations and compliance requirements
6. Investigation Guidance including:
   - 3-5 key questions for investigators
   - Critical data points to verify
   - Regulatory considerations
   - Recommended next steps

Be clear, professional, and focus on facts."""
            }
        ]

        narrative_text = await self.call_llm(messages)

        # Parse narrative into structured sections
        # In production, would use more sophisticated parsing or structured LLM output
        detailed_narrative = self._parse_narrative(narrative_text)

        # Build timeline
        timeline = self._build_timeline(alert, enrichment)

        # Generate investigation guidance
        investigation_guidance = self._generate_investigation_guidance(
            alert, risk_assessment
        )

        # Build pattern analysis
        pattern_analysis = PatternAnalysis(
            identified_patterns=[],
            similarity_to_past_cases=None,
            trend_analysis=None,
        )

        # Create context narrative
        result = ContextNarrative(
            executive_summary=self._extract_executive_summary(narrative_text),
            detailed_narrative=detailed_narrative,
            timeline=timeline,
            pattern_analysis=pattern_analysis,
            investigation_guidance=investigation_guidance,
            confidence_score=0.88,
        )

        self.logger.info(
            "context_building_completed",
            alert_id=alert.alert_id,
        )

        return result

    def _parse_narrative(self, narrative_text: str) -> DetailedNarrative:
        """Parse narrative text into structured sections."""
        # Simple extraction - in production would use more sophisticated parsing
        return DetailedNarrative(
            entity_overview=narrative_text[:200] + "...",
            alert_trigger_details="Alert triggered by screening match.",
            risk_context="Risk assessment indicates review required.",
            historical_context=None,
            regulatory_context="Applicable regulations include BSA/AML and OFAC requirements.",
        )

    def _extract_executive_summary(self, narrative_text: str) -> str:
        """Extract executive summary from narrative."""
        # Extract first paragraph as summary
        lines = narrative_text.split("\n\n")
        if lines:
            return lines[0].strip()
        return narrative_text[:300] + "..."

    def _build_timeline(
        self, alert: Alert, enrichment: EnrichmentResult
    ) -> Timeline:
        """Build chronological timeline of events."""
        events = [
            TimelineEvent(
                date=alert.timestamp,
                event="Alert generated",
                significance="Screening match detected",
                source="Screening System",
            )
        ]

        # Add historical events if available
        for prev_alert in enrichment.historical_alerts.previous_resolutions:
            events.append(
                TimelineEvent(
                    date=prev_alert.resolution_date,
                    event=f"Previous alert {prev_alert.disposition}",
                    significance=f"Risk score: {prev_alert.risk_score}",
                    source="Historical Records",
                )
            )

        return Timeline(
            events=sorted(events, key=lambda e: e.date),
            summary=f"{len(events)} events identified",
        )

    def _generate_investigation_guidance(
        self, alert: Alert, risk_assessment: RiskAssessment
    ) -> InvestigationGuidance:
        """Generate investigation guidance."""
        key_questions = [
            "Is the screening match a true positive?",
            "What is the nature of the customer's business activities?",
            "Are there any unexplained transaction patterns?",
        ]

        recommended_data_points = [
            "Verify customer identity with government-issued ID",
            "Review complete transaction history",
            "Confirm beneficial ownership information",
        ]

        regulatory_considerations = [
            "Ensure compliance with OFAC sanctions requirements",
            "Consider SAR filing obligations under 31 CFR 1020.320",
            "Document decision rationale for audit purposes",
        ]

        suggested_next_steps = []
        if risk_assessment.risk_level.value in ["HIGH", "SEVERE"]:
            suggested_next_steps.append("Escalate to senior compliance officer")
            suggested_next_steps.append("Consider enhanced due diligence")
        else:
            suggested_next_steps.append("Complete standard due diligence review")

        return InvestigationGuidance(
            key_questions=key_questions,
            recommended_data_points=recommended_data_points,
            regulatory_considerations=regulatory_considerations,
            suggested_next_steps=suggested_next_steps,
        )
