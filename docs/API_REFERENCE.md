# API Reference

## AlertTriageSystem

Main interface for the AML Alert Triage System.

### Initialization

```python
from aml_triage import AlertTriageSystem

system = AlertTriageSystem()
```

### Methods

#### process_alert(alert: Alert) → Decision

Process a single alert through the multi-agent workflow.

**Parameters:**
- `alert` (Alert): Alert object to process

**Returns:**
- `Decision`: Complete decision with risk assessment and audit trail

**Example:**
```python
decision = await system.process_alert(alert)
print(f"Disposition: {decision.disposition}")
print(f"Risk Score: {decision.risk_score}")
```

#### process_alert_batch(alerts: List[Alert]) → List[Decision]

Process multiple alerts concurrently.

**Parameters:**
- `alerts` (List[Alert]): List of alerts to process

**Returns:**
- `List[Decision]`: List of decisions

**Example:**
```python
decisions = await system.process_alert_batch([alert1, alert2, alert3])
```

#### get_system_status() → dict

Get current system status and health.

**Returns:**
- `dict`: System status information

**Example:**
```python
status = system.get_system_status()
```

## Models

### Alert

Main alert data structure.

**Fields:**
- `alert_id` (str): Unique alert identifier
- `alert_type` (AlertType): Type of alert (SANCTIONS, PEP, etc.)
- `priority` (AlertPriority): Priority level
- `customer_data` (CustomerData): Customer information
- `screening_results` (ScreeningResults): Screening match details
- `regulatory_context` (RegulatoryContext): Regulatory information
- `timestamp` (datetime): Alert creation timestamp

**Example:**
```python
alert = Alert(
    alert_type=AlertType.SANCTIONS,
    priority=AlertPriority.HIGH,
    customer_data=CustomerData(...),
    screening_results=ScreeningResults(...),
    regulatory_context=RegulatoryContext(...)
)
```

### Decision

Final decision output.

**Fields:**
- `alert_id` (str): Alert identifier
- `disposition` (DecisionDisposition): Final disposition
- `confidence_score` (float): Decision confidence (0-1)
- `rationale` (str): Human-readable rationale
- `risk_score` (int): Overall risk score (0-100)
- `supporting_evidence` (List): Supporting evidence
- `regulatory_citations` (List[str]): Regulatory citations
- `recommended_actions` (List[RecommendedAction]): Next steps
- `requires_human_review` (bool): Human review required
- `audit_trail` (List): Complete audit trail
- `processing_time_ms` (int): Processing time in milliseconds

**Example:**
```python
print(f"Disposition: {decision.disposition}")
print(f"Risk Score: {decision.risk_score}/100")
print(f"Confidence: {decision.confidence_score:.2%}")
print(f"Rationale: {decision.rationale}")
```

### AlertType

Enumeration of alert types.

**Values:**
- `SANCTIONS`: Sanctions screening alert
- `PEP`: Politically Exposed Person
- `ADVERSE_MEDIA`: Adverse media match
- `TRANSACTION`: Transaction monitoring alert
- `KYC_ONGOING`: Ongoing KYC review

### DecisionDisposition

Enumeration of decision outcomes.

**Values:**
- `AUTO_CLEAR`: Automatically cleared (low risk)
- `ESCALATE_L2`: Escalate to L2 analyst
- `ESCALATE_L3`: Escalate to L3/senior analyst
- `ESCALATE_SAR`: Escalate for SAR filing
- `BLOCK_TRANSACTION`: Block transaction immediately

### RiskLevel

Risk categorization.

**Values:**
- `LOW`: Risk score 0-30
- `MEDIUM`: Risk score 31-60
- `HIGH`: Risk score 61-80
- `SEVERE`: Risk score 81-100

## Configuration

### Environment Variables

**LLM Configuration:**
- `ANTHROPIC_API_KEY`: Anthropic API key (required)
- `OPENAI_API_KEY`: OpenAI API key (optional)

**Model Selection:**
- `SUPERVISOR_MODEL`: Supervisor agent model
- `DATA_ENRICHMENT_MODEL`: Data enrichment model
- `RISK_SCORING_MODEL`: Risk scoring model
- `CONTEXT_BUILDER_MODEL`: Context builder model
- `DECISION_MAKER_MODEL`: Decision maker model

**Thresholds:**
- `AUTO_CLEAR_THRESHOLD`: Confidence for auto-clear (default: 0.85)
- `ESCALATE_L2_THRESHOLD`: Confidence for L2 (default: 0.70)
- `RISK_SCORE_HIGH_THRESHOLD`: Risk score for HIGH (default: 70)
- `RISK_SCORE_SEVERE_THRESHOLD`: Risk score for SEVERE (default: 85)

**Performance:**
- `MAX_CONCURRENT_ALERTS`: Max concurrent processing (default: 10)
- `AGENT_TIMEOUT_SECONDS`: Agent timeout (default: 30)
- `MAX_RETRIES`: Max retry attempts (default: 3)

## Error Handling

### Exceptions

#### AgentException
Base exception for agent errors.

#### RetryableAgentException
Exception that triggers automatic retry.

#### CriticalAgentException
Critical exception that requires immediate escalation.

**Example:**
```python
try:
    decision = await system.process_alert(alert)
except CriticalAgentException as e:
    # Handle critical failure
    logger.error(f"Critical failure: {e}")
```

## Audit Trail

### AuditTrail

Tracks all processing steps for regulatory compliance.

**Methods:**
- `log_entry()`: Log an audit entry
- `get_summary()`: Get audit summary
- `get_timeline()`: Get chronological timeline
- `get_decision_chain()`: Get decision chain
- `generate_audit_report()`: Generate complete report
- `export_for_regulator()`: Export in regulator format

**Example:**
```python
audit_trail = decision.audit_trail
for entry in audit_trail:
    print(f"{entry['timestamp']}: {entry['agent']} - {entry['action']}")
```

## Best Practices

### Alert Processing
1. Always use try-except for error handling
2. Check `requires_human_review` flag
3. Review confidence scores
4. Validate audit trail completeness

### Batch Processing
1. Limit batch size to avoid timeout
2. Monitor concurrent processing
3. Handle partial failures gracefully
4. Track batch completion metrics

### Performance
1. Use batch processing for multiple alerts
2. Monitor processing times
3. Configure appropriate timeouts
4. Scale based on queue depth

### Compliance
1. Always review audit trails
2. Preserve complete decision lineage
3. Export audit reports for regulators
4. Document system configuration changes
