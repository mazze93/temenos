# Security

Temenos is itself a security system, so its own posture matters more than most.
This file states the threat model, the guarantees, and — deliberately — the
places where temenos promises nothing.

## Threat model

| Threat | Where it is addressed | What temenos can and cannot claim |
|---|---|---|
| Prompt injection in PR bodies / tool output / web results | aletheia provenance + scoring | It *flags* and can *block*; it cannot eliminate false negatives |
| Gate evasions (case folding, invisible chars, structural mimicry) | apatea invariant search | It *searches*; it cannot prove no evasion exists |
| Decision tampering after the fact | stratum append-only ledger, hash-chained evidence | It *records* immutably; it cannot undo a bad decision |
| Session integrity / configuration drift | stele (when wired) | monotonic capability degradation, not prevention |
| Model output drift / unbounded prose | adaptive-response schema (when wired) | enforces shape, not truth |

## Guarantees vs. non-guarantees

**Guaranteed** (by construction):

- Provenance is carried, never inferred. An origin's trust class comes from the
  declared source, not from the words "critical" or a semver string.
- Policy is deterministic and human-authored. No model writes or edits policy.
- Status is derived, never stored. Temenos writes events; stratum folds status.
- A ledger outage degrades loudly, never silently: the decision returns with an
  `unresolved` entry naming the failed write.

**Not guaranteed** (stated on purpose):

- A `proceed` verdict is not a security guarantee. The gate is a probabilistic
  filter, not a proof.
- `checked_at` evidence means "a check was performed," not "the check was
  meaningful." That line is drawn explicitly in stratum's own contract.
- Temenos does not validate correctness of the *underlying* action — only the
  provenance of the content that would govern it.

## Secret and token handling

- `STRATUM_TOKEN` is read from the environment, never from files or config.
- The gate path (`gate.py`, `policy.py`, `ledger.py`) is stdlib-only. The one
  runtime dependency, `pyyaml`, is used only to parse human-authored config and
  never runs in the request path.
- Signals are treated as untrusted input end to end; nothing in a signal is ever
  `eval`'d, shelled, or interpolated into a command.

## Known limitations

- `serve` binds loopback by default and has no auth of its own; put it behind a
  reverse proxy / API gateway with its own auth before exposing it.
- The adversary audit is CPU-bound and unbounded; run it out-of-band (cron), not
  in a request path.
- The vendored submodules are pinned to SHAs, but their own dependencies remain
  their responsibility; audit them on update.

Report a vulnerability privately rather than opening a public issue. See the
repository's security advisory settings.