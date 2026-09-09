"""
JPMaQS / Macrosynergy backend. Phase 3 (SUBSTRATE sections 5.6 and 16).

The download is not implemented; everything around it is, because the parts
that are easy to get wrong are the conventions, not the HTTP call.

Three conventions, all of which will silently corrupt a panel if mishandled:

1.  A JPMaQS ticker is `{cid}_{xcat}` -- a three-character cross-section id, an
    underscore, then the extended category. `USD_INTRGDP_NSA_P1M1ML12_D1M1ML3`
    is cid `USD` and xcat `INTRGDP_NSA_P1M1ML12_D1M1ML3`. The download API takes
    cids and xcats as separate lists and returns their cross product, so a set
    of requested tickers has to be split, downloaded, and filtered back down.

2.  JPMaQS `real_date` is "the date of the information state as observed by the
    markets" -- the KNOWLEDGE date. This lab's VintagePanel calls the period the
    number describes `period_end`. The two vocabularies invert; see
    decisions/0014 and the note in loaders/base.py.

3.  Every ticker must carry `value`, `grading` and `eop_lag` (SUBSTRATE 5.6).
    Without `grading` the grade filter cannot run; without `eop_lag` the period
    cannot be recovered from the knowledge date, and the result is a panel that
    looks point-in-time and is not.

SUBSTRATE section 5.6 also makes this module the gate on the whole search:
until the macro block is in the snapshot, no signal search runs.
"""

from __future__ import annotations

import os
import re

from signal_lab.loaders.base import AnalyticsPanel, ReturnPanel, VintagePanel
from signal_lab.loaders.bloomberg import LoaderNotImplemented
from signal_lab.params import Params, get_params

# cid is exactly three characters, then the xcat. Anchored so a Bloomberg
# ticker (LUACTRUU, MXUS0EN) cannot match by accident.
TICKER_RE = re.compile(r"^(?P<cid>[A-Z]{3})_(?P<xcat>[A-Z0-9][A-Z0-9_]*)$")


class JPMaQSTickerError(ValueError):
    """A ticker that is not in {cid}_{xcat} form."""


def split_ticker(ticker: str) -> tuple[str, str]:
    """`USD_CPIH_SJA_P3M3ML3AR` -> `('USD', 'CPIH_SJA_P3M3ML3AR')`."""
    m = TICKER_RE.match(ticker)
    if not m:
        raise JPMaQSTickerError(
            f"{ticker!r} is not a JPMaQS ticker; expected a 3-character cid, an "
            f"underscore, then the xcat, e.g. USD_CPIH_SJA_P3M3ML3AR"
        )
    return m.group("cid"), m.group("xcat")


def is_jpmaqs_ticker(ticker: str) -> bool:
    return bool(TICKER_RE.match(ticker))


def split_tickers(tickers: list[str]) -> tuple[list[str], list[str]]:
    """
    Split a set of tickers into the cids and xcats to request.

    The API returns the cross product, which is usually larger than what was
    asked for -- four cids and three xcats is twelve series for a request that
    named five. That is the efficient shape (one call rather than five) but the
    caller must filter the result back down to the tickers actually requested,
    or the panel silently gains series no hypothesis registered. `filter_panel`
    below does that.
    """
    cids, xcats = set(), set()
    for t in tickers:
        cid, xcat = split_ticker(t)
        cids.add(cid)
        xcats.add(xcat)
    return sorted(cids), sorted(xcats)


def cross_product_size(tickers: list[str]) -> tuple[int, int]:
    """(requested, downloaded) counts, for the request file and the digest."""
    cids, xcats = split_tickers(tickers)
    return len(tickers), len(cids) * len(xcats)


class JPMaQSLoader:
    source = "jpmaqs"
    phase = 3

    def __init__(self, params: Params | None = None):
        self.params = params or get_params()

    # --- credentials -------------------------------------------------------

    def credentials(self) -> tuple[str, str]:
        keys = self.params.get("data_sources.sources.jpmaqs.env_keys", [])
        values = [os.environ.get(k) for k in keys]
        missing = [k for k, v in zip(keys, values, strict=True) if not v]
        if missing:
            raise RuntimeError(
                f"{missing} not set. Secrets come from environment variables only; "
                f"nothing key-shaped is committed."
            )
        return values[0], values[1]

    def proxies(self) -> dict[str, str] | None:
        """
        Corporate proxy, or None.

        The owner's production helper builds
        `http://{os.getlogin()}:{PROXY_PWD}@proxynew.itau:8080` from `.env`.
        That host resolves on the corporate network and not elsewhere, so the
        proxy is optional here and off by default: this lab runs on a personal
        machine. Set `proxy.enabled: true` in params/data_sources.yaml when
        running somewhere the host resolves.
        """
        cfg = self.params.get("data_sources.sources.jpmaqs.proxy", {}) or {}
        if not cfg.get("enabled", False):
            return None
        pwd = os.environ.get(cfg.get("password_env", "PROXY_PWD"))
        if not pwd:
            raise RuntimeError(f"{cfg.get('password_env')} not set but proxy.enabled is true")
        user = os.getlogin()
        url = f"http://{user}:{pwd}@{cfg['host']}:{cfg.get('port', 8080)}"
        return {"http": url, "https": url}

    def required_metrics(self) -> list[str]:
        return list(self.params.get("data_sources.sources.jpmaqs.required_metrics", []))

    # --- the interface -----------------------------------------------------

    def load_returns(self, snapshot_id: str) -> ReturnPanel:
        raise LoaderNotImplemented("JPMaQS is a macro source, not a return source")

    def load_analytics(self, snapshot_id: str) -> AnalyticsPanel:
        raise LoaderNotImplemented("JPMaQS is a macro source, not an analytics source")

    def load_macro(self, snapshot_id: str) -> VintagePanel:
        raise LoaderNotImplemented(
            "JPMaQS download lands in phase 3. When it does: split_tickers() to get "
            "cids/xcats, download with metrics=value,grading,eop_lag, map real_date -> "
            "knowledge_date and (real_date - eop_lag) -> period_end, then filter to the "
            "requested tickers."
        )


def search_is_open(params: Params | None = None) -> tuple[bool, str]:
    """
    Whether the signal search may run at all.

    SUBSTRATE section 5.6: the search opens only when the full signal set is in.
    A leaderboard built on price signals alone would tacitly decide what works
    before the macro block is tested, so this is a gate rather than a warning.
    Holding credentials is not holding data: only `status: loaded` opens it.
    """
    params = params or get_params()
    status = params.get("data.jpmaqs.status", "pending")
    gated = bool(params.get("data.jpmaqs.search_opens_only_when_loaded", True))
    if gated and status != "loaded":
        return False, (
            f"JPMaQS status is {status!r}. SUBSTRATE section 5.6: no signal search "
            f"runs until the macro block is in."
        )
    return True, "macro block present"
