"""
Example: Running Disruption Management Agent (R2)

Demonstrates operations decision support with human-in-the-loop approval.
"""

import sys
sys.path.append('..')
from dotenv import load_dotenv

load_dotenv()
import os

from src.agents.disruption_management import DisruptionManagementAgent


def main():
    """Run disruption management example"""

    print("=" * 80)
    print("Air NZ Disruption Management - R2 (Operations Decision Support)")
    print("AI-generated recommendations with mandatory human approval")
    llm_real = bool(os.getenv("OPENAI_API_KEY"))
    flight_real = bool(os.getenv("AVIATIONSTACK_API_KEY"))
    print(f"LLM API mode: {'REAL (OPENAI_API_KEY detected)' if llm_real else 'MOCK (no OPENAI_API_KEY)'}")
    print(f"Flight API mode: {'REAL (AVIATIONSTACK_API_KEY detected)' if flight_real else 'MOCK (DB/mock fallback)'}")
    print("=" * 80)
    print()

    # Initialize agent
    agent = DisruptionManagementAgent()

    # Example disruption scenario
    disruption = {
        "flight_number": "NZ1",
        "route": "AKL-SYD",
        "scheduled_departure": "14:00",
        "issue": "Aircraft maintenance issue - hydraulic system",
        "estimated_repair_time": "150 minutes",
        "aircraft_registration": "ZK-OKM",
        "pax_count": 182,
        "connections_affected": 34
    }

    session_id = "ops_session_001"
    user_id = "dispatcher_akl_001"

    print("Disruption Scenario:")
    print(f"  Flight: {disruption['flight_number']} ({disruption['route']})")
    print(f"  Issue: {disruption['issue']}")
    print(f"  Scheduled: {disruption['scheduled_departure']}")
    print(f"  Passengers: {disruption['pax_count']}")
    print(f"  Connections: {disruption['connections_affected']}")
    print()

    print("Analyzing disruption and generating recovery options...")
    print()

    # Analyze disruption
    response = agent.analyze_disruption(
        disruption_context=disruption,
        user_id=user_id,
        session_id=session_id
    )

    if response["success"]:
        print("✓ Analysis complete\n")
        print(f"{'=' * 80}")
        print("Recovery Options (Ranked by Recommendation Score)")
        print(f"{'=' * 80}\n")

        for option in response["recovery_options"]:
            print(f"{option['option_id']}: {option['title']}")
            print(f"  {option['description']}")
            print(f"  Estimated Departure: {option['estimated_departure']}")
            print(f"  Total Delay: {option['delay_total_minutes']} minutes")
            print(f"  Recommendation Score: {option['recommendation_score']:.1%}")
            print(f"\n  Impact:")
            print(f"    - Passenger misconnects: {option['impact']['pax_misconnects']}")
            print(f"    - Crew regulatory: {option['impact']['crew_regulatory']}")
            print(f"    - Cost: {option['impact']['cost_estimate']}")
            print(f"\n  Constraints:")
            for constraint in option['constraints']:
                print(f"    - {constraint}")
            print(f"\n  Rationale: {option['rationale']}")
            print()

        print(f"{'=' * 80}")
        print("Recommended Option:")
        print(f"{'=' * 80}\n")

        recommended = response["recommended_option"]
        print(f"Option: {recommended['option_id']} - {recommended['title']}")
        print(f"Score: {recommended['recommendation_score']:.1%}")
        print(f"Rationale: {recommended['rationale']}")
        print()

        print(f"Citations:")
        for citation in response['citations']:
            print(f"  - {citation}")
        print()

        print(f"{'=' * 80}")
        print("⚠ HUMAN APPROVAL REQUIRED")
        print(f"{'=' * 80}\n")

        print(f"This is an R2 (Operations Decision Support) action.")
        print(f"AI has provided recommendations, but final decision must be made by: {response['approval_required_by']}")
        print()

        # Simulate human approval
        print("Simulating human approval decision...")
        print()

        approval_response = agent.record_approval_decision(
            trace_id=response['metadata']['trace_id'],
            option_id=recommended['option_id'],
            approved=True,
            approver_id=user_id,
            notes="Aircraft swap approved. Gate 25 confirmed available. Crew coordination in progress."
        )

        print(f"✓ Decision recorded")
        print(f"  Approved: {approval_response['approved']}")
        print(f"  Option: {approval_response['option_id']}")
        print(f"  Approver: {approval_response['approver_id']}")
        print(f"  Trace ID: {approval_response['trace_id']}")
        print()

        print(f"{'=' * 80}")
        print("Key Governance Features Demonstrated:")
        print(f"{'=' * 80}\n")

        print("✓ Risk Tier R2: Operations decision support")
        print("✓ Tool-RAG: Real-time data from authoritative systems")
        print("  - Flight status")
        print("  - Aircraft availability")
        print("  - Crew availability")
        print("  - Gate availability")
        print("✓ Evidence Contract: Procedures cited with version")
        print("✓ Human Approval: Mandatory approval recorded in audit trail")
        print("✓ Full Traceability: All steps logged for replay")
        print(f"✓ Replayable: Trace ID {approval_response['trace_id']}")
        print()

    else:
        print("✗ Analysis failed\n")
        print(f"Error: {response.get('error')}")
        print(f"Details: {response.get('details')}")

    print(f"{'=' * 80}")
    print("Demo completed")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
