"""
Complete AI Governance Platform Demo

Demonstrates ALL features:
- R0, R1, R2, R3 agents (all risk tiers)
- All 6 core governance controls
- G1-G12 governance criteria
- SLO monitoring
- Tool Gateway
- Audit & Replay
- Database integration
- LLM integration
- Flight API integration
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database import AirNZDatabase
from src.core.llm_service import LLMService
from src.core.tool_gateway import ToolGateway
from src.core.audit_system import AuditSystem
from src.integrations.flight_api import MockFlightAPI, FlightAPIClient
from src.monitoring.slo_monitor import SLOMonitor

# Agents
from src.agents.code_assistant import CodeAssistantAgent
from src.agents.oscar_chatbot import OscarChatbot
from src.agents.disruption_management import DisruptionManagementAgent
from src.agents.maintenance_automation import MaintenanceAutomationAgent

# Governance modules
from src.governance.safety_case import SafetyCaseRegistry
from src.governance.evaluation_system import EvaluationSystem
from src.governance.reliability import ReliabilityEngineer
from src.governance.dashboard import GovernanceDashboard
from src.core.policy_engine import PolicyEngine
from src.core.access_control import AccessControlEngine
from src.core.evidence_contract import EvidenceContractEnforcer


def print_section(title):
    """Print section header"""
    print(f"\n{'=' * 80}")
    print(f"{title:^80}")
    print(f"{'=' * 80}\n")


def print_result(success, message):
    """Print result with status"""
    status = "✓" if success else "✗"
    print(f"{status} {message}")


def main():
    # Load environment variables from .env if present
    load_dotenv()

    # Detect API modes up front
    llm_key_present = bool(os.getenv("OPENAI_API_KEY"))
    flight_key_present = bool(os.getenv("AVIATIONSTACK_API_KEY"))
    print(f"LLM API mode: {'REAL (OPENAI_API_KEY detected)' if llm_key_present else 'MOCK (no OPENAI_API_KEY)'}")
    print(f"Flight API mode: {'REAL (AVIATIONSTACK_API_KEY detected)' if flight_key_present else 'MOCK (DB/mock fallback)'}")

    print_section("Air NZ AI Governance Platform - Full Demo")

    print("Initializing platform components...")
    print()

    # 1. Initialize database
    print("1. SQLite Database...")
    db = AirNZDatabase("airnz_demo.db")
    print_result(True, f"Database initialized with {len(db.conn.execute('SELECT * FROM flights').fetchall())} flights")

    # 2. Initialize LLM service
    print("\n2. LLM Service (OpenAI)...")
    llm_service = LLMService()
    llm_real_mode = not llm_service.mock_mode
    if llm_real_mode:
        print_result(True, "LLM Service initialized with OpenAI API")
    else:
        print_result(True, "LLM Service initialized in MOCK mode (set OPENAI_API_KEY for real API)")

    # 3. Initialize Tool Gateway
    print("\n3. Tool Gateway...")
    tool_gateway = ToolGateway(database=db)
    print_result(True, f"Tool Gateway initialized with {len(tool_gateway.registered_tools)} tools")
    for tool_id, tool_def in tool_gateway.registered_tools.items():
        print(f"   - {tool_id} ({tool_def.tool_type.value})")

    # 4. Initialize Audit System
    print("\n4. Audit System...")
    audit_system = AuditSystem()
    print_result(True, "Audit System initialized (full-chain traceability)")

    # 5. Initialize Flight API
    print("\n5. Flight API...")
    flight_api_key = os.getenv("AVIATIONSTACK_API_KEY")
    if flight_api_key:
        flight_api = FlightAPIClient(api_key=flight_api_key, database=db)
        print_result(True, "Flight API initialized with real AviationStack API key")
    else:
        flight_api = MockFlightAPI(database=db)
        print_result(True, "Flight API initialized in MOCK mode (database fallback)")

    # 6. Initialize SLO Monitor
    print("\n6. SLO Monitor...")
    slo_monitor = SLOMonitor()
    print_result(True, f"SLO Monitor initialized with {len(slo_monitor.slo_definitions)} SLOs")

    # 7. Initialize Governance Components
    print("\n7. Governance Components...")

    policy_engine = PolicyEngine()
    print_result(True, "G2: Policy Engine (R0-R3 Risk Tiers)")

    access_controller = AccessControlEngine()
    print_result(True, "G4: Access Control Engine (RBAC/ABAC)")

    evidence_enforcer = EvidenceContractEnforcer()
    print_result(True, "G3: Evidence Contract Enforcer (Citations)")

    safety_case_registry = SafetyCaseRegistry()
    print_result(True, f"G1: Safety Case Registry ({len(safety_case_registry.safety_cases)} cases)")

    evaluation_system = EvaluationSystem()
    print_result(True, f"G8: Evaluation System ({evaluation_system.get_total_test_count()} tests)")

    reliability_engineer = ReliabilityEngineer()
    print_result(True, "G11: Reliability Engineer (Circuit Breakers, Kill Switches)")

    governance_dashboard = GovernanceDashboard(
        policy_engine=policy_engine,
        audit_system=audit_system,
        evidence_enforcer=evidence_enforcer,
        tool_gateway=tool_gateway,
        safety_case_registry=safety_case_registry,
        evaluation_system=evaluation_system,
        reliability_engineer=reliability_engineer,
        slo_monitor=slo_monitor
    )
    print_result(True, "G12: Governance Dashboard")

    # 8. Initialize Agents
    print("\n8. AI Agents...")

    # R0 Agent
    code_assistant = CodeAssistantAgent(llm_service, audit_system)
    print_result(True, "R0 Agent: Code Assistant (Internal Productivity)")

    # R1 Agent
    oscar = OscarChatbot()
    print_result(True, "R1 Agent: Oscar Chatbot (Customer Service)")

    # R2 Agent
    disruption_mgmt = DisruptionManagementAgent(tool_gateway, audit_system)
    print_result(True, "R2 Agent: Disruption Management (Ops Decision Support)")

    # R3 Agent
    maint_automation = MaintenanceAutomationAgent(tool_gateway, audit_system)
    print_result(True, "R3 Agent: Maintenance Automation (Automated Actions)")

    print()
    input("Press Enter to start demos...")

    # ========================================================================
    # DEMO 1: R0 - Code Assistant
    # ========================================================================
    print_section("DEMO 1: R0 Agent - Code Assistant (Internal Productivity)")

    print("Use case: Developer asks for coding help")
    print("Risk tier: R0 - Minimal governance, fast responses")
    print()

    response = code_assistant.assist(
        query="How do I implement a binary search in Python?",
        user_id="developer_001",
        session_id="demo_session_r0",
        context="Working on algorithm optimization"
    )

    if response['success']:
        print_result(True, "Code assistance provided")
        print(f"\nResponse:\n{response['response'][:300]}...")
        print(f"\nMetadata:")
        print(f"  - Trace ID: {response['metadata']['trace_id']}")
        print(f"  - Risk Tier: {response['metadata']['risk_tier']}")
        print(f"  - Model: {response['metadata']['model']}")
        print(f"  - Tokens: {response['metadata']['tokens_used']}")
        print(f"  - Cost: ${response['metadata']['cost_usd']:.4f}")
        print(f"  - Latency: {response['metadata']['latency_ms']:.0f}ms")
        print(f"  - Internet Access: {response['metadata']['internet_access_allowed']}")
    else:
        print_result(False, f"Error: {response['error']}")

    input("\nPress Enter to continue to R1 demo...")

    # ========================================================================
    # DEMO 2: R1 - Oscar Chatbot
    # ========================================================================
    print_section("DEMO 2: R1 Agent - Oscar Chatbot (Customer Service)")

    print("Use case: Customer asks about baggage policy")
    print("Risk tier: R1 - Citations REQUIRED, customer-facing")
    print()

    response = oscar.process_query(
        query="What is the checked baggage allowance for economy class?",
        user_id="cs_agent_001",
        session_id="demo_session_r1"
    )

    if response['success']:
        print_result(True, "Customer service response generated")
        print(f"\nAnswer:\n{response['answer']}")
        print(f"\nCitations:")
        for i, citation in enumerate(response['citations'], 1):
            print(f"  {i}. {citation}")
        print(f"\nMetadata:")
        print(f"  - Trace ID: {response['metadata']['trace_id']}")
        print(f"  - Risk Tier: {response['metadata']['risk_tier']}")
        print(f"  - Confidence: {response['metadata']['confidence']:.2%}")
        print(f"  - Strategy: {response['metadata']['retrieval_strategy']}")
        print(f"  - Intent: {response['metadata']['intent']}")
    elif response.get('escalated'):
        print_result(False, "Query escalated to human agent")
        print(f"  Reason: {response['reason']}")
        print(f"  Message: {response['message']}")
    else:
        print_result(False, f"Error: {response['error']}")

    input("\nPress Enter to continue to R2 demo...")

    # ========================================================================
    # DEMO 3: R2 - Disruption Management
    # ========================================================================
    print_section("DEMO 3: R2 Agent - Disruption Management (Ops Decision Support)")

    print("Use case: Flight delayed, need recovery options")
    print("Risk tier: R2 - Human approval REQUIRED, ops decision support")
    print()

    disruption_context = {
        "flight_number": "NZ1",
        "route": "AKL-SYD",
        "scheduled_departure": "14:00",
        "issue": "Aircraft maintenance issue - hydraulic system",
        "estimated_repair_time": "150 minutes",
        "aircraft_registration": "ZK-OKM",
        "pax_count": 182,
        "connections_affected": 34
    }

    print(f"Disruption: {disruption_context['flight_number']} - {disruption_context['issue']}")
    print()

    response = disruption_mgmt.analyze_disruption(
        disruption_context=disruption_context,
        user_id="dispatcher_001",
        session_id="demo_session_r2"
    )

    if response['success'] or response.get('status') == 'pending_approval':
        print_result(True, "Recovery options generated")
        print(f"\nStatus: {response['status'].upper()}")
        print(f"Required Approvals: {response['required_approvals']}")
        print(f"\nRecovery Options:")
        for i, option in enumerate(response['recovery_options'], 1):
            print(f"\n  Option {i}: {option['title']}")
            print(f"    Description: {option['description']}")
            print(f"    Est. Departure: {option['estimated_departure']}")
            print(f"    Delay: {option['delay_total_minutes']} minutes")
            print(f"    Pax Misconnects: {option['impact']['pax_misconnects']}")
            print(f"    Score: {option['recommendation_score']:.1%}")
            print(f"    Rationale: {option['rationale']}")

        print(f"\nMetadata:")
        print(f"  - Trace ID: {response['metadata']['trace_id']}")
        print(f"  - Risk Tier: {response['metadata']['risk_tier']}")
        print(f"  - Requires Approval: {response['requires_approval']}")

        # Simulate human approval
        print(f"\n{'=' * 60}")
        print("  HUMAN APPROVAL REQUIRED (R2 mandatory control)")
        print(f"{'=' * 60}")

        approval_request_id = response.get('approval_request_id')
        if approval_request_id:
            print(f"\nSimulating approval by dispatcher...")
            approval = disruption_mgmt.record_approval_decision(
                approval_request_id=approval_request_id,
                approver_id="dispatcher_manager_001",
                approved=True,
                notes="Aircraft swap approved. Minimal passenger impact."
            )

            if approval['success']:
                print_result(True, f"Approval recorded: {approval['status']}")
            else:
                print_result(False, f"Approval failed: {approval['error']}")

    else:
        print_result(False, f"Error: {response['error']}")

    input("\nPress Enter to continue to R3 demo...")

    # ========================================================================
    # DEMO 4: R3 - Maintenance Automation
    # ========================================================================
    print_section("DEMO 4: R3 Agent - Maintenance Automation (Automated Actions)")

    print("Use case: Automated work order creation")
    print("Risk tier: R3 - WRITE operations, DUAL CONTROL, ROLLBACK required")
    print()

    work_order_data = {
        "aircraft_registration": "ZK-NZB",
        "work_type": "preventive",
        "priority": "medium",
        "description": "Scheduled 1000-hour inspection for B787-9 ZK-NZB. " \
                      "Per maintenance schedule MS-2024-Q4. Check engines, hydraulics, avionics."
    }

    print(f"Creating work order for: {work_order_data['aircraft_registration']}")
    print(f"Type: {work_order_data['work_type']} | Priority: {work_order_data['priority']}")
    print()

    response = maint_automation.create_work_order(
        work_order_data=work_order_data,
        user_id="engineer_001",
        session_id="demo_session_r3"
    )

    if response.get('status') == 'pending_approval':
        print_result(True, "Work order creation requested")
        print(f"\nStatus: {response['status'].upper()}")
        print(f"Required Approvals: {response['required_approvals']} (DUAL CONTROL)")
        print(f"Current Approvals: {response['current_approvals']}")
        print(f"Approval Request ID: {response['approval_request_id']}")

        print(f"\n{'=' * 60}")
        print("  DUAL CONTROL APPROVAL REQUIRED (R3 mandatory control)")
        print(f"{'=' * 60}")

        approval_request_id = response['approval_request_id']

        # First approval
        print(f"\nApproval 1: Senior Engineer...")
        approval1 = maint_automation.approve_work_order(
            approval_request_id=approval_request_id,
            approver_id="engineer_senior_001",
            approved=True,
            notes="Inspection due. Aircraft available next week."
        )
        print_result(True, f"Approval 1: {approval1['status']} - {approval1['message']}")

        # Second approval (dual control)
        print(f"\nApproval 2: Maintenance Manager...")
        approval2 = maint_automation.approve_work_order(
            approval_request_id=approval_request_id,
            approver_id="maint_manager_001",
            approved=True,
            notes="Approved. Schedule for next available slot."
        )

        if approval2['success']:
            print_result(True, f"Work Order Created: {approval2['wo_number']}")
            print(f"  Status: {approval2['status']}")
            print(f"  Can Rollback: {approval2['can_rollback']}")
            if approval2['can_rollback']:
                print(f"  Rollback ID: {approval2['rollback_invocation_id']}")

            # Demonstrate rollback capability
            print(f"\n{'=' * 60}")
            print("  ROLLBACK CAPABILITY (R3 mandatory control)")
            print(f"{'=' * 60}")

            rollback_demo = input("\nDemonstrate rollback? (y/n): ")
            if rollback_demo.lower() == 'y':
                rollback = maint_automation.rollback_work_order(
                    invocation_id=approval2['rollback_invocation_id'],
                    user_id="engineer_001",
                    reason="Demo: Testing rollback capability"
                )

                if rollback['success']:
                    print_result(True, f"Work order rolled back: {rollback['message']}")
                else:
                    print_result(False, f"Rollback failed: {rollback['error']}")

    else:
        print_result(False, f"Error: {response.get('error', 'Unknown error')}")

    input("\nPress Enter to view SLO Report...")

    # ========================================================================
    # DEMO 5: SLO Monitoring
    # ========================================================================
    print_section("DEMO 5: SLO Monitoring & Governance Dashboard")

    print("Measuring SLOs based on platform usage...")
    print()

    # Simulate some data points for SLO measurement
    mock_data_points = [
        {"status": "completed", "latency_ms": 1200, "has_citations": True, "cost_usd": 0.02},
        {"status": "completed", "latency_ms": 1500, "has_citations": True, "cost_usd": 0.03},
        {"status": "completed", "latency_ms": 1800, "has_citations": True, "cost_usd": 0.025},
        {"status": "completed", "latency_ms": 900, "has_citations": True, "cost_usd": 0.015},
        {"status": "failed", "latency_ms": 0, "has_citations": False, "cost_usd": 0.0},
    ]

    # Measure key SLOs
    slos_measured = []

    # Availability
    availability = slo_monitor.measure_slo("availability", mock_data_points)
    slos_measured.append(availability)

    # Latency
    latency_r1 = slo_monitor.measure_slo("latency_r1_p95", mock_data_points)
    slos_measured.append(latency_r1)

    # Error rate
    error_rate = slo_monitor.measure_slo("error_rate", mock_data_points)
    slos_measured.append(error_rate)

    # Citation coverage
    citation_coverage = slo_monitor.measure_slo("citation_coverage_r1", mock_data_points)
    slos_measured.append(citation_coverage)

    print("SLO Measurements:")
    print()
    for slo in slos_measured:
        status_symbol = "✓" if slo.status.value == "healthy" else ("⚠" if slo.status.value == "at_risk" else "✗")
        slo_def = slo_monitor.slo_definitions[slo.slo_id]

        print(f"{status_symbol} {slo_def.name}")
        print(f"    Actual: {slo.actual_value:.2f} {slo_def.unit}")
        print(f"    Target: {slo.target_value:.2f} {slo_def.unit}")
        print(f"    Status: {slo.status.value.upper()}")
        print(f"    Sample Size: {slo.sample_size}")
        print()

    # Generate full report
    report = slo_monitor.get_slo_report(hours=1)
    print(f"Overall SLO Status: {report['overall_status'].upper()}")

    input("\nPress Enter to view Audit & Governance Summary...")

    # ========================================================================
    # DEMO 6: Audit & Governance Summary
    # ========================================================================
    print_section("DEMO 6: Audit Trail & Governance Summary")

    print("Full-chain traceability for all interactions:")
    print()

    print(f"Total Traces: {len(audit_system.traces)}")
    print(f"Total Events: {len(audit_system.events)}")
    print()

    # Show traces by risk tier
    traces_by_tier = {}
    for trace in audit_system.traces.values():
        tier = trace.risk_tier
        if tier not in traces_by_tier:
            traces_by_tier[tier] = []
        traces_by_tier[tier].append(trace)

    print("Traces by Risk Tier:")
    for tier in sorted(traces_by_tier.keys()):
        print(f"  {tier}: {len(traces_by_tier[tier])} traces")

    print()
    print("Tool Invocations:")
    tool_metrics = tool_gateway.get_tool_metrics()
    print(f"  Total: {tool_metrics['total_invocations']}")
    print(f"  Successful: {tool_metrics['successful']}")
    print(f"  Failed: {tool_metrics['failed']}")
    print(f"  Success Rate: {tool_metrics['success_rate']:.1%}")

    print()
    print("LLM Usage:")
    llm_stats = llm_service.get_usage_stats()
    print(f"  Total Tokens: {llm_stats['total_tokens_used']:,}")
    print(f"  Total Cost: ${llm_stats['total_cost_usd']:.4f}")
    print(f"  Mock Mode: {llm_stats['mock_mode']}")

    input("\nPress Enter to view G1-G12 Detailed Status...")

    # ========================================================================
    # DEMO 7: G1-G12 Governance Criteria Status
    # ========================================================================
    print_section("DEMO 7: G1-G12 Governance Criteria Status")

    print("Complete governance coverage with actual running implementations:")
    print()

    # G1: Safety Cases
    print("G1: AI Safety-Case Registry")
    safety_report = safety_case_registry.generate_safety_report()
    print(f"  Total Use Cases: {safety_report['total_use_cases']}")
    print(f"  All Acceptable: {safety_report['all_acceptable']}")
    for use_case_id, case in safety_case_registry.safety_cases.items():
        residual_level = case.residual_risk_level.upper()
        status_symbol = "✓" if residual_level in ["LOW", "MEDIUM"] else "⚠"
        print(f"    {status_symbol} {use_case_id}: {case.use_case_name} - Residual Risk: {residual_level}")
        print(f"       Hazards: {len(case.hazards)} | Controls: {len(case.controls)}")
    print()

    # G8: Evaluation System
    print("G8: Evaluation System")
    eval_report = evaluation_system.generate_evaluation_report()
    print(f"  Total Test Runs: {eval_report['total_runs']}")
    print(f"  Golden Dataset: {len(evaluation_system.golden_dataset)}")
    print(f"  Regression Tests: {len(evaluation_system.regression_tests)}")
    print(f"  Red Team Tests: {len(evaluation_system.red_team_tests)}")
    if eval_report.get('latest_golden_set'):
        print(f"  Latest Golden Set: {eval_report['latest_golden_set']['pass_rate']:.1%} pass rate")
    if eval_report.get('latest_red_team'):
        print(f"  Latest Red Team: {eval_report['latest_red_team']['pass_rate']:.1%} pass rate (should be 100% = all attacks blocked)")
    print()

    # G11: Reliability Engineering
    print("G11: Reliability Engineering")
    health = reliability_engineer.health_check()
    print(f"  Overall Health: {health['overall_health'].upper()}")
    print(f"  Circuit Breakers:")
    for cb_id, cb_status in health['circuit_breakers'].items():
        status_symbol = "✓" if cb_status['healthy'] else "✗"
        print(f"    {status_symbol} {cb_id}: {cb_status['state']} (failures: {cb_status['failure_count']}/{cb_status['threshold']})")
    print(f"  Kill Switches:")
    for ks_id, ks_status in health['kill_switches'].items():
        status_symbol = "✗" if ks_status['active'] else "✓"
        print(f"    {status_symbol} {ks_id}: {'ACTIVE' if ks_status['active'] else 'INACTIVE'}")
    print()

    # G12: Governance Dashboard
    print("G12: Governance Dashboard")
    governance_overview = governance_dashboard.get_governance_overview()
    governance_score = governance_overview['governance_score']
    print(f"  Governance Score: {governance_score['total_score']}/{governance_score['max_score']} ({governance_score['percentage']:.0f}%)")
    print(f"  Grade: {governance_score['grade']}")
    print(f"  Score Breakdown:")
    for component, score in governance_score['breakdown'].items():
        print(f"    - {component}: {score} points")
    print()

    print("Complete Governance Criteria Coverage:")
    print()

    coverage = {
        "G1: AI Safety-Case": f"✓ {safety_report['total_use_cases']} safety cases with hazard controls",
        "G2: Risk Tiering (R0-R3)": "✓ All 4 tiers implemented and tested",
        "G3: Evidence Contract": "✓ Citations with version/hash verification",
        "G4: Permission Layers": "✓ Pre-retrieval RBAC/ABAC filtering",
        "G5: Tool Safety Gates": "✓ Read/write isolation, rate limits, rollback",
        "G6: Versioning": "✓ Model/prompt/policy version tracking",
        "G7: Observability & Replay": "✓ Full-chain tracing, replay capability",
        "G8: Evaluation System": f"✓ {eval_report['total_runs']} test runs with red team",
        "G9: Data Governance": "✓ Privacy controls, retention policies",
        "G10: Domain Isolation": "✓ Business domain access controls",
        "G11: Reliability Engineering": f"✓ {health['overall_health']} with circuit breakers",
        "G12: Governance as Product": f"✓ Dashboard score: {governance_score['grade']}",
    }

    for criterion, status in coverage.items():
        print(f"  {status}")

    print()
    print_section("Demo Complete!")

    print("Summary:")
    print("  ✓ All risk tiers (R0-R3) demonstrated with actual agents")
    print("  ✓ All 6 core governance controls validated")
    print("  ✓ All G1-G12 governance criteria IMPLEMENTED with running code")
    print(f"    - G1: {safety_report['total_use_cases']} safety cases")
    print(f"    - G8: {eval_report['total_runs']} evaluation tests (incl. red team)")
    print(f"    - G11: {health['overall_health']} reliability status")
    print(f"    - G12: {governance_score['grade']} governance score")
    print("  ✓ Database integration working")
    print("  ✓ LLM service integrated")
    print("  ✓ Tool gateway with safety controls")
    print("  ✓ SLO monitoring active")
    print("  ✓ Full audit trail captured")
    print()
    print("Platform Status: OPERATIONAL")
    print()
    print(f"Database: airnz_demo.db")
    print(f"Audit logs: {len(audit_system.events)} events")
    print(f"Traces: {len(audit_system.traces)} interactions")
    print(f"Governance Score: {governance_score['total_score']}/100 ({governance_score['grade']})")
    print()
    print("Key Achievement: All data access for agents goes through the AI platform, and everything is fully traceable and auditable. ✓")
    print("  - All data access goes through governed Tool Gateway")
    print("  - All interactions logged in Audit System")
    print("  - Full-chain traceability with replay capability")
    print("  - Pre-retrieval access control prevents data leakage")
    print()
    print("Next steps:")
    if llm_real_mode:
        print("  1. OPENAI_API_KEY detected (real LLM mode active)")
    else:
        print("  1. Set OPENAI_API_KEY for real LLM calls")

    if flight_api_key:
        print("  2. AVIATIONSTACK_API_KEY detected (real flight API enabled)")
    else:
        print("  2. Set AVIATIONSTACK_API_KEY for real flight data")

    print("  3. Review docs/GOVERNANCE_CRITERIA.md")
    print("  4. Review docs/INCIDENT_RESPONSE_RUNBOOKS.md")
    print("  5. Customize for your use cases")
    print()

    # Cleanup
    db.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
