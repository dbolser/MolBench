#!/usr/bin/env python3
"""
What will a manifest run cost? No model is called; nothing is spent.

    python scripts/estimate_cost.py                              # current corpus
    python scripts/estimate_cost.py --tasks mvs=450 api_calling=250   # a planned corpus
    python scripts/estimate_cost.py --calibrate /path/to/runs    # re-measure token rates

The table has one row per model and one column per condition. Input tokens come from
the real prompts (system prompt + task prompt + grounding pack) divided by each
model's measured characters-per-token; output tokens from the size of each task's
reference answer times each model's measured output rate (which includes hidden
reasoning tokens, since those are billed). Prices come from the manifest.

``--tasks`` scales the current corpus to a planned size per track: it assumes the new
tasks have the same average prompt and answer size as today's, and that the share of
tasks each restricted condition applies to (e.g. grounding on the lookup tiers) stays
the same. Two things the planned corpus has and today's does not are therefore not in
the number: follow-up tasks send the start state as well (about 30 tasks per track; the
system prompt, at 8,000-11,000 characters, still dominates the input), and a larger
clinical tier raises the share of tasks the grounding condition runs on. Re-run without
``--tasks`` once the corpus exists: that estimate reads the real prompts. ``--calibrate`` rebuilds ``run/token_calibration.json`` from archived runs
(``run_*.json`` with real token usage).
"""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import manifest as manifest_mod  # noqa: E402
from molbench import runner  # noqa: E402

DEFAULT_MANIFEST = REPO / "run" / "final_run.toml"


# --------------------------------------------------------------------------- #
# Calibration
# --------------------------------------------------------------------------- #
def calibrate(runs: pathlib.Path, pattern: str = "run_20261018*.json") -> dict:
    """Measure, per model, prompt characters per billed input token and billed output
    tokens per reference character, over every matching MVS run archive.

    Uses today's prompts and tasks, so it is only right while they still match what
    the archives were run on. That was true for the 2026-10-18 runs until the MVS system
    prompt gained its "Follow-up requests" paragraph (about 330 characters in 8,200):
    recalibrating on those archives now would overstate characters-per-token by about
    4%. The committed ``run/token_calibration.json`` was measured before that change.
    """
    tasks = {t["id"]: t for t in runner.load_tasks(["mvs"])}
    prompts = {c: runner.build_system_prompts(c)["mvs"] for c in runner.CONDITIONS}
    acc: dict[str, Counter] = {}
    used = []
    for f in sorted(runs.glob(pattern)):
        d = json.loads(f.read_text(encoding="utf-8"))
        meta = d.get("meta", {})
        if meta.get("categories") != ["mvs"] or "raw_samples" not in d:
            continue
        for name, m in d["models"].items():
            usage = m.get("usage") or {}
            ids = [t["id"] for t in m["tasks"]]
            n_samples = d.get("samples", 1)
            if (not usage.get("calls") or usage["calls"] != len(ids) * n_samples
                    or any(i not in tasks for i in ids)):
                continue  # baseline (no tokens), partial runs, or tasks since removed
            system = prompts[meta.get("condition", "spec")]
            chars = sum(len(system) + len(runner.user_message(tasks[i], bool(meta.get("grounding"))))
                        for i in ids) * n_samples
            ref = sum(runner.reference_chars(tasks[i]) for i in ids) * n_samples
            a = acc.setdefault(name, Counter())
            a.update(prompt_chars=chars, input_tokens=usage["input_tokens"], ref_chars=ref,
                     output_tokens=usage["output_tokens"], calls=usage["calls"], runs=1)
            used.append(f.name)
    if not acc:
        raise SystemExit(f"no usable run archives matching {pattern} under {runs}")
    models = {
        name: {"chars_per_input_token": round(a["prompt_chars"] / a["input_tokens"], 3),
               "output_tokens_per_ref_char": round(a["output_tokens"] / a["ref_chars"], 4),
               "output_tokens_per_call": round(a["output_tokens"] / a["calls"], 1),
               "calls": a["calls"], "runs": a["runs"]}
        for name, a in sorted(acc.items())}
    return {
        "what": "Token rates per model, measured on archived runs. chars_per_input_token = "
                "prompt characters per billed input token; output_tokens_per_ref_char = "
                "billed output tokens (reasoning included) per character of the task's "
                "reference answer as compact JSON.",
        "built_by": "scripts/estimate_cost.py --calibrate",
        "source": f"{len(set(used))} MVS run archives matching {pattern} "
                  "(spec and bare prompts, with and without grounding packs)",
        "models": models,
        **manifest_mod.pooled_rates(models),
    }


# --------------------------------------------------------------------------- #
# Estimate
# --------------------------------------------------------------------------- #
def estimate(manifest, calib, tasks: list[dict], include_optional: bool,
             target: dict[str, int] | None = None) -> tuple[list[dict], dict]:
    panel = manifest.panel(include_optional=include_optional)
    cells = runner.build_plan(manifest, tasks, panel)
    now = Counter(t["category"] for t in tasks if t["category"] in manifest_mod.TRACKS)
    info = {"tasks_now": dict(now), "tasks": dict(now), "cells": len(cells)}
    if not target:
        return runner.project_costs(manifest, cells, calib), info
    unknown = set(target) - set(now)
    if unknown:
        raise SystemExit(f"--tasks: no {sorted(unknown)} tasks in the corpus to scale from")
    rows: dict[tuple, dict] = {}
    for track in now:
        factor = target.get(track, now[track]) / now[track]
        part = runner.project_costs(manifest, [c for c in cells if c.task["category"] == track],
                                    calib)
        for r in part:
            agg = rows.setdefault((r["model"], r["condition"]), {**copy.deepcopy(r), "calls": 0,
                                  "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
                                  "worst_cost_usd": 0.0})
            agg["calls"] += round(r["calls"] * factor)
            agg["input_tokens"] += round(r["input_tokens"] * factor)
            agg["output_tokens"] += round(r["output_tokens"] * factor)
            agg["cost_usd"] += r["cost_usd"] * factor
            agg["worst_cost_usd"] += r["worst_cost_usd"] * factor
    info["tasks"] = {t: target.get(t, now[t]) for t in now}
    info["cells"] = sum(r["calls"] for r in rows.values())
    return list(rows.values()), info


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--calibration", type=pathlib.Path, default=None)
    ap.add_argument("--tasks", nargs="+", default=None, metavar="TRACK=N",
                    help="hypothetical corpus size, e.g. mvs=450 api_calling=250")
    ap.add_argument("--core-only", action="store_true", help="leave out optional models")
    ap.add_argument("--json", action="store_true", help="print the rows as JSON")
    ap.add_argument("--calibrate", type=pathlib.Path, default=None, metavar="RUNS_DIR",
                    help="rebuild the calibration file from run archives, then exit")
    ap.add_argument("--pattern", default="run_20261018*.json")
    ap.add_argument("--out", type=pathlib.Path, default=manifest_mod.DEFAULT_CALIBRATION)
    a = ap.parse_args(argv)

    if a.calibrate:
        data = calibrate(a.calibrate, a.pattern)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {a.out}: {len(data['models'])} models; pooled default {data['default']}")
        return

    manifest = manifest_mod.load_manifest(a.manifest)
    calib = manifest_mod.Calibration.load(a.calibration)
    target = None
    if a.tasks:
        try:
            target = {k: int(v) for k, v in (x.split("=", 1) for x in a.tasks)}
        except ValueError:
            raise SystemExit("--tasks takes TRACK=N pairs, e.g. mvs=450 api_calling=250")
    tasks = runner.load_tasks(list(manifest_mod.TRACKS))
    rows, info = estimate(manifest, calib, tasks, not a.core_only, target)
    if a.json:
        print(json.dumps({"info": info, "rows": rows}, indent=1))
        return
    what = ("current corpus" if not target else
            "hypothetical corpus (scaled from today's " +
            ", ".join(f"{n} {t}" for t, n in info["tasks_now"].items()) + ")")
    print(f"{what}: " + ", ".join(f"{n} {t}" for t, n in info["tasks"].items())
          + f" tasks -> {info['cells']:,} calls")
    runner.print_projection(manifest, rows)


if __name__ == "__main__":
    main()
