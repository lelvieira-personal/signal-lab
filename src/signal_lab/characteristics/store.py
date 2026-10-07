"""
A characteristics store: `data/characteristics/<id>/`, immutable and hashed (HANDOFF task 51).

The data files hold vendor-derived values and are git-ignored; `manifest.yaml` holds counts,
dates and hashes and is committed. The directory hash is the snapshot module's
`hash_directory`, so the same rule that protects a snapshot protects this. A loader re-hashes
on every read and refuses a store whose files have changed since the manifest was written.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from signal_lab.harness.snapshot import hash_directory

REPO_ROOT = Path(__file__).resolve().parents[3]
STORE_ROOT = REPO_ROOT / "data" / "characteristics"
DATA_FILES = ("loadings", "fit", "measured", "instruments")


class StoreChanged(RuntimeError):
    """The store's files do not hash to what its manifest recorded."""


@dataclass
class Store:
    store_id: str
    path: Path
    manifest: dict[str, Any]
    frames: dict[str, pd.DataFrame]


def write_store(
    store_id: str,
    frames: dict[str, pd.DataFrame],
    manifest: dict[str, Any],
    root: Path | str = STORE_ROOT,
) -> Path:
    out = Path(root) / store_id
    if out.exists():
        raise FileExistsError(
            f"{out} exists. A store is immutable; build a new id rather than overwriting one "
            f"that a run may already reference."
        )
    missing = [n for n in DATA_FILES if n not in frames]
    if missing:
        raise ValueError(f"a store holds {list(DATA_FILES)}; missing {missing}")
    out.mkdir(parents=True)
    counts = {}
    for name in DATA_FILES:
        frames[name].to_parquet(out / f"{name}.parquet", index=False)
        counts[name] = int(len(frames[name]))
    doc = {
        "store_id": store_id,
        **manifest,
        "row_counts": counts,
        "directory_hash": hash_directory(out),
    }
    (out / "manifest.yaml").write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return out


def load_store(store_id: str, root: Path | str = STORE_ROOT) -> Store:
    path = Path(root) / store_id
    manifest_path = path / "manifest.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"no store {store_id!r} under {Path(root)}")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    now = hash_directory(path)
    if now != manifest["directory_hash"]:
        raise StoreChanged(
            f"store {store_id} has changed since it was written: "
            f"{now[:16]} against the manifest's {str(manifest['directory_hash'])[:16]}. "
            f"A store is immutable; build a new id."
        )
    frames = {name: pd.read_parquet(path / f"{name}.parquet") for name in DATA_FILES}
    return Store(store_id, path, manifest, frames)
