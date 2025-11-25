"""
Dataset loaders for GUIDE and Attack datasets.

This module provides loaders to transform GUIDE records and Attack scenarios
into Sentinel SecurityAlert schema for MVP demonstration.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import uuid4
import random

from src.shared.schemas import (
    SecurityAlert,
    SeverityLevel,
    AlertEntity,
    EntityType
)
from src.shared.logging import get_logger


logger = get_logger(__name__)


class GUIDEDatasetLoader:
    """Loader for GUIDE dataset (1.17M+ real security incidents)."""
    
    def __init__(self, data_path: str = "./mock-data"):
        """
        Initialize GUIDE dataset loader.
        
        Args:
            data_path: Path to mock data directory
        """
        self.data_path = Path(data_path)
        self._alerts: List[SecurityAlert] = []
        logger.debug(f"GUIDE dataset loader initialized with path: {data_path}")
    
    def load_alerts(
        self,
        max_alerts: int = 100,
        severity_filter: Optional[SeverityLevel] = None
    ) -> List[SecurityAlert]:
        """
        Load alerts from GUIDE dataset.
        
        Args:
            max_alerts: Maximum number of alerts to load
            severity_filter: Filter by severity level
        
        Returns:
            List[SecurityAlert]: List of security alerts
        
        Note:
            For MVP, generates mock alerts based on GUIDE patterns.
            Production would read from actual GUIDE dataset files.
        """
        alerts = []
        
        # Mock alert patterns based on GUIDE dataset analysis
        alert_patterns = [
            {
                "AlertName": "Suspicious PowerShell Execution",
                "AlertType": "SuspiciousPowerShell",
                "Severity": SeverityLevel.HIGH,
                "Description": "PowerShell executed with base64-encoded command",
                "Provider": "Microsoft Defender for Endpoint",
                "MitreTechniques": ["T1059.001"]
            },
            {
                "AlertName": "Multiple Failed Login Attempts",
                "AlertType": "BruteForceAttempt",
                "Severity": SeverityLevel.MEDIUM,
                "Description": "Multiple failed login attempts detected from single source",
                "Provider": "Azure AD Identity Protection",
                "MitreTechniques": ["T1110.001"]
            },
            {
                "AlertName": "Suspicious File Download",
                "AlertType": "MalwareDownload",
                "Severity": SeverityLevel.HIGH,
                "Description": "Executable file downloaded from suspicious domain",
                "Provider": "Microsoft Defender for Endpoint",
                "MitreTechniques": ["T1071.001", "T1204.002"]
            },
            {
                "AlertName": "Lateral Movement Detected",
                "AlertType": "LateralMovement",
                "Severity": SeverityLevel.HIGH,
                "Description": "Suspicious SMB connection to multiple hosts",
                "Provider": "Microsoft Defender for Identity",
                "MitreTechniques": ["T1021.002"]
            },
            {
                "AlertName": "Credential Dumping Attempt",
                "AlertType": "CredentialAccess",
                "Severity": SeverityLevel.HIGH,
                "Description": "LSASS memory access detected",
                "Provider": "Microsoft Defender for Endpoint",
                "MitreTechniques": ["T1003.001"]
            },
            {
                "AlertName": "Suspicious Registry Modification",
                "AlertType": "PersistenceMechanism",
                "Severity": SeverityLevel.MEDIUM,
                "Description": "Registry run key modified for persistence",
                "Provider": "Microsoft Defender for Endpoint",
                "MitreTechniques": ["T1547.001"]
            }
        ]
        
        base_time = datetime.utcnow()
        
        for i in range(min(max_alerts, len(alert_patterns) * 20)):
            pattern = alert_patterns[i % len(alert_patterns)]
            
            # Create varied alerts based on pattern
            alert = SecurityAlert(
                SystemAlertId=uuid4(),
                AlertName=pattern["AlertName"],
                AlertType=pattern["AlertType"],
                Severity=pattern["Severity"],
                Description=pattern["Description"],
                TimeGenerated=base_time - timedelta(hours=random.randint(0, 72)),
                StartTime=base_time - timedelta(hours=random.randint(0, 72)),
                EndTime=base_time - timedelta(hours=random.randint(0, 72)),
                Entities=[
                    AlertEntity(
                        Type=EntityType.HOST,
                        Properties={"HostName": f"WS-{random.randint(1, 100):03d}"}
                    ),
                    AlertEntity(
                        Type=EntityType.ACCOUNT,
                        Properties={"UserName": f"user{random.randint(1, 50)}"}
                    )
                ],
                ExtendedProperties={
                    "MitreTechniques": pattern["MitreTechniques"],
                    "ConfidenceScore": random.randint(60, 95)
                },
                ProviderName=pattern["Provider"],
                ProductName=pattern["Provider"],
                RemediationSteps=[
                    "Investigate the alert",
                    "Check for related activity",
                    "Contain affected systems if necessary"
                ]
            )
            
            if severity_filter is None or alert.Severity == severity_filter:
                alerts.append(alert)
        
        logger.info(f"Loaded {len(alerts)} alerts from GUIDE dataset patterns")
        return alerts[:max_alerts]


class AttackDatasetLoader:
    """Loader for Attack dataset (14K+ attack scenarios with MITRE mappings)."""
    
    def __init__(self, data_path: str = "./mock-data"):
        """
        Initialize Attack dataset loader.
        
        Args:
            data_path: Path to mock data directory
        """
        self.data_path = Path(data_path)
        self._scenarios: List[Dict[str, Any]] = []
        logger.debug(f"Attack dataset loader initialized with path: {data_path}")
    
    def load_scenarios(self, technique_id: Optional[str] = None, use_mock: bool = False, max_scenarios: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load attack scenarios from Attack dataset.
        
        Args:
            technique_id: Filter by MITRE ATT&CK technique ID
            use_mock: If True, return mock scenarios instead of loading from CSV
            max_scenarios: Maximum number of scenarios to load (None = all)
        
        Returns:
            List[Dict]: List of attack scenarios
        """
        if use_mock:
            # Mock attack scenarios with MITRE mappings
            scenarios = [
                {
                    "scenario_id": "ATK-001",
                    "name": "PowerShell Credential Theft",
                    "technique": "T1059.001",
                    "tactic": "Execution",
                    "description": "Adversary uses PowerShell to steal credentials",
                    "indicators": ["powershell.exe", "mimikatz", "credential dump"],
                    "severity": "high"
                },
                {
                    "scenario_id": "ATK-002",
                    "name": "Brute Force SSH",
                    "technique": "T1110.001",
                    "tactic": "Credential Access",
                    "description": "Multiple failed SSH login attempts",
                    "indicators": ["ssh", "failed login", "multiple attempts"],
                    "severity": "medium"
                },
                {
                    "scenario_id": "ATK-003",
                    "name": "Ransomware File Encryption",
                    "technique": "T1486",
                    "tactic": "Impact",
                    "description": "Mass file encryption indicating ransomware",
                    "indicators": ["file encryption", "ransom note", "mass file modification"],
                    "severity": "critical"
                },
                {
                    "scenario_id": "ATK-004",
                    "name": "Lateral Movement via SMB",
                    "technique": "T1021.002",
                    "tactic": "Lateral Movement",
                    "description": "SMB connections to multiple hosts",
                    "indicators": ["smb", "network share", "multiple hosts"],
                    "severity": "high"
                }
            ]
        else:
            # Load from CSV file
            import csv
            csv_path = self.data_path / "Attack_Dataset.csv"
            
            if not csv_path.exists():
                logger.warning(f"Attack dataset CSV not found at {csv_path}, falling back to mock data")
                return self.load_scenarios(technique_id=technique_id, use_mock=True, max_scenarios=max_scenarios)
            
            scenarios = []
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for idx, row in enumerate(reader, 1):
                        # Extract MITRE technique (first one if multiple)
                        mitre_technique = row.get('MITRE Technique', '').strip()
                        techniques = [t.strip() for t in mitre_technique.split(',') if t.strip()]
                        primary_technique = techniques[0] if techniques else 'Unknown'
                        
                        # Map severity from impact field
                        impact = row.get('Impact', '').lower()
                        if 'critical' in impact or 'complete' in impact or 'full' in impact:
                            severity = 'critical'
                        elif 'high' in impact or 'major' in impact or 'significant' in impact:
                            severity = 'high'
                        elif 'medium' in impact or 'moderate' in impact:
                            severity = 'medium'
                        else:
                            severity = 'low'
                        
                        # Extract tactic from category or attack type
                        category = row.get('Category', '').strip()
                        attack_type = row.get('Attack Type', '').strip()
                        tactic = category if category else attack_type
                        
                        # Extract indicators from tools and detection fields
                        tools = row.get('Tools Used', '').strip()
                        detection = row.get('Detection Method', '').strip()
                        indicators = []
                        if tools:
                            indicators.extend([t.strip() for t in tools.split(',') if t.strip()])
                        if detection:
                            indicators.extend([d.strip() for d in detection.split(',') if d.strip()])
                        
                        scenario = {
                            "scenario_id": f"ATK-{idx:05d}",
                            "name": row.get('Title', f'Attack Scenario {idx}').strip(),
                            "technique": primary_technique,
                            "tactic": tactic,
                            "description": row.get('Scenario Description', '').strip() or row.get('Title', '').strip(),
                            "indicators": indicators[:10],  # Limit to first 10 indicators
                            "severity": severity,
                            "attack_type": attack_type,
                            "vulnerability": row.get('Vulnerability', '').strip(),
                            "target_type": row.get('Target Type', '').strip(),
                        }
                        scenarios.append(scenario)
                        
                        if max_scenarios and len(scenarios) >= max_scenarios:
                            break
                            
            except Exception as e:
                logger.error(f"Error loading Attack dataset CSV: {e}")
                logger.warning("Falling back to mock data")
                return self.load_scenarios(technique_id=technique_id, use_mock=True, max_scenarios=max_scenarios)
        
        if technique_id:
            scenarios = [s for s in scenarios if s["technique"] == technique_id]
        
        logger.info(f"Loaded {len(scenarios)} scenarios from Attack dataset")
        return scenarios
    
    def get_mitre_mapping(self, technique_id: str) -> Optional[Dict[str, Any]]:
        """
        Get MITRE ATT&CK mapping for a technique.
        
        Args:
            technique_id: MITRE ATT&CK technique ID
        
        Returns:
            Optional[Dict]: MITRE technique details if found
        """
        scenarios = self.load_scenarios(technique_id=technique_id)
        if scenarios:
            return scenarios[0]
        return None


# Global dataset loader instances
_guide_loader: Optional[GUIDEDatasetLoader] = None
_attack_loader: Optional[AttackDatasetLoader] = None


def get_guide_loader(data_path: str = "./mock-data") -> GUIDEDatasetLoader:
    """
    Get global GUIDE dataset loader instance.
    
    Args:
        data_path: Path to mock data directory
    
    Returns:
        GUIDEDatasetLoader: Global GUIDE loader
    """
    global _guide_loader
    if _guide_loader is None:
        _guide_loader = GUIDEDatasetLoader(data_path)
    return _guide_loader


def get_attack_loader(data_path: str = "./mock-data") -> AttackDatasetLoader:
    """
    Get global Attack dataset loader instance.
    
    Args:
        data_path: Path to mock data directory
    
    Returns:
        AttackDatasetLoader: Global Attack loader
    """
    global _attack_loader
    if _attack_loader is None:
        _attack_loader = AttackDatasetLoader(data_path)
    return _attack_loader
