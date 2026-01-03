"""Unit tests for audit trail functionality."""

import pytest
from datetime import datetime

from aml_triage.core.audit import AuditTrail, AuditEntry


class TestAuditTrail:
    """Test AuditTrail functionality."""

    def test_initialization(self):
        """Test audit trail initialization."""
        trail = AuditTrail("alert-123")

        assert trail.alert_id == "alert-123"
        assert len(trail.entries) == 0
        assert trail.created_at is not None

    def test_log_entry(self):
        """Test logging an audit entry."""
        trail = AuditTrail("alert-123")

        trail.log_entry(
            agent="test_agent",
            action="test_action",
            input_data={"test": "input"},
            output_data={"test": "output"},
            metadata={"key": "value"},
        )

        assert len(trail.entries) == 1
        entry = trail.entries[0]
        assert entry.agent == "test_agent"
        assert entry.action == "test_action"
        assert entry.metadata["key"] == "value"

    def test_get_summary(self):
        """Test getting audit trail summary."""
        trail = AuditTrail("alert-123")

        trail.log_entry("agent1", "action1", {}, {})
        trail.log_entry("agent2", "action2", {}, {})
        trail.log_entry("agent1", "action3", {}, {})

        summary = trail.get_summary()

        assert summary["alert_id"] == "alert-123"
        assert summary["total_entries"] == 3
        assert set(summary["agents_involved"]) == {"agent1", "agent2"}

    def test_get_timeline(self):
        """Test getting chronological timeline."""
        trail = AuditTrail("alert-123")

        trail.log_entry("agent1", "action1", {}, {})
        trail.log_entry("agent2", "action2", {}, {})

        timeline = trail.get_timeline()

        assert len(timeline) == 2
        assert all("timestamp" in entry for entry in timeline)
        assert all("agent" in entry for entry in timeline)

    def test_get_decision_chain(self):
        """Test getting decision chain."""
        trail = AuditTrail("alert-123")

        trail.log_entry("enrichment_agent", "data_enriched", {}, {})
        trail.log_entry("risk_agent", "risk_calculated", {}, {})
        trail.log_entry("decision_agent", "decision_made", {}, {})

        decision_chain = trail.get_decision_chain()

        assert len(decision_chain) == 2  # risk and decision
        assert any("risk" in entry["action"].lower() for entry in decision_chain)
        assert any("decision" in entry["action"].lower() for entry in decision_chain)

    def test_generate_audit_report(self):
        """Test generating comprehensive audit report."""
        trail = AuditTrail("alert-123")

        trail.log_entry(
            "test_agent",
            "test_action",
            {"input": "data"},
            {"output": "data"},
            metadata={"sources": ["source1", "source2"]},
        )

        report = trail.generate_audit_report()

        assert "alert_id" in report
        assert "alert_summary" in report
        assert "workflow_timeline" in report
        assert "data_sources" in report
        assert "generated_at" in report

    def test_export_for_regulator(self):
        """Test exporting audit trail for regulatory review."""
        trail = AuditTrail("alert-123")

        trail.log_entry("agent", "action", {}, {})

        export = trail.export_for_regulator()

        assert isinstance(export, str)
        assert "alert-123" in export
