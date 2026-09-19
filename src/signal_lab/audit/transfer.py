"""
The transfer coefficient, measured. decisions/0033.

    IR_constrained = TC * IR_unconstrained

`breadth.implied_ic()` has taken a `transfer` argument since it was written and
nothing had ever estimated it, so every implied IC the ruler printed assumed the
long-only constraint, the cash and position caps and the turnover shadow cost
lose nothing. These are three estimators, computed per rebalance from what the
constrained solve already produced -- its alpha and its weights -- and none of
them re-solves anything unconstrained. That is the point: decisions/0029 found
the unconstrained twin measures its own covariance error, not the constraints.

The geometry is the solver's. A book is `w` over the holdable series, fully
invested, and its active return is `w' e` on the returns in EXCESS of the
benchmark, `e_i = r_i - b'r`. So the active covariance is

    Omega = E Sigma E',   E = S' - 1 b'

and `x' Sigma x` for the solver's active vector `x = S w - b` is exactly
`w' Omega w`. `a` is the alpha the rule solved against.

    C  full matrix   a'w / [ sqrt(a' Omega^-1 a) sqrt(w' Omega w) ]
                     Clarke, de Silva and Thorley (2006) eq. 23. The reported
                     TC, and the only one for which the identity above is exact.
    A  diagonal      corr(a_i / s_i, w_i s_i),  s_i = sqrt(Omega_ii)
                     The form comparable to the published 0.3-0.8 range. It
                     ignores correlations and CDT's own example puts it below C.
    B  alignment     corr(a, Omega w)
                     Needs no inverse, so it carries no conditioning exposure.
                     It is 1 if and only if the book is proportional to the
                     unconstrained optimum, which makes it a control on C, not
                     a level.

C solves `Omega x = a` once per date, on the same shrunk covariance the solver
built the book from, and is exposed to its small eigenvalues, so the condition
number of Omega is reported beside every reading.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

_NAN = float("nan")

ROW_KEYS = (
    "transfer_coefficient",
    "transfer_coefficient_diagonal",
    "transfer_coefficient_alignment",
    "omega_condition_median",
    "omega_condition_max",
    "transfer_n_dates",
)


def empty_row() -> dict[str, float]:
    """What a cell reports when its rule did not say what alpha it solved against."""
    row = {k: _NAN for k in ROW_KEYS}
    row["transfer_n_dates"] = 0
    return row


def active_covariance(
    sigma: pd.DataFrame, hold: list[str], legs: list[str], leg_weights: pd.Series
) -> np.ndarray:
    """Omega = E Sigma E', the covariance of the holdable series in excess of the benchmark."""
    ids = list(sigma.index)
    h = [ids.index(i) for i in hold]
    b = np.zeros(len(ids))
    for leg in legs:
        b[ids.index(leg)] = float(leg_weights[leg])
    s = sigma.to_numpy(dtype=float)
    sb = s[h, :] @ b
    return s[np.ix_(h, h)] - sb[:, None] - sb[None, :] + float(b @ s @ b)


def _corr(x: np.ndarray, y: np.ndarray) -> float:
    if x.std() < 1e-15 or y.std() < 1e-15:
        return _NAN
    return float(np.corrcoef(x, y)[0, 1])


def coefficients(a: np.ndarray, w: np.ndarray, omega: np.ndarray) -> dict[str, float]:
    """The three estimators and the condition number, for one rebalance."""
    out = {"full": _NAN, "diagonal": _NAN, "alignment": _NAN, "condition": _NAN}
    try:
        out["condition"] = float(np.linalg.cond(omega))
    except np.linalg.LinAlgError:
        return out
    ow = omega @ w
    var_w = float(w @ ow)
    scale = np.sqrt(np.clip(np.diag(omega), 0.0, None))
    if np.all(scale > 0):
        out["diagonal"] = _corr(a / scale, w * scale)
    out["alignment"] = _corr(a, ow)
    try:
        ainv = float(a @ np.linalg.solve(omega, a))
    except np.linalg.LinAlgError:
        return out
    if ainv > 0 and var_w > 0:
        out["full"] = float(a @ w) / (np.sqrt(ainv) * np.sqrt(var_w))
    return out


def path_transfer(path: Any, universe: Any, cell: Any) -> dict[str, float]:
    """
    One cell's transfer coefficient, averaged over its rebalances.

    A path whose rule did not expose its alpha yields no reading -- NaN columns
    and `transfer_n_dates = 0` -- rather than a coefficient built on a guess.
    """
    alpha = getattr(path, "alpha", None)
    if alpha is None or len(alpha) == 0:
        return empty_row()
    legs = universe.leg_ids
    rows = []
    for date in path.weights.index.intersection(alpha.index):
        cov = universe.covariance(date, cell.vol_halflife, cell.vol_overlay)
        hold = [h for h in alpha.columns if h in cov.ids]
        if not hold:
            continue
        omega = active_covariance(cov.matrix, hold, legs, universe.leg_weights)
        a = alpha.loc[date, hold].fillna(0.0).to_numpy(dtype=float)
        w = path.weights.loc[date].reindex(hold).fillna(0.0).to_numpy(dtype=float)
        rows.append(coefficients(a, w, omega))
    if not rows:
        return empty_row()
    frame = pd.DataFrame(rows)

    def mean(col: str) -> float:
        v = frame[col].dropna()
        return float(v.mean()) if len(v) else _NAN

    cond = frame["condition"].dropna()
    return {
        "transfer_coefficient": mean("full"),
        "transfer_coefficient_diagonal": mean("diagonal"),
        "transfer_coefficient_alignment": mean("alignment"),
        "omega_condition_median": float(cond.median()) if len(cond) else _NAN,
        "omega_condition_max": float(cond.max()) if len(cond) else _NAN,
        "transfer_n_dates": int(frame["full"].notna().sum()),
    }
