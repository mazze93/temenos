"""Stratum client — the durable decision record.

Stratum's API is tiny and deliberate: append an immutable event, or read the
derived projection. This client speaks that contract exactly. It is stdlib-only
(urllib) so the *audit path* — the one component that must never fail to write
— has no third-party supply chain of its own.

Payload shape follows stratum's worker contract: snake_case at the wire, an
`evidence` array where `checked_at` is non-null only when the check was actually
performed.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

from .models import Verdict


class LedgerError(Exception):
    """Raised when a write/read to stratum fails. Carries the HTTP status."""

    def __init__(self, message: str, status: Optional[int] = None, body: str = ""):
        super().__init__(message)
        self.status = status
        self.body = body


@dataclass
class StratumClient:
    base_url: str
    token: str = ""
    log_id: str = "temenos"
    timeout: float = 5.0

    # ------------------------------------------------------------------ read
    def projection(self, epoch: Optional[int] = None) -> dict:
        url = f"{self.base_url}/api/logs/{self.log_id}/projection"
        if epoch is not None:
            url += f"?epoch={epoch}"
        return self._request("GET", url)

    def events(self) -> list[dict]:
        return self._request("GET", f"{self.base_url}/api/logs/{self.log_id}/events")

    # ----------------------------------------------------------------- append
    def append_event(self, event: dict) -> dict:
        """Append one event. Returns the appended (sequenced) record."""
        return self._request(
            "POST", f"{self.base_url}/api/logs/{self.log_id}/events", body=event
        )

    # ------------------------------------------------------------- internal
    def _request(self, method: str, url: str, body: Optional[dict] = None) -> Any:
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            raise LedgerError(
                f"stratum {method} {url} -> HTTP {e.code}", status=e.code, body=detail
            ) from e
        except urllib.error.URLError as e:
            raise LedgerError(f"stratum unreachable at {url}: {e.reason}") from e


def build_event(verdict: Verdict, *, agent_id: str = "temenos",
                schema_version: int = 1, targets: Optional[list[str]] = None) -> dict:
    """Shape a Verdict into a stratum `decision` event (snake_case wire form).

    `birth_status` is `asserted`: a claim that stands until proven otherwise, with
    the gate's computed evidence attached. Temenos never writes a stored status —
    status is stratum's fold, not ours.
    """
    claim = verdict.to_dict()
    event_id = f"temenos:{verdict.signal_id}:{_short_ts()}"

    return {
        "id": event_id,
        "type": "decision",
        "agent_id": agent_id,
        "schema_version": schema_version,
        "birth_status": "asserted",
        "claim": claim,
        "evidence": verdict.evidence,
        "targets": targets or [verdict.signal_id],
        "is_trust_root": False,
        "timestamp": None,   # wall-clock metadata; stratum ignores it in projections
    }


def _short_ts() -> str:
    return str(int(time.time()))