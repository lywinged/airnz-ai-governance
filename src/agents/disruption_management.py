"""
R2 Agent: Disruption Management / Delay Avoidance (Operations Decision Support)

Tool-RAG + constraint-aware recommendations with mandatory human approval.
Risk Tier: R2 (Operations decision support)

Key requirements:
- Read-only tool access to authoritative systems
- Human approval REQUIRED for all recommendations
- Full explainability of recommendations
- Replayable for incident investigation
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

from ..core.policy_engine import (
    PolicyEngine, RiskTier, ExecutionContext, CapabilityType
)
from ..core.access_control import (
    AccessControlEngine, UserAttributes, ResourceAttributes,
    Role, BusinessDomain, SensitivityLevel, AircraftType
)
from ..core.evidence_contract import (
    EvidenceContractEnforcer, EvidencePackage, Citation,
    SourceSystem, EvidenceType
)
from ..core.retrieval_router import (
    RetrievalRouter, QueryContext, ToolRetriever
)
from ..core.audit_system import (
    AuditSystem, AuditEventType
)
from ..core.tool_gateway import ToolGateway

logger = logging.getLogger(__name__)


class DisruptionManagementAgent:
    """
    R2: Operations decision support for disruption management.

    Use cases:
    - Flight delay recovery recommendations
    - Aircraft swap scenarios
    - Gate/stand reassignment
    - Crew reallocation options
    - Connection protection

    Key principle: AI generates options, HUMAN makes final decision.
    """

    def __init__(
        self,
        tool_gateway: ToolGateway = None,
        audit_system: AuditSystem = None
    ):
        """
        Accept shared ToolGateway/AuditSystem so the demo can reuse common
        governance plumbing (G5/G7) across agents. Defaults allow the
        standalone example script to work without explicit wiring.
        """
        self.tool_gateway = tool_gateway
        self.audit_system = audit_system or AuditSystem()
        self.policy_engine = PolicyEngine()
        self.access_control = AccessControlEngine()
        self.evidence_enforcer = EvidenceContractEnforcer()
        self.retrieval_router = RetrievalRouter()
        self.pending_approvals: Dict[str, Dict] = {}

        self.risk_tier = RiskTier.R2

    def analyze_disruption(
        self,
        disruption_context: Dict,
        user_id: str,
        session_id: str
    ) -> Dict:
        """
        Analyze disruption and provide recovery recommendations.

        Args:
            disruption_context: Disruption details (flight, delay, cause, etc.)
            user_id: OCC dispatcher user ID
            session_id: Session identifier

        Returns:
            Response with recommendations requiring human approval
        """
        # Create execution context
        execution_context = ExecutionContext(
            user_id=user_id,
            role="dispatch_occ",
            business_domain="operations",
            use_case_id="disruption_management",
            risk_tier=self.risk_tier,
            session_id=session_id,
            timestamp=datetime.now()
        )

        # Create audit trace
        trace_id = f"disrupt_{session_id}_{datetime.now().timestamp()}"
        approval_request_id = f"approval_{trace_id}"
        trace = self.audit_system.create_trace(
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            query=f"Disruption: {disruption_context.get('flight_number')} - {disruption_context.get('issue')}",
            risk_tier=self.risk_tier.value,
            model_version="claude-sonnet-4.5",
            prompt_version="disruption_v1.0",
            retrieval_index_version="ops_procedures_v1.5",
            policy_version="1.0.0"
        )

        # Log request
        self.audit_system.log_event(
            trace_id=trace_id,
            event_type=AuditEventType.REQUEST_RECEIVED,
            component="disruption_management",
            action="analyze_disruption",
            status="success",
            details=disruption_context
        )

        try:
            # Step 1: Policy gate check - human approval REQUIRED for R2
            approval_check = self.policy_engine.check_capability(
                execution_context,
                CapabilityType.HUMAN_APPROVAL_REQUIRED
            )

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.POLICY_CHECK,
                component="policy_engine",
                action="check_approval_requirement",
                status="success",
                details={"requires_approval": approval_check.allowed}
            )

            # Step 2: Access control - verify user can access ops data
            user_attrs = UserAttributes(
                user_id=user_id,
                role=Role.DISPATCH_OCC,
                business_domains={BusinessDomain.OPERATIONS},
                aircraft_types={AircraftType.B787_9, AircraftType.A320},
                bases={"AKL"},
                route_regions={"Domestic", "Trans-Tasman"},
                sensitivity_clearance=SensitivityLevel.INTERNAL,
                additional_attributes={}
            )

            # Step 3: Gather real-time operational data via tools
            tool_data = self._gather_operational_data(
                trace_id,
                disruption_context,
                user_attrs
            )

            # Step 4: Retrieve relevant procedures and constraints
            procedures = self._retrieve_procedures(
                trace_id,
                disruption_context
            )

            # Step 5: Generate recovery options
            recovery_options = self._generate_recovery_options(
                trace_id,
                disruption_context,
                tool_data,
                procedures
            )

            # Step 6: Create evidence package with full explainability
            citations = self._create_procedure_citations(procedures)

            evidence_package = EvidencePackage(
                query=f"Recovery options for {disruption_context.get('flight_number')}",
                answer=self._format_recommendations(recovery_options),
                citations=citations,
                retrieval_strategy="tool_rag",
                confidence_score=0.9,  # High confidence when using authoritative tools
                timestamp=datetime.now(),
                risk_tier=self.risk_tier.value
            )

            # Validate evidence
            is_valid, errors = self.evidence_enforcer.validate_evidence_package(
                evidence_package,
                require_citations=True
            )

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.EVIDENCE_VALIDATED,
                component="evidence_enforcer",
                action="validate_evidence",
                status="success" if is_valid else "failure",
                details={"is_valid": is_valid, "errors": errors}
            )

            # Step 7: Generate response requiring approval
            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.APPROVAL_REQUESTED,
                component="disruption_management",
                action="request_human_approval",
                status="pending_approval",
                details={
                    "options_count": len(recovery_options),
                    "recommended_option": recovery_options[0]["option_id"] if recovery_options else None,
                    "approval_request_id": approval_request_id,
                    "required_approvals": 1,
                    "current_approvals": 0
                }
            )

            # Track pending approval for later decision recording
            self.pending_approvals[approval_request_id] = {
                "trace_id": trace_id,
                "options": recovery_options,
                "recommended_option": recovery_options[0]["option_id"] if recovery_options else None,
                "requested_by": user_id,
                "required_approvals": 1,
                "current_approvals": 0,
                "approvals": []
            }

            response = {
                "success": True,
                "status": "pending_approval",
                "requires_approval": True,
                "required_approvals": 1,
                "current_approvals": 0,
                "disruption": disruption_context,
                "recovery_options": recovery_options,
                "recommended_option": recovery_options[0] if recovery_options else None,
                "citations": [c.to_display_format() for c in citations],
                "approval_required_by": user_id,
                "approval_request_id": approval_request_id,
                "approval_deadline": self._calculate_approval_deadline(disruption_context),
                "metadata": {
                    "trace_id": trace_id,
                    "risk_tier": self.risk_tier.value,
                    "confidence": evidence_package.confidence_score,
                    "tool_data_sources": list(tool_data.keys()),
                    "replayable": True
                }
            }

            # Do NOT complete trace yet - waiting for approval
            return response

        except Exception as e:
            logger.error(f"Error analyzing disruption: {str(e)}")

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.ERROR_OCCURRED,
                component="disruption_management",
                action="analyze_disruption",
                status="error",
                details={"error": str(e)}
            )

            self.audit_system.complete_trace(
                trace_id=trace_id,
                final_response="Error occurred",
                status="failed"
            )

            return {
                "success": False,
                "error": "Analysis failed",
                "details": str(e),
                "metadata": {"trace_id": trace_id}
            }

    def record_approval_decision(
        self,
        trace_id: Optional[str] = None,
        option_id: Optional[str] = None,
        approved: bool = False,
        approver_id: str = "",
        approval_request_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Record human approval decision.

        Args:
            trace_id: Trace ID from analyze_disruption (optional if approval_request_id provided)
            option_id: Selected option ID (optional if approval_request_id provided)
            approved: Whether approved
            approver_id: Approver user ID
            approval_request_id: Approval request identifier returned by analyze_disruption
            notes: Optional approval notes

        Returns:
            Confirmation of recorded decision
        """
        # Resolve trace/option from approval_request_id if provided
        if approval_request_id:
            pending = self.pending_approvals.get(approval_request_id)
            if not pending:
                return {
                    "success": False,
                    "error": f"Approval request {approval_request_id} not found"
                }
            trace_id = trace_id or pending["trace_id"]
            option_id = option_id or pending.get("recommended_option")
            # Track approval progress
            pending["approvals"].append({
                "approver_id": approver_id,
                "approved": approved,
                "timestamp": datetime.now().isoformat(),
                "notes": notes
            })
            pending["current_approvals"] = len(pending["approvals"])

        if not trace_id or not option_id:
            return {
                "success": False,
                "error": "trace_id and option_id are required to record approval"
            }

        event_type = (
            AuditEventType.APPROVAL_GRANTED if approved
            else AuditEventType.APPROVAL_DENIED
        )

        self.audit_system.log_event(
            trace_id=trace_id,
            event_type=event_type,
            component="disruption_management",
            action="record_approval",
            status="approved" if approved else "denied",
            details={
                "option_id": option_id,
                "approver_id": approver_id,
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            }
        )

        # Complete trace
        self.audit_system.complete_trace(
            trace_id=trace_id,
            final_response=f"Option {option_id} {'approved' if approved else 'denied'} by {approver_id}",
            status="completed"
        )

        return {
            "success": True,
            "trace_id": trace_id,
            "approved": approved,
            "option_id": option_id,
            "approver_id": approver_id,
            "approval_request_id": approval_request_id,
            "status": "approved" if approved else "denied",
            "recorded_at": datetime.now().isoformat()
        }

    def _gather_operational_data(
        self,
        trace_id: str,
        disruption_context: Dict,
        user_attrs: UserAttributes
    ) -> Dict:
        """Gather real-time operational data from authoritative tools"""

        # Simulate tool calls (in production, would call actual systems)
        tool_data = {}

        # Tool 1: Flight status
        self.audit_system.log_event(
            trace_id=trace_id,
            event_type=AuditEventType.TOOL_INVOKED,
            component="tool_gateway",
            action="get_flight_status",
            status="success",
            details={"flight": disruption_context.get("flight_number")}
        )

        tool_data["flight_status"] = {
            "flight_number": disruption_context.get("flight_number"),
            "scheduled_departure": "14:00",
            "current_status": "delayed",
            "estimated_departure": "16:30",
            "delay_minutes": 150,
            "pax_count": 182,
            "connections": 34
        }

        # Tool 2: Aircraft availability
        self.audit_system.log_event(
            trace_id=trace_id,
            event_type=AuditEventType.TOOL_INVOKED,
            component="tool_gateway",
            action="get_aircraft_availability",
            status="success",
            details={"base": "AKL"}
        )

        tool_data["aircraft_availability"] = [
            {"registration": "ZK-NZA", "type": "B787-9", "available_from": "15:30"},
            {"registration": "ZK-NZB", "type": "B787-9", "available_from": "17:00"}
        ]

        # Tool 3: Crew availability
        self.audit_system.log_event(
            trace_id=trace_id,
            event_type=AuditEventType.TOOL_INVOKED,
            component="tool_gateway",
            action="get_crew_availability",
            status="success",
            details={"base": "AKL", "aircraft_type": "B787-9"}
        )

        tool_data["crew_availability"] = {
            "available_crews": 2,
            "regulatory_constraints": ["Flight duty period expires at 18:00 for current crew"]
        }

        # Tool 4: Gate/stand availability
        tool_data["gate_availability"] = [
            {"gate": "23", "available_from": "16:00", "aircraft_type": "widebody"},
            {"gate": "25", "available_from": "15:00", "aircraft_type": "widebody"}
        ]

        return tool_data

    def _retrieve_procedures(self, trace_id: str, disruption_context: Dict) -> List[Dict]:
        """Retrieve relevant disruption procedures"""

        # Simulate procedure retrieval
        return [
            {
                "document_id": "OPS-DISRUPT-001",
                "version": "2.1",
                "title": "Flight Delay Recovery Procedures",
                "excerpt": "For delays exceeding 120 minutes, consider aircraft swap if available. "
                          "Priority: protect connections, minimize passenger impact.",
                "source_system": SourceSystem.OPERATIONS_MANUAL,
                "evidence_type": EvidenceType.PROCEDURE,
                "paragraph_locator": "Section 4.2.1",
                "effective_date": datetime(2024, 1, 1)
            }
        ]

    def _generate_recovery_options(
        self,
        trace_id: str,
        disruption_context: Dict,
        tool_data: Dict,
        procedures: List[Dict]
    ) -> List[Dict]:
        """Generate recovery options with constraint awareness"""

        options = []

        # Option 1: Wait for original aircraft
        options.append({
            "option_id": "OPT-1",
            "title": "Wait for Original Aircraft",
            "description": "Continue with planned aircraft once maintenance complete",
            "estimated_departure": "16:30",
            "delay_total_minutes": 150,
            "impact": {
                "pax_misconnects": 12,
                "crew_regulatory": "Within limits",
                "cost_estimate": "Low"
            },
            "constraints": ["Crew flight duty period expires 18:00"],
            "recommendation_score": 0.7,
            "rationale": "Least disruptive option but misses some connections"
        })

        # Option 2: Aircraft swap
        if tool_data.get("aircraft_availability"):
            options.append({
                "option_id": "OPT-2",
                "title": "Swap to ZK-NZA",
                "description": "Swap to available B787-9 ZK-NZA",
                "estimated_departure": "15:45",
                "delay_total_minutes": 105,
                "impact": {
                    "pax_misconnects": 3,
                    "crew_regulatory": "Requires crew swap",
                    "cost_estimate": "Medium"
                },
                "constraints": ["Requires gate change to Gate 25", "Crew swap needed"],
                "recommendation_score": 0.9,
                "rationale": "Minimizes passenger impact and protects most connections"
            })

        return sorted(options, key=lambda x: x["recommendation_score"], reverse=True)

    def _create_procedure_citations(self, procedures: List[Dict]) -> List[Citation]:
        """Create citations from procedures"""
        citations = []

        for proc in procedures:
            citation = self.evidence_enforcer.create_citation_from_retrieval(
                document_id=proc["document_id"],
                version=proc["version"],
                source_system=proc["source_system"],
                evidence_type=proc["evidence_type"],
                excerpt=proc["excerpt"],
                metadata={
                    "title": proc["title"],
                    "paragraph_locator": proc["paragraph_locator"],
                    "effective_date": proc["effective_date"]
                }
            )
            citations.append(citation)

        return citations

    def _format_recommendations(self, options: List[Dict]) -> str:
        """Format recovery options as text"""
        if not options:
            return "No recovery options available"

        lines = ["Recovery Options:\n"]
        for opt in options:
            lines.append(f"{opt['option_id']}: {opt['title']}")
            lines.append(f"  Departure: {opt['estimated_departure']}")
            lines.append(f"  Impact: {opt['impact']['pax_misconnects']} misconnects")
            lines.append(f"  Score: {opt['recommendation_score']}")

        return "\n".join(lines)

    def _calculate_approval_deadline(self, disruption_context: Dict) -> str:
        """Calculate deadline for approval decision"""
        # In production, would calculate based on departure time
        return (datetime.now()).isoformat()
