# 0037 — JPMaQS may be pulled into this lab's environment

Recorded 2026-09-24 by Claude Code, transcribing the owner. Status: **decided**.

## The ruling

The owner, 2026-09-24: "jpmaqs can be pulled, this was confirmed."

OWNER-QUEUE L14 required this to be in `decisions/` before any vintage pull.
The confirmation came from the colleague whose JPMaQS access the lab uses. The
colleague's permission is to pull JPMaQS data into this personal environment.

## What it permits, and what it does not change

- **It permits** pulls of the tickers named in `data/requests/ticker_resolution.csv`
  under the tag `genuine phase-3 gap`, through `JPMaQSLoader` and the sources
  listed in `params/data_sources.yaml`.
- **Vendor data never leaves this machine** (CLAUDE.md, SUBSTRATE §1). JPMaQS
  pulls land under `data/raw/`, and the rules for that directory apply to them in
  full.
- **The holdout lock is unchanged.** Nothing on or after 2020-01-01 is read.
- **It does not settle which tickers to pull.** Three hypotheses still carry
  unresolved names; see L14 and the 2026-09-24 addendum to `decisions/0032`.

## Left for the owner to add, if wanted

This record does not have these details:
- the colleague's role;
- the date and form of the confirmation;
- any limit on scope or duration.

The owner may append them here.
