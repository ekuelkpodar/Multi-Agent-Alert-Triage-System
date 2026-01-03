"""Main Alert Triage System interface."""

from typing import List
from datetime import datetime

from aml_triage.core.config import settings
from aml_triage.core.logging import setup_logging, get_logger
from aml_triage.models.alert import Alert
from aml_triage.models.decision import Decision
from aml_triage.agents.supervisor import SupervisorAgent


class AlertTriageSystem:
    """
    Main interface for the AML Alert Triage System.

    This is the primary entry point for processing alerts through
    the multi-agent workflow.
    """

    def __init__(self):
        """Initialize the alert triage system."""
        # Setup logging
        setup_logging()
        self.logger = get_logger("alert_triage_system")

        # Initialize supervisor agent
        self.supervisor = SupervisorAgent()

        self.logger.info(
            "alert_triage_system_initialized",
            version="0.1.0",
            models={
                "supervisor": settings.supervisor_model,
                "data_enrichment": settings.data_enrichment_model,
                "risk_scoring": settings.risk_scoring_model,
                "context_builder": settings.context_builder_model,
                "decision_maker": settings.decision_maker_model,
            },
        )

    async def process_alert(self, alert: Alert) -> Decision:
        """
        Process a single alert through the multi-agent workflow.

        Args:
            alert: Alert to process

        Returns:
            Decision with complete analysis and audit trail

        Example:
            ```python
            system = AlertTriageSystem()

            alert = Alert(
                alert_type=AlertType.SANCTIONS,
                priority=AlertPriority.HIGH,
                customer_data=CustomerData(...),
                screening_results=ScreeningResults(...),
                regulatory_context=RegulatoryContext(...)
            )

            decision = await system.process_alert(alert)
            print(f"Disposition: {decision.disposition}")
            print(f"Risk Score: {decision.risk_score}")
            ```
        """
        self.logger.info(
            "processing_alert",
            alert_id=alert.alert_id,
            alert_type=alert.alert_type.value,
        )

        start_time = datetime.now()

        try:
            decision = await self.supervisor.process_alert(alert)

            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(
                "alert_processed_successfully",
                alert_id=alert.alert_id,
                disposition=decision.disposition.value,
                processing_time_seconds=processing_time,
            )

            return decision

        except Exception as e:
            self.logger.error(
                "alert_processing_failed",
                alert_id=alert.alert_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def process_alert_batch(self, alerts: List[Alert]) -> List[Decision]:
        """
        Process multiple alerts concurrently.

        Args:
            alerts: List of alerts to process

        Returns:
            List of decisions

        Example:
            ```python
            system = AlertTriageSystem()
            alerts = [alert1, alert2, alert3]
            decisions = await system.process_alert_batch(alerts)
            ```
        """
        self.logger.info("processing_alert_batch", batch_size=len(alerts))

        decisions = await self.supervisor.process_alert_batch(alerts)

        return decisions

    def get_system_status(self) -> dict:
        """
        Get current system status and health.

        Returns:
            System status dictionary

        Example:
            ```python
            system = AlertTriageSystem()
            status = system.get_system_status()
            print(f"System status: {status['supervisor']}")
            ```
        """
        return self.supervisor.get_system_status()

    def get_performance_metrics(self) -> dict:
        """
        Get system performance metrics.

        Returns:
            Performance metrics dictionary
        """
        # In production, this would query metrics from monitoring system
        return {
            "metrics_available": False,
            "message": "Connect to Prometheus for metrics",
        }
