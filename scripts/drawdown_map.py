#!/usr/bin/env python3
"""
g(IR, phi): maximum active drawdown per unit of tracking error.

    python scripts/drawdown_map.py            # the table in decisions/proposed/0025
    python scripts/drawdown_map.py --check    # reproduce the decisions/0003 Monte Carlo

The scaling law that makes this useful: an active path with drift mu and
volatility sigma is sigma times a path with drift IR = mu/sigma and unit
volatility, so E[max drawdown] = sigma * g(IR, horizon) exactly. Drawdown is
linear in tracking error and the constant depends only on the information ratio,
the horizon, and the persistence of the active return stream. Inverting a
drawdown tolerance into a tracking-error budget is therefore one division.

Simulated rather than taken from a closed form (Magdon-Ismail and Atiya, 2004):
it costs seconds, it uses the lab's own compounding convention, and the same
function can later be re-run on realised active returns instead of a model --
which is what turns the map from an assumption into a measurement.

Nothing here governs anything. It is evidence for decisions/proposed/0025.
"""

from __future__ import annotations

import argparse
import sys

import _bootstrap  # noqa: F401


def drawdown_per_unit_te(
    irs, years=19.0, periods_per_year=52, n_paths=20000, seed=0, phi=0.0, reference_te=0.06
):
    """
    g(IR) for each IR, as (median, mean, p95) of the maximum-drawdown
    distribution divided by the tracking error it was evaluated at.

    One noise draw is shared across the IR grid so the curve is smooth in IR
    rather than jagged with simulation noise; drawdown is near-linear in TE, so
    evaluating at one reference TE and dividing is enough.
    """
    import numpy as np

    n = int(years * periods_per_year)
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n_paths, n))
    if phi:
        out = np.zeros_like(z)
        out[:, 0] = z[:, 0]
        k = np.sqrt(1.0 - phi * phi)
        for t in range(1, n):
            out[:, t] = phi * out[:, t - 1] + k * z[:, t]
        z = out

    rows = {}
    for ir in irs:
        r = ir * reference_te / periods_per_year + reference_te * z / np.sqrt(periods_per_year)
        cum = np.cumprod(1.0 + r, axis=1)
        worst = (1.0 - cum / np.maximum.accumulate(cum, axis=1)).max(axis=1)
        rows[ir] = tuple(
            float(v) / reference_te
            for v in (np.median(worst), worst.mean(), np.quantile(worst, 0.95))
        )
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tolerance", type=float, default=0.18, help="active drawdown tolerance")
    parser.add_argument("--years", type=float, default=19.0)
    parser.add_argument("--paths", type=int, default=20000)
    parser.add_argument("--phi", type=float, default=0.0, help="active-return autocorrelation")
    parser.add_argument("--check", action="store_true", help="reproduce decisions/0003")
    args = parser.parse_args(argv)

    if args.check:
        published = {0.20: 20.5, 0.30: 18.3, 0.50: 15.3, 0.80: 12.2}
        rows = drawdown_per_unit_te(sorted(published), args.years, n_paths=args.paths)
        print("decisions/0003, median max active drawdown at 6% TE over 19y:")
        print(f"{'IR':>6} {'published':>10} {'simulated':>10}")
        for ir, pub in sorted(published.items()):
            print(f"{ir:>6.2f} {pub:>9.1f}% {rows[ir][0] * 0.06 * 100:>9.1f}%")
        return 0

    grid = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.65, 0.8, 1.0]
    rows = drawdown_per_unit_te(grid, args.years, n_paths=args.paths, phi=args.phi)
    print(
        f"TE budget implied by a {args.tolerance:.0%} active-drawdown tolerance "
        f"over {args.years:.0f}y (phi={args.phi})"
    )
    print(f"{'IR':>6} {'g median':>9} {'budget':>8} | {'g p95':>7} {'budget':>8}")
    for ir in grid:
        med, _mean, p95 = rows[ir]
        print(
            f"{ir:>6.2f} {med:>9.2f} {args.tolerance / med:>7.2%} | "
            f"{p95:>7.2f} {args.tolerance / p95:>7.2%}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
