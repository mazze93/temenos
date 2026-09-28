# Architecture

Temenos is a thin orchestration layer around an explicit authority boundary.

```text
                           TEMENOS RUNTIME
┌──────────┐     ┌───────────────┐     ┌─────────────┐     ┌──────────┐
│  signal  │ ──▶ │ Aletheia gate │ ──▶ │ policy.yaml │ ──▶ │ Stratum  │
└──────────┘     └───────────────┘     └─────────────┘     └────┬─────┘
                         ▲                                      │
                         │                                      ▼
                   ┌──────────┐                           human review
                   │  Apatea  │
                   │  audit   │
                   └──────────┘
```

## Runtime layers

### Signal

A `Signal` is content that may influence an action: PR text, a web result,
tool output, a commit message, or another external artifact. Provenance enters
with the signal; Temenos does not infer trusted origin from persuasive language.

### Gate

`temenos/gate.py` adapts a Signal into Aletheia, which assesses prompt-injection
risk and governing parameters. Temenos normalizes the result but does not add a
second hidden scoring system.

### Policy

`policy/policy.yaml` maps `proceed / verify / stop` to a human-facing
disposition. It is deterministic, versioned, and human-authored.

### Ledger

`temenos/ledger.py` shapes the verdict into a Stratum decision event. Status is
derived by Stratum rather than stored as mutable state in Temenos. Failed writes
surface as unresolved state.

### Adversary

Apatea is out-of-band. It searches transformations and invariants for cases in
which the gate becomes inconsistent or blind. An audit is evidence about the
gate, not proof that no evasion exists.

## Repository contract layers

Temenos also separates runtime implementation from repository authority:

```text
schemas/      machine-readable artifact contracts
policy/       human-authored operational rules
tests/        executable behavior claims
docs/adr/     consequential decisions
docs/         explanations and guides
research/     analysis; never automatically normative
assets/       communication layer
```

The ordering is deliberate. See
[`docs/architecture/AUTHORITY.md`](docs/architecture/AUTHORITY.md).

## Provenance

The provenance schema records enough context to reconstruct how an artifact was
produced: inputs and hashes, workflow version, optional model metadata, tools,
transformations, evaluations, and human edits.

Reconstruction is the goal; deterministic replay of stochastic inference is not
assumed.

## Evaluation

Evaluation methods remain disaggregated:

- deterministic validation;
- behavioral/adversarial regression;
- model-based evaluation;
- human review.

No method automatically grants authority to the artifact being evaluated.

## Adjacent stack components

Stele and adaptive-response are architecturally compatible with Temenos but are
not part of the current executable runtime. Integration becomes normative only
when implementation, tests, and an ADR establish it.

## Security boundary

The principal invariant remains:

```text
automation scope ≤ evidence quality × policy clarity
```

When evidence is thin or policy is ambiguous, Temenos may abstain or escalate.
It must not manufacture permission.
