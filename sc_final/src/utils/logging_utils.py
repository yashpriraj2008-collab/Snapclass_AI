"""Small logging helpers for production-friendly error handling."""

from __future__ import annotations

import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def log_exception(logger_name: str, message: str, exc: BaseException) -> None:
    logging.getLogger(logger_name).exception("%s: %s", message, exc)

