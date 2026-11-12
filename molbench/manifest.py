"""
The run manifest: one file that names everything a benchmark run depends on.

``run/final_run.toml`` states the corpus (version + content hash), the model panel
(ids, provider routes, prices with source and date), the prompting conditions, the
number of samples, the token limit, the retry policy and a budget cap in dollars.
``python -m molbench.runner --manifest run/final_run.toml`` reads nothing else.

This module only parses, validates and does arithmetic (corpus hash, token and cost
estimates, the budget guard). It calls no model and needs no network.

    python -m molbench.manifest run/final_run.toml     # validate + print the corpus hash
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import statistics
import sys
import threading
from dataclasses import dataclass, field
from typing import Any, Iterable

try:  # Python >= 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

REPO = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CALIBRATION = REPO / "run" / "token_calibration.json"

TRACKS = ("mvs", "api_calling")
PROMPTS = ("spec", "bare")
# How a provider is asked for JSON. "json_object" is the OpenAI-compatible
# ``response_format={"type": "json_object"}``; "none" means the model/route has no
# such switch (or we have not wired it), so it is left out of structured conditions.
STRUCTURED_MODES = ("none", "json_object")
VALIDATE_MODES = ("auto", "required", "off")


class ManifestError(ValueError):
    """The manifest is malformed, or does not match the corpus on disk."""


class BudgetExceeded(RuntimeError):
    """Projected spend is above the manifest's cap. The run stops; the archive stays."""


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Price:
    """USD per 1,000,000 tokens. ``verified`` = read from the named source on ``date``."""
    input: float
    output: float
    source: str = ""
    date: str = ""
    verified: bool = False
    note: str = ""

    def cost(self, input_tokens: float, output_tokens: float) -> float:
        return (input_tokens * self.input + output_tokens * self.output) / 1_000_000


@dataclass(frozen=True)
class ModelSpec:
    id: str                      # the name used in scorecards (stable across routes)
    route: str                   # provider spec for molbench.models.build_model
    price: Price | None = None
    open_weights: bool = False
    reasoning: bool = False      # spends output tokens on hidden reasoning
    structured: str = "none"     # one of STRUCTURED_MODES
    optional: bool = False       # proposed addition: only run with --include-optional
    max_tokens: int | None = None
    max_concurrency: int | None = None
    reason: str = ""             # why it is in the panel

    @property
    def slug(self) -> str:
        return self.route.replace(":", "_").replace("/", "_")


@dataclass(frozen=True)
class Condition:
    name: str
    prompt: str = "spec"                 # "spec" (with the reference) or "bare"
    grounding: bool = False              # append the task's frozen grounding pack
    structured: bool = False             # ask the provider for JSON mode
    tracks: tuple[str, ...] = TRACKS
    models: Any = "all"                  # "all" | "structured" | [model ids]
    where: dict[str, tuple] = field(default_factory=dict)  # task field -> allowed values
    note: str = ""

    def takes_task(self, task: dict) -> bool:
        if task.get("category") not in self.tracks:
            return False
        if self.grounding and not task.get("grounding"):
            return False  # nothing to append: the cell would duplicate the plain one
        return all(task.get(k) in allowed for k, allowed in self.where.items())

    def takes_model(self, model: ModelSpec) -> bool:
        if self.structured and model.structured == "none":
            return False
        if self.models in ("all", "structured"):
            return True
        return model.id in self.models


@dataclass(frozen=True)
class Retry:
    max_attempts: int = 5
    backoff_seconds: float = 2.0
    backoff_max_seconds: float = 60.0
    timeout_seconds: float = 300.0

    def delay(self, attempt: int) -> float:
        """Seconds to wait after failed attempt number ``attempt`` (1-based)."""
        return min(self.backoff_max_seconds, self.backoff_seconds * 2 ** (attempt - 1))


@dataclass(frozen=True)
class Manifest:
    path: pathlib.Path
    name: str
    samples: int
    max_tokens: int
    reasoning_max_tokens: int
    temperature: str
    concurrency: int
    per_model_concurrency: int
    validate: str
    retry: Retry
    budget_usd: float
    corpus_version: str
    corpus_sha256: str
    conditions: tuple[Condition, ...]
    models: tuple[ModelSpec, ...]
    sha256: str  # of the manifest file itself

    def panel(self, include_optional: bool = False,
              only: Iterable[str] | None = None) -> list[ModelSpec]:
        only = set(only or [])
        unknown = only - {m.id for m in self.models}
        if unknown:
            raise ManifestError(f"--only-models names models not in the manifest: {sorted(unknown)}")
        return [m for m in self.models
                if (m.id in only if only else (include_optional or not m.optional))]

    def max_tokens_for(self, model: ModelSpec) -> int:
        if model.max_tokens:
            return model.max_tokens
        return self.reasoning_max_tokens if model.reasoning else self.max_tokens

    def condition(self, name: str) -> Condition:
        return next(c for c in self.conditions if c.name == name)


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def _need(d: dict, key: str, where: str) -> Any:
    if key not in d:
        raise ManifestError(f"{where}: missing '{key}'")
    return d[key]


def _known(d: dict, allowed: set[str], where: str) -> None:
    extra = set(d) - allowed
    if extra:
        raise ManifestError(f"{where}: unknown key(s) {sorted(extra)}")


def _int(d: dict, key: str, where: str, default: Any = None) -> Any:
    """A whole number (or the default when absent). 2.5 or "8k" is an error, not 2 or a
    traceback: a mistyped manifest must not start a paid run with a different plan."""
    v = d.get(key, default)
    if v is not None and type(v) is not int:
        raise ManifestError(f"{where}: '{key}' must be a whole number, not {v!r}")
    return v


def _num(d: dict, key: str, where: str, default: Any = None) -> Any:
    v = d.get(key, default)
    if v is not None and type(v) not in (int, float):
        raise ManifestError(f"{where}: '{key}' must be a number, not {v!r}")
    return v if v is None else float(v)


def _price(d: dict | None, where: str) -> Price | None:
    if d is None:
        return None
    _known(d, {"input", "output", "source", "date", "verified", "note"}, where)
    _need(d, "input", where), _need(d, "output", where)
    p = Price(_num(d, "input", where), _num(d, "output", where),
              d.get("source", ""), str(d.get("date", "")), bool(d.get("verified", False)),
              d.get("note", ""))
    if p.input < 0 or p.output < 0:
        raise ManifestError(f"{where}: negative price")
    if p.verified and not (p.source and p.date):
        raise ManifestError(f"{where}: a verified price needs a source and a date")
    return p


def _model(d: dict, i: int) -> ModelSpec:
    where = f"models[{i}] ({d.get('id', '?')})"
    _known(d, {"id", "route", "price", "open_weights", "reasoning", "structured", "optional",
               "max_tokens", "max_concurrency", "reason"}, where)
    structured = d.get("structured", "none")
    if structured not in STRUCTURED_MODES:
        raise ManifestError(f"{where}: structured must be one of {STRUCTURED_MODES}")

    def _positive(key: str) -> int | None:
        v = _int(d, key, where)
        if v is not None and v < 1:
            raise ManifestError(f"{where}: '{key}' must be >= 1")
        return v
    return ModelSpec(
        id=_need(d, "id", where), route=_need(d, "route", where),
        price=_price(d.get("price"), where + ".price"),
        open_weights=bool(d.get("open_weights", False)),
        reasoning=bool(d.get("reasoning", False)), structured=structured,
        optional=bool(d.get("optional", False)), max_tokens=_positive("max_tokens"),
        max_concurrency=_positive("max_concurrency"), reason=d.get("reason", ""))


def _condition(d: dict, i: int, model_ids: set[str]) -> Condition:
    where = f"conditions[{i}] ({d.get('name', '?')})"
    _known(d, {"name", "prompt", "grounding", "structured", "tracks", "models", "where",
               "note"}, where)
    prompt = d.get("prompt", "spec")
    if prompt not in PROMPTS:
        raise ManifestError(f"{where}: prompt must be one of {PROMPTS}")
    tracks = tuple(d.get("tracks", TRACKS))
    if not tracks or set(tracks) - set(TRACKS):
        raise ManifestError(f"{where}: tracks must be drawn from {TRACKS}")
    models = d.get("models", "all")
    if isinstance(models, list):
        missing = set(models) - model_ids
        if missing:
            raise ManifestError(f"{where}: unknown model(s) {sorted(missing)}")
        models = tuple(models)
    elif models not in ("all", "structured"):
        raise ManifestError(f"{where}: models must be 'all', 'structured' or a list of ids")
    if models == "structured" and not d.get("structured"):
        raise ManifestError(f"{where}: models = 'structured' needs structured = true")
    wh = {k: tuple(v if isinstance(v, list) else [v]) for k, v in d.get("where", {}).items()}
    return Condition(name=_need(d, "name", where), prompt=prompt,
                     grounding=bool(d.get("grounding", False)),
                     structured=bool(d.get("structured", False)), tracks=tracks,
                     models=models, where=wh, note=d.get("note", ""))


def parse_manifest(text: str, path: pathlib.Path | str = "<string>") -> Manifest:
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ManifestError(f"{path}: not valid TOML: {e}") from e
    _known(raw, {"run", "budget", "corpus", "conditions", "models"}, str(path))
    run = _need(raw, "run", str(path))
    _known(run, {"name", "samples", "max_tokens", "reasoning_max_tokens", "temperature",
                 "concurrency", "per_model_concurrency", "validate", "retry"}, "run")
    retry = run.get("retry", {})
    _known(retry, {"max_attempts", "backoff_seconds", "backoff_max_seconds",
                   "timeout_seconds"}, "run.retry")
    budget = _need(raw, "budget", str(path))
    _known(budget, {"cap_usd", "note"}, "budget")
    corpus = _need(raw, "corpus", str(path))
    _known(corpus, {"version", "sha256", "note"}, "corpus")

    models = tuple(_model(d, i) for i, d in enumerate(_need(raw, "models", str(path))))
    ids = [m.id for m in models]
    for label, values in (("id", ids), ("route", [m.route for m in models])):
        dup = sorted({v for v in values if values.count(v) > 1})
        if dup:
            raise ManifestError(f"models: duplicate {label}(s) {dup}")
    conditions = tuple(_condition(d, i, set(ids))
                       for i, d in enumerate(_need(raw, "conditions", str(path))))
    names = [c.name for c in conditions]
    if len(set(names)) != len(names):
        raise ManifestError("conditions: duplicate names")
    if not conditions or not models:
        raise ManifestError("the manifest needs at least one condition and one model")

    for section, key, where in ((run, "samples", "run"), (run, "max_tokens", "run"),
                                (budget, "cap_usd", "budget")):
        _need(section, key, where)
    m = Manifest(
        path=pathlib.Path(path), name=str(_need(run, "name", "run")),
        samples=_int(run, "samples", "run"),
        max_tokens=_int(run, "max_tokens", "run"),
        reasoning_max_tokens=_int(run, "reasoning_max_tokens", "run", run["max_tokens"]),
        temperature=run.get("temperature", "provider-default"),
        concurrency=_int(run, "concurrency", "run", 4),
        per_model_concurrency=_int(run, "per_model_concurrency", "run", 2),
        validate=run.get("validate", "auto"),
        retry=Retry(**{k: (_int if k == "max_attempts" else _num)(retry, k, "run.retry")
                       for k in retry}),
        budget_usd=_num(budget, "cap_usd", "budget"),
        corpus_version=_need(corpus, "version", "corpus"),
        corpus_sha256=corpus.get("sha256", ""),
        conditions=conditions, models=models,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())
    if min(m.samples, m.max_tokens, m.reasoning_max_tokens, m.concurrency,
           m.per_model_concurrency) < 1:
        raise ManifestError("run: samples, max_tokens and concurrency must be >= 1")
    if min(m.retry.backoff_seconds, m.retry.backoff_max_seconds) < 0 or m.retry.timeout_seconds <= 0:
        raise ManifestError("run.retry: backoff must be >= 0 and timeout_seconds > 0")
    if m.retry.max_attempts < 1:
        raise ManifestError("run.retry: max_attempts must be >= 1")
    if m.budget_usd <= 0:
        raise ManifestError("budget: cap_usd must be > 0")
    if m.temperature != "provider-default":
        # FINAL_PLAN decision 12. A fixed temperature is rejected by several current
        # models, so the runner never sends one; refuse a manifest that claims otherwise.
        raise ManifestError("run: temperature must be 'provider-default' (no value is sent)")
    if m.validate not in VALIDATE_MODES:
        raise ManifestError(f"run: validate must be one of {VALIDATE_MODES}")
    if any(c in m.name for c in "/\\ "):
        raise ManifestError("run: name is used as a directory name; no slashes or spaces")
    return m


def load_manifest(path: pathlib.Path | str) -> Manifest:
    path = pathlib.Path(path)
    return parse_manifest(path.read_text(encoding="utf-8"), path)


# --------------------------------------------------------------------------- #
# Corpus identity
# --------------------------------------------------------------------------- #
def corpus_hash(tasks_dir: pathlib.Path) -> str:
    """SHA-256 over every ``tasks/**/*.json`` file: sorted relative path + bytes.

    Any change to any task (prompt, reference, grounding pack) changes it, so a run
    archive can be tied to the exact corpus it was made on.
    """
    h = hashlib.sha256()
    for f in sorted(tasks_dir.rglob("*.json"), key=lambda p: p.relative_to(tasks_dir).as_posix()):
        h.update(f.relative_to(tasks_dir).as_posix().encode("utf-8") + b"\0")
        h.update(hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()


def check_corpus(manifest: Manifest, tasks_dir: pathlib.Path, strict: bool) -> str:
    """The corpus hash on disk. With ``strict`` (a real run) it must equal the manifest's."""
    actual = corpus_hash(tasks_dir)
    if strict and not manifest.corpus_sha256:
        raise ManifestError(
            "corpus.sha256 is empty: freeze the corpus first, then pin its hash in the "
            f"manifest (hash on disk now: {actual})")
    if strict and manifest.corpus_sha256 != actual:
        raise ManifestError(
            f"corpus on disk ({actual[:12]}…) is not the corpus the manifest pins "
            f"({manifest.corpus_sha256[:12]}…, {manifest.corpus_version})")
    return actual


# --------------------------------------------------------------------------- #
# Token and cost estimates
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TokenRates:
    """How characters turn into billed tokens for one model.

    ``chars_per_input_token``: prompt characters per billed input token.
    ``output_tokens_per_ref_char``: billed output tokens per character of the task's
    reference answer (compact JSON). It folds together the tokenizer, how verbose
    the model is, and any hidden reasoning tokens - which is what is billed.
    """
    chars_per_input_token: float
    output_tokens_per_ref_char: float
    calibrated: bool = True


class Calibration:
    """Per-model token rates measured on archived runs (``scripts/estimate_cost.py
    --calibrate``), with pooled fall-backs for models that were never run."""

    def __init__(self, data: dict):
        self.data = data
        self.models = {k: TokenRates(v["chars_per_input_token"], v["output_tokens_per_ref_char"])
                       for k, v in data.get("models", {}).items()}
        d = data["default"]
        self.default = TokenRates(d["chars_per_input_token"],
                                  d["output_tokens_per_ref_char"], calibrated=False)
        r = data.get("default_reasoning", d)
        self.default_reasoning = TokenRates(r["chars_per_input_token"],
                                            r["output_tokens_per_ref_char"], calibrated=False)

    @classmethod
    def load(cls, path: pathlib.Path | str | None = None) -> "Calibration":
        return cls(json.loads(pathlib.Path(path or DEFAULT_CALIBRATION).read_text("utf-8")))

    def rates(self, model: ModelSpec) -> TokenRates:
        if model.id in self.models:
            return self.models[model.id]
        return self.default_reasoning if model.reasoning else self.default


def pooled_rates(rows: dict[str, dict]) -> dict[str, dict]:
    """Fall-back rates from the calibrated models: the median, and - for reasoning
    models, whose output is the expensive unknown - the highest output rate seen."""
    cin = [r["chars_per_input_token"] for r in rows.values()]
    out = [r["output_tokens_per_ref_char"] for r in rows.values()]
    return {
        "default": {"chars_per_input_token": round(statistics.median(cin), 3),
                    "output_tokens_per_ref_char": round(statistics.median(out), 4)},
        "default_reasoning": {"chars_per_input_token": round(min(cin), 3),
                              "output_tokens_per_ref_char": round(max(out), 4)},
    }


def estimate_tokens(prompt_chars: int, ref_chars: int, rates: TokenRates,
                    max_tokens: int) -> tuple[int, int]:
    """(input, output) tokens expected for one call. Output is capped at ``max_tokens``."""
    inp = round(prompt_chars / rates.chars_per_input_token)
    out = min(max_tokens, round(ref_chars * rates.output_tokens_per_ref_char))
    return inp, out


def estimate_cost(price: Price | None, input_tokens: float, output_tokens: float) -> float | None:
    return None if price is None else price.cost(input_tokens, output_tokens)


# --------------------------------------------------------------------------- #
# Budget guard
# --------------------------------------------------------------------------- #
class Budget:
    """Tracks spend against the cap and says when to stop. Thread-safe.

    The projection is ``spent so far + estimated cost of the calls still to make``.
    ``charge`` moves one call from "still to make" to "spent" at its real cost, and
    raises `BudgetExceeded` once the projection passes the cap - so the run stops
    before the money is gone, not after.
    """

    def __init__(self, cap_usd: float, spent: float = 0.0, remaining_estimate: float = 0.0):
        self.cap = cap_usd
        self.spent = spent
        self.remaining = remaining_estimate
        self._lock = threading.Lock()
        self.exceeded = False

    @property
    def projected(self) -> float:
        return self.spent + max(self.remaining, 0.0)

    def check(self) -> None:
        if self.projected > self.cap:
            self.exceeded = True
            raise BudgetExceeded(
                f"projected spend ${self.projected:.2f} (spent ${self.spent:.2f} + "
                f"${max(self.remaining, 0.0):.2f} still to run) is above the "
                f"${self.cap:.2f} cap")

    def charge(self, actual: float, estimate: float) -> None:
        with self._lock:
            self.spent += actual
            self.remaining -= estimate
            self.check()


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    path = pathlib.Path(argv[0]) if argv else REPO / "run" / "final_run.toml"
    m = load_manifest(path)
    actual = corpus_hash(REPO / "tasks")
    pinned = ("not pinned" if not m.corpus_sha256
              else "matches" if m.corpus_sha256 == actual else "DOES NOT MATCH the manifest")
    core = [x for x in m.models if not x.optional]
    print(f"{path}: ok  run={m.name}  samples={m.samples}  budget=${m.budget_usd:.2f}")
    print(f"  models: {len(core)} + {len(m.models) - len(core)} optional   "
          f"conditions: {', '.join(c.name for c in m.conditions)}")
    print(f"  corpus {m.corpus_version}: sha256 on disk {actual} ({pinned})")
    unverified = [x.id for x in m.models if x.price is None or not x.price.verified]
    if unverified:
        print(f"  prices missing or unverified: {', '.join(unverified)}")


if __name__ == "__main__":
    main()
