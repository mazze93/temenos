"""The gate — aletheia, wrapped.

Aletheia is the provenance engine. This module is a thin, honest adapter: it
builds aletheia's `Event` envelope from a `Signal`, runs the assessor, and asks
aletheia's policy layer what the verdict is. Temenos adds no scoring of its own;
the gate is aletheia's, kept separable exactly as aletheia intends (judge and
enforcer decoupled).
"""
from __future__ import annotations

from .models import GateResult, Signal
from .vendor import ensure


def _aletheia():
    ensure("aletheia")
    from aletheia.assess import assess  # noqa: PLC0415
    from aletheia.policy import decide  # noqa: PLC0415
    from aletheia.provenance import build  # noqa: PLC0415
    return assess, decide, build


def evaluate(signal: Signal, mode: str = "shadow") -> GateResult:
    """Run the provenance gate over a signal and return a normalized verdict.

    `mode` is aletheia's own shadow/enforce switch. In shadow the gate records
    and reasons but blocks nothing; in enforce, a `stop` verdict actually stops.
    """
    assess, decide, build = _aletheia()

    event = build(
        content=signal.content,
        origin=signal.origin,
        event=signal.event,
        tool=signal.tool,
        taint=list(signal.taint),
    )

    assessment = assess(signal.content, event.origin, signal.intended_action)
    decision = decide(event, assessment.injection_risk_score, mode=mode,
                      reasoning=assessment.reasoning)

    return GateResult(
        action=decision.action,
        score=assessment.injection_risk_score,
        severity=assessment.severity,
        factors=assessment.risk_factors,
        governing_parameters=assessment.governing_parameters,
        reason=decision.reason or assessment.reasoning,
        origin=event.origin,
        trust=event.trust,
        tainted=event.tainted,
        destructive=event.destructive,
        egress=event.egress,
        enforced=decision.enforced,
        mode=mode,
    )