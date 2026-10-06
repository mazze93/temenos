import json

from temenos.cli import main
from temenos import snyk


def test_release_check_missing_key_fails_closed(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv('TEMENOS_EVIDENCE_KEY', raising=False)
    result = main(['release-check', '--artifact', str(tmp_path/'pod.yaml'),
                   '--receipt', str(tmp_path/'receipt.json'), '--commit', 'a'*40,
                   '--target', 'sandbox-a', '--org', 'org-a'])
    assert result == 2
    assert json.loads(capsys.readouterr().out)['eligible'] is False


def test_release_check_denial_returns_nonzero(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('TEMENOS_EVIDENCE_KEY', 'ab'*32)
    artifact = tmp_path/'pod.yaml'; artifact.write_text('kind: Pod')
    receipt = tmp_path/'receipt.json'; receipt.write_text('{}')
    monkeypatch.setattr(snyk, 'evaluate', lambda *args, **kwargs: {'eligible': False, 'reasons': ['denied']})
    result = main(['release-check', '--artifact', str(artifact), '--receipt', str(receipt),
                   '--commit', 'a'*40, '--target', 'sandbox-a', '--org', 'org-a'])
    assert result == 2
    assert json.loads(capsys.readouterr().out)['eligible'] is False


def test_release_check_eligible_returns_zero(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('TEMENOS_EVIDENCE_KEY', 'ab'*32)
    receipt = tmp_path/'receipt.json'; receipt.write_text('{}')
    monkeypatch.setattr(snyk, 'evaluate', lambda *args, **kwargs: {'eligible': True})
    result = main(['release-check', '--artifact', 'pod.yaml', '--receipt', str(receipt),
                   '--commit', 'a'*40, '--target', 'sandbox-a', '--org', 'org-a'])
    assert result == 0
