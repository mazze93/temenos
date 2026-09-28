# ADR-0001: Establish a normative repository core

- **Status:** Accepted
- **Date:** 2026-09-28

## Context

Temenos already has a working runtime, tests, a threat model, and an append-only
decision path. What it lacked was a repository-level distinction between
normative contracts and explanatory material.

That ambiguity matters in an evidence-gated system: prose should not silently
become policy.

## Decision

The normative core is:

- `schemas/` — machine-readable artifact contracts
- `policy/` — human-authored operational policy
- `tests/` — executable behavior claims
- `docs/adr/` — consequential architectural decisions

Documentation, diagrams, white papers, and examples are explanatory layers.

## Consequences

- Repository claims can be checked against artifacts rather than maintainer memory.
- Prompt/provenance/evaluation formats become independently inspectable.
- Future integrations require an ADR plus tests before being described as wired.
- CI must validate the normative artifacts.
