import copy
import hashlib
import json
import subprocess

import pytest

from temenos.snyk import collect, evaluate, GateError

KEY = b'a' * 32
COMMIT = 'a' * 40
NOW = 1800000000


class Ledger:
    def __init__(self):
        self.events = []

    def append_event(self, event):
        self.events.append(event)
        return {'ok': True, 'event': event, 'seq': 0, 'head': 0}


@pytest.fixture
def artifact(tmp_path):
    p = tmp_path / 'deployment.yaml'
    p.write_text('apiVersion: v1\nkind: Pod\n')
    return p


def runner(exit_code=0, report=None):
    if report is None:
        report = {'ok': True, 'targetFile': 'deployment.yaml', 'infrastructureAsCodeIssues': []}
    def run(args, **kwargs):
        if args[-1] == '--version':
            return subprocess.CompletedProcess(args, 0, '1.1300.0', '')
        assert '--ignore-policy' in args
        assert '--scan=planned-values' in args
        assert kwargs['shell'] is False
        return subprocess.CompletedProcess(args, exit_code, json.dumps(report), '')
    return run


def receipt(artifact, **kwargs):
    return collect(artifact, commit=COMMIT, target='sandbox-a', org='org-a',
                   key=KEY, now=lambda: NOW, run=runner(**kwargs))


def check(artifact, envelope, ledger=None, **kwargs):
    return evaluate(envelope, artifact=artifact, commit=COMMIT, target='sandbox-a',
                    org='org-a', key=KEY, ledger=ledger or Ledger(), now=NOW, **kwargs)


def test_clean_scan_requires_recorded_decision(artifact):
    ledger = Ledger()
    result = check(artifact, receipt(artifact), ledger)
    assert result['eligible'] is True
    assert ledger.events[0]['birth_status'] == 'asserted'
    assert ledger.events[0]['claim']['scope'] == 'snyk_iac_evidence_gate_only'
    assert ledger.events[0]['evidence'][0]['ref'].startswith('sha256:')


@pytest.mark.parametrize('code', [1, 2, 3, -9, 99])
def test_every_nonzero_scan_exit_blocks(artifact, code):
    result = check(artifact, receipt(artifact, exit_code=code))
    assert not result['eligible']


@pytest.mark.parametrize('report', [{}, [], {'ok': True}, {'ok': True, 'infrastructureAsCodeIssues': []},
    {'ok': True, 'targetFile': 'deployment.yaml', 'infrastructureAsCodeIssues': [{'id': 'RULE', 'severity': 'high'}]},
    {'ok': True, 'targetFile': 'elsewhere.yaml', 'infrastructureAsCodeIssues': []},
    {'ok': True, 'targetFile': 'deployment.yaml', 'infrastructureAsCodeIssues': [], 'error': 'partial failure'}])
def test_empty_inconsistent_or_wrong_target_report_blocks(artifact, report):
    assert not check(artifact, receipt(artifact, report=report))['eligible']


def test_forged_scan_result_rejected(artifact):
    envelope = receipt(artifact, exit_code=1)
    envelope['receipt']['exit_code'] = 0
    assert not check(artifact, envelope)['eligible']


def test_wrong_key_rejected(artifact):
    envelope = receipt(artifact)
    envelope['signature'] = '0' * 64
    assert not check(artifact, envelope)['eligible']


@pytest.mark.parametrize('field,value', [('commit','b'*40), ('target','sandbox-b'), ('org','org-b')])
def test_valid_signature_cannot_authorize_other_scope(artifact, field, value):
    from temenos.snyk import seal
    envelope = receipt(artifact)
    envelope['receipt'][field] = value
    envelope = seal(envelope['receipt'], KEY)
    assert not check(artifact, envelope)['eligible']


def test_artifact_substitution_rejected(artifact):
    envelope = receipt(artifact)
    artifact.write_text('changed')
    assert not check(artifact, envelope)['eligible']


@pytest.mark.parametrize('offset', [-3601, 1])
def test_expired_or_future_receipt_rejected(artifact, offset):
    from temenos.snyk import seal
    envelope = receipt(artifact)
    envelope['receipt']['finished_at'] += offset
    assert not check(artifact, seal(envelope['receipt'], KEY))['eligible']


def test_ledger_failure_cannot_return_success(artifact):
    class Dead:
        def append_event(self, event):
            raise OSError('unavailable')
    assert not check(artifact, receipt(artifact), Dead())['eligible']


def test_invalid_ledger_ack_cannot_return_success(artifact):
    class Bad:
        def append_event(self, event):
            return {'ok': True}
    assert not check(artifact, receipt(artifact), Bad())['eligible']


def test_scan_timeout_is_signed_failure(artifact):
    def timeout(args, **kwargs):
        raise subprocess.TimeoutExpired(args, 1)
    envelope = collect(artifact, commit=COMMIT, target='sandbox-a', org='org-a',
                       key=KEY, now=lambda: NOW, run=timeout)
    assert not check(artifact, envelope)['eligible']


def test_collector_scans_isolated_copy_and_detects_mutation(artifact):
    def mutate(args, **kwargs):
        if args[-1] != '--version':
            artifact.write_text('substituted while scanning')
        return runner()(args, **kwargs)
    with pytest.raises(GateError, match='changed'):
        collect(artifact, commit=COMMIT, target='sandbox-a', org='org-a',
                key=KEY, now=lambda: NOW, run=mutate)


@pytest.mark.parametrize('name', ['bad;echo.yaml', 'space name.yaml', '$(id).yaml'])
def test_shell_wrapper_metacharacters_rejected(artifact, name):
    unsafe = artifact.with_name(name)
    unsafe.write_bytes(artifact.read_bytes())
    with pytest.raises(GateError):
        receipt(unsafe)


def test_ledger_ack_must_preserve_claim(artifact):
    class Altered:
        def append_event(self, event):
            altered = copy.deepcopy(event)
            altered['claim']['target'] = 'other'
            return {'ok': True, 'event': altered, 'seq': 0, 'head': 0}
    assert not check(artifact, receipt(artifact), Altered())['eligible']
