# data/october — the task corpus of the October 2026 run

`tasks/` here is the `tasks/` directory as it stood before the final corpus was built
(commit 12f1a49, 2026-11-12): the 70 MVS tasks, the 20 API tasks and the 2 visual-rubric
tasks. It is frozen. Nothing in the final benchmark reads it; it exists so that the
October numbers stay reproducible after the corpus was replaced:

- `paper/inputs.json` (`tasks_dir`) — the October tables of `scripts/paper_tables.py`;
- `scripts/build_site_data.py --results` — the October leaderboard data files.

The benchmark's own tasks are in `/tasks` (see `CORPUS.md`).
