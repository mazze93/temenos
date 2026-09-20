"""Deterministic policy — the mapping from a gate verdict to a disposition.

The rule is deliberately small and explicit. Aletheia decides proceed/verify/
stop; temenos translates that into the *human-facing* disposition and attaches
the recommendation and evidence. There is no DSL and no model in this path:
the ordering below is the policy, and a human wrote it in config.
"""
from __future__ import annotations

from .config import Settings
from .models import GateResult, Signal, Verdict


def disposition(signal: Signal, gate: GateResult, settings: Settings) -> Verdict:
    """Map (gate action) -> (disposition, recommendation) and shape evidence."""

    if gate.action == "stop":
        disp = settings.stop_disposition
        rec = (
            "Block the action and require explicit human authorization. "
            "The governing content is either tainted-and-destructive or a "
            f"high-confidence injection from {gate.origin}."
        )
    elif gate.action == "verify":
        disp = settings.verify_disposition
        rec = (
            "Do not act on this content automatically. Verify any governing "
            "parameter at its authoritative source before proceeding."
        )
    else:
        disp = settings.proceed_disposition
        rec = "No action needed. Recorded for the audit trail."

    # Evidence is shaped for stratum's contract here, so the ledger is a
    # pure append of an already-validated record.
    evidence = [
        {
            "kind": "provenance_gate",
            "ref": f"aletheia:{signal.id}",
            # A gate score is a *computed* check — checked_at is non-null only
            # when temenos itself performed the computation now.
            "checked_at": _now_iso(),
            "signer": "aletheia",
        },
        {
            "kind": "governing_parameters",
            "ref": ",".join(gate.governing_parameters) or signal.id,
            "checked_at": None,     # cited, not independently checked
            "signer": None,
        },
    ]

    verdict = Verdict(
        signal_id=signal.id,
        disposition=disp,
        gate=gate,
        recommendation=rec,
        policy_rules=[f"gate:{gate.action} -> {disp}"],
        evidence=evidence,
        confidence=1.0,
    )

    # A stop in shadow mode is still a real concern — the human must set
    # direction even though nothing was enforced.
    if gate.action == "stop" and not gate.enforced:
        verdict.unresolved.append(
            "gate would block in enforce mode; shadow mode recorded without blocking"
        )
    return verdict


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()