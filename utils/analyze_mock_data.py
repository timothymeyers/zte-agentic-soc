#!/usr/bin/env python3
"""
Comprehensive analysis of the GUIDE mock dataset for Agentic SOC system.

This script analyzes the Microsoft Security Incident Prediction dataset (GUIDE)
stored in the mock-data directory and generates a comprehensive report.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set visualization style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (14, 8)

class GUIDEDatasetAnalyzer:
    """Analyzer for GUIDE dataset."""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.train_files = sorted(list(self.data_dir.glob('GUIDE_Train_*.csv')))
        self.test_files = sorted(list(self.data_dir.glob('GUIDE_Test_*.csv')))
        self.df_sample = None
        self.df_full_sample = None
        
    def load_sample_data(self, n_files: int = 3):
        """Load a sample of the dataset for initial exploration."""
        print(f"Loading sample data from {n_files} training files...")
        
        dfs = []
        for file in self.train_files[:n_files]:
            print(f"  Loading {file.name}...")
            df = pd.read_csv(file)
            dfs.append(df)
        
        self.df_sample = pd.concat(dfs, ignore_index=True)
        print(f"Sample loaded: {len(self.df_sample):,} records from {n_files} files\n")
        return self.df_sample
    
    def get_basic_info(self):
        """Get basic information about the dataset."""
        print("=" * 80)
        print("DATASET BASIC INFORMATION")
        print("=" * 80)
        
        print(f"\nFile Structure:")
        print(f"  Training files: {len(self.train_files)}")
        print(f"  Test files: {len(self.test_files)}")
        print(f"  Total files: {len(self.train_files) + len(self.test_files)}")
        
        # Get file sizes
        total_size = sum(f.stat().st_size for f in self.train_files + self.test_files)
        print(f"  Total dataset size: {total_size / (1024**3):.2f} GB")
        
        print(f"\nSample Dataset Shape: {self.df_sample.shape}")
        print(f"  Records: {self.df_sample.shape[0]:,}")
        print(f"  Columns: {self.df_sample.shape[1]}")
        
        return {
            'train_files': len(self.train_files),
            'test_files': len(self.test_files),
            'total_size_gb': total_size / (1024**3),
            'sample_records': len(self.df_sample),
            'total_columns': self.df_sample.shape[1]
        }
    
    def analyze_schema(self):
        """Analyze and document the schema."""
        print("\n" + "=" * 80)
        print("SCHEMA ANALYSIS")
        print("=" * 80)
        
        print("\nColumn Overview:")
        print(self.df_sample.dtypes)
        
        print("\n\nDetailed Column Information:")
        schema_info = []
        
        for col in self.df_sample.columns:
            dtype = str(self.df_sample[col].dtype)
            null_count = self.df_sample[col].isnull().sum()
            null_pct = (null_count / len(self.df_sample)) * 100
            unique_count = self.df_sample[col].nunique()
            
            # Get sample values
            non_null_values = self.df_sample[col].dropna()
            if len(non_null_values) > 0:
                sample_values = non_null_values.head(3).tolist()
            else:
                sample_values = []
            
            schema_info.append({
                'Column': col,
                'DataType': dtype,
                'Null_Count': null_count,
                'Null_Pct': f"{null_pct:.1f}%",
                'Unique_Values': unique_count,
                'Sample_Values': str(sample_values)[:50]
            })
            
            print(f"\n{col}:")
            print(f"  Type: {dtype}")
            print(f"  Nulls: {null_count:,} ({null_pct:.1f}%)")
            print(f"  Unique: {unique_count:,}")
            print(f"  Sample: {str(sample_values)[:80]}")
        
        return pd.DataFrame(schema_info)
    
    def analyze_data_quality(self):
        """Analyze data quality metrics."""
        print("\n" + "=" * 80)
        print("DATA QUALITY ANALYSIS")
        print("=" * 80)
        
        # Missing values analysis
        print("\nMissing Values by Column:")
        missing = self.df_sample.isnull().sum().sort_values(ascending=False)
        missing_pct = (missing / len(self.df_sample) * 100).round(2)
        
        missing_df = pd.DataFrame({
            'Missing_Count': missing,
            'Missing_Percentage': missing_pct
        })
        
        print(missing_df[missing_df['Missing_Count'] > 0])
        
        # Duplicates
        duplicates = self.df_sample.duplicated().sum()
        print(f"\n\nDuplicate Records: {duplicates:,} ({duplicates/len(self.df_sample)*100:.2f}%)")
        
        # Check for ID uniqueness
        if 'Id' in self.df_sample.columns:
            unique_ids = self.df_sample['Id'].nunique()
            print(f"\nUnique IDs: {unique_ids:,} out of {len(self.df_sample):,}")
            print(f"ID Uniqueness: {unique_ids/len(self.df_sample)*100:.2f}%")
        
        return missing_df
    
    def analyze_key_fields(self):
        """Analyze key fields relevant to SOC operations."""
        print("\n" + "=" * 80)
        print("KEY FIELDS ANALYSIS")
        print("=" * 80)
        
        analyses = {}
        
        # Incident Grade (Critical for triage)
        if 'IncidentGrade' in self.df_sample.columns:
            print("\nIncident Grade Distribution:")
            grade_dist = self.df_sample['IncidentGrade'].value_counts()
            print(grade_dist)
            print(f"\nPercentages:")
            print((grade_dist / len(self.df_sample) * 100).round(2))
            analyses['incident_grade'] = grade_dist
        
        # Category (Attack types)
        if 'Category' in self.df_sample.columns:
            print("\n\nTop 10 Attack Categories:")
            category_dist = self.df_sample['Category'].value_counts().head(10)
            print(category_dist)
            analyses['categories'] = category_dist
        
        # MITRE ATT&CK Techniques
        if 'MitreTechniques' in self.df_sample.columns:
            print("\n\nMITRE ATT&CK Techniques Coverage:")
            mitre_techniques = self.df_sample['MitreTechniques'].dropna()
            print(f"Records with MITRE techniques: {len(mitre_techniques):,} ({len(mitre_techniques)/len(self.df_sample)*100:.1f}%)")
            if len(mitre_techniques) > 0:
                # Count individual techniques (some records may have multiple)
                print(f"Unique techniques: {mitre_techniques.nunique()}")
                print("\nTop 10 MITRE Techniques:")
                print(mitre_techniques.value_counts().head(10))
            analyses['mitre_techniques'] = mitre_techniques
        
        # DetectorId (Detection sources)
        if 'DetectorId' in self.df_sample.columns:
            print("\n\nTop 10 Detector IDs:")
            detector_dist = self.df_sample['DetectorId'].value_counts().head(10)
            print(detector_dist)
            print(f"\nTotal unique detectors: {self.df_sample['DetectorId'].nunique()}")
            analyses['detectors'] = detector_dist
        
        # Organizations
        if 'OrgId' in self.df_sample.columns:
            print("\n\nOrganization Distribution:")
            org_count = self.df_sample['OrgId'].nunique()
            print(f"Unique organizations: {org_count}")
            analyses['org_count'] = org_count
        
        # Entity Types
        if 'EntityType' in self.df_sample.columns:
            print("\n\nEntity Type Distribution:")
            entity_dist = self.df_sample['EntityType'].value_counts()
            print(entity_dist)
            analyses['entity_types'] = entity_dist
        
        # Evidence Role
        if 'EvidenceRole' in self.df_sample.columns:
            print("\n\nEvidence Role Distribution:")
            role_dist = self.df_sample['EvidenceRole'].value_counts()
            print(role_dist)
            analyses['evidence_roles'] = role_dist
        
        return analyses
    
    def analyze_temporal_patterns(self):
        """Analyze temporal patterns in the data."""
        print("\n" + "=" * 80)
        print("TEMPORAL ANALYSIS")
        print("=" * 80)
        
        if 'Timestamp' not in self.df_sample.columns:
            print("No Timestamp column found.")
            return None
        
        # Convert to datetime
        self.df_sample['Timestamp'] = pd.to_datetime(self.df_sample['Timestamp'])
        
        print(f"\nTime Range:")
        print(f"  Earliest: {self.df_sample['Timestamp'].min()}")
        print(f"  Latest: {self.df_sample['Timestamp'].max()}")
        print(f"  Duration: {self.df_sample['Timestamp'].max() - self.df_sample['Timestamp'].min()}")
        
        # Extract temporal features
        self.df_sample['Date'] = self.df_sample['Timestamp'].dt.date
        self.df_sample['Hour'] = self.df_sample['Timestamp'].dt.hour
        self.df_sample['DayOfWeek'] = self.df_sample['Timestamp'].dt.dayofweek
        
        print(f"\n\nAlerts by Day:")
        daily_counts = self.df_sample.groupby('Date').size()
        print(f"  Average per day: {daily_counts.mean():.0f}")
        print(f"  Min per day: {daily_counts.min()}")
        print(f"  Max per day: {daily_counts.max()}")
        
        print(f"\n\nAlerts by Hour of Day (sample):")
        hourly = self.df_sample['Hour'].value_counts().sort_index()
        print(hourly.head(10))
        
        return {
            'time_range': (self.df_sample['Timestamp'].min(), self.df_sample['Timestamp'].max()),
            'daily_counts': daily_counts
        }
    
    def generate_visualizations(self, output_dir: str):
        """Generate key visualizations."""
        print("\n" + "=" * 80)
        print("GENERATING VISUALIZATIONS")
        print("=" * 80)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Incident Grade Distribution
        if 'IncidentGrade' in self.df_sample.columns:
            plt.figure(figsize=(10, 6))
            grade_counts = self.df_sample['IncidentGrade'].value_counts()
            plt.bar(grade_counts.index, grade_counts.values)
            plt.title('Incident Grade Distribution', fontsize=14, fontweight='bold')
            plt.xlabel('Incident Grade')
            plt.ylabel('Count')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(output_path / 'incident_grade_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  ✓ Saved: incident_grade_distribution.png")
        
        # 2. Top Categories
        if 'Category' in self.df_sample.columns:
            plt.figure(figsize=(12, 6))
            top_categories = self.df_sample['Category'].value_counts().head(10)
            plt.barh(range(len(top_categories)), top_categories.values)
            plt.yticks(range(len(top_categories)), top_categories.index)
            plt.xlabel('Count')
            plt.title('Top 10 Attack Categories', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(output_path / 'top_categories.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  ✓ Saved: top_categories.png")
        
        # 3. Entity Type Distribution
        if 'EntityType' in self.df_sample.columns:
            plt.figure(figsize=(10, 6))
            entity_counts = self.df_sample['EntityType'].value_counts()
            plt.bar(range(len(entity_counts)), entity_counts.values)
            plt.xticks(range(len(entity_counts)), entity_counts.index, rotation=45, ha='right')
            plt.title('Entity Type Distribution', fontsize=14, fontweight='bold')
            plt.xlabel('Entity Type')
            plt.ylabel('Count')
            plt.tight_layout()
            plt.savefig(output_path / 'entity_type_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  ✓ Saved: entity_type_distribution.png")
        
        # 4. Temporal pattern - hourly
        if 'Hour' in self.df_sample.columns:
            plt.figure(figsize=(12, 6))
            hourly = self.df_sample['Hour'].value_counts().sort_index()
            plt.plot(hourly.index, hourly.values, marker='o', linewidth=2)
            plt.title('Alert Volume by Hour of Day', fontsize=14, fontweight='bold')
            plt.xlabel('Hour of Day')
            plt.ylabel('Number of Alerts')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(output_path / 'hourly_pattern.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  ✓ Saved: hourly_pattern.png")
        
        # 5. Missing data heatmap
        plt.figure(figsize=(12, 8))
        missing_matrix = self.df_sample.isnull()
        missing_pct = missing_matrix.sum() / len(self.df_sample) * 100
        missing_pct = missing_pct[missing_pct > 0].sort_values(ascending=False)
        
        if len(missing_pct) > 0:
            plt.barh(range(len(missing_pct)), missing_pct.values)
            plt.yticks(range(len(missing_pct)), missing_pct.index)
            plt.xlabel('Missing Percentage (%)')
            plt.title('Data Completeness by Column', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(output_path / 'data_completeness.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  ✓ Saved: data_completeness.png")
        
        print(f"\nAll visualizations saved to: {output_path}")
    
    def generate_insights(self):
        """Generate insights for Agentic SOC implementation."""
        print("\n" + "=" * 80)
        print("INSIGHTS FOR AGENTIC SOC IMPLEMENTATION")
        print("=" * 80)
        
        insights = []
        
        # 1. Alert Triage Agent Insights
        insights.append({
            'agent': 'Alert Triage Agent',
            'insights': []
        })
        
        if 'IncidentGrade' in self.df_sample.columns:
            grade_dist = self.df_sample['IncidentGrade'].value_counts(normalize=True) * 100
            if 'TruePositive' in grade_dist.index:
                tp_pct = grade_dist['TruePositive']
                insights[-1]['insights'].append(
                    f"Only {tp_pct:.1f}% of alerts are TruePositive - demonstrates need for intelligent triage"
                )
            if 'FalsePositive' in grade_dist.index:
                fp_pct = grade_dist['FalsePositive']
                insights[-1]['insights'].append(
                    f"{fp_pct:.1f}% of alerts are FalsePositive - agent can learn to filter these automatically"
                )
        
        # 2. Threat Hunting Agent Insights
        insights.append({
            'agent': 'Threat Hunting Agent',
            'insights': []
        })
        
        if 'EntityType' in self.df_sample.columns:
            entity_count = self.df_sample['EntityType'].nunique()
            insights[-1]['insights'].append(
                f"Dataset includes {entity_count} entity types - enables comprehensive hunting across multiple dimensions"
            )
        
        if 'MitreTechniques' in self.df_sample.columns:
            mitre_coverage = self.df_sample['MitreTechniques'].notna().sum() / len(self.df_sample) * 100
            unique_techniques = self.df_sample['MitreTechniques'].nunique()
            insights[-1]['insights'].append(
                f"{mitre_coverage:.1f}% of records have MITRE ATT&CK mappings ({unique_techniques} unique techniques) - excellent for technique-based hunting"
            )
        
        # 3. Incident Response Agent Insights
        insights.append({
            'agent': 'Incident Response Agent',
            'insights': []
        })
        
        if 'ActionGrouped' in self.df_sample.columns or 'ActionGranular' in self.df_sample.columns:
            insights[-1]['insights'].append(
                "Dataset includes Action columns - can be used to train/test automated response playbooks"
            )
        
        if 'Category' in self.df_sample.columns:
            category_count = self.df_sample['Category'].nunique()
            insights[-1]['insights'].append(
                f"{category_count} unique attack categories - enables category-specific response playbooks"
            )
        
        # 4. Threat Intelligence Agent Insights
        insights.append({
            'agent': 'Threat Intelligence Agent',
            'insights': []
        })
        
        if 'ThreatFamily' in self.df_sample.columns:
            threat_families = self.df_sample['ThreatFamily'].notna().sum()
            insights[-1]['insights'].append(
                f"{threat_families:,} records have ThreatFamily indicators - useful for threat intelligence enrichment"
            )
        
        if 'DetectorId' in self.df_sample.columns:
            detector_count = self.df_sample['DetectorId'].nunique()
            insights[-1]['insights'].append(
                f"{detector_count} unique detector sources - demonstrates multi-source intelligence integration"
            )
        
        # Print insights
        for insight_group in insights:
            print(f"\n{insight_group['agent']}:")
            for insight in insight_group['insights']:
                print(f"  • {insight}")
        
        return insights
    
    def generate_report(self, output_file: str):
        """Generate comprehensive markdown report."""
        print("\n" + "=" * 80)
        print("GENERATING COMPREHENSIVE REPORT")
        print("=" * 80)
        
        report = []
        
        # Header
        report.append("# GUIDE Dataset Analysis Report")
        report.append("")
        report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("## Executive Summary")
        report.append("")
        report.append("This report provides a comprehensive analysis of the Microsoft Security Incident Prediction (GUIDE) dataset ")
        report.append("stored in the `mock-data/` directory. The analysis focuses on understanding the dataset structure, quality, ")
        report.append("and its applicability to implementing, testing, and demonstrating the Agentic SOC system.")
        report.append("")
        
        # Dataset Overview
        report.append("## Dataset Overview")
        report.append("")
        report.append(f"- **Training Files**: {len(self.train_files)}")
        report.append(f"- **Test Files**: {len(self.test_files)}")
        report.append(f"- **Total Files**: {len(self.train_files) + len(self.test_files)}")
        
        total_size = sum(f.stat().st_size for f in self.train_files + self.test_files)
        report.append(f"- **Total Size**: {total_size / (1024**3):.2f} GB")
        report.append(f"- **Sample Records Analyzed**: {len(self.df_sample):,}")
        report.append(f"- **Total Columns**: {self.df_sample.shape[1]}")
        report.append("")
        
        # Schema Section
        report.append("## Dataset Schema")
        report.append("")
        report.append("### Column Overview")
        report.append("")
        report.append("| Column Name | Data Type | Null % | Unique Values | Description |")
        report.append("|-------------|-----------|--------|---------------|-------------|")
        
        for col in self.df_sample.columns:
            dtype = str(self.df_sample[col].dtype)
            null_pct = (self.df_sample[col].isnull().sum() / len(self.df_sample)) * 100
            unique_count = self.df_sample[col].nunique()
            
            # Infer description based on column name
            descriptions = {
                'Id': 'Unique evidence identifier',
                'OrgId': 'Organization identifier',
                'IncidentId': 'Incident identifier for grouping related alerts',
                'AlertId': 'Alert identifier',
                'Timestamp': 'When the evidence was collected',
                'DetectorId': 'Security product/detector that generated the alert',
                'AlertTitle': 'Title/name of the alert',
                'Category': 'Attack category (MITRE tactics)',
                'MitreTechniques': 'MITRE ATT&CK technique IDs',
                'IncidentGrade': 'Ground truth triage label (TruePositive, FalsePositive, etc.)',
                'ActionGrouped': 'High-level remediation action taken',
                'ActionGranular': 'Detailed remediation action',
                'EntityType': 'Type of entity in the evidence',
                'EvidenceRole': 'Role of evidence (Related, Impacted, etc.)',
                'DeviceId': 'Device identifier',
                'Sha256': 'File hash identifier',
                'IpAddress': 'IP address identifier',
                'Url': 'URL identifier',
                'AccountSid': 'Account SID identifier',
                'AccountUpn': 'Account UPN identifier',
                'AccountObjectId': 'Account object ID',
                'AccountName': 'Account name identifier',
                'DeviceName': 'Device name identifier',
                'ThreatFamily': 'Malware family name',
                'FileName': 'File name identifier',
                'FolderPath': 'Folder path identifier',
            }
            
            desc = descriptions.get(col, 'Evidence attribute')
            
            report.append(f"| {col} | {dtype} | {null_pct:.1f}% | {unique_count:,} | {desc} |")
        
        report.append("")
        
        # Data Quality
        report.append("## Data Quality Assessment")
        report.append("")
        
        missing_df = self.df_sample.isnull().sum()
        missing_pct = (missing_df / len(self.df_sample) * 100).round(2)
        
        report.append("### Completeness")
        report.append("")
        report.append("Fields with missing values (>1%):")
        report.append("")
        
        for col in missing_df[missing_pct > 1].index:
            report.append(f"- **{col}**: {missing_pct[col]:.1f}% missing")
        
        report.append("")
        
        # Key Statistics
        report.append("## Key Statistics")
        report.append("")
        
        if 'IncidentGrade' in self.df_sample.columns:
            report.append("### Incident Grade Distribution")
            report.append("")
            grade_dist = self.df_sample['IncidentGrade'].value_counts()
            grade_pct = (grade_dist / len(self.df_sample) * 100).round(2)
            
            for grade, count in grade_dist.items():
                report.append(f"- **{grade}**: {count:,} ({grade_pct[grade]:.2f}%)")
            report.append("")
        
        if 'Category' in self.df_sample.columns:
            report.append("### Top 10 Attack Categories")
            report.append("")
            top_cats = self.df_sample['Category'].value_counts().head(10)
            for cat, count in top_cats.items():
                report.append(f"- **{cat}**: {count:,}")
            report.append("")
        
        if 'MitreTechniques' in self.df_sample.columns:
            mitre_count = self.df_sample['MitreTechniques'].notna().sum()
            mitre_pct = (mitre_count / len(self.df_sample) * 100)
            unique_techniques = self.df_sample['MitreTechniques'].nunique()
            report.append("### MITRE ATT&CK Coverage")
            report.append("")
            report.append(f"- Records with MITRE techniques: {mitre_count:,} ({mitre_pct:.1f}%)")
            report.append(f"- Unique techniques: {unique_techniques}")
            report.append("")
        
        if 'Timestamp' in self.df_sample.columns:
            report.append("### Temporal Coverage")
            report.append("")
            timestamps = pd.to_datetime(self.df_sample['Timestamp'])
            report.append(f"- **Start Date**: {timestamps.min()}")
            report.append(f"- **End Date**: {timestamps.max()}")
            report.append(f"- **Duration**: {timestamps.max() - timestamps.min()}")
            report.append("")
        
        # Insights for Agentic SOC
        report.append("## Insights for Agentic SOC Implementation")
        report.append("")
        
        # Alert Triage Agent
        report.append("### 1. Alert Triage Agent")
        report.append("")
        report.append("**Key Capabilities Enabled by Dataset:**")
        report.append("")
        
        if 'IncidentGrade' in self.df_sample.columns:
            grade_dist = self.df_sample['IncidentGrade'].value_counts(normalize=True) * 100
            if 'TruePositive' in grade_dist.index:
                tp_pct = grade_dist['TruePositive']
                report.append(f"- **Ground Truth Labels**: Dataset includes incident grades with {tp_pct:.1f}% TruePositive alerts, enabling supervised learning for triage")
            if 'FalsePositive' in grade_dist.index:
                fp_pct = grade_dist['FalsePositive']
                report.append(f"- **False Positive Filtering**: {fp_pct:.1f}% labeled FalsePositive - perfect for training FP detection models")
        
        if 'IncidentId' in self.df_sample.columns:
            incidents = self.df_sample['IncidentId'].nunique()
            alerts_per_incident = len(self.df_sample) / incidents
            report.append(f"- **Alert Correlation**: {incidents:,} unique incidents across sample - average {alerts_per_incident:.1f} alerts per incident")
        
        report.append("- **Priority Scoring**: Rich metadata (category, MITRE techniques, entity types) enables risk-based prioritization")
        report.append("")
        
        # Threat Hunting Agent
        report.append("### 2. Threat Hunting Agent")
        report.append("")
        report.append("**Key Capabilities Enabled by Dataset:**")
        report.append("")
        
        if 'EntityType' in self.df_sample.columns:
            entity_count = self.df_sample['EntityType'].nunique()
            entity_types = self.df_sample['EntityType'].value_counts()
            report.append(f"- **Multi-Entity Hunting**: {entity_count} entity types available:")
            for entity, count in entity_types.items():
                report.append(f"  - {entity}: {count:,}")
        
        if 'MitreTechniques' in self.df_sample.columns:
            mitre_coverage = self.df_sample['MitreTechniques'].notna().sum() / len(self.df_sample) * 100
            unique_techniques = self.df_sample['MitreTechniques'].nunique()
            report.append(f"- **MITRE ATT&CK Mapping**: {mitre_coverage:.1f}% coverage with {unique_techniques} unique techniques - enables technique-based hunting queries")
        
        report.append("- **Pivoting Capabilities**: Dataset links devices, accounts, IPs, URLs, files - enables lateral investigation")
        report.append("")
        
        # Incident Response Agent
        report.append("### 3. Incident Response Agent")
        report.append("")
        report.append("**Key Capabilities Enabled by Dataset:**")
        report.append("")
        
        if 'ActionGrouped' in self.df_sample.columns or 'ActionGranular' in self.df_sample.columns:
            report.append("- **Response Playbooks**: Action columns provide examples of customer remediation actions for training")
        
        if 'Category' in self.df_sample.columns:
            category_count = self.df_sample['Category'].nunique()
            report.append(f"- **Category-Specific Responses**: {category_count} unique categories enable tailored response playbooks")
        
        if 'EntityType' in self.df_sample.columns:
            report.append("- **Entity-Based Actions**: Multiple entity types (User, Device, IP, File, URL) enable targeted containment")
        
        report.append("- **Incident Context**: Full incident history enables context-aware response decisions")
        report.append("")
        
        # Threat Intelligence Agent
        report.append("### 4. Threat Intelligence Agent")
        report.append("")
        report.append("**Key Capabilities Enabled by Dataset:**")
        report.append("")
        
        if 'ThreatFamily' in self.df_sample.columns:
            threat_count = self.df_sample['ThreatFamily'].notna().sum()
            unique_families = self.df_sample['ThreatFamily'].nunique()
            report.append(f"- **Threat Intelligence**: {threat_count:,} records with threat family indicators ({unique_families} unique families)")
        
        if 'DetectorId' in self.df_sample.columns:
            detector_count = self.df_sample['DetectorId'].nunique()
            report.append(f"- **Multi-Source Intelligence**: {detector_count} unique detector sources demonstrate integration complexity")
        
        report.append("- **IOC Extraction**: Dataset contains IPs, URLs, file hashes, domains - enables IOC enrichment workflows")
        report.append("- **Technique Intelligence**: MITRE ATT&CK mappings enable technique-based threat intelligence")
        report.append("")
        
        # Use Cases
        report.append("## Recommended Use Cases")
        report.append("")
        report.append("### 1. Training & Development")
        report.append("")
        report.append("- **Model Training**: Use IncidentGrade labels to train ML models for alert triage")
        report.append("- **Pattern Learning**: Learn correlation patterns between entities and attack techniques")
        report.append("- **Baseline Establishment**: Understand normal alert volumes and patterns")
        report.append("")
        
        report.append("### 2. Testing & Validation")
        report.append("")
        report.append("- **Agent Testing**: Use as test data for validating agent decisions")
        report.append("- **Performance Benchmarking**: Test agent response times and accuracy")
        report.append("- **Edge Case Testing**: Dataset includes diverse scenarios (FP, BP, TP)")
        report.append("")
        
        report.append("### 3. Demonstration")
        report.append("")
        report.append("- **Realistic Scenarios**: Real-world data makes demos more convincing")
        report.append("- **End-to-End Workflows**: Demonstrate complete triage → hunting → response → intelligence cycle")
        report.append("- **Multi-Organization**: Multiple OrgIds enable multi-tenant demonstration")
        report.append("")
        
        # Data Limitations
        report.append("## Data Limitations & Considerations")
        report.append("")
        report.append("### Missing Data")
        report.append("")
        
        high_missing = missing_pct[missing_pct > 50]
        if len(high_missing) > 0:
            report.append("Fields with >50% missing values:")
            report.append("")
            for col, pct in high_missing.items():
                report.append(f"- **{col}**: {pct:.1f}% missing")
            report.append("")
        
        report.append("### Privacy & Anonymization")
        report.append("")
        report.append("- Dataset uses anonymized identifiers (numeric IDs instead of real values)")
        report.append("- Safe for testing and demonstration without exposing real organizational data")
        report.append("")
        
        report.append("### Temporal Coverage")
        report.append("")
        report.append("- Dataset covers approximately 2 weeks (as mentioned in documentation)")
        report.append("- May not capture seasonal or long-term trends")
        report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        report.append("### For Implementation")
        report.append("")
        report.append("1. **Start with Alert Triage**: Use IncidentGrade labels to build and validate triage agent")
        report.append("2. **Leverage MITRE Mappings**: Use technique IDs for hunting and response playbook selection")
        report.append("3. **Build Entity Graph**: Use entity relationships for correlation and hunting")
        report.append("4. **Category-Based Workflows**: Implement category-specific response playbooks")
        report.append("")
        
        report.append("### For Testing")
        report.append("")
        report.append("1. **Stratified Sampling**: Ensure test sets include all incident grades and categories")
        report.append("2. **Temporal Splits**: Use chronological splits for realistic testing")
        report.append("3. **Organization-Based Splits**: Test multi-tenant capabilities")
        report.append("")
        
        report.append("### For Demonstration")
        report.append("")
        report.append("1. **Curate Demo Scenarios**: Select representative incidents showcasing each agent")
        report.append("2. **Visualize Agent Actions**: Show triage scores, hunting pivots, response timelines")
        report.append("3. **Highlight Collaboration**: Demonstrate agent-to-agent handoffs and context sharing")
        report.append("")
        
        # Conclusion
        report.append("## Conclusion")
        report.append("")
        report.append("The GUIDE dataset provides an excellent foundation for implementing, testing, and demonstrating ")
        report.append("the Agentic SOC system. Its comprehensive coverage of security events, ground truth labels, ")
        report.append("MITRE ATT&CK mappings, and multi-entity relationships make it ideal for:")
        report.append("")
        report.append("- Training supervised learning models for alert triage")
        report.append("- Validating threat hunting queries and pivots")
        report.append("- Testing incident response playbooks")
        report.append("- Demonstrating end-to-end SOC workflows")
        report.append("")
        report.append("The dataset's scale (1.6M alerts, 1M incidents, 6.1K organizations) and real-world provenance ")
        report.append("ensure that agents developed with this data will generalize well to production scenarios.")
        report.append("")
        
        # Appendix
        report.append("## Appendix")
        report.append("")
        report.append("### Visualizations")
        report.append("")
        report.append("See the `mock-data-analysis/` directory for generated visualizations:")
        report.append("")
        report.append("- `incident_grade_distribution.png` - Distribution of incident grades")
        report.append("- `top_categories.png` - Most common attack categories")
        report.append("- `entity_type_distribution.png` - Entity type frequencies")
        report.append("- `hourly_pattern.png` - Alert volume by hour")
        report.append("- `data_completeness.png` - Missing data visualization")
        report.append("")
        
        report.append("### References")
        report.append("")
        report.append("- **Dataset Source**: [Microsoft Security Incident Prediction (GUIDE)](https://www.kaggle.com/datasets/Microsoft/microsoft-security-incident-prediction/data)")
        report.append("- **Research Paper**: [GUIDE on arXiv](https://arxiv.org/abs/2407.09017)")
        report.append("- **Agentic SOC Spec**: `specs/001-agentic-soc/spec.md`")
        report.append("")
        
        # Write report
        report_text = "\n".join(report)
        
        with open(output_file, 'w') as f:
            f.write(report_text)
        
        print(f"\n✓ Report saved to: {output_file}")
        return report_text


def main():
    """Main analysis workflow."""
    print("\n" + "=" * 80)
    print("GUIDE DATASET ANALYSIS FOR AGENTIC SOC")
    print("=" * 80)
    print()
    
    # Initialize analyzer
    data_dir = "/home/runner/work/zte-agentic-soc/zte-agentic-soc/mock-data"
    analyzer = GUIDEDatasetAnalyzer(data_dir)
    
    # Load sample data (first 3 training files for efficiency)
    analyzer.load_sample_data(n_files=3)
    
    # Run analyses
    analyzer.get_basic_info()
    analyzer.analyze_schema()
    analyzer.analyze_data_quality()
    analyzer.analyze_key_fields()
    analyzer.analyze_temporal_patterns()
    
    # Generate visualizations
    viz_dir = "/home/runner/work/zte-agentic-soc/zte-agentic-soc/mock-data-analysis"
    analyzer.generate_visualizations(viz_dir)
    
    # Generate insights
    analyzer.generate_insights()
    
    # Generate comprehensive report
    report_file = "/home/runner/work/zte-agentic-soc/zte-agentic-soc/MOCK-DATA-ANALYSIS.md"
    analyzer.generate_report(report_file)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nReport: {report_file}")
    print(f"Visualizations: {viz_dir}/")
    print()


if __name__ == "__main__":
    main()
