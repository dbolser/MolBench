#!/usr/bin/env python3
"""
Re-grade stored predictions for some tasks after their references changed.

No model calls for the answers: each listed task's stored best prediction is graded
again against the task's current reference, and in scorecards made with
``--escalate`` the rendering cascade is rerun too (renders + VLM judge, written over
the task's old gallery renders). Model aggregates are then recomputed in place.
Only single-sample scorecards, as with revalidate_scorecard.py.

    python scripts/regrade_tasks.py results/r2x2/*/*.json \\
        --tasks gen-chain-1cbs gen-chain-1hho ...
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import mvs, runner  # noqa: E402

SAMPLE_KEYS = ("f1", "precision", "recall", "predicted", "error", "outcome", "mvs_issues", "load_error")


def regrade(path: pathlib.Path, tasks: dict[str, dict]) -> list[tuple[str, str, float, float]]:
    card = json.loads(path.read_text())
    if card.get("samples", 1) != 1:
        raise SystemExit(f"{path}: {card['samples']} samples per task; only 1 is supported")
    meta = card["meta"]
    cascade = None
    if meta.get("escalate"):
        from molbench.escalate import escalating_grade
        from molbench.render import render_scene
        from molbench.vlm_grader import AnthropicImagePairJudge
        judge = AnthropicImagePairJudge(meta["judge"]) if meta.get("judge") else None
        cascade = (escalating_grade, lambda tree, png: render_scene(tree, png, width=600, height=450), judge)

    changes = []
    for name, m in card["models"].items():
        for t in m["tasks"]:
            task = tasks.get(t["id"])
            if task is None or t.get("outcome") != "valid" or t.get("predicted") is None:
                continue
            before = t["f1"]
            g = mvs.grade_mvs(task["reference_mvs"], t["predicted"], accepted_refs=task.get("accepted_ids"))
            sample = {**{k: t[k] for k in SAMPLE_KEYS if k in t}, **{k: g[k] for k in ("f1", "precision", "recall")}}
            t.update(runner._aggregate([sample]))
            if cascade and t.get("escalation"):
                escalating_grade, render, judge = cascade
                old = t["escalation"]
                workdir = pathlib.Path(old["ref_png"]).parent if old.get("ref_png") else (
                    REPO / "runs" / f"regrade_{t['id']}" / name.replace("/", "_"))
                t["escalation"] = escalating_grade(
                    task["reference_mvs"], t["predicted"], prompt=task.get("prompt"),
                    render=render, vlm=judge, workdir=str(workdir),
                    accepted_refs=task.get("accepted_ids"))
            changes.append((name, t["id"], before, t["f1"]))
        graded = [t for t in m["tasks"] if t["category"] in runner.GRADED_CATEGORIES]
        m["mean_f1"] = round(sum(t["f1"] for t in graded) / len(graded), 4) if graded else 0.0
        m["by_category"] = runner._means_by_category(m["tasks"])
        m["by_skill"] = runner._means_by_skill(m["tasks"])
        m.update(runner._format_stats({t["id"]: [{k: t[k] for k in SAMPLE_KEYS if k in t}]
                                       for t in m["tasks"] if t["category"] == "mvs"}))
    meta.setdefault("regraded", []).append(sorted(tasks))
    path.write_text(json.dumps(card, indent=2))
    return changes


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scorecards", type=pathlib.Path, nargs="+")
    ap.add_argument("--tasks", nargs="+", required=True, help="task ids whose references changed")
    a = ap.parse_args(argv)
    runner.load_dotenv()
    tasks = {t["id"]: t for t in runner.load_tasks(None) if t["id"] in a.tasks}
    if missing := set(a.tasks) - set(tasks):
        raise SystemExit(f"unknown task ids: {sorted(missing)}")
    for path in a.scorecards:
        for name, tid, before, after in regrade(path, tasks):
            print(f"{path.parent.name}/{name.split('/')[-1]} {tid}: {before} -> {after}")


if __name__ == "__main__":
    main()
