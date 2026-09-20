"""Resolve the vendored aletheia/apatea packages onto `sys.path`.

The two gate tools live in separate private repos. Temenos vendors them as git
submodules (pinned to exact SHAs) so a checkout is self-contained and
reproducible — no PyPI, no git-auth at install time. This module makes them
importable regardless of how temenos itself is installed.
"""
from __future__ import annotations

import sys
from pathlib import Path

_VENDOR = Path(__file__).resolve().parent.parent / "vendor"


def _site_packages() -> list[str]:
    """Make each vendored package importable; return the names available.

    Availability is "the submodule is checked out", independent of whether the
    path happens to already be on sys.path (e.g. a test conftest added it).
    """
    available: list[str] = []
    for name in ("aletheia", "apatea"):
        src = _VENDOR / name / "src"
        if src.is_dir():
            available.append(name)
            if str(src) not in sys.path:
                sys.path.insert(0, str(src))
    return available


def ensure(*names: str) -> list[str]:
    """Import the vendored packages, raising a clear error if they are absent.

    Returns the list of submodule names that were successfully made importable.
    """
    added = _site_packages()
    missing = [n for n in names if n not in added]
    if missing:
        raise ImportError(
            "missing vendored dependencies: "
            + ", ".join(missing)
            + "\nRun:  git submodule update --init --recursive"
        )
    return added