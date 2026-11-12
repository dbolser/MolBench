# The MolBench paper

The paper is Markdown, one file per section in `sections/`. No result is typed by hand.

```bash
uv run scripts/paper_tables.py     # archives -> paper/generated/ (values.json, table_*.md, figdata.json)
uv run scripts/paper_figures.py    # figdata.json -> paper/generated/fig_*.svg and .pdf
python paper/build.py              # sections + generated -> paper/molbench.md and paper/PENDING.md
python paper/build.py --pdf        # also molbench.html and molbench.pdf (needs pandoc and Chromium)
```

The first two scripts carry their own dependencies (`json-repair`, `matplotlib`) as inline
script metadata, so `uv run <script>` is enough. `paper/build.py` uses the standard library only.

| File | What it is |
|---|---|
| `inputs.json` | The manifest: which scorecards, raw archives and task directory the numbers come from, the headline condition, model aliases and weight licences. **To rebuild on the final run, point this at the final archives (or pass `--manifest`); the scripts do not change.** Set `"status": "final"` to drop the PRELIMINARY labels. |
| `generated/` | Output of the two scripts. Committed, so the paper builds without the git-ignored archives. `provenance.json` records the inputs, code version and bootstrap seed. |
| `sections/*.md` | The text. `{{key}}` takes a value from `generated/values.json` (optionally `{{key:.3f}}`); `{{key\|PENDING: what}}` shows a PENDING tag until the key exists; `{{include:generated/table_x.md}}` pulls in a table; `[@key]` cites `references.bib`. |
| `molbench.md` | The built paper. Do not edit; edit the sections. |
| `PENDING.md` | Every PENDING tag in the built paper, and the keys and files the final run must supply. Generated. |
| `references.bib` | References. Every entry was verified; see `related_work_checks.md`. |
| `venues.md` | Where to submit, with checked requirements. |

Input paths in the manifest are looked up in this checkout first, then under `--data-root`
(default: the main git checkout, which holds the git-ignored `results/` and `runs/`).

What the scripts expect of a run: one scorecard JSON per model and condition, with
`meta.condition`, `meta.grounding` (and optionally `meta.condition_label`, `meta.run_id`), and
task rows carrying `id`, `category` (the track), `samples_f1` and `outcomes`. Raw archives
carry `raw_samples[model][task] = [{"raw": …}]` and are matched to scorecards by `run_id`, or
by start time and model. A task's regime comes from its `regime` field, else from its `source`.
