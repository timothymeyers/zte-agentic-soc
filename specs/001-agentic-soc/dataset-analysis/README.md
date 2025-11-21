# Dataset Analysis Documentation

This directory contains comprehensive analysis documentation and visualizations for the datasets used in the Agentic SOC project.

## Contents

### Documentation

#### [guide-dataset-analysis.md](./guide-dataset-analysis.md)
Comprehensive analysis of the **Microsoft GUIDE (Security Incident Prediction)** dataset.

- **Dataset**: 1.17M+ security incident records from Microsoft production systems
- **Coverage**: 260K incidents, 4,602 organizations, 28 entity types
- **Key Features**:
  - Ground truth labels (TruePositive, FalsePositive, BenignPositive)
  - MITRE ATT&CK technique mappings (993 unique techniques)
  - Multi-entity incident correlation
  - 20 attack categories with temporal patterns
- **Use Cases**: Alert triage training, threat hunting, incident correlation, ML model development

#### [attack-dataset-analysis.md](./attack-dataset-analysis.md)
Comprehensive analysis of the **Cybersecurity Attack and Defence** dataset.

- **Dataset**: 14,133 cybersecurity attack scenarios
- **Coverage**: 64 security categories, 8,834 unique attack types
- **Key Features**:
  - 99.8% MITRE ATT&CK coverage
  - Detailed attack procedures and detection methods
  - Modern threat domains (AI/ML, quantum, satellite, blockchain)
  - Remediation guidance for each scenario
- **Use Cases**: Attack pattern recognition, playbook generation, threat intelligence, security education

#### [implementation-guidance.md](./implementation-guidance.md)
**Implementation guidance** for leveraging the GUIDE dataset in the Agentic SOC system.

- Schema transformation (GUIDE → Microsoft Sentinel format)
- Agent-specific implementation strategies
- Testing and validation approaches
- Demo scenario curation
- ML model training recommendations

### Visualizations

#### [charts/guide-dataset/](./charts/guide-dataset/)
Visualizations from the GUIDE dataset analysis:
- `incident_grade_distribution.png` - Distribution of incident grades (TP/FP/BP)
- `top_categories.png` - Most common attack categories
- `entity_type_distribution.png` - Entity type frequencies
- `hourly_pattern.png` - Alert volume by hour of day
- `data_completeness.png` - Missing data visualization

#### [charts/attack-dataset/](./charts/attack-dataset/)
Visualizations from the Attack dataset analysis:
- `category_distribution.png` - Distribution across 64 security categories
- `attack_type_distribution.png` - Most common attack types
- `target_type_distribution.png` - Target system breakdown
- `data_completeness.png` - Data quality metrics

## Quick Reference

### Dataset Comparison

| Aspect | GUIDE Dataset | Attack Dataset |
|--------|---------------|----------------|
| **Size** | 1.17M records | 14,133 scenarios |
| **Focus** | Real-world incidents | Attack education/reference |
| **Time Coverage** | 2 weeks of production data | Comprehensive threat catalog |
| **MITRE Coverage** | 42.5% (993 techniques) | 99.8% (5,406+ techniques) |
| **Ground Truth** | Yes (TP/FP/BP labels) | N/A (reference data) |
| **Best For** | ML training, triage, correlation | Pattern matching, playbooks, TI |

### Integration with Agentic SOC Agents

| Agent | Primary Dataset | Use Cases |
|-------|----------------|-----------|
| **Alert Triage** | GUIDE + Attack | Ground truth training, pattern recognition, risk scoring |
| **Threat Hunting** | GUIDE | Entity correlation, pivot analysis, temporal patterns |
| **Incident Response** | Attack | Playbook generation, automated containment, detection methods |
| **Threat Intelligence** | Attack + GUIDE | IOC enrichment, emerging threats, MITRE context |

## How to Use This Documentation

1. **For Implementation**: Start with [implementation-guidance.md](./implementation-guidance.md) for architectural recommendations and code examples
2. **For Understanding**: Read the analysis documents to understand dataset characteristics and quality
3. **For Visualization**: Refer to the charts directories for graphical insights
4. **For Reference**: Use this README for quick comparisons and navigation

## Related Documentation

- **Main Specification**: [../spec.md](../spec.md)
- **Architecture**: [../AgenticSOC_Architecture.md](../AgenticSOC_Architecture.md)
- **Dataset Files**: [../../mock-data/](../../../mock-data/)

## Updates and Maintenance

**Last Updated**: 2025-11-21

To update this documentation:
1. Re-run analysis scripts in `utils/` directory (when created)
2. Update analysis markdown files with new insights
3. Regenerate charts using updated data
4. Update this README with any structural changes
