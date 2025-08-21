"""Pytest configuration helpers.

Ensure the repository root and the `src/` package directory are on sys.path
early during test collection so tests that import `src.*` succeed.

This is a minimal, non-invasive helper intended only for the test runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path


def pytest_sessionstart(session) -> None:
    """During pytest collection, ensure repo root and src/ are on sys.path.

    pluggy/pytest expect the parameter name to be exactly `session`.
    Mark it used to avoid unused-argument linters.
    """
    # Mark the session as used for linters
    _ = session

    # Keep tests isolated: we only modify sys.path at collection time.
    repo_root = Path(__file__).resolve().parent
    src_dir = repo_root / "src"

    # Prepend repo root and src/ to sys.path if not already present. Prepending
    # keeps test-local modules first and mirrors how many CI setups run tests.
    repo_root_str = str(repo_root)
    src_dir_str = str(src_dir)

    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    if src_dir.exists() and src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)
