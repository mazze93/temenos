# Contributing

Temenos accepts changes that make authority, evidence, or failure states more
legible.

## Change classes

- **Runtime:** code under `temenos/`; requires tests.
- **Normative:** schemas, policy, or authority rules; requires tests and an ADR
  when semantics change.
- **Evaluation:** fixtures, rubrics, or reports; must identify method and evidence.
- **Documentation:** explanatory only; must not silently redefine normative behavior.

## Pull requests

1. State the claim being changed.
2. Identify the authoritative artifact that supports the change.
3. Add or update tests for behavioral changes.
4. Add an ADR for consequential or difficult-to-reverse decisions.
5. Run `python tools/validate_artifacts.py` and `pytest`.

Security vulnerabilities should follow `SECURITY.md`, not a public issue.
