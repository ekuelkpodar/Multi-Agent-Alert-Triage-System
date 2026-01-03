"""Supervisor Agent - Orchestrates the multi-agent workflow."""

import asyncio
from datetime import datetime
from typing import Dict, Any

from aml_triage.core.base_agent import BaseAgent, CriticalAgentException
from aml_triage.core.config import settings
from aml_triage.core.audit import AuditTrail
from aml_triage.core.logging import get_logger
from aml_triage.models.alert import Alert
from aml_triage.models.decision import Decision, DecisionDisposition
from aml_triage.agents.data_enrichment import DataEnrichmentAgent
from aml_triage.agents.risk_scoring import RiskScoringAgent
from aml_triage.agents.context_builder import ContextBuilderAgent
from aml_triage.agents.decision_maker import DecisionMakerAgent


class WorkflowState:
    """Track workflow state for an alert."""

    def __init__(self, alert: Alert):
        self.alert = alert
        self.enrichment_result = None
        self.risk_assessment = None
        self.context_narrative = None
        self.decision = None
        self.start_time = datetime.now()
        self.stage_times: Dict[str, float] = {}

    def update(self, stage: str, result: Any) -> None:
        """Update workflow state with stage result."""
        setattr(self, f"{stage}_result", result)

        # Track stage completion time
        stage_duration = (datetime.now() - self.start_time).total_seconds() * 1000
        self.stage_times[stage] = stage_duration

    def get_total_processing_time(self) -> int:
        """Get total processing time in milliseconds."""
        return int((datetime.now() - self.start_time).total_seconds() * 1000)


class SupervisorAgent:
    """
    Supervisor Agent - Coordinates the entire alert triage workflow.

    Responsibilities:
    - Receive and validate incoming alerts
    - Orchestrate specialist agent execution
    - Aggregate outputs and ensure quality
    - Determine final escalation
    - Generate comprehensive audit trails
    - Handle failure recovery
    """

    def __init__(self):
        self.logger = get_logger("supervisor_agent")

        # Initialize specialist agents
        self.data_enrichment_agent = DataEnrichmentAgent()
        self.risk_scoring_agent = RiskScoringAgent()
        self.context_builder_agent = ContextBuilderAgent()
        self.decision_maker_agent = DecisionMakerAgent()

        self.logger.info("supervisor_agent_initialized")

    async def process_alert(self, alert: Alert) -> Decision:
        """
        Process alert through the complete multi-agent workflow.

        Args:
            alert: Alert to process

        Returns:
            Final decision with complete audit trail

        Raises:
            CriticalAgentException: If workflow fails critically
        """
        self.logger.info(
            "starting_alert_processing",
            alert_id=alert.alert_id,
            alert_type=alert.alert_type.value,
            priority=alert.priority.value,
        )

        # Initialize workflow state and audit trail
        workflow_state = WorkflowState(alert)
        audit_trail = AuditTrail(alert.alert_id)

        try:
            # Stage 1: Data Enrichment
            self.logger.info("workflow_stage_enrichment", alert_id=alert.alert_id)
            enrichment_result = await self.data_enrichment_agent.execute(
                alert.alert_id, alert
            )
            workflow_state.update("enrichment", enrichment_result)
            audit_trail.log_entry(
                agent="data_enrichment_agent",
                action="data_enrichment_completed",
                input_data=alert,
                output_data=enrichment_result,
                metadata={"sources_used": enrichment_result.sources_used},
            )

            # Stage 2: Risk Scoring
            self.logger.info("workflow_stage_risk_scoring", alert_id=alert.alert_id)
            risk_assessment = await self.risk_scoring_agent.execute(
                alert.alert_id, alert, enrichment_result
            )
            workflow_state.update("risk_assessment", risk_assessment)
            audit_trail.log_entry(
                agent="risk_scoring_agent",
                action="risk_scoring_completed",
                input_data={"alert": alert, "enrichment": enrichment_result},
                output_data=risk_assessment,
                metadata={
                    "risk_score": risk_assessment.overall_risk_score,
                    "risk_level": risk_assessment.risk_level.value,
                },
            )

            # Stage 3: Context Building
            self.logger.info("workflow_stage_context_building", alert_id=alert.alert_id)
            context_narrative = await self.context_builder_agent.execute(
                alert.alert_id, alert, enrichment_result, risk_assessment
            )
            workflow_state.update("context", context_narrative)
            audit_trail.log_entry(
                agent="context_builder_agent",
                action="context_building_completed",
                input_data={
                    "alert": alert,
                    "enrichment": enrichment_result,
                    "risk": risk_assessment,
                },
                output_data=context_narrative,
                metadata={"confidence": context_narrative.confidence_score},
            )

            # Stage 4: Decision Making
            self.logger.info("workflow_stage_decision_making", alert_id=alert.alert_id)
            decision = await self.decision_maker_agent.execute(
                alert.alert_id,
                alert,
                enrichment_result,
                risk_assessment,
                context_narrative,
            )
            workflow_state.update("decision", decision)
            audit_trail.log_entry(
                agent="decision_maker_agent",
                action="decision_made",
                input_data={
                    "alert": alert,
                    "enrichment": enrichment_result,
                    "risk": risk_assessment,
                    "context": context_narrative,
                },
                output_data=decision,
                metadata={
                    "disposition": decision.disposition.value,
                    "confidence": decision.confidence_score,
                },
            )

            # Stage 5: Finalize decision with audit trail and processing time
            final_decision = await self._finalize_decision(
                decision, workflow_state, audit_trail
            )

            self.logger.info(
                "alert_processing_completed",
                alert_id=alert.alert_id,
                disposition=final_decision.disposition.value,
                processing_time_ms=final_decision.processing_time_ms,
                requires_human_review=final_decision.requires_human_review,
            )

            return final_decision

        except CriticalAgentException as e:
            self.logger.error(
                "workflow_failed_critically",
                alert_id=alert.alert_id,
                error=str(e),
                exc_info=True,
            )

            # Create emergency escalation decision
            emergency_decision = self._create_emergency_escalation(
                alert, workflow_state, str(e)
            )
            return emergency_decision

        except Exception as e:
            self.logger.error(
                "workflow_failed_unexpectedly",
                alert_id=alert.alert_id,
                error=str(e),
                exc_info=True,
            )

            # Create emergency escalation
            emergency_decision = self._create_emergency_escalation(
                alert, workflow_state, str(e)
            )
            return emergency_decision

    async def _finalize_decision(
        self, decision: Decision, workflow_state: WorkflowState, audit_trail: AuditTrail
    ) -> Decision:
        """
        Finalize decision with audit trail and metadata.

        Args:
            decision: Initial decision
            workflow_state: Workflow state
            audit_trail: Audit trail

        Returns:
            Finalized decision
        """
        # Update processing time
        decision.processing_time_ms = workflow_state.get_total_processing_time()

        # Add audit trail to decision
        decision.audit_trail = audit_trail.get_timeline()

        # Add system metadata
        decision.system_version = "0.1.0"

        return decision

    def _create_emergency_escalation(
        self, alert: Alert, workflow_state: WorkflowState, error: str
    ) -> Decision:
        """
        Create emergency escalation decision when workflow fails.

        Args:
            alert: Original alert
            workflow_state: Current workflow state
            error: Error message

        Returns:
            Emergency escalation decision
        """
        from aml_triage.models.decision import (
            DecisionFactors,
            EscalationDetails,
            EscalationPriority,
        )

        return Decision(
            alert_id=alert.alert_id,
            disposition=DecisionDisposition.ESCALATE_L3,
            confidence_score=0.0,
            rationale=f"Emergency escalation due to system error: {error}. Human review required.",
            risk_score=100,  # Maximum risk for safety
            decision_factors=DecisionFactors(
                primary_factors=["System error during processing"],
                supporting_factors=[],
                contrary_evidence=[],
                uncertainty_factors=["Unable to complete automated analysis"],
            ),
            escalation_details=EscalationDetails(
                requires_human_review=True,
                escalation_reason=f"System error: {error}",
                priority=EscalationPriority.URGENT,
                suggested_reviewer="Senior Compliance Officer",
            ),
            requires_human_review=True,
            processing_time_ms=workflow_state.get_total_processing_time(),
        )

    async def process_alert_batch(self, alerts: list[Alert]) -> list[Decision]:
        """
        Process multiple alerts concurrently.

        Args:
            alerts: List of alerts to process

        Returns:
            List of decisions
        """
        self.logger.info("processing_alert_batch", batch_size=len(alerts))

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(settings.max_concurrent_alerts)

        async def process_with_limit(alert: Alert) -> Decision:
            async with semaphore:
                return await self.process_alert(alert)

        # Process all alerts concurrently with limit
        results = await asyncio.gather(
            *[process_with_limit(alert) for alert in alerts],
            return_exceptions=True,
        )

        # Log summary
        success_count = sum(
            1 for r in results if isinstance(r, Decision)
        )
        self.logger.info(
            "batch_processing_completed",
            total_alerts=len(alerts),
            successful=success_count,
            failed=len(alerts) - success_count,
        )

        return results

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status.

        Returns:
            System status information
        """
        return {
            "supervisor": "ACTIVE",
            "agents": {
                "data_enrichment": self.data_enrichment_agent.get_state(),
                "risk_scoring": self.risk_scoring_agent.get_state(),
                "context_builder": self.context_builder_agent.get_state(),
                "decision_maker": self.decision_maker_agent.get_state(),
            },
            "configuration": {
                "max_concurrent_alerts": settings.max_concurrent_alerts,
                "auto_clear_threshold": settings.auto_clear_threshold,
                "escalate_l2_threshold": settings.escalate_l2_threshold,
            },
        }
