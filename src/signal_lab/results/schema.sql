-- Results store. SUBSTRATE.md section 11.
--
-- Append-only, enforced by triggers rather than by convention. SUBSTRATE
-- section 2 forbids deleting or rewriting rows; a lab whose history can be
-- edited cannot support a claim about what was tried, and the whole
-- multiplicity discipline in section 9 rests on knowing how many draws there
-- were. The triggers make an UPDATE or DELETE an error at the database, so a
-- stray script cannot quietly rewrite a leaderboard.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS runs (
    run_id             TEXT PRIMARY KEY,
    ts                 TEXT NOT NULL,
    hypothesis_id      TEXT,
    family             TEXT,
    aggregation        TEXT,
    params_version     TEXT NOT NULL,
    params_hash        TEXT NOT NULL,
    data_snapshot_hash TEXT NOT NULL,
    seed               INTEGER,
    status             TEXT NOT NULL,
    killed_by          TEXT,
    cost_tokens        INTEGER,
    cost_usd           REAL
);

CREATE TABLE IF NOT EXISTS metrics (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    name   TEXT NOT NULL,
    value  REAL,
    PRIMARY KEY (run_id, name)
);

CREATE TABLE IF NOT EXISTS verdicts (
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    veto   TEXT NOT NULL,
    passed INTEGER NOT NULL,
    detail TEXT,
    PRIMARY KEY (run_id, veto)
);

-- Hypothesis lifecycle. Not in section 11's listing, but the mover in
-- KICKOFF item 5 must record transitions somewhere durable, and this is the
-- durable store. See decisions/proposed/0008.
CREATE TABLE IF NOT EXISTS hypothesis_transitions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT NOT NULL,
    hypothesis_id TEXT NOT NULL,
    from_state    TEXT NOT NULL,
    to_state      TEXT NOT NULL,
    run_id        TEXT,
    detail        TEXT
);

CREATE INDEX IF NOT EXISTS idx_runs_hypothesis ON runs(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_runs_ts         ON runs(ts);
CREATE INDEX IF NOT EXISTS idx_metrics_name    ON metrics(name);
CREATE INDEX IF NOT EXISTS idx_trans_hyp       ON hypothesis_transitions(hypothesis_id);

-- Append-only enforcement.
CREATE TRIGGER IF NOT EXISTS runs_no_update BEFORE UPDATE ON runs
BEGIN SELECT RAISE(ABORT, 'runs is append-only (SUBSTRATE section 2)'); END;
CREATE TRIGGER IF NOT EXISTS runs_no_delete BEFORE DELETE ON runs
BEGIN SELECT RAISE(ABORT, 'runs is append-only (SUBSTRATE section 2)'); END;

CREATE TRIGGER IF NOT EXISTS metrics_no_update BEFORE UPDATE ON metrics
BEGIN SELECT RAISE(ABORT, 'metrics is append-only (SUBSTRATE section 2)'); END;
CREATE TRIGGER IF NOT EXISTS metrics_no_delete BEFORE DELETE ON metrics
BEGIN SELECT RAISE(ABORT, 'metrics is append-only (SUBSTRATE section 2)'); END;

CREATE TRIGGER IF NOT EXISTS verdicts_no_update BEFORE UPDATE ON verdicts
BEGIN SELECT RAISE(ABORT, 'verdicts is append-only (SUBSTRATE section 2)'); END;
CREATE TRIGGER IF NOT EXISTS verdicts_no_delete BEFORE DELETE ON verdicts
BEGIN SELECT RAISE(ABORT, 'verdicts is append-only (SUBSTRATE section 2)'); END;

CREATE TRIGGER IF NOT EXISTS transitions_no_update BEFORE UPDATE ON hypothesis_transitions
BEGIN SELECT RAISE(ABORT, 'hypothesis_transitions is append-only'); END;
CREATE TRIGGER IF NOT EXISTS transitions_no_delete BEFORE DELETE ON hypothesis_transitions
BEGIN SELECT RAISE(ABORT, 'hypothesis_transitions is append-only'); END;
