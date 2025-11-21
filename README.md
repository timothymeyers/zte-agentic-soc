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

*Documentation for setup and deployment will be added as the MVP is implemented.*

## License

See [LICENSE](LICENSE) file for details.

## Reference

This implementation is based on research documented in [`.github/reference-material/agentic-soc-research.md`](.github/reference-material/agentic-soc-research.md).
