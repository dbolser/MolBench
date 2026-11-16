#!/usr/bin/env python3
"""
A4: do human raters agree with the benchmark's grader (set a4-v2) and with the VLM
judge (the pilot, set a4-v1)?

Two designs, told apart by the answer key (`design`), never analysed together: a key
and ratings of different sets, or a key that holds items of both designs, are refused.

Design v2 (FINAL_PLAN.md decision 23; plan in paper/a4/FINAL_CALL.md). Raters see the
reference and a model's answer, each whole and zoomed on the target atoms, and give
two answers. Reported:

  * PRIMARY, the grader against people: task success against the whole-scene answer,
    and target score = 1 against the zoomed-view answer. Per rating: raw agreement,
    Cohen's kappa, Gwet's AC1. Per pair (majority of people): sensitivity,
    specificity, and how often people confirm the grader's passes and its fails.
    Unweighted (the set as built) and weighted back to the run. Intervals resample
    tasks; a second interval resamples tasks and raters together.
  * for three groups: independent raters who pass the attention checks (primary),
    everyone but the author, and all raters with the author.
  * what people said for each of the grader's verdicts (right / close / wrong), by tier.
  * people against people (two or more answers per pair) and test-retest (repeats).
  * SECONDARY: the image-pair judge against people, if the key carries its verdicts.

Design v1 (the pilot), as before:

Raters see a reference render and a model's render and answer same / different /
can't tell. This joins their ratings (scripts/export_ratings.py) with the private
answer key (scripts/build_rating_set.py) and reports, offline:

  * per rater: items rated, attention-check results, seconds per item. A rater
    "passes" the checks with at least --min-checks accuracy on EACH kind of check
    (so answering everything "same" can't pass); "can't tell" on a check is a miss.
  * human vs judge, two ways:
      per rating  every human answer against the judge's label (pairs the humans
                  split on still count): raw agreement, Cohen's kappa, Gwet's AC1
      per pair    the judge's "same" as a test of the human majority: sensitivity,
                  specificity, balanced accuracy, and rescue precision (of the pairs
                  the judge calls "same" - the ones it rescues - how many humans
                  also call same)
    each unweighted (the rating set as built) and, with --population, weighted
    back to all judged pairs of the run: the set over-samples the judge's "same"
    calls and caps pairs per task.
  * human vs human on pairs with 2+ answers: raw agreement, Fleiss' kappa,
    Krippendorff's alpha.
  * the same broken down by difficulty tier, by model, and by rater.
  * the two optional flags: which references raters called wrong, and where the
    model's scene looked better - the references to fix before the next run.

Every number has a 95% bootstrap interval that resamples TASKS, because pairs from
one task share a prompt and a reference and are not independent.

Results are given for three groups of raters:
  all            everyone except testing-only tokens
  no_author      the same without the benchmark author's own ratings
  passed_checks  only raters who pass the attention-check rule

"Can't tell" answers count as rated but carry no label.

    python scripts/agreement.py results/a4/a4-v1/key.json results/a4/a4-v1/ratings.json \\
        --population results/a4/a4-v1/population.json \\
        --json paper/a4/tables/agreement.json --markdown paper/a4/tables/agreement.md
    python scripts/agreement.py results/a4/a4-v2/key.json results/a4/a4-v2/ratings.json \\
        --json paper/a4/tables/agreement_v2.json --markdown paper/a4/tables/agreement_v2.md

Never prints the key: output holds counts, task ids and model names, no item ids.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import random
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
LABELS = ("same", "different")
CHECKS = ("control-same", "control-different")
COHORTS = ("all", "no_author", "passed_checks")
MEASURES = ("agreement", "cohen_kappa", "gwet_ac1", "sensitivity", "specificity",
            "balanced_accuracy", "rescue_precision", "npv")
HUMAN = ("agreement", "fleiss_kappa", "krippendorff_alpha")


# --------------------------------------------------------------------------- #
# Agreement statistics
# --------------------------------------------------------------------------- #
def fleiss_kappa(counts: list[collections.Counter]) -> float | None:
    """Fleiss' kappa with a varying number of raters per item (each item needs >= 2)."""
    counts = [c for c in counts if sum(c.values()) >= 2]
    if not counts:
        return None
    p_items = [sum(v * (v - 1) for v in c.values()) / (sum(c.values()) * (sum(c.values()) - 1))
               for c in counts]
    total = sum(sum(c.values()) for c in counts)
    p_cat = [sum(c[lab] for c in counts) / total for lab in LABELS]
    p_bar, p_e = sum(p_items) / len(p_items), sum(p * p for p in p_cat)
    return None if p_e == 1 else (p_bar - p_e) / (1 - p_e)


def krippendorff_alpha(counts: list[collections.Counter]) -> float | None:
    """Krippendorff's alpha, nominal labels, any number of raters per item (>= 2 to count)."""
    counts = [c for c in counts if sum(c.values()) >= 2]
    n_c = collections.Counter()
    disagree = 0.0  # off-diagonal mass of the coincidence matrix
    for c in counts:
        m = sum(c.values())
        n_c.update(c)
        disagree += sum(c[a] * c[b] for a in c for b in c if a != b) / (m - 1)
    n = sum(n_c.values())
    expected = sum(n_c[a] * n_c[b] for a in n_c for b in n_c if a != b)
    if n < 2 or expected == 0:
        return None
    return 1 - (n - 1) * disagree / expected


def pairwise_agreement(counts: list[collections.Counter]) -> float | None:
    """Share of rater pairs, within an item, that give the same label (items weigh equally)."""
    counts = [c for c in counts if sum(c.values()) >= 2]
    if not counts:
        return None
    return statistics.fmean(sum(v * (v - 1) for v in c.values()) / (sum(c.values()) * (sum(c.values()) - 1))
                            for c in counts)


def human_measures(counts: list[collections.Counter]) -> dict:
    return {"agreement": pairwise_agreement(counts), "fleiss_kappa": fleiss_kappa(counts),
            "krippendorff_alpha": krippendorff_alpha(counts)}


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    return judge_measures([(h, j, 1.0) for h, j in pairs])["cohen_kappa"] if pairs else None


def _div(a: float, b: float) -> float | None:
    return a / b if b else None


def judge_measures(recs: list[tuple[str, str, float]]) -> dict:
    """Agreement of (human label, judge label, weight) records, as a weighted 2x2 table.

    The judge's "same" is the positive call; the human label is taken as the truth.
    """
    t = collections.Counter()
    for h, j, w in recs:
        t[h, j] += w
    a, b, c, d = t["same", "same"], t["same", "different"], t["different", "same"], t["different", "different"]
    n = a + b + c + d
    if not n:
        return dict.fromkeys(MEASURES)
    p_o, h_same, j_same = (a + d) / n, (a + b) / n, (a + c) / n
    p_e = h_same * j_same + (1 - h_same) * (1 - j_same)  # Cohen: each side's own base rate
    pi = (h_same + j_same) / 2
    p_e1 = 2 * pi * (1 - pi)                              # Gwet: at most 0.5, so robust to prevalence
    sens, spec = _div(a, a + b), _div(d, c + d)
    return {
        "agreement": p_o,
        "cohen_kappa": None if p_e == 1 else (p_o - p_e) / (1 - p_e),
        "gwet_ac1": (p_o - p_e1) / (1 - p_e1),
        "sensitivity": sens,                  # humans say same -> judge says same
        "specificity": spec,                  # humans say different -> judge says different
        "balanced_accuracy": None if sens is None or spec is None else (sens + spec) / 2,
        "rescue_precision": _div(a, a + c),   # judge says same -> humans say same
        "npv": _div(d, b + d),                # judge says different -> humans say different
    }


def bootstrap(clusters: dict[str, list], stat, reps: int, seed: int) -> dict:
    """Point estimate, 95% percentile interval and SE of each number `stat` returns.

    `clusters` maps a task to its records; whole tasks are resampled with replacement.
    Replicates where a number is undefined (e.g. no "same" calls drawn) are skipped;
    `lo`/`hi` are None if fewer than half the replicates are defined.
    """
    names = sorted(clusters)
    est = stat([r for n in names for r in clusters[n]])
    rng = random.Random(seed)
    draws = collections.defaultdict(list)
    for _ in range(reps if names else 0):
        sample = stat([r for n in rng.choices(names, k=len(names)) for r in clusters[n]])
        for k, v in sample.items():
            if v is not None:
                draws[k].append(v)
    out = {}
    for k, v in est.items():
        xs = sorted(draws[k])
        ok = v is not None and len(xs) >= max(2, reps / 2)
        out[k] = {"est": v,
                  "lo": xs[int(0.025 * (len(xs) - 1))] if ok else None,
                  "hi": xs[round(0.975 * (len(xs) - 1))] if ok else None,
                  "se": statistics.stdev(xs) if ok else None}
    return out


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
def load_ratings(data) -> tuple[list[dict], dict, str | None]:
    """(rows, rater roles, export time) from an export file, or from a bare list of rows.

    A bare list is the older format, one row per rating with `evaluator_token`; every
    rater then has the role "rater" and is named by the first 8 characters of the token.
    """
    if isinstance(data, dict):
        return data["rows"], {p: v.get("role", "rater") for p, v in data["raters"].items()}, data.get("exported_at")
    rows = [{**r, "rater": r["rater"] if "rater" in r else r["evaluator_token"][:8]} for r in data]
    return rows, {r["rater"]: "rater" for r in rows}, None


def task_tiers(key_items: dict) -> dict[str, str]:
    """Task id -> difficulty tier: the key's own `tier` if it has one, else the task's regime."""
    tiers = {v["task"]: v["tier"] for v in key_items.values() if v.get("tier")}
    missing = {v["task"] for v in key_items.values() if "task" in v} - set(tiers)
    if missing:
        sys.path.insert(0, str(REPO / "scripts"))
        from build_leaderboard import _regime_of  # the one place sources map to regimes
        sys.path.insert(0, str(REPO))
        from molbench import tasks as tasks_mod
        for task in tasks_mod.load_corpus():
            if task["id"] in missing:  # a new-format task states its tier; an old one has a source
                tiers[task["id"]] = (_regime_of(task.get("source") or "curated")
                                     if task.get("_legacy") else task["tier"])
    return tiers


def item_weights(rated: dict[str, dict], population: dict | None) -> dict[str, float] | None:
    """Weight per rated judged pair, so the rated pairs stand for every judged pair of the run.

    Each pair first gets N/n for its (task, judge label) cell: N pairs in the run, n of
    them rated. Cells of the run with no rated pair are covered by scaling the weights so
    that each judge label adds up to its total in the run.
    """
    if not population:
        return None
    big = collections.Counter({(t, lab): n for t, lab, n in population["cells"]})
    small = collections.Counter((it["task"], it["vlm_label"]) for it in rated.values())
    w = {i: big.get((it["task"], it["vlm_label"]), small[it["task"], it["vlm_label"]])
            / small[it["task"], it["vlm_label"]] for i, it in rated.items()}
    for lab in LABELS:
        ids = [i for i, it in rated.items() if it["vlm_label"] == lab]
        total = sum(n for (_, lb), n in big.items() if lb == lab)
        if ids and total:
            scale = total / sum(w[i] for i in ids)
            for i in ids:
                w[i] *= scale
    return w


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def rater_summary(rows: list[dict], items: dict, min_checks: float) -> dict:
    """Counts and attention-check results for one rater's rows (all on items in the key)."""
    checks = {}
    for kind in CHECKS:
        rs = [r for r in rows if items[r["item"]]["kind"] == kind]
        right = sum(r["label"] == items[r["item"]]["expected"] for r in rs)
        unsure = sum(r["label"] == "unsure" for r in rs)
        checks[kind] = {"n": len(rs), "right": right, "unsure": unsure, "wrong": len(rs) - right - unsure,
                        "accuracy": right / len(rs) if rs else None}
    judged = [r for r in rows if items[r["item"]]["kind"] == "vlm"]
    ms = [r["ms"] for r in rows if r.get("ms")]
    return {
        "rated": len(rows), "judged_pairs": len(judged),
        "cant_tell": sum(r["label"] == "unsure" for r in judged),
        "checks": checks,
        # Each kind must pass on its own, so lopsided luck can't carry a one-answer rater.
        "passed_checks": all(c["accuracy"] is not None and c["accuracy"] >= min_checks for c in checks.values()),
        "median_seconds": round(statistics.median(ms) / 1000, 1) if ms else None,
    }


def _judge_block(per_rating: dict, per_pair: dict, reps: int, seed: int) -> dict:
    """Per-rating and per-pair agreement with the judge, from records clustered by task."""
    flat = [r for rs in per_rating.values() for r in rs]
    pairs = [r for rs in per_pair.values() for r in rs]
    return {
        "ratings": len(flat), "pairs": len(pairs),
        "table": {f"human {h} / judge {j}": round(sum(w for a, b, w in flat if (a, b) == (h, j)), 2)
                  for h in LABELS for j in LABELS},
        "per_rating": {k: v for k, v in bootstrap(per_rating, judge_measures, reps, seed).items()
                       if k in ("agreement", "cohen_kappa", "gwet_ac1", "rescue_precision", "npv")},
        "per_pair": bootstrap(per_pair, judge_measures, reps, seed),
    }


def cohort(rows: list[dict], items: dict, tiers: dict, population: dict | None,
           reps: int, seed: int) -> dict:
    """Everything about one group of raters' answers on the judged pairs."""
    votes = collections.defaultdict(collections.Counter)   # item -> labelled answers
    by_rater = collections.defaultdict(dict)                # rater -> item -> label
    cant_tell = 0
    for r in rows:
        if items[r["item"]]["kind"] != "vlm":
            continue
        if r["label"] in LABELS:
            votes[r["item"]][r["label"]] += 1
            by_rater[r["rater"]][r["item"]] = r["label"]
        else:
            cant_tell += 1
    rated = {i: items[i] for i in votes}
    weights = item_weights(rated, population)

    def records(ids, weight: dict | None, only: dict | None = None):
        """(per-rating, per-pair) records by task. `only`: one rater's item -> label."""
        per_rating, per_pair = collections.defaultdict(list), collections.defaultdict(list)
        for i in ids:
            it, w = items[i], (weight[i] if weight is not None else 1.0)
            c = collections.Counter([only[i]]) if only else votes[i]
            k = sum(c.values())
            # Weighted: a pair counts once however many people rated it. Unweighted: every rating counts.
            per_rating[it["task"]] += [(lab, it["vlm_label"], w / k if weight is not None else 1.0) for lab in c.elements()]
            if c["same"] != c["different"]:  # a tied pair has no majority
                per_pair[it["task"]].append((max(c, key=c.get), it["vlm_label"], w))
        return per_rating, per_pair

    out = {
        "raters": sorted(by_rater),
        "judged_ratings": sum(sum(c.values()) for c in votes.values()) + cant_tell,
        "cant_tell": cant_tell,
        "pairs_rated": len(votes), "tasks": len({it["task"] for it in rated.values()}),
        "pairs_by_n_raters": dict(sorted(collections.Counter(sum(c.values()) for c in votes.values()).items())),
        "pairs_tied": sum(c["same"] == c["different"] for c in votes.values()),
        "human_same_share": _div(sum(c["same"] for c in votes.values()), sum(sum(c.values()) for c in votes.values())),
        "judge_same_share": _div(sum(it["vlm_label"] == "same" for it in rated.values()), len(rated)),
        "unweighted": _judge_block(*records(votes, None), reps, seed),
        # `is not None`: a group with no labelled answers still gets an (empty) weighted block.
        "weighted": _judge_block(*records(votes, weights), reps, seed) if weights is not None else None,
    }
    # The same bootstrap resampling pairs instead of tasks: the ratio of the two SEs says
    # how much the grouping by task costs (used by the power analysis).
    by_item = {i: [(lab, items[i]["vlm_label"], 1.0) for lab in c.elements()] for i, c in votes.items()}
    se_item = bootstrap(by_item, judge_measures, reps, seed)["cohen_kappa"]["se"]
    se_task = out["unweighted"]["per_rating"]["cohen_kappa"]["se"]
    out["kappa_se_by_task_over_by_pair"] = round(se_task / se_item, 3) if se_task and se_item else None

    multi = collections.defaultdict(list)
    for i, c in votes.items():
        if sum(c.values()) >= 2:
            multi[items[i]["task"]].append(c)
    out["human_vs_human"] = {
        "pairs": sum(len(v) for v in multi.values()), "tasks": len(multi),
        "pairs_split": sum(len(c) > 1 for v in multi.values() for c in v),
        **bootstrap(multi, human_measures, reps, seed),
    }

    def breakdown(group_of) -> dict:
        groups = collections.defaultdict(list)
        for i in votes:
            groups[group_of(items[i])].append(i)
        res = {}
        for g, ids in sorted(groups.items()):
            per_rating, _ = records(ids, None)
            b = bootstrap(per_rating, judge_measures, reps, seed)
            res[g] = {"pairs": len(ids), "tasks": len(per_rating),
                      "ratings": sum(len(v) for v in per_rating.values()),
                      "judge_same_ratings": sum(j == "same" for v in per_rating.values() for _, j, _ in v),
                      **{k: b[k] for k in ("agreement", "cohen_kappa", "rescue_precision")}}
        return res

    out["by_tier"] = breakdown(lambda it: tiers.get(it["task"], "unknown"))
    out["by_model"] = breakdown(lambda it: it["model"].split("/")[-1])
    out["by_rater"] = {}
    for p in sorted(by_rater):
        per_rating, _ = records(by_rater[p], None, only=by_rater[p])
        b = bootstrap(per_rating, judge_measures, reps, seed)
        out["by_rater"][p] = {"ratings": len(by_rater[p]),
                              "judge_same_ratings": sum(items[i]["vlm_label"] == "same" for i in by_rater[p]),
                              "human_same_share": _div(sum(v == "same" for v in by_rater[p].values()), len(by_rater[p])),
                              **{k: b[k] for k in ("agreement", "cohen_kappa", "gwet_ac1", "rescue_precision", "npv")}}
    return out


def flags(rows: list[dict], items: dict) -> dict:
    """What the two optional flags and the free-text notes say, per task.

    Distinct raters: one rater sees a task's reference once per model, but counts once.
    """
    tasks = collections.defaultdict(lambda: {"ref_wrong": set(), "model_better": collections.defaultdict(set),
                                            "notes": [], "ratings": 0, "raters": set()})
    better = collections.Counter()
    for r in rows:
        it = items[r["item"]]
        t = tasks[it["task"]]
        t["ratings"] += 1
        t["raters"].add(r["rater"])
        if r.get("ref_wrong") is True:
            t["ref_wrong"].add(r["rater"])
        if r.get("model_better") is True and it.get("model"):
            t["model_better"][it["model"].split("/")[-1]].add(r["rater"])
            better[f"human {r['label']} / judge {it.get('vlm_label', 'n/a')}"] += 1
        if (r.get("note") or "").strip():
            t["notes"].append({"rater": r["rater"], "answer": r["label"], "kind": it["kind"],
                               "model": (it.get("model") or "").split("/")[-1] or None,
                               "note": " ".join(r["note"].split())})
    per_task = {}
    for name, t in sorted(tasks.items()):
        if t["ref_wrong"] or t["model_better"] or t["notes"]:
            per_task[name] = {
                "ratings": t["ratings"], "raters": len(t["raters"]),
                "ref_wrong": sorted(t["ref_wrong"]),
                "model_better": {m: sorted(v) for m, v in sorted(t["model_better"].items())},
                "model_better_raters": sorted(set().union(*t["model_better"].values())) if t["model_better"] else [],
                "notes": t["notes"]}
    return {"ref_wrong_ratings": sum(r.get("ref_wrong") is True for r in rows),
            "model_better_ratings": sum(r.get("model_better") is True for r in rows),
            "model_better_by_answer": dict(sorted(better.items())),
            "tasks": per_task}


def analyse(key: dict, ratings, min_checks: float = 0.8, population: dict | None = None,
            reps: int = 2000, seed: int = 4) -> dict:
    if design_of(key) == "v2":   # a different instrument: its own analysis, never pooled with v1
        return analyse_v2(key, ratings, population, reps, seed)
    if isinstance(ratings, dict) and ratings.get("set") not in (None, key["set"]):
        raise ValueError(f"the key is of set {key['set']} but the ratings are of set {ratings['set']}: "
                         "ratings of different sets or designs are never analysed together")
    items = key["items"]
    rows, roles, exported_at = load_ratings(ratings)
    seen = collections.Counter((r["rater"], r["item"]) for r in rows)
    if dup := [p for p, n in seen.items() if n > 1]:
        raise ValueError(f"{len(dup)} rater-item pairs rated more than once, e.g. by {dup[0][0]}")
    for r in rows:
        if r["label"] not in (*LABELS, "unsure"):  # a typo must not pass as "can't tell"
            raise ValueError(f"label must be same, different or unsure, got {r['label']!r}")
        for f in ("ref_wrong", "model_better"):
            if r.get(f) not in (None, True, False):  # "false" from a CSV would read as true
                raise ValueError(f"{f} must be a boolean, got {r[f]!r}")

    test = [r for r in rows if roles.get(r["rater"]) == "test"]
    real = [r for r in rows if roles.get(r["rater"]) != "test"]
    orphans = [r for r in real if r["item"] not in items]  # items no longer in the set
    real = [r for r in real if r["item"] in items]

    by_rater = collections.defaultdict(list)
    for r in real:
        by_rater[r["rater"]].append(r)
    raters = {p: {"role": roles.get(p, "rater"), **rater_summary(rs, items, min_checks)}
              for p, rs in sorted(by_rater.items())}
    members = {
        "all": set(raters),
        "no_author": {p for p, v in raters.items() if v["role"] != "author"},
        "passed_checks": {p for p, v in raters.items() if v["passed_checks"]},
    }
    tiers = task_tiers(items)
    judged = [v for v in items.values() if v["kind"] == "vlm"]
    return {
        "set": key["set"], "exported_at": exported_at, "min_checks": min_checks,
        "bootstrap": {"reps": reps, "seed": seed, "unit": "task"},
        "ratings": {"exported": len(rows), "from_test_tokens": len(test),
                    "on_items_not_in_set": dict(sorted(collections.Counter(r["rater"] for r in orphans).items())),
                    "analysed": len(real)},
        "rating_set": {
            "items": len(items), "judged_pairs": len(judged), "tasks": len({v["task"] for v in judged}),
            "judge_same": sum(v["vlm_label"] == "same" for v in judged),
            "judge_different": sum(v["vlm_label"] == "different" for v in judged),
            "checks": {k: sum(v["kind"] == k for v in items.values()) for k in CHECKS},
            "ratings_per_item": dict(sorted(collections.Counter(
                sum(r["item"] == i for r in real) for i in items).items())),
        },
        "population": None if not population else {
            "frame": population.get("frame"),
            **{lab: sum(n for _, lb, n in population["cells"] if lb == lab) for lab in LABELS},
            "tasks": len({t for t, _, _ in population["cells"]})},
        "raters": raters,
        "cohorts": {name: cohort([r for r in real if r["rater"] in members[name]], items, tiers,
                                 population, reps, seed) for name in COHORTS},
        "flags": flags(real, items),
    }


# --------------------------------------------------------------------------- #
# Markdown tables
# --------------------------------------------------------------------------- #
def _ci(x: dict | None, digits: int = 2) -> str:
    if not x or x["est"] is None:
        return "n/a"
    f = lambda v: f"{round(v, digits) + 0.0:.{digits}f}"  # + 0.0: never print "-0.00"
    # An interval of zero width is the bootstrap running out of data (every resample
    # gives the same number), not certainty: show it as no interval.
    if x["lo"] is None or x["lo"] == x["hi"]:
        return f"{f(x['est'])} (no interval)"
    return f"{f(x['est'])} ({f(x['lo'])} to {f(x['hi'])})"


def markdown(res: dict) -> str:
    c = res["cohorts"]
    names = {"all": "all raters", "no_author": "without the author", "passed_checks": "passed-checks only"}
    L = [f"<!-- generated by scripts/agreement.py from the {res['set']} export of {res['exported_at']}; do not edit -->",
         "", f"# Rating study {res['set']}: tables", "",
         "Every interval is a 95% bootstrap interval that resamples tasks "
         f"({res['bootstrap']['reps']} replicates). Raters are pseudonyms. \"No interval\" means too few "
         "ratings for the bootstrap to give one; such a number is an anecdote.", ""]
    rs, n = res["rating_set"], res["ratings"]
    L += ["## The data", "",
          f"- Rating set: {rs['items']} items = {rs['judged_pairs']} judged pairs "
          f"({rs['judge_same']} the judge calls same, {rs['judge_different']} different; {rs['tasks']} tasks) "
          f"+ {rs['checks']['control-same']} known-same and {rs['checks']['control-different']} known-different checks.",
          f"- Ratings exported: {n['exported']}. From testing-only tokens: {n['from_test_tokens']}. "
          f"On items no longer in the set: {sum(n['on_items_not_in_set'].values())} "
          f"({', '.join(f'{p}: {k}' for p, k in n['on_items_not_in_set'].items()) or 'none'}). "
          f"Analysed: {n['analysed']}.",
          "- Items by number of ratings: "
          + ", ".join(f"{k} rating{'s' if k != 1 else ''}: {v}" for k, v in rs["ratings_per_item"].items()) + "."]
    if res["population"]:
        p = res["population"]
        L.append(f"- Weighted results stand for all {p['same'] + p['different']} judged pairs of the run "
                 f"({p['same']} same, {p['different']} different, {p['tasks']} tasks).")
    L += ["", "## Raters and attention checks", "",
          "| rater | role | rated | judged pairs | can't tell | known-same right | known-different right | "
          f"passes (≥ {res['min_checks']:.0%} on each) | median s/item |", "|---|---|---|---|---|---|---|---|---|"]
    for p, v in res["raters"].items():
        ck = v["checks"]
        cell = lambda k: f"{ck[k]['right']}/{ck[k]['n']}" + (f" ({ck[k]['unsure']} can't tell)" if ck[k]["unsure"] else "")
        L.append(f"| {p} | {v['role']} | {v['rated']} | {v['judged_pairs']} | {v['cant_tell']} | "
                 f"{cell('control-same')} | {cell('control-different')} | {'yes' if v['passed_checks'] else 'no'} | "
                 f"{v['median_seconds']} |")

    L += ["", "## Human vs judge", "", "| measure | " + " | ".join(names[k] for k in COHORTS) + " |",
          "|---|" + "---|" * len(COHORTS)]
    L.append("| raters | " + " | ".join(", ".join(c[k]["raters"]) or "none" for k in COHORTS) + " |")
    L.append("| ratings with a label / pairs / tasks | "
             + " | ".join(f"{c[k]['unweighted']['ratings']} / {c[k]['pairs_rated']} / {c[k]['tasks']}" for k in COHORTS) + " |")
    L.append("| can't tell | " + " | ".join(str(c[k]["cant_tell"]) for k in COHORTS) + " |")
    rows = [("per_rating", "agreement", "raw agreement"), ("per_rating", "cohen_kappa", "Cohen's kappa"),
            ("per_rating", "gwet_ac1", "Gwet's AC1"),
            ("per_rating", "rescue_precision", "rescue precision, per rating"),
            ("per_pair", "rescue_precision", "rescue precision, per pair"),
            ("per_pair", "npv", "judge \"different\" confirmed, per pair"),
            ("per_pair", "sensitivity", "sensitivity"), ("per_pair", "specificity", "specificity"),
            ("per_pair", "balanced_accuracy", "balanced accuracy")]
    for w in ("unweighted", "weighted"):
        if c["all"][w] is None:
            continue
        L.append(f"| **{w}** |" + " |" * len(COHORTS))
        for level, m, label in rows:
            L.append(f"| {label} | " + " | ".join(_ci(c[k][w][level][m]) for k in COHORTS) + " |")
    L += ["", "Rescue precision: of the pairs the judge calls \"same\", the share humans also call same. "
          "Sensitivity: of the pairs humans call same, the share the judge calls same. "
          "Specificity: of the pairs humans call different, the share the judge calls different. "
          "Per pair uses the human majority; tied pairs are left out.", ""]
    L += ["Counts behind the unweighted per-rating numbers:", "",
          "| | " + " | ".join(names[k] for k in COHORTS) + " |", "|---|" + "---|" * len(COHORTS)]
    for cell in c["all"]["unweighted"]["table"]:
        L.append(f"| {cell} | " + " | ".join(f"{c[k]['unweighted']['table'][cell]:.0f}" for k in COHORTS) + " |")

    L += ["", "## Human vs human (pairs with two or more labelled answers)", "",
          "| measure | " + " | ".join(names[k] for k in COHORTS) + " |", "|---|" + "---|" * len(COHORTS)]
    L.append("| pairs (of which split) | " + " | ".join(
        f"{c[k]['human_vs_human']['pairs']} ({c[k]['human_vs_human']['pairs_split']})" for k in COHORTS) + " |")
    for m, label in (("agreement", "raw agreement"), ("fleiss_kappa", "Fleiss' kappa"),
                     ("krippendorff_alpha", "Krippendorff's alpha")):
        L.append(f"| {label} | " + " | ".join(_ci(c[k]["human_vs_human"][m]) for k in COHORTS) + " |")

    for title, field in (("By rater", "by_rater"), ("By difficulty tier", "by_tier"), ("By model", "by_model")):
        for k in ("all", "no_author"):
            L += ["", f"## {title} ({names[k]})", "",
                  "| | ratings | judge-same ratings | raw agreement | Cohen's kappa | rescue precision |",
                  "|---|---|---|---|---|---|"]
            for g, v in c[k][field].items():
                L.append(f"| {g} | {v['ratings']} | {v['judge_same_ratings']} | {_ci(v['agreement'])} | {_ci(v['cohen_kappa'])} | "
                         f"{_ci(v['rescue_precision'])} |")

    f = res["flags"]
    L += ["", "## Flags and notes", "",
          f"- \"Reference looks wrong\": {f['ref_wrong_ratings']} ratings. "
          f"\"Model looks better\": {f['model_better_ratings']} ratings.",
          "- \"Model looks better\" by answer: "
          + (", ".join(f"{k}: {v}" for k, v in f["model_better_by_answer"].items()) or "none") + ".", "",
          "| task | ratings (raters) | reference flagged wrong by | model looked better to | notes |", "|---|---|---|---|---|"]
    order = sorted(f["tasks"].items(), key=lambda kv: (-len(kv[1]["ref_wrong"]), -len(kv[1]["notes"]),
                                                       -len(kv[1]["model_better_raters"]), kv[0]))
    for t, v in order:
        mb = "; ".join(f"{m} ({', '.join(r)})" for m, r in v["model_better"].items())
        notes = " / ".join(f"{x['rater']} ({x['answer']}): \"{x['note']}\"" for x in v["notes"]).replace("|", "\\|")
        L.append(f"| {t} | {v['ratings']} ({v['raters']}) | {', '.join(v['ref_wrong']) or '-'} | {mb or '-'} | {notes or '-'} |")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# Design v2: the grader against people (FINAL_PLAN.md decision 23)
# --------------------------------------------------------------------------- #
# A v2 item is a pair (reference vs a model's answer, each shown whole and framed on
# the target atoms) or one of three kinds of attention check. Each rating holds two
# answers: `label` on the whole scene and `target_label` on the zoomed target view.
#
#   whole scene  vs  the grader's TASK SUCCESS            (machine "same" = success)
#   zoomed view  vs  the grader's TARGET SCORE            (machine "same" = target score 1)
#
# People are the yardstick: sensitivity is the share of pairs people call same that
# the grader also passes (1 - sensitivity = the grader failing a right answer),
# specificity the share people call different that the grader fails, and "grader
# right, confirmed" the share of the grader's passes that people call same.
CHECKS_V2 = ("check-same", "check-different", "check-calibrated")
V1_KINDS = {"vlm", *CHECKS}
V2_KINDS = {"pair", *CHECKS_V2}
COHORTS_V2 = ("primary", "no_author", "all")
VIEWS = {"whole": ("label", "task success"), "target": ("target_label", "target score = 1")}
CLASSES = ("right", "close", "wrong")
PER_RATING = ("agreement", "cohen_kappa", "gwet_ac1", "rescue_precision", "npv")


def design_of(key: dict) -> str:
    """ "v1" (the pilot: judged pairs, one answer each) or "v2". A key that holds items
    of both designs is refused: their answers do not mean the same thing."""
    kinds = {v.get("kind") for v in key["items"].values()}
    design = key.get("design") or "v1"
    if design not in ("v1", "v2"):
        raise ValueError(f"unknown rating-set design {design!r}")
    wrong = kinds & (V2_KINDS if design == "v1" else V1_KINDS)
    if wrong or kinds - V1_KINDS - V2_KINDS:
        raise ValueError(f"the key of {key.get('set')} is design {design} but holds items of kind "
                         f"{sorted(wrong or kinds - V1_KINDS - V2_KINDS)}: v1 and v2 are never analysed together")
    return design


def machine_label(item: dict, view: str) -> str | None:
    """What the grader says about a pair, in the raters' words. None: no verdict for
    this view (a task without a target has no target score)."""
    if view == "whole":
        return "same" if item["success"] else "different"
    if not item.get("has_target") or item.get("target_f1") is None:
        return None
    return "same" if item["target_f1"] == 1.0 else "different"


def check_right(item: dict, row: dict) -> bool:
    """Did a rater get an attention check right? Known-same: the whole scene called
    same and the zoomed view not called different. Known-different: either view called
    different (a calibrated change can be invisible in the whole view). "Can't tell"
    on both is a miss."""
    if item["expected"] == "same":
        return row["label"] == "same" and row.get("target_label") != "different"
    return "different" in (row["label"], row.get("target_label"))


def rater_summary_v2(rows: list[dict], repeats: list[dict], items: dict) -> dict:
    """One rater: counts, attention checks and the fixed pass rule, test-retest.

    Pass rule (paper/a4/FINAL_CALL.md, fixed before any v2 rating): at least 4 checks
    answered, at most one miss over them, and no miss on an easy known-different check.
    """
    rows = sorted(rows, key=lambda r: r.get("created_at") or "")
    checks, misses, easy_miss = {}, 0, 0
    for kind in CHECKS_V2:
        rs = [r for r in rows if items[r["item"]]["kind"] == kind]
        right = sum(check_right(items[r["item"]], r) for r in rs)
        checks[kind] = {"n": len(rs), "right": right}
        misses += len(rs) - right
        easy_miss += (len(rs) - right) if kind == "check-different" else 0
    answered = sum(c["n"] for c in checks.values())
    first = {items[r["item"]]["kind"] for r in rows[:8]} & set(CHECKS_V2)
    mine = {r["item"]: r for r in rows}
    retest = {}
    for view, (field, _) in VIEWS.items():
        both = [(mine[r["item"]].get(field), r.get(field)) for r in repeats if r["item"] in mine]
        both = [(a, b) for a, b in both if a in LABELS and b in LABELS]
        retest[view] = {"n": len(both), "same_answer": sum(a == b for a, b in both)}
    pairs = [r for r in rows if items[r["item"]]["kind"] == "pair"]
    ms = [r["ms"] for r in rows if r.get("ms")]
    return {
        "rated": len(rows), "pairs": len(pairs),
        "cant_tell": {view: sum(r.get(field) == "unsure" for r in pairs) for view, (field, _) in VIEWS.items()},
        "checks": checks, "checks_answered": answered, "check_misses": misses,
        "check_kinds_in_first_8": len(first),
        "passed_checks": answered >= 4 and misses <= 1 and easy_miss == 0,
        "repeats": len(repeats), "retest": retest,
        "median_seconds": round(statistics.median(ms) / 1000, 1) if ms else None,
    }


def weights_v2(rated: dict[str, dict], population: dict | None) -> dict[str, float] | None:
    """Weight per rated pair so the rated pairs stand for every answer of the run's
    frame: N/n within its (tier, grader class) cell, then scaled so each class adds up
    to its total in the run (which covers cells of the run with no rated pair)."""
    if not population:
        return None
    big = collections.Counter({(t, c): n for t, c, n in population["cells"]})
    small = collections.Counter((it["tier"], it["grader_class"]) for it in rated.values())
    w = {i: big.get((it["tier"], it["grader_class"]), small[it["tier"], it["grader_class"]])
            / small[it["tier"], it["grader_class"]] for i, it in rated.items()}
    for cls in CLASSES:
        ids = [i for i, it in rated.items() if it["grader_class"] == cls]
        total = sum(n for (_, c), n in big.items() if c == cls)
        if ids and total:
            scale = total / sum(w[i] for i in ids)
            for i in ids:
                w[i] *= scale
    return w


def bootstrap_tasks_and_raters(recs: list[tuple], reps: int, seed: int) -> dict:
    """95% intervals of the per-rating measures when BOTH tasks and raters are resampled
    (a rating counts once for every time its task and its rater were drawn together).
    `recs`: (task, rater, human label, machine label). Raters differ, and an interval
    that resamples tasks alone treats the panel of raters as fixed."""
    tasks, raters = sorted({r[0] for r in recs}), sorted({r[1] for r in recs})
    rng = random.Random(seed)
    draws = collections.defaultdict(list)
    for _ in range(reps if tasks and len(raters) > 1 else 0):
        ct = collections.Counter(rng.choices(tasks, k=len(tasks)))
        cr = collections.Counter(rng.choices(raters, k=len(raters)))
        m = judge_measures([(h, j, ct[t] * cr[p]) for t, p, h, j in recs if ct[t] * cr[p]])
        for k in PER_RATING:
            if m[k] is not None:
                draws[k].append(m[k])
    out = {}
    for k in PER_RATING:
        xs = sorted(draws[k])
        ok = len(xs) >= max(2, reps / 2)
        out[k] = {"lo": xs[int(0.025 * (len(xs) - 1))] if ok else None,
                  "hi": xs[round(0.975 * (len(xs) - 1))] if ok else None}
    return out


def _share_same(recs: list[tuple[str, str, float]]) -> dict:
    n = sum(w for _, _, w in recs)
    return {"same_share": _div(sum(w for h, _, w in recs if h == "same"), n)}


def view_block(rows: list[dict], items: dict, view: str, machine, population: dict | None,
               reps: int, seed: int, breakdowns: bool = True) -> dict:
    """One cohort's answers on one view against one machine verdict (`machine(item)` ->
    "same" / "different" / None). Clustered by task (a paraphrase with its original)."""
    field = VIEWS[view][0]
    votes = collections.defaultdict(collections.Counter)     # item -> labelled answers
    who = collections.defaultdict(dict)                      # item -> rater -> label
    cant_tell = 0
    for r in rows:
        it = items[r["item"]]
        if it["kind"] != "pair" or machine(it) is None:
            continue
        if r.get(field) in LABELS:
            votes[r["item"]][r[field]] += 1
            who[r["item"]][r["rater"]] = r[field]
        elif r.get(field) == "unsure":
            cant_tell += 1
    cluster = lambda i: items[i].get("base_task") or items[i]["task"]

    def records(ids, weight: dict | None):
        per_rating, per_pair = collections.defaultdict(list), collections.defaultdict(list)
        for i in ids:
            c, m, w = votes[i], machine(items[i]), (weight[i] if weight is not None else 1.0)
            k = sum(c.values())
            per_rating[cluster(i)] += [(lab, m, w / k if weight is not None else 1.0) for lab in c.elements()]
            if c["same"] != c["different"]:   # a tied pair has no majority
                per_pair[cluster(i)].append((max(c, key=c.get), m, w))
        return per_rating, per_pair

    weights = weights_v2({i: items[i] for i in votes}, population)
    out = {
        "raters": sorted({p for v in who.values() for p in v}),
        "ratings": sum(sum(c.values()) for c in votes.values()), "cant_tell": cant_tell,
        "pairs": len(votes), "tasks": len({cluster(i) for i in votes}),
        "pairs_by_n_raters": dict(sorted(collections.Counter(sum(c.values()) for c in votes.values()).items())),
        "pairs_tied": sum(c["same"] == c["different"] for c in votes.values()),
        "unweighted": _judge_block(*records(votes, None), reps, seed),
        "weighted": _judge_block(*records(votes, weights), reps, seed) if weights is not None else None,
    }
    out["unweighted"]["per_rating_tasks_and_raters"] = bootstrap_tasks_and_raters(
        [(cluster(i), p, lab, machine(items[i])) for i, v in who.items() for p, lab in v.items()], reps, seed)
    if not breakdowns:
        return out
    multi = collections.defaultdict(list)
    for i, c in votes.items():
        if sum(c.values()) >= 2:
            multi[cluster(i)].append(c)
    out["human_vs_human"] = {"pairs": sum(len(v) for v in multi.values()), "tasks": len(multi),
                             "pairs_split": sum(len(c) > 1 for v in multi.values() for c in v),
                             **bootstrap(multi, human_measures, reps, seed)}

    def by(group_of, stat, keys) -> dict:
        groups = collections.defaultdict(list)
        for i in votes:
            groups[group_of(items[i])].append(i)
        res = {}
        for g, ids in sorted(groups.items(), key=lambda kv: str(kv[0])):
            per_rating, _ = records(ids, None)
            b = bootstrap(per_rating, stat, reps, seed)
            res[g] = {"pairs": len(ids), "ratings": sum(len(v) for v in per_rating.values()),
                      **{k: b[k] for k in keys}}
        return res

    order = {c: n for n, c in enumerate(CLASSES)}
    by_class = by(lambda it: it["grader_class"], _share_same, ("same_share",))
    out["by_class"] = dict(sorted(by_class.items(), key=lambda kv: order.get(kv[0], 9)))
    out["by_tier"] = by(lambda it: it.get("tier", "unknown"), judge_measures,
                        ("agreement", "cohen_kappa", "rescue_precision", "npv"))
    return out


def analyse_v2(key: dict, ratings, population: dict | None = None, reps: int = 2000, seed: int = 4) -> dict:
    if not isinstance(ratings, dict) or ratings.get("set") != key["set"]:
        raise ValueError(f"the key is of set {key['set']} (design v2) but the ratings are of set "
                         f"{ratings.get('set') if isinstance(ratings, dict) else 'an old bare export'}: "
                         "ratings of different sets or designs are never analysed together")
    items = key["items"]
    rows, roles, exported_at = load_ratings(ratings)
    repeats = ratings.get("repeats") or []
    seen = collections.Counter((r["rater"], r["item"]) for r in rows)
    if dup := [p for p, n in seen.items() if n > 1]:
        raise ValueError(f"{len(dup)} rater-item pairs rated more than once, e.g. by {dup[0][0]}")
    for r in (*rows, *repeats):
        if r["item"] not in items:
            raise ValueError("a rating is on an item that is not in the key: this export is not of "
                             f"set {key['set']} as built (v1 and v2 are never analysed together)")
        if r["label"] not in (*LABELS, "unsure") or r.get("target_label") not in (*LABELS, "unsure", None):
            raise ValueError(f"labels must be same, different or unsure, got {r['label']!r} / {r.get('target_label')!r}")
        for f in ("ref_wrong", "model_better"):
            if r.get(f) not in (None, True, False):
                raise ValueError(f"{f} must be a boolean, got {r[f]!r}")
    test = [r for r in rows if roles.get(r["rater"]) == "test"]
    real = [r for r in rows if roles.get(r["rater"]) != "test"]
    by_rater = collections.defaultdict(list)
    for r in real:
        by_rater[r["rater"]].append(r)
    raters = {p: {"role": roles.get(p, "rater"),
                  **rater_summary_v2(rs, [x for x in repeats if x["rater"] == p], items)}
              for p, rs in sorted(by_rater.items(), key=lambda kv: (len(kv[0]), kv[0]))}
    members = {
        "primary": {p for p, v in raters.items() if v["role"] != "author" and v["passed_checks"]},
        "no_author": {p for p, v in raters.items() if v["role"] != "author"},
        "all": set(raters),
    }
    pairs = {i: v for i, v in items.items() if v["kind"] == "pair"}
    judged = any(v.get("judge_label") for v in pairs.values())
    cohorts = {}
    for name in COHORTS_V2:
        mine = [r for r in real if r["rater"] in members[name]]
        cohorts[name] = {
            "raters": sorted(members[name], key=lambda p: (len(p), p)),
            **{view: view_block(mine, items, view, lambda it, v=view: machine_label(it, v), population, reps, seed)
               for view in VIEWS},
            # Secondary: the image-pair judge against people, where it was run.
            "judge": view_block(mine, items, "whole", lambda it: it.get("judge_label"), None, reps, seed,
                                breakdowns=False) if judged else None,
        }
    retest = {view: {"n": sum(v["retest"][view]["n"] for p, v in raters.items() if p in members["no_author"]),
                     "same_answer": sum(v["retest"][view]["same_answer"] for p, v in raters.items()
                                        if p in members["no_author"])} for view in VIEWS}
    return {
        "set": key["set"], "design": "v2", "exported_at": exported_at,
        "bootstrap": {"reps": reps, "seed": seed, "unit": "task (a paraphrase with its original)"},
        "ratings": {"exported": len(rows), "from_test_tokens": len(test), "analysed": len(real),
                    "repeat_answers": len(repeats)},
        "rating_set": {
            "items": len(items), "pairs": len(pairs),
            "tasks": len({v.get("base_task") or v["task"] for v in pairs.values()}),
            "models": len({v["model"] for v in pairs.values()}),
            "by_class": {c: sum(v["grader_class"] == c for v in pairs.values()) for c in CLASSES},
            "with_target_view": sum(machine_label(v, "target") is not None for v in pairs.values()),
            "with_judge_verdict": sum(bool(v.get("judge_label")) for v in pairs.values()),
            "checks": {k: sum(v["kind"] == k for v in items.values()) for k in CHECKS_V2},
            "labelled_ratings_per_pair": dict(sorted(collections.Counter(
                sum(r["item"] == i and r["label"] in LABELS for r in real) for i in pairs).items())),
        },
        "population": None if not population else {
            "frame": population.get("frame"),
            **{c: sum(n for _, cls, n in population["cells"] if cls == c) for c in CLASSES}},
        "raters": raters, "cohorts": cohorts, "retest_no_author": retest,
        "flags": flags(real, items),
    }


def markdown_v2(res: dict) -> str:
    c = res["cohorts"]
    names = {"primary": "independent raters who pass the checks (primary)",
             "no_author": "without the author", "all": "all raters, author included"}
    head = "| measure | " + " | ".join(names[k] for k in COHORTS_V2) + " |"
    rule = "|---|" + "---|" * len(COHORTS_V2)
    rs, n = res["rating_set"], res["ratings"]
    L = [f"<!-- generated by scripts/agreement.py from the {res['set']} export of {res['exported_at']}; do not edit -->",
         "", f"# Rating study {res['set']}: the grader against people", "",
         "Each pair was shown as four pictures: reference and model answer, whole and zoomed on the "
         "atoms the request is about, the answer always from the reference's camera. Each rating holds "
         "two answers: on the whole scene, and on the zoomed view. Every interval is a 95% bootstrap "
         f"interval that resamples tasks ({res['bootstrap']['reps']} replicates; a paraphrase counts with "
         "its original). \"No interval\" means too few ratings to give one. Raters are pseudonyms.", "",
         "## The data", "",
         f"- Rating set: {rs['pairs']} pairs ({rs['tasks']} tasks, {rs['models']} models): "
         + ", ".join(f"{rs['by_class'][k]} the grader calls {k}" for k in CLASSES)
         + f" (right = task success; close = not a success, target score 1; wrong = the rest). "
         f"{rs['with_target_view']} pairs have a zoomed view. Checks in the pool: "
         + ", ".join(f"{v} {k.removeprefix('check-')}" for k, v in rs["checks"].items()) + ".",
         f"- Ratings exported: {n['exported']} (from testing-only tokens: {n['from_test_tokens']}; "
         f"analysed: {n['analysed']}), plus {n['repeat_answers']} repeat answers.",
         "- Pairs by number of labelled whole-scene answers: "
         + ", ".join(f"{k}: {v}" for k, v in rs["labelled_ratings_per_pair"].items()) + "."]
    if res["population"]:
        p = res["population"]
        L.append(f"- Weighted results stand for the run's {sum(p[k] for k in CLASSES)} answers in the frame "
                 f"({', '.join(f'{p[k]} {k}' for k in CLASSES)}): {p['frame']}.")
    L += ["", "## Raters and attention checks", "",
          "Pass rule, fixed before the first rating: at least 4 checks answered, at most one miss, no miss "
          "on an easy known-different check.", "",
          "| rater | role | rated | pairs | known-same right | known-different right | calibrated right | "
          "check kinds in first 8 | passes | repeats: same answer (whole) | median s/item |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for p, v in res["raters"].items():
        ck = v["checks"]
        cell = lambda k: f"{ck[k]['right']}/{ck[k]['n']}"
        rt = v["retest"]["whole"]
        L.append(f"| {p} | {v['role']} | {v['rated']} | {v['pairs']} | {cell('check-same')} | {cell('check-different')} | "
                 f"{cell('check-calibrated')} | {v['check_kinds_in_first_8']} | {'yes' if v['passed_checks'] else 'no'} | "
                 f"{rt['same_answer']}/{rt['n']} | {v['median_seconds']} |")

    rows = [("per_rating", "agreement", "raw agreement, per rating"), ("per_rating", "cohen_kappa", "Cohen's kappa"),
            ("per_rating", "gwet_ac1", "Gwet's AC1"),
            ("per_pair", "sensitivity", "sensitivity: people say same -> grader passes"),
            ("per_pair", "specificity", "specificity: people say different -> grader fails"),
            ("per_pair", "rescue_precision", "grader passes -> people say same"),
            ("per_pair", "npv", "grader fails -> people say different"),
            ("per_pair", "balanced_accuracy", "balanced accuracy")]

    def table(block: str, what: str) -> list[str]:
        out = [head, rule,
               "| raters | " + " | ".join(str(len(c[k][block]["raters"])) for k in COHORTS_V2) + " |",
               "| labelled answers / pairs / tasks | " + " | ".join(
                   f"{c[k][block]['ratings']} / {c[k][block]['pairs']} / {c[k][block]['tasks']}" for k in COHORTS_V2) + " |",
               "| can't tell | " + " | ".join(str(c[k][block]["cant_tell"]) for k in COHORTS_V2) + " |"]
        for w in ("unweighted", "weighted"):
            if c["all"][block][w] is None:
                continue
            out.append(f"| **{w}{' (to the run)' if w == 'weighted' else ' (the set as built)'}** |" + " |" * len(COHORTS_V2))
            for level, m, label in rows:
                out.append(f"| {label.replace('grader', what)} | "
                           + " | ".join(_ci(c[k][block][w][level][m]) for k in COHORTS_V2) + " |")
        out.append("| **unweighted, tasks and raters both resampled** |" + " |" * len(COHORTS_V2))
        for m, label in (("agreement", "raw agreement"), ("cohen_kappa", "Cohen's kappa")):
            cells = []
            for k in COHORTS_V2:
                est = c[k][block]["unweighted"]["per_rating"][m]["est"]
                two = c[k][block]["unweighted"]["per_rating_tasks_and_raters"][m]
                cells.append(_ci({"est": est, **two}))
            out.append(f"| {label} | " + " | ".join(cells) + " |")
        out += ["", "Counts behind the unweighted per-rating numbers:", "",
                "| | " + " | ".join(names[k] for k in COHORTS_V2) + " |", rule]
        for cell in c["all"][block]["unweighted"]["table"]:
            out.append(f"| {cell.replace('judge', what)} | "
                       + " | ".join(f"{c[k][block]['unweighted']['table'][cell]:.0f}" for k in COHORTS_V2) + " |")
        return out

    L += ["", "## Primary: task success against people (whole scene)", "",
          "The grader's \"same\" is task success. Per pair uses the majority of people; tied pairs are left out.", ""]
    L += table("whole", "grader")
    L += ["", "## Primary: target score against people (zoomed view)", "",
          "The grader's \"same\" is a target score of 1. Pairs of tasks without a target are not in this table.", ""]
    L += table("target", "grader")

    L += ["", "## What people said, by the grader's verdict", "",
          "Share of labelled answers that say \"same\". Expected if the grader is right: high for *right* on both "
          "views; for *close*, low on the whole scene and high on the zoomed view; low for *wrong* on both.", ""]
    for k in ("primary", "no_author"):
        L += [f"**{names[k]}**", "", "| grader's verdict | pairs | whole scene: same | zoomed view: same |", "|---|---|---|---|"]
        for cls in CLASSES:
            w, t = c[k]["whole"]["by_class"].get(cls), c[k]["target"]["by_class"].get(cls)
            L.append(f"| {cls} | {w['pairs'] if w else 0} | {_ci(w['same_share']) if w else 'n/a'} | "
                     f"{_ci(t['same_share']) if t else 'n/a'} |")
        L.append("")

    L += ["## By tier (without the author, task success against the whole scene)", "",
          "| tier | pairs | labelled answers | raw agreement | Cohen's kappa | grader passes -> people say same | "
          "grader fails -> people say different |", "|---|---|---|---|---|---|---|"]
    for g, v in c["no_author"]["whole"]["by_tier"].items():
        L.append(f"| {g} | {v['pairs']} | {v['ratings']} | {_ci(v['agreement'])} | {_ci(v['cohen_kappa'])} | "
                 f"{_ci(v['rescue_precision'])} | {_ci(v['npv'])} |")

    L += ["", "## People against people (pairs with two or more labelled answers)", "", head, rule]
    for view, label in (("whole", "whole scene"), ("target", "zoomed view")):
        L.append(f"| **{label}**: pairs (of which split) | " + " | ".join(
            f"{c[k][view]['human_vs_human']['pairs']} ({c[k][view]['human_vs_human']['pairs_split']})" for k in COHORTS_V2) + " |")
        for m, lab in (("agreement", "raw agreement"), ("fleiss_kappa", "Fleiss' kappa"),
                       ("krippendorff_alpha", "Krippendorff's alpha")):
            L.append(f"| {lab} | " + " | ".join(_ci(c[k][view]["human_vs_human"][m]) for k in COHORTS_V2) + " |")
    rt = res["retest_no_author"]
    L += ["", "Test-retest (a rater's second answer to a pair they rated earlier; without the author): "
          + "; ".join(f"{label}: the same answer on {rt[v]['same_answer']} of {rt[v]['n']}"
                      for v, label in (("whole", "whole scene"), ("target", "zoomed view"))) + "."]

    L += ["", "## Secondary: the image-pair judge against people", ""]
    if c["all"]["judge"] is None:
        L.append("The image-pair judge was not run on these pairs (no pair in the key carries a verdict).")
    else:
        L += [f"{rs['with_judge_verdict']} pairs carry a judge verdict. Unweighted; whole-scene answers.", "", head, rule,
              "| labelled answers / pairs | " + " | ".join(f"{c[k]['judge']['ratings']} / {c[k]['judge']['pairs']}"
                                                           for k in COHORTS_V2) + " |"]
        for level, m, label in rows:
            L.append(f"| {label.replace('grader passes', 'judge says same').replace('grader fails', 'judge says different')} | "
                     + " | ".join(_ci(c[k]["judge"]["unweighted"][level][m]) for k in COHORTS_V2) + " |")

    f = res["flags"]
    L += ["", "## Flags and notes", "",
          f"- \"Reference looks wrong\": {f['ref_wrong_ratings']} ratings. "
          f"\"Model looks better\": {f['model_better_ratings']} ratings.", "",
          "| task | ratings (raters) | reference flagged wrong by | model looked better to | notes |", "|---|---|---|---|---|"]
    order = sorted(f["tasks"].items(), key=lambda kv: (-len(kv[1]["ref_wrong"]), -len(kv[1]["notes"]),
                                                       -len(kv[1]["model_better_raters"]), kv[0]))
    for t, v in order:
        mb = "; ".join(f"{m} ({', '.join(r)})" for m, r in v["model_better"].items())
        notes = " / ".join(f"{x['rater']} ({x['answer']}): \"{x['note']}\"" for x in v["notes"]).replace("|", "\\|")
        L.append(f"| {t} | {v['ratings']} ({v['raters']}) | {', '.join(v['ref_wrong']) or '-'} | {mb or '-'} | {notes or '-'} |")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("key", type=pathlib.Path, help="private answer key (never printed)")
    ap.add_argument("ratings", type=pathlib.Path, help="export from scripts/export_ratings.py")
    ap.add_argument("--population", type=pathlib.Path,
                    help="judged pairs of the whole run per task and label (build_rating_set.py --population-only); "
                         "adds weighted results. Default: the key's own `population`, if it has one")
    ap.add_argument("--min-checks", type=float, default=0.8,
                    help="attention-check accuracy a rater needs on each kind of check to pass")
    ap.add_argument("--reps", type=int, default=2000, help="bootstrap replicates")
    ap.add_argument("--seed", type=int, default=4)
    ap.add_argument("--json", type=pathlib.Path, help="write the full result here instead of printing it")
    ap.add_argument("--markdown", type=pathlib.Path, help="also write the tables as Markdown")
    a = ap.parse_args(argv)
    key = json.loads(a.key.read_text())
    population = json.loads(a.population.read_text()) if a.population else key.get("population")
    res = analyse(key, json.loads(a.ratings.read_text()), a.min_checks, population, a.reps, a.seed)
    text = json.dumps(res, indent=1) + "\n"
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(text)
    else:
        print(text, end="")
    if a.markdown:
        a.markdown.parent.mkdir(parents=True, exist_ok=True)
        a.markdown.write_text(markdown_v2(res) if res.get("design") == "v2" else markdown(res))


if __name__ == "__main__":
    main()
