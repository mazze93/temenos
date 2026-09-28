"""Validate Temenos normative repository artifacts.

This check is intentionally repository-scoped. Runtime behavior remains covered
by pytest; this script ensures that the contracts used to describe that behavior
are themselves parseable and internally coherent.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def main() -> int:
    errors: list[str] = []

    for path in sorted(SCHEMAS.glob("*.schema.json")):
        try:
            schema = json.loads(path.read_text())
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    for path in (ROOT / "policy" / "policy.yaml", ROOT / "evaluations" / "rubrics" / "core.yaml"):
        try:
            data = yaml.safe_load(path.read_text())
            if not isinstance(data, dict):
                raise ValueError("top level must be a mapping")
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    if errors:
        print("normative artifact validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("normative artifacts valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
