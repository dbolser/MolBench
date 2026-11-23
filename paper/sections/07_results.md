## 6. Results

The only results that exist today come from the *first version* of the benchmark: the
corpus and the two text-comparing graders that were public from May 2026 until the present
corpus replaced them. Its run of the scene tasks in October 2026 is the *pilot run*, whose
results are kept apart in the box of Section 6.6. Sections 6.1 to 6.5 show the tables that
the final run will fill; their layout and captions are fixed, and a script fills the cells.


{{include:generated/fig_final_results.md|else:figures/fig5_layout.md}}

### 6.1 Models on both tracks

**Table 6. Scene track, main condition.** One row per model; † marks an optional model.
*Valid answers*: share of
answers that parse and that the viewer accepts. *Task success rate*: share of answers whose
drawn state is exactly right. *Target score* (0 to 1): how exactly the answer marks out the
requested atoms; any other drawing is ignored. *F1* (0 to 1): how much of the drawn state
is right. *Strict*: every answer counts, an unshowable one as 0. *Valid-only*: the mean over
the model's valid answers. *All-{{plan.samples}}
rate*: share of tasks on which all {{plan.samples}} answers are exactly right. *Cost*: US
dollars for all calls of the model in this condition, at list price. Scores will carry 95%
intervals (structures resampled).

{{include:generated/table_final_leaderboard_scene.md|else:generated/shape_leaderboard.md}}

**Table 7. Call-list track, main condition.** Columns as in Table 6, except that a *valid
answer* is a JSON list in which every call and field is documented, and a schema-breaking
call list keeps, under *strict*, the scores it earns when replayed (Section 4.4).

{{include:generated/table_final_leaderboard_calls.md|PENDING: final run — the table for the call-list track, in the shape of Table 6}}

### 6.2 Categories

**Table 8. Scores by category and track**, mean over the models. *Structures*: the number of
structures under the tasks of the row, which are the units resampled for its intervals.
Scores as in Table 6. The two rows marked *of which* divide the answers of the
name-resolution category by the entry that the model chose (Section 4.1); they are sets of
answers, so they have no number of tasks. An answer on an entry that the task does not
accept, or that loads none, scores 0 and is in the category row only.

{{include:generated/table_final_tiers.md|else:generated/shape_tiers.md}}

### 6.3 The same request in two formats

**Table 9. Paired comparison of the two formats.** For each model, its pairs fall into four
cells. A side is *right* when at least 2 of
its {{plan.samples}} answers are right. *Table 9a* (primary): an answer is right when it is
target-right (a target score of exactly 1, Section 4.2), which is the same test in both
formats.
*Table 9b* (secondary): an answer is right when it is a task success, which is not the same
test in the two formats (Section 4.2). An unshowable answer is not right. *McNemar p*: exact
test that the two one-sided counts are equal. *Difference*: pairs right in the scene only
minus pairs right in the call list only, as a share of the pairs, with a 95% interval
(structures resampled).

{{include:generated/table_final_paired.md|else:generated/shape_paired.md}}

Where both formats demand the same knowledge, a pair that is target-right on one side only
points to the format, and a pair that is wrong on both sides is a candidate for an error of
content. Clinical pairs must be read differently: there a right call list does not show
that the model knew the residue, because the viewer can do the mapping (Section 3.4). The
counts without the clinical pairs are the cleaner test of the formats.
⟦PENDING: final run — the same counts without the clinical pairs, and without the {{corpus.twins.need_hide_toggle}} pairs whose reference call list switches off part of the default view (Section 3.4); and, in the SI, the one-sided pairs divided by whether the side that was not right was unshowable⟧

### 6.4 Clinical variants

**Table 10. Clinical tasks on the scene track, grouped by whether copying the number is
right.** On this track the model must map the number itself. *Target score* (the primary
score of this table) and *task success rate* as in Table 6; both are strict means over the
models. *With grounding pack*: the mapped residue is
appended to the request. The first five rows are the two groupings of the same {{clin.n}}
tasks (Table 2, Box 1); the last three are subsets. *Matched tasks*: the same variant asked
on a structure with an offset and on a predicted structure without one (descriptive only).
*Helix or strand requested*: Section 3.3.1.

{{include:generated/table_final_clinical.md|else:generated/shape_clinical.md}}

This table will answer the question of the Introduction. Four patterns are possible in its first two rows. We state them
before the run and do not predict which one a model will show.

1. *Copying.* The target score is high where copying is right and low where it is wrong.
2. *Mapping.* The target score is high in both rows.
3. *Always converting.* The target score is low where copying is right and high where it is
   wrong: the model changes the number in every case, also where the structure is numbered
   as the request is.
4. *Neither.* The target score is low in both rows, and the loss lies elsewhere.

Only pattern 2 shows that a model knows how each structure is numbered. With the grounding
pack, patterns 1 and 3 should both turn into pattern 2. The patterns describe one model: in
a mean over models, a mixture of copying and converting models could pass for pattern 4, so
the question is answered model by model (SI Section S9). A model shows pattern 1 when
the interval of its difference (copying right minus copying wrong) lies above zero, and
pattern 3 when it lies below zero; otherwise pattern 2 or 4 is read from the level of the
two rows, which we report and do not classify by rule.
⟦PENDING: final run — the number of models under each pattern, from the per-model rows of SI Section S9⟧

### 6.5 Follow-up turns, several right answers, planned comparisons

**Table 11. Follow-up turns and requests with several right answers.** *Task success rate*:
share of answers whose drawn state is exactly right (for a request with several right
answers: equal to any one of the accepted answers), strict, mean over the models. A
follow-up turn *needs no change* when the start state already shows what is asked; the
right answer returns it unaltered.

{{include:generated/table_final_followup.md|else:generated/shape_followup.md}}

**Table 12. Planned comparisons 1 to 6 of Section 5.4.** Each row compares the task success
rate (strict, mean over the models) between two groups of tasks or two conditions, with a
95% interval on the difference (structures resampled). The conditions are those of Table 5;
the one JSON-mode answer to a task is set against the mean of its {{plan.samples}} main
answers. *Both tracks* means that the tasks of the two tracks are pooled.

{{include:generated/table_final_robustness.md|else:generated/shape_robustness.md}}

⟦PENDING: final run — outcome counts per model (valid, unshowable by kind, schema-breaking, cut off), the repaired scores, F1 valid-only and the cost per model, as tables in SI Section S9⟧

⟦PENDING: rating study — the four results named in Section 5.5, with intervals: the share of the grader's task successes that people call the same, the share of the other answers that people call different, the same two shares for the target score, and the agreement between raters⟧

### 6.6 Preliminary evidence from the first version (pilot run, October 2026)

<div class="box">

**Everything in this box is preliminary.** The pilot run of {{run.date:date}} had
{{oct.spec.n_models}} of the {{plan.n_core_models}} core models, {{mvs.n_tasks}} scene tasks
on {{mvs.n_structures}} structures, and {{mvs.spec.samples_per_task:word}} answer per task. None of its tasks is in
the corpus of Section 3. Its archived answers are graded here with the present grader
against the references of that time. The numbers can show patterns; they cannot rank the
leading models.

**Finding 1: whether the answer was valid decided the ranking.** Of {{oct.spec.n:,}}
answers, {{oct.spec.valid_share:.0%}} were valid scenes. Per model the share ranged from
{{oct.spec.valid_share_min:.0%}} to {{oct.spec.valid_share_max:.0%}}, and strict F1 from
{{oct.spec.f1_min:.2f}} to {{oct.spec.f1_max:.2f}}; the two are nearly proportional
(SI Table S21). Valid-only, the models are much closer (F1 from {{oct.spec.valid.f1_min:.2f}} to
{{oct.spec.valid.f1_max:.2f}}). Most invalid answers were not parseable JSON, often with
unbalanced braces: a scene is a deeply nested tree, and one brace too many loses the whole
answer. This is why the final run reports strict and valid-only scores together and adds a
JSON-mode condition.

**Finding 2: clinical tasks lost their points on unrequested context, not on the residue.**
The clinical category scored lowest: strict F1 {{oct.spec.clinical.f1:.2f}}, and task
success in {{oct.spec.clinical.success_n}} of {{oct.spec.clinical.n}} answers (Figure 6).
The natural reading is that finding the residue of a variant is hard. That reading is wrong
for this run. In {{oct.spec.clinical.highlight_exact:.0%}} of the {{oct.spec.clinical.n}}
clinical answers, and in {{oct.spec.clinical.highlight_valid_share:.0%}} of the valid ones,
the requested residue
was drawn exactly as in the reference. The points were lost elsewhere: each clinical
reference also drew a grey cartoon of the whole protein, and the requests asked only for
the residue. There was a second flaw. All {{mvs.spec.regime.Clinical.n_tasks}} clinical
tasks used a single structure in which author numbers equal UniProt numbers, so the
category could not test the mapping at all. "Most answers drew the right residue" is
therefore a statement about drawing, not about mapping.

![**Figure 6. Pilot run: three scores by category (preliminary).** All three are on a scale from 0 to 1 (0.70 is 70% of answers; SI Table S22 gives the numbers). *F1* (how much of the drawn state is right) and *task success* (the share of answers whose drawn state is exactly right) are strict, over all answers of all {{oct.spec.n_models}} models; an unshowable answer scores 0. *Requested part exactly right*: among answers to tasks whose reference marks out a requested part against a background, the share that draw that part exactly as the reference does, whatever the rest of the answer shows. It is the forerunner of the target score; the pilot tasks stored no target. The number of answers behind each bar is printed above it (n). Three categories with few tasks are pooled in the middle group. In the clinical category the requested part was usually right and the whole drawn state almost never.](generated/fig_october_regrade.svg)

**Further findings** rest on other conditions of the pilot run and on a separate run of
the first version's call-list tasks in {{legacy_api.run:month}} (SI Section S13.1, Findings
3 to 6). Grounding packs did not help, which
Finding 2 explains: the residue was already right without them. Without the format guide,
none of {{mvs.bare.n_samples}} answers was a valid scene. In the call-list run, a keyword
script reached a mean F1 of {{legacy_api.baseline_f1:.2f}} where the models scored
{{legacy_api.f1_min:.2f}} to {{legacy_api.f1_max:.2f}}, which is why that track was
rebuilt. And a trial of the rating study with {{pilot.n_raters:word}} raters
was too small to validate anything.

</div>
