# run/ — what a benchmark run is made from

| file | what it is |
|---|---|
| `final_run.toml` | The run manifest: corpus version + hash, model panel with prices (source and date), conditions, samples, token limits, retry policy, budget cap. The only input to the run. |
| `pilot.toml` | The provider-path pilot: 39 tasks, one model per start, one sample, cap $2.25. Two routes: the direct Anthropic key, or any OpenRouter `:free` model named with `--free-model` (add `--free-model-reasoning` for one that reasons before it answers). Its commands are at the top of the file; what the pilot of 2026-11-16 found is in `PILOT.md`. |
| `select_pilot.py` | Picks the pilot's tasks by rule (every tier × track, public and held back, twins, follow-ups, accept-set, one request in three phrasings) and writes them into `pilot.toml`; `--check` says whether the list is current. |
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
python scripts/paper_tables.py --from-dry-run                       # MOCK tables -> paper/generated_mock/
python scripts/paper_tables.py --from-run results/final-v1          # the real ones -> paper/generated_final/
python scripts/paper_tables.py --from-run results/final-v1 --into-paper   # also the paper's seven tables and final_values.json -> paper/generated/
python scripts/paper_tables.py --from-run results/pilot-v1          # a pilot: its tables stay in results/pilot-v1/paper/; one labelled table -> paper/generated/pilot_results.md
python -m molbench.runner --manifest run/pilot.toml --dry-run       # rehearse the pilot, $0
```

## Run sizes (projected 2026-11-23, after the pilot fixes: 879 task files, two scripted baselines)

| size | what runs | calls | expected | cap to set | what it buys |
|---|---|---:|---:|---:|---|
| lean | core panel, every condition, `run.samples = 1` | 32,784 | $63 | $78 | every table filled once; no within-task sample spread, so no "all samples right", wider intervals, and paraphrase spread cannot be told from sampling noise |
| **recommended** (the manifest as committed) | core panel (16 models + the two scripted baselines), 3 samples; structured-output condition 1 sample | 71,982 | $138 | $165 | everything the plan decided, on the models already tracked |
| full | recommended + the five optional frontier models (`--include-optional`) | 91,647 | $496 | $610 | the same tables with a closed-frontier row from four labs and the largest open model |

One optional model at a time (`--only-models` takes manifest ids; the archive is per model,
so models can be added later without re-running the rest): claude-opus-5.5 +$142,
gpt-6.1-sol +$71, gemini-4-argon +$71, grok-4.7 +$54, deepseek-v4-pro-0813 +$20. None of
the five has measured token rates: their projection uses the highest output rate seen.

The projection is tokens × manifest price: input tokens from the real prompts, output
tokens from each model's rate on the 2026-10-18 runs. Those runs capped output at 2,000
tokens (now 8,000, and 16,000 for reasoning models), so a model that was being cut off
then (kimi-k2.6 returned an empty answer in 27 of 140 calls) will spend more now. The cap
is the guard: the run stops itself when spent + still-to-run passes it.

**Reasoning effort.** `run.reasoning_effort = "provider-default"` sends nothing, as in every
earlier run. Any other value is one setting for the whole run: it is sent unchanged to
every model flagged `reasoning = true` and archived with each call. It is not used to make
one model cheaper. A lower token limit is not a saving either: it turns reasoning into
truncated, invalid answers.

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
- **Analysis fields.** Each sample also carries, without changing any score: on a
  follow-up, the preserved score (`preserved_f1`, `preserved_ok`: the parts of the start
  state the edit had to leave alone, from `provenance.preserved`); on a resolve task,
  which kind of entry the answer loads (`entry_outcome`: accepted, a real entry of
  something else, an id that does not exist; the rule is the resolve generator's own,
  through `molbench/resolve.py`) and, on an accepted entry, whether it is the task's
  reference entry (`entry_is_reference`: other accepted entries have no atom table and
  are graded as written). Each task row carries its difficulty facts under one
  vocabulary (`molbench/difficulty.py`).
- **Samples** are per condition: `run.samples`, or a condition's own `samples`.
- **A dry run** adds the fixture tasks in `tests/fixtures/tasks/` only if the corpus has
  no follow-up, accept-set, twin, paraphrase or held-back task of its own (it has them
  all now). It also builds every paper table from its mock scorecards into
  `results/<name>.dryrun/paper/`.

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
- `paper/generated_final/` — the paper's tables, from `scripts/paper_tables.py --from-run`.
  `paper/generated_mock/` holds the same tables from the dry run: final shapes, fake
  numbers, every file flagged MOCK; the two are never written to the same directory.
  `paper/generated/` holds the October 2026 preliminary set, the provider pilot's one
  labelled table (`pilot_results.md`, `pilot_values.json`) and, once the real run is complete
  and `--into-paper` is given, the seven `table_final_*.md` files that the paper includes and
  `final_values.json` (read by `paper/build.py` as `{{final.<key>}}`). `--into-paper`
  refuses a dry run, a pilot and a run with cells missing.
- A dry run writes to `runs/<name>.dryrun/` and `results/<name>.dryrun/` instead, and
  empties them first. Everything in them is mock data.

The ordered steps from the freeze to submission, each with its command, are in
[`RELEASE_CHECKLIST.md`](../RELEASE_CHECKLIST.md).

Before the paid run: freeze the corpus and pin `corpus.sha256`; run the pilot (done on
2026-11-16, see `PILOT.md`); re-project
the cost and set `budget.cap_usd` (a test holds it between the projection and 1.5 times
it); check the prices are current (last read from OpenRouter's public model list on
2026-11-16); install the `execute` extra and the Mol* bundle (`run.validate = "required"`).
The run refuses to start if any of these is missing, and stops itself when projected
spend passes `budget.cap_usd`. It also makes every check of `scripts/validate_tasks.py`
on the corpus before its first call (each reference graded against itself, links, panel,
atom tables) and refuses to start if one fails; `--final` (no old-format task, a target
score for every reference) is run by hand at the freeze.
