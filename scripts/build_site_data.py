#!/usr/bin/env python3
"""
Derive the leaderboard's data files from the 2×2 scorecards and run archives.

    python scripts/build_site_data.py --results results/r2x2 --runs runs [--docs docs]
    python scripts/build_leaderboard.py      # then render the HTML

Reads, under ``--results``:

  * ``spec/*.json``           headline MVS run (escalated, Mol*-validated)
  * ``spec_grounded/*.json``  same models + frozen grounding packs (``--grounding``)
  * ``bare/*.json``, ``bare_grounded/*.json``  the no-reference rows
  * ``baseline_spec.json``    the free rules baseline (optional)

and, from ``--runs``, the archives (``run_*.json``) for each scorecard's raw model
text, matched on run meta. Outcomes come from the scorecards (they were
re-validated after the archives were written); raw text comes from the archives.

Writes to ``--docs``:

  * ``scorecard.json``       merged: new MVS track + the API track carried over
                             from the existing ``scorecard.json`` (not re-run)
  * ``escalation_data.json`` tiered-grading summary of the spec run
  * ``gallery_data.json``    evaluator-gallery cards (+ PNGs into ``gallery/img``)
  * ``conditions_data.json`` the 2×2 (spec vs spec+dossier, bare rows)
  * ``failures_data.json``   every failing sample, with its full detail

Re-running is idempotent: the API track is read back from ``scorecard.json``.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import statistics
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import runner  # noqa: E402

# Same model, new route: these ran via OpenRouter on 2026-10-18 instead of the
# native APIs. Keep the old key so is_open() (slash = open weights) stays right.
ALIASES = {"google/gemini-3.5-flash": "gemini-3.5-flash",
           "openai/gpt-5.4-nano": "gpt-5.4-nano"}
NATIVE = {"gemini-3.5-flash": "gemini:gemini-3.5-flash", "gpt-5.4-nano": "openai:gpt-5.4-nano"}
# In the July panel but not in the October run (upstream rate limit at Mistral).
NOT_RUN = {"mistralai/mistral-small-2603":
           "not re-run: OpenRouter upstream rate limit at Mistral (11 attempts, 2026-10-18)"}

CONDITIONS = ("spec", "spec_grounded", "bare", "bare_grounded")
RESCUED = {"rendering-equivalent", "vlm:same"}
# Lookup-heavy task sources: the ones a grounding pack is meant to help.
LOOKUP_SOURCES = {"clinvar-variant", "clinvar-hotspots", "sifts-named", "resolve"}
GALLERY_PER_CLASS = 4
RAW_SHOW = 4000      # chars of raw text shown inline on the failures page


def canonical(name: str) -> str:
    return ALIASES.get(name, name)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def _run_key(meta: dict) -> tuple:
    if meta.get("run_id"):  # runs since 2026-10-18 carry a unique id
        return (meta["run_id"],)
    return (meta.get("started_at"), tuple(meta.get("models", [])), meta.get("condition"),
            bool(meta.get("grounding")), bool(meta.get("escalate")))


def load_condition(results: pathlib.Path, cond: str) -> dict[str, dict]:
    """{canonical model: {"card": scorecard, "model": model record, "file": path}}."""
    out = {}
    for f in sorted((results / cond).glob("*.json")):
        card = json.loads(f.read_text(encoding="utf-8"))
        for name, m in card["models"].items():
            out[canonical(name)] = {"card": card, "model": m, "raw_name": name, "file": f}
    return out


def index_archives(runs: pathlib.Path) -> dict[tuple, list[pathlib.Path]]:
    idx: dict[tuple, list] = {}
    for f in sorted(runs.glob("run_*.json")):
        meta = json.loads(f.read_text(encoding="utf-8")).get("meta", {})
        idx.setdefault(_run_key(meta), []).append(f)
    return idx


def raw_samples_for(entry: dict, archives: dict, cache: dict) -> dict | None:
    """The archived raw samples ({task_id: [sample]}) behind one scorecard entry."""
    hits = archives.get(_run_key(entry["card"]["meta"]), [])
    if not hits:  # e.g. the qwen3-30b spec archive was never written; outcomes still stand
        print(f"warning: {entry['file'].name} ({entry['card']['meta']['condition']}): "
              "no run archive; raw text unavailable", file=sys.stderr)
        return None
    if len(hits) > 1:
        raise SystemExit(f"{entry['file']}: {len(hits)} matching run archives (need 1)")
    if hits[0] not in cache:
        cache[hits[0]] = json.loads(hits[0].read_text(encoding="utf-8"))["raw_samples"]
    return cache[hits[0]][entry["raw_name"]]


def load_tasks() -> dict[str, dict]:
    out = {}
    for f in (REPO / "tasks").rglob("*.json"):
        t = json.loads(f.read_text(encoding="utf-8"))
        if t.get("category") == "mvs":
            out[t["id"]] = t
    return out


# --------------------------------------------------------------------------- #
# Pure helpers (tested)
# --------------------------------------------------------------------------- #
def _mean(xs) -> float | None:
    xs = list(xs)
    return round(statistics.fmean(xs), 4) if xs else None


def validated_f1(task: dict) -> float:
    """Rescue-only: 1.0 if a valid scene was confirmed to render the reference."""
    esc = task.get("escalation") or {}
    if task.get("outcome") == "valid" and esc.get("decision") in RESCUED:
        return 1.0
    return task["f1"]


def escalation_summary(tasks: list[dict]) -> dict:
    """Per-model tiered-grading counts over its MVS tasks."""
    valid = [t for t in tasks if t.get("outcome") == "valid"]
    rendered = [t for t in valid if (t.get("escalation") or {}).get("tier") in ("visual", "vlm")]
    dec = Counter(t["escalation"]["decision"] for t in rendered)
    return {
        "mvs": len(tasks),
        "perfect": sum((t.get("escalation") or {}).get("decision") == "correct" for t in valid),
        "escalated": len(rendered),
        "failed": len(tasks) - len(valid),
        "rescued_visual": dec["rendering-equivalent"],
        "rescued_vlm": dec["vlm:same"],
        "confirmed_different": dec["vlm:different"] + dec["visually-different"],
        "rescued": dec["rendering-equivalent"] + dec["vlm:same"],
        "tree_f1": round(statistics.fmean(t["f1"] for t in tasks), 3),
        "validated_f1": round(statistics.fmean(validated_f1(t) for t in tasks), 3),
    }


def outcome_counts(tasks: list[dict]) -> dict[str, int]:
    return {o: sum(t.get("outcome") == o for t in tasks) for o in runner.OUTCOMES}


def paired_delta(spec: list[dict], other: list[dict], ids: set[str] | None = None) -> dict:
    """other - spec, overall and on the tasks whose scene is valid in both runs."""
    a = {t["id"]: t for t in spec if ids is None or t["id"] in ids}
    b = {t["id"]: t for t in other if t["id"] in a}
    both = [i for i in a if a[i].get("outcome") == "valid" and b[i].get("outcome") == "valid"]
    d = [b[i]["f1"] - a[i]["f1"] for i in both]
    return {
        "n": len(a),
        "delta": round(statistics.fmean(b[i]["f1"] for i in a)
                       - statistics.fmean(a[i]["f1"] for i in a), 4) if a else None,
        "n_both_valid": len(both),
        "delta_both_valid": _mean(d),
        "better": sum(x > 0 for x in d), "worse": sum(x < 0 for x in d),
    }


def split_issues(lines: list[str]) -> list[list[str]]:
    """Mol* reports one issue as a header line plus indented detail lines."""
    issues: list[list[str]] = []
    for ln in lines or []:
        if ln.startswith(" ") and issues:
            issues[-1].append(ln.strip())
        else:
            issues.append([ln.strip()])
    return issues


_QUOTED = re.compile(r'"[^"]*"')
_UNION = re.compile(r"\(\(?\"[^)]*\)\)?.*$")


def issue_text(issue: list[str], n_lines: int = 2, width: int = 220) -> str:
    """An issue's first lines, with long Mol* type unions cut."""
    parts = []
    for ln in issue[:n_lines]:
        ln = _UNION.sub("(…)", ln) if len(ln) > width else ln
        parts.append(ln if len(ln) <= width else ln[:width] + "…")
    return " ".join(parts)


def normalise_issue(issue: list[str]) -> str:
    """Group key: quoted names -> "…", allowed-parent lists dropped."""
    s = issue_text(issue)
    s = re.sub(r"Allowed parents for .*? are: [^.]*", "Allowed parents: …", s)
    return _QUOTED.sub('"…"', s)


_POS = re.compile(r":? ?line \d+ column \d+ \(char \d+\)")


def normalise_json_error(err: str) -> str:
    return _POS.sub("", err or "").strip()


def pick_gallery(rows: list[dict], per_class: int = GALLERY_PER_CLASS) -> list[dict]:
    """Deterministic gallery pick, ``per_class`` cards per verdict, distinct tasks.

    * rendering-equivalent / vlm:same: lowest tree F1 first (tree-match most wrong
      about a scene that renders right);
    * vlm:different: highest tree F1 first (tree-match nearly satisfied by a scene
      that looks different).
    Ties: model name, then task id.
    """
    picks, seen = [], set()
    for dec, sign in (("rendering-equivalent", 1), ("vlm:same", 1), ("vlm:different", -1)):
        cand = sorted((r for r in rows if r["decision"] == dec),
                      key=lambda r: (sign * r["mvs_score"], r["model"], r["id"]))
        n = 0
        for r in cand:
            if n == per_class:
                break
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            picks.append(r)
            n += 1
    return picks


def merge_model(new: dict | None, old: dict | None, spec_name: str | None = None) -> dict:
    """New MVS track + the old API track for one model."""
    old = old or {}
    api_tasks = [t for t in old.get("tasks", []) if t["category"] == "api_calling"]
    by_cat = {}
    if new:
        mvs_tasks = [t for t in new["tasks"] if t["category"] == "mvs"]
        by_cat["mvs"] = new["by_category"]["mvs"]
    else:
        mvs_tasks = []
    if "api_calling" in old.get("by_category", {}):
        by_cat["api_calling"] = old["by_category"]["api_calling"]
    tasks = mvs_tasks + api_tasks
    out = {
        "spec": (new or {}).get("spec") or spec_name or old.get("spec"),
        "mean_f1": round(statistics.fmean(t["f1"] for t in tasks), 4) if tasks else 0.0,
        "n_graded": len(tasks),
        "by_category": by_cat,
        # Speed is the July value: the October MVS run's wall time includes rendering.
        "sec_per_call": old.get("sec_per_call"),
    }
    if new:
        out.update({k: new.get(k) for k in ("usage", "cost_usd", "wall_seconds", "by_skill",
                                            "parse_success", "cond_f1", "outcomes",
                                            "valid_scene")})
    out["tasks"] = tasks
    return out


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #
def build_scorecard(conds: dict, baseline: dict | None, old_card: dict,
                    esc_models: dict) -> dict:
    old_models = old_card.get("models", {})
    spec = conds["spec"]
    models = {}
    for name in sorted(set(spec) | set(old_models)):
        new = spec.get(name, {}).get("model")
        if name == "baseline-rules" and baseline:
            new = baseline["models"]["baseline-rules"]
        if new is None and name not in NOT_RUN and name != "baseline-rules":
            raise SystemExit(f"{name}: in the old scorecard but not in the new run; "
                             "add it to NOT_RUN or re-run it")
        m = merge_model(new, old_models.get(name))
        if name in esc_models:
            m["validated_f1"] = esc_models[name]["validated_f1"]
        if name in NOT_RUN:
            m["mvs_not_run"] = NOT_RUN[name]
        if name in ALIASES.values():
            m["route_note"] = (f"ran via OpenRouter ({m['spec']}) on 2026-10-18; "
                               f"July API-track result via the native API ({NATIVE[name]})")
        models[name] = m
    spec_meta = next(iter(spec.values()))["card"]["meta"]
    api_note = old_card.get("meta", {}).get("api_track", {}) or {
        "run": old_card.get("meta", {}).get("api_track_rerun", {}).get("at"),
        "n_tasks": 20, "samples": old_card.get("samples", 3),
        "note": "API track not re-run in October; carried over from the July 2026 scorecard "
                "(grader unchanged).",
    }
    return {
        "n_tasks": 70 + api_note["n_tasks"],
        "samples": 1,
        "meta": {
            "built_by": "scripts/build_site_data.py",
            "mvs_track": {
                "run": "2026-10-18", "n_tasks": 70, "samples": 1, "condition": "spec",
                "escalate": True, "judge": spec_meta.get("judge"), "validate": True,
                "git_commit": spec_meta.get("git_commit"),
                "sources": {n: f"results/r2x2/spec/{e['file'].name} "
                               f"(started {e['card']['meta']['started_at']})"
                            for n, e in sorted(spec.items())},
                "note": "Atom-set grader (R7), strict T1, Mol*-validated outcomes. "
                        "Everything but a valid scene scores 0.",
            },
            "api_track": api_note,
            "renamed": {v: k for k, v in ALIASES.items()},
            "not_run": NOT_RUN,
            "speed_note": "sec_per_call is from the July run (October wall time includes rendering).",
        },
        "models": models,
    }


def build_escalation(spec: dict) -> dict:
    models = {n: escalation_summary(e["model"]["tasks"]) for n, e in spec.items()}
    lifts = [s["validated_f1"] - s["tree_f1"] for s in models.values()]
    totals = {k: sum(s[k] for s in models.values())
              for k in ("escalated", "rescued", "rescued_visual", "rescued_vlm",
                        "confirmed_different", "failed", "mvs")}
    totals["n_models"] = len(models)
    judge = next(iter(spec.values()))["card"]["meta"].get("judge")
    return {"preliminary": False, "judge": judge, "policy": "rescue-only", "run": "2026-10-18",
            "t1_rule": "≤ 2 pixels changing by > 48 in any channel, at 256 px",
            "gallery_url": "gallery.html",
            "tiers": ["tree-match", "visual diff", "VLM judge"],
            "lift_min": round(min(lifts), 3), "lift_max": round(max(lifts), 3),
            "models": models, "totals": totals}


def build_gallery(spec: dict, tasks: dict, docs: pathlib.Path) -> dict:
    rows = []
    for name, e in spec.items():
        for t in e["model"]["tasks"]:
            esc = t.get("escalation") or {}
            if t.get("outcome") != "valid" or esc.get("tier") not in ("visual", "vlm"):
                continue
            vlm = esc.get("vlm") or {}
            rows.append({"id": t["id"], "model": name, "rubric": tasks[t["id"]]["prompt"],
                         "mvs_score": t["f1"], "visual_score": esc.get("visual_sim"),
                         "changed_pixels": esc.get("changed_pixels"),
                         "decision": esc["decision"], "vlm_label": vlm.get("label"),
                         "vlm_reason": vlm.get("reason"), "judge": vlm.get("judge"),
                         "_ref": esc["ref_png"], "_pred": esc["pred_png"]})
    picks = pick_gallery(rows)
    img = docs / "gallery" / "img"
    if img.exists():
        shutil.rmtree(img)
    img.mkdir(parents=True)
    for r in picks:
        stem = f"{r['model'].replace('/', '_')}__{r['id']}"
        for side in ("ref", "pred"):
            shutil.copyfile(r.pop(f"_{side}"), img / f"{stem}_{side}.png")
            r[f"{side}_img"] = f"gallery/img/{stem}_{side}.png"
        r["note"] = {
            "rendering-equivalent": "Picked: lowest tree F1 among renders matching the reference (≤ 2 pixels differ).",
            "vlm:same": "Picked: lowest tree F1 among scenes the VLM judged the same.",
            "vlm:different": "Picked: highest tree F1 among scenes the VLM judged different.",
        }[r["decision"]]
    return {"meta": {"model": f"{len(spec)} models (spec run, 2026-10-18)",
                     "judge": next(iter(spec.values()))["card"]["meta"].get("judge"),
                     "n": len(picks),
                     "rule": f"{GALLERY_PER_CLASS} per verdict, distinct tasks: lowest tree F1 "
                             "for rescues, highest tree F1 for VLM-different; ties by model, task.",
                     "pool": dict(Counter(r["decision"] for r in rows))},
            "rows": picks}


def _cond_stats(m: dict) -> dict:
    return {"mvs_f1": m["by_category"]["mvs"]["mean_f1"], "valid_scene": m.get("valid_scene"),
            "cond_f1": m.get("cond_f1"), "parse_success": m.get("parse_success"),
            "outcomes": m.get("outcomes")}


def build_conditions(conds: dict, tasks: dict) -> dict:
    lookup = {i for i, t in tasks.items() if t.get("source") in LOOKUP_SOURCES}
    rows = {}
    for name, e in conds["spec"].items():
        st = e["model"]["tasks"]
        r = {"spec": _cond_stats(e["model"])}
        for c in ("spec_grounded", "bare", "bare_grounded"):
            if name in conds[c]:
                r[c] = _cond_stats(conds[c][name]["model"])
        if name in conds["spec_grounded"]:
            gt = conds["spec_grounded"][name]["model"]["tasks"]
            r["dossier"] = paired_delta(st, gt)
            r["dossier_lookup"] = paired_delta(st, gt, lookup)
        rows[name] = r
    pooled = []
    for name, e in conds["spec"].items():
        if name in conds["spec_grounded"]:
            a = {t["id"]: t for t in e["model"]["tasks"]}
            for t in conds["spec_grounded"][name]["model"]["tasks"]:
                if t.get("outcome") == "valid" and a[t["id"]].get("outcome") == "valid":
                    pooled.append(t["f1"] - a[t["id"]]["f1"])
    paired = [r["dossier"] for r in rows.values() if "dossier" in r]
    return {
        "run": "2026-10-18", "samples": 1, "n_tasks": 70, "n_lookup_tasks": len(lookup),
        "lookup_sources": sorted(LOOKUP_SOURCES),
        "models": rows,
        "summary": {
            "n_models": len(paired),
            "mean_delta": _mean(p["delta"] for p in paired),
            "pooled_both_valid": {"n": len(pooled), "delta": _mean(pooled),
                                  "better": sum(x > 0 for x in pooled),
                                  "worse": sum(x < 0 for x in pooled),
                                  "same": sum(x == 0 for x in pooled)},
            "mean_lookup_delta": _mean(r["dossier_lookup"]["delta"] for r in rows.values()
                                       if "dossier_lookup" in r),
        },
    }


def _failure(t: dict, raw: dict | None, prompt: str) -> dict:
    out = {"id": t["id"], "prompt": prompt, "outcome": t["outcome"]}
    if t["outcome"] in ("invalid_json", "not_mvs"):
        out["error"] = t.get("error")
        out["raw"] = None if raw is None else (raw.get("raw") or "")
    elif t["outcome"] == "invalid_mvs":
        out["mvs_issues"] = t.get("mvs_issues") or []
        out["predicted"] = t.get("predicted")
    elif t["outcome"] == "load_failed":
        out["load_error"] = t.get("load_error") or ""
        out["predicted"] = t.get("predicted")
    return out


def build_failures(conds: dict, tasks: dict, archives: dict,
                   baseline: dict | None = None) -> dict:
    cache: dict = {}
    out: dict = {"run": "2026-10-18", "outcomes": list(runner.OUTCOMES), "conditions": {}}
    msg: dict[str, dict] = {}
    jerr: dict[str, Counter] = {}
    for c in CONDITIONS:
        per = {}
        for name, e in sorted(conds[c].items()):
            mt = e["model"]["tasks"]
            fails = [t for t in mt if t.get("outcome") != "valid"]
            rec = {"outcomes": outcome_counts(mt), "n": len(mt),
                   "mvs_f1": e["model"]["by_category"]["mvs"]["mean_f1"]}
            for t in fails:
                for iss in split_issues(t.get("mvs_issues")):
                    g = msg.setdefault(normalise_issue(iss), {"counts": Counter(), "examples": Counter(),
                                                               "models": set()})
                    g["counts"][c] += 1
                    g["examples"][issue_text(iss)] += 1
                    g["models"].add(name)
                if t.get("outcome") == "invalid_json":
                    jerr.setdefault(normalise_json_error(t.get("error")), Counter())[c] += 1
            if c.startswith("spec"):  # bare: counts only, every scene fails the same way
                raws = raw_samples_for(e, archives, cache)
                if raws is None:
                    rec["raw_missing"] = True
                rec["failures"] = [_failure(t, ((raws or {}).get(t["id"]) or [None])[0],
                                            tasks[t["id"]]["prompt"]) for t in fails]
            per[name] = rec
        if c == "spec" and baseline:  # the rules floor: counts only, it is not an LLM
            bm = baseline["models"]["baseline-rules"]
            per["baseline-rules"] = {"outcomes": bm["outcomes"], "n": len(bm["tasks"]),
                                     "mvs_f1": bm["by_category"]["mvs"]["mean_f1"]}
        out["conditions"][c] = per
    out["mvs_messages"] = sorted(
        ({"pattern": k, "counts": dict(v["counts"]), "total": sum(v["counts"].values()),
          "n_models": len(v["models"]),
          "examples": [{"text": t, "n": n} for t, n in v["examples"].most_common(8)]}
         for k, v in msg.items()), key=lambda g: (-g["total"], g["pattern"]))
    out["json_errors"] = sorted(
        ({"pattern": k, "counts": dict(v), "total": sum(v.values())} for k, v in jerr.items()),
        key=lambda g: (-g["total"], g["pattern"]))
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--results", type=pathlib.Path, default=REPO / "results" / "r2x2")
    ap.add_argument("--runs", type=pathlib.Path, default=REPO / "runs")
    ap.add_argument("--docs", type=pathlib.Path, default=REPO / "docs")
    a = ap.parse_args(argv)

    conds = {c: load_condition(a.results, c) for c in CONDITIONS}
    tasks = load_tasks()
    archives = index_archives(a.runs)
    bpath = a.results / "baseline_spec.json"
    baseline = json.loads(bpath.read_text(encoding="utf-8")) if bpath.exists() else None
    old_card = json.loads((a.docs / "scorecard.json").read_text(encoding="utf-8"))

    esc = build_escalation(conds["spec"])
    card = build_scorecard(conds, baseline, old_card, esc["models"])
    files = {
        "scorecard.json": card,
        "escalation_data.json": esc,
        "gallery_data.json": build_gallery(conds["spec"], tasks, a.docs),
        "conditions_data.json": build_conditions(conds, tasks),
        "failures_data.json": build_failures(conds, tasks, archives, baseline),
    }
    for fname, data in files.items():
        # scorecard.json in build_leaderboard.py's own format, so a rebuild is a no-op.
        text = (json.dumps(data, indent=2) if fname == "scorecard.json"
                else json.dumps(data, indent=1, ensure_ascii=False) + "\n")
        (a.docs / fname).write_text(text, encoding="utf-8")
        print(f"wrote {a.docs / fname}")


if __name__ == "__main__":
    main()
