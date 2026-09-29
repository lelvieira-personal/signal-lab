#!/usr/bin/env python3
"""
FDR against FWER: a statistics-level Monte Carlo on the registry's shape.
HANDOFF task 34. **No engine runs** -- test statistics are modelled directly,
calibrated on task 30's `A-20260926-161749` and the knee run.

    make fdr-study

Writes `results/fdr_vs_fwer/<stamp>/summary.csv` and `report.md`. `params/`,
`vetoes/` and `SUBSTRATE.md` are untouched; the gate stays FWER (Romano-Wolf)
until the owner rules OWNER-QUEUE L16.

The model: `m` hypotheses, one per `hypotheses/pending/*.yaml`, grouped by
`target_axis`. Under the null every hypothesis's hypothetical excess statistic
is `N(0, 1)`; `n_true` of them are real, at `N(mu, s^2)`, same correlation
structure. Correlation is equicorrelated: `rho_w` within an axis, `rho_b`
between axes (`rho_w >= rho_b`; the reverse is not a valid equicorrelation
structure and (rho_w=0, rho_b=0.2) is skipped for that reason -- see
`VALID_CORRELATIONS`). `T0`, the `k`-row null draw matrix each procedure
needs, is drawn independently per replication from the SAME correlation
structure, exactly the property a block shuffle gives the real audit
(SUBSTRATE section 9): the shuffle destroys alignment but not a signal's
correlation with its neighbours.

Grid actually run, and why it is not the full cross product the task text
lays out (see the receipt): the full cross of {5 valid correlations} x
{6 k values} x {4 n_true} x {2 calibrated mu, when n_true > 0} is run at
5,000 replications each. The mu SWEEP (0.5, 1.0, 1.5, 2.0, 3.0), which is for
a power CURVE rather than the grid, is run only at the headline correlation
(rho_w=0.3, rho_b=0.2) and k=1000, for n_true in {1, 3, 6}. Crossing the
sweep through the full correlation x k grid as well would be a further 5x,
for a dimension the task itself frames as "for the curve", i.e. against mu
at one representative point, not a fifth grid axis.

HANDOFF task 38 extends `K_GRID` to {20, 50, 100, 200, 500, 1000} and adds
`p_any_pass`, `pfdr` and `false_share_expected`. `romano_shaikh_wolf_fdr` is
still not implemented (see its docstring -- a genuine indexing ambiguity in
the paper, not the task 34 citation error), so the FDR side of this study
remains BH and BY only; `PROCEDURES` carries no RSW-FDR row.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import _bootstrap  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parents[1]
PENDING_DIR = REPO_ROOT / "hypotheses" / "pending"
OUT_ROOT = REPO_ROOT / "results" / "fdr_vs_fwer"

# Calibrated on task 30 (A-20260926-161749) and the knee grid (HANDOFF.md 2026-09-28
# receipts). Pooled null sd at IC 0.70 was 0.168; the paired excess mean was 0.255
# and its sd across seeds was 0.193 -- mu and s below are both in units of that null
# sd, which is what standardises the modelled statistic to N(0,1) under the null.
NULL_SD_0_70 = 0.168
MU_IC_070 = 0.255 / NULL_SD_0_70
S_IC_070 = 0.193 / NULL_SD_0_70
# IC 0.35's mu comes from the knee grid's 10-seed paired excess (0.095), over the
# SAME pooled null sd (0.168) -- the task does not ask for a separate null-sd
# measurement at 0.35, and the knee and power grids share a live signal construction.
# s is NOT separately measured at 0.35; it is ASSUMED equal to the 0.70 figure.
MU_IC_035 = 0.095 / NULL_SD_0_70
S_IC_035 = S_IC_070  # assumed, not measured -- stated again in the report

MU_SOURCES = {"ic035": (MU_IC_035, S_IC_035), "ic070": (MU_IC_070, S_IC_070)}
MU_SWEEP = (0.5, 1.0, 1.5, 2.0, 3.0)
S_SWEEP = S_IC_070

# rho_w must be >= rho_b for the equicorrelation factor model (VALID_CORRELATIONS
# below); (0, 0.2) is the one cell of the requested 3x2 grid that isn't one.
RHO_W_GRID = (0.0, 0.3, 0.6)
RHO_B_GRID = (0.0, 0.2)
VALID_CORRELATIONS = tuple((rw, rb) for rw in RHO_W_GRID for rb in RHO_B_GRID if rw >= rb)
SKIPPED_CORRELATIONS = tuple(
    (rw, rb) for rw in RHO_W_GRID for rb in RHO_B_GRID if (rw, rb) not in VALID_CORRELATIONS
)
HEADLINE_CORR = (0.3, 0.2)
HEADLINE_K = 1000

K_GRID = (20, 50, 100, 200, 500, 1000)
N_TRUE_GRID = (0, 1, 3, 6)
N_REPS = 5000
ALPHA = 0.05

PROCEDURES = (
    ("holm_5", "holm", 0.05),
    ("romano_wolf_5", "romano_wolf", 0.05),
    ("bh_5", "bh", 0.05),
    ("bh_10", "bh", 0.10),
    ("by_10", "by", 0.10),
)
# romano_shaikh_wolf_fdr (10%) is NOT in PROCEDURES: it is not implemented.
# See signal_lab.stats.multiple_testing.romano_shaikh_wolf_fdr's docstring.


def read_axis_groups(pending_dir: Path = PENDING_DIR):
    """
    `(hyp_ids, group_index, axis_order)`: `hyp_ids` and `group_index` are
    parallel arrays over the `m` hypotheses, sorted by hypothesis id; axis
    groups are ordered by descending size, ties broken alphabetically, which
    is also the order `spread_true` visits them in.
    """
    import yaml

    by_axis: dict[str, list[str]] = {}
    for path in sorted(pending_dir.glob("H-*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        by_axis.setdefault(str(doc["target_axis"]), []).append(str(doc["id"]))
    axis_order = sorted(by_axis, key=lambda a: (-len(by_axis[a]), a))
    hyp_ids: list[str] = []
    group_index: list[int] = []
    for g, axis in enumerate(axis_order):
        for hid in sorted(by_axis[axis]):
            hyp_ids.append(hid)
            group_index.append(g)
    order = sorted(range(len(hyp_ids)), key=lambda i: hyp_ids[i])
    hyp_ids = [hyp_ids[i] for i in order]
    group_index = [group_index[i] for i in order]
    import numpy as np

    return hyp_ids, np.asarray(group_index), axis_order, by_axis


def spread_true(n_true: int, group_index, axis_order):
    """
    A fixed (not re-drawn per replication) boolean mask of which `n_true`
    hypotheses are real, round-robin across axes in `axis_order` so the set
    covers as many axes as possible before doubling up on one.
    """
    import numpy as np

    m = len(group_index)
    mask = np.zeros(m, dtype=bool)
    by_group: dict[int, list[int]] = {}
    for i, g in enumerate(group_index):
        by_group.setdefault(int(g), []).append(i)
    n_groups = len(axis_order)
    picked = 0
    round_ = 0
    while picked < n_true:
        for g in range(n_groups):
            members = by_group.get(g, [])
            if round_ < len(members):
                mask[members[round_]] = True
                picked += 1
                if picked == n_true:
                    break
        round_ += 1
    return mask


def draw_batch(rng, n_reps, k, m, group_index, rho_w, rho_b, true_mask, mu, s):
    """
    `(t, T0)`: `t` is `(n_reps, m)`, the modelled observed statistic; `T0` is
    `(n_reps, k, m)`, `k` independent null draws per replication. Both share
    the equicorrelated (`rho_w`, `rho_b`) structure; `t`'s TRUE columns are
    additionally shifted to `N(mu, s^2)` -- a location-scale transform of the
    same underlying draw, which leaves Pearson correlation with every other
    column unchanged.
    """

    n_groups = int(group_index.max()) + 1
    within = rho_w - rho_b
    common_sd, group_sd, idio_sd = rho_b**0.5, within**0.5, (1.0 - rho_w) ** 0.5

    common_t = rng.standard_normal((n_reps, 1))
    group_t = rng.standard_normal((n_reps, n_groups))
    idio_t = rng.standard_normal((n_reps, m))
    z = common_sd * common_t + group_sd * group_t[:, group_index] + idio_sd * idio_t
    t = z.copy()
    t[:, true_mask] = mu + s * z[:, true_mask]

    common_0 = rng.standard_normal((n_reps, k, 1))
    group_0 = rng.standard_normal((n_reps, k, n_groups))
    idio_0 = rng.standard_normal((n_reps, k, m))
    T0 = common_sd * common_0 + group_sd * group_0[..., group_index] + idio_sd * idio_0
    return t, T0


def run_scenario(rng, n_reps, k, m, group_index, rho_w, rho_b, true_mask, mu, s):
    """One scenario's metrics for every procedure in `PROCEDURES`."""
    import numpy as np

    from signal_lab.stats._batched import (
        batched_benjamini_hochberg,
        batched_benjamini_yekutieli,
        batched_holm,
        batched_marginal_pvalues,
        batched_romano_wolf,
    )

    t, T0 = draw_batch(rng, n_reps, k, m, group_index, rho_w, rho_b, true_mask, mu, s)
    p = batched_marginal_pvalues(t, T0)
    n_true = int(true_mask.sum())
    false_mask = ~true_mask

    rows = []
    for name, kind, level in PROCEDURES:
        if kind == "holm":
            reject, _ = batched_holm(p, level)
        elif kind == "romano_wolf":
            reject, _ = batched_romano_wolf(t, T0, level)
        elif kind == "bh":
            reject, _ = batched_benjamini_hochberg(p, level)
        elif kind == "by":
            reject, _ = batched_benjamini_yekutieli(p, level)
        else:
            raise ValueError(kind)

        n_reject = reject.sum(axis=1)
        n_false_reject = reject[:, false_mask].sum(axis=1) if false_mask.any() else n_reject * 0
        n_true_reject = reject[:, true_mask].sum(axis=1) if n_true > 0 else n_reject * 0
        any_reject = n_reject > 0
        fdp = np.divide(
            n_false_reject, np.maximum(n_reject, 1), out=np.zeros(n_reps), where=any_reject
        )
        # pFDR (HANDOFF task 38): E[FDP | R > 0], undefined (NaN) if nothing ever rejects.
        pfdr = float(fdp[any_reject].mean()) if any_reject.any() else float("nan")
        mean_v, mean_s = float(n_false_reject.mean()), float(n_true_reject.mean())
        row = {
            "procedure": name,
            "level": level,
            "fwer": float((n_false_reject > 0).mean()),
            "fdr": float(fdp.mean()),
            "pfdr": pfdr,
            "p_any_pass": float(any_reject.mean()),
            "false_share_expected": mean_v / (mean_v + mean_s)
            if (mean_v + mean_s) > 0
            else float("nan"),
            "mean_false_passes": mean_v,
        }
        if n_true > 0:
            row["avg_power"] = float((n_true_reject / n_true).mean())
            row["p_at_least_one_true"] = float((n_true_reject > 0).mean())
        else:
            row["avg_power"] = float("nan")
            row["p_at_least_one_true"] = float("nan")
        rows.append(row)
    return rows


def _markdown_table(df) -> str:
    """A plain markdown table, so the report needs no optional dependency."""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        cells = [f"{v:.4g}" if isinstance(v, float) else str(v) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(argv=None) -> int:
    import numpy as np
    import pandas as pd

    started = time.time()
    hyp_ids, group_index, axis_order, by_axis = read_axis_groups()
    m = len(hyp_ids)
    sizes = {a: len(by_axis[a]) for a in axis_order}
    print(f"m={m} hypotheses, axes (size): {sizes}")
    if SKIPPED_CORRELATIONS:
        print(
            f"skipped correlations (rho_w < rho_b, not a valid equicorrelation): {SKIPPED_CORRELATIONS}"
        )

    records = []
    seed = 0

    def add(rho_w, rho_b, k, n_true, mu_label, mu, s, n_reps):
        nonlocal seed
        seed += 1
        rng = np.random.default_rng(seed)
        true_mask = spread_true(n_true, group_index, axis_order)
        for row in run_scenario(rng, n_reps, k, m, group_index, rho_w, rho_b, true_mask, mu, s):
            records.append(
                {
                    "rho_w": rho_w,
                    "rho_b": rho_b,
                    "k": k,
                    "n_true": n_true,
                    "mu_label": mu_label,
                    "mu": mu,
                    "s": s,
                    "n_reps": n_reps,
                    **row,
                }
            )

    # Main grid: every valid correlation x every k x every n_true; for n_true > 0,
    # both calibrated mu sources.
    for rho_w, rho_b in VALID_CORRELATIONS:
        for k in K_GRID:
            add(rho_w, rho_b, k, 0, "null", 0.0, 1.0, N_REPS)
            for n_true in (1, 3, 6):
                for mu_label, (mu, s) in MU_SOURCES.items():
                    add(rho_w, rho_b, k, n_true, mu_label, mu, s, N_REPS)

    # The mu sweep, for the power curve: headline correlation and k only.
    rho_w, rho_b = HEADLINE_CORR
    for n_true in (1, 3, 6):
        for mu in MU_SWEEP:
            add(rho_w, rho_b, HEADLINE_K, n_true, f"sweep_{mu:g}", mu, S_SWEEP, N_REPS)

    table = pd.DataFrame.from_records(records)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    out = OUT_ROOT / stamp
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "summary.csv", index=False)

    headline = table[
        (table["rho_w"] == HEADLINE_CORR[0])
        & (table["rho_b"] == HEADLINE_CORR[1])
        & (table["k"] == HEADLINE_K)
        & (table["n_true"] == 3)
        & (table["mu_label"].isin(["ic035", "ic070"]))
    ][
        [
            "mu_label",
            "procedure",
            "avg_power",
            "p_at_least_one_true",
            "fwer",
            "fdr",
            "pfdr",
            "mean_false_passes",
        ]
    ]

    # HANDOFF task 38: the k-sensitivity table, headline correlation, n_true=3,
    # Romano-Wolf 5% and BH 10% (RSW-FDR omitted -- not implemented).
    k_sens = table[
        (table["rho_w"] == HEADLINE_CORR[0])
        & (table["rho_b"] == HEADLINE_CORR[1])
        & (table["n_true"] == 3)
        & (table["mu_label"].isin(["ic035", "ic070"]))
        & (table["procedure"].isin(["romano_wolf_5", "bh_10"]))
    ][["mu_label", "k", "procedure", "avg_power", "fwer", "fdr", "pfdr"]].sort_values(
        ["mu_label", "procedure", "k"]
    )

    seconds = round(time.time() - started, 1)
    report = [
        "# FDR against FWER -- a statistics-level Monte Carlo (HANDOFF task 34)",
        "",
        f"m = {m}, axes (size): {sizes}. {N_REPS} replications per scenario, "
        f"{len(records) // len(PROCEDURES)} scenarios, {seconds:.0f}s.",
        "",
        f"Skipped correlations (not a valid equicorrelation, rho_w < rho_b): "
        f"{SKIPPED_CORRELATIONS or 'none'}.",
        "",
        "## Headline: n_true=3, rho_w=0.3, rho_b=0.2, k=1000",
        "",
        "### IC 0.35 (mu={:.3f}, s={:.3f} -- s ASSUMED, not measured at this IC)".format(
            *MU_SOURCES["ic035"]
        ),
        _markdown_table(headline[headline["mu_label"] == "ic035"].drop(columns="mu_label")),
        "",
        "### IC 0.70 (mu={:.3f}, s={:.3f}, both measured)".format(*MU_SOURCES["ic070"]),
        _markdown_table(headline[headline["mu_label"] == "ic070"].drop(columns="mu_label")),
        "",
        "## k-sensitivity (HANDOFF task 38): n_true=3, rho_w=0.3, rho_b=0.2, "
        "Romano-Wolf 5% and BH 10% (RSW-FDR omitted -- not implemented)",
        "",
        "### IC 0.35",
        _markdown_table(k_sens[k_sens["mu_label"] == "ic035"].drop(columns="mu_label")),
        "",
        "### IC 0.70",
        _markdown_table(k_sens[k_sens["mu_label"] == "ic070"].drop(columns="mu_label")),
        "",
        "## Caveats",
        "",
        "- This models the TEST, not the engine: statistics are assumed normal, "
        "with moments calibrated on planted signals (task 30 and the knee grid), "
        "not on any real hypothesis.",
        "- The registry has one hypothesis per SUBSTRATE section 6 family, so "
        "'family level first, then within' is trivial here; this study runs flat, "
        "one stepdown over all m at once.",
        "- IC 0.35's dispersion `s` is ASSUMED equal to IC 0.70's, not separately measured.",
        "- `romano_shaikh_wolf_fdr` is not implemented (see its docstring); the "
        "FDR side of this study is BH and BY only.",
        f"- The mu sweep ({MU_SWEEP}) runs only at the headline correlation and "
        f"k={HEADLINE_K}, not through the full grid -- it is the power curve, not "
        "a further grid axis.",
    ]
    (out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wrote {out}/summary.csv and report.md  ({seconds:.0f}s)")
    print(headline.to_string(index=False))
    print(k_sens.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
