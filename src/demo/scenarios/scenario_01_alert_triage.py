"""
Scenario 01: Alert Triage Demonstration

Demonstrates the Alert Triage Agent analyzing a batch of mixed alerts
(critical, high, medium, low) and producing risk scores, prioritization,
correlation detection, and natural language explanations.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.data.scenarios import Scenario, ScenarioType
from src.orchestration.orchestrator import SOCOrchestrator
from src.shared.logging import get_logger
from src.shared.models import SecurityAlert, Severity

logger = get_logger(__name__, module="scenario_01")


def create_alert_triage_scenario() -> Scenario:
    """
    Create a mixed alert batch scenario for triage demonstration.
    
    Includes:
    - Critical: Data exfiltration with compromised admin account
    - High: Brute force attack with lateral movement
    - Medium: Suspicious PowerShell execution
    - Low: Failed login from corporate network (false positive)
    
    Returns:
        Scenario instance with mixed alerts
    """
    base_time = datetime.now(timezone.utc)
    
    # Alert 1: CRITICAL - Data Exfiltration
    alert1 = SecurityAlert(
        AlertId=str(uuid4()),
        TimeGenerated=base_time - timedelta(minutes=5),
        AlertName="Suspicious Data Transfer to External Cloud Service",
        AlertType="DataExfiltration",
        Severity=Severity.CRITICAL,
        Description=(
            "Administrator account 'admin@contoso.com' transferred 2.5 GB of data "
            "to an external cloud storage service (dropbox.com) at 3:15 AM. "
            "The account accessed multiple sensitive file shares before the transfer."
        ),
        Tactics=["Exfiltration", "Collection"],
        Techniques=["T1048", "T1074"],
        Entities=[
            {
                "Type": "Account",
                "Properties": {
                    "Name": "admin@contoso.com",
                    "UPNSuffix": "contoso.com",
                    "IsDomainAdmin": True,
                }
            },
            {
                "Type": "IP",
                "Properties": {
                    "Address": "192.168.1.50",
                    "Location": "Internal Network",
                }
            },
            {
                "Type": "URL",
                "Properties": {
                    "Url": "https://dropbox.com",
                }
            },
        ],
        ExtendedProperties={
            "DataVolume": "2.5 GB",
            "TransferTime": "03:15:00",
            "SourceShares": ["\\\\fileserver\\finance", "\\\\fileserver\\hr"],
        },
    )
    
    # Alert 2: HIGH - Brute Force with Lateral Movement
    alert2 = SecurityAlert(
        AlertId=str(uuid4()),
        TimeGenerated=base_time - timedelta(minutes=15),
        AlertName="Brute Force Attack Followed by Lateral Movement",
        AlertType="BruteForce",
        Severity=Severity.HIGH,
        Description=(
            "Account 'jdoe@contoso.com' experienced 45 failed login attempts from "
            "IP 203.0.113.42 (Russia) over 10 minutes, followed by successful login. "
            "Immediately after, the account accessed 5 different servers via SMB."
        ),
        Tactics=["InitialAccess", "LateralMovement"],
        Techniques=["T1110", "T1021.002"],
        Entities=[
            {
                "Type": "Account",
                "Properties": {
                    "Name": "jdoe@contoso.com",
                    "UPNSuffix": "contoso.com",
                }
            },
            {
                "Type": "IP",
                "Properties": {
                    "Address": "203.0.113.42",
                    "Location": "Russia",
                    "GeoData": {"Country": "RU", "City": "Moscow"},
                }
            },
            {
                "Type": "Host",
                "Properties": {
                    "HostName": "WEB-SERVER-01",
                },
            },
        ],
        ExtendedProperties={
            "FailedAttempts": 45,
            "SuccessfulLogin": True,
            "AccessedServers": [
                "SQL-SERVER-01",
                "FILE-SERVER-02",
                "DC-01",
                "BACKUP-01",
                "APP-SERVER-03",
            ],
        },
    )
    
    # Alert 3: MEDIUM - Suspicious PowerShell
    alert3 = SecurityAlert(
        AlertId=str(uuid4()),
        TimeGenerated=base_time - timedelta(minutes=30),
        AlertName="Suspicious PowerShell Execution",
        AlertType="ExecutionAnomaly",
        Severity=Severity.MEDIUM,
        Description=(
            "User 'marketing@contoso.com' executed a PowerShell command with "
            "base64-encoded payload on workstation WS-MARKETING-12. "
            "Command history shows download from pastebin.com."
        ),
        Tactics=["Execution"],
        Techniques=["T1059.001"],
        Entities=[
            {
                "Type": "Account",
                "Properties": {
                    "Name": "marketing@contoso.com",
                    "UPNSuffix": "contoso.com",
                }
            },
            {
                "Type": "Host",
                "Properties": {
                    "HostName": "WS-MARKETING-12",
                },
            },
            {
                "Type": "Process",
                "Properties": {
                    "ProcessName": "powershell.exe",
                    "CommandLine": "powershell.exe -enc aQBlAHgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQA...",
                },
            },
        ],
        ExtendedProperties={
            "EncodedPayload": True,
            "DownloadSource": "pastebin.com",
        },
    )
    
    # Alert 4: LOW - False Positive (Password Mistype)
    alert4 = SecurityAlert(
        AlertId=str(uuid4()),
        TimeGenerated=base_time - timedelta(minutes=10),
        AlertName="Multiple Failed Login Attempts",
        AlertType="AuthenticationFailure",
        Severity=Severity.LOW,
        Description=(
            "User 'employee@contoso.com' had 3 failed login attempts from "
            "corporate IP 10.0.1.25 at 9:00 AM, followed by successful login."
        ),
        Tactics=["InitialAccess"],
        Techniques=["T1078"],
        Entities=[
            {
                "Type": "Account",
                "Properties": {
                    "Name": "employee@contoso.com",
                    "UPNSuffix": "contoso.com",
                }
            },
            {
                "Type": "IP",
                "Properties": {
                    "Address": "10.0.1.25",
                    "Location": "Corporate Network - Seattle Office",
                }
            },
        ],
        ExtendedProperties={
            "FailedAttempts": 3,
            "SuccessfulLogin": True,
            "TimeOfDay": "09:00:00",
            "IsBusinessHours": True,
        },
    )
    
    alerts = [alert1, alert2, alert3, alert4]
    
    scenario = Scenario(
        name="Alert Triage - Mixed Severity Batch",
        description=(
            "Demonstrates Alert Triage Agent analyzing a realistic mix of security alerts. "
            "Includes critical data exfiltration, high-severity brute force with lateral movement, "
            "medium-severity suspicious PowerShell execution, and low-severity false positive. "
            "Tests risk scoring, prioritization, correlation detection, and natural language explanations."
        ),
        scenario_type=ScenarioType.MIXED_ALERTS,
        alerts=alerts,
        metadata={
            "expected_outcomes": {
                "alert1": "Critical priority - Escalate to incident",
                "alert2": "High priority - Investigate immediately",
                "alert3": "Medium priority - Investigate within 4-8 hours",
                "alert4": "Low priority - Document as false positive",
            },
            "correlation_opportunities": [
                "Alert 1 and Alert 2 may be related (compromised accounts)",
                "Alert 3 could be reconnaissance for Alert 1 or 2",
            ],
        },
    )
    
    logger.info(
        "Alert triage scenario created",
        alert_count=len(alerts),
        severities=[a.severity.value for a in alerts],
    )
    
    return scenario


async def run_alert_triage_scenario():
    """
    Run the alert triage scenario end-to-end.
    
    Steps:
    1. Create scenario with mixed alerts
    2. Initialize SOC orchestrator
    3. Stream alerts to triage agent
    4. Display triage results with risk scores and explanations
    """
    logger.info("Starting Alert Triage Scenario (Scenario 01)")
    
    print("\n" + "=" * 80)
    print("SCENARIO 01: Alert Triage Demonstration")
    print("=" * 80)
    print("\nObjective: Demonstrate Alert Triage Agent's ability to:")
    print("  • Analyze mixed-severity alerts")
    print("  • Assign accurate risk scores and priorities")
    print("  • Detect correlated alerts")
    print("  • Provide natural language explanations")
    print("=" * 80)
    
    # Create scenario
    scenario = create_alert_triage_scenario()
    alerts = scenario.get_alerts()
    
    print(f"\nLoaded {len(alerts)} alerts for triage:")
    for i, alert in enumerate(alerts, 1):
        print(f"  {i}. [{alert.severity.value}] {alert.alert_name}")
    
    print("\n" + "-" * 80)
    print("Initializing SOC Orchestrator...")
    print("-" * 80)
    
    try:
        # Initialize orchestrator
        orchestrator = SOCOrchestrator()
        
        # Create workflow (agents are discovered internally by the orchestrator)
        print("\n" + "-" * 80)
        print("Creating magentic workflow and loading agents from Microsoft Foundry...")
        print("-" * 80)
        
        workflow = await orchestrator.create_workflow()
        print("\n✓ Workflow created successfully")
        
        # Process each alert through the workflow
        print("\n" + "=" * 80)
        print("PROCESSING ALERTS THROUGH TRIAGE AGENT")
        print("=" * 80)
        
        for i, alert in enumerate(alerts, 1):
            print(f"\n--- Alert {i}/{len(alerts)} ---")
            print(f"Name: {alert.alert_name}")
            print(f"Severity: {alert.severity.value}")
            print(f"Description: {alert.description[:100]}...")
            
            # Create triage request message
            triage_request = f"""
            Analyze the following security alert and provide triage assessment:
            
            Alert ID: {alert.alert_id}
            Alert Name: {alert.alert_name}
            Severity: {alert.severity.value}
            Description: {alert.description}
            Tactics: {', '.join(alert.tactics)}
            Techniques: {', '.join(alert.techniques)}
            
            Provide risk assessment, priority level, and actionable recommendations.
            """
            
            print("\nSending to triage agent...")
            
            # Run workflow with alert
            try:
                async for event in workflow.run_stream(triage_request):
                    # Process workflow events
                    if hasattr(event, "agent_name"):
                        print(f"  → {event.agent_name}: {event.message[:100]}...")
                    
                print("  ✓ Triage complete")
                
            except Exception as e:
                logger.error(
                    "Workflow execution failed",
                    alert_id=str(alert.alert_id),
                    error=str(e),
                    exc_info=True,
                )
                print(f"  ❌ Triage failed: {e}")
        
        print("\n" + "=" * 80)
        print("SCENARIO COMPLETE")
        print("=" * 80)
        print("\nAll alerts processed through Alert Triage Agent.")
        print("Review the triage results above for risk scores, priorities, and recommendations.")
        
    except Exception as e:
        logger.error("Scenario execution failed", error=str(e), exc_info=True)
        print(f"\n❌ Scenario failed: {e}")
        raise


async def main():
    """Main entry point for scenario execution."""
    await run_alert_triage_scenario()


if __name__ == "__main__":
    asyncio.run(main())
