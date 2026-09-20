"""Configuration and policy loading.

Temenos separates two concerns that are easy to collapse:

    config  — how temenos runs (endpoint, token, log, mode).
    policy  — what temenos decides (thresholds, disposition mapping).

Both ship as human-authored files; both are read once at startup. Nothing here
runs inside the gate path — parsing and I/O happen at the boundary, not per
signal.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    _HAS_YAML = True
except ImportError:  # pragma: no cover — pyyaml is a declared dependency
    yaml = None
    _HAS_YAML = False


LOADERS = {
    ".yaml": lambda t: yaml.safe_load(t) if _HAS_YAML else None,
    ".yml": lambda t: yaml.safe_load(t) if _HAS_YAML else None,
    ".json": json.loads,
}


@dataclass
class Settings:
    """Runtime configuration, flattened from file + env."""

    stratum_base_url: str = "http://127.0.0.1:8787"
    stratum_token: str = ""
    log_id: str = "temenos"
    mode: str = "shadow"                 # shadow | enforce — passthrough to aletheia

    # Disposition mapping (policy). The LLM never authors these; a human does.
    proceed_disposition: str = "observe"
    verify_disposition: str = "review"
    stop_disposition: str = "approve_required"

    # Optional tool to record (if empty, provenance defaults to origin only).
    recording_enabled: bool = True

    @classmethod
    def from_file(cls, path: str | os.PathLike) -> "Settings":
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        loader = LOADERS.get(p.suffix.lower())
        if loader is None:
            if not _HAS_YAML:
                raise RuntimeError(
                    f"cannot parse {p.suffix}; pyyaml missing and the file is not JSON"
                )
            loader = yaml.safe_load
        raw = loader(text) or {}

        policy = raw.get("policy", {})
        settings = raw.get("settings", {})

        s = cls(
            stratum_base_url=settings.get("stratum_base_url", cls.stratum_base_url),
            log_id=settings.get("log_id", cls.log_id),
            mode=settings.get("mode", cls.mode),
        )
        s.stratum_token = settings.get("stratum_token", "") or ""
        esc = policy.get("escalation", {})
        s.proceed_disposition = esc.get("proceed", s.proceed_disposition)
        s.verify_disposition = esc.get("verify", s.verify_disposition)
        s.stop_disposition = esc.get("stop", s.stop_disposition)
        return s

    def apply_env(self) -> "Settings":
        """Env vars override the file (12-factor). Tokens never live in files."""
        self.stratum_base_url = os.environ.get(
            "TEMENOS_STRATUM_URL", self.stratum_base_url
        )
        self.stratum_token = os.environ.get("STRATUM_TOKEN", self.stratum_token)
        self.log_id = os.environ.get("TEMENOS_LOG_ID", self.log_id)
        self.mode = os.environ.get("TEMENOS_MODE", self.mode)
        return self


def load_settings(path: Optional[str] = None) -> Settings:
    """Load config from `path` (or `TEMENOS_CONFIG`), then overlay env vars."""
    cfg_path = path or os.environ.get("TEMENOS_CONFIG")
    if cfg_path and Path(cfg_path).exists():
        s = Settings.from_file(cfg_path)
    else:
        s = Settings()
    return s.apply_env()