"""decisions/0048: a run at any thread setting but one refuses to start."""

from __future__ import annotations

import pytest

from signal_lab.threads import THREAD_VARS, ThreadSettingError, require_one_thread, thread_setting


def test_one_thread_everywhere_passes(monkeypatch):
    for name in THREAD_VARS:
        monkeypatch.setenv(name, "1")
    assert require_one_thread() == dict.fromkeys(THREAD_VARS, "1")


@pytest.mark.parametrize("name", THREAD_VARS)
def test_any_other_setting_refuses_and_names_it(monkeypatch, name):
    for n in THREAD_VARS:
        monkeypatch.setenv(n, "1")
    monkeypatch.setenv(name, "4")
    with pytest.raises(ThreadSettingError, match=f"{name}=4"):
        require_one_thread()


def test_unset_refuses_and_is_recorded_as_unset(monkeypatch):
    for n in THREAD_VARS:
        monkeypatch.delenv(n, raising=False)
    assert set(thread_setting().values()) == {"unset"}
    with pytest.raises(ThreadSettingError, match="unset"):
        require_one_thread()
