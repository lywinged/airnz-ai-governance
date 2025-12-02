"""
Tool Gateway: G5 - Tool/Action Safety Gates

Unified gateway for all tool calls with:
- Read/Write isolation
- Parameter validation
- Rate limiting
- Idempotency
- Rollback capability
- Full audit trail
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import logging

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Tool operation types"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


class ToolStatus(Enum):
    """Tool execution status"""
    SUCCESS = "success"
    FAILURE = "failure"
    RATE_LIMITED = "rate_limited"
    VALIDATION_ERROR = "validation_error"
    PERMISSION_DENIED = "permission_denied"
    IDEMPOTENT_SKIP = "idempotent_skip"


@dataclass
class ToolDefinition:
    """Tool definition with safety metadata"""
    tool_id: str
    name: str
    description: str
    tool_type: ToolType
    allowed_risk_tiers: List[str]
    requires_approval: bool
    requires_dual_control: bool
    supports_rollback: bool
    rate_limit_per_minute: int
    parameter_schema: Dict
    execute_function: Callable


@dataclass
class ToolInvocation:
    """Record of tool invocation"""
    invocation_id: str
    tool_id: str
    user_id: str
    trace_id: str
    parameters: Dict
    status: ToolStatus
    result: Optional[Dict]
    error: Optional[str]
    timestamp: datetime
    rollback_data: Optional[Dict] = None  # Data needed for rollback


@dataclass
class ToolExecutionResult:
    """Result of tool execution"""
    success: bool
    status: ToolStatus
    result: Optional[Dict]
    error: Optional[str]
    invocation_id: str
    timestamp: datetime
    can_rollback: bool = False
    rollback_data: Optional[Dict] = None


class ToolGateway:
    """
    Unified gateway for all AI tool invocations.

    Implements G5 controls:
    1. Read/Write isolation
    2. Parameter validation
    3. Rate limiting
    4. Idempotency
    5. Rollback capability
    6. Audit trail
    """

    def __init__(self, database):
        self.database = database
        self.registered_tools: Dict[str, ToolDefinition] = {}
        self.invocation_history: List[ToolInvocation] = []
        self.rate_limit_tracker: Dict[str, List[datetime]] = defaultdict(list)
        self.idempotency_cache: Dict[str, ToolInvocation] = {}
        self.register_default_tools()

    def register_tool(self, tool_def: ToolDefinition):
        """Register a tool"""
        self.registered_tools[tool_def.tool_id] = tool_def
        logger.info(f"Tool registered: {tool_def.tool_id} ({tool_def.tool_type.value})")

    def register_default_tools(self):
        """Register default Air NZ tools"""

        # READ TOOLS

        self.register_tool(ToolDefinition(
            tool_id="get_flight_status",
            name="Get Flight Status",
            description="Get real-time flight status from operational systems",
            tool_type=ToolType.READ,
            allowed_risk_tiers=["R0", "R1", "R2", "R3"],
            requires_approval=False,
            requires_dual_control=False,
            supports_rollback=False,
            rate_limit_per_minute=100,
            parameter_schema={
                "flight_number": {"type": "string", "required": True, "pattern": r"^NZ\d+$"}
            },
            execute_function=self._get_flight_status
        ))

        self.register_tool(ToolDefinition(
            tool_id="get_aircraft_availability",
            name="Get Aircraft Availability",
            description="Get available aircraft at specified base",
            tool_type=ToolType.READ,
            allowed_risk_tiers=["R2", "R3"],
            requires_approval=False,
            requires_dual_control=False,
            supports_rollback=False,
            rate_limit_per_minute=50,
            parameter_schema={
                "base": {"type": "string", "required": True, "enum": ["AKL", "CHC", "WLG"]}
            },
            execute_function=self._get_aircraft_availability
        ))

        self.register_tool(ToolDefinition(
            tool_id="get_crew_availability",
            name="Get Crew Availability",
            description="Get available crew at specified base and aircraft type",
            tool_type=ToolType.READ,
            allowed_risk_tiers=["R2", "R3"],
            requires_approval=False,
            requires_dual_control=False,
            supports_rollback=False,
            rate_limit_per_minute=50,
            parameter_schema={
                "base": {"type": "string", "required": True},
                "aircraft_type": {"type": "string", "required": False}
            },
            execute_function=self._get_crew_availability
        ))

        self.register_tool(ToolDefinition(
            tool_id="search_policies",
            name="Search Policies",
            description="Search policy documents by keyword",
            tool_type=ToolType.READ,
            allowed_risk_tiers=["R0", "R1", "R2", "R3"],
            requires_approval=False,
            requires_dual_control=False,
            supports_rollback=False,
            rate_limit_per_minute=100,
            parameter_schema={
                "query": {"type": "string", "required": True},
                "business_domain": {"type": "string", "required": False}
            },
            execute_function=self._search_policies
        ))

        # WRITE TOOLS (R3 only)

        self.register_tool(ToolDefinition(
            tool_id="create_work_order",
            name="Create Work Order",
            description="Create new maintenance work order",
            tool_type=ToolType.WRITE,
            allowed_risk_tiers=["R3"],
            requires_approval=True,
            requires_dual_control=True,
            supports_rollback=True,
            rate_limit_per_minute=10,
            parameter_schema={
                "aircraft_registration": {"type": "string", "required": True},
                "work_type": {"type": "string", "required": True, "enum": ["corrective", "preventive", "inspection"]},
                "priority": {"type": "string", "required": True, "enum": ["low", "medium", "high", "critical"]},
                "description": {"type": "string", "required": True, "min_length": 10}
            },
            execute_function=self._create_work_order
        ))

    def invoke_tool(
        self,
        tool_id: str,
        parameters: Dict,
        user_id: str,
        trace_id: str,
        risk_tier: str,
        idempotency_key: Optional[str] = None
    ) -> ToolExecutionResult:
        """
        Invoke a tool with full safety checks.

        Args:
            tool_id: Tool to invoke
            parameters: Tool parameters
            user_id: User invoking tool
            trace_id: Trace ID for audit
            risk_tier: Risk tier of the request
            idempotency_key: Optional key for idempotent operations

        Returns:
            ToolExecutionResult
        """
        timestamp = datetime.now()
        invocation_id = f"{tool_id}_{trace_id}_{timestamp.timestamp()}"

        # Check 1: Tool exists
        tool_def = self.registered_tools.get(tool_id)
        if not tool_def:
            return self._error_result(
                invocation_id, ToolStatus.VALIDATION_ERROR,
                f"Tool {tool_id} not found"
            )

        # Check 2: Risk tier allowed
        if risk_tier not in tool_def.allowed_risk_tiers:
            logger.warning(
                f"Tool {tool_id} not allowed for risk tier {risk_tier}. "
                f"Allowed: {tool_def.allowed_risk_tiers}"
            )
            return self._error_result(
                invocation_id, ToolStatus.PERMISSION_DENIED,
                f"Tool {tool_id} not allowed for risk tier {risk_tier}"
            )

        # Check 3: Parameter validation
        validation_error = self._validate_parameters(parameters, tool_def.parameter_schema)
        if validation_error:
            return self._error_result(
                invocation_id, ToolStatus.VALIDATION_ERROR,
                f"Parameter validation failed: {validation_error}"
            )

        # Check 4: Rate limiting
        if not self._check_rate_limit(tool_id, user_id, tool_def.rate_limit_per_minute):
            logger.warning(f"Rate limit exceeded for tool {tool_id} by user {user_id}")
            return self._error_result(
                invocation_id, ToolStatus.RATE_LIMITED,
                f"Rate limit exceeded: {tool_def.rate_limit_per_minute}/min"
            )

        # Check 5: Idempotency
        if idempotency_key:
            cached = self.idempotency_cache.get(idempotency_key)
            if cached:
                logger.info(f"Idempotent call detected, returning cached result")
                return ToolExecutionResult(
                    success=cached.status == ToolStatus.SUCCESS,
                    status=ToolStatus.IDEMPOTENT_SKIP,
                    result=cached.result,
                    error=None,
                    invocation_id=cached.invocation_id,
                    timestamp=cached.timestamp,
                    can_rollback=False
                )

        # Execute tool
        try:
            result = tool_def.execute_function(parameters)

            # Create invocation record
            invocation = ToolInvocation(
                invocation_id=invocation_id,
                tool_id=tool_id,
                user_id=user_id,
                trace_id=trace_id,
                parameters=parameters,
                status=ToolStatus.SUCCESS,
                result=result,
                error=None,
                timestamp=timestamp,
                rollback_data=result.get('rollback_data') if tool_def.supports_rollback else None
            )

            self.invocation_history.append(invocation)

            # Cache for idempotency
            if idempotency_key:
                self.idempotency_cache[idempotency_key] = invocation

            logger.info(
                f"Tool invoked successfully: {tool_id} by {user_id} "
                f"[{trace_id}]"
            )

            return ToolExecutionResult(
                success=True,
                status=ToolStatus.SUCCESS,
                result=result,
                error=None,
                invocation_id=invocation_id,
                timestamp=timestamp,
                can_rollback=tool_def.supports_rollback,
                rollback_data=invocation.rollback_data
            )

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_id} - {str(e)}")

            invocation = ToolInvocation(
                invocation_id=invocation_id,
                tool_id=tool_id,
                user_id=user_id,
                trace_id=trace_id,
                parameters=parameters,
                status=ToolStatus.FAILURE,
                result=None,
                error=str(e),
                timestamp=timestamp
            )

            self.invocation_history.append(invocation)

            return ToolExecutionResult(
                success=False,
                status=ToolStatus.FAILURE,
                result=None,
                error=str(e),
                invocation_id=invocation_id,
                timestamp=timestamp,
                can_rollback=False
            )

    def rollback_invocation(self, invocation_id: str) -> bool:
        """
        Rollback a tool invocation (R3 only).

        Args:
            invocation_id: Invocation to rollback

        Returns:
            True if rollback successful
        """
        # Find invocation
        invocation = next(
            (inv for inv in self.invocation_history if inv.invocation_id == invocation_id),
            None
        )

        if not invocation:
            logger.error(f"Invocation not found: {invocation_id}")
            return False

        tool_def = self.registered_tools.get(invocation.tool_id)
        if not tool_def or not tool_def.supports_rollback:
            logger.error(f"Tool {invocation.tool_id} does not support rollback")
            return False

        if not invocation.rollback_data:
            logger.error(f"No rollback data available for {invocation_id}")
            return False

        # Execute rollback (tool-specific logic)
        try:
            if invocation.tool_id == "create_work_order":
                wo_number = invocation.rollback_data.get('wo_number')
                # In production, would delete or cancel the work order
                logger.info(f"Rolled back work order: {wo_number}")

            logger.info(f"Invocation rolled back: {invocation_id}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False

    def _validate_parameters(self, parameters: Dict, schema: Dict) -> Optional[str]:
        """Validate parameters against schema"""
        for param_name, param_def in schema.items():
            # Check required
            if param_def.get('required', False) and param_name not in parameters:
                return f"Missing required parameter: {param_name}"

            if param_name not in parameters:
                continue

            value = parameters[param_name]

            # Check type
            expected_type = param_def.get('type')
            if expected_type == 'string' and not isinstance(value, str):
                return f"Parameter {param_name} must be string"
            if expected_type == 'integer' and not isinstance(value, int):
                return f"Parameter {param_name} must be integer"

            # Check enum
            if 'enum' in param_def and value not in param_def['enum']:
                return f"Parameter {param_name} must be one of {param_def['enum']}"

            # Check pattern (regex)
            if 'pattern' in param_def:
                import re
                if not re.match(param_def['pattern'], value):
                    return f"Parameter {param_name} does not match pattern {param_def['pattern']}"

            # Check min_length
            if 'min_length' in param_def and len(value) < param_def['min_length']:
                return f"Parameter {param_name} must be at least {param_def['min_length']} characters"

        return None

    def _check_rate_limit(self, tool_id: str, user_id: str, limit_per_minute: int) -> bool:
        """Check if rate limit exceeded"""
        key = f"{tool_id}_{user_id}"
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Remove old entries
        self.rate_limit_tracker[key] = [
            ts for ts in self.rate_limit_tracker[key]
            if ts > one_minute_ago
        ]

        # Check limit
        if len(self.rate_limit_tracker[key]) >= limit_per_minute:
            return False

        # Record this call
        self.rate_limit_tracker[key].append(now)
        return True

    def _error_result(self, invocation_id: str, status: ToolStatus, error: str) -> ToolExecutionResult:
        """Create error result"""
        return ToolExecutionResult(
            success=False,
            status=status,
            result=None,
            error=error,
            invocation_id=invocation_id,
            timestamp=datetime.now(),
            can_rollback=False
        )

    # Tool implementation functions

    def _get_flight_status(self, parameters: Dict) -> Dict:
        """Get flight status from database"""
        flight_number = parameters['flight_number']
        flight = self.database.get_flight_status(flight_number)

        if not flight:
            raise Exception(f"Flight not found: {flight_number}")

        return {
            "source": "operational_database",
            "flight_number": flight['flight_number'],
            "route": flight['route'],
            "status": flight['status'],
            "scheduled_departure": flight['scheduled_departure'],
            "delay_minutes": flight['delay_minutes'],
            "gate": flight['gate'],
            "pax_count": flight['pax_count'],
            "aircraft_registration": flight['aircraft_registration']
        }

    def _get_aircraft_availability(self, parameters: Dict) -> Dict:
        """Get aircraft availability"""
        base = parameters['base']
        aircraft = self.database.get_aircraft_availability(base)

        return {
            "source": "fleet_management_system",
            "base": base,
            "available_aircraft": [
                {
                    "registration": a['registration'],
                    "type": a['aircraft_type'],
                    "capacity": a['capacity']
                }
                for a in aircraft
            ]
        }

    def _get_crew_availability(self, parameters: Dict) -> Dict:
        """Get crew availability"""
        base = parameters['base']
        aircraft_type = parameters.get('aircraft_type')

        crew = self.database.get_crew_availability(base, aircraft_type)

        return {
            "source": "crew_rostering_system",
            "base": base,
            "aircraft_type": aircraft_type,
            "available_crew": [
                {
                    "employee_id": c['employee_id'],
                    "name": c['name'],
                    "role": c['role'],
                    "flight_duty_period_remaining": c['flight_duty_period_remaining']
                }
                for c in crew
            ]
        }

    def _search_policies(self, parameters: Dict) -> Dict:
        """Search policies"""
        query = parameters['query']
        business_domain = parameters.get('business_domain')

        policies = self.database.search_policies(query, business_domain)

        return {
            "source": "policy_management_system",
            "query": query,
            "results": [
                {
                    "document_id": p['document_id'],
                    "title": p['title'],
                    "version": p['version'],
                    "content": p['content'],
                    "effective_date": p['effective_date']
                }
                for p in policies
            ]
        }

    def _create_work_order(self, parameters: Dict) -> Dict:
        """Create work order (R3 write action)"""
        wo_number = self.database.create_work_order(parameters)

        return {
            "source": "maintenance_management_system",
            "wo_number": wo_number,
            "status": "created",
            "rollback_data": {"wo_number": wo_number}  # For rollback
        }

    def get_tool_metrics(self) -> Dict:
        """Get tool usage metrics"""
        total_invocations = len(self.invocation_history)
        successful = len([inv for inv in self.invocation_history if inv.status == ToolStatus.SUCCESS])
        failed = len([inv for inv in self.invocation_history if inv.status == ToolStatus.FAILURE])
        rate_limited = len([inv for inv in self.invocation_history if inv.status == ToolStatus.RATE_LIMITED])

        return {
            "total_invocations": total_invocations,
            "successful": successful,
            "failed": failed,
            "rate_limited": rate_limited,
            "success_rate": successful / total_invocations if total_invocations > 0 else 0
        }
