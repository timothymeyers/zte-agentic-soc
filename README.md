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

1. **Python 3.11+** installed
2. **Azure CLI** for authentication (`az login`)
3. **Azure AI Foundry Project** (optional, for production-grade AI)
4. **Git** for cloning the repository

### Installation

```bash
# Clone the repository
git clone https://github.com/timothymeyers/zte-agentic-soc.git
cd zte-agentic-soc

# Install dependencies
pip install -r requirements.txt
```

### Quick Start - Alert Triage Agent Demo

The Alert Triage Agent is implemented using **Microsoft Agent Framework** and can run with or without Azure AI Foundry:

#### Option 1: With Azure AI Foundry (Recommended)

```bash
# Set up Azure AI Foundry project endpoint
export AZURE_AI_PROJECT_ENDPOINT="https://your-project.services.ai.azure.com/api/projects/project-id"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"

# Authenticate with Azure
az login

# Run the demo
python utils/demo_agent_framework.py
```

#### Option 2: Without Azure (OpenAI Fallback)

```bash
# No configuration needed - automatically uses OpenAI fallback
python utils/demo_agent_framework.py
```

### What You'll See

The demo showcases:
- ✅ **Microsoft Agent Framework** integration with `ChatAgent`
- ✅ **AI Function Tools** with `@ai_function` decorators
- ✅ **Multi-factor risk scoring** (severity, entities, MITRE techniques, confidence)
- ✅ **Alert correlation detection** by entity overlap
- ✅ **AI-powered triage decisions** with natural language explanations
- ✅ **Threat intelligence enrichment** from MITRE ATT&CK dataset
- ✅ **Audit logging** and performance metrics

### Architecture

```
GUIDE Dataset → Alert → ChatAgent (Framework) → AI Function Tools → GPT-4o → Triage Decision
                                                    ↓
                                    - calculate_risk_score
                                    - find_correlated_alerts
                                    - make_triage_decision
                                    - get_mitre_context
```

### Documentation

- **[Agent Framework Implementation](docs/AGENT-FRAMEWORK-IMPLEMENTATION.md)** - Complete architecture and usage guide
- **[Framework Migration Summary](docs/FRAMEWORK-MIGRATION-SUMMARY.md)** - Before/after comparison
- **[MVP Implementation Summary](docs/MVP-IMPLEMENTATION-SUMMARY.md)** - Overall project status

## License

See [LICENSE](LICENSE) file for details.

## Reference

This implementation is based on research documented in [`.github/reference-material/agentic-soc-research.md`](.github/reference-material/agentic-soc-research.md).
