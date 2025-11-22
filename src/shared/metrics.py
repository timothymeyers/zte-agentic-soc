"""
Metrics collection module using Prometheus-style counters and histograms.

This module provides standardized metrics for monitoring agent performance
and system health.
"""

from typing import Dict, Optional
import time
from contextlib import contextmanager


class Counter:
    """Simple counter metric."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize counter.
        
        Args:
            name: Metric name
            description: Metric description
        """
        self.name = name
        self.description = description
        self._value = 0
    
    def inc(self, amount: float = 1) -> None:
        """
        Increment counter.
        
        Args:
            amount: Amount to increment by
        """
        self._value += amount
    
    def get(self) -> float:
        """Get current counter value."""
        return self._value


class Histogram:
    """Simple histogram metric for tracking distributions."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize histogram.
        
        Args:
            name: Metric name
            description: Metric description
        """
        self.name = name
        self.description = description
        self._observations: list[float] = []
    
    def observe(self, value: float) -> None:
        """
        Record an observation.
        
        Args:
            value: Value to observe
        """
        self._observations.append(value)
    
    def get_count(self) -> int:
        """Get number of observations."""
        return len(self._observations)
    
    def get_sum(self) -> float:
        """Get sum of all observations."""
        return sum(self._observations)
    
    def get_average(self) -> float:
        """Get average of observations."""
        if not self._observations:
            return 0.0
        return self.get_sum() / self.get_count()


class MetricsRegistry:
    """Registry for all metrics."""
    
    def __init__(self):
        """Initialize metrics registry."""
        self._counters: Dict[str, Counter] = {}
        self._histograms: Dict[str, Histogram] = {}
    
    def counter(self, name: str, description: str = "") -> Counter:
        """
        Get or create a counter metric.
        
        Args:
            name: Metric name
            description: Metric description
        
        Returns:
            Counter: Counter metric
        """
        if name not in self._counters:
            self._counters[name] = Counter(name, description)
        return self._counters[name]
    
    def histogram(self, name: str, description: str = "") -> Histogram:
        """
        Get or create a histogram metric.
        
        Args:
            name: Metric name
            description: Metric description
        
        Returns:
            Histogram: Histogram metric
        """
        if name not in self._histograms:
            self._histograms[name] = Histogram(name, description)
        return self._histograms[name]
    
    def get_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get all metrics as a dictionary.
        
        Returns:
            Dict: Dictionary of all metrics and their values
        """
        metrics = {}
        
        # Add counters
        for name, counter in self._counters.items():
            metrics[name] = {
                "type": "counter",
                "value": counter.get(),
                "description": counter.description
            }
        
        # Add histograms
        for name, histogram in self._histograms.items():
            metrics[name] = {
                "type": "histogram",
                "count": histogram.get_count(),
                "sum": histogram.get_sum(),
                "average": histogram.get_average(),
                "description": histogram.description
            }
        
        return metrics


# Global metrics registry
_metrics_registry: Optional[MetricsRegistry] = None


def get_metrics_registry() -> MetricsRegistry:
    """
    Get global metrics registry.
    
    Returns:
        MetricsRegistry: Global metrics registry
    """
    global _metrics_registry
    if _metrics_registry is None:
        _metrics_registry = MetricsRegistry()
    return _metrics_registry


# Convenience functions for common metrics
def counter(name: str, description: str = "") -> Counter:
    """Get or create a counter metric."""
    return get_metrics_registry().counter(name, description)


def histogram(name: str, description: str = "") -> Histogram:
    """Get or create a histogram metric."""
    return get_metrics_registry().histogram(name, description)


@contextmanager
def measure_time(metric_name: str, description: str = ""):
    """
    Context manager to measure execution time.
    
    Args:
        metric_name: Name of histogram metric to record time in
        description: Description of the metric
    
    Yields:
        None
    
    Example:
        with measure_time("alert_processing_duration_ms"):
            process_alert(alert)
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        histogram(metric_name, description).observe(duration_ms)


# Standard metrics
ALERTS_PROCESSED = counter(
    "alerts_processed_total",
    "Total number of alerts processed"
)

ALERTS_FAILED = counter(
    "alerts_failed_total",
    "Total number of alerts that failed processing"
)

TRIAGE_DURATION = histogram(
    "triage_duration_ms",
    "Alert triage processing duration in milliseconds"
)

HUNTING_QUERIES_EXECUTED = counter(
    "hunting_queries_executed_total",
    "Total number of hunting queries executed"
)

RESPONSE_ACTIONS_EXECUTED = counter(
    "response_actions_executed_total",
    "Total number of response actions executed"
)

INCIDENTS_CREATED = counter(
    "incidents_created_total",
    "Total number of incidents created"
)
