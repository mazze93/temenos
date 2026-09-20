"""The adversary — apatea, wrapped.

A gate is only as good as what it stops, and nothing measures what a gate
misses. Apatea holds stated invariants (monotonicity, extent stability,
determinism) and searches transformations of real inputs for the cases where
aletheia's own assessor goes blind. This module points apatea at the *live*
gate so temenos can answer "is my gate still honest?" on a schedule.
"""
from __future__ import annotations

import os

from .models import AuditReport
from .vendor import ensure, _VENDOR


def _point_at_vendored_gate() -> None:
    """apatea's live-gate adapter locates aletheia via ALETHEIA_HOME. Point
    it at the vendored submodule so the operator needs no extra env."""
    os.environ.setdefault("ALETHEIA_HOME", str(_VENDOR / "aletheia"))


def audit(target: str = "aletheia", origin: str = "web_search",
          only: tuple[str, ...] | None = None) -> AuditReport:
    """Run apatea's invariant search against the configured target.

    `target` is aletheia (the live gate) by default. Returns a normalized
    report; apatea exits non-zero on violations, which the CLI surfaces.
    """
    ensure("aletheia", "apatea")
    _point_at_vendored_gate()

    from apatea.search import run  # noqa: PLC0415
    from apatea.cli import load  # noqa: PLC0415

    target_obj = load(target)
    result = run(target_obj, origin=origin, only=only)

    findings = []
    for v in result.findings:
        findings.append({
            "invariant": v.invariant,
            "atom": v.atom,
            "transformation": v.transformation,
            "variant_id": v.variant_id,
            "detail": v.detail,
            "severity": v.severity,
            "baseline_score": v.baseline_score,
            "mutated_score": v.mutated_score,
            "content_hash": v.as_dict().get("content_hash", ""),
        })

    return AuditReport(
        clean=result.clean,
        checks=result.checks,
        violations=len(findings),
        findings=findings,
        perimeter_held=result.held,
        perimeter_tried=result.tried,
        text=result.render(),
    )