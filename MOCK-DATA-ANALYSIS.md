# GUIDE Dataset Analysis Report

**Generated**: 2025-11-21 19:10:42

## Executive Summary

This report provides a comprehensive analysis of the Microsoft Security Incident Prediction (GUIDE) dataset 
stored in the `mock-data/` directory. The analysis focuses on understanding the dataset structure, quality, 
and its applicability to implementing, testing, and demonstrating the Agentic SOC system.

## Dataset Overview

- **Training Files**: 25
- **Test Files**: 11
- **Total Files**: 36
- **Total Size**: 3.26 GB
- **Sample Records Analyzed**: 1,177,277
- **Total Columns**: 48

## Dataset Schema

### Column Overview

| Column Name | Data Type | Null % | Unique Values | Description |
|-------------|-----------|--------|---------------|-------------|
| Id | int64 | 0.0% | 341,179 | Unique evidence identifier |
| OrgId | int64 | 0.0% | 4,602 | Organization identifier |
| IncidentId | int64 | 0.0% | 260,610 | Incident identifier for grouping related alerts |
| AlertId | int64 | 0.0% | 603,061 | Alert identifier |
| Timestamp | datetime64[ns, UTC] | 0.0% | 463,676 | When the evidence was collected |
| DetectorId | int64 | 0.0% | 5,932 | Security product/detector that generated the alert |
| AlertTitle | int64 | 0.0% | 50,883 | Title/name of the alert |
| Category | object | 0.0% | 20 | Attack category (MITRE tactics) |
| MitreTechniques | object | 57.5% | 993 | MITRE ATT&CK technique IDs |
| IncidentGrade | object | 0.5% | 3 | Ground truth triage label (TruePositive, FalsePositive, etc.) |
| ActionGrouped | object | 99.4% | 3 | High-level remediation action taken |
| ActionGranular | object | 99.4% | 15 | Detailed remediation action |
| EntityType | object | 0.0% | 28 | Type of entity in the evidence |
| EvidenceRole | object | 0.0% | 2 | Role of evidence (Related, Impacted, etc.) |
| DeviceId | int64 | 0.0% | 23,234 | Device identifier |
| Sha256 | int64 | 0.0% | 28,407 | File hash identifier |
| IpAddress | int64 | 0.0% | 80,734 | IP address identifier |
| Url | int64 | 0.0% | 31,212 | URL identifier |
| AccountSid | int64 | 0.0% | 121,468 | Account SID identifier |
| AccountUpn | int64 | 0.0% | 184,475 | Account UPN identifier |
| AccountObjectId | int64 | 0.0% | 119,437 | Account object ID |
| AccountName | int64 | 0.0% | 125,148 | Account name identifier |
| DeviceName | int64 | 0.0% | 34,085 | Device name identifier |
| NetworkMessageId | int64 | 0.0% | 99,393 | Evidence attribute |
| EmailClusterId | float64 | 99.0% | 6,484 | Evidence attribute |
| RegistryKey | int64 | 0.0% | 412 | Evidence attribute |
| RegistryValueName | int64 | 0.0% | 158 | Evidence attribute |
| RegistryValueData | int64 | 0.0% | 223 | Evidence attribute |
| ApplicationId | int64 | 0.0% | 410 | Evidence attribute |
| ApplicationName | int64 | 0.0% | 646 | Evidence attribute |
| OAuthApplicationId | int64 | 0.0% | 157 | Evidence attribute |
| ThreatFamily | object | 99.2% | 968 | Malware family name |
| FileName | int64 | 0.0% | 49,045 | File name identifier |
| FolderPath | int64 | 0.0% | 23,408 | Folder path identifier |
| ResourceIdName | int64 | 0.0% | 521 | Evidence attribute |
| ResourceType | object | 99.9% | 23 | Evidence attribute |
| Roles | object | 97.7% | 9 | Evidence attribute |
| OSFamily | int64 | 0.0% | 4 | Evidence attribute |
| OSVersion | int64 | 0.0% | 32 | Evidence attribute |
| AntispamDirection | object | 98.1% | 4 | Evidence attribute |
| SuspicionLevel | object | 84.8% | 2 | Evidence attribute |
| LastVerdict | object | 76.5% | 5 | Evidence attribute |
| CountryCode | int64 | 0.0% | 177 | Evidence attribute |
| State | int64 | 0.0% | 835 | Evidence attribute |
| City | int64 | 0.0% | 3,504 | Evidence attribute |
| Date | object | 0.0% | 122 | Evidence attribute |
| Hour | int32 | 0.0% | 24 | Evidence attribute |
| DayOfWeek | int32 | 0.0% | 7 | Evidence attribute |

## Data Quality Assessment

### Completeness

Fields with missing values (>1%):

- **MitreTechniques**: 57.5% missing
- **ActionGrouped**: 99.4% missing
- **ActionGranular**: 99.4% missing
- **EmailClusterId**: 99.0% missing
- **ThreatFamily**: 99.2% missing
- **ResourceType**: 99.9% missing
- **Roles**: 97.7% missing
- **AntispamDirection**: 98.1% missing
- **SuspicionLevel**: 84.8% missing
- **LastVerdict**: 76.5% missing

## Key Statistics

### Incident Grade Distribution

- **BenignPositive**: 508,034 (43.15%)
- **TruePositive**: 411,186 (34.93%)
- **FalsePositive**: 251,854 (21.39%)

### Top 10 Attack Categories

- **InitialAccess**: 530,357
- **Exfiltration**: 195,287
- **SuspiciousActivity**: 124,490
- **CommandAndControl**: 101,720
- **Impact**: 93,212
- **CredentialAccess**: 37,262
- **Execution**: 33,328
- **Malware**: 17,809
- **Discovery**: 16,079
- **Persistence**: 9,021

### MITRE ATT&CK Coverage

- Records with MITRE techniques: 500,654 (42.5%)
- Unique techniques: 993

### Temporal Coverage

- **Start Date**: 2023-12-01 20:24:40+00:00
- **End Date**: 2024-06-17 14:45:38+00:00
- **Duration**: 198 days 18:20:58

## Insights for Agentic SOC Implementation

### 1. Alert Triage Agent

**Key Capabilities Enabled by Dataset:**

- **Ground Truth Labels**: Dataset includes incident grades with 35.1% TruePositive alerts, enabling supervised learning for triage
- **False Positive Filtering**: 21.5% labeled FalsePositive - perfect for training FP detection models
- **Alert Correlation**: 260,610 unique incidents across sample - average 4.5 alerts per incident
- **Priority Scoring**: Rich metadata (category, MITRE techniques, entity types) enables risk-based prioritization

### 2. Threat Hunting Agent

**Key Capabilities Enabled by Dataset:**

- **Multi-Entity Hunting**: 28 entity types available:
  - Ip: 269,747
  - User: 239,568
  - MailMessage: 145,150
  - Machine: 86,169
  - File: 84,670
  - Url: 84,655
  - CloudLogonRequest: 78,903
  - Mailbox: 59,694
  - Process: 42,750
  - MailCluster: 27,874
  - CloudApplication: 27,112
  - CloudLogonSession: 26,141
  - RegistryValue: 1,423
  - AzureResource: 1,026
  - RegistryKey: 934
  - GenericEntity: 542
  - OAuthApplication: 322
  - Malware: 299
  - SecurityGroup: 180
  - BlobContainer: 36
  - Blob: 35
  - MailboxConfiguration: 28
  - Nic: 9
  - IoTDevice: 4
  - Container: 2
  - AmazonResource: 2
  - ActiveDirectoryDomain: 1
  - GoogleCloudResource: 1
- **MITRE ATT&CK Mapping**: 42.5% coverage with 993 unique techniques - enables technique-based hunting queries
- **Pivoting Capabilities**: Dataset links devices, accounts, IPs, URLs, files - enables lateral investigation

### 3. Incident Response Agent

**Key Capabilities Enabled by Dataset:**

- **Response Playbooks**: Action columns provide examples of customer remediation actions for training
- **Category-Specific Responses**: 20 unique categories enable tailored response playbooks
- **Entity-Based Actions**: Multiple entity types (User, Device, IP, File, URL) enable targeted containment
- **Incident Context**: Full incident history enables context-aware response decisions

### 4. Threat Intelligence Agent

**Key Capabilities Enabled by Dataset:**

- **Threat Intelligence**: 9,206 records with threat family indicators (968 unique families)
- **Multi-Source Intelligence**: 5932 unique detector sources demonstrate integration complexity
- **IOC Extraction**: Dataset contains IPs, URLs, file hashes, domains - enables IOC enrichment workflows
- **Technique Intelligence**: MITRE ATT&CK mappings enable technique-based threat intelligence

## Recommended Use Cases

### 1. Training & Development

- **Model Training**: Use IncidentGrade labels to train ML models for alert triage
- **Pattern Learning**: Learn correlation patterns between entities and attack techniques
- **Baseline Establishment**: Understand normal alert volumes and patterns

### 2. Testing & Validation

- **Agent Testing**: Use as test data for validating agent decisions
- **Performance Benchmarking**: Test agent response times and accuracy
- **Edge Case Testing**: Dataset includes diverse scenarios (FP, BP, TP)

### 3. Demonstration

- **Realistic Scenarios**: Real-world data makes demos more convincing
- **End-to-End Workflows**: Demonstrate complete triage → hunting → response → intelligence cycle
- **Multi-Organization**: Multiple OrgIds enable multi-tenant demonstration

## Data Limitations & Considerations

### Missing Data

Fields with >50% missing values:

- **MitreTechniques**: 57.5% missing
- **ActionGrouped**: 99.4% missing
- **ActionGranular**: 99.4% missing
- **EmailClusterId**: 99.0% missing
- **ThreatFamily**: 99.2% missing
- **ResourceType**: 99.9% missing
- **Roles**: 97.7% missing
- **AntispamDirection**: 98.1% missing
- **SuspicionLevel**: 84.8% missing
- **LastVerdict**: 76.5% missing

### Privacy & Anonymization

- Dataset uses anonymized identifiers (numeric IDs instead of real values)
- Safe for testing and demonstration without exposing real organizational data

### Temporal Coverage

- Dataset covers approximately 2 weeks (as mentioned in documentation)
- May not capture seasonal or long-term trends

## Recommendations

### For Implementation

1. **Start with Alert Triage**: Use IncidentGrade labels to build and validate triage agent
2. **Leverage MITRE Mappings**: Use technique IDs for hunting and response playbook selection
3. **Build Entity Graph**: Use entity relationships for correlation and hunting
4. **Category-Based Workflows**: Implement category-specific response playbooks

### For Testing

1. **Stratified Sampling**: Ensure test sets include all incident grades and categories
2. **Temporal Splits**: Use chronological splits for realistic testing
3. **Organization-Based Splits**: Test multi-tenant capabilities

### For Demonstration

1. **Curate Demo Scenarios**: Select representative incidents showcasing each agent
2. **Visualize Agent Actions**: Show triage scores, hunting pivots, response timelines
3. **Highlight Collaboration**: Demonstrate agent-to-agent handoffs and context sharing

## Conclusion

The GUIDE dataset provides an excellent foundation for implementing, testing, and demonstrating 
the Agentic SOC system. Its comprehensive coverage of security events, ground truth labels, 
MITRE ATT&CK mappings, and multi-entity relationships make it ideal for:

- Training supervised learning models for alert triage
- Validating threat hunting queries and pivots
- Testing incident response playbooks
- Demonstrating end-to-end SOC workflows

The dataset's scale (1.6M alerts, 1M incidents, 6.1K organizations) and real-world provenance 
ensure that agents developed with this data will generalize well to production scenarios.

## Appendix

### Visualizations

See the `mock-data-analysis/` directory for generated visualizations:

- `incident_grade_distribution.png` - Distribution of incident grades
- `top_categories.png` - Most common attack categories
- `entity_type_distribution.png` - Entity type frequencies
- `hourly_pattern.png` - Alert volume by hour
- `data_completeness.png` - Missing data visualization

### References

- **Dataset Source**: [Microsoft Security Incident Prediction (GUIDE)](https://www.kaggle.com/datasets/Microsoft/microsoft-security-incident-prediction/data)
- **Research Paper**: [GUIDE on arXiv](https://arxiv.org/abs/2407.09017)
- **Agentic SOC Spec**: `specs/001-agentic-soc/spec.md`
