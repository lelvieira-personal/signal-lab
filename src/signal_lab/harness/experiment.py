"""
`run_experiment()` — the only sanctioned way to run anything.

SUBSTRATE section 2: "Run experiments through `run_experiment()` and only
through it." So it lives here rather than inside a script, and every caller
goes through it.

The chain, and what is missing from each link:

    hypothesis
      -> signal module      phase 3. Nothing registered; the Implementer role
                            writes these from the hypothesis file.
      -> exposure matrix    phase 2. Estimated, walk-forward (decisions/0015).
      -> optimiser          phase 2. Views in exposure space -> long-only
                            weights, subject to section 4 and the objective.
      -> weight rule
      -> walk-forward engine   PHASE 1, BUILT AND VALIDATED
      -> RunContext -> vetoes -> store

Phase 1 finished the last three links. The first three raise precise, separate
errors rather than one vague "not implemented", because "blocked: no signal
module for real_policy_rate_change_3m" tells the owner what to build next and
"blocked: no engine" told them nothing they did not already know.

`validate_pipeline()` runs a planted synthetic path through the built part of
the chain end to end. It exists to prove the plumbing, and its runs are tagged
`status='validation'` and excluded from the leaderboard, because a run that
tests the harness is not a result about markets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from signal_lab.harness.conviction import entropy_conviction  # noqa: F401  (phase 2 objective)
from signal_lab.harness.costs import CostModel
from signal_lab.harness.engine import (
    PortfolioPath,
    constant_exposures,
    run_walk_forward,
    to_run_context,
)
from signal_lab.harness.hypotheses import Hypothesis
from signal_lab.harness.run_context import RunContext
from signal_lab.harness.snapshot import Snapshot
from signal_lab.loaders.base import ReturnPanel
from signal_lab.params import Params, get_params


class ExperimentBlocked(Exception):
    """A link in the chain is missing. The `status` attribute says which."""

    status = "blocked:unknown"


class SignalModuleMissing(ExperimentBlocked):
    """No signal module implements this hypothesis. Phase 3."""

    status = "blocked:no_signal_module"


class ExposureMatrixMissing(ExperimentBlocked):
    """No characteristic map for this snapshot. Phase 2."""

    status = "blocked:no_exposure_matrix"


class OptimiserMissing(ExperimentBlocked):
    """No exposure-space solver. Phase 2."""

    status = "blocked:no_optimiser"


# Phase 3 registers signal modules here, keyed by the hypothesis `signal` field.
# Empty by design: SUBSTRATE section 5.6 keeps the search shut until the macro
# block lands, so a module registered now could not be run anyway.
SIGNAL_MODULES: dict[str, Any] = {}


@dataclass
class ExperimentResult:
    """What a completed run produced, before any veto has looked at it."""

    run_context: RunContext
    path: PortfolioPath
    metrics: dict[str, float]
    artifacts: dict[str, pd.DataFrame]
    status: str = "completed"


def resolve_signal_module(hypothesis: Hypothesis):
    """
    The module that implements this hypothesis: a signal, or for a measurement
    hypothesis an estimator. Named by kind so the digest reads correctly --
    "no estimator implements conviction_..." rather than calling it a signal.
    """
    module = SIGNAL_MODULES.get(hypothesis.signal)
    if module is None:
        what = "estimator" if hypothesis.is_measurement else "signal module"
        raise SignalModuleMissing(
            f"no {what} implements {hypothesis.signal!r} (family {hypothesis.family}); "
            f"the Implementer role writes it in phase 3"
        )
    return module


def resolve_exposures(snapshot: Snapshot, params: Params | None = None):
    """
    The characteristic map as of each date. Phase 2 (decisions/0015).

    Raises rather than returning an identity matrix. A silent identity would
    make every exposure equal its weight, the risk decomposition would report
    pure idiosyncratic risk, and nothing would look broken.
    """
    raise ExposureMatrixMissing(
        "no characteristic map in data/characteristics/; the exposure matrix is "
        "estimated walk-forward in phase 2 (decisions/0015, 0016)"
    )


def build_weight_rule(hypothesis: Hypothesis, snapshot: Snapshot, params: Params):
    """Signal -> views in exposure space -> long-only weights. Phase 2."""
    resolve_signal_module(hypothesis)
    raise OptimiserMissing(
        "no exposure-space solver; views are mapped to long-only weights in phase 2"
    )


def run_experiment(
    hypothesis: Hypothesis,
    snapshot: Snapshot,
    panel: ReturnPanel,
    benchmark: pd.Series,
    params: Params | None = None,
    seed: int = 0,
) -> ExperimentResult:
    """
    Run one pre-registered hypothesis. The only sanctioned entry point.

    Raises an `ExperimentBlocked` subclass while any link is missing, and the
    caller records `exc.status` so the digest names the actual obstacle.
    """
    params = params or get_params()
    weight_rule = build_weight_rule(hypothesis, snapshot, params)
    exposures = resolve_exposures(snapshot, params)
    path = run_walk_forward(panel, weight_rule, benchmark, exposures, params=params)
    return _package(path, panel, params, run_id=f"R-{hypothesis.id}", seed=seed)


def validate_pipeline(
    panel: ReturnPanel,
    run_id: str,
    params: Params | None = None,
    target_ir: float = 0.5,
    target_te: float = 0.04,
    seed: int = 777,
) -> ExperimentResult:
    """
    Drive the built half of the chain end to end on a planted synthetic path.

    Proves the plumbing -- engine, costs, veto inputs, metrics, artifacts --
    without a signal module or an optimiser. Tagged `validation` so it can never
    reach the leaderboard: it is a statement about the harness, not about
    markets, and the planted IR was put there on purpose.
    """
    from signal_lab.loaders.synthetic import plant_weight_path

    params = params or get_params()
    weight_rule, benchmark, truth = plant_weight_path(
        panel, target_ir=target_ir, target_te=target_te, seed=seed
    )
    ids = weight_rule(panel.returns.index[0], panel).index
    exposures = constant_exposures(pd.DataFrame(0.0, index=ids, columns=["f0"]))

    path = run_walk_forward(
        panel, weight_rule, benchmark, exposures, cost_model=CostModel(params), params=params
    )
    result = _package(path, panel, params, run_id=run_id, seed=seed, status="validation")
    result.metrics["planted_ir"] = truth.target_ir
    result.metrics["planted_max_drawdown"] = truth.target_max_drawdown * 100
    result.metrics["ir_recovery_error"] = abs(path.information_ratio() - truth.target_ir)
    return result


def _package(
    path: PortfolioPath,
    panel: ReturnPanel,
    params: Params,
    run_id: str,
    seed: int,
    status: str = "completed",
) -> ExperimentResult:
    """Turn a completed path into veto inputs, metrics and artifacts."""
    ctx = to_run_context(path, run_id, panel)
    ctx.seed = seed

    summary = path.summary()
    metrics = {k: float(v) for k, v in summary.items() if pd.notna(v)}

    artifacts = {
        "weights": path.weights,
        "active_returns": path.active_returns.to_frame("active_return"),
        "net_returns": path.net_returns.to_frame("net_return"),
        "turnover": pd.DataFrame(
            {"traded_notional": path.turnover, "one_way": path.turnover_one_way}
        ),
        "cost_drag": path.cost_drag.to_frame("cost_drag"),
        "exposures": path.exposures,
        "active_drawdown": path.active_drawdown().to_frame("active_drawdown"),
    }
    te = path.tracking_error().dropna()
    if not te.empty:
        artifacts["tracking_error"] = te.to_frame("trailing_3y_te")

    return ExperimentResult(
        run_context=ctx, path=path, metrics=metrics, artifacts=artifacts, status=status
    )
