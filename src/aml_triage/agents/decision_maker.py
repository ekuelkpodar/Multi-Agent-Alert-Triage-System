"""Decision Maker Agent implementation."""

import json
from datetime import datetime, timedelta

from aml_triage.core.base_agent import BaseAgent
from aml_triage.core.config import settings
from aml_triage.models.alert import Alert
from aml_triage.models.enrichment import EnrichmentResult
from aml_triage.models.risk import RiskAssessment
from aml_triage.models.context import ContextNarrative
from aml_triage.models.decision import (
    Decision,
    DecisionDisposition,
    DecisionFactors,
    EscalationDetails,
    EscalationPriority,
    RecommendedAction,
    Documentation,
    AgentContribution,
)


class DecisionMakerAgent(BaseAgent[Decision]):
    """
    Decision Maker Agent - Makes final disposition decisions.

    Responsibilities:
    - Evaluate all evidence against decision criteria
    - Apply disposition policies
    - Generate regulatory-compliant rationales
    - Determine escalation requirements
    """

    def __init__(self):
        super().__init__(
            name="decision_maker_agent",
            model=settings.decision_maker_model,
            temperature=settings.llm_temperature_deterministic,
            max_tokens=4000,
            timeout=15,
        )

    @property
    def system_prompt(self) -> str:
        """System prompt for the decision maker agent."""
        return """You are the Decision Maker Agent in a multi-agent AML/KYC compliance system.

Your responsibility is to make final disposition decisions on alerts based on all available intelligence.

DECISION OPTIONS:
1. AUTO_CLEAR: Clear the alert automatically (low risk, high confidence)
2. ESCALATE_L2: Escalate to Level 2 analyst (medium risk or moderate confidence)
3. ESCALATE_L3: Escalate to Level 3 / senior analyst (high risk)
4. ESCALATE_SAR: Escalate for SAR filing consideration (severe risk)
5. BLOCK_TRANSACTION: Immediate transaction block required (sanctions/critical)

DECISION CRITERIA:
- Risk Score: Overall risk assessment (0-100)
- Confidence: Quality and completeness of data (0-1)
- Regulatory Flags: Presence of regulatory red flags
- Data Quality: Completeness and reliability of information
- Historical Precedent: Similar cases and outcomes

DECISION MATRIX GUIDELINES:
- Risk 0-30, High Data Quality, No Flags → AUTO_CLEAR
- Risk 31-60, Medium+ Quality → ESCALATE_L2
- Risk 61-80 → ESCALATE_L3
- Risk 81-100 or Critical Flags → ESCALATE_SAR
- Direct OFAC Match → BLOCK_TRANSACTION

ESCALATION TRIGGERS:
- Risk score > 70
- Confidence < 0.70
- Data completeness < 0.60
- Direct sanctions match
- PEP with adverse media
- Novel pattern not previously seen
- Conflicting evidence requiring judgment

RATIONALE REQUIREMENTS:
1. Cite specific evidence and data points
2. Reference applicable regulations
3. Explain decision pathway transparently
4. Address contrary evidence
5. Note any limitations or uncertainties
6. Provide actionable next steps

REGULATORY COMPLIANCE:
- All decisions must have audit-ready documentation
- Cite specific regulations (e.g., "31 CFR 1020.220")
- Explain how evidence was evaluated
- Maintain objective, fact-based reasoning

Be thorough, objective, and prioritize regulatory compliance."""

    async def process(
        self,
        alert: Alert,
        enrichment: EnrichmentResult,
        risk_assessment: RiskAssessment,
        context: ContextNarrative,
    ) -> Decision:
        """
        Make final disposition decision.

        Args:
            alert: Original alert
            enrichment: Enrichment data
            risk_assessment: Risk assessment
            context: Context narrative

        Returns:
            Final decision with rationale
        """
        self.logger.info(
            "starting_decision_making",
            alert_id=alert.alert_id,
            risk_score=risk_assessment.overall_risk_score,
        )

        # Prepare decision data for LLM
        decision_data = {
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type.value,
            "risk_score": risk_assessment.overall_risk_score,
            "risk_level": risk_assessment.risk_level.value,
            "data_completeness": enrichment.data_quality.completeness_score,
            "data_reliability": enrichment.data_quality.reliability_score,
            "executive_summary": context.executive_summary,
            "risk_narrative": risk_assessment.risk_narrative,
            "regulatory_concerns": risk_assessment.regulatory_context.compliance_concerns,
        }

        # Apply decision logic
        disposition = self._determine_disposition(risk_assessment, enrichment)
        requires_human = self._check_human_review_required(
            disposition, risk_assessment, enrichment
        )

        # Call LLM to generate rationale
        messages = [
            {
                "role": "user",
                "content": f"""Make a final disposition decision for this AML alert.

Decision Data:
{json.dumps(decision_data, indent=2, default=str)}

Recommended Disposition: {disposition}
Requires Human Review: {requires_human}

Provide a comprehensive decision rationale that includes:
1. Clear explanation of the disposition decision
2. Primary factors supporting the decision
3. Supporting evidence and data points
4. Any contrary evidence considered
5. Regulatory basis (cite specific regulations)
6. Recommended actions

Be thorough, objective, and provide audit-ready documentation."""
            }
        ]

        rationale = await self.call_llm(messages)

        # Extract decision factors
        decision_factors = await self._extract_decision_factors(rationale, risk_assessment)

        # Determine escalation details if needed
        escalation_details = None
        if requires_human:
            escalation_details = self._create_escalation_details(
                disposition, risk_assessment, enrichment
            )

        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(
            disposition, risk_assessment
        )

        # Create agent contributions summary
        agent_contributions = self._summarize_agent_contributions(
            enrichment, risk_assessment, context
        )

        # Build final decision
        decision = Decision(
            alert_id=alert.alert_id,
            disposition=disposition,
            confidence_score=self._calculate_decision_confidence(enrichment, risk_assessment),
            rationale=rationale,
            risk_score=risk_assessment.overall_risk_score,
            decision_factors=decision_factors,
            escalation_details=escalation_details,
            recommended_actions=recommended_actions,
            requires_human_review=requires_human,
            processing_time_ms=0,  # Will be set by supervisor
            agent_contributions=agent_contributions,
            regulatory_citations=risk_assessment.regulatory_context.regulatory_citations,
        )

        self.logger.info(
            "decision_making_completed",
            alert_id=alert.alert_id,
            disposition=disposition.value,
            requires_human=requires_human,
        )

        return decision

    def _determine_disposition(
        self, risk_assessment: RiskAssessment, enrichment: EnrichmentResult
    ) -> DecisionDisposition:
        """Determine disposition based on risk and data quality."""
        risk_score = risk_assessment.overall_risk_score
        data_completeness = enrichment.data_quality.completeness_score

        # Critical thresholds
        if risk_score >= settings.risk_score_severe_threshold:
            return DecisionDisposition.ESCALATE_SAR

        if risk_score >= settings.risk_score_high_threshold:
            return DecisionDisposition.ESCALATE_L3

        if risk_score >= 31 or data_completeness < 0.70:
            return DecisionDisposition.ESCALATE_L2

        # Low risk and high data quality
        if risk_score <= 30 and data_completeness >= 0.80:
            return DecisionDisposition.AUTO_CLEAR

        # Default to L2 escalation for safety
        return DecisionDisposition.ESCALATE_L2

    def _check_human_review_required(
        self,
        disposition: DecisionDisposition,
        risk_assessment: RiskAssessment,
        enrichment: EnrichmentResult,
    ) -> bool:
        """Check if human review is required."""
        # Always require human review for escalations
        if disposition in [
            DecisionDisposition.ESCALATE_L3,
            DecisionDisposition.ESCALATE_SAR,
            DecisionDisposition.BLOCK_TRANSACTION,
        ]:
            return True

        # Require human review for low confidence
        decision_confidence = self._calculate_decision_confidence(enrichment, risk_assessment)
        if decision_confidence < settings.escalate_l2_threshold:
            return True

        # AUTO_CLEAR can be done without human review if confidence is high
        if disposition == DecisionDisposition.AUTO_CLEAR:
            return decision_confidence < settings.auto_clear_threshold

        # L2 escalation typically requires human review
        return True

    def _calculate_decision_confidence(
        self, enrichment: EnrichmentResult, risk_assessment: RiskAssessment
    ) -> float:
        """Calculate confidence in the decision."""
        # Weighted combination of data quality and risk assessment confidence
        weights = {"data_quality": 0.4, "risk_confidence": 0.6}

        data_quality_score = (
            enrichment.data_quality.completeness_score * 0.5
            + enrichment.data_quality.reliability_score * 0.5
        )

        confidence = (
            data_quality_score * weights["data_quality"]
            + risk_assessment.confidence * weights["risk_confidence"]
        )

        return round(confidence, 2)

    async def _extract_decision_factors(
        self, rationale: str, risk_assessment: RiskAssessment
    ) -> DecisionFactors:
        """Extract decision factors from rationale."""
        # Simple extraction - in production would use more sophisticated parsing
        return DecisionFactors(
            primary_factors=risk_assessment.risk_factors.aggravating[:3],
            supporting_factors=["Data quality assessment", "Regulatory compliance check"],
            contrary_evidence=risk_assessment.risk_factors.mitigating[:2],
            uncertainty_factors=[],
        )

    def _create_escalation_details(
        self,
        disposition: DecisionDisposition,
        risk_assessment: RiskAssessment,
        enrichment: EnrichmentResult,
    ) -> EscalationDetails:
        """Create escalation details."""
        priority_map = {
            DecisionDisposition.ESCALATE_L2: EscalationPriority.MEDIUM,
            DecisionDisposition.ESCALATE_L3: EscalationPriority.HIGH,
            DecisionDisposition.ESCALATE_SAR: EscalationPriority.URGENT,
        }

        return EscalationDetails(
            requires_human_review=True,
            escalation_reason=f"Risk score: {risk_assessment.overall_risk_score}, Risk level: {risk_assessment.risk_level.value}",
            priority=priority_map.get(disposition, EscalationPriority.MEDIUM),
            suggested_reviewer="L2 Compliance Analyst" if disposition == DecisionDisposition.ESCALATE_L2 else "Senior Compliance Officer",
        )

    def _generate_recommended_actions(
        self, disposition: DecisionDisposition, risk_assessment: RiskAssessment
    ) -> list[RecommendedAction]:
        """Generate recommended actions."""
        actions = []

        if disposition == DecisionDisposition.AUTO_CLEAR:
            actions.append(
                RecommendedAction(
                    action="Close alert with documented rationale",
                    priority=1,
                    rationale="Low risk assessment and high confidence in data",
                )
            )
        else:
            actions.append(
                RecommendedAction(
                    action="Review alert details and enrichment data",
                    priority=1,
                    rationale="Human review required for disposition decision",
                )
            )
            actions.append(
                RecommendedAction(
                    action="Verify customer identity and business activities",
                    priority=2,
                    rationale="Ensure accurate risk assessment",
                )
            )

        return actions

    def _summarize_agent_contributions(
        self,
        enrichment: EnrichmentResult,
        risk_assessment: RiskAssessment,
        context: ContextNarrative,
    ) -> dict[str, AgentContribution]:
        """Summarize contributions from each agent."""
        return {
            "data_enrichment": AgentContribution(
                agent_name="data_enrichment_agent",
                processing_time_ms=0,  # Would be tracked in production
                confidence=enrichment.data_quality.completeness_score,
                output_summary=enrichment.enrichment_summary[:200],
            ),
            "risk_scoring": AgentContribution(
                agent_name="risk_scoring_agent",
                processing_time_ms=0,
                confidence=risk_assessment.confidence,
                output_summary=f"Risk score: {risk_assessment.overall_risk_score} ({risk_assessment.risk_level.value})",
            ),
            "context_builder": AgentContribution(
                agent_name="context_builder_agent",
                processing_time_ms=0,
                confidence=context.confidence_score,
                output_summary=context.executive_summary[:200],
            ),
        }
