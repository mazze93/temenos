"""Core data model for temenos.

The types here are deliberately boring dataclasses. The security value of
temenos is not in clever types — it is that every field below survives a round
trip into stratum as an immutable, evidence-linked event.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Inbound
# ---------------------------------------------------------------------------

@dataclass
class Signal:
    """An inbound artifact that will govern (or describes) an action.

    A signal is the thing the agent saw before it did something: a pull-request
    body, a web result, a tool output, a commit message. `origin` and `tool`
    carry the provenance that aletheia turns into a decision.
    """

    id: str
    content: str
    origin: str = "unclassified"
    tool: str = ""                       # Bash | Edit | Write | WebSearch | ...
    event: str = ""                      # PreToolUse | PostToolUse | ...
    taint: tuple[str, ...] = ()
    intended_action: Optional[str] = None
    source: str = ""                     # human-readable label, e.g. pr://repo/184


# ---------------------------------------------------------------------------
# Gate (aletheia is the engine; this is its normalized answer)
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    """Aletheia's verdict, flattened to fields temenos reasons about."""

    action: str                          # proceed | verify | stop
    score: float
    severity: str = "low"                 # low | moderate | high (descriptive)
    factors: list = field(default_factory=list)
    governing_parameters: list = field(default_factory=list)
    reason: str = ""
    origin: str = "unclassified"
    trust: float = 0.3
    tainted: bool = False
    destructive: bool = False
    egress: bool = False
    enforced: bool = False               # did aletheia actually block (mode=Enforce)
    mode: str = "shadow"


# ---------------------------------------------------------------------------
# Policy + verdict (the human-facing decision)
# ---------------------------------------------------------------------------

@dataclass
class Verdict:
    """The paper trail temenos produces for a signal.

    Disposition is the human-facing outcome; gate is the raw provenance verdict;
    evidence is already shaped for stratum's contract.
    """

    signal_id: str
    disposition: str                     # observe|review|approve_required|blocked|deferred|resolved
    gate: GateResult
    recommendation: str = ""
    policy_rules: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    confidence: float = 1.0
    unresolved: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "disposition": self.disposition,
            "gate": {
                "action": self.gate.action,
                "score": round(self.gate.score, 4),
                "severity": self.gate.severity,
                "governing_parameters": self.gate.governing_parameters,
                "reason": self.gate.reason,
                "origin": self.gate.origin,
                "trust": self.gate.trust,
                "tainted": self.gate.tainted,
                "destructive": self.gate.destructive,
                "egress": self.gate.egress,
                "enforced": self.gate.enforced,
                "mode": self.gate.mode,
            },
            "recommendation": self.recommendation,
            "policy_rules": self.policy_rules,
            "confidence": round(self.confidence, 4),
            "unresolved": self.unresolved,
        }


# ---------------------------------------------------------------------------
# Adversarial audit (apatea)
# ---------------------------------------------------------------------------

@dataclass
class AuditReport:
    """What apatea found (and did not find) against the live gate."""

    clean: bool
    checks: int = 0
    violations: int = 0
    findings: list = field(default_factory=list)
    perimeter_held: dict = field(default_factory=dict)
    perimeter_tried: dict = field(default_factory=dict)
    text: str = ""                       # human-readable render