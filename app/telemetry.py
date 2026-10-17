"""Logging. Locally: console. On Azure: also sent to Application Insights
(when APPLICATIONINSIGHTS_CONNECTION_STRING is set)."""
from __future__ import annotations

import logging

from app.config import settings

_configured = False


def get_logger() -> logging.Logger:
    global _configured
    logger = logging.getLogger("invoice_assistant")
    if not _configured:
        _configured = True
        logger.setLevel(logging.INFO)
        if settings.appinsights_conn_str:
            try:
                from azure.monitor.opentelemetry import configure_azure_monitor
                configure_azure_monitor(connection_string=settings.appinsights_conn_str,
                                        logger_name="invoice_assistant")
            except Exception as e:  # monitoring must never break the app
                logging.getLogger(__name__).warning("App Insights not configured: %s", e)
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s %(props)s"))
            logger.addHandler(h)
    return logger


def log_event(name: str, **props) -> None:
    """Structured event. In App Insights it appears under 'traces' with the
    props as custom dimensions, so you can query e.g. all rejected uploads."""
    get_logger().info(name, extra={"props": props, **{k: str(v) for k, v in props.items()}})
