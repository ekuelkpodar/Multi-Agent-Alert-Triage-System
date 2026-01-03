"""Integration tests for complete workflow."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from aml_triage import AlertTriageSystem
from aml_triage.models.alert import (
    Alert,
    AlertType,
    AlertPriority,
    CustomerData,
    EntityType,
    Address,
    ScreeningResults,
    MatchDetail,
    RegulatoryContext,
)
from aml_triage.models.decision import DecisionDisposition


def create_test_alert() -> Alert:
    """Create a test alert for integration testing."""
    return Alert(
        alert_type=AlertType.SANCTIONS,
        priority=AlertPriority.HIGH,
        customer_data=CustomerData(
            customer_id="TEST-001",
            name="Test Customer",
            aliases=[],
            entity_type=EntityType.INDIVIDUAL,
            addresses=[
                Address(
                    city="Test City",
                    country="USA",
                )
            ],
        ),
        screening_results=ScreeningResults(
            match_details=[
                MatchDetail(
                    source="OFAC",
                    match_type="NAME",
                    matched_name="Test Customer",
                    match_score=0.85,
                    list_name="SDN",
                )
            ],
            match_scores=[0.85],
            data_sources=["OFAC"],
        ),
        regulatory_context=RegulatoryContext(
            jurisdiction="USA",
            applicable_regulations=["BSA", "OFAC"],
        ),
    )


class TestWorkflowIntegration:
    """Integration tests for the complete multi-agent workflow."""

    @pytest.mark.asyncio
    @patch("aml_triage.core.base_agent.AsyncAnthropic")
    async def test_complete_workflow(self, mock_anthropic):
        """Test complete alert processing workflow."""

        # Mock LLM responses
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text="Test analysis response with comprehensive risk assessment and recommendations."
            )
        ]

        mock_client = Mock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        # Create system and alert
        system = AlertTriageSystem()
        alert = create_test_alert()

        # Process alert
        decision = await system.process_alert(alert)

        # Verify decision structure
        assert decision.alert_id == alert.alert_id
        assert isinstance(decision.disposition, DecisionDisposition)
        assert 0 <= decision.risk_score <= 100
        assert 0 <= decision.confidence_score <= 1
        assert decision.rationale is not None
        assert len(decision.audit_trail) > 0

    @pytest.mark.asyncio
    @patch("aml_triage.core.base_agent.AsyncAnthropic")
    async def test_batch_processing(self, mock_anthropic):
        """Test batch processing of multiple alerts."""

        # Mock LLM responses
        mock_response = Mock()
        mock_response.content = [Mock(text="Test batch response")]

        mock_client = Mock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        # Create system and alerts
        system = AlertTriageSystem()
        alerts = [create_test_alert() for _ in range(3)]

        # Process batch
        decisions = await system.process_alert_batch(alerts)

        # Verify all alerts were processed
        assert len(decisions) == 3
        assert all(hasattr(d, "disposition") for d in decisions)

    def test_system_initialization(self):
        """Test system initialization."""
        system = AlertTriageSystem()

        status = system.get_system_status()

        assert "supervisor" in status
        assert "agents" in status
        assert "configuration" in status

    @pytest.mark.asyncio
    @patch("aml_triage.core.base_agent.AsyncAnthropic")
    async def test_high_risk_escalation(self, mock_anthropic):
        """Test that high-risk alerts are properly escalated."""

        # Mock LLM with high-risk assessment
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text="High risk assessment due to direct sanctions match with adverse media. Immediate escalation required."
            )
        ]

        mock_client = Mock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        system = AlertTriageSystem()
        alert = create_test_alert()

        # Set high match score to trigger escalation
        alert.screening_results.match_scores = [0.98]

        decision = await system.process_alert(alert)

        # High-risk alerts should require human review
        assert decision.requires_human_review is True
        assert decision.escalation_details is not None
