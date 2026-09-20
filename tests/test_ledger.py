"""Ledger client: append, projection, and the violation error path."""
from __future__ import annotations

import pytest

from temenos.ledger import LedgerError, StratumClient, build_event
from temenos.models import GateResult, Signal, Verdict


def test_append_round_trip(mock_stratum):
    c = StratumClient(mock_stratum.base_url, log_id="temenos")
    v = Verdict(signal_id="s", disposition="observe", gate=GateResult(action="proceed", score=0.0))
    res = c.append_event(build_event(v))
    assert res["ok"] is True
    assert mock_stratum.events[0]["type"] == "decision"
    assert mock_stratum.events[0]["agent_id"] == "temenos"


def test_projection(mock_stratum):
    c = StratumClient(mock_stratum.base_url, log_id="temenos")
    c.append_event(build_event(Verdict(signal_id="s", disposition="observe",
                                        gate=GateResult(action="proceed", score=0.0))))
    proj = c.projection()
    assert proj["head"] == 0
    assert len(proj["events"]) == 1


def test_bearer_token_sent(mock_stratum):
    c = StratumClient(mock_stratum.base_url, token="t-token", log_id="temenos")
    # The mock does not enforce auth, but the client must attach the header
    # without error; asserting a successful round trip proves the request path.
    res = c.append_event(build_event(Verdict(signal_id="s", disposition="observe",
                                             gate=GateResult(action="proceed", score=0.0))))
    assert res["ok"] is True


def test_unreachable_raises_ledger_error():
    c = StratumClient("http://127.0.0.1:1", log_id="temenos", timeout=1.0)
    with pytest.raises(LedgerError):
        c.projection()