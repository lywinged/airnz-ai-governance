"""
R3 Agent: Maintenance Automation (Automated Actions with Dual Control)

Automated work order creation with full safety controls.
Risk Tier: R3

Key requirements:
- Write operations allowed (create work orders)
- Dual control REQUIRED (two approvers)
- Rollback capability REQUIRED
- Full audit trail
- JIT authorization
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

from ..core.policy_engine import (
    PolicyEngine, RiskTier, ExecutionContext, CapabilityType
)
from ..core.access_control import (
    AccessControlEngine, UserAttributes, Role, BusinessDomain, SensitivityLevel, AircraftType
)
from ..core.tool_gateway import ToolGateway
from ..core.audit_system import AuditSystem, AuditEventType

logger = logging.getLogger(__name__)


class MaintenanceAutomationAgent:
    """
    R3: Automated maintenance actions with dual control.

    Use cases:
    - Automated work order creation based on alerts
    - Preventive maintenance scheduling
    - Parts ordering automation

    R3 characteristics:
    - WRITE operations enabled
    - Dual control mandatory
    - Rollback required
    - JIT authorization
    - Immutable logging
    """

    def __init__(self, tool_gateway: ToolGateway, audit_system: AuditSystem):
        self.tool_gateway = tool_gateway
        self.audit_system = audit_system
        self.policy_engine = PolicyEngine()
        self.access_control = AccessControlEngine()
        self.risk_tier = RiskTier.R3

        # Track pending approvals
        self.pending_approvals: Dict[str, Dict] = {}

    def create_work_order(
        self,
        work_order_data: Dict,
        user_id: str,
        session_id: str
    ) -> Dict:
        """
        Create work order with dual control approval.

        Args:
            work_order_data: Work order details
            user_id: User initiating action
            session_id: Session identifier

        Returns:
            Response with approval request or creation result
        """
        # Create execution context
        execution_context = ExecutionContext(
            user_id=user_id,
            role="engineer",
            business_domain="engineering",
            use_case_id="maintenance_automation",
            risk_tier=self.risk_tier,
            session_id=session_id,
            timestamp=datetime.now()
        )

        # Create audit trace
        trace_id = f"maint_auto_{session_id}_{datetime.now().timestamp()}"
        trace = self.audit_system.create_trace(
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            query=f"Create work order for {work_order_data.get('aircraft_registration')}",
            risk_tier=self.risk_tier.value,
            model_version="n/a",
            prompt_version="n/a",
            retrieval_index_version="n/a",
            policy_version="1.0.0"
        )

        # Log request
        self.audit_system.log_event(
            trace_id=trace_id,
            event_type=AuditEventType.REQUEST_RECEIVED,
            component="maintenance_automation",
            action="create_work_order_request",
            status="success",
            details=work_order_data
        )

        try:
            # Step 1: Check R3 policy gates
            # Check write operations allowed
            write_check = self.policy_engine.check_capability(
                execution_context,
                CapabilityType.WRITE_OPERATIONS
            )

            if not write_check.allowed:
                return self._create_error_response(
                    trace_id, "Write operations not allowed for this tier",
                    write_check.reason
                )

            # Check dual control required
            dual_control_check = self.policy_engine.check_capability(
                execution_context,
                CapabilityType.DUAL_CONTROL_REQUIRED
            )

            # Check rollback required
            rollback_check = self.policy_engine.check_capability(
                execution_context,
                CapabilityType.ROLLBACK_REQUIRED
            )

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.POLICY_CHECK,
                component="policy_engine",
                action="check_r3_gates",
                status="success",
                details={
                    "write_allowed": write_check.allowed,
                    "dual_control_required": dual_control_check.allowed,
                    "rollback_required": rollback_check.allowed
                }
            )

            # Step 2: Request first approval
            approval_request_id = f"approval_{trace_id}"

            self.pending_approvals[approval_request_id] = {
                "trace_id": trace_id,
                "work_order_data": work_order_data,
                "requested_by": user_id,
                "approvals": [],
                "required_approvals": 2,  # Dual control
                "created_at": datetime.now(),
                "status": "pending"
            }

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.APPROVAL_REQUESTED,
                component="maintenance_automation",
                action="request_dual_approval",
                status="pending",
                details={
                    "approval_request_id": approval_request_id,
                    "required_approvals": 2,
                    "requested_by": user_id
                }
            )

            return {
                "success": False,  # Not completed yet
                "status": "pending_approval",
                "approval_request_id": approval_request_id,
                "message": "Work order creation requires dual control approval",
                "required_approvals": 2,
                "current_approvals": 0,
                "work_order_preview": work_order_data,
                "metadata": {
                    "trace_id": trace_id,
                    "risk_tier": self.risk_tier.value
                }
            }

        except Exception as e:
            logger.error(f"Work order creation failed: {str(e)}")

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.ERROR_OCCURRED,
                component="maintenance_automation",
                action="create_work_order",
                status="error",
                details={"error": str(e)}
            )

            self.audit_system.complete_trace(
                trace_id=trace_id,
                final_response="Error occurred",
                status="failed"
            )

            return self._create_error_response(trace_id, "Creation failed", str(e))

    def approve_work_order(
        self,
        approval_request_id: str,
        approver_id: str,
        approved: bool,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Approve or deny work order creation (dual control).

        Args:
            approval_request_id: Approval request ID
            approver_id: Approver user ID
            approved: Whether approved
            notes: Optional approval notes

        Returns:
            Approval result
        """
        approval_request = self.pending_approvals.get(approval_request_id)

        if not approval_request:
            return {
                "success": False,
                "error": "Approval request not found",
                "approval_request_id": approval_request_id
            }

        trace_id = approval_request['trace_id']

        # Check if approver is same as requester (not allowed)
        if approver_id == approval_request['requested_by']:
            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.APPROVAL_DENIED,
                component="maintenance_automation",
                action="approve_work_order",
                status="denied",
                details={"reason": "Self-approval not allowed", "approver": approver_id}
            )

            return {
                "success": False,
                "error": "Self-approval not allowed",
                "approval_request_id": approval_request_id
            }

        # Check if already approved by this person
        existing_approval = next(
            (a for a in approval_request['approvals'] if a['approver_id'] == approver_id),
            None
        )

        if existing_approval:
            return {
                "success": False,
                "error": "You have already approved this request",
                "approval_request_id": approval_request_id
            }

        # Record approval
        approval_request['approvals'].append({
            "approver_id": approver_id,
            "approved": approved,
            "notes": notes,
            "timestamp": datetime.now()
        })

        event_type = AuditEventType.APPROVAL_GRANTED if approved else AuditEventType.APPROVAL_DENIED

        self.audit_system.log_event(
            trace_id=trace_id,
            event_type=event_type,
            component="maintenance_automation",
            action="record_approval",
            status="approved" if approved else "denied",
            details={
                "approver_id": approver_id,
                "notes": notes,
                "approval_count": len([a for a in approval_request['approvals'] if a['approved']])
            }
        )

        # If denied, reject immediately
        if not approved:
            approval_request['status'] = 'denied'

            self.audit_system.complete_trace(
                trace_id=trace_id,
                final_response="Work order creation denied",
                status="denied"
            )

            return {
                "success": False,
                "status": "denied",
                "message": "Work order creation denied by approver",
                "approver_id": approver_id,
                "notes": notes,
                "metadata": {"trace_id": trace_id}
            }

        # Check if we have enough approvals
        approved_count = len([a for a in approval_request['approvals'] if a['approved']])

        if approved_count < approval_request['required_approvals']:
            return {
                "success": False,
                "status": "pending_approval",
                "message": f"Approval recorded. {approval_request['required_approvals'] - approved_count} more approval(s) required.",
                "required_approvals": approval_request['required_approvals'],
                "current_approvals": approved_count,
                "metadata": {"trace_id": trace_id}
            }

        # All approvals received - execute action
        return self._execute_work_order_creation(approval_request)

    def _execute_work_order_creation(self, approval_request: Dict) -> Dict:
        """Execute work order creation after approvals received"""
        trace_id = approval_request['trace_id']
        work_order_data = approval_request['work_order_data']

        # Invoke tool through gateway
        tool_result = self.tool_gateway.invoke_tool(
            tool_id="create_work_order",
            parameters=work_order_data,
            user_id=approval_request['requested_by'],
            trace_id=trace_id,
            risk_tier="R3",
            idempotency_key=f"wo_{trace_id}"  # Prevent duplicate creation
        )

        if tool_result.success:
            approval_request['status'] = 'completed'
            wo_number = tool_result.result.get('wo_number')

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.TOOL_INVOKED,
                component="tool_gateway",
                action="create_work_order",
                status="success",
                details={
                    "wo_number": wo_number,
                    "can_rollback": tool_result.can_rollback
                }
            )

            self.audit_system.complete_trace(
                trace_id=trace_id,
                final_response=f"Work order created: {wo_number}",
                status="completed"
            )

            return {
                "success": True,
                "status": "completed",
                "wo_number": wo_number,
                "message": f"Work order {wo_number} created successfully",
                "can_rollback": tool_result.can_rollback,
                "rollback_invocation_id": tool_result.invocation_id if tool_result.can_rollback else None,
                "approvals": approval_request['approvals'],
                "metadata": {
                    "trace_id": trace_id,
                    "risk_tier": "R3"
                }
            }

        else:
            approval_request['status'] = 'failed'

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.ERROR_OCCURRED,
                component="tool_gateway",
                action="create_work_order",
                status="failed",
                details={"error": tool_result.error}
            )

            self.audit_system.complete_trace(
                trace_id=trace_id,
                final_response="Work order creation failed",
                status="failed"
            )

            return {
                "success": False,
                "status": "failed",
                "error": tool_result.error,
                "metadata": {"trace_id": trace_id}
            }

    def rollback_work_order(
        self,
        invocation_id: str,
        user_id: str,
        reason: str
    ) -> Dict:
        """
        Rollback work order creation.

        Args:
            invocation_id: Tool invocation ID to rollback
            user_id: User requesting rollback
            reason: Reason for rollback

        Returns:
            Rollback result
        """
        logger.info(f"Rollback requested by {user_id}: {invocation_id} - {reason}")

        success = self.tool_gateway.rollback_invocation(invocation_id)

        if success:
            return {
                "success": True,
                "message": "Work order rolled back successfully",
                "invocation_id": invocation_id,
                "rolled_back_by": user_id,
                "reason": reason
            }
        else:
            return {
                "success": False,
                "error": "Rollback failed",
                "invocation_id": invocation_id
            }

    def _create_error_response(self, trace_id: str, error_type: str, details: str) -> Dict:
        """Create error response"""
        return {
            "success": False,
            "error": error_type,
            "details": details,
            "metadata": {"trace_id": trace_id}
        }
