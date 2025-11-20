# Clarification Questions for specs/001-agentic-soc

**Status**: Awaiting Responses  
**Created**: 2025-11-20  
**Analyzer**: GitHub Copilot Clarification Agent

---

I've analyzed the feature specification and identified several areas that need clarification to ensure accurate implementation. These questions focus on high-impact decisions that will materially affect architecture, data modeling, compliance, and operational design.

## Question 1: Authentication & Authorization Model

**Category**: Security & Privacy (Critical Infrastructure Decision)

The spec mentions "data privacy and security" but doesn't specify the authentication and authorization model for the system.

**Recommended:** Option B - Azure Managed Identity with Entra ID RBAC

Azure Managed Identity with Entra ID RBAC is recommended because it:
- Eliminates credential management overhead and security risks
- Provides native integration with all Microsoft Security services
- Supports fine-grained RBAC aligned with SOC roles
- Enables Zero Trust architecture principles
- Simplifies compliance auditing with built-in Azure AD logs

| Option | Description |
|--------|-------------|
| A | Service principals with shared secrets stored in Azure Key Vault |
| B | Azure Managed Identity with Entra ID RBAC for all agent-to-service communication |
| C | API keys with rotation policy for external integrations |
| D | OAuth 2.0 with custom identity provider |
| Short | Provide a different short answer (<=5 words) |

**Question**: Which authentication mechanism should agents use to access Microsoft Security services (Sentinel, Defender, Entra ID)?

**Your Response**: _[Please reply with option letter (A-D), "recommended", or provide your own answer]_

---

## Question 2: Data Retention & Compliance Requirements

**Category**: Compliance / Regulatory Constraints & Data Model (Affects Storage Design)

The spec mentions compliance but doesn't specify retention periods or regulatory requirements, which significantly impacts storage architecture and cost.

**Suggested:** 90 days hot, 1 year warm

Common SOC balance between investigation needs and cost optimization.

**Question**: What is the data retention requirement for security telemetry and audit logs?

**Format**: Short answer (<=5 words). Examples: "90 days", "1 year regulatory", "7 years compliance"

**Your Response**: _[Please provide retention period or say "suggested"]_

---

## Question 3: Approval Workflow Scope

**Category**: Autonomous-but-Supervised Operations (Risk Management Boundary)

The spec mentions "approval workflows for high-risk actions" but doesn't define what constitutes "high-risk" requiring human approval vs automated execution.

**Recommended:** Option C - Risk-scored threshold (critical assets/actions require approval)

Risk-scored threshold is recommended because it:
- Balances automation benefits with risk management
- Allows gradual expansion of automation as confidence grows
- Protects most critical assets while enabling speed for routine responses
- Aligns with industry best practices for security automation
- Provides flexibility to adjust thresholds based on organizational risk appetite

| Option | Description |
|--------|-------------|
| A | All containment actions require human approval (maximum safety, minimum automation) |
| B | Only account disablement and data deletion require approval (moderate automation) |
| C | Risk-scored threshold: Actions on critical assets or irreversible operations require approval |
| D | No approvals required after 30-day learning period (maximum automation) |
| Short | Provide a different short answer (<=5 words) |

**Question**: Which containment actions should require human approval before execution?

**Your Response**: _[Please reply with option letter (A-D), "recommended", or provide your own answer]_

---

## Question 4: Alert Ingestion API Format

**Category**: Integration & External Dependencies (Technical Contract Definition)

The spec mentions ingesting alerts from "multiple sources" but doesn't specify the expected input format or API contract.

**Recommended:** Option B - Microsoft Sentinel/Graph Security API format

Microsoft Sentinel/Graph Security API format is recommended because it:
- Native integration with Microsoft Security ecosystem (primary data source)
- Industry-standard schema (Common Event Format compatible)
- Rich metadata already included (reduces enrichment needs)
- Simplifies initial MVP implementation
- Easy to extend with custom source adapters later

| Option | Description |
|--------|-------------|
| A | CEF (Common Event Format) over Syslog |
| B | Microsoft Sentinel/Graph Security API format as canonical schema |
| C | Custom JSON schema with flexible mapping layer |
| D | STIX/TAXII for threat intelligence integration |
| Short | Provide a different short answer (<=5 words) |

**Question**: What alert/event format should the Alert Triage Agent expect as input?

**Your Response**: _[Please reply with option letter (A-D), "recommended", or provide your own answer]_

---

## Question 5: Incident Lifecycle States

**Category**: Domain & Data Model (Workflow State Machine)

The spec describes incident creation and response but doesn't define the incident state machine, which is essential for workflow orchestration and UI design.

**Suggested:** New → Investigating → Contained → Resolved → Closed

Standard incident response lifecycle aligned with NIST framework.

**Question**: What are the incident lifecycle states (e.g., New, Investigating, Contained, Resolved)?

**Format**: Short answer (<=5 words or comma-separated state names)

**Your Response**: _[Please provide state sequence or say "suggested"]_

---

## Summary

These 5 questions address the highest-impact ambiguities across:
- **Security Architecture** (Q1): Authentication model affects all service integrations
- **Compliance & Storage** (Q2): Retention requirements drive storage architecture and costs  
- **Risk Management** (Q3): Approval boundaries define automation scope and safety
- **Integration Design** (Q4): Input format defines data pipeline architecture
- **Workflow Design** (Q5): State machine defines orchestration and UI flows

**Recommendation**: Please provide answers to these questions before proceeding to `/speckit.plan` to minimize downstream rework risk.

---

## Coverage Status

After these clarifications, the remaining areas are:

### Deferred to Planning Phase
Better addressed during implementation planning:
- Specific performance SLAs for individual operations (will be derived from success criteria)
- Horizontal scaling strategy details (will be designed based on Azure architecture patterns)
- Detailed monitoring/observability design (will follow Azure Monitor best practices)
- Multi-language/accessibility requirements (not critical for MVP/POC phase)

### Already Clear
- Functional scope and user stories
- Core entities and relationships  
- Edge cases and failure scenarios
- Success criteria and acceptance tests
- Agent orchestration principles

**No critical blockers remain after addressing the 5 questions above.**

---

## How to Respond

1. Edit this file directly with your answers in the "Your Response" sections
2. Commit the updated file
3. Or, reply to the PR with your answers referencing question numbers (Q1-Q5)

Once responses are received, the clarifications can be integrated into the spec.md file following the standard format.
