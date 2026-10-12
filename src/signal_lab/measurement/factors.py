"""
The six weekly factors of decisions/0046 section 1, Friday to Friday.

    equity        ACWI total return minus cash       NDUEACWF - LD20TRUU
    real_yield    change in the 10y TIPS yield       GTII10
    inflation     change in the 10y breakeven        USGGBE10
    credit        change in US IG corporate OAS      LUACOAS
    dollar        log change in the dollar index     DXY
    commodities   commodity return minus cash        BCOMTR - LD20TRUU

Each is signed as its name reads: a positive value is equities up, a yield up, a
breakeven up, a spread wider, the dollar up, commodities up. They are not
orthogonalised (decisions/0046): the joint regression gives partial betas and an
ordering would decide the answer.

UNITS. The three yield-like factors are expressed in DECIMAL (a 10bp move is
0.001), so that every factor is a plain return-sized number and a bond's loading
on the real-yield factor is minus its duration in years -- which is what the
measured-against-estimated check of section 1 reads. GTII10 and USGGBE10 are
quoted in percent. LUACOAS is quoted in basis points by Bloomberg, but this
lab's own loader documents an OAS field arriving in percent, so its unit is not
taken on trust: a median level of 20 or more is basis points, below that is
percent, and the unit read is recorded in `FactorFrame.units` and printed in the
report.

Nothing on or after HOLDOUT_START is read: the panels come from loaders that cut
it, and the weekly frame is checked again on the way out.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from signal_lab.harness.engine import rebalance_dates
from signal_lab.loaders.base import AnalyticsPanel, ReturnPanel
from signal_lab.loaders.holdout import enforce_holdout
from signal_lab.params import Params, get_params
from signal_lab.portfolio.covariance import period_returns

FACTOR_NAMES = ("equity", "real_yield", "inflation", "credit", "dollar", "commodities")

EQUITY = "NDUEACWF"
CASH = "LD20TRUU"
COMMODITIES = "BCOMTR"
REAL_YIELD = ("YLD_YTM_MID", "GTII10")
BREAKEVEN = ("PX_LAST", "USGGBE10")
CREDIT = ("PX_LAST", "LUACOAS")
DOLLAR = ("PX_LAST", "DXY")


class FactorSeriesMissing(KeyError):
    """A series a factor is built from is not in the panel it should come from."""


@dataclass
class FactorFrame:
    frame: pd.DataFrame  # weeks x FACTOR_NAMES, indexed on the Friday that closes the week
    common_start: pd.Timestamp  # first week in which all six factors are observed
    n_weeks: int  # weeks in which all six are observed
    units: dict[str, str]
    dates: pd.DatetimeIndex  # the weekly calendar, including the opening Friday


def weekly_calendar(index: pd.DatetimeIndex, params: Params | None = None) -> pd.DatetimeIndex:
    params = params or get_params()
    return rebalance_dates(index, str(params.get("audit.rebalance_day", "FRI")), params)


def weekly_levels(series: pd.Series, dates: pd.DatetimeIndex) -> pd.Series:
    """The last observation in each `(previous Friday, this Friday]`, indexed on `dates`."""
    s = series.dropna()
    pos = dates.searchsorted(s.index, side="left")
    keep = pos < len(dates)
    out = s[keep].groupby(pos[keep]).last()
    return out.reindex(range(len(dates))).set_axis(dates)


def _need(frame: pd.DataFrame, column: str, where: str) -> pd.Series:
    if column not in frame.columns:
        raise FactorSeriesMissing(f"{column} is not in the {where}; the factor cannot be built")
    return frame[column]


def _field(analytics: AnalyticsPanel, field: str, ticker: str) -> pd.Series:
    if field not in analytics.fields:
        raise FactorSeriesMissing(f"analytics field {field} is absent; {ticker} cannot be read")
    return _need(analytics.fields[field], ticker, f"analytics field {field}")


def credit_scale(levels: pd.Series) -> tuple[float, str]:
    """Factor per vendor unit of the OAS series, and the unit it was read as."""
    median = float(levels.dropna().median())
    return (1e-4, "basis points") if median >= 20.0 else (1e-2, "percent")


def build_factors(
    returns: ReturnPanel,
    benchmark: ReturnPanel,
    analytics: AnalyticsPanel,
    params: Params | None = None,
    credit_series: pd.Series | None = None,
) -> FactorFrame:
    """
    The six factors. `credit_series` replaces the OAS series the credit factor is built from
    with another daily series quoted in percent (FRED's BAA10Y for store `huber6-v4`,
    decisions/0058); each observation is dated by its own date, like every other factor. Left at
    None, the credit factor is the change in `LUACOAS` exactly as before.
    """
    params = params or get_params()
    acwi = _need(benchmark.returns, EQUITY, "benchmark panel")
    cash = _need(returns.returns, CASH, "return panel")
    bcom = _need(returns.returns, COMMODITIES, "return panel")
    real = _field(analytics, *REAL_YIELD)
    breakeven = _field(analytics, *BREAKEVEN)
    oas = _field(analytics, *CREDIT) if credit_series is None else credit_series
    dxy = _field(analytics, *DOLLAR)

    daily = pd.concat({EQUITY: acwi, CASH: cash, COMMODITIES: bcom}, axis=1).sort_index()
    calendar_index = daily.index.union(analytics.fields[REAL_YIELD[0]].index)
    dates = weekly_calendar(calendar_index, params)

    weekly = period_returns(daily, dates)
    if credit_series is None:
        oas_scale, oas_unit = credit_scale(oas)
    else:
        oas_scale, oas_unit = 1e-2, "percent (FRED BAA10Y)"

    def change(series: pd.Series, scale: float) -> pd.Series:
        lv = weekly_levels(series, dates)
        return (lv.diff() * scale).iloc[1:]

    dollar_lv = weekly_levels(dxy, dates)
    frame = pd.DataFrame(
        {
            "equity": weekly[EQUITY] - weekly[CASH],
            "real_yield": change(real, 1e-2),
            "inflation": change(breakeven, 1e-2),
            "credit": change(oas, oas_scale),
            "dollar": np.log(dollar_lv / dollar_lv.shift(1)).iloc[1:],
            "commodities": weekly[COMMODITIES] - weekly[CASH],
        }
    )[list(FACTOR_NAMES)]
    frame.index.name = "date"
    enforce_holdout(frame, params, what="measurement factors")

    complete = frame.notna().all(axis=1)
    if not complete.any():
        raise ValueError("no week in which all six factors are observed")
    return FactorFrame(
        frame=frame,
        common_start=pd.Timestamp(complete[complete].index[0]),
        n_weeks=int(complete.sum()),
        units={
            "real_yield": "percent -> decimal",
            "inflation": "percent -> decimal",
            "credit": f"{oas_unit} -> decimal",
        },
        dates=dates,
    )
