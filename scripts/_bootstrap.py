"""
Put src/ and the repo root on sys.path.

The repository is a lab, not an installable package (pyproject sets
`[tool.uv] package = false`), so scripts bootstrap explicitly rather than
depending on an editable install that may or may not be present.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

for entry in (REPO_ROOT / "src", REPO_ROOT, REPO_ROOT / "render"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
