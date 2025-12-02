"""
G1: AI Safety-Case Implementation

Each AI use case has a complete assurance package:
- Use-case boundary definition
- Hazard identification
- Risk assessment
- Controls implementation
- Residual risk tracking
- Ongoing assurance
- Shutdown strategy
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import json


class HazardSeverity(Enum):
    """Hazard severity levels"""
    CATASTROPHIC = 5  # System failure, safety risk
    CRITICAL = 4      # Major operational impact
    MAJOR = 3         # Significant service degradation
    MINOR = 2         # Limited impact
    NEGLIGIBLE = 1    # Minimal impact


class HazardLikelihood(Enum):
    """Hazard likelihood levels"""
    FREQUENT = 5      # Expected to occur often
    PROBABLE = 4      # Will occur several times
    OCCASIONAL = 3    # Likely to occur sometime
    REMOTE = 2        # Unlikely but possible
    IMPROBABLE = 1    # Very unlikely


class ControlStatus(Enum):
    """Control implementation status"""
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    PLANNED = "planned"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class Hazard:
    """Identified hazard"""
    hazard_id: str
    description: str
    severity: HazardSeverity
    likelihood: HazardLikelihood
    category: str  # technical, operational, regulatory, etc.
    risk_score: int = 0  # severity * likelihood (auto-calculated)

    def __post_init__(self):
        self.risk_score = self.severity.value * self.likelihood.value


@dataclass
class Control:
    """Risk control/mitigation"""
    control_id: str
    description: str
    control_type: str  # preventive, detective, corrective
    status: ControlStatus
    effectiveness: float  # 0-1 (how much it reduces risk)
    verification_method: str
    owner: str


@dataclass
class ResidualRisk:
    """Risk remaining after controls"""
    hazard_id: str
    original_risk_score: int
    residual_risk_score: int
    risk_reduction: float
    acceptable: bool
    justification: str


@dataclass
class SafetyCase:
    """
    Complete safety case for an AI use case.

    Aligns with aviation SMS principles.
    """
    use_case_id: str
    use_case_name: str
    risk_tier: str

    # Boundary
    scope: str
    in_scope: List[str]
    out_of_scope: List[str]

    # Hazards
    hazards: List[Hazard]

    # Controls
    controls: List[Control]

    # Residual risk
    residual_risks: List[ResidualRisk]

    # Assurance
    assurance_activities: List[Dict]
    monitoring_metrics: List[str]

    # Shutdown
    shutdown_criteria: List[str]
    shutdown_procedure: str

    # Metadata
    created_by: str
    approved_by: Optional[str]
    created_at: datetime
    last_reviewed: datetime
    next_review_due: datetime

    def calculate_overall_risk(self) -> Dict:
        """Calculate overall risk assessment"""
        if not self.hazards:
            return {"status": "no_hazards", "score": 0}

        total_risk = sum(h.risk_score for h in self.hazards)
        avg_risk = total_risk / len(self.hazards)
        max_risk = max(h.risk_score for h in self.hazards)

        return {
            "total_hazards": len(self.hazards),
            "total_risk_score": total_risk,
            "average_risk": avg_risk,
            "maximum_risk": max_risk,
            "high_risk_hazards": len([h for h in self.hazards if h.risk_score >= 15])
        }

    def get_control_coverage(self) -> Dict:
        """Get control implementation coverage"""
        total = len(self.controls)
        if total == 0:
            return {"coverage": 0, "status": "no_controls"}

        implemented = len([c for c in self.controls if c.status == ControlStatus.IMPLEMENTED])
        partial = len([c for c in self.controls if c.status == ControlStatus.PARTIAL])

        return {
            "total_controls": total,
            "implemented": implemented,
            "partial": partial,
            "coverage_rate": implemented / total,
            "status": "adequate" if implemented / total >= 0.9 else "inadequate"
        }

    @property
    def residual_risk_level(self) -> str:
        """
        Derive a simple residual risk band from residual_risks.
        LOW/MEDIUM/HIGH based on max residual_risk_score; defaults LOW if none.
        """
        if not self.residual_risks:
            return "LOW"

        max_residual = max(r.residual_risk_score for r in self.residual_risks)
        if max_residual <= 4:
            return "LOW"
        if max_residual <= 9:
            return "MEDIUM"
        return "HIGH"

    def is_acceptable(self) -> bool:
        """Check if all residual risks are acceptable"""
        return all(r.acceptable for r in self.residual_risks)

    def to_dict(self) -> Dict:
        """Export safety case as dictionary"""
        return {
            "use_case_id": self.use_case_id,
            "use_case_name": self.use_case_name,
            "risk_tier": self.risk_tier,
            "scope": self.scope,
            "hazards": [
                {
                    "id": h.hazard_id,
                    "description": h.description,
                    "severity": h.severity.name,
                    "likelihood": h.likelihood.name,
                    "risk_score": h.risk_score
                }
                for h in self.hazards
            ],
            "controls": [
                {
                    "id": c.control_id,
                    "description": c.description,
                    "status": c.status.value,
                    "effectiveness": c.effectiveness
                }
                for c in self.controls
            ],
            "residual_risks": [
                {
                    "hazard_id": r.hazard_id,
                    "original_risk": r.original_risk_score,
                    "residual_risk": r.residual_risk_score,
                    "acceptable": r.acceptable
                }
                for r in self.residual_risks
            ],
            "overall_risk": self.calculate_overall_risk(),
            "control_coverage": self.get_control_coverage(),
            "acceptable": self.is_acceptable(),
            "created_at": self.created_at.isoformat(),
            "last_reviewed": self.last_reviewed.isoformat()
        }


class SafetyCaseRegistry:
    """
    Registry of all safety cases.

    Manages safety cases for all AI use cases.
    """

    def __init__(self):
        self.safety_cases: Dict[str, SafetyCase] = {}
        self._initialize_default_cases()

    def _initialize_default_cases(self):
        """Initialize safety cases for all agents"""

        # R0: Code Assistant
        self.register_safety_case(self._create_code_assistant_safety_case())

        # R1: Oscar Chatbot
        self.register_safety_case(self._create_oscar_safety_case())

        # R2: Disruption Management
        self.register_safety_case(self._create_disruption_mgmt_safety_case())

        # R3: Maintenance Automation
        self.register_safety_case(self._create_maintenance_auto_safety_case())

    def _create_code_assistant_safety_case(self) -> SafetyCase:
        """Safety case for R0 Code Assistant"""

        hazards = [
            Hazard(
                hazard_id="R0-H1",
                description="AI suggests insecure code (SQL injection, XSS, etc.)",
                severity=HazardSeverity.MAJOR,
                likelihood=HazardLikelihood.OCCASIONAL,
                category="technical"
            ),
            Hazard(
                hazard_id="R0-H2",
                description="AI provides incorrect technical advice leading to bugs",
                severity=HazardSeverity.MINOR,
                likelihood=HazardLikelihood.PROBABLE,
                category="operational"
            ),
        ]

        controls = [
            Control(
                control_id="R0-C1",
                description="Code review required before deployment",
                control_type="detective",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=0.9,
                verification_method="Manual review logs",
                owner="engineering_team"
            ),
            Control(
                control_id="R0-C2",
                description="Automated security scanning on all code",
                control_type="detective",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=0.7,
                verification_method="SAST/DAST reports",
                owner="security_team"
            ),
        ]

        residual_risks = [
            ResidualRisk(
                hazard_id="R0-H1",
                original_risk_score=9,
                residual_risk_score=2,
                risk_reduction=0.78,
                acceptable=True,
                justification="Code review + automated scanning provide adequate protection"
            ),
        ]

        return SafetyCase(
            use_case_id="code_assistant_r0",
            use_case_name="Code Assistant (R0)",
            risk_tier="R0",
            scope="Internal developer productivity tool for code assistance",
            in_scope=["Code suggestions", "Debugging help", "Best practices advice"],
            out_of_scope=["Production deployments", "Security-critical code", "Safety systems"],
            hazards=hazards,
            controls=controls,
            residual_risks=residual_risks,
            assurance_activities=[
                {"activity": "Monthly code quality review", "frequency": "monthly"},
                {"activity": "Quarterly security audit", "frequency": "quarterly"},
            ],
            monitoring_metrics=["code_review_pass_rate", "security_scan_findings"],
            shutdown_criteria=[
                "Security vulnerability rate > 10%",
                "Code quality degradation detected",
            ],
            shutdown_procedure="Disable R0 agent, revert to manual coding only",
            created_by="safety_team",
            approved_by="cto",
            created_at=datetime.now(),
            last_reviewed=datetime.now(),
            next_review_due=datetime.now()
        )

    def _create_oscar_safety_case(self) -> SafetyCase:
        """Safety case for R1 Oscar Chatbot"""

        hazards = [
            Hazard(
                hazard_id="R1-H1",
                description="AI provides incorrect policy information to customers",
                severity=HazardSeverity.CRITICAL,
                likelihood=HazardLikelihood.OCCASIONAL,
                category="operational"
            ),
            Hazard(
                hazard_id="R1-H2",
                description="AI fabricates citations or policy details",
                severity=HazardSeverity.MAJOR,
                likelihood=HazardLikelihood.REMOTE,
                category="technical"
            ),
            Hazard(
                hazard_id="R1-H3",
                description="AI leaks customer PII",
                severity=HazardSeverity.CATASTROPHIC,
                likelihood=HazardLikelihood.IMPROBABLE,
                category="regulatory"
            ),
        ]

        controls = [
            Control(
                control_id="R1-C1",
                description="Citations required for all policy answers",
                control_type="preventive",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=0.95,
                verification_method="Evidence validation tests",
                owner="ai_governance_team"
            ),
            Control(
                control_id="R1-C2",
                description="Citation hash verification",
                control_type="detective",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=0.99,
                verification_method="Automated hash checks",
                owner="ai_governance_team"
            ),
            Control(
                control_id="R1-C3",
                description="Pre-retrieval PII filtering",
                control_type="preventive",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=0.98,
                verification_method="Access control audit logs",
                owner="security_team"
            ),
        ]

        residual_risks = [
            ResidualRisk(
                hazard_id="R1-H1",
                original_risk_score=12,
                residual_risk_score=2,
                risk_reduction=0.83,
                acceptable=True,
                justification="Citation requirement + verification reduces risk significantly"
            ),
            ResidualRisk(
                hazard_id="R1-H3",
                original_risk_score=5,
                residual_risk_score=1,
                risk_reduction=0.80,
                acceptable=True,
                justification="Pre-retrieval filtering prevents PII exposure"
            ),
        ]

        return SafetyCase(
            use_case_id="oscar_chatbot_r1",
            use_case_name="Oscar Chatbot (R1)",
            risk_tier="R1",
            scope="Customer-facing chatbot for policy and booking inquiries",
            in_scope=["Policy questions", "Baggage rules", "Booking assistance"],
            out_of_scope=["Booking changes", "Payments", "Personal data updates"],
            hazards=hazards,
            controls=controls,
            residual_risks=residual_risks,
            assurance_activities=[
                {"activity": "Daily citation coverage check", "frequency": "daily"},
                {"activity": "Weekly hallucination detection review", "frequency": "weekly"},
                {"activity": "Monthly privacy audit", "frequency": "monthly"},
            ],
            monitoring_metrics=[
                "citation_coverage_rate",
                "hallucination_rate",
                "privacy_violation_count"
            ],
            shutdown_criteria=[
                "Citation coverage < 90%",
                "Hallucination rate > 5%",
                "Any PII leak detected",
            ],
            shutdown_procedure="Immediately escalate all queries to human agents",
            created_by="safety_team",
            approved_by="customer_service_director",
            created_at=datetime.now(),
            last_reviewed=datetime.now(),
            next_review_due=datetime.now()
        )

    def _create_disruption_mgmt_safety_case(self) -> SafetyCase:
        """Safety case for R2 Disruption Management"""

        hazards = [
            Hazard(
                hazard_id="R2-H1",
                description="AI recommends unsafe aircraft swap",
                severity=HazardSeverity.CATASTROPHIC,
                likelihood=HazardLikelihood.REMOTE,
                category="safety"
            ),
            Hazard(
                hazard_id="R2-H2",
                description="AI ignores crew duty time limitations",
                severity=HazardSeverity.CRITICAL,
                likelihood=HazardLikelihood.OCCASIONAL,
                category="regulatory"
            ),
            Hazard(
                hazard_id="R2-H3",
                description="AI provides incomplete disruption analysis",
                severity=HazardSeverity.MAJOR,
                likelihood=HazardLikelihood.PROBABLE,
                category="operational"
            ),
        ]

        controls = [
            Control(
                control_id="R2-C1",
                description="Human approval mandatory for all recommendations",
                control_type="preventive",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=0.99,
                verification_method="Approval audit trail",
                owner="occ_manager"
            ),
            Control(
                control_id="R2-C2",
                description="Read-only tool access (no automated actions)",
                control_type="preventive",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=1.0,
                verification_method="Tool gateway logs",
                owner="ai_governance_team"
            ),
            Control(
                control_id="R2-C3",
                description="Constraint validation (crew, maintenance, regulatory)",
                control_type="preventive",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=0.95,
                verification_method="Validation test suite",
                owner="operations_team"
            ),
        ]

        residual_risks = [
            ResidualRisk(
                hazard_id="R2-H1",
                original_risk_score=10,
                residual_risk_score=1,
                risk_reduction=0.90,
                acceptable=True,
                justification="Human-in-the-loop prevents unsafe recommendations"
            ),
        ]

        return SafetyCase(
            use_case_id="disruption_mgmt_r2",
            use_case_name="Disruption Management (R2)",
            risk_tier="R2",
            scope="Decision support for OCC during flight disruptions",
            in_scope=["Recovery options", "Aircraft swaps", "Crew reassignment"],
            out_of_scope=["Automated execution", "Safety-critical decisions"],
            hazards=hazards,
            controls=controls,
            residual_risks=residual_risks,
            assurance_activities=[
                {"activity": "Post-event review of all disruptions", "frequency": "per_event"},
                {"activity": "Monthly OCC feedback review", "frequency": "monthly"},
            ],
            monitoring_metrics=[
                "human_approval_rate",
                "recommendation_accuracy",
                "constraint_violation_count"
            ],
            shutdown_criteria=[
                "Constraint violation detected",
                "OCC feedback score < 7/10",
                "Recommendation error rate > 10%",
            ],
            shutdown_procedure="Disable AI recommendations, use manual procedures only",
            created_by="safety_team",
            approved_by="head_of_operations",
            created_at=datetime.now(),
            last_reviewed=datetime.now(),
            next_review_due=datetime.now()
        )

    def _create_maintenance_auto_safety_case(self) -> SafetyCase:
        """Safety case for R3 Maintenance Automation"""

        hazards = [
            Hazard(
                hazard_id="R3-H1",
                description="AI creates incorrect work order (wrong aircraft/task)",
                severity=HazardSeverity.CRITICAL,
                likelihood=HazardLikelihood.OCCASIONAL,
                category="operational"
            ),
            Hazard(
                hazard_id="R3-H2",
                description="AI work order cannot be rolled back causing data issues",
                severity=HazardSeverity.MAJOR,
                likelihood=HazardLikelihood.REMOTE,
                category="technical"
            ),
        ]

        controls = [
            Control(
                control_id="R3-C1",
                description="Dual control approval required",
                control_type="preventive",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=0.98,
                verification_method="Dual approval audit logs",
                owner="maintenance_manager"
            ),
            Control(
                control_id="R3-C2",
                description="Rollback capability for all actions",
                control_type="corrective",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=0.99,
                verification_method="Rollback test suite",
                owner="ai_governance_team"
            ),
            Control(
                control_id="R3-C3",
                description="Parameter validation before action",
                control_type="preventive",
                status=ControlStatus.IMPLEMENTED,
                effectiveness=0.95,
                verification_method="Validation test results",
                owner="engineering_team"
            ),
        ]

        residual_risks = [
            ResidualRisk(
                hazard_id="R3-H1",
                original_risk_score=12,
                residual_risk_score=2,
                risk_reduction=0.83,
                acceptable=True,
                justification="Dual approval + parameter validation prevents errors"
            ),
        ]

        return SafetyCase(
            use_case_id="maintenance_auto_r3",
            use_case_name="Maintenance Automation (R3)",
            risk_tier="R3",
            scope="Automated creation of routine maintenance work orders",
            in_scope=["Preventive maintenance", "Scheduled inspections"],
            out_of_scope=["Corrective maintenance", "AOG situations", "Safety-critical items"],
            hazards=hazards,
            controls=controls,
            residual_risks=residual_risks,
            assurance_activities=[
                {"activity": "Daily review of automated work orders", "frequency": "daily"},
                {"activity": "Monthly rollback test", "frequency": "monthly"},
            ],
            monitoring_metrics=[
                "dual_approval_rate",
                "work_order_accuracy",
                "rollback_success_rate"
            ],
            shutdown_criteria=[
                "Work order error rate > 5%",
                "Rollback failure detected",
                "Dual approval bypass attempt",
            ],
            shutdown_procedure="Disable automated work order creation, revert to manual process",
            created_by="safety_team",
            approved_by="director_of_engineering",
            created_at=datetime.now(),
            last_reviewed=datetime.now(),
            next_review_due=datetime.now()
        )

    def register_safety_case(self, safety_case: SafetyCase):
        """Register a safety case"""
        self.safety_cases[safety_case.use_case_id] = safety_case

    def get_safety_case(self, use_case_id: str) -> Optional[SafetyCase]:
        """Get safety case by ID"""
        return self.safety_cases.get(use_case_id)

    def get_all_safety_cases(self) -> List[SafetyCase]:
        """Get all safety cases"""
        return list(self.safety_cases.values())

    def generate_safety_report(self) -> Dict:
        """Generate overall safety report"""
        cases = self.get_all_safety_cases()

        return {
            "total_use_cases": len(cases),
            "by_risk_tier": {
                "R0": len([c for c in cases if c.risk_tier == "R0"]),
                "R1": len([c for c in cases if c.risk_tier == "R1"]),
                "R2": len([c for c in cases if c.risk_tier == "R2"]),
                "R3": len([c for c in cases if c.risk_tier == "R3"]),
            },
            "all_acceptable": all(c.is_acceptable() for c in cases),
            "cases_requiring_review": [
                c.use_case_id for c in cases
                if c.next_review_due < datetime.now()
            ],
            "high_risk_cases": [
                c.use_case_id for c in cases
                if c.calculate_overall_risk().get("maximum_risk", 0) >= 15
            ],
            "control_coverage": {
                c.use_case_id: c.get_control_coverage()
                for c in cases
            },
            "generated_at": datetime.now().isoformat()
        }
