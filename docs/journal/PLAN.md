# PLAN — temenos

Evidence-gated runtime for autonomous agents. Binds four existing tools into one
product: **aletheia** (provenance gate), **apatea** (adversarial auditor),
**stratum** (immutable decision ledger), **stele** (integrity harness), with
**adaptive-response** as the structured-output contract for agent synthesis.

## Phases

- [x] **P0 — Scaffold + journal.** Repo, git identity, PLAN/DECISIONS/CHECKPOINT.
- [ ] **P1 — Data model + config.** `models.py`, YAML config/policy loaders.
- [ ] **P2 — Tools.** `gate.py` (aletheia), `adversary.py` (apatea), `policy.py`, `ledger.py` (stratum client).
- [ ] **P3 — Orchestrator + CLI.** `orchestrator.py`, `cli.py` (`decide` / `audit` / `serve`).
- [ ] **P4 — Control plane HTTP server.** `server.py` (the Review Gate API).
- [ ] **P5 — Tests.** Unit + end-to-end against a faithful mock stratum.
- [ ] **P6 — Docs + deploy.** README, ARCHITECTURE, SECURITY, Dockerfile/compose/fly.
- [ ] **P7 — Vendor aletheia/apatea as submodules + final validation.**

## Known constraints

- Python 3.11+ (aletheia/apatea floor). Sandbox has 3.14.3.
- aletheia/apatea are **private** on GitHub → vendored as submodules (pinned SHAs).
- Live stratum is behind a Cloudflare challenge from this sandbox → test with a
  local mock that reproduces stratum's contract; live smoke test documented for
  the operator with a real `STRATUM_TOKEN`.
- Writes to stratum require a bearer token (`STRATUM_TOKEN`); non-`demo`/`playground-`
  logs are auth-gated for both read and write.

## Constraints deferred to user

- Repo name/wording (`temenos` is the working title — trivial to rename).
- Making `aletheia`/`apatea` public (needed for a fully self-contained clone).
- Live deployment target (Fly/Render/Railway/Docker-on-VPS) and credentials.