# Incident Response Runbooks

Operational runbooks for AI Governance Platform incidents.

## Table of Contents

1. [SLO Violation Response](#slo-violation-response)
2. [Hallucination Detection](#hallucination-detection)
3. [Privilege Escalation Attempt](#privilege-escalation-attempt)
4. [Tool Failure](#tool-failure)
5. [LLM Service Outage](#llm-service-outage)
6. [Database Corruption](#database-corruption)
7. [Evidence Validation Failure](#evidence-validation-failure)
8. [Emergency Shutdown](#emergency-shutdown)

---

## SLO Violation Response

### Detection
- SLO monitor alerts on violated SLO
- Dashboard shows red status
- Automated alert sent to on-call engineer

### Severity Classification
- **P1 (Critical)**: Availability < 99%, Latency > 10s, Privilege escalations > 0
- **P2 (High)**: Citation coverage < 90%, Tool success < 95%
- **P3 (Medium)**: Latency 20% above target
- **P4 (Low)**: Minor deviations within 10% of target

### Response Steps

#### Immediate (0-15 minutes)
1. **Acknowledge** the alert
2. **Check** the SLO dashboard for affected metrics
3. **Identify** the risk tier(s) affected
4. **Query** recent audit logs for error patterns
   ```python
   from src.monitoring.slo_monitor import SLOMonitor
   monitor = SLOMonitor()
   report = monitor.get_slo_report(hours=1)
   print(report)
   ```

#### Investigation (15-60 minutes)
1. **Review** traces from affected requests
   ```python
   from src.core.audit_system import AuditSystem
   audit = AuditSystem()
   recent_traces = audit.get_trace_history(
       start_date=datetime.now() - timedelta(hours=1)
   )
   failed = [t for t in recent_traces if t.status == 'failed']
   ```

2. **Check** system health:
   - Database connectivity
   - LLM service availability
   - Tool gateway status
   - External API status (FlightAPI)

3. **Identify** root cause:
   - Model degradation?
   - Tool/API failure?
   - Database slowness?
   - Spike in traffic?

#### Mitigation (60 minutes+)
1. **For latency violations**:
   - Check LLM response times
   - Review tool invocation times
   - Consider scaling database
   - Enable caching for frequently accessed policies

2. **For availability violations**:
   - Identify failing component
   - Enable fallback mode if available
   - Consider disabling specific features temporarily

3. **For quality violations** (citations, hallucinations):
   - Review recent model/prompt changes
   - Rollback to previous version if needed
   - Add affected queries to regression test suite

#### Resolution
1. **Implement** fix
2. **Test** in staging environment
3. **Deploy** to production
4. **Monitor** SLOs for 24 hours
5. **Document** incident in post-mortem

### Rollback Procedure
```python
from src.core.policy_engine import PolicyEngine
engine = PolicyEngine()

# Rollback policy to previous version
engine.rollback_policy(RiskTier.R1)
```

---

## Hallucination Detection

### Detection
- User reports incorrect information
- Automated quality checks flag response
- Citation verification fails
- Escalation from human reviewer

### Response Steps

#### Immediate (0-5 minutes)
1. **Capture** the trace ID from the reported interaction
2. **Retrieve** full execution trace
   ```python
   trace = audit_system.traces.get(trace_id)
   ```

3. **Verify** citations:
   ```python
   for citation in evidence_package.citations:
       is_valid = citation.verify_content(actual_source_content)
       if not is_valid:
           logger.critical(f"Citation mismatch: {citation.document_id}")
   ```

#### Investigation (5-30 minutes)
1. **Check** if evidence was provided
   - Was retrieval successful?
   - Were citations included?
   - Did evidence match the query?

2. **Review** the LLM prompt and response
   - Did model stick to evidence?
   - Did model fabricate details?
   - Was prompt clear about evidence-only responses?

3. **Check** for pattern:
   - Query similar traces
   - Is this a systematic issue?
   - Is it specific to a model version?

#### Mitigation
1. **Block** the affected response (if still being served)
2. **Add** to hallucination detection dataset
3. **If systematic**:
   - Rollback model/prompt version
   - Tighten evidence requirements
   - Add stronger "stick to evidence" instructions

4. **Notify** affected users if possible
   ```python
   # Mark response as invalid
   response.metadata['hallucination_detected'] = True
   response.metadata['invalidated_at'] = datetime.now()
   ```

#### Prevention
1. **Update** prompt templates to emphasize evidence-only responses
2. **Add** query pattern to regression tests
3. **Increase** citation coverage requirements
4. **Review** retrieval strategy for this query type

---

## Privilege Escalation Attempt

### Detection
- Access control logs show denied access attempt
- User attempts to access data outside their domain
- Tool invocation denied due to risk tier mismatch

### Severity: P1 (CRITICAL - immediate response required)

### Response Steps

#### Immediate (0-5 minutes)
1. **ALERT** security team
2. **Capture** full context:
   ```python
   trace = audit_system.traces.get(trace_id)
   user_id = trace.user_id
   attempted_resource = trace.details['resource_id']
   ```

3. **Check** if attempt was successful
   - Review all access decisions for this user
   - Check if any bypass occurred

#### Investigation (5-30 minutes)
1. **Review** user's recent activity
   ```python
   user_traces = audit.get_trace_history(user_id=user_id, hours=24)
   ```

2. **Check** for pattern:
   - Multiple attempts?
   - Targeting specific data?
   - Legitimate mistake or malicious?

3. **Verify** access control logic:
   - Did pre-retrieval filter work?
   - Were all gates enforced?
   - Any configuration errors?

#### Containment
1. **If malicious**:
   ```python
   # Suspend user account
   database.execute(
       "UPDATE users SET active = 0 WHERE user_id = ?",
       (user_id,)
   )
   ```

2. **Review** and tighten access controls if bypass found
3. **Audit** all data accessed by user in past 7 days

#### Post-Incident
1. **Security review** of access control logic
2. **Red team** test for similar bypasses
3. **Document** in security incident report
4. **Update** access control rules if needed

---

## Tool Failure

### Detection
- Tool invocation returns error
- Tool success rate SLO violated
- External API timeout/error

### Response Steps

#### Immediate (0-10 minutes)
1. **Identify** failing tool:
   ```python
   tool_metrics = tool_gateway.get_tool_metrics()
   failed_tools = [t for t in tool_metrics if t['success_rate'] < 0.95]
   ```

2. **Check** tool type:
   - READ tool (data loss risk: LOW)
   - WRITE tool (data loss risk: HIGH)

3. **Enable** fallback if available:
   - Flight API ’ Database fallback
   - Policy search ’ Cached results

#### Investigation (10-30 minutes)
1. **For external API failures**:
   - Check API status page
   - Test API directly
   - Review rate limits
   - Check authentication

2. **For database failures**:
   - Check connection pool
   - Review slow query log
   - Check disk space
   - Verify connectivity

3. **For internal tools**:
   - Check implementation logs
   - Review recent code changes
   - Test tool manually

#### Mitigation
1. **Enable** circuit breaker:
   ```python
   # Temporarily disable failing tool
   tool_gateway.registered_tools[tool_id].enabled = False
   ```

2. **Route** to alternative:
   - Use cached data
   - Fall back to database
   - Escalate to human for critical operations

3. **If WRITE tool** (R3):
   - HALT all automated actions
   - Notify approvers
   - Switch to manual approval only

#### Recovery
1. **Fix** root cause
2. **Test** tool in isolation
3. **Gradually re-enable**:
   - Start with read-only tools
   - Monitor error rates
   - Enable write tools last

---

## LLM Service Outage

### Detection
- OpenAI API returns 5xx errors
- Timeouts on LLM requests
- All generations failing

### Severity: P1 for R1/R2, P2 for R0

### Response Steps

#### Immediate (0-5 minutes)
1. **Enable** mock mode:
   ```python
   llm_service.mock_mode = True
   ```

2. **Notify** users:
   - R0: "AI assistant temporarily unavailable"
   - R1: Escalate ALL queries to human agents
   - R2: Provide fallback recommendations from procedures

#### Mitigation (5-60 minutes)
1. **Check** OpenAI status: https://status.openai.com
2. **Try** alternative models:
   - gpt-3.5-turbo ’ gpt-4
   - Retry with exponential backoff

3. **For extended outage**:
   - R0: Disable code assistant, notify developers
   - R1: Route ALL customer queries to human agents
   - R2: Provide procedure-based decision support (no LLM)
   - R3: HALT all automated actions

4. **Consider** alternative LLM provider if > 2 hours

#### Recovery
1. **Test** LLM service with low-risk queries
2. **Re-enable** gradually:
   - R0 first (lowest risk)
   - R1 next (customer-facing)
   - R2 last (operations)
3. **Monitor** closely for 24 hours

---

## Database Corruption

### Detection
- SQLite integrity check fails
- Query errors on read
- Data inconsistencies detected

### Severity: P1 (CRITICAL)

### Response Steps

#### Immediate (0-5 minutes)
1. **HALT** all WRITE operations
   ```python
   # Block all R3 agents
   for tool_id in tool_gateway.registered_tools:
       if tool_gateway.registered_tools[tool_id].tool_type == ToolType.WRITE:
           tool_gateway.registered_tools[tool_id].enabled = False
   ```

2. **Enable** read-only mode
3. **Take** database backup immediately

#### Investigation (5-30 minutes)
1. **Run** integrity check:
   ```bash
   sqlite3 airnz.db "PRAGMA integrity_check;"
   ```

2. **Identify** corrupted tables
3. **Check** disk space and file system errors

4. **Review** recent WRITE operations:
   ```python
   recent_writes = [
       inv for inv in tool_gateway.invocation_history
       if inv.tool_id == "create_work_order"
   ]
   ```

#### Recovery
1. **If minor corruption**:
   - Export uncorrupted data
   - Recreate database
   - Re-import data

2. **If major corruption**:
   - Restore from last known good backup
   - Replay audit log to recover missing transactions
   - Verify data integrity

3. **Audit** all data created since last backup

#### Prevention
1. **Implement** regular backups (hourly)
2. **Add** database health checks
3. **Enable** write-ahead logging (WAL)
4. **Consider** migration to PostgreSQL for production

---

## Evidence Validation Failure

### Detection
- Citation verification fails
- Document version mismatch
- Source content hash mismatch

### Severity: P2

### Response Steps

#### Immediate (0-10 minutes)
1. **Identify** affected citations:
   ```python
   failed_citations = [
       c for c in citations
       if not c.verify_content(actual_content)
   ]
   ```

2. **Block** responses using failed citations
3. **Escalate** to human review

#### Investigation (10-30 minutes)
1. **Check** if document was updated:
   - Was new version released?
   - Did content change?
   - Is our index stale?

2. **Verify** retrieval system:
   - Is index up to date?
   - Are version numbers correct?
   - Is source system accessible?

3. **Check** for systematic issue:
   - Multiple documents affected?
   - Specific source system?
   - Index corruption?

#### Resolution
1. **Re-index** affected documents
2. **Update** version metadata
3. **Invalidate** cached results for affected documents
4. **Re-run** recent queries that used affected citations

---

## Emergency Shutdown

### When to Use
- Active security breach
- Systematic hallucinations causing harm
- Data integrity crisis
- Regulatory requirement

### Procedure

#### 1. Initiate Shutdown (0-2 minutes)
```python
# Kill switch - disable all AI operations
from src.core.policy_engine import PolicyEngine

engine = PolicyEngine()

# Disable all risk tiers
for tier in [RiskTier.R0, RiskTier.R1, RiskTier.R2, RiskTier.R3]:
    # Block all capabilities
    policy = engine.active_policies[tier]
    policy.blocked_capabilities = set(CapabilityType)
    policy.allowed_capabilities = set()
```

#### 2. Notify Stakeholders (2-5 minutes)
- Engineering team
- Operations team
- Customer service team
- Management
- Regulatory (if required)

#### 3. Secure System (5-15 minutes)
1. **Take** full database backup
2. **Export** all audit logs
3. **Preserve** all traces for investigation
4. **Document** shutdown reason and time

#### 4. Fallback Operations
- **R0**: Notify developers - no code assistant
- **R1**: Route ALL customers to human agents
- **R2**: Provide procedure-only decision support
- **R3**: Manual approval for ALL actions

#### 5. Investigation & Resolution
1. **Identify** root cause
2. **Implement** fix in isolated environment
3. **Test** thoroughly with regression suite
4. **Get** management approval for restart

#### 6. Gradual Restart
1. **Start** with R0 (lowest risk)
2. **Monitor** for 2 hours
3. **Enable** R1 if stable
4. **Monitor** for 4 hours
5. **Enable** R2 if stable
6. **R3** requires explicit approval + dual sign-off

---

## Escalation Matrix

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| P1 (Critical) | < 15 min | Immediate: On-call + Manager |
| P2 (High) | < 1 hour | On-call engineer |
| P3 (Medium) | < 4 hours | Next business day |
| P4 (Low) | < 24 hours | Log only, fix in sprint |

## On-Call Contacts

- **Engineering On-Call**: Slack #ai-platform-oncall
- **Security On-Call**: Slack #security-incidents
- **Ops Manager**: [Contact info]
- **CTO**: [Contact info]

## Post-Incident Review Template

```markdown
# Post-Incident Review: [Incident Title]

## Incident Summary
- **Date**: YYYY-MM-DD
- **Duration**: X hours
- **Severity**: P1/P2/P3/P4
- **Affected Systems**: [List]
- **User Impact**: [Description]

## Timeline
- HH:MM - Detection
- HH:MM - Response initiated
- HH:MM - Root cause identified
- HH:MM - Mitigation deployed
- HH:MM - Incident resolved

## Root Cause
[Detailed explanation]

## What Went Well
- [Positives]

## What Went Wrong
- [Issues]

## Action Items
1. [Action] - Owner: [Name] - Due: [Date]
2. [Action] - Owner: [Name] - Due: [Date]

## Preventative Measures
[How to prevent recurrence]
```
