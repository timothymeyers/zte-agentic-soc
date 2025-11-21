# Quickstart: Agentic SOC MVP

**Version**: 1.0.0  
**Last Updated**: 2025-11-21  
**Estimated Setup Time**: 30-45 minutes

This guide walks you through setting up and running the Agentic SOC MVP on your local development environment or Azure.

---

## Prerequisites

### Required Software

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Azure CLI 2.50+** ([Install](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))
- **Git** ([Download](https://git-scm.com/downloads))
- **VS Code** (recommended) with Python extension

### Azure Resources (for deployment)

- **Azure Subscription** with contributor access
- **Azure AI Foundry** workspace
- **Azure Cosmos DB** account
- **Azure Event Hubs** namespace
- **Application Insights** instance

### Authentication

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "<your-subscription-id>"
```

---

## Quick Start (Local Development)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/zte-agentic-soc.git
cd zte-agentic-soc
```

### 2. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file in project root:

```bash
# Azure AI Foundry
AZURE_AI_PROJECT_ENDPOINT="https://<your-project>.services.ai.azure.com/api/projects/<project-id>"
AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"

# Azure Cosmos DB
COSMOS_DB_ENDPOINT="https://<your-account>.documents.azure.com:443/"
COSMOS_DB_KEY="<your-key>"
COSMOS_DB_DATABASE_NAME="agentic-soc"

# Azure Event Hubs
EVENT_HUB_CONNECTION_STRING="Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=..."
ALERT_INGESTION_EVENT_HUB="alert-ingestion"

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=<key>;IngestionEndpoint=..."

# Mock Data Configuration
MOCK_DATA_ENABLED="true"
MOCK_DATA_STREAM_INTERVAL_SECONDS="15"
MOCK_DATA_CHECKPOINT_FILE="/tmp/mock_data_checkpoint.json"
```

### 4. Initialize Database

```bash
# Run database setup script
python utils/setup_cosmos_db.py
```

This creates the required Cosmos DB collections:
- `alerts`
- `incidents`
- `triage_results`
- `response_actions`
- `agent_state`
- `audit_logs`

### 5. Start Mock Data Stream

```bash
# In a separate terminal
python src/mock/stream.py
```

This starts streaming mock alerts from the GUIDE dataset every 15 seconds (configurable).

### 6. Start the Orchestrator

```bash
# Run the main orchestrator
python src/orchestration/orchestrator.py
```

You should see:

```
[2025-11-21 10:30:00] INFO: Orchestrator starting...
[2025-11-21 10:30:01] INFO: Connected to Cosmos DB
[2025-11-21 10:30:02] INFO: Alert Triage Agent initialized
[2025-11-21 10:30:03] INFO: Listening for events on Event Hubs...
[2025-11-21 10:30:15] INFO: Alert received: SystemAlertId=<uuid>
[2025-11-21 10:30:16] INFO: Triage completed: RiskScore=85, Priority=High
```

### 7. Start the API Server (Optional - for human interaction)

```bash
# In another terminal
python src/api/main.py
```

API available at: `http://localhost:8000`

Swagger UI: `http://localhost:8000/docs`

---

## Demo Scenarios

### Scenario 1: Basic Alert Triage

**Goal**: Demonstrate automated alert triage and risk scoring

1. **Trigger**: Mock data stream sends alert
2. **Expected Flow**:
   - Alert ingested via Event Hubs
   - Triage Agent analyzes alert
   - Risk score calculated (0-100)
   - Triage decision made (Escalate/Correlate/FalsePositive)
   - Incident created if risk score > 70
3. **Validation**:
   ```bash
   # Check triage results in Cosmos DB
   python utils/query_cosmos.py --collection triage_results --limit 10
   ```

### Scenario 2: Incident Correlation

**Goal**: Show multiple alerts being correlated into a single incident

1. **Setup**: Ensure mock data includes related alerts (same user, same attack pattern)
2. **Expected Flow**:
   - Alert 1: Failed login attempt → Risk Score 40 (Low)
   - Alert 2: Multiple failed logins → Risk Score 65 (Medium)
   - Alert 3: Successful login from unusual location → Risk Score 90 (High)
   - **Correlation**: All three alerts grouped into one incident
3. **Validation**:
   ```bash
   # Query incident with correlated alerts
   python utils/query_cosmos.py --collection incidents --filter "AlertIds.length > 1"
   ```

### Scenario 3: Interactive Threat Hunting

**Goal**: Natural language hunting query execution

1. **Submit Query** (via API):
   ```bash
   curl -X POST http://localhost:8000/api/v1/hunting/queries \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Show me all failed login attempts from external IPs in the last 24 hours",
       "analyst": "analyst@example.com"
     }'
   ```

2. **Expected Flow**:
   - Hunting Agent receives natural language query
   - GPT-4 translates to KQL
   - Query executed against mock dataset
   - Findings returned with anomaly scores

3. **Check Results**:
   ```bash
   curl http://localhost:8000/api/v1/hunting/queries/<query-id>
   ```

### Scenario 4: Containment Action with Approval

**Goal**: Demonstrate human-in-the-loop approval for high-risk actions

1. **Trigger**: High-severity incident (e.g., ransomware detected)
2. **Expected Flow**:
   - Incident Response Agent recommends isolating endpoint
   - Action requires approval (high-risk)
   - Approval request created
   - Human approves via API
   - Containment action executed (mocked)
3. **Approve Action**:
   ```bash
   # List pending approvals
   curl http://localhost:8000/api/v1/approvals
   
   # Approve action
   curl -X POST http://localhost:8000/api/v1/approvals/<approval-id> \
     -H "Content-Type: application/json" \
     -d '{
       "decision": "Approve",
       "approver": "admin@example.com",
       "comment": "Approved for containment"
     }'
   ```

### Scenario 5: Daily Threat Briefing

**Goal**: AI-generated threat intelligence briefing

1. **Trigger**: Scheduled run (or manual execution)
   ```bash
   python src/agents/threat_intelligence/briefing.py --generate-daily
   ```

2. **Expected Output**: Natural language briefing with:
   - Executive summary of threats in last 24h
   - Trending attack patterns
   - Recommended actions
   - Relevant IOCs

---

## Monitoring & Observability

### View Logs

```bash
# Structured logs in JSON format
tail -f logs/agentic-soc.log | jq .
```

### View Metrics

```bash
# Prometheus metrics endpoint
curl http://localhost:8000/metrics
```

### Application Insights (Azure)

1. Go to Azure Portal → Application Insights resource
2. Navigate to:
   - **Live Metrics**: Real-time agent activity
   - **Application Map**: Agent-to-agent communication flow
   - **Transaction Search**: Find specific triage events

Example KQL query in Application Insights:

```kql
traces
| where message == "alert_triaged"
| extend risk_score = toreal(customDimensions.risk_score)
| summarize avg(risk_score), percentile(risk_score, 95) by bin(timestamp, 5m)
| render timechart
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'azure'"

**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: "Authentication failed for Azure AI Foundry"

**Solution**:
```bash
# Ensure you're logged in
az login

# Verify subscription
az account show
```

### Issue: "No alerts being processed"

**Solution**:
```bash
# Check mock data stream is running
ps aux | grep "stream.py"

# Check Event Hubs connection
az eventhubs namespace authorization-rule keys list \
  --resource-group <rg-name> \
  --namespace-name <namespace> \
  --name RootManageSharedAccessKey
```

### Issue: "Triage taking > 5 seconds"

**Solution**:
- Check Azure OpenAI quota/throttling
- Verify model deployment name in `.env`
- Consider using `gpt-4o-mini` instead of `gpt-4o` for faster responses

---

## Next Steps

1. **Customize Agents**: Modify agent instructions in `src/agents/*/agent.py`
2. **Add Custom Scenarios**: Edit mock data in `mock-data/` directory
3. **Deploy to Azure**: Follow deployment guide in `docs/deployment.md`
4. **Integrate Real Data**: Replace mock services with production APIs

---

## Architecture Overview

```
┌─────────────────┐
│ Mock Data Stream│
│  (15s interval) │
└────────┬────────┘
         │
         v
┌─────────────────┐      ┌──────────────────┐
│  Event Hubs     │─────>│  Orchestrator    │
│ (Alert Ingestion)│      │ (Agent Framework)│
└─────────────────┘      └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    v             v             v
         ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
         │Triage Agent  │ │Hunting Agent │ │Response Agent│
         │(GPT-4o-mini) │ │(GPT-4o-mini) │ │(GPT-4o-mini) │
         └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
                │                │                │
                └────────────────┴────────────────┘
                                 │
                                 v
                        ┌─────────────────┐
                        │   Cosmos DB     │
                        │ (State & Audit) │
                        └─────────────────┘
```

---

## Support

- **Documentation**: `/docs/` directory
- **Issues**: GitHub Issues
- **Architecture Decisions**: `/docs/adr/` directory

---

**Ready to start?** Run `python src/orchestration/orchestrator.py` and watch the magic! 🎉
