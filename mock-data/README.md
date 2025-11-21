# Mock Data for Agentic SOC

This directory contains datasets used for implementing, testing, and demonstrating the Agentic SOC system.

## Datasets

### Attack_Dataset.csv

**Comprehensive cybersecurity attack scenarios dataset** with 14,133 entries covering 64 security categories and 8,834 unique attack types.

- **Source**: https://www.kaggle.com/datasets/tannubarot/cybersecurity-attack-and-defence-dataset
- **Analysis Report**: [Attack Dataset Analysis](../specs/001-agentic-soc/dataset-analysis/attack-dataset-analysis.md)
- **Key Features**:
  - 99.8% MITRE ATT&CK technique coverage
  - Detailed attack scenarios with step-by-step procedures
  - Detection methods and remediation solutions for each scenario
  - Modern threat coverage (AI/ML, quantum, satellite, blockchain)
  - 14,905+ tools and technologies referenced

**Use Cases**:
- Alert Triage Agent: Pattern recognition, risk scoring, false positive filtering
- Threat Hunting Agent: Hypothesis generation, natural language query translation
- Incident Response Agent: Automated playbook generation, containment actions
- Threat Intelligence Agent: Threat briefings, indicator enrichment

See the [comprehensive analysis report](../specs/001-agentic-soc/dataset-analysis/attack-dataset-analysis.md) for detailed insights and implementation recommendations.

### GUIDE Dataset (Microsoft Security Incidents)

**Time-series security incident data** for predictive modeling and trend analysis.

- **Source**: https://www.kaggle.com/datasets/Microsoft/microsoft-security-incident-prediction
- **Analysis Report**: [GUIDE Dataset Analysis](../specs/001-agentic-soc/dataset-analysis/guide-dataset-analysis.md)
- **Implementation Guidance**: [Implementation Guidance](../specs/001-agentic-soc/dataset-analysis/implementation-guidance.md)
- **Files**: GUIDE_Train_*.csv (25 files) and GUIDE_Test_*.csv (11 files)

## Dataset Analysis

All dataset analysis documentation, charts, and implementation guidance have been consolidated in:
**[specs/001-agentic-soc/dataset-analysis/](../specs/001-agentic-soc/dataset-analysis/)**

## Data Licensing

TODO: Need to address data licensing and citations for these datasets 
