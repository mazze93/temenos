"""Temenos — τέμενος, the sacred boundary that contains without claiming.

An evidence-gated runtime for autonomous agents. Temenos is the integrating
layer that binds four existing tools into one auditable control plane:

    aletheia   provenance gate (prompt-injection detection)
    apatea     adversarial auditor (red-team the gate itself)
    stratum    immutable decision ledger (append-only, evidence-gated)
    stele      integrity harness (session posture + audit)
    adaptive-response   structured, schema-validated agent output

The loop is small and deliberate:

    observe a signal  ->  gate its provenance  ->  apply deterministic policy
    ->  record an immutable decision  ->  escalate only what a human must set.

Temenos never grants authority to a model. It makes the *next honest action*
visible, records the evidence, and preserves the human's judgment for the few
moments where judgment actually matters.
"""

__version__ = "0.1.0"