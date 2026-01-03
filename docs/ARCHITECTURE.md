# System Architecture

## Overview

The AML Alert Triage System uses a hierarchical multi-agent architecture where specialized AI agents collaborate to process compliance alerts automatically.

## Agent Hierarchy

```
┌─────────────────────────────────────────────┐
│       Supervisor Agent (Orchestrator)       │
│  - Workflow coordination                    │
│  - Escalation routing                       │
│  - Quality assurance                        │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┬───────────┬──────────┐
       │               │           │          │
┌──────▼──────┐ ┌─────▼─────┐ ┌──▼────┐ ┌───▼─────┐
│ Data        │ │ Risk      │ │Context│ │Decision │
│ Enrichment  │ │ Scoring   │ │Builder│ │Maker    │
│ Agent       │ │ Agent     │ │Agent  │ │Agent    │
└─────────────┘ └───────────┘ └───────┘ └─────────┘
```

## Agent Responsibilities

### Supervisor Agent
- **Purpose**: Orchestrate the entire workflow
- **Model**: Claude Sonnet 4.5
- **Temperature**: 0.1
- **Key Functions**:
  - Receive and validate alerts
  - Route to specialist agents
  - Aggregate outputs
  - Manage audit trail
  - Handle errors and retries

### Data Enrichment Agent
- **Purpose**: Augment alerts with additional context
- **Model**: Claude Haiku 4.5 (optimized for speed)
- **Temperature**: 0.2
- **Data Sources**:
  - Historical alert database
  - Customer relationship management (CRM)
  - Transaction monitoring systems
  - External sanctions lists (OFAC, UN, EU)
  - Adverse media feeds
  - Corporate registries

### Risk Scoring Agent
- **Purpose**: Calculate comprehensive risk scores
- **Model**: Claude Sonnet 4.5
- **Temperature**: 0.15
- **Scoring Components**:
  - Customer Risk (30%)
  - Geographic Risk (20%)
  - Transaction Risk (25%)
  - Adverse Media Risk (15%)
  - Network Risk (10%)

### Context Builder Agent
- **Purpose**: Synthesize data into narratives
- **Model**: Claude Sonnet 4.5
- **Temperature**: 0.3
- **Outputs**:
  - Executive summaries
  - Detailed narratives
  - Investigation guidance
  - Regulatory documentation

### Decision Maker Agent
- **Purpose**: Make final disposition decisions
- **Model**: Claude Opus 4.5 (highest reasoning)
- **Temperature**: 0.05 (maximum determinism)
- **Decision Types**:
  - AUTO_CLEAR
  - ESCALATE_L2
  - ESCALATE_L3
  - ESCALATE_SAR
  - BLOCK_TRANSACTION

## Workflow Stages

### Stage 1: Data Enrichment
1. Receive alert from screening system
2. Query internal systems for customer history
3. Fetch external data (adverse media, sanctions)
4. Assess data quality and completeness
5. Generate enrichment summary

**Output**: EnrichmentResult with comprehensive context

### Stage 2: Risk Scoring
1. Apply regulatory risk framework
2. Calculate component scores
3. Compute weighted risk score
4. Identify mitigating/aggravating factors
5. Generate risk narrative with citations

**Output**: RiskAssessment with detailed scoring

### Stage 3: Context Building
1. Synthesize enrichment and risk data
2. Create executive summary
3. Build investigation timeline
4. Generate regulatory documentation
5. Provide investigation guidance

**Output**: ContextNarrative with complete documentation

### Stage 4: Decision Making
1. Evaluate all evidence
2. Apply decision matrix
3. Determine disposition
4. Check escalation triggers
5. Generate audit-ready rationale

**Output**: Decision with recommended actions

### Stage 5: Finalization
1. Aggregate all agent outputs
2. Complete audit trail
3. Calculate processing metrics
4. Route to appropriate destination
5. Notify relevant stakeholders

**Output**: Complete Decision object

## Data Flow

```
Alert Input
    ↓
[Supervisor receives alert]
    ↓
[Data Enrichment Agent]
    ├─→ Historical data
    ├─→ External sources
    └─→ Quality assessment
    ↓
EnrichmentResult
    ↓
[Risk Scoring Agent]
    ├─→ Component scores
    ├─→ Risk factors
    └─→ Regulatory citations
    ↓
RiskAssessment
    ↓
[Context Builder Agent]
    ├─→ Narrative synthesis
    ├─→ Timeline creation
    └─→ Investigation guidance
    ↓
ContextNarrative
    ↓
[Decision Maker Agent]
    ├─→ Decision matrix
    ├─→ Escalation check
    └─→ Rationale generation
    ↓
Decision Output
```

## Error Handling

### Retry Logic
- Agents automatically retry on transient failures
- Exponential backoff (2s, 4s, 8s)
- Maximum 3 retry attempts
- Critical errors skip retry

### Failure Recovery
- Agent failures trigger emergency escalation
- Partial results are preserved
- Human review automatically required
- Complete audit trail maintained

### Escalation Triggers
- Agent timeout (>30s)
- Confidence below threshold (<0.70)
- Data completeness insufficient (<0.60)
- Critical regulatory flags
- Novel patterns not in training data

## Performance Optimization

### Parallel Processing
- Independent agents can run concurrently
- Risk Scoring and Context Building parallelized
- Batch processing for multiple alerts
- Semaphore limits concurrent executions

### Caching Strategy
- Historical data cached in Redis
- External API responses cached
- 15-minute TTL for data freshness
- Cache invalidation on updates

### Resource Management
- Agent pooling for scalability
- Auto-scaling based on queue depth
- Graceful degradation under load
- Circuit breakers for external APIs

## Security & Compliance

### Data Protection
- PII encryption at rest
- Anonymized logging
- Access control with RBAC
- Audit trail immutability

### Regulatory Alignment
- BSA/AML compliance built-in
- OFAC requirements enforced
- FinCEN guidance integrated
- SAR filing considerations

### Audit Trail
- Complete decision lineage
- Data source tracking
- Version control for agents
- Regulatory export format

## Monitoring & Observability

### Key Metrics
- Processing time per alert
- Agent-level latency
- Confidence score distribution
- Disposition breakdown
- Human override rate

### Alerting Thresholds
- P95 latency > 10s
- Error rate > 5%
- Confidence < 70%
- Queue depth > 500

### Logging
- Structured JSON logging
- Correlation IDs for tracing
- Performance metrics
- Compliance events

## Deployment Architecture

### Infrastructure
- Kubernetes for orchestration
- PostgreSQL for persistence
- Redis for caching
- RabbitMQ for messaging

### Scalability
- Horizontal pod autoscaling
- Load balancing across agents
- Database connection pooling
- Message queue partitioning

### High Availability
- Multi-region deployment
- Database replication
- Failover automation
- Disaster recovery procedures
