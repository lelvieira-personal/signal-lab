# 0006 — Grade-3 JPMaQS vintages: excluded or downweighted?

Status: proposed, 2026-09-07, agent. Blocking: not yet, JPMaQS is not loaded.

## Question

SUBSTRATE section 5.6: "Grade-3 vintages are downweighted or excluded per
`params/data.yaml`." The substrate delegates the choice to params and params
did not exist.

## What was done

`params/data.yaml` sets `jpmaqs.grade_3: exclude`, with an empty `downweights`
map alongside it.

## Why that way

Exclusion is the conservative option and needs no further number. Downweighting
requires a weight, and choosing one would be inventing a threshold, which
KICKOFF forbids. Exclusion also fails loudly: a signal that depends heavily on
grade-3 data will simply fail the coverage veto, which is visible, whereas a
downweight quietly changes the estimate.

## What to decide

Whether exclusion costs too much coverage in practice. That cannot be known
until the data is in, so this should be revisited with a coverage report in
phase 3, not before. If downweighting is preferred, the weight itself needs to
be a decision, not a default.

---
## Owner decision (2026-09-09, Leo)

Grade-3 exclusion stands for now; revisit in phase 3 against a real coverage
report. The owner has a JPMaQS API key and will test access.

### One correction, agreed in discussion

The owner proposed calling the API per hypothesis, to avoid a bulk pull hitting
a rate limit. That is not compatible with reproducibility: every run records a
`data_snapshot_hash` so a result can be regenerated, and data fetched live at
run time makes that hash a claim about something that may have changed. Two
runs of the same hypothesis could then see different data and be recorded as
comparable.

`params/data.yaml` therefore sets `jpmaqs.live_api_during_run: forbidden` and
`jpmaqs.incremental_snapshot_build: allowed`. If rate limits bite, the snapshot
is built across several sessions and then frozen. The API is called to *build*
a snapshot, never to *serve* a run.

Status: **open for phase 3** on the grading question; the snapshot rule is closed.


---
## Access configured (2026-09-09, Leo)

Credentials are in `.env` as `DQ_CLIENT_ID` / `DQ_CLIENT_SECRET`, reached
through the vendor SDK rather than raw HTTP:

```python
from macrosynergy.download import JPMaQSDownload
JPMaQSDownload(client_id=..., client_secret=..., proxy=get_proxies(prefix="PROXY"))
```

Recorded in `params/data_sources.yaml`. `macrosynergy` is a `jpmaqs` extra in
`pyproject.toml`, not a core dependency: phases 0-2 do not need it and it pulls
a large tree.

### One catch in the working snippet

The snippet requests `metrics=["value"]`. SUBSTRATE section 5.6 requires every
ticker to carry **`value`, `grading` and `eop_lag`**. Without `grading` the
grade-3 filter cannot run; without `eop_lag` a knowledge date cannot be
constructed, and a `VintagePanel` built from values alone would be
indistinguishable from a non-point-in-time panel — which is the entire reason
JPMaQS is worth paying for, and exactly what the `lookahead` veto exists to
catch.

`params/data_sources.yaml` therefore sets
`metrics: ["value", "grading", "eop_lag"]` and `required_metrics` to the same,
and the phase 3 loader refuses a pull missing any of them.

### The search gate stays closed

`params/data.yaml` moves `jpmaqs.status` from `pending` to
`credentials_supplied`. That is deliberately **not** `loaded`: SUBSTRATE section
5.6 opens the search only when the macro block is in the snapshot, and having a
key is not having the data. `scripts/nightly_cycle.py` still prints
`search gate: CLOSED`.
