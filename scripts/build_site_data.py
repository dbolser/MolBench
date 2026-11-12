#!/usr/bin/env python3
"""
Derive the leaderboard's data files from scorecards and run archives.

    # a manifest run (python -m molbench.runner --manifest ...): both tracks, one run
    python scripts/build_site_data.py --run results/final-v1 --runs runs/final-v1 --docs OUT

    # the October 2026 layout: MVS re-run, API track carried over from docs/scorecard.json
    python scripts/build_site_data.py --results results/r2x2 --runs runs [--docs docs]

    python scripts/build_leaderboard.py      # then render the HTML

Dates, task counts and sample counts are read from the scorecards. The few facts a
scorecard cannot carry (a model renamed between runs, a model that could not be run)
live in a small config file, ``--site-config`` (default ``run/site_r2x2.toml``).

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
import calendar
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
from molbench.manifest import tomllib  # noqa: E402

DEFAULT_SITE_CONFIG = REPO / "run" / "site_r2x2.toml"

# Filled from the site config (see `configure`):
ALIASES: dict[str, str] = {}   # run name -> leaderboard name (same model, new route)
NATIVE: dict[str, str] = {}    # leaderboard name -> the route of its older result
NOT_RUN: dict[str, str] = {}   # in the older panel, absent from this run -> why


def configure(path: pathlib.Path | None) -> None:
    """Load renames and not-run notes; ``None`` clears them (a manifest run has none)."""
    cfg = tomllib.loads(path.read_text(encoding="utf-8")) if path else {}
    ALIASES.clear(), NATIVE.clear(), NOT_RUN.clear()
    for run_name, a in cfg.get("aliases", {}).items():
        ALIASES[run_name] = a["name"]
        NATIVE[a["name"]] = a["native"]
    for name, n in cfg.get("not_run", {}).items():
        NOT_RUN[name] = n["reason"]


configure(DEFAULT_SITE_CONFIG if DEFAULT_SITE_CONFIG.exists() else None)

ROUTE_LABELS = {"openrouter": "OpenRouter", "anthropic": "Anthropic", "openai": "OpenAI",
                "gemini": "Google", "google": "Google"}

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


def cell_samples_for(entry: dict, archive: pathlib.Path, cache: dict) -> dict | None:
    """Raw samples behind a manifest-run scorecard: ``{task_id: [record by sample]}``
    from ``<archive>/cells/<model>/<condition>.jsonl``."""
    f = archive / "cells" / entry["file"].stem / f"{entry['file'].parent.name}.jsonl"
    if not f.exists():
        return None
    if f not in cache:
        per: dict[str, dict] = {}
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                per.setdefault(r["task_id"], {})[r["sample"]] = r
        cache[f] = per
    return cache[f]


def mvs_tasks(m: dict) -> list[dict]:
    return [t for t in m["tasks"] if t["category"] == "mvs"]


def run_date(spec: dict) -> str:
    """The day(s) the spec scorecards were started: one date, or 'first to last'."""
    days = sorted({e["card"]["meta"]["started_at"][:10] for e in spec.values()})
    return days[0] if len(days) == 1 else f"{days[0]} to {days[-1]}"


def month_name(date: str | None) -> str:
    """'2026-10-18...' -> 'October' ('?' when there is no date)."""
    try:
        return calendar.month_name[int(date[5:7])]
    except (TypeError, ValueError, IndexError):
        return "?"


def n_mvs_tasks(spec: dict) -> int:
    return max(len(mvs_tasks(e["model"])) for e in spec.values())


def n_samples(spec: dict) -> int:
    return next(iter(spec.values()))["card"].get("samples", 1)


def task_outcomes(t: dict) -> list[str]:
    """The outcome of every sample of a task (a single-sample task has one)."""
    if len(t.get("outcomes") or []) > 1:
        return t["outcomes"]
    return [t.get("outcome")]


def all_valid(t: dict) -> bool:
    return all(o == "valid" for o in task_outcomes(t))


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
    """Samples per outcome (every sample of every task)."""
    seen = Counter(o for t in tasks for o in task_outcomes(t))
    return {o: seen[o] for o in runner.OUTCOMES}


def paired_delta(spec: list[dict], other: list[dict], ids: set[str] | None = None) -> dict:
    """other - spec, overall and on the tasks whose scene is valid in both runs."""
    a = {t["id"]: t for t in spec if ids is None or t["id"] in ids}
    b = {t["id"]: t for t in other if t["id"] in a}
    a = {i: t for i, t in a.items() if i in b}  # a condition may cover only some tasks
    both = [i for i in a if all_valid(a[i]) and all_valid(b[i])]
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
        models[name] = m
    spec_meta = next(iter(spec.values()))["card"]["meta"]
    when = run_date(spec)
    n_mvs, samples = n_mvs_tasks(spec), n_samples(spec)
    old_meta = old_card.get("meta", {})
    api_run = (old_meta.get("api_track") or {}).get("run") \
        or old_meta.get("api_track_rerun", {}).get("at")
    api_month, mvs_month = month_name(api_run), month_name(when)
    api_note = old_meta.get("api_track", {}) or {
        "run": api_run,
        "n_tasks": max((sum(t["category"] == "api_calling" for t in m.get("tasks", []))
                        for m in old_models.values()), default=0),
        "samples": old_card.get("samples", 3),
        "note": f"API track not re-run in {mvs_month}; carried over from the {api_month} "
                f"{(api_run or '?')[:4]} scorecard (grader unchanged).",
    }
    for name, m in models.items():
        if name in NATIVE:
            route = ROUTE_LABELS.get(str(m["spec"]).split(":")[0], str(m["spec"]).split(":")[0])
            m["route_note"] = (f"ran via {route} ({m['spec']}) on {when}; "
                               f"{api_month} API-track result via the native API ({NATIVE[name]})")
    src = "/".join(next(iter(spec.values()))["file"].parent.parts[-3:])  # results/<set>/spec
    return {
        "n_tasks": n_mvs + api_note["n_tasks"],
        "samples": samples,
        "meta": {
            "built_by": "scripts/build_site_data.py",
            "mvs_track": {
                "run": when, "n_tasks": n_mvs, "samples": samples, "condition": "spec",
                "escalate": bool(spec_meta.get("escalate")), "judge": spec_meta.get("judge"),
                "validate": bool(spec_meta.get("validate")),
                "git_commit": spec_meta.get("git_commit"),
                "sources": {n: f"{src}/{e['file'].name} "
                               f"(started {e['card']['meta']['started_at']})"
                            for n, e in sorted(spec.items())},
                "note": "Atom-set grader (R7), strict T1, Mol*-validated outcomes. "
                        "Everything but a valid scene scores 0.",
            },
            "api_track": api_note,
            "renamed": {v: k for k, v in ALIASES.items()},
            "not_run": NOT_RUN,
            "speed_note": f"sec_per_call is from the {api_month} run ({mvs_month} wall time "
                          "includes rendering).",
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
    return {"preliminary": False, "judge": judge, "policy": "rescue-only", "run": run_date(spec),
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
    return {"meta": {"model": f"{len(spec)} models (spec run, {run_date(spec)})",
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
        st = mvs_tasks(e["model"])
        r = {"spec": _cond_stats(e["model"])}
        for c in conds:
            if c != "spec" and name in conds[c] and "mvs" in conds[c][name]["model"]["by_category"]:
                r[c] = _cond_stats(conds[c][name]["model"])
        if name in conds["spec_grounded"]:
            gt = mvs_tasks(conds["spec_grounded"][name]["model"])
            r["dossier"] = paired_delta(st, gt)
            r["dossier_lookup"] = paired_delta(st, gt, lookup)
        rows[name] = r
    pooled = []
    for name, e in conds["spec"].items():
        if name in conds["spec_grounded"]:
            a = {t["id"]: t for t in mvs_tasks(e["model"])}
            for t in mvs_tasks(conds["spec_grounded"][name]["model"]):
                if all_valid(t) and all_valid(a[t["id"]]):
                    pooled.append(t["f1"] - a[t["id"]]["f1"])
    paired = [r["dossier"] for r in rows.values() if "dossier" in r]
    return {
        "run": run_date(conds["spec"]), "samples": n_samples(conds["spec"]),
        "n_tasks": n_mvs_tasks(conds["spec"]), "n_lookup_tasks": len(lookup),
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


def _sample_failures(t: dict, raws: dict | None, prompt: str) -> list[dict]:
    """One entry per failing *sample* of a multi-sample task (manifest runs). The
    scorecard keeps only the best sample's tree, so the others show their raw text."""
    out = []
    for s in t["samples"]:
        if s.get("outcome") == "valid":
            continue
        raw = ((raws or {}).get(t["id"]) or {}).get(s["sample"])
        f = _failure({**s, "id": t["id"]}, raw, prompt)
        f["sample"] = s["sample"]
        if s.get("outcome") in ("invalid_mvs", "load_failed", "unchecked"):
            f["raw"] = None if raw is None else (raw.get("raw") or "")
        out.append(f)
    return out


def build_failures(conds: dict, tasks: dict, archives: dict | pathlib.Path,
                   baseline: dict | None = None) -> dict:
    """``archives``: the index of ``run_*.json`` archives, or a manifest run's archive
    directory (per-sample failures, raw text from its cell files)."""
    cache: dict = {}
    per_sample = isinstance(archives, pathlib.Path)
    spec = conds["spec"]
    out: dict = {"run": run_date(spec), "samples": n_samples(spec),
                 "n_tasks": n_mvs_tasks(spec), "outcomes": list(runner.OUTCOMES),
                 "conditions": {}}
    msg: dict[str, dict] = {}
    jerr: dict[str, Counter] = {}
    for c in conds:
        per = {}
        for name, e in sorted(conds[c].items()):
            mt = mvs_tasks(e["model"])
            if not mt:
                continue
            fails = [t for t in mt if not all_valid(t)]
            counts = outcome_counts(mt)
            rec = {"outcomes": counts, "n": sum(counts.values()),
                   "mvs_f1": e["model"]["by_category"]["mvs"]["mean_f1"]}
            for t in fails:
                rows = [s for s in t["samples"] if s.get("outcome") != "valid"] \
                    if per_sample else [t]
                for row in rows:
                    for iss in split_issues(row.get("mvs_issues")):
                        g = msg.setdefault(normalise_issue(iss),
                                           {"counts": Counter(), "examples": Counter(),
                                            "models": set()})
                        g["counts"][c] += 1
                        g["examples"][issue_text(iss)] += 1
                        g["models"].add(name)
                    if row.get("outcome") == "invalid_json":
                        jerr.setdefault(normalise_json_error(row.get("error")), Counter())[c] += 1
            if c.startswith("spec"):  # bare: counts only, every scene fails the same way
                raws = (cell_samples_for(e, archives, cache) if per_sample
                        else raw_samples_for(e, archives, cache))
                if raws is None:
                    rec["raw_missing"] = True
                if per_sample:
                    rec["failures"] = [f for t in fails
                                       for f in _sample_failures(t, raws, tasks[t["id"]]["prompt"])]
                else:
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


def build_run_scorecard(spec: dict) -> dict:
    """The leaderboard scorecard of a manifest run: both tracks from the same run, so
    nothing is carried over and nothing is renamed."""
    first = next(iter(spec.values()))["card"]
    meta = first["meta"]
    when = run_date(spec)
    n_mvs = n_mvs_tasks(spec)
    n_api = max(sum(t["category"] == "api_calling" for t in e["model"]["tasks"])
                for e in spec.values())
    samples = n_samples(spec)
    track = {"run": when, "samples": samples, "condition": "spec", "same_run": True}
    return {
        "n_tasks": n_mvs + n_api,
        "samples": samples,
        "meta": {
            "built_by": "scripts/build_site_data.py",
            "run": {k: meta.get(k) for k in ("run_name", "manifest", "manifest_sha256",
                                             "corpus_version", "corpus_sha256", "git_commit",
                                             "mock", "archive")},
            "mvs_track": {**track, "n_tasks": n_mvs, "escalate": False, "judge": None,
                          "validate": bool(meta.get("validate")),
                          "git_commit": meta.get("git_commit"),
                          "sources": {n: f"{e['file'].parent.name}/{e['file'].name}"
                                      for n, e in sorted(spec.items())},
                          "note": "Strict score: anything but a valid output scores 0."},
            "api_track": {**track, "n_tasks": n_api,
                          "note": "Run together with the MVS track (same models, same day)."},
            "incomplete": sorted(n for n, e in spec.items()
                                 if not e["card"]["meta"].get("complete", True)),
        },
        "models": {n: e["model"] for n, e in sorted(spec.items())},
    }


def build_from_run(run_dir: pathlib.Path, archive: pathlib.Path, docs: pathlib.Path) -> dict:
    """The data files of a manifest run (no render cascade: no escalation or gallery)."""
    configure(None)
    names = [d.name for d in sorted(run_dir.iterdir())
             if d.is_dir() and any(d.glob("*.json"))]
    order = [c for c in CONDITIONS if c in names] + [c for c in names if c not in CONDITIONS]
    conds = {c: load_condition(run_dir, c) for c in order}
    if not conds.get("spec"):
        raise SystemExit(f"{run_dir}: no spec/ scorecards; nothing to build")
    conds.setdefault("spec_grounded", {})
    tasks = load_tasks()
    return {
        "scorecard.json": build_run_scorecard(conds["spec"]),
        "conditions_data.json": build_conditions(conds, tasks),
        "failures_data.json": build_failures(conds, tasks, archive),
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", type=pathlib.Path, default=None,
                    help="scorecards of a manifest run (results/<run name>); with --runs "
                         "pointing at its archive (runs/<run name>)")
    ap.add_argument("--results", type=pathlib.Path, default=REPO / "results" / "r2x2")
    ap.add_argument("--runs", type=pathlib.Path, default=REPO / "runs")
    ap.add_argument("--docs", type=pathlib.Path, default=REPO / "docs")
    ap.add_argument("--site-config", type=pathlib.Path, default=DEFAULT_SITE_CONFIG,
                    help="renamed / not-run models for the --results layout")
    a = ap.parse_args(argv)

    if a.run:
        files = build_from_run(a.run, a.runs, a.docs)
        for stale in ("escalation_data.json", "gallery_data.json"):
            (a.docs / stale).unlink(missing_ok=True)  # none in a manifest run
    else:
        configure(a.site_config)
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
    a.docs.mkdir(parents=True, exist_ok=True)
    for fname, data in files.items():
        # scorecard.json in build_leaderboard.py's own format, so a rebuild is a no-op.
        text = (json.dumps(data, indent=2) if fname == "scorecard.json"
                else json.dumps(data, indent=1, ensure_ascii=False) + "\n")
        (a.docs / fname).write_text(text, encoding="utf-8")
        print(f"wrote {a.docs / fname}")


if __name__ == "__main__":
    main()
