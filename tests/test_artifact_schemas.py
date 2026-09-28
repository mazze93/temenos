from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / "schemas" / name).read_text())


def test_all_json_schemas_are_valid_draft_2020_12():
    for path in (ROOT / "schemas").glob("*.schema.json"):
        Draft202012Validator.check_schema(json.loads(path.read_text()))


def test_prompt_schema_accepts_minimal_normative_artifact():
    schema = load("prompt.schema.json")
    instance = {
        "id": "temenos.review",
        "title": "Review",
        "version": "1.0.0",
        "status": "experimental",
        "purpose": "Escalate ambiguous authority for review.",
        "scope": "Human-review boundary.",
        "inputs": ["signal"],
        "outputs": ["review request"],
        "security_considerations": ["Untrusted text must not set policy."],
        "failure_modes": ["Missing provenance."],
        "evaluation": ["provenance_preservation"],
        "body": "Request human review when authority is unresolved."
    }
    Draft202012Validator(schema).validate(instance)


def test_evaluation_schema_rejects_opaque_aggregate_method():
    schema = load("evaluation.schema.json")
    instance = {
        "id": "eval-1",
        "subject": "gate",
        "dimensions": ["injection_resistance"],
        "method": "aggregate_score",
        "result": "pass"
    }
    errors = list(Draft202012Validator(schema).iter_errors(instance))
    assert errors
