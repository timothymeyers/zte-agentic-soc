"""
Mock data streamer for simulating real-time alert ingestion.

This module streams alerts at configurable intervals with checkpoint-based
replay for reproducible demonstrations.
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable, Awaitable
from pathlib import Path
import json

from src.shared.schemas import SecurityAlert
from src.shared.logging import get_logger
from src.data.datasets import get_guide_loader


logger = get_logger(__name__)


class MockDataStreamer:
    """Streams mock alerts at configurable intervals."""
    
    def __init__(
        self,
        interval_seconds: int = 15,
        checkpoint_file: str = "./mock-data/checkpoint.json"
    ):
        """
        Initialize mock data streamer.
        
        Args:
            interval_seconds: Interval between alert streams
            checkpoint_file: Path to checkpoint file for replay
        """
        self.interval_seconds = interval_seconds
        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._is_streaming = False
        self._current_index = 0
        self._alert_cache: list[SecurityAlert] = []
        
        logger.info(
            f"Mock data streamer initialized",
            interval_seconds=interval_seconds,
            checkpoint_file=str(checkpoint_file)
        )
    
    def _load_checkpoint(self) -> int:
        """
        Load checkpoint from file.
        
        Returns:
            int: Last processed alert index
        """
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    index = data.get('last_index', 0)
                    logger.info(f"Loaded checkpoint: index={index}")
                    return index
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
        return 0
    
    def _save_checkpoint(self) -> None:
        """Save current checkpoint to file."""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump({
                    'last_index': self._current_index,
                    'timestamp': datetime.utcnow().isoformat()
                }, f)
            logger.debug(f"Saved checkpoint: index={self._current_index}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def _load_alerts(self, count: int = 1000) -> None:
        """
        Load alerts into cache.
        
        Args:
            count: Number of alerts to load
        """
        loader = get_guide_loader()
        self._alert_cache = loader.load_alerts(max_alerts=count)
        logger.info(f"Loaded {len(self._alert_cache)} alerts into cache")
    
    async def start_streaming(
        self,
        callback: Callable[[SecurityAlert], Awaitable[None]],
        max_alerts: Optional[int] = None
    ) -> None:
        """
        Start streaming alerts.
        
        Args:
            callback: Async function to call for each alert
            max_alerts: Maximum number of alerts to stream (None for infinite)
        """
        if self._is_streaming:
            logger.warning("Streamer already running")
            return
        
        self._is_streaming = True
        self._current_index = self._load_checkpoint()
        
        # Load alerts if cache is empty
        if not self._alert_cache:
            self._load_alerts()
        
        logger.info(
            "Starting alert stream",
            interval_seconds=self.interval_seconds,
            max_alerts=max_alerts,
            starting_index=self._current_index
        )
        
        alerts_streamed = 0
        
        try:
            while self._is_streaming:
                if max_alerts and alerts_streamed >= max_alerts:
                    logger.info(f"Reached max alerts limit: {max_alerts}")
                    break
                
                # Get next alert (circular buffer)
                alert_index = self._current_index % len(self._alert_cache)
                alert = self._alert_cache[alert_index]
                
                # Stream alert
                try:
                    await callback(alert)
                    logger.debug(
                        "alert_streamed",
                        alert_id=str(alert.SystemAlertId),
                        alert_name=alert.AlertName,
                        index=self._current_index
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing alert: {e}",
                        alert_id=str(alert.SystemAlertId),
                        error=str(e)
                    )
                
                self._current_index += 1
                alerts_streamed += 1
                
                # Save checkpoint periodically
                if self._current_index % 10 == 0:
                    self._save_checkpoint()
                
                # Wait for next interval
                await asyncio.sleep(self.interval_seconds)
        
        finally:
            self._save_checkpoint()
            logger.info(
                "Alert stream stopped",
                total_streamed=alerts_streamed,
                final_index=self._current_index
            )
    
    def stop_streaming(self) -> None:
        """Stop streaming alerts."""
        if self._is_streaming:
            self._is_streaming = False
            logger.info("Stopping alert stream")
    
    def reset_checkpoint(self) -> None:
        """Reset checkpoint to start from beginning."""
        self._current_index = 0
        self._save_checkpoint()
        logger.info("Checkpoint reset to 0")


# Global streamer instance
_streamer: Optional[MockDataStreamer] = None


def get_streamer(
    interval_seconds: int = 15,
    checkpoint_file: str = "./mock-data/checkpoint.json"
) -> MockDataStreamer:
    """
    Get global mock data streamer instance.
    
    Args:
        interval_seconds: Interval between alerts
        checkpoint_file: Path to checkpoint file
    
    Returns:
        MockDataStreamer: Global streamer instance
    """
    global _streamer
    if _streamer is None:
        _streamer = MockDataStreamer(interval_seconds, checkpoint_file)
    return _streamer
