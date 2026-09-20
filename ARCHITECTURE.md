# Architecture

Temenos is not a monolith and not a rewrite. It is a thin, stdlib-first
orchestration layer that gives four existing tools one coherent interface and,
critically, one coherent **authority model**.

```
                        ┌────────────────────────────────────────────┐
                        │                 Temenos                     │
                        │                                            │
  ┌───────────┐         │  ┌─────────┐   ┌────────┐   ┌───────────┐  │
  │  signal   │ ────────▶│  │  gate   │──▶│ policy │──▶│  ledger   │──┼──▶ stratum
  │ (PR body, │         │  │ aletheia│   │ (YAML) │   │ (client)  │  │    (append)
  │  tool out)│         │  └─────────┘   └────────┘   └───────────┘  │
  └───────────┘         │        ▲                        │         │
                        │        │                        ▼         │
                        │  ┌─────────┐               ┌───────────┐  │
                        │  │adversary│               │  control  │──┼──▶ HTTP
                        │  │ apatea  │               │  plane    │  │    /decide
                        │  └─────────┘               └───────────┘  │
                        └────────────────────────────────────────────┘
```

## Components

### gate — aletheia (vendored)

Provenance is the load-bearing idea. Aletheia maps each origin to a trust class
(`user`/`agent`/`file` = trusted, `mcp_tool` = semi-trusted, `web_*`/`clipboard` =
untrusted) and scores content for governing parameters, urgency, prescriptive
framing, authority claims, and structural mimicry. Judging and enforcing are
separate modules by design; temenos preserves that separation.

`temenos/gate.py` builds aletheia's `Event` from a `Signal`, runs `assess`, then
asks aletheia's `decide` for `proceed`/`verify`/`stop`.

### policy — deterministic

A human-authored YAML file maps the gate verdict to a **disposition**:

```
observe            proceed        recorded, nothing else
review             verify          a human should inspect
approve_required   stop            a human must set direction
```

There is no DSL and no model in this path. The ordering is the policy, and it is
versioned like code. The verdict's evidence is shaped here, so the ledger write
is a pure append of an already-validated record.

### ledger — stratum

Stratum's contract is tiny: append an immutable event, or read the derived
projection. Temenos speaks it exactly — snake_case at the wire, `evidence` entries
carry `checked_at: null` when cited-but-not-checked. A `checked_at` is non-null
only when temenos actually performed the check, so "verified" is never a synonym
for "trusted because I said so."

The ledger client is `urllib`-only deliberately: the audit path — the one
component that must never fail to write — has no third-party supply chain.

### adversary — apatea

A gate is judged by what it stops; nothing measures what it misses. Apatea holds
stated invariants (monotonicity, extent stability, determinism) and searches
**transformations** of real inputs for the cases where aletheia's assessor goes
blind. Temenos points it at the vendored gate via `ALETHEIA_HOME`, so `temenos
audit` is a one-command answer to "is my gate still honest?"

### control plane — server

A stdlib `ThreadingHTTPServer` exposes three endpoints (`/health`, `/decide`,
`/queue`). It is the programmatic surface, not the dashboard — the human review
UI already exists as stratum's Atrium. Temenos deliberately does not re-ship one.

## Authority model

The single invariant the whole system exists to preserve:

```
automation scope  ≤  evidence quality  ×  policy clarity
```

When evidence is thin or policy is ambiguous, temenos **abstains and escalates**
rather than inferring permission. Every field that could govern an action must
have a declared source, and untrusted sources cannot supply one without the
human knowing.

## What is new vs. reused

Temenos adds the orchestration layer and the unified authority model. The four
tools are pre-existing, separately-maintained systems with their own tests and
threat models. This is a feature, not a shortcut: the gate, the adversary, and
the ledger are independently auditable, and temenos inherits their guarantees
instead of re-implementing them.