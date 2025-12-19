"""
Mock data streaming module for Agentic SOC.

Implements configurable alert streaming with checkpoint-based replay functionality.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Dict, Optional

from src.data.datasets import DatasetLoader
from src.shared.logging import get_logger
from src.shared.models import SecurityAlert

logger = get_logger(__name__, module="streaming")


class MockDataStreamer:
    """
    Stream mock security alerts with configurable intervals and checkpoint replay.
    """

    def __init__(
        self,
        interval_seconds: Optional[float] = None,
        checkpoint_file: Optional[str] = None,
        dataset: str = "guide",
        guide_split: str = "test",
        guide_file_index: int = 0,
    ):
        """
        Initialize mock data streamer.

        Args:
            interval_seconds: Time between alerts in seconds.
                            Defaults to MOCK_DATA_INTERVAL env var or 15.0.
            checkpoint_file: Path to checkpoint file for replay.
                           Defaults to MOCK_DATA_CHECKPOINT_FILE env var.
            dataset: 'guide' or 'attack'
            guide_split: 'train' or 'test' (only for guide dataset)
            guide_file_index: GUIDE file index (only for guide dataset)
        """
        if interval_seconds is None:
            interval_seconds = float(os.getenv("MOCK_DATA_INTERVAL", "15.0"))

        if checkpoint_file is None:
            checkpoint_file = os.getenv(
                "MOCK_DATA_CHECKPOINT_FILE", ".mock_data_checkpoint.json"
            )

        self.interval_seconds = interval_seconds
        self.checkpoint_file = Path(checkpoint_file)
        self.dataset = dataset
        self.guide_split = guide_split
        self.guide_file_index = guide_file_index

        self.loader = DatasetLoader()
        self.current_index = 0
        self.total_streamed = 0

        logger.info(
            "MockDataStreamer initialized",
            interval_seconds=interval_seconds,
            checkpoint_file=str(checkpoint_file),
            dataset=dataset,
        )

    def load_checkpoint(self) -> Dict:
        """
        Load checkpoint from file.

        Returns:
            Checkpoint data with 'index', 'total_streamed', 'timestamp'

        Note:
            Returns empty checkpoint if file doesn't exist or is invalid.
        """
        if not self.checkpoint_file.exists():
            logger.info("No checkpoint file found", file=str(self.checkpoint_file))
            return {"index": 0, "total_streamed": 0, "timestamp": None}

        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)

            logger.info(
                "Checkpoint loaded",
                index=checkpoint.get("index", 0),
                total_streamed=checkpoint.get("total_streamed", 0),
            )

            return checkpoint

        except Exception as e:  # pylint: disable=broad-except
            logger.error(
                "Failed to load checkpoint",
                file=str(self.checkpoint_file),
                error=str(e),
                exc_info=True,
            )
            return {"index": 0, "total_streamed": 0, "timestamp": None}

    def save_checkpoint(self) -> None:
        """
        Save current position to checkpoint file.
        """
        checkpoint = {
            "index": self.current_index,
            "total_streamed": self.total_streamed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset": self.dataset,
        }

        try:
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, indent=2)

            logger.debug(
                "Checkpoint saved",
                index=self.current_index,
                total_streamed=self.total_streamed,
            )

        except Exception as e:  # pylint: disable=broad-except
            logger.error(
                "Failed to save checkpoint",
                file=str(self.checkpoint_file),
                error=str(e),
                exc_info=True,
            )

    def reset_checkpoint(self) -> None:
        """
        Delete checkpoint file and reset counters.
        """
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
                logger.info("Checkpoint file deleted", file=str(self.checkpoint_file))
            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    "Failed to delete checkpoint",
                    file=str(self.checkpoint_file),
                    error=str(e),
                )

        self.current_index = 0
        self.total_streamed = 0
        logger.info("Checkpoint reset")

    async def stream_alerts(
        self,
        limit: Optional[int] = None,
        resume_from_checkpoint: bool = False,
    ) -> AsyncIterator[SecurityAlert]:
        """
        Stream security alerts asynchronously with configurable delay.

        Args:
            limit: Maximum number of alerts to stream. If None, streams all.
            resume_from_checkpoint: If True, resume from saved checkpoint.

        Yields:
            SecurityAlert instances

        Example:
            >>> streamer = MockDataStreamer(interval_seconds=1.0)
            >>> async for alert in streamer.stream_alerts(limit=10):
            ...     print(f"Alert: {alert.alert_name}")
        """
        # Load checkpoint if requested
        if resume_from_checkpoint:
            checkpoint = self.load_checkpoint()
            self.current_index = checkpoint.get("index", 0)
            self.total_streamed = checkpoint.get("total_streamed", 0)

            logger.info(
                "Resuming from checkpoint",
                index=self.current_index,
                total_streamed=self.total_streamed,
            )

        # Get alert iterator
        if self.dataset == "guide":
            alert_iter = self.loader.stream_guide_alerts(
                split=self.guide_split,
                file_index=self.guide_file_index,
                limit=limit,
            )
        elif self.dataset == "attack":
            alert_iter = self.loader.stream_attack_alerts(limit=limit)
        else:
            raise ValueError(
                f"Invalid dataset: {self.dataset}. Must be 'guide' or 'attack'."
            )

        # Skip to checkpoint position
        for _ in range(self.current_index):
            try:
                next(alert_iter)
            except StopIteration:
                logger.warning(
                    "Checkpoint position exceeds dataset length",
                    checkpoint_index=self.current_index,
                )
                break

        # Stream alerts with delay
        logger.info(
            "Starting alert stream",
            interval_seconds=self.interval_seconds,
            limit=limit,
            dataset=self.dataset,
        )

        count = 0
        async for alert in self._async_iterator_wrapper(alert_iter):
            if limit and count >= limit:
                break

            yield alert

            self.current_index += 1
            self.total_streamed += 1
            count += 1

            # Save checkpoint periodically (every 10 alerts)
            if self.total_streamed % 10 == 0:
                self.save_checkpoint()

            # Wait before next alert
            await asyncio.sleep(self.interval_seconds)

        # Final checkpoint save
        self.save_checkpoint()

        logger.info(
            "Alert stream complete",
            total_streamed=self.total_streamed,
            current_index=self.current_index,
        )

    async def _async_iterator_wrapper(self, sync_iter):
        """
        Wrap synchronous iterator to async iterator.

        Args:
            sync_iter: Synchronous iterator

        Yields:
            Items from sync_iter
        """
        for item in sync_iter:
            yield item


# =============================================================================
# Convenience Functions
# =============================================================================


async def stream_sample_alerts(
    count: int = 10,
    interval_seconds: float = 1.0,
    dataset: str = "guide",
) -> AsyncIterator[SecurityAlert]:
    """
    Stream a sample of alerts for testing.

    Args:
        count: Number of alerts to stream
        interval_seconds: Time between alerts
        dataset: 'guide' or 'attack'

    Yields:
        SecurityAlert instances

    Example:
        >>> async for alert in stream_sample_alerts(count=5, interval_seconds=0.5):
        ...     print(f"Alert: {alert.alert_name}")
    """
    streamer = MockDataStreamer(
        interval_seconds=interval_seconds,
        dataset=dataset,
    )

    async for alert in streamer.stream_alerts(limit=count):
        yield alert


async def test_streaming():
    """
    Test function to demonstrate streaming functionality.
    """
    print("Testing mock data streaming...")
    print("-" * 60)

    streamer = MockDataStreamer(interval_seconds=0.5, dataset="guide")

    count = 0
    async for alert in streamer.stream_alerts(limit=5):
        count += 1
        print(f"\n[Alert {count}]")
        print(f"  Name: {alert.alert_name}")
        print(f"  Severity: {alert.severity.value}")
        print(f"  Type: {alert.alert_type}")
        print(f"  Tactics: {', '.join(alert.tactics)}")

    print("\n" + "-" * 60)
    print("Streaming test complete!")


if __name__ == "__main__":
    # Run test when module is executed directly
    asyncio.run(test_streaming())
