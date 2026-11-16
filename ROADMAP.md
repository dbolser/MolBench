# MolBench — where things are

This file used to hold the plan and its history (421 lines). The history is kept in git:
`git show f9fd540:ROADMAP.md` prints the last full version. What is current lives in the files below.

| To find | Read |
|---|---|
| The plan, its decisions and the rulings made after the corpus was merged | [`FINAL_PLAN.md`](FINAL_PLAN.md) |
| What the corpus holds, the checks run on it, known weaknesses | [`CORPUS.md`](CORPUS.md) |
| How answers are graded, and the grader's control set | [`GRADING.md`](GRADING.md) |
| The task file format | [`TASK_FORMAT.md`](TASK_FORMAT.md) |
| How a run is defined, started and re-graded | [`run/README.md`](run/README.md) |
| Every open idea and old to-do, each with a disposition | [`LEDGER.md`](LEDGER.md) |
| The paper, its Supporting Information and what they still wait for | [`paper/README.md`](paper/README.md), [`paper/PENDING.md`](paper/PENDING.md) |
| The human rating study: pilot readout and the design of the next one | [`paper/a4/REPORT.md`](paper/a4/REPORT.md), [`paper/a4/FINAL_CALL.md`](paper/a4/FINAL_CALL.md) |
| Where to submit | [`paper/venues.md`](paper/venues.md) |

## What is left, in order

1. Freeze the corpus: pin its version and hash in `run/final_run.toml`, set the budget cap.
2. Rehearse: `python -m molbench.runner --manifest run/final_run.toml --dry-run` (no cost).
3. The one paid run: the same command with `--go`.
4. Rebuild the paper: `scripts/paper_tables.py`, `paper/corpus_values.py`, `paper/figures.py`,
   `paper/build.py`. `paper/PENDING.md` should then list only author decisions.
5. Second rating study on the final run's scenes (`paper/a4/FINAL_CALL.md`).
6. Deposit corpus, archives and ratings for a DOI; preprint; submit.

## Not in this paper

Open-ended requests graded by rubric, a live tool loop, viewers other than Mol\*, and the Mol\*
command layer of the next viewer version. See `FINAL_PLAN.md` (decisions 8, 9 and 14) and
`tasks_future/`.
