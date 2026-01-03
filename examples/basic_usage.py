"""Basic usage example for the AML Alert Triage System."""

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
    """Demonstrate basic usage of the alert triage system."""

    # Initialize the system
    print("Initializing AML Alert Triage System...")
    system = AlertTriageSystem()

    # Create a sample alert
    alert = Alert(
        alert_type=AlertType.SANCTIONS,
        priority=AlertPriority.HIGH,
        customer_data=CustomerData(
            customer_id="CUST-12345",
            name="John Smith",
            aliases=["Jon Smith", "J. Smith"],
            dob=datetime(1970, 5, 15),
            addresses=[
                Address(
                    street="123 Main St",
                    city="New York",
                    state="NY",
                    country="USA",
                    postal_code="10001",
                )
            ],
            entity_type=EntityType.INDIVIDUAL,
            nationality="USA",
        ),
        screening_results=ScreeningResults(
            match_details=[
                MatchDetail(
                    source="OFAC",
                    match_type="NAME",
                    matched_name="John Smith",
                    match_score=0.92,
                    list_name="SDN",
                    additional_info={"program": "NARCOTICS"},
                )
            ],
            match_scores=[0.92],
            data_sources=["OFAC", "UN", "EU"],
        ),
        regulatory_context=RegulatoryContext(
            jurisdiction="USA",
            applicable_regulations=["BSA", "OFAC", "FinCEN"],
            institution_type="BANK",
            risk_appetite="MEDIUM",
        ),
    )

    print(f"\nProcessing Alert ID: {alert.alert_id}")
    print(f"Alert Type: {alert.alert_type.value}")
    print(f"Customer: {alert.customer_data.name}")
    print(f"Match Score: {alert.screening_results.match_scores[0]}")

    # Process the alert
    print("\nProcessing through multi-agent workflow...")
    decision = await system.process_alert(alert)

    # Display results
    print("\n" + "=" * 60)
    print("DECISION SUMMARY")
    print("=" * 60)
    print(f"Disposition: {decision.disposition.value}")
    print(f"Risk Score: {decision.risk_score}/100")
    print(f"Confidence: {decision.confidence_score:.2%}")
    print(f"Requires Human Review: {decision.requires_human_review}")
    print(f"Processing Time: {decision.processing_time_ms}ms")

    print("\n" + "-" * 60)
    print("RATIONALE:")
    print("-" * 60)
    print(decision.rationale)

    if decision.decision_factors.primary_factors:
        print("\n" + "-" * 60)
        print("PRIMARY FACTORS:")
        print("-" * 60)
        for factor in decision.decision_factors.primary_factors:
            print(f"  • {factor}")

    if decision.recommended_actions:
        print("\n" + "-" * 60)
        print("RECOMMENDED ACTIONS:")
        print("-" * 60)
        for i, action in enumerate(decision.recommended_actions, 1):
            print(f"{i}. {action.action}")
            print(f"   Rationale: {action.rationale}")

    print("\n" + "-" * 60)
    print("AGENT CONTRIBUTIONS:")
    print("-" * 60)
    for agent_name, contribution in decision.agent_contributions.items():
        print(f"\n{agent_name}:")
        print(f"  Confidence: {contribution.confidence:.2%}")
        print(f"  Summary: {contribution.output_summary}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
