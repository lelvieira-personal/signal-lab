"""
A malformed secret is refused by name, and never echoed (HANDOFF task 26).

Dummy values only; no network, no macrosynergy import.
"""

from __future__ import annotations

import pytest

from signal_lab.loaders.fred import FredLoader
from signal_lab.loaders.jpmaqs import JPMaQSLoader

DUMMY_ID = "dummy-client-id-7f3a"
DUMMY_SECRET = "dummy-client-secret-91c2"


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.setenv("DQ_CLIENT_ID", DUMMY_ID)
    monkeypatch.setenv("DQ_CLIENT_SECRET", DUMMY_SECRET)
    return monkeypatch


def test_a_clean_pair_passes(params, clean_env):
    assert JPMaQSLoader(params).credentials() == (DUMMY_ID, DUMMY_SECRET)


@pytest.mark.parametrize(
    ("malformed", "defect"),
    [
        (DUMMY_ID + "\r", "carriage return"),
        (DUMMY_ID + " ", "trailing whitespace"),
        ("dummy-client\n-id-7f3a", "line break"),
        ("\t" + DUMMY_ID, "leading whitespace"),
        ("dummy-client\x7f-id-7f3a", "control character"),
    ],
    ids=["trailing-cr", "trailing-space", "embedded-newline", "leading-tab", "del"],
)
def test_a_malformed_value_is_refused_by_name_and_not_echoed(params, clean_env, malformed, defect):
    clean_env.setenv("DQ_CLIENT_ID", malformed)
    with pytest.raises(RuntimeError) as err:
        JPMaQSLoader(params).credentials()
    message = str(err.value)
    assert "DQ_CLIENT_ID" in message
    assert defect in message
    assert DUMMY_ID not in message
    assert "dummy-client" not in message
    assert DUMMY_SECRET not in message


def test_the_crlf_message_says_how_to_fix_it(params, clean_env):
    clean_env.setenv("DQ_CLIENT_SECRET", DUMMY_SECRET + "\r")
    with pytest.raises(RuntimeError, match=r"DQ_CLIENT_SECRET .*CRLF"):
        JPMaQSLoader(params).credentials()


def test_fred_uses_the_same_check(params, monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "dummyfredkey\r")
    with pytest.raises(RuntimeError) as err:
        FredLoader(params).api_key()
    assert "FRED_API_KEY" in str(err.value)
    assert "dummyfredkey" not in str(err.value)
    monkeypatch.setenv("FRED_API_KEY", "dummyfredkey")
    assert FredLoader(params).api_key() == "dummyfredkey"
