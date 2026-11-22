# The MolBench paper

The paper, its Supporting Information and a plain-language summary are Markdown, one file per
section. No number is typed by hand.

```bash
uv run python paper/corpus_values.py           # task files, frozen data -> generated/corpus_values.json, tables
uv run --with matplotlib python paper/figures.py   # generated/fig_*.svg (five schematics, one chart)
python paper/build.py                          # -> molbench.md, si.md, plain_summary.md, PENDING.md
python paper/build.py --check                  # same checks, writes nothing; exit 1 if anything is stale or wrong
python paper/build.py --pdf                    # also HTML and PDF of the paper and the SI (pandoc + Chromium)
```

After a model run: `uv run scripts/paper_tables.py` (archives → `generated/values.json` and the
result tables), then the three commands above.

| File | What it is |
|---|---|
| `sections/*.md` | The paper. Title 11 words; abstract at most 200 words (checked by the build). The build also checks that the running example is shown with the colour and representation of its request in the generated table and figures. |
| `si/*.md` | Supporting Information S1–S8: running example in full, templates, panel, grading rules, control set, manifest and models, prompts, pilot-run tables. |
| `plain/summary.md` | A 150-word summary for volunteer raters, to paste into an email (length checked by the build). |
| `molbench.md`, `si.md`, `plain_summary.md` | Built. Do not edit; edit the sources. |
| `PENDING.md` | Built. Every PENDING tag with what fills it, and the files the final run must write. |
| `corpus_values.py` | Every number that does not come from a model run: corpus counts, panel and variant facts, control set, the October answers regraded, the pilot rating study, the run plan, the running example graded by the benchmark's grader. Also writes the corpus table, the empty result tables (`generated/shape_*.md`) and the SI tables. `--check` fails if a committed file is stale. |
| `figures.py` | Schematic figures as plain SVG (pipeline, tiers, paired design, drawn-state grading, shapes of the result figures) and the chart of the pilot run. Okabe–Ito colours; every mark also has a label or a pattern. |
| `generated/` | Output of the scripts, committed so the paper builds without the git-ignored archives. `values.json` and the `table_mvs_*`/`fig_mvs_*` files are written by `scripts/paper_tables.py` and `scripts/paper_figures.py` from the October 2026 pilot run. |
| `inputs.json` | Which archives `scripts/paper_tables.py` reads. |
| `references.bib`, `related_work_checks.md` | References, and the record of how each was verified. |
| `a4/` | The pilot rating study (readout) and the design of the next one. |
| `venues.md` | Where to submit, with checked requirements. |
| `REVIEW_LOG.md` | Clarity reviews of the manuscript, round by round: scores, what changed, what was declined and why. |

## Markers in the sources

- `{{key}}`, `{{key:.1%}}`: a value from `generated/values.json` or `generated/corpus_values.json`.
  An unknown key is an error; so is a key in both files.
- `{{include:generated/x.md|pilot:Table S7}}`: a pilot table of SI Section S8, shown with that
  table number and in the words of the paper (`PILOT_WORDS` in `build.py` maps words, never
  numbers).
- `{{include:generated/x.md}}`: a generated table. `{{include:generated/table_final_x.md|else:generated/shape_x.md}}`
  shows the table in its final shape, with pending cells, until the final run writes the real one.
- `[@key]`: a citation from `references.bib`.
- `⟦PENDING: owner — what⟧`: something still open. The first words name what fills it: `final run`,
  `corpus freeze`, `rating study`, `deposit` or `Dan`. A tag that starts in another way fails the build.

## What the final run has to write

`scripts/paper_tables.py` should write these files into `generated/`; each replaces the
shape table of the same name, and the captions in `sections/07_results.md` already define every
column:

`table_final_leaderboard_scene.md`, `table_final_leaderboard_calls.md`, `table_final_tiers.md`,
`table_final_paired.md`, `table_final_clinical.md`, `table_final_followup.md`,
`table_final_robustness.md`. The three result figures (`fig_result_shapes.svg` shows their
layout) are then drawn from the same archive.

The October pilot numbers are reported in Section 6.6 of the paper (boxed) and in SI Section S8;
where another section cites one, it says that it is a pilot result.

## Words and table numbers (review round 2)

The paper says *category* where the repository says tier, *style* where `GRADING.md` says
draw, *format guide* for the vendored reference in the system prompt, *main* for the `spec`
condition, *structure panel* for the 79 structures and *core / optional models* for the
models. The clinical results are grouped by *copying the number* (primary) and by *offset*.
Tables: 1 corpus, 2 clinical groupings, 3 running example, 4 control set, 5 conditions,
6 and 7 per model, 8 categories, 9a and 9b pairs, 10 clinical, 11 follow-up, 12 planned
comparisons, 13 what changed, 14 licences. The final tables that `scripts/paper_tables.py`
writes must use the column names of `generated/shape_*.md`.
