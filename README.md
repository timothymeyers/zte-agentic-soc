# zte-agentic-soc

Implementation of an Agentic Security Operations Center MVP using AI-powered agents for modern threat detection and response.

## Overview

This project implements an **AI-enhanced Security Operations Center (SOC)** architecture based on the **Agentic SOC Layer** design. It leverages specialized AI agents built with Azure AI Foundry and Microsoft Security Copilot to augment human security analysts, enabling faster threat detection, automated triage, proactive hunting, and coordinated incident response.

### Core Agents

The Agentic SOC implements four specialized AI agents working collaboratively:

1. **Alert Triage Agent** - Prioritizes and correlates incoming alerts, filters false positives, and provides risk-based explanations
2. **Threat Hunting Agent** - Proactively searches for hidden threats using natural language queries and automated analytics
3. **Incident Response Agent** - Automates containment, eradication, and recovery actions through orchestrated playbooks
4. **Threat Intelligence Agent** - Aggregates and distills threat intelligence to provide context and daily briefings

These agents are coordinated by an **Orchestration Layer** that manages workflows, context sharing, and human escalation.

## Constitutional Principles

This project is governed by a comprehensive constitution that establishes seven core principles for development and operations. See [`.specify/memory/constitution.md`](.specify/memory/constitution.md) for the complete framework.

**Key Principles**:
- AI-First Security Operations
- Agent Collaboration & Orchestration
- Autonomous-but-Supervised Operations
- Proactive Threat Detection
- Continuous Context Sharing
- Explainability & Transparency
- Continuous Learning & Adaptation

## Technology Stack

- **AI Platform**: Azure AI Foundry, Azure OpenAI (via Security Copilot)
- **SIEM/XDR**: Microsoft Sentinel, Microsoft Defender XDR
- **Orchestration**: Azure Logic Apps, Azure Functions, Azure AI Foundry Agent Service
- **Identity**: Microsoft Entra ID (Azure AD)
- **Data**: Azure Monitor, Log Analytics, Cosmos DB

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
- Incremental agent implementation with testing at each stage
- Human-in-the-loop for high-risk automated actions
- Explainable AI decisions with clear rationale
- Integration with Microsoft security ecosystem
- Continuous learning from analyst feedback

## Getting Started

*Documentation for setup and deployment will be added as the MVP is implemented.*

## License

See [LICENSE](LICENSE) file for details.

## Reference

This implementation is based on research documented in [`.github/reference-material/agentic-soc-research.md`](.github/reference-material/agentic-soc-research.md).
