"""
Scenario manager for curated demo scenarios.

Provides pre-configured alert sequences for demonstrating SOC capabilities.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

from src.shared.logging import get_logger
from src.shared.models import SecurityAlert, Severity

logger = get_logger(__name__, module="scenarios")


class ScenarioType(str, Enum):
    """Types of demo scenarios."""

    BRUTE_FORCE = "brute_force"
    PHISHING_CAMPAIGN = "phishing_campaign"
    RANSOMWARE = "ransomware"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"
    MIXED_ALERTS = "mixed_alerts"


class Scenario:
    """
    Represents a curated demo scenario with a sequence of alerts.
    """

    def __init__(
        self,
        name: str,
        description: str,
        scenario_type: ScenarioType,
        alerts: List[SecurityAlert],
        metadata: Optional[Dict] = None,
    ):
        """
        Initialize scenario.

        Args:
            name: Scenario name
            description: Scenario description
            scenario_type: Type of scenario
            alerts: List of security alerts in sequence
            metadata: Optional metadata (tactics, techniques, etc.)
        """
        self.name = name
        self.description = description
        self.scenario_type = scenario_type
        self.alerts = alerts
        self.metadata = metadata or {}

        logger.info(
            "Scenario created",
            name=name,
            scenario_type=scenario_type.value,
            alert_count=len(alerts),
        )

    def get_alerts(self) -> List[SecurityAlert]:
        """Get all alerts in the scenario."""
        return self.alerts

    def get_alert_count(self) -> int:
        """Get number of alerts in the scenario."""
        return len(self.alerts)

    def get_summary(self) -> Dict:
        """Get scenario summary."""
        return {
            "name": self.name,
            "description": self.description,
            "scenario_type": self.scenario_type.value,
            "alert_count": len(self.alerts),
            "severity_breakdown": self._get_severity_breakdown(),
            "metadata": self.metadata,
        }

    def _get_severity_breakdown(self) -> Dict[str, int]:
        """Get count of alerts by severity."""
        breakdown = {}
        for alert in self.alerts:
            severity = alert.severity.value
            breakdown[severity] = breakdown.get(severity, 0) + 1
        return breakdown


class ScenarioManager:
    """
    Manages curated demo scenarios for the Agentic SOC.
    """

    def __init__(self):
        """Initialize scenario manager."""
        self.scenarios: Dict[str, Scenario] = {}
        self._load_builtin_scenarios()

        logger.info(
            "ScenarioManager initialized", scenario_count=len(self.scenarios)
        )

    def get_scenario(self, scenario_name: str) -> Optional[Scenario]:
        """
        Get scenario by name.

        Args:
            scenario_name: Name of the scenario

        Returns:
            Scenario instance or None if not found
        """
        scenario = self.scenarios.get(scenario_name)

        if scenario:
            logger.info("Scenario retrieved", scenario_name=scenario_name)
        else:
            logger.warning("Scenario not found", scenario_name=scenario_name)

        return scenario

    def list_scenarios(self) -> List[str]:
        """
        List all available scenario names.

        Returns:
            List of scenario names
        """
        return list(self.scenarios.keys())

    def get_scenario_summary(self, scenario_name: str) -> Optional[Dict]:
        """
        Get summary of a scenario.

        Args:
            scenario_name: Name of the scenario

        Returns:
            Scenario summary dict or None if not found
        """
        scenario = self.get_scenario(scenario_name)
        return scenario.get_summary() if scenario else None

    def register_scenario(self, scenario: Scenario) -> None:
        """
        Register a custom scenario.

        Args:
            scenario: Scenario instance to register
        """
        self.scenarios[scenario.name] = scenario
        logger.info("Scenario registered", scenario_name=scenario.name)

    def _load_builtin_scenarios(self) -> None:
        """Load built-in demo scenarios."""
        # Brute Force Attack Scenario
        self.scenarios["brute_force"] = self._create_brute_force_scenario()

        # Phishing Campaign Scenario
        self.scenarios["phishing_campaign"] = self._create_phishing_scenario()

        # Ransomware Scenario
        self.scenarios["ransomware"] = self._create_ransomware_scenario()

        # Lateral Movement Scenario
        self.scenarios["lateral_movement"] = self._create_lateral_movement_scenario()

        # Mixed Alerts Scenario (for testing prioritization)
        self.scenarios["mixed_alerts"] = self._create_mixed_alerts_scenario()

    def _create_brute_force_scenario(self) -> Scenario:
        """
        Create brute force attack scenario.

        Timeline:
        1. Multiple failed login attempts (20 failures)
        2. Successful login from suspicious IP
        3. Lateral movement attempt
        """
        base_time = datetime.utcnow()
        alerts = []

        # Failed login attempts
        for i in range(20):
            alert = SecurityAlert(
                AlertId=uuid4(),
                TimeGenerated=base_time + timedelta(minutes=i),
                AlertName=f"Failed Login Attempt #{i+1}",
                AlertType="Authentication",
                Severity=Severity.LOW if i < 10 else Severity.MEDIUM,
                Description=f"Failed login attempt from IP 192.168.1.100",
                Tactics=["InitialAccess"],
                Techniques=["T1078"],
                ExtendedProperties={
                    "SourceIP": "192.168.1.100",
                    "TargetAccount": "admin",
                    "AttemptNumber": i + 1,
                },
            )
            alerts.append(alert)

        # Successful login after brute force
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=20),
            AlertName="Successful Login After Multiple Failures",
            AlertType="Authentication",
            Severity=Severity.HIGH,
            Description="Successful login from IP 192.168.1.100 after 20 failed attempts",
            Tactics=["InitialAccess"],
            Techniques=["T1078"],
            ExtendedProperties={
                "SourceIP": "192.168.1.100",
                "TargetAccount": "admin",
                "FailedAttempts": 20,
            },
        )
        alerts.append(alert)

        # Lateral movement
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=25),
            AlertName="Lateral Movement Detected",
            AlertType="LateralMovement",
            Severity=Severity.CRITICAL,
            Description="Suspicious SMB connection to multiple hosts",
            Tactics=["LateralMovement"],
            Techniques=["T1021.002"],
            ExtendedProperties={
                "SourceAccount": "admin",
                "TargetHosts": ["SERVER-01", "SERVER-02", "WORKSTATION-05"],
            },
        )
        alerts.append(alert)

        return Scenario(
            name="brute_force",
            description="Brute force attack leading to successful compromise and lateral movement",
            scenario_type=ScenarioType.BRUTE_FORCE,
            alerts=alerts,
            metadata={
                "tactics": ["InitialAccess", "LateralMovement"],
                "techniques": ["T1078", "T1021.002"],
                "duration_minutes": 25,
                "expected_triage": "P1-Critical",
            },
        )

    def _create_phishing_scenario(self) -> Scenario:
        """
        Create phishing campaign scenario.

        Timeline:
        1. Suspicious email received
        2. User clicks malicious link
        3. Credential theft detected
        4. Data exfiltration attempt
        """
        base_time = datetime.utcnow()
        alerts = []

        # Suspicious email
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time,
            AlertName="Suspicious Email Detected",
            AlertType="Phishing",
            Severity=Severity.MEDIUM,
            Description="Email contains suspicious link and sender spoofing",
            Tactics=["InitialAccess"],
            Techniques=["T1566.002"],
            ExtendedProperties={
                "Sender": "admin@examp1e.com",
                "Recipient": "user@company.com",
                "Subject": "Urgent: Password Reset Required",
            },
        )
        alerts.append(alert)

        # User clicked link
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=5),
            AlertName="User Clicked Suspicious Link",
            AlertType="Phishing",
            Severity=Severity.HIGH,
            Description="User navigated to known phishing site",
            Tactics=["InitialAccess"],
            Techniques=["T1566.002"],
            ExtendedProperties={
                "User": "user@company.com",
                "URL": "http://malicious-site.com/login",
            },
        )
        alerts.append(alert)

        # Credential theft
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=10),
            AlertName="Credential Theft Detected",
            AlertType="CredentialAccess",
            Severity=Severity.CRITICAL,
            Description="Credentials submitted to phishing site",
            Tactics=["CredentialAccess"],
            Techniques=["T1056.003"],
            ExtendedProperties={
                "User": "user@company.com",
                "StolenCredentials": "Username and password",
            },
        )
        alerts.append(alert)

        # Data exfiltration
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=30),
            AlertName="Suspicious Data Exfiltration",
            AlertType="Exfiltration",
            Severity=Severity.CRITICAL,
            Description="Large file upload to external site using stolen credentials",
            Tactics=["Exfiltration"],
            Techniques=["T1567.002"],
            ExtendedProperties={
                "User": "user@company.com",
                "BytesTransferred": 500000000,
                "Destination": "attacker-server.com",
            },
        )
        alerts.append(alert)

        return Scenario(
            name="phishing_campaign",
            description="Phishing attack leading to credential theft and data exfiltration",
            scenario_type=ScenarioType.PHISHING_CAMPAIGN,
            alerts=alerts,
            metadata={
                "tactics": ["InitialAccess", "CredentialAccess", "Exfiltration"],
                "techniques": ["T1566.002", "T1056.003", "T1567.002"],
                "duration_minutes": 30,
                "expected_triage": "P1-Critical",
            },
        )

    def _create_ransomware_scenario(self) -> Scenario:
        """Create ransomware attack scenario."""
        base_time = datetime.utcnow()
        alerts = []

        # Malware execution
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time,
            AlertName="Malware Execution Detected",
            AlertType="Malware",
            Severity=Severity.HIGH,
            Description="Suspicious executable launched from temp directory",
            Tactics=["Execution"],
            Techniques=["T1204.002"],
            ExtendedProperties={
                "FileName": "invoice.exe",
                "FilePath": "C:\\Users\\user\\AppData\\Local\\Temp\\",
                "MD5": "5d41402abc4b2a76b9719d911017c592",
            },
        )
        alerts.append(alert)

        # File encryption
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=2),
            AlertName="Ransomware File Encryption",
            AlertType="Ransomware",
            Severity=Severity.CRITICAL,
            Description="Mass file encryption detected - ransomware activity",
            Tactics=["Impact"],
            Techniques=["T1486"],
            ExtendedProperties={
                "EncryptedFiles": 5000,
                "FileExtension": ".locked",
                "Device": "WORKSTATION-10",
            },
        )
        alerts.append(alert)

        # C2 communication
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=5),
            AlertName="Command and Control Communication",
            AlertType="CommandAndControl",
            Severity=Severity.CRITICAL,
            Description="Communication with known ransomware C2 server",
            Tactics=["CommandAndControl"],
            Techniques=["T1071.001"],
            ExtendedProperties={
                "C2Server": "malware-c2.onion.to",
                "Protocol": "HTTPS",
                "Device": "WORKSTATION-10",
            },
        )
        alerts.append(alert)

        return Scenario(
            name="ransomware",
            description="Ransomware attack with file encryption and C2 communication",
            scenario_type=ScenarioType.RANSOMWARE,
            alerts=alerts,
            metadata={
                "tactics": ["Execution", "Impact", "CommandAndControl"],
                "techniques": ["T1204.002", "T1486", "T1071.001"],
                "duration_minutes": 5,
                "expected_triage": "P1-Critical",
            },
        )

    def _create_lateral_movement_scenario(self) -> Scenario:
        """Create lateral movement scenario."""
        base_time = datetime.utcnow()
        alerts = []

        # Initial compromise
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time,
            AlertName="Suspicious PowerShell Execution",
            AlertType="Execution",
            Severity=Severity.MEDIUM,
            Description="Encoded PowerShell command executed",
            Tactics=["Execution"],
            Techniques=["T1059.001"],
            ExtendedProperties={
                "Device": "WORKSTATION-01",
                "Command": "powershell.exe -encodedCommand ...",
            },
        )
        alerts.append(alert)

        # Credential dumping
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=5),
            AlertName="Credential Dumping Detected",
            AlertType="CredentialAccess",
            Severity=Severity.HIGH,
            Description="LSASS memory access - possible credential theft",
            Tactics=["CredentialAccess"],
            Techniques=["T1003.001"],
            ExtendedProperties={"Device": "WORKSTATION-01", "TargetProcess": "lsass.exe"},
        )
        alerts.append(alert)

        # Lateral movement
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=10),
            AlertName="SMB Lateral Movement",
            AlertType="LateralMovement",
            Severity=Severity.HIGH,
            Description="Suspicious SMB connection to domain controller",
            Tactics=["LateralMovement"],
            Techniques=["T1021.002"],
            ExtendedProperties={
                "SourceDevice": "WORKSTATION-01",
                "TargetDevice": "DC-01",
                "Protocol": "SMB",
            },
        )
        alerts.append(alert)

        return Scenario(
            name="lateral_movement",
            description="Lateral movement attack with credential theft",
            scenario_type=ScenarioType.LATERAL_MOVEMENT,
            alerts=alerts,
            metadata={
                "tactics": ["Execution", "CredentialAccess", "LateralMovement"],
                "techniques": ["T1059.001", "T1003.001", "T1021.002"],
                "duration_minutes": 10,
                "expected_triage": "P2-High",
            },
        )

    def _create_mixed_alerts_scenario(self) -> Scenario:
        """Create mixed alerts scenario for testing prioritization."""
        base_time = datetime.utcnow()
        alerts = []

        # Low severity - false positive
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time,
            AlertName="Routine Software Update",
            AlertType="Informational",
            Severity=Severity.INFORMATIONAL,
            Description="Scheduled software update executed",
            Tactics=[],
            Techniques=[],
        )
        alerts.append(alert)

        # Critical alert - real threat
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=1),
            AlertName="Active Directory Compromise",
            AlertType="CredentialAccess",
            Severity=Severity.CRITICAL,
            Description="Domain Admin credentials compromised",
            Tactics=["CredentialAccess"],
            Techniques=["T1003.003"],
        )
        alerts.append(alert)

        # Medium severity - benign
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=2),
            AlertName="Failed Login - User Error",
            AlertType="Authentication",
            Severity=Severity.MEDIUM,
            Description="User forgot password - 3 failed attempts",
            Tactics=["InitialAccess"],
            Techniques=["T1078"],
        )
        alerts.append(alert)

        # High severity - needs investigation
        alert = SecurityAlert(
            AlertId=uuid4(),
            TimeGenerated=base_time + timedelta(minutes=3),
            AlertName="Suspicious Network Traffic",
            AlertType="CommandAndControl",
            Severity=Severity.HIGH,
            Description="Connection to suspicious domain",
            Tactics=["CommandAndControl"],
            Techniques=["T1071.001"],
        )
        alerts.append(alert)

        return Scenario(
            name="mixed_alerts",
            description="Mixed severity alerts for testing triage prioritization",
            scenario_type=ScenarioType.MIXED_ALERTS,
            alerts=alerts,
            metadata={
                "expected_order": [
                    "Active Directory Compromise (Critical)",
                    "Suspicious Network Traffic (High)",
                    "Failed Login - User Error (Medium)",
                    "Routine Software Update (Informational)",
                ],
            },
        )


# =============================================================================
# Convenience Functions
# =============================================================================


def get_scenario_manager() -> ScenarioManager:
    """
    Get singleton scenario manager instance.

    Returns:
        ScenarioManager instance
    """
    return ScenarioManager()


def list_available_scenarios() -> List[str]:
    """
    List all available scenario names.

    Returns:
        List of scenario names
    """
    manager = get_scenario_manager()
    return manager.list_scenarios()
