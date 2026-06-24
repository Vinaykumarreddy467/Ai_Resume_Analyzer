"""Centralized logging for AI Resume Analyzer.

Usage:
    from services.logger import logger
    logger.info("Processing started")
    logger.error("Something failed", exc_info=True)
"""

import os
import sys
import logging
from pathlib import Path

# ── Log directory ──────────────────────────────────────────────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# ── Formatters ─────────────────────────────────────────────────
CONSOLE_FMT = "%(asctime)s | %(levelname)-5s | %(message)s"
FILE_FMT = (
    "%(asctime)s | %(levelname)-5s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
)
DATE_FMT = "%Y-%m-%d %H:%M:%S"

# ── Logger setup ───────────────────────────────────────────────
_logger = logging.getLogger("resume-analyzer")
_logger.setLevel(logging.DEBUG)  # capture everything, handlers filter down

# ── Console handler (INFO+) ────────────────────────────────────
console = logging.StreamHandler(sys.stdout)
console.setLevel(os.getenv("LOG_LEVEL_CONSOLE", "INFO").upper())
console.setFormatter(logging.Formatter(CONSOLE_FMT, datefmt=DATE_FMT))
_logger.addHandler(console)

# ── File handler (DEBUG+) — rotates on each run ────────────────
log_file = LOG_DIR / "analyzer.log"
file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
file_handler.setLevel(os.getenv("LOG_LEVEL_FILE", "DEBUG").upper())
file_handler.setFormatter(logging.Formatter(FILE_FMT, datefmt=DATE_FMT))
_logger.addHandler(file_handler)

# ── Error file handler (ERROR+) — separate file for errors ─────
err_file = LOG_DIR / "errors.log"
err_handler = logging.FileHandler(err_file, mode="a", encoding="utf-8")
err_handler.setLevel(logging.ERROR)
err_handler.setFormatter(logging.Formatter(FILE_FMT, datefmt=DATE_FMT))
_logger.addHandler(err_handler)


# ── Convenience ────────────────────────────────────────────────
def get_logger(name: str | None = None) -> logging.Logger:
    """Return the root logger or a child logger for the given name."""
    if name:
        return _logger.getChild(name)
    return _logger


# Module-level convenience access
logger = _logger
