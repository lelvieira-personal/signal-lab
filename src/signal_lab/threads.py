"""
One thread is the lab's reference configuration (decisions/0048).

A BLAS built for several threads sums in a different order from run to run, so
the recorded numbers repeat only at one thread. `make` exports the three
variables; a run made at any other setting refuses to start rather than record
a number that cannot be reproduced.
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
