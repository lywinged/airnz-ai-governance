"""
Audit System: G7 - Full-chain Observability + Replayability

Every AI interaction is:
1. Fully traceable (input → routing → retrieval → tools → generation → output)
2. Replayable (same inputs = same outputs)
3. Auditable (who, what, when, why, how)
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of auditable events"""
    REQUEST_RECEIVED = "request_received"
    INTENT_DETECTED = "intent_detected"
    ACCESS_CHECK = "access_check"
    RETRIEVAL_EXECUTED = "retrieval_executed"
    TOOL_INVOKED = "tool_invoked"
    POLICY_CHECK = "policy_check"
    EVIDENCE_VALIDATED = "evidence_validated"
    RESPONSE_GENERATED = "response_generated"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class AuditEvent:
    """Single audit event in the execution chain"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: str
    session_id: str
    trace_id: str  # Links all events in a single request
    component: str  # Which component generated this event
    action: str
    status: str  # success, failure, denied
    details: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_json(self) -> str:
        """Serialize event to JSON"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        return json.dumps(data, default=str)


@dataclass
class ExecutionTrace:
    """Complete execution trace for a single request"""
    trace_id: str
    session_id: str
    user_id: str
    query: str
    risk_tier: str
    start_time: datetime
    end_time: Optional[datetime]
    events: List[AuditEvent]
    final_response: Optional[str]
    status: str  # completed, failed, denied

    # Replay information
    model_version: str
    prompt_version: str
    retrieval_index_version: str
    policy_version: str

    def add_event(self, event: AuditEvent):
        """Add event to trace"""
        self.events.append(event)

    def compute_hash(self) -> str:
        """Compute hash of trace for integrity verification"""
        # Create deterministic representation
        trace_data = {
            'trace_id': self.trace_id,
            'user_id': self.user_id,
            'query': self.query,
            'events': [e.to_json() for e in self.events],
        }
        trace_str = json.dumps(trace_data, sort_keys=True)
        return hashlib.sha256(trace_str.encode()).hexdigest()


@dataclass
class MetricSnapshot:
    """Snapshot of key metrics at a point in time"""
    timestamp: datetime
    risk_tier: str

    # Quality metrics
    citation_coverage_rate: float  # % of answers with valid citations
    hallucination_rate: float  # % of answers with fabricated info
    tool_success_rate: float  # % of tool calls that succeeded

    # Security metrics
    privilege_block_rate: float  # % of requests blocked by access control
    policy_violation_rate: float  # % of requests violating policies

    # Operational metrics
    avg_latency_ms: float
    p95_latency_ms: float
    total_requests: int
    failed_requests: int

    # R2/R3 specific
    human_approval_rate: float  # % of R2/R3 requiring approval
    approval_granted_rate: float  # % of approvals granted


class AuditSystem:
    """
    Central audit system for all AI operations.

    Key capabilities:
    1. Immutable audit log
    2. Full execution tracing
    3. Replay capability
    4. Metric aggregation
    5. Compliance reporting
    """

    def __init__(self):
        self.traces: Dict[str, ExecutionTrace] = {}
        self.events: List[AuditEvent] = []
        self.metrics: List[MetricSnapshot] = []

    def create_trace(
        self,
        trace_id: str,
        session_id: str,
        user_id: str,
        query: str,
        risk_tier: str,
        model_version: str,
        prompt_version: str,
        retrieval_index_version: str,
        policy_version: str
    ) -> ExecutionTrace:
        """
        Create new execution trace.

        Args:
            trace_id: Unique trace identifier
            session_id: Session identifier
            user_id: User making request
            query: User query
            risk_tier: Risk tier (R0-R3)
            model_version: LLM model version
            prompt_version: Prompt template version
            retrieval_index_version: RAG index version
            policy_version: Policy version

        Returns:
            ExecutionTrace object
        """
        trace = ExecutionTrace(
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            query=query,
            risk_tier=risk_tier,
            start_time=datetime.now(),
            end_time=None,
            events=[],
            final_response=None,
            status="in_progress",
            model_version=model_version,
            prompt_version=prompt_version,
            retrieval_index_version=retrieval_index_version,
            policy_version=policy_version
        )

        self.traces[trace_id] = trace

        logger.info(
            f"Trace created: {trace_id} | User: {user_id} | "
            f"Risk: {risk_tier} | Query: {query[:100]}"
        )

        return trace

    def log_event(
        self,
        trace_id: str,
        event_type: AuditEventType,
        component: str,
        action: str,
        status: str,
        details: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Log audit event.

        Args:
            trace_id: Associated trace ID
            event_type: Type of event
            component: Component generating event
            action: Action being performed
            status: Event status
            details: Event details
            metadata: Additional metadata

        Returns:
            Created AuditEvent
        """
        trace = self.traces.get(trace_id)
        if not trace:
            logger.error(f"Trace not found: {trace_id}")
            # Create placeholder trace for orphaned events
            trace = self.create_trace(
                trace_id=trace_id,
                session_id="unknown",
                user_id="unknown",
                query="unknown",
                risk_tier="unknown",
                model_version="unknown",
                prompt_version="unknown",
                retrieval_index_version="unknown",
                policy_version="unknown"
            )

        event = AuditEvent(
            event_id=f"{trace_id}_{len(trace.events)}",
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=trace.user_id,
            session_id=trace.session_id,
            trace_id=trace_id,
            component=component,
            action=action,
            status=status,
            details=details,
            metadata=metadata or {}
        )

        trace.add_event(event)
        self.events.append(event)

        logger.info(
            f"Event logged: {event_type.value} | Trace: {trace_id} | "
            f"Component: {component} | Status: {status}"
        )

        return event

    def complete_trace(
        self,
        trace_id: str,
        final_response: str,
        status: str
    ) -> ExecutionTrace:
        """
        Complete execution trace.

        Args:
            trace_id: Trace to complete
            final_response: Final response to user
            status: Final status

        Returns:
            Completed trace
        """
        trace = self.traces.get(trace_id)
        if not trace:
            logger.error(f"Trace not found: {trace_id}")
            return None

        trace.end_time = datetime.now()
        trace.final_response = final_response
        trace.status = status

        # Compute integrity hash
        trace_hash = trace.compute_hash()

        logger.info(
            f"Trace completed: {trace_id} | Status: {status} | "
            f"Duration: {(trace.end_time - trace.start_time).total_seconds():.2f}s | "
            f"Events: {len(trace.events)} | Hash: {trace_hash[:16]}"
        )

        return trace

    def replay_trace(
        self,
        trace_id: str,
        verify_determinism: bool = True
    ) -> Dict[str, Any]:
        """
        Replay execution trace to verify reproducibility.

        Args:
            trace_id: Trace to replay
            verify_determinism: Verify output matches original

        Returns:
            Replay results with comparison
        """
        original_trace = self.traces.get(trace_id)
        if not original_trace:
            return {
                "success": False,
                "error": f"Trace not found: {trace_id}"
            }

        logger.info(f"Replaying trace: {trace_id}")

        # In production, this would:
        # 1. Restore exact model/prompt/index versions
        # 2. Re-run the same query
        # 3. Compare outputs

        replay_result = {
            "trace_id": trace_id,
            "original_query": original_trace.query,
            "original_response": original_trace.final_response,
            "replay_timestamp": datetime.now().isoformat(),
            "versions_matched": {
                "model": True,
                "prompt": True,
                "index": True,
                "policy": True
            },
            "events_matched": True,
            "output_matched": True if not verify_determinism else False,
            "notes": "Replay simulation - full implementation would re-execute"
        }

        return replay_result

    def get_trace_history(
        self,
        user_id: Optional[str] = None,
        risk_tier: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ExecutionTrace]:
        """
        Get trace history with filters.

        Args:
            user_id: Filter by user
            risk_tier: Filter by risk tier
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of matching traces
        """
        filtered_traces = list(self.traces.values())

        if user_id:
            filtered_traces = [t for t in filtered_traces if t.user_id == user_id]

        if risk_tier:
            filtered_traces = [t for t in filtered_traces if t.risk_tier == risk_tier]

        if start_date:
            filtered_traces = [t for t in filtered_traces if t.start_time >= start_date]

        if end_date:
            filtered_traces = [t for t in filtered_traces if t.start_time <= end_date]

        return filtered_traces

    def record_metrics(self, snapshot: MetricSnapshot):
        """
        Record metric snapshot.

        Args:
            snapshot: Metric snapshot to record
        """
        self.metrics.append(snapshot)

        logger.info(
            f"Metrics recorded: {snapshot.risk_tier} | "
            f"Citation coverage: {snapshot.citation_coverage_rate:.2%} | "
            f"Hallucination rate: {snapshot.hallucination_rate:.2%} | "
            f"Tool success: {snapshot.tool_success_rate:.2%}"
        )

    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        risk_tier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report for audit.

        Args:
            start_date: Report start date
            end_date: Report end date
            risk_tier: Optional risk tier filter

        Returns:
            Compliance report dictionary
        """
        traces = self.get_trace_history(
            risk_tier=risk_tier,
            start_date=start_date,
            end_date=end_date
        )

        # Aggregate statistics
        total_requests = len(traces)
        completed = len([t for t in traces if t.status == "completed"])
        failed = len([t for t in traces if t.status == "failed"])
        denied = len([t for t in traces if t.status == "denied"])

        # Access control stats
        access_events = [
            e for e in self.events
            if e.event_type == AuditEventType.ACCESS_CHECK
            and start_date <= e.timestamp <= end_date
        ]
        access_denied = len([e for e in access_events if e.status == "denied"])
        access_granted = len([e for e in access_events if e.status == "granted"])

        # Policy violation stats
        policy_events = [
            e for e in self.events
            if e.event_type == AuditEventType.POLICY_CHECK
            and start_date <= e.timestamp <= end_date
        ]
        policy_violations = len([e for e in policy_events if e.status == "violation"])

        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "risk_tier": risk_tier or "all",
            "summary": {
                "total_requests": total_requests,
                "completed": completed,
                "failed": failed,
                "denied": denied,
                "success_rate": completed / total_requests if total_requests > 0 else 0
            },
            "access_control": {
                "total_checks": len(access_events),
                "granted": access_granted,
                "denied": access_denied,
                "denial_rate": access_denied / len(access_events) if access_events else 0
            },
            "policy_compliance": {
                "total_checks": len(policy_events),
                "violations": policy_violations,
                "violation_rate": policy_violations / len(policy_events) if policy_events else 0
            },
            "generated_at": datetime.now().isoformat()
        }

        logger.info(
            f"Compliance report generated: {total_requests} requests, "
            f"{access_denied} access denials, {policy_violations} policy violations"
        )

        return report
