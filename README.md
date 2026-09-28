# Temenos

**τέμενος** — the sacred boundary that contains without claiming.

Temenos is an **evidence-gated runtime for autonomous agents**. Its purpose is
not to make model output authoritative; it is to preserve the boundary between
what an agent generated, what evidence supports, what policy permits, and where
a human must set direction.

```text
signal → Aletheia gate → deterministic policy → Stratum ledger → human review
```

Apatea audits the gate out-of-band.

## Why it exists

Agentic systems often collapse generation and authority. A model reads a PR
body, web result, tool output, or prior model message; the content persists;
later behavior treats that persistence as permission.

Temenos separates those layers:

- **provenance** describes where a governing signal came from;
- **gate evidence** describes what was observed about it;
- **policy** maps evidence to a human-authored disposition;
- **Stratum** records the decision as an immutable event;
- **human review** resolves what automation is not authorized to infer.

The load-bearing invariant is:

```text
automation scope ≤ evidence quality × policy clarity
```

## Implemented runtime

| Component | Current role |
|---|---|
| [Aletheia](https://github.com/mazze93/aletheia) | provenance and prompt-injection gate |
| `policy/policy.yaml` | deterministic human-authored disposition mapping |
| [Stratum](https://github.com/mazze93/stratum) | append-only evidence/decision ledger |
| [Apatea](https://github.com/mazze93/apatea) | adversarial audit of the gate |

[Stele](https://github.com/mazze93/stele) and
[adaptive-response](https://github.com/mazze93/adaptive-response) belong to the
wider integrity stack, but **are not runtime dependencies of Temenos 0.1**.
Future integration must be established by code, tests, and an ADR before the
README claims otherwise.

## Normative core

Repository authority is intentionally explicit:

1. `schemas/` — machine-readable artifact contracts
2. `policy/` — human-authored operational policy
3. `tests/` — executable behavior claims
4. `docs/adr/` — consequential architectural decisions
5. explanatory documentation and examples

See [Authority Model](docs/architecture/AUTHORITY.md).

This prevents a white paper, README sentence, or model-generated explanation
from silently becoming operational policy.

## What Temenos does

- carries provenance into the decision path;
- gates signals for injection and governing-parameter risk;
- applies deterministic policy;
- records evidence-linked decisions to Stratum;
- surfaces ledger failures rather than hiding them;
- adversarially audits the gate;
- exposes a small `decide / audit / serve` control plane.

## What it does not do

- grant a model permission to rewrite policy;
- claim that a `proceed` verdict proves safety;
- merge code, rotate secrets, or mutate production state on its own;
- treat evaluator output as authority;
- hide uncertainty to keep a workflow moving.

## Quickstart

Prerequisites: Python 3.11+ and the vendored submodules.

```bash
git clone --recurse-submodules https://github.com/mazze93/temenos
cd temenos
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Evaluate without writing to the ledger:

```bash
temenos decide fixtures/injection-signal.json --no-record
```

Audit the gate:

```bash
temenos audit
```

Validate repository contracts:

```bash
python tools/validate_artifacts.py
pytest -q
```

Run the control plane:

```bash
temenos serve --port 8788
```

## Stratum

Point Temenos at a reachable Stratum worker to persist decisions.

```bash
export STRATUM_TOKEN="<your token>"
export TEMENOS_STRATUM_URL="http://127.0.0.1:8787"
temenos decide fixtures/injection-signal.json
```

A failed ledger write is returned as unresolved state; persistence failure is
never silently converted into success.

## Evaluation

Temenos separates deterministic, behavioral, model-based, and human evaluation.
It deliberately does **not** collapse these into one trust score.

See:

- [evaluations/README.md](evaluations/README.md)
- [evaluations/rubrics/core.yaml](evaluations/rubrics/core.yaml)
- [SECURITY.md](SECURITY.md)

## Contributing and governance

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [GOVERNANCE.md](GOVERNANCE.md)
- [CHANGELOG.md](CHANGELOG.md)
- [CITATION.cff](CITATION.cff)

## License

MIT. Vendored projects retain their own licenses.
