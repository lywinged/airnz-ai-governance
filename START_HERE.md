# 🚀 START HERE - Air NZ AI Governance Platform

Welcome! This is a fully runnable AI governance platform demo.

## ✅ System Highlights

### End-to-end coverage - real running code, not just docs
- ✓ **All risk tiers R0-R3** (4 live agents)
- ✓ **All governance standards G1-G12** ⭐ **each implemented in code**
  - G1: four complete safety cases (safety_case.py)
  - G8: evaluation system with red teaming (evaluation_system.py)
  - G11: circuit breaker and kill switches (reliability.py)
  - G12: governance dashboard and scoring (dashboard.py)
- ✓ **Core 6 controls** (all included)
- ✓ **Real database** (SQLite)
- ✓ **Real LLM integration** (OpenAI + mock mode)
- ✓ **Real Flight API** (AviationStack + database fallback)
- ✓ **Full audit trail** (replayable)
- ✓ **SLO monitoring** (12 SLOs)
- ✓ **Incident response runbooks** (8 runbooks)

### Key Principles
🎯 **All data flows through the AI platform** - every access passes governance controls  
🔍 **Fully traceable** - every interaction has a complete audit chain  
🔄 **Replayable** - any trace can be reproduced  
🛡️ **Safety controls** - access control, rate limits, dual approvals, rollback capability

## 🏃 Quick Start (3 steps)

### 1. Install dependencies

```bash
cd airnz-ai-governance
pip install -r requirements.txt
```

### 2. Configure (optional)

```bash
# Copy the config template
cp .env.example .env

# Edit .env to add API keys (optional)
# OPENAI_API_KEY=sk-...
# AVIATIONSTACK_API_KEY=...
```

**Note:** It also runs without keys; mock mode will be used.

### 3. Run the full demo

```bash
python run_full_demo.py
```

## 🔌 API Modes (real vs mock)

- **LLM (OpenAI)**: set `OPENAI_API_KEY` to use real OpenAI calls; otherwise it stays in mock mode.
- **Flight data (AviationStack)**: set `AVIATIONSTACK_API_KEY` to fetch live flight status; otherwise R2 uses SQLite/mock data.
- No extra flags needed — the demo and CLI examples auto-detect these env vars and print whether real or mock mode is active.

## 📋 What the demo shows

Running `run_full_demo.py` will show:

### DEMO 1: R0 - Code Assistant
- **Risk level**: R0 (internal productivity)
- **Governance**: minimal governance overhead, fast response
- **Shows**: developer code assistant with internet access

### DEMO 2: R1 - Oscar Chatbot
- **Risk level**: R1 (customer-facing)
- **Governance**: enforced citations, evidence validation
- **Shows**: customer service chatbot with verifiable citations

### DEMO 3: R2 - Disruption Management
- **Risk level**: R2 (operations decision support)
- **Governance**: mandatory human approval, tool RAG
- **Shows**: flight disruption recovery suggestions, requires human approval

### DEMO 4: R3 - Maintenance Automation
- **Risk level**: R3 (automated operations)
- **Governance**: write operations, dual control, rollback capability
- **Shows**: auto-create work orders, dual approvals, rollback

### DEMO 5: SLO Monitoring
- **Shows**: real-time monitoring of 12 SLOs
- **Metrics**: availability, latency, error rate, citation coverage, tool success rate

### DEMO 6: Audit & Governance
- **Shows**: full audit trail
- **Features**: end-to-end traceability, replay capability, governance metrics

## 📜 Examples (CLI)

- R1 Oscar Chatbot: `python3 examples/run_oscar_chatbot.py`
- R2 Disruption Management: `python3 examples/run_disruption_management.py` (mock by default; uses real APIs if keys are set)

## 📁 Project Structure

```
airnz-ai-governance/
├── run_full_demo.py           # ⭐ Main demo script (start here)
├── src/
│   ├── core/                  # 6 core governance components
│   │   ├── policy_engine.py       # R0-R3 risk tiers
│   │   ├── access_control.py      # RBAC/ABAC access control
│   │   ├── evidence_contract.py   # Verifiable citations
│   │   ├── retrieval_router.py    # Multi-strategy RAG routing
│   │   ├── privacy_control.py     # Privacy protection (NZ Privacy Act)
│   │   ├── audit_system.py        # Audit system (replayable)
│   │   ├── tool_gateway.py        # Tool safety gateway
│   │   └── llm_service.py         # LLM service (OpenAI)
│   ├── data/
│   │   └── database.py        # SQLite database
│   ├── agents/                # 4 AI agents (R0-R3)
│   │   ├── code_assistant.py      # R0
│   │   ├── oscar_chatbot.py       # R1
│   │   ├── disruption_management.py  # R2
│   │   └── maintenance_automation.py # R3
│   ├── integrations/
│   │   └── flight_api.py      # Flight API integration
│   └── monitoring/
│       └── slo_monitor.py     # SLO monitoring
├── docs/                      # Full documentation
│   ├── QUICK_START.md
│   ├── GOVERNANCE_CRITERIA.md     # G1-G12 deep dive
│   ├── INCIDENT_RESPONSE_RUNBOOKS.md  # Ops runbooks
│   └── CONFIGURATION_DEPLOYMENT.md    # Deployment guide
└── .env.example               # Config template
```

## 🎯 Feature Coverage

### R0-R3 coverage ✓
- R0: Code assistant (minimal governance)
- R1: Oscar chatbot (mandatory citations)
- R2: Disruption management (human approval)
- R3: Maintenance automation (dual control + rollback)

### G1-G12 coverage ✓
- G1: AI safety cases - risk assessment for each use case
- G2: Risk tiering - dynamic gates for R0-R3
- G3: Evidence contract - verifiable citations (version + hash)
- G4: Permission layer - RBAC/ABAC filtering before retrieval
- G5: Tool safety gate - read/write isolation, rate limits, rollback
- G6: Version control - tracking models/prompts/policies
- G7: Observability - end-to-end tracing + replay
- G8: Evaluation system - SLO monitoring + metrics tracking
- G9: Data governance - privacy controls + retention policy
- G10: Domain isolation - business domain access control
- G11: Reliability engineering - fallback modes + circuit breakers
- G12: Governance as product - policy-as-code + audit dashboard

### Core 6 coverage ✓
1. Policy Engine - policy engine
2. Access Control - access control
3. Evidence Contract - evidence contract
4. Retrieval Router - retrieval routing
5. Privacy Control - privacy control
6. Audit System - audit system

### Data source integration ✓
- SQLite database (flights, aircraft, crew, policies, work orders)
- OpenAI API (LLM service)
- Flight API (real-time flight data)

### Safety controls ✓
- Pre-retrieval access control (prevent data leakage)
- Rate limits (prevent abuse)
- Idempotency control (prevent duplicate operations)
- Dual approval (required for R3)
- Rollback capability (required for R3)
- Full audit log (immutable)

## 📚 Next steps

1. **Run the demo**: `python run_full_demo.py`
2. **Implementation summary**: [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - ⭐ **G1-G12 implementation confirmation**
3. **Read the docs**:
   - [QUICK_START.md](docs/QUICK_START.md) - 5-minute intro
   - [GOVERNANCE_CRITERIA.md](docs/GOVERNANCE_CRITERIA.md) - G1-G12 details
   - [INCIDENT_RESPONSE_RUNBOOKS.md](docs/INCIDENT_RESPONSE_RUNBOOKS.md) - Ops runbooks
4. **Configure APIs**: edit `.env` to add OpenAI and Flight API keys (optional)
5. **Customize**: adapt agents to your use cases
6. **Deploy**: see [CONFIGURATION_DEPLOYMENT.md](docs/CONFIGURATION_DEPLOYMENT.md)

## ❓ FAQ

**Q: Can it run without API keys?**  
A: Yes! It will automatically switch to mock mode with simulated data.

**Q: Where is the database?**  
A: The SQLite file `airnz_demo.db` is created automatically on first run.

**Q: How do I view audit logs?**  
A: After running the demo, audit logs are stored in the `audit_log` table in the database.

**Q: Is this production-ready?**  
A: This is a demo. For production you need to:
- Migrate to PostgreSQL
- Add authentication/authorization
- Deploy to servers
- Set up monitoring and alerting
- See [CONFIGURATION_DEPLOYMENT.md](docs/CONFIGURATION_DEPLOYMENT.md)

## 🔗 Links

- OpenAI API: https://platform.openai.com/api-keys
- AviationStack API: https://aviationstack.com/ (free 100 calls/month)
- NZ Privacy Act: https://www.privacy.org.nz/

## 📧 支持

查看项目文档或提issue。

---

**准备好了吗？运行这个命令开始：**

```bash
python run_full_demo.py
```

🎉 享受完整的AI治理平台演示！
