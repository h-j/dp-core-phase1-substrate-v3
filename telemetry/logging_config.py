"""
Structured logging configuration for DP-Core.

Call configure_logging() once from any replay entry point.
All modules use logging.getLogger(__name__) — no custom handler setup needed.

Phase 3 remediation: replaces scattered print() calls
and provides the root configuration for structured observability.
"""
import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure root logging with a single stream handler.

    Args:
        level: Root log level. Default INFO. Set DEBUG to see ContradictionDetector,
               LessonExtractor, and ValidationEngine diagnostic traces.
    """
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)

    root.setLevel(level)
    root.addHandler(handler)

    # Suppress noisy third-party loggers at INFO level
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("ollama").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
