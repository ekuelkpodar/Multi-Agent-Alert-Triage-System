# Getting Started

## Installation

### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)
- Anthropic API key

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Multi-Agent
```

### Step 2: Install Dependencies

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Required configuration:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DATABASE_URL=postgresql://localhost:5432/aml_triage
REDIS_URL=redis://localhost:6379/0
```

### Step 4: Verify Installation

```bash
# Run tests to verify installation
poetry run pytest

# Check system status
poetry run python -c "from aml_triage import AlertTriageSystem; print('Installation successful!')"
```

## Quick Start

### Basic Usage

Create a file `my_first_alert.py`:

```python
import asyncio
from datetime import datetime
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

async def main():
    # Initialize the system
    system = AlertTriageSystem()

    # Create an alert
    alert = Alert(
        alert_type=AlertType.SANCTIONS,
        priority=AlertPriority.HIGH,
        customer_data=CustomerData(
            customer_id="CUST-001",
            name="John Doe",
            entity_type=EntityType.INDIVIDUAL,
            addresses=[Address(country="USA")]
        ),
        screening_results=ScreeningResults(
            match_details=[
                MatchDetail(
                    source="OFAC",
                    match_type="NAME",
                    matched_name="John Doe",
                    match_score=0.85,
                    list_name="SDN"
                )
            ],
            match_scores=[0.85],
            data_sources=["OFAC"]
        ),
        regulatory_context=RegulatoryContext(
            jurisdiction="USA",
            applicable_regulations=["BSA", "OFAC"]
        )
    )

    # Process the alert
    decision = await system.process_alert(alert)

    # Display results
    print(f"Disposition: {decision.disposition.value}")
    print(f"Risk Score: {decision.risk_score}/100")
    print(f"Confidence: {decision.confidence_score:.2%}")
    print(f"\nRationale:\n{decision.rationale}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
poetry run python my_first_alert.py
```

## Examples

The `examples/` directory contains several example scripts:

### Basic Usage
```bash
poetry run python examples/basic_usage.py
```

Demonstrates single alert processing with detailed output.

### Batch Processing
```bash
poetry run python examples/batch_processing.py
```

Shows how to process multiple alerts concurrently.

## Understanding the Output

### Decision Object

The system returns a `Decision` object with:

- **disposition**: The final decision (AUTO_CLEAR, ESCALATE_L2, etc.)
- **risk_score**: Overall risk (0-100)
- **confidence_score**: Confidence in decision (0-1)
- **rationale**: Human-readable explanation
- **recommended_actions**: Next steps to take
- **audit_trail**: Complete processing history

### Example Output

```
Disposition: ESCALATE_L2
Risk Score: 65/100
Confidence: 78%
Requires Human Review: True
Processing Time: 2847ms

Rationale:
Customer matched OFAC SDN list with 85% confidence. The entity
is located in a medium-risk jurisdiction. Further investigation
needed to verify identity match and assess true positive likelihood.
Risk factors include screening match and limited historical data.

Primary Factors:
  • OFAC screening match (85% confidence)
  • Medium-risk jurisdiction
  • Limited customer history

Recommended Actions:
1. Review screening match details
   Rationale: Verify if match is true positive
2. Conduct enhanced due diligence
   Rationale: Assess risk level and compliance requirements
```

## Architecture Overview

The system uses a multi-agent architecture:

1. **Data Enrichment Agent**: Gathers additional context
2. **Risk Scoring Agent**: Calculates risk scores
3. **Context Builder Agent**: Creates narratives
4. **Decision Maker Agent**: Makes final decision
5. **Supervisor Agent**: Orchestrates the workflow

Each agent is powered by Claude and specialized for its task.

## Configuration

### Adjusting Thresholds

Edit `.env` to customize decision thresholds:

```env
# Confidence threshold for auto-clear
AUTO_CLEAR_THRESHOLD=0.85

# Confidence threshold for L2 escalation
ESCALATE_L2_THRESHOLD=0.70

# Risk score thresholds
RISK_SCORE_HIGH_THRESHOLD=70
RISK_SCORE_SEVERE_THRESHOLD=85
```

### Performance Tuning

```env
# Maximum concurrent alerts
MAX_CONCURRENT_ALERTS=10

# Agent timeout in seconds
AGENT_TIMEOUT_SECONDS=30

# Maximum retry attempts
MAX_RETRIES=3
```

## Testing

### Run All Tests
```bash
poetry run pytest
```

### Run with Coverage
```bash
poetry run pytest --cov=aml_triage --cov-report=html
```

### Run Specific Tests
```bash
# Unit tests only
poetry run pytest tests/unit/

# Integration tests only
poetry run pytest tests/integration/

# Specific test file
poetry run pytest tests/unit/test_base_agent.py
```

## Development

### Code Formatting
```bash
poetry run black src/ tests/
```

### Type Checking
```bash
poetry run mypy src/
```

### Linting
```bash
poetry run ruff check src/
```

## Troubleshooting

### Common Issues

**Issue**: "ModuleNotFoundError: No module named 'aml_triage'"
**Solution**: Run `poetry install` to install the package in development mode.

**Issue**: "AuthenticationError: Invalid API key"
**Solution**: Check that `ANTHROPIC_API_KEY` is set correctly in `.env`.

**Issue**: Slow processing times
**Solution**:
- Check your internet connection (API calls)
- Increase `AGENT_TIMEOUT_SECONDS` if needed
- Consider using faster models for non-critical agents

**Issue**: "Database connection error"
**Solution**: Ensure PostgreSQL is running or update `DATABASE_URL` in `.env`.

## Next Steps

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design details
2. Review [API_REFERENCE.md](API_REFERENCE.md) for complete API documentation
3. Explore the `examples/` directory for more use cases
4. Check `tests/` for example implementations
5. Customize agent prompts and thresholds for your use case

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Email: support@example.com
- Documentation: [docs/](docs/)
