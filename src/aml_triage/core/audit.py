"""Audit trail system for regulatory compliance."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from hashlib import sha256
import json

from pydantic import BaseModel, Field


class AuditEntry(BaseModel):
    """Single audit trail entry."""

    timestamp: datetime = Field(default_factory=datetime.now)
    agent: str
    action: str
    input_hash: str
    output_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    system_versions: Dict[str, str] = Field(default_factory=dict)


class AuditTrail:
    """
    Comprehensive audit trail for regulatory compliance.

    Tracks all agent actions, data transformations, and decisions
    with immutable logging for regulatory review.
    """

    def __init__(self, alert_id: str):
        """
        Initialize audit trail for an alert.

        Args:
            alert_id: Unique alert identifier
        """
        self.alert_id = alert_id
        self.entries: List[AuditEntry] = []
        self.created_at = datetime.now()

    def log_entry(
        self,
        agent: str,
        action: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an audit entry.

        Args:
            agent: Name of the agent performing the action
            action: Description of the action
            input_data: Input data (will be hashed)
            output_data: Output data (will be hashed)
            metadata: Additional metadata to log
        """
        entry = AuditEntry(
            agent=agent,
            action=action,
            input_hash=self._hash_data(input_data),
            output_hash=self._hash_data(output_data),
            metadata=metadata or {},
            system_versions=self._get_system_versions(),
        )
        self.entries.append(entry)

    def _hash_data(self, data: Any) -> str:
        """
        Create a hash of data for audit purposes.

        Args:
            data: Data to hash

        Returns:
            SHA256 hash of the data
        """
        # Convert data to JSON string for consistent hashing
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, default=str)
        elif hasattr(data, "model_dump_json"):
            data_str = data.model_dump_json()
        else:
            data_str = str(data)

        return sha256(data_str.encode()).hexdigest()

    def _get_system_versions(self) -> Dict[str, str]:
        """
        Get current system component versions.

        Returns:
            Dictionary of component versions
        """
        # In production, this would pull actual version numbers
        return {
            "system_version": "0.1.0",
            "models_version": "0.1.0",
            "agents_version": "0.1.0",
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of the audit trail.

        Returns:
            Summary dictionary
        """
        return {
            "alert_id": self.alert_id,
            "created_at": self.created_at.isoformat(),
            "total_entries": len(self.entries),
            "agents_involved": list(set(e.agent for e in self.entries)),
            "actions": list(set(e.action for e in self.entries)),
        }

    def get_timeline(self) -> List[Dict[str, Any]]:
        """
        Get chronological timeline of audit entries.

        Returns:
            List of audit entries in chronological order
        """
        return [
            {
                "timestamp": entry.timestamp.isoformat(),
                "agent": entry.agent,
                "action": entry.action,
                "metadata": entry.metadata,
            }
            for entry in sorted(self.entries, key=lambda e: e.timestamp)
        ]

    def get_decision_chain(self) -> List[Dict[str, Any]]:
        """
        Get the decision chain showing how the final decision was reached.

        Returns:
            List of decision-related audit entries
        """
        decision_keywords = ["decision", "risk", "score", "classification", "escalate"]

        decision_entries = [
            {
                "timestamp": entry.timestamp.isoformat(),
                "agent": entry.agent,
                "action": entry.action,
                "metadata": entry.metadata,
            }
            for entry in self.entries
            if any(keyword in entry.action.lower() for keyword in decision_keywords)
        ]

        return sorted(decision_entries, key=lambda e: e["timestamp"])

    def get_data_sources(self) -> List[str]:
        """
        Get all data sources consulted during processing.

        Returns:
            List of unique data sources
        """
        sources = set()
        for entry in self.entries:
            if "sources" in entry.metadata:
                sources.update(entry.metadata["sources"])
            if "data_source" in entry.metadata:
                sources.add(entry.metadata["data_source"])

        return sorted(list(sources))

    def get_compliance_checks(self) -> List[Dict[str, Any]]:
        """
        Get all regulatory compliance checks performed.

        Returns:
            List of compliance check results
        """
        compliance_entries = [
            {
                "timestamp": entry.timestamp.isoformat(),
                "agent": entry.agent,
                "action": entry.action,
                "result": entry.metadata.get("compliance_result"),
                "regulations": entry.metadata.get("regulations", []),
            }
            for entry in self.entries
            if "compliance" in entry.action.lower()
            or "regulatory" in entry.action.lower()
        ]

        return compliance_entries

    def get_system_metadata(self) -> Dict[str, Any]:
        """
        Get system metadata for the audit trail.

        Returns:
            System metadata dictionary
        """
        if self.entries:
            return self.entries[0].system_versions
        return {}

    def generate_audit_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive audit report.

        Returns:
            Complete audit report with all relevant information
        """
        return {
            "alert_id": self.alert_id,
            "alert_summary": self.get_summary(),
            "workflow_timeline": self.get_timeline(),
            "decision_chain": self.get_decision_chain(),
            "data_sources": self.get_data_sources(),
            "regulatory_compliance": self.get_compliance_checks(),
            "system_metadata": self.get_system_metadata(),
            "generated_at": datetime.now().isoformat(),
        }

    def export_for_regulator(self) -> str:
        """
        Export audit trail in regulator-friendly format.

        Returns:
            JSON string of the audit report
        """
        report = self.generate_audit_report()
        return json.dumps(report, indent=2, default=str)
