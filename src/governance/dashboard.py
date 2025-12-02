"""
G12: Governance Dashboard - Governance as a Product

Operational governance dashboard:
- Policy-as-Code visualization
- Audit dashboards
- Approval workflows
- Evidence quality reports
- Data source health monitoring
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from src.core.policy_engine import RiskTier


@dataclass
class PolicyStatus:
    """Policy version status"""
    policy_id: str
    version: str
    risk_tier: str
    active: bool
    approved_by: str
    effective_date: datetime
    last_modified: datetime
    changes_from_previous: List[str]


@dataclass
class ApprovalWorkflow:
    """Approval workflow status"""
    workflow_id: str
    request_type: str  # policy_change, model_update, prompt_update
    requested_by: str
    requested_at: datetime
    required_approvals: int
    current_approvals: int
    approvers: List[Dict]
    status: str  # pending, approved, denied
    decision_deadline: datetime


class GovernanceDashboard:
    """
    G12: Governance Dashboard

    Makes governance operational:
    - Real-time visibility
    - Policy-as-Code tracking
    - Approval workflow management
    - Evidence quality monitoring
    - Data source health checks
    """

    def __init__(
        self,
        policy_engine,
        audit_system,
        evidence_enforcer,
        tool_gateway,
        safety_case_registry,
        evaluation_system,
        reliability_engineer,
        slo_monitor
    ):
        self.policy_engine = policy_engine
        self.audit_system = audit_system
        self.evidence_enforcer = evidence_enforcer
        self.tool_gateway = tool_gateway
        self.safety_case_registry = safety_case_registry
        self.evaluation_system = evaluation_system
        self.reliability_engineer = reliability_engineer
        self.slo_monitor = slo_monitor

        self.approval_workflows: List[ApprovalWorkflow] = []

    def get_governance_overview(self) -> Dict:
        """
        Get complete governance overview.

        Returns:
            Comprehensive governance status
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "policy_status": self._get_policy_status(),
            "safety_cases": self._get_safety_status(),
            "slo_compliance": self._get_slo_compliance(),
            "audit_metrics": self._get_audit_metrics(),
            "evidence_quality": self._get_evidence_quality(),
            "tool_health": self._get_tool_health(),
            "evaluation_status": self._get_evaluation_status(),
            "reliability": self._get_reliability_status(),
            "approval_workflows": self._get_approval_workflows(),
            "governance_score": self._calculate_governance_score()
        }

    def _get_policy_status(self) -> Dict:
        """Get policy-as-code status"""
        return {
            "R0": {
                "version": self.policy_engine.active_policies[RiskTier.R0].version,
                "effective_date": self.policy_engine.active_policies[RiskTier.R0].effective_date.isoformat(),
                "approved_by": self.policy_engine.active_policies[RiskTier.R0].approved_by
            },
            "R1": {
                "version": self.policy_engine.active_policies[RiskTier.R1].version,
                "effective_date": self.policy_engine.active_policies[RiskTier.R1].effective_date.isoformat(),
                "approved_by": self.policy_engine.active_policies[RiskTier.R1].approved_by
            },
            "R2": {
                "version": self.policy_engine.active_policies[RiskTier.R2].version,
                "effective_date": self.policy_engine.active_policies[RiskTier.R2].effective_date.isoformat(),
                "approved_by": self.policy_engine.active_policies[RiskTier.R2].approved_by
            },
            "R3": {
                "version": self.policy_engine.active_policies[RiskTier.R3].version,
                "effective_date": self.policy_engine.active_policies[RiskTier.R3].effective_date.isoformat(),
                "approved_by": self.policy_engine.active_policies[RiskTier.R3].approved_by
            }
        }

    def _get_safety_status(self) -> Dict:
        """Get AI safety case status"""
        report = self.safety_case_registry.generate_safety_report()
        return {
            "total_cases": report["total_use_cases"],
            "all_acceptable": report["all_acceptable"],
            "high_risk_cases": report.get("high_risk_cases", []),
            "cases_requiring_review": report.get("cases_requiring_review", [])
        }

    def _get_slo_compliance(self) -> Dict:
        """Get SLO compliance status"""
        report = self.slo_monitor.get_slo_report(hours=24)
        return {
            "overall_status": report["overall_status"],
            "slo_count": len(report.get("slos", {})),
            "violations": [
                slo_id for slo_id, slo in report.get("slos", {}).items()
                if slo.get("status") == "violated"
            ]
        }

    def _get_audit_metrics(self) -> Dict:
        """Get audit trail metrics"""
        return {
            "total_traces": len(self.audit_system.traces),
            "total_events": len(self.audit_system.events),
            "traces_by_tier": {
                tier: len([
                    t for t in self.audit_system.traces.values()
                    if t.risk_tier == tier
                ])
                for tier in ["R0", "R1", "R2", "R3"]
            },
            "traces_by_status": {
                status: len([
                    t for t in self.audit_system.traces.values()
                    if t.status == status
                ])
                for status in ["completed", "failed", "denied"]
            }
        }

    def _get_evidence_quality(self) -> Dict:
        """Get evidence quality metrics"""
        return {
            "total_citations": len(self.evidence_enforcer.citation_cache),
            "verification_failures": len(self.evidence_enforcer.verification_failures),
            "cache_hit_rate": 0.85,  # Simulated
            "average_citation_age_days": 30  # Simulated
        }

    def _get_tool_health(self) -> Dict:
        """Get tool gateway health"""
        metrics = self.tool_gateway.get_tool_metrics()
        return {
            "total_tools": len(self.tool_gateway.registered_tools),
            "total_invocations": metrics["total_invocations"],
            "success_rate": metrics["success_rate"],
            "failed_invocations": metrics["failed"],
            "rate_limited": metrics["rate_limited"]
        }

    def _get_evaluation_status(self) -> Dict:
        """Get evaluation system status"""
        report = self.evaluation_system.generate_evaluation_report()
        return {
            "total_runs": report["total_runs"],
            "latest_golden_pass_rate": report.get("latest_golden_set", {}).get("pass_rate", 0) if report.get("latest_golden_set") else 0,
            "latest_regression_pass_rate": report.get("latest_regression", {}).get("pass_rate", 0) if report.get("latest_regression") else 0,
            "latest_redteam_pass_rate": report.get("latest_red_team", {}).get("pass_rate", 0) if report.get("latest_red_team") else 0,
            "overall_health": report.get("overall_health", "unknown")
        }

    def _get_reliability_status(self) -> Dict:
        """Get reliability engineering status"""
        health = self.reliability_engineer.health_check()
        return {
            "overall_health": health["overall_health"],
            "circuit_breakers_open": sum(
                1 for cb in health["circuit_breakers"].values()
                if not cb["healthy"]
            ),
            "components_degraded": sum(
                1 for deg in health["degradation"].values()
                if deg["degraded"]
            ),
            "kill_switches_active": sum(
                1 for ks in health["kill_switches"].values()
                if ks["active"]
            )
        }

    def _get_approval_workflows(self) -> Dict:
        """Get approval workflow status"""
        pending = [w for w in self.approval_workflows if w.status == "pending"]
        approved = [w for w in self.approval_workflows if w.status == "approved"]
        denied = [w for w in self.approval_workflows if w.status == "denied"]

        return {
            "total_workflows": len(self.approval_workflows),
            "pending": len(pending),
            "approved": len(approved),
            "denied": len(denied),
            "overdue": len([
                w for w in pending
                if w.decision_deadline < datetime.now()
            ])
        }

    def _calculate_governance_score(self) -> Dict:
        """
        Calculate overall governance score.

        100 = perfect governance
        0 = no governance

        Weighted components:
        - Policy compliance: 15%
        - Safety cases: 15%
        - SLO compliance: 20%
        - Evidence quality: 15%
        - Tool health: 10%
        - Evaluation health: 15%
        - Reliability: 10%
        """
        scores = {}

        # Policy compliance (15%)
        scores["policy"] = 15  # All policies active

        # Safety cases (15%)
        safety = self._get_safety_status()
        scores["safety"] = 15 if safety["all_acceptable"] else 10

        # SLO compliance (20%)
        slo = self._get_slo_compliance()
        if slo["overall_status"] == "healthy":
            scores["slo"] = 20
        elif slo["overall_status"] == "at_risk":
            scores["slo"] = 15
        else:
            scores["slo"] = 10

        # Evidence quality (15%)
        evidence = self._get_evidence_quality()
        if evidence["verification_failures"] == 0:
            scores["evidence"] = 15
        else:
            scores["evidence"] = 10

        # Tool health (10%)
        tools = self._get_tool_health()
        if tools["success_rate"] >= 0.99:
            scores["tools"] = 10
        elif tools["success_rate"] >= 0.95:
            scores["tools"] = 7
        else:
            scores["tools"] = 5

        # Evaluation health (15%)
        evaluation = self._get_evaluation_status()
        if evaluation["overall_health"] == "healthy":
            scores["evaluation"] = 15
        else:
            scores["evaluation"] = 10

        # Reliability (10%)
        reliability = self._get_reliability_status()
        if reliability["overall_health"] == "healthy":
            scores["reliability"] = 10
        elif reliability["overall_health"] == "degraded":
            scores["reliability"] = 7
        else:
            scores["reliability"] = 3

        total_score = sum(scores.values())

        return {
            "total_score": total_score,
            "max_score": 100,
            "percentage": total_score,
            "grade": self._score_to_grade(total_score),
            "breakdown": scores
        }

    def _score_to_grade(self, score: int) -> str:
        """Convert score to letter grade"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        else:
            return "D"

    def export_dashboard_json(self) -> str:
        """Export dashboard as JSON"""
        overview = self.get_governance_overview()
        return json.dumps(overview, indent=2, default=str)

    def generate_html_dashboard(self) -> str:
        """Generate simple HTML dashboard"""
        overview = self.get_governance_overview()
        score = overview["governance_score"]

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Governance Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #1a1a1a; color: white; padding: 20px; }}
        .score {{ font-size: 48px; font-weight: bold; }}
        .grade {{ font-size: 36px; color: #4CAF50; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f0f0f0; }}
        .status-healthy {{ color: green; }}
        .status-degraded {{ color: orange; }}
        .status-failed {{ color: red; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Air NZ AI Governance Dashboard</h1>
        <div class="score">Governance Score: {score['total_score']}/100</div>
        <div class="grade">Grade: {score['grade']}</div>
        <p>Generated: {overview['timestamp']}</p>
    </div>

    <div class="section">
        <h2>Policy Status</h2>
        <div class="metric">R0: v{overview['policy_status']['R0']['version']}</div>
        <div class="metric">R1: v{overview['policy_status']['R1']['version']}</div>
        <div class="metric">R2: v{overview['policy_status']['R2']['version']}</div>
        <div class="metric">R3: v{overview['policy_status']['R3']['version']}</div>
    </div>

    <div class="section">
        <h2>Safety Cases</h2>
        <div class="metric">Total: {overview['safety_cases']['total_cases']}</div>
        <div class="metric">Acceptable: {overview['safety_cases']['all_acceptable']}</div>
    </div>

    <div class="section">
        <h2>SLO Compliance</h2>
        <div class="metric status-{overview['slo_compliance']['overall_status']}">
            Status: {overview['slo_compliance']['overall_status']}
        </div>
        <div class="metric">Violations: {len(overview['slo_compliance']['violations'])}</div>
    </div>

    <div class="section">
        <h2>Reliability</h2>
        <div class="metric status-{overview['reliability']['overall_health']}">
            Health: {overview['reliability']['overall_health']}
        </div>
        <div class="metric">Circuit Breakers Open: {overview['reliability']['circuit_breakers_open']}</div>
        <div class="metric">Kill Switches Active: {overview['reliability']['kill_switches_active']}</div>
    </div>

    <div class="section">
        <h2>Audit Metrics</h2>
        <div class="metric">Total Traces: {overview['audit_metrics']['total_traces']}</div>
        <div class="metric">Total Events: {overview['audit_metrics']['total_events']}</div>
    </div>
</body>
</html>
        """

        return html
