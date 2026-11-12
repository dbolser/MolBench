#!/usr/bin/env python3
"""
Re-grade the surviving July 2026 API-track answers with the state grader. Costs $0.

``docs/scorecard.json`` keeps, per model and task, the July F1 of each of the three
samples and the answer of the **best** sample (the raw outputs are gone). This script
grades those kept answers against today's tasks with ``molbench/pdbe_state.py`` and
prints, per model, the July F1 next to the new F1 and the new strict task success.

Read the table with two cautions, both printed with it:

* **Upward bias.** The kept answer is the best of three *as the July grader scored
  it*. New-grader numbers on it are therefore not a model's expected score; they are
  closer to a ceiling, and a ceiling chosen by a metric we now know was wrong (it
  preferred, for example, label-numbered answers that select the wrong residues).
* **The tasks changed.** Only tasks whose prompt is unchanged (``provenance.july_task
  == "unchanged"``) are a like-for-like re-grade. Reworded tasks ask for something
  slightly different from what the answer was written for, and replaced tasks are
  left out altogether.

Also bear in mind that in July the models were shown an API reference that taught
label numbering for author-numbered residues and never mentioned
``representationColor``; some of the failures below are that document's.

    python scripts/regrade_api.py                       # table
    python scripts/regrade_api.py --json out.json       # + machine-readable results
    python scripts/regrade_api.py --scorecard path.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import grader  # noqa: E402

TASKS = REPO / "tasks" / "api_calling"
DEFAULT_SCORECARD = pathlib.Path("/home/danbolser/Build/MolBench/docs/scorecard.json")
GROUPS = ("unchanged", "reworded")


def load_tasks() -> dict[str, dict]:
    return {t["id"]: t for t in (json.loads(p.read_text()) for p in sorted(TASKS.glob("*.json")))}


def regrade(scorecard: dict, tasks: dict[str, dict]) -> dict[str, dict]:
    """model -> {task id -> {july_mean, july_best, f1, success, status, legacy_f1}}."""
    out: dict[str, dict] = {}
    for model, entry in scorecard["models"].items():
        rows = {}
        for rec in entry["tasks"]:
            if rec.get("category") != "api_calling" or rec["id"] not in tasks:
                continue
            task = tasks[rec["id"]]
            status = task["provenance"]["july_task"]
            pred = rec.get("predicted")
            row = {"status": status, "july_mean": rec.get("f1", 0.0),
                   "july_best": rec.get("f1_max", rec.get("f1", 0.0)),
                   "has_answer": pred is not None}
            if status != "replaced":
                new = grader.grade_task(task, pred) if pred is not None else \
                    {"f1": 0.0, "success": False}
                old = grader.grade_sequence(task["reference"], pred) if pred is not None else {"f1": 0.0}
                row.update(f1=new["f1"], success=bool(new["success"]), legacy_f1=old["f1"],
                           unresolved=len(new.get("unresolved", [])))
            rows[rec["id"]] = row
        out[model] = rows
    return out


def _mean(xs: list[float]) -> float:
    return statistics.fmean(xs) if xs else float("nan")


def summarise(results: dict[str, dict]) -> list[dict]:
    table = []
    for model, rows in results.items():
        line = {"model": model,
                "july_mean_all": _mean([r["july_mean"] for r in rows.values()]),
                "july_best_all": _mean([r["july_best"] for r in rows.values()])}
        for group in GROUPS + ("both",):
            sel = [r for r in rows.values()
                   if (r["status"] in GROUPS if group == "both" else r["status"] == group)]
            line[group] = {"n": len(sel),
                           "july_mean": _mean([r["july_mean"] for r in sel]),
                           "july_best": _mean([r["july_best"] for r in sel]),
                           "legacy_on_new_refs": _mean([r["legacy_f1"] for r in sel]),
                           "f1": _mean([r["f1"] for r in sel]),
                           "success": sum(r["success"] for r in sel)}
        table.append(line)
    table.sort(key=lambda x: (-x["unchanged"]["success"], -x["unchanged"]["f1"]))
    return table


def print_table(table: list[dict], results: dict[str, dict], tasks: dict[str, dict]) -> None:
    n_un = table[0]["unchanged"]["n"]
    n_re = table[0]["reworded"]["n"]
    print(f"July answers (best of 3 under the July grader), re-graded by final viewer state.\n"
          f"Columns: July F1 as published (mean of 3, all 20 July tasks) | then for the {n_un} "
          f"tasks whose prompt is\nunchanged: July F1 of the kept (best) answer, new state F1, "
          f"tasks solved | the same for the {n_re} reworded tasks.\n")
    head = (f"{'model':36} {'July':>6} | {'July best':>9} {'new F1':>7} {'solved':>7} "
            f"| {'July best':>9} {'new F1':>7} {'solved':>7}")
    print(head)
    print(f"{'':36} {'all 20':>6} | {'unchanged prompts (' + str(n_un) + ')':>25} "
          f"| {'reworded prompts (' + str(n_re) + ')':>25}")
    print("-" * len(head))
    for line in table:
        u, r = line["unchanged"], line["reworded"]
        print(f"{line['model'][:36]:36} {line['july_mean_all']:6.3f} | {u['july_best']:9.3f} "
              f"{u['f1']:7.3f} {u['success']:>4}/{u['n']:<2} | {r['july_best']:9.3f} "
              f"{r['f1']:7.3f} {r['success']:>4}/{r['n']:<2}")
    print("\nPer task: models (of {}) whose kept answer is solved / mean new F1 / mean July best F1"
          .format(len(results)))
    for tid, task in tasks.items():
        status = task["provenance"]["july_task"]
        if status == "replaced":
            print(f"  {tid}  replaced   (July answers were written for a different task)")
            continue
        rows = [results[m][tid] for m in results if tid in results[m]]
        print(f"  {tid}  {status:9}  solved {sum(r['success'] for r in rows):>2}/{len(rows)}   "
              f"new F1 {_mean([r['f1'] for r in rows]):.3f}   "
              f"July best {_mean([r['july_best'] for r in rows]):.3f}")
    print(
        "\nCautions.\n"
        "1. Upward bias: each kept answer is the best of three samples as the JULY grader ranked\n"
        "   them. The new numbers are not expected scores; they sit near a ceiling, and one\n"
        "   picked by the old metric. The other two samples per task are lost.\n"
        "2. Only the unchanged-prompt columns are like for like. Reworded prompts ask for\n"
        "   something slightly different from what the answer was written for; replaced tasks\n"
        "   are not graded.\n"
        "3. In July the models saw an API reference that taught label numbering for\n"
        "   author-numbered residues and did not document representationColor.\n"
        "4. baseline-rules is the keyword script (no model).")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scorecard", type=pathlib.Path, default=DEFAULT_SCORECARD)
    ap.add_argument("--json", type=pathlib.Path, help="also write the per-task results here")
    args = ap.parse_args()
    tasks = load_tasks()
    results = regrade(json.loads(args.scorecard.read_text()), tasks)
    table = summarise(results)
    print_table(table, results, tasks)
    if args.json:
        args.json.write_text(json.dumps({"per_task": results, "per_model": table}, indent=1))


if __name__ == "__main__":
    main()
