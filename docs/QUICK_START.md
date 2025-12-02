# Quick Start Guide

Get started with the Air NZ AI Governance Platform in 5 minutes.

## Prerequisites

- Python 3.9+
- Basic understanding of AI governance concepts

## Installation

```bash
# Clone or navigate to the project directory
cd airnz-ai-governance

# Install dependencies
pip install -r requirements.txt
```

## API modes (real vs mock)

- **LLM (OpenAI)**: Set `OPENAI_API_KEY` to use real OpenAI calls; otherwise the platform runs in mock mode with simulated responses.
- **Flight data (AviationStack)**: Set `AVIATIONSTACK_API_KEY` to fetch live flight status; otherwise the R2 example uses the built-in SQLite fallback/mock data.
- No extra flags needed—`run_full_demo.py` and the CLI examples auto-detect these env vars and print whether real or mock mode is active.

> Tip: `.env` is auto-loaded by `run_full_demo.py` and the CLI examples (`examples/run_oscar_chatbot.py`, `examples/run_disruption_management.py`). Just set the keys in `.env` or export them in your shell.

## Running the Examples

### Example 1: Oscar Chatbot (R1 - Customer Service)

The Oscar chatbot demonstrates an R1 (customer-facing) agent with evidence-backed responses.

```bash
cd examples
python run_oscar_chatbot.py
```

**What you'll see:**
- Evidence-backed customer service responses
- Verifiable citations with version info
- Privacy controls in action
- Full audit trail

**Key features demonstrated:**
- Citations REQUIRED for R1
- Pre-retrieval access control
- Evidence validation
- Escalation when evidence is missing

---

### Example 2: Disruption Management (R2 - Operations Support)

The disruption management agent demonstrates R2 (operations decision support) with mandatory human approval.

```bash
cd examples
python run_disruption_management.py
```

**What you'll see:**
- AI-generated recovery options
- Tool-RAG pulling real-time operational data
- Constraint-aware recommendations
- Human approval workflow
- Full traceability for incident investigation

**Key features demonstrated:**
- Human approval REQUIRED for R2
- Tool invocation with read-only access
- Multiple recovery options with scoring
- Evidence from operational procedures
- Audit trail for replay

---

## Understanding the Core Components

### 1. Policy Engine ([policy_engine.py](../src/core/policy_engine.py))

Controls what each risk tier can do:

```python
from src.core.policy_engine import PolicyEngine, RiskTier, ExecutionContext, CapabilityType

# Create policy engine
engine = PolicyEngine()

# Create execution context
context = ExecutionContext(
    user_id="user123",
    role="customer_service",
    business_domain="customer_service",
    use_case_id="oscar_chatbot",
    risk_tier=RiskTier.R1,
    session_id="session_001",
    timestamp=datetime.now()
)

# Check if citations are required
decision = engine.check_capability(context, CapabilityType.CITATIONS_REQUIRED)
print(f"Citations required: {decision.allowed}")
```

---

### 2. Access Control ([access_control.py](../src/core/access_control.py))

Pre-retrieval filtering to prevent data leakage:

```python
from src.core.access_control import AccessControlEngine, UserAttributes, ResourceAttributes

# Create access control engine
ac_engine = AccessControlEngine()

# Define user
user = UserAttributes(
    user_id="cs_agent_001",
    role=Role.CUSTOMER_SERVICE,
    business_domains={BusinessDomain.CUSTOMER_SERVICE},
    aircraft_types=set(AircraftType),
    bases={"AKL"},
    route_regions={"Domestic"},
    sensitivity_clearance=SensitivityLevel.INTERNAL,
    additional_attributes={}
)

# Define resource
resource = ResourceAttributes(
    resource_id="POL-001",
    resource_type="policy",
    business_domain=BusinessDomain.CUSTOMER_SERVICE,
    aircraft_types=set(AircraftType),
    applicable_bases={"AKL"},
    applicable_regions={"Domestic"},
    sensitivity_level=SensitivityLevel.INTERNAL,
    version="1.0",
    effective_date=datetime.now(),
    metadata={}
)

# Check access (BEFORE retrieval)
decision = ac_engine.check_access(user, resource, "read")
print(f"Access granted: {decision.allowed}")
```

---

### 3. Evidence Contract ([evidence_contract.py](../src/core/evidence_contract.py))

Verifiable citations with version tracking:

```python
from src.core.evidence_contract import EvidenceContractEnforcer, EvidencePackage, Citation

# Create enforcer
enforcer = EvidenceContractEnforcer()

# Create citation
citation = enforcer.create_citation_from_retrieval(
    document_id="POL-BAGGAGE-001",
    version="3.2",
    source_system=SourceSystem.POLICY_MANAGEMENT,
    evidence_type=EvidenceType.POLICY,
    excerpt="Economy passengers are entitled to 2 checked bags...",
    metadata={
        "title": "Baggage Policy",
        "paragraph_locator": "Section 2.1.3",
        "effective_date": datetime(2024, 1, 1)
    }
)

# Create evidence package
package = EvidencePackage(
    query="What is baggage allowance?",
    answer="Economy passengers can check 2 bags...",
    citations=[citation],
    retrieval_strategy="hybrid_rag",
    confidence_score=0.85,
    timestamp=datetime.now(),
    risk_tier="R1"
)

# Validate (R1 requires citations)
is_valid, errors = enforcer.validate_evidence_package(package, require_citations=True)
print(f"Evidence valid: {is_valid}")
```

---

### 4. Audit System ([audit_system.py](../src/core/audit_system.py))

Full traceability and replay:

```python
from src.core.audit_system import AuditSystem, AuditEventType

# Create audit system
audit = AuditSystem()

# Create trace
trace = audit.create_trace(
    trace_id="trace_001",
    session_id="session_001",
    user_id="user123",
    query="What is baggage policy?",
    risk_tier="R1",
    model_version="claude-sonnet-4.5",
    prompt_version="oscar_v1.0",
    retrieval_index_version="policies_v2.3",
    policy_version="1.0.0"
)

# Log events
audit.log_event(
    trace_id="trace_001",
    event_type=AuditEventType.REQUEST_RECEIVED,
    component="oscar_chatbot",
    action="query_received",
    status="success",
    details={"query": "What is baggage policy?"}
)

# Complete trace
audit.complete_trace(
    trace_id="trace_001",
    final_response="Economy passengers can check 2 bags...",
    status="completed"
)

# Replay trace
replay_result = audit.replay_trace("trace_001")
print(f"Replay successful: {replay_result['output_matched']}")
```

---

## Risk Tier Decision Tree

Use this to determine the appropriate risk tier for your use case:

```
Does it generate customer-facing content?
├─ YES → R1 (Citations required, no write ops)
└─ NO ↓

Does it support operational/safety decisions?
├─ YES → R2 (Human approval required, read-only tools)
└─ NO ↓

Does it perform automated actions?
├─ YES → R3 (Dual control, rollback required)
└─ NO → R0 (Low-risk internal productivity)
```

---

## Common Patterns

### Pattern 1: Evidence-backed Q&A (R1)

```python
1. Check policy gates (citations required?)
2. Check access control (can user see this data?)
3. Retrieve with pre-filtering
4. Create citations
5. Validate evidence
6. If valid → generate answer
7. If invalid → escalate to human
8. Log everything
```

### Pattern 2: Decision Support (R2)

```python
1. Check policy gates (human approval required?)
2. Gather real-time data via tools (read-only)
3. Retrieve procedures
4. Generate options with rationale
5. Create evidence package
6. Present to human for approval
7. Record approval decision
8. Log everything (replayable)
```

### Pattern 3: Automated Action (R3)

```python
1. Check policy gates (dual control? rollback?)
2. Validate parameters
3. Get JIT authorization
4. Execute with idempotency
5. Log action (immutable)
6. Enable rollback
7. Dual approval if needed
8. Monitor and alert
```

---

## Next Steps

1. **Read the governance criteria**: [GOVERNANCE_CRITERIA.md](GOVERNANCE_CRITERIA.md)
2. **Understand the architecture**: [README.md](../README.md)
3. **Explore the code**: Start with [oscar_chatbot.py](../src/agents/oscar_chatbot.py)
4. **Customize for your use case**: Create your own agent following the patterns

---

## Key Principles to Remember

1. **Platform First**: Build the governance platform, then attach agents
2. **No Evidence = No Answer**: R1-R3 require verifiable citations
3. **Pre-Retrieval Filtering**: Filter BEFORE fetching to prevent leaks
4. **Human in the Loop**: R2-R3 require human approval
5. **Everything is Traceable**: Every decision is logged and replayable
6. **Governance Enables**: Good governance accelerates safe delivery

---

## Getting Help

- Check the [docs/](../docs/) directory for detailed documentation
- Review the [examples/](../examples/) for working code
- Read the inline comments in the source code

## Production Deployment

This is a demo/reference implementation. For production:

1. Integrate actual LLM API (Claude, etc.)
2. Connect to real data sources
3. Implement actual tool integrations
4. Set up persistent storage (database, vector store)
5. Deploy with proper security (authentication, encryption)
6. Establish SLOs and monitoring
7. Create runbooks for incident response

**Remember**: The governance framework is the foundation. The specific agents (Oscar, disruption management, etc.) are just applications running on top of it.
