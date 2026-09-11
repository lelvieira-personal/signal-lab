"""
The ruler audit. decisions/0023, phase 2.5.

What the weekly ETF layer can deliver at the section 4 budget, measured before
any hypothesis exists: effective breadth, a simulated-IC ladder through the real
solver, engine and cost model, the IC required to clear the bar, and how much
of that alpha the turnover constraint and the spread take.

Nothing here is a run. The planted signals are forward returns with noise --
an oracle dialled down to a chosen IC -- which is a lookahead by construction.
That is the point, and it is why this package writes to `results/audit/` and
never to the results store, never through `run_experiment()`, and never onto
the leaderboard.
"""

from signal_lab.audit.breadth import effective_breadth, independent_decisions_per_year
from signal_lab.audit.ladder import AuditCell, run_cell, run_grid
from signal_lab.audit.signals import PlantedSignal, plant_signal, realised_ic

__all__ = [
    "AuditCell",
    "PlantedSignal",
    "effective_breadth",
    "independent_decisions_per_year",
    "plant_signal",
    "realised_ic",
    "run_cell",
    "run_grid",
]
