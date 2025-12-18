# zte-agentic-soc

**MVP Proof of Concept** for an Agentic Security Operations Center using AI-powered agents for modern threat detection and response.

## Overview

This project implements an **AI-enhanced Security Operations Center (SOC)** architecture as a **proof of concept demonstration** based on the **Agentic SOC Layer** design. It leverages specialized AI agents built with Microsoft Foundry (AI Foundry) and Microsoft Agent Framework to augment human security analysts, enabling faster threat detection, automated triage, proactive hunting, and coordinated incident response.

**MVP Approach**: This implementation is designed to be demonstrable with simulated or mock data without requiring full production infrastructure deployment. All components include clear "plugin" points for production integration in future phases.

### Core Agents

The Agentic SOC implements four specialized AI agents working collaboratively:

1. **Alert Triage Agent** - Prioritizes and correlates incoming alerts, filters false positives, and provides risk-based explanations
2. **Threat Hunting Agent** - Proactively searches for hidden threats using natural language queries and automated analytics
3. **Incident Response Agent** - Automates containment, eradication, and recovery actions through orchestrated playbooks
4. **Threat Intelligence Agent** - Aggregates and distills threat intelligence to provide context and daily briefings

These top-level agents may be composed of sub-agents, tools, or knowledge sources as implementation details. They are coordinated by an **Orchestration Layer** built with Microsoft Foundry or Microsoft Agent Framework that manages agent-to-agent communication, workflows, context sharing, and human escalation.

## Constitutional Principles

This project is governed by a comprehensive constitution that establishes eight core principles for development and operations. See [`.specify/memory/constitution.md`](.specify/memory/constitution.md) for the complete framework.

**Key Principles**:
- AI-First Security Operations
- Agent Collaboration & Orchestration
- Autonomous-but-Supervised Operations
- Proactive Threat Detection
- Continuous Context Sharing
- Explainability & Transparency
- Continuous Learning & Adaptation
- Observability & Operational Excellence

## Technology Stack

**MVP/POC Phase**:
- **AI Platform**: Microsoft Foundry (AI Foundry) with AI Foundry Client interface
- **Orchestration**: Microsoft Foundry or Microsoft Agent Framework for agent-to-agent communication
- **Data Storage**: Microsoft Fabric (preferred) or mock data sources with clear plugin points
- **SIEM/XDR**: Simulated data or optional Microsoft Sentinel/Defender XDR integration
- **Identity**: Optional Microsoft Entra ID integration with clear plugin points

**Production Integration Points**:
- Microsoft Sentinel and Microsoft Defender XDR for security telemetry
- Microsoft Entra ID (Azure AD) for user and entity context
- Microsoft Fabric for scalable data storage
- Azure Monitor and Log Analytics for operational telemetry

**Production Deployment**:
In a production scenario, the Agentic SOC will be deployed following Azure best practices:
- **Azure Landing Zone** architecture for enterprise-grade deployment
- **Azure Verified Modules** (AVM) for consistent, compliant infrastructure
- **Microsoft Cloud Adoption Framework** (CAF) alignment
- **Well-Architected Framework** compliance (Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency)

## Project Structure

```
.specify/
├── memory/
│   └── constitution.md      # Constitutional framework and principles
├── templates/               # Feature specification and planning templates
└── scripts/                 # Automation scripts

.github/
├── agents/                  # Agent configuration files
├── prompts/                 # Prompt templates for AI agents
└── reference-material/      # Research and architectural documentation
```

## Development Approach

All development follows the constitutional framework with emphasis on:
- **MVP/POC demonstration** with simulated or mock data
- Clear **plugin points** for production integration
- Incremental agent implementation with testing at each stage
- Agent flexibility: may start monolithic, evolve to sub-agents/tools/knowledge sources
- Human-in-the-loop for high-risk automated actions
- Explainable AI decisions with clear rationale
- Agent-to-agent communication via Microsoft Foundry or Microsoft Agent Framework

## Getting Started

### Prerequisites

- **Python**: 3.11 or higher
- **Azure CLI**: Installed and authenticated
- **Azure Access**: RBAC access to an Azure resource group (e.g., `asoc-zte-rg`)
- **Microsoft Foundry**: Access to Microsoft Foundry workspace and project

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/timothymeyers/zte-agentic-soc.git
   cd zte-agentic-soc
   ```

2. **Set up Python environment**:
   ```bash
   # Create virtual environment
   python3.11 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

3. **Configure environment variables**:
   ```bash
   # Copy template and edit with your values
   cp .env.example .env
   
   # Edit .env with your Azure credentials and endpoints
   # Required variables:
   # - AZURE_TENANT_ID
   # - AZURE_SUBSCRIPTION_ID
   # - AZURE_RESOURCE_GROUP
   # - AZURE_AI_FOUNDRY_PROJECT_ENDPOINT
   # - AZURE_OPENAI_DEPLOYMENT_NAME
   ```

4. **Verify Azure authentication**:
   ```bash
   # Login to Azure CLI (if not already logged in)
   az login
   
   # Verify access to resource group
   az group show --name asoc-zte-rg
   ```

5. **Run linting and tests**:
   ```bash
   # Format code
   black src/ tests/
   
   # Run linters
   ruff check src/ tests/
   pylint src/
   
   # Run type checking
   mypy src/
   
   # Run tests (when available)
   pytest tests/
   ```

### Development Workflow

1. **Project Structure**:
   ```
   src/
   ├── deployment/        # Agent deployment scripts
   ├── orchestration/     # Agent coordination and workflows
   ├── data/             # Mock data processing
   ├── shared/           # Shared utilities (auth, logging, models)
   └── demo/             # Demo scenarios and CLI
   ```

2. **Key Configuration Files**:
   - `pyproject.toml` - Python project configuration and dependencies
   - `.env` - Environment variables (not committed)
   - `.env.example` - Environment variable template

3. **Running the Demo** (coming soon):
   ```bash
   # Deploy agents to Microsoft Foundry
   python -m src.demo.cli deploy
   
   # Run a demo scenario
   python -m src.demo.cli run-workflow alert_triage
   ```

### Architecture Overview

The Agentic SOC uses a **two-phase architecture**:

**Phase A: Infrastructure Deployment**
- Deploy AI agents to Microsoft Foundry using `azure-ai-projects` SDK
- Agents are cloud-hosted and persistent
- Instructions define agent behavior (no tools initially)

**Phase B: Runtime Orchestration**
- Use Microsoft Agent Framework's magentic orchestrator for coordination
- Manager agent selects appropriate specialized agents
- Context shared between agents via Sentinel incidents and Cosmos DB

### MVP Implementation Status

- [x] Phase 1: Setup (project structure, dependencies, configuration)
- [ ] Phase 2: Foundational (models, auth, logging, mock data)
- [ ] Phase 3: Orchestration (manager agent, magentic workflow)
- [ ] Phase 4: Alert Triage Agent (P1 - first agent)
- [ ] Phase 5-7: Additional agents (Intelligence, Hunting, Response)
- [ ] Phase 8+: Integration, infrastructure, polish

## License

See [LICENSE](LICENSE) file for details.

## Reference

This implementation is based on research documented in [`.github/reference-material/agentic-soc-research.md`](.github/reference-material/agentic-soc-research.md).
