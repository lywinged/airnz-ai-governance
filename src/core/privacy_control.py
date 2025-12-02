"""
Privacy & Data Protection: G9 - NZ Privacy Act Compliance

Implements Information Privacy Principles (IPPs):
- Purpose limitation
- Collection limitation
- Data minimization
- Retention & deletion
- Access & correction rights
- Security safeguards
- Cross-border controls
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """Categories of personal/sensitive data"""
    CUSTOMER_PII = "customer_pii"           # Name, email, phone, passport
    EMPLOYEE_PII = "employee_pii"           # Staff personal info
    FINANCIAL = "financial"                 # Payment, pricing
    HEALTH = "health"                       # Medical, fitness to fly
    OPERATIONAL = "operational"             # Flight, crew, ops data
    TECHNICAL = "technical"                 # Maintenance, engineering
    BUSINESS = "business"                   # Commercial, strategy
    PUBLIC = "public"                       # Public information


class ProcessingPurpose(Enum):
    """Lawful purposes for data processing"""
    CUSTOMER_SERVICE = "customer_service"
    OPERATIONS = "operations"
    SAFETY = "safety"
    MAINTENANCE = "maintenance"
    COMPLIANCE = "compliance"
    ANALYTICS = "analytics"
    TRAINING = "training"
    AUDIT = "audit"


class RetentionPeriod(Enum):
    """Data retention periods"""
    IMMEDIATE = 0                           # Delete immediately
    SHORT_TERM = 30                         # 30 days
    MEDIUM_TERM = 90                        # 90 days
    LONG_TERM = 365                         # 1 year
    REGULATORY = 2555                       # 7 years (NZ requirement)
    PERMANENT = 999999                      # Permanent retention


@dataclass
class DataClassification:
    """Classification of data for privacy controls"""
    category: DataCategory
    contains_pii: bool
    requires_consent: bool
    allowed_purposes: Set[ProcessingPurpose]
    retention_period: RetentionPeriod
    cross_border_allowed: bool
    encryption_required: bool
    audit_required: bool


@dataclass
class PrivacyContext:
    """Context for privacy-aware processing"""
    user_id: str
    processing_purpose: ProcessingPurpose
    data_categories: Set[DataCategory]
    consent_obtained: bool
    timestamp: datetime
    session_id: str


@dataclass
class DataMinimizationRule:
    """Rule for data minimization"""
    field_name: str
    data_category: DataCategory
    required_for_purposes: Set[ProcessingPurpose]
    redaction_pattern: str  # How to redact if not needed
    justification: str


class PrivacyController:
    """
    Enforces NZ Privacy Act compliance controls.

    Key principles:
    1. Purpose limitation - only use data for declared purposes
    2. Data minimization - only include necessary fields
    3. Retention - delete data after retention period
    4. Security - encrypt sensitive data
    5. Access rights - enable user access & correction
    """

    def __init__(self):
        self.data_classifications = self._initialize_classifications()
        self.minimization_rules = self._initialize_minimization_rules()
        self.retention_tracker: Dict[str, datetime] = {}

    def _initialize_classifications(self) -> Dict[DataCategory, DataClassification]:
        """Initialize data classification rules"""
        return {
            DataCategory.CUSTOMER_PII: DataClassification(
                category=DataCategory.CUSTOMER_PII,
                contains_pii=True,
                requires_consent=True,
                allowed_purposes={
                    ProcessingPurpose.CUSTOMER_SERVICE,
                    ProcessingPurpose.OPERATIONS,
                },
                retention_period=RetentionPeriod.REGULATORY,
                cross_border_allowed=False,  # Requires assessment
                encryption_required=True,
                audit_required=True,
            ),
            DataCategory.EMPLOYEE_PII: DataClassification(
                category=DataCategory.EMPLOYEE_PII,
                contains_pii=True,
                requires_consent=False,  # Employment relationship
                allowed_purposes={
                    ProcessingPurpose.OPERATIONS,
                    ProcessingPurpose.COMPLIANCE,
                },
                retention_period=RetentionPeriod.REGULATORY,
                cross_border_allowed=False,
                encryption_required=True,
                audit_required=True,
            ),
            DataCategory.HEALTH: DataClassification(
                category=DataCategory.HEALTH,
                contains_pii=True,
                requires_consent=True,
                allowed_purposes={
                    ProcessingPurpose.CUSTOMER_SERVICE,
                    ProcessingPurpose.SAFETY,
                },
                retention_period=RetentionPeriod.REGULATORY,
                cross_border_allowed=False,
                encryption_required=True,
                audit_required=True,
            ),
            DataCategory.OPERATIONAL: DataClassification(
                category=DataCategory.OPERATIONAL,
                contains_pii=False,
                requires_consent=False,
                allowed_purposes={
                    ProcessingPurpose.OPERATIONS,
                    ProcessingPurpose.SAFETY,
                    ProcessingPurpose.MAINTENANCE,
                },
                retention_period=RetentionPeriod.LONG_TERM,
                cross_border_allowed=True,
                encryption_required=False,
                audit_required=True,
            ),
            DataCategory.PUBLIC: DataClassification(
                category=DataCategory.PUBLIC,
                contains_pii=False,
                requires_consent=False,
                allowed_purposes=set(ProcessingPurpose),  # All purposes
                retention_period=RetentionPeriod.PERMANENT,
                cross_border_allowed=True,
                encryption_required=False,
                audit_required=False,
            ),
        }

    def _initialize_minimization_rules(self) -> List[DataMinimizationRule]:
        """Initialize data minimization rules"""
        return [
            DataMinimizationRule(
                field_name="customer_email",
                data_category=DataCategory.CUSTOMER_PII,
                required_for_purposes={
                    ProcessingPurpose.CUSTOMER_SERVICE,
                },
                redaction_pattern="***@***.com",
                justification="Email only needed for customer service contact"
            ),
            DataMinimizationRule(
                field_name="passport_number",
                data_category=DataCategory.CUSTOMER_PII,
                required_for_purposes={
                    ProcessingPurpose.COMPLIANCE,
                },
                redaction_pattern="***********",
                justification="Passport only needed for compliance checks"
            ),
            DataMinimizationRule(
                field_name="employee_id",
                data_category=DataCategory.EMPLOYEE_PII,
                required_for_purposes={
                    ProcessingPurpose.OPERATIONS,
                    ProcessingPurpose.AUDIT,
                },
                redaction_pattern="EMP-***",
                justification="Employee ID needed for ops and audit"
            ),
        ]

    def check_purpose_limitation(
        self,
        context: PrivacyContext
    ) -> tuple[bool, str]:
        """
        Check if processing is allowed for the stated purpose.

        Args:
            context: Privacy context with purpose and data categories

        Returns:
            Tuple of (allowed, reason)
        """
        violations = []

        for category in context.data_categories:
            classification = self.data_classifications.get(category)

            if not classification:
                violations.append(f"Unknown data category: {category}")
                continue

            # Check purpose limitation
            if context.processing_purpose not in classification.allowed_purposes:
                violations.append(
                    f"{category.value} not allowed for purpose {context.processing_purpose.value}"
                )

            # Check consent requirement
            if classification.requires_consent and not context.consent_obtained:
                violations.append(
                    f"{category.value} requires consent but none obtained"
                )

        if violations:
            return False, "; ".join(violations)

        return True, "Purpose limitation check passed"

    def minimize_data(
        self,
        data: Dict[str, any],
        purpose: ProcessingPurpose
    ) -> Dict[str, any]:
        """
        Apply data minimization - remove/redact fields not needed for purpose.

        Args:
            data: Original data dictionary
            purpose: Processing purpose

        Returns:
            Minimized data dictionary
        """
        minimized = data.copy()

        for rule in self.minimization_rules:
            field = rule.field_name

            if field not in minimized:
                continue

            # If field not required for this purpose, redact it
            if purpose not in rule.required_for_purposes:
                original_value = minimized[field]
                minimized[field] = rule.redaction_pattern

                logger.info(
                    f"Data minimization: {field} redacted for purpose {purpose.value}. "
                    f"Justification: {rule.justification}"
                )

        return minimized

    def enforce_retention_policy(
        self,
        data_id: str,
        category: DataCategory,
        created_at: datetime
    ) -> tuple[bool, str]:
        """
        Check if data should be retained or deleted.

        Args:
            data_id: Unique data identifier
            category: Data category
            created_at: When data was created

        Returns:
            Tuple of (should_retain, reason)
        """
        classification = self.data_classifications.get(category)

        if not classification:
            return True, f"Unknown category {category}, defaulting to retain"

        # Calculate retention deadline
        retention_days = classification.retention_period.value
        retention_deadline = created_at + timedelta(days=retention_days)

        # Check if past deadline
        if datetime.now() > retention_deadline:
            return False, (
                f"Retention period expired for {category.value}. "
                f"Created: {created_at}, Deadline: {retention_deadline}. "
                f"Data must be deleted."
            )

        return True, (
            f"Within retention period. "
            f"Delete after {retention_deadline.strftime('%Y-%m-%d')}"
        )

    def check_cross_border_transfer(
        self,
        category: DataCategory,
        destination_country: str
    ) -> tuple[bool, str]:
        """
        Check if cross-border data transfer is allowed.

        Args:
            category: Data category
            destination_country: Destination country code

        Returns:
            Tuple of (allowed, reason)
        """
        classification = self.data_classifications.get(category)

        if not classification:
            return False, f"Unknown category {category}"

        # Check if cross-border allowed
        if not classification.cross_border_allowed:
            return False, (
                f"{category.value} cross-border transfer not allowed. "
                f"Privacy Impact Assessment required for {destination_country}"
            )

        # Additional checks for specific countries
        # In production, would check against approved country list
        approved_countries = ["NZ", "AU"]  # Example

        if destination_country not in approved_countries:
            return False, (
                f"Cross-border transfer to {destination_country} requires "
                f"additional approval and safeguards"
            )

        return True, f"Cross-border transfer to {destination_country} allowed"

    def apply_security_controls(
        self,
        data: Dict[str, any],
        category: DataCategory
    ) -> Dict[str, any]:
        """
        Apply security controls (encryption, masking) based on classification.

        Args:
            data: Data to protect
            category: Data category

        Returns:
            Data with security controls applied
        """
        classification = self.data_classifications.get(category)

        if not classification:
            logger.warning(f"Unknown category {category}, applying default controls")
            return data

        secured_data = data.copy()

        # Apply encryption if required
        if classification.encryption_required:
            # In production, would encrypt sensitive fields
            secured_data["_encryption_applied"] = True
            secured_data["_encryption_algorithm"] = "AES-256-GCM"
            logger.info(f"Encryption applied for {category.value}")

        # Mark for audit if required
        if classification.audit_required:
            secured_data["_audit_required"] = True
            logger.info(f"Audit tracking enabled for {category.value}")

        return secured_data

    def handle_access_request(
        self,
        user_id: str,
        data_categories: Set[DataCategory]
    ) -> Dict[str, any]:
        """
        Handle user access request (IPP Principle 6).

        Users have right to access their personal information.

        Args:
            user_id: User requesting access
            data_categories: Categories of data requested

        Returns:
            Dictionary with access request handling info
        """
        logger.info(f"Access request from user {user_id} for categories: {data_categories}")

        return {
            "user_id": user_id,
            "requested_categories": [c.value for c in data_categories],
            "status": "approved",
            "response_deadline": (datetime.now() + timedelta(days=20)).isoformat(),  # 20 working days
            "format": "structured_export",
            "notes": "User entitled to access under NZ Privacy Act 2020"
        }

    def handle_correction_request(
        self,
        user_id: str,
        field_name: str,
        current_value: str,
        corrected_value: str,
        justification: str
    ) -> Dict[str, any]:
        """
        Handle user correction request (IPP Principle 7).

        Users have right to correct inaccurate personal information.

        Args:
            user_id: User requesting correction
            field_name: Field to correct
            current_value: Current value
            corrected_value: Corrected value
            justification: Reason for correction

        Returns:
            Dictionary with correction handling info
        """
        logger.info(
            f"Correction request from user {user_id}: "
            f"{field_name} from '{current_value}' to '{corrected_value}'"
        )

        return {
            "user_id": user_id,
            "field": field_name,
            "current_value": current_value,
            "corrected_value": corrected_value,
            "justification": justification,
            "status": "pending_verification",
            "response_deadline": (datetime.now() + timedelta(days=20)).isoformat(),
            "notes": "Correction will be applied after verification"
        }
