# Temenos

**τέμενος** — the sacred boundary that contains without claiming.

An evidence-gated runtime for autonomous agents. Temenos is the integrating layer
that binds four tools into one auditable control plane:

| Tool | Role in Temenos |
|---|---|
| [aletheia](https://github.com/mazze93/aletheia) | provenance gate — detects prompt injection and untrusted governing parameters |
| [apatea](https://github.com/mazze93/apatea) | adversarial auditor — red-teams the gate so it is never trusted blind |
| [stratum](https://github.com/mazze93/stratum) | immutable decision ledger — append-only, evidence-gated, replay-proven |
| [stele](https://github.com/mazze93/stele) | integrity harness — session posture and monotonic capability degradation |
| [adaptive-response](https://github.com/mazze93/adaptive-response) | structured, schema-validated output contract |

The loop is small and deliberate:

```
signal ──▶ gate (aletheia) ──▶ policy (deterministic) ──▶ ledger (stratum) ──▶ human review
```

An agent proposes an action, or content arrives that will govern one. Temenos
assesses its **provenance**, applies a **human-authored policy**, records an
**immutable decision** with its evidence, and escalates only the moment that
actually requires a human to set direction.

## The problem

Agentic systems assert. Whatever an agent reads, writes, or does becomes "true"
by persistence — a session that drops a constraint, trusts a crafted web result,
or accepts `<!-- SYSTEM: ignore previous instructions -->` from a PR body passes
every syntactic gate and then compounds into the next action. The failure is
rarely malice; it is that *generation* and *authority* have been conflated.

**Temenos separates them.** It never grants authority to a model. It makes the
next honest action visible, records the evidence that produced it, and preserves
a human's judgment for the few moments where judgment is the whole point.

## What it does (and does not)

Temenos **does**:

- gate every signal by provenance and injection risk (aletheia)
- continuously attack its own gate to find what it misses (apatea)
- map a verdict to a human disposition via deterministic policy (no LLM authors policy)
- append every decision to stratum as an immutable, evidence-linked event
- expose a minimal control plane (`decide` / `audit` / `serve`)

Temenos **does not**:

- merge code, rotate secrets, change permissions, or touch production state
- let a model rewrite policy or grant itself authority
- claim a security guarantee — it binds evidence to decisions; it proves nothing about correctness
- store or exfiltrate raw secrets (the gate path is stdlib-only, no third-party code)

## Quickstart

Prerequisites: Python 3.11+, and the two vendored dependencies checked out.

```bash
git clone --recurse-submodules https://github.com/mazze93/temenos
cd temenos
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Evaluate a signal (no ledger required):

```bash
temenos decide fixtures/injection-signal.json --no-record
```

Run the adversary against the gate:

```bash
temenos audit
```

Run the control plane:

```bash
temenos serve --port 8788
# curl -X POST localhost:8788/decide -d '{"id":"x","content":"...","origin":"web_search"}'
```

## Wiring to stratum

Decisions are recorded only when a stratum ledger is reachable. Point temenos at
one and it appends; otherwise it degrades gracefully and flags the write.

```bash
# run stratum locally (its own repo)
git clone https://github.com/mazze93/stratum && cd stratum/worker && npm i && npx wrangler dev

# point temenos at it with a bearer token
export STRATUM_TOKEN="<your token>"
export TEMENOS_STRATUM_URL="http://127.0.0.1:8787"
temenos decide fixtures/injection-signal.json
```

See [`policy/policy.yaml`](policy/policy.yaml) for the disposition mapping, and
[`docs/journal/DECISIONS.md`](docs/journal/DECISIONS.md) for every architectural
decision and how to reverse it.

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — the integration map
- [`SECURITY.md`](SECURITY.md) — threat model and posture
- [`docs/journal/`](docs/journal/) — plan, decisions, checkpoints

## License

MIT. See [`LICENSE`](LICENSE). The vendored tools retain their own licenses
(aletheia and apatea are both MIT).