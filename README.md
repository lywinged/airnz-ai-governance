
# The Risks of using Companion AI + Custom GPTs:
1) Permission & data leakage ambiguity
* Users often confuse “I can access it” with “I can paste it into a GPT,” risking PII/sensitive ops data exposure and unclear retention/spread. This habit increases the risk that users, when using personal GPTs, may accidentally upload sensitive company content due to misoperation.

2) Sprawl & duplication
* Team-made GPTs quickly explode (1000+): duplicate functions, messy naming, no ownership, and the best ones get buried.

3) Quality drift & inconsistency
*  Model updates, source changes, or prompt tweaks cause drift; without regression tests you can’t prove changes didn’t break behavior.

4) No verifiable evidence/citations
* Many GPTs produce “citations” that aren’t verifiable; enterprises can’t validate existence/version/applicability, making audits painful.

5) No routing; guessing instead of authoritative truth
*  For truth queries (flight status, work orders, inventory), custom GPTs may guess from static info instead of forcing authoritative tools.

6) Inconsistent tool access; no action gates
*  Even with tools, lacks gateway controls (validation/rate limits/idempotency/approvals/rollback); enabling writes becomes high-risk fast.

7) Non-operational governance: low visibility
* Hard to answer “who uses which GPT, what they ask, where the risks are, and who burns the cost.”

8) Hard to standardize workflows
*  Custom GPTs are great conversationally, but enterprises need repeatable workflow templates: structured inputs, steps, approvals, outputs, storage, and tracking.

9) Compliance not enforced as controls
*  Compliance is often left to training instead of system controls: purpose limitation, retention/deletion, access/correction requests, cross-border constraints.

10) Poor incident forensics: no replay/evidence chain
*  When incidents happen, you can’t replay the exact configuration nor provide a complete evidence chain.



# The Risks of building AI agents or Agent-flow without AI governance:
The risk is similar to above,

1) Data leakage & privilege violations
*  Employees may paste PII, PNR/booking details, internal operational data, or manual excerpts into Copilot/agents. Without data classification and pre-retrieval ABAC, you can’t guarantee “only retrieve what the user is allowed to access” or “only output what is safe to disclose.”

2) “Truth” questions get guessed instead of verified
*  Flight status, disruption details, baggage tracking, work-order status, etc. must come from authoritative systems. Without Tool-RAG enforcement and hard routing rules, agents will guess from static docs or hallucinate—misleading customers and operations.

3) Unverifiable evidence → audit failure
*  Without an Evidence Contract (doc_id, version, effective date, locator, content hash), you cannot prove which version of a policy/manual a response relied on. That makes SMS-aligned assurance, internal audit, and external audit extremely difficult.

4) Uncontrolled change & drift
*  Model updates, prompt edits, workflow tweaks in n8n, and knowledge-base refreshes cause behavior drift. Without regression evaluation and release gating, breakages are discovered in production—classic “slow-burn” incidents.

5) No clear boundaries → misuse in R2/R3 scenarios
*  Assistants meant for R0/R1 quickly get used for ops/engineering decision support (R2) or even automated actions (R3). Without risk-tiering and dynamic gates, “adding one tool” can turn an assistant into a high-risk system overnight.

6) Tools without safety gates
*  LangGraph/n8n makes internal API integration easy, but typically lacks: parameter validation, allowlists, rate limits, idempotency, rollback, JIT authorization, and dual control. The risk rises sharply the moment write actions (tickets/permissions/config changes) are enabled.

7) Low observability & weak accountability
*  You won’t be able to answer: who asked what, what data was retrieved, which tools were called, what was sent to whom, where the costs went, and how often risky events occur. Without unified trace + audit, the system isn’t operable.

8) Poor incident forensics (no replay)
*  When a complaint or investigation happens, you can’t reproduce outputs using the same model/prompt/index/tool versions, and you can’t produce a complete evidence chain—undermining root-cause analysis.

9) Fragmentation across teams (“AI shadow IT”)
*  Different teams build their own Copilot setups, n8n flows, prompt libraries, vector stores, and tool connectors. This leads to duplication, inconsistent standards, uncontrolled costs, and a growing “shadow IT” footprint.

10) Compliance becomes training, not enforcement
*  Critical requirements become “user training” rather than system controls: purpose limitation, retention/deletion, cross-border restrictions, access/correction requests, breach handling—hard to close the loop.

11) Misalignment with SMS risk management
*  SMS expects a hazard → risk → control → assurance loop. Without a governance platform, you cannot clearly show where controls exist, whether they work, or whether residual risk remains acceptable.

12) Business risk: cost is uncontrolled, ROI is unprovable
*  Without unified metrics (quality/risk/cost) and an A/B feedback loop, leadership can’t see what creates value vs. risk—often ending in a blanket shutdown.


# Air NZ AI Governance Platform Demo

A compliance-grade AI governance platform implementing the 12 governance criteria (G1-G12) across risk tiers R0-R3 with live, runnable code.

## Quick Start (3 steps)

```bash
cd airnz-ai-governance
pip install -r requirements.txt

# optional: configure API keys (mock mode works without keys)
cp .env.example .env
# OPENAI_API_KEY=sk-...
# AVIATIONSTACK_API_KEY=...

python run_full_demo.py
```

## API Modes (real vs mock)

- **LLM (OpenAI)**: set `OPENAI_API_KEY` to use real OpenAI calls; otherwise the platform runs in mock mode.
- **Flight data (AviationStack)**: set `AVIATIONSTACK_API_KEY` to fetch live flight status; otherwise the R2 flow/examples use SQLite/mock data.
- No extra flags needed — the demo and CLI examples auto-detect these env vars and print whether real or mock mode is active.

## What the demo shows

- **DEMO 1: R0 Code Assistant** — internal productivity, minimal governance, internet allowed
- **DEMO 2: R1 Oscar Chatbot** — customer-facing, citations required, evidence validation
- **DEMO 3: R2 Disruption Management** — ops decision support, mandatory human approval
- **DEMO 4: R3 Maintenance Automation** — write operations, dual control, rollback
- **DEMO 5: SLO Monitoring** — 12 SLOs: availability, latency, errors, citation coverage, tool success
- **DEMO 6: Audit & Governance** — full audit trail, replayable traces, governance metrics

## Examples (CLI)

- R1 Oscar Chatbot: `python3 examples/run_oscar_chatbot.py`
- R2 Disruption Management: `python3 examples/run_disruption_management.py` (uses mock data by default; real APIs if keys are set)

## Risk Tiers

- **R0**: Low-risk internal productivity (writing, coding assistance)
- **R1**: External/customer-facing (Oscar chatbot, policy clarification)
- **R2**: Operations/maintenance decision support (human-in-the-loop mandatory)
- **R3**: Actions & closed loops (write operations, dual control required)

## Key Features (G1-G12)

- **G1: AI Safety-Case** — per-use-case assurance: hazards, risk assessment, controls.
- **G2: Risk Tiering + Dynamic Gates** — runtime gates for internet/tools/write/citations/approvals.
- **G3: Evidence Contract** — citations carry doc ID, version, effective date, applicability, source, paragraph locator.
- **G4: Permission Layers** — pre-retrieval RBAC/ABAC filtering by role, aircraft type, base, business domain.
- **G5: Tool/Action Safety Gates** — unified gateway with validation, rate limits, idempotency, rollback.
- **G6: Prompt/Policy/Model Versioning** — change control with versioning, approvals, canary, rollback.
- **G7: Full-chain Observability + Replayability** — deterministic replays with model/prompt/index/tool inputs logged.
- **G8: Evaluation System** — offline golden sets/regression; online metrics (citation coverage, hallucination, tool success); red-team (prompt injection, privilege escalation, data leaks).
- **G9: Data Governance** — versioning, retention, minimization, deletion, cross-border controls aligned to NZ Privacy Act.
- **G10: Tenant/Domain Isolation** — ops, engineering, customer service, HR, finance, safety domains isolated.
- **G11: Reliability Engineering** — SLOs, graceful degradation, circuit breakers, kill switches.
- **G12: Governance as a Product** — policy-as-code, audit dashboards, approval workflows, data-source health monitoring.

## G1–G12 → Code Mapping

- **G1 – Safety Cases**: `src/governance/safety_case.py` (`SafetyCase`, `SafetyCaseRegistry` for R0–R3).
- **G2 – Risk Tiering**: `src/core/policy_engine.py` (`RiskTier`, `PolicyEngine`, tier gates R0–R3).
- **G3 – Evidence Contract**: `src/core/evidence_contract.py` (`Citation`, `EvidenceContractEnforcer`).
- **G4 – Permission Layers**: `src/core/access_control.py` (`AccessControlEngine`, `BusinessDomain`, RBAC/ABAC).
- **G5 – Tool Safety Gates**: `src/core/tool_gateway.py` (`ToolGateway`, read/write isolation, rate limiting, rollback).
- **G6 – Versioning**: `src/core/llm_service.py` (model & prompt templates) + `policy_engine.py` (policy versions).
- **G7 – Observability & Replay**: `src/core/audit_system.py` (`AuditSystem`, traces + events + replay).
- **G8 – Evaluation System**: `src/governance/evaluation_system.py` (golden sets, regression, red team).
- **G9 – Privacy Control**: `src/core/privacy_control.py` (`PrivacyController`, NZ Privacy Act alignment).
- **G10 – Domain Isolation**: `src/core/access_control.py` (domain-scoped access via `BusinessDomain` etc.).
- **G11 – Reliability Engineering**: `src/governance/reliability.py` (`ReliabilityEngineer`, circuit breakers, kill switches).
- **G12 – Governance as Product**: `src/governance/dashboard.py` (`GovernanceDashboard`) + `src/monitoring/slo_monitor.py` (SLOs).

## Diagrams (Mermaid)

- Execution flows are in `docs/diagrams/*.md` / `*.mmd` (e.g., `flow_r1_oscar_chatbot.md`, `flow_r2_disruption_management.mmd`).
- View in VS Code: open the file and use Markdown preview (`⌘K V` / `⌘Shift+V`) with Mermaid support.
- CLI render: `npx @mermaid-js/mermaid-cli -i docs/diagrams/flow_r2_disruption_management.mmd -o /tmp/flow.svg`.
- For `.mmd` files, wrap content in ```mermaid code fences or use Markdown mode to render.

- What each diagram shows:
  - `docs/diagrams/flow_r1_oscar_chatbot.md`: R1 Oscar chatbot flow with evidence contract, citations, and audit.
  - `docs/diagrams/flow_r2_disruption_management.mmd`: R2 disruption management flow with safety case, tool gateway, and mandatory human approval.
  - `docs/diagrams/flow_r3_maintenance_automation.md` / `.mmd`: R3 maintenance automation with dual approval and rollback path.
  - `docs/EXECUTION_FLOWS_EN.md`: English overview linking the flows across agents and governance controls.
  - `docs/EXECUTION_FLOWS_CN.md`: 中文版执行流程概览，对应 EN 版的图文说明。

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Applications                       │
│  (Code Assistant, Oscar Chatbot, Disruption Mgmt, R3 Ops)    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│              AI Governance Platform (Core)                   │
├──────────────────────────────────────────────────────────────┤
│  1. Policy Engine (R0-R3 Risk Tiers)                        │
│  2. Identity & Access (RBAC/ABAC + Domain Isolation)        │
│  3. Evidence Contract (Verifiable Citations)                │
│  4. Retrieval Router (Multi-strategy RAG)                   │
│  5. Privacy & Data Protection (NZ Privacy Act)              │
│  6. Observability + Audit + Replay                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│              External Systems & Data Sources                 │
│  (Flight Status, Policies, Manuals, Work Orders, etc.)      │
└──────────────────────────────────────────────────────────────┘
```

## Feature Coverage

- **R0-R3 coverage**: R0 (code assistant), R1 (Oscar chatbot), R2 (disruption management with human approval), R3 (maintenance automation with dual control + rollback)
- **G1-G12 coverage**:
  - G1: AI safety cases and risk assessments
  - G2: Risk tiering with dynamic gates
  - G3: Evidence contract with version/hash citations
  - G4: Permission layers (RBAC/ABAC, domain isolation)
  - G5: Tool safety gates (read/write isolation, rate limits, rollback)
  - G6: Version control for models/prompts/policies
  - G7: Observability with full replay
  - G8: Evaluation system (SLOs, metrics, red teaming)
  - G9: Data governance (privacy controls, retention)
  - G10: Domain isolation (ops/eng/cust svc/etc.)
  - G11: Reliability engineering (fallbacks, circuit breakers, kill switches)
  - G12: Governance as product (policy-as-code, dashboard)
- **Core 6**: policy engine, access control, evidence contract, retrieval router, privacy control, audit system

## Project Structure

```
airnz-ai-governance/
├── run_full_demo.py           # Main demo entrypoint
├── verify_g1_g12.py           # Governance criteria verifier
├── src/
│   ├── core/                  # Core governance components
│   │   ├── policy_engine.py
│   │   ├── access_control.py
│   │   ├── evidence_contract.py
│   │   ├── retrieval_router.py
│   │   ├── privacy_control.py
│   │   ├── audit_system.py
│   │   ├── tool_gateway.py
│   │   └── llm_service.py
│   ├── agents/                # 4 agents (R0-R3)
│   │   ├── code_assistant.py
│   │   ├── oscar_chatbot.py
│   │   ├── disruption_management.py
│   │   └── maintenance_automation.py
│   ├── data/                  # SQLite database
│   │   └── database.py
│   ├── integrations/          # External APIs
│   │   └── flight_api.py
│   ├── governance/            # G1/G8/G11/G12 implementations
│   │   ├── safety_case.py
│   │   ├── evaluation_system.py
│   │   ├── reliability.py
│   │   └── dashboard.py
│   └── monitoring/
│       └── slo_monitor.py
├── docs/                      # Full documentation
│   ├── QUICK_START.md
│   ├── GOVERNANCE_CRITERIA.md
│   ├── INCIDENT_RESPONSE_RUNBOOKS.md
│   ├── CONFIGURATION_DEPLOYMENT.md
│   ├── EXECUTION_FLOWS_EN.md
│   └── diagrams/
├── airnz.png                  # init MindMap
├── START_HERE.md              # Friendly intro
├── IMPLEMENTATION_COMPLETE.md # G1-G12 implementation confirmation
└── requirements.txt
```

## Key Capabilities

- **All data through governed platform**: every access is gated, logged, and traceable.
- **Full traceability & replay**: unique trace IDs, deterministic replays, immutable audit log.
- **Real integrations**: OpenAI API (or mock), AviationStack flight API (or DB fallback), SQLite data.
- **Safety controls**: rate limits, idempotency, dual approval (R3), rollback capability.
- **Monitoring & ops**: 12 SLOs, incident runbooks, tool gateway metrics, kill switch and circuit breakers.

## Documentation

- Quick start: `docs/QUICK_START.md`
- Governance criteria: `docs/GOVERNANCE_CRITERIA.md`
- Execution flows: `docs/EXECUTION_FLOWS_EN.md` (diagrams in `docs/diagrams/`)
- Incident runbooks: `docs/INCIDENT_RESPONSE_RUNBOOKS.md`
- Deployment/config: `docs/CONFIGURATION_DEPLOYMENT.md`
- Implementation proof: `IMPLEMENTATION_COMPLETE.md`

## FAQ

- **Can it run without API keys?** Yes. It auto-switches to mock mode if keys are missing.
- **Where is the database?** `airnz_demo.db` is created on first run (SQLite).
- **How to view audit logs?** After running the demo, inspect the `audit_log` table in the DB.
- **Is it production-ready?** This is a demo. For production: move to PostgreSQL, add authN/Z, deploy to servers, add monitoring/alerting, follow `docs/CONFIGURATION_DEPLOYMENT.md`.

## Next Steps

1. Run `python run_full_demo.py` to see all demos.
2. Explore `START_HERE.md` for a guided tour.
3. Read `docs/GOVERNANCE_CRITERIA.md` to map controls to code.
4. Customize agents or policies for your scenarios, then rerun the demo.
