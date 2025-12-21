"""
Structured logging module for Agentic SOC.

Provides JSON-formatted structured logging with OpenTelemetry integration.
"""

import logging
import os
import sys
from typing import Any, Optional
from uuid import uuid4

import structlog


def setup_logging(
    log_level: Optional[str] = None,
    enable_json: bool = False,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to LOG_LEVEL environment variable or INFO.
        enable_json: If True, use JSON formatter. If False, use console formatter.
                  Defaults to False for cleaner CLI output.
        correlation_id: Optional correlation ID for distributed tracing.

    Example:
        >>> setup_logging(log_level="DEBUG", enable_json=False)
        >>> logger = get_logger("my_module")
        >>> logger.info("Application started", component="api", version="1.0.0")
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    level = getattr(logging, log_level, logging.INFO)

    # Configure structlog processors
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add correlation ID processor if provided
    if correlation_id:
        processors.insert(0, structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ))

    # Add JSON or console renderer
    if enable_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Use development-friendly console output
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Suppress verbose logging from Azure SDK and other libraries
    # These libraries log HTTP request/response details at DEBUG level
    logging.getLogger("azure.core").setLevel(logging.ERROR)
    logging.getLogger("azure.identity").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("requests").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("aiohttp").setLevel(logging.ERROR)
    logging.getLogger("asyncio").setLevel(logging.ERROR)
    logging.getLogger("agent_framework").setLevel(logging.ERROR)


def get_logger(name: str, **initial_context: Any) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger with optional initial context.

    Args:
        name: Logger name (typically __name__)
        **initial_context: Initial context to bind to the logger

    Returns:
        Bound logger with context

    Example:
        >>> logger = get_logger(__name__, service="triage-agent", version="1.0.0")
        >>> logger.info("Processing alert", alert_id="12345", severity="High")
    """
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


def create_correlation_id() -> str:
    """
    Create a unique correlation ID for request tracing.

    Returns:
        UUID string for correlation

    Example:
        >>> correlation_id = create_correlation_id()
        >>> logger = get_logger(__name__, correlation_id=correlation_id)
    """
    return str(uuid4())


class LogContext:
    """
    Context manager for scoped logging context.

    Example:
        >>> logger = get_logger(__name__)
        >>> with LogContext(logger, alert_id="12345", severity="High"):
        ...     logger.info("Processing alert")
        ...     logger.info("Alert processed")
    """

    def __init__(self, logger: structlog.stdlib.BoundLogger, **context: Any):
        """
        Initialize log context.

        Args:
            logger: Logger to bind context to
            **context: Context key-value pairs
        """
        self.logger = logger
        self.context = context
        self.bound_logger: Optional[structlog.stdlib.BoundLogger] = None

    def __enter__(self) -> structlog.stdlib.BoundLogger:
        """Enter context and bind context to logger."""
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context (context is automatically unbound)."""
        if exc_type is not None:
            if self.bound_logger:
                self.bound_logger.error(
                    "Exception in log context",
                    exc_type=exc_type.__name__,
                    exc_val=str(exc_val),
                )
        return False


# =============================================================================
# OpenTelemetry Integration (Future)
# =============================================================================


def setup_opentelemetry(
    service_name: str = "agentic-soc",
    enable_tracing: bool = False,
    enable_metrics: bool = False,
) -> None:
    """
    Setup OpenTelemetry instrumentation (future implementation).

    Args:
        service_name: Name of the service for telemetry
        enable_tracing: Enable distributed tracing
        enable_metrics: Enable metrics collection

    Note:
        This is a placeholder for future OpenTelemetry integration.
        Requires azure-monitor-opentelemetry and additional configuration.
    """
    if not (enable_tracing or enable_metrics):
        return

    # TODO: Implement OpenTelemetry setup when ready
    # from azure.monitor.opentelemetry import configure_azure_monitor
    # configure_azure_monitor(
    #     connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"),
    #     service_name=service_name,
    # )

    logger = get_logger(__name__)
    logger.info(
        "OpenTelemetry setup requested but not yet implemented",
        service_name=service_name,
        enable_tracing=enable_tracing,
        enable_metrics=enable_metrics,
    )


# =============================================================================
# Logging Helpers
# =============================================================================


def log_agent_action(
    logger: structlog.stdlib.BoundLogger,
    agent_name: str,
    action: str,
    result: str,
    **details: Any,
) -> None:
    """
    Log an agent action with standard fields.

    Args:
        logger: Structured logger
        agent_name: Name of the agent
        action: Action performed
        result: Result (Success, Failure, Pending)
        **details: Additional context

    Example:
        >>> logger = get_logger(__name__)
        >>> log_agent_action(
        ...     logger,
        ...     agent_name="AlertTriageAgent",
        ...     action="TriageAlert",
        ...     result="Success",
        ...     alert_id="12345",
        ...     risk_score=85,
        ... )
    """
    logger.info(
        "Agent action",
        agent_name=agent_name,
        action=action,
        result=result,
        **details,
    )


def log_api_call(
    logger: structlog.stdlib.BoundLogger,
    endpoint: str,
    method: str,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    **details: Any,
) -> None:
    """
    Log an API call with standard fields.

    Args:
        logger: Structured logger
        endpoint: API endpoint
        method: HTTP method
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        **details: Additional context

    Example:
        >>> logger = get_logger(__name__)
        >>> log_api_call(
        ...     logger,
        ...     endpoint="/api/agents/triage",
        ...     method="POST",
        ...     status_code=200,
        ...     duration_ms=1250.5,
        ... )
    """
    logger.info(
        "API call",
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        **details,
    )


def log_security_event(
    logger: structlog.stdlib.BoundLogger,
    event_type: str,
    severity: str,
    description: str,
    **details: Any,
) -> None:
    """
    Log a security-relevant event.

    Args:
        logger: Structured logger
        event_type: Type of security event
        severity: Severity level
        description: Event description
        **details: Additional context

    Example:
        >>> logger = get_logger(__name__)
        >>> log_security_event(
        ...     logger,
        ...     event_type="AuthenticationFailure",
        ...     severity="High",
        ...     description="Failed login attempt",
        ...     username="admin",
        ...     source_ip="192.168.1.100",
        ... )
    """
    logger.warning(
        "Security event",
        event_type=event_type,
        severity=severity,
        description=description,
        **details,
    )


# Initialize logging on module import
setup_logging()
