"""Policy: disposition mapping and evidence shaping."""
from __future__ import annotations

from temenos.config import Settings
from temenos.models import GateResult, Signal
from temenos import policy


def _gate(action="proceed", score=0.0) -> GateResult:
    return GateResult(action=action, score=score, severity="low")


def test_proceed_maps_to_observe():
    v = policy.disposition(Signal(id="s", content="x"), _gate("proceed"), Settings())
    assert v.disposition == "observe"


def test_verify_maps_to_review():
    v = policy.disposition(Signal(id="s", content="x"), _gate("verify", 0.4), Settings())
    assert v.disposition == "review"


def test_stop_maps_to_approve_required_and_flags_shadow():
    s = Settings()
    v = policy.disposition(
        Signal(id="s", content="x"), _gate("stop", 0.8), s
    )
    assert v.disposition == "approve_required"
    # shadow stop: not enforced, so the human is told nothing actually blocked
    assert any("shadow" in u for u in v.unresolved)


def test_evidence_is_stratum_shaped():
    v = policy.disposition(Signal(id="s", content="x"), _gate("proceed"), Settings())
    for e in v.evidence:
        assert set(e) >= {"kind", "ref", "checked_at", "signer"}


def test_configurable_disposition_labels():
    s = Settings(stop_disposition="blocked")
    v = policy.disposition(Signal(id="s", content="x"), _gate("stop", 0.9), s)
    assert v.disposition == "blocked"