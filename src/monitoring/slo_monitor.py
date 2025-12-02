"""
SLO Monitor: Service Level Objectives

Defines and monitors SLOs for AI governance platform:
- Availability
- Latency (p50, p95, p99)
- Error rates
- Citation coverage
- Tool success rates
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import statistics
import logging

logger = logging.getLogger(__name__)


class SLOStatus(Enum):
    """SLO compliance status"""
    HEALTHY = "healthy"           # Meeting SLO
    AT_RISK = "at_risk"          # Close to violation
    VIOLATED = "violated"         # SLO violated
    NO_DATA = "no_data"          # Insufficient data


@dataclass
class SLODefinition:
    """Service Level Objective definition"""
    slo_id: str
    name: str
    description: str
    target_value: float
    measurement_window_minutes: int
    risk_tier: Optional[str] = None  # None = all tiers
    unit: str = "percent"


@dataclass
class SLOMeasurement:
    """SLO measurement at a point in time"""
    slo_id: str
    timestamp: datetime
    actual_value: float
    target_value: float
    status: SLOStatus
    sample_size: int
    details: Dict


class SLOMonitor:
    """
    Monitor and report on SLOs.

    Key SLOs:
    1. Availability: 99.9% uptime
    2. Latency: p95 < 2s for R0/R1, < 5s for R2
    3. Error Rate: < 0.1%
    4. Citation Coverage: > 95% for R1-R3
    5. Tool Success Rate: > 99%
    6. Security: 0 privilege escalations
    """

    def __init__(self):
        self.slo_definitions = self._define_slos()
        self.measurements: List[SLOMeasurement] = []

    def _define_slos(self) -> Dict[str, SLODefinition]:
        """Define all SLOs"""
        return {
            # Availability SLO
            "availability": SLODefinition(
                slo_id="availability",
                name="System Availability",
                description="Percentage of successful requests (non-5xx errors)",
                target_value=99.9,
                measurement_window_minutes=60,
                unit="percent"
            ),

            # Latency SLOs (by risk tier)
            "latency_r0_p95": SLODefinition(
                slo_id="latency_r0_p95",
                name="R0 Latency (p95)",
                description="95th percentile latency for R0 (internal productivity) requests",
                target_value=2000,  # 2 seconds in ms
                measurement_window_minutes=15,
                risk_tier="R0",
                unit="milliseconds"
            ),

            "latency_r1_p95": SLODefinition(
                slo_id="latency_r1_p95",
                name="R1 Latency (p95)",
                description="95th percentile latency for R1 (customer-facing) requests",
                target_value=2000,  # 2 seconds
                measurement_window_minutes=15,
                risk_tier="R1",
                unit="milliseconds"
            ),

            "latency_r2_p95": SLODefinition(
                slo_id="latency_r2_p95",
                name="R2 Latency (p95)",
                description="95th percentile latency for R2 (ops decision support) requests",
                target_value=5000,  # 5 seconds (more complex queries)
                measurement_window_minutes=15,
                risk_tier="R2",
                unit="milliseconds"
            ),

            # Error Rate SLO
            "error_rate": SLODefinition(
                slo_id="error_rate",
                name="Error Rate",
                description="Percentage of requests resulting in errors",
                target_value=0.1,  # < 0.1%
                measurement_window_minutes=60,
                unit="percent"
            ),

            # Quality SLOs
            "citation_coverage_r1": SLODefinition(
                slo_id="citation_coverage_r1",
                name="R1 Citation Coverage",
                description="Percentage of R1 responses with valid citations",
                target_value=95.0,  # > 95%
                measurement_window_minutes=60,
                risk_tier="R1",
                unit="percent"
            ),

            "citation_coverage_r2": SLODefinition(
                slo_id="citation_coverage_r2",
                name="R2 Citation Coverage",
                description="Percentage of R2 responses with valid citations",
                target_value=98.0,  # > 98% (higher standard for ops)
                measurement_window_minutes=60,
                risk_tier="R2",
                unit="percent"
            ),

            "hallucination_rate": SLODefinition(
                slo_id="hallucination_rate",
                name="Hallucination Rate",
                description="Percentage of responses containing fabricated information",
                target_value=1.0,  # < 1%
                measurement_window_minutes=60,
                unit="percent"
            ),

            # Tool Success SLO
            "tool_success_rate": SLODefinition(
                slo_id="tool_success_rate",
                name="Tool Success Rate",
                description="Percentage of tool invocations that succeed",
                target_value=99.0,  # > 99%
                measurement_window_minutes=30,
                unit="percent"
            ),

            # Security SLOs
            "privilege_escalation_rate": SLODefinition(
                slo_id="privilege_escalation_rate",
                name="Privilege Escalation Rate",
                description="Number of successful privilege escalation attempts (must be 0)",
                target_value=0.0,  # Zero tolerance
                measurement_window_minutes=60,
                unit="count"
            ),

            "access_control_deny_rate": SLODefinition(
                slo_id="access_control_deny_rate",
                name="Access Control Deny Rate",
                description="Percentage of requests denied by access control (tracking effectiveness)",
                target_value=5.0,  # Expected ~5% denials (normal security filtering)
                measurement_window_minutes=60,
                unit="percent"
            ),

            # Cost SLO
            "cost_per_request": SLODefinition(
                slo_id="cost_per_request",
                name="Cost Per Request",
                description="Average cost per AI request in USD",
                target_value=0.05,  # < $0.05 per request
                measurement_window_minutes=60,
                unit="usd"
            ),
        }

    def measure_slo(
        self,
        slo_id: str,
        data_points: List[Dict],
        timestamp: Optional[datetime] = None
    ) -> SLOMeasurement:
        """
        Measure SLO compliance.

        Args:
            slo_id: SLO to measure
            data_points: Data points from the measurement window
            timestamp: Measurement timestamp (defaults to now)

        Returns:
            SLOMeasurement
        """
        slo_def = self.slo_definitions.get(slo_id)
        if not slo_def:
            raise ValueError(f"Unknown SLO: {slo_id}")

        timestamp = timestamp or datetime.now()

        if not data_points:
            return SLOMeasurement(
                slo_id=slo_id,
                timestamp=timestamp,
                actual_value=0.0,
                target_value=slo_def.target_value,
                status=SLOStatus.NO_DATA,
                sample_size=0,
                details={"error": "No data points available"}
            )

        # Calculate actual value based on SLO type
        if "availability" in slo_id:
            actual_value = self._calculate_availability(data_points)

        elif "latency" in slo_id:
            actual_value = self._calculate_latency_p95(data_points)

        elif "error_rate" in slo_id:
            actual_value = self._calculate_error_rate(data_points)

        elif "citation_coverage" in slo_id:
            actual_value = self._calculate_citation_coverage(data_points)

        elif "hallucination" in slo_id:
            actual_value = self._calculate_hallucination_rate(data_points)

        elif "tool_success" in slo_id:
            actual_value = self._calculate_tool_success_rate(data_points)

        elif "privilege_escalation" in slo_id:
            actual_value = self._calculate_privilege_escalations(data_points)

        elif "access_control_deny" in slo_id:
            actual_value = self._calculate_deny_rate(data_points)

        elif "cost_per_request" in slo_id:
            actual_value = self._calculate_average_cost(data_points)

        else:
            actual_value = 0.0

        # Determine status
        status = self._determine_status(slo_id, actual_value, slo_def.target_value)

        measurement = SLOMeasurement(
            slo_id=slo_id,
            timestamp=timestamp,
            actual_value=actual_value,
            target_value=slo_def.target_value,
            status=status,
            sample_size=len(data_points),
            details={
                "measurement_window_minutes": slo_def.measurement_window_minutes,
                "risk_tier": slo_def.risk_tier
            }
        )

        self.measurements.append(measurement)

        # Log if SLO violated
        if status == SLOStatus.VIOLATED:
            logger.error(
                f"SLO VIOLATED: {slo_def.name} | "
                f"Actual: {actual_value:.2f} {slo_def.unit} | "
                f"Target: {slo_def.target_value:.2f} {slo_def.unit}"
            )
        elif status == SLOStatus.AT_RISK:
            logger.warning(
                f"SLO AT RISK: {slo_def.name} | "
                f"Actual: {actual_value:.2f} {slo_def.unit} | "
                f"Target: {slo_def.target_value:.2f} {slo_def.unit}"
            )

        return measurement

    def _determine_status(self, slo_id: str, actual: float, target: float) -> SLOStatus:
        """Determine SLO status"""

        # For metrics where lower is better (latency, error rate, etc.)
        lower_is_better = [
            "latency", "error_rate", "hallucination",
            "privilege_escalation", "cost_per_request"
        ]

        # For metrics where higher is better (availability, coverage, etc.)
        higher_is_better = [
            "availability", "citation_coverage", "tool_success"
        ]

        is_lower_better = any(metric in slo_id for metric in lower_is_better)
        is_higher_better = any(metric in slo_id for metric in higher_is_better)

        if is_lower_better:
            if actual <= target:
                return SLOStatus.HEALTHY
            elif actual <= target * 1.1:  # Within 10% of target
                return SLOStatus.AT_RISK
            else:
                return SLOStatus.VIOLATED

        elif is_higher_better:
            if actual >= target:
                return SLOStatus.HEALTHY
            elif actual >= target * 0.95:  # Within 5% of target
                return SLOStatus.AT_RISK
            else:
                return SLOStatus.VIOLATED

        # Special case: access control deny rate (target is expected value)
        if "access_control_deny" in slo_id:
            if abs(actual - target) < 2:  # Within 2%
                return SLOStatus.HEALTHY
            elif abs(actual - target) < 5:  # Within 5%
                return SLOStatus.AT_RISK
            else:
                return SLOStatus.VIOLATED

        return SLOStatus.NO_DATA

    # Calculation methods

    def _calculate_availability(self, data_points: List[Dict]) -> float:
        """Calculate availability percentage"""
        total = len(data_points)
        successful = len([dp for dp in data_points if dp.get('status') not in ['error', 'failed']])
        return (successful / total) * 100 if total > 0 else 0.0

    def _calculate_latency_p95(self, data_points: List[Dict]) -> float:
        """Calculate 95th percentile latency"""
        latencies = [dp.get('latency_ms', 0) for dp in data_points]
        if not latencies:
            return 0.0
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        return latencies[p95_index] if p95_index < len(latencies) else latencies[-1]

    def _calculate_error_rate(self, data_points: List[Dict]) -> float:
        """Calculate error rate percentage"""
        total = len(data_points)
        errors = len([dp for dp in data_points if dp.get('status') in ['error', 'failed']])
        return (errors / total) * 100 if total > 0 else 0.0

    def _calculate_citation_coverage(self, data_points: List[Dict]) -> float:
        """Calculate citation coverage percentage"""
        total = len(data_points)
        with_citations = len([dp for dp in data_points if dp.get('has_citations', False)])
        return (with_citations / total) * 100 if total > 0 else 0.0

    def _calculate_hallucination_rate(self, data_points: List[Dict]) -> float:
        """Calculate hallucination rate (requires manual review/eval)"""
        total = len(data_points)
        hallucinations = len([dp for dp in data_points if dp.get('hallucination_detected', False)])
        return (hallucinations / total) * 100 if total > 0 else 0.0

    def _calculate_tool_success_rate(self, data_points: List[Dict]) -> float:
        """Calculate tool success rate"""
        total = len(data_points)
        successful = len([dp for dp in data_points if dp.get('tool_status') == 'success'])
        return (successful / total) * 100 if total > 0 else 0.0

    def _calculate_privilege_escalations(self, data_points: List[Dict]) -> float:
        """Count privilege escalation attempts"""
        return len([dp for dp in data_points if dp.get('privilege_escalation', False)])

    def _calculate_deny_rate(self, data_points: List[Dict]) -> float:
        """Calculate access control deny rate"""
        total = len(data_points)
        denied = len([dp for dp in data_points if dp.get('access_denied', False)])
        return (denied / total) * 100 if total > 0 else 0.0

    def _calculate_average_cost(self, data_points: List[Dict]) -> float:
        """Calculate average cost per request"""
        costs = [dp.get('cost_usd', 0) for dp in data_points]
        return statistics.mean(costs) if costs else 0.0

    def get_slo_report(self, hours: int = 24) -> Dict:
        """
        Generate SLO compliance report.

        Args:
            hours: Hours of history to include

        Returns:
            SLO report dictionary
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_measurements = [
            m for m in self.measurements
            if m.timestamp >= cutoff
        ]

        if not recent_measurements:
            return {
                "period_hours": hours,
                "overall_status": "no_data",
                "slos": {},
                "message": "No measurements available",
                "generated_at": datetime.now().isoformat()
            }

        # Group by SLO
        slo_status = {}
        for slo_id, slo_def in self.slo_definitions.items():
            slo_measurements = [m for m in recent_measurements if m.slo_id == slo_id]

            if not slo_measurements:
                slo_status[slo_id] = {
                    "name": slo_def.name,
                    "status": "no_data",
                    "target": slo_def.target_value,
                    "unit": slo_def.unit
                }
                continue

            # Get latest measurement
            latest = max(slo_measurements, key=lambda m: m.timestamp)

            # Count violations
            violations = len([m for m in slo_measurements if m.status == SLOStatus.VIOLATED])

            slo_status[slo_id] = {
                "name": slo_def.name,
                "status": latest.status.value,
                "current_value": latest.actual_value,
                "target": latest.target_value,
                "unit": slo_def.unit,
                "violations_count": violations,
                "measurements_count": len(slo_measurements),
                "last_measured": latest.timestamp.isoformat()
            }

        # Overall status
        any_violated = any(s['status'] == 'violated' for s in slo_status.values())
        any_at_risk = any(s['status'] == 'at_risk' for s in slo_status.values())

        overall_status = "violated" if any_violated else ("at_risk" if any_at_risk else "healthy")

        return {
            "period_hours": hours,
            "overall_status": overall_status,
            "slos": slo_status,
            "generated_at": datetime.now().isoformat()
        }
