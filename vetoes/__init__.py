"""
The veto set. SUBSTRATE.md section 10. Owner-only: agents may not edit this
package, and may not change a threshold to make a run pass (section 2).

Eleven boolean functions, each `veto(run_context, params) -> Verdict`. They are
applied to every run and evaluated BEFORE any return statistic is computed or
displayed, so that a run that should not be looked at is never looked at.

Design rules, all of them deliberate:

  * Thresholds come from params/vetoes.yaml. No number is written in this
    package.
  * A veto whose input is missing FAILS. Fail-open would put an unmeasured run
    on the leaderboard; fail-closed only costs an engineer an error message.
  * Every verdict carries a detail string with the realised value against the
    threshold, so a reader can see how close a run was rather than only whether
    it passed.
  * apply_vetoes records ALL verdicts and returns the first failure in the
    order set by params. Recording only the first failure would hide that a run
    breached five constraints, which is diagnostic information.
"""

from vetoes.registry import VETO_ORDER, VETOES, apply_vetoes, first_failure
from vetoes.rules import (
    veto_active_drawdown,
    veto_cash,
    veto_coverage,
    veto_direction,
    veto_frequency,
    veto_lookahead,
    veto_multiple_testing,
    veto_positions,
    veto_seed_stability,
    veto_tracking_error,
    veto_turnover,
)

__all__ = [
    "VETOES",
    "VETO_ORDER",
    "apply_vetoes",
    "first_failure",
    "veto_active_drawdown",
    "veto_cash",
    "veto_coverage",
    "veto_direction",
    "veto_frequency",
    "veto_lookahead",
    "veto_multiple_testing",
    "veto_positions",
    "veto_seed_stability",
    "veto_tracking_error",
    "veto_turnover",
]
