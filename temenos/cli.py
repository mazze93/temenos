"""temenos — command-line interface.

Three verbs, each a single step of the loop:

    temenos decide    evaluate a signal and record the decision
    temenos audit     run the adversary against the gate
    temenos serve     run the control-plane HTTP server
"""
from __future__ import annotations

import argparse
import json
import os
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


def cmd_snyk(args, temenos: Temenos) -> int:
    from .snyk import collect, evaluate, GateError
    try:
        key = bytes.fromhex(os.environ.get('TEMENOS_EVIDENCE_KEY', ''))
        if len(key) < 32:
            raise GateError('missing runner key')
        scope = dict(artifact=Path(args.artifact), commit=args.commit,
                     target=args.target, org=args.org, key=key)
        if args.cmd == 'snyk-collect':
            if Path(args.output).exists():
                raise GateError('receipt output already exists')
            envelope = collect(**scope)
            # Exclusive creation: never overwrite the scanned artifact or an old receipt.
            with open(args.output, 'x', encoding='utf-8') as stream:
                json.dump(envelope, stream, indent=2, allow_nan=False)
            print(json.dumps({'collected': True, 'receipt': args.output,
                              'scope': 'collection_only_not_release_approval'}))
            return 0 if envelope['receipt']['failure'] is None else 2
        receipt_path = Path(args.receipt)
        if receipt_path.stat().st_size > 12 * 1024 * 1024:
            raise GateError('receipt too large')
        envelope = json.loads(receipt_path.read_text())
        result = evaluate(envelope, **scope, ledger=temenos.ledger)
        print(json.dumps(result))
        return 0 if result['eligible'] else 2
    except (OSError, ValueError, TypeError):
        # Input errors are denials; never echo token-bearing process output.
        print(json.dumps({'eligible': False, 'reasons': ['invalid_or_unavailable_evidence']}))
        return 2


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

    for command in ('snyk-collect', 'release-check'):
        q = sub.add_parser(command, help='collect or gate trusted-runner Snyk IaC evidence')
        q.add_argument('--artifact', required=True, help='one standalone YAML or Terraform plan JSON')
        q.add_argument('--commit', required=True, help='full commit SHA attested by the trusted runner')
        q.add_argument('--target', required=True, help='explicit promotion target identifier')
        q.add_argument('--org', required=True, help='Snyk organization ID or slug')
        if command == 'snyk-collect':
            q.add_argument('--output', required=True, help='new signed receipt file')
        else:
            q.add_argument('--receipt', required=True, help='signed receipt to check')
        q.set_defaults(func=cmd_snyk)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings(args.config)
    temenos = Temenos(settings)
    return args.func(args, temenos)


if __name__ == "__main__":
    raise SystemExit(main())
