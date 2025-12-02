"""
R0 Agent: Code Assistant (Internal Productivity)

Low-risk internal productivity tool for developers.
Risk Tier: R0

Key characteristics:
- No citations required (internal use)
- Internet access allowed
- No write operations to production systems
- Minimal governance overhead
"""

from datetime import datetime
from typing import Dict
import logging

from ..core.policy_engine import (
    PolicyEngine, RiskTier, ExecutionContext, CapabilityType
)
from ..core.llm_service import LLMService
from ..core.audit_system import AuditSystem, AuditEventType

logger = logging.getLogger(__name__)


class CodeAssistantAgent:
    """
    R0: Internal productivity - coding assistance for developers.

    Use cases:
    - Code writing and review
    - Debugging assistance
    - Best practices advice
    - Technical documentation

    R0 characteristics:
    - Minimal governance overhead
    - Fast responses
    - No mandatory citations
    - Internet access for docs/Stack Overflow
    """

    def __init__(self, llm_service: LLMService, audit_system: AuditSystem):
        self.llm_service = llm_service
        self.audit_system = audit_system
        self.policy_engine = PolicyEngine()
        self.risk_tier = RiskTier.R0

    def assist(
        self,
        query: str,
        user_id: str,
        session_id: str,
        context: str = ""
    ) -> Dict:
        """
        Provide coding assistance.

        Args:
            query: Developer's question or request
            user_id: Developer user ID
            session_id: Session identifier
            context: Optional context (code snippet, error message, etc.)

        Returns:
            Response with assistance
        """
        # Create execution context
        execution_context = ExecutionContext(
            user_id=user_id,
            role="developer",
            business_domain="it",
            use_case_id="code_assistant",
            risk_tier=self.risk_tier,
            session_id=session_id,
            timestamp=datetime.now()
        )

        # Create audit trace
        trace_id = f"code_assist_{session_id}_{datetime.now().timestamp()}"
        trace = self.audit_system.create_trace(
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            query=query,
            risk_tier=self.risk_tier.value,
            model_version="gpt-3.5-turbo",  # Faster/cheaper for R0
            prompt_version="code_assistant_v1.0",
            retrieval_index_version="n/a",
            policy_version="1.0.0"
        )

        # Log request
        self.audit_system.log_event(
            trace_id=trace_id,
            event_type=AuditEventType.REQUEST_RECEIVED,
            component="code_assistant",
            action="assist_request",
            status="success",
            details={"query": query[:200], "has_context": bool(context)}
        )

        try:
            # R0: Internet access allowed (minimal checks)
            internet_check = self.policy_engine.check_capability(
                execution_context,
                CapabilityType.INTERNET_ACCESS
            )

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.POLICY_CHECK,
                component="policy_engine",
                action="check_internet_access",
                status="allowed" if internet_check.allowed else "denied",
                details={"reason": internet_check.reason}
            )

            # Generate response using LLM
            llm_response = self.llm_service.generate(
                template_id="code_assistant",
                template_version="1.0",
                variables={
                    "query": query,
                    "context": context or "No additional context provided"
                },
                model="gpt-3.5-turbo",  # Fast and cheap for R0
                temperature=0.7,
                max_tokens=1500
            )

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.RESPONSE_GENERATED,
                component="code_assistant",
                action="generate_response",
                status="success",
                details={
                    "model": llm_response.model,
                    "tokens": llm_response.total_tokens,
                    "cost_usd": llm_response.cost_usd,
                    "latency_ms": llm_response.latency_ms
                }
            )

            # Complete trace
            self.audit_system.complete_trace(
                trace_id=trace_id,
                final_response=llm_response.content,
                status="completed"
            )

            return {
                "success": True,
                "response": llm_response.content,
                "metadata": {
                    "trace_id": trace_id,
                    "risk_tier": self.risk_tier.value,
                    "model": llm_response.model,
                    "tokens_used": llm_response.total_tokens,
                    "cost_usd": llm_response.cost_usd,
                    "latency_ms": llm_response.latency_ms,
                    "internet_access_allowed": internet_check.allowed
                }
            }

        except Exception as e:
            logger.error(f"Code assistance failed: {str(e)}")

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.ERROR_OCCURRED,
                component="code_assistant",
                action="assist",
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
                "error": "Assistant error",
                "details": str(e),
                "metadata": {"trace_id": trace_id}
            }
