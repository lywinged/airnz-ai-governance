# AI Governance Criteria (G1-G12)

This document details the 12 core governance criteria implemented in the Air NZ AI Governance Platform.

## G1: AI Safety-Case

Each AI use case has a complete "assurance package" including:

- **Use-case boundary**: Clear definition of what the AI does and doesn't do
- **Hazard identification**: What could go wrong
- **Risk assessment**: Likelihood and severity of hazards
- **Controls**: Mitigations in place
- **Residual risk**: Remaining risk after controls
- **Ongoing assurance**: Monitoring and evaluation
- **Shutdown strategy**: How to safely disable if needed

This aligns with aviation SMS (Safety Management System) and Part 100 guidance philosophy.

**Implementation**: See [policy_engine.py](../src/core/policy_engine.py) for risk tier classification.

---

## G2: Risk Tiering + Dynamic Gates (R0-R3)

Gates control real execution paths, not just documentation:

### R0: Low-risk Internal Productivity
- **Use cases**: Writing, coding assistance, summarization
- **Controls**:
  - Internet access allowed
  - No write operations
  - No dual control required
  - Citations optional

### R1: External/Customer-facing
- **Use cases**: Oscar chatbot, policy clarification, customer service
- **Controls**:
  - Citations REQUIRED
  - Tool invocation allowed (read-only)
  - No write operations
  - No internet access

### R2: Operations/Maintenance Decision Support
- **Use cases**: Disruption management, maintenance planning, OCC support
- **Controls**:
  - Citations REQUIRED
  - Human approval REQUIRED
  - Tool invocation allowed (read-only)
  - No write operations

### R3: Actions & Closed Loops
- **Use cases**: Automated actions (default FORBIDDEN)
- **Controls**:
  - All R2 controls PLUS:
  - Dual control REQUIRED
  - Rollback REQUIRED
  - Write operations allowed (with gates)

**Implementation**: See [policy_engine.py](../src/core/policy_engine.py)

---

## G3: Evidence Contract with Verifiable Citations

Citations must include:

- **Document ID**: Unique identifier
- **Version**: Document version
- **Revision**: Revision number
- **Effective Date**: When document became effective
- **Effective Until**: When document expires/supersedes
- **Source System**: Where document lives
- **Paragraph Locator**: Section/chapter/page/paragraph
- **Content Hash**: SHA-256 of excerpt for verification
- **Applicability**: Aircraft types, bases, regions, domains

### No Evidence = No Answer

For policy/procedure/manual answers in R1-R3:
- If no evidence exists → escalate to human
- If evidence is outdated → flag and escalate
- If evidence cannot be verified → block answer

**Implementation**: See [evidence_contract.py](../src/core/evidence_contract.py)

---

## G4: Permission Layers (Pre-Retrieval Filtering)

Access control happens BEFORE retrieval to prevent "see first then mask" leakage.

### Multi-dimensional Access Control

Users are filtered by:
- **Role**: customer_service, engineering, dispatch_occ, safety, etc.
- **Business Domain**: operations, engineering, customer_service, hr, finance, safety
- **Aircraft Types**: A320, B787-9, ATR72, etc.
- **Bases**: AKL, CHC, WLG, etc.
- **Route Regions**: Domestic, Trans-Tasman, Pacific, etc.
- **Sensitivity Clearance**: public, internal, confidential, restricted

### Access Decision Logging

Every access check logs:
- Who requested access
- What resource was requested
- Why access was granted/denied
- Which rules matched

**Implementation**: See [access_control.py](../src/core/access_control.py)

---

## G5: Tool/Action Safety Gates

All tool calls go through a unified gateway with:

- **Read/Write Isolation**: Read-only tools separated from write tools
- **Parameter Validation**: All inputs validated before invocation
- **Rate Limiting**: Prevent abuse and runaway costs
- **Idempotency**: Duplicate calls don't cause duplicate actions
- **Rollback**: Write actions can be undone

### Write Actions (R3) Require:
- Just-in-time authorization
- Dual control (two approvers)
- Rollback capability
- Immutable logging

**Implementation**: See [policy_engine.py](../src/core/policy_engine.py) capability gates

---

## G6: Prompt/Policy/Model Versioning

All components are under change control:

### Versioned Components
- **Model**: claude-sonnet-4.5, claude-opus-4, etc.
- **Prompt Templates**: oscar_v1.0, disruption_v1.0, etc.
- **Retrieval Indexes**: policies_v2.3, ops_procedures_v1.5, etc.
- **Policies**: R0_v1.0, R1_v1.0, etc.

### Change Control Process
1. Propose change
2. Get approval
3. Run regression tests
4. Canary rollout
5. Monitor metrics
6. Rollback if needed

Every change must answer:
- What changed?
- Who approved?
- Which use cases affected?
- What regression results show?

**Implementation**: See [policy_engine.py](../src/core/policy_engine.py) update_policy() and rollback_policy()

---

## G7: Full-chain Observability + Replayability

Every response must be reproducible.

### Execution Trace
Every request creates a trace with:
- Trace ID
- User ID
- Query
- All events (routing, retrieval, tools, generation, approval)
- Final response
- All version info (model, prompt, index, policy)

### Replay Capability
Given a trace ID, you can:
1. Restore exact versions (model, prompt, index, policy)
2. Re-run the same query
3. Compare outputs
4. Verify determinism

### Use Cases for Replay
- Incident investigation
- Audit compliance
- Regression testing
- Quality verification

**Implementation**: See [audit_system.py](../src/core/audit_system.py)

---

## G8: Evaluation System (Offline + Online + Red Team)

### Offline Evaluation
- **Golden datasets**: Curated question-answer pairs
- **Regression tests**: Verify changes don't break existing behavior
- **Stratified coverage**: Test across roles, aircraft, bases, risk tiers

### Online Metrics
- **Citation coverage rate**: % of answers with valid citations
- **Hallucination rate**: % of answers with fabricated info
- **Tool success rate**: % of tool calls that succeeded
- **Privilege block rate**: % of requests blocked by access control
- **Human approval rate**: % of R2/R3 requiring approval

### Red Team Testing
- **Prompt injection**: Attempts to bypass controls
- **Privilege escalation**: Attempts to access unauthorized data
- **Fabricated citations**: Fake evidence detection
- **Sensitive data leaks**: PII/confidential data exposure
- **Tool abuse**: Malicious tool invocation attempts

**Implementation**: See [audit_system.py](../src/core/audit_system.py) metrics

---

## G9: Data Governance (NZ Privacy Act)

Aligned with Information Privacy Principles (IPPs):

### IPP1-2: Purpose Limitation & Collection Limitation
- Only collect/use data for declared purposes
- Log all purpose checks

### IPP3: Data Quality
- Ensure accuracy and currency
- Support correction requests

### IPP4-5: Security & Retention
- Encrypt sensitive data
- Delete after retention period
- Track retention deadlines

### IPP6: Access Rights
- Users can request their data
- 20 working day response SLA

### IPP7: Correction Rights
- Users can request corrections
- Verify and apply corrections

### IPP8-11: Accuracy, Use, Disclosure, Safeguards
- Cross-border controls
- Data minimization
- Purpose-based filtering

**Implementation**: See [privacy_control.py](../src/core/privacy_control.py)

---

## G10: Tenant/Domain Isolation

Air NZ's internal business domains are isolated:

- **Operations**: OCC, dispatch, airport ops
- **Engineering**: Maintenance, technical services
- **Customer Service**: Contact center, airports
- **Safety**: Safety management, investigations
- **Finance**: Revenue management, pricing
- **HR**: Employee data

The same question may return:
- Different evidence in different domains
- Different answers based on domain context
- Different access permissions

**Implementation**: See [access_control.py](../src/core/access_control.py) domain isolation

---

## G11: Reliability Engineering

### SLOs (Service Level Objectives)
- Availability: 99.9% uptime
- Latency: p95 < 2s for R0/R1, < 5s for R2
- Error rate: < 0.1%

### Graceful Degradation
When failures occur:
1. **Model failure** → Fallback to simpler model or escalate
2. **Retrieval failure** → Use cached results or read-only mode
3. **Tool failure** → Circuit breaker, return partial results
4. **Policy violation** → Block and escalate

### Kill Switches
Ability to:
- Disable specific use cases
- Disable specific risk tiers
- Disable all AI operations
- Rollback to previous versions

**Implementation**: Pattern embedded across all components

---

## G12: Governance as a Product

Make governance operational, not a blocker:

### Policy-as-Code
- Policies defined in code (not Word docs)
- Version controlled
- Testable and verifiable

### Audit Dashboards
- Real-time metrics
- Compliance reports
- Anomaly detection

### Approval Workflows
- Built into the system
- Trackable and auditable
- SLA monitoring

### Evidence Quality Reports
- Citation coverage
- Outdated evidence detection
- Verification failures

### Data Source Health Monitoring
- Index freshness
- Tool availability
- Permission sync status

**Goal**: Governance should accelerate safe delivery, not block it.

**Implementation**: See all core modules - governance is embedded, not bolted on

---

## Summary

These 12 criteria create a **compliance-grade foundation** where:

1. Every AI use case has a safety case (G1)
2. Risk-appropriate controls are enforced at runtime (G2)
3. All answers are evidence-backed and verifiable (G3)
4. Access is controlled before retrieval (G4)
5. Actions are gated and reversible (G5)
6. Changes are controlled and auditable (G6)
7. Everything is traceable and replayable (G7)
8. Quality is continuously measured (G8)
9. Privacy is protected by design (G9)
10. Domains are isolated (G10)
11. Failures degrade gracefully (G11)
12. Governance enables, not blocks (G12)

This foundation allows you to attach any number of agents (Oscar, disruption management, maintenance, etc.) and they'll all run inside the same controlled system.
