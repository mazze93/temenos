"""Trusted-runner Snyk IaC evidence. Eligibility is not deployment authority.

The runner owns the HMAC key, scanner binary, source checkout and CI identity.
Never expose collect() or its key to an agent-controlled execution environment.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

POLICY = 'snyk-iac/no-findings/v1'
MAX_BYTES = 10 * 1024 * 1024


class GateError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _key(key):
    if not isinstance(key, bytes) or len(key) < 32:
        raise GateError('runner evidence key must contain at least 32 bytes')


def seal(receipt, key):
    _key(key)
    return {'receipt': receipt, 'signature': hmac.new(key, canonical(receipt), hashlib.sha256).hexdigest()}


def _scope(commit, target, org):
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise GateError('commit must be a full lowercase Git SHA-1')
    if any(not isinstance(v, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}', v)
           for v in (target, org)):
        raise GateError('target and org must be explicit scope identifiers')


def _artifact(path):
    path = Path(path)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', path.name):
        raise GateError('artifact filename must be shell-wrapper safe')
    if path.is_symlink() or not path.is_file() or path.suffix.lower() not in ('.json', '.yaml', '.yml'):
        raise GateError('artifact must be a regular standalone YAML or JSON file, not a symlink')
    if path.stat().st_size > MAX_BYTES:
        raise GateError('artifact exceeds 10 MiB')
    return path.read_bytes()


def collect(artifact, *, commit, target, org, key, now=time.time, run=subprocess.run):
    """Scan a private snapshot; bind the result to the trusted runner's scope.

    Commit/target are runner attestations, not values recovered from Snyk.
    No shell, policy overrides, severity filtering or model-produced reports.
    """
    _key(key)
    _scope(commit, target, org)
    artifact = Path(artifact)
    content = _artifact(artifact)
    version, report, code, failure = '', None, None, None
    with tempfile.TemporaryDirectory(prefix='temenos-snyk-') as tmp:
        snapshot = Path(tmp) / artifact.name
        snapshot.write_bytes(content)
        snapshot.chmod(0o400)
        try:
            version_run = run(['snyk', '--version'], cwd=tmp, capture_output=True,
                              text=True, timeout=30, shell=False, check=False)
            version = version_run.stdout.strip()
            if version_run.returncode != 0 or not re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][\w.-]+)?', version):
                raise GateError('scanner version unavailable')
            result = run(['snyk', 'iac', 'test', str(snapshot), '--json', '--ignore-policy',
                          '--scan=planned-values', f'--org={org}'], cwd=tmp,
                         capture_output=True, text=True, timeout=300, shell=False, check=False)
            code = result.returncode
            if len(result.stdout.encode()) > MAX_BYTES:
                raise GateError('scanner report exceeds 10 MiB')
            report = json.loads(result.stdout)
        except (OSError, subprocess.SubprocessError, ValueError):
            # Do not persist stderr or exception text: either may include credentials.
            failure = 'scanner_unavailable_or_invalid_output'
        if snapshot.read_bytes() != content or _artifact(artifact) != content:
            raise GateError('artifact changed during scan')
    receipt = {
        'schema_version': 1, 'policy': POLICY, 'scanner': 'snyk-iac',
        'scanner_version': version, 'commit': commit, 'target': target, 'org': org,
        'artifact_name': artifact.name, 'artifact_sha256': digest(content),
        'finished_at': int(now()), 'exit_code': code, 'failure': failure,
        'report': report, 'report_sha256': digest(canonical(report)),
    }
    return seal(receipt, key)


def _check(envelope, *, artifact, commit, target, org, key, now, max_age):
    _key(key)
    _scope(commit, target, org)
    if not isinstance(envelope, dict) or set(envelope) != {'receipt', 'signature'}:
        raise GateError('missing signed receipt')
    r, signature = envelope['receipt'], envelope['signature']
    if not isinstance(r, dict) or not isinstance(signature, str):
        raise GateError('invalid receipt shape')
    expected = seal(r, key)['signature']
    if not hmac.compare_digest(expected, signature):
        raise GateError('invalid runner signature')
    required = {'schema_version','policy','scanner','scanner_version','commit','target','org',
                'artifact_name','artifact_sha256','finished_at','exit_code','failure','report','report_sha256'}
    if set(r) != required or type(r['schema_version']) is not int or r['schema_version'] != 1:
        raise GateError('unsupported receipt contract')
    if r['policy'] != POLICY or r['scanner'] != 'snyk-iac':
        raise GateError('scanner policy mismatch')
    if (r['commit'], r['target'], r['org']) != (commit, target, org):
        raise GateError('receipt scope mismatch')
    if type(max_age) is not int or not 0 < max_age <= 3600:
        raise GateError('evidence lifetime must be between 1 and 3600 seconds')
    if type(r['finished_at']) is not int or not 0 <= now-r['finished_at'] <= max_age:
        raise GateError('expired or future receipt')
    if r['artifact_name'] != Path(artifact).name or r['artifact_sha256'] != digest(_artifact(artifact)):
        raise GateError('artifact mismatch')
    if r['failure'] is not None or type(r['exit_code']) is not int or r['exit_code'] != 0:
        raise GateError('Snyk findings or incomplete scan')
    if not isinstance(r['scanner_version'], str) or not re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][\w.-]+)?', r['scanner_version']):
        raise GateError('invalid scanner version')
    report = r['report']
    if digest(canonical(report)) != r['report_sha256']:
        raise GateError('report digest mismatch')
    # v1 deliberately supports one result for one standalone artifact.
    if isinstance(report, list) and len(report) == 1:
        report = report[0]
    if not isinstance(report, dict) or report.get('ok') is not True or report.get('error') or report.get('errors'):
        raise GateError('missing or unsuccessful Snyk result')
    if report.get('infrastructureAsCodeIssues') != []:
        raise GateError('findings present or missing issue collection')
    target_file = report.get('targetFile')
    if not isinstance(target_file, str) or Path(target_file).name != r['artifact_name']:
        raise GateError('scanner result target mismatch')
    return r


def evaluate(envelope, *, artifact, commit, target, org, key, ledger, now=None, max_age=900):
    """Require sound receipt binding AND a matching Stratum append acknowledgement.

    A receipt may be re-evaluated while fresh; this is not a single-use action
    token. The deployment runner must consume the same immutable artifact and
    enforce current IAM, review and environment approval independently.
    """
    now = int(time.time()) if now is None else now
    reasons = []
    try:
        r = _check(envelope, artifact=artifact, commit=commit, target=target, org=org,
                   key=key, now=now, max_age=max_age)
    except (GateError, OSError, ValueError, TypeError, KeyError):
        reasons.append('snyk_evidence_denied')
        r = None
    event_id = 'temenos:promotion:' + uuid.uuid4().hex
    claim = {'eligible': not reasons, 'scope': 'snyk_iac_evidence_gate_only',
             'commit': commit, 'target': target, 'org': org, 'policy': POLICY, 'reasons': reasons.copy()}
    event = {'id': event_id, 'type': 'decision', 'agent_id': 'temenos-snyk',
             'schema_version': 1, 'birth_status': 'asserted', 'claim': claim,
             'evidence': [] if r is None else [{
                 'kind': 'snyk_iac_receipt', 'ref': 'sha256:' + digest(canonical(envelope)),
                 'checked_at': datetime.fromtimestamp(now, timezone.utc).isoformat(),
                 'signer': 'trusted-runner-hmac'}],
             'targets': [], 'is_trust_root': False, 'timestamp': None}
    recorded = False
    try:
        ack = ledger.append_event(event)
        recorded = (isinstance(ack, dict) and ack.get('ok') is True
                    and isinstance(ack.get('event'), dict)
                    and all(ack['event'].get(k) == event[k] for k in
                            ('id', 'type', 'claim', 'evidence', 'targets', 'birth_status'))
                    and type(ack.get('seq')) is int and ack['seq'] >= 0
                    and type(ack.get('head')) is int and ack['head'] >= ack['seq'])
    except Exception:
        # Any ambiguous transport/provider response blocks the gate.
        recorded = False
    if not recorded:
        reasons.append('ledger_unacknowledged')
    return {'eligible': not reasons, 'scope': 'snyk_iac_evidence_gate_only',
            'reasons': reasons, 'recorded': recorded, 'event_id': event_id}
