"""
The hypothesis registry: parse, validate, move, request.

SUBSTRATE section 7 makes pre-registration binding. This module is what makes it
mechanical rather than aspirational:

  * a hypothesis with no direction or no rationale is rejected before it runs;
  * `literature` provenance with an unresolvable reference is rejected, and a
    fabricated citation is logged as a failure of the proposer;
  * a hypothesis needing series the snapshot does not have is `blocked:data`
    and writes a request file, rather than quietly substituting a proxy;
  * a declared proxy is tagged, and proxy runs are excluded from the main
    leaderboard.

The states are directories: hypotheses/pending, running, done. Moving between
them writes a transition to the results store, so the lifecycle is auditable
even after the files have moved.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from signal_lab.params import Params, get_params
from signal_lab.results.store import ResultsStore

REPO_ROOT = Path(__file__).resolve().parents[3]
HYPOTHESES_DIR = REPO_ROOT / "hypotheses"
REQUESTS_DIR = REPO_ROOT / "data" / "requests"

STATES = ("pending", "running", "done")

# SUBSTRATE section 6.
FAMILIES = (
    "growth",
    "inflation",
    "policy_rates",
    "credit_conditions",
    "liquidity",
    "terms_of_trade",
    "spreads_curve",
    "volatility_stress",
    "trend",
    "carry",
    "valuation",
)

DIRECTIONS = ("positive", "negative")

# decisions/0016. A signal hypothesis is judged on net IR against the 50/50; a
# measurement hypothesis is about the exposure matrix itself and is judged on
# out-of-sample loading fidelity. Choosing an estimator on the strategy's own
# objective would select the mapping on the outcome, so the two are ranked on
# separate leaderboards with multiplicity controlled separately within each.
KINDS = ("signal", "measurement")

# Vetoes that describe a portfolio. A measurement run does not produce one, so
# these are recorded as not_applicable rather than passed -- a measurement run
# must never be mistakable for a portfolio run that passed everything.
PORTFOLIO_VETOES = ("turnover", "cash", "positions", "tracking_error", "active_drawdown")
PROVENANCE = ("literature", "adaptation", "novel")
EXPRESSIONS = ("cross_sectional", "directional", "both")
TARGET_AXES = ("duration", "credit", "region", "sector", "style", "real_nominal", "cash")

# decisions/0016 says a measurement hypothesis uses the same template with the
# fields reinterpreted. That only works if the vocabularies are actually
# different: a hypothesis about how conviction is measured has no `family` in
# SUBSTRATE section 6's sense and no exposure axis it targets. Validating it
# against the signal vocabulary would force a proposer to file it under
# something false.
MEASUREMENT_FAMILIES = (
    "exposure_estimation",  # the characteristic map's loadings (decisions/0015)
    "conviction",  # how conviction is measured and combined (decisions/0019)
    "covariance",  # the risk model
    "aggregation",  # how family scores are combined into one view
)
MEASUREMENT_TARGETS = (
    "loadings",
    "conviction",
    "covariance",
    "aggregation_weights",
    *TARGET_AXES,  # a loadings hypothesis may target one exposure axis
)

REQUIRED_FIELDS = (
    "id",
    "family",
    "signal",
    "direction",
    "target_axis",
    "rationale",
    "horizon_weeks",
    "expected_expression",
    "proposed_by",
    "provenance",
    "data_required",
)

ID_PATTERN = re.compile(r"^H-\d{4}-\d{4}$")
HORIZON_PATTERN = re.compile(r"^\d+(-\d+)?$")


class HypothesisRejected(Exception):
    """The harness refuses to run this hypothesis. The reason is the message."""


@dataclass
class Hypothesis:
    """A parsed, validated pre-registration."""

    id: str
    family: str
    signal: str
    direction: str
    target_axis: str
    rationale: str
    horizon_weeks: str
    expected_expression: str
    proposed_by: str
    provenance: str
    data_required: list[str]
    kind: str = "signal"
    reference: str | None = None
    proxy_for: dict[str, str] | None = None
    notes: str = ""
    path: Path | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_measurement(self) -> bool:
        """True when this hypothesis is about the exposure matrix, not a signal."""
        return self.kind == "measurement"

    @property
    def objective(self) -> str:
        """The pre-registered metric this hypothesis is ranked on."""
        return "loading_fidelity" if self.is_measurement else "net_ir"

    def applicable_vetoes(self, all_vetoes: tuple[str, ...] | list[str]) -> list[str]:
        """The vetoes that can be evaluated for this kind of run."""
        if not self.is_measurement:
            return list(all_vetoes)
        return [v for v in all_vetoes if v not in PORTFOLIO_VETOES]

    @property
    def is_proxy(self) -> bool:
        """Proxy runs are tagged and excluded from the main leaderboard."""
        return bool(self.proxy_for)

    def horizon_range(self) -> tuple[int, int]:
        parts = str(self.horizon_weeks).split("-")
        lo = int(parts[0])
        hi = int(parts[-1])
        return lo, hi

    def as_dict(self) -> dict[str, Any]:
        out = {
            "id": self.id,
            "kind": self.kind,
            "family": self.family,
            "signal": self.signal,
            "direction": self.direction,
            "target_axis": self.target_axis,
            "rationale": self.rationale,
            "horizon_weeks": self.horizon_weeks,
            "expected_expression": self.expected_expression,
            "proposed_by": self.proposed_by,
            "provenance": self.provenance,
            "data_required": list(self.data_required),
        }
        if self.reference:
            out["reference"] = self.reference
        if self.proxy_for:
            out["proxy_for"] = self.proxy_for
        return out


# --- reference resolution ----------------------------------------------------


class NullReferenceResolver:
    """
    The default resolver: resolves nothing.

    SUBSTRATE section 7 requires the harness to fetch a `literature` reference
    and reject the hypothesis if it cannot be resolved. No resolver host is
    allowlisted in params/data_sources.yaml yet, and SUBSTRATE section 2 forbids
    calling an API that is not listed. So `literature` provenance is rejected
    until the owner enables a resolver. Rejecting is the safe direction: the
    alternative is accepting citations nobody checked, and a fabricated citation
    is precisely what section 7 calls a failure of the proposer.
    """

    enabled = False

    def resolve(self, reference: str) -> tuple[bool, str]:
        return False, (
            "no reference resolver is enabled (params/data_sources.yaml: "
            "reference_resolver.enabled is false), so a literature citation "
            "cannot be verified and is not accepted on trust"
        )


def get_resolver(params: Params | None = None):
    params = params or get_params()
    if not params.get("data_sources.reference_resolver.enabled", False):
        return NullReferenceResolver()
    raise NotImplementedError(
        "an HTTP reference resolver lands with phase 3; enable it in "
        "params/data_sources.yaml with an explicit allowed_hosts list"
    )


# --- parse and validate ------------------------------------------------------


def parse_hypothesis(path: Path | str, params: Params | None = None) -> Hypothesis:
    """Read one YAML file and validate it. Raises HypothesisRejected."""
    path = Path(path)
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise HypothesisRejected(f"{path.name}: not valid YAML: {exc}") from exc
    if not isinstance(doc, dict):
        raise HypothesisRejected(f"{path.name}: top level must be a mapping")
    return validate_hypothesis(doc, params=params, path=path)


def validate_hypothesis(
    doc: dict[str, Any], params: Params | None = None, path: Path | None = None
) -> Hypothesis:
    params = params or get_params()
    where = path.name if path else doc.get("id", "<unnamed>")

    kind = str(doc.get("kind", "signal"))

    # A measurement hypothesis may legitimately require no vendor series: its
    # inputs are the harness's own outputs -- a regime model's state
    # probabilities, an estimated loading, a covariance matrix. The field must
    # still be PRESENT, so that "needs nothing from a vendor" is an explicit
    # claim rather than an omission, but it may be empty.
    empty_ok = {"data_required"} if kind == "measurement" else set()
    missing = [
        f
        for f in REQUIRED_FIELDS
        if f not in doc or (doc[f] in (None, "") or (doc[f] == [] and f not in empty_ok))
    ]
    if missing:
        raise HypothesisRejected(f"{where}: missing required field(s) {missing}")

    hid = str(doc["id"])
    if not ID_PATTERN.match(hid):
        raise HypothesisRejected(f"{where}: id {hid!r} must look like H-2026-0001")

    if kind not in KINDS:
        raise HypothesisRejected(f"{where}: kind {kind!r} is not one of {list(KINDS)}")

    families = MEASUREMENT_FAMILIES if kind == "measurement" else FAMILIES
    family = str(doc["family"])
    if family not in families:
        raise HypothesisRejected(
            f"{where}: family {family!r} is not one of {list(families)} for a {kind} hypothesis"
        )

    direction = str(doc["direction"]).strip().lower()
    if direction not in DIRECTIONS:
        raise HypothesisRejected(
            f"{where}: direction must be one of {list(DIRECTIONS)}, got {direction!r}. "
            f"A hypothesis without a stated direction cannot fail the direction veto, "
            f"which is the point of stating it."
        )

    targets = MEASUREMENT_TARGETS if kind == "measurement" else TARGET_AXES
    axis = str(doc["target_axis"])
    if axis not in targets:
        raise HypothesisRejected(
            f"{where}: target_axis {axis!r} is not one of {list(targets)} for a {kind} hypothesis"
        )

    rationale = str(doc["rationale"]).strip()
    if len(rationale) < 120:
        raise HypothesisRejected(
            f"{where}: rationale is {len(rationale)} characters. SUBSTRATE section 7 asks "
            f"for a paragraph of economics: why this predicts that, at this horizon, in a "
            f"way that survives the long-only constraint."
        )

    horizon = str(doc["horizon_weeks"]).strip()
    if not HORIZON_PATTERN.match(horizon):
        raise HypothesisRejected(f"{where}: horizon_weeks {horizon!r} must be N or N-M weeks")
    lo, hi = int(horizon.split("-")[0]), int(horizon.split("-")[-1])
    if lo < 1 or hi < lo:
        raise HypothesisRejected(f"{where}: horizon_weeks {horizon!r} is not a sane range")

    expression = str(doc["expected_expression"])
    if expression not in EXPRESSIONS:
        raise HypothesisRejected(
            f"{where}: expected_expression {expression!r} is not one of {list(EXPRESSIONS)}"
        )

    provenance = str(doc["provenance"])
    if provenance not in PROVENANCE:
        raise HypothesisRejected(
            f"{where}: provenance {provenance!r} is not one of {list(PROVENANCE)}"
        )

    reference = doc.get("reference")
    if provenance == "literature":
        if not reference:
            raise HypothesisRejected(f"{where}: provenance is literature but no reference is given")
        resolved, detail = get_resolver(params).resolve(str(reference))
        if not resolved:
            raise HypothesisRejected(f"{where}: reference {reference!r} did not resolve: {detail}")

    data_required = doc["data_required"]
    if not isinstance(data_required, list) or not all(isinstance(s, str) for s in data_required):
        raise HypothesisRejected(f"{where}: data_required must be a list of series ids")

    proxy_for = doc.get("proxy_for")
    if proxy_for is not None and not isinstance(proxy_for, dict):
        raise HypothesisRejected(
            f"{where}: proxy_for must be a mapping of proxy series id -> the series it stands in for"
        )

    return Hypothesis(
        id=hid,
        kind=kind,
        family=family,
        signal=str(doc["signal"]),
        direction=direction,
        target_axis=axis,
        rationale=rationale,
        horizon_weeks=horizon,
        expected_expression=expression,
        proposed_by=str(doc["proposed_by"]),
        provenance=provenance,
        data_required=list(data_required),
        reference=str(reference) if reference else None,
        proxy_for=dict(proxy_for) if proxy_for else None,
        notes=str(doc.get("notes", "")),
        path=path,
        raw=doc,
    )


# --- data availability -------------------------------------------------------


@dataclass
class DataCheck:
    """Which required series the snapshot has, and which it does not."""

    available: list[str]
    missing: list[str]

    @property
    def blocked(self) -> bool:
        return bool(self.missing)

    @property
    def status(self) -> str:
        return "blocked:data" if self.blocked else "ready"


def check_data(hyp: Hypothesis, snapshot_manifest: list[str] | set[str]) -> DataCheck:
    manifest = set(snapshot_manifest)
    available = [s for s in hyp.data_required if s in manifest]
    missing = [s for s in hyp.data_required if s not in manifest]
    return DataCheck(available=available, missing=missing)


def write_data_request(
    hyp: Hypothesis, check: DataCheck, requests_dir: Path | str = REQUESTS_DIR
) -> Path:
    """
    Write data/requests/<hypothesis_id>.yaml with source, series, fields, reason.

    SUBSTRATE section 7. The request is the sanctioned response to missing data;
    silent substitution fails the coverage veto and, more to the point, produces
    a result about a different signal than the one registered.
    """
    requests_dir = Path(requests_dir)
    requests_dir.mkdir(parents=True, exist_ok=True)
    path = requests_dir / f"{hyp.id}.yaml"
    doc = {
        "hypothesis_id": hyp.id,
        "signal": hyp.signal,
        "family": hyp.family,
        "requested_by": hyp.proposed_by,
        "status": "awaiting_owner",
        "series": [
            {
                "id": sid,
                "source": _guess_source(sid),
                "fields": _guess_fields(sid),
            }
            for sid in check.missing
        ],
        "reason": (
            f"{hyp.id} requires {len(check.missing)} series absent from the snapshot. "
            f"The hypothesis is blocked:data rather than run on a substitute."
        ),
        "available_already": check.available,
    }
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def _guess_source(series_id: str) -> str:
    """
    A hint for the owner, not a decision.

    The prefix conventions are the vendors' own, so this is a lookup rather than
    an inference: anything unrecognised is reported as unknown rather than
    assigned to a vendor that may not carry it.
    """
    from signal_lab.loaders.jpmaqs import is_jpmaqs_ticker

    if is_jpmaqs_ticker(series_id):
        return "jpmaqs"
    sid = series_id.upper()
    if sid.startswith(
        (
            "DGS",
            "DFII",
            "T10",
            "T5",
            "VIXCLS",
            "NFCI",
            "ANFCI",
            "STLFSI",
            "DTWEX",
            "DFF",
            "DCOIL",
            "DRTSCILM",
        )
    ):
        return "fred"
    if sid.startswith(
        (
            "LT",
            "LU",
            "LF",
            "LEGA",
            "LP0",
            "LD",
            "LB",
            "LG",
            "MX",
            "ND",
            "M1",
            "M2",
            "M0",
            "I0",
            "I1",
            "I2",
            "H0",
            "H1",
            "BTSY",
            "SPBD",
            "G3O",
            "SBWG",
            "EMUS",
            "BCOM",
            "SPX",
            "TAMSCI",
            "ENXG",
            "FGCI",
            "SPGNR",
            "LET",
            "NDU",
        )
    ):
        return "bloomberg"
    return "unknown"


def _guess_fields(series_id: str) -> list[str]:
    sid = series_id.upper()
    if any(tag in sid for tag in ("OAS", "SPREAD")):
        return ["INDEX_OAS_TSY"]
    if "OAD" in sid or "DURATION" in sid:
        return ["INDEX_OAD_TSY"]
    if "YTW" in sid or "YIELD" in sid:
        return ["INDEX_YIELD_TO_WORST"]
    if _guess_source(series_id) == "bloomberg":
        return ["TOT_RETURN_INDEX_GROSS_DVDS"]
    return ["value"]


# --- the registry ------------------------------------------------------------


class HypothesisRegistry:
    """Directory-backed lifecycle with transitions recorded in the store."""

    def __init__(
        self,
        root: Path | str = HYPOTHESES_DIR,
        store: ResultsStore | None = None,
        params: Params | None = None,
        requests_dir: Path | str = REQUESTS_DIR,
    ):
        self.root = Path(root)
        self.store = store
        self.params = params or get_params()
        self.requests_dir = Path(requests_dir)
        for state in STATES:
            (self.root / state).mkdir(parents=True, exist_ok=True)

    def paths(self, state: str) -> list[Path]:
        if state not in STATES:
            raise ValueError(f"unknown state {state!r}; expected one of {list(STATES)}")
        return sorted(p for p in (self.root / state).glob("*.yaml"))

    def load(self, state: str = "pending") -> list[Hypothesis]:
        """Parse every hypothesis in a state. Invalid files raise; they do not skip."""
        return [parse_hypothesis(p, self.params) for p in self.paths(state)]

    def load_tolerant(
        self, state: str = "pending"
    ) -> tuple[list[Hypothesis], list[tuple[Path, str]]]:
        """Parse a state, returning (valid, [(path, rejection reason)])."""
        good: list[Hypothesis] = []
        bad: list[tuple[Path, str]] = []
        for path in self.paths(state):
            try:
                good.append(parse_hypothesis(path, self.params))
            except HypothesisRejected as exc:
                bad.append((path, str(exc)))
        return good, bad

    def find(self, hypothesis_id: str) -> tuple[str, Path] | None:
        for state in STATES:
            for path in self.paths(state):
                if path.stem == hypothesis_id or path.stem.startswith(hypothesis_id):
                    return state, path
        return None

    def move(
        self,
        hypothesis_id: str,
        to_state: str,
        run_id: str | None = None,
        detail: str = "",
    ) -> Path:
        """
        Move a hypothesis between states and record the transition.

        The file moves and the transition is appended; nothing is overwritten, so
        the store shows the whole path a hypothesis took including the ones that
        went pending -> done without ever running.
        """
        if to_state not in STATES:
            raise ValueError(f"unknown state {to_state!r}")
        found = self.find(hypothesis_id)
        if not found:
            raise FileNotFoundError(f"no hypothesis {hypothesis_id!r} in {self.root}")
        from_state, path = found
        if from_state == to_state:
            return path

        target = self.root / to_state / path.name
        if target.exists():
            raise FileExistsError(f"{target} already exists; refusing to overwrite a registration")
        shutil.move(str(path), str(target))

        if self.store is not None:
            self.store.record_transition(hypothesis_id, from_state, to_state, run_id, detail)
        return target

    def triage(self, snapshot_manifest: list[str] | set[str]) -> dict[str, Any]:
        """
        Validate every pending hypothesis and split it into ready, blocked and
        rejected. Blocked hypotheses get a request file written.
        """
        good, bad = self.load_tolerant("pending")
        ready: list[Hypothesis] = []
        blocked: list[tuple[Hypothesis, DataCheck, Path]] = []
        for hyp in good:
            check = check_data(hyp, snapshot_manifest)
            if check.blocked:
                request = write_data_request(hyp, check, self.requests_dir)
                blocked.append((hyp, check, request))
            else:
                ready.append(hyp)
        return {"ready": ready, "blocked": blocked, "rejected": bad}
