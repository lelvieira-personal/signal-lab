# 0061 — The implied-vol file: how `bbg_impvol_values_only.xlsx` is loaded, and the four hypotheses it serves

**Status:** decided 2026-10-16 by the owner ("i am ok with the decisions on
0061"), including rules 4 and 6 and the week ending 2020-01-03 being dropped
whole. Drafted by Cowork. Built by HANDOFF task 59. Follows
`decisions/0053` (USD base), `0054` and `0057` (labels and scope), `0059` (the
solver contract, with its 2026-10-16 addendum: the burn-in is 52 weeks).
No change to `params/`, `vetoes/` or `SUBSTRATE.md`.

## What the owner said (2026-10-15 and 2026-10-16)

- On moving the Janus Henderson / Alankar–Scholes tail-ratio idea into the
  lab: "Can we turn this into a hypothesis for this lab? Maybe we would need
  data we don't have mapped today, but the framework looks interesting."
- The signal is the 10-delta call/put premium ratio, with 25-delta as a
  variant: "1) yes". Europe: first "SX5E (local currency)", then "maybe better
  to go with EZU then?". Direction: "ok, let's go with 1" (the forecasting
  sign). Scope: "4) yes" (region cross-section, directional legs, a
  measurement; no asset-class cross-section).
- "52 weeks, lab wide" (the burn-in; `0059` addendum).
- "agreed with the proposed hypotheses" (H-2026-0018 to 0021).
- On this task: "yes, but check the handoff receipts from a previous task to
  see if there is anything else to address to in the next prompt".

The detail behind those choices is in the Project doc
`claude/impvol-coverage-2026-10-15.md` (mirror copy in
`Claude outputs/project-mirror/`).

## The file

`data/raw/bloomberg/bbg_impvol_values_only.xlsx`, pulled by the owner with
Claude in Excel on 2026-10-15, sha256 prefix `aeb90f8758e46fbd`. Its companion
`bbg_impvol_all.xlsx` holds the live BDH formulas and is **not** read.

Sheets: `IV_Weekly_v` (49 series, Bloomberg weekly, every date a Friday),
`IV_Daily_v` (31 series, daily), `Probe_Summary_v` (the coverage probe: one row
per candidate series, `series_id ... gap_months_2001_2019`; a record, not
data). Each series is a block of three columns: date, value, blank. Rows 1-4
of a block are `series_id`, security, field, overrides; data starts on row 5.

## The rules the loader follows (proposed)

1. **Identifiers.** A series is named `<security>|<point>`: the part of the
   workbook's `series_id` from `IV3M_` on (`SPX_IV3M_10DP` becomes
   `SPX Index|IV3M_10DP`; `XAUUSD_IV3M_25R` becomes
   `XAUUSD25R3M BGN Curncy|IV3M_25R`), and `SKEW` becomes `SKEW Index|PX_LAST`.
   The workbook's own ids look like JPMaQS tickers (three capitals, an
   underscore) and `loaders/jpmaqs.TICKER_RE` would classify them as JPMaQS;
   no lab id may match it. The workbook id is kept beside it.
2. **The holdout first.** Observations on or after `holdout_start` are dropped
   before anything else, as in every loader.
3. **Weekly, dated by Friday.** The weekly sheet is read as it is; a date that
   is not a Friday is refused. A daily series becomes weekly by taking the last
   observation in each Monday-to-Friday week, dated by that week's Friday; a
   week whose Friday falls on or after the holdout is dropped whole (so the
   week ending 2020-01-03 is dropped though it holds two 2019 days). Nothing
   is carried across weeks.
4. **Stale quotes are missing.** In a series' weekly values, a run of **6 or
   more** consecutive identical values keeps its first week and marks the
   rest missing. On this file the rule removes 385 weeks, all gold
   (`XAUUSD`): the risk reversals and butterflies sit unchanged for up to 56
   weeks between 2006-02 and 2008-03, and the ATM vol in runs before 2005. It
   removes nothing from any equity, bond or SKEW series. *The threshold is
   Cowork's choice, not a measurement; 6 weeks is longer than any run in the
   non-gold series (2 at most).*
5. **Values as delivered.** Implied vols stay in Bloomberg's units (percentage
   points); SKEW stays an index level. No conversion, no interpolation, no
   fill.
6. **Not in the snapshot yet.** The loaded panel is not joined to the
   snapshot the registry's `check_data` reads, so H-2026-0018 to 0021 stay
   `blocked:data` (`awaiting_loader` in their request files) until the
   `signals/` build says how a phase-3 signal reads it.

## The four hypotheses

Registered 2026-10-16 (`hypotheses/pending/`), each with a request file in
`data/requests/`:

| Id | Signal | Axis | Expression | Scope |
|---|---|---|---|---|
| H-2026-0018 | `implied_tail_ratio_10d_3m` | region | both | none (SPX, EZU, EWJ, EWA, EWC, EEM) |
| H-2026-0019 | `implied_tail_ratio_10d_3m_tlt` | duration | directional | `curve: [USD]` |
| H-2026-0020 | `implied_tail_ratio_10d_3m_hyg` | credit | directional | `rating: [HY]` |
| H-2026-0021 | `implied_downside_vs_realised_downside` | covariance (measurement) | both | none |

Two clerical corrections were made on 2026-10-16, before any commit and before
any result: H-2026-0021's family and target became `covariance` (the
validator's measurement vocabulary has no `volatility_stress` and no
`conviction` target for a risk-forecast test), and every `data_required` id
moved to the rule-1 form.

**Not registered, and why:** gold (SUBSTRATE §6 has no axis it could target);
investment grade (LQD's option skew is mostly rates, so it would repeat
H-2026-0019); a 25-delta variant (a separate registration if wanted); the
asset-class cross-section (no axis).

## What would reopen it

- The `signals/` build finds the panel needs a different shape: rule 6 is
  revisited there, not here.
- A re-pull of the file: the sha256 pin fails and the loader refuses it until
  a task updates the pin and the expectations.
