#!/usr/bin/env python3
"""
The null distribution of the WORST annual bias statistic.

    python scripts/bias_map.py              # the table in decisions/proposed/0030
    python scripts/bias_map.py --check      # reproduce the analytic Gaussian case

`decisions/0030` makes the realised tracking error a disclosed characteristic
and puts the ex-post gate on the risk MODEL instead: the bias statistic, the
standard deviation of z_t = r_t / sigma_ex_ante(t-1), which is 1 when a book
runs the risk it was sized for. `decisions/0027` section 2 introduced it as a
full-sample number, and the TE path probe showed that reading is too coarse to
gate on -- it came out 0.92 to 1.01 on Bloomberg base cells whose 2008 reading
was 2.03. A gate has to read the worst year, not the average of sixteen.

Reading the worst of K draws needs the null distribution of that maximum, which
is what this produces. Two properties of the real z series drive it and neither
is optional:

**Fat tails.** The sampling variance of a standard deviation is
Var(s^2) = sigma^4 (2/(n-1) + kappa/n) in excess kurtosis kappa, so tails widen
the null band directly. Measured on the seventeen Bloomberg base cells of
`results/audit/_probe/TE-20260917-bbg1`, the median excess kurtosis of z is
2.37 (range 1.04 to 14.65). Assuming kappa = 0 would put the analytic annual
standard deviation at 0.099 against 0.146 -- a threshold roughly 47 per cent
too tight, and a veto that kills honestly sized books.

**Autocorrelation.** Measured at -0.068 (range -0.105 to 0.036), so materially
absent. It is a knob here anyway, because a future signal set could change it
and the number should be re-derivable rather than re-argued.

Simulated rather than taken from the closed form, for the reasons
`scripts/drawdown_map.py` gives: it costs seconds, it composes the calendar the
way the audit actually reads it, and the same function can later be run on
realised z series instead of a model.

Nothing here governs anything. It is evidence for `decisions/proposed/0030`.
"""

from __future__ import annotations

import argparse
import sys

import _bootstrap

_bootstrap.require_one_thread()


def _unit_variance_t(rng, shape, kurtosis: float):
    """Student-t scaled to unit variance, or normal when kurtosis is 0.

    Excess kurtosis of a t with nu degrees of freedom is 6/(nu-4), so a target
    kappa fixes nu = 4 + 6/kappa. Below about nu = 5 the fourth moment is barely
    finite and the simulated kurtosis is itself wild; that is a property of the
    distribution, not a defect here.
    """
    import numpy as np

    if kurtosis <= 0:
        return rng.standard_normal(shape)
    nu = 4.0 + 6.0 / float(kurtosis)
    return rng.standard_t(nu, size=shape) / np.sqrt(nu / (nu - 2.0))


def worst_annual_bias(
    years: int = 16,
    periods_per_year: int = 52,
    kurtosis: float = 2.37,
    phi: float = 0.0,
    n_paths: int = 40000,
    seed: int = 0,
):
    """
    The distribution of max over years of the annual bias reading, under a
    CORRECTLY specified risk model.

    The null is z ~ unit variance, so every reading is an estimate of 1 and the
    maximum is above 1 by construction. Returns (median, p95, p99, mean of the
    full-sample reading), the last as the control: it is the number
    `decisions/0027` gates on today and it barely moves.
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    n = years * periods_per_year
    z = _unit_variance_t(rng, (n_paths, n), kurtosis)
    if phi:
        out = np.zeros_like(z)
        out[:, 0] = z[:, 0]
        k = np.sqrt(1.0 - phi * phi)
        for t in range(1, n):
            out[:, t] = phi * out[:, t - 1] + k * z[:, t]
        z = out
    blocks = z.reshape(n_paths, years, periods_per_year)
    annual = blocks.std(axis=2, ddof=1)
    worst = annual.max(axis=1)
    return (
        float(np.median(worst)),
        float(np.quantile(worst, 0.95)),
        float(np.quantile(worst, 0.99)),
        float(z.std(axis=1, ddof=1).mean()),
    )


def main(argv=None) -> int:
    import numpy as np

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, default=16)
    parser.add_argument("--periods-per-year", type=int, default=52)
    parser.add_argument("--kurtosis", type=float, default=2.37, help="excess kurtosis of z")
    parser.add_argument("--phi", type=float, default=0.0)
    parser.add_argument("--paths", type=int, default=40000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--check", action="store_true", help="analytic Gaussian cross-check")
    args = parser.parse_args(argv)

    if args.check:
        n = args.periods_per_year
        analytic = 0.5 * np.sqrt(2.0 / (n - 1))
        med, p95, p99, full = worst_annual_bias(
            years=1, periods_per_year=n, kurtosis=0.0, n_paths=args.paths, seed=args.seed
        )
        rng = np.random.default_rng(args.seed)
        simulated = float(rng.standard_normal((args.paths, n)).std(axis=1, ddof=1).std())
        print(f"one year, gaussian: analytic sd {analytic:.4f}  simulated sd {simulated:.4f}")
        print(f"  median {med:.3f}  p95 {p95:.3f}  p99 {p99:.3f}")
        return 0

    print(f"Worst annual bias statistic under a correct model, {args.years} years")
    print(f"of {args.periods_per_year} readings, {args.paths} paths.\n")
    print("| excess kurtosis | phi | median worst | p95 worst | p99 worst | full-sample |")
    print("|---|---|---|---|---|---|")
    for kappa in (0.0, 1.0, args.kurtosis, 4.0):
        for phi in sorted({0.0, args.phi}):
            med, p95, p99, full = worst_annual_bias(
                years=args.years,
                periods_per_year=args.periods_per_year,
                kurtosis=kappa,
                phi=phi,
                n_paths=args.paths,
                seed=args.seed,
            )
            print(
                f"| {kappa:.2f} | {phi:+.2f} | {med:.3f} | **{p95:.3f}** | {p99:.3f} | {full:.3f} |"
            )
    print(
        f"\nMeasured on the Bloomberg base cells: excess kurtosis {args.kurtosis:.2f}, "
        f"phi about -0.07."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
