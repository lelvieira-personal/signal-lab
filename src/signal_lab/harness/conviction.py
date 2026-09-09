"""
Conviction: how strongly a model believes what it is telling you.

SUBSTRATE section 4 makes the tracking-error penalty conviction-dependent --
"TE is cheap when conviction dispersion is high and expensive when it is not" --
which means the coefficient is a function, not a number. This module is that
function's input.

The owner's worked example, for a three-state regime model
[risk on, neutral, risk off]:

    [0.40, 0.30, 0.30]   weak    -- barely distinguishable from no view
    [0.70, 0.20, 0.10]   strong  -- the model has actually decided something

Two properties make a conviction measure usable here.

**It is direction-agnostic.** [0.7, 0.2, 0.1] and [0.1, 0.2, 0.7] carry the same
conviction and opposite views. Conviction scales the size of a tilt; the view
sets its sign. Collapsing the two would make a confident risk-off call look like
a weak risk-on one.

**It is bounded in [0, 1]**, with 0 at the uniform distribution (the model knows
nothing) and 1 at a point mass (the model is certain). Bounded so that a penalty
built on it cannot be driven to zero by an overconfident estimate, which is the
failure mode that matters: an overfit regime model reporting a spurious
[0.95, 0.03, 0.02] would otherwise buy itself maximum tracking error at exactly
the wrong moment.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

EPS = 1e-12


def _clean(probabilities) -> np.ndarray:
    p = np.asarray(pd.Series(probabilities, dtype="float64").to_numpy(), dtype="float64")
    if p.ndim != 1 or p.size < 2:
        raise ValueError("conviction needs a probability vector of at least two states")
    if np.any(p < -EPS):
        raise ValueError("probabilities cannot be negative")
    total = p.sum()
    if not np.isfinite(total) or total <= EPS:
        raise ValueError("probabilities must sum to something positive")
    return np.clip(p / total, 0.0, 1.0)


def entropy_conviction(probabilities) -> float:
    """
    1 - H(p) / log(K). The owner's stated method.

    Uses the whole distribution rather than just the mode, so a model that is
    unsure between two states scores differently from one that is unsure across
    all of them. It discriminates hard at the weak end: a near-uniform vector
    scores close to zero, because entropy is flat near the uniform point and
    falls away steeply. Whether that steepness is wanted is a calibration
    question -- see `conviction_comparison`.
    """
    p = _clean(probabilities)
    k = p.size
    nonzero = p[p > EPS]
    entropy = float(-(nonzero * np.log(nonzero)).sum())
    return float(np.clip(1.0 - entropy / np.log(k), 0.0, 1.0))


def max_probability_conviction(probabilities) -> float:
    """
    (max(p) - 1/K) / (1 - 1/K).

    Rescaled so the uniform vector scores 0 rather than 1/K. Ignores the shape
    of the losing states, which is a real loss of information -- but it is close
    to how a portfolio manager reads a state model, and it is far gentler than
    entropy at the weak end.
    """
    p = _clean(probabilities)
    k = p.size
    floor = 1.0 / k
    return float(np.clip((p.max() - floor) / (1.0 - floor), 0.0, 1.0))


def dispersion_conviction(views: pd.Series, cap: float = 3.0) -> float:
    """
    Cross-sectional dispersion of views, as a conviction measure.

    This is the OTHER reading of SUBSTRATE section 4's "conviction dispersion",
    and it is not the same quantity as the two above. Those measure how sure one
    model is about a state; this measures how much the resulting views disagree
    across instruments -- how much there is to bet on.

    The distinction is real: a model can be certain about a regime that implies
    almost no cross-sectional tilt, and an unsure model can produce wide views.
    See decisions/0019 for which one the penalty should read.

    Standard deviation of the (already standardised) views, capped and scaled.
    """
    v = pd.Series(views, dtype="float64").dropna()
    if len(v) < 2:
        return 0.0
    return float(np.clip(v.std() / cap, 0.0, 1.0))


def conviction_series(probabilities: pd.DataFrame, method: str = "entropy") -> pd.Series:
    """Apply a conviction measure row-wise to a dates x states probability frame."""
    fn = {"entropy": entropy_conviction, "max_probability": max_probability_conviction}.get(method)
    if fn is None:
        raise ValueError(f"unknown conviction method {method!r}")
    return probabilities.apply(fn, axis=1)


def conviction_comparison(vectors: dict[str, list[float]]) -> pd.DataFrame:
    """
    The measures side by side on named vectors, for calibration.

    A diagnostic, not a selection tool: choosing the measure that flatters a
    backtest is the same error as choosing a loading estimator that way
    (decisions/0016), and it belongs in a measurement hypothesis.
    """
    return pd.DataFrame(
        {
            "entropy": {k: entropy_conviction(v) for k, v in vectors.items()},
            "max_probability": {k: max_probability_conviction(v) for k, v in vectors.items()},
        }
    )
