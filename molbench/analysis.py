"""
Every results table of the paper, from the scorecards of one manifest run.

    python scripts/paper_tables.py --from-dry-run            # mock numbers -> paper/generated_mock/
    python scripts/paper_tables.py --from-run results/final-v1 --out paper/generated_final

Input: ``results/<run>/<condition>/<model>.json`` as `molbench.runner.write_scorecards`
writes them (one per model and condition; each task row carries its tier, split, style,
links, cluster and its per-sample summaries), plus the task files for what only the
corpus knows (edit kinds, readings, clinical facts) and ``tests/controls/summary.json``.
Nothing is called and nothing touches the network.

Output: ``table_*.md`` and ``values.json``. When the run was answered by the mock
model (a dry run), every file says so on its first line and ``values.json`` carries
``"status": "MOCK"``: the shapes are final, the numbers are fake.

Conventions, the same in every table:

* **original tasks only** unless a table says otherwise: the 88 paraphrases are extra
  wordings of tasks already counted and enter the paraphrase table alone;
* a task's score is the mean over its samples; **task success** is the share of its
  samples whose final state is exactly right; "all samples" is the share of tasks
  where every sample is;
* a group's value is the mean over its tasks; 95% intervals are a percentile bootstrap
  that resamples whole **structures** (all tasks on one entry are drawn together);
* for paired tests a task counts as solved when **more than half** of its samples are
  exactly right;
* the keyword baseline is listed, and left out of every "panel mean".
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import statistics
from collections import Counter, defaultdict
from typing import Any, Callable, Iterable

from . import difficulty as difficulty_mod
from . import resolve as resolve_mod
from . import tasks as tasks_mod

REPO = pathlib.Path(__file__).resolve().parent.parent
CONTROLS = REPO / "tests" / "controls" / "summary.json"

TRACKS = ("mvs", "api_calling")
TRACK_NAME = {"mvs": "MVS", "api_calling": "API"}
TRACK_KEY = {"mvs": "mvs", "api_calling": "api"}
TIER_NAME = {"translation": "translation", "grounded": "grounded", "interactions": "interactions",
             "resolve": "resolve", "clinical": "clinical", "followup": "follow-up",
             "accept_set": "accept-set", "tool_only": "tool-only"}
BASELINE = "baseline-rules"
HEADLINE = "spec"
MOCK_BANNER = ("> **MOCK DATA.** Dry run answered by the mock model: the table has its final "
               "shape, **every number in it is fake**.")
CLINICAL_SSE = ("clin-sse-helix", "clin-sse-strand")
# Tables that are not results of the run (counted from the task files, or measured on
# the grader's control set): real whatever answered the run, so they carry no mock banner.
NOT_RUN_RESULTS = ("table_corpus", "table_corpus_kinds", "table_corpus_difficulty",
                   "table_controls")
REAL_NOTE = ("*Not a run result: counted from the task files, so these numbers are real "
             "whatever answered the run.*")


def n_samples(n) -> str:
    return f"{n} sample per task" if n == 1 else f"{n} samples per task"


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #
def f3(x) -> str:
    return "–" if x is None else f"{x:.3f}"


def pct(x) -> str:
    return "–" if x is None else f"{100 * x:.1f}%"


def signed(x) -> str:
    return "–" if x is None else f"{x:+.3f}"


def ci(pair, fmt=f3) -> str:
    return "" if not pair or pair[0] is None else f" [{fmt(pair[0])}, {fmt(pair[1])}]"


def with_ci(x, pair, fmt=f3) -> str:
    return fmt(x) + ci(pair, fmt)


def pval(p) -> str:
    if p is None:
        return "–"
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def md_table(header: list[str], rows: list[list], align: str | None = None) -> str:
    align = align or "l" + "r" * (len(header) - 1)
    rule = [":---" if a == "l" else "---:" for a in align]
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(rule) + "|"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def mean(xs: Iterable[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    return statistics.fmean(xs) if xs else None


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def mcnemar_exact(b: int, c: int) -> float | None:
    """Two-sided exact McNemar test on the discordant pairs (``b`` solved on the first
    side only, ``c`` on the second only): the binomial probability, under no
    difference, of a split at least this uneven. None when there are no discordant
    pairs (nothing to test)."""
    n = b + c
    if n == 0:
        return None
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def percentile(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    pos = q * (len(xs) - 1)
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


class Bootstrap:
    """Percentile bootstrap of a mean over tasks, resampling whole clusters."""

    def __init__(self, replicates: int = 2000, seed: int = 20261115):
        self.n = replicates
        self.seed = seed

    def _replicates(self, items: list[tuple[str, float]], label: str) -> list[float]:
        sums: dict[str, float] = defaultdict(float)
        counts: Counter = Counter()
        for cluster, value in items:
            sums[cluster] += value
            counts[cluster] += 1
        keys = sorted(sums)
        s, c, k = [sums[x] for x in keys], [counts[x] for x in keys], len(keys)
        rng = random.Random(f"{self.seed}|{label}")
        out = []
        for _ in range(self.n):
            num = den = 0.0
            for i in rng.choices(range(k), k=k):
                num += s[i]
                den += c[i]
            out.append(num / den)
        return out

    def ci(self, items: list[tuple[str, float]], label: str = "") -> tuple | None:
        """95% interval of the mean of ``items`` = [(cluster, value), ...]. None with
        fewer than two clusters (an interval from one structure would be a point)."""
        if len({c for c, _ in items}) < 2 or not self.n:
            return None
        reps = self._replicates(items, label)
        return (percentile(reps, 0.025), percentile(reps, 0.975))

    def diff_ci(self, a: list[tuple[str, float]], b: list[tuple[str, float]],
                label: str = "") -> tuple | None:
        """95% interval of mean(a) - mean(b) for two groups on *different* clusters
        (public and held-back structures): each side is resampled on its own."""
        if min(len({c for c, _ in a}), len({c for c, _ in b})) < 2 or not self.n:
            return None
        ra, rb = self._replicates(a, label + "|a"), self._replicates(b, label + "|b")
        d = [x - y for x, y in zip(ra, rb)]
        return (percentile(d, 0.025), percentile(d, 0.975))


# --------------------------------------------------------------------------- #
# Loading a run
# --------------------------------------------------------------------------- #
class Run:
    """The scorecards of one manifest run, and the corpus they were run on."""

    def __init__(self, results_dir: pathlib.Path, tasks_dir: pathlib.Path | None = None,
                 extra_tasks: pathlib.Path | None = None):
        self.dir = pathlib.Path(results_dir)
        self.cards: dict[tuple[str, str], dict] = {}     # (condition, model) -> model record
        self.card_meta: dict[tuple[str, str], dict] = {}
        self.samples: dict[str, int] = {}                # condition -> samples per task
        for f in sorted(self.dir.glob("*/*.json")):
            if f.parent.name in ("site", "samples", "paper"):
                continue
            card = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(card.get("models"), dict) or "meta" not in card:
                continue
            cond = card["meta"].get("condition_name") or f.parent.name
            for model, rec in card["models"].items():
                self.cards[(cond, model)] = rec
                self.card_meta[(cond, model)] = card["meta"]
            self.samples[cond] = card.get("samples", 1)
        if not self.cards:
            raise SystemExit(f"no scorecards under {self.dir} (expected <condition>/<model>.json)")
        self.meta = next(iter(self.card_meta.values()))
        self.mock = any(m.get("mock") for m in self.card_meta.values())
        if self.mock and not all(m.get("mock") for m in self.card_meta.values()):
            raise SystemExit(f"{self.dir} mixes mock and real scorecards; refusing to build tables")
        self.validated = all(m.get("validate") for m in self.card_meta.values())
        self.incomplete = sorted(f"{c}/{m}" for (c, m), meta in self.card_meta.items()
                                 if not meta.get("complete", True))
        self.conditions = [c for c in ("spec", "spec_structured", "spec_grounded", "bare")
                           if any(k[0] == c for k in self.cards)]
        self.conditions += sorted({k[0] for k in self.cards} - set(self.conditions))
        corpus = tasks_mod.load_corpus(tasks_dir) if tasks_dir else tasks_mod.load_corpus()
        if extra_tasks:
            corpus = corpus + tasks_mod.load_corpus(extra_tasks, repo=REPO)
        self.tasks = {t["id"]: t for t in corpus}
        self._rows: dict[tuple[str, str], dict[str, dict]] = {}
        order = self.models(HEADLINE) if HEADLINE in self.conditions else []
        rank = {m: -(self.cards[(HEADLINE, m)].get("mean_f1") or 0.0) for m in order}
        self.model_order = sorted(order, key=lambda m: (m == BASELINE, rank[m], m))
        self.model_order += sorted({k[1] for k in self.cards} - set(self.model_order))

    # -- access ----------------------------------------------------------------
    def models(self, cond: str, baseline: bool = True) -> list[str]:
        got = [m for (c, m) in self.cards if c == cond and (baseline or m != BASELINE)]
        order = getattr(self, "model_order", None)
        return sorted(got, key=order.index) if order else got

    def rows(self, cond: str, model: str) -> dict[str, dict]:
        """{task id: task row} of one scorecard. Rows are the runner's per-task entries."""
        key = (cond, model)
        if key not in self._rows:
            rec = self.cards.get(key)
            self._rows[key] = {t["id"]: t for t in rec["tasks"]} if rec else {}
        return self._rows[key]

    def pick(self, cond: str, model: str, test: Callable[[dict], bool] | None = None,
             originals: bool = True) -> list[dict]:
        return [t for t in self.rows(cond, model).values()
                if (not originals or not t.get("paraphrase_of")) and (test is None or test(t))]

    def task(self, row: dict) -> dict | None:
        return self.tasks.get(row["id"])

    def provenance(self, row: dict) -> dict:
        t = self.task(row)
        return difficulty_mod.source_provenance(t) if t else {}

    def weights(self, model: str) -> str:
        rec = next((r for (c, m), r in self.cards.items() if m == model), {})
        if model == BASELINE:
            return "no model"
        return "open" if rec.get("open_weights") else "closed"


def solved(row: dict) -> bool:
    """A task counts as solved (for paired tests) when more than half of its samples
    are exactly right."""
    return row["success"] > 0.5


def samples_of(rows: list[dict]) -> list[dict]:
    return [s for t in rows for s in t.get("samples") or []]


def items(rows: list[dict], field: str = "success") -> list[tuple[str, float]]:
    return [(t["cluster"], float(t[field])) for t in rows if t.get(field) is not None]


def is_track(track: str) -> Callable[[dict], bool]:
    return lambda t: t["category"] == track


# --------------------------------------------------------------------------- #
# The tables
# --------------------------------------------------------------------------- #
class Tables:
    def __init__(self, run: Run, replicates: int = 2000, seed: int = 20261115):
        self.run = run
        self.boot = Bootstrap(replicates, seed)
        self.tables: dict[str, str] = {}
        self.values: dict[str, Any] = {}
        self.notes: list[str] = []

    # -- plumbing ----------------------------------------------------------------
    def put(self, key: str, value) -> None:
        if isinstance(value, float):
            value = round(value, 4)
        self.values[key] = value

    def add(self, name: str, title: str, body: str, caption: str = "") -> None:
        real = name in NOT_RUN_RESULTS
        parts = [MOCK_BANNER, ""] if self.run.mock and not real else []
        parts += [f"**{title}**", "", body]
        if real and self.run.mock:
            caption = (caption + " " if caption else "") + REAL_NOTE
        if caption:
            parts += ["", caption]
        self.tables[name] = "\n".join(parts)

    def panel_values(self, cond: str, test: Callable[[dict], bool], field: str = "success",
                     models: list[str] | None = None) -> list[tuple[str, float]]:
        """One (cluster, value) per task: the task's ``field`` averaged over the panel's
        models (baseline left out). The panel is fixed; structures are what is resampled."""
        models = models or self.run.models(cond, baseline=False)
        acc: dict[str, list[float]] = defaultdict(list)
        cluster: dict[str, str] = {}
        for m in models:
            for t in self.run.pick(cond, m, test):
                if t.get(field) is not None:
                    acc[t["id"]].append(float(t[field]))
                    cluster[t["id"]] = t["cluster"]
        return [(cluster[i], statistics.fmean(v)) for i, v in acc.items()]

    def stat(self, its: list[tuple[str, float]], label: str) -> tuple:
        """(mean, CI) of a list of (cluster, value)."""
        return (mean(v for _, v in its), self.boot.ci(its, label))

    def name(self, model: str) -> str:
        return model + (" (keyword baseline)" if model == BASELINE else "")

    # -- build -------------------------------------------------------------------
    def build(self) -> "Tables":
        r = self.run
        self.put("status", "MOCK" if r.mock else "final")
        self.put("run.name", r.meta.get("run_name"))
        self.put("run.corpus_version", r.meta.get("corpus_version"))
        self.put("run.corpus_sha256", r.meta.get("corpus_sha256"))
        self.put("run.validated_by_molstar", r.validated)
        self.put("run.reasoning_effort", r.meta.get("reasoning_effort"))
        for cond, n in r.samples.items():
            self.put(f"run.samples.{cond}", n)
        if r.incomplete:
            self.notes.append(f"{len(r.incomplete)} scorecard(s) are incomplete (cells not "
                              f"archived yet): {', '.join(r.incomplete[:5])}")
        if not r.validated:
            self.notes.append("Mol* validation did not run: parsed MVS scenes are 'unchecked', "
                              "and the tables count them as shown")
        self.corpus()
        self.panel()
        self.controls()
        if HEADLINE in r.conditions:
            for track in TRACKS:
                if any(r.pick(HEADLINE, m, is_track(track)) for m in r.models(HEADLINE)):
                    self.leaderboard(track)
                    self.validity(track)
                    self.tiers(track)
            self.tier_track()
            self.tracks()
            self.split()
            self.paraphrases()
            self.paired()
            self.followup()
            self.accept_set()
            self.clinical()
            self.difficulty()
        self.resolve_entries()
        self.structured()
        self.grounding()
        self.bare()
        self.cost()
        return self

    # -- corpus (from the task files alone) ---------------------------------------------
    def corpus(self) -> None:
        tasks = list(self.run.tasks.values())
        orig = [t for t in tasks if not t.get("paraphrase_of")]
        para = [t for t in tasks if t.get("paraphrase_of")]
        n = Counter((t["track"], t["tier"], t["split"]) for t in orig)
        npara = Counter((t["track"], t["tier"]) for t in para)
        rows = []
        for tier in tasks_mod.TIERS:
            if not any(k[1] == tier for k in n):
                continue
            row = [TIER_NAME.get(tier, tier)]
            for track in ("mvs", "api"):
                pub, held = n[(track, tier, "public")], n[(track, tier, "heldback")]
                row += [pub or "–", held or "–", pub + held or "–", npara[(track, tier)] or "–"]
            rows.append(row)
        total = ["**all**"]
        for track in ("mvs", "api"):
            pub = sum(v for k, v in n.items() if k[0] == track and k[2] == "public")
            held = sum(v for k, v in n.items() if k[0] == track and k[2] == "heldback")
            total += [f"**{pub}**", f"**{held}**", f"**{pub + held}**",
                      f"**{sum(v for k, v in npara.items() if k[0] == track)}**"]
        rows.append(total)
        structures = {s for t in orig for s in t["structures"]}
        held_structs = {s for t in orig if t["split"] == "heldback" for s in t["structures"]}
        families = {t["family"] for t in orig}
        self.add("table_corpus", "Corpus: original tasks by tier, track and split",
                 md_table(["tier", "MVS public", "MVS held back", "MVS total", "MVS paraphrases",
                           "API public", "API held back", "API total", "API paraphrases"], rows),
                 f"Counted from the task files. {len(orig)} original tasks and {len(para)} "
                 f"paraphrases on {len(structures)} structures ({len(held_structs)} held back), "
                 f"from {len(families)} templates.")
        self.put("corpus.n_task_files", len(tasks))
        self.put("corpus.n_original", len(orig))
        self.put("corpus.n_paraphrases", len(para))
        self.put("corpus.n_structures", len(structures))
        self.put("corpus.n_heldback_structures", len(held_structs))
        self.put("corpus.n_families", len(families))
        for track in ("mvs", "api"):
            mine = [t for t in orig if t["track"] == track]
            self.put(f"corpus.{track}.n", len(mine))
            self.put(f"corpus.{track}.n_heldback", sum(t["split"] == "heldback" for t in mine))
            for tier in tasks_mod.TIERS:
                k = sum(t["tier"] == tier for t in mine)
                if k:
                    self.put(f"corpus.{track}.{tier}.n", k)

        # special kinds
        def count(test) -> list:
            return [sum(test(t) for t in orig if t["track"] == tr) for tr in ("mvs", "api")]
        para_requests = {(t["track"], t["paraphrase_of"]) for t in para}
        acc = [t for t in orig if t["tier"] == "accept_set"]
        kinds = [
            ["twins (same request on both tracks)", *count(lambda t: bool(t.get("twin_of")))],
            ["  of which need an unstated hide toggle on the API side",
             "–", sum(bool(difficulty_mod.normalised(t)["hide_toggle"]) for t in orig)],
            ["follow-up tasks", *count(lambda t: bool(t.get("context")))],
            ["  of which the right answer is no change",
             *count(lambda t: bool(t.get("context")) and t["context"].get("noop"))],
            ["accept-set tasks (several right final states)",
             *count(lambda t: t["tier"] == "accept_set")],
            ["  readings accepted, in all",
             *[sum(len(readings(t)) for t in acc if t["track"] == tr) for tr in ("mvs", "api")]],
            ["other tasks that list equivalent answers",
             *count(lambda t: bool(t.get("accepted")) and t["tier"] != "accept_set")],
            ["requests with three phrasings",
             *[sum(1 for k in para_requests if k[0] == tr) for tr in ("mvs", "api")]],
            ["tasks with a grounding pack", *count(lambda t: bool(t.get("grounding")))],
            ["clinical: answer needs a numbering offset",
             *count(lambda t: t["tier"] == "clinical" and difficulty_mod.normalised(t)["needs_offset"])],
            ["clinical: number in the name is already the right author number",
             *count(lambda t: t["tier"] == "clinical" and difficulty_mod.normalised(t)[
                 "number_in_name_as_author_number_is_right"])],
            ["clinical: helix / strand context tasks",
             *count(lambda t: t["family"] in CLINICAL_SSE)],
        ]
        self.add("table_corpus_kinds", "Corpus: special kinds of task (original tasks)",
                 md_table(["kind", "MVS", "API"], kinds),
                 "Accept-set counts are of the accept-set tier only and count readings, not "
                 "the call forms a reading can be written in.")
        twins = sum(bool(t.get("twin_of")) for t in orig if t["track"] == "mvs")
        self.put("corpus.n_twin_pairs", twins)
        self.put("corpus.n_twin_pairs_hide_toggle",
                 sum(bool(difficulty_mod.normalised(t)["hide_toggle"]) for t in orig))
        self.put("corpus.n_paraphrase_requests",
                 # a twin pair asked in three phrasings is one request, not two
                 len({min(t["paraphrase_of"], self.run.tasks.get(
                     t["paraphrase_of"], {}).get("twin_of") or t["paraphrase_of"]) for t in para}))
        for track in ("mvs", "api"):
            mine = [t for t in orig if t["track"] == track]
            self.put(f"corpus.{track}.followup.n_noop",
                     sum(bool(t.get("context")) and bool(t["context"].get("noop")) for t in mine))
            self.put(f"corpus.{track}.accept_set.n_readings",
                     sum(len(readings(t)) for t in mine if t["tier"] == "accept_set"))

        rows = []
        for key in difficulty_mod.KEYS:
            row = [f"`{key}`"]
            for track in ("mvs", "api"):
                vals = [difficulty_mod.normalised(t)[key] for t in orig if t["track"] == track]
                yes, known = sum(v is True for v in vals), sum(v is not None for v in vals)
                row.append(f"{yes} of {known}" if known else "–")
            rows.append(row + [difficulty_mod.VOCABULARY[key]])
        self.add("table_corpus_difficulty", "Corpus: difficulty facts under one vocabulary",
                 md_table(["key", "MVS", "API", "meaning"], rows, "lrrl"),
                 "\"k of n\": the fact holds in k of the n original tasks whose generator "
                 "records it (`molbench/difficulty.py` maps each generator's own key names).")

    # -- model panel ---------------------------------------------------------------------
    def panel(self) -> None:
        r = self.run
        rows = []
        for m in r.model_order:
            recs = {c: r.cards[(c, m)] for c in r.conditions if (c, m) in r.cards}
            rec = next(iter(recs.values()))
            price = rec.get("price") or {}
            rows.append([self.name(m), f"`{rec.get('spec')}`", r.weights(m),
                         f"{price.get('input')} / {price.get('output')}" if price else "–",
                         price.get("date") or "–", ", ".join(recs)])
        self.add("table_panel", "Model panel",
                 md_table(["model", "route", "weights", "price in / out (USD per million tokens)",
                           "price read on", "conditions run"], rows, "llllll"),
                 "From the run's scorecards (the manifest names each route and price). "
                 f"Reasoning effort sent: {r.meta.get('reasoning_effort') or 'provider-default'}; "
                 "no temperature is sent.")
        self.put("panel.n_models", len([m for m in r.model_order if m != BASELINE]))

    # -- grader control set --------------------------------------------------------------
    def controls(self) -> None:
        if not CONTROLS.exists():
            self.notes.append(f"{CONTROLS} is missing: no grader control table")
            return
        d = json.loads(CONTROLS.read_text(encoding="utf-8"))
        rows = []
        for key, name in (("mvs", "MVS"), ("api", "API")):
            t = d["tracks"].get(key)
            if not t:
                continue
            for who, label in (("grader", "this grader"), ("previous_grader", "previous grader")):
                g = t.get(who)
                if not g:
                    continue
                fp, ff = g["false_pass"], g["false_fail"]
                rows.append([name, label, t["n_controls"], t["n_identical"], t["n_equivalent"],
                             t["n_wrong"], f"{fp['errors']} of {fp['n']} ({pct(fp['rate'])})",
                             f"{ff['errors']} of {ff['n']} ({pct(ff['rate'])})"])
                if who == "grader":
                    self.put(f"controls.{key}.n", t["n_controls"])
                    self.put(f"controls.{key}.false_pass_rate", fp["rate"])
                    self.put(f"controls.{key}.false_fail_rate", ff["rate"])
        # Not a run result: real whatever answered the run, so it carries no mock banner.
        body = md_table(["track", "grader", "controls", "identical", "equivalent", "wrong",
                         "false passes", "false fails"], rows, "llrrrrrr")
        self.tables["table_controls"] = "\n".join([
            "**Grader control set: the grader's own error rate**", "", body, "",
            "From `tests/controls/summary.json` (built by `scripts/grader_controls.py`; these are "
            "measured values, not run results). A false pass is a wrong answer graded as a task "
            "success; a false fail is an identical or equivalent answer graded as not a success."])

    # -- leaderboard ---------------------------------------------------------------------
    def leaderboard(self, track: str) -> None:
        r, T = self.run, TRACK_KEY[track]
        rows, board = [], []
        for m in r.models(HEADLINE):
            got = r.pick(HEADLINE, m, is_track(track))
            if not got:
                continue
            ss = samples_of(got)
            valid = [s for s in ss if s["outcome"] in ("valid", "unchecked")]
            f1, f1ci = self.stat(items(got, "f1"), f"lb|{track}|{m}|f1")
            su, suci = self.stat(items(got, "success"), f"lb|{track}|{m}|su")
            e = {"model": m, "n": len(got), "f1": f1, "success": su,
                 "success_all": mean(float(t["success_all"]) for t in got),
                 "target": mean(t["target_f1"] for t in got),
                 "valid_rate": len(valid) / len(ss), "valid_f1": mean(s["f1"] for s in valid),
                 "repair_f1": mean((s.get("repair") or s)["f1"] for s in ss)}
            board.append(e)
            rows.append([self.name(m), r.weights(m), with_ci(f1, f1ci), with_ci(su, suci),
                         f3(e["success_all"]), f3(e["target"]), pct(e["valid_rate"]),
                         f3(e["valid_f1"]), f3(e["repair_f1"])])
            for k in ("f1", "success", "success_all", "target", "valid_rate", "valid_f1",
                      "repair_f1"):
                self.put(f"{T}.{HEADLINE}.{m}.{k}", e[k])
            self.put(f"{T}.{HEADLINE}.{m}.f1_ci", [round(x, 4) for x in f1ci] if f1ci else None)
            self.put(f"{T}.{HEADLINE}.{m}.success_ci", [round(x, 4) for x in suci] if suci else None)
        n = board[0]["n"] if board else 0
        self.put(f"{T}.n_tasks", n)
        models = [e for e in board if e["model"] != BASELINE]
        if models:
            best = max(models, key=lambda e: e["success"])
            self.put(f"{T}.best_model", best["model"])
            self.put(f"{T}.best_success", best["success"])
            self.put(f"{T}.panel_mean_success", mean(e["success"] for e in models))
            self.put(f"{T}.panel_mean_f1", mean(e["f1"] for e in models))
        self.add(f"table_{T}_leaderboard",
                 f"{TRACK_NAME[track]} track: leaderboard ({n} original tasks, headline condition, "
                 f"{n_samples(r.samples.get(HEADLINE))})",
                 md_table(["model", "weights", "strict F1 [95% CI]", "task success [95% CI]",
                           "success, all samples", "target score", "valid output",
                           "F1 over valid outputs", "F1 after JSON repair"], rows, "llrrrrrrr"),
                 "Strict F1: mean score over all tasks, an output the viewer cannot show scores "
                 "0. Task success: share of samples whose final state is exactly right. Target "
                 "score: the requested atoms alone. Valid output: share of samples that parse "
                 "and that the viewer accepts. F1 after JSON repair: the same samples with "
                 "broken JSON mended offline by `json-repair` (a counterfactual; the strict "
                 "score is never changed). Intervals: bootstrap over structures.")

    def validity(self, track: str) -> None:
        r, T = self.run, TRACK_KEY[track]
        names = (("valid", "invalid_json", "not_mvs", "invalid_mvs") if track == "mvs"
                 else ("valid", "invalid_json", "invalid_api"))
        if track == "mvs" and not r.validated:
            names = ("unchecked",) + names[1:]
        label = {"valid": "valid", "unchecked": "parsed, not checked by Mol*",
                 "invalid_json": "not JSON", "not_mvs": "JSON, not a scene",
                 "invalid_mvs": "rejected by Mol*", "invalid_api": "not a valid call list"}
        rows = []
        for m in r.models(HEADLINE):
            ss = samples_of(r.pick(HEADLINE, m, is_track(track)))
            if not ss:
                continue
            c = Counter(s["outcome"] for s in ss)
            bad = [s for s in ss if s["outcome"] not in ("valid", "unchecked")]
            cut = sum(bool(s.get("truncated")) for s in bad)
            rows.append([self.name(m), len(ss), *[c[o] for o in names], len(bad), cut,
                         len(bad) - cut, sum("repair" in s for s in ss)])
            self.put(f"{T}.{HEADLINE}.{m}.n_samples", len(ss))
            self.put(f"{T}.{HEADLINE}.{m}.n_not_valid", len(bad))
            self.put(f"{T}.{HEADLINE}.{m}.n_truncated_not_valid", cut)
            self.put(f"{T}.{HEADLINE}.{m}.n_malformed", len(bad) - cut)
        self.add(f"table_{T}_validity",
                 f"{TRACK_NAME[track]} track: what came back (samples, headline condition)",
                 md_table(["model", "samples", *[label[o] for o in names], "not valid, in all",
                           "of those: cut off at the token limit", "of those: malformed",
                           "mended by JSON repair"], rows),
                 "A sample is \"cut off\" when the provider reports that it stopped at the token "
                 "limit; that says the limit was too low, not that the model cannot write the "
                 "format. \"Not a valid call list\" samples are still graded.")

    def tiers(self, track: str) -> None:
        r, T = self.run, TRACK_KEY[track]
        tiers = [t for t in tasks_mod.TIERS
                 if any(r.pick(HEADLINE, m, lambda x, t=t: x["category"] == track and x["tier"] == t)
                        for m in r.models(HEADLINE)[:1])]
        rows = []
        for m in r.models(HEADLINE):
            row = [self.name(m)]
            for tier in tiers:
                got = r.pick(HEADLINE, m, lambda x: x["category"] == track and x["tier"] == tier)
                su, suci = self.stat(items(got), f"tier|{track}|{tier}|{m}")
                row.append(with_ci(su, suci))
                self.put(f"{T}.{HEADLINE}.{m}.{tier}.success", su)
                self.put(f"{T}.{HEADLINE}.{m}.{tier}.f1", mean(t["f1"] for t in got))
            rows.append(row)
        n = {tier: len(r.pick(HEADLINE, r.models(HEADLINE)[0],
                              lambda x: x["category"] == track and x["tier"] == tier))
             for tier in tiers}
        self.add(f"table_{T}_tiers",
                 f"{TRACK_NAME[track]} track: task success by tier [95% CI]",
                 md_table(["model"] + [f"{TIER_NAME[t]} (n = {n[t]})" for t in tiers], rows),
                 "Original tasks, headline condition. Intervals: bootstrap over structures.")

    def tier_track(self) -> None:
        r = self.run
        rows = []
        for tier in tasks_mod.TIERS:
            row, seen = [TIER_NAME.get(tier, tier)], False
            for track in TRACKS:
                test = lambda x: x["category"] == track and x["tier"] == tier  # noqa: E731
                su = self.panel_values(HEADLINE, test, "success")
                if not su:
                    row += ["–", "–", "–", "–"]
                    continue
                seen = True
                s, sci = self.stat(su, f"tt|{tier}|{track}|su")
                f, fci = self.stat(self.panel_values(HEADLINE, test, "f1"), f"tt|{tier}|{track}|f1")
                t, _ = self.stat(self.panel_values(HEADLINE, test, "target_f1"), "")
                row += [len(su), with_ci(s, sci), with_ci(f, fci), f3(t)]
                T = TRACK_KEY[track]
                self.put(f"{T}.panel.{tier}.n", len(su))
                self.put(f"{T}.panel.{tier}.success", s)
                self.put(f"{T}.panel.{tier}.success_ci", [round(x, 4) for x in sci] if sci else None)
                self.put(f"{T}.panel.{tier}.f1", f)
                self.put(f"{T}.panel.{tier}.target", t)
            if seen:
                rows.append(row)
        head = ["tier"]
        for track in TRACKS:
            n = TRACK_NAME[track]
            head += [f"{n} tasks", f"{n} task success [95% CI]", f"{n} strict F1 [95% CI]",
                     f"{n} target score"]
        self.add("table_tier_track", "Tier by track: panel mean",
                 md_table(head, rows),
                 f"Each task's value is its mean over the {len(r.models(HEADLINE, False))} models "
                 "of the panel (keyword baseline left out); a cell is the mean over the tier's "
                 "original tasks. Intervals: bootstrap over structures, the panel held fixed.")

    # -- the two tracks, model by model ------------------------------------------------------
    def tracks(self) -> None:
        """Per model: MVS against API (ledger L-032: in October the two were unrelated)."""
        r = self.run
        rows, pts = [], {"success": [], "f1": []}
        for m in r.models(HEADLINE):
            got = {t: r.pick(HEADLINE, m, is_track(t)) for t in TRACKS}
            if not all(got.values()):
                continue
            su = [mean(t["success"] for t in got[t]) for t in TRACKS]
            f1 = [mean(t["f1"] for t in got[t]) for t in TRACKS]
            rows.append([self.name(m), f3(su[0]), f3(su[1]), signed(su[1] - su[0]),
                         f3(f1[0]), f3(f1[1]), signed(f1[1] - f1[0])])
            if m != BASELINE:
                pts["success"].append(su)
                pts["f1"].append(f1)
        if len(pts["success"]) < 3:
            return
        rs = {k: statistics.correlation([a for a, _ in v], [b for _, b in v])
              if len({a for a, _ in v}) > 1 and len({b for _, b in v}) > 1 else None
              for k, v in pts.items()}
        self.put("tracks.r_success", rs["success"])
        self.put("tracks.r_f1", rs["f1"])
        self.put("tracks.n_models", len(pts["success"]))
        self.add("table_tracks", "The two tracks, model by model",
                 md_table(["model", "MVS task success", "API task success", "API − MVS",
                           "MVS strict F1", "API strict F1", "API − MVS"], rows),
                 f"All original tasks of each track (not only twins), headline condition. Over "
                 f"the {len(pts['success'])} models (keyword baseline left out), Pearson r "
                 f"between the two tracks is {f3(rs['success'])} for task success and "
                 f"{f3(rs['f1'])} for strict F1.")

    # -- public vs held back -------------------------------------------------------------
    def split(self) -> None:
        r = self.run
        for track in TRACKS:
            T = TRACK_KEY[track]
            rows = []

            def line(name, pub, held, label):
                p, h = mean(v for _, v in pub), mean(v for _, v in held)
                d = None if p is None or h is None else h - p
                dci = self.boot.diff_ci(held, pub, label)
                return [name, len(pub), f3(p), len(held), f3(h), signed(d) + ci(dci, signed)], d, dci
            for m in r.models(HEADLINE):
                pub = items(r.pick(HEADLINE, m, lambda x: x["category"] == track and x["split"] == "public"))
                held = items(r.pick(HEADLINE, m, lambda x: x["category"] == track and x["split"] == "heldback"))
                if not pub and not held:
                    continue
                row, d, dci = line(self.name(m), pub, held, f"split|{track}|{m}")
                rows.append(row)
                self.put(f"{T}.{HEADLINE}.{m}.heldback_minus_public", d)
            pub = self.panel_values(HEADLINE, lambda x: x["category"] == track and x["split"] == "public")
            held = self.panel_values(HEADLINE, lambda x: x["category"] == track and x["split"] == "heldback")
            if not rows:
                continue
            row, d, dci = line("**panel mean**", pub, held, f"split|{track}|panel")
            rows.append(row)
            self.put(f"{T}.panel.public.success", mean(v for _, v in pub))
            self.put(f"{T}.panel.heldback.success", mean(v for _, v in held))
            self.put(f"{T}.panel.heldback_minus_public", d)
            self.put(f"{T}.panel.heldback_minus_public_ci", [round(x, 4) for x in dci] if dci else None)
            for tier in tasks_mod.TIERS:
                pub = self.panel_values(HEADLINE, lambda x: x["category"] == track and x["tier"] == tier and x["split"] == "public")
                held = self.panel_values(HEADLINE, lambda x: x["category"] == track and x["tier"] == tier and x["split"] == "heldback")
                if pub or held:
                    rows.append(line(f"panel, {TIER_NAME[tier]} tier", pub, held,
                                     f"split|{track}|{tier}")[0])
            self.add(f"table_{T}_split",
                     f"{TRACK_NAME[track]} track: public and held-back tasks (task success)",
                     md_table(["model", "public tasks", "public", "held-back tasks", "held back",
                               "held back − public [95% CI]"], rows),
                     "Held-back tasks come from the same generators on structures no public task "
                     "uses and were not published before the run. The two splits share no "
                     "structure, so each side of the difference is resampled on its own.")

    # -- paraphrases ---------------------------------------------------------------------
    def paraphrase_groups(self, track: str) -> dict[str, dict[str, str]]:
        """{original id: {style: task id}} for the requests with three phrasings."""
        groups: dict[str, dict[str, str]] = {}
        for t in self.run.tasks.values():
            if t.get("paraphrase_of") and t["category"] == track:
                groups.setdefault(t["paraphrase_of"], {"full": t["paraphrase_of"]})[t["style"]] = t["id"]
        return {k: v for k, v in groups.items() if len(v) == 3}

    def paraphrases(self) -> None:
        r = self.run
        styles = ("full", "terse", "indirect")
        for track in TRACKS:
            T = TRACK_KEY[track]
            groups = self.paraphrase_groups(track)
            if not groups:
                continue
            rows, pooled = [], defaultdict(list)
            for m in r.models(HEADLINE):
                all_rows = r.rows(HEADLINE, m)
                per = [[all_rows[g[s]]["success"] for s in styles]
                       for g in groups.values() if all(g[s] in all_rows for s in styles)]
                if not per:
                    continue
                spread = mean(max(p) - min(p) for p in per)
                flips = sum(len({x > 0.5 for x in p}) > 1 for p in per)
                # the noise floor: phrasings whose own samples disagree with each other
                mixed = mean(0.0 < x < 1.0 for p in per for x in p)
                by_style = [mean(p[i] for p in per) for i in range(3)]
                rows.append([self.name(m), len(per), *map(f3, by_style), f3(spread),
                             f"{flips} of {len(per)}", pct(mixed)])
                self.put(f"{T}.{HEADLINE}.{m}.paraphrase_spread", spread)
                if m != BASELINE:
                    pooled["mixed"].append(mixed)
                    pooled["spread"].append(spread)
                    pooled["flips"].append(flips / len(per))
                    for i, s in enumerate(styles):
                        pooled[s].append(by_style[i])
            if not rows:
                continue
            rows.append(["**panel mean**", len(groups), *[f3(mean(pooled[s])) for s in styles],
                         f3(mean(pooled["spread"])), pct(mean(pooled["flips"])),
                         pct(mean(pooled["mixed"]))])
            self.put(f"{T}.panel.paraphrase_samples_disagree", mean(pooled["mixed"]))
            self.put(f"{T}.paraphrase.n_requests", len(groups))
            self.put(f"{T}.panel.paraphrase_spread", mean(pooled["spread"]))
            self.put(f"{T}.panel.paraphrase_flip_rate", mean(pooled["flips"]))
            for s in styles:
                self.put(f"{T}.panel.paraphrase.{s}.success", mean(pooled[s]))
            self.add(f"table_{T}_paraphrase",
                     f"{TRACK_NAME[track]} track: sensitivity to wording ({len(groups)} requests, "
                     "three phrasings each)",
                     md_table(["model", "requests", "full", "terse", "indirect",
                               "mean spread per request", "requests where the outcome flips",
                               "phrasings whose own samples disagree"], rows),
                     "Task success per phrasing. Spread: for each request, the highest minus the "
                     "lowest task success among its three phrasings, then the mean over requests. "
                     "A request flips when it is solved (more than half the samples right) in "
                     "one phrasing and not in another. Sampling noise alone gives a spread above "
                     "0: the last column is the share of single phrasings whose own samples do "
                     "not all agree, the noise the spread has to be read against.")

    # -- twins ---------------------------------------------------------------------------
    def twin_pairs(self) -> list[tuple[str, str, dict]]:
        """(MVS id, API id, MVS task) for every original twin pair in the corpus."""
        out = []
        for t in self.run.tasks.values():
            if t["track"] == "mvs" and t.get("twin_of") and not t.get("paraphrase_of"):
                out.append((t["id"], t["twin_of"], t))
        return sorted(out)

    def paired(self) -> None:
        r = self.run
        pairs = self.twin_pairs()
        if not pairs:
            return
        hide = {a for a, b, _ in pairs
                if difficulty_mod.normalised(r.tasks[b])["hide_toggle"]} if pairs else set()
        sets = [
            ("all", "All twins outside the clinical tier",
             [p for p in pairs if p[2]["tier"] != "clinical"]),
            ("no_hide_toggle", "Sensitivity: without the twins whose API side needs a hide "
             "toggle the request does not state",
             [p for p in pairs if p[2]["tier"] != "clinical" and p[0] not in hide]),
            ("clinical", "Clinical twins (reported apart: the PDBe viewer maps UniProt "
             "numbering itself, an MVS scene cannot)",
             [p for p in pairs if p[2]["tier"] == "clinical"]),
        ]
        blocks = []

        def tally(model: str, chosen) -> Counter:
            rows = r.rows(HEADLINE, model)
            c: Counter = Counter()
            for a, b, _ in chosen:
                if a in rows and b in rows:
                    c[(solved(rows[a]), solved(rows[b]))] += 1
            return c

        def line(name: str, c: Counter) -> list:
            n = sum(c.values())
            both, mvs_only, api_only, neither = c[(True, True)], c[(True, False)], c[(False, True)], c[(False, False)]
            return [name, n, both, mvs_only, api_only, neither,
                    pct((both + mvs_only) / n) if n else "–", pct((both + api_only) / n) if n else "–",
                    pval(mcnemar_exact(mvs_only, api_only))]
        head = ["model", "pairs", "both solved", "MVS only", "API only", "neither",
                "MVS solved", "API solved", "McNemar p (exact)"]
        for key, title, chosen in sets:
            rows, pooled = [], Counter()
            for m in r.models(HEADLINE):
                c = tally(m, chosen)
                if not c:
                    continue
                rows.append(line(self.name(m), c))
                self.put(f"paired.{key}.{m}.mvs_only", c[(True, False)])
                self.put(f"paired.{key}.{m}.api_only", c[(False, True)])
                self.put(f"paired.{key}.{m}.p", mcnemar_exact(c[(True, False)], c[(False, True)]))
                if m != BASELINE:
                    pooled.update(c)
            if not rows:
                continue
            rows.append(line("**pooled over models**", pooled))
            self.put(f"paired.{key}.n_pairs", len(chosen))
            self.put(f"paired.{key}.pooled.mvs_only", pooled[(True, False)])
            self.put(f"paired.{key}.pooled.api_only", pooled[(False, True)])
            self.put(f"paired.{key}.pooled.p", mcnemar_exact(pooled[(True, False)], pooled[(False, True)]))
            blocks.append(f"*{title} ({len(chosen)} pairs).*\n\n" + md_table(head, rows))
        rows = []
        for tier in tasks_mod.TIERS:
            chosen = [p for p in pairs if p[2]["tier"] == tier]
            pooled = Counter()
            for m in r.models(HEADLINE, baseline=False):
                pooled.update(tally(m, chosen))
            if pooled:
                rows.append(line(TIER_NAME[tier], pooled)[:-1] + [len(chosen)] + line("", pooled)[-1:])
        if rows:
            blocks.append("*Pooled over models, by tier.*\n\n" + md_table(
                ["tier", "model × pair", "both solved", "MVS only", "API only", "neither",
                 "MVS solved", "API solved", "pairs", "McNemar p (exact)"], rows))
        self.add("table_paired", "The same request in both formats: paired analysis",
                 "\n\n".join(blocks),
                 "A pair is one request posed on both tracks with the same target atoms. A side "
                 "is solved when more than half of its samples are exactly right. McNemar's "
                 "exact test uses the discordant pairs only (solved on one side and not the "
                 "other). The pooled rows add the counts of all models (keyword baseline left "
                 "out); the same pairs recur across models, so their p value is descriptive.")

    # -- follow-ups ------------------------------------------------------------------------
    def followup(self) -> None:
        r = self.run
        blocks = []
        for track in TRACKS:
            T = TRACK_KEY[track]
            rows = []
            for m in r.models(HEADLINE):
                got = r.pick(HEADLINE, m, lambda x: x["category"] == track and x["tier"] == "followup")
                if not got:
                    continue
                noop = [t for t in got if (r.task(t) or {}).get("context", {}).get("noop")]
                edit = [t for t in got if t not in noop]
                kept = [t for t in got if t.get("preserved_f1") is not None]
                e = {"success": mean(t["success"] for t in got), "f1": mean(t["f1"] for t in got),
                     "target": mean(t["target_f1"] for t in got if t in kept),
                     "preserved": mean(t["preserved_f1"] for t in kept),
                     "preserved_ok": mean(t["preserved_ok"] for t in kept),
                     "noop_success": mean(t["success"] for t in noop),
                     "edit_success": mean(t["success"] for t in edit)}
                rows.append([self.name(m), len(got), f3(e["success"]), f3(e["f1"]), len(kept),
                             f3(e["target"]), f3(e["preserved"]), pct(e["preserved_ok"]),
                             f"{f3(e['edit_success'])} ({len(edit)})",
                             f"{f3(e['noop_success'])} ({len(noop)})"])
                for k, v in e.items():
                    self.put(f"{T}.{HEADLINE}.{m}.followup.{k}", v)
            if rows:
                blocks.append(f"*{TRACK_NAME[track]} track.*\n\n" + md_table(
                    ["model", "tasks", "task success", "strict F1", "tasks with a preserved part",
                     "target score (those tasks)", "preserved score", "everything preserved",
                     "success, edit tasks (n)", "success, no-change tasks (n)"], rows))
        if not blocks:
            return
        self.add("table_followup", "Follow-up turns: the edit made, and what had to stay",
                 "\n\n".join(blocks),
                 "Target score: the atoms the edit request is about, alone. Preserved score: "
                 "the parts of the start state the edit must leave alone, graded the same way "
                 "(mean over the parts; \"everything preserved\" = share of samples where every "
                 "part scores 1). An answer that makes the edit on an empty viewer scores its "
                 "target and loses the preserved score. In a no-change task the start state "
                 "returned unchanged is the right answer.")
        rows = []
        edits: dict[tuple, list] = defaultdict(list)
        for track in TRACKS:
            for m in r.models(HEADLINE, baseline=False):
                for t in r.pick(HEADLINE, m, lambda x: x["category"] == track and x["tier"] == "followup"):
                    kind = self.run.provenance(t).get("edit") or "?"
                    edits[(kind, track)].append(t)
        for kind in sorted({k for k, _ in edits}):
            row = [kind]
            for track in TRACKS:
                got = edits.get((kind, track), [])
                n = len({t["id"] for t in got})
                row += [n or "–", f3(mean(t["success"] for t in got)),
                        f3(mean(t["target_f1"] for t in got)),
                        f3(mean(t.get("preserved_f1") for t in got))]
            rows.append(row)
        head = ["edit"]
        for track in TRACKS:
            n = TRACK_NAME[track]
            head += [f"{n} tasks", f"{n} success", f"{n} target", f"{n} preserved"]
        self.add("table_followup_edits", "Follow-up turns by kind of edit (panel mean)",
                 md_table(head, rows),
                 "\"–\" in a score column: no task of that kind has such a part (an edit that "
                 "removes something has no target on the MVS track; an edit that touches "
                 "everything has nothing to preserve).")

    # -- resolve: which entry -----------------------------------------------------------------
    def resolve_entries(self) -> None:
        r = self.run
        conds = [c for c in ("spec", "spec_grounded") if c in r.conditions]
        rows = []
        for cond in conds:
            pooled: Counter = Counter()
            for m in r.models(cond):
                got = r.pick(cond, m, lambda x: x["tier"] == "resolve")
                ss = [s for s in samples_of(got) if s.get("entry_outcome")]
                if not ss:
                    continue
                c = Counter(s["entry_outcome"] for s in ss)
                rows.append([self.name(m), cond, len(ss),
                             *[pct(c[o] / len(ss)) for o in resolve_mod.ENTRY_OUTCOMES],
                             f3(mean(t["success"] for t in got))])
                for o in resolve_mod.ENTRY_OUTCOMES:
                    self.put(f"mvs.{cond}.{m}.resolve.{o}", c[o] / len(ss))
                if m != BASELINE:
                    pooled.update(c)
            n = sum(pooled.values())
            if n:
                rows.append([f"**all models, {cond}**", cond, n,
                             *[pct(pooled[o] / n) for o in resolve_mod.ENTRY_OUTCOMES], "–"])
                for o in resolve_mod.ENTRY_OUTCOMES:
                    self.put(f"mvs.{cond}.panel.resolve.{o}", pooled[o] / n)
        if not rows:
            return
        self.add("table_resolve_entries",
                 "Resolve tier: which entry the answer loads (share of samples)",
                 md_table(["model", "condition", "samples",
                           *[resolve_mod.ENTRY_OUTCOME_LABEL[o] for o in resolve_mod.ENTRY_OUTCOMES],
                           "task success"], rows, "llrrrrrrr"),
                 "The request names a protein; many entries are right (the frozen accepted "
                 "list). A wrong id is either a real entry of something else or an id that no "
                 f"entry has (the list of current PDB ids frozen on {resolve_mod.pdb_ids_date()}). "
                 "\"No entry loaded\" includes answers that could not be read. Paraphrases "
                 "are left out.")

    # -- accept-set ---------------------------------------------------------------------------
    def accept_set(self) -> None:
        r = self.run
        fam_rows, task_rows = [], []
        for track in TRACKS:
            T = TRACK_KEY[track]
            by_family: dict[str, list[dict]] = defaultdict(list)
            for t in r.tasks.values():
                if t["tier"] == "accept_set" and t["category"] == track and not t.get("paraphrase_of"):
                    by_family[t["family"]].append(t)
            total_right = total_first = 0
            for family, tasks in sorted(by_family.items()):
                chosen: Counter = Counter()        # (task id, reading) -> right samples
                n_samples = n_right = 0
                success = []
                for m in r.models(HEADLINE, baseline=False):
                    rows = r.rows(HEADLINE, m)
                    for t in tasks:
                        row = rows.get(t["id"])
                        if not row:
                            continue
                        success.append(row["success"])
                        names = readings_by_state(t)
                        for s in row.get("samples") or []:
                            n_samples += 1
                            if s["success"]:
                                n_right += 1
                                i = s.get("matched_reference") or 0
                                chosen[(t["id"], names[i] if i < len(names) else "?")] += 1
                if not n_samples:
                    continue
                first = sum(v for (tid, name), v in chosen.items()
                            if name == readings(r.tasks[tid])[0])
                n_readings = sum(len(readings(t)) for t in tasks)
                fam_rows.append([TRACK_NAME[track], f"`{family}`", len(tasks), n_readings,
                                 f3(mean(success)), n_right,
                                 pct(first / n_right) if n_right else "–",
                                 f"{len(chosen)} of {n_readings}"])
                total_right += n_right
                total_first += first
                for t in tasks:
                    for name in readings(t):
                        task_rows.append([TRACK_NAME[track], f"`{t['id']}`", name,
                                          chosen[(t["id"], name)]])
            if total_right:
                self.put(f"{T}.accept_set.right_samples", total_right)
                self.put(f"{T}.accept_set.share_first_reading", total_first / total_right)
        if not fam_rows:
            return
        self.add("table_accept_readings", "Accept-set tier: which reading the right answers took",
                 md_table(["track", "template", "tasks", "readings accepted", "task success",
                           "right samples", "of those, on the first-listed reading",
                           "readings ever chosen"], fam_rows, "llrrrrrr"),
                 "An accept-set request leaves one countable thing open (which of two copies, "
                 "which chain gets which colour) and every reading is accepted. Readings are "
                 "counted, not the call forms a reading can be written in on the API track. "
                 "Pooled over the panel's models, headline condition. The first-listed reading "
                 "is the one the reference draws; a share near 1 / (readings per task) would "
                 "mean no preferred reading.")
        self.add("table_accept_tasks", "Accept-set tier: right samples per reading (supplement)",
                 md_table(["track", "task", "reading", "right samples, all models"], task_rows,
                          "lllr"))

    # -- clinical -----------------------------------------------------------------------------
    def clinical(self) -> None:
        r = self.run
        if not any(t["tier"] == "clinical" for t in r.tasks.values()):
            return
        norm = {i: difficulty_mod.normalised(t) for i, t in r.tasks.items() if t["tier"] == "clinical"}
        fam = {i: t["family"] for i, t in r.tasks.items()}
        strata: list[tuple[str, Callable[[dict], bool]]] = [
            ("all clinical tasks", lambda x: True),
            ("without helix / strand context tasks", lambda x: fam.get(x["id"]) not in CLINICAL_SSE),
            ("helix / strand context tasks only", lambda x: fam.get(x["id"]) in CLINICAL_SSE),
        ]
        for key in difficulty_mod.CLINICAL_STRATA:
            for want, word in ((True, "yes"), (False, "no")):
                strata.append((f"`{key}`: {word}",
                               lambda x, key=key, want=want: fam.get(x["id"]) not in CLINICAL_SSE
                               and norm.get(x["id"], {}).get(key) is want))
        conds = [(HEADLINE, "mvs"), (HEADLINE, "api_calling")]
        if "spec_grounded" in r.conditions:
            conds.insert(1, ("spec_grounded", "mvs"))
        rows = []
        for label, test in strata:
            row = [label]
            for cond, track in conds:
                full = lambda x: x["category"] == track and x["tier"] == "clinical" and test(x)  # noqa: E731
                su = self.panel_values(cond, full)
                s, sci = self.stat(su, f"clin|{label}|{cond}|{track}")
                tg, _ = self.stat(self.panel_values(cond, full, "target_f1"), "")
                row += [len(su) or "–", with_ci(s, sci), f3(tg)]
                slug = label.replace("`", "").replace(": ", ".").replace(" ", "_").replace("/", "")
                self.put(f"clinical.{TRACK_KEY[track]}.{cond}.{slug}.success", s)
                self.put(f"clinical.{TRACK_KEY[track]}.{cond}.{slug}.n", len(su))
            rows.append(row)
        genes: dict[bool, set] = {True: set(), False: set()}
        for i, t in r.tasks.items():
            if (t["tier"] == "clinical" and t["track"] == "mvs" and not t.get("paraphrase_of")
                    and t["family"] not in CLINICAL_SSE and norm[i]["needs_offset"] is not None):
                clin = difficulty_mod.source_provenance(t).get("clinical") or {}
                genes[bool(norm[i]["needs_offset"])].add(clin.get("gene") or t["structures"][0])
        self.put("clinical.needs_offset.yes.n_proteins", len(genes[True]))
        self.put("clinical.needs_offset.no.n_proteins", len(genes[False]))
        self.put("clinical.needs_offset.both.n_proteins", len(genes[True] & genes[False]))
        head = ["stratum"]
        for cond, track in conds:
            name = TRACK_NAME[track] + (", with grounding pack" if cond != HEADLINE else "")
            head += [f"{name}: tasks", f"{name}: task success [95% CI]", f"{name}: target score"]
        self.add("table_clinical_strata", "Clinical tier: results by what the task demands (panel mean)",
                 md_table(head, rows),
                 "The helix / strand context tasks need the entry's own secondary-structure "
                 "annotation, which only the grounding pack states, and are reported apart; the "
                 "strata below them leave those tasks out. `needs_offset`: the residue's author "
                 f"number differs from its UniProt number (yes: {len(genes[True])} proteins, no: "
                 f"{len(genes[False])}, {len(genes[True] & genes[False])} of them on both sides). "
                 "`number_in_name_as_author_number_is_right`: using the number in the variant "
                 "name as the author residue number already gives the right residue, so such a "
                 "task can be solved without any mapping. On the API track the viewer maps "
                 "UniProt numbering itself. Intervals: bootstrap over structures.")

        rows = []
        key = "number_in_name_as_author_number_is_right"
        for m in r.models(HEADLINE):
            row = [self.name(m)]
            for cond, track in conds:
                for want in (True, False):
                    got = r.pick(cond, m, lambda x: x["category"] == track and x["tier"] == "clinical"
                                 and fam.get(x["id"]) not in CLINICAL_SSE
                                 and norm.get(x["id"], {}).get(key) is want)
                    row.append(f3(mean(t["success"] for t in got)))
                    self.put(f"clinical.{TRACK_KEY[track]}.{cond}.{m}.name_number_right_"
                             f"{'yes' if want else 'no'}.success", mean(t["success"] for t in got))
            rows.append(row)
        head = ["model"]
        for cond, track in conds:
            name = TRACK_NAME[track] + (" + pack" if cond != HEADLINE else "")
            head += [f"{name}: name number is right", f"{name}: mapping needed"]
        self.add("table_clinical_models",
                 "Clinical tier: task success when the number in the variant name is already "
                 "the author number, and when a mapping is needed",
                 md_table(head, rows), "Helix / strand context tasks left out.")

        # pairs: the same variant on two structures
        pair_rows = []
        seen = set()
        for t in sorted(r.tasks.values(), key=lambda t: t["id"]):
            if t["tier"] != "clinical" or t.get("paraphrase_of") or t["id"] in seen:
                continue
            clin = t["provenance"].get("clinical") or {}
            pair = clin.get("pair")
            other = r.tasks.get((pair or {}).get("with"))
            if not pair or not other:
                continue
            seen |= {t["id"], other["id"]}
            a, b = sorted([t, other], key=lambda x: bool(difficulty_mod.normalised(x)["needs_offset"]))
            cells = []
            for x in (a, b):
                vals = [r.rows(HEADLINE, m)[x["id"]]["success"]
                        for m in r.models(HEADLINE, baseline=False) if x["id"] in r.rows(HEADLINE, m)]
                cells += [x["structures"][0].upper(),
                          "yes" if difficulty_mod.normalised(x)["needs_offset"] else "no",
                          f3(mean(vals))]
            variant = (clin.get("variants") or [{}])[0].get("variant", "?")
            pair_rows.append([TRACK_NAME[t["category"]], clin.get("gene", "?"), variant, *cells])
        if pair_rows:
            genes = sorted({row[1] for row in pair_rows})
            self.put("clinical.pairs.n", len(pair_rows))
            self.put("clinical.pairs.genes", ", ".join(genes))
            self.add("table_clinical_pairs",
                     "Clinical tier: the same variant on two structures (panel mean task success)",
                     md_table(["track", "gene", "variant", "structure A", "A needs offset",
                               "A success", "structure B", "B needs offset", "B success"],
                              pair_rows, "lllllrllr"),
                     f"Each row is one request asked twice, on two structures of the same protein "
                     f"({', '.join(genes)}). Where the two differ only in whether the author "
                     "numbering equals the UniProt numbering, the gap is the cost of the offset.")

    # -- difficulty keys across tiers -----------------------------------------------------------
    def difficulty(self) -> None:
        r = self.run
        norm = {i: difficulty_mod.normalised(t) for i, t in r.tasks.items()}
        rows = []
        for key in difficulty_mod.KEYS:
            row, seen = [f"`{key}`"], False
            for track in TRACKS:
                for want in (True, False):
                    su = self.panel_values(HEADLINE, lambda x: x["category"] == track
                                           and norm.get(x["id"], {}).get(key) is want)
                    row += [len(su) or "–", f3(mean(v for _, v in su))]
                    seen = seen or (want and bool(su))
                    if su:
                        self.put(f"difficulty.{TRACK_KEY[track]}.{key}."
                                 f"{'yes' if want else 'no'}.success", mean(v for _, v in su))
            if seen:
                rows.append(row)
        head = ["key"]
        for track in TRACKS:
            n = TRACK_NAME[track]
            head += [f"{n}: tasks, yes", f"{n}: success, yes", f"{n}: tasks, no", f"{n}: success, no"]
        self.add("table_difficulty", "Task success by difficulty fact (panel mean, all tiers)",
                 md_table(head, rows),
                 "Original tasks whose generator records the fact. The two groups differ in "
                 "tier mix as well, so read a row as a description, not as the effect of the "
                 "fact; the clinical table holds the tier fixed.")

    # -- conditions -----------------------------------------------------------------------------
    def _paired_condition(self, name: str, cond: str, title: str, caption: str,
                          tests: list[tuple[str, Callable[[dict], bool]]]) -> None:
        r = self.run
        if cond not in r.conditions or HEADLINE not in r.conditions:
            return
        rows = []
        pooled: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for m in r.models(cond):
            base_rows, new_rows = r.rows(HEADLINE, m), r.rows(cond, m)
            for label, test in tests:
                ids = [i for i, t in new_rows.items() if i in base_rows and test(t)
                       and not t.get("paraphrase_of")]
                if not ids:
                    continue
                a, b = [base_rows[i] for i in ids], [new_rows[i] for i in ids]
                sa, sb = samples_of(a), samples_of(b)
                va = mean(s["outcome"] in ("valid", "unchecked") for s in sa)
                vb = mean(s["outcome"] in ("valid", "unchecked") for s in sb)
                d = [(x["cluster"], y["success"] - x["success"]) for x, y in zip(a, b)]
                dm, dci = self.stat(d, f"{name}|{label}|{m}")
                dt = mean(y["target_f1"] - x["target_f1"] for x, y in zip(a, b)
                          if x.get("target_f1") is not None and y.get("target_f1") is not None)
                rows.append([self.name(m), label, len(ids), pct(va), pct(vb),
                             f3(mean(t["f1"] for t in a)), f3(mean(t["f1"] for t in b)),
                             f3(mean(t["success"] for t in a)), f3(mean(t["success"] for t in b)),
                             signed(dm) + ci(dci, signed), signed(dt)])
                slug = label.replace(" ", "_")
                self.put(f"{name}.{slug}.{m}.delta_success", dm)
                self.put(f"{name}.{slug}.{m}.valid_plain", va)
                self.put(f"{name}.{slug}.{m}.valid_with", vb)
                if m != BASELINE:
                    for x, y in zip(a, b):
                        pooled[label][x["id"]].append((x["cluster"], y["success"] - x["success"]))
        if not rows:
            return
        for label, _ in tests:
            per_task = [(v[0][0], statistics.fmean(d for _, d in v)) for v in pooled[label].values()]
            if per_task:
                dm, dci = self.stat(per_task, f"{name}|{label}|panel")
                rows.append(["**panel mean**", label, len(per_task), "", "", "", "", "", "",
                             signed(dm) + ci(dci, signed), ""])
                self.put(f"{name}.{label.replace(' ', '_')}.panel.delta_success", dm)
                self.put(f"{name}.{label.replace(' ', '_')}.panel.delta_success_ci",
                         [round(x, 4) for x in dci] if dci else None)
        self.add(f"table_{name}", title,
                 md_table(["model", "tasks", "n", "valid output, plain", "valid output, with",
                           "strict F1, plain", "strict F1, with", "task success, plain",
                           "task success, with", "Δ task success [95% CI]", "Δ target score"],
                          rows, "llrrrrrrrrr"),
                 caption + f" \"Plain\" is the headline condition "
                 f"({n_samples(r.samples.get(HEADLINE))}); \"with\" has "
                 f"{n_samples(r.samples.get(cond))}. Each "
                 "task's score is its mean over its samples, the same tasks on both sides; "
                 "intervals: bootstrap over structures of the per-task difference.")

    def structured(self) -> None:
        self._paired_condition(
            "structured", "spec_structured",
            "Structured output (the provider's JSON mode) against plain output",
            "The same prompt with JSON mode switched on, for every model whose route has it.",
            [("MVS track", is_track("mvs")), ("API track", is_track("api_calling"))])

    def grounding(self) -> None:
        self._paired_condition(
            "grounding", "spec_grounded",
            "Grounding pack against none, on the lookup tiers",
            "The task's frozen grounding pack appended to the request, on the tiers whose "
            "answer needs a fact from outside the request.",
            [(f"{TIER_NAME[t]} tier", lambda x, t=t: x["tier"] == t) for t in tasks_mod.LOOKUP_TIERS])

    def bare(self) -> None:
        self._paired_condition(
            "bare", "bare", "Bare prompt (output contract only) against the prompt with the reference",
            "The system prompt without the format reference, MVS track.",
            [("MVS track", is_track("mvs"))])

    # -- cost -----------------------------------------------------------------------------------
    def cost(self) -> None:
        r = self.run
        rows, total = [], 0.0
        for m in r.model_order:
            calls = inp = out = reason = 0
            per, known = [], True
            for cond in r.conditions:
                rec = r.cards.get((cond, m))
                if not rec:
                    per.append("–")
                    continue
                u = rec.get("usage") or {}
                calls += u.get("calls", 0)
                inp += u.get("input_tokens", 0)
                out += u.get("output_tokens", 0)
                reason += u.get("reasoning_tokens", 0)
                c = rec.get("cost_usd")
                known = known and c is not None
                per.append("?" if c is None else f"${c:.2f}")
            cost = sum(r.cards[(c, m)].get("cost_usd") or 0.0 for c in r.conditions if (c, m) in r.cards)
            total += cost
            rows.append([self.name(m), f"{calls:,}", f"{inp:,}", f"{out:,}", f"{reason:,}", *per,
                         f"${cost:.2f}" + ("" if known else " (incomplete)")])
            self.put(f"cost.{m}.usd", cost)
            self.put(f"cost.{m}.output_tokens_per_call", out / calls if calls else None)
        self.put("cost.total_usd", total)
        self.add("table_cost", "Calls, tokens and cost of the run",
                 md_table(["model", "calls", "input tokens", "output tokens",
                           "of which reasoning", *r.conditions, "total"], rows),
                 f"Total ${total:.2f}. Cost is what the provider billed for each call where it "
                 "reports that, otherwise tokens times the manifest price. Reasoning tokens are "
                 "counted where the provider reports them.")


# --------------------------------------------------------------------------- #
# Accept-set readings
# --------------------------------------------------------------------------- #
def readings_by_state(task: dict) -> list[str]:
    """The reading each accepted final state belongs to, in the order [reference,
    accepted...]. ``provenance.accepted_states`` names every state; on the API track a
    reading can be written in several call forms, named "<reading>; <call form>", and
    the reading is the part before the semicolon."""
    states = difficulty_mod.source_provenance(task).get("accepted_states") or []
    return [str(s).split(";")[0].strip() for s in states]


def readings(task: dict) -> list[str]:
    """The distinct readings of an accept-set task, the reference's first."""
    out: list[str] = []
    for name in readings_by_state(task):
        if name not in out:
            out.append(name)
    return out


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #
README = """# {title}

{banner}

Built by `scripts/paper_tables.py {flag}` from the scorecards in `{source}`
(run `{run}`, corpus `{corpus}`, {n_cards} scorecards). Rebuild, do not edit.

| file | what |
|---|---|
{files}
| `values.json` | every number above as a flat key → value map; `"status"` says whether it is mock |

{notes}
"""


def write(tables: Tables, out: pathlib.Path, flag: str = "") -> None:
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("table_*.md"):
        old.unlink()
    for name, text in tables.tables.items():
        (out / f"{name}.md").write_text(text.rstrip() + "\n", encoding="utf-8")
    (out / "values.json").write_text(
        json.dumps(dict(sorted(tables.values.items())), indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    run = tables.run
    try:
        source = str(run.dir.resolve().relative_to(REPO))
    except ValueError:
        source = run.dir.name
    titles = {n: t.replace(MOCK_BANNER, "").strip().split("\n")[0].strip("*")
              for n, t in tables.tables.items()}
    (out / "README.md").write_text(README.format(
        title=("MOCK tables: final shapes, fake numbers" if run.mock
               else "Paper tables of the final run"),
        banner=(MOCK_BANNER + "\n\nNothing here may be quoted as a result. The real tables are "
                "written to another directory and never mixed with these." if run.mock else ""),
        flag=flag, source=source, run=run.meta.get("run_name"),
        corpus=f"{run.meta.get('corpus_version')} {str(run.meta.get('corpus_sha256'))[:12]}",
        n_cards=len(run.cards),
        files="\n".join(f"| `{n}.md` | {t} |" for n, t in titles.items()),
        notes="\n".join(f"- {n}" for n in tables.notes)).rstrip() + "\n", encoding="utf-8")


def build(results_dir: pathlib.Path, out: pathlib.Path, replicates: int = 2000,
          seed: int = 20261115, tasks_dir: pathlib.Path | None = None,
          extra_tasks: pathlib.Path | None = None, flag: str = "",
          require_mock: bool | None = None) -> Tables:
    """Build every table from a run's scorecards and write them to ``out``.

    ``require_mock``: True refuses a real run (the mock directory must never hold real
    numbers), False refuses a dry run (and the other way round), None takes either."""
    run = Run(results_dir, tasks_dir, extra_tasks)
    if require_mock is True and not run.mock:
        raise SystemExit(f"{results_dir} is a real run; it is not written among the mock tables")
    if require_mock is False and run.mock:
        raise SystemExit(f"{results_dir} is a dry run (mock model); use --from-dry-run, which "
                         "writes to the mock directory")
    marker = out / "values.json"
    if marker.exists():
        was = json.loads(marker.read_text(encoding="utf-8")).get("status")
        now = "MOCK" if run.mock else "final"
        if was is not None and was != now:
            raise SystemExit(f"{out} holds {was} tables; refusing to overwrite them with {now} "
                             "ones (mock and real numbers are never mixed)")
        if was is None:
            raise SystemExit(f"{out} holds tables of another kind (no status); choose another --out")
    tables = Tables(run, replicates, seed).build()
    write(tables, out, flag)
    return tables
