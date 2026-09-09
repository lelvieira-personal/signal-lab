"""
Snapshots: hashed, immutable panels the harness runs on.

SUBSTRATE section 11 requires every run to record a hash of the data snapshot it
ran on, so any result can be regenerated. A snapshot is therefore a directory of
parquet files plus a manifest, and its hash is over the file bytes, so two
snapshots with the same hash are the same data on any machine.

Snapshots are not committed (.gitignore). They are rebuildable from the loader
and the params that made them, both of which are recorded in the manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from signal_lab.loaders.base import ReturnPanel
from signal_lab.loaders.holdout import enforce_holdout
from signal_lab.params import Params, get_params

REPO_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOTS_DIR = REPO_ROOT / "data" / "snapshots"


def snapshots_root(override: Path | str | None = None) -> Path:
    """
    Where snapshots live, resolved at call time.

    Deliberately not a default argument: a module-level constant baked into a
    signature at import time cannot be redirected, which makes the scripts
    untestable against a temporary directory and makes relocating the store a
    code change rather than a configuration one.
    """
    if override is not None:
        return Path(override)
    return Path(os.environ.get("SIGNAL_LAB_SNAPSHOTS_DIR", SNAPSHOTS_DIR))


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    path: Path
    data_snapshot_hash: str
    manifest: dict[str, Any]

    @property
    def series_ids(self) -> list[str]:
        return list(self.manifest.get("series_ids", []))

    @property
    def macro_ids(self) -> list[str]:
        return list(self.manifest.get("macro_ids", []))

    def available_ids(self) -> set[str]:
        """
        Everything a hypothesis's `data_required` can be satisfied by.

        A hypothesis naming anything outside this set is blocked:data and gets a
        request file, rather than being run on whatever happens to be nearby.
        """
        return set(self.series_ids) | set(self.macro_ids)


def hash_directory(path: Path) -> str:
    """sha256 over every file's relative name and bytes, in sorted order."""
    digest = hashlib.sha256()
    for file in sorted(
        p for p in Path(path).rglob("*") if p.is_file() and p.name != "manifest.yaml"
    ):
        digest.update(str(file.relative_to(path)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_snapshot(
    snapshot_id: str,
    source: str = "synthetic",
    params: Params | None = None,
    snapshots_dir: Path | str | None = None,
    seed: int | None = None,
    overwrite: bool = False,
) -> Snapshot:
    """
    Freeze a panel and hash it.

    The holdout is enforced on the way in as well as inside the loader: a
    snapshot is the thing every later run reads, so a leak here would be a leak
    everywhere, and the check is cheap.
    """
    from signal_lab.loaders import get_loader

    params = params or get_params()
    out = snapshots_root(snapshots_dir) / snapshot_id
    if out.exists() and not overwrite:
        raise FileExistsError(
            f"{out} exists. A snapshot is immutable; build a new id rather than "
            f"overwriting one that runs may already reference."
        )
    out.mkdir(parents=True, exist_ok=True)

    loader = get_loader(source, params=params, **({"seed": seed} if seed is not None else {}))
    returns: ReturnPanel = loader.load_returns(snapshot_id)
    enforce_holdout(returns.returns, params, what=f"snapshot {snapshot_id} returns")

    returns.levels.to_parquet(out / "levels.parquet")
    returns.returns.to_parquet(out / "returns.parquet")
    returns.meta_frame().to_parquet(out / "meta.parquet")

    macro_ids: list[str] = []
    try:
        macro = loader.load_macro(snapshot_id)
        enforce_holdout(macro.frame["knowledge_date"], params, what=f"snapshot {snapshot_id} macro")
        macro.frame.to_parquet(out / "macro.parquet", index=False)
        macro_ids = sorted(macro.frame["series_id"].unique().tolist())
    except NotImplementedError:
        pass

    analytics_fields: list[str] = []
    try:
        analytics = loader.load_analytics(snapshot_id)
        for name, frame in analytics.fields.items():
            frame.to_parquet(out / f"analytics_{name}.parquet")
        analytics_fields = analytics.field_names
    except NotImplementedError:
        pass

    data_hash = hash_directory(out)
    manifest = {
        "snapshot_id": snapshot_id,
        "source": source,
        "data_snapshot_hash": data_hash,
        "params_version": params.params_version,
        "params_hash": params.params_hash,
        "seed": seed if seed is not None else params.get("data.synthetic.seed"),
        "dev_start": str(params.require("data.windows.dev_start")),
        "dev_end": str(params.require("data.windows.dev_end")),
        "holdout_start": str(params.require("data.windows.holdout_start")),
        "first_date": str(returns.returns.index.min().date()),
        "last_date": str(returns.returns.index.max().date()),
        "n_series": len(returns.series_ids),
        "series_ids": sorted(returns.series_ids),
        "macro_ids": macro_ids,
        "analytics_fields": analytics_fields,
        "tiers": {
            tier: len(returns.by_tier(tier)) for tier in ("backbone", "second", "tradable-only")
        },
        "hedged_ids": sorted(returns.hedged_ids()),
        "splices": [s.as_row() for s in returns.splices],
    }
    (out / "manifest.yaml").write_text(
        yaml.safe_dump(json.loads(json.dumps(manifest, default=str)), sort_keys=False),
        encoding="utf-8",
    )
    return Snapshot(snapshot_id, out, data_hash, manifest)


def load_snapshot(snapshot_id: str, snapshots_dir: Path | str | None = None) -> Snapshot:
    path = snapshots_root(snapshots_dir) / snapshot_id
    manifest_path = path / "manifest.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"no snapshot at {path}; build it with scripts/build_snapshot.py")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    return Snapshot(snapshot_id, path, str(manifest["data_snapshot_hash"]), manifest)


def verify_snapshot(snapshot: Snapshot) -> tuple[bool, str]:
    """Re-hash a snapshot on disk and compare it to its manifest."""
    actual = hash_directory(snapshot.path)
    if actual == snapshot.data_snapshot_hash:
        return True, f"hash matches ({actual[:12]})"
    return False, (
        f"snapshot {snapshot.snapshot_id} has changed on disk: manifest says "
        f"{snapshot.data_snapshot_hash[:12]}, files hash to {actual[:12]}"
    )


def read_returns(snapshot: Snapshot) -> pd.DataFrame:
    return pd.read_parquet(snapshot.path / "returns.parquet")
