# run/ — what a benchmark run is made from

| file | what it is |
|---|---|
| `final_run.toml` | The run manifest: corpus version + hash, model panel with prices (source and date), conditions, samples, token limits, retry policy, budget cap. The only input to the run. |
| `token_calibration.json` | Per-model token rates measured on the 2026-10-18 archives; used to project cost. Rebuild with `python scripts/estimate_cost.py --calibrate <runs dir>`. |
| `site_r2x2.toml` | Renamed / not-run models of the October 2026 leaderboard build (`scripts/build_site_data.py --results`). Not used by a manifest run. |

```bash
python -m molbench.manifest run/final_run.toml                      # validate; print the corpus hash
python scripts/validate_tasks.py                                    # the corpus against TASK_FORMAT.md
python scripts/estimate_cost.py --tasks mvs=450 api_calling=250     # cost of a planned corpus, $0
python -m molbench.runner --manifest run/final_run.toml --dry-run   # rehearse everything, $0
python -m molbench.runner --manifest run/final_run.toml             # plan + projected cost, no calls
python -m molbench.runner --manifest run/final_run.toml --go        # the paid run (resumable)
python -m molbench.runner --manifest run/final_run.toml --grade-only   # re-grade the archive, $0
```

What a run sends and scores:

- **Tasks** are read through `molbench.tasks` (format: `TASK_FORMAT.md`). A task whose
  structure has no atom table is refused when the run is planned.
- **Conditions and tiers.** `spec` and `spec_structured` take every task of both tracks,
  public and held-back alike. `spec_grounded` takes the lookup tiers only (`resolve`,
  `clinical`), MVS track, tasks that carry a grounding pack. `bare` is MVS only.
- **Prompts.** One system prompt per track (`prompts/`). A single-turn request is sent
  as it is; a follow-up is sent as the current scene (MVS) or the calls made so far
  (API), then `Request: ...`, and the answer is the full new scene / call list.
- **Model panel.** The rule is written in the manifest (`[panel] rule`). The keyword
  baseline (`baseline-rules`, no model call) is a panel member on both tracks.
- **Scores.** Every answer goes to `grader.grade_task`. Reported per model, track, tier
  and split: strict F1; task success as the mean over samples (`success`) and as the
  share of tasks with every sample right (`success_all`); the target score
  (`target_f1`, once the grader reports it); the valid-output rate on both tracks; and
  outputs cut off at the token limit counted apart from malformed ones (`not_valid`).
- **A dry run** adds the fixture tasks in `tests/fixtures/tasks/` while the corpus has
  no follow-up, accept-set, twin, paraphrase or held-back task of its own, so those
  paths are rehearsed too. They are left out of the cost projection.

Where things land (`<name>` is `run.name` in the manifest):

- `runs/<name>/cells/<model>/<condition>.jsonl` — one line per model call: raw text, token
  usage, finish reason, latency, cost, token limit, serving provider, prompt hash.
  Append-only. This is the record.
- `runs/<name>/LOCK` — held while a run writes the archive; a second start on the same
  archive is refused instead of archiving every cell twice.
- `runs/<name>/errors.jsonl` — calls that failed every retry. They are not archived, so
  starting the same command again retries them.
- `runs/<name>/run.json` — corpus hash and one entry per start of the run.
- `results/<name>/<condition>/<model>.json` — scorecards, rebuilt from the archive.
- `results/<name>/samples/<condition>/<model>.jsonl` — one line per sample with call and
  grade together: predicted text, parsed prediction, F1, success, target score, outcome,
  finish reason, tokens, cost, latency, temperature, token limit, serving provider,
  prompt hash. Rebuilt from the archive on every grading.
- `results/<name>/site/` — leaderboard data files and pages built from those scorecards.
- A dry run writes to `runs/<name>.dryrun/` and `results/<name>.dryrun/` instead, and
  empties them first. Everything in them is mock data.

Before the paid run: freeze the corpus and pin `corpus.sha256`; check the prices are
current; install the `execute` extra and the Mol* bundle (`run.validate = "required"`).
The run refuses to start if any of these is missing, and stops itself when projected
spend passes `budget.cap_usd`.
