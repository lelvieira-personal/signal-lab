"""
One thread is the lab's reference configuration (decisions/0048).

The recorded numbers depend on the thread count: HANDOFF task 49 measured
four goldens in `tests/test_baseline.py` that read differently with the three
variables set to 1 than with them unset (net IR differences of 1e-4 to 1e-3), and
with them at 1 the same four values came back from two fresh processes. It did
not measure a difference between runs at one setting. `make` exports the three
variables; a run made at any other setting refuses to start rather than record
a number made under a configuration it cannot name.
"""

from __future__ import annotations

import os

THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")


class ThreadSettingError(RuntimeError):
    pass


def thread_setting() -> dict[str, str]:
    """The three variables as set, `unset` where absent. Recorded in run summaries."""
    return {name: os.environ.get(name, "unset") for name in THREAD_VARS}


def require_one_thread() -> dict[str, str]:
    setting = thread_setting()
    bad = {k: v for k, v in setting.items() if v.strip() != "1"}
    if bad:
        shown = ", ".join(f"{k}={v}" for k, v in bad.items())
        raise ThreadSettingError(
            f"numbers are made at one thread (decisions/0048); {shown}. "
            "Use `make <target>`, which sets all three to 1, or export "
            f"{' '.join(f'{k}=1' for k in THREAD_VARS)} before calling python directly."
        )
    return setting
