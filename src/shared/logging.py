"""
Structured logging setup using structlog with JSON formatting.

This module provides standardized logging configuration for the Agentic SOC,
with support for Azure Monitor and distributed tracing.
"""

import logging
import sys
from typing import Optional
from uuid import uuid4

import structlog
from structlog.types import EventDict, Processor


# Global correlation ID for distributed tracing
_correlation_id: Optional[str] = None


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for distributed tracing.
    
    Args:
        correlation_id: Correlation ID to track requests across services
    """
    global _correlation_id
    _correlation_id = correlation_id


def get_correlation_id() -> str:
    """
    Get current correlation ID, generating one if not set.
    
    Returns:
        str: Correlation ID
    """
    global _correlation_id
    if _correlation_id is None:
        _correlation_id = str(uuid4())
    return _correlation_id


def add_correlation_id(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Processor to add correlation ID to log entries.
    
    Args:
        logger: Logger instance
        method_name: Method name
        event_dict: Event dictionary
    
    Returns:
        EventDict: Modified event dictionary with correlation ID
    """
    event_dict["correlation_id"] = get_correlation_id()
    return event_dict


def configure_logging(
    log_level: str = "INFO",
    json_output: bool = True,
    azure_monitor_enabled: bool = False
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Whether to output logs in JSON format
        azure_monitor_enabled: Whether to enable Azure Monitor integration
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure structlog processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_correlation_id,
    ]
    
    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )
    
    # If Azure Monitor is enabled, configure OpenTelemetry
    if azure_monitor_enabled:
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor
            configure_azure_monitor()
        except ImportError:
            logging.warning(
                "Azure Monitor OpenTelemetry not available. "
                "Install azure-monitor-opentelemetry to enable Azure Monitor integration."
            )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        BoundLogger: Configured structlog logger
    """
    return structlog.get_logger(name)


# Configure default logging on module import
configure_logging()
