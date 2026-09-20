"""temenos — command-line interface.

Three verbs, each a single step of the loop:

    temenos decide    evaluate a signal and record the decision
    temenos audit     run the adversary against the gate
    temenos serve     run the control-plane HTTP server
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_settings
from .models import Signal
from .orchestrator import Temenos


def _read_signal(path: str | None) -> dict:
    if path and path != "-":
        raw = Path(path).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    if not raw.strip():
        raise SystemExit("no signal provided (empty stdin/file)")
    return json.loads(raw)


def _signal_from(d: dict) -> Signal:
    return Signal(
        id=d.get("id", ""),
        content=d.get("content", ""),
        origin=d.get("origin", "unclassified"),
        tool=d.get("tool", ""),
        event=d.get("event", ""),
        taint=tuple(d.get("taint", [])),
        intended_action=d.get("intended_action"),
        source=d.get("source", ""),
    )


def cmd_decide(args, temenos: Temenos) -> int:
    d = _read_signal(args.file)
    signal = _signal_from(d)
    verdict = temenos.decide(signal, record=not args.no_record)
    print(json.dumps(verdict.to_dict(), indent=2, ensure_ascii=False))
    # Non-zero exit mirrors the disposition so scripts can act on it.
    return 2 if verdict.disposition in ("approve_required", "blocked") else 0


def cmd_audit(args, temenos: Temenos) -> int:
    report = temenos.audit(target=args.target, origin=args.origin)
    print(report.text)
    if not args.summary:
        print(json.dumps({
            "clean": report.clean,
            "checks": report.checks,
            "violations": report.violations,
            "findings": report.findings,
        }, indent=2, ensure_ascii=False))
    return 0 if report.clean else 1


def cmd_serve(args, temenos: Temenos) -> int:
    from .server import run

    run(temenos, host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="temenos", description=__doc__)
    p.add_argument("--config", default=None, help="path to config YAML/JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("decide", help="evaluate a signal and record the decision")
    d.add_argument("file", nargs="?", help="signal JSON (or - for stdin)")
    d.add_argument("--no-record", action="store_true", help="do not write to stratum")
    d.set_defaults(func=cmd_decide)

    a = sub.add_parser("audit", help="run the adversary against the gate")
    a.add_argument("--target", default="aletheia")
    a.add_argument("--origin", default="web_search")
    a.add_argument("--summary", action="store_true", help="perimeter only, no findings")
    a.set_defaults(func=cmd_audit)

    s = sub.add_parser("serve", help="run the control-plane HTTP server")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8788)
    s.set_defaults(func=cmd_serve)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings(args.config)
    temenos = Temenos(settings)
    return args.func(args, temenos)


if __name__ == "__main__":
    raise SystemExit(main())