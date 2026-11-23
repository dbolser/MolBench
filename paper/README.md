# The MolBench paper

The paper, its Supporting Information and a plain-language summary are Markdown, one file per
section. No number is typed by hand.

```bash
uv run python paper/corpus_values.py           # task files, frozen data -> generated/corpus_values.json, tables
uv run --with matplotlib python paper/figures.py   # generated/fig_*.svg (five schematics, one chart)
uv run --with matplotlib python paper/figures.py --viewer-strip   # only when the running example changes: the three Mol* pictures of Figure 4
python paper/build.py                          # -> molbench.md, si.md, plain_summary.md, PENDING.md
python paper/build.py --check                  # same checks, writes nothing; exit 1 if anything is stale or wrong
python paper/build.py --pdf                    # also HTML and PDF of the paper and the SI (pandoc + Chromium)
```

After a model run: `uv run scripts/paper_tables.py` (archives → `generated/values.json` and the
result tables), then the three commands above.

| File | What it is |
|---|---|
| `sections/*.md` | The paper: about 9,300 words of text (the brief is 8,000 to 9,500; `build.py` prints the count). What a reader does not need in order to follow what was built, why, and how an answer is scored is in SI Sections S10 to S15, with a one-sentence pointer in the paper. Title 11 words; abstract at most 200 words (checked by the build). The build also checks that the running example is shown with the colour and representation of its request in the generated table and figures. |
| `si/*.md` | Supporting Information S0–S15. S0 to S9: glossary (Tables S0a to S0f; S0d to S0f are the full glossaries that were Boxes 1 and 2 of the paper), running example in full, templates, panel and variant list, grading rules, control set, manifest, models and provider pilot, prompts, pilot-run tables with the trial of the rating study, and the place for the final-run tables. S10 to S15 (`sa10_*.md` to `sa15_*.md`; the file names sort after `s9_`) hold the long form of the paper's Sections 3 to 5, the six pilot findings and the nine errors of the first version, the limitations in full, related work in detail and the licences. SI tables are numbered S0 to S24 in order (S4 the variant list, S8 to S19 the pilot tables, S20 further properties of the clinical tasks, S21 and S22 the pilot run regraded per model and per category, S23 the nine errors with how each was found, S24 licences). |
| `plain/summary.md` | A 150-word summary for volunteer raters, to paste into an email (length checked by the build). |
| `molbench.md`, `si.md`, `plain_summary.md` | Built. Do not edit; edit the sources. |
| `PENDING.md` | Built. Every PENDING tag with what fills it, and the files the final run must write. |
| `corpus_values.py` | Every number that does not come from a model run: corpus counts, panel and variant facts, control set, the October answers regraded, the pilot rating study, the run plan, the running example graded by the benchmark's grader. Also writes the corpus table, the empty result tables (`generated/shape_*.md`) and the SI tables. `--check` fails if a committed file is stale. |
| `figures/fig5_layout.md` | The line that shows Figure 5 as a layout sketch. The paper includes `generated/fig_final_results.md` in its place once `scripts/paper_figures.py --result-figure paper/generated` has drawn the figure from the final tables. |
| `figures.py` | Schematic figures as plain SVG (pipeline, tiers, paired design, drawn-state grading, shapes of the result figures) and the chart of the pilot run. Okabe–Ito colours; every mark also has a label or a pattern. The schematics are 660 px wide, the width at which the PDF prints them, and the script refuses in-figure text below 9.5 px (7 pt in print). |
| `generated/` | Output of the scripts, committed so the paper builds without the git-ignored archives. `values.json` and the `table_mvs_*`/`fig_mvs_*` files are written by `scripts/paper_tables.py` and `scripts/paper_figures.py` from the October 2026 pilot run. |
| `generated/viewer_strip/` | The three pictures at the top of Figure 4 (reference, Answer A, Answer B of the running example), rendered by headless Mol\* from one camera, and `record.json` with the hash of the scenes they were rendered from. Rendering needs a browser and the Mol\* bundle (`scripts/fetch_molstar.py`, `playwright install chromium`), so the pictures are committed and `figures.py` only embeds them; it stops if the running example has changed since. |
| `generated/viewer_sample.json` | How many call-list controls were in the sample replayed in PDBe Mol\*. The record of that check counts call lists, not controls; `uv run python paper/corpus_values.py --viewer-sample` works the number out from the record and the control set of the same commit (it needs the git history) and writes this file. `corpus_values.py` reads it and stops if it no longer fits the record. Run the command again whenever `tests/controls/viewer_check.json` changes. |
| `inputs.json` | Which archives `scripts/paper_tables.py` reads. |
| `references.bib`, `related_work_checks.md` | References, and the record of how each was verified. |
| `a4/` | The pilot rating study (readout) and the design of the next one. |
| `venues.md` | Where to submit, with checked requirements. |
| `REVIEW_LOG.md` | Clarity reviews of the manuscript, round by round: scores, what changed, what was declined and why. |

## Markers in the sources

- `{{key}}`, `{{key:.1%}}`: a value from `generated/values.json` or `generated/corpus_values.json`.
  An unknown key is an error; so is a key in both files. Three specs are the build's own:
  `{{key:word}}` writes a count below ten as a word ("three times"), `{{key:date}}` writes an
  ISO date as "13 November 2026", and `{{key:month}}` as "November 2026".
- `{{final.key}}`: a value of the final run, for the result sentences of the prose. The file
  `generated/final_values.json` is written by `scripts/paper_tables.py --from-run
  results/final-v1 --into-paper`; until it exists, no such key can be used. The key names are
  those of `generated_mock/values.json`.
- `{{include:generated/pilot_results.md}}`: the one table of the provider pilot (SI Section
  S6.1), written by `scripts/paper_tables.py --from-run results/pilot-v1`. The paper calls
  this the *provider pilot*; the *pilot run* is the October 2026 run of the first version.
- `{{include:generated/x.md|pilot:Table S8}}`: a pilot table of SI Section S8, shown with that
  table number and in the words of the paper (`PILOT_WORDS` in `build.py` maps words, never
  numbers).
- `{{include:generated/x.md}}`: a generated table. `{{include:generated/table_final_x.md|else:generated/shape_x.md}}`
  shows the table in its final shape, with pending cells, until the final run writes the real one.
- `[@key]`: a citation from `references.bib`.
- `⟦PENDING: owner — what⟧`: something still open. The first words name what fills it: `final run`,
  `corpus freeze`, `rating study`, `deposit` or `Dan`. A tag that starts in another way fails the build.

## What the final run has to write

`scripts/paper_tables.py --from-run results/final-v1 --into-paper` writes these files into
`generated/` (`Tables.final` in `molbench/analysis.py`; a dry run, a pilot and an incomplete
run are refused). Each replaces the shape table of the same name and has its columns and row
labels, which a test holds; the captions in `sections/07_results.md` define every column:

`table_final_leaderboard_scene.md`, `table_final_leaderboard_calls.md`, `table_final_tiers.md`,
`table_final_paired.md`, `table_final_clinical.md`, `table_final_followup.md`,
`table_final_robustness.md`. The result figure (Figure 5; `fig_result_shapes.svg` shows its
layout) is then drawn from four of these tables by
`uv run scripts/paper_figures.py --result-figure paper/generated`, which also writes
`fig_final_results.md`, the line the paper includes. The same command on
`paper/generated_mock` draws the figure from the dry-run tables; it is stamped as mock and is
refused in `paper/generated`.

The October pilot numbers are reported in Section 6.6 of the paper (boxed) and in SI Section S8;
where another section cites one, it says that it is a pilot result.

## Words and table numbers (review rounds 2 to 6, and the condensing pass)

The paper says *category* where the repository says tier, *set-aside split* for the `heldback` split (the other tasks have no name: "tasks on the other structures"), *mature-protein numbering* for the numbering of a traditional name, *style* where `GRADING.md` says
draw, *format guide* for the vendored reference in the system prompt, *main* for the `spec`
condition, *structure panel* for the 79 structures and *core / optional models* for the
models. The clinical results are grouped by *copying the number* and, for description, by *offset*. Categories are listed in one order everywhere (`TIERS` in `corpus_values.py`).

**The target score has one wording, and it must stay one.** Long form (Section 4.2, Table 3,
SI Sections S1 and S4.3, SI Table S0f): "how exactly the answer marks out the requested atoms.
It is 1 (*target-right*) when they carry the requested style, no other atom carries that
style, and no other representation is drawn on them alone; any other drawing, such as a
cartoon of the protein, is ignored." Short form (abstract, other captions): "how exactly the
answer marks out the requested atoms; any other drawing is ignored." Both agree with every
row of Table 3. Task success and F1 are each defined once, in Section 4.2, and repeated only
in captions.

Section numbers of the paper are kept stable (3.1 to 3.7, 4.1 to 4.6, 5.1 to 5.6, 6.1 to 6.6,
7 to 12), because the generated tables and the SI cite them. Section 9 has no subsections;
the four groups of limitations are SI Sections S14.1 to S14.4.
Tables: 1 corpus, 2 clinical groupings, 3 running example (rows S1 to S10 and C1 to C7; the
text cites them through `{{ex.row.*}}`), 4 control set, 5 conditions, 6 and 7 per model,
8 categories, 9a and 9b pairs, 10 clinical, 11 follow-up, 12 planned comparisons, 13 the nine
errors of the first version (short form). Figures: 1 pipeline, 2 categories, 3 pair, 4 grading,
5 results (layout until the final run), 6 pilot run. One box of terms, Box 1, at the start of
Section 3. The final tables that `scripts/paper_tables.py` writes must use the column
names of `generated/shape_*.md`. In particular, Table 9a is on the pairs that have a target
score (250 of 258) and Table 9b on all pairs, and Table 8 has one header row per track.

Three checks of the build keep prose and numbers together: the running example must look the
same in its table and figures; a number that the prose states in words (`STATED_IN_WORDS` in
`build.py`, for example "a single structure") must still have that value; and
`corpus_values.py` asserts each fact that a sentence states without a number (which proteins
have no task, where the multi-variant tasks sit in Table 2, what the format guides document).
A column of a pipe table is as wide as its run of dashes in the header rule, relative to the
others; the generators set these so that text columns are wide and number columns narrow.
