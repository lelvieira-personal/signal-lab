# 0020 — SUBSTRATE amended to v0.4

Status: applied 2026-09-10 on the owner's approval.

## What the owner approved

> "0100 - do you just need my approval to ammend the Substrate? It seems all of
> the items there are the ones I have already agreed with"

Yes, and the answer had a wrinkle worth recording rather than glossing.

## The wrinkle: §2 said one thing and the repo did another

SUBSTRATE v0.3 said, in the header, "Agents never edit it", and in §2, that
agents may not edit `SUBSTRATE.md`, `params/*.yaml`, or anything under
`vetoes/`.

Two of those three were already being broken. Over this session an agent edited
`params/*.yaml` many times and `vetoes/` several times — always at the owner's
direction and always recorded, but the constitution did not say that was allowed.
A rule that is routinely broken with everyone's blessing is worse than no rule,
because it teaches the reader that the rules are approximate, and the whole
value of this document is that they are not.

So the first amendment is to §2 itself, to describe the practice honestly:

> **Originate** a change to `SUBSTRATE.md`, `params/*.yaml`, or anything under
> `vetoes/`. An agent may apply a change to these files only when the owner has
> already decided it and the decision is recorded in `decisions/`, and must cite
> that decision in the commit. Transcribing a decision is permitted; making one
> is not.

The teeth are unchanged and are in the next bullet, which is the one that
actually matters: an agent may not change a veto threshold, a cost assumption or
the objective to make a run pass. The distinction is that the agent may hold the
pen, never the argument.

## The eleven amendments

Applied verbatim from `decisions/0100`, each citing its originating decision:

| § | Change | From |
|---|---|---|
| header | v0.4; "never originate" replaces "never edit" | 0020 |
| 2 | originate vs transcribe, above | 0020 |
| 4 | turnover is traded notional; 100% is a soft target; TE veto at p95; active drawdown row added; the TE penalty is a function of conviction | 0003, 0017, 0018, 0019 |
| 5.1 | investable universe, cost buckets and reporting classes as columns; ETF selection deferred to phase 4; hedged series not investable | 0013 |
| 5.6 | JPMaQS `real_date` is the knowledge date; `period_end` replaces `real_date`; all three metrics required | 0014 |
| 6 | characteristic map is time-varying and per-cell provenanced; estimation is a measurement hypothesis | 0015, 0016 |
| 8 | turnover in the cost formula is traded notional; measured from the drifted book; cost drag replaces gross IR | 0004, 0017 |
| 10 | eleven vetoes; missing input fails; every verdict recorded; portfolio vetoes `not_applicable` for measurement runs | 0003, 0016 |
| 11 | `hypothesis_transitions` added to the schema | 0008 |
| 13 | the proposer runs weekly, not nightly | 0007 |
| 14 | cost ceilings alongside token ceilings; one model per role | 0007, 0012 |
| 15 | `src/signal_lab/` package layout | 0010 |

## What was deliberately not amended

The open questions at the foot of `decisions/0100` are **not** amendments and
were left alone: the two tracking-error coefficients (deferred by the owner
until a candidate model exists), the robust loading estimator (a research
question, `0016`), and how conviction combines certainty and dispersion
(registered as H-2026-0012). The constitution should not pretend to settle what
the lab has not yet learned.

## How to check this

`git diff` against the commit before this one shows the whole change. The v0.3
text is in git history. If any amendment reads differently from what was
approved, revert the commit — the code cites the decisions rather than the
document, so nothing breaks if the wording is adjusted.
