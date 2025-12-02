"""
Evidence Contract: G3 - Verifiable Citations with Version Control

Citations must include: document ID, version, effective date, applicability,
source system, paragraph locator, and content hash for verification.

For policy/procedure/manual answers: no evidence = no answer (or escalate).
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)


class SourceSystem(Enum):
    """Source systems for evidence"""
    POLICY_MANAGEMENT = "policy_management"
    MAINTENANCE_MANUAL = "maintenance_manual"
    OPERATIONS_MANUAL = "operations_manual"
    FLIGHT_OPS = "flight_ops"
    ENGINEERING_DOCS = "engineering_docs"
    WORK_ORDER_SYSTEM = "work_order_system"
    SAFETY_MANAGEMENT = "safety_management"
    SHAREPOINT = "sharepoint"
    CONFLUENCE = "confluence"


class EvidenceType(Enum):
    """Type of evidence source"""
    POLICY = "policy"
    PROCEDURE = "procedure"
    MANUAL = "manual"
    REGULATION = "regulation"
    NOTICE = "notice"
    WORK_ORDER = "work_order"
    CASE_HISTORY = "case_history"
    TRAINING_MATERIAL = "training_material"


@dataclass
class ApplicabilityContext:
    """Defines when and where evidence applies"""
    aircraft_types: List[str]
    bases: List[str]
    route_regions: List[str]
    business_domains: List[str]
    effective_from: datetime
    effective_until: Optional[datetime] = None
    superseded_by: Optional[str] = None


@dataclass
class Citation:
    """
    Complete citation with full traceability.

    This is the core contract - every AI-generated answer that references
    company knowledge MUST provide a citation that can be verified.
    """
    # Core identifiers
    document_id: str
    version: str
    revision: str
    title: str

    # Source tracking
    source_system: SourceSystem
    evidence_type: EvidenceType

    # Content location
    paragraph_locator: str  # Section/chapter/page/paragraph
    excerpt: str  # Actual text excerpt
    content_hash: str  # SHA-256 of excerpt for verification

    # Temporal validity
    effective_date: datetime
    retrieval_timestamp: datetime
    effective_until: Optional[datetime] = None

    # Applicability
    applicability: Optional[ApplicabilityContext] = None

    # Verification
    url: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Dict[str, str] = None

    def __post_init__(self):
        """Validate citation completeness"""
        if not self.content_hash:
            self.content_hash = self._compute_hash(self.excerpt)

    @staticmethod
    def _compute_hash(text: str) -> str:
        """Compute SHA-256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def verify_content(self, actual_content: str) -> bool:
        """
        Verify that the citation content hash matches actual content.

        Args:
            actual_content: The actual content from the source

        Returns:
            True if content hash matches
        """
        actual_hash = self._compute_hash(actual_content)
        return actual_hash == self.content_hash

    def is_currently_effective(self, as_of: Optional[datetime] = None) -> bool:
        """
        Check if citation is currently effective.

        Args:
            as_of: Date to check (defaults to now)

        Returns:
            True if effective on the given date
        """
        check_date = as_of or datetime.now()

        # Must be after effective date
        if check_date < self.effective_date:
            return False

        # Must be before expiry (if set)
        if self.effective_until and check_date >= self.effective_until:
            return False

        return True

    def to_display_format(self) -> str:
        """
        Format citation for display to users.

        Returns:
            Human-readable citation string
        """
        parts = [
            f"{self.title}",
            f"Version {self.version}",
            f"Effective {self.effective_date.strftime('%Y-%m-%d')}",
            f"Section {self.paragraph_locator}",
        ]

        if self.applicability:
            if self.applicability.aircraft_types:
                parts.append(f"Aircraft: {', '.join(self.applicability.aircraft_types)}")

        return " | ".join(parts)


@dataclass
class EvidencePackage:
    """
    Complete evidence package for an AI-generated answer.

    For R1-R3 use cases, this is MANDATORY.
    For R0, it may be optional depending on the query type.
    """
    query: str
    answer: str
    citations: List[Citation]
    retrieval_strategy: str  # hybrid, graph, tool, etc.
    confidence_score: float
    timestamp: datetime
    risk_tier: str

    def has_valid_evidence(self) -> bool:
        """
        Check if evidence package has valid citations.

        Returns:
            True if at least one valid citation exists
        """
        return len(self.citations) > 0

    def verify_all_citations(self, source_verifier) -> Dict[str, bool]:
        """
        Verify all citations against source systems.

        Args:
            source_verifier: Function to verify citation against source

        Returns:
            Dictionary mapping citation IDs to verification results
        """
        results = {}

        for citation in self.citations:
            citation_id = f"{citation.document_id}_{citation.version}"
            results[citation_id] = source_verifier(citation)

        return results


class EvidenceContractEnforcer:
    """
    Enforces evidence contract requirements.

    Key rules:
    - R1-R3: Citations REQUIRED (no evidence = no answer or escalate)
    - R0: Citations optional but encouraged
    - All citations must be verifiable
    - Outdated citations must be flagged
    """

    def __init__(self):
        self.citation_cache: Dict[str, Citation] = {}
        self.verification_failures: List[Dict] = []

    def validate_evidence_package(
        self,
        package: EvidencePackage,
        require_citations: bool = True
    ) -> tuple[bool, List[str]]:
        """
        Validate that evidence package meets requirements.

        Args:
            package: Evidence package to validate
            require_citations: Whether citations are mandatory

        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []

        # Check if citations exist when required
        if require_citations and not package.has_valid_evidence():
            errors.append(
                "CRITICAL: Citations required but none provided. "
                "Answer MUST NOT be returned to user."
            )

        # Validate each citation
        for i, citation in enumerate(package.citations):
            citation_errors = self._validate_citation(citation)
            if citation_errors:
                errors.extend([f"Citation {i+1}: {err}" for err in citation_errors])

        is_valid = len(errors) == 0

        if not is_valid:
            logger.error(
                f"Evidence validation FAILED for query: {package.query[:100]}... "
                f"Errors: {errors}"
            )

        return is_valid, errors

    def _validate_citation(self, citation: Citation) -> List[str]:
        """
        Validate individual citation completeness.

        Args:
            citation: Citation to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Required fields
        if not citation.document_id:
            errors.append("Missing document_id")
        if not citation.version:
            errors.append("Missing version")
        if not citation.effective_date:
            errors.append("Missing effective_date")
        if not citation.paragraph_locator:
            errors.append("Missing paragraph_locator")
        if not citation.excerpt:
            errors.append("Missing excerpt")
        if not citation.content_hash:
            errors.append("Missing content_hash")

        # Check if currently effective
        if not citation.is_currently_effective():
            errors.append(
                f"Citation is NOT currently effective. "
                f"Effective: {citation.effective_date}, "
                f"Until: {citation.effective_until}"
            )

        # Check if superseded
        if citation.applicability and citation.applicability.superseded_by:
            errors.append(
                f"Citation has been superseded by {citation.applicability.superseded_by}"
            )

        return errors

    def enforce_no_answer_without_evidence(
        self,
        package: EvidencePackage,
        risk_tier: str
    ) -> tuple[bool, str]:
        """
        Enforce "no evidence = no answer" policy for R1-R3.

        Args:
            package: Evidence package to check
            risk_tier: Risk tier (R0, R1, R2, R3)

        Returns:
            Tuple of (allow_answer, reason)
        """
        # R0 can proceed without citations
        if risk_tier == "R0":
            return True, "R0 tier allows answers without citations"

        # R1-R3 require valid evidence
        is_valid, errors = self.validate_evidence_package(
            package,
            require_citations=True
        )

        if not is_valid:
            return False, (
                f"Evidence validation failed for {risk_tier}: {'; '.join(errors)}. "
                "Answer blocked. Escalate to human."
            )

        return True, "Evidence validation passed"

    def create_citation_from_retrieval(
        self,
        document_id: str,
        version: str,
        source_system: SourceSystem,
        evidence_type: EvidenceType,
        excerpt: str,
        metadata: Dict
    ) -> Citation:
        """
        Create a citation from retrieval results.

        Args:
            document_id: Unique document identifier
            version: Document version
            source_system: Source system
            evidence_type: Type of evidence
            excerpt: Text excerpt
            metadata: Additional metadata from source

        Returns:
            Complete Citation object
        """
        citation = Citation(
            document_id=document_id,
            version=version,
            revision=metadata.get("revision", "0"),
            title=metadata.get("title", "Unknown"),
            source_system=source_system,
            evidence_type=evidence_type,
            paragraph_locator=metadata.get("paragraph_locator", "unknown"),
            excerpt=excerpt,
            content_hash="",  # Will be computed in __post_init__
            effective_date=metadata.get("effective_date", datetime.now()),
            retrieval_timestamp=datetime.now(),
            effective_until=metadata.get("effective_until"),
            url=metadata.get("url"),
            file_path=metadata.get("file_path"),
            metadata=metadata
        )

        # Cache citation
        cache_key = f"{document_id}_{version}"
        self.citation_cache[cache_key] = citation

        return citation
