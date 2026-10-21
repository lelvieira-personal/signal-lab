"""
A one-off report: which `data_required` names in the registry the resolver rejects.

decisions/0034 asks for this pass once the rule exists. It reads
`hypotheses/pending/` and `hypotheses/done/`, prints each file with its rejected
entries and then the totals. It writes nothing, edits no hypothesis and exits 0:
what to do about a rejected name is the owner's call.
"""

from __future__ import annotations

import sys
from pathlib import Path

import _bootstrap  # noqa: F401
import yaml

from signal_lab.harness.hypotheses import HYPOTHESES_DIR, unresolved_names

STATES = ("pending", "done")


def main(root: Path = HYPOTHESES_DIR) -> int:
    files = entries = rejected_entries = rejected_files = 0
    for state in STATES:
        for path in sorted((root / state).glob("*.yaml")):
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            names = [s for s in (doc.get("data_required") or []) if isinstance(s, str)]
            bad = unresolved_names(names)
            files += 1
            entries += len(names)
            rejected_entries += len(bad)
            rejected_files += bool(bad)
            for name in bad:
                print(f"{state}/{path.name}: {name}")
    print(
        f"{files} files, {entries} entries; "
        f"{rejected_entries} entries rejected in {rejected_files} files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
