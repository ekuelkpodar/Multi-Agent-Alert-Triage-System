"""Batch processing example for multiple alerts."""

import asyncio
from datetime import datetime
from typing import List

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
from aml_triage.models.decision import Decision


def create_sample_alerts() -> List[Alert]:
    """Create a batch of sample alerts for testing."""

    alerts = []

    # Alert 1: High-risk sanctions match
    alerts.append(
        Alert(
            alert_type=AlertType.SANCTIONS,
            priority=AlertPriority.HIGH,
            customer_data=CustomerData(
                customer_id="CUST-001",
                name="Mohammed Ahmed",
                aliases=["M. Ahmed"],
                entity_type=EntityType.INDIVIDUAL,
                addresses=[Address(country="IRN")],
            ),
            screening_results=ScreeningResults(
                match_details=[
                    MatchDetail(
                        source="OFAC",
                        match_type="NAME",
                        matched_name="Mohammed Ahmed",
                        match_score=0.95,
                        list_name="SDN",
                    )
                ],
                match_scores=[0.95],
                data_sources=["OFAC"],
            ),
            regulatory_context=RegulatoryContext(
                jurisdiction="USA",
                applicable_regulations=["OFAC"],
            ),
        )
    )

    # Alert 2: PEP alert
    alerts.append(
        Alert(
            alert_type=AlertType.PEP,
            priority=AlertPriority.MEDIUM,
            customer_data=CustomerData(
                customer_id="CUST-002",
                name="Jane Politician",
                entity_type=EntityType.INDIVIDUAL,
                addresses=[Address(country="USA")],
            ),
            screening_results=ScreeningResults(
                match_details=[
                    MatchDetail(
                        source="WorldCheck",
                        match_type="PEP",
                        matched_name="Jane Politician",
                        match_score=0.88,
                        list_name="US PEP",
                    )
                ],
                match_scores=[0.88],
                data_sources=["WorldCheck"],
            ),
            regulatory_context=RegulatoryContext(
                jurisdiction="USA",
                applicable_regulations=["BSA"],
            ),
        )
    )

    # Alert 3: Low-risk transaction alert
    alerts.append(
        Alert(
            alert_type=AlertType.TRANSACTION,
            priority=AlertPriority.LOW,
            customer_data=CustomerData(
                customer_id="CUST-003",
                name="Small Business LLC",
                entity_type=EntityType.BUSINESS,
                addresses=[Address(country="USA")],
            ),
            screening_results=ScreeningResults(
                match_details=[],
                match_scores=[],
                data_sources=["Internal TM"],
            ),
            regulatory_context=RegulatoryContext(
                jurisdiction="USA",
                applicable_regulations=["BSA"],
            ),
        )
    )

    return alerts


async def main():
    """Process a batch of alerts concurrently."""

    print("=" * 60)
    print("BATCH ALERT PROCESSING EXAMPLE")
    print("=" * 60)

    # Initialize system
    print("\nInitializing system...")
    system = AlertTriageSystem()

    # Create sample alerts
    alerts = create_sample_alerts()
    print(f"\nCreated {len(alerts)} sample alerts for processing")

    # Process batch
    print("\nProcessing alerts concurrently...")
    start_time = datetime.now()

    decisions = await system.process_alert_batch(alerts)

    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()

    # Display results
    print("\n" + "=" * 60)
    print("BATCH PROCESSING RESULTS")
    print("=" * 60)
    print(f"Total Alerts: {len(alerts)}")
    print(f"Total Processing Time: {processing_time:.2f}s")
    print(f"Average Time per Alert: {processing_time/len(alerts):.2f}s")

    # Summarize decisions
    disposition_counts = {}
    for decision in decisions:
        if isinstance(decision, Decision):
            disp = decision.disposition.value
            disposition_counts[disp] = disposition_counts.get(disp, 0) + 1

    print("\nDisposition Summary:")
    for disposition, count in disposition_counts.items():
        print(f"  {disposition}: {count}")

    # Detailed results
    print("\n" + "=" * 60)
    print("INDIVIDUAL ALERT RESULTS")
    print("=" * 60)

    for i, (alert, decision) in enumerate(zip(alerts, decisions), 1):
        if isinstance(decision, Decision):
            print(f"\nAlert {i}:")
            print(f"  Customer: {alert.customer_data.name}")
            print(f"  Alert Type: {alert.alert_type.value}")
            print(f"  Disposition: {decision.disposition.value}")
            print(f"  Risk Score: {decision.risk_score}/100")
            print(f"  Confidence: {decision.confidence_score:.2%}")
            print(f"  Human Review: {decision.requires_human_review}")
        else:
            print(f"\nAlert {i}: ERROR - {decision}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
