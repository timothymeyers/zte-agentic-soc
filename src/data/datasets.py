"""
Mock data loader for Agentic SOC.

Loads and transforms GUIDE and Attack datasets to Sentinel-compatible format.
"""

import os
from pathlib import Path
from typing import Iterator, List, Optional
from uuid import uuid4

import pandas as pd

from src.shared.logging import get_logger
from src.shared.models import SecurityAlert, Severity

logger = get_logger(__name__, module="datasets")


class DatasetLoader:
    """
    Load and transform mock data from GUIDE and Attack datasets.
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize dataset loader.

        Args:
            data_dir: Path to mock data directory. Defaults to MOCK_DATA_DIR env var
                     or 'mock-data' relative to project root.
        """
        if data_dir is None:
            data_dir = os.getenv("MOCK_DATA_DIR", "mock-data")

        self.data_dir = Path(data_dir)
        if not self.data_dir.is_absolute():
            # Make relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.data_dir = project_root / self.data_dir

        logger.info("Dataset loader initialized", data_dir=str(self.data_dir))

        if not self.data_dir.exists():
            logger.warning("Data directory does not exist", data_dir=str(self.data_dir))

    def load_attack_dataset(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load Attack dataset CSV.

        Args:
            limit: Maximum number of rows to load. If None, loads all rows.

        Returns:
            DataFrame with attack scenarios

        Raises:
            FileNotFoundError: If Attack_Dataset.csv not found
        """
        attack_file = self.data_dir / "Attack_Dataset.csv"

        if not attack_file.exists():
            raise FileNotFoundError(f"Attack dataset not found: {attack_file}")

        logger.info("Loading attack dataset", file=str(attack_file), limit=limit)

        # Load with pandas - handle large file efficiently
        if limit:
            df = pd.read_csv(attack_file, nrows=limit)
        else:
            df = pd.read_csv(attack_file)

        logger.info(
            "Attack dataset loaded",
            rows=len(df),
            columns=len(df.columns),
            categories=df["Category"].nunique() if "Category" in df.columns else 0,
        )

        return df

    def load_guide_dataset(
        self,
        split: str = "test",
        file_index: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Load GUIDE dataset CSV files.

        Args:
            split: 'train' or 'test'
            file_index: Specific file index (0-24 for train, 0-10 for test).
                       If None, loads first file.
            limit: Maximum number of rows to load. If None, loads all rows.

        Returns:
            DataFrame with security incidents

        Raises:
            FileNotFoundError: If GUIDE file not found
            ValueError: If invalid split or file_index
        """
        if split not in ("train", "test"):
            raise ValueError(f"Invalid split: {split}. Must be 'train' or 'test'.")

        if file_index is None:
            file_index = 0

        # Validate file index
        max_index = 24 if split == "train" else 10
        if not 0 <= file_index <= max_index:
            raise ValueError(
                f"Invalid file_index: {file_index}. "
                f"Must be 0-{max_index} for split='{split}'."
            )

        # Construct filename
        filename = f"GUIDE_{split.capitalize()}_{file_index:02d}.csv"
        guide_file = self.data_dir / filename

        if not guide_file.exists():
            raise FileNotFoundError(f"GUIDE file not found: {guide_file}")

        logger.info("Loading GUIDE dataset", file=str(guide_file), limit=limit)

        # Load with pandas
        if limit:
            df = pd.read_csv(guide_file, nrows=limit)
        else:
            df = pd.read_csv(guide_file)

        logger.info(
            "GUIDE dataset loaded",
            split=split,
            file_index=file_index,
            rows=len(df),
            columns=len(df.columns),
        )

        return df

    def guide_to_sentinel_alert(self, row: pd.Series) -> SecurityAlert:
        """
        Transform GUIDE dataset row to Sentinel SecurityAlert format.

        Args:
            row: Single row from GUIDE dataset

        Returns:
            SecurityAlert model instance
        """
        # Map IncidentGrade to Severity
        grade_to_severity = {
            "TruePositive": Severity.HIGH,
            "BenignPositive": Severity.LOW,
            "FalsePositive": Severity.INFORMATIONAL,
        }

        incident_grade = row.get("IncidentGrade", "BenignPositive")
        severity = grade_to_severity.get(incident_grade, Severity.MEDIUM)

        # Extract MITRE techniques
        techniques = []
        if pd.notna(row.get("MitreTechniques")):
            techniques = str(row["MitreTechniques"]).split(";")

        # Map Category to tactics
        tactics = []
        category = row.get("Category", "")
        if category:
            tactics = [category]

        # Build extended properties
        extended_props = {}
        for key in [
            "OrgId",
            "IncidentId",
            "DetectorId",
            "EntityType",
            "EvidenceRole",
            "DeviceId",
            "ThreatFamily",
            "Usage",
        ]:
            if pd.notna(row.get(key)):
                extended_props[key] = str(row[key])

        # Build entities list
        entities = []

        # Add device entity if present
        if pd.notna(row.get("DeviceName")):
            entities.append(
                {"Type": "device", "Name": str(row["DeviceName"]), "DeviceId": str(row.get("DeviceId", ""))}
            )

        # Add user entity if present
        if pd.notna(row.get("AccountName")):
            entities.append(
                {
                    "Type": "account",
                    "Name": str(row["AccountName"]),
                    "Upn": str(row.get("AccountUpn", "")),
                }
            )

        # Add IP entity if present
        if pd.notna(row.get("IpAddress")):
            entities.append({"Type": "ip", "Address": str(row["IpAddress"])})

        # Create SecurityAlert
        alert = SecurityAlert(
            AlertId=uuid4(),
            AlertName=str(row.get("AlertTitle", "Unknown Alert")),
            AlertType=str(row.get("Category", "Unknown")),
            Severity=severity,
            Description=f"Incident Grade: {incident_grade}. Detector ID: {row.get('DetectorId', 'Unknown')}",
            Tactics=tactics,
            Techniques=techniques,
            ExtendedProperties=extended_props,
            Entities=entities,
        )

        return alert

    def attack_to_sentinel_alert(self, row: pd.Series) -> SecurityAlert:
        """
        Transform Attack dataset row to Sentinel SecurityAlert format.

        Args:
            row: Single row from Attack dataset

        Returns:
            SecurityAlert model instance
        """
        # Map Category to severity (simplified heuristic)
        high_severity_categories = [
            "Ransomware",
            "Data Breach",
            "Zero-Day",
            "Supply Chain",
            "Critical Infrastructure",
        ]

        category = row.get("Category", "")
        if any(cat in category for cat in high_severity_categories):
            severity = Severity.CRITICAL
        else:
            severity = Severity.HIGH

        # Extract MITRE techniques
        techniques = []
        if pd.notna(row.get("MITRE Technique")):
            techniques = str(row["MITRE Technique"]).split(",")
            techniques = [t.strip() for t in techniques]

        # Extract tags as tactics (simplified)
        tactics = []
        if pd.notna(row.get("Tags")):
            tags = str(row["Tags"]).split(",")
            # Use first tag as tactic
            if tags:
                tactics = [tags[0].strip("#").strip()]

        # Build extended properties
        extended_props = {
            "AttackType": str(row.get("Attack Type", "")),
            "TargetType": str(row.get("Target Type", "")),
            "Vulnerability": str(row.get("Vulnerability", "")),
            "Impact": str(row.get("Impact", "")),
            "ToolsUsed": str(row.get("Tools Used", "")),
            "Source": str(row.get("Source", "")),
        }

        # Create SecurityAlert
        alert = SecurityAlert(
            AlertId=uuid4(),
            AlertName=str(row.get("Title", "Unknown Attack")),
            AlertType=str(row.get("Attack Type", "Unknown")),
            Severity=severity,
            Description=str(row.get("Scenario Description", "No description available")),
            RemediationSteps=str(row.get("Solution", "")),
            Tactics=tactics,
            Techniques=techniques,
            ExtendedProperties=extended_props,
            Entities=[],  # Attack dataset doesn't have specific entities
        )

        return alert

    def stream_guide_alerts(
        self,
        split: str = "test",
        file_index: int = 0,
        limit: Optional[int] = None,
    ) -> Iterator[SecurityAlert]:
        """
        Stream GUIDE alerts one at a time.

        Args:
            split: 'train' or 'test'
            file_index: GUIDE file index
            limit: Maximum number of alerts to stream

        Yields:
            SecurityAlert instances
        """
        df = self.load_guide_dataset(split=split, file_index=file_index, limit=limit)

        logger.info("Starting GUIDE alert stream", count=len(df))

        for idx, row in df.iterrows():
            try:
                alert = self.guide_to_sentinel_alert(row)
                yield alert
            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    "Failed to transform GUIDE row",
                    row_index=idx,
                    error=str(e),
                    exc_info=True,
                )
                continue

    def stream_attack_alerts(
        self, limit: Optional[int] = None
    ) -> Iterator[SecurityAlert]:
        """
        Stream Attack dataset alerts one at a time.

        Args:
            limit: Maximum number of alerts to stream

        Yields:
            SecurityAlert instances
        """
        df = self.load_attack_dataset(limit=limit)

        logger.info("Starting Attack alert stream", count=len(df))

        for idx, row in df.iterrows():
            try:
                alert = self.attack_to_sentinel_alert(row)
                yield alert
            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    "Failed to transform Attack row",
                    row_index=idx,
                    error=str(e),
                    exc_info=True,
                )
                continue


# =============================================================================
# Convenience Functions
# =============================================================================


def get_sample_alerts(count: int = 10, dataset: str = "guide") -> List[SecurityAlert]:
    """
    Get a sample of alerts for testing.

    Args:
        count: Number of alerts to return
        dataset: 'guide' or 'attack'

    Returns:
        List of SecurityAlert instances
    """
    loader = DatasetLoader()

    alerts = []
    if dataset == "guide":
        for alert in loader.stream_guide_alerts(limit=count):
            alerts.append(alert)
    elif dataset == "attack":
        for alert in loader.stream_attack_alerts(limit=count):
            alerts.append(alert)
    else:
        raise ValueError(f"Invalid dataset: {dataset}. Must be 'guide' or 'attack'.")

    return alerts
