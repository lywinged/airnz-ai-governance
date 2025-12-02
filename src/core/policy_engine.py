"""
Policy Engine: G2 - Risk Tiering + Dynamic Gates

Implements R0-R3 risk tiers with runtime capability controls.
Enforces change control for model/prompt/policy updates.
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskTier(Enum):
    """Risk tier classification for AI use cases"""
    R0 = "low_risk_internal"           # Internal productivity
    R1 = "external_customer_facing"    # Customer-facing content
    R2 = "operations_decision_support" # Ops/maintenance with human-in-loop
    R3 = "actions_closed_loop"         # Automated actions


class CapabilityType(Enum):
    """Available capabilities that can be controlled per risk tier"""
    INTERNET_ACCESS = "internet_access"
    TOOL_INVOCATION = "tool_invocation"
    WRITE_OPERATIONS = "write_operations"
    CITATIONS_REQUIRED = "citations_required"
    DUAL_CONTROL_REQUIRED = "dual_control_required"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"
    ROLLBACK_REQUIRED = "rollback_required"


@dataclass
class PolicyVersion:
    """Versioned policy configuration"""
    version: str
    effective_date: datetime
    approved_by: str
    risk_tier: RiskTier
    allowed_capabilities: Set[CapabilityType]
    blocked_capabilities: Set[CapabilityType]
    description: str
    rollback_version: Optional[str] = None


@dataclass
class ExecutionContext:
    """Runtime execution context for an AI request"""
    user_id: str
    role: str
    business_domain: str
    use_case_id: str
    risk_tier: RiskTier
    session_id: str
    timestamp: datetime


@dataclass
class GateDecision:
    """Decision from a capability gate check"""
    allowed: bool
    capability: CapabilityType
    risk_tier: RiskTier
    reason: str
    policy_version: str
    timestamp: datetime


class PolicyEngine:
    """
    Enforces risk-based policies and capability gates.

    Key responsibilities:
    - Risk tier assignment
    - Capability gate enforcement
    - Policy version management
    - Change control compliance
    """

    def __init__(self):
        self.policies: Dict[str, PolicyVersion] = {}
        self.active_policies: Dict[RiskTier, PolicyVersion] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self):
        """Initialize default policies for each risk tier"""

        # R0: Low-risk internal productivity
        r0_policy = PolicyVersion(
            version="1.0.0",
            effective_date=datetime.now(),
            approved_by="system_admin",
            risk_tier=RiskTier.R0,
            allowed_capabilities={
                CapabilityType.INTERNET_ACCESS,
            },
            blocked_capabilities={
                CapabilityType.WRITE_OPERATIONS,
                CapabilityType.DUAL_CONTROL_REQUIRED,
            },
            description="Internal productivity: writing, coding, summarization"
        )

        # R1: External/Customer-facing
        r1_policy = PolicyVersion(
            version="1.0.0",
            effective_date=datetime.now(),
            approved_by="system_admin",
            risk_tier=RiskTier.R1,
            allowed_capabilities={
                CapabilityType.TOOL_INVOCATION,
                CapabilityType.CITATIONS_REQUIRED,
            },
            blocked_capabilities={
                CapabilityType.WRITE_OPERATIONS,
                CapabilityType.INTERNET_ACCESS,
            },
            description="Customer service: policy clarification, baggage/rebooking guidance"
        )

        # R2: Operations/Maintenance decision support
        r2_policy = PolicyVersion(
            version="1.0.0",
            effective_date=datetime.now(),
            approved_by="system_admin",
            risk_tier=RiskTier.R2,
            allowed_capabilities={
                CapabilityType.TOOL_INVOCATION,
                CapabilityType.CITATIONS_REQUIRED,
                CapabilityType.HUMAN_APPROVAL_REQUIRED,
            },
            blocked_capabilities={
                CapabilityType.WRITE_OPERATIONS,
                CapabilityType.INTERNET_ACCESS,
            },
            description="Ops/maintenance decision support with mandatory human review"
        )

        # R3: Actions & closed loops
        r3_policy = PolicyVersion(
            version="1.0.0",
            effective_date=datetime.now(),
            approved_by="system_admin",
            risk_tier=RiskTier.R3,
            allowed_capabilities={
                CapabilityType.TOOL_INVOCATION,
                CapabilityType.WRITE_OPERATIONS,
                CapabilityType.CITATIONS_REQUIRED,
                CapabilityType.DUAL_CONTROL_REQUIRED,
                CapabilityType.HUMAN_APPROVAL_REQUIRED,
                CapabilityType.ROLLBACK_REQUIRED,
            },
            blocked_capabilities={
                CapabilityType.INTERNET_ACCESS,
            },
            description="Automated actions with dual control and rollback"
        )

        self.policies = {
            "r0_v1.0.0": r0_policy,
            "r1_v1.0.0": r1_policy,
            "r2_v1.0.0": r2_policy,
            "r3_v1.0.0": r3_policy,
        }

        self.active_policies = {
            RiskTier.R0: r0_policy,
            RiskTier.R1: r1_policy,
            RiskTier.R2: r2_policy,
            RiskTier.R3: r3_policy,
        }

    def check_capability(
        self,
        context: ExecutionContext,
        capability: CapabilityType
    ) -> GateDecision:
        """
        Check if a capability is allowed for the given execution context.

        Args:
            context: Current execution context
            capability: Capability to check

        Returns:
            GateDecision with allowed/denied and reason
        """
        policy = self.active_policies.get(context.risk_tier)

        if not policy:
            return GateDecision(
                allowed=False,
                capability=capability,
                risk_tier=context.risk_tier,
                reason=f"No active policy found for risk tier {context.risk_tier}",
                policy_version="unknown",
                timestamp=datetime.now()
            )

        # Check if capability is explicitly blocked
        if capability in policy.blocked_capabilities:
            return GateDecision(
                allowed=False,
                capability=capability,
                risk_tier=context.risk_tier,
                reason=f"Capability {capability.value} is blocked for {context.risk_tier.value}",
                policy_version=policy.version,
                timestamp=datetime.now()
            )

        # Check if capability is explicitly allowed
        if capability in policy.allowed_capabilities:
            return GateDecision(
                allowed=True,
                capability=capability,
                risk_tier=context.risk_tier,
                reason=f"Capability {capability.value} is allowed for {context.risk_tier.value}",
                policy_version=policy.version,
                timestamp=datetime.now()
            )

        # Default deny if not explicitly allowed
        return GateDecision(
            allowed=False,
            capability=capability,
            risk_tier=context.risk_tier,
            reason=f"Capability {capability.value} not explicitly allowed for {context.risk_tier.value}",
            policy_version=policy.version,
            timestamp=datetime.now()
        )

    def update_policy(
        self,
        risk_tier: RiskTier,
        new_policy: PolicyVersion,
        approved_by: str,
        regression_test_results: Dict
    ) -> bool:
        """
        Update policy with change control compliance.

        Args:
            risk_tier: Risk tier to update
            new_policy: New policy version
            approved_by: Approver identifier
            regression_test_results: Test results showing no degradation

        Returns:
            True if update successful
        """
        logger.info(
            f"Policy update requested for {risk_tier.value} "
            f"from v{self.active_policies[risk_tier].version} to v{new_policy.version}"
        )

        # Store current policy for rollback
        current_policy = self.active_policies[risk_tier]
        new_policy.rollback_version = current_policy.version

        # Validate regression tests passed
        if not regression_test_results.get("passed", False):
            logger.error("Policy update rejected: regression tests failed")
            return False

        # Store new policy version
        policy_key = f"{risk_tier.value}_v{new_policy.version}"
        self.policies[policy_key] = new_policy

        # Activate new policy
        self.active_policies[risk_tier] = new_policy

        logger.info(
            f"Policy updated successfully for {risk_tier.value} to v{new_policy.version} "
            f"by {approved_by}"
        )

        return True

    def rollback_policy(self, risk_tier: RiskTier) -> bool:
        """
        Rollback to previous policy version.

        Args:
            risk_tier: Risk tier to rollback

        Returns:
            True if rollback successful
        """
        current_policy = self.active_policies[risk_tier]

        if not current_policy.rollback_version:
            logger.error(f"No rollback version available for {risk_tier.value}")
            return False

        rollback_key = f"{risk_tier.value}_v{current_policy.rollback_version}"
        rollback_policy = self.policies.get(rollback_key)

        if not rollback_policy:
            logger.error(f"Rollback policy not found: {rollback_key}")
            return False

        self.active_policies[risk_tier] = rollback_policy
        logger.info(
            f"Policy rolled back for {risk_tier.value} "
            f"from v{current_policy.version} to v{rollback_policy.version}"
        )

        return True

    def get_required_controls(self, context: ExecutionContext) -> List[CapabilityType]:
        """
        Get list of required controls for the execution context.

        Args:
            context: Current execution context

        Returns:
            List of required capability controls
        """
        policy = self.active_policies.get(context.risk_tier)
        if not policy:
            return []

        return [
            cap for cap in policy.allowed_capabilities
            if "REQUIRED" in cap.value.upper()
        ]
