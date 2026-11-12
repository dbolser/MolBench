# run/ — what a benchmark run is made from

| file | what it is |
|---|---|
| `final_run.toml` | The run manifest: corpus version + hash, model panel with prices (source and date), conditions, samples, token limits, retry policy, budget cap. The only input to the run. |
| `token_calibration.json` | Per-model token rates measured on the 2026-10-18 archives; used to project cost. Rebuild with `python scripts/estimate_cost.py --calibrate <runs dir>`. |
| `site_r2x2.toml` | Renamed / not-run models of the October 2026 leaderboard build (`scripts/build_site_data.py --results`). Not used by a manifest run. |

```bash
python -m molbench.manifest run/final_run.toml                      # validate; print the corpus hash
python scripts/estimate_cost.py --tasks mvs=300 api_calling=150     # cost of a planned corpus, $0
python -m molbench.runner --manifest run/final_run.toml --dry-run   # rehearse everything, $0
python -m molbench.runner --manifest run/final_run.toml             # plan + projected cost, no calls
python -m molbench.runner --manifest run/final_run.toml --go        # the paid run (resumable)
python -m molbench.runner --manifest run/final_run.toml --grade-only   # re-grade the archive, $0
```

Where things land (`<name>` is `run.name` in the manifest):

- `runs/<name>/cells/<model>/<condition>.jsonl` — one line per model call: raw text, token
  usage, finish reason, latency, cost, prompt hash. Append-only. This is the record.
- `runs/<name>/errors.jsonl` — calls that failed every retry. They are not archived, so
  starting the same command again retries them.
- `runs/<name>/run.json` — corpus hash and one entry per start of the run.
- `results/<name>/<condition>/<model>.json` — scorecards, rebuilt from the archive.
- `results/<name>/site/` — leaderboard data files and pages built from those scorecards.
- A dry run writes to `runs/<name>.dryrun/` and `results/<name>.dryrun/` instead, and
  empties them first. Everything in them is mock data.

Before the paid run: freeze the corpus and pin `corpus.sha256`; check the prices are
current; install the `execute` extra and the Mol* bundle (`run.validate = "required"`).
The run refuses to start if any of these is missing, and stops itself when projected
spend passes `budget.cap_usd`.
