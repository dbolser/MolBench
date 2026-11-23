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
| What the provider pilot of November 2026 found and changed | [`PILOT.md`](PILOT.md) |
| **Every step from here to submission, with its command** | [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) |
| Every open idea and old to-do, each with a disposition | [`LEDGER.md`](LEDGER.md) |
| The paper, its Supporting Information and what they still wait for | [`paper/README.md`](paper/README.md), [`paper/PENDING.md`](paper/PENDING.md) |
| The human rating study: pilot readout, the plan of the next one and its runbook | [`paper/a4/REPORT.md`](paper/a4/REPORT.md), [`paper/a4/FINAL_CALL.md`](paper/a4/FINAL_CALL.md), [`paper/a4/RATING_V2_RUNBOOK.md`](paper/a4/RATING_V2_RUNBOOK.md) |
| Where to submit | [`paper/venues.md`](paper/venues.md) |

## Where things stand (2026-11-23)

Built and checked at no cost: the corpus (879 task files, 78 structures), both graders with
their control set, the runner with its manifest and dry run, the paper draft with every
result cell marked as pending, and the tooling of the second rating study. A provider pilot
on 39 tasks (US $0.21) proved the path to a provider and led to eight fixes (`PILOT.md`).
Nothing is frozen yet: the corpus has no tag and its hash is not pinned.

## What is left, in order

The steps and their commands are in [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md). In short:

1. Rule on the open points, then freeze the corpus (tag, pinned hash, budget cap).
2. Top up the provider account; rehearse; the one paid run.
3. Tables into the paper; write the result sentences; rebuild.
4. Second rating study on the final run's scenes.
5. Deposit corpus, archives and ratings for a DOI; preprint; submit.

## Not in this paper

Open-ended requests graded by rubric, a live tool loop, viewers other than Mol\*, and the Mol\*
command layer of the next viewer version. See `FINAL_PLAN.md` (decisions 8, 9 and 14) and
`tasks_future/`.
