# Model Selection Analysis of Alternatives (AOA)

**Date**: 2025-11-21  
**Purpose**: Comprehensive analysis of Azure OpenAI model options for Agentic SOC agents  
**Scope**: MVP and Production recommendations with cost, performance, and lifecycle considerations

---

## Executive Summary

**MVP Recommendation**: GPT-4o-mini (2024-07-18) as primary model for all agents
- **Cost**: 60% cheaper than GPT-4o
- **Performance**: 82% MMLU score (vs 70% for GPT-3.5-Turbo)
- **Speed**: Fastest model in GPT-4 family
- **Lifecycle**: Retirement not before September 15, 2025 → February 27, 2026 (15+ months)
- **Replacement Path**: GPT-4.1-mini (2025-04-14) available for migration

**Production Recommendation**: Agent-specific model selection
- **Alert Triage Agent**: GPT-4.1-mini (cost-optimized, fast, sufficient reasoning)
- **Threat Hunting Agent**: GPT-4.1 (complex query generation, advanced reasoning)
- **Incident Response Agent**: GPT-4.1 (critical decisions, high-risk actions)
- **Threat Intelligence Agent**: GPT-4.1-mini (summarization, briefing generation)

---

## Model Comparison Matrix

### Current Generation (Available Now)

| Model | Release | MMLU Score | Context | Output Tokens | Cost (per 1M tokens) | Speed | Retirement Date |
|-------|---------|------------|---------|---------------|----------------------|-------|-----------------|
| **GPT-4o-mini** | 2024-07-18 | 82% | 128K | 16,384 | Input: $0.15<br>Output: $0.60 | Fastest | Sep 15, 2025+ |
| **GPT-4o** | 2024-11-20 | ~85% | 128K | 16,384 | Input: $2.50<br>Output: $10.00 | Fast | Mar 1, 2026+ |
| **GPT-4o** | 2024-08-06 | ~85% | 128K | 16,384 | Input: $2.50<br>Output: $10.00 | Fast | Oct 15, 2025+ |
| **o1-mini** | 2024-09-12 | N/A (reasoning) | 128K | 65,536 | Input: $3.00<br>Output: $12.00 | Slow (reasoning) | Sep 26, 2025+ |
| **o1** | 2024-12-17 | N/A (reasoning) | 128K | 32,768 | Input: $15.00<br>Output: $60.00 | Very Slow | Dec 17, 2025+ |

### Next Generation (Available Q2 2025)

| Model | Release | Context | Output Tokens | Expected Cost | Retirement Date |
|-------|---------|---------|---------------|---------------|-----------------|
| **GPT-4.1-mini** | 2025-04-14 | 128K | TBD | Lower than 4o-mini | Apr 11, 2026+ |
| **GPT-4.1** | 2025-04-14 | 128K | TBD | Lower than 4o | Apr 11, 2026+ |
| **o4-mini** | 2025-04-16 | 128K | TBD | TBD | Apr 11, 2026+ |

---

## Agent-Specific Analysis

### 1. Alert Triage Agent (P1 - MVP Priority)

**Requirements**:
- Risk scoring (0-100) with explainability
- Alert correlation (pattern matching)
- False positive filtering
- Natural language explanations
- **Target**: < 5 seconds per alert at p95

**MVP Model**: **GPT-4o-mini (2024-07-18)**

**Rationale**:
- ✅ **Performance**: 82% MMLU sufficient for risk scoring logic
- ✅ **Speed**: Fastest model → meets < 5s latency target
- ✅ **Cost**: 60% cheaper than GPT-4o (critical for high volume: 10K alerts/day)
- ✅ **Explainability**: Excellent natural language generation
- ✅ **Context**: 128K tokens (handles large alert payloads with enrichment data)

**Cost Analysis (10,000 alerts/day)**:
- Average tokens per triage: ~2,000 input, ~500 output
- Daily cost with GPT-4o-mini: (20M input × $0.15/1M) + (5M output × $0.60/1M) = **$6.00/day** = **$180/month**
- Daily cost with GPT-4o: (20M × $2.50/1M) + (5M × $10.00/1M) = **$100/day** = **$3,000/month**
- **Savings**: $2,820/month (94% cost reduction)

**Production Model**: **GPT-4.1-mini (2025-04-14)**
- Successor to GPT-4o-mini
- Expected cost reduction
- Enhanced capabilities
- Longer lifecycle (12+ months from release)

---

### 2. Threat Hunting Agent (P2)

**Requirements**:
- Natural language → KQL translation
- Complex query generation (multi-table joins, time-based analysis)
- Anomaly detection reasoning
- Hypothesis generation
- **Target**: < 30 seconds for query generation

**MVP Model**: **GPT-4o-mini (2024-07-18)**

**Rationale**:
- ✅ **Code Generation**: Strong KQL/SQL generation capabilities
- ✅ **Speed**: Fast enough for interactive hunting
- ⚠️ **Complexity**: May struggle with very complex multi-stage queries
- ✅ **Cost**: Hunting queries less frequent than triage (100-500/day vs 10K/day)

**Cost Analysis (200 queries/day)**:
- Average tokens per query: ~3,000 input, ~1,000 output
- Daily cost with GPT-4o-mini: (0.6M input × $0.15/1M) + (0.2M output × $0.60/1M) = **$0.21/day** = **$6.30/month**

**Production Model**: **GPT-4.1 (2025-04-14)**

**Rationale for Upgrade**:
- ✅ **Advanced Reasoning**: Better for complex query logic
- ✅ **Multi-step Planning**: Improved for hunting workflows (pivot analysis, hypothesis testing)
- ✅ **Critical Use Case**: Hunting quality directly impacts threat detection effectiveness
- ✅ **Cost Justifiable**: Lower volume (200/day vs 10K/day) makes premium model affordable

**Cost Comparison (Production)**:
- GPT-4.1 daily cost: ~$5/day = **$150/month** (estimated based on GPT-4o pricing)
- **Value**: Enhanced threat detection capability worth premium

---

### 3. Incident Response Agent (P2)

**Requirements**:
- Playbook selection and execution
- Risk assessment for containment actions
- Approval workflow recommendations
- Multi-step reasoning (e.g., isolate endpoint → verify isolation → search for lateral movement)
- **Critical**: High-risk actions require accurate decision-making

**MVP Model**: **GPT-4o-mini (2024-07-18)**

**Rationale**:
- ✅ **Sufficient for MVP**: Playbook execution is mostly rule-based
- ✅ **Explainability**: Good for approval rationale
- ⚠️ **Risk**: Lower reasoning capability for complex incidents

**Cost Analysis (50 incidents/day)**:
- Average tokens per incident: ~5,000 input, ~1,500 output
- Daily cost with GPT-4o-mini: (0.25M input × $0.15/1M) + (0.075M output × $0.60/1M) = **$0.08/day** = **$2.40/month**

**Production Model**: **GPT-4.1 (2025-04-14)** ⚠️ **CRITICAL UPGRADE**

**Rationale for Upgrade**:
- ✅ **Safety-Critical**: Incorrect containment actions can cause outages or data loss
- ✅ **Advanced Reasoning**: Better risk assessment for high-stakes decisions
- ✅ **Multi-step Planning**: Complex incident response requires sophisticated reasoning
- ✅ **Compliance**: Higher-quality decision logs for audit trails
- ✅ **Cost Justifiable**: Low volume (50/day) makes premium model affordable

**Cost Comparison (Production)**:
- GPT-4.1 daily cost: ~$2/day = **$60/month** (estimated)
- **Value**: Risk mitigation for critical business operations

---

### 4. Threat Intelligence Agent (P3)

**Requirements**:
- Daily briefing generation (summarization)
- IOC enrichment (lookup and contextualization)
- Threat correlation (pattern matching)
- Natural language report generation
- **Target**: Daily briefing quality over speed

**MVP Model**: **GPT-4o-mini (2024-07-18)**

**Rationale**:
- ✅ **Summarization**: Excellent at generating concise, readable briefings
- ✅ **Pattern Matching**: Good for correlating threats with MITRE ATT&CK
- ✅ **Cost**: Daily briefing (1/day) + IOC enrichment (hundreds/day) is low volume

**Cost Analysis (1 briefing/day, 500 enrichments/day)**:
- Daily cost with GPT-4o-mini: ~**$1.50/day** = **$45/month**

**Production Model**: **GPT-4.1-mini (2025-04-14)**

**Rationale**:
- ✅ **Sufficient Capability**: Intelligence summarization doesn't require advanced reasoning
- ✅ **Cost-Optimized**: "mini" model appropriate for this workload
- ✅ **Quality**: Enhanced writing capabilities in GPT-4.1 generation

---

## Model Lifecycle & Deprecation Analysis

### Current Model Lifecycle

| Model | GA Date | Retirement Date | Months Available | Replacement |
|-------|---------|-----------------|------------------|-------------|
| GPT-4o-mini (2024-07-18) | Jul 2024 | Sep 15, 2025+ → Feb 27, 2026 | **15+ months** | GPT-4.1-mini |
| GPT-4o (2024-11-20) | Nov 2024 | Mar 1, 2026+ | **16+ months** | GPT-4.1 |
| GPT-4o (2024-08-06) | Aug 2024 | Oct 15, 2025+ | **14+ months** | GPT-4.1 |

### Migration Timeline

```
Nov 2024                    Apr 2025              Sep 2025              Feb 2026
    |                          |                     |                     |
    |-- MVP (GPT-4o-mini) -----|-- Evaluate 4.1 ----|-- Migrate Start ----|-- Complete -->
    |                          |                     |                     |
    |                          GPT-4.1 releases      Deprecation begins    Retirement
```

**MVP Strategy**:
- Use GPT-4o-mini (2024-07-18) for **all agents** in MVP (15+ months lifecycle)
- Plan migration to GPT-4.1 family in Q2 2025 (April release)
- Evaluate GPT-4.1-mini for triage/intelligence, GPT-4.1 for hunting/response

**Production Strategy**:
- Deploy with GPT-4.1 family (April 2025+) for longer lifecycle
- Differentiate models by agent requirements (mini vs standard)
- Monitor GPT-4.2/5.0 announcements for next generation

---

## Reasoning Models Analysis (o-series)

### o1-mini & o1

**Capabilities**:
- ✅ **Advanced Reasoning**: PhD-level problem solving
- ✅ **Multi-step Planning**: Complex workflows
- ❌ **Speed**: 5-10x slower than GPT-4o
- ❌ **Cost**: 2-20x more expensive

**Use Case Evaluation**:

| Agent | Should Use o-series? | Rationale |
|-------|---------------------|-----------|
| Alert Triage | ❌ No | Speed requirement (<5s) incompatible with reasoning latency |
| Threat Hunting | ⚠️ Maybe (Edge Cases) | Complex hypothetical scenarios could benefit, but 99% of queries don't need it |
| Incident Response | ⚠️ Maybe (High-Risk) | Novel/complex incidents with no playbook could use advanced reasoning |
| Threat Intelligence | ❌ No | Summarization doesn't require reasoning |

**Recommendation**: **Not for MVP**. Consider o-series for production edge cases:
- **o1-mini** for complex hunting hypotheses (analyst-initiated, not automated)
- **o1** for novel incident response scenarios (human-approved, not real-time)

---

## Fine-Tuning Considerations

### Models Available for Fine-Tuning

| Model | Fine-Tuning Status | Use Case |
|-------|-------------------|----------|
| GPT-4o-mini (2024-07-18) | ✅ Public Preview | Alert Triage optimization |
| GPT-4o (2024-08-06) | ✅ Available | Hunting/Response optimization |
| GPT-4.1-mini (2025-04-14) | ✅ Expected | Future optimization |

### Fine-Tuning Strategy

**MVP**: No fine-tuning (use base models with prompt engineering)

**Production**: Fine-tune GPT-4.1-mini for Alert Triage Agent
- **Data**: Use GUIDE dataset ground truth labels (1.17M incidents with TP/FP/BP labels)
- **Benefit**: Improve false positive filtering by 10-20%
- **Cost**: Training cost + inference premium
- **Timeline**: Q3 2025 after 6 months of production data collection

---

## Cost Summary

### MVP Cost Breakdown (Per Month)

| Agent | Model | Daily Cost | Monthly Cost |
|-------|-------|------------|--------------|
| Alert Triage | GPT-4o-mini | $6.00 | $180 |
| Threat Hunting | GPT-4o-mini | $0.21 | $6.30 |
| Incident Response | GPT-4o-mini | $0.08 | $2.40 |
| Threat Intelligence | GPT-4o-mini | $1.50 | $45 |
| **Total MVP** | | **$7.79/day** | **$233.70/month** |

### Production Cost Breakdown (Per Month) - Differentiated Models

| Agent | Model | Daily Cost | Monthly Cost |
|-------|-------|------------|--------------|
| Alert Triage | GPT-4.1-mini | $5.00 | $150 |
| Threat Hunting | GPT-4.1 | $5.00 | $150 |
| Incident Response | GPT-4.1 | $2.00 | $60 |
| Threat Intelligence | GPT-4.1-mini | $1.25 | $37.50 |
| **Total Production** | | **$13.25/day** | **$397.50/month** |

**Cost Increase**: +$163.80/month (+70%)  
**Value**: Enhanced threat detection, safer containment decisions, longer model lifecycle

---

## Recommendations

### MVP Phase (Now - Q2 2025)

✅ **Use GPT-4o-mini (2024-07-18) for all agents**

**Justification**:
1. **Cost**: 60% cheaper than GPT-4o → MVP budget-friendly
2. **Performance**: 82% MMLU sufficient for MVP requirements
3. **Speed**: Meets latency targets (<5s triage, <30s hunting)
4. **Lifecycle**: 15+ months before retirement (ample time for MVP → production)
5. **Simplicity**: Single model reduces operational complexity during development

**Risk Mitigation**:
- Monitor GPT-4.1 release (April 2025) for evaluation
- Design agents with pluggable model configuration (environment variable for model name)
- Track latency/accuracy metrics to validate model performance

### Production Phase (Q2 2025+)

✅ **Differentiate models by agent requirements**

| Agent | Production Model | Justification |
|-------|-----------------|---------------|
| Alert Triage | **GPT-4.1-mini** | High volume (10K/day) requires cost optimization |
| Threat Hunting | **GPT-4.1** | Complex reasoning justifies premium model |
| Incident Response | **GPT-4.1** | Safety-critical decisions require best model |
| Threat Intelligence | **GPT-4.1-mini** | Summarization doesn't need advanced reasoning |

**Migration Plan**:
1. **Q2 2025**: Evaluate GPT-4.1 family (April release)
2. **Q2 2025**: A/B test GPT-4.1 vs GPT-4o-mini in production
3. **Q3 2025**: Migrate Hunting + Response to GPT-4.1
4. **Q3 2025**: Migrate Triage + Intelligence to GPT-4.1-mini
5. **Q3 2025**: Retire GPT-4o-mini deployments

---

## Decision Matrix

| Criterion | Weight | GPT-4o-mini (MVP) | GPT-4.1-mini (Prod) | GPT-4.1 (Prod) |
|-----------|--------|-------------------|---------------------|----------------|
| Cost | 25% | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐ (3/5) |
| Performance | 30% | ⭐⭐⭐⭐ (4/5) | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐⭐⭐ (5/5) |
| Speed | 20% | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐⭐ (4/5) |
| Lifecycle | 15% | ⭐⭐⭐ (3/5) | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐⭐⭐ (5/5) |
| Context | 10% | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐⭐⭐ (5/5) | ⭐⭐⭐⭐⭐ (5/5) |
| **Total** | | **4.4/5** | **5.0/5** | **4.4/5** |

---

## References

- [Azure OpenAI Models Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/models)
- [Model Retirements & Lifecycle](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/model-retirements)
- [GPT-4o-mini Announcement](https://azure.microsoft.com/blog/openais-fastest-model-gpt-4o-mini-is-now-available-on-azure-ai/)
- [Azure OpenAI Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)

---

**Document Status**: Complete  
**Last Updated**: 2025-11-21  
**Next Review**: Q1 2025 (GPT-4.1 release evaluation)
