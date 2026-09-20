# DECISIONS

Append-only. Reversals are appended, never edits.

- **2026-09-20 · language** · Python 3.11+ · aletheia/apatea are canonical Python
  stdlib; the mature Strands/Python runtime is a natural fit. · reverse: port the
  integration to TS if the Cloudflare Worker surface becomes mandatory.
- **2026-09-20 · working name** · `temenos` (the sacred boundary that contains
  without claiming) · matches the strand of Greek/architectural names; short and
  greppable. · reverse: `git mv` + sed, ~5 minutes.
- **2026-09-20 · dependency shape** · aletheia/apatea vendored as **git submodules**
  under `vendor/`, pinned to SHAs · single source of truth + reproducibility, no
  PyPI publishing needed while they remain private. · reverse: publish both to PyPI
  and declare them as normal deps.
- **2026-09-20 · stratum reachability** · ledger client built to stratum's public
  contract (`POST /api/logs/:id/events`, snake_case payload) and tested against a
  stdlib mock; live endpoint is challenge-gated from this sandbox · honest test
  surface without a fake credential. · reverse: switch tests to hit
  `wrangler dev` when run on the operator's machine.
- **2026-09-20 · policy layer** · deterministic mapping from aletheia's verdict +
  user YAML to a human disposition (`observe|review|approve_required|blocked|deferred|resolved`)
  · the LLM never authors policy; it only narrates ambiguity. No mini-DSL invented. ·
  reverse: none expected.