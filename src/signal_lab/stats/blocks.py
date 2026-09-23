"""
Block permutation of a panel along its date axis. SUBSTRATE section 9.

The primitive the block-shuffled baseline (decisions/0036 section 4a) is built
on, and the one the search null and the Romano-Wolf stepdown will need: destroy
the alignment between a series and the future while keeping its marginal
distribution, its persistence inside a block and -- because one permutation is
shared by every column -- its cross-section on each date.

Only the ORDER of the rows changes. Nothing here creates, fills or moves an
availability pattern; callers that hold a ragged panel re-apply their own mask.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Folded into the seed so the permutation stream is independent of any stream
# the caller seeds with the bare `seed` (decisions/0036 section 4b.3): drawing
# the permutation from the noise generator would advance it and unpair a
# baseline cell from its live twin.
BASELINE_STREAM = 0x5EED_B10C
# The score shuffle's streams (HANDOFF task 25): one per permutation `perm`,
# independent of the noise stream and of the truth shuffle's `baseline_rng`.
SCORE_STREAM = 0x5C0_5EED


def block_permutation(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    """
    Row order for `n` rows shuffled in contiguous blocks of `block` rows.

    Blocks keep their internal order; the blocks are permuted. A short final
    block is a block of its own, so the result is always a permutation of
    range(n).
    """
    if n < 0 or block < 1:
        raise ValueError("n must be non-negative and block at least 1")
    starts = np.arange(0, n, block)
    order = rng.permutation(len(starts))
    pieces = [np.arange(starts[i], min(starts[i] + block, n)) for i in order]
    return np.concatenate(pieces) if pieces else np.empty(0, dtype=int)


def block_shuffle_rows(panel: pd.DataFrame, block: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    `panel` with its rows permuted in blocks, one permutation for every column.

    The index and columns are those of the input: values move, dates do not, so
    no observation leaves the date range it was given.
    """
    order = block_permutation(len(panel), block, rng)
    return pd.DataFrame(panel.to_numpy()[order], index=panel.index, columns=panel.columns)


def baseline_rng(seed: int) -> np.random.Generator:
    """The permutation stream for `seed`, independent of `default_rng(seed)`."""
    return np.random.default_rng([int(seed), BASELINE_STREAM])


def score_shuffle_rng(seed: int, perm: int) -> np.random.Generator:
    """
    Permutation stream `perm` for `seed`, for the whole-score shuffle.

    A sibling rather than an argument to `baseline_rng`, so the truth shuffle's
    call and stream stay exactly what every baseline cell before it drew.
    """
    return np.random.default_rng([int(seed), SCORE_STREAM, int(perm)])
