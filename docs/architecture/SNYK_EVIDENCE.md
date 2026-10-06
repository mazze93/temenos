# Snyk as a required evidence predicate

Status: implemented CLI and manual demonstration workflow; live provider execution unverified.

Temenos now refuses release eligibility unless a trusted runner supplies a fresh,
scope-bound Snyk IaC receipt and Stratum acknowledges the decision. Snyk is a
required input to this gate: missing evidence, findings, scan errors, altered
artifacts, or an unavailable ledger all return exit 2. Exit 0 satisfies only this
predicate. It does not authorize a cloud action or establish remediation success.

## Authority perimeter

The trusted runner owns the checkout, pinned scanner, commit/target assignment,
and evidence key. The agent may propose a manifest but cannot mint receipts,
choose the expected scope, replace the verifier, or read its key. HMAC proves
possession of the runner key, not a Snyk-issued signature. Both collector and
verifier are trusted; a compromised runner or key defeats this design.

Collection scans a private snapshot of one standalone Kubernetes YAML or Terraform
plan JSON (full planned values), with policy ignores disabled and no severity
filter. It records CLI version, exit status, report digest, artifact digest,
commit, target, Snyk organization and completion time. Verification accepts only a
complete single-file result with zero findings and an age of at most 15 minutes.
Unknown output shapes deny. The v1 policy has no exceptions or waivers.

The Stratum event asserts the evidence check result, not mutable global closure.
The gate additionally requires a matching append acknowledgment with sequence and
head. Receipts remain separate artifacts, referenced by digest; retain them at
least as long as the associated decision is needed. A lost acknowledgment blocks
even if the append succeeded. Retries create distinct events. No ledger rollback
is attempted.

## Reproduce

Install from a reviewed checkout:

```sh
git submodule update --init --recursive
python -m pip install -e '.[dev]'
pytest tests/test_snyk_gate.py tests/test_snyk_cli.py -q
```

These are deterministic tests with synthetic scanner output and ledger responses,
not claims of a live Snyk or cloud test. Each failure asserts ineligibility:

| Case | Concrete reproduction | Objective |
|---|---|---|
| Forged or misbound evidence | Run `pytest tests/test_snyk_gate.py -k 'forged or scope or substitution' -q`; change the signed report, expected target, or artifact bytes | Least privilege through exact scope binding; broader cloud least privilege remains provider-owned |
| Stale authorization input | Run `pytest tests/test_snyk_gate.py -k 'expired or future' -q`; replay an expired or future receipt | Fresh evidence at evaluation time; not provider authorization-at-time-of-action |
| Incomplete outcome record | Run `pytest tests/test_snyk_gate.py -k 'ledger or nonzero or inconsistent or timeout' -q`; fail scanning or ledger acknowledgment | Evidence completeness; no eligibility on missing or contradictory evidence |

For a live test, install Snyk CLI v1.1307.4 and supply `SNYK_TOKEN`,
`TEMENOS_EVIDENCE_KEY` (a secret random key of at least 32 bytes, hex encoded),
`STRATUM_TOKEN`, `TEMENOS_STRATUM_URL`, `TEMENOS_LOG_ID`, and `SNYK_ORG_ID`.
Use an authenticated HTTPS Stratum endpoint and a dedicated demonstration log.
Never put tokens or the signing key in source or an agent-accessible environment.

```sh
commit=$(git rev-parse HEAD)
temenos snyk-collect --artifact examples/snyk/deployment.yaml \
  --commit "$commit" --target sandbox-demonstration --org "$SNYK_ORG_ID" \
  --output receipt.json
temenos release-check --artifact examples/snyk/deployment.yaml \
  --commit "$commit" --target sandbox-demonstration --org "$SNYK_ORG_ID" \
  --receipt receipt.json
```

The fixture is intentionally privileged: expect findings, exit 2 from release-check,
and a recorded denial. Never deploy it. Inspect receipt and decision together to
distinguish findings from authentication, network, parser, or ledger failures.
The manual `Snyk evidence gate` workflow runs this same path on main only; its
expected denial makes the job red and prevents the next eligibility step.

Before enabling it, create a `snyk-evidence` environment restricted to reviewed
main commits, require an owning-team reviewer, and configure the above secrets
and variables there. Environment protection is an operator setup requirement,
not something the YAML can guarantee. No PR code receives credentials. The
workflow retains the public fixture's receipt and decision for 14 days. Real
plans can contain sensitive values: use restricted retention/storage before
extending this demonstration to them.

## Touchstone result and remaining perimeter

The acknowledgment-composition and scanner-wrapper boundaries initially did not
hold: an altered claim with the same event ID was accepted, and shell-sensitive
filenames reached the scanner wrapper. Regression probes now require unchanged
claim/evidence acknowledgment and restricted filenames; the repaired probes pass.
Other probes cover signed wrong scope, artifact mutation during scanning,
timeouts, contradictory reports, and evidence expiry.

This slice does not implement MCP call dispatch, delegated IAM enforcement,
merge protection, deployment, post-deployment verification, token revocation,
one-use receipts, or independent validation of scanner coverage. A clean report
means this scanner reported no findings in this artifact; it does not prove a
secure environment. The deployment runner must re-evaluate provider authority
and consume the exact immutable artifact after this check. Never turn this
eligibility result into a reusable authorization token. CLI output is bounded
for acceptance, but subprocess capture is not a hard memory sandbox.

Integration contract: [Snyk IaC CLI](https://docs.snyk.io/developer-tools/snyk-cli/commands/iac-test).
