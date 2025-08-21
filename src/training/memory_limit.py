"""Memory limit helper for training entrypoints.

Provides a small, opt-in mechanism to enforce a soft memory limit for training
processes. On Unix, it will attempt to set RLIMIT_AS (address space). When that
is not available or not effective (macOS sometimes ignores AS), a watchdog thread
will monitor RSS via psutil and raise MemoryError if the process exceeds the
configured limit.

This file is intentionally small and opt-in. Call enforce_memory_limit(bytes=...) at
the start of a training process. Use the environment variable
PLANTGUARD_TRAIN_MEMORY_LIMIT_BYTES to opt-in without code changes.
"""

from __future__ import annotations

import logging
import os
import threading
import time

logger = logging.getLogger(__name__)


def _set_rlimit(limit_bytes: int) -> bool:
    try:
        import resource

        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, hard))
        logger.info("Set RLIMIT_AS soft limit to %d bytes", limit_bytes)
        return True
    except Exception as e:  # pragma: no cover - depends on OS
        logger.debug("Failed to set RLIMIT_AS: %s", e)
        return False


def _start_watchdog(limit_bytes: int, check_interval: float = 1.0) -> threading.Thread:
    try:
        import psutil

        pid = os.getpid()
        proc = psutil.Process(pid)

        def _watch():
            logger.debug("Memory watchdog started (limit=%d bytes)", limit_bytes)
            while True:
                try:
                    rss = proc.memory_info().rss
                    if rss > limit_bytes:
                        logger.error("Memory limit exceeded: rss=%d bytes > limit=%d bytes", rss, limit_bytes)
                        raise MemoryError(f"Process exceeded memory limit: {rss} > {limit_bytes}")
                except MemoryError:
                    # Re-raise to abort training
                    raise
                except Exception:
                    # On transient errors, keep the watchdog alive
                    logger.debug("Watchdog transient error", exc_info=True)
                time.sleep(check_interval)

        t = threading.Thread(target=_watch, daemon=True, name="memory-watchdog")
        t.start()
        return t
    except Exception as e:  # pragma: no cover - psutil availability
        logger.debug("Watchdog not started: %s", e)
        raise


def enforce_memory_limit(limit_bytes: int | None = None) -> None:
    """Enforce a soft memory limit for the current process.

    Behavior:
      - If PLANTGUARD_TRAIN_MEMORY_LIMIT_BYTES is set in the environment, it takes precedence.
      - Tries RLIMIT_AS first (Unix). If that fails, starts a watchdog thread that polls RSS.
      - This function is best-effort and opt-in. It will not be aggressive by default.
    """
    env = os.environ.get("PLANTGUARD_TRAIN_MEMORY_LIMIT_BYTES")
    if env:
        try:
            env_val = int(env)
            limit_bytes = env_val
        except Exception:
            logger.warning("Invalid PLANTGUARD_TRAIN_MEMORY_LIMIT_BYTES: %s", env)

    if not limit_bytes or limit_bytes <= 0:
        logger.debug("No memory limit configured (limit_bytes=%r)", limit_bytes)
        return

    # Try RLIMIT_AS first
    if _set_rlimit(limit_bytes):
        return

    # Fallback: start watchdog thread to abort if RSS grows beyond limit
    try:
        _start_watchdog(limit_bytes)
    except Exception:
        logger.warning("Unable to enforce memory limit: both RLIMIT_AS and watchdog failed")
