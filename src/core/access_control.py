"""
Access Control: G4 - Permission Layers with RBAC/ABAC + Domain Isolation

Implements pre-retrieval filtering to prevent "see first then mask" leakage.
Enforces role-based and attribute-based access control.
"""

from enum import Enum
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Role(Enum):
    """User roles within Air NZ"""
    CUSTOMER_SERVICE = "customer_service"
    ENGINEERING = "engineering"
    DISPATCH_OCC = "dispatch_occ"
    SAFETY = "safety"
    REVENUE_MANAGEMENT = "revenue_management"
    AIRPORT_OPS = "airport_ops"
    MAINTENANCE = "maintenance"
    IT_SECURITY = "it_security"
    ADMIN = "admin"


class BusinessDomain(Enum):
    """Business domain isolation boundaries"""
    OPERATIONS = "operations"
    ENGINEERING = "engineering"
    CUSTOMER_SERVICE = "customer_service"
    HR = "hr"
    FINANCE = "finance"
    SAFETY = "safety"
    CARGO = "cargo"
    RETAIL = "retail"


class AircraftType(Enum):
    """Aircraft fleet types"""
    A320 = "a320"
    A321NEO = "a321neo"
    B787_9 = "b787_9"
    B787_10 = "b787_10"
    ATR72 = "atr72"


class SensitivityLevel(Enum):
    """Data sensitivity classification"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class UserAttributes:
    """Attribute-based access control attributes"""
    user_id: str
    role: Role
    business_domains: Set[BusinessDomain]
    aircraft_types: Set[AircraftType]
    bases: Set[str]  # AKL, CHC, WLG, etc.
    route_regions: Set[str]  # Domestic, Trans-Tasman, Pacific, etc.
    sensitivity_clearance: SensitivityLevel
    additional_attributes: Dict[str, str]


@dataclass
class ResourceAttributes:
    """Attributes of a resource being accessed"""
    resource_id: str
    resource_type: str  # document, policy, manual, work_order, etc.
    business_domain: BusinessDomain
    aircraft_types: Set[AircraftType]
    applicable_bases: Set[str]
    applicable_regions: Set[str]
    sensitivity_level: SensitivityLevel
    version: str
    effective_date: datetime
    metadata: Dict[str, str]


@dataclass
class AccessDecision:
    """Decision from access control check"""
    allowed: bool
    user_id: str
    resource_id: str
    reason: str
    matched_rules: List[str]
    timestamp: datetime


class AccessControlEngine:
    """
    Enforces RBAC/ABAC with pre-retrieval filtering.

    Key principles:
    - Filter BEFORE retrieval (not after)
    - Log both allow and deny decisions
    - Support multi-dimensional access (role + aircraft + base + domain)
    - Domain isolation enforcement
    """

    def __init__(self):
        self.role_permissions: Dict[Role, Set[str]] = {}
        self.domain_isolation_rules: Dict[BusinessDomain, Set[Role]] = {}
        self._initialize_role_permissions()
        self._initialize_domain_isolation()

    def _initialize_role_permissions(self):
        """Initialize default role-based permissions"""

        self.role_permissions = {
            Role.CUSTOMER_SERVICE: {
                "read:policies",
                "read:fare_rules",
                "read:baggage_policies",
                "read:rebooking_procedures",
                "read:customer_data",
            },
            Role.ENGINEERING: {
                "read:maintenance_manuals",
                "read:engineering_docs",
                "read:work_orders",
                "read:component_history",
                "read:airworthiness_directives",
            },
            Role.DISPATCH_OCC: {
                "read:flight_status",
                "read:weather",
                "read:crew_availability",
                "read:aircraft_status",
                "read:disruption_procedures",
                "read:gate_assignments",
            },
            Role.SAFETY: {
                "read:incident_reports",
                "read:safety_procedures",
                "read:risk_assessments",
                "read:audit_logs",
                "read:compliance_docs",
            },
            Role.MAINTENANCE: {
                "read:maintenance_manuals",
                "read:mel_procedures",
                "read:work_orders",
                "write:work_orders",
                "read:component_history",
            },
            Role.ADMIN: {
                "read:*",
                "write:*",
                "delete:*",
            }
        }

    def _initialize_domain_isolation(self):
        """Initialize business domain isolation rules"""

        self.domain_isolation_rules = {
            BusinessDomain.OPERATIONS: {
                Role.DISPATCH_OCC,
                Role.AIRPORT_OPS,
                Role.ADMIN,
            },
            BusinessDomain.ENGINEERING: {
                Role.ENGINEERING,
                Role.MAINTENANCE,
                Role.SAFETY,
                Role.ADMIN,
            },
            BusinessDomain.CUSTOMER_SERVICE: {
                Role.CUSTOMER_SERVICE,
                Role.ADMIN,
            },
            BusinessDomain.HR: {
                Role.ADMIN,
            },
            BusinessDomain.FINANCE: {
                Role.REVENUE_MANAGEMENT,
                Role.ADMIN,
            },
            BusinessDomain.SAFETY: {
                Role.SAFETY,
                Role.ENGINEERING,
                Role.ADMIN,
            },
            BusinessDomain.CARGO: {
                Role.CUSTOMER_SERVICE,  # Reusing for demo
                Role.ADMIN,
            },
        }

    def check_access(
        self,
        user: UserAttributes,
        resource: ResourceAttributes,
        action: str
    ) -> AccessDecision:
        """
        Check if user can access resource.

        This is the PRIMARY gate - all retrieval must pass through here BEFORE
        fetching data to prevent "see first then mask" leakage.

        Args:
            user: User requesting access
            resource: Resource being accessed
            action: Action being performed (read, write, delete)

        Returns:
            AccessDecision with allow/deny and detailed reason
        """
        matched_rules = []
        deny_reasons = []

        # Rule 1: Domain isolation check
        allowed_roles = self.domain_isolation_rules.get(resource.business_domain, set())
        if user.role not in allowed_roles:
            deny_reasons.append(
                f"Role {user.role.value} not authorized for domain {resource.business_domain.value}"
            )
        else:
            matched_rules.append("domain_isolation_passed")

        # Rule 2: Role-based permission check
        required_permission = f"{action}:{resource.resource_type}"
        user_permissions = self.role_permissions.get(user.role, set())

        has_permission = (
            required_permission in user_permissions or
            f"{action}:*" in user_permissions
        )

        if not has_permission:
            deny_reasons.append(
                f"Role {user.role.value} lacks permission {required_permission}"
            )
        else:
            matched_rules.append("role_permission_granted")

        # Rule 3: Sensitivity level check
        if resource.sensitivity_level.value > user.sensitivity_clearance.value:
            deny_reasons.append(
                f"User clearance {user.sensitivity_clearance.value} insufficient "
                f"for {resource.sensitivity_level.value} resource"
            )
        else:
            matched_rules.append("sensitivity_clearance_ok")

        # Rule 4: Business domain membership check
        if resource.business_domain not in user.business_domains:
            deny_reasons.append(
                f"User not member of required domain {resource.business_domain.value}"
            )
        else:
            matched_rules.append("domain_membership_ok")

        # Rule 5: Aircraft type applicability
        if resource.aircraft_types and not resource.aircraft_types.intersection(user.aircraft_types):
            deny_reasons.append(
                f"User aircraft types {user.aircraft_types} do not match "
                f"resource types {resource.aircraft_types}"
            )
        else:
            matched_rules.append("aircraft_type_match")

        # Rule 6: Base applicability
        if resource.applicable_bases and not resource.applicable_bases.intersection(user.bases):
            deny_reasons.append(
                f"User bases {user.bases} do not match "
                f"resource bases {resource.applicable_bases}"
            )
        else:
            matched_rules.append("base_match")

        # Final decision
        allowed = len(deny_reasons) == 0

        decision = AccessDecision(
            allowed=allowed,
            user_id=user.user_id,
            resource_id=resource.resource_id,
            reason="; ".join(deny_reasons) if deny_reasons else "Access granted",
            matched_rules=matched_rules,
            timestamp=datetime.now()
        )

        # Log decision (both allow and deny)
        log_level = logging.INFO if allowed else logging.WARNING
        logger.log(
            log_level,
            f"Access {'GRANTED' if allowed else 'DENIED'} - "
            f"User: {user.user_id} ({user.role.value}), "
            f"Resource: {resource.resource_id}, "
            f"Action: {action}, "
            f"Reason: {decision.reason}"
        )

        return decision

    def filter_retrievable_resources(
        self,
        user: UserAttributes,
        candidate_resources: List[ResourceAttributes],
        action: str = "read"
    ) -> List[ResourceAttributes]:
        """
        PRE-RETRIEVAL filtering: remove resources user cannot access.

        This ensures we NEVER retrieve sensitive data and then try to mask it.
        Filtering happens BEFORE any data leaves the secure store.

        Args:
            user: User requesting access
            candidate_resources: List of candidate resources
            action: Action being performed

        Returns:
            Filtered list of accessible resources
        """
        accessible = []

        for resource in candidate_resources:
            decision = self.check_access(user, resource, action)
            if decision.allowed:
                accessible.append(resource)

        logger.info(
            f"Pre-retrieval filter: {len(accessible)}/{len(candidate_resources)} "
            f"resources accessible for user {user.user_id}"
        )

        return accessible

    def get_user_scope(self, user: UserAttributes) -> Dict[str, Set]:
        """
        Get the complete access scope for a user.

        Useful for understanding what a user CAN access for debugging
        and audit purposes.

        Args:
            user: User to check

        Returns:
            Dictionary of accessible scopes
        """
        return {
            "domains": user.business_domains,
            "aircraft_types": user.aircraft_types,
            "bases": user.bases,
            "regions": user.route_regions,
            "max_sensitivity": user.sensitivity_clearance.value,
            "role_permissions": self.role_permissions.get(user.role, set()),
        }
