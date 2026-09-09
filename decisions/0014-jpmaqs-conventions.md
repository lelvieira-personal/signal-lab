# 0014 — JPMaQS conventions, and a name collision worth renaming for

Status: decided, 2026-09-09. Changes `VintagePanel`.

## The collision

`VintagePanel` had two columns: `real_date`, the period the number describes,
and `knowledge_date`, when it could first have been known.

JPMaQS also has a column called `real_date`. It means **"the date of the
information state as observed by the markets"** — which is this lab's
`knowledge_date`. The two vocabularies use the same word for opposite ends of
the same pair.

A loader joining them would produce a panel that looks perfectly well-formed and
is off by the publication lag on every row — one to six weeks of lookahead,
uniformly, invisibly. No test would catch it: the shape is right, the dtypes are
right, `as_of` returns something plausible, and the `lookahead` veto would pass
because the knowledge dates it checks would be the ones the loader invented.

## Decision

Rename the field. `VintagePanel.real_date` becomes **`period_end`**, which is
unambiguous and is also exactly what JPMaQS lets you recover:

```
period_end     = jpmaqs.real_date - jpmaqs.eop_lag days
knowledge_date = jpmaqs.real_date
```

`knowledge_date` is unchanged. Done now, while the only producer is the
synthetic backend and the rename costs 37 lines; after phase 3 it would mean
touching a loaded snapshot.

## The other two conventions, recorded so phase 3 does not rediscover them

**Ticker form.** A JPMaQS ticker is `{cid}_{xcat}`: a three-character
cross-section id, an underscore, then the extended category.
`USD_INTRGDP_NSA_P1M1ML12_D1M1ML3` is cid `USD`, xcat
`INTRGDP_NSA_P1M1ML12_D1M1ML3`. The eleven registered hypotheses named these
with a `JPMAQS.` prefix, which is not the vendor's form; 27 tickers across 8
files were corrected.

**The download returns a cross product.** `download(cids=[...], xcats=[...])`
returns every combination, which is usually more than was asked for — three
tickers spanning two cids and two xcats download as four series. That is the
efficient shape, one call rather than three, but the result must be filtered
back to the requested tickers or the panel silently gains series no hypothesis
registered, and the coverage veto starts measuring against a universe nobody
chose. `split_tickers()` and `cross_product_size()` in
`src/signal_lab/loaders/jpmaqs.py` handle the split; the filter belongs with the
download in phase 3.

**Metrics.** Every ticker carries `value`, `grading` and `eop_lag`
(SUBSTRATE 5.6). The owner's working snippet requests `metrics=["value"]`; with
the value alone the grading filter cannot run and `period_end` cannot be
recovered, so the panel would be non-point-in-time while looking otherwise.
`required_metrics` in `params/data_sources.yaml` is enforced by the loader.

## Proxy

The production helper builds `http://{os.getlogin()}:{PROXY_PWD}@proxynew.itau:8080`
from `.env`. Recorded in `params/data_sources.yaml` under
`sources.jpmaqs.proxy`, **disabled by default**: that host resolves on the
corporate network and this lab runs on a personal machine, so the direct
connection is the right default and the proxy is one flag away.

## One thing for the owner to confirm

SUBSTRATE section 1 opens "This is a personal research lab." The JPMaQS
credentials were described as shared with the owner, and the proxy helper is
corporate infrastructure. Whether a vendor entitlement obtained through the
employer may be used in a personal lab is a licensing question, not a technical
one, and not one this file can settle. Worth confirming before the macro block
is pulled, because the answer is cheaper to act on before the data lands than
after.
