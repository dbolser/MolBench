#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["json-repair>=0.30"]
# ///
"""Regenerate every number the paper cites, from run scorecards and raw archives.

    uv run scripts/paper_tables.py                      # paper/inputs.json, the October panel
    uv run scripts/paper_tables.py --manifest FINAL.json --data-root /path/to/data

Reads (all named by the manifest, nothing is hard-coded to the October file names):

* **scorecards** -- one JSON per (model, condition) as the runner writes them:
  ``{"meta": {"condition", "grounding", ...}, "models": {name: {"tasks": [row...],
  "usage", "cost_usd"}}}``. A task row carries ``id``, ``category`` (the track), and
  per-sample ``samples_f1`` + ``outcomes`` (or a single ``f1`` + ``outcome``).
* **archives** -- the raw ``run_*.json`` files (``raw_samples[model][task] = [sample]``);
  only used for the offline json-repair counterfactual and the bracket-error breakdown.
* **tasks_dir** -- the task corpus, for each task's regime, structure and reference.
* **legacy_scorecard** (optional) -- the July API-track numbers, reported only as the
  reason the API track was rebuilt.

Writes ``paper/generated/``: ``values.json`` (flat key -> number/string; the only place
paper text may take a number from), ``table_*.md``, ``figdata.json`` (what
``scripts/paper_figures.py`` draws) and ``provenance.json``.

Metrics, in plain words (the same wording goes into the table captions):

* **strict F1** -- mean score over all tasks; an output the viewer cannot show scores 0.
* **valid-scene rate** -- share of outputs that parse and that Mol* accepts and loads.
* **F1 over valid scenes** -- mean score over the valid outputs only.
* **task success** -- share of outputs that are valid and score exactly 1.
* 95% confidence intervals: bootstrap over tasks, resampling whole *structures* (all
  tasks on one PDB entry are drawn together), percentile method.

The json-repair counterfactual needs the ``json-repair`` package (pulled in by the
inline script metadata above when run with ``uv run scripts/paper_tables.py``). Without
it the script still runs and marks those values as not computed.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import pathlib
import random
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import mvs  # noqa: E402  (stdlib-only grader)

DEFAULT_MANIFEST = REPO / "paper" / "inputs.json"
DEFAULT_OUT = REPO / "paper" / "generated"

# How a task's ``source`` maps to a regime when the task file names no ``regime`` itself.
# A source that is not listed becomes its own regime (and is reported on stderr), so a new
# tier in the final corpus shows up in the tables instead of silently joining another row.
SOURCE_REGIME = {
    "generated": "Translation", "curated": "Translation",
    "grounded": "Grounded",
    "clinvar-variant": "Clinical", "clinvar-hotspots": "Clinical", "sifts-named": "Clinical",
    "resolve": "Resolution",
    "interactions": "Interactions",
}
REGIME_ORDER = ["Translation", "Grounded", "Clinical", "Resolution", "Interactions"]
DEFAULT_LOOKUP_SOURCES = ["clinvar-variant", "clinvar-hotspots", "sifts-named", "resolve"]
OUTCOME_ORDER = ["valid", "invalid_json", "not_mvs", "invalid_mvs", "load_failed", "unchecked"]
OUTCOME_LABEL = {
    "valid": "valid scene", "invalid_json": "invalid JSON", "not_mvs": "JSON, not a scene",
    "invalid_mvs": "scene rejected by Mol*", "load_failed": "structure failed to load",
    "unchecked": "not checked",
}
RESCUED = {"rendering-equivalent", "vlm:same"}
SUCCESS_EPS = 1e-9


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
def default_data_root() -> pathlib.Path:
    """Where the git-ignored run data lives.

    The repo root, unless this is a linked git worktree without ``results/``: then the
    main checkout (which holds the archives) is used.
    """
    if (REPO / "results").exists() or (REPO / "runs").exists():
        return REPO
    try:
        common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
        main = pathlib.Path(common).parent
        if (main / "results").exists() or (main / "runs").exists():
            return main
    except (OSError, subprocess.CalledProcessError):
        pass
    return REPO


def expand(patterns, roots: list[pathlib.Path]) -> list[pathlib.Path]:
    """Glob each pattern under the first root where it matches anything."""
    if isinstance(patterns, str):
        patterns = [patterns]
    out: list[pathlib.Path] = []
    for pat in patterns or []:
        if pathlib.Path(pat).is_absolute():
            out += [pathlib.Path(p) for p in sorted(glob.glob(pat, recursive=True))]
            continue
        for root in roots:
            hits = sorted(glob.glob(str(root / pat), recursive=True))
            if hits:
                out += [pathlib.Path(h) for h in hits]
                break
    return out


def structure_of(task: dict) -> str:
    """The PDB entry (or other structure id) a task is about: the bootstrap cluster."""
    if task.get("pdb"):
        return str(task["pdb"]).lower()
    urls = re.findall(r'"url":\s*"([^"]+)"', json.dumps(task.get("reference_mvs") or {}))
    ids = sorted({re.sub(r"\.(bcif|cif|pdb)(\.gz)?$", "", u.rsplit("/", 1)[-1]).lower()
                  for u in urls})
    if ids:
        return "+".join(ids)
    return f"task:{task['id']}"


def load_tasks(tasks_dir: pathlib.Path, lookup_sources: set[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    unknown: set[str] = set()
    for f in sorted(tasks_dir.rglob("*.json")):
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if not isinstance(t, dict) or "id" not in t:
            continue
        source = t.get("source", "curated")
        regime = t.get("regime") or SOURCE_REGIME.get(source)
        if regime is None:
            regime = source
            unknown.add(source)
        out[t["id"]] = {
            "id": t["id"], "track": t.get("category"), "source": source, "regime": regime,
            "structure": structure_of(t), "template": t.get("template"),
            "lookup": bool(t.get("lookup", source in lookup_sources)),
            "reference_mvs": t.get("reference_mvs"), "accepted_ids": t.get("accepted_ids"),
        }
    if unknown:
        print(f"note: task sources with no regime mapping, used as their own regime: "
              f"{sorted(unknown)}", file=sys.stderr)
    return out


def condition_of(meta: dict) -> str:
    """One label per prompting condition, read from the run's own metadata."""
    if meta.get("condition_label"):
        return meta["condition_label"]
    c = meta.get("condition") or "spec"
    if meta.get("grounding"):
        c += "_grounded"
    if meta.get("structured_output") or meta.get("json_mode"):
        c += "_json"
    return c


def row_samples(row: dict) -> list[dict]:
    """A task row as a list of samples: ``{"f1", "outcome", "decision", "tier"}``."""
    if isinstance(row.get("samples"), list) and row["samples"] and isinstance(row["samples"][0], dict):
        return [{"f1": float(s.get("f1", 0.0)), "outcome": s.get("outcome", "valid"),
                 "decision": (s.get("escalation") or {}).get("decision"),
                 "tier": (s.get("escalation") or {}).get("tier")} for s in row["samples"]]
    f1s = row.get("samples_f1") or [row.get("f1", 0.0)]
    outs = row.get("outcomes") or [row.get("outcome")] * len(f1s)
    if len(outs) != len(f1s):
        outs = (list(outs) + [outs[-1] if outs else None] * len(f1s))[:len(f1s)]
    esc = row.get("escalation") or {}
    one = len(f1s) == 1
    return [{"f1": float(f), "outcome": o or ("valid" if row.get("error") is None else "invalid_json"),
             "decision": esc.get("decision") if one else None,
             "tier": esc.get("tier") if one else None} for f, o in zip(f1s, outs)]


def load_scorecards(paths: list[pathlib.Path], aliases: dict[str, str]) -> dict:
    """``{(track, condition, model): record}``; a second scorecard for one cell is an error."""
    cells: dict[tuple, dict] = {}
    for f in paths:
        card = json.loads(f.read_text(encoding="utf-8"))
        meta = card.get("meta", {})
        cond = condition_of(meta)
        for raw_name, m in card.get("models", {}).items():
            name = aliases.get(raw_name, raw_name)
            by_track: dict[str, dict] = defaultdict(dict)
            errors: dict[str, str] = {}
            for row in m.get("tasks", []):
                by_track[row.get("category", "mvs")][row["id"]] = row_samples(row)
                if row.get("error"):
                    errors[row["id"]] = str(row["error"])
            for track, tasks in by_track.items():
                key = (track, cond, name)
                if key in cells:
                    raise SystemExit(f"two scorecards for {key}: {cells[key]['file']} and {f}")
                cells[key] = {
                    "file": str(f), "meta": meta, "raw_name": raw_name, "tasks": tasks,
                    "errors": errors, "usage": m.get("usage") or {}, "cost_usd": m.get("cost_usd"),
                    "baseline": m.get("spec") == "baseline" or raw_name.startswith("baseline"),
                }
    return cells


def archive_index(paths: list[pathlib.Path]) -> dict[tuple, pathlib.Path]:
    """Find a run's raw archive by its ``run_id``, else by (start time, model, flags)."""
    idx: dict[tuple, pathlib.Path] = {}
    for f in paths:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        meta = d.get("meta", {})
        if not d.get("raw_samples"):
            continue
        for k in archive_keys(meta, list(d["raw_samples"])):
            idx[k] = f
    return idx


def archive_keys(meta: dict, model_names: list[str]) -> list[tuple]:
    keys = []
    if meta.get("run_id"):
        keys += [("run_id", meta["run_id"], n) for n in model_names]
    keys += [("start", meta.get("started_at"), n, condition_of(meta), bool(meta.get("escalate")))
             for n in model_names]
    return keys


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def task_stats(samples: list[dict]) -> dict:
    n = len(samples)
    valid = [s for s in samples if s["outcome"] == "valid"]
    return {
        "n": n, "f1_sum": sum(s["f1"] for s in samples), "n_valid": len(valid),
        "f1_valid_sum": sum(s["f1"] for s in valid),
        "n_success": sum(s["f1"] >= 1 - SUCCESS_EPS for s in valid),
    }


def metrics(stats: list[dict]) -> dict:
    """Headline metrics over a list of per-task stats (tasks weigh equally)."""
    if not stats:
        return {"f1": None, "valid": None, "f1_valid": None, "success": None}
    nt = len(stats)
    n_valid = sum(s["n_valid"] for s in stats)
    return {
        "f1": sum(s["f1_sum"] / s["n"] for s in stats) / nt,
        "valid": sum(s["n_valid"] / s["n"] for s in stats) / nt,
        "f1_valid": (sum(s["f1_valid_sum"] for s in stats) / n_valid) if n_valid else None,
        "success": sum(s["n_success"] / s["n"] for s in stats) / nt,
    }


def percentile(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    pos = (len(xs) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


class Bootstrap:
    """Cluster bootstrap with one shared set of draws, so paired differences are honest."""

    def __init__(self, tasks: dict[str, dict], task_ids: list[str], n_boot: int, seed: int):
        self.clusters: dict[str, list[str]] = defaultdict(list)
        for i in task_ids:
            self.clusters[tasks[i]["structure"] if i in tasks else f"task:{i}"].append(i)
        self.names = sorted(self.clusters)
        rng = random.Random(seed)
        k = len(self.names)
        self.draws = [[rng.randrange(k) for _ in range(k)] for _ in range(n_boot)] if k > 1 else []

    @property
    def n_clusters(self) -> int:
        return len(self.names)

    def ci(self, num: dict[str, float], den: dict[str, float] | None = None
           ) -> tuple[float, float] | None:
        """95% percentile interval of ``sum(num) / sum(den)`` over resampled structures.

        ``num`` and ``den`` map task id -> that task's contribution (``den`` defaults to 1
        per task in ``num``, giving a plain mean over tasks). Every statistic in the paper
        is such a ratio of sums, so the per-structure totals are computed once. Returns
        None when fewer than two structures carry data (no interval can be estimated).
        """
        tot = []
        for name in self.names:
            ids = [i for i in self.clusters[name] if i in num]
            tot.append((sum(num[i] for i in ids),
                        sum(den[i] for i in ids) if den is not None else float(len(ids))))
        if sum(1 for _, d in tot if d) < 2:
            return None
        vals = []
        for draw in self.draws:
            n = d = 0.0
            for j in draw:
                n += tot[j][0]
                d += tot[j][1]
            if d:
                vals.append(n / d)
        if len(vals) < 20:
            return None
        return (percentile(vals, 0.025), percentile(vals, 0.975))


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if not sxx or not syy:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #
def r4(x):
    return None if x is None else round(float(x), 4)


def f3(x) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def pct(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def ci_str(ci, fmt=f3) -> str:
    return "n/a" if ci is None else f"{fmt(ci[0])}–{fmt(ci[1])}"


def short(name: str) -> str:
    return name.split("/")[-1]


def key_name(name: str) -> str:
    """A model name as a values.json key segment."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", short(name))


def md_table(header: list[str], rows: list[list], align: str | None = None) -> str:
    align = align or "l" + "r" * (len(header) - 1)
    sep = [":---" if a == "l" else "---:" for a in align]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def usd(x) -> str:
    return "not recorded" if x is None else f"${x:.2f}" if x >= 1 else f"${x:.3f}"


# --------------------------------------------------------------------------- #
# The analysis
# --------------------------------------------------------------------------- #
class Paper:
    def __init__(self, manifest: dict, roots: list[pathlib.Path], n_boot: int, seed: int):
        self.man = manifest
        self.roots = roots
        self.n_boot, self.seed = n_boot, seed
        self.values: dict[str, object] = {}
        self.tables: dict[str, str] = {}
        self.fig: dict[str, object] = {}
        self.notes: list[str] = []
        self.status = manifest.get("status", "final")
        self.tag = " (PRELIMINARY)" if self.status == "preliminary" else ""
        self.headline = manifest.get("headline_condition", "spec")
        self.grounded = manifest.get("grounded_condition", f"{self.headline}_grounded")
        self.weights = {k: v.get("weights") for k, v in manifest.get("model_info", {}).items()}

        tasks_dir = expand(manifest.get("tasks_dir", "tasks"), roots)
        if not tasks_dir:
            raise SystemExit("tasks_dir not found")
        self.tasks = load_tasks(tasks_dir[0], set(manifest.get("lookup_sources",
                                                               DEFAULT_LOOKUP_SOURCES)))
        self.score_files = expand(manifest.get("scorecards", []), roots)
        if not self.score_files:
            raise SystemExit(f"no scorecards matched {manifest.get('scorecards')} under {roots}")
        self.cells = load_scorecards(self.score_files, manifest.get("aliases", {}))
        self.archive_files = expand(manifest.get("archives", []), roots)
        self.archives = archive_index(self.archive_files)
        self._archive_cache: dict[pathlib.Path, dict] = {}

    # -- small accessors ---------------------------------------------------- #
    def put(self, key: str, value) -> None:
        if isinstance(value, float):
            value = round(value, 4)
        self.values[key] = value

    def models(self, track: str, cond: str, baselines: bool = False) -> list[str]:
        return sorted(m for (t, c, m), cell in self.cells.items()
                      if t == track and c == cond and (baselines or not cell["baseline"]))

    def stats(self, track: str, cond: str, model: str) -> dict[str, dict]:
        return {i: task_stats(s) for i, s in self.cells[(track, cond, model)]["tasks"].items()}

    def regime(self, task_id: str) -> str:
        return self.tasks[task_id]["regime"] if task_id in self.tasks else "Unknown"

    def regimes(self, ids) -> list[str]:
        seen = {self.regime(i) for i in ids}
        return [r for r in REGIME_ORDER if r in seen] + sorted(seen - set(REGIME_ORDER))

    # -- sections ------------------------------------------------------------ #
    def run(self) -> None:
        self.put("run.label", self.man.get("label", "unnamed run"))
        self.put("run.status", self.status)
        self.put("run.status_tag", "PRELIMINARY" if self.status == "preliminary" else "FINAL")
        self.put("run.date", self.man.get("run_date", ""))
        self.put("run.bootstrap_replicates", self.n_boot)
        tracks = sorted({t for (t, _, _) in self.cells})
        self.put("run.tracks", ", ".join(tracks))
        for track in tracks:
            self.track(track)
        self.legacy_api()

    def track(self, track: str) -> None:
        T = track if track != "api_calling" else "api"
        conds = sorted({c for (t, c, _) in self.cells if t == track})
        if self.headline not in conds:
            self.notes.append(f"{track}: no '{self.headline}' scorecards; track skipped")
            return
        ids = sorted({i for m in self.models(track, self.headline, True)
                      for i in self.cells[(track, self.headline, m)]["tasks"]})
        boot = Bootstrap(self.tasks, ids, self.n_boot, self.seed)
        self.corpus(T, ids, boot)
        board = self.leaderboard(T, track, ids, boot)
        self.regime_table(T, track, ids)
        self.conditions(T, track, conds, ids, boot)
        self.failures(T, track)
        self.semantic_errors(T, track)
        self.repair(T, track, board)
        self.escalation(T, track)
        self.cost(T, track, board)

    def corpus(self, T: str, ids: list[str], boot: Bootstrap) -> None:
        known = [i for i in ids if i in self.tasks]
        if len(known) < len(ids):
            self.notes.append(f"{T}: {len(ids) - len(known)} graded tasks have no task file")
        self.put(f"{T}.n_tasks", len(ids))
        self.put(f"{T}.n_structures", boot.n_clusters)
        by_regime = Counter(self.regime(i) for i in ids)
        rows = []
        for rg in self.regimes(ids):
            rid = [i for i in ids if self.regime(i) == rg]
            structs = {self.tasks[i]["structure"] for i in rid if i in self.tasks}
            self.put(f"{T}.regime.{rg}.n_tasks", by_regime[rg])
            self.put(f"{T}.regime.{rg}.n_structures", len(structs))
            rows.append([rg, by_regime[rg], len(structs)])
        rows.append(["**All**", len(ids), boot.n_clusters])
        self.tables[f"table_{T}_corpus"] = (
            f"**Corpus used for the {self.man.get('label', 'run')}{self.tag}.** Tasks and distinct "
            "structures (PDB entries) per regime. A regime is a group of tasks that need the same "
            "kind of knowledge.\n\n" + md_table(["Regime", "Tasks", "Structures"], rows))

    def leaderboard(self, T: str, track: str, ids: list[str], boot: Bootstrap) -> list[dict]:
        H = self.headline
        board = []
        for m in self.models(track, H, baselines=True):
            cell = self.cells[(track, H, m)]
            st = self.stats(track, H, m)
            mt = metrics(list(st.values()))
            row = {"model": m, "short": short(m), "baseline": cell["baseline"],
                   "weights": self.weights.get(m, "unknown"),
                   "n_tasks": len(st), "n_samples": sum(s["n"] for s in st.values()),
                   "n_valid": sum(s["n_valid"] for s in st.values()), **mt}
            row["f1_ci"] = boot.ci({i: s["f1_sum"] / s["n"] for i, s in st.items()})
            row["valid_ci"] = boot.ci({i: s["n_valid"] / s["n"] for i, s in st.items()})
            row["success_ci"] = boot.ci({i: s["n_success"] / s["n"] for i, s in st.items()})
            row["f1_valid_ci"] = boot.ci({i: s["f1_valid_sum"] for i, s in st.items()},
                                         {i: float(s["n_valid"]) for i, s in st.items()})
            board.append(row)
        board.sort(key=lambda r: (-(r["f1"] or 0), r["model"]))
        llms = [r for r in board if not r["baseline"]]
        if not llms:
            return board

        samples_per_task = sorted({s["n"] for m in self.models(track, H)
                                   for s in self.stats(track, H, m).values()})
        self.put(f"{T}.{H}.n_models", len(llms))
        self.put(f"{T}.{H}.samples_per_task",
                 samples_per_task[0] if len(samples_per_task) == 1 else
                 f"{samples_per_task[0]}–{samples_per_task[-1]}")
        self.put(f"{T}.{H}.n_samples", sum(r["n_samples"] for r in llms))
        self.put(f"{T}.{H}.n_valid", sum(r["n_valid"] for r in llms))
        self.put(f"{T}.{H}.n_invalid", sum(r["n_samples"] - r["n_valid"] for r in llms))
        self.put(f"{T}.{H}.valid_pooled", sum(r["n_valid"] for r in llms)
                 / sum(r["n_samples"] for r in llms))
        for r in llms:
            k = f"{T}.{H}.model.{key_name(r['model'])}"
            for name in ("f1", "valid", "f1_valid", "success"):
                self.put(f"{k}.{name}", r[name])
                if r[f"{name}_ci"]:
                    self.put(f"{k}.{name}_lo", r[f"{name}_ci"][0])
                    self.put(f"{k}.{name}_hi", r[f"{name}_ci"][1])
        best, worst = llms[0], llms[-1]
        for tag, r in (("best", best), ("worst", worst)):
            self.put(f"{T}.{H}.{tag}.name", r["short"])
            for name in ("f1", "valid", "f1_valid", "success"):
                self.put(f"{T}.{H}.{tag}.{name}", r[name])
            if r["f1_ci"]:
                self.put(f"{T}.{H}.{tag}.f1_lo", r["f1_ci"][0])
                self.put(f"{T}.{H}.{tag}.f1_hi", r["f1_ci"][1])
        f1s = [r["f1"] for r in llms]
        fv = [r["f1_valid"] for r in llms if r["f1_valid"] is not None]
        self.put(f"{T}.{H}.f1_min", min(f1s))
        self.put(f"{T}.{H}.f1_max", max(f1s))
        self.put(f"{T}.{H}.f1_spread", max(f1s) - min(f1s))
        self.put(f"{T}.{H}.f1_valid_min", min(fv))
        self.put(f"{T}.{H}.f1_valid_max", max(fv))
        self.put(f"{T}.{H}.f1_valid_spread", max(fv) - min(fv))
        self.put(f"{T}.{H}.valid_min", min(r["valid"] for r in llms))
        self.put(f"{T}.{H}.valid_max", max(r["valid"] for r in llms))
        self.put(f"{T}.{H}.success_min", min(r["success"] for r in llms))
        self.put(f"{T}.{H}.success_max", max(r["success"] for r in llms))
        rr = pearson([r["valid"] for r in llms], f1s)
        self.put(f"{T}.{H}.r_valid_f1", round(rr, 3) if rr is not None else None)
        # How many models' intervals overlap the best model's interval.
        if best["f1_ci"]:
            tied = sum(1 for r in llms[1:] if r["f1_ci"] and r["f1_ci"][1] >= best["f1_ci"][0])
            self.put(f"{T}.{H}.n_overlap_best", tied)
        base = [r for r in board if r["baseline"]]
        if base:
            self.put(f"{T}.{H}.baseline_f1", base[0]["f1"])

        rows = []
        for i, r in enumerate(llms, 1):
            rows.append([i, r["short"], r["weights"], f3(r["f1"]), ci_str(r["f1_ci"]),
                         pct(r["valid"]), ci_str(r["valid_ci"], pct), f3(r["f1_valid"]),
                         ci_str(r["f1_valid_ci"]), pct(r["success"])])
        for r in base:
            rows.append(["–", r["short"] + " (no model)", "–", f3(r["f1"]), "–", pct(r["valid"]),
                         "–", f3(r["f1_valid"]), "–", pct(r["success"])])
        n_s = self.values[f"{T}.{H}.samples_per_task"]
        self.tables[f"table_{T}_leaderboard"] = (
            f"**{T.upper()} track, `{H}` condition{self.tag}.** {len(llms)} models, {len(ids)} "
            f"tasks on {boot.n_clusters} structures, {n_s} sample{'' if n_s == 1 else 's'} per task. "
            "*Strict F1*: mean score over all tasks, where an output the viewer cannot show "
            "scores 0. *Valid*: share of outputs that parse as JSON and that Mol\\* accepts and "
            "loads. *F1 (valid)*: mean score over the valid outputs only. *Success*: share of "
            "outputs that are valid and score exactly 1. 95% CI: bootstrap over tasks, "
            f"resampling whole structures ({self.n_boot} replicates). Weights: whether the model "
            "weights are openly released.\n\n"
            + md_table(["#", "Model", "Weights", "Strict F1", "95% CI", "Valid", "95% CI",
                        "F1 (valid)", "95% CI", "Success"], rows, "rllrrrrrrr"))
        self.fig[f"{T}_leaderboard"] = [
            {"model": r["short"], "weights": r["weights"], "f1": r4(r["f1"]),
             "f1_ci": [r4(x) for x in r["f1_ci"]] if r["f1_ci"] else None,
             "valid": r4(r["valid"]), "f1_valid": r4(r["f1_valid"]),
             "f1_valid_ci": [r4(x) for x in r["f1_valid_ci"]] if r["f1_valid_ci"] else None,
             "success": r4(r["success"])} for r in llms]
        return board

    def regime_table(self, T: str, track: str, ids: list[str]) -> None:
        H = self.headline
        models = self.models(track, H)
        all_stats = {m: self.stats(track, H, m) for m in models}
        rows, figrows = [], []
        for rg in self.regimes(ids):
            rid = [i for i in ids if self.regime(i) == rg]
            rboot = Bootstrap(self.tasks, rid, self.n_boot, self.seed + 1)
            pooled = [all_stats[m][i] for m in models for i in rid if i in all_stats[m]]
            n_s, n_v = sum(s["n"] for s in pooled), sum(s["n_valid"] for s in pooled)
            pm = metrics(pooled)
            per_model = [metrics([all_stats[m][i] for i in rid if i in all_stats[m]]) for m in models]
            have_valid = [x["f1_valid"] for x in per_model if x["f1_valid"] is not None]
            mean_valid = statistics.fmean(have_valid) if have_valid else None
            mean_all = statistics.fmean(x["f1"] for x in per_model if x["f1"] is not None)
            mean_succ = statistics.fmean(x["success"] for x in per_model if x["success"] is not None)

            def over_models(field):
                return {i: sum(all_stats[m][i][field] for m in models if i in all_stats[m])
                        for i in rid}
            ci_valid = rboot.ci(over_models("f1_valid_sum"), over_models("n_valid"))
            ci_all = rboot.ci(over_models("f1_sum"), over_models("n"))
            k = f"{T}.{H}.regime.{rg}"
            self.put(f"{k}.n_tasks", len(rid))
            self.put(f"{k}.n_structures", rboot.n_clusters)
            self.put(f"{k}.n_samples", n_s)
            self.put(f"{k}.n_valid", n_v)
            self.put(f"{k}.n_models_with_valid", len(have_valid))
            self.put(f"{k}.f1_valid_mean", mean_valid)
            self.put(f"{k}.f1_valid_pooled", pm["f1_valid"])
            self.put(f"{k}.f1_mean", mean_all)
            self.put(f"{k}.f1_pooled", pm["f1"])
            self.put(f"{k}.success_mean", mean_succ)
            if have_valid:
                self.put(f"{k}.f1_valid_model_min", min(have_valid))
                self.put(f"{k}.f1_valid_model_max", max(have_valid))
            rows.append([rg, len(rid), rboot.n_clusters, f"{n_v}/{n_s}",
                         f"{len(have_valid)}/{len(models)}", f3(mean_valid), f3(pm["f1_valid"]),
                         ci_str(ci_valid), f3(mean_all), ci_str(ci_all), pct(mean_succ)])
            figrows.append({"regime": rg, "n_tasks": len(rid), "n_structures": rboot.n_clusters,
                            "n_valid": n_v, "n_samples": n_s, "f1_valid": r4(mean_valid),
                            "f1": r4(mean_all),
                            "f1_valid_models": [r4(x) for x in have_valid],
                            "f1_models": [r4(x["f1"]) for x in per_model]})
        self.tables[f"table_{T}_regimes"] = (
            f"**Scores by regime, `{H}` condition{self.tag}.** *Valid / all*: valid outputs out of "
            "all outputs, pooled over models. *Models*: models with at least one valid output in "
            "the regime (the others cannot contribute to a valid-only mean). *F1 (valid)*: mean "
            "score over valid outputs, first averaged per model and then over models (mean), and "
            "over all valid outputs together (pooled). *Strict F1*: mean over all outputs, invalid "
            "ones scoring 0, averaged per model then over models. *Success*: share of outputs that "
            "are valid and score exactly 1. 95% CIs are for the pooled valid-only and pooled "
            "strict values, resampling whole structures; n/a where a regime has a single "
            "structure. Read the thin rows with care: the sample sizes are in the table.\n\n"
            + md_table(["Regime", "Tasks", "Structures", "Valid / all", "Models",
                        "F1 (valid), mean", "F1 (valid), pooled", "95% CI", "Strict F1", "95% CI",
                        "Success"], rows, "lrrrrrrrrrr"))
        self.fig[f"{T}_regimes"] = figrows

    def conditions(self, T: str, track: str, conds: list[str], ids: list[str],
                   boot: Bootstrap) -> None:
        H, G = self.headline, self.grounded
        rows = []
        for c in conds:
            ms = self.models(track, c)
            if not ms:
                continue
            per = [metrics(list(self.stats(track, c, m).values())) for m in ms]
            n_s = sum(s["n"] for m in ms for s in self.stats(track, c, m).values())
            n_v = sum(s["n_valid"] for m in ms for s in self.stats(track, c, m).values())
            fv = [p["f1_valid"] for p in per if p["f1_valid"] is not None]
            k = f"{T}.cond.{c}"
            self.put(f"{k}.n_models", len(ms))
            self.put(f"{k}.n_samples", n_s)
            self.put(f"{k}.n_valid", n_v)
            self.put(f"{k}.f1_mean", statistics.fmean(p["f1"] for p in per))
            self.put(f"{k}.valid_mean", statistics.fmean(p["valid"] for p in per))
            self.put(f"{k}.f1_valid_mean", statistics.fmean(fv) if fv else None)
            self.put(f"{k}.models", ", ".join(short(m) for m in ms))
            rows.append([f"`{c}`", len(ms), f"{n_v}/{n_s}",
                         f3(statistics.fmean(p["f1"] for p in per)),
                         pct(statistics.fmean(p["valid"] for p in per)),
                         f3(statistics.fmean(fv)) if fv else "n/a (no valid output)"])
        self.tables[f"table_{T}_conditions"] = (
            f"**Prompting conditions{self.tag}.** `spec`: the system prompt contains the frozen "
            "MolViewSpec reference. `bare`: it contains only the output contract (\"answer with "
            "one MolViewSpec JSON scene\"). `_grounded`: the task's frozen grounding pack (facts "
            "about the structure, built offline) is added to the request. Each row is a mean over "
            "the models that ran that condition; the number of models differs by row and is "
            "stated. *Strict F1*, *Valid* and *F1 (valid)* as in the leaderboard table.\n\n"
            + md_table(["Condition", "Models", "Valid / all", "Strict F1", "Valid", "F1 (valid)"],
                       rows, "lrrrrr"))

        # Conditions that never produced a valid scene (the bare rows in October).
        bare = [c for c in conds if c.startswith("bare")]
        if bare:
            bm = sorted({m for c in bare for m in self.models(track, c)})
            n_s = sum(s["n"] for c in bare for m in self.models(track, c)
                      for s in self.stats(track, c, m).values())
            n_v = sum(s["n_valid"] for c in bare for m in self.models(track, c)
                      for s in self.stats(track, c, m).values())
            self.put(f"{T}.bare.n_models", len(bm))
            self.put(f"{T}.bare.models", ", ".join(short(m) for m in bm))
            self.put(f"{T}.bare.n_cells", len(bare))
            self.put(f"{T}.bare.n_samples", n_s)
            self.put(f"{T}.bare.n_valid", n_v)
            oc = Counter(s["outcome"] for c in bare for m in self.models(track, c)
                         for ss in self.cells[(track, c, m)]["tasks"].values() for s in ss)
            self.put(f"{T}.bare.outcomes", ", ".join(
                f"{n} {OUTCOME_LABEL.get(o, o)}" for o, n in oc.most_common()))

        # Grounding packs: three numbers, each with its own denominator.
        both = [m for m in self.models(track, H) if (track, G, m) in self.cells]
        if not both:
            return
        S = {m: self.stats(track, H, m) for m in both}
        Gs = {m: self.stats(track, G, m) for m in both}
        lookup = {i for i in ids if i in self.tasks and self.tasks[i]["lookup"]}

        def task_f1(st, i):
            return st[i]["f1_sum"] / st[i]["n"]

        def mean_delta(picked, subset=None):
            per = []
            for m in both:
                use = [i for i in picked if i in S[m] and i in Gs[m]
                       and (subset is None or i in subset)]
                if use:
                    per.append(statistics.fmean(task_f1(Gs[m], i) - task_f1(S[m], i) for i in use))
            return statistics.fmean(per) if per else None

        def both_valid_pairs(picked, subset=None):
            out = []
            for m in both:
                for i in picked:
                    if subset is not None and i not in subset:
                        continue
                    a, b = S[m].get(i), Gs[m].get(i)
                    if a and b and a["n_valid"] == a["n"] and b["n_valid"] == b["n"]:
                        out.append(task_f1(Gs[m], i) - task_f1(S[m], i))
            return out

        def task_mean_delta(subset=None):
            """Per task: the mean over models of (grounded - plain) task F1."""
            out = {}
            for i in ids:
                if subset is not None and i not in subset:
                    continue
                d = [task_f1(Gs[m], i) - task_f1(S[m], i) for m in both
                     if i in S[m] and i in Gs[m]]
                if d:
                    out[i] = statistics.fmean(d)
            return out

        def pair_sums(subset=None):
            num, den = defaultdict(float), defaultdict(float)
            for m in both:
                for i in ids:
                    if subset is not None and i not in subset:
                        continue
                    a, b = S[m].get(i), Gs[m].get(i)
                    if a and b and a["n_valid"] == a["n"] and b["n_valid"] == b["n"]:
                        num[i] += task_f1(Gs[m], i) - task_f1(S[m], i)
                        den[i] += 1.0
            return dict(num), dict(den)

        k = f"{T}.grounding"
        self.put(f"{k}.n_models", len(both))
        self.put(f"{k}.n_lookup_tasks", len(lookup))
        self.put(f"{k}.lookup_regimes", ", ".join(self.regimes(lookup)))
        results = []
        d_all = mean_delta(ids)
        ci_all = boot.ci(task_mean_delta())
        results.append(("all", "All tasks, all outputs (mean over models)", len(ids), d_all, ci_all))
        d_look = mean_delta(ids, lookup) if lookup else None
        ci_look = boot.ci(task_mean_delta(lookup)) if lookup else None
        results.append(("lookup", "Lookup tasks only, all outputs (mean over models)",
                        len(lookup), d_look, ci_look))
        pairs = both_valid_pairs(ids)
        d_pool = statistics.fmean(pairs) if pairs else None
        ci_pool = boot.ci(*pair_sums())
        results.append(("both_valid", "Task × model pairs valid in both conditions (pooled)",
                        len(pairs), d_pool, ci_pool))
        rows = []
        for tag, label, n, d, ci in results:
            self.put(f"{k}.{tag}.delta", d)
            self.put(f"{k}.{tag}.n", n)
            if ci:
                self.put(f"{k}.{tag}.lo", ci[0])
                self.put(f"{k}.{tag}.hi", ci[1])
            rows.append([label, n, "n/a" if d is None else f"{d:+.3f}",
                         "n/a" if ci is None else f"{ci[0]:+.3f} to {ci[1]:+.3f}"])
        self.put(f"{k}.both_valid.better", sum(x > 0 for x in pairs))
        self.put(f"{k}.both_valid.worse", sum(x < 0 for x in pairs))
        self.put(f"{k}.both_valid.same", sum(x == 0 for x in pairs))
        lp = both_valid_pairs(ids, lookup) if lookup else []
        self.put(f"{k}.lookup.n_both_valid", len(lp))
        self.put(f"{k}.lookup.better", sum(x > 0 for x in lp))
        self.put(f"{k}.lookup.worse", sum(x < 0 for x in lp))
        self.put(f"{k}.lookup.same", sum(x == 0 for x in lp))
        self.put(f"{k}.lookup.delta_both_valid", statistics.fmean(lp) if lp else None)
        # Per model: change on lookup tasks and change in valid-scene rate.
        per_model = []
        for m in both:
            ms, mg = metrics(list(S[m].values())), metrics(list(Gs[m].values()))
            use = [i for i in lookup if i in S[m] and i in Gs[m]]
            dl = statistics.fmean(task_f1(Gs[m], i) - task_f1(S[m], i) for i in use) if use else None
            per_model.append({"model": short(m), "delta": r4(mg["f1"] - ms["f1"]),
                              "delta_lookup": r4(dl), "valid_spec": r4(ms["valid"]),
                              "valid_grounded": r4(mg["valid"]),
                              "delta_valid": r4(mg["valid"] - ms["valid"])})
        self.put(f"{k}.n_models_better", sum(p["delta"] > 0 for p in per_model))
        self.put(f"{k}.n_models_worse", sum(p["delta"] < 0 for p in per_model))
        self.put(f"{k}.n_models_lookup_gain_10", sum((p["delta_lookup"] or 0) >= 0.10
                                                     for p in per_model))
        self.put(f"{k}.n_models_lookup_loss_10", sum((p["delta_lookup"] or 0) <= -0.10
                                                     for p in per_model))
        self.put(f"{k}.valid_delta_mean", statistics.fmean(p["delta_valid"] for p in per_model))
        worst = min(per_model, key=lambda p: p["delta_valid"])
        self.put(f"{k}.valid_drop_max.name", worst["model"])
        self.put(f"{k}.valid_drop_max.from", worst["valid_spec"])
        self.put(f"{k}.valid_drop_max.to", worst["valid_grounded"])
        self.tables[f"table_{T}_grounding"] = (
            f"**Effect of grounding packs{self.tag}.** Change in F1 when the task's frozen "
            f"grounding pack is added to the request (`{G}` minus `{H}`), for the {len(both)} "
            "models that ran both. Three ways to count, because they answer different questions. "
            "Row 1 includes the outputs that became invalid. Row 2 keeps only the "
            f"{len(lookup)} tasks that need a lookup ({', '.join(self.regimes(lookup))}). Row 3 "
            "keeps only task × model pairs whose output was valid in both conditions, so it "
            "isolates the effect on content; of those pairs "
            f"{self.values[f'{k}.both_valid.better']} improved, "
            f"{self.values[f'{k}.both_valid.worse']} got worse and "
            f"{self.values[f'{k}.both_valid.same']} did not change. 95% CI: bootstrap, resampling "
            "whole structures.\n\n"
            + md_table(["Comparison", "n", "Change in F1", "95% CI"], rows, "lrrr"))
        self.fig[f"{T}_grounding"] = sorted(per_model, key=lambda p: p["delta"])

    def failures(self, T: str, track: str) -> None:
        H = self.headline
        models = self.models(track, H)
        tot: Counter = Counter()
        per = {}
        for m in models:
            c = Counter(s["outcome"] for ss in self.cells[(track, H, m)]["tasks"].values()
                        for s in ss)
            per[m] = c
            tot.update(c)
        outs = [o for o in OUTCOME_ORDER if tot[o]] + sorted(set(tot) - set(OUTCOME_ORDER))
        n = sum(tot.values())
        for o in OUTCOME_ORDER:
            self.put(f"{T}.{H}.outcome.{o}", tot[o])
        n_fail = n - tot["valid"]
        self.put(f"{T}.{H}.n_failed", n_fail)
        self.put(f"{T}.{H}.invalid_json_share_of_failures",
                 tot["invalid_json"] / n_fail if n_fail else None)
        order = sorted(models, key=lambda m: (-per[m]["valid"], m))
        rows = [[short(m)] + [per[m][o] for o in outs] for m in order]
        rows.append(["**All models**"] + [tot[o] for o in outs])
        # Concentration: how many models account for most of the invalid output.
        inv = sorted(((sum(c.values()) - c["valid"], m) for m, c in per.items()), reverse=True)
        top3 = sum(x for x, _ in inv[:3])
        self.put(f"{T}.{H}.failures_top3_share", top3 / n_fail if n_fail else None)
        self.put(f"{T}.{H}.failures_top3_models", ", ".join(short(m) for _, m in inv[:3]))
        self.tables[f"table_{T}_outcomes"] = (
            f"**What happened to each output, `{H}` condition{self.tag}.** Every output falls "
            "into exactly one class. *Valid scene*: parses as JSON, Mol\\* accepts it as "
            "MolViewSpec and loads the structure. *Invalid JSON*: no parsable JSON object. "
            "*JSON, not a scene*: valid JSON that is not a MolViewSpec tree. *Scene rejected by "
            "Mol\\**: a tree with a wrong node or parameter. *Structure failed to load*: the "
            "scene is well formed but names a file that does not load. All classes except the "
            "first score 0.\n\n"
            + md_table(["Model"] + [OUTCOME_LABEL.get(o, o) for o in outs], rows))

        # What kind of JSON error: parser message + bracket balance of the raw text.
        msgs: Counter = Counter()
        for m in models:
            cell = self.cells[(track, H, m)]
            for i, ss in cell["tasks"].items():
                if any(s["outcome"] == "invalid_json" for s in ss):
                    e = cell["errors"].get(i, "unknown")
                    e = re.sub(r":? ?line \d+ column \d+ \(char \d+\)", "", e)
                    msgs[e.replace("JSON parse error: ", "").strip()] += 1
        self.tables[f"table_{T}_json_errors"] = (
            f"**Parser messages for the invalid-JSON outputs{self.tag}.** One row per message "
            "from Python's `json` module (position removed), counted over tasks.\n\n"
            + md_table(["Parser message", "Tasks"], [[k, v] for k, v in msgs.most_common()]))
        shapes: Counter = Counter()
        n_raw = 0
        for m in models:
            for i, idx, raw in self.invalid_json_raw(track, H, m):
                n_raw += 1
                text = (raw or "").strip()
                if not text or text in ("[]", "{}"):
                    shapes["empty output"] += 1
                    continue
                d = text.count("{") - text.count("}")
                shapes["too few closing braces" if d > 0 else
                       "too many closing braces" if d < 0 else
                       "braces balance; other syntax error"] += 1
        if n_raw:
            self.put(f"{T}.{H}.json_shape.n_raw", n_raw)
            for name, key in (("empty output", "empty"), ("too few closing braces", "too_few"),
                              ("too many closing braces", "too_many"),
                              ("braces balance; other syntax error", "balanced")):
                self.put(f"{T}.{H}.json_shape.{key}", shapes[name])
            self.put(f"{T}.{H}.json_shape.brace_count_share",
                     (shapes["too few closing braces"] + shapes["too many closing braces"]) / n_raw)
            self.tables[f"table_{T}_json_shapes"] = (
                f"**Shape of the invalid-JSON outputs{self.tag}.** For the {n_raw} invalid-JSON "
                "outputs whose raw text was archived: does the text open and close the same "
                "number of braces? A scene is a deeply nested tree, so a miscount by one brace "
                "is enough to lose the whole answer.\n\n"
                + md_table(["Shape", "Outputs", "Share"],
                           [[k, v, pct(v / n_raw)] for k, v in shapes.most_common()], "lrr"))

    def invalid_json_raw(self, track: str, cond: str, model: str):
        """Yield (task id, sample index, raw text) for invalid-JSON samples with archived text."""
        cell = self.cells[(track, cond, model)]
        f = None
        for key in archive_keys(cell["meta"], [cell["raw_name"]]):
            if key in self.archives:
                f = self.archives[key]
                break
        if f is None:
            return
        if f not in self._archive_cache:
            self._archive_cache[f] = json.loads(f.read_text(encoding="utf-8"))["raw_samples"]
        raws = self._archive_cache[f].get(cell["raw_name"], {})
        for i, ss in cell["tasks"].items():
            for idx, s in enumerate(ss):
                if s["outcome"] != "invalid_json":
                    continue
                arch = raws.get(i) or []
                if idx < len(arch) and "raw" in arch[idx]:
                    yield i, idx, arch[idx]["raw"]

    def semantic_errors(self, T: str, track: str) -> None:
        """For valid scenes that are not perfect: which part of the scene differs."""
        if track != "mvs":
            return
        H = self.headline
        kinds: Counter = Counter()
        by_regime: dict[str, Counter] = defaultdict(Counter)
        n_imperfect = n_valid = 0
        for f in self.score_files:
            card = json.loads(f.read_text(encoding="utf-8"))
            if condition_of(card.get("meta", {})) != H:
                continue
            for name, m in card.get("models", {}).items():
                if m.get("spec") == "baseline" or name.startswith("baseline"):
                    continue
                for row in m.get("tasks", []):
                    if row.get("category", "mvs") != track or row["id"] not in self.tasks:
                        continue
                    samples = row_samples(row)
                    if len(samples) != 1 or samples[0]["outcome"] != "valid":
                        continue  # per-sample trees are not in the scorecard for N > 1
                    n_valid += 1
                    if samples[0]["f1"] >= 1 - SUCCESS_EPS:
                        continue
                    n_imperfect += 1
                    t = self.tasks[row["id"]]
                    found = scene_differences(t["reference_mvs"], row.get("predicted"),
                                              t.get("accepted_ids"))
                    for kd in found:
                        kinds[kd] += 1
                        by_regime[t["regime"]][kd] += 1
                    by_regime[t["regime"]]["_n"] += 1
        if not n_valid:
            return
        self.put(f"{T}.{H}.n_valid_imperfect", n_imperfect)
        self.put(f"{T}.{H}.n_valid_perfect", n_valid - n_imperfect)
        for kd, n in kinds.items():
            self.put(f"{T}.{H}.diff.{kd.replace(' ', '_')}", n)
        regs = [r for r in REGIME_ORDER if r in by_regime] + sorted(set(by_regime) - set(REGIME_ORDER))
        order = [k for k, _ in kinds.most_common()]
        rows = [[kd, kinds[kd], pct(kinds[kd] / n_imperfect)] + [by_regime[r][kd] for r in regs]
                for kd in order]
        rows.append(["*imperfect valid scenes*", n_imperfect, "", *[by_regime[r]["_n"] for r in regs]])
        self.tables[f"table_{T}_differences"] = (
            f"**Where valid scenes lose points, `{H}` condition{self.tag}.** For the "
            f"{n_imperfect} valid scenes that scored below 1 (of {n_valid} valid scenes): which "
            "part of the scene differs from the reference. One scene can differ in several "
            "parts, so the rows add up to more than the total. *Selection*: the right kind of "
            "component, but it picks different atoms. *Unrequested colour*: the output colours "
            "something the reference leaves at the viewer default; the tree score counts this "
            "as a difference even where a reader might not. *Missing* / *extra component*: a part of "
            "the reference scene is absent, or the output draws something the reference does "
            "not. *Structure*: a different entry or file is loaded.\n\n"
            + md_table(["Difference", "Scenes", "Share"] + regs, rows, "lrr" + "r" * len(regs)))

    def repair(self, T: str, track: str, board: list[dict]) -> None:
        """Offline counterfactual: what if invalid JSON were repaired before grading?"""
        if track != "mvs":
            return
        H = self.headline
        k = f"{T}.{H}.repair"
        try:
            import json_repair
        except ImportError:
            self.notes.append("json-repair not installed: repair counterfactual not computed "
                              "(run with `uv run scripts/paper_tables.py`)")
            self.put(f"{k}.computed", False)
            return
        self.put(f"{k}.computed", True)
        rows, fig = [], []
        tot_inv = tot_raw = tot_scene = tot_pos = 0
        all_f1: list[float] = []
        repaired_f1s = []
        for r in [x for x in board if not x["baseline"]]:
            m = r["model"]
            st = self.stats(track, H, m)
            n_inv = sum(s["outcome"] == "invalid_json"
                        for ss in self.cells[(track, H, m)]["tasks"].values() for s in ss)
            gain = defaultdict(float)
            f1s = []
            n_scene = 0
            for i, idx, raw in self.invalid_json_raw(track, H, m):
                t = self.tasks.get(i)
                if not t:
                    continue
                try:
                    obj = json_repair.loads(raw or "")
                except Exception:  # noqa: BLE001  (any repair failure counts as not repaired)
                    obj = None
                f1 = 0.0
                if mvs.extract_root(obj) is not None:
                    n_scene += 1
                    f1 = mvs.grade_mvs(t["reference_mvs"], obj, t.get("accepted_ids"))["f1"]
                f1s.append(f1)
                gain[i] += f1 / st[i]["n"]
            new = (sum(s["f1_sum"] / s["n"] for s in st.values()) + sum(gain.values())) / len(st)
            tot_inv += n_inv
            tot_raw += len(f1s)
            tot_scene += n_scene
            tot_pos += sum(x > 0 for x in f1s)
            all_f1 += f1s
            repaired_f1s.append(new)
            kk = f"{k}.model.{key_name(m)}"
            self.put(f"{kk}.strict", r["f1"])
            self.put(f"{kk}.repaired", new)
            self.put(f"{kk}.n_invalid_json", n_inv)
            self.put(f"{kk}.n_raw", len(f1s))
            rows.append([r["short"], n_inv, len(f1s), n_scene, f3(r["f1"]), f3(new),
                         f"{new - r['f1']:+.3f}"])
            fig.append({"model": r["short"], "strict": r4(r["f1"]), "repaired": r4(new),
                        "n_invalid_json": n_inv, "n_raw": len(f1s)})
        self.put(f"{k}.n_invalid_json", tot_inv)
        self.put(f"{k}.n_raw", tot_raw)
        self.put(f"{k}.n_no_raw", tot_inv - tot_raw)
        self.put(f"{k}.n_scene", tot_scene)
        self.put(f"{k}.n_positive", tot_pos)
        self.put(f"{k}.mean_f1", statistics.fmean(all_f1) if all_f1 else None)
        if repaired_f1s:
            self.put(f"{k}.f1_min", min(repaired_f1s))
            self.put(f"{k}.f1_max", max(repaired_f1s))
            self.put(f"{k}.f1_spread", max(repaired_f1s) - min(repaired_f1s))
        gains = sorted(fig, key=lambda x: x["strict"] - x["repaired"])
        for j, g in enumerate(gains[:3], 1):
            self.put(f"{k}.top{j}.name", g["model"])
            self.put(f"{k}.top{j}.strict", g["strict"])
            self.put(f"{k}.top{j}.repaired", g["repaired"])
        missing = [x["model"] for x in fig if x["n_raw"] < x["n_invalid_json"]]
        self.put(f"{k}.models_missing_raw", ", ".join(missing) if missing else "none")
        self.tables[f"table_{T}_repair"] = (
            f"**Offline JSON-repair counterfactual, `{H}` condition{self.tag}.** Each invalid-JSON "
            "output with archived raw text was passed through the `json-repair` library and "
            "graded again. No model was called. *Strict F1* is the reported score. *Repaired "
            "F1* adds the score of the repaired outputs. The repaired scenes were graded as "
            "trees but **not** checked by Mol\\*, so repaired F1 is an upper bound. Outputs "
            "with no archived raw text stay at 0 (*Raw text* < *Invalid JSON*).\n\n"
            + md_table(["Model", "Invalid JSON", "Raw text", "Repaired to a scene", "Strict F1",
                        "Repaired F1", "Change"], rows))
        self.fig[f"{T}_repair"] = fig

    def escalation(self, T: str, track: str) -> None:
        """Tree F1 vs "validated" F1 (a render-equivalent scene is counted as correct)."""
        H = self.headline
        rows, lifts = [], []
        tot: Counter = Counter()
        for m in self.models(track, H):
            samples = [s for ss in self.cells[(track, H, m)]["tasks"].values() for s in ss]
            if not any(s["decision"] for s in samples):
                continue
            valid = [s for s in samples if s["outcome"] == "valid"]
            c = Counter()
            c["n"] = len(samples)
            c["failed"] = len(samples) - len(valid)
            c["perfect"] = sum(s["decision"] == "correct" for s in valid)
            esc = [s for s in valid if s["tier"] in ("visual", "vlm")]
            c["escalated"] = len(esc)
            c["rescued_pixel"] = sum(s["decision"] == "rendering-equivalent" for s in esc)
            c["rescued_judge"] = sum(s["decision"] == "vlm:same" for s in esc)
            c["different"] = len(esc) - c["rescued_pixel"] - c["rescued_judge"]
            tree = statistics.fmean(s["f1"] for s in samples)
            val = statistics.fmean(1.0 if (s["outcome"] == "valid" and s["decision"] in RESCUED)
                                   else s["f1"] for s in samples)
            lifts.append(val - tree)
            tot.update(c)
            kk = f"{T}.{H}.escalation.model.{key_name(m)}"
            self.put(f"{kk}.tree_f1", tree)
            self.put(f"{kk}.validated_f1", val)
            rows.append((tree, [short(m), f3(tree), f3(val), f"{val - tree:+.3f}", c["escalated"],
                                c["rescued_pixel"], c["rescued_judge"], c["different"]]))
        if not rows:
            return
        k = f"{T}.{H}.escalation"
        for name in ("n", "failed", "perfect", "escalated", "rescued_pixel", "rescued_judge",
                     "different"):
            self.put(f"{k}.{name}", tot[name])
        self.put(f"{k}.rescued", tot["rescued_pixel"] + tot["rescued_judge"])
        self.put(f"{k}.n_models", len(rows))
        self.put(f"{k}.lift_min", min(lifts))
        self.put(f"{k}.lift_max", max(lifts))
        self.put(f"{k}.lift_mean", statistics.fmean(lifts))
        judges = sorted({str(self.cells[(track, H, m)]["meta"].get("judge"))
                         for m in self.models(track, H)
                         if self.cells[(track, H, m)]["meta"].get("judge")})
        self.put(f"{k}.judge", ", ".join(judges) if judges else "none")
        rows.sort(key=lambda x: -x[0])
        self.tables[f"table_{T}_escalation"] = (
            f"**Tree score vs render-checked score, `{H}` condition{self.tag}.** *Tree F1*: the "
            "strict F1 from comparing scene trees. A valid scene that scores below 1 is "
            "*escalated*: it is rendered next to the reference. It is *rescued* (counted as "
            "correct) if the two images are near-identical pixel for pixel, or if the image-pair "
            "judge model calls them the same. *Validated F1* is the tree F1 with rescued scenes "
            "set to 1. Scores are never lowered by escalation.\n\n"
            + md_table(["Model", "Tree F1", "Validated F1", "Change", "Escalated",
                        "Rescued (pixels)", "Rescued (judge)", "Judged different"],
                       [r for _, r in rows]))

    def cost(self, T: str, track: str, board: list[dict]) -> None:
        H = self.headline
        rows = []
        tot_in = tot_out = tot_calls = 0
        tot_cost, n_priced = 0.0, 0
        prices = self.man.get("prices_usd_per_mtok", {})
        llms = [r for r in board if not r["baseline"]]
        info = {}
        for r in llms:
            cell = self.cells[(track, H, r["model"])]
            u = cell["usage"]
            i, o, calls = u.get("input_tokens"), u.get("output_tokens"), u.get("calls")
            cost = cell["cost_usd"]
            src = "recorded"
            if cost is None and r["model"] in prices and i is not None:
                pi, po = prices[r["model"]]
                cost, src = (i * pi + o * po) / 1e6, "manifest price"
            info[r["model"]] = cost
            tot_in += i or 0
            tot_out += o or 0
            tot_calls += calls or 0
            if cost is not None:
                tot_cost += cost
                n_priced += 1
            kk = f"{T}.{H}.cost.model.{key_name(r['model'])}"
            self.put(f"{kk}.usd", cost)
            self.put(f"{kk}.input_tokens", i)
            self.put(f"{kk}.output_tokens", o)
            rows.append([r["short"], r["weights"], f3(r["f1"]),
                         "n/a" if i is None else f"{i:,}", "n/a" if o is None else f"{o:,}",
                         "not recorded" if cost is None else f"${cost:.4f}",
                         "–" if cost is None or not r["n_tasks"] else f"${100 * cost / r['n_samples']:.3f}"])
        k = f"{T}.{H}.cost"
        self.put(f"{k}.input_tokens", tot_in)
        self.put(f"{k}.output_tokens", tot_out)
        self.put(f"{k}.input_mtok", round(tot_in / 1e6, 2))
        self.put(f"{k}.output_mtok", round(tot_out / 1e6, 2))
        self.put(f"{k}.calls", tot_calls)
        self.put(f"{k}.n_priced", n_priced)
        self.put(f"{k}.n_unpriced", len(llms) - n_priced)
        self.put(f"{k}.total_priced_usd", round(tot_cost, 2))
        # Best open-weight vs best closed-weight model, if both are priced.
        for w in ("open", "closed"):
            ms = [r for r in llms if r["weights"] == w]
            if ms:
                b = ms[0]
                self.put(f"{k}.best_{w}.name", b["short"])
                self.put(f"{k}.best_{w}.f1", b["f1"])
                self.put(f"{k}.best_{w}.usd", info[b["model"]])
        bo, bc = self.values.get(f"{k}.best_open.usd"), self.values.get(f"{k}.best_closed.usd")
        if bo and bc:
            self.put(f"{k}.closed_over_open", round(bc / bo, 1))
        self.tables[f"table_{T}_cost"] = (
            f"**Tokens and cost, `{H}` condition{self.tag}.** Tokens are as reported by the "
            "provider for the whole run of the model. Cost is in US dollars at list price on the "
            "day of the run; *not recorded* means no price was stored for that model, not that "
            f"it was free. *Per 100 outputs*: cost divided by the number of outputs, times 100. "
            f"Total for the {n_priced} priced models: ${tot_cost:.2f}.\n\n"
            + md_table(["Model", "Weights", "Strict F1", "Input tokens", "Output tokens", "Cost",
                        "Per 100 outputs"], rows, "llrrrrr"))

    def legacy_api(self) -> None:
        """July API-track scores under the old grader: cited only as the reason for the rebuild."""
        paths = expand(self.man.get("legacy_scorecard", []), self.roots)
        if not paths:
            return
        d = json.loads(paths[0].read_text(encoding="utf-8"))
        llm, mvs_f1, base = {}, {}, None
        n_tasks = set()
        for name, m in d.get("models", {}).items():
            api = (m.get("by_category") or {}).get("api_calling")
            if not api:
                continue
            n_tasks.add(api["n"])
            if m.get("spec") == "baseline":
                base = (name, m)
                continue
            llm[name] = api["mean_f1"]
            if "mvs" in m["by_category"]:
                mvs_f1[name] = m["by_category"]["mvs"]["mean_f1"]
        if not llm or base is None:
            return
        k = "legacy_api"
        bf = base[1]["by_category"]["api_calling"]["mean_f1"]
        self.put(f"{k}.n_tasks", max(n_tasks))
        self.put(f"{k}.n_models", len(llm))
        self.put(f"{k}.baseline_f1", bf)
        self.put(f"{k}.f1_min", min(llm.values()))
        self.put(f"{k}.f1_max", max(llm.values()))
        self.put(f"{k}.f1_median", statistics.median(llm.values()))
        self.put(f"{k}.run", str((d.get("meta", {}).get("api_track") or {}).get("run", ""))[:10])
        self.put(f"{k}.samples", (d.get("meta", {}).get("api_track") or {}).get("samples"))
        common = sorted(set(llm) & set(mvs_f1))
        rr = pearson([llm[m] for m in common], [mvs_f1[m] for m in common])
        self.put(f"{k}.r_api_mvs", round(rr, 2) if rr is not None else None)
        self.put(f"{k}.r_api_mvs_n", len(common))
        # Per task: where does the keyword script match or beat the mean model?
        bt = {t["id"]: t["f1"] for t in base[1]["tasks"] if t.get("category") == "api_calling"}
        per_task = defaultdict(list)
        for name in llm:
            for t in d["models"][name]["tasks"]:
                if t.get("category") == "api_calling":
                    per_task[t["id"]].append(t["f1"])
        self.put(f"{k}.n_tasks_baseline_ge_mean",
                 sum(bt[i] >= statistics.fmean(v) for i, v in per_task.items() if i in bt))
        self.put(f"{k}.n_tasks_llm_mean_ge_095",
                 sum(statistics.fmean(v) >= 0.95 for v in per_task.values()))
        self.put(f"{k}.baseline_n_perfect", sum(v >= 1 - SUCCESS_EPS for v in bt.values()))


def scene_differences(reference, predicted, accepted=None) -> list[str]:
    """Which parts of a valid scene differ from the reference (coarse, for the taxonomy).

    Each reference path (root → … → leaf) is paired with its most similar predicted path,
    as the grader does. A pair that is not identical is labelled by the node kinds whose
    segments differ; unpaired paths are a missing or an extra component.
    """
    ref_root, pred_root = mvs.extract_root(reference), mvs.extract_root(predicted)
    if ref_root is None or pred_root is None:
        return ["other"]
    ref_paths, pred_paths = mvs.flatten_paths(ref_root), mvs.flatten_paths(pred_root)
    if accepted:
        pred_paths = mvs._fold_accepted_refs(ref_paths, pred_paths, set(accepted))
    pairs = sorted(((mvs._path_similarity(r, p), i, j) for i, r in enumerate(ref_paths)
                    for j, p in enumerate(pred_paths)), reverse=True)
    used_r, used_p, found = set(), set(), set()
    label = {"download": "structure", "parse": "structure", "structure": "structure",
             "component": "selection", "representation": "representation", "color": "colour",
             "focus": "camera", "camera": "camera", "primitive": "drawn lines or labels",
             "primitives": "drawn lines or labels", "label": "drawn lines or labels",
             "opacity": "transparency"}
    for s, i, j in pairs:
        if s == 0 or i in used_r or j in used_p:
            continue
        used_r.add(i)
        used_p.add(j)
        if s >= 1 - SUCCESS_EPS:
            continue
        r, p = ref_paths[i], pred_paths[j]
        for n in range(max(len(r), len(p))):
            a = r[n] if n < len(r) else None
            b = p[n] if n < len(p) else None
            if mvs._segment_similarity(a, b) < 1 - SUCCESS_EPS:
                kind = (a or b)[0]
                if kind == "root":
                    continue
                name = label.get(kind, "other")
                if name == "colour":
                    name = ("unrequested colour" if a is None else
                            "missing colour" if b is None else "wrong colour")
                found.add(name)
    if len(used_r) < len(ref_paths):
        found.add("missing component")
    if len(used_p) < len(pred_paths):
        found.add("extra component")
    return sorted(found) or ["other"]


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def write_outputs(p: Paper, out: pathlib.Path, manifest_path: pathlib.Path | None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("table_*.md"):
        old.unlink()
    for name, text in p.tables.items():
        (out / f"{name}.md").write_text(text.rstrip() + "\n", encoding="utf-8")
    (out / "values.json").write_text(
        json.dumps(dict(sorted(p.values.items())), indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (out / "figdata.json").write_text(
        json.dumps({"status": p.status, "label": p.man.get("label"), **p.fig}, indent=1,
                   ensure_ascii=False) + "\n", encoding="utf-8")

    def rel(f) -> str:
        f = pathlib.Path(f)
        for root in p.roots:
            try:
                return str(f.relative_to(root))
            except ValueError:
                continue
        return f.name

    commit = None
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
                                text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    prov = {
        "built_by": "scripts/paper_tables.py",
        "manifest": rel(manifest_path) if manifest_path else None,
        "label": p.man.get("label"), "status": p.status,
        "code_commit": commit,
        "bootstrap": {"replicates": p.n_boot, "seed": p.seed, "cluster": "structure"},
        "n_scorecards": len(p.score_files), "n_archives": len(p.archive_files),
        "scorecards": sorted(rel(f) for f in p.score_files),
        "run_commits": sorted({str(c["meta"].get("git_commit")) for c in p.cells.values()}),
        "cells": sorted(f"{t}/{c}/{m}" for (t, c, m) in p.cells),
        "notes": p.notes,
    }
    (out / "provenance.json").write_text(json.dumps(prov, indent=1) + "\n", encoding="utf-8")


def build(manifest: dict, data_root: pathlib.Path | None = None, n_boot: int = 10000,
          seed: int = 20261112) -> Paper:
    roots = [REPO] + ([pathlib.Path(data_root)] if data_root else [])
    p = Paper(manifest, roots, n_boot, seed)
    p.run()
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST,
                    help="JSON file naming the inputs (default: paper/inputs.json)")
    ap.add_argument("--data-root", type=pathlib.Path, default=None,
                    help="where relative input paths are looked up after the repo itself "
                         "(default: the main git checkout, which holds results/ and runs/)")
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    ap.add_argument("--bootstrap", type=int, default=10000, help="bootstrap replicates")
    ap.add_argument("--seed", type=int, default=20261112)
    args = ap.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    data_root = args.data_root or default_data_root()
    p = build(manifest, data_root, args.bootstrap, args.seed)
    write_outputs(p, args.out, args.manifest.resolve())
    for n in p.notes:
        print(f"note: {n}", file=sys.stderr)
    print(f"wrote {len(p.values)} values and {len(p.tables)} tables to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
