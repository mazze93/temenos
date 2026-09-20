"""Shared fixtures. Adds the vendored submodules to sys.path once."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _vendor_on_path():
    for name in ("aletheia", "apatea"):
        src = ROOT / "vendor" / name / "src"
        if src.is_dir() and str(src) not in sys.path:
            sys.path.insert(0, str(src))
    yield


@pytest.fixture
def mock_stratum():
    from mock_stratum import MockStratum  # noqa: PLC0415 — local test module

    s = MockStratum().start()
    yield s
    s.stop()


@pytest.fixture
def settings(mock_stratum):
    from temenos.config import Settings  # noqa: PLC0415

    return Settings(
        stratum_base_url=mock_stratum.base_url,
        stratum_token="test-token",
        log_id="temenos",
        mode="shadow",
    )