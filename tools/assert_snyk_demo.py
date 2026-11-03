#!/usr/bin/env python3
"""Verify the paired live Snyk + Stratum demo. Not a promotion authorization."""
import argparse
import json
from pathlib import Path

def read(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected object")
    return data

def verify(receipt_path, decision_path, gate_exit, *, findings, label):
    envelope = read(receipt_path)
    r = envelope.get("receipt")
    if not isinstance(r, dict) or not isinstance(envelope.get("signature"), str):
        raise ValueError(f"{label}: signed receipt missing")
    if r.get("failure") is not None:
        raise ValueError(f"{label}: scanner failed; not a security verdict")
    scanner_exit = 1 if findings else 0
    if r.get("exit_code") != scanner_exit:
        raise ValueError(f"{label}: unexpected scanner exit {r.get('exit_code')}")
    report = r.get("report")
    if isinstance(report, list) and len(report) == 1:
        report = report[0]
    if not isinstance(report, dict) or report.get("ok") is not True or report.get("error") or report.get("errors"):
        raise ValueError(f"{label}: malformed Snyk result")
    issues = report.get("infrastructureAsCodeIssues")
    if not isinstance(issues, list) or bool(issues) != findings:
        raise ValueError(f"{label}: missing or contradictory finding list")
    decision = read(decision_path)
    if decision.get("recorded") is not True or not isinstance(decision.get("event_id"), str):
        raise ValueError(f"{label}: Stratum append not acknowledged")
    if decision.get("eligible") is not (not findings):
        raise ValueError(f"{label}: eligibility mismatch")
    if decision.get("reasons") != (["snyk_evidence_denied"] if findings else []):
        raise ValueError(f"{label}: incorrect denial reason")
    if gate_exit != (2 if findings else 0):
        raise ValueError(f"{label}: unexpected release-check exit {gate_exit}")
    print(f"{label}: verified scanner result, policy outcome, Stratum acknowledgment")

def main():
    p = argparse.ArgumentParser()
    for name in ("clean", "unsafe"):
        p.add_argument(f"--{name}-receipt", required=True)
        p.add_argument(f"--{name}-decision", required=True)
        p.add_argument(f"--{name}-exit", type=int, required=True)
    a = p.parse_args()
    verify(a.clean_receipt, a.clean_decision, a.clean_exit, findings=False, label="clean")
    verify(a.unsafe_receipt, a.unsafe_decision, a.unsafe_exit, findings=True, label="unsafe")
    print("Paired evidence gate verified; no deployment or provider IAM verified.")

if __name__ == "__main__":
    main()
