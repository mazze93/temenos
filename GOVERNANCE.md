# Governance

Temenos is maintainer-led and evidence-constrained.

## Maintainer authority

Maintainers may merge, release, deprecate, and revise architecture. Normative
changes remain reviewable because their authority is expressed in versioned
policy, schemas, tests, and ADRs rather than undocumented convention.

## Decision process

```text
proposal → evidence → review → ADR when consequential → implementation → evaluation → release
```

Rejections should record the reason when they affect architecture or future
compatibility.

## Releases

- Semantic versioning is used for the Python package.
- Normative schema changes must be called out in `CHANGELOG.md`.
- Breaking schema or policy changes require migration notes.
- A release must not claim an integration that lacks executable wiring and tests.

## Deprecation

Deprecated contracts remain documented for at least one minor release where
practical, with a replacement path.
