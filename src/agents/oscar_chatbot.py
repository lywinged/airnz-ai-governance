"""
R1 Agent: Oscar Chatbot (Customer Service)

Evidence-backed customer service chatbot with verifiable citations.
Risk Tier: R1 (External/Customer-facing)

Key requirements:
- Citations REQUIRED (no evidence = no answer or escalate)
- Pre-retrieval permission filtering
- Privacy controls for customer data
- Full audit trail
"""

from datetime import datetime
from typing import Dict, Optional
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
    RetrievalRouter, QueryContext, HybridRetriever
)
from ..core.privacy_control import (
    PrivacyController, PrivacyContext, DataCategory, ProcessingPurpose
)
from ..core.audit_system import (
    AuditSystem, AuditEventType
)

logger = logging.getLogger(__name__)


class OscarChatbot:
    """
    R1: Customer-facing chatbot with evidence-backed responses.

    Use cases:
    - Baggage policy questions
    - Booking and rebooking assistance
    - Fare rules clarification
    - Flight information
    - General customer service
    """

    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.access_control = AccessControlEngine()
        self.evidence_enforcer = EvidenceContractEnforcer()
        self.retrieval_router = RetrievalRouter()
        self.privacy_controller = PrivacyController()
        self.audit_system = AuditSystem()

        self.risk_tier = RiskTier.R1

    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str
    ) -> Dict:
        """
        Process customer query with full governance controls.

        Args:
            query: Customer question
            user_id: Customer/agent user ID
            session_id: Session identifier

        Returns:
            Response dictionary with answer and metadata
        """
        # Create execution context
        execution_context = ExecutionContext(
            user_id=user_id,
            role="customer_service",
            business_domain="customer_service",
            use_case_id="oscar_chatbot",
            risk_tier=self.risk_tier,
            session_id=session_id,
            timestamp=datetime.now()
        )

        # Create audit trace
        trace_id = f"oscar_{session_id}_{datetime.now().timestamp()}"
        trace = self.audit_system.create_trace(
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            query=query,
            risk_tier=self.risk_tier.value,
            model_version="claude-sonnet-4.5",
            prompt_version="oscar_v1.0",
            retrieval_index_version="policies_v2.3",
            policy_version="1.0.0"
        )

        # Log request received
        self.audit_system.log_event(
            trace_id=trace_id,
            event_type=AuditEventType.REQUEST_RECEIVED,
            component="oscar_chatbot",
            action="query_received",
            status="success",
            details={"query": query[:200]}
        )

        try:
            # Step 1: Policy gate check - ensure citations required for R1
            citation_check = self.policy_engine.check_capability(
                execution_context,
                CapabilityType.CITATIONS_REQUIRED
            )

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.POLICY_CHECK,
                component="policy_engine",
                action="check_citation_requirement",
                status="success" if citation_check.allowed else "denied",
                details={"reason": citation_check.reason}
            )

            # Step 2: Privacy check
            privacy_context = PrivacyContext(
                user_id=user_id,
                processing_purpose=ProcessingPurpose.CUSTOMER_SERVICE,
                data_categories={DataCategory.CUSTOMER_PII},
                consent_obtained=True,
                timestamp=datetime.now(),
                session_id=session_id
            )

            privacy_allowed, privacy_reason = self.privacy_controller.check_purpose_limitation(
                privacy_context
            )

            if not privacy_allowed:
                self.audit_system.log_event(
                    trace_id=trace_id,
                    event_type=AuditEventType.POLICY_CHECK,
                    component="privacy_controller",
                    action="check_purpose_limitation",
                    status="denied",
                    details={"reason": privacy_reason}
                )

                return self._create_error_response(
                    trace_id,
                    "Privacy check failed",
                    privacy_reason
                )

            # Step 3: Create query context and route
            query_context = QueryContext(
                query=query,
                user_id=user_id,
                role="customer_service",
                business_domain="customer_service",
                risk_tier=self.risk_tier.value,
                session_id=session_id,
                timestamp=datetime.now()
            )

            strategy, intent = self.retrieval_router.route_query(query_context)

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.INTENT_DETECTED,
                component="retrieval_router",
                action="route_query",
                status="success",
                details={
                    "intent": intent.value,
                    "strategy": strategy.value
                }
            )

            # Step 4: Execute retrieval with access control
            # Create user attributes for access control
            user_attrs = UserAttributes(
                user_id=user_id,
                role=Role.CUSTOMER_SERVICE,
                business_domains={BusinessDomain.CUSTOMER_SERVICE},
                aircraft_types=set(AircraftType),  # All aircraft types for CS
                bases={"AKL", "CHC", "WLG"},
                route_regions={"Domestic", "Trans-Tasman", "Pacific"},
                sensitivity_clearance=SensitivityLevel.INTERNAL,
                additional_attributes={}
            )

            # Simulate retrieval results (in production, would query actual systems)
            retrieval_results = self._simulate_retrieval(query, user_attrs)

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.RETRIEVAL_EXECUTED,
                component="retrieval_router",
                action="retrieve_evidence",
                status="success",
                details={
                    "results_count": len(retrieval_results),
                    "strategy": strategy.value
                }
            )

            # Step 5: Create evidence package with citations
            citations = self._create_citations_from_results(retrieval_results)

            evidence_package = EvidencePackage(
                query=query,
                answer="",  # Will be filled after generation
                citations=citations,
                retrieval_strategy=strategy.value,
                confidence_score=0.85,
                timestamp=datetime.now(),
                risk_tier=self.risk_tier.value
            )

            # Step 6: Validate evidence contract
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
                details={
                    "is_valid": is_valid,
                    "errors": errors,
                    "citation_count": len(citations)
                }
            )

            # If evidence validation fails, must not return answer
            if not is_valid:
                return self._escalate_to_human(
                    trace_id,
                    query,
                    "Insufficient evidence for customer-facing answer",
                    errors
                )

            # Step 7: Generate response (simulated)
            answer = self._generate_answer(query, citations)
            evidence_package.answer = answer

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.RESPONSE_GENERATED,
                component="oscar_chatbot",
                action="generate_response",
                status="success",
                details={
                    "answer_length": len(answer),
                    "citation_count": len(citations)
                }
            )

            # Step 8: Complete trace
            self.audit_system.complete_trace(
                trace_id=trace_id,
                final_response=answer,
                status="completed"
            )

            # Return response with citations
            return {
                "success": True,
                "answer": answer,
                "citations": [c.to_display_format() for c in citations],
                "metadata": {
                    "trace_id": trace_id,
                    "risk_tier": self.risk_tier.value,
                    "confidence": evidence_package.confidence_score,
                    "retrieval_strategy": strategy.value,
                    "intent": intent.value
                }
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")

            self.audit_system.log_event(
                trace_id=trace_id,
                event_type=AuditEventType.ERROR_OCCURRED,
                component="oscar_chatbot",
                action="process_query",
                status="error",
                details={"error": str(e)}
            )

            self.audit_system.complete_trace(
                trace_id=trace_id,
                final_response="Error occurred",
                status="failed"
            )

            return self._create_error_response(trace_id, "Internal error", str(e))

    def _simulate_retrieval(
        self,
        query: str,
        user_attrs: UserAttributes
    ) -> list:
        """Simulate retrieval results (placeholder)"""
        return [
            {
                "document_id": "POL-BAGGAGE-001",
                "version": "3.2",
                "title": "Checked Baggage Allowance Policy",
                "excerpt": "Economy passengers are entitled to 2 pieces of checked baggage, "
                          "each not exceeding 23kg. Excess baggage charges apply beyond this allowance.",
                "source_system": SourceSystem.POLICY_MANAGEMENT,
                "evidence_type": EvidenceType.POLICY,
                "paragraph_locator": "Section 2.1.3",
                "effective_date": datetime(2024, 1, 1),
                "metadata": {
                    "aircraft_types": ["all"],
                    "route_regions": ["all"]
                }
            }
        ]

    def _create_citations_from_results(self, results: list) -> list:
        """Create Citation objects from retrieval results"""
        citations = []

        for result in results:
            citation = self.evidence_enforcer.create_citation_from_retrieval(
                document_id=result["document_id"],
                version=result["version"],
                source_system=result["source_system"],
                evidence_type=result["evidence_type"],
                excerpt=result["excerpt"],
                metadata={
                    "title": result["title"],
                    "paragraph_locator": result["paragraph_locator"],
                    "effective_date": result["effective_date"],
                }
            )
            citations.append(citation)

        return citations

    def _generate_answer(self, query: str, citations: list) -> str:
        """Generate answer from citations (simulated)"""
        # In production, this would use an LLM with citations as context
        if citations:
            return (
                f"Based on our current baggage policy, economy passengers are entitled "
                f"to 2 pieces of checked baggage, each not exceeding 23kg. "
                f"Excess baggage charges apply beyond this allowance.\n\n"
                f"Source: {citations[0].to_display_format()}"
            )
        return "I don't have enough information to answer this question. Let me connect you with an agent."

    def _escalate_to_human(
        self,
        trace_id: str,
        query: str,
        reason: str,
        errors: list
    ) -> Dict:
        """Escalate to human agent when evidence is insufficient"""
        self.audit_system.log_event(
            trace_id=trace_id,
            event_type=AuditEventType.APPROVAL_REQUESTED,
            component="oscar_chatbot",
            action="escalate_to_human",
            status="escalated",
            details={
                "reason": reason,
                "errors": errors
            }
        )

        self.audit_system.complete_trace(
            trace_id=trace_id,
            final_response="Escalated to human agent",
            status="escalated"
        )

        return {
            "success": False,
            "escalated": True,
            "reason": reason,
            "message": "I'm connecting you with one of our customer service agents who can better assist you.",
            "metadata": {
                "trace_id": trace_id,
                "errors": errors
            }
        }

    def _create_error_response(
        self,
        trace_id: str,
        error_type: str,
        details: str
    ) -> Dict:
        """Create error response"""
        return {
            "success": False,
            "error": error_type,
            "details": details,
            "metadata": {
                "trace_id": trace_id
            }
        }
