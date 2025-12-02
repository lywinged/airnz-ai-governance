"""
G11: Reliability Engineering - Circuit Breakers, Graceful Degradation, Kill Switches

Implements:
- Circuit breakers for failing components
- Graceful degradation strategies
- Emergency kill switches
- Health checks
- Failover mechanisms
"""

from enum import Enum
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker state"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing recovery


class ComponentHealth(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    DOWN = "down"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int  # Number of failures before opening
    timeout_seconds: int    # How long to wait before half-open
    success_threshold: int  # Successes needed to close from half-open


@dataclass
class CircuitBreaker:
    """Circuit breaker for a component"""
    component_id: str
    config: CircuitBreakerConfig
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime]
    opened_at: Optional[datetime]

    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._close()

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._open()

        elif self.state == CircuitState.HALF_OPEN:
            self._open()

    def can_attempt(self) -> bool:
        """Check if request can be attempted"""
        if self.state == CircuitState.CLOSED:
            return True

        elif self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.opened_at:
                elapsed = (datetime.now() - self.opened_at).total_seconds()
                if elapsed >= self.config.timeout_seconds:
                    self._half_open()
                    return True
            return False

        elif self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def _open(self):
        """Open circuit (block requests)"""
        self.state = CircuitState.OPEN
        self.opened_at = datetime.now()
        logger.error(f"Circuit breaker OPENED for {self.component_id}")

    def _close(self):
        """Close circuit (allow requests)"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None
        logger.info(f"Circuit breaker CLOSED for {self.component_id}")

    def _half_open(self):
        """Half-open circuit (test recovery)"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        logger.info(f"Circuit breaker HALF-OPEN for {self.component_id}")


class DegradationMode(Enum):
    """Graceful degradation modes"""
    FULL_OPERATION = "full_operation"
    CACHE_ONLY = "cache_only"
    READONLY = "readonly"
    ESSENTIAL_ONLY = "essential_only"
    EMERGENCY = "emergency"


@dataclass
class DegradationStrategy:
    """Degradation strategy for a component"""
    component_id: str
    current_mode: DegradationMode
    fallback_modes: Dict[str, Callable]  # Mode -> fallback function
    degradation_reason: Optional[str]
    degraded_at: Optional[datetime]


class ReliabilityEngineer:
    """
    Reliability engineering for AI governance platform.

    Implements G11 requirements:
    - Circuit breakers
    - Graceful degradation
    - Kill switches
    - Health monitoring
    """

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.degradation_strategies: Dict[str, DegradationStrategy] = {}
        self.kill_switches: Dict[str, bool] = {}
        self.component_health: Dict[str, ComponentHealth] = {}

        self._initialize_circuit_breakers()
        self._initialize_degradation_strategies()
        self._initialize_kill_switches()

    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for components"""

        # LLM Service circuit breaker
        self.circuit_breakers["llm_service"] = CircuitBreaker(
            component_id="llm_service",
            config=CircuitBreakerConfig(
                failure_threshold=3,
                timeout_seconds=60,
                success_threshold=2
            ),
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            last_failure_time=None,
            opened_at=None
        )

        # Database circuit breaker
        self.circuit_breakers["database"] = CircuitBreaker(
            component_id="database",
            config=CircuitBreakerConfig(
                failure_threshold=5,
                timeout_seconds=30,
                success_threshold=3
            ),
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            last_failure_time=None,
            opened_at=None
        )

        # Tool Gateway circuit breaker
        self.circuit_breakers["tool_gateway"] = CircuitBreaker(
            component_id="tool_gateway",
            config=CircuitBreakerConfig(
                failure_threshold=5,
                timeout_seconds=45,
                success_threshold=2
            ),
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            last_failure_time=None,
            opened_at=None
        )

    def _initialize_degradation_strategies(self):
        """Initialize graceful degradation strategies"""

        # LLM Service degradation
        self.degradation_strategies["llm_service"] = DegradationStrategy(
            component_id="llm_service",
            current_mode=DegradationMode.FULL_OPERATION,
            fallback_modes={
                "cache_only": lambda: "Use cached responses",
                "readonly": lambda: "Provide pre-written templates",
                "emergency": lambda: "Escalate to human immediately"
            },
            degradation_reason=None,
            degraded_at=None
        )

        # Database degradation
        self.degradation_strategies["database"] = DegradationStrategy(
            component_id="database",
            current_mode=DegradationMode.FULL_OPERATION,
            fallback_modes={
                "readonly": lambda: "Read-only mode, no writes",
                "cache_only": lambda: "Use in-memory cache only",
                "emergency": lambda: "System unavailable"
            },
            degradation_reason=None,
            degraded_at=None
        )

        # Retrieval degradation
        self.degradation_strategies["retrieval"] = DegradationStrategy(
            component_id="retrieval",
            current_mode=DegradationMode.FULL_OPERATION,
            fallback_modes={
                "cache_only": lambda: "Use cached policy documents",
                "readonly": lambda: "Static policy responses only",
                "emergency": lambda: "No AI retrieval, human only"
            },
            degradation_reason=None,
            degraded_at=None
        )

    def _initialize_kill_switches(self):
        """Initialize kill switches for all risk tiers"""
        self.kill_switches = {
            "R0": False,  # Code Assistant
            "R1": False,  # Oscar Chatbot
            "R2": False,  # Disruption Management
            "R3": False,  # Maintenance Automation
            "ALL": False  # Master kill switch
        }

    def check_circuit_breaker(self, component_id: str) -> bool:
        """
        Check if component circuit breaker allows request.

        Args:
            component_id: Component to check

        Returns:
            True if request allowed
        """
        breaker = self.circuit_breakers.get(component_id)
        if not breaker:
            return True  # No breaker = allow

        return breaker.can_attempt()

    def record_operation(self, component_id: str, success: bool):
        """
        Record operation result for circuit breaker.

        Args:
            component_id: Component that performed operation
            success: Whether operation succeeded
        """
        breaker = self.circuit_breakers.get(component_id)
        if not breaker:
            return

        if success:
            breaker.record_success()
        else:
            breaker.record_failure()

            # Check if we should degrade
            if breaker.state == CircuitState.OPEN:
                self._trigger_degradation(component_id, "Circuit breaker opened")

    def _trigger_degradation(self, component_id: str, reason: str):
        """
        Trigger graceful degradation for component.

        Args:
            component_id: Component to degrade
            reason: Reason for degradation
        """
        strategy = self.degradation_strategies.get(component_id)
        if not strategy:
            return

        logger.warning(f"Triggering degradation for {component_id}: {reason}")

        # Move to cache-only mode first
        if strategy.current_mode == DegradationMode.FULL_OPERATION:
            strategy.current_mode = DegradationMode.CACHE_ONLY
            strategy.degradation_reason = reason
            strategy.degraded_at = datetime.now()
            logger.info(f"{component_id} degraded to CACHE_ONLY")

        # If still failing, move to readonly
        elif strategy.current_mode == DegradationMode.CACHE_ONLY:
            strategy.current_mode = DegradationMode.READONLY
            logger.warning(f"{component_id} degraded to READONLY")

        # If still failing, emergency mode
        elif strategy.current_mode == DegradationMode.READONLY:
            strategy.current_mode = DegradationMode.EMERGENCY
            logger.error(f"{component_id} degraded to EMERGENCY")

    def restore_full_operation(self, component_id: str):
        """
        Restore component to full operation.

        Args:
            component_id: Component to restore
        """
        strategy = self.degradation_strategies.get(component_id)
        if not strategy:
            return

        strategy.current_mode = DegradationMode.FULL_OPERATION
        strategy.degradation_reason = None
        strategy.degraded_at = None

        logger.info(f"{component_id} restored to FULL_OPERATION")

    def activate_kill_switch(self, risk_tier: str, reason: str):
        """
        Activate kill switch for risk tier.

        Args:
            risk_tier: Risk tier to disable (R0, R1, R2, R3, or ALL)
            reason: Reason for activation
        """
        if risk_tier not in self.kill_switches:
            logger.error(f"Unknown risk tier: {risk_tier}")
            return

        self.kill_switches[risk_tier] = True

        logger.critical(
            f"KILL SWITCH ACTIVATED: {risk_tier} | Reason: {reason}"
        )

        # If ALL, disable everything
        if risk_tier == "ALL":
            for tier in self.kill_switches:
                self.kill_switches[tier] = True

    def deactivate_kill_switch(self, risk_tier: str):
        """
        Deactivate kill switch (careful!)

        Args:
            risk_tier: Risk tier to re-enable
        """
        if risk_tier not in self.kill_switches:
            logger.error(f"Unknown risk tier: {risk_tier}")
            return

        self.kill_switches[risk_tier] = False

        logger.warning(f"Kill switch DEACTIVATED: {risk_tier}")

    def is_operational(self, risk_tier: str) -> bool:
        """
        Check if risk tier is operational.

        Args:
            risk_tier: Risk tier to check

        Returns:
            True if operational
        """
        # Check master kill switch
        if self.kill_switches.get("ALL"):
            return False

        # Check tier-specific kill switch
        return not self.kill_switches.get(risk_tier, False)

    def health_check(self) -> Dict:
        """
        Comprehensive health check.

        Returns:
            Health status report
        """
        circuit_status = {
            component_id: {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "healthy": breaker.state == CircuitState.CLOSED,
                "threshold": breaker.config.failure_threshold
            }
            for component_id, breaker in self.circuit_breakers.items()
        }

        degradation_status = {
            component_id: {
                "mode": strategy.current_mode.value,
                "reason": strategy.degradation_reason,
                "degraded": strategy.current_mode != DegradationMode.FULL_OPERATION
            }
            for component_id, strategy in self.degradation_strategies.items()
        }

        kill_switch_status = {
            tier: {"active": active, "operational": not active}
            for tier, active in self.kill_switches.items()
        }

        overall_health = "healthy"
        if any(status["active"] for status in kill_switch_status.values()):
            overall_health = "killed"
        elif any(status["degraded"] for status in degradation_status.values()):
            overall_health = "degraded"
        elif any(not status["healthy"] for status in circuit_status.values()):
            overall_health = "unstable"

        return {
            "overall_health": overall_health,
            "circuit_breakers": circuit_status,
            "degradation": degradation_status,
            "kill_switches": kill_switch_status,
            "timestamp": datetime.now().isoformat()
        }
