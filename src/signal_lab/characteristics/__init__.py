"""
The characteristic map's estimated half (decisions/0049, HANDOFF task 51).

`build` makes the Huber loadings on the six factors, week by week and walk-forward, with
their uncertainty and each instrument's out-of-sample explained share, and reads the measured
cells (`INDEX_OAD_TSY`, `INDEX_OAS_TSY`) beside them without merging. `store` writes them as a
versioned, hashed directory under `data/characteristics/` and refuses one that has changed.

Nothing here chooses the matrix's columns (OWNER-QUEUE L27), and nothing here is wired into
`resolve_exposures`, which still raises.
"""
