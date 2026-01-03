"""Structured logging configuration."""

import sys
import logging
from typing import Any, Dict
import structlog
from structlog.types import EventDict, Processor

from aml_triage.core.config import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log entries."""
    event_dict["app"] = "aml-triage"
    event_dict["environment"] = "production"
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # Configure structlog
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add JSON rendering for production, console for development
    if settings.log_level == "DEBUG":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance for a module."""
    return structlog.get_logger(name)


def log_agent_action(
    logger: structlog.BoundLogger,
    agent_name: str,
    action: str,
    alert_id: str,
    metadata: Dict[str, Any],
) -> None:
    """Log an agent action with structured metadata."""
    logger.info(
        "agent_action",
        agent=agent_name,
        action=action,
        alert_id=alert_id,
        **metadata,
    )


def log_performance_metric(
    logger: structlog.BoundLogger,
    metric_name: str,
    value: float,
    unit: str,
    tags: Dict[str, str],
) -> None:
    """Log a performance metric."""
    logger.info(
        "performance_metric",
        metric=metric_name,
        value=value,
        unit=unit,
        **tags,
    )
