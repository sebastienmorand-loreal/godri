"""Logging configuration."""

import logging
import colorlog


def setup_logging():
    """Set up colored logging."""
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "[ %(asctime)s ] %(log_color)s%(levelname)7s%(reset)s: %(module)s.%(funcName)s: %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    logging.basicConfig(level=logging.INFO, handlers=[handler])

    for logger_name in (
        "google.auth.transport.requests",
        "google.cloud.bigquery.opentelemetry_tracing",
        "google.auth._default",
        "urllib3.connectionpool",
        "urllib3.util.retry",
        "googleapiclient.discovery",
        "googleapiclient.discovery_cache",
    ):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
