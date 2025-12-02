# Configuration & Deployment Guide

Complete guide to configure and deploy the Air NZ AI Governance Platform.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Database Setup](#database-setup)
4. [API Integration](#api-integration)
5. [Running the Platform](#running-the-platform)
6. [Production Deployment](#production-deployment)
7. [Monitoring & Operations](#monitoring--operations)

---

## Quick Start

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- SQLite3 (included with Python)

### Installation

```bash
# 1. Navigate to project directory
cd airnz-ai-governance

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Edit .env with your API keys (optional for demo)
nano .env  # or use your preferred editor
```

### Run Full Demo

```bash
python run_full_demo.py
```

This will demonstrate:
- All risk tiers (R0-R3)
- All governance controls (G1-G12)
- Database integration
- LLM integration
- Tool Gateway
- SLO monitoring
- Audit trail

---

## Configuration

### Environment Variables

Create a `.env` file with the following:

```bash
# OpenAI API (optional - will use mock mode if not provided)
OPENAI_API_KEY=sk-...

# AviationStack API (optional - will use database fallback)
AVIATIONSTACK_API_KEY=your_key_here

# Database
DATABASE_PATH=airnz.db

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Environment
ENV=development  # development, staging, production
```

### API Keys

#### OpenAI API

1. Sign up at https://platform.openai.com
2. Create API key at https://platform.openai.com/api-keys
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

**Note**: If not provided, platform runs in mock mode with simulated responses.

#### AviationStack API (Optional)

1. Sign up at https://aviationstack.com
2. Free tier: 100 requests/month
3. Add to `.env`: `AVIATIONSTACK_API_KEY=your_key`

**Note**: If not provided, falls back to local database for flight data.

---

## Database Setup

### Automatic Setup

The database is automatically created and populated on first run:

```python
from src.data.database import AirNZDatabase

db = AirNZDatabase("airnz.db")  # Creates and populates
```

### Manual Setup

```bash
# Initialize database manually
python -c "from src.data.database import AirNZDatabase; AirNZDatabase('airnz.db')"
```

### Database Schema

The SQLite database includes:

- `flights` - Flight operations data
- `aircraft` - Fleet information
- `crew` - Crew availability
- `gates` - Gate assignments
- `policies` - Policy documents
- `work_orders` - Maintenance work orders
- `users` - User accounts
- `audit_log` - Audit trail
- `system_metrics` - SLO metrics

### Database Inspection

```bash
# Open database
sqlite3 airnz.db

# List tables
.tables

# View flights
SELECT * FROM flights;

# View policies
SELECT document_id, title, version FROM policies;

# View audit log
SELECT * FROM audit_log LIMIT 10;

# Exit
.quit
```

---

## API Integration

### LLM Service Integration

The platform uses OpenAI by default but is designed to support multiple providers:

```python
from src.core.llm_service import LLMService

# Initialize
llm_service = LLMService(api_key="your_key")

# Or use environment variable
llm_service = LLMService()  # Reads OPENAI_API_KEY from env

# Generate
response = llm_service.generate(
    template_id="oscar_chatbot",
    template_version="1.0",
    variables={"query": "...", "evidence": "..."},
    model="gpt-3.5-turbo-0125"
)
```

**Supported Models**:
- gpt-3.5-turbo-0125 (fast, cheap - recommended for R0)
- gpt-4o-mini (balanced)
- gpt-4o (highest quality)

### Flight API Integration

```python
from src.integrations.flight_api import FlightAPIClient, MockFlightAPI

# With API key
flight_api = FlightAPIClient(api_key="your_key", database=db)

# Mock mode (for testing)
flight_api = MockFlightAPI(database=db)

# Get flight status
status = flight_api.get_flight_status("NZ1")
```

---

## Running the Platform

### Individual Agents

#### R0: Code Assistant

```python
from src.agents.code_assistant import CodeAssistantAgent
from src.core.llm_service import LLMService
from src.core.audit_system import AuditSystem

llm_service = LLMService()
audit_system = AuditSystem()

agent = CodeAssistantAgent(llm_service, audit_system)

response = agent.assist(
    query="How do I implement a binary search?",
    user_id="dev_001",
    session_id="session_123"
)
```

#### R1: Oscar Chatbot

```python
from src.agents.oscar_chatbot import OscarChatbot

oscar = OscarChatbot()

response = oscar.process_query(
    query="What is the baggage allowance?",
    user_id="cs_agent_001",
    session_id="session_456"
)
```

#### R2: Disruption Management

```python
from src.agents.disruption_management import DisruptionManagementAgent
from src.core.tool_gateway import ToolGateway

tool_gateway = ToolGateway(database=db)
agent = DisruptionManagementAgent(tool_gateway, audit_system)

response = agent.analyze_disruption(
    disruption_context={
        "flight_number": "NZ1",
        "issue": "Maintenance delay",
        ...
    },
    user_id="dispatcher_001",
    session_id="session_789"
)

# Approve decision
agent.record_approval_decision(
    trace_id=response['metadata']['trace_id'],
    option_id="OPT-1",
    approved=True,
    approver_id="manager_001"
)
```

#### R3: Maintenance Automation

```python
from src.agents.maintenance_automation import MaintenanceAutomationAgent

agent = MaintenanceAutomationAgent(tool_gateway, audit_system)

# Request work order creation
response = agent.create_work_order(
    work_order_data={
        "aircraft_registration": "ZK-NZB",
        "work_type": "preventive",
        "priority": "medium",
        "description": "Scheduled inspection..."
    },
    user_id="engineer_001",
    session_id="session_abc"
)

# Dual approval (R3 requirement)
agent.approve_work_order(
    approval_request_id=response['approval_request_id'],
    approver_id="engineer_senior_001",
    approved=True
)

agent.approve_work_order(
    approval_request_id=response['approval_request_id'],
    approver_id="manager_001",
    approved=True
)
```

### SLO Monitoring

```python
from src.monitoring.slo_monitor import SLOMonitor

monitor = SLOMonitor()

# Measure SLO
measurement = monitor.measure_slo(
    slo_id="latency_r1_p95",
    data_points=[
        {"latency_ms": 1200},
        {"latency_ms": 1500},
        ...
    ]
)

# Generate report
report = monitor.get_slo_report(hours=24)
print(f"Overall Status: {report['overall_status']}")
```

---

## Production Deployment

### Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Python 3.9+
- PostgreSQL (recommended for production instead of SQLite)
- Redis (for caching and rate limiting)
- Nginx (reverse proxy)
- Systemd (process management)

### Migration to PostgreSQL

For production, migrate from SQLite to PostgreSQL:

```python
# 1. Install psycopg2
pip install psycopg2-binary

# 2. Update database.py to use PostgreSQL
# (requires code changes - see production guide)

# 3. Create PostgreSQL database
sudo -u postgres createdb airnz_governance

# 4. Run migrations
python scripts/migrate_to_postgres.py
```

### Systemd Service

Create `/etc/systemd/system/airnz-governance.service`:

```ini
[Unit]
Description=Air NZ AI Governance Platform
After=network.target

[Service]
Type=simple
User=airnz
WorkingDirectory=/opt/airnz-governance
Environment="OPENAI_API_KEY=sk-..."
ExecStart=/opt/airnz-governance/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable airnz-governance
sudo systemctl start airnz-governance
sudo systemctl status airnz-governance
```

### Nginx Configuration

Create `/etc/nginx/sites-available/airnz-governance`:

```nginx
server {
    listen 80;
    server_name ai-governance.airnz.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/airnz-governance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY run_full_demo.py .

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
```

Build and run:

```bash
docker build -t airnz-governance .
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  airnz-governance
```

---

## Monitoring & Operations

### Health Checks

```python
# Check database
db.conn.execute("SELECT 1").fetchone()

# Check LLM service
llm_service.generate(template_id="test", template_version="1.0", ...)

# Check tool gateway
tool_metrics = tool_gateway.get_tool_metrics()
```

### Logging

Logs are written to:
- Console (development)
- File: `/var/log/airnz-governance/app.log` (production)
- Structured JSON format for production

View logs:

```bash
# Systemd logs
sudo journalctl -u airnz-governance -f

# File logs
tail -f /var/log/airnz-governance/app.log
```

### SLO Dashboards

Access SLO dashboard:

```python
from src.monitoring.slo_monitor import SLOMonitor

monitor = SLOMonitor()
report = monitor.get_slo_report(hours=24)

# Export to JSON for dashboards
import json
print(json.dumps(report, indent=2))
```

### Incident Response

Follow runbooks in [INCIDENT_RESPONSE_RUNBOOKS.md](INCIDENT_RESPONSE_RUNBOOKS.md).

Quick shutdown:

```python
from src.core.policy_engine import PolicyEngine, RiskTier, CapabilityType

engine = PolicyEngine()

# Emergency kill switch
for tier in [RiskTier.R0, RiskTier.R1, RiskTier.R2, RiskTier.R3]:
    policy = engine.active_policies[tier]
    policy.blocked_capabilities = set(CapabilityType)
    policy.allowed_capabilities = set()
```

### Backup & Recovery

```bash
# Backup database
cp airnz.db airnz_backup_$(date +%Y%m%d_%H%M%S).db

# Backup audit logs
python scripts/export_audit_logs.py > audit_backup_$(date +%Y%m%d).json

# Restore from backup
cp airnz_backup_20241202_143000.db airnz.db
```

### Performance Tuning

1. **Database**:
   - Enable WAL mode: `PRAGMA journal_mode=WAL;`
   - Add indexes on frequently queried columns
   - Monitor slow queries

2. **LLM**:
   - Use gpt-3.5-turbo-0125 for R0 (faster, cheaper)
   - Cache frequent queries
   - Implement rate limiting

3. **Tool Gateway**:
   - Enable result caching
   - Use connection pooling
   - Monitor rate limits

---

## Troubleshooting

### Common Issues

**Problem**: Database locked errors

**Solution**:
```python
# Enable WAL mode
db.conn.execute("PRAGMA journal_mode=WAL")
```

**Problem**: OpenAI API rate limits

**Solution**:
```python
# Implement exponential backoff
# Or use mock mode temporarily
llm_service.mock_mode = True
```

**Problem**: High latency on R2 queries

**Solution**:
- Check tool gateway metrics
- Review database query performance
- Enable caching for policies

---

## Security Checklist

- [ ] Change default database path
- [ ] Rotate API keys regularly
- [ ] Enable HTTPS in production
- [ ] Implement authentication/authorization
- [ ] Set up firewall rules
- [ ] Enable audit logging
- [ ] Regular security scans
- [ ] Backup encryption
- [ ] Monitor for anomalies

---

## Support & Resources

- **Documentation**: [docs/](../docs/)
- **Governance Criteria**: [GOVERNANCE_CRITERIA.md](GOVERNANCE_CRITERIA.md)
- **Incident Runbooks**: [INCIDENT_RESPONSE_RUNBOOKS.md](INCIDENT_RESPONSE_RUNBOOKS.md)
- **Quick Start**: [QUICK_START.md](QUICK_START.md)

---

## Next Steps

1. ✅ Run the full demo
2. ✅ Review governance criteria
3. ✅ Understand incident runbooks
4. Configure for your environment
5. Customize agents for your use cases
6. Deploy to staging
7. Conduct security review
8. Deploy to production
9. Monitor SLOs
10. Iterate and improve
