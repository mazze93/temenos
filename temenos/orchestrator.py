"""The loop — signal in, immutable decision out.

Temenos is small on purpose:

    gate (aletheia)   ->   policy (deterministic)   ->   ledger (stratum)

The orchestrator wires those three without adding authority of its own. If the
ledger is unavailable, the decision is still returned to the caller (fail
loud); persistence failure is never silent.
"""
from __future__ import annotations

import logging
from typing import Optional

from . import gate, policy
from .config import Settings
from .ledger import LedgerError, StratumClient, build_event
from .models import Signal, Verdict

log = logging.getLogger("temenos")


class Temenos:
    """A configured runtime: settings + the three tools wired together."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.ledger = StratumClient(
            base_url=self.settings.stratum_base_url,
            token=self.settings.stratum_token,
            log_id=self.settings.log_id,
        )

    def decide(self, signal: Signal, *, record: bool = True) -> Verdict:
        """Evaluate one signal and (optionally) persist the decision.

        Returns the verdict immediately. Recording is the default; a ledger
        failure is logged and surfaced on the verdict rather than raised, so an
        unreachable ledger never takes down the decision path.
        """
        g = gate.evaluate(signal, mode=self.settings.mode)
        verdict = policy.disposition(signal, g, self.settings)

        if record and self.settings.recording_enabled:
            try:
                event = build_event(verdict)
                self.ledger.append_event(event)
            except LedgerError as e:
                log.warning("ledger write failed for %s: %s", signal.id, e)
                verdict.unresolved.append(f"ledger write failed: {e}")
        return verdict

    def audit(self, target: str = "aletheia", origin: str = "web_search"):
        """Run the adversary against the gate. Exists on Temenos, not the CLI,
        so scheduled jobs and the control plane share one code path."""
        from . import adversary

        return adversary.audit(target=target, origin=origin)