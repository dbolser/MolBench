#!/usr/bin/env python3
"""
Check the whole task corpus against the task format (TASK_FORMAT.md). $0, no network.

    python scripts/validate_tasks.py                      # tasks/
    python scripts/validate_tasks.py --final              # what the frozen corpus must pass
    python scripts/validate_tasks.py tests/fixtures/tasks # any other task directory

What is checked:

* every file against the schema (`molbench.tasks.validate_task`); every file's
  errors are listed, not only the first;
* ids are unique; `twin_of` is mutual, across tracks, with the same prompt, structures,
  split and target atoms; a paraphrase names an original with the same answer;
* every structure is in the panel and has a frozen atom table; a held-back structure
  is used by no public task;
* every reference grades as exactly right against its own task (success, F1 = 1 and -
  once the grader reports it - target score 1); every accepted alternative grades as
  itself, is accepted by its task and, in the accept-set tier, is a different final
  state from the reference;
* a follow-up's start state grades as itself, and its `noop` flag says what the
  grader says (the start state already is / is not the requested final state);
* no task uses 1HSG, the structure of the API prompt's worked example.

``--final`` also refuses tasks in the old format and tasks the grader gives no target
score for. Exit status 1 if any check fails.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import runner, tasks as T  # noqa: E402


def load_all(tasks_dir: pathlib.Path) -> tuple[list[dict], list[str]]:
    """Every task that loads, and one error line per file that does not."""
    tasks, errors = [], []
    for path in sorted(tasks_dir.rglob("*.json")):
        try:
            task = T.load_task(path)
        except T.TaskError as e:
            errors.append(str(e))
            continue
        if task is not None:
            tasks.append(task)
    return tasks, errors


def summary(tasks: list[dict]) -> list[str]:
    lines = []
    for track in T.TRACKS:
        mine = [t for t in tasks if t["track"] == track]
        tiers = Counter(t["tier"] for t in mine)
        lines.append(f"  {track:<4} {len(mine):>4} tasks   "
                     + ", ".join(f"{tier} {n}" for tier, n in sorted(tiers.items())))
    kinds = runner.kinds_present(tasks)
    lines.append("  kinds: " + "; ".join(
        f"{kind} {per['mvs']} MVS / {per['api_calling']} API" for kind, per in kinds.items()))
    structures = {s for t in tasks for s in t["structures"]}
    held = {s for t in tasks if t["split"] == "heldback" for s in t["structures"]}
    lines.append(f"  structures: {len(structures)} ({len(held)} held back)   "
                 f"families: {len({t['family'] for t in tasks})}   "
                 f"old-format tasks: {sum(bool(t.get('_legacy')) for t in tasks)}")
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tasks_dir", nargs="?", type=pathlib.Path, default=T.TASKS_DIR)
    ap.add_argument("--final", action="store_true",
                    help="also refuse old-format tasks and tasks with no target score")
    ap.add_argument("--no-grade", action="store_true",
                    help="skip the checks that run the grader (schema and links only)")
    a = ap.parse_args(argv)

    tasks, errors = load_all(a.tasks_dir)
    more, notes = T.check_corpus(tasks, grade=None if a.no_grade else runner.grade_parsed,
                                 final=a.final,
                                 check=None if a.no_grade else runner.grader_problems)
    errors += more
    print(f"{a.tasks_dir}: {len(tasks)} tasks read")
    for line in summary(tasks):
        print(line)
    for n in notes:
        print(f"  note: {n}")
    if not runner.grader_grades_mvs() and not a.no_grade:
        print("  note: MVS references were graded by mvs.grade_mvs (grader.grade_task does not "
              "grade the MVS track yet)")
    if errors:
        print(f"\n{len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nOK: every check passed" + (" (final)" if a.final else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
