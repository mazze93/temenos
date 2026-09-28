# Authority Model

Temenos exists to separate **generation** from **authority**.

The normative invariant is:

```text
automation scope ≤ evidence quality × policy clarity
```

## Authority order

When repository artifacts disagree, use this order:

1. Executable schemas under `schemas/`
2. Human-authored policy under `policy/`
3. Runtime contracts enforced by tests under `tests/`
4. Architecture Decision Records under `docs/adr/`
5. Explanatory architecture and guides
6. README examples

Lower layers explain higher layers; they do not override them.

## Runtime authority

The currently implemented runtime is:

```text
signal → Aletheia gate → deterministic policy → Stratum ledger
```

Apatea audits the gate out-of-band. Stele and adaptive-response are related
components in the wider stack, but they are **not runtime dependencies of the
current Temenos 0.1 implementation** unless and until an ADR and executable test
establish that integration.

## Trust boundary

A field does not become authoritative because a model emitted it. Governing
parameters require an attributable source, and provenance must survive every
transformation into the decision ledger.

Temenos may abstain, escalate, or record uncertainty. It must not silently
manufacture authority to keep a workflow moving.
