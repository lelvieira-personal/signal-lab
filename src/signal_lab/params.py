"""
Parameter access. Every threshold and cost in the lab lives in params/*.yaml
and nowhere else; this module is the only way code reads them.

Invariant: the params directory is hashed, and that hash plus the declared
params_version travel with every run in the results store, so any result can
be traced to the exact configuration that produced it.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PARAMS_DIR = REPO_ROOT / "params"

# The files that make up the configuration. A file added to params/ but not
# listed here is not read and not hashed, so the list is explicit.
PARAM_FILES = (
    "constraints.yaml",
    "costs.yaml",
    "vetoes.yaml",
    "data.yaml",
    "data_sources.yaml",
    "agents.yaml",
)


# Sentinel for "no default supplied"; None is a legitimate parameter value.
_REQUIRED = object()


class ParamsError(Exception):
    """Raised when the parameter set is missing, inconsistent or unset."""


class ParamNotConfigured(ParamsError):
    """
    Raised when a required parameter is null.

    SUBSTRATE forbids inventing thresholds. Where the constitution requires a
    ceiling but does not state a number, the parameter is null and the code
    that needs it refuses to run rather than substituting a guess.
    """


@dataclass(frozen=True)
class Params:
    """An immutable snapshot of params/, with its hash."""

    constraints: dict[str, Any]
    costs: dict[str, Any]
    vetoes: dict[str, Any]
    data: dict[str, Any]
    data_sources: dict[str, Any]
    agents: dict[str, Any]
    params_version: str
    params_hash: str
    params_dir: str

    def get(self, dotted: str, default: Any = _REQUIRED) -> Any:
        """
        Fetch by dotted path, e.g. params.get("vetoes.turnover.max_annualised").

        Raises ParamsError on an unknown path unless a default is supplied.
        A null value is returned as None; callers that must have a value use
        `require` instead.
        """
        node: Any = self.as_dict()
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                if default is _REQUIRED:
                    raise ParamsError(f"no such parameter: {dotted}")
                return default
            node = node[part]
        return node

    def as_dict(self) -> dict[str, Any]:
        """The whole configuration as one nested dict, keyed by file stem."""
        return {
            "constraints": self.constraints,
            "costs": self.costs,
            "vetoes": self.vetoes,
            "data": self.data,
            "data_sources": self.data_sources,
            "agents": self.agents,
        }

    def require(self, dotted: str) -> Any:
        """Fetch by dotted path and refuse a null value."""
        value = self.get(dotted)
        if value is None:
            raise ParamNotConfigured(
                f"{dotted} is null in params/. SUBSTRATE requires it and the lab does "
                f"not invent thresholds; set it in params/ and record the decision."
            )
        return value


def hash_params_dir(params_dir: Path | str = PARAMS_DIR) -> str:
    """
    sha256 over the params files, name and bytes, in a fixed order.

    Content-addressed rather than mtime-based so the same configuration hashes
    the same on any machine and after any checkout.
    """
    params_dir = Path(params_dir)
    digest = hashlib.sha256()
    for name in PARAM_FILES:
        path = params_dir / name
        if not path.exists():
            raise ParamsError(f"missing parameter file: {path}")
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_params(params_dir: Path | str = PARAMS_DIR) -> Params:
    """Read params/, check version agreement across files, and hash the set."""
    params_dir = Path(params_dir)
    loaded: dict[str, dict[str, Any]] = {}
    versions: dict[str, str] = {}
    for name in PARAM_FILES:
        path = params_dir / name
        if not path.exists():
            raise ParamsError(f"missing parameter file: {path}")
        with path.open("r", encoding="utf-8") as fh:
            doc = yaml.safe_load(fh) or {}
        if "params_version" not in doc:
            raise ParamsError(f"{name} has no params_version")
        key = name.removesuffix(".yaml")
        loaded[key] = doc
        versions[name] = str(doc["params_version"])

    distinct = set(versions.values())
    if len(distinct) != 1:
        raise ParamsError(
            "params_version disagrees across files, so no single version can be "
            f"recorded with a run: {versions}"
        )

    return Params(
        constraints=loaded["constraints"],
        costs=loaded["costs"],
        vetoes=loaded["vetoes"],
        data=loaded["data"],
        data_sources=loaded["data_sources"],
        agents=loaded["agents"],
        params_version=distinct.pop(),
        params_hash=hash_params_dir(params_dir),
        params_dir=str(params_dir),
    )


@lru_cache(maxsize=8)
def _cached(params_dir: str) -> Params:
    return load_params(params_dir)


def get_params(params_dir: Path | str | None = None) -> Params:
    """
    Process-wide params, cached.

    SIGNAL_LAB_PARAMS_DIR overrides the location, which is how tests point at a
    fixture directory without touching the real one.
    """
    if params_dir is None:
        params_dir = os.environ.get("SIGNAL_LAB_PARAMS_DIR", str(PARAMS_DIR))
    return _cached(str(params_dir))


def clear_cache() -> None:
    _cached.cache_clear()
